"""Gemeinsamer Bildlade-Helfer für Canvas und Worker.

``ImageCanvas.load_image`` (direkte Aufrufer und Tests) und
``ImageLoadWorker._work`` (Dateidialog, zuletzt geöffnete Dateien und
Drag & Drop) nutzen ``open_validated_image``. Dadurch greifen
Strukturprüfung, Format-Whitelist und Megapixel-Schutz in beiden Pfaden
identisch.
"""
from __future__ import annotations

import io
import math
import os

from PIL import Image, ImageOps, UnidentifiedImageError

from bgremover.constants import (
    _ALLOWED_IMAGE_FORMATS,
    _MAX_INPUT_FILE_BYTES,
    _MAX_MEGAPIXELS,
)
from bgremover.i18n import tr

# Chunkgröße für das begrenzte Einlesen. Bewusst klein gegenüber dem
# Dateigrößen-Limit (512 MiB): ``fh.read(limit + 1)`` würde bei CPythons
# gepuffertem Reader sofort einen Puffer in Limitgröße reservieren und damit
# selbst eine kleine valide Datei unter knappem Adressraum mit ``MemoryError``
# scheitern lassen (#258). 8 MiB hält die Vorallokation klein und die Anzahl
# der Lese-Iterationen für reale Bilddateien gering.
_READ_CHUNK_BYTES = 8 * 1024 * 1024
# Kleiner Probe-Read für die Wachstumserkennung NACH der per ``fstat`` bekannten
# Größe. Eine Datei exakt in fstat-Größe ist danach am EOF; ein voller
# ``_READ_CHUNK_BYTES``-Read nur zum EOF-Erkennen würde erneut ~8 MiB Headroom
# anfordern (CPythons gepufferter Reader allokiert anhand der angeforderten
# Menge, bevor er EOF erkennt – Befund #286). 64 KiB reichen, um Wachstum
# (TOCTOU bzw. Pipe/Socket ohne verlässliches ``st_size``) zu erkennen; danach
# wird wieder in ``_READ_CHUNK_BYTES``-Schritten gelesen.
_GROWTH_PROBE_BYTES = 64 * 1024


def _too_large_message(mp: float | None = None) -> str:
    """Einheitliche „Bild zu groß"-Meldung – mit Megapixel-Angabe, wenn bekannt.

    Läuft – analog zu ``_file_too_large_message`` (#258) – über Übersetzungs-Keys
    statt über einen deutschen Literaltext, sonst erschiene die Meldung im
    englischen UI gemischtsprachig (#275). Zwei Varianten: mit bekannter
    Megapixel-Zahl (``status.image_too_large_mp``) und ohne
    (``status.image_too_large``, z. B. beim DecompressionBomb-Schutz).
    """
    if mp is None:
        return tr("status.image_too_large", limit=_MAX_MEGAPIXELS)
    return tr("status.image_too_large_mp", mp=mp, limit=_MAX_MEGAPIXELS)


def _file_too_large_message(size_bytes: int) -> str:
    """Meldung für zu große *Eingabedateien*.

    Bewusst getrennt von ``_too_large_message``: Hier geht es um die
    Dateigröße in MB (vor dem Einlesen), nicht um die Megapixel-Zahl des
    dekodierten Bildes. Die unterschiedlichen Einheiten (MB vs. MP) und
    Worte (Datei vs. Bild) machen für Nutzer klar, welche Grenze griff.

    Die Meldung läuft über einen Übersetzungs-Key (``status.file_too_large``)
    statt über einen deutschen Literaltext, sonst erschiene sie in anderen
    Sprachen gemischt – ``status.load_error`` übersetzt nur den Rahmen (#258).

    Der Ist-Wert wird **auf**-, der Grenzwert **ab**gerundet. So ist die
    angezeigte Dateigröße bei einer Überschreitung garantiert sichtbar größer
    als das Limit – auch bei „Limit + 1 Byte", das mit ``.0f`` sonst als
    „512 MB bei Maximum 512 MB" erschiene (#258).
    """
    size_mb = math.ceil(size_bytes / (1024 * 1024))
    limit_mb = _MAX_INPUT_FILE_BYTES // (1024 * 1024)
    return tr("status.file_too_large", size=size_mb, limit=limit_mb)


def _read_capped(
    fh: io.BufferedReader, limit: int, size_hint: int,
) -> bytearray | None:
    """Liest höchstens ``limit + 1`` Bytes – ohne 2×-Spitze, ohne Vorallokation
    in Limitgröße.

    Gibt die gelesenen Bytes (höchstens ``limit`` lang) als ``bytearray`` zurück
    oder ``None``, sobald der Inhalt das Limit übersteigt.

    *size_hint* ist die per ``fstat`` bekannte Größe. Der Puffer wird EINMAL in
    dieser Größe angelegt und per Slice gefüllt – kein wachsender Puffer und kein
    ``b"".join(chunks)``, das Chunks und Ergebnis gleichzeitig (~2×, bis ~1 GiB
    nahe dem Limit) hielte (Befund #286/1). Das ``bytearray`` wird direkt
    weitergereicht (kein abschließendes ``bytes(...)``, das nochmals vollständig
    kopierte).

    Die Reads bleiben durch ``size_hint`` begrenzt, sodass eine kleine Datei nie
    einen vollen ``_READ_CHUNK_BYTES``-Puffer (8 MiB) anfordert (Befund #286/2).
    Nach Erreichen der bekannten Größe folgt ein kleiner Probe-Read, der Wachstum
    (TOCTOU bzw. Pipe/Socket ohne verlässliches ``st_size``) erkennt; wächst der
    Inhalt über das Limit, kommt ``None``.
    """
    # fstat-Größe defensiv klemmen: ``size`` ist oben bereits als ``<= limit``
    # geprüft; das ``min(..., limit + 1)`` hält ``_read_capped`` auch bei direktem
    # Aufruf mit unplausiblem Hinweis sicher, ``max(0, ...)`` fängt negative ab.
    target = max(0, min(size_hint, limit + 1))
    buf = bytearray(target)
    total = 0
    # Phase 1: die bekannte Größe gechunkt einlesen. Jeder Read ist durch die
    # (Rest-)Größe begrenzt; per Slice-Zuweisung wächst ``buf`` nicht (#286/2).
    while total < target:
        chunk = fh.read(min(_READ_CHUNK_BYTES, target - total))
        if not chunk:
            del buf[total:]            # Datei kürzer als fstat → auf Ist-Größe kürzen
            return buf
        n = len(chunk)
        buf[total:total + n] = chunk
        total += n
    # Phase 2: Wachstumserkennung jenseits der bekannten Größe. Ein normaler File
    # ist hier am EOF; der erste Folge-Read bleibt klein (Probe), damit eine
    # Datei exakt in fstat-Größe nicht erneut 8 MiB nur zum EOF-Erkennen
    # anfordert. Nach bestätigtem Wachstum wird in vollen Chunks weitergelesen.
    read_size = _GROWTH_PROBE_BYTES
    while total <= limit:
        chunk = fh.read(min(read_size, limit + 1 - total))
        if not chunk:
            break
        buf.extend(chunk)
        total += len(chunk)
        read_size = _READ_CHUNK_BYTES
    if total > limit:
        return None
    return buf


def open_validated_image(path: str) -> tuple[Image.Image | None, str | None]:
    """Öffnet und validiert *path*.

    Bei Erfolg kommt ``(rgba_image, None)`` zurück. Bei Fehlern kommt
    ``(None, message)`` mit einer nutzerverständlichen Statusmeldung.
    Erfolgreich geladene Bilder sind EXIF-orientiert und nach RGBA
    konvertiert.
    """
    img, _raw_modes, err = _open_validated_raw(path)
    if img is None:
        return None, err
    return ImageOps.exif_transpose(img).convert("RGBA"), None


def open_validated_height_image(path: str) -> tuple[Image.Image | None, str | None]:
    """Öffnet und validiert *path* für den 16-Bit-Höhenimport (#589).

    Identische Schutzschicht wie :func:`open_validated_image` (Dateigrößen-
    Limit, Struktur-``verify``, Format-Whitelist, Megapixel-/Bomb-Schutz),
    aber **ohne** die abschließende RGBA-Konvertierung: 16-Bit-Graustufen
    (PNG ``I;16``/``I``, TIFF ``I;16``/``I;16B``) behalten ihren nativen
    Pixelmodus und damit alle 65536 Stufen.

    **Abgewiesen** werden 16-Bit-Quellen, die Pillow nur 8-Bit-quantisiert
    ausliefern kann (16-Bit-Grau **mit Alphakanal** sowie 16-Bit-Farbbilder,
    Roh-Dekodiermodi wie ``LA;16B``/``RGB;16N``): Die Niederbits wären vor
    unserem Import bereits verworfen – eine klare Meldung ist ehrlicher als
    eine stille ``×257``-Requantisierung (Codex-Review-Befund zu #589).
    Die EXIF-Orientierung wird wie im RGBA-Pfad angewandt; die übrige
    Moduslogik (nativ vs. Luminanz vs. Abweisung) liegt in
    :func:`bgremover.height_map.image_to_height_field`.
    """
    img, raw_modes, err = _open_validated_raw(path)
    if img is None:
        return None, err
    if img.mode in ("L", "LA", "P", "RGB", "RGBA"):
        quantized = next((mode for mode in raw_modes if ";16" in mode), None)
        if quantized is not None:
            return None, tr("status.height_source_unsupported", mode=quantized)
    return ImageOps.exif_transpose(img), None


def _tile_raw_modes(image: Image.Image) -> tuple[str, ...]:
    """Roh-Dekodiermodi der Bildkacheln – **vor** ``load()`` ausgelesen.

    Nur über die Kachel-Metadaten ist erkennbar, ob eine Quelle 16-Bit-Kanäle
    trägt, die Pillow beim Dekodieren auf 8 Bit reduziert (z. B. PNG-Farbtyp
    „Grau+Alpha" mit Bittiefe 16 → Modus ``LA``, Rohmodus ``LA;16B``).
    Defensiv extrahiert: unerwartete Kachelformen liefern einfach keine Modi.
    """
    modes: list[str] = []
    for tile in getattr(image, "tile", ()):
        try:
            args = tile[3]
        except (IndexError, TypeError):
            continue
        raw = args[0] if isinstance(args, tuple) and args else args
        if isinstance(raw, str):
            modes.append(raw)
    return tuple(modes)


def _open_validated_raw(
    path: str,
) -> tuple[Image.Image | None, tuple[str, ...], str | None]:
    """Gemeinsamer, modus-erhaltender Kern der validierten Ladepfade."""
    # Datei genau EINMAL lesen und verify() wie Decode aus diesem Puffer
    # bedienen. Frueher wurde der Pfad zweimal geoeffnet (verify schliesst das
    # File, der Decode oeffnet neu) – dazwischen konnte unter demselben Pfad
    # eine andere Datei liegen (TOCTOU). Ein einzelner Read schliesst dieses
    # Fenster; der Megapixel-/Bomb-Schutz bleibt unten vor dem load() erhalten.
    try:
        with open(path, "rb") as fh:
            # Größe per fstat() VOR dem Einlesen prüfen: eine mehrere Gigabyte
            # große (auch falsch benannte/beschädigte) Datei darf keinen ebenso
            # großen bytes-Puffer erzeugen. Das Megapixel-Limit greift erst nach
            # dem Dekodieren und schützt davor gerade nicht (Befund #230).
            size = os.fstat(fh.fileno()).st_size
            if size > _MAX_INPUT_FILE_BYTES:
                return None, (), _file_too_large_message(size)
            # Begrenzt und in Chunks lesen (kein read() in Limitgröße, das sonst
            # einen 512-MiB-Puffer vorallokiert und kleine Dateien unter knappem
            # Speicher killt). Die fstat-Größe begrenzt den ersten Read, und der
            # Puffer wird ohne 2×-Spitze zusammengesetzt (Befund #286). Fängt
            # ungewöhnliche Fileobjekte (Pipes/Sockets ohne verlässliches
            # st_size) und eine Größenänderung zwischen fstat() und Lesen ab –
            # ``None`` signalisiert „über dem Limit".
            data = _read_capped(fh, _MAX_INPUT_FILE_BYTES, size)
    except OSError as e:
        return None, (), f"{type(e).__name__}: {e}"

    if data is None:
        # Inhalt wuchs zwischen fstat() und Lesen über das Limit (TOCTOU) oder
        # das Fileobjekt liefert keine verlässliche Größe. Den genauen Ist-Wert
        # kennen wir hier nicht; „Limit + 1 Byte" zeigt eindeutig die
        # Überschreitung an.
        return None, (), _file_too_large_message(_MAX_INPUT_FILE_BYTES + 1)

    # verify() prueft die Struktur (Header, Chunks) ohne die Pixel zu
    # dekodieren – manipulierte oder abgeschnittene Dateien werden so
    # frueh abgewiesen, bevor load() Speicher allokiert. PIL invalidiert
    # das Image-Objekt nach verify(); fuer den echten Decode-Pfad muss
    # erneut aus dem Puffer geoeffnet werden.
    try:
        with Image.open(io.BytesIO(data)) as probe:
            probe.verify()
    except Image.DecompressionBombError:
        # Pillow lehnt Bilder über 2× MAX_IMAGE_PIXELS bereits hier ab –
        # noch bevor die Megapixel-Prüfung unten greift. DecompressionBombError
        # ist KEINE OSError-Subklasse und entkäme sonst dem except-Tupel
        # (im synchronen load_image-Pfad als ungefangene Exception). Auf
        # dieselbe nutzerfreundliche „zu groß"-Meldung abbilden statt den
        # rohen DOS-Schutz-Text durchzureichen.
        return None, (), _too_large_message()
    except (UnidentifiedImageError, SyntaxError, OSError) as e:
        return None, (), f"{type(e).__name__}: {e}"

    try:
        img: Image.Image = Image.open(io.BytesIO(data))
        if img.format not in _ALLOWED_IMAGE_FORMATS:
            return None, (), f"Format nicht unterstützt: {img.format}"
        mp = img.width * img.height / 1_000_000
        if mp > _MAX_MEGAPIXELS:
            return None, (), _too_large_message(mp)
        # Roh-Dekodiermodi VOR load() sichern – danach sind die Kacheln
        # konsumiert und die 16-Bit-Erkennung (Höhenpfad) unmöglich.
        raw_modes = _tile_raw_modes(img)
        img.load()
    except Image.DecompressionBombError:
        return None, (), _too_large_message()
    except (UnidentifiedImageError, OSError) as e:
        return None, (), f"{type(e).__name__}: {e}"

    return img, raw_modes, None
