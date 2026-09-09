"""``make doctor`` gegen die beiden Installationsverträge (#1053).

Bis #1053 wertete ``scripts/check_test_env.py`` jeden editable Install als
``FAIL`` – und widersprach damit dem SessionStart-Hook, der seit #1031 bewusst
editable installiert. Der Doctor akzeptiert jetzt **einen** der beiden
Verträge (editable Link auf diesen Checkout / nicht-editable Install) und
verlangt mit ``--require-installed`` (``make pr-check``) nur den zweiten. Die
Gültigkeit eines Links entscheidet weiterhin allein
``scripts/check_install_provenance.py``; der Doctor importiert die Regel.

Die Fälle werden über synthetische Distributions-Metadaten nachgestellt
(Muster von ``tests/test_check_install_provenance.py``), die Subprozess-Importe
werden gepatcht – netzfrei, ohne pip, ohne die echte Umgebung zu verändern.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "check_test_env.py"
MAKEFILE = ROOT / "Makefile"

_SPEC = importlib.util.spec_from_file_location("check_test_env", SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
cte = importlib.util.module_from_spec(_SPEC)
sys.modules["check_test_env"] = cte
_SPEC.loader.exec_module(cte)
cip = cte.cip


# ── Hilfen ────────────────────────────────────────────────────────────


def _dist_info(site: Path, *, direct_url: object | None = None, version: str = "1.0") -> Path:
    info = site / f"bgremover-{version}.dist-info"
    info.mkdir(parents=True)
    (info / "METADATA").write_text(
        f"Metadata-Version: 2.1\nName: bgremover\nVersion: {version}\n", encoding="utf-8"
    )
    if direct_url is not None:
        (info / "direct_url.json").write_text(json.dumps(direct_url), encoding="utf-8")
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


@pytest.fixture
def imports(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    """Subprozess-Importe patchen: der Test steuert, was der Import trifft."""
    state: dict[str, object] = {"neutral_ok": True, "installed_from": None, "called": []}
    calls = state["called"]
    assert isinstance(calls, list)

    def fake_neutral(repo_root: Path, python: str = sys.executable) -> object:
        calls.append("neutral")
        ok = bool(state["neutral_ok"])
        return cip.Finding(ok, "neutral-import", "gepatcht")

    def fake_location(python: str = sys.executable) -> tuple[Path | None, str]:
        calls.append("location")
        target = state["installed_from"]
        return (None, "kaputt") if target is None else (Path(str(target)), "")

    monkeypatch.setattr(cip, "check_neutral_import", fake_neutral)
    monkeypatch.setattr(cte, "_neutral_import_location", fake_location)
    monkeypatch.setattr(cte.shutil, "which", lambda name: f"/venv/bin/{name}")
    return state


def _run(repo: Path, site: Path, *, require_installed: bool = False) -> cte.Reporter:
    reporter = cte.Reporter()
    cte._check_bgremover_install(
        reporter,
        require_installed=require_installed,
        repo_root=repo,
        search_path=[str(site)],
    )
    return reporter


# ── Vertragszuordnung ─────────────────────────────────────────────────


def test_classify_editable_link_on_this_checkout(repo: Path, site: Path) -> None:
    _dist_info(site, direct_url=_editable(repo))
    contract, _ = cte.classify_install(cip.check_metadata_provenance(repo, search_path=[str(site)]))
    assert contract == cte.CONTRACT_EDITABLE


def test_classify_single_non_editable_install(repo: Path, site: Path) -> None:
    _dist_info(site, direct_url=_editable(repo, editable=False))
    contract, _ = cte.classify_install(cip.check_metadata_provenance(repo, search_path=[str(site)]))
    assert contract == cte.CONTRACT_INSTALLED


def test_classify_foreign_checkout_matches_no_contract(repo: Path, site: Path, tmp_path: Path) -> None:
    other = tmp_path / "other"
    other.mkdir()
    _dist_info(site, direct_url=_editable(other))
    contract, details = cte.classify_install(
        cip.check_metadata_provenance(repo, search_path=[str(site)])
    )
    assert contract is None
    assert cip.KIND_FOREIGN_EDITABLE in details


def test_classify_stale_copy_next_to_a_link_matches_no_contract(
    repo: Path, site: Path, tmp_path: Path
) -> None:
    """Der #1031-Fall: gültiger Link plus alte Wheel-Kopie – der Import
    entscheidet nach Suchpfad, nicht nach Gültigkeit. In keinem Modus grün."""
    other_site = tmp_path / "other-site"
    _dist_info(site, direct_url=_editable(repo))
    _dist_info(other_site, direct_url=_editable(tmp_path / "snapshot", editable=False))
    contract, _ = cte.classify_install(
        cip.check_metadata_provenance(repo, search_path=[str(site), str(other_site)])
    )
    assert contract is None


def test_classify_two_non_editable_copies_match_no_contract(
    repo: Path, site: Path, tmp_path: Path
) -> None:
    other_site = tmp_path / "other-site"
    _dist_info(site, direct_url=_editable(tmp_path / "a", editable=False))
    _dist_info(other_site, direct_url=_editable(tmp_path / "b", editable=False), version="0.9")
    contract, _ = cte.classify_install(
        cip.check_metadata_provenance(repo, search_path=[str(site), str(other_site)])
    )
    assert contract is None


# ── Doctor-Verdikt je Modus ───────────────────────────────────────────


def test_editable_link_is_ok_in_session_mode(repo: Path, site: Path, imports: dict) -> None:
    _dist_info(site, direct_url=_editable(repo))
    reporter = _run(repo, site)
    assert not reporter.errors and not reporter.warnings
    assert imports["called"] == ["neutral"], "Postcondition des Hook-Vertrags muss laufen"


def test_editable_link_fails_with_require_installed(repo: Path, site: Path, imports: dict) -> None:
    _dist_info(site, direct_url=_editable(repo))
    reporter = _run(repo, site, require_installed=True)
    assert len(reporter.errors) == 1
    assert "make install-test" in reporter.errors[0]
    assert "editable" in reporter.errors[0]


def test_editable_link_whose_neutral_import_misses_fails(
    repo: Path, site: Path, imports: dict
) -> None:
    _dist_info(site, direct_url=_editable(repo))
    imports["neutral_ok"] = False
    reporter = _run(repo, site)
    assert len(reporter.errors) == 1
    assert "neutral-cwd import" in reporter.errors[0]


@pytest.mark.parametrize("require_installed", [False, True])
def test_non_editable_install_is_ok_in_both_modes(
    repo: Path, site: Path, imports: dict, require_installed: bool
) -> None:
    _dist_info(site, direct_url=_editable(repo, editable=False))
    imports["installed_from"] = site / "bgremover" / "__init__.py"
    reporter = _run(repo, site, require_installed=require_installed)
    assert not reporter.errors and not reporter.warnings
    assert imports["called"] == ["location"]


def test_non_editable_install_importing_from_source_tree_warns(
    repo: Path, site: Path, imports: dict
) -> None:
    _dist_info(site, direct_url=_editable(repo, editable=False))
    imports["installed_from"] = repo / "bgremover" / "__init__.py"
    reporter = _run(repo, site)
    assert not reporter.errors
    assert len(reporter.warnings) == 1 and "source tree" in reporter.warnings[0]


def test_non_editable_install_that_cannot_import_fails(
    repo: Path, site: Path, imports: dict
) -> None:
    _dist_info(site, direct_url=_editable(repo, editable=False))
    imports["installed_from"] = None
    reporter = _run(repo, site)
    assert len(reporter.errors) == 1 and "neutral cwd" in reporter.errors[0]


@pytest.mark.parametrize("require_installed", [False, True])
def test_foreign_checkout_fails_in_both_modes(
    repo: Path, site: Path, tmp_path: Path, imports: dict, require_installed: bool
) -> None:
    other = tmp_path / "other"
    other.mkdir()
    _dist_info(site, direct_url=_editable(other))
    reporter = _run(repo, site, require_installed=require_installed)
    assert len(reporter.errors) == 1
    assert "neither contract" in reporter.errors[0]
    assert imports["called"] == [], "auf einer ungültigen Installation wird nichts importiert"


def test_missing_distribution_fails(repo: Path, site: Path, imports: dict) -> None:
    reporter = _run(repo, site)
    assert reporter.errors == ["bgremover is not installed. Run: make install-test"]


def test_missing_console_script_is_a_finding(
    repo: Path, site: Path, imports: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    _dist_info(site, direct_url=_editable(repo))
    monkeypatch.setattr(cte.shutil, "which", lambda name: None)
    reporter = _run(repo, site)
    assert any("Console script" in err for err in reporter.errors)


# ── CLI, Makefile, echte Umgebung ─────────────────────────────────────


def test_cli_flag_is_parsed() -> None:
    assert cte.build_parser().parse_args([]).require_installed is False
    assert cte.build_parser().parse_args(["--require-installed"]).require_installed is True


def test_makefile_requires_installed_only_for_pr_check() -> None:
    text = MAKEFILE.read_text(encoding="utf-8")
    assert re.search(r"^pr-check: DOCTOR_ARGS := --require-installed$", text, re.M)
    assert re.search(r'^\tscripts/check_test_env\.py|check_test_env\.py \$\(DOCTOR_ARGS\)$', text, re.M)
    doctor_recipe = re.search(r"^doctor:\n\t(.*)$", text, re.M)
    assert doctor_recipe and "$(DOCTOR_ARGS)" in doctor_recipe.group(1)
    assert "--require-installed" not in doctor_recipe.group(1), "make doctor bleibt der Session-Modus"


def test_the_real_environment_satisfies_one_contract() -> None:
    """Web-Session (editable, Hook) wie PR-CI (nicht-editable, pr-check): ohne
    Option muss der Doctor die tatsächliche Umgebung akzeptieren."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)], cwd=ROOT, text=True, capture_output=True, timeout=180
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "contract" in proc.stdout
