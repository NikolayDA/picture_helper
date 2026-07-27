#!/usr/bin/env python3
"""Prueft einen Commit als selbstkonsistenten Release-Kandidaten (#699).

Hintergrund: Der Scope-Freeze fuer 2.7.1 nannte einen handkopierten Kurz-SHA
(``ba7e7cd``) als verbindliche Freeze-Basis. An genau diesem Commit stand
``pyproject.toml`` aber noch auf ``2.7.0`` – Versionsschnitt und Freeze-Dokument
kamen erst mit dem naechsten Commit. Das ist kein Schreibfehler, sondern
strukturell unvermeidbar: **ein Dokument kann seinen eigenen Commit-SHA nicht
enthalten.** Ein handgepflegter Freeze-Hash driftet deshalb systematisch.

Dieses Skript ersetzt die Handarbeit durch eine *abgeleitete* Kandidatenregel:

    Kandidat = der juengste Commit der Mainline (first-parent) seit dem
    Basis-Tag, der einen kandidatenrelevanten Pfad aendert.

Kandidatenrelevant ist alles ausser einer kurzen, explizit erlaubten Liste von
Protokoll-Pfaden (Freeze-/Historien-Dokumente, Statusdoku). Die Regel ist
fail-closed: unbekannte Pfade gelten als kandidatenrelevant, damit ein neuer
Pfad nie stillschweigend aus dem Freeze herausfaellt.

Darauf aufbauend verifiziert das Skript genau diesen Commit: Versionsquellen,
CHANGELOG-Abschnitt in allen sechs Sprachen, AppStream-Metadaten, Lizenz-
Snapshots, vollstaendige Klassifizierung aller Commits im Vergleichsfenster und
den tatsaechlich veroeffentlichten Release-Body (``extract_release_notes.py``).

Nur Standardbibliothek + ``git``, damit es auf jedem Runner ohne Zusatzpakete
laeuft. Exit 0 = keine Fehler, 1 = mindestens ein Fehler, 2 = Aufruf-/Git-Fehler.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, cast

_REPO_ROOT: Final = Path(__file__).resolve().parent.parent
#: Quelle des Release-Bodys – wird am geprueften Commit gelesen, nicht lokal.
_EXTRACT_SCRIPT_PATH: Final = "scripts/extract_release_notes.py"

LANGUAGES: Final = ("en", "es", "fr", "uk", "zh")

#: Standardpfad des Freeze-Dokuments je Version (relativ zur Repo-Wurzel).
FREEZE_DOC_TEMPLATE: Final = "docs/history/RELEASE-{version}-scope-freeze.md"

#: Einzelne Pfade, die den Kandidaten nicht beruehren (reine Protokoll-/
#: Statusdoku). Alles andere gilt als kandidatenrelevant (fail-closed).
PROTOCOL_PATHS: Final = frozenset(
    {
        "CLAUDE.md",
        "RECOMMENDATIONS.md",
        *(f"docs/i18n/{lang}/RECOMMENDATIONS.md" for lang in LANGUAGES),
    }
)

#: Verzeichnisse, deren Inhalte den Kandidaten nicht beruehren.
PROTOCOL_PREFIXES: Final = ("docs/history/",)

#: Pflichtangaben des veroeffentlichten Release-Bodys (#683/#699). Der Body wird
#: aus dem CHANGELOG-Abschnitt extrahiert – die Angaben muessen also im
#: CHANGELOG selbst stehen, nicht nur im Freeze-Dokument.
RELEASE_BODY_MARKERS: Final[dict[str, tuple[str, ...]]] = {
    "de": (
        "**Auswirkung:**",
        "**Betroffene Anwender:innen:**",
        "**Upgrade-Relevanz:**",
        "**Bekannte Einschränkungen:**",
    ),
    "en": (
        "**Impact:**",
        "**Affected users:**",
        "**Upgrade relevance:**",
        "**Known limitations:**",
    ),
    "es": (
        "**Impacto:**",
        "**Usuarios afectados:**",
        "**Relevancia de la actualización:**",
        "**Limitaciones conocidas:**",
    ),
    "fr": (
        "**Impact :**",
        "**Utilisateurs concernés :**",
        "**Pertinence de la mise à jour :**",
        "**Limitations connues :**",
    ),
    "uk": (
        "**Вплив:**",
        "**Кого це стосується:**",
        "**Чи потрібне оновлення:**",
        "**Відомі обмеження:**",
    ),
    "zh": (
        "**影响：**",
        "**受影响的用户：**",
        "**升级相关性：**",
        "**已知限制：**",
    ),
}

_ERROR: Final = "error"
_WARNING: Final = "warning"
_OK: Final = "ok"

_SEVERITY_ORDER: Final = {_ERROR: 0, _WARNING: 1, _OK: 2}

# ── Dokument-Parsing ───────────────────────────────────────────────────
#
# Das Freeze-Dokument ist menschenlesbar; die maschinenlesbaren Angaben stehen
# in festen Listenzeilen bzw. als voller SHA in der ersten Tabellenspalte.

_DOC_VERSION_RE: Final = re.compile(r"(?m)^- \*\*Kandidatenversion:\*\* `(\d+\.\d+\.\d+)`")
#: Das Basis-Tag wird mit seinem vollen SHA eingefroren. Ein Tag ist verschiebbar –
#: nur der SHA legt das Vergleichsfenster unveraenderlich fest (Codex-Review #701).
_DOC_BASE_RE: Final = re.compile(
    r"(?m)^- \*\*Basis-Tag:\*\* `(v\d+\.\d+\.\d+)` \(= `([0-9a-f]{40})`\)"
)
_DOC_COUNT_RE: Final = re.compile(r"(?m)^- \*\*Commits im Fenster:\*\* (\d+)\b")
_DOC_PIN_RE: Final = re.compile(
    r"(?m)^- \*\*Protokollierter Kandidaten-SHA:\*\* `([0-9a-f]{40}|nachzutragen)`"
)
_DOC_ROW_SHA_RE: Final = re.compile(r"(?m)^\| `([0-9a-f]{40})`")
_DOC_SELF_ROW_RE: Final = re.compile(r"(?m)^\| `Kandidaten-Commit`")

_PYPROJECT_VERSION_RE: Final = re.compile(r'(?m)^\s*version\s*=\s*"([^"]+)"')
_LICENSE_TITLE_RE: Final = re.compile(r"(?m)^#\s+.*\bbgremover\s+(\S+)\s*$")
_PIN_PLACEHOLDER: Final = "nachzutragen"


class GitError(RuntimeError):
    """``git`` hat einen Aufruf mit Fehlerstatus beendet."""


class DocFormatError(RuntimeError):
    """Das Freeze-Dokument fehlt oder haelt die maschinenlesbaren Zeilen nicht ein."""


@dataclass(frozen=True)
class Finding:
    """Ein einzelner Prueffund (stabiler ``code`` fuer Tests/Logs)."""

    severity: str
    code: str
    message: str


@dataclass(frozen=True)
class FreezeDoc:
    """Maschinenlesbarer Kern des Freeze-Dokuments."""

    version: str
    base_tag: str
    base_sha: str
    declared_count: int
    pinned_candidate: str | None
    classified: tuple[str, ...]
    has_self_row: bool


def parse_freeze_doc(text: str) -> FreezeDoc:
    """Liest die verbindlichen Angaben aus dem Freeze-Dokument.

    Wirft ``DocFormatError``, wenn eine der Pflichtzeilen fehlt – ein
    unlesbares Freeze-Dokument darf nie als „geprueft" durchgehen.
    """
    version = _DOC_VERSION_RE.search(text)
    base = _DOC_BASE_RE.search(text)
    count = _DOC_COUNT_RE.search(text)
    pin = _DOC_PIN_RE.search(text)
    missing = [
        name
        for name, match in (
            ("Kandidatenversion", version),
            ("Basis-Tag", base),
            ("Commits im Fenster", count),
            ("Protokollierter Kandidaten-SHA", pin),
        )
        if match is None
    ]
    if missing:
        raise DocFormatError(
            "Pflichtzeilen im Freeze-Dokument fehlen bzw. weichen vom Format ab: "
            + ", ".join(missing)
        )
    assert version is not None and base is not None and count is not None and pin is not None
    pinned = None if pin.group(1) == _PIN_PLACEHOLDER else pin.group(1)
    return FreezeDoc(
        version=version.group(1),
        base_tag=base.group(1),
        base_sha=base.group(2),
        declared_count=int(count.group(1)),
        pinned_candidate=pinned,
        classified=tuple(match.group(1) for match in _DOC_ROW_SHA_RE.finditer(text)),
        has_self_row=_DOC_SELF_ROW_RE.search(text) is not None,
    )


# ── Pfadklassifizierung ────────────────────────────────────────────────


def is_candidate_relevant(path: str) -> bool:
    """Ob *path* den Release-Kandidaten inhaltlich veraendert (fail-closed)."""
    if path in PROTOCOL_PATHS:
        return False
    return not path.startswith(PROTOCOL_PREFIXES)


def candidate_relevant_paths(paths: Iterable[str]) -> tuple[str, ...]:
    """Die kandidatenrelevante Teilmenge von *paths*, Reihenfolge erhalten."""
    return tuple(path for path in paths if is_candidate_relevant(path))


# ── Git-Zugriffe ───────────────────────────────────────────────────────


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise GitError(f"git {' '.join(args)} -> {result.returncode}: {result.stderr.strip()}")
    return result.stdout


def rev_parse(repo: Path, rev: str) -> str:
    """Voller 40-stelliger SHA von *rev*."""
    return _git(repo, "rev-parse", f"{rev}^{{commit}}").strip()


def commits_between(
    repo: Path, base: str, rev: str, *, first_parent: bool = False
) -> tuple[str, ...]:
    """Volle SHAs in ``base..rev``, jüngster zuerst.

    ``first_parent`` folgt nur der Mainline: bei einem Merge zählt der Merge-Commit
    selbst (mit seinem *netto* eingebrachten Baum), nicht die Seitenzweig-Commits.
    """
    args = ["rev-list", "--first-parent"] if first_parent else ["rev-list"]
    out = _git(repo, *args, f"{base}..{rev}")
    return tuple(line.strip() for line in out.splitlines() if line.strip())


def changed_paths(repo: Path, sha: str) -> tuple[str, ...]:
    """Pfade, die *sha* gegenueber seinem ersten Parent aendert.

    ``--no-renames`` ist Pflicht: mit Umbenennungserkennung meldet git fuer
    ``git mv bgremover/x.py docs/history/x.py`` nur das *Ziel*. Der Commit
    saehe damit wie ein reiner Protokoll-Commit aus, obwohl er Anwendungscode
    aus dem Baum entfernt – der Kandidat wuerde nicht nachgezogen und
    ``--require-pin`` bliebe gruen (Codex-Review #701). Ohne Erkennung
    erscheinen beide Seiten, und die Quelle ist kandidatenrelevant.
    """
    parents = _git(repo, "rev-list", "--parents", "-n", "1", sha).split()[1:]
    if parents:
        out = _git(repo, "diff", "--no-renames", "--name-only", parents[0], sha)
    else:  # Root-Commit (im Repo praktisch nicht erreichbar, aber definiert)
        out = _git(repo, "show", "--no-renames", "--name-only", "--pretty=format:", sha)
    return tuple(line.strip() for line in out.splitlines() if line.strip())


def is_ancestor(repo: Path, ancestor: str, descendant: str) -> bool:
    """Ob *ancestor* ein Vorfahr von *descendant* ist (beide muessen existieren)."""
    result = subprocess.run(
        ["git", "-C", str(repo), "merge-base", "--is-ancestor", ancestor, descendant],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode in (0, 1):
        return result.returncode == 0
    raise GitError(f"git merge-base --is-ancestor -> {result.returncode}: {result.stderr.strip()}")


def read_at_rev(repo: Path, rev: str, path: str) -> str:
    """Dateiinhalt von *path* am Commit *rev*."""
    return _git(repo, "show", f"{rev}:{path}")


def subject(repo: Path, sha: str) -> str:
    return _git(repo, "log", "-1", "--format=%s", sha).strip()


def derive_candidate(repo: Path, base: str, rev: str) -> str | None:
    """Juengster kandidatenrelevanter Commit der Mainline (oder ``None``).

    Bewusst **first-parent**: ein unsquashed Merge zaehlt mit dem Baum, den er
    tatsaechlich in die Release-Linie eingebracht hat. Wuerde man alle Commits
    aufzaehlen, koennte ein Seitenzweig-Commit zum Kandidaten werden, dessen
    Aenderung nie ankam (Konfliktaufloesung, ``-s ours``, spaeterer Revert) –
    alle Folgepruefungen liefen dann gegen einen Baum, der nie getaggt wird.
    """
    for sha in commits_between(repo, base, rev, first_parent=True):
        if candidate_relevant_paths(changed_paths(repo, sha)):
            return sha
    return None


# ── Release-Body ───────────────────────────────────────────────────────


def load_extract_release_notes(repo: Path, rev: str) -> Callable[[str, str], str]:
    """Laedt ``extract_release_notes`` **aus dem geprueften Commit**.

    Der Release-Body entsteht aus dem Skript, das im getaggten Stand liegt.
    Wuerde hier die Arbeitsbaum-Fassung geladen, koennte die Pruefung einen Body
    melden, den der Kandidat selbst nie erzeugt (anderer ``--rev``/``--repo``).
    """
    source = read_at_rev(repo, rev, _EXTRACT_SCRIPT_PATH)
    # ``__file__`` setzen: das Skript leitet daraus seinen CHANGELOG-Default ab.
    # ``__name__`` ist bewusst nicht "__main__" – so laeuft dort kein CLI an.
    namespace: dict[str, object] = {
        "__name__": "extract_release_notes_at_rev",
        "__file__": str(repo / _EXTRACT_SCRIPT_PATH),
    }
    exec(compile(source, f"{rev}:{_EXTRACT_SCRIPT_PATH}", "exec"), namespace)
    func = namespace.get("extract_release_notes")
    if not callable(func):
        raise DocFormatError(
        f"{_EXTRACT_SCRIPT_PATH} am Commit {rev} ohne extract_release_notes()"
        )
    return cast(Callable[[str, str], str], func)


def changelog_release_date(changelog: str, version: str) -> str | None:
    """Datum der Ueberschrift ``## [version] – JJJJ-MM-TT`` (oder ``None``)."""
    match = re.search(rf"(?m)^## \[{re.escape(version)}\] – (\d{{4}}-\d{{2}}-\d{{2}})$", changelog)
    return match.group(1) if match else None


def missing_release_body_markers(notes: str, language: str) -> tuple[str, ...]:
    """Pflichtangaben, die im Release-Body *notes* der *language* fehlen."""
    return tuple(marker for marker in RELEASE_BODY_MARKERS[language] if marker not in notes)


# ── Einzelpruefungen ───────────────────────────────────────────────────


def _check_versions(repo: Path, rev: str, doc: FreezeDoc) -> list[Finding]:
    """pyproject, CHANGELOG-Datum, AppStream und Lizenz-Snapshots am Kandidaten."""
    findings: list[Finding] = []
    version = doc.version

    pyproject = _PYPROJECT_VERSION_RE.search(read_at_rev(repo, rev, "pyproject.toml"))
    if pyproject is None:
        findings.append(Finding(_ERROR, "pyproject-version-missing", "pyproject.toml ohne version"))
    elif pyproject.group(1) != version:
        findings.append(
            Finding(
                _ERROR,
                "pyproject-version-mismatch",
                f"pyproject.toml meldet {pyproject.group(1)}, Freeze-Dokument {version}",
            )
        )
    else:
        findings.append(Finding(_OK, "pyproject-version", f"pyproject.toml = {version}"))

    release_date = changelog_release_date(read_at_rev(repo, rev, "CHANGELOG.md"), version)
    if release_date is None:
        findings.append(
            Finding(
                _ERROR,
                "changelog-section-missing",
                f"CHANGELOG.md ohne datierte Überschrift '## [{version}] – JJJJ-MM-TT'",
            )
        )
    else:
        findings.append(
            Finding(_OK, "changelog-section", f"CHANGELOG.md [{version}] – {release_date}")
        )
        metainfo = ET.fromstring(
            read_at_rev(repo, rev, "packaging/linux/de.bgremover.app.metainfo.xml")
        )
        release = metainfo.find("releases/release")
        if release is None:
            findings.append(
                Finding(_ERROR, "appstream-release-missing", "AppStream ohne <release>-Eintrag")
            )
        elif (release.get("version"), release.get("date")) != (version, release_date):
            findings.append(
                Finding(
                    _ERROR,
                    "appstream-release-mismatch",
                    f"AppStream meldet {release.get('version')}/{release.get('date')}, "
                    f"erwartet {version}/{release_date}",
                )
            )
        else:
            findings.append(
                Finding(_OK, "appstream-release", f"AppStream {version}/{release_date}")
            )

    for path in ("LICENSES.md", *(f"docs/i18n/{lang}/LICENSES.md" for lang in LANGUAGES)):
        title = _LICENSE_TITLE_RE.search(read_at_rev(repo, rev, path))
        if title is None:
            findings.append(
                Finding(_ERROR, "license-title-missing", f"{path}: keine 'bgremover <version>'-H1")
            )
        elif title.group(1) != version:
            findings.append(
                Finding(
                    _ERROR,
                    "license-version-mismatch",
                    f"{path} meldet {title.group(1)}, erwartet {version}",
                )
            )
    if not any(f.code.startswith("license-") for f in findings):
        findings.append(Finding(_OK, "license-versions", f"6 Lizenz-Snapshots auf {version}"))
    return findings


def _check_release_body(repo: Path, rev: str, doc: FreezeDoc) -> list[Finding]:
    """Der tatsaechlich veroeffentlichte Body nennt die Pflichtangaben (#683).

    Zusaetzlich wird je Sprache die *Datumszeile* geprueft. ``extract_release_notes``
    akzeptiert hinter ``## [2.7.1]`` beliebigen Text – eine Uebersetzung koennte
    also ein fehlendes oder falsches Release-Datum tragen, waehrend der Body
    formal vollstaendig ist; verglichen wurde bisher nur das deutsche Datum mit
    AppStream (Codex-Review #701).
    """
    extract = load_extract_release_notes(repo, rev)
    findings: list[Finding] = []
    root_date = changelog_release_date(read_at_rev(repo, rev, "CHANGELOG.md"), doc.version)
    for language in ("de", *LANGUAGES):
        path = "CHANGELOG.md" if language == "de" else f"docs/i18n/{language}/CHANGELOG.md"
        changelog = read_at_rev(repo, rev, path)
        date = changelog_release_date(changelog, doc.version)
        if date is None:
            findings.append(
                Finding(
                    _ERROR,
                    "release-date-missing",
                    f"{path}: Überschrift [{doc.version}] ohne Datum 'JJJJ-MM-TT'",
                )
            )
        elif root_date is not None and date != root_date:
            findings.append(
                Finding(
                    _ERROR,
                    "release-date-mismatch",
                    f"{path}: Release-Datum {date}, CHANGELOG.md nennt {root_date}",
                )
            )
        try:
            notes = extract(changelog, doc.version)
        except KeyError:
            findings.append(
                Finding(
                    _ERROR,
                    "release-body-missing",
                    f"{path}: kein Abschnitt [{doc.version}] – Release-Body nicht ableitbar",
                )
            )
            continue
        missing = missing_release_body_markers(notes, language)
        if missing:
            findings.append(
                Finding(
                    _ERROR,
                    "release-body-incomplete",
                    f"{path}: Release-Body ohne {', '.join(missing)}",
                )
            )
    if not any(f.code.startswith("release-body") for f in findings):
        findings.append(
            Finding(
                _OK,
                "release-body",
                "Release-Body nennt Auswirkung/Betroffene/Upgrade/Einschränkungen (6 Sprachen)",
            )
        )
    if not any(f.code.startswith("release-date") for f in findings):
        findings.append(
            Finding(_OK, "release-dates", f"6 CHANGELOG-Überschriften datiert auf {root_date}")
        )
    return findings


def _check_classification(
    repo: Path, base: str, candidate: str, window: Sequence[str], doc: FreezeDoc
) -> list[Finding]:
    """Jeder Commit im Fenster ist klassifiziert – oder nachweislich Protokoll."""
    findings: list[Finding] = []
    classified = set(doc.classified)

    unknown = classified - set(window)
    if unknown:
        findings.append(
            Finding(
                _ERROR,
                "classified-outside-window",
                "Tabelle nennt SHAs außerhalb von "
                f"{base}..{candidate[:12]}: {', '.join(sorted(s[:12] for s in unknown))}",
            )
        )

    for sha in window:
        if sha in classified:
            continue
        if sha == candidate:
            if not doc.has_self_row:
                findings.append(
                    Finding(
                        _ERROR,
                        "self-row-missing",
                        "Der Kandidaten-Commit selbst braucht eine Tabellenzeile "
                        "`Kandidaten-Commit` (er kann seinen eigenen SHA nicht enthalten)",
                    )
                )
            continue
        relevant = candidate_relevant_paths(changed_paths(repo, sha))
        if relevant:
            findings.append(
                Finding(
                    _ERROR,
                    "unclassified-candidate-commit",
                    f"{sha} ({subject(repo, sha)}) ändert kandidatenrelevante Pfade "
                    f"({', '.join(relevant[:3])}…) und ist nicht klassifiziert",
                )
            )
        else:
            findings.append(
                Finding(
                    _WARNING,
                    "unclassified-protocol-commit",
                    f"{sha} ({subject(repo, sha)}) ist ein reiner Protokoll-Commit, "
                    "aber noch nicht in der Tabelle nachgetragen",
                )
            )

    if len(window) != doc.declared_count:
        findings.append(
            Finding(
                _ERROR,
                "commit-count-mismatch",
                f"Fenster {base}..{candidate[:12]} enthält {len(window)} Commits, "
                f"Dokument nennt {doc.declared_count}",
            )
        )
    if not any(f.severity == _ERROR for f in findings):
        findings.append(
            Finding(_OK, "classification", f"{len(window)} Commits vollständig klassifiziert")
        )
    return findings


def _check_pin(repo: Path, rev: str, candidate: str, doc: FreezeDoc, require_pin: bool) -> Finding:
    """Der protokollierte 40-stellige SHA stimmt mit dem abgeleiteten Kandidaten."""
    if doc.pinned_candidate is None:
        severity = _ERROR if require_pin else _WARNING
        return Finding(
            severity,
            "candidate-sha-unpinned",
            "Kandidaten-SHA noch nicht protokolliert – Protokoll-Commit ausstehend "
            f"(abgeleitet: {candidate})",
        )
    if doc.pinned_candidate != candidate:
        # Ein Merge-/Squash-Commit beim Einbringen nach ``main`` erzeugt einen
        # neuen kandidatenrelevanten Commit mit identischem kandidatenrelevanten
        # Inhalt. Das ist kein Freeze-Bruch, sondern ein Protokoll-Nachtrag.
        drift = candidate_relevant_paths(
            _git(
                repo, "diff", "--no-renames", "--name-only", doc.pinned_candidate, candidate
            ).splitlines()
        )
        if drift:
            return Finding(
                _ERROR,
                "candidate-sha-mismatch",
                f"Dokument protokolliert {doc.pinned_candidate}, abgeleitet ist {candidate}; "
                f"kandidatenrelevante Abweichung: {', '.join(drift[:5])}",
            )
        # Ohne --require-pin ist das der normale Merge-Uebergang (Warnung). Als
        # Gate fuer #685/#686 zaehlt dagegen nur der exakte, aktuelle SHA: sonst
        # baut/taggt der Release einen anderen Commit als den dokumentierten.
        return Finding(
            _ERROR if require_pin else _WARNING,
            "candidate-sha-equivalent",
            f"Abgeleiteter Kandidat {candidate} ist freeze-äquivalent zum protokollierten "
            f"{doc.pinned_candidate} (identischer kandidatenrelevanter Baum), aber nicht "
            "identisch – Protokoll-Commit muss den SHA nachziehen, bevor gebaut/getaggt wird",
        )
    ahead = commits_between(repo, candidate, rev)
    suffix = f" (+{len(ahead)} Protokoll-Commit(s) darüber)" if ahead else ""
    return Finding(_OK, "candidate-sha", f"Kandidaten-SHA {candidate} protokolliert{suffix}")


# ── Orchestrierung ─────────────────────────────────────────────────────


def verify(repo: Path, rev: str, *, require_pin: bool = False) -> list[Finding]:
    """Alle Pruefungen fuer *rev*; sammelt Befunde statt beim ersten zu stoppen."""
    head = rev_parse(repo, rev)
    findings: list[Finding] = []

    # Version und Dokument werden am geprueften Commit gelesen, nicht im Arbeitsbaum.
    version = version_at_rev(repo, head)
    if version is None:
        return [Finding(_ERROR, "pyproject-version-missing", "pyproject.toml ohne version")]
    doc = parse_freeze_doc(read_at_rev(repo, head, FREEZE_DOC_TEMPLATE.format(version=version)))

    # Das Vergleichsfenster haengt am eingefrorenen **SHA**, nicht am Tag-Namen:
    # ein verschobenes Tag koennte auf einen Geschwister-Commit mit demselben
    # Parent zeigen und dasselbe base..head-Fenster erzeugen, waehrend alle
    # Pruefungen gegen die falsche Basis liefen (Codex-Review #701).
    base = doc.base_sha
    try:
        resolved_tag = rev_parse(repo, doc.base_tag)
    except GitError:
        return [
            Finding(
                _ERROR,
                "base-tag-missing",
                f"Basis-Tag {doc.base_tag} ist lokal nicht bekannt (git fetch --tags?)",
            )
        ]
    if resolved_tag != base:
        return [
            Finding(
                _ERROR,
                "base-tag-moved",
                f"Basis-Tag {doc.base_tag} zeigt auf {resolved_tag}, eingefroren ist {base} – "
                "das Tag wurde verschoben oder das Freeze-Dokument nennt die falsche Basis",
            )
        ]
    if not is_ancestor(repo, base, head):
        return [
            Finding(
                _ERROR,
                "base-not-ancestor",
                f"Eingefrorene Basis {base} ist kein Vorfahr von {head[:12]} – "
                "der geprüfte Commit steht nicht auf der Release-Linie",
            )
        ]
    findings.append(
        Finding(_OK, "base-tag", f"Basis {doc.base_tag} = {base}, Vorfahr von {head[:12]}")
    )

    candidate = derive_candidate(repo, base, head)
    if candidate is None:
        return [
            Finding(
                _ERROR,
                "no-candidate-commit",
                f"Kein kandidatenrelevanter Commit in {base}..{head[:12]}",
            )
        ]

    findings.append(
        Finding(_OK, "candidate", f"Abgeleiteter Kandidat: {candidate} ({subject(repo, candidate)})")
    )
    findings += _check_versions(repo, candidate, doc)
    findings += _check_release_body(repo, candidate, doc)
    findings += _check_classification(
        repo, doc.base_tag, candidate, commits_between(repo, base, candidate), doc
    )
    findings.append(_check_pin(repo, head, candidate, doc, require_pin))
    return findings


def version_at_rev(repo: Path, rev: str) -> str | None:
    """Die am Commit *rev* gueltige Version aus ``pyproject.toml``."""
    match = _PYPROJECT_VERSION_RE.search(read_at_rev(repo, rev, "pyproject.toml"))
    return match.group(1) if match else None


def format_findings(findings: Sequence[Finding]) -> str:
    """Sortierter, menschenlesbarer Bericht (Fehler zuerst)."""
    symbols = {_ERROR: "FEHLER ", _WARNING: "WARNUNG", _OK: "ok     "}
    ordered = sorted(findings, key=lambda f: (_SEVERITY_ORDER[f.severity], f.code))
    return "\n".join(f"{symbols[f.severity]} [{f.code}] {f.message}" for f in ordered)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rev", default="HEAD", help="Zu pruefender Commit (Default: HEAD)")
    parser.add_argument(
        "--repo", type=Path, default=_REPO_ROOT, help="Repo-Wurzel (Default: dieses Repository)"
    )
    parser.add_argument(
        "--print-candidate",
        action="store_true",
        help="Nur den abgeleiteten, vollen 40-stelligen Kandidaten-SHA ausgeben",
    )
    parser.add_argument(
        "--require-pin",
        action="store_true",
        help="Fehlender protokollierter Kandidaten-SHA ist ein Fehler (fuer #685/#686)",
    )
    args = parser.parse_args(argv)

    try:
        if args.print_candidate:
            head = rev_parse(args.repo, args.rev)
            version = version_at_rev(args.repo, head)
            if version is None:
                print("::error::pyproject.toml ohne version", file=sys.stderr)
                return 2
            doc = parse_freeze_doc(
                read_at_rev(args.repo, head, FREEZE_DOC_TEMPLATE.format(version=version))
            )
            candidate = derive_candidate(args.repo, doc.base_sha, head)
            if candidate is None:
                print("::error::kein kandidatenrelevanter Commit im Fenster", file=sys.stderr)
                return 2
            print(candidate)
            return 0
        findings = verify(args.repo, args.rev, require_pin=args.require_pin)
    except (GitError, DocFormatError, ET.ParseError) as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 2

    print(format_findings(findings))
    errors = sum(1 for finding in findings if finding.severity == _ERROR)
    warnings = sum(1 for finding in findings if finding.severity == _WARNING)
    print(f"\n{errors} Fehler, {warnings} Warnung(en).")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
