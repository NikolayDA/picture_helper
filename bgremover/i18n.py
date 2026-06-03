"""Lightweight runtime string lookup with a stable German fallback.

PR 3 deliberately introduces only the foundation: a runtime locale value,
normalization/fallback rules, and a first central string table. Additional
runtime languages can be added by extending ``_TRANSLATIONS`` in a later PR
without changing the calling code.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Final

DEFAULT_LOCALE: Final = "de"
SETTINGS_LOCALE_KEY: Final = "locale"

_TRANSLATIONS: Final[Mapping[str, Mapping[str, str]]] = {
    "de": {
        # Status bar messages
        "status.no_image_loaded": "Kein Bild geladen",
        "status.no_image_to_save": "Kein Bild zum Speichern",
        "status.already_loading": "Lädt bereits ein Bild…",
        "status.ai_already_running": "KI läuft bereits…",
        "status.ai_processing": "🤖 KI verarbeitet Bild… (kann einige Sekunden dauern)",
        "status.ai_ready": "🤖 KI bereit",
        "status.ai_model_loading": "🤖 KI-Modell wird geladen…",
        "status.ai_warmup_failed": "⚠️ KI-Modell konnte nicht geladen werden",
        "status.ai_result_discarded": (
            "KI-Ergebnis verworfen – Bild wurde inzwischen geändert"
        ),
        "status.wand_busy": "Zauberstab arbeitet noch…",
        "status.selection_calculating": "⏳ Auswahl wird berechnet…",
        "status.wand_discarded": (
            "Wand-Auswahl verworfen – Bild wurde inzwischen geändert"
        ),
        "status.no_selection": (
            "Keine Auswahl – erst Bereich mit Zauberstab oder Pinsel auswählen"
        ),
        "status.start_hint": (
            "Bild öffnen: Datei → Öffnen  oder  per Drag & Drop auf die Arbeitsfläche"
        ),
        "status.quitting": "Beende…",
        # Main menu
        "menu.file": "Datei",
        "menu.recent_files": "Zuletzt geöffnet",
        "menu.edit": "Bearbeiten",
        "menu.view": "Ansicht",
        "menu.extras": "Extras",
        "action.open": "Öffnen…",
        "action.save": "Speichern",
        "action.save_as": "Speichern unter…",
        "action.undo": "Rückgängig",
        "action.redo": "Wiederherstellen",
        "action.rotate_left_90": "90° links drehen",
        "action.rotate_right_90": "90° rechts drehen",
        "action.rotate_180": "180° drehen",
        "action.flip_horizontal": "Horizontal spiegeln",
        "action.flip_vertical": "Vertikal spiegeln",
        "action.clear_selection": "Auswahl aufheben",
        "action.invert_selection": "Auswahl invertieren",
        "action.restore_original": "Original wiederherstellen",
        "action.fit_to_view": "Fit to View",
        "action.settings": "Einstellungen…",
        # Left toolbar
        "toolbar.wand.tooltip": (
            "Zauberstab  (W)\n"
            "Klick wählt Farbfläche (Flood Fill)\n"
            "Shift = addieren  ·  {modifier} = subtrahieren"
        ),
        "toolbar.brush.tooltip": "Pinsel  (B)\nBereiche manuell zur Auswahl hinzufügen",
        "toolbar.eraser.tooltip": "Radiergummi  (E)\nAuswahl-Bereiche wieder entfernen",
        "toolbar.lasso.tooltip": (
            "Polygon-Lasso  (L)\n"
            "Klicken setzt Punkte · Doppelklick schließt Polygon\n"
            "Shift = addieren  ·  {modifier} = subtrahieren  ·  Esc = abbrechen"
        ),
        "toolbar.ai.available.tooltip": (
            "KI-Hintergrundentfernung (rembg)\n"
            "Entfernt den Hintergrund vollautomatisch"
        ),
        "toolbar.ai.missing.tooltip": (
            'rembg nicht installiert\n→ python3 -m pip install -e ".[ai]"'
        ),
        "toolbar.undo.tooltip": (
            "Rückgängig  ({shortcut})\n"
            "Letzten Bearbeitungsschritt rückgängig machen"
        ),
        "toolbar.redo.tooltip": (
            "Wiederherstellen  ({shortcut})\n"
            "Letzten rückgängig gemachten Schritt wiederherstellen"
        ),
        "toolbar.restore.tooltip": "Original wiederherstellen\nAlle Bearbeitungen verwerfen",
        "toolbar.history.tooltip": (
            "Änderungshistorie\n"
            "Zeigt alle bisherigen Bearbeitungsschritte.\n"
            "Doppelklick auf Eintrag → zu diesem Schritt zurück"
        ),
        "toolbar.open.tooltip": "Bild öffnen  ({shortcut})",
        "toolbar.save.tooltip": "Bild speichern  ({shortcut})",
        # Right panel tabs
        "right_panel.tab.selection": "Auswahl",
        "right_panel.tab.selection.tooltip": (
            "Auswahl – Zauberstab, Pinsel, Radiergummi"
        ),
        "right_panel.tab.background": "Hintergrund",
        "right_panel.tab.background.tooltip": (
            "Hintergrund – Entfernen, Farbe ersetzen"
        ),
        "right_panel.tab.transform": "Drehen/Spiegeln",
        "right_panel.tab.transform.tooltip": "Transform – Drehen, Spiegeln",
        "right_panel.tab.shape": "Form",
        "right_panel.tab.shape.tooltip": (
            "Form & Zuschnitt – Ecken abrunden, Format-Auswahl"
        ),
        # History popup
        "history.window_title": "Änderungshistorie",
        "history.hint": "Doppelklick auf Eintrag → zu diesem Schritt zurück",
        "history.list.tooltip": (
            "Verlauf aller Bearbeitungsschritte.\n"
            "Doppelklick auf einen Eintrag springt zu diesem Schritt zurück."
        ),
        # Crop bar
        "crop_bar.label": "✂  Ausschnitt positionieren, dann bestätigen:",
        "crop_bar.confirm": "✓  Zuschnitt anwenden",
        "crop_bar.cancel": "✗  Abbrechen",
    },
}

_current_locale = DEFAULT_LOCALE


def available_locales() -> tuple[str, ...]:
    """Return runtime locales currently backed by a string table."""

    return tuple(_TRANSLATIONS)


def normalize_locale(locale: object | None) -> str:
    """Normalize a locale-ish value and fall back to German if unsupported."""

    if locale is None:
        return DEFAULT_LOCALE
    text = str(locale).strip()
    if not text:
        return DEFAULT_LOCALE

    normalized = text.split(".", 1)[0].replace("_", "-").lower()
    language = normalized.split("-", 1)[0]
    for candidate in (normalized, language):
        if candidate in _TRANSLATIONS:
            return candidate
    return DEFAULT_LOCALE


def configure_locale(locale: object | None) -> str:
    """Set the process-local UI locale and return the effective locale."""

    global _current_locale
    _current_locale = normalize_locale(locale)
    return _current_locale


def init_locale_from_settings(settings_value: object | None) -> str:
    """Initialize runtime locale from persisted settings.

    An unset value intentionally resolves to German. That keeps the current UI
    stable until a later rollout PR adds a visible language setting.
    """

    return configure_locale(settings_value)


def current_locale() -> str:
    """Return the effective process-local UI locale."""

    return _current_locale


def tr(key: str, **values: object) -> str:
    """Translate ``key`` for the current locale, falling back to German."""

    active = _TRANSLATIONS.get(_current_locale, {})
    fallback = _TRANSLATIONS[DEFAULT_LOCALE]
    if key in active:
        template = active[key]
    elif key in fallback:
        template = fallback[key]
    else:
        raise KeyError(f"Unbekannter UI-String: {key}")

    if values:
        return template.format(**values)
    return template
