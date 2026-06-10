"""Tests für das asynchrone Bildladen (B2).

``ImageLoadWorker`` führt den teuren ``Image.open`` + ``exif_transpose``-
Schritt im Hintergrund aus; ``ImageCanvas.apply_loaded_image`` übernimmt
das Ergebnis ohne erneuten Disk-IO.
"""
from pathlib import Path

from PIL import Image

from bgremover import ImageCanvas, ImageLoadWorker, MainWindow
from bgremover.status_messages import StatusMessages as SM


def test_apply_loaded_image_sets_state(qapp):
    canvas = ImageCanvas()
    img = Image.new("RGBA", (32, 24), (50, 100, 150, 255))
    canvas.apply_loaded_image(img, "/tmp/x.png")
    assert canvas.image is img
    assert canvas.selection_mask.shape == (24, 32)
    canvas.undo()
    assert canvas.image is img
    canvas.redo()
    assert canvas.image is img
    canvas.apply_edit(Image.new("RGBA", (32, 24), (1, 2, 3, 255)), desc="edit")
    canvas.restore_original()
    assert canvas.image is not None
    assert canvas.image.getpixel((0, 0)) == (50, 100, 150, 255)


def test_apply_loaded_image_emits_image_loaded(qapp):
    canvas = ImageCanvas()
    received = []
    canvas.imageLoaded.connect(received.append)
    img = Image.new("RGBA", (10, 10), (1, 2, 3, 255))
    canvas.apply_loaded_image(img, "/tmp/x.png")
    # imageLoaded liefert laut Signal-Vertrag den aufgeloesten absoluten Pfad
    # (str(Path(path).resolve())) – plattformneutral exakt pruefen statt per
    # schwacher OR-Klausel, die jeden auf "x.png" endenden Pfad durchwinkt.
    assert received == [str(Path("/tmp/x.png").resolve())]


def test_image_load_worker_emits_finished(qapp, tmp_path):
    p = tmp_path / "x.png"
    Image.new("RGB", (10, 10), (1, 2, 3)).save(p)
    worker = ImageLoadWorker(str(p))
    received = []
    worker.finished.connect(lambda img, path: received.append((img, path)))
    worker.run()
    assert len(received) == 1
    img, path = received[0]
    assert img.mode == "RGBA"
    assert path == str(p)


def test_image_load_worker_emits_error_on_invalid(qapp, tmp_path):
    bad = tmp_path / "broken.png"
    bad.write_bytes(b"not a png")
    worker = ImageLoadWorker(str(bad))
    errors = []
    worker.error.connect(errors.append)
    worker.run()
    assert errors


def test_async_load_result_is_discarded_after_canvas_edit(
    qapp, monkeypatch,
):
    win = MainWindow()
    try:
        original = Image.new("RGBA", (8, 8), (10, 20, 30, 255))
        edited = Image.new("RGBA", (8, 8), (40, 50, 60, 255))
        stale_load = Image.new("RGBA", (8, 8), (70, 80, 90, 255))
        win._canvas.apply_loaded_image(original, "original.png")

        callbacks = {}

        def defer_load(_path, on_loaded, on_error):
            callbacks["loaded"] = on_loaded
            callbacks["error"] = on_error
            return True

        monkeypatch.setattr(
            win._worker_controller, "start_image_load", defer_load)
        loaded_paths: list[str] = []
        win._canvas.imageLoaded.connect(loaded_paths.append)

        win._load_image_async("slow.png")
        win._canvas.apply_edit(edited, desc="edit-during-load")
        edited_revision = win._canvas.content_revision

        callbacks["loaded"](stale_load, "slow.png")

        assert win._canvas.image is edited
        assert win._canvas.content_revision == edited_revision
        assert loaded_paths == []
        assert win.statusBar().currentMessage() == SM.LADEERGEBNIS_VERWORFEN

        win._canvas.undo()
        assert win._canvas.image is not None
        assert win._canvas.image.getpixel((0, 0)) == original.getpixel((0, 0))
    finally:
        win.close()


def test_older_load_generation_cannot_overwrite_newer_request(
    qapp, monkeypatch,
):
    win = MainWindow()
    try:
        original = Image.new("RGBA", (8, 8), (10, 20, 30, 255))
        old_result = Image.new("RGBA", (8, 8), (40, 50, 60, 255))
        new_result = Image.new("RGBA", (8, 8), (70, 80, 90, 255))
        win._canvas.apply_loaded_image(original, "original.png")

        callbacks: list = []

        def defer_load(_path, on_loaded, on_error):
            callbacks.append((on_loaded, on_error))
            return True

        monkeypatch.setattr(
            win._worker_controller, "start_image_load", defer_load)

        win._load_image_async("old.png")
        win._load_image_async("new.png")

        callbacks[0][0](old_result, "old.png")
        assert win._canvas.image is original
        assert win.statusBar().currentMessage() == SM.LADEERGEBNIS_VERWORFEN

        callbacks[1][0](new_result, "new.png")
        assert win._canvas.image is new_result
    finally:
        win.close()
