"""Qt-freier Geometriekern der 3D-Reliefvorschau (#592, Epic #582).

Rendererunabhängige, deterministische Aufbereitung eines kanonischen
:class:`~bgremover.height_map.HeightField` in ein begrenztes Grid-Mesh:
Decimation → Vertices/Normalen/Indizes/Gültigkeitsmaske. Es gibt hier **keinen**
Qt-, OpenGL- oder Viewer-Code – der Kern ist rein numerisch und in reinen
Unit-Tests ohne Display importierbar. Konventionen analog ``height_ops``/
``relief_preview``: keine Qt-, Datei- oder Netzzugriffe, deutsche Docstrings,
englische Identifier, strikte mypy-Typisierung.

Verbindliche Verträge (ADR
[ADR-2026-3d-reliefvorschau-renderer.md](docs/history/ADR-2026-3d-reliefvorschau-renderer.md)):

- **Koordinatensystem** (rechtshändig): ``+X`` = Bildspalten nach rechts,
  ``+Y`` = Bild-„oben" (Zeile 0 hat den größten Y-Wert), ``+Z`` = aus der Ebene
  zum Betrachter, **hell = hoch = +Z**. Ursprung im Zentrum der Grundfläche;
  die **längere** Grundseite spannt das Weltmaß ``1,0`` auf, die kürzere folgt
  dem Seitenverhältnis (physische Größe falls gesetzt, sonst Pixelverhältnis).
- **HEIGHT→Z:** ``z_norm = values / max_value`` (float32, für ``max_value`` 255
  **und** 65535 äquivalent). ``z = z_norm × BASE_Z_SCALE × exaggeration``;
  ``exaggeration`` ist reiner Anzeigeparameter und verändert die Quelldaten nie.
  Die Steigung ``slope = (∂z_base/∂x, ∂z_base/∂y)`` (exaggerations-unabhängig,
  ``z_base = z_norm × BASE_Z_SCALE``) wird zusätzlich mitgeführt, damit der
  Viewer die Überhöhung als Uniform ohne Mesh-Neubau anwenden kann.
- **Winding:** CCW von ``+Z`` betrachtet; gerendert wird doppelseitig.
- **Transparenz:** Die decimierte Deckung wird pro Grid-Vertex mit fester
  Schwelle ``COVERAGE_THRESHOLD`` binärisiert; ein Dreieck entsteht nur, wenn
  **alle drei** Vertices gültig sind → echte Löcher, keine Brückendreiecke.
- **Budgets:** Grid-Kantenlänge, Vertex- und Dreieckszahl sind je Qualitätsstufe
  hart gedeckelt (:class:`MeshQuality`); ein 40-MP-Bild erzeugt nie ein
  Vollauflösungs-Mesh, weil die Decimation **vor** jeder float-Expansion auf dem
  ``uint16``-Feld läuft. Das Downsampling arbeitet zeilenbandweise mit hartem
  64-MiB-Deckel (Muster von ``height_ops._MEDIAN_MAX_TEMP_BYTES``, #365).

Ausgabeformat (:class:`ReliefMesh`): ``positions`` ``float32 (N, 3)``,
``normals`` ``float32 (N, 3)`` (normiert), ``slope`` ``float32 (N, 2)``,
``indices`` ``uint32 (M, 3)`` (Vertexindex ``i*gw + j``). Alle Arrays sind nach
Konstruktion write-gelockt; die Quell-Payload wird nie kopiert oder mutiert.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

import numpy as np

from bgremover.height_map import HeightField

# Basis-Höhenskalierung: bei Überhöhung 1,0 entspricht der volle Höhenumfang
# 10 % der längeren Grundkante (flaches Druckrelief als neutraler Standard, ADR).
BASE_Z_SCALE = 0.1

# Feste Deckungs-Schwelle: gültig ⇔ decimierte Deckung ≥ 128 (ADR, MVP konstant).
COVERAGE_THRESHOLD = 128

# Hartes Temp-Budget der zeilenbandweisen Decimation (ADR: 64 MiB, #365-Muster).
_DECIMATE_MAX_TEMP_BYTES = 64 * 1024 * 1024


class ReliefMeshError(ValueError):
    """Ungültige Eingabe/Parameter der Geometrie-Aufbereitung."""


class MeshBuildCancelled(RuntimeError):
    """Der Mesh-Aufbau wurde kooperativ abgebrochen (kein vollständiges Mesh)."""


class MeshQuality(Enum):
    """Qualitätsstufen mit hartem Grid-/Vertex-/Dreiecks-Budget (ADR-Tabelle).

    ``grid_limit`` deckelt die **längere** Gitterseite nach der Decimation. Da
    beide Gitterseiten damit ``≤ grid_limit`` sind, gilt automatisch
    ``vertices ≤ grid_limit²`` und ``triangles ≤ 2·(grid_limit-1)²`` – die
    ADR-Budgets werden per Konstruktion eingehalten (und unten defensiv geprüft).
    """

    REDUCED = "reduced"
    STANDARD = "standard"
    HIGH = "high"

    @property
    def grid_limit(self) -> int:
        return _QUALITY_GRID_LIMIT[self]

    @property
    def max_vertices(self) -> int:
        return self.grid_limit * self.grid_limit

    @property
    def max_triangles(self) -> int:
        return 2 * (self.grid_limit - 1) * (self.grid_limit - 1)


_QUALITY_GRID_LIMIT: dict[MeshQuality, int] = {
    MeshQuality.REDUCED: 256,
    MeshQuality.STANDARD: 512,
    MeshQuality.HIGH: 1024,
}


@dataclass(frozen=True)
class ReliefMesh:
    """Rendererunabhängiges, unveränderliches Grid-Mesh (frozen numpy-DTO).

    ``positions`` sind die Weltkoordinaten (Z mit ``exaggeration`` skaliert),
    ``normals`` die zugehörigen normierten Oberflächennormalen, ``slope`` die
    exaggerations-unabhängige Steigung ``(∂z_base/∂x, ∂z_base/∂y)`` (für den
    Uniform-Pfad des Viewers), ``indices`` die Dreiecks-Vertexindizes (CCW).
    ``grid_size`` ist ``(gh, gw)`` des decimierten Felds, ``source_size`` die
    ``(width, height)`` der Quelle, ``decimation_factor`` das gerundete
    Verhältnis längere Quellseite ÷ längere Gitterseite (``1`` = keine
    Vereinfachung). Alle Arrays sind write-gelockt.
    """

    positions: np.ndarray
    normals: np.ndarray
    slope: np.ndarray
    indices: np.ndarray
    grid_size: tuple[int, int]
    source_size: tuple[int, int]
    quality: MeshQuality
    exaggeration: float
    decimation_factor: int

    def __post_init__(self) -> None:
        for arr in (self.positions, self.normals, self.slope, self.indices):
            arr.setflags(write=False)

    @property
    def vertex_count(self) -> int:
        return int(self.positions.shape[0])

    @property
    def triangle_count(self) -> int:
        return int(self.indices.shape[0])

    @property
    def is_decimated(self) -> bool:
        return self.decimation_factor > 1

    @property
    def bounds(self) -> tuple[np.ndarray, np.ndarray]:
        """Achsenparallele Bounding-Box ``(min_xyz, max_xyz)`` (leer → Nullbox)."""
        if self.vertex_count == 0:
            zero = np.zeros(3, dtype=np.float32)
            return zero, zero.copy()
        return self.positions.min(axis=0), self.positions.max(axis=0)


@dataclass(frozen=True)
class MeshCacheKey:
    """Deterministischer, hashbarer Schlüssel aller geometriebestimmenden Größen.

    Enthält bewusst **keine** reinen Anzeige-Zustände (Kamera, Licht, Theme) und
    **nicht** die Überhöhung (Uniform, ADR): nur Inhaltsrevision, Canvas-Größe,
    effektives Seitenverhältnis, Qualität und Deckungsschwelle. Zwei logisch
    gleiche Zustände liefern denselben Schlüssel; Kamera/Licht/Überhöhung
    erzwingen keinen Rebuild.
    """

    content_revision: int
    source_size: tuple[int, int]
    aspect: tuple[float, float]
    quality: MeshQuality
    coverage_threshold: int = COVERAGE_THRESHOLD


def mesh_cache_key(
    *,
    content_revision: int,
    source_size: tuple[int, int],
    quality: MeshQuality,
    physical_size_mm: tuple[float, float] | None = None,
) -> MeshCacheKey:
    """Baut den :class:`MeshCacheKey` inklusive normalisiertem Seitenverhältnis."""
    aspect = _base_aspect(source_size, physical_size_mm)
    return MeshCacheKey(
        content_revision=content_revision,
        source_size=source_size,
        aspect=aspect,
        quality=quality,
    )


def _base_aspect(
    source_size: tuple[int, int],
    physical_size_mm: tuple[float, float] | None,
) -> tuple[float, float]:
    """Normalisiertes Grundflächen-Seitenverhältnis (längere Seite = 1,0).

    Nutzt die physische Größe (falls positiv gesetzt), sonst das Pixelverhältnis.
    """
    if physical_size_mm is not None:
        w, h = physical_size_mm
        if w > 0.0 and h > 0.0:
            longer = max(w, h)
            return (float(w) / longer, float(h) / longer)
    pw, ph = source_size
    longer_px = max(pw, ph)
    if longer_px <= 0:
        raise ReliefMeshError(f"Quellgröße muss positiv sein, war {source_size}")
    return (pw / longer_px, ph / longer_px)


def _target_grid(width: int, height: int, grid_limit: int) -> tuple[int, int]:
    """Zielgitter ``(gh, gw)`` nach Decimation, seitenverhältniserhaltend.

    Ist die längere Quellseite ``≤ grid_limit``, bleibt das Gitter identisch zur
    Quelle (keine Decimation). Sonst wird die längere Seite exakt auf
    ``grid_limit`` gesetzt und die kürzere proportional (mindestens 1).
    """
    if width <= 0 or height <= 0:
        raise ReliefMeshError(f"Quellgröße muss positiv sein, war {width}x{height}")
    longer = max(width, height)
    if longer <= grid_limit:
        return height, width
    if width >= height:
        gw = grid_limit
        gh = max(1, int(round(height * grid_limit / width)))
    else:
        gh = grid_limit
        gw = max(1, int(round(width * grid_limit / height)))
    return gh, gw


def _block_edges(n: int, groups: int) -> np.ndarray:
    """Monotone Blockgrenzen (Länge ``groups+1``) für Area-Downsampling.

    ``edges[0] == 0``, ``edges[groups] == n``; jeder Block umfasst ``≥ 1`` Pixel
    (garantiert, weil ``groups ≤ n``). Deterministisch über gerundete
    ``linspace``-Grenzen – randerhaltend (Zeile/Spalte 0 bzw. ``n-1`` bleiben in
    den äußersten Blöcken).
    """
    return np.round(np.linspace(0, n, groups + 1)).astype(np.int64)


def _check_cancel(cancel: Callable[[], bool] | None) -> None:
    if cancel is not None and cancel():
        raise MeshBuildCancelled("Mesh-Aufbau abgebrochen")


def _report(progress: Callable[[float], None] | None, value: float) -> None:
    if progress is not None:
        progress(max(0.0, min(1.0, value)))


def decimate_field(
    field: HeightField,
    grid_h: int,
    grid_w: int,
    *,
    max_temp_bytes: int = _DECIMATE_MAX_TEMP_BYTES,
    cancel: Callable[[], bool] | None = None,
    progress: Callable[[float], None] | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Area-Downsampling des ``uint16``-Höhenfelds auf ``(grid_h, grid_w)``.

    Deckungsgewichtete Höhen-Blockmittelung (``z = Σ(values·coverage)/Σ(coverage)``):
    Pixel mit ``coverage == 0`` tragen keinen Höhenbeitrag (kein „Bleed" beliebiger
    Werte unter Transparenz in Randgeometrie); bei ``Σ(coverage) == 0`` ist der
    Block ungültig, der Höhenwert dort deterministisch ``0``. Die Deckung selbst
    wird **ungewichtet** blockgemittelt und erst am Vertex binärisiert. Rückgabe
    ``(values_u16 (gh, gw), coverage_u8 (gh, gw))``.

    Die Spaltenreduktion läuft zeilenbandweise; der Bandpuffer bleibt hart unter
    ``max_temp_bytes`` (Bildmaß-unabhängiger Zusatzspeicher). Gleiche Gittergröße
    wie die Quelle ergibt eine reine Kopie (Identitäts-Decimation).
    """
    values = field.values
    coverage = field.coverage
    h, w = values.shape[:2]
    if grid_h <= 0 or grid_w <= 0 or grid_h > h or grid_w > w:
        raise ReliefMeshError(
            f"Zielgitter {grid_h}x{grid_w} unzulässig für Quelle {h}x{w}"
        )
    if (grid_h, grid_w) == (h, w):
        return values.copy(), coverage.copy()

    col_edges = _block_edges(w, grid_w)
    row_edges = _block_edges(h, grid_h)
    # Persistente Akkumulatoren nur in Zielgröße (klein). Die Reduktion läuft in
    # **Ausgabezeilen-Bändern**: je Band werden nur die zugehörigen Quellzeilen
    # geladen und sofort auf ihre Zielzeilen reduziert – der transiente Puffer
    # bleibt vom Bildmaß unabhängig (Deckel ``max_temp_bytes``, zwei float64-
    # Arbeitsarrays cov + weighted eingerechnet).
    wsum = np.empty((grid_h, grid_w), dtype=np.float64)
    csum = np.empty((grid_h, grid_w), dtype=np.float64)
    # Budget für die drei gleichzeitig lebenden Band-Arbeitsarrays (cov,
    # weighted, Spalten-Reduktion) – hält den transienten Peak vom Bildmaß
    # unabhängig unter dem Deckel.
    src_rows_budget = max(1, max_temp_bytes // (w * 8 * 3))
    gi = 0
    while gi < grid_h:
        _check_cancel(cancel)
        # So viele Zielzeilen bündeln, dass ihre Quellzeilen im Temp-Budget bleiben
        # (mindestens eine Zielzeile, auch wenn ihr Block das Budget überschreitet).
        gj = gi + 1
        while gj < grid_h and (row_edges[gj + 1] - row_edges[gi]) <= src_rows_budget:
            gj += 1
        src0, src1 = int(row_edges[gi]), int(row_edges[gj])
        cov = coverage[src0:src1].astype(np.float64)
        # weighted = values·cov in-place (kein separater values-float-Puffer).
        weighted = values[src0:src1].astype(np.float64)
        weighted *= cov
        wc = np.add.reduceat(weighted, col_edges[:-1], axis=1)
        cc = np.add.reduceat(cov, col_edges[:-1], axis=1)
        local_edges = row_edges[gi:gj + 1] - src0
        wsum[gi:gj] = np.add.reduceat(wc, local_edges[:-1], axis=0)
        csum[gi:gj] = np.add.reduceat(cc, local_edges[:-1], axis=0)
        gi = gj
        _report(progress, 0.6 * gi / grid_h)
    _check_cancel(cancel)

    row_counts = np.diff(row_edges).astype(np.float64)
    col_counts = np.diff(col_edges).astype(np.float64)
    counts = row_counts[:, None] * col_counts[None, :]

    covered = csum > 0.0
    height_mean = np.where(covered, wsum / np.where(covered, csum, 1.0), 0.0)
    values_u16 = np.clip(
        np.rint(height_mean), 0, field.max_value
    ).astype(np.uint16)
    coverage_u8 = np.clip(np.rint(csum / counts), 0, 255).astype(np.uint8)
    _report(progress, 0.6)
    return values_u16, coverage_u8


def _grid_gradient(z: np.ndarray, axis: int) -> np.ndarray:
    """Deterministische zentrale Differenz je Gitterschritt (auch 1-breit).

    Identische Kantenbehandlung wie ``relief_preview._gradient`` (Vorwärts-/
    Rückwärtsdifferenz an den Rändern), damit 2D- und 3D-Relief konsistent sind.
    Rechnet im dtype der Eingabe (``float32`` im Geometriepfad – halber
    Speicher, für Anzeige-Normalen ausreichend präzise).
    """
    result = np.zeros(z.shape, dtype=z.dtype)
    length = z.shape[axis]
    if length <= 1:
        return result
    if axis == 0:
        result[0, :] = z[1, :] - z[0, :]
        result[-1, :] = z[-1, :] - z[-2, :]
        if length > 2:
            result[1:-1, :] = (z[2:, :] - z[:-2, :]) * 0.5
    else:
        result[:, 0] = z[:, 1] - z[:, 0]
        result[:, -1] = z[:, -1] - z[:, -2]
        if length > 2:
            result[:, 1:-1] = (z[:, 2:] - z[:, :-2]) * 0.5
    return result


def _extents(aspect: tuple[float, float]) -> tuple[float, float]:
    """Weltausdehnung ``(ext_x, ext_y)`` – längere Seite ``1,0``."""
    ax, ay = aspect
    longer = max(ax, ay)
    if longer <= 0.0:
        raise ReliefMeshError(f"Seitenverhältnis muss positiv sein, war {aspect}")
    return ax / longer, ay / longer


def build_relief_mesh(
    field: HeightField,
    quality: MeshQuality = MeshQuality.STANDARD,
    *,
    exaggeration: float = 1.0,
    physical_size_mm: tuple[float, float] | None = None,
    max_temp_bytes: int = _DECIMATE_MAX_TEMP_BYTES,
    cancel: Callable[[], bool] | None = None,
    progress: Callable[[float], None] | None = None,
) -> ReliefMesh:
    """Baut ein begrenztes Grid-Mesh aus ``field`` (Decimation + Geometrie).

    Reihenfolge: Zielgitter aus Budget bestimmen → Area-Downsampling (nur auf
    ``uint16``, vor jeder float-Expansion) → Weltkoordinaten/Steigungen/Normalen
    → gültigkeitsbewusste Dreiecksindizierung. Die Quelldaten werden nie mutiert;
    ``exaggeration`` skaliert ausschließlich die Z-Positionen und Normalen der
    **Ausgabe** (Standard 1,0). ``cancel``/``progress`` werden an den Bandgrenzen
    ausgewertet; ein Abbruch wirft :class:`MeshBuildCancelled` (nie ein
    unvollständiges, fälschlich als fertig markiertes Mesh).
    """
    if not np.isfinite(exaggeration) or exaggeration <= 0.0:
        raise ReliefMeshError(
            f"exaggeration muss endlich und > 0 sein, war {exaggeration!r}"
        )
    width, height = field.size
    grid_limit = quality.grid_limit
    grid_h, grid_w = _target_grid(width, height, grid_limit)
    _report(progress, 0.0)

    values_u16, coverage_u8 = decimate_field(
        field, grid_h, grid_w,
        max_temp_bytes=max_temp_bytes, cancel=cancel, progress=progress,
    )
    _check_cancel(cancel)

    aspect = _base_aspect((width, height), physical_size_mm)
    ext_x, ext_y = _extents(aspect)

    # Weltkoordinaten der Zellzentren (float32-Geometriepfad): Ränder sind die
    # äußersten Zellzentren.
    if grid_w > 1:
        xs = (np.arange(grid_w, dtype=np.float32) / (grid_w - 1) - 0.5) * ext_x
    else:
        xs = np.zeros(1, dtype=np.float32)
    if grid_h > 1:
        # +Y = Bild-oben: Zeile 0 bekommt den größten Y-Wert.
        ys = (0.5 - np.arange(grid_h, dtype=np.float32) / (grid_h - 1)) * ext_y
    else:
        ys = np.zeros(1, dtype=np.float32)

    z_norm = values_u16.astype(np.float32) / np.float32(field.max_value)
    z_base = z_norm * np.float32(BASE_Z_SCALE)
    z = z_base * np.float32(exaggeration)

    xx = np.broadcast_to(xs[None, :], (grid_h, grid_w))
    yy = np.broadcast_to(ys[:, None], (grid_h, grid_w))
    positions = np.stack([xx.ravel(), yy.ravel(), z.ravel()], axis=1).astype(np.float32)

    # Steigung des Basis-Reliefs (exaggerations-unabhängig) in Weltkoordinaten.
    dx_step = np.float32(ext_x / (grid_w - 1) if grid_w > 1 else 1.0)
    dy_step = np.float32(ext_y / (grid_h - 1) if grid_h > 1 else 1.0)
    dz_base_dx = _grid_gradient(z_base, axis=1) / dx_step
    # y nimmt mit dem Zeilenindex ab (y = y0 - i·dy_step) → Vorzeichenumkehr.
    dz_base_dy = -_grid_gradient(z_base, axis=0) / dy_step
    slope = np.stack([dz_base_dx.ravel(), dz_base_dy.ravel()], axis=1).astype(np.float32)

    # Normalen der überhöhten Fläche: n = normalize(-∂z/∂x, -∂z/∂y, 1).
    exagg32 = np.float32(exaggeration)
    nx = -dz_base_dx * exagg32
    ny = -dz_base_dy * exagg32
    nz = np.ones_like(nx)
    inv_len = np.float32(1.0) / np.sqrt(nx * nx + ny * ny + nz * nz)
    normals = np.stack(
        [(nx * inv_len).ravel(), (ny * inv_len).ravel(), (nz * inv_len).ravel()],
        axis=1,
    ).astype(np.float32)
    _report(progress, 0.8)

    indices = _build_indices(coverage_u8, grid_h, grid_w, cancel=cancel)
    _report(progress, 1.0)

    decimation_factor = max(1, int(round(max(width, height) / max(grid_w, grid_h))))
    mesh = ReliefMesh(
        positions=positions,
        normals=normals,
        slope=slope,
        indices=indices,
        grid_size=(grid_h, grid_w),
        source_size=(width, height),
        quality=quality,
        exaggeration=float(exaggeration),
        decimation_factor=decimation_factor,
    )
    _validate_budget(mesh, quality)
    return mesh


def _build_indices(
    coverage_u8: np.ndarray,
    grid_h: int,
    grid_w: int,
    *,
    cancel: Callable[[], bool] | None = None,
) -> np.ndarray:
    """Dreiecks-Vertexindizes (CCW) – ein Dreieck nur bei drei gültigen Vertices.

    Gültig ⇔ ``coverage ≥ COVERAGE_THRESHOLD``. Ein Quad ``(i,j)`` liefert die
    Dreiecke ``(v00, v10, v11)`` und ``(v00, v11, v01)`` (CCW von ``+Z``); nur
    Dreiecke mit ausschließlich gültigen Ecken werden aufgenommen (echte Löcher,
    keine Brückendreiecke). Ergebnis ``uint32 (M, 3)``.
    """
    if grid_h < 2 or grid_w < 2:
        return np.empty((0, 3), dtype=np.uint32)
    _check_cancel(cancel)
    valid = coverage_u8 >= COVERAGE_THRESHOLD
    v00 = valid[:-1, :-1]
    v01 = valid[:-1, 1:]
    v10 = valid[1:, :-1]
    v11 = valid[1:, 1:]

    idx = np.arange(grid_h * grid_w, dtype=np.uint32).reshape(grid_h, grid_w)
    i00 = idx[:-1, :-1]
    i01 = idx[:-1, 1:]
    i10 = idx[1:, :-1]
    i11 = idx[1:, 1:]

    # Speicherschonend: keine getrennten ``tri_a``/``tri_b`` plus Concatenate
    # (drei Vollkopien), sondern spaltenweise Masken-Selektion direkt in ein
    # vorab dimensioniertes Ergebnis (nur eine Spalte je Zeitpunkt transient).
    tri_a_ok = v00 & v10 & v11
    tri_b_ok = v00 & v11 & v01
    na = int(tri_a_ok.sum())
    nb = int(tri_b_ok.sum())
    out = np.empty((na + nb, 3), dtype=np.uint32)
    for col, src in enumerate((i00, i10, i11)):
        out[:na, col] = src[tri_a_ok]
    for col, src in enumerate((i00, i11, i01)):
        out[na:, col] = src[tri_b_ok]
    return out


def _validate_budget(mesh: ReliefMesh, quality: MeshQuality) -> None:
    """Defensive Budgetprüfung (per Konstruktion erfüllt, aber verifiziert)."""
    if mesh.vertex_count > quality.max_vertices:
        raise ReliefMeshError(
            f"Vertexbudget verletzt: {mesh.vertex_count} > {quality.max_vertices}"
        )
    if mesh.triangle_count > quality.max_triangles:
        raise ReliefMeshError(
            f"Dreiecksbudget verletzt: {mesh.triangle_count} > "
            f"{quality.max_triangles}"
        )
