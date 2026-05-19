"""Tests für Worker-Klassen: Fehlerpfade, Grössenvalidierung und Concurrent-Load-Schutz."""
import io
from unittest.mock import patch

import pytest
from PIL import Image

from BgRemover import (
    AIWorker,
    ImageCanvas,
    ImageLoadWorker,
    _MAX_MEGAPIXELS,
)


# ─────────────────────────────────────────────────────────────
# ImageLoadWorker – Fehlerpfade
# ─────────────────────────────────────────────────────────────

def test_image_load_worker_error_on_missing_file(qapp) -> None:
    worker = ImageLoadWorker("/nonexistent/path/image.png")
    errors: list[str] = []
    worker.error.connect(errors.append)
    worker.run()
    assert len(errors) == 1
    assert errors[0]  # Fehlermeldung nicht leer


def test_image_load_worker_error_on_corrupt_file(qapp, tmp_path) -> None:
    corrupt = tmp_path / "bad.png"
    corrupt.write_bytes(b"this is not a png")
    worker = ImageLoadWorker(str(corrupt))
    errors: list[str] = []
    worker.error.connect(errors.append)
    worker.run()
    assert len(errors) == 1


def test_image_load_worker_rejects_oversized_image(qapp, tmp_path) -> None:
    """Bilder grösser als _MAX_MEGAPIXELS sollen einen Fehler emittieren."""
    # Erstelle ein Dummy-Image mit überschrittener Pixelzahl per Mock,
    # ohne tatsächlich eine riesige Datei zu schreiben.
    small = tmp_path / "small.png"
    Image.new("RGB", (10, 10), (1, 2, 3)).save(small)

    oversized_mp = _MAX_MEGAPIXELS + 1
    fake_size = (int((oversized_mp * 1_000_000) ** 0.5),) * 2

    errors: list[str] = []
    finished: list = []
    worker = ImageLoadWorker(str(small))
    worker.error.connect(errors.append)
    worker.finished.connect(lambda img, p: finished.append(img))

    with patch("bgremover.workers.Image.open") as mock_open:
        mock_img = mock_open.return_value
        mock_img.width, mock_img.height = fake_size
        worker.run()

    assert len(errors) == 1
    assert str(_MAX_MEGAPIXELS) in errors[0]
    assert len(finished) == 0


def test_image_load_worker_accepts_normal_size(qapp, tmp_path) -> None:
    p = tmp_path / "ok.png"
    Image.new("RGB", (100, 100), (1, 2, 3)).save(p)
    worker = ImageLoadWorker(str(p))
    finished: list = []
    errors: list[str] = []
    worker.finished.connect(lambda img, path: finished.append(img))
    worker.error.connect(errors.append)
    worker.run()
    assert len(finished) == 1
    assert len(errors) == 0


# ─────────────────────────────────────────────────────────────
# ImageCanvas – synchroner Ladepfad (Drag & Drop)
# ─────────────────────────────────────────────────────────────

def test_canvas_load_image_rejects_oversized(qapp, tmp_path) -> None:
    small = tmp_path / "small.png"
    Image.new("RGB", (10, 10), (1, 2, 3)).save(small)

    canvas = ImageCanvas()
    msgs: list[str] = []
    canvas.statusMsg.connect(msgs.append)

    oversized_mp = _MAX_MEGAPIXELS + 1
    fake_size = (int((oversized_mp * 1_000_000) ** 0.5),) * 2

    with patch("bgremover.canvas.Image.open") as mock_open:
        mock_img = mock_open.return_value
        mock_img.width, mock_img.height = fake_size
        canvas.load_image(str(small))

    # Kein Bild geladen, Fehlermeldung in Status
    assert canvas._pil is None
    assert any(str(_MAX_MEGAPIXELS) in m for m in msgs)


# ─────────────────────────────────────────────────────────────
# AIWorker – Fehlerpfade
# ─────────────────────────────────────────────────────────────

@pytest.fixture()
def _mock_rembg():
    """Stellt sicher, dass rembg_remove im Modul mockbar ist (auch wenn nicht installiert)."""
    import bgremover.workers as _m
    had = hasattr(_m, "rembg_remove")
    if not had:
        _m.rembg_remove = None  # Platzhalter damit patch() greift
    yield
    if not had:
        delattr(_m, "rembg_remove")


def test_ai_worker_error_signal_on_bad_input(qapp, _mock_rembg) -> None:
    """AIWorker soll error emittieren wenn rembg_remove fehlschlägt."""
    img = Image.new("RGBA", (4, 4), (0, 0, 0, 255))
    worker = AIWorker(img)
    errors: list[str] = []
    finished: list = []
    worker.error.connect(errors.append)
    worker.finished.connect(finished.append)

    with patch("bgremover.workers.rembg_remove", side_effect=RuntimeError("mock rembg failure")):
        worker.run()

    assert len(errors) == 1
    assert "RuntimeError" in errors[0] or "mock rembg failure" in errors[0]
    assert len(finished) == 0


def test_ai_worker_finished_signal_on_success(qapp, _mock_rembg) -> None:
    img = Image.new("RGBA", (4, 4), (0, 0, 0, 255))
    worker = AIWorker(img)
    finished: list = []
    errors: list[str] = []
    worker.finished.connect(finished.append)
    worker.error.connect(errors.append)

    result_img = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
    result_buf = io.BytesIO()
    result_img.save(result_buf, format="PNG")

    with patch("bgremover.workers.rembg_remove", return_value=result_buf.getvalue()):
        worker.run()

    assert len(finished) == 1
    assert len(errors) == 0


# ─────────────────────────────────────────────────────────────
# Canvas – Versionszähler (Stale-Check für KI-Ergebnis)
# ─────────────────────────────────────────────────────────────

def test_canvas_version_increments_on_load(qapp, tmp_path) -> None:
    canvas = ImageCanvas()
    assert canvas._version == 0
    img = Image.new("RGBA", (10, 10), (1, 2, 3, 255))
    canvas.apply_loaded_image(img, str(tmp_path / "x.png"))
    assert canvas._version == 1
    canvas.apply_loaded_image(img, str(tmp_path / "y.png"))
    assert canvas._version == 2


def test_canvas_version_not_incremented_by_undo(qapp, tmp_path) -> None:
    canvas = ImageCanvas()
    img = Image.new("RGBA", (10, 10), (1, 2, 3, 255))
    canvas.apply_loaded_image(img, str(tmp_path / "x.png"))
    v_after_load = canvas._version
    # Undo verändert die Version nicht – nur apply_loaded_image tut das
    canvas._apply_pil(img.copy(), push=True, desc="test-edit")
    canvas.undo()
    assert canvas._version == v_after_load
