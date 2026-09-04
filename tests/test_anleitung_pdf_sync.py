"""Wächter: ``ANLEITUNG.pdf`` darf nicht hinter ``ANLEITUNG.md`` zurückfallen (#974).

Das PDF wird von Hand über ``scripts/generate_anleitung_pdf.py`` erzeugt.
Vergisst jemand den Nachzug, zeigt das ausgelieferte Handbuch einen alten
Stand, ohne dass etwas anschlägt – einmal real passiert: ``ac64c3b`` (#953)
änderte die Quelle ohne das PDF, nachgeholt hat es erst ``91b32b4`` (#954)
einen Tag später, gefunden von einem Menschen.

**Warum kein Byte- oder Hashvergleich.** Der Bau ist nicht deterministisch:
Zwei Läufe aus identischer Quelle liefern verschiedene Bytes und Größen
(Font-Subsetting bzw. Objektreihenfolge), obwohl die Metadaten keinen
Zeitstempel tragen und der extrahierte Text gleich bleibt.

**Warum nicht neu erzeugen und den Text vergleichen.** Das führe zwar jede
Abweichung, zöge aber das ``docs``-Extra (WeasyPrint samt Pango/Cairo und
DejaVu-Schriften) in einen CI-Pfad – gegen die bewusste Ausnahme in
``tests/test_dependency_constraints.py`` (``_UNAUDITED_EXTRAS``), nach der
``docs`` in keinem CI-/Release-Pfad installiert wird.

Geprüft wird deshalb die **Disziplin statt des Inhalts**: Der Commit, der
zuletzt die Quelle berührt hat, muss auch das PDF berühren – oder älter sein
als der letzte PDF-Commit. Das genügt, weil jede Änderung an der Quelle das
gerenderte PDF verändert. Nur die deutsche Fassung ist betroffen; die fünf
Übersetzungen unter ``docs/i18n/`` haben kein PDF.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

SOURCE = "ANLEITUNG.md"
PDF = "ANLEITUNG.pdf"


def _git(repo: Path, *args: str) -> str:
    """``git`` im Repo; leere Ausgabe bei Fehlschlag statt einer Ausnahme."""
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _last_commit(repo: Path, relative: str, commitish: str) -> str:
    return _git(repo, "log", "-1", "--format=%H", commitish, "--", relative)


def stale_pdf(repo: Path, commitish: str = "HEAD") -> tuple[str, str] | None:
    """``(Quell-Commit, PDF-Commit)``, wenn das PDF hinter der Quelle liegt.

    ``None`` heißt synchron – derselbe Commit, oder der PDF-Commit ist ein
    Nachfahre des Quell-Commits (das PDF wurde später noch einmal erzeugt).
    """
    source = _last_commit(repo, SOURCE, commitish)
    pdf = _last_commit(repo, PDF, commitish)
    if not source or not pdf or source == pdf:
        return None

    # Ist der Quell-Commit ein Vorfahre des PDF-Commits, wurde das PDF danach
    # geschrieben – dann ist nichts offen.
    newer = subprocess.run(
        ["git", "-C", str(repo), "merge-base", "--is-ancestor", source, pdf],
        capture_output=True,
    )
    return None if newer.returncode == 0 else (source, pdf)


def _history_reaches_the_manual() -> bool:
    """Deckt die lokale Historie beide Dateien ab?

    Bewusste Entscheidung statt eines stillen Übergehens (#974): Ein Klon,
    dessen Historie die Dateien nicht erreicht, kann die Frage nicht
    beantworten – dort wird mit Begründung übersprungen statt fälschlich
    Alarm zu schlagen. Die PR-CI checkt mit ``fetch-depth: 0`` aus, der
    Wächter läuft dort also immer. Ein flacher Klon genügt, solange er die
    beiden letzten Commits noch enthält; deshalb wird die Reichweite geprüft
    und nicht das Shallow-Flag.
    """
    return bool(
        _last_commit(ROOT, SOURCE, "HEAD") and _last_commit(ROOT, PDF, "HEAD")
    )


def test_anleitung_pdf_is_not_behind_its_source() -> None:
    """Das committete PDF muss aus dem aktuellen Markdown stammen."""
    if not _history_reaches_the_manual():
        pytest.skip(
            "Git-Historie erreicht ANLEITUNG.md/ANLEITUNG.pdf nicht "
            "(flacher Klon ohne die betreffenden Commits) – die PR-CI checkt "
            "mit fetch-depth: 0 aus und prüft dort."
        )

    stale = stale_pdf(ROOT)

    if stale is not None:
        source_commit, pdf_commit = stale
        pytest.fail(
            f"ANLEITUNG.pdf ist nicht nachgezogen: {SOURCE} zuletzt geändert in "
            f"{source_commit}, {PDF} in {pdf_commit}. Neu erzeugen mit "
            '`pip install -e ".[docs]"` und '
            "`python scripts/generate_anleitung_pdf.py`."
        )


# ── Regelverhalten an synthetischen Repos ──────────────────────────────
#
# Muster von tests/test_release_freeze.py: Die Regel wird an eigens gebauten
# Historien geprüft, damit sie nicht von der echten Historie abhängt.


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    for args in (
        ("init", "-q", "-b", "main"),
        ("config", "user.email", "test@example.org"),
        ("config", "user.name", "Test"),
    ):
        subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)
    return repo


def _commit(repo: Path, files: dict[str, str], message: str) -> str:
    for name, text in files.items():
        (repo / name).write_text(text, encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo), "commit", "-q", "-m", message],
        check=True,
        capture_output=True,
    )
    return _git(repo, "rev-parse", "HEAD")


def test_stale_pdf_accepts_a_joint_commit(tmp_path: Path) -> None:
    """Quelle und PDF im selben Commit – der Normalfall."""
    repo = _repo(tmp_path)
    _commit(repo, {SOURCE: "eins", PDF: "PDF-eins"}, "beides")

    assert stale_pdf(repo) is None


def test_stale_pdf_flags_a_source_change_without_the_pdf(tmp_path: Path) -> None:
    """Genau der Fall aus ``ac64c3b``: Quelle geändert, PDF nicht."""
    repo = _repo(tmp_path)
    _commit(repo, {SOURCE: "eins", PDF: "PDF-eins"}, "beides")
    source_only = _commit(repo, {SOURCE: "zwei"}, "nur die Quelle")

    stale = stale_pdf(repo)

    assert stale is not None
    assert stale[0] == source_only
    assert stale[0] != stale[1]


def test_stale_pdf_accepts_a_later_pdf_commit(tmp_path: Path) -> None:
    """Ein nachgereichtes PDF löst den Befund wieder auf (``91b32b4``)."""
    repo = _repo(tmp_path)
    _commit(repo, {SOURCE: "eins", PDF: "PDF-eins"}, "beides")
    _commit(repo, {SOURCE: "zwei"}, "nur die Quelle")
    assert stale_pdf(repo) is not None

    _commit(repo, {PDF: "PDF-zwei"}, "PDF nachgezogen")

    assert stale_pdf(repo) is None
