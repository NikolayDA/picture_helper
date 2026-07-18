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
