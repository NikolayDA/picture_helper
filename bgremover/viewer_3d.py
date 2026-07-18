"""Interaktiver 3D-Reliefviewer und Zustandscontainer (#593, Epic #582).

Zwei Bausteine:

- :class:`GLReliefViewer` – ein ``QOpenGLWidget``, das ein
  :class:`~bgremover.relief_mesh.ReliefMesh` über einen GL-2.1-Shaderpfad
  rendert (Lambert, doppelseitig) und Orbit/Pan/Zoom per Maus/Tastatur bedient.
  **Alle** GL-Hooks sind gekapselt: ein Fehler in ``initializeGL``/``paintGL``
  propagiert nie in den Event-Loop, sondern schaltet das Widget in einen
  neutralen Fehlerzustand und meldet ihn über ``initFailed`` (ADR-Fallback).
  Der GL-Zugriff läuft über ``QOpenGLVersionFunctionsFactory`` (PyQt6 bindet
  keine generische ``QOpenGLContext.functions()``-API, ADR).
- :class:`Relief3DView` – der einbettbare Zustandscontainer (``QStackedWidget``)
  mit den UX-Zuständen Empty/Unavailable/Loading/Error/Ready. Er ist **ohne**
  GL-Kontext vollständig testbar (reine Widgets/Labels); den GL-Viewer erzeugt
  er erst, wenn die Capability-Probe positiv ist und ein Mesh vorliegt. Dieser
  Zustandsautomat ist der garantierte 2D-Fallbackpfad des Epics.

Der Viewer besitzt **keinen** Schreibpfad ins Modell: Kamera/Licht/Überhöhung
sind reine Anzeige-Uniforms, Bildexport und Projektpersistenz bleiben unberührt.
"""
from __future__ import annotations

import contextlib
import math
from typing import Any

import numpy as np
from PyQt6.QtCore import Qt, pyqtBoundSignal, pyqtSignal
from PyQt6.QtGui import QMatrix4x4, QSurfaceFormat
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

try:  # QOpenGLWidget + GL-Klassen liegen in eigenen PyQt6-Modulen
    from PyQt6.QtOpenGL import (
        QOpenGLBuffer,
        QOpenGLShader,
        QOpenGLShaderProgram,
        QOpenGLVersionFunctionsFactory,
        QOpenGLVersionProfile,
        QOpenGLVertexArrayObject,
    )
    from PyQt6.QtOpenGLWidgets import QOpenGLWidget

    _HAS_GL_WIDGET = True
except Exception:  # noqa: BLE001 – ohne GL-Klassen bleibt nur der Fallback
    QOpenGLWidget = QWidget  # type: ignore[assignment,misc]
    _HAS_GL_WIDGET = False

from bgremover.constants import logger
from bgremover.i18n import tr
from bgremover.preview3d_camera import OrbitCamera
from bgremover.relief_mesh import ReliefMesh
from bgremover.theme import Palette, active_palette

# GL-Enum-Konstanten (roh, damit sie nicht an ein bestimmtes PyQt6-Enum-Modul
# gebunden sind – der Wert ist Teil des OpenGL-Vertrags, nicht der Bindings).
_GL_DEPTH_TEST = 0x0B71
_GL_COLOR_BUFFER_BIT = 0x00004000
_GL_DEPTH_BUFFER_BIT = 0x00000100
_GL_TRIANGLES = 0x0004
_GL_UNSIGNED_INT = 0x1405
_GL_FLOAT = 0x1406

# GLSL 1.20 (OpenGL 2.1). ``abs(dot(...))`` beleuchtet doppelseitig, damit ein
# Orbit unter das Relief die Struktur weiter sichtbar hält.
_VERTEX_SHADER = """
#version 120
attribute vec3 a_pos;
attribute vec2 a_slope;
uniform mat4 u_mvp;
uniform float u_exagg;
varying vec3 v_normal;
void main() {
    vec3 p = vec3(a_pos.xy, a_pos.z * u_exagg);
    v_normal = normalize(vec3(-a_slope * u_exagg, 1.0));
    gl_Position = u_mvp * vec4(p, 1.0);
}
"""

_FRAGMENT_SHADER = """
#version 120
varying vec3 v_normal;
uniform vec3 u_light_dir;
uniform vec3 u_color;
void main() {
    vec3 n = normalize(v_normal);
    float lam = abs(dot(n, normalize(u_light_dir)));
    float shade = 0.28 + 0.72 * lam;
    gl_FragColor = vec4(u_color * shade, 1.0);
}
"""


def _light_direction(azimuth_deg: float, elevation_deg: float) -> tuple[float, float, float]:
    """Weltlichtvektor aus Azimut/Elevation (Konvention wie 2D-Hillshade)."""
    az = math.radians(azimuth_deg % 360.0)
    el = math.radians(max(0.0, min(90.0, elevation_deg)))
    horiz = math.cos(el)
    return (math.sin(az) * horiz, -math.cos(az) * horiz, math.sin(el))


class GLReliefViewer(QOpenGLWidget):  # type: ignore[misc,valid-type]
    """``QOpenGLWidget``-Renderer eines begrenzten Grid-Meshes (gekapselte GL-Hooks).

    Öffentliche Steuerung ist rein visuell: ``set_mesh``, ``set_exaggeration``,
    ``set_light``, ``fit_view``, ``reset_view``. ``initFailed(str)`` meldet einen
    Kontext-/Shader-/Bufferfehler an den Container, der dann in den
    Fehlerzustand wechselt.
    """

    initFailed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        fmt = QSurfaceFormat()
        fmt.setVersion(2, 1)
        fmt.setDepthBufferSize(24)
        with contextlib.suppress(Exception):
            self.setFormat(fmt)
        self._mesh: ReliefMesh | None = None
        self._pending_mesh: ReliefMesh | None = None
        self._camera = OrbitCamera()
        self._exaggeration = 1.0
        self._light = (315.0, 45.0)
        self._program: Any = None
        self._pos_vbo: Any = None
        self._slope_vbo: Any = None
        self._index_ibo: Any = None
        self._vao: Any = None
        self._index_count = 0
        self._gl_ready = False
        self._failed = False
        self._last_pos: tuple[float, float] | None = None
        self._palette = active_palette()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumSize(240, 200)
        self.setAccessibleName(tr("preview3d.a11y.name"))
        self.setAccessibleDescription(tr("preview3d.a11y.desc"))

    # ── Öffentliche, rein visuelle Steuerung ─────────────────────────────
    def set_palette(self, palette: Palette) -> None:
        self._palette = palette
        self._safe_update()

    def set_mesh(self, mesh: ReliefMesh) -> None:
        """Übernimmt ein neues Mesh und rahmt es ein (Upload beim nächsten Frame)."""
        self._mesh = mesh
        self._pending_mesh = mesh
        lo, hi = mesh.bounds
        self._camera.reset(lo, hi)
        self._safe_update()

    def set_exaggeration(self, value: float) -> None:
        self._exaggeration = max(0.1, min(10.0, float(value)))
        self._safe_update()

    def set_light(self, azimuth: float, elevation: float) -> None:
        self._light = (float(azimuth), float(elevation))
        self._safe_update()

    def fit_view(self) -> None:
        if self._mesh is not None:
            lo, hi = self._mesh.bounds
            self._camera.fit_bounds(lo, hi)
            self._safe_update()

    def reset_view(self) -> None:
        if self._mesh is not None:
            lo, hi = self._mesh.bounds
            self._camera.reset(lo, hi)
        self._exaggeration = 1.0
        self._light = (315.0, 45.0)
        self._safe_update()

    @property
    def camera(self) -> OrbitCamera:
        return self._camera

    @property
    def has_failed(self) -> bool:
        return self._failed

    # ── GL-Lifecycle (gekapselt – propagiert nie) ────────────────────────
    def initializeGL(self) -> None:  # noqa: N802 (Qt-Override)
        try:
            self._init_gl()
            self._gl_ready = True
        except Exception as exc:  # noqa: BLE001
            self._fail(f"initializeGL: {type(exc).__name__}: {exc}")

    def resizeGL(self, w: int, h: int) -> None:  # noqa: N802 (Qt-Override)
        # Viewport folgt Qt automatisch beim nächsten paintGL; nichts Riskantes.
        return None

    def paintGL(self) -> None:  # noqa: N802 (Qt-Override)
        if self._failed or not self._gl_ready:
            return
        try:
            self._paint_gl()
        except Exception as exc:  # noqa: BLE001
            self._fail(f"paintGL: {type(exc).__name__}: {exc}")

    # ── interne GL-Implementierung ───────────────────────────────────────
    def _functions(self) -> Any:
        """GL-2.1-Funktionssatz über die Versions-Factory (PyQt6-Vertrag, ADR)."""
        profile = QOpenGLVersionProfile()
        profile.setVersion(2, 1)
        return QOpenGLVersionFunctionsFactory.get(profile, self.context())

    def _init_gl(self) -> None:
        program = QOpenGLShaderProgram(self)
        if not program.addShaderFromSourceCode(
            QOpenGLShader.ShaderTypeBit.Vertex, _VERTEX_SHADER
        ):
            raise RuntimeError(f"Vertex-Shader: {program.log()}")
        if not program.addShaderFromSourceCode(
            QOpenGLShader.ShaderTypeBit.Fragment, _FRAGMENT_SHADER
        ):
            raise RuntimeError(f"Fragment-Shader: {program.log()}")
        if not program.link():
            raise RuntimeError(f"Programm-Link: {program.log()}")
        self._program = program

    def _ensure_buffers(self) -> None:
        if self._pending_mesh is None:
            return
        mesh = self._pending_mesh
        self._pending_mesh = None
        positions = np.ascontiguousarray(mesh.positions, dtype=np.float32)
        slope = np.ascontiguousarray(mesh.slope, dtype=np.float32)
        indices = np.ascontiguousarray(mesh.indices, dtype=np.uint32).ravel()
        self._index_count = int(indices.size)

        vao = QOpenGLVertexArrayObject(self)
        self._vao = vao if vao.create() else None

        self._pos_vbo = self._make_buffer(QOpenGLBuffer.Type.VertexBuffer, positions)
        self._slope_vbo = self._make_buffer(QOpenGLBuffer.Type.VertexBuffer, slope)
        self._index_ibo = self._make_buffer(QOpenGLBuffer.Type.IndexBuffer, indices)

    @staticmethod
    def _make_buffer(buffer_type: Any, data: np.ndarray) -> Any:
        buf = QOpenGLBuffer(buffer_type)
        buf.create()
        buf.bind()
        raw = data.tobytes()
        # PyQt6 akzeptiert ein bytes-Objekt als Lesepuffer (sip.voidptr); der
        # Stub kennt nur den voidptr-Overload, daher hier bewusst ignoriert.
        buf.allocate(raw, len(raw))  # type: ignore[call-overload]
        buf.release()
        return buf

    def _paint_gl(self) -> None:
        fns = self._functions()
        if fns is None:
            raise RuntimeError("Keine GL-2.1-Versionsfunktionen verfügbar")
        r, g, b = _hex_rgb(self._palette.bg)
        fns.glClearColor(r, g, b, 1.0)
        fns.glEnable(_GL_DEPTH_TEST)
        fns.glClear(_GL_COLOR_BUFFER_BIT | _GL_DEPTH_BUFFER_BIT)
        if self._program is None or self._mesh is None:
            return
        self._ensure_buffers()
        if self._index_count == 0 or self._pos_vbo is None:
            return

        program = self._program
        program.bind()
        w = max(1, self.width())
        h = max(1, self.height())
        mvp = self._camera.projection_matrix(w / h) @ self._camera.view_matrix()
        program.setUniformValue(program.uniformLocation("u_mvp"), _qmatrix(mvp))
        program.setUniformValue(
            program.uniformLocation("u_exagg"), float(self._exaggeration)
        )
        lx, ly, lz = _light_direction(*self._light)
        program.setUniformValue(program.uniformLocation("u_light_dir"), lx, ly, lz)
        program.setUniformValue(program.uniformLocation("u_color"), 0.72, 0.74, 0.78)

        if self._vao is not None:
            self._vao.bind()
        self._bind_attribute(program, "a_pos", self._pos_vbo, 3)
        self._bind_attribute(program, "a_slope", self._slope_vbo, 2)
        self._index_ibo.bind()
        fns.glDrawElements(_GL_TRIANGLES, self._index_count, _GL_UNSIGNED_INT, None)
        self._index_ibo.release()
        if self._vao is not None:
            self._vao.release()
        program.release()

    def _bind_attribute(
        self, program: Any, name: str, vbo: Any, components: int
    ) -> None:
        if vbo is None:
            return
        loc = program.attributeLocation(name)
        if loc < 0:
            return
        vbo.bind()
        program.enableAttributeArray(loc)
        program.setAttributeBuffer(loc, _GL_FLOAT, 0, components, 0)

    def _fail(self, message: str) -> None:
        if self._failed:
            return
        self._failed = True
        logger.warning("3D-Viewer-Fehler: %s", message)
        self.initFailed.emit(message)

    def _safe_update(self) -> None:
        if not self._failed:
            self.update()

    # ── Interaktion (nur bei Fokus/Zeiger im Viewport) ───────────────────
    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event is None:
            return
        self._last_pos = (event.position().x(), event.position().y())
        self.setFocus(Qt.FocusReason.MouseFocusReason)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if event is None or self._last_pos is None:
            return
        x, y = event.position().x(), event.position().y()
        dx = x - self._last_pos[0]
        dy = y - self._last_pos[1]
        self._last_pos = (x, y)
        buttons = event.buttons()
        mods = event.modifiers()
        pan = bool(buttons & Qt.MouseButton.MiddleButton) or (
            bool(buttons & Qt.MouseButton.LeftButton)
            and bool(mods & Qt.KeyboardModifier.AltModifier)
        )
        if pan:
            self._camera.pan(dx / max(1, self.width()), dy / max(1, self.height()))
        elif buttons & Qt.MouseButton.LeftButton:
            self._camera.orbit(dx * 0.4, -dy * 0.4)
        self._safe_update()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._last_pos = None

    def wheelEvent(self, event) -> None:  # noqa: N802
        if event is None:
            return
        delta = event.angleDelta().y()
        if delta == 0:
            return
        self._camera.zoom(0.9 if delta > 0 else 1.0 / 0.9)
        self._safe_update()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event is None:
            return
        key = event.key()
        shift = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        step = 12.0
        if key == Qt.Key.Key_Left:
            self._camera.pan(-0.05, 0.0) if shift else self._camera.orbit(-step, 0.0)
        elif key == Qt.Key.Key_Right:
            self._camera.pan(0.05, 0.0) if shift else self._camera.orbit(step, 0.0)
        elif key == Qt.Key.Key_Up:
            self._camera.pan(0.0, -0.05) if shift else self._camera.orbit(0.0, step)
        elif key == Qt.Key.Key_Down:
            self._camera.pan(0.0, 0.05) if shift else self._camera.orbit(0.0, -step)
        elif key in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
            self._camera.zoom(0.9)
        elif key == Qt.Key.Key_Minus:
            self._camera.zoom(1.0 / 0.9)
        elif key == Qt.Key.Key_Home:
            if shift:
                self.reset_view()
            else:
                self.fit_view()
        else:
            super().keyPressEvent(event)
            return
        self._safe_update()

    def cleanup_gl(self) -> None:
        """Gibt GL-Ressourcen kontrolliert frei (Projektwechsel/Schließen)."""
        try:
            if _HAS_GL_WIDGET:
                self.makeCurrent()
            for buf in (self._pos_vbo, self._slope_vbo, self._index_ibo):
                if buf is not None:
                    buf.destroy()
            if self._vao is not None:
                self._vao.destroy()
        except Exception:  # noqa: BLE001
            pass
        finally:
            self._pos_vbo = self._slope_vbo = self._index_ibo = self._vao = None
            self._program = None
            self._gl_ready = False
            if _HAS_GL_WIDGET:
                with contextlib.suppress(Exception):
                    self.doneCurrent()


def _hex_rgb(value: str) -> tuple[float, float, float]:
    """Zerlegt einen ``#rrggbb``-Hexstring in ``0..1``-Floats (Fallback dunkel)."""
    text = value.strip()
    if text.startswith("#") and len(text) >= 7:
        try:
            r = int(text[1:3], 16) / 255.0
            g = int(text[3:5], 16) / 255.0
            b = int(text[5:7], 16) / 255.0
            return r, g, b
        except ValueError:
            pass
    return 0.12, 0.14, 0.17


def _qmatrix(mat: np.ndarray) -> QMatrix4x4:
    """numpy-4×4 (Mathe-Konvention, row-major) → ``QMatrix4x4``."""
    flat = [float(v) for v in np.asarray(mat, dtype=np.float64).ravel()]
    return QMatrix4x4(*flat)


class Relief3DView(QStackedWidget):
    """Einbettbarer Zustandscontainer der 3D-Vorschau (garantierter 2D-Fallback).

    Zustände (UX §5): ``empty``/``unavailable``/``loading``/``error``/``ready``.
    Der GL-Viewer wird lazy erzeugt und nur im Ready-Zustand gezeigt; alle
    übrigen Zustände sind reine Label-/Button-Seiten und damit ohne GL-Kontext
    testbar. Signale ``show2DRequested``/``retryRequested`` reicht der Container
    an das MainWindow durch (Fallback bzw. „Erneut versuchen").
    """

    show2DRequested = pyqtSignal()
    retryRequested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._state = "empty"
        self._viewer: GLReliefViewer | None = None
        self._palette = active_palette()

        self._empty_label = self._make_message_page(tr("preview3d.empty"))
        self._unavailable_page, self._unavailable_label = self._make_action_page(
            tr("preview3d.unavailable"),
            [(tr("preview3d.error.retry"), self.retryRequested)],
        )
        self._loading_label = self._make_message_page(tr("preview3d.loading"))
        self._error_page, self._error_label = self._make_action_page(
            tr("preview3d.error"),
            [
                (tr("preview3d.error.show_2d"), self.show2DRequested),
                (tr("preview3d.error.retry"), self.retryRequested),
            ],
        )
        # Ready-Seite: GL-Viewer + Decimation-Badge (Overlay oben links).
        self._ready_page = QWidget()
        ready_lay = QVBoxLayout(self._ready_page)
        ready_lay.setContentsMargins(0, 0, 0, 0)
        self._badge = QLabel(self._ready_page)
        self._badge.setVisible(False)
        self._badge.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        self.addWidget(self._empty_label)          # index 0
        self.addWidget(self._unavailable_page)      # index 1
        self.addWidget(self._loading_label)         # index 2
        self.addWidget(self._error_page)            # index 3
        self.addWidget(self._ready_page)            # index 4
        self._apply_page_styles()
        self.show_empty()

    # ── Zustands-API ─────────────────────────────────────────────────────
    @property
    def state(self) -> str:
        return self._state

    def viewer(self) -> GLReliefViewer | None:
        return self._viewer

    def show_empty(self) -> None:
        self._state = "empty"
        self.setCurrentWidget(self._empty_label)

    def show_unavailable(self) -> None:
        self._state = "unavailable"
        self.setCurrentWidget(self._unavailable_page)

    def show_loading(self) -> None:
        self._state = "loading"
        self.setCurrentWidget(self._loading_label)

    def show_error(self) -> None:
        self._state = "error"
        self.setCurrentWidget(self._error_page)

    def show_mesh(self, mesh: ReliefMesh) -> None:
        """Zeigt ein Mesh im GL-Viewer; ein GL-Init-Fehler wechselt zu ``error``."""
        viewer = self._ensure_viewer()
        if viewer is None:
            self.show_error()
            return
        viewer.set_mesh(mesh)
        self._update_badge(mesh)
        self._state = "ready"
        self.setCurrentWidget(self._ready_page)

    # ── Anzeige-Parameter durchreichen ───────────────────────────────────
    def set_exaggeration(self, value: float) -> None:
        if self._viewer is not None:
            self._viewer.set_exaggeration(value)

    def set_light(self, azimuth: float, elevation: float) -> None:
        if self._viewer is not None:
            self._viewer.set_light(azimuth, elevation)

    def fit_view(self) -> None:
        if self._viewer is not None:
            self._viewer.fit_view()

    def reset_view(self) -> None:
        if self._viewer is not None:
            self._viewer.reset_view()

    def apply_palette(self, palette: Palette) -> None:
        self._palette = palette
        self._apply_page_styles()
        if self._viewer is not None:
            self._viewer.set_palette(palette)

    def cleanup(self) -> None:
        """Gibt den GL-Viewer frei (Projektwechsel/Schließen)."""
        if self._viewer is not None:
            self._viewer.cleanup_gl()

    # ── intern ───────────────────────────────────────────────────────────
    def _ensure_viewer(self) -> GLReliefViewer | None:
        if self._viewer is not None:
            return self._viewer
        if not _HAS_GL_WIDGET:
            return None
        try:
            viewer = GLReliefViewer(self._ready_page)
            viewer.set_palette(self._palette)
            viewer.initFailed.connect(lambda _msg: self.show_error())
            layout = self._ready_page.layout()
            assert isinstance(layout, QVBoxLayout)
            layout.addWidget(viewer)
            self._viewer = viewer
            self._badge.raise_()
            return viewer
        except Exception as exc:  # noqa: BLE001
            logger.warning("3D-Viewer konnte nicht erstellt werden: %s", exc)
            return None

    def _update_badge(self, mesh: ReliefMesh) -> None:
        if mesh.is_decimated:
            self._badge.setText(
                tr("preview3d.decimated", factor=mesh.decimation_factor)
            )
            self._badge.adjustSize()
            self._badge.move(10, 10)
            self._badge.setVisible(True)
        else:
            self._badge.setVisible(False)

    def _make_message_page(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label

    def _make_action_page(
        self, message: str, actions: list[tuple[str, pyqtBoundSignal]]
    ) -> tuple[QWidget, QLabel]:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(14)
        lay.addStretch()
        label = QLabel(message)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(label)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()
        for action_text, signal in actions:
            btn = QPushButton(action_text)
            btn.setAccessibleName(action_text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _=False, s=signal: s.emit())
            btn_row.addWidget(btn)
        btn_row.addStretch()
        lay.addLayout(btn_row)
        lay.addStretch()
        return page, label

    def _apply_page_styles(self) -> None:
        p = self._palette
        for label in (
            self._unavailable_label, self._error_label,
        ):
            label.setStyleSheet(
                f"color: {p.text2}; background: transparent; font-size: 13px;"
            )
        for page in (self._ready_page, self._unavailable_page, self._error_page):
            page.setStyleSheet(f"background: {p.bg};")
        self._empty_label.setStyleSheet(
            f"color: {p.text2}; background: {p.bg}; font-size: 13px; padding: 24px;"
        )
        self._loading_label.setStyleSheet(
            f"color: {p.text2}; background: {p.bg}; font-size: 13px; padding: 24px;"
        )
        self._badge.setStyleSheet(
            f"color: {p.on_accent}; background: {p.accent}; border-radius: 6px;"
            " padding: 3px 8px; font-size: 11px; font-weight: 600;"
        )
