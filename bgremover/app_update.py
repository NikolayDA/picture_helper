"""Qt-freie Update-Check-Kernlogik (#564, Teil von Epic #563).

Prüft über die GitHub-Releases-API, ob eine neuere Version von BgRemover
verfügbar ist, als aktuell läuft (`bgremover._version.get_version()`). Nutzt
bewusst nur `urllib.request` aus der Stdlib – kein neuer Pflicht-Abhängigkeits-
Zugriff für ein rein optionales Feature. Jeder Netzwerk-/Parsing-Fehler wird
als :data:`UpdateStatus.CHECK_FAILED` zurückgegeben; es verlässt **niemals**
eine Exception die öffentliche Funktion `check_for_update`.

Lädt zu keinem Zeitpunkt Release-Assets/Binärdateien herunter – nur die
JSON-Metadaten des `/releases/latest`-Endpunkts (`tag_name`, `html_url`).
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from enum import Enum, auto

_RELEASES_API_URL = "https://api.github.com/repos/NikolayDA/picture_helper/releases/latest"
_REQUEST_HEADERS = {"Accept": "application/vnd.github+json"}

# `vX.Y.Z` optional mit Vorabversions-Suffix (z. B. `-rc1`, `-beta.2`).
_VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.]+))?$")


class UpdateStatus(Enum):
    """Ergebnis eines Update-Checks."""

    UP_TO_DATE = auto()
    UPDATE_AVAILABLE = auto()
    CHECK_FAILED = auto()


@dataclass(frozen=True)
class UpdateCheckResult:
    """Strukturiertes Ergebnis von :func:`check_for_update`."""

    status: UpdateStatus
    latest_version: str | None = None
    release_url: str | None = None
    error: str | None = None


def _parse_version(raw: str) -> tuple[tuple[int, int, int], str]:
    """Zerlegt ``raw`` (z. B. ``v1.2.3-rc1``) in ``((1, 2, 3), "rc1")``.

    Wirft ``ValueError`` bei unparsebarem Format – ein fehlendes Suffix ergibt
    den leeren String (Release ohne Vorabversions-Kennzeichnung).
    """
    match = _VERSION_RE.match(raw.strip())
    if match is None:
        raise ValueError(f"Kein gültiges vX.Y.Z-Versionsformat: {raw!r}")
    major, minor, patch, suffix = match.groups()
    return (int(major), int(minor), int(patch)), suffix or ""


def _is_newer(latest: tuple[tuple[int, int, int], str], current: tuple[tuple[int, int, int], str]) -> bool:
    """Vergleicht zwei ``(Kernversion, Suffix)``-Paare nach SemVer-Konvention.

    Ein Release **ohne** Vorabversions-Suffix hat bei gleicher Kernversion
    Vorrang vor einem mit Suffix (z. B. ``1.2.3`` > ``1.2.3-rc1``); zwei
    Suffixe werden lexikografisch verglichen (ausreichend für dieses Projekt,
    das keine numerisch fortlaufenden Vorabversionen über zweistellig hinaus
    veröffentlicht).
    """
    latest_core, latest_suffix = latest
    current_core, current_suffix = current
    if latest_core != current_core:
        return latest_core > current_core
    if latest_suffix == current_suffix:
        return False
    if latest_suffix == "":
        return True
    if current_suffix == "":
        return False
    return latest_suffix > current_suffix


def check_for_update(current_version: str, *, timeout: float = 5.0) -> UpdateCheckResult:
    """Prüft gegen die neueste GitHub-Release, ob ein Update verfügbar ist.

    Jeder Fehler (Netzwerk, HTTP-Status, ungültiges JSON, unparsebares
    Tag-Format) ergibt :data:`UpdateStatus.CHECK_FAILED` mit lesbarer
    ``error``-Nachricht – niemals eine Exception nach außen.
    """
    try:
        request = urllib.request.Request(_RELEASES_API_URL, headers=_REQUEST_HEADERS)
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return UpdateCheckResult(
            status=UpdateStatus.CHECK_FAILED,
            error=f"GitHub-Release-Abfrage fehlgeschlagen (HTTP {e.code}).",
        )
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return UpdateCheckResult(
            status=UpdateStatus.CHECK_FAILED,
            error=f"GitHub-Release-Abfrage nicht erreichbar: {e}",
        )
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return UpdateCheckResult(
            status=UpdateStatus.CHECK_FAILED,
            error=f"Ungültige Antwort der GitHub-Release-API: {e}",
        )

    if not isinstance(payload, dict):
        return UpdateCheckResult(
            status=UpdateStatus.CHECK_FAILED,
            error="Ungültige Antwort der GitHub-Release-API (kein JSON-Objekt).",
        )

    tag_name = payload.get("tag_name")
    release_url = payload.get("html_url")
    if not isinstance(tag_name, str) or not isinstance(release_url, str):
        return UpdateCheckResult(
            status=UpdateStatus.CHECK_FAILED,
            error="GitHub-Release-Antwort ohne Tag-Namen oder Release-URL.",
        )

    try:
        latest = _parse_version(tag_name)
        current = _parse_version(current_version)
    except ValueError as e:
        return UpdateCheckResult(status=UpdateStatus.CHECK_FAILED, error=str(e))

    if _is_newer(latest, current):
        return UpdateCheckResult(
            status=UpdateStatus.UPDATE_AVAILABLE,
            latest_version=tag_name,
            release_url=release_url,
        )
    return UpdateCheckResult(status=UpdateStatus.UP_TO_DATE)
