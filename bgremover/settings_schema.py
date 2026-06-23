"""QSettings-Schema-Versionierung.

Aktuell existiert nur Version 1 – das Modul legt lediglich den
Grundstein, damit kuenftige Format-Wechsel (z. B. ein anderes Layout der
``recent_files``-Liste) ihre Migration an einer einzigen Stelle
einhaengen koennen, ohne dass alte gespeicherte Werte den Start crashen
lassen.

Der Schluessel ``schema_version`` ist absichtlich nur als Integer
persistiert – QSettings serialisiert ihn auf macOS als plist-``int``,
auf Linux als INI-String. Beide Faelle deckt ``_read_version`` ab.
"""
from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import QSettings

from bgremover.constants import logger

SCHEMA_VERSION = 2
SCHEMA_VERSION_KEY = "schema_version"

# QSettings-Schluessel des EufyMake-Studio-Imports (#355). Bewusst nicht
# projektspezifisch: gemerkt werden nur das letzte Exportziel und die zuletzt
# freigegebenen, allgemeinen Optionen. Eingefuehrt mit Schema-Version 2; fehlen
# sie (aeltere Settings), greifen beim Lesen schlicht die Defaults.
EXPORT_DIR_KEY = "eufymake_export_dir"
EXPORT_INCLUDE_HEIGHT_KEY = "eufymake_include_height"
EXPORT_INCLUDE_GLOSS_KEY = "eufymake_include_gloss"
EXPORT_BIT_DEPTH_KEY = "eufymake_bit_depth"


def _read_version(settings: QSettings) -> int | None:
    """Liest die persistierte Schema-Version.

    ``None`` = noch nie gesetzt (frische Settings oder Pre-Schema-Stand).
    Nicht-numerische Werte werden als "kaputt" behandelt und ebenfalls
    als ``None`` zurueckgegeben, damit die Migration normal greift,
    statt mit ValueError abzubrechen.
    """
    raw = settings.value(SCHEMA_VERSION_KEY, None)
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        logger.warning(
            "QSettings: unleserlicher schema_version-Wert %r – behandle "
            "als nicht gesetzt.", raw,
        )
        return None


def _migrate_0_to_1(_settings: QSettings) -> None:
    """No-op fuer die erste explizit versionierte Settings-Generation."""


def _migrate_1_to_2(_settings: QSettings) -> None:
    """No-op: Version 2 fuegt nur additive EufyMake-Export-Schluessel hinzu.

    Die neuen Schluessel (``EXPORT_*``) defaulten beim Lesen, wenn sie fehlen –
    es muss nichts umgeschrieben werden. Der Schritt ist dennoch explizit
    registriert, damit jede Vorversion einen lueckenlosen Weg zur aktuellen
    Version hat (siehe ``test_every_supported_previous_version_has_a_registered_step``).
    """


# Migrationen von Version N nach N+1. Auch No-op-Schritte werden explizit
# registriert, damit jede unterstuetzte Vorversion einen eindeutigen Weg zur
# aktuellen Version besitzt.
_MIGRATIONS: dict[int, Callable[[QSettings], None]] = {
    0: _migrate_0_to_1,
    1: _migrate_1_to_2,
}


def migrate(settings: QSettings) -> None:
    """Bringt ``settings`` auf ``SCHEMA_VERSION``.

    - Frische Settings ohne ``schema_version`` werden auf
      ``SCHEMA_VERSION`` gehoben.
    - Bestehende Settings mit aelterer Version durchlaufen die
      entsprechenden ``_MIGRATIONS``-Schritte (aktuell keine).
    - Settings mit ZUKUENFTIGER Version (> ``SCHEMA_VERSION``) werden
      nicht angefasst; es wird lediglich gewarnt, damit ein Downgrade
      keine User-Daten verliert.
    """
    current = _read_version(settings)

    if current is None:
        settings.setValue(SCHEMA_VERSION_KEY, SCHEMA_VERSION)
        return

    if current == SCHEMA_VERSION:
        return

    if current > SCHEMA_VERSION:
        logger.warning(
            "QSettings: gespeicherte schema_version=%d ist neuer als die "
            "vom Code unterstuetzte Version %d. Lasse Settings unveraendert "
            "– bitte eine neuere App-Version verwenden.",
            current, SCHEMA_VERSION,
        )
        return

    for version in range(current, SCHEMA_VERSION):
        if version not in _MIGRATIONS:
            logger.error(
                "QSettings: keine Migration fuer Version %d -> %d "
                "registriert. Breche bei schema_version=%d ab.",
                version, version + 1, current,
            )
            return

    while current < SCHEMA_VERSION:
        step = _MIGRATIONS[current]
        step(settings)
        current += 1
        settings.setValue(SCHEMA_VERSION_KEY, current)


def is_future_schema(settings: QSettings) -> bool:
    """True, wenn die gespeicherte ``schema_version`` neuer ist als die vom Code
    unterstuetzte.

    In diesem Fall duerfen Settings NICHT umgeschrieben werden – analog zu
    ``migrate``, das Zukunfts-Versionen bewusst unangetastet laesst. Ein
    aelteres Binary wuerde sonst Daten eines neueren Schemas (z. B. ein
    veraendertes ``recent_files``-Layout) ueberschreiben und so beim Downgrade
    still Daten verlieren. Ein nicht gesetzter oder unleserlicher Wert gilt
    NICHT als Zukunft (``_read_version`` liefert dort ``None``)."""
    current = _read_version(settings)
    return current is not None and current > SCHEMA_VERSION
