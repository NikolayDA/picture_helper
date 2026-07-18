"""Tests des Qt-freien 3D-Geometriekerns (#592, Epic #582).

Analytische Referenzen (Ebene, X-/Y-Rampe, Stufe, Impuls, maskierte Inseln),
Budget-/Decimation-Grenzen, Determinismus, Nicht-Mutation und Abbruch. Kein Test
benötigt einen Display-/Grafik-Kontext.
"""
from __future__ import annotations

import hashlib

import numpy as np
import pytest

from bgremover.height_map import HEIGHT_MAX_8BIT, HEIGHT_MAX_16BIT, HeightField
from bgremover.relief_mesh import (
    BASE_Z_SCALE,
    MeshBuildCancelled,
    MeshQuality,
    ReliefMeshError,
    build_relief_mesh,
    decimate_field,
    mesh_cache_key,
)


def _field(values: np.ndarray, coverage: np.ndarray | None = None,
           max_value: int = HEIGHT_MAX_16BIT) -> HeightField:
    if coverage is None:
        coverage = np.full(values.shape, 255, dtype=np.uint8)
    return HeightField(values.astype(np.uint16), coverage, max_value)


def _full(h: int, w: int, value: int) -> HeightField:
    return _field(np.full((h, w), value, dtype=np.uint16))


# ── Ebene / Grundgeometrie ───────────────────────────────────────────────
def test_flat_field_has_constant_up_normal_and_closed_grid() -> None:
    mesh = build_relief_mesh(_full(30, 30, 5000), MeshQuality.STANDARD)
    assert mesh.vertex_count == 30 * 30
    assert mesh.triangle_count == 2 * 29 * 29
    assert np.allclose(mesh.normals[:, 2], 1.0, atol=1e-5)
    assert np.abs(mesh.normals[:, :2]).max() < 1e-6


def test_aspect_ratio_longer_side_spans_unit_extent() -> None:
    mesh = build_relief_mesh(_full(20, 40, 0), MeshQuality.STANDARD)  # W=40 länger
    xs, ys = mesh.positions[:, 0], mesh.positions[:, 1]
    assert xs.min() == pytest.approx(-0.5) and xs.max() == pytest.approx(0.5)
    assert ys.min() == pytest.approx(-0.25) and ys.max() == pytest.approx(0.25)


def test_physical_size_overrides_pixel_aspect() -> None:
    mesh = build_relief_mesh(
        _full(40, 40, 0), MeshQuality.STANDARD, physical_size_mm=(100.0, 50.0))
    xs, ys = mesh.positions[:, 0], mesh.positions[:, 1]
    assert xs.max() - xs.min() == pytest.approx(1.0)
    assert ys.max() - ys.min() == pytest.approx(0.5)


def test_height_maps_to_z_independent_of_bit_depth() -> None:
    # 8-Bit voll (255) und 16-Bit voll (65535) ergeben identisches z_norm=1.
    m8 = build_relief_mesh(_full(10, 10, 255).__class__(
        np.full((10, 10), 255, np.uint16), np.full((10, 10), 255, np.uint8),
        HEIGHT_MAX_8BIT), MeshQuality.STANDARD)
    m16 = build_relief_mesh(_full(10, 10, HEIGHT_MAX_16BIT), MeshQuality.STANDARD)
    assert m8.positions[:, 2].max() == pytest.approx(BASE_Z_SCALE)
    assert m16.positions[:, 2].max() == pytest.approx(BASE_Z_SCALE)


# ── Rampen / Normalen ────────────────────────────────────────────────────
def test_x_ramp_normal_points_against_increase() -> None:
    ramp = np.tile(
        np.linspace(0, HEIGHT_MAX_16BIT, 50, dtype=np.uint16), (30, 1))
    mesh = build_relief_mesh(_field(ramp), MeshQuality.STANDARD)
    assert mesh.normals[:, 0].mean() < 0.0          # nx zeigt gegen +x
    assert abs(mesh.normals[:, 1].mean()) < 1e-6     # ny ~ 0
    # z monoton entlang der ersten Zeile
    row0 = mesh.positions[:50, 2]
    assert np.all(np.diff(row0) >= -1e-9)


def test_y_ramp_normal_points_along_y() -> None:
    ramp = np.tile(
        np.linspace(0, HEIGHT_MAX_16BIT, 30, dtype=np.uint16)[:, None], (1, 40))
    mesh = build_relief_mesh(_field(ramp), MeshQuality.STANDARD)
    assert abs(mesh.normals[:, 0].mean()) < 1e-6
    assert abs(mesh.normals[:, 1].mean()) > 1e-3


def test_exaggeration_scales_z_and_adjusts_normals() -> None:
    ramp = np.tile(np.linspace(0, HEIGHT_MAX_16BIT, 40, dtype=np.uint16), (40, 1))
    m1 = build_relief_mesh(_field(ramp), MeshQuality.STANDARD, exaggeration=1.0)
    m2 = build_relief_mesh(_field(ramp), MeshQuality.STANDARD, exaggeration=2.0)
    assert m2.positions[:, 2].max() == pytest.approx(2.0 * m1.positions[:, 2].max())
    # Steilere Fläche → Normale stärker aus der Vertikalen gekippt.
    assert abs(m2.normals[:, 0].mean()) > abs(m1.normals[:, 0].mean())
    assert np.all(np.isfinite(m2.normals))
    # slope ist exaggerations-unabhängig (Uniform-Pfad des Viewers).
    assert np.allclose(m1.slope, m2.slope)


# ── Transparenz / Löcher ─────────────────────────────────────────────────
def test_transparent_center_creates_hole_without_bridges() -> None:
    cov = np.full((20, 20), 255, dtype=np.uint8)
    cov[8:12, 8:12] = 0
    mesh = build_relief_mesh(_field(np.zeros((20, 20), np.uint16), cov),
                             MeshQuality.STANDARD)
    full = build_relief_mesh(_full(20, 20, 0), MeshQuality.STANDARD)
    assert mesh.triangle_count < full.triangle_count
    # Kein Dreieck referenziert einen ungedeckten Vertex.
    invalid = np.where(cov.ravel() < 128)[0]
    assert not np.isin(mesh.indices.ravel(), invalid).any()


def test_fully_transparent_field_yields_no_triangles() -> None:
    cov = np.zeros((15, 15), dtype=np.uint8)
    mesh = build_relief_mesh(_field(np.zeros((15, 15), np.uint16), cov),
                             MeshQuality.STANDARD)
    assert mesh.triangle_count == 0
    lo, hi = mesh.bounds
    assert lo.shape == (3,)


# ── Budgets / Decimation ─────────────────────────────────────────────────
@pytest.mark.parametrize("quality,limit", [
    (MeshQuality.REDUCED, 256),
    (MeshQuality.STANDARD, 512),
    (MeshQuality.HIGH, 1024),
])
def test_budget_respected_for_large_input(quality: MeshQuality, limit: int) -> None:
    big = _full(5164, 7746, 0)  # ~40 MP
    mesh = build_relief_mesh(big, quality)
    gh, gw = mesh.grid_size
    assert max(gh, gw) <= limit
    assert mesh.vertex_count <= quality.max_vertices
    assert mesh.triangle_count <= quality.max_triangles
    assert mesh.is_decimated and mesh.decimation_factor > 1


def test_decimation_preserves_edges_and_min_max() -> None:
    ramp = np.tile(
        np.linspace(0, HEIGHT_MAX_16BIT, 1000, dtype=np.uint16), (1000, 1))
    values, coverage = decimate_field(_field(ramp), 100, 100)
    assert values.shape == (100, 100)
    # Randspalten behalten die Extremwerte (± eine Quantisierungsstufe).
    assert values[:, 0].max() <= 700
    assert values[:, -1].min() >= HEIGHT_MAX_16BIT - 700
    # Monotonie bleibt erhalten.
    assert np.all(np.diff(values[0].astype(int)) >= 0)


def test_coverage_weighted_decimation_ignores_uncovered_height() -> None:
    # Ein Block: eine Hälfte hoch aber ungedeckt, andere niedrig und gedeckt.
    values = np.zeros((2, 4), np.uint16)
    values[:, :2] = 60000       # ungedeckt
    values[:, 2:] = 1000        # gedeckt
    coverage = np.zeros((2, 4), np.uint8)
    coverage[:, 2:] = 255
    v, c = decimate_field(_field(values, coverage), 1, 1)
    # Höhe nur aus dem gedeckten Bereich → nahe 1000, nicht ~30500.
    assert v[0, 0] == 1000


def test_banded_decimation_matches_single_band() -> None:
    rng = np.random.default_rng(7)
    values = rng.integers(0, HEIGHT_MAX_16BIT, (400, 400), dtype=np.uint16)
    field = _field(values)
    a, ca = decimate_field(field, 80, 80, max_temp_bytes=1024)      # viele Bänder
    b, cb = decimate_field(field, 80, 80, max_temp_bytes=1 << 30)   # ein Band
    assert np.array_equal(a, b) and np.array_equal(ca, cb)


# ── Determinismus / Nicht-Mutation / Abbruch ─────────────────────────────
def test_build_is_deterministic() -> None:
    rng = np.random.default_rng(3)
    field = _field(rng.integers(0, HEIGHT_MAX_16BIT, (300, 200), dtype=np.uint16))
    m1 = build_relief_mesh(field, MeshQuality.STANDARD)
    m2 = build_relief_mesh(field, MeshQuality.STANDARD)
    assert np.array_equal(m1.positions, m2.positions)
    assert np.array_equal(m1.normals, m2.normals)
    assert np.array_equal(m1.indices, m2.indices)


def test_source_field_not_mutated() -> None:
    rng = np.random.default_rng(5)
    values = rng.integers(0, HEIGHT_MAX_16BIT, (256, 256), dtype=np.uint16)
    coverage = rng.integers(0, 256, (256, 256), dtype=np.uint8)
    field = _field(values, coverage)
    before_v = hashlib.sha256(field.values.tobytes()).hexdigest()
    before_c = hashlib.sha256(field.coverage.tobytes()).hexdigest()
    build_relief_mesh(field, MeshQuality.HIGH, exaggeration=3.0)
    assert hashlib.sha256(field.values.tobytes()).hexdigest() == before_v
    assert hashlib.sha256(field.coverage.tobytes()).hexdigest() == before_c


def test_output_arrays_are_write_locked() -> None:
    mesh = build_relief_mesh(_full(10, 10, 100), MeshQuality.STANDARD)
    for arr in (mesh.positions, mesh.normals, mesh.slope, mesh.indices):
        assert arr.flags.writeable is False


def test_cancel_raises_and_yields_no_mesh() -> None:
    big = _full(4000, 4000, 0)
    with pytest.raises(MeshBuildCancelled):
        build_relief_mesh(big, MeshQuality.STANDARD, cancel=lambda: True)


def test_progress_is_monotonic() -> None:
    seen: list[float] = []
    build_relief_mesh(_full(600, 600, 100), MeshQuality.STANDARD,
                      progress=seen.append)
    assert seen and seen[-1] == pytest.approx(1.0)
    assert all(b >= a - 1e-9 for a, b in zip(seen, seen[1:], strict=False))


# ── Fehlerfälle / Cache-Key ──────────────────────────────────────────────
def test_invalid_exaggeration_rejected() -> None:
    with pytest.raises(ReliefMeshError):
        build_relief_mesh(_full(4, 4, 0), exaggeration=0.0)


def test_degenerate_shapes_do_not_crash() -> None:
    for shape in [(1, 1), (1, 8), (8, 1)]:
        mesh = build_relief_mesh(_full(*shape, 100), MeshQuality.STANDARD)
        assert np.all(np.isfinite(mesh.normals))
        assert mesh.triangle_count == 0  # keine 2D-Fläche aufspannbar


def test_cache_key_ignores_camera_but_tracks_geometry() -> None:
    k1 = mesh_cache_key(content_revision=1, source_size=(100, 100),
                        quality=MeshQuality.STANDARD)
    k2 = mesh_cache_key(content_revision=1, source_size=(100, 100),
                        quality=MeshQuality.STANDARD)
    assert k1 == k2
    k3 = mesh_cache_key(content_revision=2, source_size=(100, 100),
                        quality=MeshQuality.STANDARD)
    k4 = mesh_cache_key(content_revision=1, source_size=(100, 100),
                        quality=MeshQuality.HIGH)
    k5 = mesh_cache_key(content_revision=1, source_size=(100, 100),
                        quality=MeshQuality.STANDARD, physical_size_mm=(50.0, 10.0))
    assert k1 != k3 and k1 != k4 and k1 != k5
