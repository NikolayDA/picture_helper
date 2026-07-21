"""Tests für die geteilte Software-/Hardware-Renderer-Regel (#642)."""
from __future__ import annotations

from bgremover import renderer_provenance as rp


def test_known_software_renderers_detected() -> None:
    assert rp.is_software_renderer("Mesa / llvmpipe (LLVM 18.1.8, 256 bits) / 4.5")
    assert rp.is_software_renderer("Google / SwiftShader Device / 4.5")
    assert rp.is_software_renderer("Microsoft / Basic Render Driver / 1.1")


def test_hardware_renderers_pass() -> None:
    assert not rp.is_software_renderer("Apple / Apple M3 Max / 2.1 Metal - 90.5")
    assert not rp.is_software_renderer("Broadcom / V3D 7.1 / OpenGL ES 3.1")
    assert not rp.is_software_renderer("NVIDIA / RTX 4090 / 4.6")


def test_screenshot_generator_shares_the_same_markers() -> None:
    """Kein Marker-Drift zwischen Smoke (#642) und Screenshot-Generator (#635)."""
    import importlib.util
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    spec = importlib.util.spec_from_file_location(
        "generate_app_screenshots", root / "scripts" / "generate_app_screenshots.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Modulname muss in sys.modules stehen, sonst scheitert die frozen-dataclass-
    # Typprüfung unter ``from __future__ import annotations`` (wie test_benchmark).
    sys.modules["generate_app_screenshots"] = module
    spec.loader.exec_module(module)
    # Der Generator nutzt exakt die geteilte Regel (kein Marker-Drift).
    assert module._is_software_renderer is rp.is_software_renderer
