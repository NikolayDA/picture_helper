"""Lightweight runtime string lookup with a stable German fallback.

The central ``_TRANSLATIONS`` table maps string keys to per-locale values.
German is the default and the guaranteed fallback for any key a locale is
missing; English is available as a runtime language and the settings dialog
exposes a language selector. Further locales can be added by extending
``_TRANSLATIONS`` (kept key-for-key in sync with German) without touching the
call sites.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Final

DEFAULT_LOCALE: Final = "de"
SETTINGS_LOCALE_KEY: Final = "locale"

# Endonyms for the language selector; only locales actually present in
# ``_TRANSLATIONS`` are offered at runtime (see ``available_locales``).
LOCALE_NAMES: Final[Mapping[str, str]] = {
    "de": "Deutsch",
    "en": "English",
    "es": "Español",
    "fr": "Français",
    "uk": "Українська",
    "zh": "简体中文",
}

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
        # Status bar messages with interpolated values
        "status.loading": "⏳ Lädt: {name}…",
        "status.load_error": "Ladefehler: {msg}",
        "status.file_missing": "Datei nicht mehr vorhanden: {name}",
        "status.ai_error": "KI-Fehler: {msg}",
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
        # Right panel — Selection tab contents
        "right_panel.selection.section.tool": "Werkzeug",
        "right_panel.selection.hint.wand": "Zauberstab (W) — Farbfläche auswählen",
        "right_panel.selection.hint.brush": "Pinsel (B) — Auswahl aufmalen",
        "right_panel.selection.hint.eraser": "Radiergummi (E) — Auswahl entfernen",
        "right_panel.selection.hint.lasso": (
            "Polygon-Lasso (L) — Punkte klicken, Doppelklick abschließen"
        ),
        "right_panel.selection.hint.add": "Shift+Klick  →  Auswahl addieren",
        "right_panel.selection.hint.subtract": "{modifier}+Klick   →  Auswahl subtrahieren",
        "right_panel.selection.section.settings": "Einstellungen",
        "right_panel.selection.tolerance": "Toleranz (Zauberstab):  {value}",
        "right_panel.selection.tolerance.tooltip": (
            "Steuert wie ähnlich Farben sein müssen um ausgewählt zu werden.\n"
            "Niedrig = nur sehr ähnliche Farben · Hoch = viele Farbtöne"
        ),
        "right_panel.selection.brush_size": "Pinselgröße:  {value} px",
        "right_panel.selection.brush_size.tooltip": (
            "Größe des Pinsel-/Radiergummi-Werkzeugs in Pixeln"
        ),
        "right_panel.selection.clear": "Auswahl aufheben",
        "right_panel.selection.clear.tooltip": (
            "Hebt die aktuelle Auswahl auf (auch: Esc-Taste)"
        ),
        "right_panel.selection.invert": "Auswahl invertieren",
        "right_panel.selection.invert.tooltip": (
            "Tauscht aus- und nicht-ausgewählte Bereiche  ({modifier}+Shift+I)"
        ),
        "right_panel.selection.morph.tooltip": (
            "Radius in Pixeln für Erweitern/Schrumpfen der Auswahl"
        ),
        "right_panel.selection.expand": "➕ Erweitern",
        "right_panel.selection.expand.tooltip": (
            "Erweitert die Auswahl um den eingestellten Radius"
        ),
        "right_panel.selection.shrink": "➖ Schrumpfen",
        "right_panel.selection.shrink.tooltip": (
            "Schrumpft die Auswahl um den eingestellten Radius"
        ),
        # Right panel — Background tab contents
        "right_panel.background.section": "Hintergrund bearbeiten",
        "right_panel.background.remove": "Entfernen (transparent)",
        "right_panel.background.remove.tooltip": (
            "Macht den ausgewählten Bereich vollständig transparent.\n"
            "Tipp: Zuerst mit Zauberstab Hintergrund auswählen."
        ),
        "right_panel.background.color_label": "Farbe wählen und Auswahl einfärben:",
        "right_panel.background.color.tooltip": "Klicken um Ersatz-Hintergrundfarbe zu wählen",
        "right_panel.background.replace": "Farbe ersetzen",
        "right_panel.background.replace.tooltip": (
            "Füllt den ausgewählten Bereich mit der gewählten Farbe"
        ),
        # Right panel — Transform tab contents
        "right_panel.transform.section.rotate": "Drehen",
        "right_panel.transform.quick_label": "Schnell-Drehung:",
        "right_panel.transform.rotate_left_90": "↺ 90° links",
        "right_panel.transform.rotate_left_90.tooltip": "90° gegen den Uhrzeigersinn drehen",
        "right_panel.transform.rotate_right_90": "↻ 90° rechts",
        "right_panel.transform.rotate_right_90.tooltip": "90° im Uhrzeigersinn drehen",
        "right_panel.transform.rotate_180": "↺ 180°",
        "right_panel.transform.rotate_180.tooltip": "Bild um 180° drehen",
        "right_panel.transform.rotate_270": "↺ 270°",
        "right_panel.transform.rotate_270.tooltip": "270° gegen den Uhrzeigersinn (= 90° rechts)",
        "right_panel.transform.free_label": "Freier Winkel:",
        "right_panel.transform.angle_slider.tooltip": "Drehwinkel einstellen: −180° bis +180°",
        "right_panel.transform.angle_spin.tooltip": "Drehwinkel direkt eingeben",
        "right_panel.transform.apply_angle": "Winkel anwenden",
        "right_panel.transform.apply_angle.tooltip": (
            "Dreht das Bild um den eingestellten Winkel.\n"
            "Transparente Ecken entstehen bei schrägen Winkeln."
        ),
        "right_panel.transform.section.flip": "Spiegeln",
        "right_panel.transform.flip_h": "Horizontal",
        "right_panel.transform.flip_h.tooltip": "Bild horizontal spiegeln (links ↔ rechts)",
        "right_panel.transform.flip_v": "Vertikal",
        "right_panel.transform.flip_v.tooltip": "Bild vertikal spiegeln (oben ↕ unten)",
        # Right panel — Shape tab contents
        "right_panel.shape.section.corner": "Ecken abrunden",
        "right_panel.shape.radius": "Radius:  {value} px",
        "right_panel.shape.radius.tooltip": (
            "Radius der Eckenrundung in Pixeln.\n"
            "0 = keine Rundung · 500 = maximal rund"
        ),
        "right_panel.shape.round": "Ecken abrunden",
        "right_panel.shape.round.tooltip": (
            "Wendet die Eckenrundung an.\n"
            "Das Ergebnis wird als PNG mit transparenten Ecken gespeichert."
        ),
        "right_panel.shape.section.format": "Ausgabe-Format & Zuschnitt",
        "right_panel.shape.format_info": (
            "⇲ Format wählen → Rahmen erscheint auf dem Bild\n"
            "• Rahmen verschieben: Mitte ziehen\n"
            "• Größe ändern: Ecken ziehen (Proportionen bleiben)"
        ),
        "right_panel.shape.special_label": "Sonderformate:",
        "right_panel.shape.circle": "⬤  Kreis",
        "right_panel.shape.circle.tooltip": "Runden Ausschnitt positionieren und zuschneiden",
        "right_panel.shape.square": "■  1 : 1",
        "right_panel.shape.square.tooltip": "Quadratischen Ausschnitt positionieren",
        "right_panel.shape.landscape_label": "Querformat:",
        "right_panel.shape.landscape.tooltip": (
            "Querformat {label} — Ecken ziehen für Größe, Mitte zum Verschieben"
        ),
        "right_panel.shape.portrait_label": "Hochformat:",
        "right_panel.shape.portrait.tooltip": (
            "Hochformat {label} — Ecken ziehen für Größe, Mitte zum Verschieben"
        ),
        # Settings dialog
        "settings.title": "Einstellungen",
        "settings.open_dir.label": "Standard-Verzeichnis zum Öffnen",
        "settings.save_dir.label": "Standard-Verzeichnis für Export / Speichern",
        "settings.dir.placeholder": "Leer = zuletzt verwendetes Verzeichnis",
        "settings.format.label": "Bevorzugtes Bilddateiformat",
        "settings.log.label": "Protokolldatei",
        "settings.log.tooltip": "Pfad der Log-Datei (markieren zum Kopieren)",
        "settings.log.open_button": "Ordner öffnen",
        "settings.log.open_failed": "Ordner konnte nicht geöffnet werden:\n{target}",
        "settings.cancel": "Abbrechen",
        "settings.ok": "OK",
        "settings.pick_open.title": "Verzeichnis zum Öffnen wählen",
        "settings.pick_save.title": "Verzeichnis für Export/Speichern wählen",
        "settings.invalid_dir.title": "Ungültiges Verzeichnis",
        "settings.invalid_dir.body": "{label} ist kein existierendes Verzeichnis:\n{value}",
        "settings.language.label": "Sprache",
        "settings.language.restart_title": "Neustart erforderlich",
        "settings.language.restart_hint": (
            "Die Sprachänderung wird beim nächsten Start wirksam."
        ),
        # Dialogs (QMessageBox)
        "dialog.ai_error.title": "KI-Fehler",
        "dialog.ai_error.body": (
            "Fehler bei der automatischen Hintergrundentfernung:\n\n{msg}"
        ),
    },
    "en": {
        # Status bar messages
        "status.no_image_loaded": "No image loaded",
        "status.no_image_to_save": "No image to save",
        "status.already_loading": "Already loading an image…",
        "status.ai_already_running": "AI is already running…",
        "status.ai_processing": "🤖 AI is processing the image… (may take a few seconds)",
        "status.ai_ready": "🤖 AI ready",
        "status.ai_model_loading": "🤖 Loading AI model…",
        "status.ai_warmup_failed": "⚠️ Could not load the AI model",
        "status.ai_result_discarded": (
            "AI result discarded – the image changed in the meantime"
        ),
        "status.wand_busy": "Magic wand is still working…",
        "status.selection_calculating": "⏳ Calculating selection…",
        "status.wand_discarded": (
            "Wand selection discarded – the image changed in the meantime"
        ),
        "status.no_selection": (
            "No selection – first select an area with the magic wand or brush"
        ),
        "status.start_hint": (
            "Open an image: File → Open  or  drag & drop onto the canvas"
        ),
        "status.quitting": "Quitting…",
        # Status bar messages with interpolated values
        "status.loading": "⏳ Loading: {name}…",
        "status.load_error": "Load error: {msg}",
        "status.file_missing": "File no longer exists: {name}",
        "status.ai_error": "AI error: {msg}",
        # Main menu
        "menu.file": "File",
        "menu.recent_files": "Recently opened",
        "menu.edit": "Edit",
        "menu.view": "View",
        "menu.extras": "Extras",
        "action.open": "Open…",
        "action.save": "Save",
        "action.save_as": "Save as…",
        "action.undo": "Undo",
        "action.redo": "Redo",
        "action.rotate_left_90": "Rotate 90° left",
        "action.rotate_right_90": "Rotate 90° right",
        "action.rotate_180": "Rotate 180°",
        "action.flip_horizontal": "Flip horizontally",
        "action.flip_vertical": "Flip vertically",
        "action.clear_selection": "Clear selection",
        "action.invert_selection": "Invert selection",
        "action.restore_original": "Restore original",
        "action.fit_to_view": "Fit to View",
        "action.settings": "Settings…",
        # Left toolbar
        "toolbar.wand.tooltip": (
            "Magic wand  (W)\n"
            "Click selects a color area (flood fill)\n"
            "Shift = add  ·  {modifier} = subtract"
        ),
        "toolbar.brush.tooltip": "Brush  (B)\nAdd areas to the selection manually",
        "toolbar.eraser.tooltip": "Eraser  (E)\nRemove areas from the selection",
        "toolbar.lasso.tooltip": (
            "Polygon lasso  (L)\n"
            "Click to place points · double-click closes the polygon\n"
            "Shift = add  ·  {modifier} = subtract  ·  Esc = cancel"
        ),
        "toolbar.ai.available.tooltip": (
            "AI background removal (rembg)\n"
            "Removes the background fully automatically"
        ),
        "toolbar.ai.missing.tooltip": (
            'rembg not installed\n→ python3 -m pip install -e ".[ai]"'
        ),
        "toolbar.undo.tooltip": (
            "Undo  ({shortcut})\n"
            "Undo the last editing step"
        ),
        "toolbar.redo.tooltip": (
            "Redo  ({shortcut})\n"
            "Redo the last undone step"
        ),
        "toolbar.restore.tooltip": "Restore original\nDiscard all edits",
        "toolbar.history.tooltip": (
            "Change history\n"
            "Shows all previous editing steps.\n"
            "Double-click an entry → jump back to that step"
        ),
        "toolbar.open.tooltip": "Open image  ({shortcut})",
        "toolbar.save.tooltip": "Save image  ({shortcut})",
        # Right panel tabs
        "right_panel.tab.selection": "Selection",
        "right_panel.tab.selection.tooltip": (
            "Selection – magic wand, brush, eraser"
        ),
        "right_panel.tab.background": "Background",
        "right_panel.tab.background.tooltip": (
            "Background – remove, replace color"
        ),
        "right_panel.tab.transform": "Rotate/Flip",
        "right_panel.tab.transform.tooltip": "Transform – rotate, flip",
        "right_panel.tab.shape": "Shape",
        "right_panel.tab.shape.tooltip": (
            "Shape & crop – round corners, format selection"
        ),
        # History popup
        "history.window_title": "Change history",
        "history.hint": "Double-click an entry → jump back to that step",
        "history.list.tooltip": (
            "History of all editing steps.\n"
            "Double-click an entry to jump back to that step."
        ),
        # Crop bar
        "crop_bar.label": "✂  Position the crop, then confirm:",
        "crop_bar.confirm": "✓  Apply crop",
        "crop_bar.cancel": "✗  Cancel",
        # Right panel — Selection tab contents
        "right_panel.selection.section.tool": "Tool",
        "right_panel.selection.hint.wand": "Magic wand (W) — select a color area",
        "right_panel.selection.hint.brush": "Brush (B) — paint a selection",
        "right_panel.selection.hint.eraser": "Eraser (E) — remove selection",
        "right_panel.selection.hint.lasso": (
            "Polygon lasso (L) — click points, double-click to finish"
        ),
        "right_panel.selection.hint.add": "Shift+click  →  add to selection",
        "right_panel.selection.hint.subtract": "{modifier}+click   →  subtract from selection",
        "right_panel.selection.section.settings": "Settings",
        "right_panel.selection.tolerance": "Tolerance (magic wand):  {value}",
        "right_panel.selection.tolerance.tooltip": (
            "Controls how similar colors must be to get selected.\n"
            "Low = only very similar colors · High = many shades"
        ),
        "right_panel.selection.brush_size": "Brush size:  {value} px",
        "right_panel.selection.brush_size.tooltip": (
            "Size of the brush/eraser tool in pixels"
        ),
        "right_panel.selection.clear": "Clear selection",
        "right_panel.selection.clear.tooltip": (
            "Clears the current selection (also: Esc key)"
        ),
        "right_panel.selection.invert": "Invert selection",
        "right_panel.selection.invert.tooltip": (
            "Swaps selected and unselected areas  ({modifier}+Shift+I)"
        ),
        "right_panel.selection.morph.tooltip": (
            "Radius in pixels for growing/shrinking the selection"
        ),
        "right_panel.selection.expand": "➕ Grow",
        "right_panel.selection.expand.tooltip": (
            "Grows the selection by the set radius"
        ),
        "right_panel.selection.shrink": "➖ Shrink",
        "right_panel.selection.shrink.tooltip": (
            "Shrinks the selection by the set radius"
        ),
        # Right panel — Background tab contents
        "right_panel.background.section": "Edit background",
        "right_panel.background.remove": "Remove (transparent)",
        "right_panel.background.remove.tooltip": (
            "Makes the selected area fully transparent.\n"
            "Tip: first select the background with the magic wand."
        ),
        "right_panel.background.color_label": "Pick a color and fill the selection:",
        "right_panel.background.color.tooltip": "Click to choose a replacement background color",
        "right_panel.background.replace": "Replace color",
        "right_panel.background.replace.tooltip": (
            "Fills the selected area with the chosen color"
        ),
        # Right panel — Transform tab contents
        "right_panel.transform.section.rotate": "Rotate",
        "right_panel.transform.quick_label": "Quick rotate:",
        "right_panel.transform.rotate_left_90": "↺ 90° left",
        "right_panel.transform.rotate_left_90.tooltip": "Rotate 90° counterclockwise",
        "right_panel.transform.rotate_right_90": "↻ 90° right",
        "right_panel.transform.rotate_right_90.tooltip": "Rotate 90° clockwise",
        "right_panel.transform.rotate_180": "↺ 180°",
        "right_panel.transform.rotate_180.tooltip": "Rotate the image by 180°",
        "right_panel.transform.rotate_270": "↺ 270°",
        "right_panel.transform.rotate_270.tooltip": "270° counterclockwise (= 90° right)",
        "right_panel.transform.free_label": "Free angle:",
        "right_panel.transform.angle_slider.tooltip": "Set rotation angle: −180° to +180°",
        "right_panel.transform.angle_spin.tooltip": "Enter rotation angle directly",
        "right_panel.transform.apply_angle": "Apply angle",
        "right_panel.transform.apply_angle.tooltip": (
            "Rotates the image by the set angle.\n"
            "Oblique angles produce transparent corners."
        ),
        "right_panel.transform.section.flip": "Flip",
        "right_panel.transform.flip_h": "Horizontal",
        "right_panel.transform.flip_h.tooltip": "Flip the image horizontally (left ↔ right)",
        "right_panel.transform.flip_v": "Vertical",
        "right_panel.transform.flip_v.tooltip": "Flip the image vertically (top ↕ bottom)",
        # Right panel — Shape tab contents
        "right_panel.shape.section.corner": "Round corners",
        "right_panel.shape.radius": "Radius:  {value} px",
        "right_panel.shape.radius.tooltip": (
            "Corner rounding radius in pixels.\n"
            "0 = no rounding · 500 = maximally round"
        ),
        "right_panel.shape.round": "Round corners",
        "right_panel.shape.round.tooltip": (
            "Applies the corner rounding.\n"
            "The result is saved as PNG with transparent corners."
        ),
        "right_panel.shape.section.format": "Output format & crop",
        "right_panel.shape.format_info": (
            "⇲ Choose a format → a frame appears on the image\n"
            "• Move the frame: drag the center\n"
            "• Resize: drag the corners (aspect ratio kept)"
        ),
        "right_panel.shape.special_label": "Special formats:",
        "right_panel.shape.circle": "⬤  Circle",
        "right_panel.shape.circle.tooltip": "Position a circular crop and apply it",
        "right_panel.shape.square": "■  1 : 1",
        "right_panel.shape.square.tooltip": "Position a square crop",
        "right_panel.shape.landscape_label": "Landscape:",
        "right_panel.shape.landscape.tooltip": (
            "Landscape {label} — drag corners to resize, center to move"
        ),
        "right_panel.shape.portrait_label": "Portrait:",
        "right_panel.shape.portrait.tooltip": (
            "Portrait {label} — drag corners to resize, center to move"
        ),
        # Settings dialog
        "settings.title": "Settings",
        "settings.open_dir.label": "Default directory for opening",
        "settings.save_dir.label": "Default directory for export / saving",
        "settings.dir.placeholder": "Empty = last used directory",
        "settings.format.label": "Preferred image file format",
        "settings.log.label": "Log file",
        "settings.log.tooltip": "Path of the log file (select to copy)",
        "settings.log.open_button": "Open folder",
        "settings.log.open_failed": "Could not open the folder:\n{target}",
        "settings.cancel": "Cancel",
        "settings.ok": "OK",
        "settings.pick_open.title": "Choose directory for opening",
        "settings.pick_save.title": "Choose directory for export/saving",
        "settings.invalid_dir.title": "Invalid directory",
        "settings.invalid_dir.body": "{label} is not an existing directory:\n{value}",
        "settings.language.label": "Language",
        "settings.language.restart_title": "Restart required",
        "settings.language.restart_hint": (
            "The language change takes effect on the next start."
        ),
        # Dialogs (QMessageBox)
        "dialog.ai_error.title": "AI error",
        "dialog.ai_error.body": (
            "Error during automatic background removal:\n\n{msg}"
        ),
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

    An unset value intentionally resolves to German, so a fresh install starts
    in the default language until the user picks another in the settings dialog.
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
