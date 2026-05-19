"""BgRemover – Hintergrund-Entfernungs- und Bildbearbeitungs-Tool.

Übergangszustand (Phase B des Monolith→Paket-Schnitts, Runde 5): Die
Implementierung liegt aktuell noch in ``BgRemover.py``; dieses Paket
stellt bereits den Paket-Einstiegspunkt bereit (``bgremover`` /
``python -m bgremover``). Module werden schrittweise, verhaltensneutral
hierher verschoben.

Öffentliche Re-Exporte (für Tests / API): wachsen pro Schritt mit, damit
der finale Import-Wechsel ``from BgRemover import X`` →
``from bgremover import X`` ein minimaler Eingriff bleibt.
"""
from bgremover.constants import (
    LOG_FILENAME,
    TOOL_BRUSH,
    TOOL_ERASER,
    TOOL_LASSO,
    TOOL_WAND,
    _MAX_MEGAPIXELS,
    _THREAD_SHUTDOWN_MS,
    _UNDO_MEMORY_LIMIT,
    logger,
)

__all__ = [
    "LOG_FILENAME",
    "TOOL_BRUSH",
    "TOOL_ERASER",
    "TOOL_LASSO",
    "TOOL_WAND",
    "_MAX_MEGAPIXELS",
    "_THREAD_SHUTDOWN_MS",
    "_UNDO_MEMORY_LIMIT",
    "logger",
]
