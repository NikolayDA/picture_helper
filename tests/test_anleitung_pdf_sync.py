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
gerenderte PDF verändert. Mitgeprüft wird ``scripts/generate_anleitung_pdf.py``
selbst: ``build_pdf`` setzt das Markdown mit ``_css()`` zusammen, eine reine
Layout-/Schriftänderung dort ändert das PDF also ebenso.

Die eingebetteten Screenshots sind nur **mittelbar** gedeckt: Ihr
Satzverzeichnis trägt einen Zeitstempel, ein neuer Satz fasst deshalb
ohnehin die Links in ``ANLEITUNG.md`` an. Würde das je auf einen stabilen
Pfad umgestellt, fiele diese Deckung weg.

Nur die deutsche Fassung ist betroffen; die fünf Übersetzungen unter
``docs/i18n/`` haben kein PDF.

In einem flachen Klon ist der Grenzcommit elternlos und gilt ``git log``
als Hinzufüger jeder Datei; beide Pfade lösen dann auf denselben Commit
auf. Das sähe wie „synchron" aus, ist aber keine Aussage – solche Stände
werden deshalb ausdrücklich als nicht prüfbar übersprungen.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

SOURCE = "ANLEITUNG.md"
GENERATOR = "scripts/generate_anleitung_pdf.py"
PDF = "ANLEITUNG.pdf"
#: Alles, was in das gerenderte PDF eingeht. Der Generator zählt mit, weil
#: ``build_pdf`` das Markdown mit ``_css()`` zusammensetzt – eine reine
#: Layout-/Schriftänderung dort ändert das PDF genauso wie eine
#: Textänderung (Review-Befund zu PR #979).
SOURCES = (SOURCE, GENERATOR)


def _git(repo: Path, *args: str) -> str:
    """``git`` im Repo; leere Ausgabe bei Fehlschlag statt einer Ausnahme."""
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _last_commit(repo: Path, relative: str, commitish: str) -> str:
    return _git(repo, "log", "-1", "--format=%H", commitish, "--", relative)


def stale_pdf(repo: Path, commitish: str = "HEAD") -> dict[str, tuple[str, str]] | None:
    """Quellen, die neuer sind als das PDF – ``None``, wenn keine.

    Je Eintrag ``Quelle -> (Quell-Commit, PDF-Commit)``. Synchron heißt:
    derselbe Commit, oder der PDF-Commit ist ein Nachfahre des Quell-Commits
    (das PDF wurde später noch einmal erzeugt).
    """
    pdf = _last_commit(repo, PDF, commitish)
    if not pdf:
        return None

    behind: dict[str, tuple[str, str]] = {}
    for relative in SOURCES:
        source = _last_commit(repo, relative, commitish)
        if not source or source == pdf:
            continue
        # Ist der Quell-Commit ein Vorfahre des PDF-Commits, wurde das PDF
        # danach geschrieben – dann ist nichts offen.
        newer = subprocess.run(
            ["git", "-C", str(repo), "merge-base", "--is-ancestor", source, pdf],
            capture_output=True,
        )
        if newer.returncode != 0:
            behind[relative] = (source, pdf)

    return behind or None


def _shallow_boundary(repo: Path) -> set[str]:
    """Die Grenz-Commits eines flachen Klons.

    Der Grenzcommit ist dort elternlos; ``git log`` behandelt ihn deshalb so,
    als füge er **jede** Datei des Trees hinzu. Ein Treffer darauf sieht aus
    wie „beide Dateien zuletzt gemeinsam geändert" und beantwortet die Frage
    in Wahrheit gar nicht. In einem vollständigen Klon ist ein elternloser
    Commit dagegen eine echte Wurzel und bleibt aussagekräftig – deshalb
    zählt das Shallow-Flag hier mit.
    """
    if _git(repo, "rev-parse", "--is-shallow-repository") != "true":
        return set()
    return set(_git(repo, "rev-list", "--max-parents=0", "HEAD").split())


def unresolved_history(repo: Path, commitish: str = "HEAD") -> str | None:
    """Grund, warum die Historie die Frage nicht beantworten kann; sonst ``None``.

    Bewusste Entscheidung statt eines stillen Übergehens (#974): Wo die
    Historie keine Aussage trägt, wird mit Begründung übersprungen – aber
    eben nur dort. Ein flacher Klon genügt, solange die letzten Commits
    beider Dateien innerhalb seiner Tiefe liegen.
    """
    commits = {name: _last_commit(repo, name, commitish) for name in (*SOURCES, PDF)}
    missing = sorted(name for name, commit in commits.items() if not commit)
    if missing:
        return "Die Historie erreicht " + ", ".join(missing) + " nicht."

    boundary = _shallow_boundary(repo)
    if boundary & set(commits.values()):
        return (
            "Flacher Klon: Der letzte Commit mindestens einer beteiligten "
            "Datei liegt auf der Grenze der Historie und ist damit nicht "
            "aussagekräftig."
        )
    return None


def test_anleitung_pdf_is_not_behind_its_source() -> None:
    """Das committete PDF muss aus dem aktuellen Markdown stammen."""
    reason = unresolved_history(ROOT)
    if reason is not None:
        pytest.skip(f"{reason} Die PR-CI checkt mit fetch-depth: 0 aus und prüft dort.")

    stale = stale_pdf(ROOT)

    if stale is not None:
        details = "; ".join(
            f"{name} zuletzt geändert in {source}, {PDF} in {pdf}"
            for name, (source, pdf) in sorted(stale.items())
        )
        pytest.fail(
            f"ANLEITUNG.pdf ist nicht nachgezogen: {details}. Neu erzeugen mit "
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
        target = repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
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
    _commit(repo, {SOURCE: "eins", GENERATOR: "css-eins", PDF: "PDF-eins"}, "alles")

    assert stale_pdf(repo) is None


def test_stale_pdf_flags_a_source_change_without_the_pdf(tmp_path: Path) -> None:
    """Genau der Fall aus ``ac64c3b``: Quelle geändert, PDF nicht."""
    repo = _repo(tmp_path)
    _commit(repo, {SOURCE: "eins", GENERATOR: "css-eins", PDF: "PDF-eins"}, "alles")
    source_only = _commit(repo, {SOURCE: "zwei"}, "nur die Quelle")

    stale = stale_pdf(repo)

    assert stale is not None
    assert set(stale) == {SOURCE}
    assert stale[SOURCE][0] == source_only


def test_stale_pdf_accepts_a_later_pdf_commit(tmp_path: Path) -> None:
    """Ein nachgereichtes PDF löst den Befund wieder auf (``91b32b4``)."""
    repo = _repo(tmp_path)
    _commit(repo, {SOURCE: "eins", GENERATOR: "css-eins", PDF: "PDF-eins"}, "alles")
    _commit(repo, {SOURCE: "zwei"}, "nur die Quelle")
    assert stale_pdf(repo) is not None

    _commit(repo, {PDF: "PDF-zwei"}, "PDF nachgezogen")

    assert stale_pdf(repo) is None


def test_shallow_clone_is_reported_as_unresolved_not_as_synchron(tmp_path: Path) -> None:
    """Ein Tiefe-1-Klon darf nicht „synchron" melden, sondern „nicht prüfbar".

    Review-Befund zu PR #979: Im flachen Klon ist der Grenzcommit elternlos,
    ``git log -1 -- <pfad>`` liefert ihn deshalb für **beide** Dateien. Ohne
    die Grenzerkennung fielen sie über ``source == pdf`` in den Zweig
    „synchron" – der Wächter hätte ein nachweislich veraltetes PDF still
    durchgewinkt. Betroffen sind alle Checkouts ohne ``fetch-depth``
    (``coverage.yml``, ``ui-nightly.yml``), nicht die PR-CI.
    """
    full = _repo(tmp_path)
    _commit(full, {SOURCE: "eins", GENERATOR: "css-eins", PDF: "PDF-eins"}, "alles")
    _commit(full, {SOURCE: "zwei"}, "nur die Quelle")

    # Im vollständigen Klon ist der Befund eindeutig.
    assert unresolved_history(full) is None
    assert stale_pdf(full) is not None

    shallow = tmp_path / "flach"
    subprocess.run(
        ["git", "clone", "-q", "--depth", "1", f"file://{full}", str(shallow)],
        check=True,
        capture_output=True,
    )

    # Dort melden beide Dateien denselben Grenzcommit – das ist keine Aussage.
    assert _last_commit(shallow, SOURCE, "HEAD") == _last_commit(shallow, PDF, "HEAD")
    reason = unresolved_history(shallow)
    assert reason is not None and "Flacher Klon" in reason


def test_stale_pdf_flags_a_generator_change_without_the_pdf(tmp_path: Path) -> None:
    """Auch eine reine Layout-Änderung am Generator macht das PDF veraltet.

    Review-Befund zu PR #979: ``build_pdf`` setzt das Markdown mit ``_css()``
    zusammen. Wer dort Schrift oder Abstände ändert, ohne das PDF neu zu
    erzeugen, hinterlässt denselben Zustand, den dieser Wächter verhindern
    soll – nur ohne dass die Quelle angefasst wurde.
    """
    repo = _repo(tmp_path)
    _commit(repo, {SOURCE: "eins", GENERATOR: "css-eins", PDF: "PDF-eins"}, "alles")
    generator_only = _commit(repo, {GENERATOR: "css-zwei"}, "nur das Layout")

    stale = stale_pdf(repo)

    assert stale is not None
    assert set(stale) == {GENERATOR}
    assert stale[GENERATOR][0] == generator_only
