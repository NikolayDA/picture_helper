"""Qt-freie Statuserkennung für das gecachte rembg-Modell (#568, Teil von Epic #563).

Stellt fest, ob das rembg-Standardmodell (`u2net.onnx`) bereits lokal im
rembg-Cache-Verzeichnis liegt, **ohne** einen Download auszulösen und **ohne**
`rembg` zu importieren (reine Pfad-/Datei-Prüfung – Konsistenz mit Befund N7,
der den teuren rembg-Import bewusst aus dem Hauptprozess heraushält, siehe
`workers.REMBG_AVAILABLE`).
"""
from __future__ import annotations

import importlib.util
import os
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

_DEFAULT_MODEL_FILENAME = "u2net.onnx"


def _rembg_available() -> bool:
    """Prüft nur die *Installation* von rembg (kein teurer Import).

    Duplikat der gleichnamigen Prüfung in `workers.REMBG_AVAILABLE`: dieses
    Modul soll Qt-frei bleiben und importiert daher bewusst nicht `workers`
    (das PyQt6 zieht).
    """
    try:
        return importlib.util.find_spec("rembg") is not None
    except (ImportError, ValueError):
        return False


class ModelStatus(Enum):
    """Cache-Zustand des rembg-Standardmodells."""

    DOWNLOADED = auto()
    NOT_DOWNLOADED = auto()
    REMBG_UNAVAILABLE = auto()


@dataclass(frozen=True)
class ModelStatusResult:
    """Strukturiertes Ergebnis von :func:`get_model_status`."""

    status: ModelStatus
    model_path: Path
    size_bytes: int | None = None


def _u2net_home() -> Path:
    """Rembg-Cache-Verzeichnis, gemäß `rembg.session_base.u2net_home()`-Fallback.

    Reihenfolge: `U2NET_HOME`-Override, sonst `$XDG_DATA_HOME/.u2net` (falls
    `XDG_DATA_HOME` gesetzt ist), sonst `~/.u2net`.
    """
    override = os.environ.get("U2NET_HOME")
    if override:
        return Path(override)
    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home) / ".u2net"
    return Path.home() / ".u2net"


def get_model_status() -> ModelStatusResult:
    """Prüft, ob das rembg-Standardmodell bereits lokal gecacht ist.

    Importiert **kein** `rembg` – nur Pfad-/Dateigrößenprüfung. Respektiert
    `U2NET_HOME`/`XDG_DATA_HOME` wie `rembg.session_base.u2net_home()` (siehe
    :func:`_u2net_home`). Keine Integritätsprüfung (Checksumme) in v1, nur
    Existenz als Datei + Größe > 0.
    """
    model_path = _u2net_home() / _DEFAULT_MODEL_FILENAME

    if not _rembg_available():
        return ModelStatusResult(status=ModelStatus.REMBG_UNAVAILABLE, model_path=model_path)

    try:
        stat_result = model_path.stat()
    except OSError:
        return ModelStatusResult(status=ModelStatus.NOT_DOWNLOADED, model_path=model_path)

    if not model_path.is_file():
        # Ein Verzeichnis (z. B. nach fehlgeschlagenem Download/Extrakt) ist
        # kein gültiges Modell, auch wenn `stat()` eine positive Größe liefert.
        return ModelStatusResult(status=ModelStatus.NOT_DOWNLOADED, model_path=model_path)

    size_bytes = stat_result.st_size
    if size_bytes <= 0:
        return ModelStatusResult(status=ModelStatus.NOT_DOWNLOADED, model_path=model_path)

    return ModelStatusResult(
        status=ModelStatus.DOWNLOADED, model_path=model_path, size_bytes=size_bytes
    )
