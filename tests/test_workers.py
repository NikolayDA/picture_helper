"""Tests für Worker-Klassen: Fehlerpfade, Grössenvalidierung und Concurrent-Load-Schutz."""
import io
import os
import subprocess
import sys
from unittest.mock import patch

import numpy as np
import pytest
from PIL import Image

from bgremover import (
    AIWorker,
    FloodFillWorker,
    ImageCanvas,
    ImageLoadWorker,
    MainWindow,
)
from bgremover.constants import _MAX_MEGAPIXELS
from bgremover.image_loading import open_validated_image

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

    with patch("bgremover.image_loading.Image.open") as mock_open:
        mock_img = mock_open.return_value
        mock_img.format = "PNG"
        mock_img.width, mock_img.height = fake_size
        worker.run()

    assert len(errors) == 1
    assert str(_MAX_MEGAPIXELS) in errors[0]
    assert len(finished) == 0


def test_open_validated_image_handles_decompression_bomb(tmp_path, monkeypatch) -> None:
    """Bilder über 2× MAX_IMAGE_PIXELS lösen Pillows ``DecompressionBombError``
    schon in ``verify()``/``open()`` aus – noch bevor die App-eigene
    Megapixel-Prüfung greift. Dieser Fehler ist KEINE ``OSError``-Subklasse;
    ohne expliziten Handler entkäme er dem ``except``-Tupel.

    Anders als ``test_image_load_worker_rejects_oversized_image`` wird hier
    ``Image.open`` NICHT gemockt, sondern Pillows echter Bomb-Schutz über ein
    abgesenktes ``MAX_IMAGE_PIXELS`` real ausgelöst – genau der Pfad, den der
    gemockte Test nicht abdeckt.
    """
    p = tmp_path / "bomb.png"
    Image.new("RGB", (100, 100), (1, 2, 3)).save(p)
    # 100×100 = 10 000 px > 2×5 → Bomb-Error bereits beim Öffnen.
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 5)

    img, err = open_validated_image(str(p))   # darf NICHT werfen

    assert img is None
    assert err is not None
    assert "zu groß" in err
    assert str(_MAX_MEGAPIXELS) in err


def test_image_load_worker_rejects_unknown_format(qapp, tmp_path) -> None:
    p = tmp_path / "icon.xyz"
    p.write_bytes(b"fake image")
    worker = ImageLoadWorker(str(p))
    errors: list[str] = []
    finished: list = []
    worker.error.connect(errors.append)
    worker.finished.connect(lambda img, path: finished.append((img, path)))

    with patch("bgremover.image_loading.Image.open") as mock_open:
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

    with patch("bgremover.image_loading.Image.open") as mock_open:
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

    with patch("bgremover.image_loading.Image.open") as mock_open:
        mock_img = mock_open.return_value
        mock_img.format = "PNG"
        mock_img.width, mock_img.height = fake_size
        canvas.load_image(str(small))

    # Kein Bild geladen, Fehlermeldung in Status
    assert canvas.image is None
    assert any(str(_MAX_MEGAPIXELS) in m for m in msgs)


def test_canvas_load_image_rejects_unknown_format(qapp, tmp_path) -> None:
    """Der synchrone Lade-Pfad muss dieselbe Format-Whitelist nutzen wie
    der Worker – sonst akzeptiert Drag & Drop Formate, die der File-
    Dialog ablehnt."""
    p = tmp_path / "icon.xyz"
    p.write_bytes(b"fake image")

    canvas = ImageCanvas()
    msgs: list[str] = []
    canvas.statusMsg.connect(msgs.append)

    with patch("bgremover.image_loading.Image.open") as mock_open:
        mock_img = mock_open.return_value
        mock_img.format = "ICO"
        canvas.load_image(str(p))

    assert canvas.image is None
    assert any("Format nicht unterstützt: ICO" in m for m in msgs)


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
# FloodFillWorker – Wand-Auswahl im Hintergrund
# ─────────────────────────────────────────────────────────────

def _solid_rgba(w: int, h: int, color=(50, 100, 150)) -> np.ndarray:
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    arr[:, :, 0] = color[0]
    arr[:, :, 1] = color[1]
    arr[:, :, 2] = color[2]
    arr[:, :, 3] = 255
    return arr


def test_flood_fill_worker_emits_finished_with_mask(qapp) -> None:
    """Einfarbiger Block ⇒ Worker liefert eine Maske, die alles selektiert."""
    arr = _solid_rgba(8, 6)
    worker = FloodFillWorker(arr, 0, 0, tolerance=0)
    results: list[np.ndarray] = []
    errors: list[str] = []
    worker.finished.connect(results.append)
    worker.error.connect(errors.append)

    worker.run()

    assert len(results) == 1
    assert errors == []
    mask = results[0]
    assert mask.shape == (6, 8)
    assert mask.dtype == bool
    assert mask.all()


def test_flood_fill_worker_emits_empty_mask_for_click_outside(qapp) -> None:
    arr = _solid_rgba(4, 4)
    worker = FloodFillWorker(arr, -1, 0, tolerance=10)
    results: list[np.ndarray] = []
    worker.finished.connect(results.append)

    worker.run()

    assert len(results) == 1
    assert not results[0].any()


def test_flood_fill_worker_error_signal_on_bad_array(qapp) -> None:
    """flood_fill greift auf ``arr.shape`` zu – ein nicht-Array fliegt
    direkt mit AttributeError und muss im ``error``-Signal landen."""
    worker = FloodFillWorker("not an array", 0, 0, 0)  # type: ignore[arg-type]
    finished: list = []
    errors: list[str] = []
    worker.finished.connect(finished.append)
    worker.error.connect(errors.append)

    worker.run()

    assert finished == []
    assert len(errors) == 1


# ─────────────────────────────────────────────────────────────
# RembgWarmupWorker – Always-emit-finished-Vertrag
# ─────────────────────────────────────────────────────────────

def test_warmup_worker_emits_finished_on_success(qapp, _mock_rembg) -> None:
    """Erfolgsfall: ``finished`` muss genau einmal feuern, ``rembg_remove``
    bekommt das Dummy-Bild zu sehen."""
    from bgremover.workers import RembgWarmupWorker

    worker = RembgWarmupWorker()
    finished: list = []
    worker.finished.connect(lambda: finished.append(True))

    calls: list[bytes] = []

    def fake_remove(payload: bytes) -> bytes:
        calls.append(payload)
        return b""

    with patch("bgremover.workers.rembg_remove", side_effect=fake_remove):
        worker.run()

    assert finished == [True]
    assert len(calls) == 1
    assert calls[0]  # Nicht-leeres Dummy-PNG


def test_warmup_worker_emits_finished_on_error(qapp, _mock_rembg) -> None:
    """Fehlerfall: ``finished`` muss trotzdem feuern – sonst hängt der
    WorkerController-Thread-Lifecycle (``warmup_done`` würde nie gesetzt)."""
    from bgremover.workers import RembgWarmupWorker

    worker = RembgWarmupWorker()
    finished: list = []
    worker.finished.connect(lambda: finished.append(True))

    with patch("bgremover.workers.rembg_remove",
               side_effect=RuntimeError("mock warmup failure")):
        worker.run()

    assert finished == [True]


# ─────────────────────────────────────────────────────────────
# N7 – rembg wird lazy importiert (App-Start-Latenz)
# ─────────────────────────────────────────────────────────────

def test_rembg_available_is_bool_and_lazy_loader_present() -> None:
    """``REMBG_AVAILABLE`` stammt aus ``find_spec`` (kein teurer Import beim
    Modul-Load); der lazy Loader ``_ensure_rembg_remove`` zieht rembg erst im
    Worker-Thread und ist bis dahin ungebunden."""
    from bgremover import workers

    assert isinstance(workers.REMBG_AVAILABLE, bool)
    assert callable(workers._ensure_rembg_remove)


def test_importing_workers_does_not_eager_import_rembg() -> None:
    """N7: Der Modul-Import von ``workers`` darf weder ``rembg`` noch
    ``onnxruntime`` laden – sonst zahlt jeder App-Start (``main_window``
    importiert ``workers`` für ``REMBG_AVAILABLE``) die Importkosten, auch ohne
    KI-Nutzung. Frischer Subprozess, damit ein in anderen Tests evtl. schon
    geladenes Modul das Ergebnis nicht verfälscht."""
    code = (
        "import sys, bgremover.workers; "
        "assert 'rembg' not in sys.modules, 'rembg eager-importiert'; "
        "assert 'onnxruntime' not in sys.modules, 'onnxruntime eager-importiert'; "
        "print('OK')"
    )
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(p for p in sys.path if p))
    r = subprocess.run([sys.executable, "-c", code], env=env,
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0 and "OK" in r.stdout, (
        f"--- stdout ---\n{r.stdout}\n--- stderr ---\n{r.stderr}"
    )


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


def test_load_image_async_cancels_running_flood_fill(qapp, monkeypatch) -> None:
    """Beim Laden eines neuen Bildes muss eine laufende Zauberstab-Berechnung
    abgebrochen werden – symmetrisch zu ``cancel_ai()``. Sonst verbrennt der
    alte Flood-Fill-Worker CPU auf einem bereits ersetzten Bild und blockiert
    (über ``is_flood_fill_running``) den nächsten Zauberstab-Klick.
    """
    win = MainWindow()
    try:
        calls: list[str] = []
        monkeypatch.setattr(
            win._worker_controller, "cancel_flood_fill",
            lambda: calls.append("flood"))
        # Echten Ladevorgang unterdrücken – nur die Cancel-Logik prüfen.
        monkeypatch.setattr(
            win._worker_controller, "start_image_load",
            lambda *a, **k: True)

        win._load_image_async("/beliebiger/pfad.png")

        assert calls == ["flood"]
    finally:
        win.close()


def test_load_image_async_frees_wand_gate_on_load_error(qapp, monkeypatch) -> None:
    """N1: Schlägt das asynchrone Laden fehl, wird ``apply_loaded_image`` →
    ``_reset_transient_state`` nie erreicht. Das ``_wand_busy``-Gate muss
    dennoch frei werden, sonst bliebe der Zauberstab auf dem weiterhin
    sichtbaren alten Bild blockiert. Der abgebrochene Flood-Fill-Worker
    emittiert dafür kein Signal – die Freigabe passiert im Ladepfad selbst.
    """
    win = MainWindow()
    try:
        win._canvas.apply_loaded_image(
            Image.new("RGBA", (8, 8), (1, 2, 3, 255)), "alt.png")
        # Laufende Zauberstab-Berechnung simulieren.
        win._canvas._wand_busy = True

        # Ladevorgang scheitert sofort: on_error läuft, on_loaded nie.
        def fail_load(_path, on_loaded, on_error):  # noqa: ARG001
            on_error("Format nicht unterstützt")
            return False

        monkeypatch.setattr(
            win._worker_controller, "start_image_load", fail_load)

        win._load_image_async("/kaputt/bild.xyz")

        # Gate frei → ein erneuter Zauberstab-Klick ist wieder möglich.
        assert win._canvas._wand_busy is False
        status_bar = win.statusBar()
        assert status_bar is not None
        # Nutzer sieht den Ladefehler, nicht den irreführenden Auswahl-Fehler.
        assert "Ladefehler" in status_bar.currentMessage()
        assert "Auswahl-Fehler" not in status_bar.currentMessage()
    finally:
        win.close()
