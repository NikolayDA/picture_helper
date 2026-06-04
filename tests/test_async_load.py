"""Tests für das asynchrone Bildladen (B2).

``ImageLoadWorker`` führt den teuren ``Image.open`` + ``exif_transpose``-
Schritt im Hintergrund aus; ``ImageCanvas.apply_loaded_image`` übernimmt
das Ergebnis ohne erneuten Disk-IO.
"""
from pathlib import Path

from PIL import Image

from bgremover import ImageCanvas, ImageLoadWorker


def test_apply_loaded_image_sets_state(qapp):
    canvas = ImageCanvas()
    img = Image.new("RGBA", (32, 24), (50, 100, 150, 255))
    canvas.apply_loaded_image(img, "/tmp/x.png")
    assert canvas.image is img
    assert canvas._mask.shape == (24, 32)
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
