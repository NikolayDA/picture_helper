#!/usr/bin/env python3
"""Installationsprovenienz von ``bgremover`` gegen den Checkout pruefen (#1031).

Der SessionStart-Hook (``.claude/hooks/session-start.sh``) prueft in einer
Folge-Session mit gecachtem Container, ob die Umgebung schon steht, und
ueberspringt dann ``pip install -e ".[test]"``. Bis #1031 fragte er dafuer
nur, **dass** eine Distribution ``bgremover`` existiert – nicht **welche**.
``make pr-check`` installiert bewusst nicht-editable (Makefile, Ziel
``install-test``); dieser Zustand ueberlebt die Session, und der Kurzschluss
der naechsten zementierte ihn: Jeder Test, der Repo-Code als Subprozess ueber
den **Dateipfad** startet (``sys.path[0]`` = Skriptverzeichnis, nicht die
Repo-Wurzel), mass danach eine Kopie aus einem fremden Commit, waehrend
In-Prozess-Tests ueber den von pytest eingetragenen Checkout unauffaellig
blieben. Der gefaehrliche Fall ist der **gruene** Subprozess-Test auf altem
Code.

Zwei Pruefungen, beide fail-closed:

1. **Metadaten-Provenienz.** Jede auffindbare Distribution ``bgremover`` muss
   ein editierbarer Link auf genau diesen Checkout sein: PEP 660 ueber
   ``direct_url.json`` (``dir_info.editable == true`` und eine ``file:``-URL,
   die aufgeloest die Repo-Wurzel ist) oder Legacy-editable ueber ein
   Distributions-Root (``locate_file("")``), das die Repo-Wurzel ist. Eine
   Wheel-/nicht-editable Installation, ein editierbarer Link auf einen anderen
   Checkout, eine fehlende Distribution und eine veraltete Kopie **neben**
   einem gueltigen Link schlagen fehl.
2. **Neutraler Import (Postcondition).** ``import bgremover`` aus einem leeren
   temporaeren Arbeitsverzeichnis muss ``bgremover/__init__.py`` **dieses**
   Checkouts liefern – genau die Suchpfad-Situation eines per Dateipfad
   gestarteten Skripts.

Der Paketimport im Prozess des Skripts selbst ist bewusst **kein** Beleg: Bei
``python -c`` aus der Repo-Wurzel steht das Arbeitsverzeichnis vorn auf
``sys.path`` und der Import traefe den Checkout, selbst wenn in
``site-packages`` eine veraltete Kopie liegt. Dieses Skript wird deshalb ueber
seinen Dateipfad gestartet (``sys.path[0]`` = ``scripts/``) und wertet nur
Distributions-Metadaten aus; ein verwaistes ``bgremover.egg-info`` in der
Repo-Wurzel taeuscht es dadurch ebenfalls nicht.

Nur Standardbibliothek, Qt-frei: Das Skript laeuft **vor** jeder Installation
und darf nichts voraussetzen, was die Installation erst bringt.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from urllib.parse import unquote, urlsplit
from urllib.request import url2pathname

REPO_ROOT = Path(__file__).resolve().parent.parent
DISTRIBUTION_NAME = "bgremover"
LOG_PREFIX = "[install-provenance]"

#: Provenienzklassen (``Finding.kind``). Die beiden ersten sind gueltig.
KIND_PEP660_EDITABLE = "pep660-editable"
KIND_LEGACY_EDITABLE = "legacy-editable"
KIND_FOREIGN_EDITABLE = "foreign-editable"
KIND_NON_EDITABLE = "non-editable"
KIND_MISSING = "missing"
KIND_INVALID_METADATA = "invalid-metadata"
VALID_KINDS: frozenset[str] = frozenset({KIND_PEP660_EDITABLE, KIND_LEGACY_EDITABLE})


@dataclass(frozen=True)
class Finding:
    """Ein Befund je Distribution bzw. je Pruefung."""

    ok: bool
    kind: str
    detail: str


@dataclass(frozen=True)
class ProvenanceReport:
    """Gesamtergebnis: Metadaten-Befunde plus (optional) Import-Postcondition."""

    metadata: tuple[Finding, ...]
    neutral_import: Finding | None

    @property
    def ok(self) -> bool:
        if not self.metadata or not all(item.ok for item in self.metadata):
            return False
        return self.neutral_import is None or self.neutral_import.ok

    def lines(self) -> list[str]:
        out = [
            f"{LOG_PREFIX} {'ok' if item.ok else 'FEHLER'}: {item.kind} – {item.detail}"
            for item in self.metadata
        ]
        if self.neutral_import is not None:
            status = "ok" if self.neutral_import.ok else "FEHLER"
            out.append(
                f"{LOG_PREFIX} {status}: {self.neutral_import.kind} – {self.neutral_import.detail}"
            )
        return out


def _normalise_name(name: str) -> str:
    """PEP-503-Normalisierung, damit ``BgRemover``/``bgremover`` gleich zaehlen."""
    return "".join("-" if ch in "-_." else ch.lower() for ch in name)


def _same_path(candidate: Path, repo_root: Path) -> bool:
    try:
        return candidate.resolve() == repo_root.resolve()
    except OSError:
        return False


def _file_url_to_path(url: str) -> Path | None:
    """``file:``-URL aus ``direct_url.json`` in einen lokalen Pfad ueberfuehren.

    Nur lokale ``file:``-URLs (ohne fremden Host) gelten; alles andere ist
    keine Verknuepfung mit einem Checkout.
    """
    parts = urlsplit(url)
    if parts.scheme != "file" or parts.netloc not in ("", "localhost"):
        return None
    local = url2pathname(unquote(parts.path))
    if not local:
        return None
    return Path(local)


def find_distributions(
    name: str = DISTRIBUTION_NAME, search_path: Sequence[str] | None = None
) -> list[metadata.Distribution]:
    """Alle auffindbaren Distributionen *name* – dedupliziert je Metadatenpfad.

    ``search_path`` ersetzt ``sys.path`` (Testhaken); ohne Angabe gilt der
    Suchpfad des laufenden Interpreters. Ein Verzeichnis, das mehrfach auf dem
    Suchpfad steht, liefert dieselbe Distribution mehrfach – das ist kein
    zweiter Fund.
    """
    wanted = _normalise_name(name)
    found: list[metadata.Distribution] = []
    seen: set[str] = set()
    iterator: Iterable[metadata.Distribution] = (
        metadata.distributions()
        if search_path is None
        else metadata.distributions(path=list(search_path))
    )
    for dist in iterator:
        try:
            # Verwaiste ``~*.dist-info``-Reste ohne METADATA sind in
            # Containern real; sie sind kein Fund und kein Abbruchgrund.
            dist_name = dist.metadata["Name"] if dist.metadata else None
        except Exception:  # noqa: BLE001 -- unlesbare Metadaten überspringen
            continue
        if not dist_name or _normalise_name(dist_name) != wanted:
            continue
        key = str(Path(str(dist.locate_file(""))).resolve()) + "|" + str(dist.version)
        info_dir = getattr(dist, "_path", None)
        if info_dir is not None:
            key = str(Path(str(info_dir)).resolve())
        if key in seen:
            continue
        seen.add(key)
        found.append(dist)
    return found


def classify_distribution(dist: metadata.Distribution, repo_root: Path = REPO_ROOT) -> Finding:
    """Eine Distribution gegen die Repo-Wurzel einordnen."""
    version = dist.version
    raw = dist.read_text("direct_url.json")
    if raw is not None:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            return Finding(
                False, KIND_INVALID_METADATA, f"direct_url.json unlesbar ({exc}), Version {version}"
            )
        if not isinstance(data, dict):
            return Finding(False, KIND_INVALID_METADATA, "direct_url.json ist kein Objekt")
        dir_info = data.get("dir_info")
        editable = isinstance(dir_info, dict) and dir_info.get("editable") is True
        url = data.get("url")
        if not editable:
            return Finding(
                False,
                KIND_NON_EDITABLE,
                f"nicht-editable Installation (Version {version}, Quelle {url!r}) – "
                "ein Schnappschuss statt des Checkouts",
            )
        target = _file_url_to_path(str(url)) if isinstance(url, str) else None
        if target is None:
            return Finding(
                False, KIND_INVALID_METADATA, f"editable ohne lokale file:-URL ({url!r})"
            )
        if _same_path(target, repo_root):
            return Finding(
                True, KIND_PEP660_EDITABLE, f"PEP-660-editable auf {repo_root} (Version {version})"
            )
        return Finding(
            False,
            KIND_FOREIGN_EDITABLE,
            f"editable auf fremden Checkout {target} statt {repo_root} (Version {version})",
        )
    # Ohne direct_url.json bleibt nur Legacy-editable (setup.py develop /
    # egg-info im Checkout) als gueltiger Fall: Das Distributions-Root muss die
    # Repo-Wurzel sein. Ein Wheel in site-packages faellt hier durch.
    root = Path(str(dist.locate_file("")))
    if _same_path(root, repo_root):
        return Finding(
            True,
            KIND_LEGACY_EDITABLE,
            f"Legacy-editable, Distributions-Root {repo_root} (Version {version})",
        )
    return Finding(
        False,
        KIND_NON_EDITABLE,
        f"Installation ohne direct_url.json, Distributions-Root {root} (Version {version}) – "
        f"kein editierbarer Link auf den Checkout {repo_root} (Wheel-Install oder "
        "Legacy-Link auf einen anderen Checkout)",
    )


def check_metadata_provenance(
    repo_root: Path = REPO_ROOT,
    name: str = DISTRIBUTION_NAME,
    search_path: Sequence[str] | None = None,
) -> tuple[Finding, ...]:
    """Alle Distributionen *name* einordnen; keine gefundene ist ein Befund."""
    dists = find_distributions(name, search_path)
    if not dists:
        return (Finding(False, KIND_MISSING, f"keine Distribution {name!r} auffindbar"),)
    findings = tuple(classify_distribution(dist, repo_root) for dist in dists)
    if (
        len(findings) > 1
        and any(item.ok for item in findings)
        and not all(item.ok for item in findings)
    ):
        # Ein gueltiger Link neben einer Kopie: Der Import entscheidet nach
        # sys.path-Reihenfolge, nicht nach Gueltigkeit – daher fail-closed.
        findings = findings + (
            Finding(
                False,
                KIND_INVALID_METADATA,
                f"{len(findings)} Distributionen {name!r} nebeneinander – "
                "welche der Import trifft, entscheidet die Suchpfad-Reihenfolge",
            ),
        )
    return findings


def check_neutral_import(
    repo_root: Path = REPO_ROOT,
    name: str = DISTRIBUTION_NAME,
    python: str = sys.executable,
    env: Mapping[str, str] | None = None,
    timeout: float = 60.0,
) -> Finding:
    """Postcondition: Import aus leerem Arbeitsverzeichnis trifft den Checkout.

    ``python -c`` setzt das Arbeitsverzeichnis vorn auf ``sys.path``; ein
    leeres Temp-Verzeichnis stellt damit exakt die Lage eines per Dateipfad
    gestarteten Skripts nach, dessen ``sys.path[0]`` nicht die Repo-Wurzel ist.
    """
    expected = (repo_root / name / "__init__.py").resolve()
    code = f"import pathlib, {name}; print(pathlib.Path({name}.__file__).resolve())"
    with tempfile.TemporaryDirectory(prefix="bgremover-provenance-") as neutral:
        try:
            proc = subprocess.run(
                [python, "-c", code],
                cwd=neutral,
                env=None if env is None else dict(env),
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return Finding(False, "neutral-import", f"Import nicht ausfuehrbar: {exc}")
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip().splitlines()
        tail = stderr[-1] if stderr else "(kein stderr)"
        return Finding(
            False,
            "neutral-import",
            f"import {name} aus neutralem Arbeitsverzeichnis scheitert: {tail}",
        )
    imported = Path(proc.stdout.strip())
    if imported == expected:
        return Finding(True, "neutral-import", f"import {name} aus neutralem cwd trifft {expected}")
    return Finding(
        False,
        "neutral-import",
        f"import {name} aus neutralem cwd trifft {imported}, erwartet {expected}",
    )


def run(
    repo_root: Path = REPO_ROOT,
    name: str = DISTRIBUTION_NAME,
    search_path: Sequence[str] | None = None,
    python: str = sys.executable,
    with_import: bool = True,
) -> ProvenanceReport:
    """Beide Pruefungen; die Postcondition laeuft nur, wenn die Metadaten stimmen.

    Ein Import auf einer bereits als ungueltig erkannten Installation braechte
    keinen zusaetzlichen Befund, koennte aber (fremder Code) Seiteneffekte
    haben.
    """
    findings = check_metadata_provenance(repo_root, name, search_path)
    neutral: Finding | None = None
    if with_import and all(item.ok for item in findings):
        neutral = check_neutral_import(repo_root, name, python)
    return ProvenanceReport(metadata=findings, neutral_import=neutral)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Checkout, auf den die Installation zeigen muss (Default: Repo dieses Skripts)",
    )
    parser.add_argument(
        "--distribution", default=DISTRIBUTION_NAME, help="Distributionsname (Default: bgremover)"
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Interpreter fuer die Import-Postcondition (Default: der laufende)",
    )
    parser.add_argument(
        "--search-path",
        action="append",
        default=None,
        metavar="DIR",
        help="Metadaten nur in diesen Verzeichnissen suchen statt in sys.path (Testhaken)",
    )
    parser.add_argument(
        "--skip-import",
        action="store_true",
        help="nur die Metadaten pruefen, keine Import-Postcondition",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = run(
        repo_root=args.repo_root,
        name=args.distribution,
        search_path=args.search_path,
        python=args.python,
        with_import=not args.skip_import,
    )
    for line in report.lines():
        print(line)
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
