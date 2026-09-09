"""Installationsprovenienz-Prüfung des SessionStart-Hooks (#1031).

``scripts/check_install_provenance.py`` entscheidet, ob der Hook den
Kurzschluss nehmen darf. Die Fälle aus den Akzeptanzkriterien werden hier
über synthetische Distributions-Metadaten (``importlib.metadata`` mit
eigenem Suchpfad) und ein synthetisches Paket für die Import-Postcondition
nachgestellt – netzfrei, ohne pip und ohne die echte Umgebung zu verändern.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "check_install_provenance.py"
HOOK = ROOT / ".claude" / "hooks" / "session-start.sh"

_SPEC = importlib.util.spec_from_file_location("check_install_provenance", SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
cip = importlib.util.module_from_spec(_SPEC)
sys.modules["check_install_provenance"] = cip
_SPEC.loader.exec_module(cip)


# ── Hilfen: synthetische Metadaten ────────────────────────────────────


def _metadata_text(name: str = "bgremover", version: str = "1.0") -> str:
    return f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n"


def _dist_info(
    site: Path,
    *,
    version: str = "1.0",
    direct_url: object | None = None,
    raw_direct_url: str | None = None,
    name: str = "bgremover",
) -> Path:
    """Ein ``*.dist-info`` wie von pip geschrieben (optional mit direct_url.json)."""
    info = site / f"{name}-{version}.dist-info"
    info.mkdir(parents=True)
    (info / "METADATA").write_text(_metadata_text(name, version), encoding="utf-8")
    if raw_direct_url is not None:
        (info / "direct_url.json").write_text(raw_direct_url, encoding="utf-8")
    elif direct_url is not None:
        (info / "direct_url.json").write_text(json.dumps(direct_url), encoding="utf-8")
    return info


def _egg_info(checkout: Path, *, version: str = "1.0") -> Path:
    """Legacy-editable: ``bgremover.egg-info`` liegt im Checkout selbst."""
    info = checkout / "bgremover.egg-info"
    info.mkdir(parents=True)
    (info / "PKG-INFO").write_text(_metadata_text(version=version), encoding="utf-8")
    return info


def _editable(url_root: Path, editable: bool = True) -> dict[str, object]:
    return {"url": url_root.resolve().as_uri(), "dir_info": {"editable": editable}}


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    checkout = tmp_path / "checkout"
    (checkout / "bgremover").mkdir(parents=True)
    (checkout / "bgremover" / "__init__.py").write_text("", encoding="utf-8")
    return checkout


@pytest.fixture
def site(tmp_path: Path) -> Path:
    path = tmp_path / "site-packages"
    path.mkdir()
    return path


def _only(findings: tuple[object, ...]) -> object:
    assert len(findings) == 1, findings
    return findings[0]


# ── Metadaten-Provenienz ──────────────────────────────────────────────


def test_pep660_editable_on_this_checkout_is_valid(repo: Path, site: Path) -> None:
    _dist_info(site, direct_url=_editable(repo))
    finding = _only(cip.check_metadata_provenance(repo, search_path=[str(site)]))
    assert finding.ok and finding.kind == cip.KIND_PEP660_EDITABLE


def test_pep660_editable_on_another_checkout_is_rejected(
    repo: Path, site: Path, tmp_path: Path
) -> None:
    """Akzeptanzkriterium: Ein editable Link auf einen anderen Checkout nimmt
    den Kurzschluss nicht."""
    other = tmp_path / "other-checkout"
    other.mkdir()
    _dist_info(site, direct_url=_editable(other))
    finding = _only(cip.check_metadata_provenance(repo, search_path=[str(site)]))
    assert not finding.ok and finding.kind == cip.KIND_FOREIGN_EDITABLE
    assert str(other.resolve()) in finding.detail and str(repo.resolve()) in finding.detail


def test_non_editable_install_from_a_directory_is_rejected(repo: Path, site: Path) -> None:
    """Der #1031-Fall: ``pip install .`` bzw. ``make pr-check`` – direct_url.json
    zeigt auf den Checkout, aber ohne ``editable``: ein Schnappschuss."""
    _dist_info(site, direct_url=_editable(repo, editable=False))
    finding = _only(cip.check_metadata_provenance(repo, search_path=[str(site)]))
    assert not finding.ok and finding.kind == cip.KIND_NON_EDITABLE


def test_wheel_install_without_direct_url_is_rejected(repo: Path, site: Path) -> None:
    _dist_info(site)
    finding = _only(cip.check_metadata_provenance(repo, search_path=[str(site)]))
    assert not finding.ok and finding.kind == cip.KIND_NON_EDITABLE
    assert str(repo.resolve()) in finding.detail


def test_vcs_install_is_not_an_editable_link(repo: Path, site: Path) -> None:
    _dist_info(
        site,
        direct_url={
            "url": "https://github.com/NikolayDA/picture_helper",
            "vcs_info": {"vcs": "git", "commit_id": "0" * 40},
        },
    )
    finding = _only(cip.check_metadata_provenance(repo, search_path=[str(site)]))
    assert not finding.ok and finding.kind == cip.KIND_NON_EDITABLE


def test_legacy_editable_on_this_checkout_is_valid(repo: Path) -> None:
    """setup.py develop / egg-info im Checkout: Distributions-Root = Repo-Wurzel."""
    _egg_info(repo)
    finding = _only(cip.check_metadata_provenance(repo, search_path=[str(repo)]))
    assert finding.ok and finding.kind == cip.KIND_LEGACY_EDITABLE


def test_legacy_editable_on_another_checkout_is_rejected(repo: Path, tmp_path: Path) -> None:
    other = tmp_path / "other-checkout"
    other.mkdir()
    _egg_info(other)
    finding = _only(cip.check_metadata_provenance(repo, search_path=[str(other)]))
    assert not finding.ok and finding.kind == cip.KIND_NON_EDITABLE


def test_missing_distribution_is_a_finding(repo: Path, site: Path) -> None:
    finding = _only(cip.check_metadata_provenance(repo, search_path=[str(site)]))
    assert not finding.ok and finding.kind == cip.KIND_MISSING


def test_a_stale_copy_next_to_a_valid_link_fails_closed(
    repo: Path, site: Path, tmp_path: Path
) -> None:
    """Zwei Distributionen: Welche der Import trifft, entscheidet die
    Suchpfad-Reihenfolge – nicht die Gültigkeit. Deshalb fail-closed."""
    stale = tmp_path / "user-site"
    _dist_info(stale, version="0.9")
    _dist_info(site, direct_url=_editable(repo))
    findings = cip.check_metadata_provenance(repo, search_path=[str(site), str(stale)])
    assert not all(item.ok for item in findings)
    assert any(item.ok and item.kind == cip.KIND_PEP660_EDITABLE for item in findings)
    assert any(
        item.kind == cip.KIND_INVALID_METADATA and "nebeneinander" in item.detail
        for item in findings
    )


def test_the_same_metadata_dir_on_the_search_path_twice_counts_once(repo: Path, site: Path) -> None:
    _dist_info(site, direct_url=_editable(repo))
    findings = cip.check_metadata_provenance(repo, search_path=[str(site), str(site)])
    assert len(findings) == 1 and findings[0].ok


def test_unrelated_distributions_are_ignored_and_names_are_normalised(
    repo: Path, site: Path
) -> None:
    _dist_info(site, name="pytest-qt")
    _dist_info(site, name="BgRemover", direct_url=_editable(repo))
    finding = _only(cip.check_metadata_provenance(repo, search_path=[str(site)]))
    assert finding.ok


def test_name_normalisation_follows_pep_503() -> None:
    assert cip._normalise_name("Bg__Remover") == "bg-remover"
    assert cip._normalise_name("bg.-_remover") == "bg-remover"


def test_two_dist_info_dirs_of_the_same_version_stay_two_findings(repo: Path, site: Path) -> None:
    """Rest einer abgebrochenen Deinstallation: gleiches ``site-packages``,
    gleiche Version, zwei Metadatenverzeichnisse – der Dedupe darf sie nicht
    zu einem Fund zusammenfassen (Review PR #1047)."""
    _dist_info(site, direct_url=_editable(repo))
    stale = site / "~gremover-1.0.dist-info"
    stale.mkdir()
    (stale / "METADATA").write_text(_metadata_text(), encoding="utf-8")
    findings = cip.check_metadata_provenance(repo, search_path=[str(site)])
    assert len(findings) >= 2 and not all(item.ok for item in findings)


def test_missing_private_metadata_path_disables_dedupe_fail_closed(
    repo: Path, site: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fehlt ``PathDistribution._path`` (private API), wird nicht dedupliziert –
    derselbe Fund zweimal ergibt zwei Eintraege und damit hoechstens einen
    ueberfluessigen Befund, nie eine still zusammengefasste Kopie."""
    _dist_info(site, direct_url=_editable(repo))
    (dist,) = cip.find_distributions(search_path=[str(site)])
    monkeypatch.setattr(cip.metadata, "distributions", lambda **_kw: iter([dist, dist]))
    assert len(cip.find_distributions(search_path=[str(site)])) == 1
    monkeypatch.setattr(cip, "_metadata_dir", lambda _dist: None)
    assert len(cip.find_distributions(search_path=[str(site)])) == 2


def test_malformed_direct_url_is_invalid_metadata(repo: Path, site: Path) -> None:
    _dist_info(site, raw_direct_url="{not json")
    finding = _only(cip.check_metadata_provenance(repo, search_path=[str(site)]))
    assert not finding.ok and finding.kind == cip.KIND_INVALID_METADATA


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("file://localhost{path}", True),
        ("file://otherhost{path}", False),
        ("https://example.invalid{path}", False),
    ],
)
def test_only_local_file_urls_link_to_the_checkout(
    repo: Path, site: Path, url: str, expected: bool
) -> None:
    _dist_info(
        site,
        direct_url={
            "url": url.format(path=repo.resolve().as_posix()),
            "dir_info": {"editable": True},
        },
    )
    finding = _only(cip.check_metadata_provenance(repo, search_path=[str(site)]))
    assert finding.ok is expected


@pytest.mark.parametrize("dirname", ["check out", "a%20b", "100%"])
def test_percent_encoded_file_url_resolves_to_the_checkout(
    tmp_path: Path, site: Path, dirname: str
) -> None:
    """Genau **eine** Dekodierung: Ein literales ``%20`` im Checkout-Pfad wird
    von ``as_uri`` als ``%2520`` abgelegt und darf nicht zum Leerzeichen
    werden (Review PR #1047 – eine zweite Dekodierung machte den Link zu
    ``foreign-editable``, und der Hook brach nach jeder Neuinstallation ab)."""
    checkout = tmp_path / dirname
    (checkout / "bgremover").mkdir(parents=True)
    _dist_info(site, direct_url=_editable(checkout))
    assert "%" in checkout.resolve().as_uri()
    finding = _only(cip.check_metadata_provenance(checkout, search_path=[str(site)]))
    assert finding.ok, finding


# ── Import-Postcondition aus neutralem Arbeitsverzeichnis ────────────


def _env_with(pythonpath: Path | None) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    if pythonpath is not None:
        env["PYTHONPATH"] = str(pythonpath)
    return env


def test_neutral_import_hits_the_checkout(repo: Path) -> None:
    finding = cip.check_neutral_import(repo, env=_env_with(repo))
    assert finding.ok, finding
    assert str((repo / "bgremover" / "__init__.py").resolve()) in finding.detail


def test_neutral_import_tolerates_noise_on_stdout(repo: Path) -> None:
    """``sitecustomize``/``.pth`` duerfen vor dem Ergebnis auf stdout schreiben
    (Review PR #1047): Gewertet wird die letzte nichtleere Zeile."""
    (repo / "sitecustomize.py").write_text(
        "print('Container-Rauschen aus sitecustomize')\nprint()\n", encoding="utf-8"
    )
    finding = cip.check_neutral_import(repo, env=_env_with(repo))
    assert finding.ok, finding


def test_neutral_import_from_a_foreign_copy_is_rejected(repo: Path, tmp_path: Path) -> None:
    """Die Suchpfad-Situation eines per Dateipfad gestarteten Skripts: Gewinnt
    eine fremde Kopie, nennt der Befund beide Pfade."""
    other = tmp_path / "other-checkout"
    (other / "bgremover").mkdir(parents=True)
    (other / "bgremover" / "__init__.py").write_text("", encoding="utf-8")
    finding = cip.check_neutral_import(repo, env=_env_with(other))
    assert not finding.ok
    assert str((other / "bgremover" / "__init__.py").resolve()) in finding.detail
    assert str((repo / "bgremover" / "__init__.py").resolve()) in finding.detail


def test_neutral_import_failure_is_a_finding_with_the_error_line(repo: Path) -> None:
    finding = cip.check_neutral_import(
        repo, name="bgremover_provenance_probe_does_not_exist", env=_env_with(None)
    )
    assert not finding.ok and "ModuleNotFoundError" in finding.detail


def test_unusable_interpreter_is_a_finding_not_a_crash(repo: Path, tmp_path: Path) -> None:
    finding = cip.check_neutral_import(repo, python=str(tmp_path / "no-such-python"))
    assert not finding.ok and "nicht ausfuehrbar" in finding.detail


# ── Orchestrierung und CLI ────────────────────────────────────────────


def test_run_skips_the_import_when_metadata_already_fail(
    repo: Path, site: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _dist_info(site)

    def _boom(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("Import darf auf ungültiger Installation nicht laufen")

    monkeypatch.setattr(cip, "check_neutral_import", _boom)
    report = cip.run(repo, search_path=[str(site)])
    assert not report.ok and report.neutral_import is None


def test_run_requires_both_checks(repo: Path, site: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _dist_info(site, direct_url=_editable(repo))
    monkeypatch.setattr(
        cip,
        "check_neutral_import",
        lambda *_a, **_k: cip.Finding(False, "neutral-import", "fremde Kopie"),
    )
    report = cip.run(repo, search_path=[str(site)])
    assert all(item.ok for item in report.metadata)
    assert not report.ok
    lines = report.lines()
    assert lines[0].startswith(f"{cip.LOG_PREFIX} ok: {cip.KIND_PEP660_EDITABLE}")
    assert lines[-1].startswith(f"{cip.LOG_PREFIX} FEHLER: neutral-import")


def test_cli_exit_code_follows_the_verdict(
    repo: Path, site: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _dist_info(site)
    rc = cip.main(["--repo-root", str(repo), "--search-path", str(site), "--skip-import"])
    out = capsys.readouterr().out
    assert rc == 1 and f"{cip.LOG_PREFIX} FEHLER: {cip.KIND_NON_EDITABLE}" in out

    _only(tuple(site.iterdir())).rename(site / "removed")
    _dist_info(site, direct_url=_editable(repo))
    rc = cip.main(["--repo-root", str(repo), "--search-path", str(site), "--skip-import"])
    assert rc == 0 and "FEHLER" not in capsys.readouterr().out


def test_cli_started_by_file_path_reports_the_real_environment_consistently() -> None:
    """Der Weg des Hooks: Start über den Dateipfad, ``sys.path[0]`` = ``scripts/``.

    Das Verdikt selbst hängt von der Umgebung ab (editable im Entwickler-venv,
    bewusst nicht-editable in der PR-CI nach ``make install-test``); geprüft
    wird deshalb die Konsistenz von Ausgabe und Exit-Code, nicht ein Wert.
    """
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=ROOT,
        check=False,
    )
    lines = [line for line in proc.stdout.splitlines() if line.startswith(cip.LOG_PREFIX)]
    assert lines, proc.stderr
    failed = any(" FEHLER: " in line for line in lines)
    assert proc.returncode == (1 if failed else 0), proc.stdout


# ── Verdrahtung im Hook ───────────────────────────────────────────────


def test_hook_gates_the_shortcut_and_the_postcondition_on_the_provenance_check() -> None:
    """Der Kurzschluss darf nicht mehr nur die Existenz der Distribution
    prüfen (#1031), und nach dem Install muss die Postcondition hart laufen."""
    hook = HOOK.read_text(encoding="utf-8")
    assert "metadata.version('bgremover')" not in hook
    assert 'PROVENANCE_CHECK="scripts/check_install_provenance.py"' in hook
    before, _, after = hook.partition(
        'pip install -q --constraint requirements/constraints.txt -e ".[test]"'
    )
    assert 'provenance_report="$(python3 "$PROVENANCE_CHECK" 2>&1)"' in before
    assert 'python3 "$PROVENANCE_CHECK"\n' in after
    # Der Kurzschluss verlangt beide Hälften.
    assert '[ "$tools_ready" = 1 ] && [ "$provenance_ready" = 1 ]' in before
