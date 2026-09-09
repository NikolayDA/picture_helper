#!/usr/bin/env python3
"""Vorabprüfung der Drift-Pflichten eines PRs (#1041).

``make pr-check`` prüft, sagt aber nicht vorab, **welche** Pflicht der eigene
Diff auslöst. Drei der Pflichten haben zudem versetzte Wächter, die erst nach
dem Commit (``tests/test_anleitung_pdf_sync.py``) oder erst in der PR-CI
(``license-check.yml``, ``release-freeze-check``) anschlagen – man erfährt sie
also frühestens eine Runde zu spät.

Dieses Skript benennt sie aus dem Diff gegen ``origin/main``: Merge-Basis bis
``HEAD`` **plus Arbeitsbaum**, und dort staged, unstaged *und untracked* –
sonst fehlte ausgerechnet die neue Datei, die eine Policy-Lücke aufreißt.
Alle Pfadlisten laufen NUL-getrennt (``-z``) und mit ``--no-renames`` wie im
Freeze-Gate: Mit Umbenennungserkennung meldete git für ``git mv a b`` nur das
Ziel, und die Quelle verschwände aus der Klassifikation. ``-z`` ist kein
Zierrat, sondern Pflicht – im Repository liegt mit
``design/Prototyp A - Geführter Workflow.dc.html`` ein Pfad mit Leerzeichen
und Umlaut, dessen zeilenweise Ausgabe von ``core.quotepath`` abhinge.

Es entscheidet **nichts** und ersetzt ``make pr-check`` nicht: Fehler sind
nachweisbare Verstöße (eine Pflicht ist fällig und nicht erfüllt), Hinweise
sind Fälle, die eine menschliche Beurteilung brauchen – nicht jede Änderung an
``bgremover/`` ist nutzersichtbar. Netzfrei: Es ruft bewusst kein ``git
fetch`` auf, druckt aber Basis-Ref und aufgelösten SHA, damit ein veralteter
lokaler Stand sichtbar wird statt still zu wirken.

Exit-Codes: 0 (keine Fehler), 1 (mindestens ein Fehler), 2 (nicht lauffähig,
etwa ein unbekannter Basis-Ref).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, TextIO

try:  # Dateiaufruf: ``python scripts/pr_ready.py``
    import release_path_policy as rpp
except ModuleNotFoundError:  # Import als ``scripts.pr_ready`` in Tests
    from scripts import release_path_policy as rpp

_REPO_ROOT: Final = Path(__file__).resolve().parent.parent

DEFAULT_BASE: Final = "origin/main"

#: Doku-Familien mit je fünf Übersetzungen. Handgepflegte Kopie von
#: ``tests/test_i18n_docs.py`` – das Produktionsskript importiert kein
#: Testmodul; ``tests/test_pr_ready.py`` hält beide Mengen gegeneinander.
DOC_NAMES: Final = (
    "README.md",
    "LICENSES.md",
    "INSTALL_LINUX.md",
    "CHANGELOG.md",
    "INSTALL_MAC.md",
    "RESOURCES.md",
    "ANLEITUNG.md",
)
LANGUAGES: Final = ("en", "es", "fr", "uk", "zh")

#: Genau die ``[project]``-Felder, die ``scripts/generate_license_report.py``
#: liest. ``[build-system]`` und ``[tool.*]`` sind **keine** Eingabe des
#: Reports – eine reine Werkzeugänderung darf keinen Snapshot-Fehler erzeugen.
LICENSE_PROJECT_FIELDS: Final = (
    "name",
    "version",
    "license",
    "dependencies",
    "optional-dependencies",
)
CONSTRAINTS_PATH: Final = "requirements/constraints.txt"
PYPROJECT_PATH: Final = "pyproject.toml"
LICENSES_PATH: Final = "LICENSES.md"

ANLEITUNG_SOURCES: Final = ("ANLEITUNG.md", "scripts/generate_anleitung_pdf.py")
ANLEITUNG_PDF: Final = "ANLEITUNG.pdf"

#: Ausgeliefertes Verhalten: Anwendungscode und die Eingaben, aus denen die
#: Pakete gebaut bzw. gestartet werden. Eine Änderung hier *kann* nutzersichtbar
#: sein – ob sie es ist, entscheidet ein Mensch.
SHIPPED_PREFIXES: Final = ("bgremover/", "packaging/")
SHIPPED_FILES: Final = ("create_BgRemover_app.sh", "BgRemover.command")

ERROR: Final = "FEHLER"
NOTE: Final = "HINWEIS"

#: Mehr unbekannte Pfade werden gekürzt aufgezählt (wie im Freeze-Gate).
_MAX_LISTED: Final = 5


class PrReadyError(Exception):
    """Das Skript kann nicht laufen (etwa: Basis-Ref unbekannt)."""

    def __init__(self, message: str, recipe: Sequence[str] = ()) -> None:
        super().__init__(message)
        self.recipe = tuple(recipe)


@dataclass(frozen=True)
class Finding:
    """Ein Befund: ``level`` ist ``FEHLER`` oder ``HINWEIS``."""

    level: str
    code: str
    message: str
    recipe: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ChangeSet:
    """Die geänderten Pfade, getrennt nach Herkunft (für die Ausgabe)."""

    base_ref: str
    base_sha: str
    merge_base: str
    committed: tuple[str, ...]
    worktree: tuple[str, ...]
    untracked: tuple[str, ...]

    @property
    def paths(self) -> frozenset[str]:
        return frozenset(self.committed) | frozenset(self.worktree) | frozenset(self.untracked)


def _git(repo: Path, *args: str) -> str:
    """Rohe Ausgabe – bewusst **ohne** ``strip``.

    Diese Funktion bedient nur NUL-getrennte Listen, und ``strip`` liefe über
    die **gesamte** Ausgabe statt über die Einträge. Betroffen ist der erste:
    Ein unter Linux völlig legales ``" führend.txt"`` verlöre sein
    Leerzeichen und würde gegen einen anderen Pfad klassifiziert – dieselbe
    Fehlerklasse, gegen die ``-z`` hier antritt (Review-Befund PR #1065). Das
    Listen*ende* ist dagegen unkritisch: git terminiert auch den letzten
    Eintrag mit NUL, und der schirmt abschließende Leerzeichen ab (gemessen).
    ``_split_nul`` wirft leere Einträge ohnehin weg.
    """
    result = subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    )
    return result.stdout


def _git_optional(repo: Path, *args: str) -> str | None:
    """Wie ``_git``, gibt bei einem Fehlschlag aber ``None`` statt zu werfen."""
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return result.stdout


def _split_nul(raw: str | None) -> tuple[str, ...]:
    if not raw:
        return ()
    return tuple(entry for entry in raw.split("\0") if entry)


def _diff_paths(repo: Path, *revisions: str) -> tuple[str, ...]:
    return _split_nul(_git(repo, "diff", "--no-renames", "--name-only", "-z", *revisions))


def resolve_base(repo: Path, base_ref: str) -> str:
    """Löst *base_ref* zu einem Commit-SHA auf.

    Ein fehlender Ref ist der häufigste Startfehler (frischer Klon, nie
    gefetchtes ``origin/main``) und bekommt deshalb ein Rezept statt einer
    git-Fehlermeldung.
    """
    sha = _git_optional(repo, "rev-parse", "--verify", "--quiet", f"{base_ref}^{{commit}}")
    if sha is None or not sha.strip():
        remote, _, branch = base_ref.partition("/")
        recipe = [f"git fetch {remote} {branch}"] if branch else ["git fetch --all"]
        raise PrReadyError(
            f"Basis-Ref {base_ref!r} ist lokal nicht bekannt oder zeigt auf keinen Commit.",
            recipe,
        )
    return sha.strip()


def collect_changes(repo: Path, base_ref: str) -> ChangeSet:
    """Sammelt Commits seit der Merge-Basis und den gesamten Arbeitsbaum.

    Jeder git-Fehlschlag wird zu ``PrReadyError``: Ein ``--repo`` ohne
    Repository und ein Repository ohne Commits (ungeborener ``HEAD``, an dem
    ``git diff HEAD`` scheitert) endeten sonst im Traceback statt im
    zugesicherten Exit 2 – der Docstring verspricht „nicht lauffähig", nicht
    „Stacktrace" (Review-Befund PR #1065).
    """
    if not (repo / ".git").exists():
        raise PrReadyError(
            f"{repo} ist kein git-Repository (kein .git).",
            ("--repo auf die Wurzel eines Checkouts zeigen lassen",),
        )
    base_sha = resolve_base(repo, base_ref)
    merge_base = _git_optional(repo, "merge-base", base_sha, "HEAD")
    # Ohne gemeinsamen Vorfahren (unverbundene Historien) ist der Basis-Commit
    # selbst der beste Vergleichspunkt – besser ein zu weiter Diff als keiner.
    resolved_base = merge_base.strip() if merge_base and merge_base.strip() else base_sha
    try:
        return ChangeSet(
            base_ref=base_ref,
            base_sha=base_sha,
            merge_base=resolved_base,
            committed=_diff_paths(repo, resolved_base, "HEAD"),
            # Ein einzelnes ``git diff HEAD`` deckt staged und unstaged gemeinsam ab.
            worktree=_diff_paths(repo, "HEAD"),
            untracked=_split_nul(_git(repo, "ls-files", "--others", "--exclude-standard", "-z")),
        )
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or "").strip().splitlines()
        raise PrReadyError(
            f"git konnte den Diff in {repo} nicht lesen"
            + (f": {detail[-1]}" if detail else "."),
            ("Repository mit mindestens einem Commit und lesbarem HEAD nötig",),
        ) from error


def toml_parser_available() -> bool:
    """Ob überhaupt ein TOML-Parser bereitsteht (``tomllib`` bzw. ``tomli``)."""
    try:
        import tomllib  # noqa: F401
    except ModuleNotFoundError:  # pragma: no cover - nur unter Python 3.10
        try:
            import tomli  # noqa: F401
        except ModuleNotFoundError:
            return False
    return True


def _load_toml(text: str) -> dict[str, Any] | None:
    """TOML lesen, sofern es lesbar ist.

    ``None`` steht für „nicht entscheidbar" und hat **zwei** Ursachen:
    ``tomllib`` gibt es erst ab Python 3.11 (das Projekt unterstützt 3.10),
    und der gelesene Text kann ungültig sein. Der zweite Fall ist hier der
    wahrscheinlichere: Gelesen wird ``pyproject.toml`` aus dem **Arbeitsbaum**,
    und der ist der ausdrückliche Normalfall dieses Skripts – eine halb
    editierte Datei beendete den Lauf sonst mit einem Traceback statt mit dem
    zugesicherten Verhalten (Review-Befund PR #1065). Der Aufrufer stuft in
    beiden Fällen auf einen Hinweis herab.
    """
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover - nur unter Python 3.10
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ModuleNotFoundError:
            return None
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return None


def _project_license_fields(text: str) -> dict[str, Any] | None:
    data = _load_toml(text)
    if data is None:
        return None
    project = data.get("project", {})
    if not isinstance(project, dict):
        return {}
    return {name: project.get(name) for name in LICENSE_PROJECT_FIELDS}


def license_relevant_pyproject_fields(repo: Path, changes: ChangeSet) -> tuple[str, ...] | None:
    """Welche der fünf Lizenz-Felder sich geändert haben.

    ``None`` heißt „nicht entscheidbar" (kein TOML-Parser). Ein leeres Tupel
    heißt „nur Werkzeug-/Build-Abschnitte berührt" – das ist der Fall, der
    keinen Snapshot-Fehler erzeugen darf.
    """
    if PYPROJECT_PATH not in changes.paths:
        return ()
    previous = _git_optional(repo, "show", f"{changes.merge_base}:{PYPROJECT_PATH}")
    current_path = repo / PYPROJECT_PATH
    current_text = current_path.read_text(encoding="utf-8") if current_path.is_file() else ""
    before = _project_license_fields(previous) if previous is not None else {}
    after = _project_license_fields(current_text) if current_text else {}
    if before is None or after is None:
        return None
    return tuple(
        name for name in LICENSE_PROJECT_FIELDS if before.get(name) != after.get(name)
    )


def _rule_changelog(paths: frozenset[str]) -> list[Finding]:
    touched = sorted(
        path
        for path in paths
        if path.startswith(SHIPPED_PREFIXES) or path in SHIPPED_FILES
    )
    if not touched or "CHANGELOG.md" in paths:
        return []
    return [
        Finding(
            NOTE,
            "changelog",
            "Ausgeliefertes Verhalten berührt, CHANGELOG.md nicht: "
            f"{_join(touched)}. Nutzersichtbar?",
            (
                "wenn ja: Abschnitt [Unreleased] in CHANGELOG.md ergänzen",
                "und in allen fünf Fassungen unter docs/i18n/<lang>/CHANGELOG.md",
            ),
        )
    ]


def _rule_i18n(paths: frozenset[str]) -> list[Finding]:
    findings: list[Finding] = []
    for name in DOC_NAMES:
        if name not in paths:
            continue
        missing = [
            f"docs/i18n/{language}/{name}"
            for language in LANGUAGES
            if f"docs/i18n/{language}/{name}" not in paths
        ]
        if missing:
            findings.append(
                Finding(
                    ERROR,
                    "i18n",
                    f"{name} geändert, {len(missing)} Übersetzung(en) nicht mitgeändert.",
                    tuple(missing),
                )
            )
    return findings


def _rule_anleitung_pdf(paths: frozenset[str]) -> list[Finding]:
    touched = sorted(path for path in ANLEITUNG_SOURCES if path in paths)
    if not touched or ANLEITUNG_PDF in paths:
        return []
    return [
        Finding(
            ERROR,
            "anleitung-pdf",
            f"{_join(touched)} geändert, {ANLEITUNG_PDF} nicht neu erzeugt.",
            (
                'pip install -e ".[docs]"',
                "python scripts/generate_anleitung_pdf.py",
            ),
        )
    ]


def _rule_license_snapshot(repo: Path, changes: ChangeSet) -> list[Finding]:
    """Zwei Auslöser, die getrennt entscheidbar sind.

    ``requirements/constraints.txt`` ist ein reiner Pfadvergleich und damit
    **immer** entscheidbar; nur der ``pyproject.toml``-Teil braucht einen
    TOML-Parser. Beides zusammen abzubrechen, sobald der Parser fehlt, ließe
    genau den häufigen Fall durchgehen – ein Dependency-Bump berührt
    typischerweise beide Dateien, und ohne ``tomli`` (Python 3.10, die
    Mindestversion) wäre der Lauf grün, obwohl die Pflicht nachweisbar fällig
    ist (Review-Befund PR #1065).
    """
    paths = changes.paths
    findings: list[Finding] = []
    reasons: list[str] = []
    if CONSTRAINTS_PATH in paths:
        reasons.append(CONSTRAINTS_PATH)
    fields = license_relevant_pyproject_fields(repo, changes)
    if fields is None:
        cause = (
            "ungültiges TOML"
            if toml_parser_available()
            else "kein TOML-Parser (Python 3.10 ohne tomli)"
        )
        findings.append(
            Finding(
                NOTE,
                "lizenz-snapshot",
                f"{PYPROJECT_PATH} geändert, aber nicht semantisch prüfbar "
                f"({cause}). license-check.yml entscheidet.",
                (
                    "pyproject.toml auf gültiges TOML prüfen"
                    if toml_parser_available()
                    else "optional: pip install tomli",
                ),
            )
        )
    elif fields:
        reasons.append(f"{PYPROJECT_PATH} [project]: {_join(list(fields))}")
    if reasons and LICENSES_PATH not in paths:
        findings.append(
            Finding(
                ERROR,
                "lizenz-snapshot",
                f"Lizenzrelevante Eingabe geändert ({_join(reasons)}), {LICENSES_PATH} nicht.",
                (
                    "in einem frischen venv wie license-check.yml (Python 3.12):",
                    f'pip install --constraint {CONSTRAINTS_PATH} ".[ai,test]"',
                    "python scripts/generate_license_report.py "
                    f"--report {LICENSES_PATH} --all-langs",
                ),
            )
        )
    return findings


def _rule_path_policy(repo: Path, paths: frozenset[str]) -> list[Finding]:
    """Klassifiziert gegen die Policy **des geprüften** Repositories.

    ``rpp.load_policy()`` nähme die Vorgabe – also immer die Policy dieses
    Checkouts – während alle anderen Regeln aus ``--repo`` lesen. Bei einem
    zweiten Worktree klassifizierte das fremde Pfade still gegen die hiesigen
    Regeln (Review-Befund PR #1065). Fehlt dort eine Policy, entfällt die
    Regel mit Hinweis statt mit einem Abbruch.
    """
    if not paths:
        return []
    policy_path = repo / rpp.POLICY_PATH
    if not policy_path.is_file():
        return [
            Finding(
                NOTE,
                "pfadpolicy",
                f"{rpp.POLICY_PATH} fehlt in diesem Repository – Pfade bleiben "
                "unklassifiziert.",
            )
        ]
    policy = rpp.load_policy(policy_path)
    unknown = sorted(
        path for path in paths if not rpp.classify_path(path, policy).explicit
    )
    if not unknown:
        return []
    level = ERROR if policy.unknown_paths_block else NOTE
    shown = unknown[:_MAX_LISTED]
    rest = len(unknown) - len(shown)
    listed = _join(shown) + (f" (+{rest} weitere)" if rest else "")
    return [
        Finding(
            level,
            "pfadpolicy",
            f"{len(unknown)} Pfad(e) kennt release/path-policy.json nicht: {listed}. "
            "Sie gelten als kandidatenrelevant.",
            (
                "bewusst release-neutral? Eintrag in release/path-policy.json ergänzen",
                "sonst nichts zu tun – release-freeze-check meldet sie als Warnung",
            ),
        )
    ]


def _join(items: Iterable[str]) -> str:
    return ", ".join(items)


def evaluate(repo: Path, changes: ChangeSet) -> list[Finding]:
    """Alle Regeln in stabiler Reihenfolge; Fehler vor Hinweisen."""
    findings = [
        *_rule_i18n(changes.paths),
        *_rule_anleitung_pdf(changes.paths),
        *_rule_license_snapshot(repo, changes),
        *_rule_path_policy(repo, changes.paths),
        *_rule_changelog(changes.paths),
    ]
    return sorted(findings, key=lambda item: (item.level != ERROR, item.code, item.message))


def report(changes: ChangeSet, findings: Sequence[Finding], stream: TextIO) -> None:
    print(
        f"[pr-ready] Basis {changes.base_ref} = {changes.base_sha[:12]}"
        f" · Merge-Basis {changes.merge_base[:12]}",
        file=stream,
    )
    print(
        f"[pr-ready] {len(changes.committed)} Pfad(e) aus Commits,"
        f" {len(changes.worktree)} im Arbeitsbaum,"
        f" {len(changes.untracked)} untracked",
        file=stream,
    )
    if not findings:
        print("ok      keine Drift-Pflicht fällig", file=stream)
        return
    for finding in findings:
        print(f"{finding.level:<7} [{finding.code}] {finding.message}", file=stream)
        for line in finding.recipe:
            print(f"        → {line}", file=stream)
    errors = sum(1 for finding in findings if finding.level == ERROR)
    notes = len(findings) - errors
    print(f"\n{errors} Fehler, {notes} Hinweis(e).", file=stream)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(
        "--base",
        default=DEFAULT_BASE,
        help=f"Vergleichsstand (Vorgabe: {DEFAULT_BASE}); es wird nie gefetcht.",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=_REPO_ROOT,
        help="Repository-Wurzel (Vorgabe: dieses Repository).",
    )
    args = parser.parse_args(argv)

    try:
        changes = collect_changes(args.repo, args.base)
    except PrReadyError as error:
        print(f"{ERROR}  [start] {error}", file=sys.stdout)
        for line in error.recipe:
            print(f"        → {line}", file=sys.stdout)
        return 2

    findings = evaluate(args.repo, changes)
    report(changes, findings, sys.stdout)
    return 1 if any(finding.level == ERROR for finding in findings) else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
