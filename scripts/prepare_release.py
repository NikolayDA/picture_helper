#!/usr/bin/env python3
"""Erzeugt den Rohstand von Runbook-Schritt 1/2 (#923).

Die Inhalte dieses Schritts sind hochgradig schematisch – Paketversion,
sechs datierte CHANGELOG-Abschnitte, AppStream-Eintrag, Scope-Freeze-Dokument
und das Release-Issue mit seinen Bindungswerten. Die **Pruefung** existiert
laengst fail-closed (``verify_release_freeze.py``, i18n-/CHANGELOG-/Markdown-
Waechter); Fleissarbeit mit Vertipp-Risiko war nur die **Erstellung**, und
zwar in sechs Sprachfassungen.

Dieses Skript erzeugt genau diesen Rohstand, und zwar deterministisch: Gleiche
Version, gleiches Datum und gleicher Repository-Stand ergeben Byte-fuer-Byte
dasselbe Ergebnis. Was es NICHT tut, ist ebenso wichtig:

* Es waehlt keine Version und faellt keine Scope-Entscheidung.
* Es schreibt keine Release-Notes-Aussagen. Auswirkung, Betroffene,
  Upgrade-Relevanz und Einschraenkungen bleiben redaktionelle Handarbeit
  (``NOTES-01``) und stehen im Geruest als ``TODO(release)``.
* Es legt nichts auf GitHub an. Das Release-Issue entsteht als Datei bzw. auf
  der Standardausgabe; ``--create-issue`` ist ein ausdruecklicher Opt-in.
  Scheitert dieser Aufruf, bleibt der bereits geschriebene Rohstand stehen und
  der Issue-Text liegt als Datei vor – auch ohne ``--issue-output``. Die
  Fehlermeldung nennt dann den fertigen Wiederanlaufbefehl; er legt genau
  dieses Issue an und schreibt keine Release-Datei erneut.

Die Platzhalter sind kein Schoenheitsfehler, sondern der Vertrag: Ein Geruest
mit offenen ``TODO(release)``-Luecken macht den Vorbereitungs-PR **nicht**
gruen. ``verify_release_freeze.py`` weist sie als blockierenden Befund aus,
bis sie redaktionell gefuellt sind.

Beispiel:

    python scripts/prepare_release.py 2.10.0 --issue-output /tmp/release-issue.md
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import os
import re
import shlex
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone  # noqa: UP017 - Projekt unterstuetzt Python 3.10
from pathlib import Path
from typing import Final

try:  # Dateiaufruf: ``python scripts/prepare_release.py``
    import release_contract as rc
    import release_path_policy as rpp
    import verify_release_freeze as vrf
except ModuleNotFoundError:  # Import als ``scripts.prepare_release`` in Tests
    from scripts import release_contract as rc
    from scripts import release_path_policy as rpp
    from scripts import verify_release_freeze as vrf

_REPO_ROOT: Final = Path(__file__).resolve().parent.parent

#: Redaktionelle Luecke. Bewusst ein Token, das in normalem Fliesstext nicht
#: vorkommt: Das Freeze-Gate sucht genau danach.
PLACEHOLDER: Final = vrf.EDITORIAL_PLACEHOLDER

#: Sprachen der uebersetzten Fassungen (Deutsch ist das Original).
LANGUAGES: Final = vrf.LANGUAGES

APPSTREAM_PATH: Final = "packaging/linux/de.bgremover.app.metainfo.xml"
PYPROJECT_PATH: Final = "pyproject.toml"

#: Bewusst ASCII-Ziffern: ``\d`` akzeptiert auch Unicode-Ziffern, und ``２.１０.０``
#: liefe bis in Dateinamen, Tags und Metadaten durch – der Freigabevertrag
#: (``release_contract``) nutzt aus demselben Grund ``[0-9]``.
_SEMVER_RE: Final = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


def _semver_key(version: str) -> tuple[int, ...]:
    """X.Y.Z als Zahlentripel – Voraussetzung: ``_SEMVER_RE`` hat gepasst.

    Numerisch statt lexikografisch: Als Text verglichen läge ``2.10.0`` unter
    ``2.9.0`` und der Downgrade-Schutz (#943 Befund 3) wiese ausgerechnet den
    regulären Minor-Sprung ab.
    """
    return tuple(int(part) for part in version.split("."))

#: Abschnittsueberschriften je Sprache, in der Reihenfolge des Hausstils.
#: ``tests/test_prepare_release.py`` haelt sie gegen die tatsaechlich in den
#: CHANGELOG-Dateien verwendeten Ueberschriften – erfundene Uebersetzungen
#: fallen damit auf, bevor sie in sechs Dateien landen.
SECTION_HEADINGS: Final[dict[str, tuple[str, str, str, str]]] = {
    "de": ("Hinzugefügt", "Geändert", "Behoben", "Hinweise zu diesem Release"),
    "en": ("Added", "Changed", "Fixed", "Notes for this release"),
    "es": ("Añadido", "Cambiado", "Corregido", "Notas sobre esta versión"),
    "fr": ("Ajouté", "Modifié", "Corrigé", "Notes sur cette version"),
    "uk": ("Додано", "Змінено", "Виправлено", "Примітки до цього релізу"),
    "zh": ("新增", "变更", "修复", "本版本说明"),
}


class PrepareError(RuntimeError):
    """Abbruchgrund, der dem Menschen gehoert (nie stillschweigend geheilt)."""


@dataclass(frozen=True)
class ReleaseInputs:
    """Alles, was das Geruest bestimmt – bewusst vollstaendig explizit."""

    version: str
    release_date: str
    base_tag: str
    base_sha: str


@dataclass(frozen=True)
class PlannedFile:
    """Eine zu schreibende Datei mit ihrem vollstaendigen neuen Inhalt."""

    path: str
    content: str


def changelog_path(language: str) -> str:
    """Pfad der CHANGELOG-Fassung einer Sprache (``de`` = Original im Root)."""
    return "CHANGELOG.md" if language == "de" else f"docs/i18n/{language}/CHANGELOG.md"


def freeze_doc_path(version: str) -> str:
    """Pfad des Scope-Freeze-Dokuments dieser Version."""
    return vrf.FREEZE_DOC_TEMPLATE.format(version=version)


# ── Git ────────────────────────────────────────────────────────────────


def _git(repo: Path, *args: str) -> str:
    """``git`` im *repo* ausfuehren; jeder Fehler ist ein Abbruchgrund."""
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise PrepareError(f"git {' '.join(args)} fehlgeschlagen: {result.stderr.strip()}")
    return result.stdout.strip()


def resolve_tag(repo: Path, tag: str) -> str:
    """Voller Commit-SHA eines Tags (annotiert oder leichtgewichtig)."""
    try:
        return _git(repo, "rev-list", "-n", "1", tag)
    except PrepareError as exc:
        raise PrepareError(
            f"Basis-Tag {tag} ist lokal nicht bekannt – 'git fetch --tags' ausfuehren "
            f"oder --base-tag setzen. ({exc})"
        ) from exc


# ── Bausteine ──────────────────────────────────────────────────────────


def bump_pyproject(text: str, version: str) -> str:
    """Setzt ``project.version``; genau ein Treffer, sonst Abbruch."""
    matches = list(re.finditer(r'(?m)^(version\s*=\s*")([^"]+)(")', text))
    if len(matches) != 1:
        raise PrepareError(
            f"pyproject.toml: erwarte genau eine version-Zeile, gefunden {len(matches)}"
        )
    match = matches[0]
    return text[: match.start()] + f"{match.group(1)}{version}{match.group(3)}" + text[match.end() :]


def changelog_section(language: str, version: str, release_date: str) -> str:
    """Der Geruest-Abschnitt einer Sprache – ohne fuehrende/abschliessende Leerzeile.

    Enthaelt bewusst alle vier Pflichtmarker des Release-Bodys: Sie sind die
    Gliederung, die der Mensch fuellt. Die Werte selbst bleiben offen und
    blockieren bis dahin das Freeze-Gate.
    """
    added, changed, fixed, notes = SECTION_HEADINGS[language]
    markers = vrf.RELEASE_BODY_MARKERS[language]
    lines = [f"## [{version}] – {release_date}", ""]
    for heading in (added, changed, fixed):
        lines += [f"### {heading}", "", f"- {PLACEHOLDER}", ""]
    lines += [f"### {notes}", ""]
    lines += [f"- {marker} {PLACEHOLDER}" for marker in markers]
    return "\n".join(lines)


def insert_changelog_section(text: str, language: str, version: str, release_date: str) -> str:
    """Setzt den Geruest-Abschnitt direkt unter ``## [Unreleased]``.

    Idempotent: Ein bereits vorhandener Abschnitt derselben Version wird
    ersetzt – aber **nur**, wenn er noch Platzhalter traegt. Ein redaktionell
    bearbeiteter Abschnitt bleibt unangetastet und fuehrt zum Abbruch; ein
    Vorbereitungsskript darf Handarbeit nicht ueberschreiben.
    """
    section = changelog_section(language, version, release_date)
    existing = re.search(
        rf"(?ms)^## \[{re.escape(version)}\](?P<head>[^\n]*)\n.*?(?=^## \[|\Z)",
        text,
    )
    if existing is not None:
        # Ueberschrieben wird nur, was byte-gleich ein frueher erzeugtes Geruest
        # ist – das Datum als einzige zulaessige Abweichung, damit ein Lauf mit
        # anderem ``--date`` funktioniert. "Enthaelt noch einen Platzhalter"
        # genuegt NICHT: Wer die Eintraege schon ausformuliert und nur die
        # Notizen offen gelassen hat, verlaere sie sonst kommentarlos.
        existing_date = re.search(r"(\d{4}-\d{2}-\d{2})", existing.group("head"))
        expected = (
            changelog_section(language, version, existing_date.group(1))
            if existing_date is not None
            else None
        )
        if expected is None or existing.group(0).strip() != expected.strip():
            raise PrepareError(
                f"{changelog_path(language)}: Abschnitt [{version}] weicht vom erzeugten "
                "Gerüst ab – er wird nicht überschrieben."
            )
        return text[: existing.start()] + section + "\n\n" + text[existing.end() :]

    # ``[ \t]*`` statt ``\s*``: ``\s`` schluckt den Zeilenumbruch und erzeugte
    # eine zusaetzliche Leerzeile vor dem eingefuegten Abschnitt.
    unreleased = re.search(r"(?m)^## \[Unreleased\][ \t]*$", text)
    if unreleased is None:
        raise PrepareError(f"{changelog_path(language)}: '## [Unreleased]' nicht gefunden")
    cut = unreleased.end()
    head, tail = text[:cut], text[cut:].lstrip("\n")
    return f"{head}\n\n{section}\n\n{tail}"


_UNRELEASED_LINK_RE: Final = re.compile(
    r"(?m)^\[Unreleased\]: (?P<base>\S+?/compare/)v(?P<from>\d+\.\d+\.\d+)\.\.\.HEAD$"
)


def update_changelog_links(text: str, version: str) -> str:
    """Zieht die Fussnoten-Links nach: ``[Unreleased]`` und der neue Vergleich.

    Genau diese mechanische Luecke – fehlender Fussnoten-Eintrag fuer die
    neueste Ueberschrift, veraltetes ``[Unreleased]``-Vergleichsziel – rutschte
    an zwei aufeinanderfolgenden Release-Schnitten durch (#773/#827) und hat
    seitdem einen eigenen Waechter. Ein Geruest ohne diese Zeilen macht
    ``make check`` rot, und zwar an einer Stelle, die kein redaktionelles
    Fuellen behebt.

    Idempotent: Zeigt ``[Unreleased]`` bereits auf *version*, bleibt der Text
    unveraendert.
    """
    match = _UNRELEASED_LINK_RE.search(text)
    if match is None:
        raise PrepareError("CHANGELOG ohne '[Unreleased]: …/compare/vX.Y.Z...HEAD'-Fussnote")
    previous = match.group("from")
    if previous == version:
        return text
    base = match.group("base")
    replacement = (
        f"[Unreleased]: {base}v{version}...HEAD\n"
        f"[{version}]: {base}v{previous}...v{version}"
    )
    return text[: match.start()] + replacement + text[match.end() :]


def insert_appstream_release(xml_text: str, version: str, release_date: str) -> str:
    """Ergaenzt den AppStream-``<release>``-Eintrag als juengsten der Liste.

    Textuell statt ueber ElementTree: Ein Reserialisieren wuerde Kommentare und
    Formatierung der gesamten Datei umschreiben und den Diff unlesbar machen.
    """
    opening = re.search(r"(?m)^(?P<indent>[ \t]*)<releases>[ \t]*$", xml_text)
    if opening is None:
        raise PrepareError(f"{APPSTREAM_PATH}: <releases>-Block nicht gefunden")
    # Einrueckung aus der Datei ableiten statt fest zu verdrahten: Sie wurde
    # bisher erfasst und wieder verworfen, eine Formatänderung wäre unbemerkt
    # geblieben (Review-Hinweis auf PR #932).
    indent = opening.group("indent") + "  "
    entry = f'{indent}<release version="{version}" date="{release_date}"/>'
    # Einen vorhandenen Eintrag entfernen statt in place zu aktualisieren: Das
    # Gate liest den **ersten** <release> und vergleicht ihn mit der
    # Kandidatenversion. Ein an alter Stelle aktualisierter Eintrag liesse die
    # Datei formal richtig aussehen und das Gate trotzdem scheitern.
    existing = re.search(
        rf'(?m)^[ \t]*<release version="{re.escape(version)}" date="[^"]*"/>[ \t]*\n', xml_text
    )
    if existing is not None:
        xml_text = xml_text[: existing.start()] + xml_text[existing.end() :]
        opening = re.search(r"(?m)^[ \t]*<releases>[ \t]*$", xml_text)
        if opening is None:  # pragma: no cover - oben bereits geprueft
            raise PrepareError(f"{APPSTREAM_PATH}: <releases>-Block nicht gefunden")
    cut = opening.end()
    return xml_text[:cut] + "\n" + entry + xml_text[cut:]


POLICY_PATH: Final = rpp.POLICY_PATH

#: Die Pfadpolicy haelt jeden Eintrag auf genau einer Zeile. Der Rollover ist
#: deshalb eine Zeilenoperation und veraendert die Formatierung der uebrigen
#: 500+ Zeilen nicht – ein ``json.dumps``-Roundtrip wuerde die kompakten
#: ``evidence``-Listen aufblaehen und einen 650-Zeilen-Diff erzeugen.
_POLICY_VERSION_RE: Final = re.compile(r'(?m)^(\s*"policy_version":\s*)(\d+)(\s*,)$')
_CURRENT_FREEZE_RE: Final = re.compile(r'(?m)^(\s*)\{"id": "current-freeze",[^\n]*\}(,?)$')
#: Letzter Eintrag der Drift-Wächter-Liste ``release_documents``. Der Wächter
#: ``tests/test_release_freeze.py::test_release_document_drift_guard_is_explicit_and_current``
#: leitet seine Sollmenge aus der *aktuellen* ``pyproject``-Version ab – nach dem
#: Versionssprung gehört das neue Freeze-Dokument also dazu, sonst ist ``make
#: check`` im erzeugten Stand rot. Rein schematisch, deshalb Teil des Rollovers.
_LAST_RELEASE_DOCUMENT_RE: Final = re.compile(
    r'(?ms)("release_documents":\s*\[.*?)^(\s*)"([^"]+)"\n(\s*)\]'
)


def roll_over_freeze_policy(
    policy_text: str, *, version: str, predecessor_version: str
) -> tuple[str, int]:
    """Zeigt ``current-freeze`` auf das neue Dokument und hebt die Policy-Version.

    Dieser Rollover ist kein Sonderfall, sondern faellt bei **jedem** Release
    an: Das neue Freeze-Dokument ist ein unbekannter Pfad und blockiert das
    Gate fail-closed, waehrend der Pfad des bisherigen aktiven Dokuments ohne
    Regel zurueckbliebe. Beides ist vollstaendig aus den Versionsnummern
    bestimmt – genau die schematische Arbeit, die dieses Skript abnimmt. Die
    Begruendungstexte folgen wortgleich dem bisherigen Muster
    (``historical-freeze-2.8.0`` als Vorlage).

    Liefert den neuen Dateiinhalt und die angehobene Policy-Version.
    """
    version_match = _POLICY_VERSION_RE.search(policy_text)
    if version_match is None:
        raise PrepareError(f"{POLICY_PATH}: policy_version nicht gefunden")
    current_version = int(version_match.group(2))

    current = _CURRENT_FREEZE_RE.search(policy_text)
    if current is None:
        raise PrepareError(f"{POLICY_PATH}: Eintrag 'current-freeze' nicht gefunden")
    indent, comma = current.group(1), current.group(2)
    new_path = freeze_doc_path(version)
    old_path = freeze_doc_path(predecessor_version)
    if f'"path": "{new_path}"' in current.group(0):
        # Bereits umgehaengt: ein zweiter Lauf darf die Policy-Version NICHT
        # erneut anheben. Ohne diesen Zweig waere das Skript nicht idempotent
        # und jede Wiederholung erzeugte eine neue Vertragsversion.
        return policy_text, current_version
    new_version = current_version + 1
    if f'"path": "{old_path}"' not in current.group(0):
        raise PrepareError(
            f"{POLICY_PATH}: 'current-freeze' zeigt nicht auf {old_path} – "
            "der Rollover würde einen anderen Stand überschreiben."
        )
    replacement = (
        f'{indent}{{"id": "current-freeze", "kind": "exact", "path": "{new_path}", '
        f'"sample_path": "{new_path}", "reason": "Das aktive Freeze-Dokument '
        f'enthält Basis, Scope und Policy-Version."}},\n'
        f'{indent}{{"id": "historical-freeze-{predecessor_version}", "kind": "exact", '
        f'"path": "{old_path}", "sample_path": "{old_path}", "reason": '
        f'"Vormals aktives Freeze-Dokument fuer den {predecessor_version}-Kandidaten. '
        f"'current-freeze' zeigt seit dem {version}-Rollover nicht mehr hierher, der Pfad "
        f'bleibt aber ein candidate-relevanter Release-Governance-Artefakt."}}{comma}'
    )
    text = policy_text[: current.start()] + replacement + policy_text[current.end() :]

    guard = _LAST_RELEASE_DOCUMENT_RE.search(text)
    if guard is None:
        raise PrepareError(f"{POLICY_PATH}: drift_guards.release_documents nicht gefunden")
    if f'"{new_path}"' not in guard.group(0):
        text = (
            text[: guard.start()]
            + f'{guard.group(1)}{guard.group(2)}"{guard.group(3)}",\n'
            + f'{guard.group(2)}"{new_path}"\n{guard.group(4)}]'
            + text[guard.end() :]
        )
    return _POLICY_VERSION_RE.sub(rf"\g<1>{new_version}\g<3>", text, count=1), new_version


def scope_name(version: str, predecessor_version: str) -> str:
    """Release-Scope im Hausstil: ``minor-release-`` bzw. ``patch-release-``.

    Ableitbar aus dem Versionssprung, deshalb kein Freitext: Die bisherigen
    Freeze-Dokumente fuehren ``patch-release-2.7.2``/``minor-release-2.9.0``.
    Ein erfundenes Schema haette den Hausstil nach vier Releases gebrochen.
    """
    new_parts = tuple(int(part) for part in version.split("."))
    old_parts = tuple(int(part) for part in predecessor_version.split("."))
    kind = "patch" if new_parts[:2] == old_parts[:2] else "minor"
    return f"{kind}-release-{version}"


def freeze_document(
    inputs: ReleaseInputs, *, predecessor_version: str, policy_version: int
) -> str:
    """Geruest des Scope-Freeze-Dokuments.

    Die vier maschinenlesbaren Zeilen sind vollstaendig: Sie sind vor dem Merge
    bekannt und dieses Skript kennt sie. Der **Scope** ist die eine Aussage,
    die ein Mensch treffen muss – er bleibt als ``TODO(release)`` offen und
    blockiert bis dahin das Gate.
    """
    predecessor_doc = f"RELEASE-{predecessor_version}-scope-freeze.md"
    return f"""# Release {inputs.version} – stabiler Scope-Freeze

Nachfolger von [`{predecessor_doc}`]({predecessor_doc}).
Dieses Dokument enthält ausschließlich Angaben, die **vor** seinem Merge
bekannt sind. Kandidaten-SHA, Commitliste, Pfadklassifikationen und Zähler
werden nicht nachgetragen, sondern beim Gate aus Git abgeleitet und als
maschinenlesbare Provenienz außerhalb der Git-Historie gespeichert (#742).

Erzeugt mit `scripts/prepare_release.py` (#923). Die unten markierten Stellen
sind redaktionelle Handarbeit; das Freeze-Gate weist sie als blockierenden
Befund aus, bis sie gefüllt sind. Der Platzhalter darf deshalb **nirgends
sonst** im Dokument stehen – auch nicht erklärend: Der Wächter durchsucht die
ganze Datei, ein erklärender Satz mit dem Token bliebe für immer rot.

## Stabile, maschinenlesbare Angaben

- **Basis-Tag:** `{inputs.base_tag}` (= `{inputs.base_sha}`)
- **Kandidatenversion:** `{inputs.version}`
- **Release-Scope:** `{scope_name(inputs.version, predecessor_version)}`
- **Pfadpolicy:** `release/path-policy.json` (Version `{policy_version}`)

Der volle Basis-SHA ist unveränderlich. Der Tagname allein genügt nicht: Das
Gate weist ein verschobenes Tag zurück. Die Policy-Version bindet die Semantik,
mit der alle Pfade im Fenster `Basis..Laufkopf` klassifiziert werden.

## Scope

{PLACEHOLDER}: Fachlichen Scope beschreiben – welche Issues sind
anwender:innensichtbar, was ist reine Test-/CI-/Doku-Governance ohne
Auswirkung auf das Programmverhalten, und welche Änderungen wirken
ausdrücklich **nicht** im ausgelieferten Artefakt. Die übrigen Commits seit
`{inputs.base_tag}` sind Teil des First-Parent-Fensters und werden vom Gate
einzeln klassifiziert; der fachliche Scope entsteht hier.

Änderungen außerhalb dieses Scope benötigen vor dem Build eine bewusste
Scope-Entscheidung. Unbekannte Pfade blockieren das Gate fail-closed, auch wenn
sie vorsichtshalber als kandidatenrelevant gelten.

## Kandidat und Commit-Ledger

Der Kandidaten-SHA ist der von GitHub Actions geprüfte Laufkopf
(`GITHUB_SHA`). `scripts/verify_release_freeze.py` rekonstruiert aus der
First-Parent-Historie seit dem Basis-SHA alle Commits, ihre geänderten Pfade,
Regel und Klasse jedes Pfades, die primäre Klasse jedes Commits und den
jüngsten kandidatenrelevanten Inhaltscommit. Ein exakter Post-Merge-SHA, eine
Commit-Anzahl oder eine manuelle SHA-Tabelle stehen bewusst **nicht** in
diesem Dokument.

Lokale Prüfung:

```bash
make release-freeze-check
python scripts/verify_release_freeze.py \\
  --output-provenance /tmp/release-freeze-provenance.json
python scripts/verify_release_freeze.py \\
  --verify-provenance /tmp/release-freeze-provenance.json
```

## Pfadklassen

Die einzige Quelle ist [`release/path-policy.json`](../../release/path-policy.json):

- `release-neutral` ist eine enge positive Allowlist mit Begründung und
  Build-Input-Nachweis je Eintrag.
- `candidate-relevant` umfasst bekannte Produkt-, Metadaten-, Build-, Test-,
  Workflow-, Release- und Evidenzpfade.
- unbekannte Pfade sind kandidatenrelevant **und blockierend**, bis die Policy
  bewusst ergänzt und versioniert wurde.

{PLACEHOLDER}: Falls dieser Kandidat die Policy verändert hat, den
Versionssprung hier begründen (Regel, Anlass, betroffene Pfade). Ohne
Policy-Änderung diesen Absatz durch einen Satz ersetzen, der das festhält.

## Verbindliche Konsistenzprüfungen

Das Gate prüft am Laufkopf Paketversion, datierte CHANGELOG-Abschnitte und
Release-Body-Pflichtangaben in sechs Sprachen, AppStream-Version und -Datum,
sechs Lizenz-Snapshots, unveränderten Basis-Tag/SHA, Policy-Version und
-Digest, die vollständige Pfadklassifikation aller First-Parent-Commits sowie
die Bindung des Kandidaten an `GITHUB_SHA` und die Actions-Run-IDs.

Die Entscheidung und verworfene Alternativen stehen in
[`ADR-2026-release-freeze-provenienz.md`](ADR-2026-release-freeze-provenienz.md).

## Noch offene Release-Schuld

{PLACEHOLDER}: Offene Punkte aus dem vorherigen Freeze prüfen und entweder als
erledigt vermerken oder als weiterhin offen übernehmen.
"""


#: Die neun Runbook-Schritte. Ein Test haelt sie gegen die Ueberschriften in
#: ``docs/RELEASE_PROCESS.md`` – die Schritt-Tabelle des Issues ist eine
#: handgepflegte Kopie des Runbooks und braucht denselben Waechter.
RUNBOOK_STEPS: Final = (
    "Release vorbereiten",
    "Kandidatenstand einfrieren",
    "Unveränderlichen Kandidaten bauen",
    "Kandidatenartefakte und Sicherheitsbefunde vorprüfen",
    "Abnahme auf echter Hardware durchführen",
    "Freigabemanifest und Release-Instanz abnehmen",
    "Tag auf exakt den abgenommenen Commit setzen",
    "Abgenommene Bytes veröffentlichen",
    "Öffentliche und nachgelagerte Prüfung abschließen",
)


def paused_x86_64_criteria(checklist: dict[str, object]) -> tuple[str, ...]:
    """IDs der über ``ABNAHME_X86_64_ENABLED`` pausierten Hardware-Kriterien.

    Abgeleitet aus dem Checklistenvertrag (``verification`` = ``platform:
    linux-x86_64``) statt hart notiert: Kommt ein x86_64-Kriterium hinzu oder
    faellt eines weg, wandert es ohne Codeaenderung in das Issue.
    """
    criteria = checklist.get("criteria")
    if not isinstance(criteria, list):
        raise PrepareError("Checklistenvertrag ohne Kriterienliste")
    found: list[str] = []
    for item in criteria:
        if isinstance(item, dict) and item.get("verification") == "platform:linux-x86_64":
            found.append(str(item["id"]))
    return tuple(sorted(found))


def release_issue(
    inputs: ReleaseInputs,
    *,
    checklist_version: str,
    checklist_sha256: str,
    paused_criteria: tuple[str, ...],
    policy_version: int,
) -> str:
    """Rendert das Release-Issue mit allen vor dem Kandidatenbau bekannten Werten.

    Offen bleibt genau das, was erst spaeter entsteht: Kandidaten-SHA,
    Build-Run, Abnahme und die Go-/No-Go-Entscheidung.
    """
    steps = "\n".join(
        f"| {number} {title} | offen |" for number, title in enumerate(RUNBOOK_STEPS, start=1)
    )
    paused = "\n".join(
        f"- [ ] `{criterion}` (SHOULD): bleibt `PENDING`, solange der x86_64-Pfad über "
        "`ABNAHME_X86_64_ENABLED` pausiert ist. Erscheint in der Abschlussmatrix "
        "ausdrücklich als „pausiert“ und wird **nicht** als bestanden umgedeutet."
        for criterion in paused_criteria
    )
    return f"""## Ziel

Dieses Issue ist das verbindliche Entscheidungs- und Evidenzprotokoll für die
Abnahme und Veröffentlichung von BgRemover {inputs.version} nach
[`docs/RELEASE_PROCESS.md`](https://github.com/NikolayDA/picture_helper/blob/main/docs/RELEASE_PROCESS.md)
und der versionierten Checkliste `{checklist_version}`. Seine Nummer ist der
`RELEASE_ISSUE` des Runbooks und der `target_issue`-Eingabewert von
`release-abnahme.yml`.

Erzeugt mit `scripts/prepare_release.py` (#923). Alle Bindungswerte unten sind
vorbefüllt; die mit `{PLACEHOLDER}` markierten Stellen entstehen erst im
Ablauf und bleiben Handarbeit.

## Aktueller Stand

**Offen — Runbook-Schritt 1/2 vorbereitet.**

| Schritt | Stand |
|---|---|
{steps}

## Gebundener Release-Stand

- Version: `{inputs.version}`
- Geplanter Tag: `v{inputs.version}`
- Release-Ref: `release/v{inputs.version}` (entsteht in Schritt 2)
- Kandidaten-Commit: {PLACEHOLDER} (entsteht in Schritt 2)
- Kandidaten-Build: {PLACEHOLDER} (entsteht in Schritt 3)
- Hardware-Abnahme: _steht aus_
- Freigabeartefakt: _entsteht in Schritt 6_
- Vorgänger-Release: `{inputs.base_tag}` (= `{inputs.base_sha}`, zugleich Freeze-Basis)
- Scope-Freeze: [`{freeze_doc_path(inputs.version)}`](https://github.com/NikolayDA/picture_helper/blob/main/{freeze_doc_path(inputs.version)}), Pfadpolicy `{policy_version}`
- Checklistenvertrag: `{checklist_version}`, Schema `{rc.CHECKLIST_SCHEMA}`, Datei-SHA-256 `{checklist_sha256}`
- Produktumfang: fünf Artefakte mit gebündeltem KI-Backend (`with_ai=true`); Windows ist nicht Teil dieses Releasevertrags
- Aktive Hardware: macOS arm64 und Linux arm64
- Bewusst pausiert: Linux-x86_64-Hardwarekriterien bleiben `PENDING` (`ABNAHME_X86_64_ENABLED`)

### Fachlicher Scope

{PLACEHOLDER}: Anwender:innensichtbare Änderungen benennen und von reiner
Test-/CI-/Doku-Governance abgrenzen (dieselbe Aussage wie im Scope-Freeze).

## Sichtbar offene und bewusst pausierte Punkte

{paused}
- [ ] `UPDATE-LINUX-ARM-01` und `UPDATE-MACOS-ARM-01` (POST_RELEASE): werden nach der Veröffentlichung mit einem echten `{inputs.base_tag}`-Vorgängerartefakt nachgewiesen (Runbook-Schritt 9, `predecessor_tag={inputs.base_tag}`).

## Voraussetzungen für Schritt 5

- [ ] `macos-arm64` und `linux-arm64` sind online und haben eine grafische Sitzung.
- [ ] Der Release-Ref `release/v{inputs.version}` zeigt unverändert auf den Kandidaten-Commit; `candidate-source` vergleicht den Workflow-SHA damit und bricht bei Abweichung ab.

## Go/No-Go

_Offen._ Die Entscheidung wird nach Schritt 6 hier protokolliert. Ein
Malware-Fund oder ein offenes MUST ist ein hartes NO-GO.

## Wiederanlauf

- Bei Code-, Dokument- oder Policyänderungen beginnt die Abnahme wieder bei Schritt 1 mit einem neuen Kandidaten.
- Bei reinem Runner- oder Infrastrukturfehler darf derselbe unveränderte Kandidat mit einer neuen Run-ID wiederholt werden.
- Fehlende aktive Hardware oder ein fachlicher Fehler bleibt blockierend; ein MUST-Kriterium wird nicht umgangen.
- Frühere Kandidaten- und Abnahmeläufe bleiben historische Evidenz und werden nicht weiterverwendet.
"""


# ── Planung und Anwendung ──────────────────────────────────────────────


def _read(repo: Path, relative: str) -> str:
    path = repo / relative
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PrepareError(f"{relative} kann nicht gelesen werden: {exc}") from exc


def unknown_paths_since(repo: Path, base_sha: str, head: str = "HEAD") -> tuple[str, ...]:
    """Pfade im Fenster ``base..head`` ohne explizite Klassifikation.

    Sie blockieren das Gate fail-closed. Der Hinweis gehoert in die
    Vorbereitung, nicht in den Kandidatenbau: Dort kostet er einen ganzen Lauf.
    """
    # Die Policy des *gewaehlten* Repositorys, nicht die des Checkouts, in dem
    # dieses Skript liegt: Sonst klassifizierte der Hinweis fremde Historie
    # gegen die eigene Policy und verschwiege oder erfaende unbekannte Pfade.
    policy = rpp.load_policy(repo / POLICY_PATH)
    unknown: set[str] = set()
    for sha in vrf.commits_between(repo, base_sha, vrf.rev_parse(repo, head)):
        for path in vrf.changed_paths(repo, sha):
            if not rpp.classify_path(path, policy).explicit:
                unknown.add(path)
    return tuple(sorted(unknown))


@dataclass(frozen=True)
class PlannedRelease:
    """Der vollstaendige Rohstand plus die dabei entstandene Policy-Version."""

    files: list[PlannedFile]
    policy_version: int


def plan(repo: Path, inputs: ReleaseInputs, *, predecessor_version: str) -> PlannedRelease:
    """Alle zu schreibenden Dateien mit ihrem vollstaendigen Inhalt.

    Getrennt von ``apply``, damit ein Lauf ohne Schreibzugriff denselben Code
    durchlaeuft: Determinismus und Idempotenz sind so pruefbar, ohne dass ein
    Test ein Repository veraendern muss.
    """
    planned: list[PlannedFile] = [
        PlannedFile(PYPROJECT_PATH, bump_pyproject(_read(repo, PYPROJECT_PATH), inputs.version))
    ]
    for language in ("de", *LANGUAGES):
        relative = changelog_path(language)
        planned.append(
            PlannedFile(
                relative,
                update_changelog_links(
                    insert_changelog_section(
                        _read(repo, relative), language, inputs.version, inputs.release_date
                    ),
                    inputs.version,
                ),
            )
        )
    planned.append(
        PlannedFile(
            APPSTREAM_PATH,
            insert_appstream_release(
                _read(repo, APPSTREAM_PATH), inputs.version, inputs.release_date
            ),
        )
    )
    # Der Rollover der Pfadpolicy gehoert in denselben Stand: Das neue
    # Freeze-Dokument ist sonst ein unbekannter Pfad und blockiert das Gate.
    policy_text, policy_version = roll_over_freeze_policy(
        _read(repo, POLICY_PATH), version=inputs.version, predecessor_version=predecessor_version
    )
    planned.append(PlannedFile(POLICY_PATH, policy_text))

    freeze_relative = freeze_doc_path(inputs.version)
    freeze_text = freeze_document(
        inputs, predecessor_version=predecessor_version, policy_version=policy_version
    )
    existing_freeze = repo / freeze_relative
    if existing_freeze.is_file() and existing_freeze.read_text(encoding="utf-8") != freeze_text:
        # Gleiche Regel wie beim CHANGELOG: Nur ein unveraendertes Geruest wird
        # ersetzt. Ein zu 90 % ausformulierter Scope traegt noch Platzhalter und
        # waere unter der alten Bedingung still verloren gegangen.
        raise PrepareError(
            f"{freeze_relative}: weicht vom erzeugten Gerüst ab – wird nicht überschrieben."
        )
    planned.append(PlannedFile(freeze_relative, freeze_text))
    return PlannedRelease(files=planned, policy_version=policy_version)


def apply(repo: Path, planned: list[PlannedFile]) -> None:
    """Schreibt den geplanten Stand; legt fehlende Verzeichnisse an.

    Jede Datei atomar (``write_text_atomic``): Ein Abbruch hinterlässt nie
    eine halb geschriebene Datei. Ein Abbruch **zwischen** den Dateien bleibt
    möglich, ist im Arbeitsbaum aber per ``git checkout`` umkehrbar – die
    einzige Ablage außerhalb der Versionskontrolle (der Issue-Text) liegt
    seit #943 Befund 4 bereits vor dem ersten Schreiben hier.
    """
    for item in planned:
        write_text_atomic(repo / item.path, item.content)


def sha256_file(path: Path) -> str:
    """SHA-256 einer Datei als Hexstring (Bindungswert des Issues)."""
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


# ── Release-Issue: Ablage, Aufruf, Wiederanlauf ────────────────────────


def write_text_atomic(path: Path, text: str) -> None:
    """Schreibt *text* atomar nach *path* (``mkstemp`` + ``os.replace``).

    Muster aus ``project_io.save_project``. Entscheidend ist hier nicht der
    Absturzschutz, sondern der Wiederanlauf: Die Vorlage fuer ``gh`` steht
    entweder vollstaendig da oder gar nicht – ein halb geschriebener
    Issue-Text waere schlimmer als keiner.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp_name, path)
    finally:
        # Nach erfolgreichem ``os.replace`` existiert der Name nicht mehr.
        Path(tmp_name).unlink(missing_ok=True)


def fallback_root(repo: Path) -> Path:
    """Wurzelverzeichnis der Ablage – garantiert **ausserhalb** von *repo*.

    ``tempfile`` folgt ``TMPDIR``. Zeigt das in den Arbeitsbaum, laege die
    Ablage im Repository: ein unbekannter Pfad, den ein ``git add -A``
    mitnaehme und der dann das fail-closed Freeze-Gate blockiert. Deshalb die
    erste beschreibbare Wahl, die wirklich ausserhalb liegt – ``repo.parent``
    schliesst die Kette ab, weil es das per Definition immer ist.
    """
    candidates = (Path(tempfile.gettempdir()), Path("/tmp"), repo.parent)
    for candidate in candidates:
        resolved = candidate.resolve()
        inside = resolved == repo or repo in resolved.parents
        if not inside and resolved.is_dir() and os.access(resolved, os.W_OK):
            return resolved
    return repo.parent  # unerreichbar ausser bei unbeschreibbarem Elternpfad


def fallback_issue_path(version: str, repo: Path) -> Path:
    """Ablage des Issue-Texts, wenn ``--issue-output`` fehlt.

    Bewusst ausserhalb des Arbeitsbaums (siehe ``fallback_root``). Das eigene
    Verzeichnis kommt von ``mkdtemp`` (0700, kollisionsfrei); ein geratener
    Name in einem weltschreibbaren ``/tmp`` waere die schlechtere Wahl.
    """
    directory = Path(tempfile.mkdtemp(prefix="bgremover-release-", dir=fallback_root(repo)))
    return directory / f"release-issue-{version}.md"


def discard_fallback(path: Path) -> None:
    """Raeumt die Fallback-Ablage weg, sobald das Issue wirklich existiert.

    Sie hat genau einen Zweck – den Wiederanlauf – und ist danach nur noch
    eine zweite, alternde Fassung desselben Textes.
    """
    path.unlink(missing_ok=True)
    # Fremde Eintraege im Verzeichnis: dann bleibt es stehen.
    with contextlib.suppress(OSError):
        path.parent.rmdir()


def issue_create_argv(title: str, body_file: Path) -> list[str]:
    """Der ``gh``-Aufruf – **eine** Quelle fuer Ausfuehrung und Wiederanlauf.

    Der Body geht als Datei, nicht als Argument: Er ist mehrere Kilobyte gross.
    Und weil der ausgegebene Wiederanlauf genau diese Argumentliste rendert,
    kann er nicht von dem abweichen, was das Skript selbst versucht hat.
    """
    return ["gh", "issue", "create", "--title", title, "--body-file", str(body_file)]


def resume_command(repo: Path, argv: list[str]) -> str:
    """Der Wiederanlauf als **eine** ausfuehrbare Shell-Zeile.

    Das ``cd`` gehoert dazu: ``gh`` waehlt das Zielrepository aus dem
    Arbeitsverzeichnis, und der mit ``--repo`` gewaehlte Zielkontext darf im
    Wiederanlauf nicht verloren gehen. ``shlex`` quotet Pfade und Titel, damit
    die Zeile ohne Nacharbeit kopierbar ist.
    """
    return f"cd {shlex.quote(str(repo))} && {shlex.join(argv)}"


def create_issue(repo: Path, argv: list[str]) -> str:
    """Legt das Release-Issue ueber ``gh`` an – nur auf ausdruecklichen Wunsch."""
    result = subprocess.run(
        argv,
        cwd=repo,
        # Der Body kommt aus der Datei; eine geerbte stdin haette ``gh`` nur
        # blockieren koennen.
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise PrepareError(f"gh issue create fehlgeschlagen: {result.stderr.strip()}")
    return result.stdout.strip()


# ── CLI ────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="Zielversion, z. B. 2.10.0")
    parser.add_argument(
        "--date",
        default="",
        help="Release-Datum (JJJJ-MM-TT). Ohne Angabe: heute (UTC-Datum des Systems).",
    )
    parser.add_argument(
        "--base-tag",
        default="",
        help="Vorgänger-Tag. Ohne Angabe aus der bisherigen pyproject-Version abgeleitet.",
    )
    parser.add_argument("--repo", type=Path, default=_REPO_ROOT, help="Repository-Wurzel")
    parser.add_argument(
        "--issue-output",
        type=Path,
        default=None,
        help=(
            "Zieldatei des Release-Issues. Ohne Angabe auf die Standardausgabe – "
            "mit --create-issue zusätzlich in eine temporäre Datei, deren Pfad "
            "ausgegeben wird und die den Wiederanlauf trägt."
        ),
    )
    parser.add_argument(
        "--create-issue",
        action="store_true",
        help=(
            "Legt das Issue über 'gh issue create' an (ausdrücklicher Opt-in). "
            "Scheitert der Aufruf, nennt die Fehlermeldung den fertigen "
            "Wiederanlaufbefehl; die Release-Dateien bleiben dabei unangetastet."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur berichten, welche Dateien entstünden – nichts schreiben.",
    )
    args = parser.parse_args(argv)

    if not _SEMVER_RE.fullmatch(args.version):
        parser.error(f"Version muss X.Y.Z sein: {args.version!r}")
    # Bewusst UTC statt ``date.today()``: Das Release-Datum steht in sechs
    # CHANGELOG-Dateien und in den AppStream-Metadaten und soll nicht davon
    # abhaengen, in welcher Zeitzone der Release-Owner sitzt. Die Hilfe zu
    # ``--date`` verspricht genau das.
    release_date = args.date or datetime.now(timezone.utc).date().isoformat()
    try:
        # Echte Kalenderpruefung statt einer Formpruefung: ``2026-02-31`` haette
        # die Form erfuellt und stuende danach in sechs CHANGELOG-Dateien und in
        # den AppStream-Metadaten – das Freeze-Gate prueft nur Form und
        # Gleichheit ueber die Dateien, nicht die Existenz des Datums.
        if datetime.fromisoformat(release_date).date().isoformat() != release_date:
            raise ValueError(release_date)
    except ValueError:
        parser.error(f"Datum muss ein gültiges Kalenderdatum JJJJ-MM-TT sein: {release_date!r}")

    repo = args.repo.resolve()
    # Beide Pfade absolut: Geschrieben wird relativ zum Prozess-CWD, ``gh``
    # laeuft aber mit ``cwd=repo``. Ein relativer ``--issue-output`` zeigte
    # sonst auf zwei verschiedene Dateien – und die Wiederanlaufzeile auf gar
    # keine (#933-Review).
    issue_output: Path | None = None if args.issue_output is None else args.issue_output.resolve()
    try:
        previous = vrf._PYPROJECT_VERSION_RE.search(_read(repo, PYPROJECT_PATH))
        if previous is None:
            raise PrepareError("pyproject.toml ohne version")
        predecessor_version = previous.group(1)
        if predecessor_version == args.version:
            raise PrepareError(
                f"pyproject.toml steht bereits auf {args.version} – "
                "Zielversion und Vorgänger dürfen nicht gleich sein."
            )
        # Nur Gleichheit abzuweisen genügte nicht: Bei Stand 2.9.0 lief ein
        # Aufruf für 2.8.1 durch und plante ein in sich konsistentes
        # Downgrade-Gerüst über pyproject, sechs CHANGELOGs, AppStream,
        # Pfadpolicy und Freeze-Dokument (#943 Befund 3). Fail-closed heißt
        # hier: Die Zielversion muss belegbar größer sein – ein Vorgänger
        # außerhalb des X.Y.Z-Schemas macht den Vergleich unmöglich und ist
        # deshalb selbst der Abbruchgrund.
        if not _SEMVER_RE.fullmatch(predecessor_version):
            raise PrepareError(
                f"pyproject.toml-Version {predecessor_version!r} ist nicht X.Y.Z – "
                "Downgrade-Schutz nicht prüfbar, Vorbereitung abgebrochen."
            )
        if _semver_key(args.version) < _semver_key(predecessor_version):
            raise PrepareError(
                f"Zielversion {args.version} liegt unter der pyproject-Version "
                f"{predecessor_version} – ein Tippfehler erzeugte sonst ein "
                "konsistentes Downgrade-Gerüst statt eines Fehlers."
            )
        base_tag = args.base_tag or f"v{predecessor_version}"
        base_sha = resolve_tag(repo, base_tag)

        inputs = ReleaseInputs(
            version=args.version,
            release_date=release_date,
            base_tag=base_tag,
            base_sha=base_sha,
        )
        prepared = plan(repo, inputs, predecessor_version=predecessor_version)

        checklist_path = repo / rc.CHECKLIST_PATH
        checklist = rc.load_release_checklist(checklist_path)
        issue_body = release_issue(
            inputs,
            checklist_version=str(checklist["checklist_version"]),
            checklist_sha256=sha256_file(checklist_path),
            paused_criteria=paused_x86_64_criteria(checklist),
            policy_version=prepared.policy_version,
        )
        unknown = unknown_paths_since(repo, base_sha)
    except (PrepareError, rc.ContractError) as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        return 2

    issue_title = f"[Release {args.version}] Abnahme- und Veröffentlichungsprotokoll"
    # Externe Ablagen ZUERST, dann erst die Repo-Mutation (#943 Befund 4).
    # Vorher lief ``apply`` zuerst: Ein nicht beschreibbarer ``--issue-output``
    # (oder eine scheiternde Fallback-Ablage) hinterliess ein bereits
    # mutiertes Repo, und der zweite Skriptlauf brach ab, weil
    # ``pyproject.toml`` schon auf der Zielversion stand. Scheitert die Ablage
    # jetzt, ist noch nichts geschrieben – Pfad korrigieren und erneut
    # ausführen ist der vollständige Wiederanlauf. Vor jedem GitHub-Aufruf
    # liegt der Issue-Text damit weiterhin als Datei vor (#933).
    fallback: Path | None = None
    issue_path: Path | None = issue_output
    if not args.dry_run:
        try:
            if issue_output is not None:
                write_text_atomic(issue_output, issue_body)
            elif args.create_issue:
                fallback = fallback_issue_path(args.version, repo)
                issue_path = fallback
                write_text_atomic(fallback, issue_body)
        except OSError as exc:
            print(
                f"FEHLER: Issue-Ablage nicht beschreibbar ({exc}). Es wurde noch "
                "keine Release-Datei geschrieben – Pfad korrigieren und das "
                "Skript unverändert erneut ausführen.",
                file=sys.stderr,
            )
            return 2

    if args.dry_run:
        print(f"Vorbereitung {predecessor_version} → {args.version} ({release_date}), nur Bericht:")
    else:
        apply(repo, prepared.files)
    for item in prepared.files:
        print(f"  {'geplant' if args.dry_run else 'geschrieben'}: {item.path}")
    print(f"  Pfadpolicy: Version {prepared.policy_version} (current-freeze umgehängt)")

    if args.dry_run:
        # Ein Probelauf soll ALLES zeigen, was entstuende – auch das Issue.
        # Geschrieben oder angelegt wird dabei nichts.
        print(f"\n--- Release-Issue (Vorschau): {issue_title} ---")
        print(issue_body)
        if args.create_issue:
            print("\nHINWEIS: --create-issue wird im Probelauf nicht ausgeführt.", file=sys.stderr)
    elif issue_output is not None:
        print(f"  geschrieben: {issue_output}")
    else:
        print(f"\n--- Release-Issue: {issue_title} ---")
        print(issue_body)
        if fallback is not None:
            print(f"\n  gesichert für den Wiederanlauf: {fallback}")

    if args.create_issue and not args.dry_run:
        # Oben gesetzt: entweder ``--issue-output`` oder die Fallback-Ablage.
        assert issue_path is not None
        gh_argv = issue_create_argv(issue_title, issue_path)
        try:
            url = create_issue(repo, gh_argv)
        except PrepareError as exc:
            # Die Dateien stehen bereits; ein zweiter Skriptlauf braeche ab
            # ("pyproject steht bereits auf ..."). Deshalb hier der konkrete
            # Wiederanlauf statt eines blossen Fehlers: dieselbe Argumentliste,
            # die soeben scheiterte, gegen dieselbe bereits geschriebene Datei.
            print(f"FEHLER: {exc}", file=sys.stderr)
            print(
                "Der Rohstand ist vollständig geschrieben – nur das Anlegen scheiterte. "
                "Wiederanlauf ohne erneuten Skriptlauf (legt genau dieses Issue an und "
                f"schreibt keine Release-Datei neu):\n"
                f"  {resume_command(repo, gh_argv)}",
                file=sys.stderr,
            )
            return 2
        print(f"Issue angelegt: {url}")
        if fallback is not None:
            discard_fallback(fallback)

    # Der Policy-Hinweis steht bewusst am Ende: Er ist die einzige Stelle, an
    # der dieses Skript etwas ueber den *Inhalt* des Fensters sagen kann.
    if unknown:
        print(
            f"\nHINWEIS: {len(unknown)} Pfad(e) seit {base_tag} ohne explizite Klassifikation. "
            "Sie blockieren das Freeze-Gate fail-closed, bis release/path-policy.json "
            "ergänzt und ihre policy_version angehoben ist:",
            file=sys.stderr,
        )
        for path in unknown:
            print(f"  - {path}", file=sys.stderr)

    # Was das Skript bewusst NICHT erledigt, gehoert hierher – sonst sucht der
    # Release-Owner die Ursache eines roten ``make check`` im Erzeugten statt
    # in der eigenen Liste. Beide Punkte brauchen eine Entscheidung bzw. die
    # installierte Umgebung und sind deshalb keine Automatisierung.
    print(
        f"""
Nächste Schritte (in dieser Reihenfolge):
  1. Redaktionelle {PLACEHOLDER}-Lücken füllen: Scope im Freeze-Dokument sowie
     Auswirkung, Betroffene, Upgrade-Relevanz und Einschränkungen in allen
     sechs CHANGELOG-Fassungen.
  2. Lizenz-Snapshots neu erzeugen: python scripts/generate_license_report.py
     (braucht die installierte Umgebung, deshalb nicht Teil dieses Laufs).
  3. Paket neu installieren (pip install -e '.[test]'), sonst meldet
     tests/test_version.py weiter die alte Metadaten-Version.
  4. tests/test_release_freeze.py pinnt Basis-Tag und Release-Scope des
     jeweils aktuellen Release – beide Literale von Hand nachziehen.
  5. make check und python scripts/verify_release_freeze.py."""
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI-Einstieg
    sys.exit(main())
