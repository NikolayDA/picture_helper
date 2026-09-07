"""Tests der 3D-Capability-Probe (#593, Epic #582).

Die Gating-Logik ist über ``probe_fn`` Qt-frei mit Mocks testbar; ein Test
prüft zusätzlich den Vertrag der echten Probe (sie wirft nie und ist in sich
konsistent). Der Fallback-Zweig selbst haengt an der GL-Weiche: „offscreen"
heisst nicht „kein GL-Kontext" (Raspberry Pi mit Broadcom V3D).
"""
from __future__ import annotations

import pytest

from bgremover.preview3d_capability import (
    UNAVAILABLE_KEY,
    RendererCapability,
    _default_probe,
    _gl_string,
    _render_probe,
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


def test_default_probe_keeps_its_contract(qapp) -> None:
    """Die echte Qt-Probe (kein Mock) haelt in beiden Umgebungen ihren Vertrag.

    Frueher stand hier ``assert not cap.ok`` mit der Begruendung „offscreen
    ohne X". Das ist keine Eigenschaft der Probe, sondern eine Annahme ueber
    den Rechner: auf einem Raspberry Pi (Broadcom V3D + Mesa) liefert auch die
    Offscreen-Plattform einen Kontext, und der Test scheiterte. Geprueft wird
    jetzt der Vertrag – die Probe wirft nie und ist in sich konsistent.
    """
    cap = probe_3d_capability(use_cache=False)
    if cap.ok:
        assert cap.error_key is None
        assert cap.diagnostic, "Erfolg ohne Renderer-Provenienz waere nicht nachvollziehbar"
    else:
        assert cap.error_key == UNAVAILABLE_KEY


def test_offscreen_default_probe_reports_unavailable(qapp, gl_capability_ok) -> None:
    # Der echte Fallback-Zweig – nur dort messbar, wo es keinen GL-Kontext gibt.
    if gl_capability_ok:
        pytest.skip("Umgebung liefert einen GL-Kontext; Fallback-Zweig nicht erreichbar")
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


# ── Render-Nachweis: „Kontext ja, aber kein Framebuffer" (#1002) ──────────
#
# Der reale Zustand („QOpenGLWidget: No fbo, cannot render" bei gelungener
# Kontexterzeugung) tritt nur auf bestimmter Hardware auf (beobachtet: Raspberry
# Pi 5, Broadcom V3D + Mesa, `QT_QPA_PLATFORM=offscreen`). Hier wird er über
# dieselben lokalen Qt-Importe gestellt wie die Fehlerzweige oben.

class _ReadyContext(_FakeContext):
    """Kontext, der bis zum Render-Nachweis alles besteht.

    ``currentContext`` gehört dazu: ``_render_probe`` fragt es ab, bevor es ein
    Framebuffer-Objekt baut – Qt dereferenziert den aktuellen Kontext dort
    ungeprüft (ohne ihn SIGSEGV statt Ausnahme).
    """

    def makeCurrent(self, surface: object) -> bool:  # noqa: N802
        return True

    @staticmethod
    def currentContext() -> object:  # noqa: N802
        return object()


class _FakeFunctions:
    """GL-2.1-Funktionssatz-Stand-in: liefert Provenienz und zählt ``glClear``."""

    def __init__(self, clear_error: Exception | None = None) -> None:
        self.clear_masks: list[int] = []
        self._clear_error = clear_error

    def glGetString(self, name: int) -> bytes:  # noqa: N802
        return {0x1F00: b"Broadcom", 0x1F01: b"V3D 7.1", 0x1F02: b"2.1 Mesa"}[name]

    def glClear(self, mask: int) -> None:  # noqa: N802
        if self._clear_error is not None:
            raise self._clear_error
        self.clear_masks.append(mask)


def _install_ready_context(monkeypatch, fns: _FakeFunctions) -> None:
    """Patcht Kontext, Oberfläche und Funktions-Factory auf den Erfolgspfad."""

    class _Factory:
        @staticmethod
        def get(profile: object, ctx: object) -> _FakeFunctions:
            return fns

    monkeypatch.setattr("PyQt6.QtGui.QOpenGLContext", _ReadyContext)
    monkeypatch.setattr("PyQt6.QtGui.QOffscreenSurface", _FakeSurface)
    monkeypatch.setattr("PyQt6.QtOpenGL.QOpenGLVersionFunctionsFactory", _Factory)


class _FakeFbo:
    """``QOpenGLFramebufferObject``-Stand-in mit steuerbarem Ausgang."""

    valid = True
    bindable = True
    construct_error: Exception | None = None
    last: _FakeFbo | None = None

    class Attachment:
        CombinedDepthStencil = "combined-depth-stencil"

    def __init__(self, width: int, height: int, attachment: object) -> None:
        if type(self).construct_error is not None:
            raise type(self).construct_error
        self.size = (width, height)
        self.attachment = attachment
        self.released = 0
        type(self).last = self

    def isValid(self) -> bool:  # noqa: N802
        return type(self).valid

    def bind(self) -> bool:
        return type(self).bindable

    def release(self) -> None:
        self.released += 1


@pytest.fixture
def fake_fbo(monkeypatch):
    """Frische ``_FakeFbo``-Klasse je Test (die Schalter sind Klassenattribute)."""
    cls = type("_Fbo", (_FakeFbo,), {"valid": True, "bindable": True,
                                     "construct_error": None, "last": None})
    monkeypatch.setattr("PyQt6.QtOpenGL.QOpenGLFramebufferObject", cls)
    return cls


def test_render_proof_mirrors_the_widget_framebuffer(monkeypatch, fake_fbo) -> None:
    """Der Nachweis stellt genau nach, was ``QOpenGLWidget`` selbst anlegt.

    ``QOpenGLWidgetPrivate::recreateFbos`` erzeugt ein
    ``QOpenGLFramebufferObject`` mit ``CombinedDepthStencil``, bindet es und
    leert es per ``glClear``. Weil die Probe dieselbe Folge fährt, kann sie
    **nie strenger** sein als der Viewer – ein Falsch-Negativ (3D grundlos
    abgeschaltet) ist damit ausgeschlossen. Genau diese Bindung hält der Test.
    """
    fns = _FakeFunctions()
    _install_ready_context(monkeypatch, fns)

    cap = _default_probe()

    assert cap.ok is True
    assert cap.diagnostic == "Broadcom / V3D 7.1 / 2.1 Mesa"
    assert fake_fbo.last is not None
    assert fake_fbo.last.size == (4, 4)
    assert fake_fbo.last.attachment == fake_fbo.Attachment.CombinedDepthStencil
    assert fake_fbo.last.released == 1  # Bindung wieder gelöst
    # Farbe + Tiefe + Stencil, wie recreateFbos() leert.
    assert fns.clear_masks == [0x00004000 | 0x00000100 | 0x00000400]


def test_default_probe_reports_unavailable_without_a_usable_framebuffer(
    monkeypatch, fake_fbo
) -> None:
    """Der eigentliche #1002-Fall: Kontext vorhanden, Render-Ziel unvollständig."""
    fake_fbo.valid = False
    _install_ready_context(monkeypatch, _FakeFunctions())

    cap = _default_probe()

    assert cap.ok is False
    assert cap.error_key == UNAVAILABLE_KEY
    assert cap.detail == "Kontext ohne vollständiges Framebuffer-Objekt"
    # Die Provenienz überlebt den Fehlerfall – sonst wäre das Gerät, das genau
    # hier scheitert, aus dem Log nicht einzuordnen.
    assert cap.diagnostic == "Broadcom / V3D 7.1 / 2.1 Mesa"


def test_default_probe_reports_unavailable_when_the_framebuffer_cannot_bind(
    monkeypatch, fake_fbo
) -> None:
    fake_fbo.bindable = False
    _install_ready_context(monkeypatch, _FakeFunctions())

    cap = _default_probe()

    assert cap.ok is False
    assert cap.error_key == UNAVAILABLE_KEY
    assert cap.detail == "Framebuffer-Objekt nicht bindbar"


def test_default_probe_reports_unavailable_when_the_render_proof_raises(
    monkeypatch, fake_fbo
) -> None:
    """Ein Treiber, der beim Leeren abstürzt, ist ein Befund – kein App-Absturz."""
    _install_ready_context(monkeypatch, _FakeFunctions(clear_error=RuntimeError("GPU weg")))

    cap = _default_probe()

    assert cap.ok is False
    assert cap.error_key == UNAVAILABLE_KEY
    assert cap.detail.startswith("Render-Nachweis fehlgeschlagen: RuntimeError")
    assert "GPU weg" in cap.detail


def test_default_probe_reports_unavailable_when_the_framebuffer_is_not_constructible(
    monkeypatch, fake_fbo
) -> None:
    fake_fbo.construct_error = RuntimeError("kein FBO-Support")
    _install_ready_context(monkeypatch, _FakeFunctions())

    cap = _default_probe()

    assert cap.ok is False
    assert cap.error_key == UNAVAILABLE_KEY
    assert "kein FBO-Support" in cap.detail


def test_render_proof_refuses_without_a_current_context(monkeypatch, fake_fbo) -> None:
    """Fail-closed statt SIGSEGV.

    ``QOpenGLFramebufferObjectPrivate::init`` dereferenziert
    ``QOpenGLContext::currentContext()`` ungeprüft; ohne aktuellen Kontext
    stirbt der Prozess mit SIGSEGV – kein ``except`` fängt das. ``_default_probe``
    hat den Kontext immer (``makeCurrent()`` ist geprüft), die Schranke sichert
    einen künftigen zweiten Aufrufer ab.
    """

    class _NoCurrent:
        @staticmethod
        def currentContext() -> None:  # noqa: N802
            return None

    monkeypatch.setattr("PyQt6.QtGui.QOpenGLContext", _NoCurrent)

    assert _render_probe(object()) == "Render-Nachweis ohne aktuellen Kontext angefordert"
    assert fake_fbo.last is None  # kein Konstruktoraufruf ohne Kontext
