"""Tests für Worker-Klassen: Fehlerpfade, Grössenvalidierung und Concurrent-Load-Schutz."""
import io
from unittest.mock import patch

import pytest
from PIL import Image

from bgremover import (
    AIWorker,
    ImageCanvas,
    ImageLoadWorker,
    MainWindow,
)
from bgremover.constants import _MAX_MEGAPIXELS

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
        mock_img.format = "PNG"
        mock_img.width, mock_img.height = fake_size
        worker.run()

    assert len(errors) == 1
    assert str(_MAX_MEGAPIXELS) in errors[0]
    assert len(finished) == 0


def test_image_load_worker_rejects_unknown_format(qapp, tmp_path) -> None:
    p = tmp_path / "icon.xyz"
    p.write_bytes(b"fake image")
    worker = ImageLoadWorker(str(p))
    errors: list[str] = []
    finished: list = []
    worker.error.connect(errors.append)
    worker.finished.connect(lambda img, path: finished.append((img, path)))

    with patch("bgremover.workers.Image.open") as mock_open:
        mock_img = mock_open.return_value
        mock_img.format = "ICO"
        worker.run()

    assert errors == ["Format nicht unterstützt: ICO"]
    assert len(finished) == 0


def test_image_load_worker_error_on_decode_failure(qapp, tmp_path) -> None:
    p = tmp_path / "bad.png"
    p.write_bytes(b"fake png")
    worker = ImageLoadWorker(str(p))
    errors: list[str] = []
    finished: list = []
    worker.error.connect(errors.append)
    worker.finished.connect(lambda img, path: finished.append((img, path)))

    with patch("bgremover.workers.Image.open") as mock_open:
        mock_img = mock_open.return_value
        mock_img.format = "PNG"
        mock_img.width = 10
        mock_img.height = 10
        mock_img.load.side_effect = OSError("decode failed")
        worker.run()

    assert len(errors) == 1
    assert "decode failed" in errors[0]
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


def test_image_load_worker_verify_rejects_truncated_png(qapp, tmp_path) -> None:
    """verify() muss strukturell kaputte PNGs (z. B. abgeschnittener IDAT)
    abweisen, bevor der eigentliche Decode laeuft."""
    src = io.BytesIO()
    Image.new("RGB", (32, 32), (200, 100, 50)).save(src, format="PNG")
    raw = src.getvalue()

    # IEND-Chunk (letzte 12 Bytes) abschneiden und mitten im IDAT kuerzen.
    truncated = raw[: max(64, len(raw) - 40)]
    bad = tmp_path / "truncated.png"
    bad.write_bytes(truncated)

    worker = ImageLoadWorker(str(bad))
    finished: list = []
    errors: list[str] = []
    worker.finished.connect(lambda img, path: finished.append((img, path)))
    worker.error.connect(errors.append)
    worker.run()

    assert len(errors) == 1
    assert len(finished) == 0


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
    assert canvas.image is None
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


def test_ai_worker_cancel_skips_finished_signal(qapp, _mock_rembg) -> None:
    img = Image.new("RGBA", (4, 4), (0, 0, 0, 255))
    worker = AIWorker(img)
    finished: list = []
    errors: list[str] = []
    worker.finished.connect(finished.append)
    worker.error.connect(errors.append)
    worker.cancel()

    result_img = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
    result_buf = io.BytesIO()
    result_img.save(result_buf, format="PNG")

    with patch("bgremover.workers.rembg_remove", return_value=result_buf.getvalue()):
        worker.run()

    assert len(finished) == 0
    assert len(errors) == 0


# ─────────────────────────────────────────────────────────────
# Canvas – Versions- und Content-Revisionszähler (Stale-Check für KI-Ergebnis)
# ─────────────────────────────────────────────────────────────

def test_canvas_version_increments_on_load(qapp, tmp_path) -> None:
    canvas = ImageCanvas()
    assert canvas.version == 0
    img = Image.new("RGBA", (10, 10), (1, 2, 3, 255))
    canvas.apply_loaded_image(img, str(tmp_path / "x.png"))
    assert canvas.version == 1
    canvas.apply_loaded_image(img, str(tmp_path / "y.png"))
    assert canvas.version == 2


def test_canvas_version_tracks_edits_and_undo(qapp, tmp_path) -> None:
    canvas = ImageCanvas()
    img = Image.new("RGBA", (10, 10), (1, 2, 3, 255))
    canvas.apply_loaded_image(img, str(tmp_path / "x.png"))
    v_after_load = canvas.version
    canvas.apply_edit(img.copy(), desc="test-edit")
    assert canvas.version == v_after_load + 1
    canvas.undo()
    assert canvas.version == v_after_load + 2


def test_canvas_content_revision_tracks_edits_and_undo(qapp, tmp_path) -> None:
    canvas = ImageCanvas()
    img = Image.new("RGBA", (10, 10), (1, 2, 3, 255))
    canvas.apply_loaded_image(img, str(tmp_path / "x.png"))
    rev_after_load = canvas.content_revision

    canvas.apply_edit(Image.new("RGBA", (10, 10), (4, 5, 6, 255)),
                      desc="test-edit")
    assert canvas.content_revision == rev_after_load + 1

    canvas.undo()
    assert canvas.content_revision == rev_after_load + 2


def test_ai_result_is_discarded_after_canvas_edit(qapp, tmp_path) -> None:
    win = MainWindow()
    try:
        original = Image.new("RGBA", (4, 4), (10, 20, 30, 255))
        edited = Image.new("RGBA", (4, 4), (40, 50, 60, 255))
        stale_ai_result = Image.new("RGBA", (4, 4), (70, 80, 90, 255))

        win._canvas.apply_loaded_image(original, str(tmp_path / "x.png"))
        win._ai_input_version = win._canvas.version
        win._canvas.apply_edit(edited, desc="edit-after-ai-start")

        win._on_ai_done(stale_ai_result)

        assert win._canvas.image is not None
        assert win._canvas.image.getpixel((0, 0)) == (40, 50, 60, 255)
        status_bar = win.statusBar()
        assert status_bar is not None
        assert "verworfen" in status_bar.currentMessage()
    finally:
        win.close()
