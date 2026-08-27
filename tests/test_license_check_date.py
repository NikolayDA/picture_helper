"""Der Stand-Stempel des Lizenz-Checks darf nicht am Committer-Datum haengen.

``license-check.yml`` regeneriert ``LICENSES.md`` samt der fuenf Uebersetzungen
und vergleicht fail-closed gegen den committeten Stand. Den Datumsstempel im
Report holte der Workflow frueher aus
``git log -1 --format=%cd -- LICENSES.md``. Das ueberlebt einen Squash-Merge
nicht: ``main`` squasht, der Squash-Commit traegt den **Merge**-Zeitpunkt statt
des Edit-Zeitpunkts. Ein Merge nach UTC-Mitternacht machte den Check auf
``main`` damit rot, obwohl sich am Abhaengigkeits-Snapshot nichts geaendert
hatte – und zwar genau im Moment des Kandidatenbaus (Review-Befund zu PR #877).

Seither liest der Workflow den Stempel aus der committeten Datei selbst. Drei
Dinge muessen dafuer zusammenpassen und driften sonst unbemerkt auseinander:
der Verzicht auf die Git-Historie, der Ausdruck im Workflow und die
``Stand:``-Zeile, die ``scripts/generate_license_report.py`` tatsaechlich
schreibt. Dieser Test haelt sie netzfrei zusammen (Muster wie die Qt-apt-Liste,
Befund N6, und die Markerlisten aus #845/#852).
"""
from __future__ import annotations

import importlib.util
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "license-check.yml"
LICENSES = ROOT / "LICENSES.md"

_SPEC = importlib.util.spec_from_file_location(
    "generate_license_report", ROOT / "scripts" / "generate_license_report.py"
)
glr = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(glr)

#: Die ``Stand:``-Zeile der committeten Datei – Referenzwert des Vergleichs.
_ISO_DATE_RE = re.compile(r"(?m)^> Stand: (\d{4}-\d{2}-\d{2}) ")


def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def _gen_date_command() -> str:
    """Die Zuweisung an ``gen_date``, wortgleich aus dem Workflow."""
    lines = [
        line.strip()
        for line in _workflow_text().splitlines()
        if line.strip().startswith("gen_date=") and "date -u" not in line
    ]
    assert len(lines) == 1, (
        f"erwarte genau eine primaere gen_date-Zuweisung, gefunden: {lines}"
    )
    return lines[0]


def test_generated_date_does_not_come_from_git_history() -> None:
    """Regression: ``git log`` liefert nach dem Squash den Merge-Zeitpunkt.

    Kehrt der Workflow dorthin zurueck, ist der Check auf ``main`` wieder von
    der Tageszeit des Merges abhaengig.
    """
    command = _gen_date_command()
    assert "git log" not in command, (
        "gen_date darf nicht aus der Git-Historie kommen: der Squash-Commit "
        f"traegt den Merge-Zeitpunkt, nicht den Edit-Zeitpunkt. Zeile: {command}"
    )
    assert "LICENSES.md" in command, (
        f"gen_date muss aus der committeten LICENSES.md kommen. Zeile: {command}"
    )


def test_workflow_expression_extracts_the_committed_date() -> None:
    """Der Ausdruck aus dem Workflow liefert exakt das Datum der Datei.

    Ausgefuehrt wird die Zeile im Wortlaut – eine rein in Python nachgebaute
    Variante koennte vom Shell-Verhalten abweichen und genau die Drift
    verstecken, die dieser Test verhindern soll.
    """
    expected = _ISO_DATE_RE.search(LICENSES.read_text(encoding="utf-8"))
    assert expected is not None, (
        "LICENSES.md traegt keine '> Stand: JJJJ-MM-TT '-Zeile – dann kann der "
        "Workflow den Stempel nicht lesen und faellt auf 'heute' zurueck."
    )

    result = subprocess.run(
        ["bash", "-e", "-c", f'{_gen_date_command()}\nprintf "%s" "$gen_date"'],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == expected.group(1), (
        f"Workflow-Ausdruck liefert {result.stdout!r}, LICENSES.md nennt "
        f"{expected.group(1)!r}"
    )


def test_generator_writes_the_prefix_the_workflow_matches() -> None:
    """Workflow-Ausdruck und deutsche ``Stand:``-Zeile bleiben synchron.

    Aendert der Generator sein Praefix, greift der Ausdruck ins Leere: Der
    Workflow fiele still auf ``date -u`` zurueck und der Vergleich waere ab der
    naechsten UTC-Mitternacht wieder tageszeitabhaengig – ohne dass irgendetwas
    darauf hinwiese.
    """
    status_line = glr.STRINGS["de"]["full"]["status_line"]
    assert status_line.startswith("> Stand: {generated} "), (
        "Die deutsche Stand-Zeile muss mit '> Stand: {generated} ' beginnen, "
        f"damit der Workflow-Ausdruck sie trifft. Ist: {status_line!r}"
    )
    assert "> Stand: " in _gen_date_command(), (
        "Der Workflow-Ausdruck muss auf dasselbe Praefix passen."
    )


def test_missing_file_falls_back_to_today_even_under_pipefail(tmp_path: Path) -> None:
    """Der ``date -u``-Rueckfall bleibt auch unter ``pipefail`` erreichbar.

    Der Step deklariert kein ``shell:``; GitHub Actions nutzt dann
    ``bash -e {0}`` **ohne** ``pipefail``, und der Status der Pipeline ist der
    von ``head`` (0) – der Rueckfall greift. Ein spaeter ergaenztes
    ``shell: bash`` am Step oder ein ``defaults: run: shell: bash`` setzt
    jedoch ``-eo pipefail``: ``sed`` liefert bei fehlender Datei Exit 2, und
    ohne ``|| true`` risse das die Zuweisung samt Step ab, statt
    zurueckzufallen (Review-Befund auf PR #879). Geprueft wird deshalb im
    schaerferen Modus – nur so haengt der Rueckfall nicht an einer nirgends
    festgehaltenen Voraussetzung.
    """
    assert 'gen_date="$(date -u +%Y-%m-%d)"' in _workflow_text(), (
        "Der Rueckfall auf 'heute' muss erhalten bleiben – sonst laeuft der "
        "Generator ohne --generated-date auf einem frischen Branch ohne "
        "LICENSES.md."
    )

    result = subprocess.run(
        ["bash", "-eo", "pipefail", "-c",
         f'{_gen_date_command()}\nprintf "%s" "$gen_date"'],
        cwd=tmp_path,  # bewusst ohne LICENSES.md
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "Ohne LICENSES.md bricht der Ausdruck unter pipefail ab, statt leer zu "
        f"liefern – der 'heute'-Rueckfall waere unerreichbar. stderr: "
        f"{result.stderr!r}"
    )
    assert result.stdout == "", (
        f"erwarte leeren gen_date ohne LICENSES.md, bekommen: {result.stdout!r}"
    )


def test_dateless_file_yields_an_empty_gen_date(tmp_path: Path) -> None:
    """Eine LICENSES.md ohne brauchbare Datumszeile liefert **leer**.

    Der zweite Rueckfall-Ausloeser: Aendert der Generator sein Praefix, trifft
    der Ausdruck die Zeile nicht mehr. Er muss dann leer liefern, damit die
    ``[ -z ]``-Verzweigung greift. Eine Umformulierung, die stattdessen die
    ganze Zeile ausgibt, wuerde ``--generated-date`` mit Muell fuettern statt
    mit 'heute' – ohne dass ein Test anschlaegt (Review-Befund auf PR #879).
    """
    (tmp_path / "LICENSES.md").write_text(
        "**Deutsch**\n\n# Lizenz- & Rechtsuebersicht – bgremover 9.9.9\n\n"
        "> Stand: nicht-datierbar · Eigenlizenz des Projekts: `GPL-3.0-or-later`.\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["bash", "-eo", "pipefail", "-c",
         f'{_gen_date_command()}\nprintf "%s" "$gen_date"'],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "", (
        "Ohne verwertbare Datumszeile muss gen_date leer bleiben, damit der "
        f"'heute'-Rueckfall greift; bekommen: {result.stdout!r}"
    )


def test_checkout_needs_no_full_history() -> None:
    """``fetch-depth: 0`` existierte allein fuer die entfernte ``git log``-Zeile.

    Die Drift-Pruefung nutzt nur ``git diff`` gegen den Arbeitsbaum. Kehrt der
    volle Klon zurueck, ist das ein Hinweis darauf, dass jemand wieder auf die
    Historie zugreift.

    Geprueft werden nur echte Konfigurationszeilen: Der Begriff kommt auch im
    erklaerenden Kommentar vor, und ein reiner Texttreffer haette den Test an
    seiner eigenen Begruendung scheitern lassen.
    """
    settings = [
        line.strip()
        for line in _workflow_text().splitlines()
        if line.strip().startswith("fetch-depth:")
    ]
    assert not settings, (
        "license-check.yml braucht keine Git-Historie mehr; ein wieder "
        f"eingefuegtes fetch-depth deutet auf einen Rueckfall hin: {settings}"
    )
