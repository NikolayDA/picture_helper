#!/usr/bin/env python3
"""Prueft einen Laufkopf und erzeugt Release-Freeze-Provenienz (#742/#743).

Das versionierte Freeze-Dokument enthaelt nur vor einem Merge bekannte stabile
Angaben: Version, unveraenderliche Basis, Scope und Pfadpolicy-Version. Der
Kandidaten-SHA ist der tatsaechlich gepruefte Laufkopf; Commitliste, Pfade,
Klassifikationen und Zaehler werden aus der First-Parent-Historie abgeleitet und
als maschinenlesbare Actions-Evidenz ausgegeben. Damit gibt es keinen
selbstreferenziellen Pin- oder Ledger-Nachtrags-Commit mehr.

Die gemeinsame Policy aus ``release/path-policy.json`` ist fail-closed:
Unbekannte Pfade sind kandidatenrelevant und blockieren das Release-Gate, bis
ihre Klasse bewusst dokumentiert wurde. Nur Standardbibliothek + ``git`` sind
erforderlich. Exit 0 = keine Fehler, 1 = mindestens ein Fehler, 2 = Aufruf-/
Git-/Dokumentfehler.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, cast

try:  # Dateiaufruf: ``python scripts/verify_release_freeze.py``
    import release_path_policy as rpp
except ModuleNotFoundError:  # Import als ``scripts.verify_release_freeze`` in Tests
    from scripts import release_path_policy as rpp

_REPO_ROOT: Final = Path(__file__).resolve().parent.parent
#: Quelle des Release-Bodys – wird am geprueften Commit gelesen, nicht lokal.
_EXTRACT_SCRIPT_PATH: Final = "scripts/extract_release_notes.py"

LANGUAGES: Final = ("en", "es", "fr", "uk", "zh")

#: Standardpfad des Freeze-Dokuments je Version (relativ zur Repo-Wurzel).
FREEZE_DOC_TEMPLATE: Final = "docs/history/RELEASE-{version}-scope-freeze.md"
PATH_POLICY_PATH: Final = rpp.POLICY_PATH
PROVENANCE_SCHEMA: Final = 1
PROVENANCE_KIND: Final = "release-freeze-provenance"

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
# Das Freeze-Dokument ist menschenlesbar; maschinenlesbar bleiben nur Angaben,
# die bereits vor seinem Merge bekannt sind.

_DOC_VERSION_RE: Final = re.compile(r"(?m)^- \*\*Kandidatenversion:\*\* `(\d+\.\d+\.\d+)`")
#: Das Basis-Tag wird mit seinem vollen SHA eingefroren. Ein Tag ist verschiebbar –
#: nur der SHA legt das Vergleichsfenster unveraenderlich fest (Codex-Review #701).
_DOC_BASE_RE: Final = re.compile(
    r"(?m)^- \*\*Basis-Tag:\*\* `(v\d+\.\d+\.\d+)` \(= `([0-9a-f]{40})`\)"
)
_DOC_SCOPE_RE: Final = re.compile(r"(?m)^- \*\*Release-Scope:\*\* `([^`]+)`")
_DOC_POLICY_RE: Final = re.compile(
    r"(?m)^- \*\*Pfadpolicy:\*\* `release/path-policy\.json` \(Version `(\d+)`\)"
)

_PYPROJECT_VERSION_RE: Final = re.compile(r'(?m)^\s*version\s*=\s*"([^"]+)"')
_LICENSE_TITLE_RE: Final = re.compile(r"(?m)^#\s+.*\bbgremover\s+(\S+)\s*$")


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
    """Stabiler, vor dem Merge bekannter Kern des Freeze-Dokuments."""

    version: str
    base_tag: str
    base_sha: str
    scope: str
    policy_version: int


@dataclass(frozen=True)
class CommitRecord:
    """Automatisch abgeleitete Klassifikation eines First-Parent-Commits."""

    sha: str
    subject: str
    classification: str
    paths: tuple[rpp.PathClassification, ...]


def parse_freeze_doc(text: str) -> FreezeDoc:
    """Liest die verbindlichen Angaben aus dem Freeze-Dokument.

    Wirft ``DocFormatError``, wenn eine der Pflichtzeilen fehlt – ein
    unlesbares Freeze-Dokument darf nie als „geprueft" durchgehen.
    """
    version = _DOC_VERSION_RE.search(text)
    base = _DOC_BASE_RE.search(text)
    scope = _DOC_SCOPE_RE.search(text)
    policy = _DOC_POLICY_RE.search(text)
    missing = [
        name
        for name, match in (
            ("Kandidatenversion", version),
            ("Basis-Tag", base),
            ("Release-Scope", scope),
            ("Pfadpolicy", policy),
        )
        if match is None
    ]
    if missing:
        raise DocFormatError(
            "Pflichtzeilen im Freeze-Dokument fehlen bzw. weichen vom Format ab: "
            + ", ".join(missing)
        )
    assert version is not None and base is not None and scope is not None and policy is not None
    return FreezeDoc(
        version=version.group(1),
        base_tag=base.group(1),
        base_sha=base.group(2),
        scope=scope.group(1),
        policy_version=int(policy.group(1)),
    )


# ── Pfadklassifizierung ────────────────────────────────────────────────


def load_policy_at_rev(repo: Path, rev: str) -> rpp.PathPolicy:
    """Laedt die Pfadpolicy aus dem geprueften Commit, nie aus dem Arbeitsbaum."""
    return rpp.parse_policy(read_at_rev(repo, rev, PATH_POLICY_PATH))


def is_candidate_relevant(path: str, policy: rpp.PathPolicy | None = None) -> bool:
    """Ob *path* den Release-Kandidaten veraendert (gemeinsame #743-Policy)."""
    return rpp.is_candidate_relevant(path, policy or rpp.load_policy())


def candidate_relevant_paths(
    paths: Iterable[str], policy: rpp.PathPolicy | None = None
) -> tuple[str, ...]:
    """Die kandidatenrelevante Teilmenge von *paths*, Reihenfolge erhalten."""
    active = policy or rpp.load_policy()
    return tuple(path for path in paths if rpp.is_candidate_relevant(path, active))


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
    ``git mv bgremover/x.py RECOMMENDATIONS.md`` nur das *Ziel*. Der Commit
    saehe damit wie release-neutral aus, obwohl er Anwendungscode aus dem Baum
    entfernt. Ohne Erkennung erscheinen beide Seiten, und die Quelle bleibt
    kandidatenrelevant (Codex-Review #701).
    """
    parents = _git(repo, "rev-list", "--parents", "-n", "1", sha).split()[1:]
    if parents:
        out = _git(repo, "diff", "--no-renames", "--name-only", "-z", parents[0], sha)
    else:  # Root-Commit (im Repo praktisch nicht erreichbar, aber definiert)
        out = _git(repo, "show", "--no-renames", "--name-only", "-z", "--pretty=format:", sha)
    return tuple(path for path in out.split("\0") if path)


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


def derive_candidate(
    repo: Path, base: str, rev: str, policy: rpp.PathPolicy | None = None
) -> str | None:
    """Juengster inhaltlich kandidatenrelevanter Mainline-Commit (oder ``None``).

    Bewusst **first-parent**: ein unsquashed Merge zaehlt mit dem Baum, den er
    tatsaechlich in die Release-Linie eingebracht hat. Wuerde man alle Commits
    aufzaehlen, koennte ein Seitenzweig-Commit zum Kandidaten werden, dessen
    Aenderung nie ankam (Konfliktaufloesung, ``-s ours``, spaeterer Revert) –
    alle Folgepruefungen liefen dann gegen einen Baum, der nie getaggt wird.
    """
    active = policy or rpp.load_policy()
    for sha in commits_between(repo, base, rev, first_parent=True):
        if candidate_relevant_paths(changed_paths(repo, sha), active):
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


def classify_commits(
    repo: Path, base: str, head: str, policy: rpp.PathPolicy
) -> tuple[tuple[CommitRecord, ...], list[Finding]]:
    """Leitet Commit-Ledger und Pfadklassen vollstaendig aus Git ab.

    Unbekannte Pfade bleiben kandidatenrelevant, blockieren das Gate aber als
    ``unclassified-path``. So ist die sichere Wirkung definiert und zugleich
    eine bewusste Build-Input-Pruefung erzwungen.
    """
    findings: list[Finding] = []
    records: list[CommitRecord] = []
    window = tuple(reversed(commits_between(repo, base, head, first_parent=True)))
    for sha in window:
        paths = changed_paths(repo, sha)
        if not paths:
            findings.append(
                Finding(
                    _ERROR,
                    "unclassified-commit",
                    f"{sha} ({subject(repo, sha)}) hat keine ableitbare First-Parent-Baumaenderung",
                )
            )
        classified = tuple(rpp.classify_path(path, policy) for path in paths)
        unknown = tuple(item.path for item in classified if not item.explicit)
        if unknown:
            findings.append(
                Finding(
                    _ERROR,
                    "unclassified-path",
                    f"{sha} ({subject(repo, sha)}) enthält unbekannte Pfade: "
                    + ", ".join(unknown[:5]),
                )
            )
        commit_class = (
            rpp.CANDIDATE_RELEVANT
            if any(item.classification == rpp.CANDIDATE_RELEVANT for item in classified)
            else rpp.RELEASE_NEUTRAL
        )
        records.append(
            CommitRecord(
                sha=sha,
                subject=subject(repo, sha),
                classification=commit_class,
                paths=classified,
            )
        )
    if not window:
        findings.append(
            Finding(_ERROR, "empty-release-window", f"Keine Commits in {base}..{head[:12]}")
        )
    if not any(f.code in {"unclassified-commit", "unclassified-path"} for f in findings):
        relevant = sum(record.classification == rpp.CANDIDATE_RELEVANT for record in records)
        neutral = len(records) - relevant
        findings.append(
            Finding(
                _OK,
                "classification",
                f"{len(records)} Commits abgeleitet: {relevant} kandidatenrelevant, "
                f"{neutral} release-neutral",
            )
        )
    return tuple(records), findings


def _check_policy(repo: Path, doc: FreezeDoc, policy: rpp.PathPolicy) -> Finding:
    if doc.policy_version != policy.version:
        return Finding(
            _ERROR,
            "policy-version-mismatch",
            f"Freeze-Dokument nennt Policy {doc.policy_version}, "
            f"{PATH_POLICY_PATH} ist Version {policy.version}",
        )
    policy_at_base = _git(
        repo,
        "ls-tree",
        "--name-only",
        doc.base_sha,
        "--",
        PATH_POLICY_PATH,
    ).strip()
    if policy_at_base:
        base_policy = load_policy_at_rev(repo, doc.base_sha)
        if policy.digest != base_policy.digest and policy.version <= base_policy.version:
            return Finding(
                _ERROR,
                "policy-version-not-bumped",
                f"Pfadpolicy wurde seit der Basis geändert, Version {policy.version} "
                f"ist aber nicht größer als Basis-Version {base_policy.version}",
            )
    return Finding(
        _OK,
        "path-policy",
        f"Pfadpolicy {policy.version} ({policy.digest})",
    )


# ── Orchestrierung und Provenienz ──────────────────────────────────────


def _check_workflow_candidate(repo: Path, head: str) -> list[Finding]:
    """Bindet das Gate in Actions explizit an ``GITHUB_SHA`` und Run-IDs."""
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return []
    findings: list[Finding] = []
    github_sha = os.environ.get("GITHUB_SHA", "")
    if not github_sha:
        findings.append(
            Finding(_ERROR, "workflow-candidate-missing", "GITHUB_SHA fehlt in GitHub Actions")
        )
    elif rev_parse(repo, github_sha) != head:
        findings.append(
            Finding(
                _ERROR,
                "workflow-candidate-mismatch",
                f"geprüfter Laufkopf {head}, GITHUB_SHA {github_sha}",
            )
        )
    for name in ("GITHUB_REPOSITORY", "GITHUB_WORKFLOW", "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT"):
        if not os.environ.get(name):
            findings.append(
                Finding(_ERROR, "workflow-provenance-missing", f"{name} fehlt in GitHub Actions")
            )
    if not findings:
        findings.append(Finding(_OK, "workflow-candidate", f"Laufkopf = GITHUB_SHA = {head}"))
    return findings


def verify(repo: Path, rev: str) -> list[Finding]:
    """Alle Pruefungen fuer den Laufkopf *rev*; kein Pin/Nachtrag erforderlich."""
    head = rev_parse(repo, rev)
    findings: list[Finding] = []

    # Version und Dokument werden am geprueften Commit gelesen, nicht im Arbeitsbaum.
    version = version_at_rev(repo, head)
    if version is None:
        return [Finding(_ERROR, "pyproject-version-missing", "pyproject.toml ohne version")]
    doc = parse_freeze_doc(read_at_rev(repo, head, FREEZE_DOC_TEMPLATE.format(version=version)))
    policy = load_policy_at_rev(repo, head)
    findings += _check_workflow_candidate(repo, head)

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
    findings.append(_check_policy(repo, doc, policy))

    content_candidate = derive_candidate(repo, base, head, policy)
    if content_candidate is None:
        return [
            Finding(
                _ERROR,
                "no-candidate-commit",
                f"Kein kandidatenrelevanter Commit in {base}..{head[:12]}",
            )
        ]

    findings.append(
        Finding(_OK, "candidate", f"Geprüfter Kandidaten-/Laufkopf: {head} ({subject(repo, head)})")
    )
    findings.append(
        Finding(
            _OK,
            "content-candidate",
            f"Jüngster kandidatenrelevanter Commit: {content_candidate} "
            f"({subject(repo, content_candidate)})",
        )
    )
    findings += _check_versions(repo, head, doc)
    findings += _check_release_body(repo, head, doc)
    _records, classification_findings = classify_commits(repo, base, head, policy)
    findings += classification_findings
    return findings


def _workflow_metadata() -> dict[str, object | None]:
    def integer(name: str) -> int | None:
        value = os.environ.get(name)
        if not value:
            return None
        try:
            return int(value)
        except ValueError as exc:
            raise DocFormatError(f"{name} ist keine Ganzzahl: {value!r}") from exc

    return {
        "repository": os.environ.get("GITHUB_REPOSITORY"),
        "workflow": os.environ.get("GITHUB_WORKFLOW"),
        "run_id": integer("GITHUB_RUN_ID"),
        "run_attempt": integer("GITHUB_RUN_ATTEMPT"),
        "job": os.environ.get("GITHUB_JOB"),
        "ref": os.environ.get("GITHUB_REF"),
    }


def _record_to_json(record: CommitRecord) -> dict[str, object]:
    return {
        "sha": record.sha,
        "subject": record.subject,
        "classification": record.classification,
        "paths": [
            {
                "path": item.path,
                "classification": item.classification,
                "rule_id": item.rule_id,
                "explicit": item.explicit,
            }
            for item in record.paths
        ],
    }


def build_provenance(repo: Path, rev: str) -> dict[str, object]:
    """Erzeugt die rekonstruierbare, maschinenlesbare Freeze-Evidenz."""
    findings = verify(repo, rev)
    errors = [finding for finding in findings if finding.severity == _ERROR]
    if errors:
        raise DocFormatError("Provenienz bei fehlerhaftem Gate verweigert: " + errors[0].message)
    head = rev_parse(repo, rev)
    version = version_at_rev(repo, head)
    assert version is not None
    doc = parse_freeze_doc(read_at_rev(repo, head, FREEZE_DOC_TEMPLATE.format(version=version)))
    policy = load_policy_at_rev(repo, head)
    records, record_findings = classify_commits(repo, doc.base_sha, head, policy)
    if any(finding.severity == _ERROR for finding in record_findings):
        raise DocFormatError("Commit-Klassifikation ist nicht vollstaendig")
    content_candidate = derive_candidate(repo, doc.base_sha, head, policy)
    assert content_candidate is not None
    return {
        "schema": PROVENANCE_SCHEMA,
        "kind": PROVENANCE_KIND,
        "release": {
            "version": doc.version,
            "scope": doc.scope,
            "base_tag": doc.base_tag,
            "base_sha": doc.base_sha,
        },
        "candidate_sha": head,
        "content_candidate_sha": content_candidate,
        "policy": {
            "path": PATH_POLICY_PATH,
            "version": policy.version,
            "digest": policy.digest,
        },
        "commit_count": len(records),
        "commits": [_record_to_json(record) for record in records],
        "workflow": _workflow_metadata(),
    }


def write_provenance(path: Path, provenance: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def verify_provenance(repo: Path, data: object, expected_rev: str) -> list[Finding]:
    """Erkennt Manipulationen an Basis, Kandidat, Ledger und Policy-Bindung."""
    if not isinstance(data, dict):
        return [Finding(_ERROR, "provenance-format", "Provenienz-Wurzel ist kein Objekt")]
    evidence = cast(dict[str, Any], data)
    findings: list[Finding] = []
    if evidence.get("schema") != PROVENANCE_SCHEMA or evidence.get("kind") != PROVENANCE_KIND:
        findings.append(
            Finding(_ERROR, "provenance-format", "Schema oder Art der Provenienz ist unbekannt")
        )
        return findings
    expected_head = rev_parse(repo, expected_rev)
    if evidence.get("candidate_sha") != expected_head:
        findings.append(
            Finding(
                _ERROR,
                "provenance-candidate-mismatch",
                f"Evidenz nennt {evidence.get('candidate_sha')}, erwartet ist {expected_head}",
            )
        )
        return findings
    expected = build_provenance(repo, expected_head)
    comparisons = (
        ("release", "provenance-base-mismatch"),
        ("content_candidate_sha", "provenance-content-candidate-mismatch"),
        ("policy", "provenance-policy-mismatch"),
        ("commit_count", "provenance-commit-count-mismatch"),
        ("commits", "provenance-commit-list-mismatch"),
    )
    for key, code in comparisons:
        if evidence.get(key) != expected.get(key):
            findings.append(Finding(_ERROR, code, f"Provenienzfeld {key!r} ist manipuliert"))
    if not findings:
        findings.append(
            Finding(_OK, "provenance", f"Provenienz für {expected_head} vollständig rekonstruiert")
        )
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
        help="Nur den geprueften vollen 40-stelligen Laufkopf ausgeben",
    )
    parser.add_argument(
        "--output-provenance",
        type=Path,
        help="Nach erfolgreichem Gate maschinenlesbare Provenienz hier schreiben",
    )
    parser.add_argument(
        "--verify-provenance",
        type=Path,
        help="Vorhandene Provenienz gegen --rev (Default HEAD) rekonstruieren",
    )
    args = parser.parse_args(argv)

    try:
        if args.print_candidate:
            print(rev_parse(args.repo, args.rev))
            return 0
        if args.verify_provenance is not None:
            data = json.loads(args.verify_provenance.read_text(encoding="utf-8"))
            findings = verify_provenance(args.repo, data, args.rev)
        else:
            findings = verify(args.repo, args.rev)
            if args.output_provenance is not None and not any(
                finding.severity == _ERROR for finding in findings
            ):
                write_provenance(
                    args.output_provenance,
                    build_provenance(args.repo, args.rev),
                )
                findings.append(
                    Finding(
                        _OK,
                        "provenance-written",
                        f"Provenienz geschrieben: {args.output_provenance}",
                    )
                )
    except (GitError, DocFormatError, rpp.PolicyFormatError, ET.ParseError, OSError, json.JSONDecodeError) as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 2

    print(format_findings(findings))
    errors = sum(1 for finding in findings if finding.severity == _ERROR)
    warnings = sum(1 for finding in findings if finding.severity == _WARNING)
    print(f"\n{errors} Fehler, {warnings} Warnung(en).")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
