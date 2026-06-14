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


def _too_large_message(mp: float | None = None) -> str:
    """Einheitliche „Bild zu groß"-Meldung – mit Megapixel-Angabe, wenn bekannt."""
    if mp is None:
        return f"Bild zu groß – Maximum: {_MAX_MEGAPIXELS} MP"
    return f"Bild zu groß ({mp:.0f} MP) – Maximum: {_MAX_MEGAPIXELS} MP"


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


def _read_capped(fh: io.BufferedReader, limit: int) -> bytes | None:
    """Liest höchstens ``limit + 1`` Bytes in Chunks – ohne Vorallokation.

    Gibt die gelesenen Bytes zurück (höchstens ``limit`` lang) oder ``None``,
    sobald der Inhalt das Limit übersteigt. Anders als ``fh.read(limit + 1)``
    reserviert das nie einen Puffer in Limitgröße; eine kleine Datei belegt nur
    ihre eigene Größe. Im Überschreitungsfall werden die Daten verworfen, statt
    sie zu materialisieren – das Wachstum zwischen ``fstat()`` und Lesen (TOCTOU
    bzw. Pipes/Sockets ohne verlässliches ``st_size``) wird dennoch erkannt.
    """
    chunks: list[bytes] = []
    total = 0
    while total <= limit:
        chunk = fh.read(min(_READ_CHUNK_BYTES, limit + 1 - total))
        if not chunk:
            break
        total += len(chunk)
        if total > limit:
            return None
        chunks.append(chunk)
    return b"".join(chunks)


def open_validated_image(path: str) -> tuple[Image.Image | None, str | None]:
    """Öffnet und validiert *path*.

    Bei Erfolg kommt ``(rgba_image, None)`` zurück. Bei Fehlern kommt
    ``(None, message)`` mit einer nutzerverständlichen Statusmeldung.
    Erfolgreich geladene Bilder sind EXIF-orientiert und nach RGBA
    konvertiert.
    """
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
                return None, _file_too_large_message(size)
            # Begrenzt und in Chunks lesen (kein read() in Limitgröße, das sonst
            # einen 512-MiB-Puffer vorallokiert und kleine Dateien unter knappem
            # Speicher killt). Fängt ungewöhnliche Fileobjekte (Pipes/Sockets
            # ohne verlässliches st_size) und eine Größenänderung zwischen
            # fstat() und Lesen ab – ``None`` signalisiert „über dem Limit".
            data = _read_capped(fh, _MAX_INPUT_FILE_BYTES)
    except OSError as e:
        return None, f"{type(e).__name__}: {e}"

    if data is None:
        # Inhalt wuchs zwischen fstat() und Lesen über das Limit (TOCTOU) oder
        # das Fileobjekt liefert keine verlässliche Größe. Den genauen Ist-Wert
        # kennen wir hier nicht; „Limit + 1 Byte" zeigt eindeutig die
        # Überschreitung an.
        return None, _file_too_large_message(_MAX_INPUT_FILE_BYTES + 1)

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
        return None, _too_large_message()
    except (UnidentifiedImageError, SyntaxError, OSError) as e:
        return None, f"{type(e).__name__}: {e}"

    try:
        img: Image.Image = Image.open(io.BytesIO(data))
        if img.format not in _ALLOWED_IMAGE_FORMATS:
            return None, f"Format nicht unterstützt: {img.format}"
        mp = img.width * img.height / 1_000_000
        if mp > _MAX_MEGAPIXELS:
            return None, _too_large_message(mp)
        img.load()
    except Image.DecompressionBombError:
        return None, _too_large_message()
    except (UnidentifiedImageError, OSError) as e:
        return None, f"{type(e).__name__}: {e}"

    img = ImageOps.exif_transpose(img).convert("RGBA")
    return img, None
