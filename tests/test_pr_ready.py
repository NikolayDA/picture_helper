"""Drift-Vorabprüfung ``scripts/pr_ready.py`` (#1041).

Geprüft wird an synthetischen Repositories (Muster ``tiny_repo`` aus
``tests/test_release_freeze.py``), weil die Regeln auf echten git-Diffs
arbeiten – gegen Attrappen wäre gerade das ungeprüft, was schiefgeht:
Rename-Auflösung, ``core.quotepath`` und untracked Dateien.

Dazu zwei Drift-Wächter: Die Namensmengen des Skripts sind handgepflegte
Kopien (``DOC_NAMES``/``LANGUAGES`` aus ``tests/test_i18n_docs.py``, die
Lizenzfelder aus ``scripts/generate_license_report.py``). Das Produktionsskript
darf kein Testmodul importieren; ohne diese Wächter liefen die Kopien still
auseinander und die Vorabprüfung prüfte eine Pflicht, die es nicht mehr gibt –
oder übersähe eine neue.
"""
from __future__ import annotations

import contextlib
import io
import json
import re
import subprocess
from pathlib import Path

import pytest

from scripts import pr_ready

ROOT = Path(__file__).resolve().parent.parent

#: Existiert real im Repository und ist der Grund für ``-z``.
SPACED_UMLAUT_PATH = "design/Prototyp Ä - Geführter Workflow.dc.html"

#: Diese Datei kennt **nur** die Policy des Fixtures. Klassifizierte das
#: Skript gegen die Policy des eigenen Checkouts, erschiene sie als unbekannt –
#: der Test würde den Unterschied also sehen (Review-Befund PR #1065).
FIXTURE_ONLY_PATH = "nur-im-fixture.md"


def _fixture_policy() -> str:
    """Minimale, gültige Pfadpolicy für die synthetischen Repositories.

    ``design/`` bleibt bewusst unklassifiziert – daran hängt der Nachweis für
    Sonderzeichen-Pfade.
    """
    return json.dumps(
        {
            "schema": 1,
            "policy_version": 1,
            "unknown_path_behavior": "candidate-relevant-warning",
            "release_neutral": [
                {
                    "id": "fixture-only",
                    "kind": "exact",
                    "path": FIXTURE_ONLY_PATH,
                    "sample_path": FIXTURE_ONLY_PATH,
                    "reason": "Nur im Fixture – Beleg, dass --repo zählt.",
                    "evidence": ["Kein Build-Input; existiert nur im Test"],
                }
            ],
            "candidate_relevant": [
                {"id": name.replace("/", "-").replace(".", "-"), "kind": kind,
                 "path": name, "sample_path": sample,
                 "reason": "Fixture-Regel."}
                for name, kind, sample in (
                    ("docs/", "prefix", "docs/x.md"),
                    ("bgremover/", "prefix", "bgremover/x.py"),
                    ("packaging/", "prefix", "packaging/x.sh"),
                    ("requirements/", "prefix", "requirements/x.txt"),
                    ("release/", "prefix", "release/path-policy.json"),
                    ("scripts/", "prefix", "scripts/x.py"),
                    ("README.md", "exact", "README.md"),
                    ("LIESMICH.md", "exact", "LIESMICH.md"),
                    ("ANLEITUNG.md", "exact", "ANLEITUNG.md"),
                    ("ANLEITUNG.pdf", "exact", "ANLEITUNG.pdf"),
                    ("LICENSES.md", "exact", "LICENSES.md"),
                    ("pyproject.toml", "exact", "pyproject.toml"),
                )
            ],
            "drift_guards": {},
        },
        indent=2,
    )


def _run(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _write(repo: Path, relative: str, text: str) -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _commit_all(repo: Path, message: str) -> None:
    _run(repo, "add", "-A")
    _run(repo, "commit", "-q", "-m", message)


@pytest.fixture
def pr_repo(tmp_path: Path) -> Path:
    """Repository mit ``main`` als Basis und ausgechecktem Feature-Branch."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(repo, "init", "-q", "-b", "main")
    _run(repo, "config", "user.email", "test@example.invalid")
    _run(repo, "config", "user.name", "Test")
    # Nicht-ASCII-Pfade würden ohne -z escaped ausgegeben – genau der Fall,
    # gegen den die Erfassung immun sein muss.
    _run(repo, "config", "core.quotepath", "true")
    _write(repo, "README.md", "basis\n")
    _write(repo, "ANLEITUNG.md", "basis\n")
    _write(repo, "ANLEITUNG.pdf", "%PDF-basis\n")
    _write(repo, "LICENSES.md", "basis\n")
    _write(repo, "pyproject.toml", _pyproject(deps='["pillow"]'))
    _write(repo, "release/path-policy.json", _fixture_policy())
    for language in pr_ready.LANGUAGES:
        for name in pr_ready.DOC_NAMES:
            _write(repo, f"docs/i18n/{language}/{name}", "basis\n")
    _commit_all(repo, "basis")
    _run(repo, "checkout", "-q", "-b", "feature")
    return repo


def _pyproject(*, deps: str = '["pillow"]', tool_line: str = "line-length = 100") -> str:
    return (
        "[project]\n"
        'name = "bgremover"\n'
        'version = "2.9.0"\n'
        'license = "GPL-3.0-or-later"\n'
        f"dependencies = {deps}\n\n"
        "[tool.ruff]\n"
        f"{tool_line}\n"
    )


def _check(repo: Path, base: str = "main") -> tuple[int, str]:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = pr_ready.main(["--repo", str(repo), "--base", base])
    return code, buffer.getvalue()


def _codes(output: str) -> set[str]:
    return set(re.findall(r"^(?:FEHLER|HINWEIS)\s+\[([a-z0-9-]+)\]", output, flags=re.M))


# ── Grünfall und Startfehler ──────────────────────────────────────────


def test_clean_branch_reports_no_duty_and_shows_the_base(pr_repo: Path) -> None:
    code, output = _check(pr_repo)

    assert code == 0
    assert "keine Drift-Pflicht fällig" in output
    # Basis-Ref und aufgelöster SHA müssen sichtbar sein: ein veralteter
    # lokaler Stand soll auffallen, statt still zu wirken.
    head = subprocess.run(
        ["git", "-C", str(pr_repo), "rev-parse", "main"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert "Basis main" in output
    assert head[:12] in output


def test_missing_base_ref_aborts_with_a_recipe(pr_repo: Path) -> None:
    code, output = _check(pr_repo, base="origin/main")

    assert code == 2
    assert "[start]" in output
    assert "git fetch origin main" in output
    assert "keine Drift-Pflicht" not in output


# ── Die vier Pflichten ────────────────────────────────────────────────


def test_anleitung_without_regenerated_pdf_is_an_error(pr_repo: Path) -> None:
    _write(pr_repo, "ANLEITUNG.md", "neu\n")
    for language in pr_ready.LANGUAGES:
        _write(pr_repo, f"docs/i18n/{language}/ANLEITUNG.md", "neu\n")
    _commit_all(pr_repo, "handbuch")

    code, output = _check(pr_repo)

    assert code == 1
    assert "anleitung-pdf" in _codes(output)
    assert 'pip install -e ".[docs]"' in output
    assert "python scripts/generate_anleitung_pdf.py" in output


def test_regenerated_pdf_clears_the_duty(pr_repo: Path) -> None:
    _write(pr_repo, "ANLEITUNG.md", "neu\n")
    _write(pr_repo, "ANLEITUNG.pdf", "%PDF-neu\n")
    for language in pr_ready.LANGUAGES:
        _write(pr_repo, f"docs/i18n/{language}/ANLEITUNG.md", "neu\n")
    _commit_all(pr_repo, "handbuch samt pdf")

    code, output = _check(pr_repo)

    assert code == 0
    assert "anleitung-pdf" not in _codes(output)


def test_canonical_doc_without_translations_is_an_error(pr_repo: Path) -> None:
    _write(pr_repo, "README.md", "neu\n")
    _commit_all(pr_repo, "readme")

    code, output = _check(pr_repo)

    assert code == 1
    assert "i18n" in _codes(output)
    for language in pr_ready.LANGUAGES:
        assert f"docs/i18n/{language}/README.md" in output


def test_translated_doc_change_is_clean(pr_repo: Path) -> None:
    _write(pr_repo, "README.md", "neu\n")
    for language in pr_ready.LANGUAGES:
        _write(pr_repo, f"docs/i18n/{language}/README.md", "neu\n")
    _commit_all(pr_repo, "readme in sechs Sprachen")

    code, output = _check(pr_repo)

    assert code == 0, output


def test_license_relevant_pyproject_change_is_an_error(pr_repo: Path) -> None:
    _write(pr_repo, "pyproject.toml", _pyproject(deps='["pillow", "numpy"]'))
    _commit_all(pr_repo, "neue abhaengigkeit")

    code, output = _check(pr_repo)

    assert code == 1
    assert "lizenz-snapshot" in _codes(output)
    assert "dependencies" in output
    assert "--all-langs" in output


def test_tool_only_pyproject_change_is_not_a_snapshot_error(pr_repo: Path) -> None:
    """Der Lizenzreport liest ``[project]`` – ``[tool.*]`` ist keine Eingabe.

    Ohne den semantischen Vergleich wäre jede Ruff-Einstellung ein Fehlalarm,
    und ein Fehlalarm pro Werkzeugänderung entwertet die Prüfung schneller,
    als eine übersehene Pflicht sie rechtfertigt.
    """
    _write(pr_repo, "pyproject.toml", _pyproject(tool_line="line-length = 120"))
    _commit_all(pr_repo, "ruff-einstellung")

    code, output = _check(pr_repo)

    assert code == 0, output
    assert "lizenz-snapshot" not in _codes(output)


def test_constraints_change_without_snapshot_is_an_error(pr_repo: Path) -> None:
    _write(pr_repo, "requirements/constraints.txt", "pillow==11.0.0\n")
    _commit_all(pr_repo, "pin")

    code, output = _check(pr_repo)

    assert code == 1
    assert "lizenz-snapshot" in _codes(output)


def test_constraints_stay_decidable_without_a_toml_parser(
    pr_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Der häufigste Fall darf nicht am fehlenden Parser vorbeirutschen.

    Ein Dependency-Bump berührt typischerweise ``constraints.txt`` **und**
    ``pyproject.toml``. Ohne ``tomli`` (Python 3.10, die Mindestversion) ist
    nur der zweite Teil unentscheidbar; der erste bleibt ein reiner
    Pfadvergleich. Ein gemeinsamer Abbruch hätte den Lauf grün gemacht,
    obwohl die Pflicht nachweisbar fällig ist (Review-Befund PR #1065).
    """
    monkeypatch.setattr(pr_ready, "_load_toml", lambda text: None)
    monkeypatch.setattr(pr_ready, "toml_parser_available", lambda: False)
    _write(pr_repo, "requirements/constraints.txt", "pillow==11.0.0\n")
    _write(pr_repo, "pyproject.toml", _pyproject(deps='["pillow", "numpy"]'))
    _commit_all(pr_repo, "bump")

    code, output = _check(pr_repo)

    assert code == 1, output
    assert "FEHLER" in output and "HINWEIS" in output
    assert "requirements/constraints.txt" in output
    assert "kein TOML-Parser" in output


def test_pyproject_alone_without_a_toml_parser_stays_a_note(
    pr_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ohne Parser ist der pyproject-Teil allein wirklich unentscheidbar."""
    monkeypatch.setattr(pr_ready, "_load_toml", lambda text: None)
    monkeypatch.setattr(pr_ready, "toml_parser_available", lambda: False)
    _write(pr_repo, "pyproject.toml", _pyproject(deps='["pillow", "numpy"]'))
    _commit_all(pr_repo, "bump")

    code, output = _check(pr_repo)

    assert code == 0, output
    assert "kein TOML-Parser" in output


def test_invalid_toml_in_the_worktree_does_not_crash(pr_repo: Path) -> None:
    """Der Arbeitsbaum ist der Normalfall – auch halb editiert.

    ``tomllib.loads`` wirft bei kaputtem TOML; ohne Abfangen endete
    ``make pr-ready`` mit einem Traceback statt mit dem zugesicherten
    Verhalten (Review-Befund PR #1065).
    """
    (pr_repo / "pyproject.toml").write_text("[project\nkaputt = \n", encoding="utf-8")

    code, output = _check(pr_repo)

    assert code == 0, output
    assert "ungültiges TOML" in output
    assert "lizenz-snapshot" in _codes(output)


def test_path_policy_comes_from_the_repository_under_check(pr_repo: Path) -> None:
    """``--repo`` muss auch für die Pfadpolicy gelten.

    Die Fixture-Policy kennt ``nur-im-fixture.md``, die echte Policy dieses
    Checkouts nicht. Klassifizierte das Skript gegen die eigene, erschiene die
    Datei als unbekannter Pfad – der Unterschied ist hier der ganze Nachweis.
    """
    from scripts import release_path_policy as rpp

    assert not rpp.classify_path(FIXTURE_ONLY_PATH, rpp.load_policy()).explicit

    _write(pr_repo, FIXTURE_ONLY_PATH, "inhalt\n")
    _commit_all(pr_repo, "fixture-eigener pfad")

    code, output = _check(pr_repo)

    assert code == 0, output
    assert "pfadpolicy" not in _codes(output)


def test_missing_policy_in_the_checked_repository_is_a_note(pr_repo: Path) -> None:
    """Ohne Policy entfällt die Regel mit Hinweis statt mit einem Abbruch."""
    (pr_repo / "release" / "path-policy.json").unlink()
    _commit_all(pr_repo, "policy entfernt")

    code, output = _check(pr_repo)

    assert code == 0, output
    assert "fehlt in diesem Repository" in output


def test_changelog_heuristic_stays_a_note(pr_repo: Path) -> None:
    """Nicht jede Codeänderung ist nutzersichtbar – deshalb kein Fehler."""
    _write(pr_repo, "bgremover/canvas.py", "x = 1\n")
    _commit_all(pr_repo, "code")

    code, output = _check(pr_repo)

    assert code == 0, output
    assert "changelog" in _codes(output)
    assert "HINWEIS" in output


def test_packaging_change_also_triggers_the_changelog_note(pr_repo: Path) -> None:
    _write(pr_repo, "packaging/linux/build_deb.sh", "echo neu\n")
    _commit_all(pr_repo, "packaging")

    assert "changelog" in _codes(_check(pr_repo)[1])


# ── Arbeitsbaum, Sonderzeichen, Umbenennung ───────────────────────────


def test_untracked_unknown_path_is_a_note_and_stays_green(pr_repo: Path) -> None:
    """Die neue Datei ist der Fall, den ein reiner Commit-Diff verpasst."""
    _write(pr_repo, "unbekannt/neu.txt", "inhalt\n")

    code, output = _check(pr_repo)

    assert code == 0, output
    assert "pfadpolicy" in _codes(output)
    assert "unbekannt/neu.txt" in output
    assert "kandidatenrelevant" in output
    assert "1 untracked" in output


def test_unstaged_worktree_change_counts(pr_repo: Path) -> None:
    _write(pr_repo, "ANLEITUNG.md", "nur im arbeitsbaum\n")

    code, output = _check(pr_repo)

    assert code == 1
    assert "anleitung-pdf" in _codes(output)


def test_path_with_space_and_umlaut_survives_quotepath(pr_repo: Path) -> None:
    """``core.quotepath`` steht im Fixture auf ``true`` – ohne ``-z`` käme hier
    ein escapter Name an und die Klassifikation liefe auf einen anderen Pfad."""
    _write(pr_repo, SPACED_UMLAUT_PATH, "<html>\n")
    _commit_all(pr_repo, "prototyp")

    changes = pr_ready.collect_changes(pr_repo, "main")

    assert SPACED_UMLAUT_PATH in changes.paths
    assert not any("\\" in path for path in changes.paths)
    # Und er wird klassifiziert, nicht nur erfasst: die Pfadpolicy kennt
    # ``design/`` nicht, der Pfad muss also unverstümmelt im Befund stehen.
    code, output = _check(pr_repo)
    assert code == 0, output
    assert "pfadpolicy" in _codes(output)
    assert SPACED_UMLAUT_PATH in output


def test_leading_space_in_the_first_entry_survives(pr_repo: Path) -> None:
    """``strip`` über die NUL-Liste beschädigt genau den ersten Eintrag.

    Gemessen: git terminiert auch den letzten Eintrag mit NUL, ein
    *abschließendes* Leerzeichen ist dadurch geschützt – ein *führendes* im
    ersten Eintrag nicht. Diese Datei ist die einzige Änderung und damit
    zugleich der erste Eintrag (Review-Befund PR #1065).
    """
    leading = " führend.txt"
    _write(pr_repo, leading, "inhalt\n")

    changes = pr_ready.collect_changes(pr_repo, "main")

    assert leading in changes.paths
    assert leading.strip() not in changes.paths


def test_rename_reports_both_sides(pr_repo: Path) -> None:
    """``--no-renames``: sonst meldete git nur das Ziel und die Quelle fiele
    aus der Klassifikation – dieselbe Falle wie im Freeze-Gate."""
    _run(pr_repo, "mv", "README.md", "LIESMICH.md")
    _commit_all(pr_repo, "umbenannt")

    changes = pr_ready.collect_changes(pr_repo, "main")

    assert "README.md" in changes.paths
    assert "LIESMICH.md" in changes.paths


# ── Drift-Wächter der handgepflegten Kopien ───────────────────────────


def test_doc_names_and_languages_match_the_i18n_test() -> None:
    from tests import test_i18n_docs

    assert pr_ready.DOC_NAMES == test_i18n_docs.DOC_NAMES
    assert pr_ready.LANGUAGES == test_i18n_docs.LANGUAGES


def test_license_fields_match_what_the_generator_reads() -> None:
    """Regel 4 steht und fällt mit dieser Menge.

    Der Generator liest sie als ``proj.get("<feld>")``; kommt dort ein Feld
    hinzu, prüfte die Vorabprüfung sonst weiter die alte Menge und bliebe bei
    einer echten Änderung still.
    """
    source = (ROOT / "scripts" / "generate_license_report.py").read_text(encoding="utf-8")
    read = set(re.findall(r'proj\.get\(\s*"([a-z-]+)"', source))

    assert read == set(pr_ready.LICENSE_PROJECT_FIELDS), sorted(read)


def test_makefile_and_documentation_offer_pr_ready() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    phony = re.search(r"(?m)^\.PHONY:(?P<targets>.*)$", makefile)
    assert phony and "pr-ready" in phony.group("targets").split()
    assert re.search(r"(?m)^pr-ready:", makefile)
    assert "scripts/pr_ready.py" in makefile

    for name in ("CLAUDE.md", "CONTRIBUTING.md", ".github/PULL_REQUEST_TEMPLATE.md"):
        assert "make pr-ready" in (ROOT / name).read_text(encoding="utf-8"), name
