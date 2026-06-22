"""Leichtgewichtiges Laufzeit-String-Lookup mit stabilem deutschen Fallback.

Die zentrale ``_TRANSLATIONS``-Tabelle bildet String-Keys auf Werte je Locale
ab. Deutsch ist Default und garantierter Fallback für jeden Key, der einer
Locale fehlt; Englisch ist als Laufzeitsprache verfügbar, der
Einstellungsdialog bietet eine Sprachauswahl. Weitere Locales lassen sich durch
Erweitern von ``_TRANSLATIONS`` ergänzen (Key-für-Key synchron zum Deutschen),
ohne die Aufrufstellen anzufassen.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Final

DEFAULT_LOCALE: Final = "de"
SETTINGS_LOCALE_KEY: Final = "locale"

# Endonyme für die Sprachauswahl; zur Laufzeit werden nur Locales angeboten,
# die tatsächlich in ``_TRANSLATIONS`` vorhanden sind (siehe ``available_locales``).
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
        "status.load_result_discarded": (
            "Ladeergebnis verworfen – Bild wurde inzwischen geändert"
        ),
        "status.ai_already_running": "KI läuft bereits…",
        "status.ai_processing": "🤖 KI verarbeitet Bild… (kann einige Sekunden dauern)",
        "status.ai_ready": "🤖 KI bereit",
        "status.ai_model_loading": "🤖 KI-Modell wird geladen…",
        "status.ai_warmup_failed": "⚠️ KI-Modell konnte nicht geladen werden",
        "status.ai_cancelling": "Abbruch – warte auf laufende KI…",
        "status.ai_cancelled": "KI-Verarbeitung abgebrochen",
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
        "status.shutdown_failed": (
            "Beenden fehlgeschlagen – ein Hintergrundprozess läuft noch"
        ),
        # Statusleisten-Meldungen mit interpolierten Werten
        "status.loading": "⏳ Lädt: {name}…",
        "status.load_error": "Ladefehler: {msg}",
        "status.file_too_large": "Datei zu groß ({size} MB) – Maximum: {limit} MB",
        "status.image_too_large": "Bild zu groß – Maximum: {limit} MP",
        "status.image_too_large_mp": "Bild zu groß ({mp:.0f} MP) – Maximum: {limit} MP",
        "status.file_missing": "Datei nicht mehr vorhanden: {name}",
        "status.open_not_local": "Nur lokale Dateien können geöffnet werden.",
        "status.ai_error": "KI-Fehler: {msg}",
        # Projektdatei (.bgrproj) – Lade-/Speicherfehler
        "project.error.corrupt": "Projektdatei beschädigt oder kein gültiges Projekt",
        "project.error.too_large": (
            "Projektdatei zu groß ({size} MB) – Maximum: {limit} MB"
        ),
        "project.error.manifest_missing": "Projektdatei unvollständig: manifest.json fehlt",
        "project.error.manifest_invalid": "Projektdatei beschädigt: ungültiges Manifest",
        "project.error.unsupported_version": (
            "Projektformat-Version {version} wird nicht unterstützt"
        ),
        "project.error.unexpected_entry": (
            "Projektdatei abgewiesen: unerwarteter Eintrag „{name}“"
        ),
        "project.error.entry_too_large": (
            "Projektdatei abgewiesen: Eintrag „{name}“ ist zu groß (entpackt)"
        ),
        "project.error.layer_file_missing": (
            "Projektdatei unvollständig: Ebenen-Bild „{file}“ fehlt"
        ),
        "project.error.layer_too_large": (
            "Ebene zu groß ({mp:.0f} MP) – Maximum: {limit} MP"
        ),
        "project.error.layer_size_mismatch": (
            "Ebenengröße {actual} passt nicht zur Canvas-Größe {expected}"
        ),
        # Ebenen-Panel & Projekt-Aktionen (#334)
        "layers.new_name": "Ebene {n}",
        "layers.role.none": "Keine",
        "layers.role.color_motif": "Farbmotiv",
        "layers.role.height_map": "Height Map",
        "layers.role.gloss": "Gloss",
        "layers.height_name": "Höhenkarte",
        "history.desc.layer_added": "Ebene hinzugefügt",
        "history.desc.layer_removed": "Ebene gelöscht",
        "history.desc.layer_duplicated": "Ebene dupliziert",
        "history.desc.layer_reordered": "Ebene verschoben",
        "history.desc.layer_renamed": "Ebene umbenannt",
        "history.desc.layer_active": "Aktive Ebene gewechselt",
        "history.desc.layer_visibility": "Sichtbarkeit geändert",
        "history.desc.layer_opacity": "Opazität geändert",
        "history.desc.layer_role": "Rolle geändert",
        "history.desc.height_generated": "Höhenkarte erzeugt",
        "history.desc.height_imported": "Höhenkarte importiert",
        "history.desc.height_lighten": "Höhe aufgehellt",
        "history.desc.height_darken": "Höhe abgedunkelt",
        "history.desc.height_set": "Höhe gesetzt",
        "history.desc.height_invert": "Höhe invertiert",
        "history.desc.height_optimized": "Höhe optimiert",
        "canvas.layer_added": "Neue Ebene hinzugefügt",
        "canvas.height_generated": "Höhenkarte aus Bild erzeugt",
        "canvas.height_imported": "Höhenkarte importiert: {name}",
        "canvas.height_lightened": "Höhe aufgehellt",
        "canvas.height_darkened": "Höhe abgedunkelt",
        "canvas.height_set": "Höhe gesetzt",
        "canvas.height_inverted": "Höhe invertiert",
        "canvas.height_optimized": "Höhe optimiert",
        "canvas.height_op_error": "Höhen-Operation fehlgeschlagen: {error}",
        "canvas.not_height_layer": "Keine Höhenebene aktiv",
        "canvas.layer_removed": "Ebene gelöscht",
        "canvas.layer_duplicated": "Ebene dupliziert",
        "canvas.cannot_delete_last": "Die letzte Ebene kann nicht gelöscht werden",
        "right_panel.tab.layers": "Ebenen",
        "right_panel.tab.layers.tooltip": "Ebenen verwalten",
        "right_panel.tab.height": "Höhe",
        "right_panel.tab.height.tooltip": "Höhenkarte (Relief)",
        "right_panel.height.section.acquire": "Beschaffen",
        "right_panel.height.section.edit": "Bearbeiten",
        "right_panel.height.section.optimize": "Optimieren",
        "right_panel.height.generate": "Aus Bild erzeugen",
        "right_panel.height.generate.tooltip": (
            "Höhenkarte aus dem aktuellen Bild erzeugen"
        ),
        "right_panel.height.import": "Graustufe importieren…",
        "right_panel.height.import.tooltip": (
            "Graustufenbild als Höhenkarte importieren"
        ),
        "right_panel.height.hint": (
            "Höhenwerkzeuge wirken auf die aktive Höhenebene."
        ),
        "right_panel.height.strength": "Stärke",
        "right_panel.height.lighten": "Aufhellen",
        "right_panel.height.lighten.tooltip": (
            "Höhe in der Auswahl (sonst global) anheben"
        ),
        "right_panel.height.darken": "Abdunkeln",
        "right_panel.height.darken.tooltip": (
            "Höhe in der Auswahl (sonst global) senken"
        ),
        "right_panel.height.set_value": "Wert",
        "right_panel.height.set": "Höhe setzen",
        "right_panel.height.set.tooltip": (
            "Höhe auf den Wert setzen (Auswahl bzw. global)"
        ),
        "right_panel.height.invert": "Invertieren",
        "right_panel.height.invert.tooltip": (
            "Höhe invertieren (Auswahl bzw. global)"
        ),
        "right_panel.height.levels": "Tonwert (Schwarz/Weiß)",
        "right_panel.height.gamma": "Gamma",
        "right_panel.height.gaussian": "Gauß-Glättung (Radius)",
        "right_panel.height.median": "Median-Glättung (Radius)",
        "right_panel.height.threshold": "Schwelle",
        "right_panel.height.steps": "Stufen",
        "right_panel.height.range": "Bereich (Min/Max)",
        "right_panel.height.apply": "Anwenden",
        "right_panel.height.apply.tooltip": "Vorschau auf die Höhenebene anwenden",
        "right_panel.height.discard_preview": "Vorschau verwerfen",
        "right_panel.height.discard_preview.tooltip": (
            "Vorschau verwerfen, ohne anzuwenden"
        ),
        "right_panel.layers.section": "Ebenen",
        "right_panel.layers.add.tooltip": "Neue Ebene",
        "right_panel.layers.duplicate.tooltip": "Aktive Ebene duplizieren",
        "right_panel.layers.delete.tooltip": "Aktive Ebene löschen",
        "right_panel.layers.move_up.tooltip": "Ebene nach oben",
        "right_panel.layers.move_down.tooltip": "Ebene nach unten",
        "right_panel.layers.rename.tooltip": "Aktive Ebene umbenennen",
        "right_panel.layers.role_label": "Rolle:",
        "right_panel.layers.role.tooltip": (
            "Rolle der aktiven Ebene (für spätere UV-Druck-Werkzeuge)"
        ),
        "right_panel.layers.visible.tooltip": "Sichtbarkeit umschalten",
        "right_panel.layers.select.tooltip": "Als aktive Ebene wählen",
        "right_panel.layers.opacity.tooltip": "Opazität (beim Loslassen übernommen)",
        "right_panel.layers.empty": (
            "Kein Projekt geladen – Bild öffnen oder „Neues Projekt“."
        ),
        "menu.project": "Projekt",
        "action.new_project": "Neues Projekt",
        "action.open_project": "Projekt öffnen…",
        "action.save_project": "Projekt speichern",
        "action.save_project_as": "Projekt speichern unter…",
        "dialog.open_project.title": "Projekt öffnen",
        "dialog.open_project.filter": "BgRemover-Projekt (*.bgrproj)",
        "dialog.save_project.title": "Projekt speichern",
        "dialog.rename.title": "Ebene umbenennen",
        "dialog.rename.label": "Neuer Name:",
        "dialog.import_height.title": "Höhenkarte importieren",
        "dialog.project_error.title": "Projektfehler",
        "project.new": "Neues Projekt erstellt",
        "project.saved": "Projekt gespeichert: {name}",
        "project.opened": "Projekt geöffnet: {name}",
        "project.no_project": "Kein Projekt zum Speichern",
        "project.save_failed": "Projekt speichern fehlgeschlagen: {error}",
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
        "action.resize": "Größe ändern…",
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
        "right_panel.tab.adjust": "Anpassen",
        "right_panel.tab.adjust.tooltip": (
            "Farbkorrektur – Helligkeit, Kontrast, Sättigung"
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
        "right_panel.transform.section.resize": "Größe ändern",
        "right_panel.transform.resize": "Größe ändern…",
        "right_panel.transform.resize.tooltip": (
            "Bild/Projekt auf eine Zielgröße in Pixeln skalieren (Resampling)"
        ),
        # Größe-ändern-Dialog (#359)
        "resize.title": "Größe ändern",
        "resize.width": "Breite",
        "resize.height": "Höhe",
        "resize.link_aspect": "Seitenverhältnis koppeln",
        "resize.resample.label": "Verfahren:",
        "resize.resample.lanczos": "Lanczos (beste Qualität)",
        "resize.resample.bicubic": "Bikubisch",
        "resize.resample.bilinear": "Bilinear",
        "resize.resample.nearest": "Nächster Nachbar",
        "resize.megapixels": "{mp:.1f} MP (Maximum: {maximum} MP)",
        "resize.ok": "Anwenden",
        "resize.cancel": "Abbrechen",
        # Right panel — Adjust tab contents (#360)
        "right_panel.adjust.section": "Farbkorrektur",
        "right_panel.adjust.hint": "Wirkt auf die aktive Farbebene.",
        "right_panel.adjust.brightness": "Helligkeit:  {value} %",
        "right_panel.adjust.brightness.tooltip": (
            "Helligkeit der aktiven Farbebene (100 % = unverändert)"
        ),
        "right_panel.adjust.contrast": "Kontrast:  {value} %",
        "right_panel.adjust.contrast.tooltip": (
            "Kontrast der aktiven Farbebene (100 % = unverändert)"
        ),
        "right_panel.adjust.saturation": "Sättigung:  {value} %",
        "right_panel.adjust.saturation.tooltip": (
            "Sättigung der aktiven Farbebene (0 % = Graustufe, 100 % = unverändert)"
        ),
        "right_panel.adjust.reset": "Zurücksetzen",
        "right_panel.adjust.reset.tooltip": (
            "Regler auf 100 % zurücksetzen und Vorschau verwerfen"
        ),
        "right_panel.adjust.apply": "Anwenden",
        "right_panel.adjust.apply.tooltip": (
            "Farbkorrektur auf die aktive Farbebene anwenden"
        ),
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
        # Main-window dialogs
        "dialog.unsaved.title": "Ungespeicherte Änderungen",
        "dialog.unsaved.body": (
            "Das Bild wurde bearbeitet. Änderungen speichern, bevor es "
            "verworfen wird?"
        ),
        "dialog.open.title": "Bild öffnen",
        "dialog.open.filter": (
            "Bilder (*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.tif *.gif);;"
            "Alle Dateien (*)"
        ),
        "dialog.save.title": "Bild speichern unter…",
        "dialog.color.title": "Hintergrundfarbe wählen",
        # Canvas status messages
        "canvas.opened": "Geöffnet: {name}  ({w} × {h} px)",
        "canvas.opened_extra": (
            "Geöffnet: {name}  ({extra} weitere Datei(en) ignoriert)"
        ),
        "canvas.undo_none": "Nichts mehr zum Rückgängigmachen",
        "canvas.undo_done": "↩  Rückgängig: {desc}",
        "canvas.redo_none": "Nichts mehr zum Wiederherstellen",
        "canvas.redo_done": "↪  Wiederherstellen: {desc}",
        "canvas.undo_to": "↩  {steps} Schritt(e) rückgängig  (bis: {desc})",
        "canvas.original_restored": "🔄  Original wiederhergestellt",
        "canvas.selection_cleared": "Auswahl aufgehoben",
        "canvas.selection_inverted": "Auswahl invertiert: {pixels:,} Pixel",
        "canvas.selection_expanded": "Auswahl um {radius} px erweitert: {pixels:,} Pixel",
        "canvas.selection_shrunk": "Auswahl um {radius} px geschrumpft: {pixels:,} Pixel",
        "canvas.bg_removed": "Hintergrund entfernt (transparent)",
        "canvas.remove_error": "Fehler beim Entfernen: {error}",
        "canvas.bg_replaced": "Hintergrund ersetzt: {color}",
        "canvas.replace_error": "Fehler beim Ersetzen: {error}",
        "canvas.ai_done": "✅ KI-Hintergrundentfernung abgeschlossen",
        "canvas.selection_pixels": "Auswahl: {pixels:,} Pixel",
        "canvas.selection_error": "Auswahl-Fehler: {msg}",
        "canvas.lasso_cancelled": "Polygon-Lasso abgebrochen",
        "canvas.lasso_selected": "Polygon-Lasso: {pixels:,} Pixel ausgewählt",
        "canvas.lasso_points_one": (
            "Polygon-Lasso: {n} Punkt — Doppelklick zum Abschließen · Esc = abbrechen"
        ),
        "canvas.lasso_points_many": (
            "Polygon-Lasso: {n} Punkte — Doppelklick zum Abschließen · Esc = abbrechen"
        ),
        "canvas.format_unsupported": "Format nicht unterstützt",
        "canvas.radius_positive": "Radius muss > 0 sein",
        "canvas.corners_rounded": "Ecken abgerundet: {r} px Radius",
        "canvas.rotate_too_large": (
            "Drehung um {degrees}° würde das Bild zu groß machen "
            "({mp:.0f} MP) – Maximum: {maximum} MP"
        ),
        "canvas.rotated": "{direction} Gedreht: {degrees}°  ({w} × {h} px)",
        "canvas.resized": "⇲ Größe geändert: {w} × {h} px",
        "canvas.resize_too_large": (
            "Zielgröße {w} × {h} px zu groß ({mp:.0f} MP) – Maximum: {maximum} MP"
        ),
        "canvas.color_adjusted": "🎨 Farbkorrektur angewendet",
        "canvas.not_color_layer": "Keine Farbebene aktiv",
        "canvas.flipped_h": "↔ Horizontal gespiegelt",
        "canvas.flipped_v": "↕ Vertikal gespiegelt",
        "canvas.crop_cancelled": "Zuschnitt abgebrochen",
        "canvas.crop_size": "⇲ Größe: {w} × {h} px",
        "canvas.crop_start_circle": (
            "✂  Ausschnitt verschieben  [Kreis]  —  dann ✓ Anwenden klicken"
        ),
        "canvas.crop_start_ratio": (
            "✂  Ausschnitt verschieben  [{w} × {h} px]  —  dann ✓ Anwenden klicken"
        ),
        "canvas.cropped": "✂  Zugeschnitten: {w} × {h} px",
        "canvas.save_failed": "Speichern fehlgeschlagen: {error}",
        "canvas.saved": "💾 Gespeichert: {name}",
        # History step descriptions
        "history.desc.generic": "Bearbeitung",
        "history.desc.original_restored": "🔄 Original wiederhergestellt",
        "history.desc.bg_removed": "Hintergrund entfernt",
        "history.desc.color_replaced": "Farbe ersetzt ({color})",
        "history.desc.ai_bg": "KI-Hintergrundentfernung",
        "history.desc.round_corners": "Ecken abgerundet ({r} px)",
        "history.desc.rotated": "{direction} Gedreht {degrees}°",
        "history.desc.resized": "Größe geändert ({w}×{h} px)",
        "history.desc.color_adjusted": "Farbkorrektur",
        "history.desc.crop_circle": "Format: Kreis",
        "history.desc.crop_ratio": "Format: {w}×{h} px",
    },
    "en": {
        # Status bar messages
        "status.no_image_loaded": "No image loaded",
        "status.no_image_to_save": "No image to save",
        "status.already_loading": "Already loading an image…",
        "status.load_result_discarded": (
            "Load result discarded – the image changed in the meantime"
        ),
        "status.ai_already_running": "AI is already running…",
        "status.ai_processing": "🤖 AI is processing the image… (may take a few seconds)",
        "status.ai_ready": "🤖 AI ready",
        "status.ai_model_loading": "🤖 Loading AI model…",
        "status.ai_warmup_failed": "⚠️ Could not load the AI model",
        "status.ai_cancelling": "Cancelling – waiting for the running AI…",
        "status.ai_cancelled": "AI processing cancelled",
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
        "status.shutdown_failed": (
            "Could not quit – a background process is still running"
        ),
        # Statusleisten-Meldungen mit interpolierten Werten
        "status.loading": "⏳ Loading: {name}…",
        "status.load_error": "Load error: {msg}",
        "status.file_too_large": "File too large ({size} MB) – maximum: {limit} MB",
        "status.image_too_large": "Image too large – maximum: {limit} MP",
        "status.image_too_large_mp": "Image too large ({mp:.0f} MP) – maximum: {limit} MP",
        "status.file_missing": "File no longer exists: {name}",
        "status.open_not_local": "Only local files can be opened.",
        "status.ai_error": "AI error: {msg}",
        # Project file (.bgrproj) – load/save errors
        "project.error.corrupt": "Project file is corrupt or not a valid project",
        "project.error.too_large": (
            "Project file too large ({size} MB) – maximum: {limit} MB"
        ),
        "project.error.manifest_missing": "Project file incomplete: manifest.json is missing",
        "project.error.manifest_invalid": "Project file corrupt: invalid manifest",
        "project.error.unsupported_version": (
            "Project format version {version} is not supported"
        ),
        "project.error.unexpected_entry": (
            "Project file rejected: unexpected entry “{name}”"
        ),
        "project.error.entry_too_large": (
            "Project file rejected: entry “{name}” is too large (uncompressed)"
        ),
        "project.error.layer_file_missing": (
            "Project file incomplete: layer image “{file}” is missing"
        ),
        "project.error.layer_too_large": (
            "Layer too large ({mp:.0f} MP) – maximum: {limit} MP"
        ),
        "project.error.layer_size_mismatch": (
            "Layer size {actual} does not match the canvas size {expected}"
        ),
        # Layer panel & project actions (#334)
        "layers.new_name": "Layer {n}",
        "layers.role.none": "None",
        "layers.role.color_motif": "Color motif",
        "layers.role.height_map": "Height map",
        "layers.role.gloss": "Gloss",
        "layers.height_name": "Height map",
        "history.desc.layer_added": "Layer added",
        "history.desc.layer_removed": "Layer deleted",
        "history.desc.layer_duplicated": "Layer duplicated",
        "history.desc.layer_reordered": "Layer reordered",
        "history.desc.layer_renamed": "Layer renamed",
        "history.desc.layer_active": "Active layer changed",
        "history.desc.layer_visibility": "Visibility changed",
        "history.desc.layer_opacity": "Opacity changed",
        "history.desc.layer_role": "Role changed",
        "history.desc.height_generated": "Height map generated",
        "history.desc.height_imported": "Height map imported",
        "history.desc.height_lighten": "Height lightened",
        "history.desc.height_darken": "Height darkened",
        "history.desc.height_set": "Height set",
        "history.desc.height_invert": "Height inverted",
        "history.desc.height_optimized": "Height optimized",
        "canvas.layer_added": "New layer added",
        "canvas.height_generated": "Height map generated from image",
        "canvas.height_imported": "Height map imported: {name}",
        "canvas.height_lightened": "Height lightened",
        "canvas.height_darkened": "Height darkened",
        "canvas.height_set": "Height set",
        "canvas.height_inverted": "Height inverted",
        "canvas.height_optimized": "Height optimized",
        "canvas.height_op_error": "Height operation failed: {error}",
        "canvas.not_height_layer": "No height layer active",
        "canvas.layer_removed": "Layer deleted",
        "canvas.layer_duplicated": "Layer duplicated",
        "canvas.cannot_delete_last": "The last layer cannot be deleted",
        "right_panel.tab.layers": "Layers",
        "right_panel.tab.layers.tooltip": "Manage layers",
        "right_panel.tab.height": "Height",
        "right_panel.tab.height.tooltip": "Height map (relief)",
        "right_panel.height.section.acquire": "Acquire",
        "right_panel.height.section.edit": "Edit",
        "right_panel.height.section.optimize": "Optimize",
        "right_panel.height.generate": "Generate from image",
        "right_panel.height.generate.tooltip": (
            "Generate a height map from the current image"
        ),
        "right_panel.height.import": "Import grayscale…",
        "right_panel.height.import.tooltip": (
            "Import a grayscale image as a height map"
        ),
        "right_panel.height.hint": (
            "Height tools act on the active height layer."
        ),
        "right_panel.height.strength": "Strength",
        "right_panel.height.lighten": "Lighten",
        "right_panel.height.lighten.tooltip": (
            "Raise height within the selection (otherwise global)"
        ),
        "right_panel.height.darken": "Darken",
        "right_panel.height.darken.tooltip": (
            "Lower height within the selection (otherwise global)"
        ),
        "right_panel.height.set_value": "Value",
        "right_panel.height.set": "Set height",
        "right_panel.height.set.tooltip": (
            "Set height to the value (selection or global)"
        ),
        "right_panel.height.invert": "Invert",
        "right_panel.height.invert.tooltip": (
            "Invert height (selection or global)"
        ),
        "right_panel.height.levels": "Levels (black/white)",
        "right_panel.height.gamma": "Gamma",
        "right_panel.height.gaussian": "Gaussian blur (radius)",
        "right_panel.height.median": "Median blur (radius)",
        "right_panel.height.threshold": "Threshold",
        "right_panel.height.steps": "Steps",
        "right_panel.height.range": "Range (min/max)",
        "right_panel.height.apply": "Apply",
        "right_panel.height.apply.tooltip": "Apply the preview to the height layer",
        "right_panel.height.discard_preview": "Discard preview",
        "right_panel.height.discard_preview.tooltip": (
            "Discard the preview without applying"
        ),
        "right_panel.layers.section": "Layers",
        "right_panel.layers.add.tooltip": "New layer",
        "right_panel.layers.duplicate.tooltip": "Duplicate active layer",
        "right_panel.layers.delete.tooltip": "Delete active layer",
        "right_panel.layers.move_up.tooltip": "Move layer up",
        "right_panel.layers.move_down.tooltip": "Move layer down",
        "right_panel.layers.rename.tooltip": "Rename active layer",
        "right_panel.layers.role_label": "Role:",
        "right_panel.layers.role.tooltip": (
            "Role of the active layer (for later UV-print tools)"
        ),
        "right_panel.layers.visible.tooltip": "Toggle visibility",
        "right_panel.layers.select.tooltip": "Select as active layer",
        "right_panel.layers.opacity.tooltip": "Opacity (applied on release)",
        "right_panel.layers.empty": (
            "No project loaded – open an image or “New project”."
        ),
        "menu.project": "Project",
        "action.new_project": "New project",
        "action.open_project": "Open project…",
        "action.save_project": "Save project",
        "action.save_project_as": "Save project as…",
        "dialog.open_project.title": "Open project",
        "dialog.open_project.filter": "BgRemover project (*.bgrproj)",
        "dialog.save_project.title": "Save project",
        "dialog.rename.title": "Rename layer",
        "dialog.rename.label": "New name:",
        "dialog.import_height.title": "Import height map",
        "dialog.project_error.title": "Project error",
        "project.new": "New project created",
        "project.saved": "Project saved: {name}",
        "project.opened": "Project opened: {name}",
        "project.no_project": "No project to save",
        "project.save_failed": "Saving project failed: {error}",
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
        "action.resize": "Resize…",
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
        "right_panel.tab.adjust": "Adjust",
        "right_panel.tab.adjust.tooltip": (
            "Color correction – brightness, contrast, saturation"
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
        "right_panel.transform.section.resize": "Resize",
        "right_panel.transform.resize": "Resize…",
        "right_panel.transform.resize.tooltip": (
            "Scale the image/project to a target size in pixels (resampling)"
        ),
        # Resize dialog (#359)
        "resize.title": "Resize",
        "resize.width": "Width",
        "resize.height": "Height",
        "resize.link_aspect": "Link aspect ratio",
        "resize.resample.label": "Method:",
        "resize.resample.lanczos": "Lanczos (best quality)",
        "resize.resample.bicubic": "Bicubic",
        "resize.resample.bilinear": "Bilinear",
        "resize.resample.nearest": "Nearest neighbor",
        "resize.megapixels": "{mp:.1f} MP (maximum: {maximum} MP)",
        "resize.ok": "Apply",
        "resize.cancel": "Cancel",
        # Right panel — Adjust tab contents (#360)
        "right_panel.adjust.section": "Color correction",
        "right_panel.adjust.hint": "Acts on the active color layer.",
        "right_panel.adjust.brightness": "Brightness:  {value} %",
        "right_panel.adjust.brightness.tooltip": (
            "Brightness of the active color layer (100% = unchanged)"
        ),
        "right_panel.adjust.contrast": "Contrast:  {value} %",
        "right_panel.adjust.contrast.tooltip": (
            "Contrast of the active color layer (100% = unchanged)"
        ),
        "right_panel.adjust.saturation": "Saturation:  {value} %",
        "right_panel.adjust.saturation.tooltip": (
            "Saturation of the active color layer (0% = grayscale, 100% = unchanged)"
        ),
        "right_panel.adjust.reset": "Reset",
        "right_panel.adjust.reset.tooltip": (
            "Reset the sliders to 100% and discard the preview"
        ),
        "right_panel.adjust.apply": "Apply",
        "right_panel.adjust.apply.tooltip": (
            "Apply the color correction to the active color layer"
        ),
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
        # Main-window dialogs
        "dialog.unsaved.title": "Unsaved changes",
        "dialog.unsaved.body": (
            "The image has been edited. Save changes before discarding it?"
        ),
        "dialog.open.title": "Open image",
        "dialog.open.filter": (
            "Images (*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.tif *.gif);;"
            "All files (*)"
        ),
        "dialog.save.title": "Save image as…",
        "dialog.color.title": "Choose background color",
        # Canvas status messages
        "canvas.opened": "Opened: {name}  ({w} × {h} px)",
        "canvas.opened_extra": (
            "Opened: {name}  ({extra} more file(s) ignored)"
        ),
        "canvas.undo_none": "Nothing left to undo",
        "canvas.undo_done": "↩  Undone: {desc}",
        "canvas.redo_none": "Nothing left to redo",
        "canvas.redo_done": "↪  Redone: {desc}",
        "canvas.undo_to": "↩  {steps} step(s) undone  (to: {desc})",
        "canvas.original_restored": "🔄  Original restored",
        "canvas.selection_cleared": "Selection cleared",
        "canvas.selection_inverted": "Selection inverted: {pixels:,} pixels",
        "canvas.selection_expanded": "Selection grown by {radius} px: {pixels:,} pixels",
        "canvas.selection_shrunk": "Selection shrunk by {radius} px: {pixels:,} pixels",
        "canvas.bg_removed": "Background removed (transparent)",
        "canvas.remove_error": "Error while removing: {error}",
        "canvas.bg_replaced": "Background replaced: {color}",
        "canvas.replace_error": "Error while replacing: {error}",
        "canvas.ai_done": "✅ AI background removal complete",
        "canvas.selection_pixels": "Selection: {pixels:,} pixels",
        "canvas.selection_error": "Selection error: {msg}",
        "canvas.lasso_cancelled": "Polygon lasso cancelled",
        "canvas.lasso_selected": "Polygon lasso: {pixels:,} pixels selected",
        "canvas.lasso_points_one": (
            "Polygon lasso: {n} point — double-click to finish · Esc = cancel"
        ),
        "canvas.lasso_points_many": (
            "Polygon lasso: {n} points — double-click to finish · Esc = cancel"
        ),
        "canvas.format_unsupported": "Format not supported",
        "canvas.radius_positive": "Radius must be > 0",
        "canvas.corners_rounded": "Corners rounded: {r} px radius",
        "canvas.rotate_too_large": (
            "Rotating by {degrees}° would make the image too large "
            "({mp:.0f} MP) – maximum: {maximum} MP"
        ),
        "canvas.rotated": "{direction} Rotated: {degrees}°  ({w} × {h} px)",
        "canvas.resized": "⇲ Resized: {w} × {h} px",
        "canvas.resize_too_large": (
            "Target size {w} × {h} px too large ({mp:.0f} MP) – maximum: {maximum} MP"
        ),
        "canvas.color_adjusted": "🎨 Color correction applied",
        "canvas.not_color_layer": "No color layer active",
        "canvas.flipped_h": "↔ Flipped horizontally",
        "canvas.flipped_v": "↕ Flipped vertically",
        "canvas.crop_cancelled": "Crop cancelled",
        "canvas.crop_size": "⇲ Size: {w} × {h} px",
        "canvas.crop_start_circle": (
            "✂  Move the crop  [Circle]  —  then click ✓ Apply"
        ),
        "canvas.crop_start_ratio": (
            "✂  Move the crop  [{w} × {h} px]  —  then click ✓ Apply"
        ),
        "canvas.cropped": "✂  Cropped: {w} × {h} px",
        "canvas.save_failed": "Save failed: {error}",
        "canvas.saved": "💾 Saved: {name}",
        # History step descriptions
        "history.desc.generic": "Edit",
        "history.desc.original_restored": "🔄 Original restored",
        "history.desc.bg_removed": "Background removed",
        "history.desc.color_replaced": "Color replaced ({color})",
        "history.desc.ai_bg": "AI background removal",
        "history.desc.round_corners": "Corners rounded ({r} px)",
        "history.desc.rotated": "{direction} Rotated {degrees}°",
        "history.desc.resized": "Resized ({w}×{h} px)",
        "history.desc.color_adjusted": "Color correction",
        "history.desc.crop_circle": "Format: Circle",
        "history.desc.crop_ratio": "Format: {w}×{h} px",
    },
}

_current_locale = DEFAULT_LOCALE


def available_locales() -> tuple[str, ...]:
    """Return runtime locales currently backed by a string table."""

    return tuple(_TRANSLATIONS)


def normalize_locale(locale: object | None) -> str:
    """Normalisiert einen Locale-artigen Wert; Fallback auf Deutsch, falls nicht unterstützt."""

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
    """Setzt die prozesslokale UI-Locale und gibt die effektive Locale zurück."""

    global _current_locale
    _current_locale = normalize_locale(locale)
    return _current_locale


def init_locale_from_settings(settings_value: object | None) -> str:
    """Initialisiert die Laufzeit-Locale aus den persistierten Einstellungen.

    Ein nicht gesetzter Wert führt bewusst zu Deutsch, damit eine frische
    Installation in der Default-Sprache startet, bis der Nutzer im
    Einstellungsdialog eine andere wählt.
    """

    return configure_locale(settings_value)


def current_locale() -> str:
    """Gibt die effektive prozesslokale UI-Locale zurück."""

    return _current_locale


def tr(key: str, **values: object) -> str:
    """Übersetzt ``key`` für die aktuelle Locale, mit Fallback auf Deutsch."""

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
