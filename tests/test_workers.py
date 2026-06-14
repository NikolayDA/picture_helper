"""Tests für Worker-Klassen: Fehlerpfade, Grössenvalidierung und Concurrent-Load-Schutz."""
import io
import os
import subprocess
import sys
import threading
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
from bgremover.status_messages import StatusMessages as SM

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


def test_open_validated_image_reads_path_only_once(tmp_path) -> None:
    """TOCTOU-Schutz: Der Pfad darf nur EINMAL vom Dateisystem geoeffnet
    werden – verify() und Decode laufen danach aus dem In-Memory-Puffer.
    Zweimaliges Oeffnen liesse ein Fenster, in dem unter dem Pfad eine andere
    Datei landen koennte."""
    import builtins

    p = tmp_path / "ok.png"
    Image.new("RGB", (8, 8), (10, 20, 30)).save(p)

    real_open = builtins.open
    path_opens: list[str] = []

    def counting_open(file, *args, **kwargs):
        if file == str(p):
            path_opens.append(str(file))
        return real_open(file, *args, **kwargs)

    with patch("builtins.open", side_effect=counting_open):
        img, err = open_validated_image(str(p))

    assert err is None and img is not None
    assert path_opens == [str(p)]  # ein Disk-Open statt getrenntem verify+decode


def test_open_validated_image_enforces_input_file_size_limit(tmp_path, monkeypatch) -> None:
    """Dateigrößen-Gate vor dem Einlesen: Grenzwert wird akzeptiert, knapp
    darunter akzeptiert, knapp darüber abgelehnt. Variiert wird das Limit
    relativ zur realen Dateigröße – äquivalent zu variabler Dateigröße bei
    festem Limit, aber ohne riesige Dateien schreiben zu müssen."""
    import bgremover.image_loading as il

    p = tmp_path / "ok.png"
    Image.new("RGB", (16, 16), (10, 20, 30)).save(p)
    size = p.stat().st_size
    assert size > 1  # Plausibilität

    # Grenzwert: Datei == Limit → akzeptiert (Bedingung lehnt nur „> Limit" ab).
    monkeypatch.setattr(il, "_MAX_INPUT_FILE_BYTES", size)
    img, err = open_validated_image(str(p))
    assert err is None and img is not None

    # Knapp darunter: Datei < Limit → akzeptiert.
    monkeypatch.setattr(il, "_MAX_INPUT_FILE_BYTES", size + 1)
    img, err = open_validated_image(str(p))
    assert err is None and img is not None

    # Knapp darüber: Datei > Limit → abgelehnt; Meldung nennt MB, nicht MP.
    monkeypatch.setattr(il, "_MAX_INPUT_FILE_BYTES", size - 1)
    img, err = open_validated_image(str(p))
    assert img is None
    assert err is not None
    assert "Datei zu groß" in err and "MB" in err
    assert "MP" not in err  # klar von der Megapixel-Meldung abgegrenzt


def test_open_validated_image_rejects_oversized_file_without_unbounded_read() -> None:
    """Akzeptanzkriterium: Bei übergroßen Dateien wird ``read()`` NICHT
    unbeschränkt aufgerufen. Die fstat()-Größe liegt über dem Limit, daher
    bricht die Funktion ab, bevor sie den (riesigen) Inhalt einliest."""
    import bgremover.image_loading as il

    class _FakeStat:
        st_size = il._MAX_INPUT_FILE_BYTES + 1

    with patch("bgremover.image_loading.os.fstat", return_value=_FakeStat()), \
         patch("bgremover.image_loading.open") as mock_open:
        mock_fh = mock_open.return_value.__enter__.return_value
        mock_fh.fileno.return_value = 0
        img, err = open_validated_image("/some/huge.png")

    assert img is None
    assert err is not None and "Datei zu groß" in err
    mock_fh.read.assert_not_called()  # kein Lesezugriff auf die Riesendatei


def test_open_validated_image_bounded_read_catches_size_growth(monkeypatch) -> None:
    """Sicherheitsnetz gegen TOCTOU / ungewöhnliche Fileobjekte: meldet fstat()
    eine kleine Größe, liefert read() aber mehr als das Limit, greift die
    Chunk-Leseschleife und meldet „zu groß". Jeder read() bleibt begrenzt
    (höchstens Limit + 1) statt unbeschränkt."""
    import bgremover.image_loading as il

    monkeypatch.setattr(il, "_MAX_INPUT_FILE_BYTES", 100)

    class _FakeStat:
        st_size = 0  # täuscht eine winzige Datei vor

    oversized = b"x" * (il._MAX_INPUT_FILE_BYTES + 1)  # 101 Bytes > Limit

    with patch("bgremover.image_loading.os.fstat", return_value=_FakeStat()), \
         patch("bgremover.image_loading.open") as mock_open:
        mock_fh = mock_open.return_value.__enter__.return_value
        mock_fh.fileno.return_value = 0
        mock_fh.read.return_value = oversized
        img, err = open_validated_image("/some/file.png")

    assert img is None
    assert err is not None and "Datei zu groß" in err
    # Kein unbeschränktes read(): jede angeforderte Lesegröße ist begrenzt.
    assert mock_fh.read.call_args_list  # es wurde überhaupt gelesen
    for call in mock_fh.read.call_args_list:
        (requested,) = call.args
        assert requested is not None and requested <= il._MAX_INPUT_FILE_BYTES + 1


def test_open_validated_image_reads_in_bounded_chunks(monkeypatch, tmp_path) -> None:
    """#258: Der Inhalt wird in kleinen Chunks gelesen – nie ein einzelner
    read() in Limitgröße. Sonst reserviert CPythons BufferedReader sofort einen
    Puffer in Limitgröße (~512 MiB) und selbst eine kleine valide Datei kann
    unter knappem Adressraum mit MemoryError scheitern."""
    import bgremover.image_loading as il

    p = tmp_path / "ok.png"
    Image.new("RGB", (16, 16), (10, 20, 30)).save(p)
    raw = p.read_bytes()
    assert len(raw) > 8  # mehrere Chunks bei winziger Chunkgröße

    monkeypatch.setattr(il, "_READ_CHUNK_BYTES", 8)

    read_sizes: list[int] = []

    class _SpyFile:
        def __init__(self, data: bytes) -> None:
            self._buf = io.BytesIO(data)

        def fileno(self) -> int:
            return -1  # os.fstat ist gepatcht; Wert irrelevant

        def read(self, n: int = -1) -> bytes:
            read_sizes.append(n)
            return self._buf.read(n)

        def __enter__(self):
            return self

        def __exit__(self, *exc) -> None:
            self._buf.close()

    class _FakeStat:
        st_size = len(raw)  # <= reales Limit (512 MiB) → kein fstat-Abbruch

    with patch("bgremover.image_loading.open", return_value=_SpyFile(raw)), \
         patch("bgremover.image_loading.os.fstat", return_value=_FakeStat()):
        img, err = open_validated_image(str(p))

    assert err is None and img is not None
    # Mehrere Chunk-Reads, jeder höchstens chunkgroß – nie ein read() in
    # Limitgröße (das wäre ~512 MiB).
    assert len(read_sizes) >= 2
    assert max(read_sizes) <= il._READ_CHUNK_BYTES


def test_file_too_large_message_is_localized(monkeypatch) -> None:
    """#258: Die Größenmeldung wird über einen Translation-Key vollständig
    lokalisiert – keine gemischte (deutsch-in-englisch) Meldung."""
    import bgremover.image_loading as il
    from bgremover.i18n import configure_locale

    monkeypatch.setattr(il, "_MAX_INPUT_FILE_BYTES", 100)

    class _FakeStat:
        st_size = il._MAX_INPUT_FILE_BYTES + 1  # über dem Limit

    try:
        configure_locale("en")
        with patch("bgremover.image_loading.os.fstat", return_value=_FakeStat()), \
             patch("bgremover.image_loading.open") as mock_open:
            mock_open.return_value.__enter__.return_value.fileno.return_value = 0
            img, err = open_validated_image("/some/huge.png")
    finally:
        configure_locale("de")

    assert img is None and err is not None
    assert "File too large" in err   # englischer Wortlaut
    assert "Datei" not in err        # kein deutscher Literaltext


def test_file_too_large_message_rounds_actual_up_above_limit(monkeypatch) -> None:
    """#258: Bei „Limit + 1 Byte" ist der angezeigte Ist-Wert sichtbar größer
    als der Grenzwert (Aufrunden statt .0f-Abrunden auf denselben Wert)."""
    import bgremover.image_loading as il

    one_mib = 1024 * 1024
    monkeypatch.setattr(il, "_MAX_INPUT_FILE_BYTES", 512 * one_mib)

    class _FakeStat:
        st_size = 512 * one_mib + 1  # exakt ein Byte über dem Limit

    with patch("bgremover.image_loading.os.fstat", return_value=_FakeStat()), \
         patch("bgremover.image_loading.open") as mock_open:
        mock_open.return_value.__enter__.return_value.fileno.return_value = 0
        img, err = open_validated_image("/some/big.png")

    assert img is None and err is not None
    assert "513 MB" in err   # Ist-Wert aufgerundet
    assert "512 MB" in err   # Grenzwert abgerundet → sichtbar kleiner


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

    def fake_remove(payload: bytes, session: object = None) -> bytes:
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
# #229 – rembg-Session: einmalig erzeugen und wiederverwenden
# ─────────────────────────────────────────────────────────────

def test_rembg_session_created_once_and_reused_across_workers(qapp, _mock_rembg) -> None:
    """Der Warmup erzeugt genau EINE Session, ``new_session()`` läuft über
    mehrere aufeinanderfolgende KI-Aufrufe höchstens einmal, und jeder
    ``remove()``-Aufruf (Warmup + AIWorker) bekommt dieselbe Session-Instanz
    übergeben – Kern von Issue #229 (teure Inferenz-Session wiederverwenden)."""
    from bgremover.workers import RembgWarmupWorker

    sentinel_session = object()
    new_session_calls: list = []

    def fake_new_session(*args, **kwargs):
        new_session_calls.append((args, kwargs))
        return sentinel_session

    result_buf = io.BytesIO()
    Image.new("RGBA", (4, 4), (0, 0, 0, 0)).save(result_buf, format="PNG")
    result_png = result_buf.getvalue()

    seen_sessions: list = []

    def fake_remove(_payload, session=None):
        seen_sessions.append(session)
        return result_png

    with patch("bgremover.workers.rembg_new_session", side_effect=fake_new_session), \
         patch("bgremover.workers.rembg_remove", side_effect=fake_remove):
        RembgWarmupWorker().run()
        AIWorker(Image.new("RGBA", (4, 4), (10, 20, 30, 255))).run()
        AIWorker(Image.new("RGBA", (4, 4), (40, 50, 60, 255))).run()

    # new_session() genau einmal: die Session wird wiederverwendet, nicht je
    # KI-Aufruf neu initialisiert.
    assert len(new_session_calls) == 1
    # Warmup + zwei KI-Läufe rufen remove() – jeder mit DERSELBEN Session.
    assert len(seen_sessions) == 3
    assert all(s is sentinel_session for s in seen_sessions)


def test_ensure_rembg_session_reports_init_error(qapp, _mock_rembg, monkeypatch) -> None:
    """Schlägt ``new_session()`` fehl, propagiert der Fehler über das
    Worker-``error``-Signal und ``_rembg_session`` bleibt ``None`` – es bleibt
    kein fälschlich „bereiter" Zustand zurück (Akzeptanzkriterium #229)."""
    import bgremover.workers as _m
    from bgremover.workers import RembgWarmupWorker

    def boom(*_a, **_k):
        raise RuntimeError("session init failed")

    worker = RembgWarmupWorker()
    errors: list[str] = []
    finished: list = []
    worker.error.connect(errors.append)
    worker.finished.connect(lambda: finished.append(True))

    with patch("bgremover.workers.rembg_remove", side_effect=lambda *a, **k: b""), \
         patch("bgremover.workers.rembg_new_session", side_effect=boom):
        worker.run()

    assert finished == [True]                 # Lifecycle-Abschluss feuert immer
    assert len(errors) == 1
    assert "session init failed" in errors[0]
    assert _m._rembg_session is None          # kein false-ready-Zustand


def test_ensure_rembg_session_creates_once_under_concurrency() -> None:
    """Double-Checked Locking für die Session: Sehen mehrere Threads gleichzeitig
    ``_rembg_session is None``, darf trotzdem nur EIN Thread ``new_session()``
    ausführen – sonst würde das teure ONNX-Modell mehrfach geladen
    (Akzeptanzkriterium #229: threadsichere Session-Initialisierung)."""
    import time
    import types

    import bgremover.workers as _m

    saved_new_session = _m.rembg_new_session
    saved_session = _m._rembg_session
    _m.rembg_new_session = None
    _m._rembg_session = None

    creating_threads: set[int] = set()
    sessions: list = []
    fake = types.ModuleType("rembg")

    def _module_getattr(name: str):
        # ``from rembg import new_session`` loest dies aus. Die zurueckgegebene
        # Funktion haelt das Race-Fenster offen (sleep) und vermerkt, welcher
        # Thread tatsaechlich eine Session erzeugt.
        if name == "new_session":
            def _new_session(*_a, **_k):
                creating_threads.add(threading.get_ident())
                time.sleep(0.05)
                session = object()
                sessions.append(session)
                return session
            return _new_session
        raise AttributeError(name)

    fake.__getattr__ = _module_getattr

    results: list = []
    start = threading.Barrier(8)

    def call() -> None:
        start.wait(timeout=5)
        results.append(_m._ensure_rembg_session())

    threads = [threading.Thread(target=call) for _ in range(8)]
    try:
        with patch.dict(sys.modules, {"rembg": fake}):
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=5)

        assert len(creating_threads) == 1, creating_threads
        assert len(sessions) == 1                       # new_session genau einmal
        assert len(results) == 8
        assert all(r is results[0] for r in results)    # alle teilen die Session
    finally:
        _m.rembg_new_session = saved_new_session
        _m._rembg_session = saved_session


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


def test_ensure_rembg_remove_imports_once_under_concurrency() -> None:
    """Double-Checked Locking: Sehen mehrere Threads gleichzeitig
    ``rembg_remove is None``, darf trotzdem nur EIN Thread den Lazy-Import
    betreten. Ohne Lock waere das ein latenter Race um den teuren Import."""
    import time
    import types

    import bgremover.workers as _m

    saved = _m.rembg_remove
    _m.rembg_remove = None

    importing_threads: set[int] = set()
    fake = types.ModuleType("rembg")

    def _module_getattr(name: str):
        # ``from rembg import remove`` loest dies aus (``remove`` ist kein
        # echtes Attribut). Haelt das Race-Fenster offen und vermerkt, welcher
        # Thread den Import-Block betritt – robust gegen die mehrfachen
        # getattr-Aufrufe eines einzelnen ``from``-Imports.
        if name == "remove":
            importing_threads.add(threading.get_ident())
            time.sleep(0.05)
            return lambda data: data
        raise AttributeError(name)

    fake.__getattr__ = _module_getattr

    results: list = []
    start = threading.Barrier(8)

    def call() -> None:
        start.wait(timeout=5)
        results.append(_m._ensure_rembg_remove())

    threads = [threading.Thread(target=call) for _ in range(8)]
    try:
        with patch.dict(sys.modules, {"rembg": fake}):
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=5)

        assert len(importing_threads) == 1, importing_threads
        assert len(results) == 8
        assert all(r is results[0] for r in results)
    finally:
        _m.rembg_remove = saved


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


def test_load_image_async_reports_pending_ai_cancellation(qapp, monkeypatch) -> None:
    """Bildwechsel während rembg läuft erklärt die unvermeidbare Wartezeit.

    ``AIWorker.cancel`` kann den blockierenden rembg-Aufruf nicht abbrechen;
    bis zu dessen Rückkehr bleibt der KI-Button deaktiviert. Die Statusleiste
    muss diesen Zustand anzeigen und nach Threadende sauber abschließen.
    """
    win = MainWindow()
    try:
        class RunningThread:
            @staticmethod
            def isRunning() -> bool:
                return True

        class CancellableWorker:
            def __init__(self) -> None:
                self.cancelled = False

            def cancel(self) -> None:
                self.cancelled = True

        worker = CancellableWorker()
        win._worker_controller.ai_thread = RunningThread()
        win._worker_controller.ai_worker = worker
        monkeypatch.setattr(
            win._worker_controller, "start_image_load",
            lambda *a, **k: True,
        )

        win._load_image_async("/beliebiger/pfad.png")

        assert worker.cancelled
        assert win.statusBar().currentMessage() == SM.KI_ABBRUCH_WARTET

        win._on_ai_thread_finished()

        assert win.statusBar().currentMessage() == SM.KI_ABGEBROCHEN
        assert win._toolbar.btn_ai.isEnabled()
    finally:
        win._worker_controller.ai_thread = None
        win._worker_controller.ai_worker = None
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
        assert win._canvas.wand_busy is False
        status_bar = win.statusBar()
        assert status_bar is not None
        # Nutzer sieht den Ladefehler, nicht den irreführenden Auswahl-Fehler.
        assert "Ladefehler" in status_bar.currentMessage()
        assert "Auswahl-Fehler" not in status_bar.currentMessage()
    finally:
        win.close()
