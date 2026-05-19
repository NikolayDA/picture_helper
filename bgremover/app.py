"""Anwendungs-Einstiegspunkt.

Übergangs-Shim (Phase B, Schritt 1): delegiert byte-identisch an die noch
monolithische ``BgRemover.py`` via ``runpy`` – führt also exakt denselben
``__main__``-Block aus wie der bisherige ``python BgRemover.py``-Start.
Wird in einem späteren Schritt durch den echten ``main()``-Body ersetzt.
"""
from __future__ import annotations

import runpy


def main() -> None:
    """Startet die Anwendung (derzeit über das Monolith-Modul)."""
    runpy.run_module("BgRemover", run_name="__main__")
