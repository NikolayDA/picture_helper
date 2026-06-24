"""Gemeinsamer, Qt-freier Modusvertrag der 2D-Vorschau (#387/#388)."""
from __future__ import annotations

from enum import Enum


class PreviewMode(Enum):
    """Explizite, von der aktiven Ebene unabhängige Canvas-Vorschaumodi."""

    COLOR = "color"
    RELIEF = "relief"
    HEIGHT = "height"
    GLOSS = "gloss"
    COMBINED = "combined"
