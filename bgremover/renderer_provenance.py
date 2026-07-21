"""Geteilte Regel: Software- vs. Hardware-GL-Renderer (#642, ADR #639).

Einzige Quelle der Wahrheit für die Erkennung reiner CPU-/Software-Renderer in
einer OpenGL-Diagnose (``Vendor / Renderer / Version``). Ein Software-Renderer
(llvmpipe & Co.) ist als **Hardware-Nachweis ungültig**: Die
Release-Abnahme-Smokes (#642/#643) und der Live-3D-Screenshot-Generator (#635)
weisen ihn gleichermaßen ab. Beide Konsumenten importieren diese Regel, damit
es keinen Marker-Drift zwischen ihnen gibt.

Qt-frei und strikt getypt – die Diagnose selbst liefert
``preview3d_capability.probe_3d_capability`` (bzw. der Screenshot-Generator).
"""
from __future__ import annotations

# Bekannte CPU-/Software-Rasterizer in GL-Renderer-Strings (casefold-Vergleich).
SOFTWARE_RENDERER_MARKERS: tuple[str, ...] = (
    "llvmpipe",
    "softpipe",
    "software rasterizer",
    "swiftshader",
    "basic render driver",
)


def is_software_renderer(diagnostic: str) -> bool:
    """Erkennt bekannte CPU-/Software-Renderer in der GL-Diagnose."""
    normalized = diagnostic.casefold()
    return any(marker in normalized for marker in SOFTWARE_RENDERER_MARKERS)
