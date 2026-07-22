"""Tests der 3D-Capability-Probe (#593, Epic #582).

Die Gating-Logik ist über ``probe_fn`` Qt-frei mit Mocks testbar; ein Test
prüft zusätzlich, dass die echte Offscreen-Probe den Fallback-Zweig ehrlich
trifft (kein GL-Kontext ohne X).
"""
from __future__ import annotations

import pytest

from bgremover.preview3d_capability import (
    UNAVAILABLE_KEY,
    RendererCapability,
    _default_probe,
    _gl_string,
    probe_3d_capability,
    reset_capability_cache,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    reset_capability_cache()
    yield
    reset_capability_cache()


def test_ok_probe_returns_capable() -> None:
    cap = probe_3d_capability(
        probe_fn=lambda: RendererCapability(ok=True, diagnostic="Mesa / llvmpipe"),
        use_cache=False,
    )
    assert cap.ok and cap.diagnostic == "Mesa / llvmpipe"


def test_failing_probe_returns_unavailable_key() -> None:
    cap = probe_3d_capability(
        probe_fn=lambda: RendererCapability(
            ok=False, error_key=UNAVAILABLE_KEY, detail="kein Kontext"),
        use_cache=False,
    )
    assert not cap.ok and cap.error_key == UNAVAILABLE_KEY


def test_raising_probe_never_propagates() -> None:
    def boom() -> RendererCapability:
        raise RuntimeError("Treiber explodiert")

    cap = probe_3d_capability(probe_fn=boom, use_cache=False)
    assert not cap.ok and cap.error_key == UNAVAILABLE_KEY


def test_result_is_cached_until_reset() -> None:
    calls = {"n": 0}

    def counting() -> RendererCapability:
        calls["n"] += 1
        return RendererCapability(ok=True)

    probe_3d_capability(probe_fn=counting)
    probe_3d_capability(probe_fn=counting)
    assert calls["n"] == 1  # zweiter Aufruf trifft den Cache
    reset_capability_cache()
    probe_3d_capability(probe_fn=counting)
    assert calls["n"] == 2


def test_offscreen_default_probe_reports_unavailable(qapp) -> None:
    # Repo-Standardpfad (offscreen ohne X): der echte Fallback-Zweig.
    cap = probe_3d_capability(use_cache=False)
    assert not cap.ok
    assert cap.error_key == UNAVAILABLE_KEY


# ── Spätere Fehlerzweige von ``_default_probe`` (#659, O8) ────────────────
#
# Der reale Offscreen-Testpfad oben trifft nur ``ctx.create() == False`` (den
# frühesten Fehlerzweig). Die tieferen Zweige (Surface/Make-current, GLES,
# fehlende Versionsfunktionen, äußere Exception) werden hier über gefakte
# PyQt6-Klassen erreicht – ``_default_probe`` importiert seine Qt-Klassen
# lokal je Aufruf, ein Patch auf dem Modulattribut wirkt daher sofort
# (Konvention aus ``test_app.py``, ``monkeypatch.setattr("PyQt6....", ...)``).

class _FakeContext:
    """Minimaler ``QOpenGLContext``-Stand-in: Kontext erzeugbar, aber tot."""

    def setFormat(self, fmt: object) -> None:  # noqa: N802
        pass

    def create(self) -> bool:
        return True

    def format(self) -> object:
        return None

    def makeCurrent(self, surface: object) -> bool:  # noqa: N802
        return False

    def isOpenGLES(self) -> bool:  # noqa: N802
        return False

    def doneCurrent(self) -> None:  # noqa: N802
        pass


class _FakeSurface:
    def setFormat(self, fmt: object) -> None:  # noqa: N802
        pass

    def create(self) -> None:
        pass

    def isValid(self) -> bool:
        return True


def test_default_probe_reports_unavailable_when_makecurrent_fails(monkeypatch) -> None:
    monkeypatch.setattr("PyQt6.QtGui.QOpenGLContext", _FakeContext)
    monkeypatch.setattr("PyQt6.QtGui.QOffscreenSurface", _FakeSurface)

    cap = _default_probe()

    assert cap.ok is False
    assert cap.error_key == UNAVAILABLE_KEY
    assert cap.detail == "Kein aktueller Offscreen-Kontext"


def test_default_probe_reports_unavailable_for_opengl_es_context(monkeypatch) -> None:
    class _ESContext(_FakeContext):
        def makeCurrent(self, surface: object) -> bool:  # noqa: N802
            return True

        def isOpenGLES(self) -> bool:  # noqa: N802
            return True

    monkeypatch.setattr("PyQt6.QtGui.QOpenGLContext", _ESContext)
    monkeypatch.setattr("PyQt6.QtGui.QOffscreenSurface", _FakeSurface)

    cap = _default_probe()

    assert cap.ok is False
    assert cap.error_key == UNAVAILABLE_KEY
    assert cap.detail == "Nur OpenGL-ES-Kontext verfügbar"


def test_default_probe_reports_unavailable_without_version_functions(monkeypatch) -> None:
    class _ReadyContext(_FakeContext):
        def makeCurrent(self, surface: object) -> bool:  # noqa: N802
            return True

    class _NoFunctionsFactory:
        @staticmethod
        def get(profile: object, ctx: object) -> None:
            return None

    monkeypatch.setattr("PyQt6.QtGui.QOpenGLContext", _ReadyContext)
    monkeypatch.setattr("PyQt6.QtGui.QOffscreenSurface", _FakeSurface)
    monkeypatch.setattr(
        "PyQt6.QtOpenGL.QOpenGLVersionFunctionsFactory", _NoFunctionsFactory
    )

    cap = _default_probe()

    assert cap.ok is False
    assert cap.error_key == UNAVAILABLE_KEY
    assert cap.detail == "Keine GL-2.1-Versionsfunktionen verfügbar"


def test_default_probe_never_propagates_outer_exception(monkeypatch) -> None:
    class _RaisingContext:
        def __init__(self) -> None:
            raise RuntimeError("Treiber explodiert")

    monkeypatch.setattr("PyQt6.QtGui.QOpenGLContext", _RaisingContext)

    cap = _default_probe()

    assert cap.ok is False
    assert cap.error_key == UNAVAILABLE_KEY
    assert "RuntimeError" in cap.detail
    assert "Treiber explodiert" in cap.detail


def test_gl_string_returns_empty_on_exception() -> None:
    class _Boom:
        def glGetString(self, name: int) -> str:  # noqa: N802
            raise RuntimeError("boom")

    assert _gl_string(_Boom(), 0x1F00) == ""


def test_gl_string_returns_empty_when_none() -> None:
    class _NoneReturning:
        def glGetString(self, name: int) -> None:  # noqa: N802
            return None

    assert _gl_string(_NoneReturning(), 0x1F00) == ""


def test_gl_string_decodes_bytes() -> None:
    class _BytesReturning:
        def glGetString(self, name: int) -> bytes:  # noqa: N802
            return b"Mesa"

    assert _gl_string(_BytesReturning(), 0x1F00) == "Mesa"
