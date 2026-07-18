"""Qt-freie Orbit-Kamera-Mathematik der 3D-Reliefvorschau (#593, Epic #582).

Reine, deterministisch testbare Kamera- und Matrix-Logik neben dem
Geometriekern (:mod:`bgremover.relief_mesh`) – ohne Qt, OpenGL oder Viewer.
Konvention: rechtshändiges Weltsystem mit **+Z oben** (aus der Reliefebene zum
Betrachter; siehe ADR). Alle Matrizen sind Spaltenvektor-Konvention
(``v' = M @ v``) und werden als ``float64 (4, 4)`` geliefert; der Viewer
transponiert beim GL-Upload.

Interaktionsgrenzen (UX-Vertrag §3/§4): Polhöhe geklemmt (±88°) gegen
Kamerasprünge, Zoom über feste Nah-/Fernklemmen. „Einpassen" rahmt die
Bounding-Box, „Zurücksetzen" stellt die dokumentierte Standardkamera her.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

# Standardkamera (reproduzierbar; „Zurücksetzen" stellt genau diese Werte her).
DEFAULT_AZIMUTH = -55.0
DEFAULT_ELEVATION = 35.0
DEFAULT_FOV_Y = 45.0

# Polhöhen-Klemme gegen Gimbal-/Up-Degeneration nahe dem Zenit (UX §3).
_MAX_ELEVATION = 88.0

# Zoom-/Distanzklemmen (Vielfache des Fit-Abstands); verhindern Durchdringen
# bzw. Verlieren des Modells (UX §3).
_MIN_DISTANCE_FACTOR = 0.1
_MAX_DISTANCE_FACTOR = 8.0
_ABS_MIN_DISTANCE = 1e-3

# Rahmen-Reserve beim Einpassen (10 % Luft um die Bounding-Sphere).
_FIT_MARGIN = 1.1


def _normalize(v: np.ndarray) -> np.ndarray:
    length = float(np.linalg.norm(v))
    if length <= 1e-12:
        return v
    return v / length


def look_at(eye: np.ndarray, center: np.ndarray, up: np.ndarray) -> np.ndarray:
    """Rechtshändige Blickmatrix (Spaltenvektor-Konvention, ``float64 (4,4)``)."""
    forward = _normalize(center - eye)
    right = _normalize(np.cross(forward, up))
    true_up = np.cross(right, forward)
    mat = np.eye(4, dtype=np.float64)
    mat[0, :3] = right
    mat[1, :3] = true_up
    mat[2, :3] = -forward
    mat[0, 3] = -float(np.dot(right, eye))
    mat[1, 3] = -float(np.dot(true_up, eye))
    mat[2, 3] = float(np.dot(forward, eye))
    return mat


def perspective(fov_y_deg: float, aspect: float, near: float, far: float) -> np.ndarray:
    """Perspektivische Projektionsmatrix (Spaltenvektor-Konvention).

    ``aspect`` = Breite/Höhe des Viewports; ``near``/``far`` sind positive
    Clip-Ebenen. Nicht-positive/entartete Parameter werden defensiv geklemmt.
    """
    aspect = max(aspect, 1e-6)
    fov = math.radians(max(1.0, min(179.0, fov_y_deg)))
    f = 1.0 / math.tan(fov / 2.0)
    near = max(near, 1e-4)
    far = max(far, near + 1e-3)
    mat = np.zeros((4, 4), dtype=np.float64)
    mat[0, 0] = f / aspect
    mat[1, 1] = f
    mat[2, 2] = (far + near) / (near - far)
    mat[2, 3] = (2.0 * far * near) / (near - far)
    mat[3, 2] = -1.0
    return mat


@dataclass
class OrbitCamera:
    """Orbit-/Pan-/Zoom-Kamera um einen Fokuspunkt (Welt-Up ``+Z``).

    Zustand: ``azimuth``/``elevation`` (Grad), ``distance`` (Fokusabstand),
    ``focus`` (3-Vektor). Der Fit-Abstand (aus dem letzten „Einpassen") setzt die
    Zoomgrenzen; vor dem ersten Fit gilt eine großzügige Absolut-Klemme.
    """

    azimuth: float = DEFAULT_AZIMUTH
    elevation: float = DEFAULT_ELEVATION
    distance: float = 3.0
    focus: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float64))
    fov_y: float = DEFAULT_FOV_Y
    _fit_distance: float = 3.0

    def __post_init__(self) -> None:
        self.focus = np.asarray(self.focus, dtype=np.float64).reshape(3).copy()
        self._clamp()

    # ── Interaktion ──────────────────────────────────────────────────────
    def orbit(self, d_azimuth: float, d_elevation: float) -> None:
        """Dreht um den Fokuspunkt; die Polhöhe bleibt geklemmt (±88°)."""
        self.azimuth = (self.azimuth + d_azimuth) % 360.0
        self.elevation = max(
            -_MAX_ELEVATION, min(_MAX_ELEVATION, self.elevation + d_elevation)
        )

    def zoom(self, factor: float) -> None:
        """Multipliziert den Fokusabstand (``<1`` = näher); geklemmt."""
        if not math.isfinite(factor) or factor <= 0.0:
            return
        self.distance *= factor
        self._clamp()

    def pan(self, dx: float, dy: float) -> None:
        """Verschiebt den Fokuspunkt in der Ansichtsebene (rechts/oben skaliert).

        ``dx``/``dy`` sind auf die Distanz normierte Anteile, damit das Pan-Tempo
        zoomunabhängig konsistent bleibt.
        """
        right, up = self._view_plane_axes()
        scale = self.distance * math.tan(math.radians(self.fov_y) / 2.0)
        self.focus = self.focus - right * (dx * scale) + up * (dy * scale)

    # ── Rahmen / Reset ───────────────────────────────────────────────────
    def fit_bounds(self, min_xyz: np.ndarray, max_xyz: np.ndarray) -> None:
        """Rahmt die Bounding-Box: Fokus = Zentrum, Distanz = Sphere/sin(fov/2)."""
        lo = np.asarray(min_xyz, dtype=np.float64).reshape(3)
        hi = np.asarray(max_xyz, dtype=np.float64).reshape(3)
        self.focus = (lo + hi) * 0.5
        radius = float(np.linalg.norm(hi - lo)) * 0.5
        if radius <= 1e-6:
            radius = 0.5
        half_fov = math.radians(self.fov_y) / 2.0
        self._fit_distance = radius / max(math.sin(half_fov), 1e-3) * _FIT_MARGIN
        self.distance = self._fit_distance
        self._clamp()

    def reset(self, min_xyz: np.ndarray, max_xyz: np.ndarray) -> None:
        """Standardkamera + Einpassen (Winkel/FOV auf Defaults, dann Fit)."""
        self.azimuth = DEFAULT_AZIMUTH
        self.elevation = DEFAULT_ELEVATION
        self.fov_y = DEFAULT_FOV_Y
        self.fit_bounds(min_xyz, max_xyz)

    # ── Matrizen ─────────────────────────────────────────────────────────
    def eye(self) -> np.ndarray:
        """Weltposition der Kamera (Fokus + Distanz · Richtung)."""
        az = math.radians(self.azimuth)
        el = math.radians(self.elevation)
        direction = np.array(
            [math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)],
            dtype=np.float64,
        )
        return self.focus + direction * self.distance

    def view_matrix(self) -> np.ndarray:
        up = np.array([0.0, 0.0, 1.0], dtype=np.float64)
        return look_at(self.eye(), self.focus, up)

    def projection_matrix(self, aspect: float) -> np.ndarray:
        near = max(self.distance * 0.01, 1e-3)
        far = self.distance * 10.0 + 10.0
        return perspective(self.fov_y, aspect, near, far)

    # ── intern ───────────────────────────────────────────────────────────
    def _view_plane_axes(self) -> tuple[np.ndarray, np.ndarray]:
        up = np.array([0.0, 0.0, 1.0], dtype=np.float64)
        forward = _normalize(self.focus - self.eye())
        right = _normalize(np.cross(forward, up))
        true_up = _normalize(np.cross(right, forward))
        return right, true_up

    def _clamp(self) -> None:
        lo = max(self._fit_distance * _MIN_DISTANCE_FACTOR, _ABS_MIN_DISTANCE)
        hi = self._fit_distance * _MAX_DISTANCE_FACTOR
        self.distance = max(lo, min(hi, self.distance))
