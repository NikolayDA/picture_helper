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
        "status.ai_processing": "KI verarbeitet Bild… (kann einige Sekunden dauern)",
        "status.ai_ready": "KI bereit",
        "status.ai_model_loading": "KI-Modell wird geladen…",
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
        "project.warning.role_normalized": (
            "Inkompatible Height-Map-Rolle entfernt: „{name}“ ist keine Höhenebene"
        ),
        # EufyMake-Export – Konsistenzbefunde (#354)
        "eufymake.export.color_motif_missing": (
            "Farbmotiv fehlt: keine COLOR_MOTIF-Rolle und keine zum Komposit "
            "beitragende Farbebene."
        ),
        "eufymake.export.optional_role_missing": (
            "Ausgewählte optionale Rolle „{role_name}“ hat keine Ebene."
        ),
        "eufymake.export.asset_size_mismatch": (
            "Assetgröße {actual} passt nicht zur Zielgröße {expected}."
        ),
        "eufymake.export.invalid_target_params": "Ungültige Zielparameter: {detail}",
        "eufymake.export.height_map_empty": (
            "Höhenkarte ist leer oder konstant und liefert möglicherweise kein Relief."
        ),
        "eufymake.export.gloss_mask_empty": (
            "Gloss-Maske ist leer oder konstant und ist möglicherweise nutzlos."
        ),
        "eufymake.export.bit_depth_unconfirmed": (
            "{bits}-Bit-Höhenkarte ist für EufyMake Studio nicht offiziell bestätigt."
        ),
        "eufymake.export.gloss_ink_mode": (
            "Gloss ist nur ein Import-/Hilfsasset – Ink-Mode und Layerzuweisung "
            "erfolgen in EufyMake Studio."
        ),
        "eufymake.export.physical_size_unverified": (
            "Physische Größe bzw. Pixel↔mm/DPI-Annahme ist plausibel, aber kein "
            "bestätigter Herstellervertrag."
        ),
        # Allgemeine Pre-Export-Prüfung (#379)
        "export.checks.dimensions_invalid": (
            "Ungültige Abmessungen: {width}×{height} px – Breite und Höhe müssen positiv sein."
        ),
        "export.checks.dimensions_too_large": (
            "Ausgabe zu groß: {mp} MP überschreiten das Limit von {limit} MP."
        ),
        "export.checks.color_space_unexpected": (
            "Unerwarteter Farbraum: {actual} (erwartet: {expected})."
        ),
        "export.checks.output_empty": "Leere Ausgabe: Das Projekt enthält keine Ebenen.",
        "export.checks.resolution_too_low": (
            "Auflösung niedrig: {dpi} DPI (empfohlenes Minimum: {minimum} DPI)."
        ),
        "export.checks.resolution_too_high": (
            "Auflösung sehr hoch: {dpi} DPI (empfohlenes Maximum: {maximum} DPI)."
        ),
        "export.checks.fully_transparent": (
            "Vollständig transparent: Die Ausgabe enthält keine sichtbaren Pixel."
        ),
        "export.checks.unexpected_alpha": (
            "Teiltransparenz: {percent}% der Pixel sind teildurchsichtig."
        ),
        "export.checks.print_area_exceeded": (
            "Motiv überschreitet die Druckfläche: "
            "{width}×{height} mm > {medium_w}×{medium_h} mm."
        ),
        # Pre-Export-Prüfung beim normalen Speichern (#380)
        "export.check.error.title": "Speichern nicht möglich",
        "export.check.blocked": (
            "Das Speichern wurde wegen folgender Probleme abgebrochen:\n\n{details}"
        ),
        "export.check.warning.title": "Warnungen vor dem Speichern",
        "export.check.confirm": (
            "Es liegen Warnungen vor:\n\n{details}\n\nTrotzdem speichern?"
        ),
        # EufyMake-Export – Menü, Dialog & Meldungen (#355)
        "action.export_eufymake": "Assets für EufyMake Studio exportieren…",
        "eufymake.dialog.title": "Assets für EufyMake Studio exportieren",
        "eufymake.dialog.intro": (
            "BgRemover schreibt Import-Assets für EufyMake Studio – kein fertiges "
            "„.empf“-Projekt. Importiere und positioniere sie anschließend in "
            "Studio, weise dort Ink-Modi/Layer zu und speichere das Projekt selbst "
            "als „.empf“."
        ),
        "eufymake.dialog.section.assets": "Assets",
        "eufymake.dialog.color_motif": "Farbmotiv (erforderlich)",
        "eufymake.dialog.color_motif.hint": (
            "RGBA-PNG aus dem Farbkomposit; Transparenz bleibt erhalten."
        ),
        "eufymake.dialog.height": "Höhenkarte einbeziehen",
        "eufymake.dialog.height.hint": "Graustufen-PNG: hell = hoch, dunkel = niedrig.",
        "eufymake.dialog.height.unavailable": "Keine Höhenebene im Projekt.",
        "eufymake.dialog.gloss": "Gloss-Maske einbeziehen (experimentell)",
        "eufymake.dialog.gloss.hint": (
            "Optionales Hilfsasset. Ink-Mode und Layerzuweisung erfolgen in "
            "EufyMake Studio."
        ),
        "eufymake.dialog.gloss.unavailable": "Keine Gloss-Ebene im Projekt.",
        "eufymake.dialog.section.target": "Zielparameter",
        "eufymake.dialog.bit_depth": "Bittiefe der Höhenkarte:",
        "eufymake.dialog.bit_depth.8": "8 Bit (Standard)",
        "eufymake.dialog.bit_depth.16": "16 Bit (experimentell, nicht bestätigt)",
        "eufymake.dialog.size": "Zielgröße: {w} × {h} px",
        "eufymake.dialog.physical": "Physische Größe: {w} × {h} mm ({dpi} dpi)",
        "eufymake.dialog.physical.unset": "Physische Größe: nicht gesetzt",
        "eufymake.dialog.section.dest": "Ziel",
        "eufymake.dialog.dest.label": "Exportordner:",
        "eufymake.dialog.dest.placeholder": "Noch kein Ordner gewählt",
        "eufymake.dialog.dest.is_file": (
            "Das Ziel ist eine vorhandene Datei – bitte einen Ordner wählen."
        ),
        "eufymake.dialog.dest.browse": "Durchsuchen…",
        "eufymake.dialog.dest.dialog_title": "Exportordner wählen",
        "eufymake.dialog.section.findings": "Prüfung",
        "eufymake.dialog.findings.ok": "Keine Beanstandungen.",
        "eufymake.dialog.finding.error": "⛔  {msg}",
        "eufymake.dialog.finding.warning": "⚠️  {msg}",
        "eufymake.dialog.confirm_warnings": "Warnungen verstanden – trotzdem exportieren",
        "eufymake.dialog.cancel": "Abbrechen",
        "eufymake.dialog.export": "Exportieren",
        "eufymake.status.no_project": "Kein Projekt zum Exportieren",
        "eufymake.status.cancelled": "Export abgebrochen",
        "eufymake.status.exported": "✅ Assets für EufyMake Studio exportiert: {path}",
        "eufymake.error.title": "Export fehlgeschlagen",
        "eufymake.error.write": "Export fehlgeschlagen: {error}",
        "eufymake.error.not_directory": (
            "Das Ziel „{path}“ ist eine vorhandene Datei. Bitte einen Ordner als "
            "Exportziel wählen."
        ),
        "eufymake.error.blocked": "Export blockiert – bitte zuerst beheben:\n{details}",
        "eufymake.overwrite.title": "Ordner überschreiben?",
        "eufymake.overwrite.body": "„{path}“ existiert bereits. Inhalt ersetzen?",
        "eufymake.success.title": "Export abgeschlossen",
        "eufymake.success.body": (
            "Import-Assets geschrieben nach:\n{path}\n\n"
            "Nächste Schritte in EufyMake Studio:\n"
            "1. Assets importieren und positionieren.\n"
            "2. Ink-Modi/Layer zuweisen (z. B. Gloss/Varnish).\n"
            "3. Projekt in Studio als „.empf“ speichern."
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
        "canvas.role_incompatible": (
            "Rolle „Height Map“ ist nur für Höhenebenen verfügbar"
        ),
        "canvas.layer_removed": "Ebene gelöscht",
        "canvas.layer_duplicated": "Ebene dupliziert",
        "canvas.cannot_delete_last": "Die letzte Ebene kann nicht gelöscht werden",
        "right_panel.tab.layers": "Ebenen",
        "right_panel.tab.layers.tooltip": "Ebenen verwalten",
        "right_panel.tab.height": "Höhe",
        "right_panel.tab.height.tooltip": "Höhenkarte (Relief)",
        "right_panel.tab.preview": "Vorschau",
        "right_panel.tab.preview.tooltip": "2D-Anzeige für Farbe, Relief und Gloss",
        "right_panel.preview.section": "2D-Vorschaumodus",
        "right_panel.preview.hint": (
            "Die Vorschau ist unabhängig von der aktiven Ebene."
        ),
        "right_panel.preview.mode": "Anzeige:",
        "right_panel.preview.relief_strength": "Relief-Stärke:  {value} %",
        "right_panel.preview.relief_strength.tooltip": (
            "Stärke des Hillshades in Relief- und Kombiniert-Modus"
        ),
        "right_panel.preview.gloss_visible": "Gloss anzeigen",
        "right_panel.preview.gloss_visible.tooltip": (
            "Gloss-Sheen in Gloss- und Kombiniert-Modus ein-/ausblenden"
        ),
        "right_panel.preview.export_hint": (
            "Nur Anzeige – „Bild speichern“ exportiert weiterhin ausschließlich "
            "das Farbmotiv."
        ),
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
        "menu.preview_mode": "Vorschaumodus",
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
        # Verlauf-Popup: Menü-Anker seit #458 (Rail-Button entfallen)
        "action.history": "Verlauf",
        # Zoom-Kontrolle auf der Arbeitsfläche (#464)
        "zoom.in.tooltip": "Vergrößern (+10 %)",
        "zoom.out.tooltip": "Verkleinern (−10 %)",
        "zoom.lock.tooltip": "Zoom fixieren (aktuellen Wert beibehalten)",
        "zoom.unlock.tooltip": "Zoom-Fixierung aufheben",
        "preview.mode.color": "Farbe",
        "preview.mode.relief": "Relief über Farbe",
        "preview.mode.height": "Höhe (Graustufe)",
        "preview.mode.gloss": "Gloss",
        "preview.mode.combined": "Kombiniert",
        # Kurzlabels für das Segmented-Control der 2D-Vorschau (§9 Schritt 6)
        "preview.seg.color": "Farbe",
        "preview.seg.relief": "Relief",
        "preview.seg.height": "Höhe",
        "preview.seg.gloss": "Gloss",
        # Design-Umschalter (Epic #424, Issue #428)
        "action.light_mode": "Helles Design",
        "theme.switched.light": "Helles Design aktiviert.",
        "theme.switched.dark": "Dunkles Design aktiviert.",
        "action.settings": "Einstellungen…",
        # Left toolbar
        "toolbar.move.tooltip": (
            "Verschieben / Zoom\n"
            "Linksklick-Ziehen verschiebt den Ausschnitt · Mausrad zoomt"
        ),
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
        "toolbar.height_lighten.tooltip": (
            "Aufhellen (höher)\n"
            "Malstrich hebt die Höhe der aktiven Höhen-Ebene an"
        ),
        "toolbar.height_darken.tooltip": (
            "Abdunkeln (tiefer)\n"
            "Malstrich senkt die Höhe der aktiven Höhen-Ebene ab"
        ),
        "toolbar.height_tools.disabled.tooltip": (
            "Höhen-Werkzeug\n"
            "Erst eine Höhen-Ebene aktivieren (Schritt 5: Höhenkarte erzeugen/importieren)"
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
        "toolbar.theme.to_light.tooltip": "Zu hellem Design wechseln",
        "toolbar.theme.to_dark.tooltip": "Zu dunklem Design wechseln",
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
        "right_panel.selection.section.settings": "Werkzeug-Einstellungen",
        "right_panel.selection.section.select": "Auswahl",
        "right_panel.selection.tolerance": "Toleranz (Zauberstab):  {value}",
        "right_panel.selection.tolerance.tooltip": (
            "Steuert wie ähnlich Farben sein müssen um ausgewählt zu werden.\n"
            "Niedrig = nur sehr ähnliche Farben · Hoch = viele Farbtöne"
        ),
        "right_panel.selection.brush_size": "Pinselgröße:  {value} px",
        "right_panel.selection.brush_size.tooltip": (
            "Größe des Pinsel-/Radiergummi-Werkzeugs in Pixeln"
        ),
        "right_panel.selection.clear": "Aufheben",
        "right_panel.selection.clear.tooltip": (
            "Hebt die aktuelle Auswahl auf (auch: Esc-Taste)"
        ),
        "right_panel.selection.invert": "Invertieren",
        "right_panel.selection.invert.tooltip": (
            "Tauscht aus- und nicht-ausgewählte Bereiche  ({modifier}+Shift+I)"
        ),
        "right_panel.selection.morph.tooltip": (
            "Radius in Pixeln für Erweitern/Schrumpfen der Auswahl"
        ),
        "right_panel.selection.expand": "+ Erweitern",
        "right_panel.selection.expand.tooltip": (
            "Erweitert die Auswahl um den eingestellten Radius"
        ),
        "right_panel.selection.shrink": "− Schrumpfen",
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
        "right_panel.background.section.feather": "Kante glätten",
        "right_panel.background.feather_hint": (
            "Weichzeichnet die Freistellungskante (nur Alpha)."
        ),
        "right_panel.background.feather_radius": "Radius:  {value} px",
        "right_panel.background.feather_radius.tooltip": (
            "Radius der Kantenglättung in Pixeln (0 = aus)"
        ),
        "right_panel.background.feather": "Kante glätten",
        "right_panel.background.feather.tooltip": (
            "Alphakante der aktiven Ebene weichzeichnen (Auswahl bzw. global)"
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
        # mm/DPI-Modus + Druckflächenprüfung (#377)
        "resize.mode.label": "Maßeinheit:",
        "resize.mode.pixel": "Pixel",
        "resize.mode.mm": "Millimeter (mm + DPI)",
        "resize.width_mm": "Breite",
        "resize.height_mm": "Höhe",
        "resize.dpi": "Auflösung",
        "resize.medium.label": "Zielmedium:",
        "resize.pixels_result": "Ergebnis: {width}×{height} px ({mp} MP)",
        "resize.print_area_ok": "Passt auf {medium} ({medium_w}×{medium_h} mm).",
        "resize.print_area_exceeded": (
            "⚠ Motiv {width}×{height} mm überschreitet {medium} "
            "({medium_w}×{medium_h} mm)."
        ),
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
        "right_panel.shape.section.resize": "Größe ändern",
        "right_panel.shape.resize_apply": "Größe anwenden",
        "right_panel.shape.resize_apply.tooltip": "Auf die eingegebene Größe skalieren",
        "right_panel.shape.section.format": "Zuschnitt-Format",
        "right_panel.shape.circle": "⬤  Kreis",
        "right_panel.shape.circle.tooltip": "Runden Ausschnitt positionieren und zuschneiden",
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
        "canvas.feathered": "🪶 Kante geglättet: {radius} px",
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
        "history.desc.feathered": "Kante geglättet ({radius} px)",
        "history.desc.crop_circle": "Format: Kreis",
        "history.desc.crop_ratio": "Format: {w}×{h} px",
        # §9-Angleich rechte Spalte – KI/Export/Speichern (#436–#440)
        # Kurzlabel, damit der Primärbutton einzeilig bleibt (§5.4, #515);
        # der volle Wortlaut steht im Tooltip.
        "right_panel.ai.remove": "Hintergrund entfernen (KI)",
        "right_panel.ai.remove.tooltip": (
            "Hintergrund automatisch entfernen: Motiv per KI vom Hintergrund trennen"),
        "right_panel.export.section.save": "Speichern",
        "right_panel.export.format_label": "Dateiformat",
        "right_panel.export.save": "Bild speichern",
        "right_panel.export.save.tooltip": "Das Farbmotiv als Bild speichern",
        "right_panel.export.section.uvprint": "UV-Druck",
        "right_panel.export.eufymake": "Assets für EufyMake Studio exportieren…",
        "right_panel.export.eufymake.tooltip": (
            "Farbe, Höhe und Gloss für EufyMake Studio exportieren"),
        "workflow.open.recent": "Zuletzt geöffnet",
        # Geführter Workflow – Schrittleiste, Inspector-Kopf, Navigation (Epic #418)
        "workflow.step.open": "Öffnen",
        "workflow.step.cutout": "Freistellen",
        "workflow.step.adjust": "Anpassen",
        "workflow.step.shape": "Form & Maße",
        "workflow.step.relief": "Relief & Ebenen",
        "workflow.step.export": "Export",
        "workflow.title.open": "Schritt 1 · Öffnen",
        "workflow.title.cutout": "Schritt 2 · Freistellen",
        "workflow.title.adjust": "Schritt 3 · Anpassen",
        "workflow.title.shape": "Schritt 4 · Form & Maße",
        "workflow.title.relief": "Schritt 5 · Relief & Ebenen",
        "workflow.title.export": "Schritt 6 · Export",
        "workflow.desc.open": "Bild laden — per Drag & Drop, Dialog oder zuletzt geöffnet.",
        "workflow.desc.cutout": "Motiv vom Hintergrund trennen — automatisch oder von Hand.",
        "workflow.desc.adjust": "Helligkeit, Kontrast und Sättigung mit Live-Vorschau.",
        "workflow.desc.shape": "Drehen, spiegeln, abrunden, zuschneiden und skalieren.",
        "workflow.desc.relief": "Ebenen verwalten und die Höhenkarte für den Reliefdruck.",
        "workflow.desc.export": "Ergebnis prüfen, speichern oder für EufyMake exportieren.",
        "workflow.next.open": "Weiter: Freistellen →",
        "workflow.next.cutout": "Weiter: Anpassen →",
        "workflow.next.adjust": "Weiter: Form & Maße →",
        "workflow.next.shape": "Weiter: Relief & Ebenen →",
        "workflow.next.relief": "Weiter: Export →",
        "workflow.next.export": "Exportieren ✓",
        "workflow.back": "← Zurück",
        "workflow.open.drop": "Bild hierher ziehen",
        "workflow.open.formats": "PNG · JPEG · WebP · TIFF · BMP · GIF",
        "workflow.open.button": "Datei öffnen…",
        "workflow.locked": "Erst ein Bild öffnen (Schritt 1)",
        "workflow.status.step": "Schritt {num}/{total}: {title}",
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
        "status.ai_processing": "AI is processing the image… (may take a few seconds)",
        "status.ai_ready": "AI ready",
        "status.ai_model_loading": "Loading AI model…",
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
        "project.warning.role_normalized": (
            "Removed incompatible height-map role: “{name}” is not a height layer"
        ),
        # EufyMake export – consistency findings (#354)
        "eufymake.export.color_motif_missing": (
            "Color motif missing: no COLOR_MOTIF role and no color layer "
            "contributing to the composite."
        ),
        "eufymake.export.optional_role_missing": (
            "Selected optional role “{role_name}” has no layer."
        ),
        "eufymake.export.asset_size_mismatch": (
            "Asset size {actual} does not match the target size {expected}."
        ),
        "eufymake.export.invalid_target_params": "Invalid target parameters: {detail}",
        "eufymake.export.height_map_empty": (
            "The height map is empty or constant and may not produce any relief."
        ),
        "eufymake.export.gloss_mask_empty": (
            "The gloss mask is empty or constant and may be useless."
        ),
        "eufymake.export.bit_depth_unconfirmed": (
            "A {bits}-bit height map is not officially confirmed for EufyMake Studio."
        ),
        "eufymake.export.gloss_ink_mode": (
            "Gloss is only an import/helper asset – ink mode and layer assignment "
            "happen in EufyMake Studio."
        ),
        "eufymake.export.physical_size_unverified": (
            "Physical size and the pixel↔mm/DPI assumption are plausible but not a "
            "confirmed vendor contract."
        ),
        # General pre-export checks (#379)
        "export.checks.dimensions_invalid": (
            "Invalid dimensions: {width}×{height} px – width and height must be positive."
        ),
        "export.checks.dimensions_too_large": (
            "Output too large: {mp} MP exceed the limit of {limit} MP."
        ),
        "export.checks.color_space_unexpected": (
            "Unexpected color space: {actual} (expected: {expected})."
        ),
        "export.checks.output_empty": "Empty output: the project contains no layers.",
        "export.checks.resolution_too_low": (
            "Resolution low: {dpi} DPI (recommended minimum: {minimum} DPI)."
        ),
        "export.checks.resolution_too_high": (
            "Resolution very high: {dpi} DPI (recommended maximum: {maximum} DPI)."
        ),
        "export.checks.fully_transparent": (
            "Fully transparent: the output has no visible pixels."
        ),
        "export.checks.unexpected_alpha": (
            "Partial transparency: {percent}% of pixels are semi-transparent."
        ),
        "export.checks.print_area_exceeded": (
            "Motif exceeds the print area: "
            "{width}×{height} mm > {medium_w}×{medium_h} mm."
        ),
        # Pre-export checks on a normal save (#380)
        "export.check.error.title": "Cannot save",
        "export.check.blocked": (
            "Saving was aborted due to the following problems:\n\n{details}"
        ),
        "export.check.warning.title": "Warnings before saving",
        "export.check.confirm": (
            "There are warnings:\n\n{details}\n\nSave anyway?"
        ),
        # EufyMake export – menu, dialog & messages (#355)
        "action.export_eufymake": "Export assets for EufyMake Studio…",
        "eufymake.dialog.title": "Export assets for EufyMake Studio",
        "eufymake.dialog.intro": (
            "BgRemover writes import assets for EufyMake Studio – not a finished "
            "“.empf” project. Import and position them in Studio afterwards, assign "
            "ink modes/layers there, and save the project yourself as “.empf”."
        ),
        "eufymake.dialog.section.assets": "Assets",
        "eufymake.dialog.color_motif": "Color motif (required)",
        "eufymake.dialog.color_motif.hint": (
            "RGBA PNG from the color composite; transparency is preserved."
        ),
        "eufymake.dialog.height": "Include height map",
        "eufymake.dialog.height.hint": "Grayscale PNG: light = high, dark = low.",
        "eufymake.dialog.height.unavailable": "No height layer in the project.",
        "eufymake.dialog.gloss": "Include gloss mask (experimental)",
        "eufymake.dialog.gloss.hint": (
            "Optional helper asset. Ink mode and layer assignment happen in "
            "EufyMake Studio."
        ),
        "eufymake.dialog.gloss.unavailable": "No gloss layer in the project.",
        "eufymake.dialog.section.target": "Target parameters",
        "eufymake.dialog.bit_depth": "Height-map bit depth:",
        "eufymake.dialog.bit_depth.8": "8-bit (default)",
        "eufymake.dialog.bit_depth.16": "16-bit (experimental, unconfirmed)",
        "eufymake.dialog.size": "Target size: {w} × {h} px",
        "eufymake.dialog.physical": "Physical size: {w} × {h} mm ({dpi} dpi)",
        "eufymake.dialog.physical.unset": "Physical size: not set",
        "eufymake.dialog.section.dest": "Destination",
        "eufymake.dialog.dest.label": "Export folder:",
        "eufymake.dialog.dest.placeholder": "No folder selected yet",
        "eufymake.dialog.dest.is_file": (
            "The destination is an existing file – please choose a folder."
        ),
        "eufymake.dialog.dest.browse": "Browse…",
        "eufymake.dialog.dest.dialog_title": "Choose export folder",
        "eufymake.dialog.section.findings": "Check",
        "eufymake.dialog.findings.ok": "No issues found.",
        "eufymake.dialog.finding.error": "⛔  {msg}",
        "eufymake.dialog.finding.warning": "⚠️  {msg}",
        "eufymake.dialog.confirm_warnings": "I understand the warnings – export anyway",
        "eufymake.dialog.cancel": "Cancel",
        "eufymake.dialog.export": "Export",
        "eufymake.status.no_project": "No project to export",
        "eufymake.status.cancelled": "Export cancelled",
        "eufymake.status.exported": "✅ Assets exported for EufyMake Studio: {path}",
        "eufymake.error.title": "Export failed",
        "eufymake.error.write": "Export failed: {error}",
        "eufymake.error.not_directory": (
            "The target “{path}” is an existing file. Please choose a folder as the "
            "export destination."
        ),
        "eufymake.error.blocked": "Export blocked – please fix these first:\n{details}",
        "eufymake.overwrite.title": "Overwrite folder?",
        "eufymake.overwrite.body": "“{path}” already exists. Replace its contents?",
        "eufymake.success.title": "Export complete",
        "eufymake.success.body": (
            "Import assets written to:\n{path}\n\n"
            "Next steps in EufyMake Studio:\n"
            "1. Import and position the assets.\n"
            "2. Assign ink modes/layers (e.g. gloss/varnish).\n"
            "3. Save the project in Studio as “.empf”."
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
        "canvas.role_incompatible": (
            "The “Height map” role is only available for height layers"
        ),
        "canvas.layer_removed": "Layer deleted",
        "canvas.layer_duplicated": "Layer duplicated",
        "canvas.cannot_delete_last": "The last layer cannot be deleted",
        "right_panel.tab.layers": "Layers",
        "right_panel.tab.layers.tooltip": "Manage layers",
        "right_panel.tab.height": "Height",
        "right_panel.tab.height.tooltip": "Height map (relief)",
        "right_panel.tab.preview": "Preview",
        "right_panel.tab.preview.tooltip": "2D display for color, relief, and gloss",
        "right_panel.preview.section": "2D preview mode",
        "right_panel.preview.hint": (
            "The preview is independent of the active layer."
        ),
        "right_panel.preview.mode": "Display:",
        "right_panel.preview.relief_strength": "Relief strength:  {value}%",
        "right_panel.preview.relief_strength.tooltip": (
            "Hillshade strength in Relief and Combined modes"
        ),
        "right_panel.preview.gloss_visible": "Show gloss",
        "right_panel.preview.gloss_visible.tooltip": (
            "Show or hide the gloss sheen in Gloss and Combined modes"
        ),
        "right_panel.preview.export_hint": (
            "Display only — “Save image” still exports the color motif only."
        ),
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
        "menu.preview_mode": "Preview mode",
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
        # History popup: menu anchor since #458 (rail button removed)
        "action.history": "History",
        # Canvas zoom control (#464)
        "zoom.in.tooltip": "Zoom in (+10%)",
        "zoom.out.tooltip": "Zoom out (−10%)",
        "zoom.lock.tooltip": "Lock zoom (keep the current value)",
        "zoom.unlock.tooltip": "Unlock zoom",
        "preview.mode.color": "Color",
        "preview.mode.relief": "Relief over color",
        "preview.mode.height": "Height (grayscale)",
        "preview.mode.gloss": "Gloss",
        "preview.mode.combined": "Combined",
        # Short labels for the 2D-preview segmented control (§9 step 6)
        "preview.seg.color": "Color",
        "preview.seg.relief": "Relief",
        "preview.seg.height": "Height",
        "preview.seg.gloss": "Gloss",
        # Design toggle (Epic #424, Issue #428)
        "action.light_mode": "Light theme",
        "theme.switched.light": "Light theme enabled.",
        "theme.switched.dark": "Dark theme enabled.",
        "action.settings": "Settings…",
        # Left toolbar
        "toolbar.move.tooltip": (
            "Move / Zoom\n"
            "Left-click drag pans the view · mouse wheel zooms"
        ),
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
        "toolbar.height_lighten.tooltip": (
            "Lighten (raise)\n"
            "Brush stroke raises the height of the active height layer"
        ),
        "toolbar.height_darken.tooltip": (
            "Darken (lower)\n"
            "Brush stroke lowers the height of the active height layer"
        ),
        "toolbar.height_tools.disabled.tooltip": (
            "Height tool\n"
            "Activate a height layer first (step 5: generate/import a height map)"
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
        "toolbar.theme.to_light.tooltip": "Switch to the light theme",
        "toolbar.theme.to_dark.tooltip": "Switch to the dark theme",
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
        "right_panel.selection.section.settings": "Tool settings",
        "right_panel.selection.section.select": "Selection",
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
        "right_panel.selection.expand": "+ Grow",
        "right_panel.selection.expand.tooltip": (
            "Grows the selection by the set radius"
        ),
        "right_panel.selection.shrink": "− Shrink",
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
        "right_panel.background.section.feather": "Smooth edge",
        "right_panel.background.feather_hint": (
            "Softens the cut-out edge (alpha only)."
        ),
        "right_panel.background.feather_radius": "Radius:  {value} px",
        "right_panel.background.feather_radius.tooltip": (
            "Edge-smoothing radius in pixels (0 = off)"
        ),
        "right_panel.background.feather": "Smooth edge",
        "right_panel.background.feather.tooltip": (
            "Soften the alpha edge of the active layer (selection or global)"
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
        # mm/DPI mode + print-area check (#377)
        "resize.mode.label": "Unit:",
        "resize.mode.pixel": "Pixels",
        "resize.mode.mm": "Millimeters (mm + DPI)",
        "resize.width_mm": "Width",
        "resize.height_mm": "Height",
        "resize.dpi": "Resolution",
        "resize.medium.label": "Target medium:",
        "resize.pixels_result": "Result: {width}×{height} px ({mp} MP)",
        "resize.print_area_ok": "Fits on {medium} ({medium_w}×{medium_h} mm).",
        "resize.print_area_exceeded": (
            "⚠ Motif {width}×{height} mm exceeds {medium} "
            "({medium_w}×{medium_h} mm)."
        ),
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
        "right_panel.shape.section.resize": "Resize",
        "right_panel.shape.resize_apply": "Apply size",
        "right_panel.shape.resize_apply.tooltip": "Scale to the entered size",
        "right_panel.shape.section.format": "Crop format",
        "right_panel.shape.circle": "⬤  Circle",
        "right_panel.shape.circle.tooltip": "Position a circular crop and apply it",
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
        "canvas.feathered": "🪶 Edge smoothed: {radius} px",
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
        "history.desc.feathered": "Edge smoothed ({radius} px)",
        "history.desc.crop_circle": "Format: Circle",
        "history.desc.crop_ratio": "Format: {w}×{h} px",
        # §9 alignment of the right column – AI/export/save (#436–#440)
        # Kurzlabel, damit der Primärbutton einzeilig bleibt (§5.4, #515);
        # der volle Wortlaut steht im Tooltip.
        "right_panel.ai.remove": "Remove background (AI)",
        "right_panel.ai.remove.tooltip": (
            "Remove the background automatically: separate the subject from the"
            " background with AI"),
        "right_panel.export.section.save": "Save",
        "right_panel.export.format_label": "File format",
        "right_panel.export.save": "Save image",
        "right_panel.export.save.tooltip": "Save the color motif as an image",
        "right_panel.export.section.uvprint": "UV printing",
        "right_panel.export.eufymake": "Export assets for EufyMake Studio…",
        "right_panel.export.eufymake.tooltip": (
            "Export color, height, and gloss for EufyMake Studio"),
        "workflow.open.recent": "Recently opened",
        # Guided workflow – step bar, inspector header, navigation (Epic #418)
        "workflow.step.open": "Open",
        "workflow.step.cutout": "Cut out",
        "workflow.step.adjust": "Adjust",
        "workflow.step.shape": "Shape & Size",
        "workflow.step.relief": "Relief & Layers",
        "workflow.step.export": "Export",
        "workflow.title.open": "Step 1 · Open",
        "workflow.title.cutout": "Step 2 · Cut out",
        "workflow.title.adjust": "Step 3 · Adjust",
        "workflow.title.shape": "Step 4 · Shape & Size",
        "workflow.title.relief": "Step 5 · Relief & Layers",
        "workflow.title.export": "Step 6 · Export",
        "workflow.desc.open": "Load an image — via drag & drop, dialog, or recently opened.",
        "workflow.desc.cutout": "Separate the subject from the background — automatically or by hand.",
        "workflow.desc.adjust": "Brightness, contrast, and saturation with live preview.",
        "workflow.desc.shape": "Rotate, flip, round corners, crop, and scale.",
        "workflow.desc.relief": "Manage layers and the height map for relief printing.",
        "workflow.desc.export": "Review the result, save, or export for EufyMake.",
        "workflow.next.open": "Next: Cut out →",
        "workflow.next.cutout": "Next: Adjust →",
        "workflow.next.adjust": "Next: Shape & Size →",
        "workflow.next.shape": "Next: Relief & Layers →",
        "workflow.next.relief": "Next: Export →",
        "workflow.next.export": "Export ✓",
        "workflow.back": "← Back",
        "workflow.open.drop": "Drag an image here",
        "workflow.open.formats": "PNG · JPEG · WebP · TIFF · BMP · GIF",
        "workflow.open.button": "Open file…",
        "workflow.locked": "Open an image first (Step 1)",
        "workflow.status.step": "Step {num}/{total}: {title}",
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
