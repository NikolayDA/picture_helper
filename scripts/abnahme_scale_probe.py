#!/usr/bin/env python3
"""devicePixelRatio-Probe für den macOS-Retina-Nachweis (#643).

Öffnet einen nativen Qt-Kontext und gibt den devicePixelRatio des primären
Bildschirms auf stdout aus (``0`` bei fehlendem Kontext). Der Abnahme-Smoke
(``abnahme_smoke.py``) bewertet den Wert über ``evaluate_retina``. Bewusst
klein und Qt-gekapselt – die Bewertung selbst ist Qt-frei getestet.
"""
from __future__ import annotations

import sys


def scale_factor() -> float:
    """devicePixelRatio des primären Bildschirms (0.0 ohne Kontext)."""
    try:
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance() or QApplication(sys.argv)
        screen = app.primaryScreen()  # type: ignore[union-attr]
        return float(screen.devicePixelRatio()) if screen is not None else 0.0
    except Exception:  # noqa: BLE001 - Probe darf nie werfen (Abnahme-Kontext).
        return 0.0


if __name__ == "__main__":
    print(scale_factor())
