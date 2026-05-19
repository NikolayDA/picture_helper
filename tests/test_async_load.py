"""Tests für das asynchrone Bildladen (B2).

``ImageLoadWorker`` führt den teuren ``Image.open`` + ``exif_transpose``-
Schritt im Hintergrund aus; ``ImageCanvas.apply_loaded_image`` übernimmt
das Ergebnis ohne erneuten Disk-IO.
"""
from PIL import Image

from bgremover import ImageCanvas, ImageLoadWorker


def test_apply_loaded_image_sets_state(qapp):
    canvas = ImageCanvas()
    img = Image.new("RGBA", (32, 24), (50, 100, 150, 255))
    canvas.apply_loaded_image(img, "/tmp/x.png")
    assert canvas._pil is img
    assert canvas._mask.shape == (24, 32)
    assert canvas._original is not None
    assert len(canvas._undo) == 0
    assert len(canvas._redo) == 0


def test_apply_loaded_image_emits_image_loaded(qapp):
    canvas = ImageCanvas()
    received = []
    canvas.imageLoaded.connect(received.append)
    img = Image.new("RGBA", (10, 10), (1, 2, 3, 255))
    canvas.apply_loaded_image(img, "/tmp/x.png")
    assert received == ["/tmp/x.png"] or received[0].endswith("x.png")


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
