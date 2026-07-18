"""Leichtgewichtiges Laufzeit-String-Lookup mit stabilem deutschen Fallback.

Die zentrale ``_TRANSLATIONS``-Tabelle bildet String-Keys auf Werte je Locale
ab. Deutsch ist Default und garantierter Fallback für jeden Key, der einer
Locale fehlt; als Laufzeitsprachen sind Deutsch, Englisch, Spanisch,
Französisch, Ukrainisch und vereinfachtes Chinesisch gepflegt (#430), der
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
        "status.ai_warmup_cancelled": "KI-Modell-Download abgebrochen",
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
        "project.error.future_version": (
            "Dieses Projekt wurde mit einer neueren BgRemover-Version erstellt "
            "(Format v{version}; unterstützt: v{supported}). Bitte aktualisieren "
            "Sie die Anwendung. Die Datei wurde nicht verändert."
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
        "project.error.height16_invalid": (
            "Projektdatei beschädigt: 16-Bit-Höhendaten „{file}“ sind ungültig"
        ),
        "project.error.height16_integrity": (
            "Projektdatei beschädigt: Integritätsprüfung für „{file}“ fehlgeschlagen "
            "(Datei abgeschnitten oder vertauscht)"
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
        "canvas.height_imported_16bit": (
            "Höhenkarte importiert: {name} (16 Bit nativ)"
        ),
        "right_panel.height.depth_info": (
            "Höhendaten intern: 16 Bit (0–65535)"
        ),
        "eufymake.export.height_precision_loss": (
            "8-Bit-Export quantisiert die 16-Bit-Höhen kontrolliert auf 256 "
            "Stufen – für volle Präzision Bittiefe 16 wählen"
        ),
        "status.height_source_unsupported": (
            "Höhen-Import: Bildmodus „{mode}“ wird nicht unterstützt"
        ),
        "status.height_import_failed": "Höhen-Import fehlgeschlagen",
        "right_panel.height.scale_hint": (
            "Skala 0–255; wird proportional auf den 16-Bit-Höhenbereich "
            "(0–65535) abgebildet"
        ),
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
        # 3D-Reliefvorschau (Epic #582)
        "menu.view.show_3d": "3D-Relief anzeigen",
        "preview3d.section": "3D-Reliefvorschau",
        "preview3d.display": "Darstellung:",
        "preview3d.display.2d": "2D",
        "preview3d.display.3d": "3D",
        "preview3d.display.3d.disabled_tooltip": (
            "3D benötigt eine Höhenkarte mit gültigen Daten und OpenGL 2.1."
        ),
        "preview3d.exaggeration": "Überhöhung:  {value}×",
        "preview3d.exaggeration.hint": "Verändert nur die Anzeige, nie die Höhendaten.",
        "preview3d.light_azimuth": "Licht-Azimut:  {value}°",
        "preview3d.light_elevation": "Licht-Höhe:  {value}°",
        "preview3d.quality": "Qualität:",
        "preview3d.quality.reduced": "Reduziert",
        "preview3d.quality.standard": "Standard",
        "preview3d.quality.high": "Hoch",
        "preview3d.fit": "Einpassen",
        "preview3d.reset": "Zurücksetzen",
        "preview3d.empty": (
            "Keine Höhenkarte vorhanden. Erzeugen Sie im Höhen-Tab eine Höhenkarte, "
            "um die 3D-Vorschau zu nutzen."
        ),
        "preview3d.unavailable": (
            "3D-Vorschau nicht verfügbar: Diese Umgebung bietet kein OpenGL 2.1. "
            "Die 2D-Reliefvorschau steht weiterhin zur Verfügung."
        ),
        "preview3d.loading": "3D-Vorschau wird berechnet…",
        "preview3d.ready_hint": (
            "3D-Vorschau aktiv – gespeicherte Bilder und Exporte bleiben unverändert."
        ),
        "preview3d.decimated": "Vereinfachte Darstellung 1:{factor}",
        "preview3d.error": (
            "Die 3D-Vorschau ist auf einen Grafikfehler gestoßen. Ihre Bearbeitung, "
            "das Projekt und der Export sind davon nicht betroffen."
        ),
        "preview3d.error.show_2d": "2D-Relief anzeigen",
        "preview3d.error.retry": "Erneut versuchen",
        "preview3d.a11y.name": "3D-Reliefvorschau",
        "preview3d.a11y.desc": (
            "Interaktive 3D-Oberfläche. Ziehen zum Drehen, Mausrad zum Zoomen, "
            "Alt+Ziehen zum Verschieben; Pfeiltasten drehen, Pos1 passt ein."
        ),
        # Design-Umschalter (Epic #424, Issue #428)
        "action.light_mode": "Helles Design",
        "theme.switched.light": "Helles Design aktiviert.",
        "theme.switched.dark": "Dunkles Design aktiviert.",
        "action.settings": "Einstellungen…",
        "action.check_for_updates": "Nach Updates suchen…",
        "action.manage_ai_model": "KI-Modell verwalten…",
        "action.install_ai_backend": "KI-Hintergrundentfernung installieren…",
        # App-Update-Check (#565)
        "status.update_check_running": "Suche nach Updates…",
        "status.update_available_hint": "🆕 Update verfügbar: {version} – klicken für Details",
        "dialog.update_check.title": "Update-Check",
        "dialog.update_check.up_to_date.body": (
            "Sie verwenden bereits die aktuelle Version ({version})."
        ),
        "dialog.update_check.available.body": (
            "Eine neue Version ist verfügbar: {latest} (installiert: {current})."
        ),
        "dialog.update_check.open_release": "Release-Seite öffnen",
        "dialog.update_check.failed.body": (
            "Der Update-Check ist fehlgeschlagen. Bitte später erneut versuchen."
        ),
        # KI-Modell-Verwaltung (#569)
        "ai_model.dialog.title": "KI-Modell verwalten",
        "ai_model.status.downloaded": "Heruntergeladen ({path}, {size})",
        "ai_model.status.not_downloaded": "Nicht heruntergeladen",
        "ai_model.status.rembg_unavailable": (
            "KI-Funktion nicht verfügbar (rembg nicht installiert)"
        ),
        "ai_model.status.python_hint": "Aktive Python-Umgebung: {path}",
        "ai_model.dialog.download": "Jetzt herunterladen",
        "ai_model.dialog.retry": "Erneut versuchen",
        "ai_model.dialog.cancel": "Abbrechen",
        "ai_model.dialog.close": "Schließen",
        "ai_model.dialog.cancelled": "Download abgebrochen",
        # KI-Backend nachrüsten (Menü-Aktion ohne Auto-Install)
        "ai_install.dialog.title": "KI-Hintergrundentfernung installieren",
        "ai_install.dialog.intro": (
            "Diese Installation enthält kein rembg (KI-Backend). Aus der App heraus "
            "wird nichts automatisch installiert – moderne Linux-Systeme blockieren "
            "pip ins System-Python (PEP 668), und ein frisch installiertes Paket "
            "wäre im laufenden Prozess ohnehin erst nach einem Neustart sichtbar. "
            "Im Terminal im Projektordner ausführen:"
        ),
        "ai_install.dialog.venv_note": (
            'Schon eine eigene venv aktiv? Dann reicht: pip install "rembg[cpu]"'
        ),
        "ai_install.dialog.already_installed": (
            "Hinweis: rembg ist in der aktuell laufenden Umgebung bereits installiert."
        ),
        "ai_install.dialog.python_too_old": (
            "⚠ Aktives Python {version} ist zu alt für die KI: rembg/onnxruntime "
            "benötigen Python 3.11+. Vor dem Befehl eine neuere Python-Version "
            "installieren (z. B. via Homebrew/pyenv/apt) und sicherstellen, dass "
            "„python3“ darauf zeigt."
        ),
        "ai_install.dialog.copy": "Befehl kopieren",
        "ai_install.dialog.copied": "In die Zwischenablage kopiert.",
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
        "right_panel.selection.morph.label": "Radius:",
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
        "settings.update.auto_check.label": (
            "Beim Start automatisch nach Updates suchen"
        ),
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
        "right_panel.ai.remove.tooltip.warmup": (
            "KI-Modell wird geladen… – Button wird gleich aktiv"),
        "right_panel.ai.remove.tooltip.no_image": "Zuerst ein Bild öffnen",
        "right_panel.ai.remove.tooltip.processing": "KI verarbeitet bereits ein Bild…",
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
        "status.ai_warmup_cancelled": "AI model download cancelled",
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
        "project.error.future_version": (
            "This project was created with a newer BgRemover version "
            "(format v{version}; supported: v{supported}). Please update the "
            "application. The file was not modified."
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
        "project.error.height16_invalid": (
            "Project file corrupt: 16-bit height data “{file}” is invalid"
        ),
        "project.error.height16_integrity": (
            "Project file corrupt: integrity check failed for “{file}” "
            "(file truncated or swapped)"
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
        "canvas.height_imported_16bit": (
            "Height map imported: {name} (native 16-bit)"
        ),
        "right_panel.height.depth_info": (
            "Internal height data: 16-bit (0–65535)"
        ),
        "eufymake.export.height_precision_loss": (
            "8-bit export quantizes the 16-bit heights to 256 controlled "
            "levels – choose bit depth 16 for full precision"
        ),
        "status.height_source_unsupported": (
            "Height import: image mode “{mode}” is not supported"
        ),
        "status.height_import_failed": "Height import failed",
        "right_panel.height.scale_hint": (
            "0–255 scale; mapped proportionally onto the 16-bit height "
            "range (0–65535)"
        ),
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
        # 3D relief preview (Epic #582)
        "menu.view.show_3d": "Show 3D relief",
        "preview3d.section": "3D relief preview",
        "preview3d.display": "Display:",
        "preview3d.display.2d": "2D",
        "preview3d.display.3d": "3D",
        "preview3d.display.3d.disabled_tooltip": (
            "3D needs a height map with valid data and OpenGL 2.1."
        ),
        "preview3d.exaggeration": "Exaggeration:  {value}×",
        "preview3d.exaggeration.hint": "Changes only the display, never the height data.",
        "preview3d.light_azimuth": "Light azimuth:  {value}°",
        "preview3d.light_elevation": "Light elevation:  {value}°",
        "preview3d.quality": "Quality:",
        "preview3d.quality.reduced": "Reduced",
        "preview3d.quality.standard": "Standard",
        "preview3d.quality.high": "High",
        "preview3d.fit": "Fit to view",
        "preview3d.reset": "Reset",
        "preview3d.empty": (
            "No height map yet. Create a height map in the Height tab to use the "
            "3D preview."
        ),
        "preview3d.unavailable": (
            "3D preview unavailable: this environment does not provide OpenGL 2.1. "
            "The 2D relief preview remains available."
        ),
        "preview3d.loading": "Computing 3D preview…",
        "preview3d.ready_hint": (
            "3D preview active – saved images and exports remain unchanged."
        ),
        "preview3d.decimated": "Simplified view 1:{factor}",
        "preview3d.error": (
            "The 3D preview hit a graphics error. Your edits, project, and export "
            "are not affected."
        ),
        "preview3d.error.show_2d": "Show 2D relief",
        "preview3d.error.retry": "Try again",
        "preview3d.a11y.name": "3D relief preview",
        "preview3d.a11y.desc": (
            "Interactive 3D surface. Drag to orbit, scroll to zoom, Alt+drag to pan; "
            "arrow keys orbit, Home fits the view."
        ),
        # Design toggle (Epic #424, Issue #428)
        "action.light_mode": "Light theme",
        "theme.switched.light": "Light theme enabled.",
        "theme.switched.dark": "Dark theme enabled.",
        "action.settings": "Settings…",
        "action.check_for_updates": "Check for updates…",
        "action.manage_ai_model": "Manage AI model…",
        "action.install_ai_backend": "Install AI background removal…",
        # App-Update-Check (#565)
        "status.update_check_running": "Checking for updates…",
        "status.update_available_hint": "🆕 Update available: {version} – click for details",
        "dialog.update_check.title": "Update Check",
        "dialog.update_check.up_to_date.body": (
            "You are already using the latest version ({version})."
        ),
        "dialog.update_check.available.body": (
            "A new version is available: {latest} (installed: {current})."
        ),
        "dialog.update_check.open_release": "Open release page",
        "dialog.update_check.failed.body": (
            "The update check failed. Please try again later."
        ),
        # KI-Modell-Verwaltung (#569)
        "ai_model.dialog.title": "Manage AI Model",
        "ai_model.status.downloaded": "Downloaded ({path}, {size})",
        "ai_model.status.not_downloaded": "Not downloaded",
        "ai_model.status.rembg_unavailable": (
            "AI feature unavailable (rembg not installed)"
        ),
        "ai_model.status.python_hint": "Active Python environment: {path}",
        "ai_model.dialog.download": "Download now",
        "ai_model.dialog.retry": "Retry",
        "ai_model.dialog.cancel": "Cancel",
        "ai_model.dialog.close": "Close",
        "ai_model.dialog.cancelled": "Download cancelled",
        # KI-Backend nachrüsten (Menü-Aktion ohne Auto-Install)
        "ai_install.dialog.title": "Install AI Background Removal",
        "ai_install.dialog.intro": (
            "This installation does not include rembg (the AI backend). Nothing "
            "is installed automatically from within the app – modern Linux "
            "systems block pip into the system Python (PEP 668), and a freshly "
            "installed package wouldn't be visible in the running process until "
            "a restart anyway. Run this in a terminal inside the project folder:"
        ),
        "ai_install.dialog.venv_note": (
            'Already using your own venv? Just run: pip install "rembg[cpu]"'
        ),
        "ai_install.dialog.already_installed": (
            "Note: rembg is already installed in the currently running environment."
        ),
        "ai_install.dialog.python_too_old": (
            "⚠ Active Python {version} is too old for the AI: rembg/onnxruntime "
            "require Python 3.11+. Install a newer Python first (e.g. via "
            'Homebrew/pyenv/apt) and make sure "python3" points to it before '
            "running the command."
        ),
        "ai_install.dialog.copy": "Copy command",
        "ai_install.dialog.copied": "Copied to clipboard.",
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
        "right_panel.selection.morph.label": "Radius:",
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
        "settings.update.auto_check.label": (
            "Automatically check for updates on startup"
        ),
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
        "right_panel.ai.remove.tooltip.warmup": (
            "Loading AI model… – the button will become active shortly"),
        "right_panel.ai.remove.tooltip.no_image": "Open an image first",
        "right_panel.ai.remove.tooltip.processing": "AI is already processing an image…",
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
    "es": {
        # Status bar messages
        "status.no_image_loaded": "No hay imagen cargada",
        "status.no_image_to_save": "No hay imagen para guardar",
        "status.already_loading": "Ya se está cargando una imagen…",
        "status.load_result_discarded": (
            "Resultado de carga descartado – la imagen cambió mientras tanto"
        ),
        "status.ai_already_running": "La IA ya está en marcha…",
        "status.ai_processing": "La IA está procesando la imagen… (puede tardar unos segundos)",
        "status.ai_ready": "IA lista",
        "status.ai_model_loading": "Cargando el modelo de IA…",
        "status.ai_warmup_failed": "⚠️ No se pudo cargar el modelo de IA",
        "status.ai_warmup_cancelled": "Descarga del modelo de IA cancelada",
        "status.ai_cancelling": "Cancelando – esperando a la IA en curso…",
        "status.ai_cancelled": "Procesamiento de IA cancelado",
        "status.ai_result_discarded": (
            "Resultado de IA descartado – la imagen cambió mientras tanto"
        ),
        "status.wand_busy": "La varita mágica sigue trabajando…",
        "status.selection_calculating": "⏳ Calculando la selección…",
        "status.wand_discarded": (
            "Selección de la varita descartada – la imagen cambió mientras tanto"
        ),
        "status.no_selection": (
            "No hay selección – selecciona primero un área con la varita mágica o el pincel"
        ),
        "status.start_hint": (
            "Abrir una imagen: Archivo → Abrir  o  arrástrala al lienzo"
        ),
        "status.quitting": "Cerrando…",
        "status.shutdown_failed": (
            "No se pudo cerrar – todavía hay un proceso en segundo plano"
        ),
        # Statusleisten-Meldungen mit interpolierten Werten
        "status.loading": "⏳ Cargando: {name}…",
        "status.load_error": "Error de carga: {msg}",
        "status.file_too_large": "Archivo demasiado grande ({size} MB) – máximo: {limit} MB",
        "status.image_too_large": "Imagen demasiado grande – máximo: {limit} MP",
        "status.image_too_large_mp": "Imagen demasiado grande ({mp:.0f} MP) – máximo: {limit} MP",
        "status.file_missing": "El archivo ya no existe: {name}",
        "status.open_not_local": "Solo se pueden abrir archivos locales.",
        "status.ai_error": "Error de IA: {msg}",
        # Projektdatei (.bgrproj) – Lade-/Speicherfehler
        "project.error.corrupt": "El archivo de proyecto está dañado o no es un proyecto válido",
        "project.error.too_large": (
            "Archivo de proyecto demasiado grande ({size} MB) – máximo: {limit} MB"
        ),
        "project.error.manifest_missing": "Archivo de proyecto incompleto: falta manifest.json",
        "project.error.manifest_invalid": "Archivo de proyecto dañado: manifiesto no válido",
        "project.error.unsupported_version": (
            "La versión de formato de proyecto {version} no es compatible"
        ),
        "project.error.future_version": (
            "Este proyecto se creó con una versión más reciente de BgRemover "
            "(formato v{version}; compatible: v{supported}). Actualiza la "
            "aplicación. El archivo no se ha modificado."
        ),
        "project.error.unexpected_entry": (
            "Archivo de proyecto rechazado: entrada inesperada “{name}”"
        ),
        "project.error.entry_too_large": (
            "Archivo de proyecto rechazado: la entrada “{name}” es demasiado grande (descomprimida)"
        ),
        "project.error.layer_file_missing": (
            "Archivo de proyecto incompleto: falta la imagen de capa “{file}”"
        ),
        "project.error.layer_too_large": (
            "Capa demasiado grande ({mp:.0f} MP) – máximo: {limit} MP"
        ),
        "project.error.layer_size_mismatch": (
            "El tamaño de capa {actual} no coincide con el tamaño del lienzo {expected}"
        ),
        "project.error.height16_invalid": (
            "Archivo de proyecto dañado: los datos de altura de 16 bits “{file}” no son válidos"
        ),
        "project.error.height16_integrity": (
            "Archivo de proyecto dañado: la comprobación de integridad de “{file}” falló "
            "(archivo truncado o intercambiado)"
        ),
        "project.warning.role_normalized": (
            "Rol de mapa de altura incompatible eliminado: “{name}” no es una capa de altura"
        ),
        # EufyMake-Export – Konsistenzbefunde (#354)
        "eufymake.export.color_motif_missing": (
            "Falta el motivo de color: no hay rol COLOR_MOTIF ni ninguna capa de "
            "color que contribuya a la composición."
        ),
        "eufymake.export.optional_role_missing": (
            "El rol opcional seleccionado “{role_name}” no tiene capa."
        ),
        "eufymake.export.asset_size_mismatch": (
            "El tamaño del asset {actual} no coincide con el tamaño objetivo {expected}."
        ),
        "eufymake.export.invalid_target_params": "Parámetros de destino no válidos: {detail}",
        "eufymake.export.height_map_empty": (
            "El mapa de altura está vacío o es constante y puede no producir relieve."
        ),
        "eufymake.export.gloss_mask_empty": (
            "La máscara de gloss está vacía o es constante y puede ser inútil."
        ),
        "eufymake.export.bit_depth_unconfirmed": (
            "Un mapa de altura de {bits} bits no está confirmado oficialmente para EufyMake Studio."
        ),
        "eufymake.export.gloss_ink_mode": (
            "El gloss es solo un asset auxiliar de importación – el modo de tinta y "
            "la asignación de capas se hacen en EufyMake Studio."
        ),
        "eufymake.export.physical_size_unverified": (
            "El tamaño físico y la suposición píxel↔mm/DPI son plausibles, pero no "
            "un contrato confirmado del fabricante."
        ),
        # Allgemeine Pre-Export-Prüfung (#379)
        "export.checks.dimensions_invalid": (
            "Dimensiones no válidas: {width}×{height} px – ancho y alto deben ser positivos."
        ),
        "export.checks.dimensions_too_large": (
            "Salida demasiado grande: {mp} MP superan el límite de {limit} MP."
        ),
        "export.checks.color_space_unexpected": (
            "Espacio de color inesperado: {actual} (esperado: {expected})."
        ),
        "export.checks.output_empty": "Salida vacía: el proyecto no contiene capas.",
        "export.checks.resolution_too_low": (
            "Resolución baja: {dpi} DPI (mínimo recomendado: {minimum} DPI)."
        ),
        "export.checks.resolution_too_high": (
            "Resolución muy alta: {dpi} DPI (máximo recomendado: {maximum} DPI)."
        ),
        "export.checks.fully_transparent": (
            "Completamente transparente: la salida no tiene píxeles visibles."
        ),
        "export.checks.unexpected_alpha": (
            "Transparencia parcial: el {percent}% de los píxeles son semitransparentes."
        ),
        "export.checks.print_area_exceeded": (
            "El motivo supera el área de impresión: "
            "{width}×{height} mm > {medium_w}×{medium_h} mm."
        ),
        # Pre-Export-Prüfung beim normalen Speichern (#380)
        "export.check.error.title": "No se puede guardar",
        "export.check.blocked": (
            "El guardado se canceló por los siguientes problemas:\n\n{details}"
        ),
        "export.check.warning.title": "Advertencias antes de guardar",
        "export.check.confirm": (
            "Hay advertencias:\n\n{details}\n\n¿Guardar de todos modos?"
        ),
        # EufyMake-Export – Menü, Dialog & Meldungen (#355)
        "action.export_eufymake": "Exportar assets para EufyMake Studio…",
        "eufymake.dialog.title": "Exportar assets para EufyMake Studio",
        "eufymake.dialog.intro": (
            "BgRemover escribe assets de importación para EufyMake Studio – no un "
            "proyecto “.empf” terminado. Impórtalos y colócalos después en Studio, "
            "asigna allí los modos de tinta/capas y guarda el proyecto tú mismo "
            "como “.empf”."
        ),
        "eufymake.dialog.section.assets": "Assets",
        "eufymake.dialog.color_motif": "Motivo de color (obligatorio)",
        "eufymake.dialog.color_motif.hint": (
            "PNG RGBA de la composición de color; la transparencia se conserva."
        ),
        "eufymake.dialog.height": "Incluir mapa de altura",
        "eufymake.dialog.height.hint": "PNG en escala de grises: claro = alto, oscuro = bajo.",
        "eufymake.dialog.height.unavailable": "No hay capa de altura en el proyecto.",
        "eufymake.dialog.gloss": "Incluir máscara de gloss (experimental)",
        "eufymake.dialog.gloss.hint": (
            "Asset auxiliar opcional. El modo de tinta y la asignación de capas se "
            "hacen en EufyMake Studio."
        ),
        "eufymake.dialog.gloss.unavailable": "No hay capa de gloss en el proyecto.",
        "eufymake.dialog.section.target": "Parámetros de destino",
        "eufymake.dialog.bit_depth": "Profundidad de bits del mapa de altura:",
        "eufymake.dialog.bit_depth.8": "8 bits (estándar)",
        "eufymake.dialog.bit_depth.16": "16 bits (experimental, sin confirmar)",
        "eufymake.dialog.size": "Tamaño objetivo: {w} × {h} px",
        "eufymake.dialog.physical": "Tamaño físico: {w} × {h} mm ({dpi} dpi)",
        "eufymake.dialog.physical.unset": "Tamaño físico: sin definir",
        "eufymake.dialog.section.dest": "Destino",
        "eufymake.dialog.dest.label": "Carpeta de exportación:",
        "eufymake.dialog.dest.placeholder": "Aún no se ha elegido carpeta",
        "eufymake.dialog.dest.is_file": (
            "El destino es un archivo existente – elige una carpeta."
        ),
        "eufymake.dialog.dest.browse": "Examinar…",
        "eufymake.dialog.dest.dialog_title": "Elegir carpeta de exportación",
        "eufymake.dialog.section.findings": "Comprobación",
        "eufymake.dialog.findings.ok": "Sin observaciones.",
        "eufymake.dialog.finding.error": "⛔  {msg}",
        "eufymake.dialog.finding.warning": "⚠️  {msg}",
        "eufymake.dialog.confirm_warnings": "Entiendo las advertencias – exportar igualmente",
        "eufymake.dialog.cancel": "Cancelar",
        "eufymake.dialog.export": "Exportar",
        "eufymake.status.no_project": "No hay proyecto para exportar",
        "eufymake.status.cancelled": "Exportación cancelada",
        "eufymake.status.exported": "✅ Assets exportados para EufyMake Studio: {path}",
        "eufymake.error.title": "Exportación fallida",
        "eufymake.error.write": "Exportación fallida: {error}",
        "eufymake.error.not_directory": (
            "El destino “{path}” es un archivo existente. Elige una carpeta como "
            "destino de exportación."
        ),
        "eufymake.error.blocked": "Exportación bloqueada – corrige esto primero:\n{details}",
        "eufymake.overwrite.title": "¿Sobrescribir carpeta?",
        "eufymake.overwrite.body": "“{path}” ya existe. ¿Reemplazar su contenido?",
        "eufymake.success.title": "Exportación completada",
        "eufymake.success.body": (
            "Assets de importación escritos en:\n{path}\n\n"
            "Próximos pasos en EufyMake Studio:\n"
            "1. Importar y colocar los assets.\n"
            "2. Asignar modos de tinta/capas (p. ej. gloss/barniz).\n"
            "3. Guardar el proyecto en Studio como “.empf”."
        ),
        # Ebenen-Panel & Projekt-Aktionen (#334)
        "layers.new_name": "Capa {n}",
        "layers.role.none": "Ninguno",
        "layers.role.color_motif": "Motivo de color",
        "layers.role.height_map": "Mapa de altura",
        "layers.role.gloss": "Gloss",
        "layers.height_name": "Mapa de altura",
        "history.desc.layer_added": "Capa añadida",
        "history.desc.layer_removed": "Capa eliminada",
        "history.desc.layer_duplicated": "Capa duplicada",
        "history.desc.layer_reordered": "Capa movida",
        "history.desc.layer_renamed": "Capa renombrada",
        "history.desc.layer_active": "Capa activa cambiada",
        "history.desc.layer_visibility": "Visibilidad cambiada",
        "history.desc.layer_opacity": "Opacidad cambiada",
        "history.desc.layer_role": "Rol cambiado",
        "history.desc.height_generated": "Mapa de altura generado",
        "history.desc.height_imported": "Mapa de altura importado",
        "history.desc.height_lighten": "Altura aclarada",
        "history.desc.height_darken": "Altura oscurecida",
        "history.desc.height_set": "Altura establecida",
        "history.desc.height_invert": "Altura invertida",
        "history.desc.height_optimized": "Altura optimizada",
        "canvas.layer_added": "Nueva capa añadida",
        "canvas.height_generated": "Mapa de altura generado a partir de la imagen",
        "canvas.height_imported": "Mapa de altura importado: {name}",
        "canvas.height_imported_16bit": (
            "Mapa de altura importado: {name} (16 bits nativo)"
        ),
        "right_panel.height.depth_info": (
            "Datos de altura internos: 16 bits (0–65535)"
        ),
        "eufymake.export.height_precision_loss": (
            "La exportación de 8 bits cuantiza las alturas de 16 bits a 256 "
            "niveles controlados; elige 16 bits para precisión completa"
        ),
        "status.height_source_unsupported": (
            "Importación de alturas: el modo de imagen “{mode}” no es compatible"
        ),
        "status.height_import_failed": "La importación de alturas falló",
        "right_panel.height.scale_hint": (
            "Escala 0–255; se proyecta proporcionalmente sobre el rango de "
            "alturas de 16 bits (0–65535)"
        ),
        "canvas.height_lightened": "Altura aclarada",
        "canvas.height_darkened": "Altura oscurecida",
        "canvas.height_set": "Altura establecida",
        "canvas.height_inverted": "Altura invertida",
        "canvas.height_optimized": "Altura optimizada",
        "canvas.height_op_error": "La operación de altura falló: {error}",
        "canvas.not_height_layer": "No hay capa de altura activa",
        "canvas.role_incompatible": (
            "El rol “Mapa de altura” solo está disponible para capas de altura"
        ),
        "canvas.layer_removed": "Capa eliminada",
        "canvas.layer_duplicated": "Capa duplicada",
        "canvas.cannot_delete_last": "La última capa no se puede eliminar",
        "right_panel.tab.layers": "Capas",
        "right_panel.tab.layers.tooltip": "Gestionar capas",
        "right_panel.tab.height": "Altura",
        "right_panel.tab.height.tooltip": "Mapa de altura (relieve)",
        "right_panel.tab.preview": "Vista previa",
        "right_panel.tab.preview.tooltip": "Vista 2D de color, relieve y gloss",
        "right_panel.preview.section": "Modo de vista previa 2D",
        "right_panel.preview.hint": (
            "La vista previa es independiente de la capa activa."
        ),
        "right_panel.preview.mode": "Mostrar:",
        "right_panel.preview.relief_strength": "Intensidad del relieve:  {value} %",
        "right_panel.preview.relief_strength.tooltip": (
            "Intensidad del sombreado en los modos Relieve y Combinado"
        ),
        "right_panel.preview.gloss_visible": "Mostrar gloss",
        "right_panel.preview.gloss_visible.tooltip": (
            "Mostrar u ocultar el brillo de gloss en los modos Gloss y Combinado"
        ),
        "right_panel.preview.export_hint": (
            "Solo visualización – “Guardar imagen” sigue exportando únicamente "
            "el motivo de color."
        ),
        "right_panel.height.section.acquire": "Obtener",
        "right_panel.height.section.edit": "Editar",
        "right_panel.height.section.optimize": "Optimizar",
        "right_panel.height.generate": "Generar desde la imagen",
        "right_panel.height.generate.tooltip": (
            "Generar un mapa de altura a partir de la imagen actual"
        ),
        "right_panel.height.import": "Importar escala de grises…",
        "right_panel.height.import.tooltip": (
            "Importar una imagen en escala de grises como mapa de altura"
        ),
        "right_panel.height.hint": (
            "Las herramientas de altura actúan sobre la capa de altura activa."
        ),
        "right_panel.height.strength": "Intensidad",
        "right_panel.height.lighten": "Aclarar",
        "right_panel.height.lighten.tooltip": (
            "Elevar la altura en la selección (si no, global)"
        ),
        "right_panel.height.darken": "Oscurecer",
        "right_panel.height.darken.tooltip": (
            "Reducir la altura en la selección (si no, global)"
        ),
        "right_panel.height.set_value": "Valor",
        "right_panel.height.set": "Establecer altura",
        "right_panel.height.set.tooltip": (
            "Establecer la altura al valor (selección o global)"
        ),
        "right_panel.height.invert": "Invertir",
        "right_panel.height.invert.tooltip": (
            "Invertir la altura (selección o global)"
        ),
        "right_panel.height.levels": "Niveles (negro/blanco)",
        "right_panel.height.gamma": "Gamma",
        "right_panel.height.gaussian": "Desenfoque gaussiano (radio)",
        "right_panel.height.median": "Desenfoque de mediana (radio)",
        "right_panel.height.threshold": "Umbral",
        "right_panel.height.steps": "Escalones",
        "right_panel.height.range": "Rango (mín/máx)",
        "right_panel.height.apply": "Aplicar",
        "right_panel.height.apply.tooltip": "Aplicar la vista previa a la capa de altura",
        "right_panel.height.discard_preview": "Descartar vista previa",
        "right_panel.height.discard_preview.tooltip": (
            "Descartar la vista previa sin aplicarla"
        ),
        "right_panel.layers.section": "Capas",
        "right_panel.layers.add.tooltip": "Nueva capa",
        "right_panel.layers.duplicate.tooltip": "Duplicar la capa activa",
        "right_panel.layers.delete.tooltip": "Eliminar la capa activa",
        "right_panel.layers.move_up.tooltip": "Subir capa",
        "right_panel.layers.move_down.tooltip": "Bajar capa",
        "right_panel.layers.rename.tooltip": "Renombrar la capa activa",
        "right_panel.layers.role_label": "Rol:",
        "right_panel.layers.role.tooltip": (
            "Rol de la capa activa (para futuras herramientas de impresión UV)"
        ),
        "right_panel.layers.visible.tooltip": "Alternar visibilidad",
        "right_panel.layers.select.tooltip": "Elegir como capa activa",
        "right_panel.layers.opacity.tooltip": "Opacidad (se aplica al soltar)",
        "right_panel.layers.empty": (
            "No hay proyecto cargado – abre una imagen o “Nuevo proyecto”."
        ),
        "menu.project": "Proyecto",
        "action.new_project": "Nuevo proyecto",
        "action.open_project": "Abrir proyecto…",
        "action.save_project": "Guardar proyecto",
        "action.save_project_as": "Guardar proyecto como…",
        "dialog.open_project.title": "Abrir proyecto",
        "dialog.open_project.filter": "Proyecto de BgRemover (*.bgrproj)",
        "dialog.save_project.title": "Guardar proyecto",
        "dialog.rename.title": "Renombrar capa",
        "dialog.rename.label": "Nuevo nombre:",
        "dialog.import_height.title": "Importar mapa de altura",
        "dialog.project_error.title": "Error de proyecto",
        "project.new": "Nuevo proyecto creado",
        "project.saved": "Proyecto guardado: {name}",
        "project.opened": "Proyecto abierto: {name}",
        "project.no_project": "No hay proyecto para guardar",
        "project.save_failed": "Error al guardar el proyecto: {error}",
        # Main menu
        "menu.file": "Archivo",
        "menu.recent_files": "Abiertos recientemente",
        "menu.edit": "Edición",
        "menu.view": "Ver",
        "menu.preview_mode": "Modo de vista previa",
        "menu.extras": "Herramientas",
        "action.open": "Abrir…",
        "action.save": "Guardar",
        "action.save_as": "Guardar como…",
        "action.undo": "Deshacer",
        "action.redo": "Rehacer",
        "action.rotate_left_90": "Girar 90° a la izquierda",
        "action.rotate_right_90": "Girar 90° a la derecha",
        "action.rotate_180": "Girar 180°",
        "action.flip_horizontal": "Voltear horizontalmente",
        "action.flip_vertical": "Voltear verticalmente",
        "action.resize": "Cambiar tamaño…",
        "action.clear_selection": "Anular selección",
        "action.invert_selection": "Invertir selección",
        "action.restore_original": "Restaurar original",
        "action.fit_to_view": "Ajustar a la vista",
        # Verlauf-Popup: Menü-Anker seit #458 (Rail-Button entfallen)
        "action.history": "Historial",
        # Zoom-Kontrolle auf der Arbeitsfläche (#464)
        "zoom.in.tooltip": "Acercar (+10 %)",
        "zoom.out.tooltip": "Alejar (−10 %)",
        "zoom.lock.tooltip": "Fijar zoom (mantener el valor actual)",
        "zoom.unlock.tooltip": "Liberar el zoom",
        "preview.mode.color": "Color",
        "preview.mode.relief": "Relieve sobre color",
        "preview.mode.height": "Altura (escala de grises)",
        "preview.mode.gloss": "Gloss",
        "preview.mode.combined": "Combinado",
        # Kurzlabels für das Segmented-Control der 2D-Vorschau (§9 Schritt 6)
        "preview.seg.color": "Color",
        "preview.seg.relief": "Relieve",
        "preview.seg.height": "Altura",
        "preview.seg.gloss": "Gloss",
        # Vista previa de relieve 3D (Epic #582)
        "menu.view.show_3d": "Mostrar relieve 3D",
        "preview3d.section": "Vista previa de relieve 3D",
        "preview3d.display": "Visualización:",
        "preview3d.display.2d": "2D",
        "preview3d.display.3d": "3D",
        "preview3d.display.3d.disabled_tooltip": (
            "3D necesita un mapa de altura con datos válidos y OpenGL 2.1."
        ),
        "preview3d.exaggeration": "Exageración:  {value}×",
        "preview3d.exaggeration.hint": "Solo cambia la visualización, nunca los datos de altura.",
        "preview3d.light_azimuth": "Azimut de luz:  {value}°",
        "preview3d.light_elevation": "Elevación de luz:  {value}°",
        "preview3d.quality": "Calidad:",
        "preview3d.quality.reduced": "Reducida",
        "preview3d.quality.standard": "Estándar",
        "preview3d.quality.high": "Alta",
        "preview3d.fit": "Ajustar a vista",
        "preview3d.reset": "Restablecer",
        "preview3d.empty": (
            "Aún no hay mapa de altura. Crea un mapa de altura en la pestaña Altura "
            "para usar la vista previa 3D."
        ),
        "preview3d.unavailable": (
            "Vista previa 3D no disponible: este entorno no ofrece OpenGL 2.1. "
            "La vista previa de relieve 2D sigue disponible."
        ),
        "preview3d.loading": "Calculando vista previa 3D…",
        "preview3d.ready_hint": (
            "Vista previa 3D activa: las imágenes guardadas y las exportaciones no cambian."
        ),
        "preview3d.decimated": "Vista simplificada 1:{factor}",
        "preview3d.error": (
            "La vista previa 3D encontró un error gráfico. Tu edición, el proyecto y "
            "la exportación no se ven afectados."
        ),
        "preview3d.error.show_2d": "Mostrar relieve 2D",
        "preview3d.error.retry": "Reintentar",
        "preview3d.a11y.name": "Vista previa de relieve 3D",
        "preview3d.a11y.desc": (
            "Superficie 3D interactiva. Arrastra para orbitar, rueda para acercar, "
            "Alt+arrastrar para desplazar; las flechas orbitan, Inicio ajusta la vista."
        ),
        # Design-Umschalter (Epic #424, Issue #428)
        "action.light_mode": "Tema claro",
        "theme.switched.light": "Tema claro activado.",
        "theme.switched.dark": "Tema oscuro activado.",
        "action.settings": "Ajustes…",
        "action.check_for_updates": "Buscar actualizaciones…",
        "action.manage_ai_model": "Gestionar modelo de IA…",
        "action.install_ai_backend": "Instalar eliminación de fondo por IA…",
        # App-Update-Check (#565)
        "status.update_check_running": "Buscando actualizaciones…",
        "status.update_available_hint": (
            "🆕 Actualización disponible: {version} – haz clic para más información"
        ),
        "dialog.update_check.title": "Comprobación de actualizaciones",
        "dialog.update_check.up_to_date.body": (
            "Ya tienes la versión más reciente ({version})."
        ),
        "dialog.update_check.available.body": (
            "Hay una nueva versión disponible: {latest} (instalada: {current})."
        ),
        "dialog.update_check.open_release": "Abrir página de la versión",
        "dialog.update_check.failed.body": (
            "La comprobación de actualizaciones falló. Inténtalo de nuevo más tarde."
        ),
        # KI-Modell-Verwaltung (#569)
        "ai_model.dialog.title": "Gestionar modelo de IA",
        "ai_model.status.downloaded": "Descargado ({path}, {size})",
        "ai_model.status.not_downloaded": "No descargado",
        "ai_model.status.rembg_unavailable": (
            "Función de IA no disponible (rembg no instalado)"
        ),
        "ai_model.status.python_hint": "Entorno de Python activo: {path}",
        "ai_model.dialog.download": "Descargar ahora",
        "ai_model.dialog.retry": "Reintentar",
        "ai_model.dialog.cancel": "Cancelar",
        "ai_model.dialog.close": "Cerrar",
        "ai_model.dialog.cancelled": "Descarga cancelada",
        # KI-Backend nachrüsten (Menü-Aktion ohne Auto-Install)
        "ai_install.dialog.title": "Instalar eliminación de fondo por IA",
        "ai_install.dialog.intro": (
            "Esta instalación no incluye rembg (el backend de IA). La app no "
            "instala nada automáticamente: los sistemas Linux modernos bloquean "
            "pip en el Python del sistema (PEP 668), y un paquete recién "
            "instalado no sería visible en el proceso en ejecución hasta "
            "reiniciar. Ejecuta esto en una terminal dentro de la carpeta del "
            "proyecto:"
        ),
        "ai_install.dialog.venv_note": (
            '¿Ya usas tu propio venv? Basta con: pip install "rembg[cpu]"'
        ),
        "ai_install.dialog.already_installed": (
            "Nota: rembg ya está instalado en el entorno en ejecución actual."
        ),
        "ai_install.dialog.python_too_old": (
            "⚠ El Python activo {version} es demasiado antiguo para la IA: "
            "rembg/onnxruntime requieren Python 3.11+. Instala primero una "
            'versión de Python más reciente (p. ej. con Homebrew/pyenv/apt) y '
            'asegúrate de que "python3" apunte a ella antes de ejecutar el '
            "comando."
        ),
        "ai_install.dialog.copy": "Copiar comando",
        "ai_install.dialog.copied": "Copiado al portapapeles.",
        # Left toolbar
        "toolbar.move.tooltip": (
            "Mover / Zoom\n"
            "Arrastrar con clic izquierdo desplaza la vista · la rueda del ratón hace zoom"
        ),
        "toolbar.wand.tooltip": (
            "Varita mágica  (W)\n"
            "Un clic selecciona un área de color (relleno por difusión)\n"
            "Shift = añadir  ·  {modifier} = restar"
        ),
        "toolbar.brush.tooltip": "Pincel  (B)\nAñadir áreas a la selección manualmente",
        "toolbar.eraser.tooltip": "Borrador  (E)\nQuitar áreas de la selección",
        "toolbar.lasso.tooltip": (
            "Lazo poligonal  (L)\n"
            "Clic coloca puntos · doble clic cierra el polígono\n"
            "Shift = añadir  ·  {modifier} = restar  ·  Esc = cancelar"
        ),
        "toolbar.height_lighten.tooltip": (
            "Aclarar (elevar)\n"
            "La pincelada eleva la altura de la capa de altura activa"
        ),
        "toolbar.height_darken.tooltip": (
            "Oscurecer (bajar)\n"
            "La pincelada reduce la altura de la capa de altura activa"
        ),
        "toolbar.height_tools.disabled.tooltip": (
            "Herramienta de altura\n"
            "Activa primero una capa de altura (paso 5: generar/importar un mapa de altura)"
        ),
        "toolbar.ai.missing.tooltip": (
            'rembg no está instalado\n→ python3 -m pip install -e ".[ai]"'
        ),
        "toolbar.undo.tooltip": (
            "Deshacer  ({shortcut})\n"
            "Deshacer el último paso de edición"
        ),
        "toolbar.redo.tooltip": (
            "Rehacer  ({shortcut})\n"
            "Rehacer el último paso deshecho"
        ),
        "toolbar.theme.to_light.tooltip": "Cambiar al tema claro",
        "toolbar.theme.to_dark.tooltip": "Cambiar al tema oscuro",
        # Right panel tabs
        "right_panel.tab.selection": "Selección",
        "right_panel.tab.selection.tooltip": (
            "Selección – varita mágica, pincel, borrador"
        ),
        "right_panel.tab.background": "Fondo",
        "right_panel.tab.background.tooltip": (
            "Fondo – eliminar, reemplazar color"
        ),
        "right_panel.tab.adjust": "Ajustar",
        "right_panel.tab.adjust.tooltip": (
            "Corrección de color – brillo, contraste, saturación"
        ),
        "right_panel.tab.transform": "Girar/Voltear",
        "right_panel.tab.transform.tooltip": "Transformar – girar, voltear",
        "right_panel.tab.shape": "Forma",
        "right_panel.tab.shape.tooltip": (
            "Forma y recorte – redondear esquinas, elegir formato"
        ),
        # History popup
        "history.window_title": "Historial de cambios",
        "history.hint": "Doble clic en una entrada → volver a ese paso",
        "history.list.tooltip": (
            "Historial de todos los pasos de edición.\n"
            "Doble clic en una entrada vuelve a ese paso."
        ),
        # Crop bar
        "crop_bar.label": "✂  Posiciona el recorte y confirma:",
        "crop_bar.confirm": "✓  Aplicar recorte",
        "crop_bar.cancel": "✗  Cancelar",
        # Right panel — Selection tab contents
        "right_panel.selection.section.settings": "Ajustes de herramienta",
        "right_panel.selection.section.select": "Selección",
        "right_panel.selection.tolerance": "Tolerancia (varita mágica):  {value}",
        "right_panel.selection.tolerance.tooltip": (
            "Controla cuán similares deben ser los colores para seleccionarse.\n"
            "Bajo = solo colores muy similares · Alto = muchos tonos"
        ),
        "right_panel.selection.brush_size": "Tamaño del pincel:  {value} px",
        "right_panel.selection.brush_size.tooltip": (
            "Tamaño de la herramienta pincel/borrador en píxeles"
        ),
        "right_panel.selection.clear": "Anular",
        "right_panel.selection.clear.tooltip": (
            "Anula la selección actual (también: tecla Esc)"
        ),
        "right_panel.selection.invert": "Invertir",
        "right_panel.selection.invert.tooltip": (
            "Intercambia áreas seleccionadas y no seleccionadas  ({modifier}+Shift+I)"
        ),
        "right_panel.selection.morph.label": "Radio:",
        "right_panel.selection.morph.tooltip": (
            "Radio en píxeles para ampliar/encoger la selección"
        ),
        "right_panel.selection.expand": "+ Ampliar",
        "right_panel.selection.expand.tooltip": (
            "Amplía la selección según el radio establecido"
        ),
        "right_panel.selection.shrink": "− Encoger",
        "right_panel.selection.shrink.tooltip": (
            "Encoge la selección según el radio establecido"
        ),
        # Right panel — Background tab contents
        "right_panel.background.section": "Editar fondo",
        "right_panel.background.remove": "Eliminar (transparente)",
        "right_panel.background.remove.tooltip": (
            "Hace completamente transparente el área seleccionada.\n"
            "Consejo: selecciona primero el fondo con la varita mágica."
        ),
        "right_panel.background.color_label": "Elegir color y rellenar la selección:",
        "right_panel.background.color.tooltip": "Clic para elegir el color de fondo de reemplazo",
        "right_panel.background.replace": "Reemplazar color",
        "right_panel.background.replace.tooltip": (
            "Rellena el área seleccionada con el color elegido"
        ),
        "right_panel.background.section.feather": "Suavizar borde",
        "right_panel.background.feather_hint": (
            "Difumina el borde del recorte (solo alfa)."
        ),
        "right_panel.background.feather_radius": "Radio:  {value} px",
        "right_panel.background.feather_radius.tooltip": (
            "Radio del suavizado de borde en píxeles (0 = desactivado)"
        ),
        "right_panel.background.feather": "Suavizar borde",
        "right_panel.background.feather.tooltip": (
            "Difuminar el borde alfa de la capa activa (selección o global)"
        ),
        # Right panel — Transform tab contents
        "right_panel.transform.section.rotate": "Girar",
        "right_panel.transform.quick_label": "Giro rápido:",
        "right_panel.transform.rotate_left_90": "↺ 90° izquierda",
        "right_panel.transform.rotate_left_90.tooltip": "Girar 90° en sentido antihorario",
        "right_panel.transform.rotate_right_90": "↻ 90° derecha",
        "right_panel.transform.rotate_right_90.tooltip": "Girar 90° en sentido horario",
        "right_panel.transform.rotate_180": "↺ 180°",
        "right_panel.transform.rotate_180.tooltip": "Girar la imagen 180°",
        "right_panel.transform.rotate_270": "↺ 270°",
        "right_panel.transform.rotate_270.tooltip": "270° antihorario (= 90° a la derecha)",
        "right_panel.transform.free_label": "Ángulo libre:",
        "right_panel.transform.angle_slider.tooltip": "Ajustar el ángulo de giro: −180° a +180°",
        "right_panel.transform.angle_spin.tooltip": "Introducir el ángulo de giro directamente",
        "right_panel.transform.apply_angle": "Aplicar ángulo",
        "right_panel.transform.apply_angle.tooltip": (
            "Gira la imagen según el ángulo establecido.\n"
            "Los ángulos oblicuos crean esquinas transparentes."
        ),
        "right_panel.transform.section.flip": "Voltear",
        "right_panel.transform.flip_h": "Horizontal",
        "right_panel.transform.flip_h.tooltip": "Voltear la imagen horizontalmente (izquierda ↔ derecha)",
        "right_panel.transform.flip_v": "Vertical",
        "right_panel.transform.flip_v.tooltip": "Voltear la imagen verticalmente (arriba ↕ abajo)",
        # Größe-ändern-Dialog (#359)
        "resize.title": "Cambiar tamaño",
        "resize.width": "Ancho",
        "resize.height": "Alto",
        "resize.link_aspect": "Mantener proporciones",
        "resize.resample.label": "Método:",
        "resize.resample.lanczos": "Lanczos (mejor calidad)",
        "resize.resample.bicubic": "Bicúbico",
        "resize.resample.bilinear": "Bilineal",
        "resize.resample.nearest": "Vecino más próximo",
        "resize.megapixels": "{mp:.1f} MP (máximo: {maximum} MP)",
        "resize.ok": "Aplicar",
        "resize.cancel": "Cancelar",
        # mm/DPI-Modus + Druckflächenprüfung (#377)
        "resize.mode.label": "Unidad:",
        "resize.mode.pixel": "Píxeles",
        "resize.mode.mm": "Milímetros (mm + DPI)",
        "resize.width_mm": "Ancho",
        "resize.height_mm": "Alto",
        "resize.dpi": "Resolución",
        "resize.medium.label": "Medio de destino:",
        "resize.pixels_result": "Resultado: {width}×{height} px ({mp} MP)",
        "resize.print_area_ok": "Cabe en {medium} ({medium_w}×{medium_h} mm).",
        "resize.print_area_exceeded": (
            "⚠ El motivo {width}×{height} mm supera {medium} "
            "({medium_w}×{medium_h} mm)."
        ),
        # Right panel — Adjust tab contents (#360)
        "right_panel.adjust.section": "Corrección de color",
        "right_panel.adjust.hint": "Actúa sobre la capa de color activa.",
        "right_panel.adjust.brightness": "Brillo:  {value} %",
        "right_panel.adjust.brightness.tooltip": (
            "Brillo de la capa de color activa (100 % = sin cambios)"
        ),
        "right_panel.adjust.contrast": "Contraste:  {value} %",
        "right_panel.adjust.contrast.tooltip": (
            "Contraste de la capa de color activa (100 % = sin cambios)"
        ),
        "right_panel.adjust.saturation": "Saturación:  {value} %",
        "right_panel.adjust.saturation.tooltip": (
            "Saturación de la capa de color activa (0 % = escala de grises, 100 % = sin cambios)"
        ),
        "right_panel.adjust.reset": "Restablecer",
        "right_panel.adjust.reset.tooltip": (
            "Restablecer los controles al 100 % y descartar la vista previa"
        ),
        "right_panel.adjust.apply": "Aplicar",
        "right_panel.adjust.apply.tooltip": (
            "Aplicar la corrección de color a la capa de color activa"
        ),
        # Right panel — Shape tab contents
        "right_panel.shape.section.corner": "Redondear esquinas",
        "right_panel.shape.radius": "Radio:  {value} px",
        "right_panel.shape.radius.tooltip": (
            "Radio del redondeo de esquinas en píxeles.\n"
            "0 = sin redondeo · 500 = redondeo máximo"
        ),
        "right_panel.shape.round": "Redondear esquinas",
        "right_panel.shape.round.tooltip": (
            "Aplica el redondeo de esquinas.\n"
            "El resultado se guarda como PNG con esquinas transparentes."
        ),
        "right_panel.shape.section.resize": "Cambiar tamaño",
        "right_panel.shape.resize_apply": "Aplicar tamaño",
        "right_panel.shape.resize_apply.tooltip": "Escalar al tamaño introducido",
        "right_panel.shape.section.format": "Formato de recorte",
        "right_panel.shape.circle": "⬤  Círculo",
        "right_panel.shape.circle.tooltip": "Posicionar un recorte circular y aplicarlo",
        # Settings dialog
        "settings.title": "Ajustes",
        "settings.open_dir.label": "Directorio predeterminado para abrir",
        "settings.save_dir.label": "Directorio predeterminado para exportar / guardar",
        "settings.dir.placeholder": "Vacío = último directorio usado",
        "settings.format.label": "Formato de imagen preferido",
        "settings.log.label": "Archivo de registro",
        "settings.log.tooltip": "Ruta del archivo de registro (selecciónala para copiar)",
        "settings.log.open_button": "Abrir carpeta",
        "settings.log.open_failed": "No se pudo abrir la carpeta:\n{target}",
        "settings.update.auto_check.label": (
            "Buscar actualizaciones automáticamente al iniciar"
        ),
        "settings.cancel": "Cancelar",
        "settings.ok": "OK",
        "settings.pick_open.title": "Elegir directorio para abrir",
        "settings.pick_save.title": "Elegir directorio para exportar/guardar",
        "settings.invalid_dir.title": "Directorio no válido",
        "settings.invalid_dir.body": "{label} no es un directorio existente:\n{value}",
        "settings.language.label": "Idioma",
        "settings.language.restart_title": "Reinicio necesario",
        "settings.language.restart_hint": (
            "El cambio de idioma se aplicará en el próximo inicio."
        ),
        # Dialogs (QMessageBox)
        "dialog.ai_error.title": "Error de IA",
        "dialog.ai_error.body": (
            "Error durante la eliminación automática del fondo:\n\n{msg}"
        ),
        # Main-window dialogs
        "dialog.unsaved.title": "Cambios sin guardar",
        "dialog.unsaved.body": (
            "La imagen ha sido editada. ¿Guardar los cambios antes de descartarla?"
        ),
        "dialog.open.title": "Abrir imagen",
        "dialog.open.filter": (
            "Imágenes (*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.tif *.gif);;"
            "Todos los archivos (*)"
        ),
        "dialog.save.title": "Guardar imagen como…",
        "dialog.color.title": "Elegir color de fondo",
        # Canvas status messages
        "canvas.opened": "Abierto: {name}  ({w} × {h} px)",
        "canvas.opened_extra": (
            "Abierto: {name}  ({extra} archivo(s) adicional(es) ignorado(s))"
        ),
        "canvas.undo_none": "No queda nada por deshacer",
        "canvas.undo_done": "↩  Deshecho: {desc}",
        "canvas.redo_none": "No queda nada por rehacer",
        "canvas.redo_done": "↪  Rehecho: {desc}",
        "canvas.undo_to": "↩  {steps} paso(s) deshecho(s)  (hasta: {desc})",
        "canvas.original_restored": "🔄  Original restaurado",
        "canvas.selection_cleared": "Selección anulada",
        "canvas.selection_inverted": "Selección invertida: {pixels:,} píxeles",
        "canvas.selection_expanded": "Selección ampliada en {radius} px: {pixels:,} píxeles",
        "canvas.selection_shrunk": "Selección encogida en {radius} px: {pixels:,} píxeles",
        "canvas.bg_removed": "Fondo eliminado (transparente)",
        "canvas.remove_error": "Error al eliminar: {error}",
        "canvas.bg_replaced": "Fondo reemplazado: {color}",
        "canvas.replace_error": "Error al reemplazar: {error}",
        "canvas.ai_done": "✅ Eliminación de fondo por IA completada",
        "canvas.selection_pixels": "Selección: {pixels:,} píxeles",
        "canvas.selection_error": "Error de selección: {msg}",
        "canvas.lasso_cancelled": "Lazo poligonal cancelado",
        "canvas.lasso_selected": "Lazo poligonal: {pixels:,} píxeles seleccionados",
        "canvas.lasso_points_one": (
            "Lazo poligonal: {n} punto — doble clic para terminar · Esc = cancelar"
        ),
        "canvas.lasso_points_many": (
            "Lazo poligonal: {n} puntos — doble clic para terminar · Esc = cancelar"
        ),
        "canvas.format_unsupported": "Formato no compatible",
        "canvas.radius_positive": "El radio debe ser > 0",
        "canvas.corners_rounded": "Esquinas redondeadas: radio de {r} px",
        "canvas.rotate_too_large": (
            "Girar {degrees}° haría la imagen demasiado grande "
            "({mp:.0f} MP) – máximo: {maximum} MP"
        ),
        "canvas.rotated": "{direction} Girado: {degrees}°  ({w} × {h} px)",
        "canvas.resized": "⇲ Tamaño cambiado: {w} × {h} px",
        "canvas.resize_too_large": (
            "Tamaño objetivo {w} × {h} px demasiado grande ({mp:.0f} MP) – máximo: {maximum} MP"
        ),
        "canvas.color_adjusted": "🎨 Corrección de color aplicada",
        "canvas.not_color_layer": "No hay capa de color activa",
        "canvas.feathered": "🪶 Borde suavizado: {radius} px",
        "canvas.flipped_h": "↔ Volteado horizontalmente",
        "canvas.flipped_v": "↕ Volteado verticalmente",
        "canvas.crop_cancelled": "Recorte cancelado",
        "canvas.crop_size": "⇲ Tamaño: {w} × {h} px",
        "canvas.crop_start_circle": (
            "✂  Mueve el recorte  [círculo]  —  luego pulsa ✓ Aplicar"
        ),
        "canvas.crop_start_ratio": (
            "✂  Mueve el recorte  [{w} × {h} px]  —  luego pulsa ✓ Aplicar"
        ),
        "canvas.cropped": "✂  Recortado: {w} × {h} px",
        "canvas.save_failed": "Error al guardar: {error}",
        "canvas.saved": "💾 Guardado: {name}",
        # History step descriptions
        "history.desc.generic": "Edición",
        "history.desc.original_restored": "🔄 Original restaurado",
        "history.desc.bg_removed": "Fondo eliminado",
        "history.desc.color_replaced": "Color reemplazado ({color})",
        "history.desc.ai_bg": "Eliminación de fondo por IA",
        "history.desc.round_corners": "Esquinas redondeadas ({r} px)",
        "history.desc.rotated": "{direction} Girado {degrees}°",
        "history.desc.resized": "Tamaño cambiado ({w}×{h} px)",
        "history.desc.color_adjusted": "Corrección de color",
        "history.desc.feathered": "Borde suavizado ({radius} px)",
        "history.desc.crop_circle": "Formato: círculo",
        "history.desc.crop_ratio": "Formato: {w}×{h} px",
        # §9-Angleich rechte Spalte – KI/Export/Speichern (#436–#440)
        # Kurzlabel, damit der Primärbutton einzeilig bleibt (§5.4, #515);
        # der volle Wortlaut steht im Tooltip.
        "right_panel.ai.remove": "Eliminar fondo (IA)",
        "right_panel.ai.remove.tooltip": (
            "Eliminar el fondo automáticamente: separar el motivo del fondo con IA"),
        "right_panel.ai.remove.tooltip.warmup": (
            "Cargando modelo de IA… – el botón se activará en breve"),
        "right_panel.ai.remove.tooltip.no_image": "Primero abre una imagen",
        "right_panel.ai.remove.tooltip.processing": "La IA ya está procesando una imagen…",
        "right_panel.export.section.save": "Guardar",
        "right_panel.export.format_label": "Formato de archivo",
        "right_panel.export.save": "Guardar imagen",
        "right_panel.export.save.tooltip": "Guardar el motivo de color como imagen",
        "right_panel.export.section.uvprint": "Impresión UV",
        "right_panel.export.eufymake": "Exportar assets para EufyMake Studio…",
        "right_panel.export.eufymake.tooltip": (
            "Exportar color, altura y gloss para EufyMake Studio"),
        "workflow.open.recent": "Abiertos recientemente",
        # Geführter Workflow – Schrittleiste, Inspector-Kopf, Navigation (Epic #418)
        "workflow.step.open": "Abrir",
        "workflow.step.cutout": "Quitar fondo",
        "workflow.step.adjust": "Ajustar",
        "workflow.step.shape": "Forma y medidas",
        "workflow.step.relief": "Relieve y capas",
        "workflow.step.export": "Exportar",
        "workflow.title.open": "Paso 1 · Abrir",
        "workflow.title.cutout": "Paso 2 · Quitar fondo",
        "workflow.title.adjust": "Paso 3 · Ajustar",
        "workflow.title.shape": "Paso 4 · Forma y medidas",
        "workflow.title.relief": "Paso 5 · Relieve y capas",
        "workflow.title.export": "Paso 6 · Exportar",
        "workflow.desc.open": "Cargar una imagen — arrastrar y soltar, diálogo o abiertas recientemente.",
        "workflow.desc.cutout": "Separar el motivo del fondo — automáticamente o a mano.",
        "workflow.desc.adjust": "Brillo, contraste y saturación con vista previa en vivo.",
        "workflow.desc.shape": "Girar, voltear, redondear, recortar y escalar.",
        "workflow.desc.relief": "Gestionar capas y el mapa de altura para la impresión en relieve.",
        "workflow.desc.export": "Revisar el resultado, guardar o exportar para EufyMake.",
        "workflow.next.open": "Siguiente: Quitar fondo →",
        "workflow.next.cutout": "Siguiente: Ajustar →",
        "workflow.next.adjust": "Siguiente: Forma y medidas →",
        "workflow.next.shape": "Siguiente: Relieve y capas →",
        "workflow.next.relief": "Siguiente: Exportar →",
        "workflow.next.export": "Exportar ✓",
        "workflow.back": "← Atrás",
        "workflow.open.drop": "Arrastra una imagen aquí",
        "workflow.open.formats": "PNG · JPEG · WebP · TIFF · BMP · GIF",
        "workflow.open.button": "Abrir archivo…",
        "workflow.locked": "Abre primero una imagen (paso 1)",
        "workflow.status.step": "Paso {num}/{total}: {title}",
    },
    "fr": {
        # Status bar messages
        "status.no_image_loaded": "Aucune image chargée",
        "status.no_image_to_save": "Aucune image à enregistrer",
        "status.already_loading": "Une image est déjà en cours de chargement…",
        "status.load_result_discarded": (
            "Résultat de chargement abandonné – l'image a changé entre-temps"
        ),
        "status.ai_already_running": "L'IA est déjà en cours…",
        "status.ai_processing": "L'IA traite l'image… (peut prendre quelques secondes)",
        "status.ai_ready": "IA prête",
        "status.ai_model_loading": "Chargement du modèle d'IA…",
        "status.ai_warmup_failed": "⚠️ Impossible de charger le modèle d'IA",
        "status.ai_warmup_cancelled": "Téléchargement du modèle d'IA annulé",
        "status.ai_cancelling": "Annulation – en attente de l'IA en cours…",
        "status.ai_cancelled": "Traitement IA annulé",
        "status.ai_result_discarded": (
            "Résultat IA abandonné – l'image a changé entre-temps"
        ),
        "status.wand_busy": "La baguette magique travaille encore…",
        "status.selection_calculating": "⏳ Calcul de la sélection…",
        "status.wand_discarded": (
            "Sélection de la baguette abandonnée – l'image a changé entre-temps"
        ),
        "status.no_selection": (
            "Aucune sélection – sélectionnez d'abord une zone avec la baguette magique ou le pinceau"
        ),
        "status.start_hint": (
            "Ouvrir une image : Fichier → Ouvrir  ou  glisser-déposer sur la zone de travail"
        ),
        "status.quitting": "Fermeture…",
        "status.shutdown_failed": (
            "Fermeture impossible – un processus en arrière-plan est encore actif"
        ),
        # Statusleisten-Meldungen mit interpolierten Werten
        "status.loading": "⏳ Chargement : {name}…",
        "status.load_error": "Erreur de chargement : {msg}",
        "status.file_too_large": "Fichier trop volumineux ({size} Mo) – maximum : {limit} Mo",
        "status.image_too_large": "Image trop grande – maximum : {limit} Mpx",
        "status.image_too_large_mp": "Image trop grande ({mp:.0f} Mpx) – maximum : {limit} Mpx",
        "status.file_missing": "Le fichier n'existe plus : {name}",
        "status.open_not_local": "Seuls les fichiers locaux peuvent être ouverts.",
        "status.ai_error": "Erreur IA : {msg}",
        # Projektdatei (.bgrproj) – Lade-/Speicherfehler
        "project.error.corrupt": "Fichier de projet endommagé ou projet non valide",
        "project.error.too_large": (
            "Fichier de projet trop volumineux ({size} Mo) – maximum : {limit} Mo"
        ),
        "project.error.manifest_missing": "Fichier de projet incomplet : manifest.json manquant",
        "project.error.manifest_invalid": "Fichier de projet endommagé : manifeste non valide",
        "project.error.unsupported_version": (
            "La version de format de projet {version} n'est pas prise en charge"
        ),
        "project.error.future_version": (
            "Ce projet a été créé avec une version plus récente de BgRemover "
            "(format v{version} ; pris en charge : v{supported}). Mettez "
            "l'application à jour. Le fichier n'a pas été modifié."
        ),
        "project.error.unexpected_entry": (
            "Fichier de projet rejeté : entrée inattendue « {name} »"
        ),
        "project.error.entry_too_large": (
            "Fichier de projet rejeté : l'entrée « {name} » est trop volumineuse (décompressée)"
        ),
        "project.error.layer_file_missing": (
            "Fichier de projet incomplet : l'image de calque « {file} » est manquante"
        ),
        "project.error.layer_too_large": (
            "Calque trop grand ({mp:.0f} Mpx) – maximum : {limit} Mpx"
        ),
        "project.error.layer_size_mismatch": (
            "La taille du calque {actual} ne correspond pas à la taille du plan de travail {expected}"
        ),
        "project.error.height16_invalid": (
            "Fichier de projet endommagé : les données de hauteur 16 bits « {file} » sont invalides"
        ),
        "project.error.height16_integrity": (
            "Fichier de projet endommagé : la vérification d'intégrité de « {file} » a échoué "
            "(fichier tronqué ou interverti)"
        ),
        "project.warning.role_normalized": (
            "Rôle de carte de hauteur incompatible retiré : « {name} » n'est pas un calque de hauteur"
        ),
        # EufyMake-Export – Konsistenzbefunde (#354)
        "eufymake.export.color_motif_missing": (
            "Motif couleur manquant : aucun rôle COLOR_MOTIF et aucun calque de "
            "couleur contribuant au composite."
        ),
        "eufymake.export.optional_role_missing": (
            "Le rôle optionnel sélectionné « {role_name} » n'a pas de calque."
        ),
        "eufymake.export.asset_size_mismatch": (
            "La taille de l'asset {actual} ne correspond pas à la taille cible {expected}."
        ),
        "eufymake.export.invalid_target_params": "Paramètres cibles non valides : {detail}",
        "eufymake.export.height_map_empty": (
            "La carte de hauteur est vide ou constante et pourrait ne produire aucun relief."
        ),
        "eufymake.export.gloss_mask_empty": (
            "Le masque gloss est vide ou constant et pourrait être inutile."
        ),
        "eufymake.export.bit_depth_unconfirmed": (
            "Une carte de hauteur {bits} bits n'est pas officiellement confirmée pour EufyMake Studio."
        ),
        "eufymake.export.gloss_ink_mode": (
            "Le gloss n'est qu'un asset d'import/d'aide – le mode d'encre et "
            "l'affectation des calques se font dans EufyMake Studio."
        ),
        "eufymake.export.physical_size_unverified": (
            "La taille physique et l'hypothèse pixel↔mm/DPI sont plausibles, mais "
            "sans contrat fabricant confirmé."
        ),
        # Allgemeine Pre-Export-Prüfung (#379)
        "export.checks.dimensions_invalid": (
            "Dimensions non valides : {width}×{height} px – largeur et hauteur doivent être positives."
        ),
        "export.checks.dimensions_too_large": (
            "Sortie trop grande : {mp} Mpx dépassent la limite de {limit} Mpx."
        ),
        "export.checks.color_space_unexpected": (
            "Espace colorimétrique inattendu : {actual} (attendu : {expected})."
        ),
        "export.checks.output_empty": "Sortie vide : le projet ne contient aucun calque.",
        "export.checks.resolution_too_low": (
            "Résolution faible : {dpi} DPI (minimum recommandé : {minimum} DPI)."
        ),
        "export.checks.resolution_too_high": (
            "Résolution très élevée : {dpi} DPI (maximum recommandé : {maximum} DPI)."
        ),
        "export.checks.fully_transparent": (
            "Entièrement transparent : la sortie ne contient aucun pixel visible."
        ),
        "export.checks.unexpected_alpha": (
            "Transparence partielle : {percent} % des pixels sont semi-transparents."
        ),
        "export.checks.print_area_exceeded": (
            "Le motif dépasse la surface d'impression : "
            "{width}×{height} mm > {medium_w}×{medium_h} mm."
        ),
        # Pre-Export-Prüfung beim normalen Speichern (#380)
        "export.check.error.title": "Enregistrement impossible",
        "export.check.blocked": (
            "L'enregistrement a été interrompu à cause des problèmes suivants :\n\n{details}"
        ),
        "export.check.warning.title": "Avertissements avant l'enregistrement",
        "export.check.confirm": (
            "Des avertissements existent :\n\n{details}\n\nEnregistrer quand même ?"
        ),
        # EufyMake-Export – Menü, Dialog & Meldungen (#355)
        "action.export_eufymake": "Exporter les assets pour EufyMake Studio…",
        "eufymake.dialog.title": "Exporter les assets pour EufyMake Studio",
        "eufymake.dialog.intro": (
            "BgRemover écrit des assets d'import pour EufyMake Studio – pas un "
            "projet « .empf » fini. Importez-les et positionnez-les ensuite dans "
            "Studio, affectez-y les modes d'encre/calques et enregistrez vous-même "
            "le projet en « .empf »."
        ),
        "eufymake.dialog.section.assets": "Assets",
        "eufymake.dialog.color_motif": "Motif couleur (obligatoire)",
        "eufymake.dialog.color_motif.hint": (
            "PNG RGBA issu du composite couleur ; la transparence est conservée."
        ),
        "eufymake.dialog.height": "Inclure la carte de hauteur",
        "eufymake.dialog.height.hint": "PNG en niveaux de gris : clair = haut, sombre = bas.",
        "eufymake.dialog.height.unavailable": "Aucun calque de hauteur dans le projet.",
        "eufymake.dialog.gloss": "Inclure le masque gloss (expérimental)",
        "eufymake.dialog.gloss.hint": (
            "Asset d'aide optionnel. Le mode d'encre et l'affectation des calques "
            "se font dans EufyMake Studio."
        ),
        "eufymake.dialog.gloss.unavailable": "Aucun calque gloss dans le projet.",
        "eufymake.dialog.section.target": "Paramètres cibles",
        "eufymake.dialog.bit_depth": "Profondeur de bits de la carte de hauteur :",
        "eufymake.dialog.bit_depth.8": "8 bits (par défaut)",
        "eufymake.dialog.bit_depth.16": "16 bits (expérimental, non confirmé)",
        "eufymake.dialog.size": "Taille cible : {w} × {h} px",
        "eufymake.dialog.physical": "Taille physique : {w} × {h} mm ({dpi} dpi)",
        "eufymake.dialog.physical.unset": "Taille physique : non définie",
        "eufymake.dialog.section.dest": "Destination",
        "eufymake.dialog.dest.label": "Dossier d'export :",
        "eufymake.dialog.dest.placeholder": "Aucun dossier choisi pour l'instant",
        "eufymake.dialog.dest.is_file": (
            "La destination est un fichier existant – veuillez choisir un dossier."
        ),
        "eufymake.dialog.dest.browse": "Parcourir…",
        "eufymake.dialog.dest.dialog_title": "Choisir le dossier d'export",
        "eufymake.dialog.section.findings": "Vérification",
        "eufymake.dialog.findings.ok": "Aucune anomalie.",
        "eufymake.dialog.finding.error": "⛔  {msg}",
        "eufymake.dialog.finding.warning": "⚠️  {msg}",
        "eufymake.dialog.confirm_warnings": "Avertissements compris – exporter quand même",
        "eufymake.dialog.cancel": "Annuler",
        "eufymake.dialog.export": "Exporter",
        "eufymake.status.no_project": "Aucun projet à exporter",
        "eufymake.status.cancelled": "Export annulé",
        "eufymake.status.exported": "✅ Assets exportés pour EufyMake Studio : {path}",
        "eufymake.error.title": "Échec de l'export",
        "eufymake.error.write": "Échec de l'export : {error}",
        "eufymake.error.not_directory": (
            "La cible « {path} » est un fichier existant. Veuillez choisir un "
            "dossier comme destination d'export."
        ),
        "eufymake.error.blocked": "Export bloqué – corrigez d'abord ceci :\n{details}",
        "eufymake.overwrite.title": "Écraser le dossier ?",
        "eufymake.overwrite.body": "« {path} » existe déjà. Remplacer son contenu ?",
        "eufymake.success.title": "Export terminé",
        "eufymake.success.body": (
            "Assets d'import écrits dans :\n{path}\n\n"
            "Étapes suivantes dans EufyMake Studio :\n"
            "1. Importer et positionner les assets.\n"
            "2. Affecter les modes d'encre/calques (p. ex. gloss/vernis).\n"
            "3. Enregistrer le projet dans Studio en « .empf »."
        ),
        # Ebenen-Panel & Projekt-Aktionen (#334)
        "layers.new_name": "Calque {n}",
        "layers.role.none": "Aucun",
        "layers.role.color_motif": "Motif couleur",
        "layers.role.height_map": "Carte de hauteur",
        "layers.role.gloss": "Gloss",
        "layers.height_name": "Carte de hauteur",
        "history.desc.layer_added": "Calque ajouté",
        "history.desc.layer_removed": "Calque supprimé",
        "history.desc.layer_duplicated": "Calque dupliqué",
        "history.desc.layer_reordered": "Calque déplacé",
        "history.desc.layer_renamed": "Calque renommé",
        "history.desc.layer_active": "Calque actif changé",
        "history.desc.layer_visibility": "Visibilité modifiée",
        "history.desc.layer_opacity": "Opacité modifiée",
        "history.desc.layer_role": "Rôle modifié",
        "history.desc.height_generated": "Carte de hauteur générée",
        "history.desc.height_imported": "Carte de hauteur importée",
        "history.desc.height_lighten": "Hauteur éclaircie",
        "history.desc.height_darken": "Hauteur assombrie",
        "history.desc.height_set": "Hauteur définie",
        "history.desc.height_invert": "Hauteur inversée",
        "history.desc.height_optimized": "Hauteur optimisée",
        "canvas.layer_added": "Nouveau calque ajouté",
        "canvas.height_generated": "Carte de hauteur générée depuis l'image",
        "canvas.height_imported": "Carte de hauteur importée : {name}",
        "canvas.height_imported_16bit": (
            "Carte de hauteur importée : {name} (16 bits natif)"
        ),
        "right_panel.height.depth_info": (
            "Données de hauteur internes : 16 bits (0–65535)"
        ),
        "eufymake.export.height_precision_loss": (
            "L'export 8 bits quantifie les hauteurs 16 bits sur 256 niveaux "
            "contrôlés – choisissez 16 bits pour la pleine précision"
        ),
        "status.height_source_unsupported": (
            "Import de hauteurs : le mode d'image « {mode} » n'est pas pris en charge"
        ),
        "status.height_import_failed": "L'import de hauteurs a échoué",
        "right_panel.height.scale_hint": (
            "Échelle 0–255 ; projetée proportionnellement sur la plage de "
            "hauteurs 16 bits (0–65535)"
        ),
        "canvas.height_lightened": "Hauteur éclaircie",
        "canvas.height_darkened": "Hauteur assombrie",
        "canvas.height_set": "Hauteur définie",
        "canvas.height_inverted": "Hauteur inversée",
        "canvas.height_optimized": "Hauteur optimisée",
        "canvas.height_op_error": "Échec de l'opération de hauteur : {error}",
        "canvas.not_height_layer": "Aucun calque de hauteur actif",
        "canvas.role_incompatible": (
            "Le rôle « Carte de hauteur » n'est disponible que pour les calques de hauteur"
        ),
        "canvas.layer_removed": "Calque supprimé",
        "canvas.layer_duplicated": "Calque dupliqué",
        "canvas.cannot_delete_last": "Le dernier calque ne peut pas être supprimé",
        "right_panel.tab.layers": "Calques",
        "right_panel.tab.layers.tooltip": "Gérer les calques",
        "right_panel.tab.height": "Hauteur",
        "right_panel.tab.height.tooltip": "Carte de hauteur (relief)",
        "right_panel.tab.preview": "Aperçu",
        "right_panel.tab.preview.tooltip": "Affichage 2D pour couleur, relief et gloss",
        "right_panel.preview.section": "Mode d'aperçu 2D",
        "right_panel.preview.hint": (
            "L'aperçu est indépendant du calque actif."
        ),
        "right_panel.preview.mode": "Affichage :",
        "right_panel.preview.relief_strength": "Intensité du relief :  {value} %",
        "right_panel.preview.relief_strength.tooltip": (
            "Intensité de l'ombrage dans les modes Relief et Combiné"
        ),
        "right_panel.preview.gloss_visible": "Afficher le gloss",
        "right_panel.preview.gloss_visible.tooltip": (
            "Afficher ou masquer le reflet gloss dans les modes Gloss et Combiné"
        ),
        "right_panel.preview.export_hint": (
            "Affichage seulement – « Enregistrer l'image » exporte toujours "
            "uniquement le motif couleur."
        ),
        "right_panel.height.section.acquire": "Obtenir",
        "right_panel.height.section.edit": "Modifier",
        "right_panel.height.section.optimize": "Optimiser",
        "right_panel.height.generate": "Générer depuis l'image",
        "right_panel.height.generate.tooltip": (
            "Générer une carte de hauteur à partir de l'image actuelle"
        ),
        "right_panel.height.import": "Importer niveaux de gris…",
        "right_panel.height.import.tooltip": (
            "Importer une image en niveaux de gris comme carte de hauteur"
        ),
        "right_panel.height.hint": (
            "Les outils de hauteur agissent sur le calque de hauteur actif."
        ),
        "right_panel.height.strength": "Intensité",
        "right_panel.height.lighten": "Éclaircir",
        "right_panel.height.lighten.tooltip": (
            "Augmenter la hauteur dans la sélection (sinon globalement)"
        ),
        "right_panel.height.darken": "Assombrir",
        "right_panel.height.darken.tooltip": (
            "Diminuer la hauteur dans la sélection (sinon globalement)"
        ),
        "right_panel.height.set_value": "Valeur",
        "right_panel.height.set": "Définir la hauteur",
        "right_panel.height.set.tooltip": (
            "Définir la hauteur à la valeur (sélection ou global)"
        ),
        "right_panel.height.invert": "Inverser",
        "right_panel.height.invert.tooltip": (
            "Inverser la hauteur (sélection ou global)"
        ),
        "right_panel.height.levels": "Niveaux (noir/blanc)",
        "right_panel.height.gamma": "Gamma",
        "right_panel.height.gaussian": "Flou gaussien (rayon)",
        "right_panel.height.median": "Flou médian (rayon)",
        "right_panel.height.threshold": "Seuil",
        "right_panel.height.steps": "Paliers",
        "right_panel.height.range": "Plage (min/max)",
        "right_panel.height.apply": "Appliquer",
        "right_panel.height.apply.tooltip": "Appliquer l'aperçu au calque de hauteur",
        "right_panel.height.discard_preview": "Abandonner l'aperçu",
        "right_panel.height.discard_preview.tooltip": (
            "Abandonner l'aperçu sans l'appliquer"
        ),
        "right_panel.layers.section": "Calques",
        "right_panel.layers.add.tooltip": "Nouveau calque",
        "right_panel.layers.duplicate.tooltip": "Dupliquer le calque actif",
        "right_panel.layers.delete.tooltip": "Supprimer le calque actif",
        "right_panel.layers.move_up.tooltip": "Monter le calque",
        "right_panel.layers.move_down.tooltip": "Descendre le calque",
        "right_panel.layers.rename.tooltip": "Renommer le calque actif",
        "right_panel.layers.role_label": "Rôle :",
        "right_panel.layers.role.tooltip": (
            "Rôle du calque actif (pour de futurs outils d'impression UV)"
        ),
        "right_panel.layers.visible.tooltip": "Basculer la visibilité",
        "right_panel.layers.select.tooltip": "Choisir comme calque actif",
        "right_panel.layers.opacity.tooltip": "Opacité (appliquée au relâchement)",
        "right_panel.layers.empty": (
            "Aucun projet chargé – ouvrez une image ou « Nouveau projet »."
        ),
        "menu.project": "Projet",
        "action.new_project": "Nouveau projet",
        "action.open_project": "Ouvrir un projet…",
        "action.save_project": "Enregistrer le projet",
        "action.save_project_as": "Enregistrer le projet sous…",
        "dialog.open_project.title": "Ouvrir un projet",
        "dialog.open_project.filter": "Projet BgRemover (*.bgrproj)",
        "dialog.save_project.title": "Enregistrer le projet",
        "dialog.rename.title": "Renommer le calque",
        "dialog.rename.label": "Nouveau nom :",
        "dialog.import_height.title": "Importer une carte de hauteur",
        "dialog.project_error.title": "Erreur de projet",
        "project.new": "Nouveau projet créé",
        "project.saved": "Projet enregistré : {name}",
        "project.opened": "Projet ouvert : {name}",
        "project.no_project": "Aucun projet à enregistrer",
        "project.save_failed": "Échec de l'enregistrement du projet : {error}",
        # Main menu
        "menu.file": "Fichier",
        "menu.recent_files": "Récemment ouverts",
        "menu.edit": "Édition",
        "menu.view": "Affichage",
        "menu.preview_mode": "Mode d'aperçu",
        "menu.extras": "Outils",
        "action.open": "Ouvrir…",
        "action.save": "Enregistrer",
        "action.save_as": "Enregistrer sous…",
        "action.undo": "Annuler",
        "action.redo": "Rétablir",
        "action.rotate_left_90": "Pivoter de 90° à gauche",
        "action.rotate_right_90": "Pivoter de 90° à droite",
        "action.rotate_180": "Pivoter de 180°",
        "action.flip_horizontal": "Retourner horizontalement",
        "action.flip_vertical": "Retourner verticalement",
        "action.resize": "Redimensionner…",
        "action.clear_selection": "Annuler la sélection",
        "action.invert_selection": "Inverser la sélection",
        "action.restore_original": "Restaurer l'original",
        "action.fit_to_view": "Ajuster à la vue",
        # Verlauf-Popup: Menü-Anker seit #458 (Rail-Button entfallen)
        "action.history": "Historique",
        # Zoom-Kontrolle auf der Arbeitsfläche (#464)
        "zoom.in.tooltip": "Zoom avant (+10 %)",
        "zoom.out.tooltip": "Zoom arrière (−10 %)",
        "zoom.lock.tooltip": "Verrouiller le zoom (garder la valeur actuelle)",
        "zoom.unlock.tooltip": "Déverrouiller le zoom",
        "preview.mode.color": "Couleur",
        "preview.mode.relief": "Relief sur couleur",
        "preview.mode.height": "Hauteur (niveaux de gris)",
        "preview.mode.gloss": "Gloss",
        "preview.mode.combined": "Combiné",
        # Kurzlabels für das Segmented-Control der 2D-Vorschau (§9 Schritt 6)
        "preview.seg.color": "Couleur",
        "preview.seg.relief": "Relief",
        "preview.seg.height": "Hauteur",
        "preview.seg.gloss": "Gloss",
        # Aperçu du relief 3D (Epic #582)
        "menu.view.show_3d": "Afficher le relief 3D",
        "preview3d.section": "Aperçu du relief 3D",
        "preview3d.display": "Affichage :",
        "preview3d.display.2d": "2D",
        "preview3d.display.3d": "3D",
        "preview3d.display.3d.disabled_tooltip": (
            "La 3D nécessite une carte de hauteur valide et OpenGL 2.1."
        ),
        "preview3d.exaggeration": "Exagération :  {value}×",
        "preview3d.exaggeration.hint": "Modifie seulement l'affichage, jamais les données de hauteur.",
        "preview3d.light_azimuth": "Azimut de lumière :  {value}°",
        "preview3d.light_elevation": "Élévation de lumière :  {value}°",
        "preview3d.quality": "Qualité :",
        "preview3d.quality.reduced": "Réduite",
        "preview3d.quality.standard": "Standard",
        "preview3d.quality.high": "Haute",
        "preview3d.fit": "Ajuster à la vue",
        "preview3d.reset": "Réinitialiser",
        "preview3d.empty": (
            "Aucune carte de hauteur pour l'instant. Créez-en une dans l'onglet "
            "Hauteur pour utiliser l'aperçu 3D."
        ),
        "preview3d.unavailable": (
            "Aperçu 3D indisponible : cet environnement ne fournit pas OpenGL 2.1. "
            "L'aperçu du relief 2D reste disponible."
        ),
        "preview3d.loading": "Calcul de l'aperçu 3D…",
        "preview3d.ready_hint": (
            "Aperçu 3D actif – les images enregistrées et les exports restent inchangés."
        ),
        "preview3d.decimated": "Vue simplifiée 1:{factor}",
        "preview3d.error": (
            "L'aperçu 3D a rencontré une erreur graphique. Votre édition, le projet "
            "et l'export ne sont pas affectés."
        ),
        "preview3d.error.show_2d": "Afficher le relief 2D",
        "preview3d.error.retry": "Réessayer",
        "preview3d.a11y.name": "Aperçu du relief 3D",
        "preview3d.a11y.desc": (
            "Surface 3D interactive. Glissez pour orbiter, molette pour zoomer, "
            "Alt+glisser pour déplacer ; les flèches orbitent, Origine ajuste la vue."
        ),
        # Design-Umschalter (Epic #424, Issue #428)
        "action.light_mode": "Thème clair",
        "theme.switched.light": "Thème clair activé.",
        "theme.switched.dark": "Thème sombre activé.",
        "action.settings": "Réglages…",
        "action.check_for_updates": "Rechercher des mises à jour…",
        "action.manage_ai_model": "Gérer le modèle d'IA…",
        "action.install_ai_backend": "Installer la suppression d'arrière-plan par IA…",
        # App-Update-Check (#565)
        "status.update_check_running": "Recherche de mises à jour…",
        "status.update_available_hint": (
            "🆕 Mise à jour disponible : {version} – cliquez pour plus de détails"
        ),
        "dialog.update_check.title": "Vérification des mises à jour",
        "dialog.update_check.up_to_date.body": (
            "Vous utilisez déjà la dernière version ({version})."
        ),
        "dialog.update_check.available.body": (
            "Une nouvelle version est disponible : {latest} (installée : {current})."
        ),
        "dialog.update_check.open_release": "Ouvrir la page de la version",
        "dialog.update_check.failed.body": (
            "La vérification des mises à jour a échoué. Veuillez réessayer plus tard."
        ),
        # KI-Modell-Verwaltung (#569)
        "ai_model.dialog.title": "Gérer le modèle d'IA",
        "ai_model.status.downloaded": "Téléchargé ({path}, {size})",
        "ai_model.status.not_downloaded": "Non téléchargé",
        "ai_model.status.rembg_unavailable": (
            "Fonction d'IA indisponible (rembg non installé)"
        ),
        "ai_model.status.python_hint": "Environnement Python actif : {path}",
        "ai_model.dialog.download": "Télécharger maintenant",
        "ai_model.dialog.retry": "Réessayer",
        "ai_model.dialog.cancel": "Annuler",
        "ai_model.dialog.close": "Fermer",
        "ai_model.dialog.cancelled": "Téléchargement annulé",
        # KI-Backend nachrüsten (Menü-Aktion ohne Auto-Install)
        "ai_install.dialog.title": "Installer la suppression d'arrière-plan par IA",
        "ai_install.dialog.intro": (
            "Cette installation ne contient pas rembg (le moteur d'IA). Rien "
            "n'est installé automatiquement depuis l'application : les systèmes "
            "Linux récents bloquent pip vers le Python système (PEP 668), et un "
            "paquet fraîchement installé ne serait de toute façon visible dans "
            "le processus en cours qu'après un redémarrage. Exécutez ceci dans "
            "un terminal, dans le dossier du projet :"
        ),
        "ai_install.dialog.venv_note": (
            'Déjà dans votre propre venv ? Il suffit de : pip install "rembg[cpu]"'
        ),
        "ai_install.dialog.already_installed": (
            "Remarque : rembg est déjà installé dans l'environnement en cours "
            "d'exécution."
        ),
        "ai_install.dialog.python_too_old": (
            "⚠ Le Python actif {version} est trop ancien pour l'IA : "
            "rembg/onnxruntime nécessitent Python 3.11+. Installez d'abord une "
            'version de Python plus récente (p. ex. via Homebrew/pyenv/apt) et '
            'assurez-vous que "python3" pointe dessus avant d\'exécuter la '
            "commande."
        ),
        "ai_install.dialog.copy": "Copier la commande",
        "ai_install.dialog.copied": "Copié dans le presse-papiers.",
        # Left toolbar
        "toolbar.move.tooltip": (
            "Déplacer / Zoom\n"
            "Glisser avec le clic gauche déplace la vue · la molette zoome"
        ),
        "toolbar.wand.tooltip": (
            "Baguette magique  (W)\n"
            "Un clic sélectionne une zone de couleur (remplissage par diffusion)\n"
            "Maj = ajouter  ·  {modifier} = soustraire"
        ),
        "toolbar.brush.tooltip": "Pinceau  (B)\nAjouter manuellement des zones à la sélection",
        "toolbar.eraser.tooltip": "Gomme  (E)\nRetirer des zones de la sélection",
        "toolbar.lasso.tooltip": (
            "Lasso polygonal  (L)\n"
            "Cliquer pose des points · double-clic ferme le polygone\n"
            "Maj = ajouter  ·  {modifier} = soustraire  ·  Échap = annuler"
        ),
        "toolbar.height_lighten.tooltip": (
            "Éclaircir (rehausser)\n"
            "Le coup de pinceau augmente la hauteur du calque de hauteur actif"
        ),
        "toolbar.height_darken.tooltip": (
            "Assombrir (abaisser)\n"
            "Le coup de pinceau diminue la hauteur du calque de hauteur actif"
        ),
        "toolbar.height_tools.disabled.tooltip": (
            "Outil de hauteur\n"
            "Activez d'abord un calque de hauteur (étape 5 : générer/importer une carte de hauteur)"
        ),
        "toolbar.ai.missing.tooltip": (
            'rembg non installé\n→ python3 -m pip install -e ".[ai]"'
        ),
        "toolbar.undo.tooltip": (
            "Annuler  ({shortcut})\n"
            "Annuler la dernière étape d'édition"
        ),
        "toolbar.redo.tooltip": (
            "Rétablir  ({shortcut})\n"
            "Rétablir la dernière étape annulée"
        ),
        "toolbar.theme.to_light.tooltip": "Passer au thème clair",
        "toolbar.theme.to_dark.tooltip": "Passer au thème sombre",
        # Right panel tabs
        "right_panel.tab.selection": "Sélection",
        "right_panel.tab.selection.tooltip": (
            "Sélection – baguette magique, pinceau, gomme"
        ),
        "right_panel.tab.background": "Arrière-plan",
        "right_panel.tab.background.tooltip": (
            "Arrière-plan – supprimer, remplacer la couleur"
        ),
        "right_panel.tab.adjust": "Ajuster",
        "right_panel.tab.adjust.tooltip": (
            "Correction colorimétrique – luminosité, contraste, saturation"
        ),
        "right_panel.tab.transform": "Pivoter/Retourner",
        "right_panel.tab.transform.tooltip": "Transformation – pivoter, retourner",
        "right_panel.tab.shape": "Forme",
        "right_panel.tab.shape.tooltip": (
            "Forme & recadrage – arrondir les coins, choix du format"
        ),
        # History popup
        "history.window_title": "Historique des modifications",
        "history.hint": "Double-clic sur une entrée → revenir à cette étape",
        "history.list.tooltip": (
            "Historique de toutes les étapes d'édition.\n"
            "Double-cliquez sur une entrée pour revenir à cette étape."
        ),
        # Crop bar
        "crop_bar.label": "✂  Positionnez le recadrage, puis confirmez :",
        "crop_bar.confirm": "✓  Appliquer le recadrage",
        "crop_bar.cancel": "✗  Annuler",
        # Right panel — Selection tab contents
        "right_panel.selection.section.settings": "Réglages de l'outil",
        "right_panel.selection.section.select": "Sélection",
        "right_panel.selection.tolerance": "Tolérance (baguette magique) :  {value}",
        "right_panel.selection.tolerance.tooltip": (
            "Contrôle la similarité requise des couleurs pour être sélectionnées.\n"
            "Bas = seulement des couleurs très proches · Haut = beaucoup de nuances"
        ),
        "right_panel.selection.brush_size": "Taille du pinceau :  {value} px",
        "right_panel.selection.brush_size.tooltip": (
            "Taille de l'outil pinceau/gomme en pixels"
        ),
        "right_panel.selection.clear": "Annuler",
        "right_panel.selection.clear.tooltip": (
            "Annule la sélection actuelle (aussi : touche Échap)"
        ),
        "right_panel.selection.invert": "Inverser",
        "right_panel.selection.invert.tooltip": (
            "Échange les zones sélectionnées et non sélectionnées  ({modifier}+Maj+I)"
        ),
        "right_panel.selection.morph.label": "Rayon :",
        "right_panel.selection.morph.tooltip": (
            "Rayon en pixels pour dilater/contracter la sélection"
        ),
        "right_panel.selection.expand": "+ Dilater",
        "right_panel.selection.expand.tooltip": (
            "Dilate la sélection du rayon défini"
        ),
        "right_panel.selection.shrink": "− Contracter",
        "right_panel.selection.shrink.tooltip": (
            "Contracte la sélection du rayon défini"
        ),
        # Right panel — Background tab contents
        "right_panel.background.section": "Modifier l'arrière-plan",
        "right_panel.background.remove": "Supprimer (transparent)",
        "right_panel.background.remove.tooltip": (
            "Rend la zone sélectionnée entièrement transparente.\n"
            "Astuce : sélectionnez d'abord l'arrière-plan avec la baguette magique."
        ),
        "right_panel.background.color_label": "Choisir une couleur et remplir la sélection :",
        "right_panel.background.color.tooltip": "Cliquez pour choisir la couleur d'arrière-plan de remplacement",
        "right_panel.background.replace": "Remplacer la couleur",
        "right_panel.background.replace.tooltip": (
            "Remplit la zone sélectionnée avec la couleur choisie"
        ),
        "right_panel.background.section.feather": "Lisser le bord",
        "right_panel.background.feather_hint": (
            "Adoucit le bord du détourage (alpha uniquement)."
        ),
        "right_panel.background.feather_radius": "Rayon :  {value} px",
        "right_panel.background.feather_radius.tooltip": (
            "Rayon du lissage de bord en pixels (0 = désactivé)"
        ),
        "right_panel.background.feather": "Lisser le bord",
        "right_panel.background.feather.tooltip": (
            "Adoucir le bord alpha du calque actif (sélection ou global)"
        ),
        # Right panel — Transform tab contents
        "right_panel.transform.section.rotate": "Pivoter",
        "right_panel.transform.quick_label": "Rotation rapide :",
        "right_panel.transform.rotate_left_90": "↺ 90° à gauche",
        "right_panel.transform.rotate_left_90.tooltip": "Pivoter de 90° dans le sens antihoraire",
        "right_panel.transform.rotate_right_90": "↻ 90° à droite",
        "right_panel.transform.rotate_right_90.tooltip": "Pivoter de 90° dans le sens horaire",
        "right_panel.transform.rotate_180": "↺ 180°",
        "right_panel.transform.rotate_180.tooltip": "Pivoter l'image de 180°",
        "right_panel.transform.rotate_270": "↺ 270°",
        "right_panel.transform.rotate_270.tooltip": "270° antihoraire (= 90° à droite)",
        "right_panel.transform.free_label": "Angle libre :",
        "right_panel.transform.angle_slider.tooltip": "Régler l'angle de rotation : −180° à +180°",
        "right_panel.transform.angle_spin.tooltip": "Saisir directement l'angle de rotation",
        "right_panel.transform.apply_angle": "Appliquer l'angle",
        "right_panel.transform.apply_angle.tooltip": (
            "Pivote l'image de l'angle défini.\n"
            "Les angles obliques créent des coins transparents."
        ),
        "right_panel.transform.section.flip": "Retourner",
        "right_panel.transform.flip_h": "Horizontal",
        "right_panel.transform.flip_h.tooltip": "Retourner l'image horizontalement (gauche ↔ droite)",
        "right_panel.transform.flip_v": "Vertical",
        "right_panel.transform.flip_v.tooltip": "Retourner l'image verticalement (haut ↕ bas)",
        # Größe-ändern-Dialog (#359)
        "resize.title": "Redimensionner",
        "resize.width": "Largeur",
        "resize.height": "Hauteur",
        "resize.link_aspect": "Conserver les proportions",
        "resize.resample.label": "Méthode :",
        "resize.resample.lanczos": "Lanczos (meilleure qualité)",
        "resize.resample.bicubic": "Bicubique",
        "resize.resample.bilinear": "Bilinéaire",
        "resize.resample.nearest": "Plus proche voisin",
        "resize.megapixels": "{mp:.1f} Mpx (maximum : {maximum} Mpx)",
        "resize.ok": "Appliquer",
        "resize.cancel": "Annuler",
        # mm/DPI-Modus + Druckflächenprüfung (#377)
        "resize.mode.label": "Unité :",
        "resize.mode.pixel": "Pixels",
        "resize.mode.mm": "Millimètres (mm + DPI)",
        "resize.width_mm": "Largeur",
        "resize.height_mm": "Hauteur",
        "resize.dpi": "Résolution",
        "resize.medium.label": "Support cible :",
        "resize.pixels_result": "Résultat : {width}×{height} px ({mp} Mpx)",
        "resize.print_area_ok": "Tient sur {medium} ({medium_w}×{medium_h} mm).",
        "resize.print_area_exceeded": (
            "⚠ Le motif {width}×{height} mm dépasse {medium} "
            "({medium_w}×{medium_h} mm)."
        ),
        # Right panel — Adjust tab contents (#360)
        "right_panel.adjust.section": "Correction colorimétrique",
        "right_panel.adjust.hint": "Agit sur le calque de couleur actif.",
        "right_panel.adjust.brightness": "Luminosité :  {value} %",
        "right_panel.adjust.brightness.tooltip": (
            "Luminosité du calque de couleur actif (100 % = inchangé)"
        ),
        "right_panel.adjust.contrast": "Contraste :  {value} %",
        "right_panel.adjust.contrast.tooltip": (
            "Contraste du calque de couleur actif (100 % = inchangé)"
        ),
        "right_panel.adjust.saturation": "Saturation :  {value} %",
        "right_panel.adjust.saturation.tooltip": (
            "Saturation du calque de couleur actif (0 % = niveaux de gris, 100 % = inchangé)"
        ),
        "right_panel.adjust.reset": "Réinitialiser",
        "right_panel.adjust.reset.tooltip": (
            "Réinitialiser les curseurs à 100 % et abandonner l'aperçu"
        ),
        "right_panel.adjust.apply": "Appliquer",
        "right_panel.adjust.apply.tooltip": (
            "Appliquer la correction colorimétrique au calque de couleur actif"
        ),
        # Right panel — Shape tab contents
        "right_panel.shape.section.corner": "Arrondir les coins",
        "right_panel.shape.radius": "Rayon :  {value} px",
        "right_panel.shape.radius.tooltip": (
            "Rayon de l'arrondi des coins en pixels.\n"
            "0 = aucun arrondi · 500 = arrondi maximal"
        ),
        "right_panel.shape.round": "Arrondir les coins",
        "right_panel.shape.round.tooltip": (
            "Applique l'arrondi des coins.\n"
            "Le résultat est enregistré en PNG avec des coins transparents."
        ),
        "right_panel.shape.section.resize": "Redimensionner",
        "right_panel.shape.resize_apply": "Appliquer la taille",
        "right_panel.shape.resize_apply.tooltip": "Mettre à l'échelle à la taille saisie",
        "right_panel.shape.section.format": "Format de recadrage",
        "right_panel.shape.circle": "⬤  Cercle",
        "right_panel.shape.circle.tooltip": "Positionner un recadrage circulaire et l'appliquer",
        # Settings dialog
        "settings.title": "Réglages",
        "settings.open_dir.label": "Répertoire par défaut pour l'ouverture",
        "settings.save_dir.label": "Répertoire par défaut pour l'export / l'enregistrement",
        "settings.dir.placeholder": "Vide = dernier répertoire utilisé",
        "settings.format.label": "Format d'image préféré",
        "settings.log.label": "Fichier journal",
        "settings.log.tooltip": "Chemin du fichier journal (sélectionner pour copier)",
        "settings.log.open_button": "Ouvrir le dossier",
        "settings.log.open_failed": "Impossible d'ouvrir le dossier :\n{target}",
        "settings.update.auto_check.label": (
            "Rechercher automatiquement des mises à jour au démarrage"
        ),
        "settings.cancel": "Annuler",
        "settings.ok": "OK",
        "settings.pick_open.title": "Choisir le répertoire pour l'ouverture",
        "settings.pick_save.title": "Choisir le répertoire pour l'export/l'enregistrement",
        "settings.invalid_dir.title": "Répertoire non valide",
        "settings.invalid_dir.body": "{label} n'est pas un répertoire existant :\n{value}",
        "settings.language.label": "Langue",
        "settings.language.restart_title": "Redémarrage requis",
        "settings.language.restart_hint": (
            "Le changement de langue prendra effet au prochain démarrage."
        ),
        # Dialogs (QMessageBox)
        "dialog.ai_error.title": "Erreur IA",
        "dialog.ai_error.body": (
            "Erreur lors de la suppression automatique de l'arrière-plan :\n\n{msg}"
        ),
        # Main-window dialogs
        "dialog.unsaved.title": "Modifications non enregistrées",
        "dialog.unsaved.body": (
            "L'image a été modifiée. Enregistrer les modifications avant de l'abandonner ?"
        ),
        "dialog.open.title": "Ouvrir une image",
        "dialog.open.filter": (
            "Images (*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.tif *.gif);;"
            "Tous les fichiers (*)"
        ),
        "dialog.save.title": "Enregistrer l'image sous…",
        "dialog.color.title": "Choisir la couleur d'arrière-plan",
        # Canvas status messages
        "canvas.opened": "Ouvert : {name}  ({w} × {h} px)",
        "canvas.opened_extra": (
            "Ouvert : {name}  ({extra} autre(s) fichier(s) ignoré(s))"
        ),
        "canvas.undo_none": "Plus rien à annuler",
        "canvas.undo_done": "↩  Annulé : {desc}",
        "canvas.redo_none": "Plus rien à rétablir",
        "canvas.redo_done": "↪  Rétabli : {desc}",
        "canvas.undo_to": "↩  {steps} étape(s) annulée(s)  (jusqu'à : {desc})",
        "canvas.original_restored": "🔄  Original restauré",
        "canvas.selection_cleared": "Sélection annulée",
        "canvas.selection_inverted": "Sélection inversée : {pixels:,} pixels",
        "canvas.selection_expanded": "Sélection dilatée de {radius} px : {pixels:,} pixels",
        "canvas.selection_shrunk": "Sélection contractée de {radius} px : {pixels:,} pixels",
        "canvas.bg_removed": "Arrière-plan supprimé (transparent)",
        "canvas.remove_error": "Erreur lors de la suppression : {error}",
        "canvas.bg_replaced": "Arrière-plan remplacé : {color}",
        "canvas.replace_error": "Erreur lors du remplacement : {error}",
        "canvas.ai_done": "✅ Suppression de l'arrière-plan par IA terminée",
        "canvas.selection_pixels": "Sélection : {pixels:,} pixels",
        "canvas.selection_error": "Erreur de sélection : {msg}",
        "canvas.lasso_cancelled": "Lasso polygonal annulé",
        "canvas.lasso_selected": "Lasso polygonal : {pixels:,} pixels sélectionnés",
        "canvas.lasso_points_one": (
            "Lasso polygonal : {n} point — double-clic pour terminer · Échap = annuler"
        ),
        "canvas.lasso_points_many": (
            "Lasso polygonal : {n} points — double-clic pour terminer · Échap = annuler"
        ),
        "canvas.format_unsupported": "Format non pris en charge",
        "canvas.radius_positive": "Le rayon doit être > 0",
        "canvas.corners_rounded": "Coins arrondis : rayon de {r} px",
        "canvas.rotate_too_large": (
            "Une rotation de {degrees}° rendrait l'image trop grande "
            "({mp:.0f} Mpx) – maximum : {maximum} Mpx"
        ),
        "canvas.rotated": "{direction} Pivoté : {degrees}°  ({w} × {h} px)",
        "canvas.resized": "⇲ Redimensionné : {w} × {h} px",
        "canvas.resize_too_large": (
            "Taille cible {w} × {h} px trop grande ({mp:.0f} Mpx) – maximum : {maximum} Mpx"
        ),
        "canvas.color_adjusted": "🎨 Correction colorimétrique appliquée",
        "canvas.not_color_layer": "Aucun calque de couleur actif",
        "canvas.feathered": "🪶 Bord lissé : {radius} px",
        "canvas.flipped_h": "↔ Retourné horizontalement",
        "canvas.flipped_v": "↕ Retourné verticalement",
        "canvas.crop_cancelled": "Recadrage annulé",
        "canvas.crop_size": "⇲ Taille : {w} × {h} px",
        "canvas.crop_start_circle": (
            "✂  Déplacez le recadrage  [cercle]  —  puis cliquez sur ✓ Appliquer"
        ),
        "canvas.crop_start_ratio": (
            "✂  Déplacez le recadrage  [{w} × {h} px]  —  puis cliquez sur ✓ Appliquer"
        ),
        "canvas.cropped": "✂  Recadré : {w} × {h} px",
        "canvas.save_failed": "Échec de l'enregistrement : {error}",
        "canvas.saved": "💾 Enregistré : {name}",
        # History step descriptions
        "history.desc.generic": "Modification",
        "history.desc.original_restored": "🔄 Original restauré",
        "history.desc.bg_removed": "Arrière-plan supprimé",
        "history.desc.color_replaced": "Couleur remplacée ({color})",
        "history.desc.ai_bg": "Suppression de l'arrière-plan par IA",
        "history.desc.round_corners": "Coins arrondis ({r} px)",
        "history.desc.rotated": "{direction} Pivoté {degrees}°",
        "history.desc.resized": "Redimensionné ({w}×{h} px)",
        "history.desc.color_adjusted": "Correction colorimétrique",
        "history.desc.feathered": "Bord lissé ({radius} px)",
        "history.desc.crop_circle": "Format : cercle",
        "history.desc.crop_ratio": "Format : {w}×{h} px",
        # §9-Angleich rechte Spalte – KI/Export/Speichern (#436–#440)
        # Kurzlabel, damit der Primärbutton einzeilig bleibt (§5.4, #515);
        # der volle Wortlaut steht im Tooltip.
        "right_panel.ai.remove": "Supprimer le fond (IA)",
        "right_panel.ai.remove.tooltip": (
            "Supprimer l'arrière-plan automatiquement : séparer le sujet du fond par IA"),
        "right_panel.ai.remove.tooltip.warmup": (
            "Chargement du modèle IA… – le bouton sera bientôt actif"),
        "right_panel.ai.remove.tooltip.no_image": "Ouvrez d'abord une image",
        "right_panel.ai.remove.tooltip.processing": "L'IA traite déjà une image…",
        "right_panel.export.section.save": "Enregistrer",
        "right_panel.export.format_label": "Format de fichier",
        "right_panel.export.save": "Enregistrer l'image",
        "right_panel.export.save.tooltip": "Enregistrer le motif couleur comme image",
        "right_panel.export.section.uvprint": "Impression UV",
        "right_panel.export.eufymake": "Exporter les assets pour EufyMake Studio…",
        "right_panel.export.eufymake.tooltip": (
            "Exporter couleur, hauteur et gloss pour EufyMake Studio"),
        "workflow.open.recent": "Récemment ouverts",
        # Geführter Workflow – Schrittleiste, Inspector-Kopf, Navigation (Epic #418)
        "workflow.step.open": "Ouvrir",
        "workflow.step.cutout": "Détourer",
        "workflow.step.adjust": "Ajuster",
        "workflow.step.shape": "Forme & dimensions",
        "workflow.step.relief": "Relief & calques",
        "workflow.step.export": "Export",
        "workflow.title.open": "Étape 1 · Ouvrir",
        "workflow.title.cutout": "Étape 2 · Détourer",
        "workflow.title.adjust": "Étape 3 · Ajuster",
        "workflow.title.shape": "Étape 4 · Forme & dimensions",
        "workflow.title.relief": "Étape 5 · Relief & calques",
        "workflow.title.export": "Étape 6 · Export",
        "workflow.desc.open": "Charger une image — par glisser-déposer, dialogue ou récemment ouverts.",
        "workflow.desc.cutout": "Séparer le sujet de l'arrière-plan — automatiquement ou à la main.",
        "workflow.desc.adjust": "Luminosité, contraste et saturation avec aperçu en direct.",
        "workflow.desc.shape": "Pivoter, retourner, arrondir, recadrer et mettre à l'échelle.",
        "workflow.desc.relief": "Gérer les calques et la carte de hauteur pour l'impression en relief.",
        "workflow.desc.export": "Vérifier le résultat, enregistrer ou exporter pour EufyMake.",
        "workflow.next.open": "Suivant : Détourer →",
        "workflow.next.cutout": "Suivant : Ajuster →",
        "workflow.next.adjust": "Suivant : Forme & dimensions →",
        "workflow.next.shape": "Suivant : Relief & calques →",
        "workflow.next.relief": "Suivant : Export →",
        "workflow.next.export": "Exporter ✓",
        "workflow.back": "← Retour",
        "workflow.open.drop": "Glissez une image ici",
        "workflow.open.formats": "PNG · JPEG · WebP · TIFF · BMP · GIF",
        "workflow.open.button": "Ouvrir un fichier…",
        "workflow.locked": "Ouvrez d'abord une image (étape 1)",
        "workflow.status.step": "Étape {num}/{total} : {title}",
    },
    "uk": {
        # Status bar messages
        "status.no_image_loaded": "Зображення не завантажено",
        "status.no_image_to_save": "Немає зображення для збереження",
        "status.already_loading": "Зображення вже завантажується…",
        "status.load_result_discarded": (
            "Результат завантаження відхилено – зображення тим часом змінилося"
        ),
        "status.ai_already_running": "ШІ вже працює…",
        "status.ai_processing": "ШІ обробляє зображення… (може тривати кілька секунд)",
        "status.ai_ready": "ШІ готовий",
        "status.ai_model_loading": "Завантаження моделі ШІ…",
        "status.ai_warmup_failed": "⚠️ Не вдалося завантажити модель ШІ",
        "status.ai_warmup_cancelled": "Завантаження моделі ШІ скасовано",
        "status.ai_cancelling": "Скасування – очікування завершення ШІ…",
        "status.ai_cancelled": "Обробку ШІ скасовано",
        "status.ai_result_discarded": (
            "Результат ШІ відхилено – зображення тим часом змінилося"
        ),
        "status.wand_busy": "Чарівна паличка ще працює…",
        "status.selection_calculating": "⏳ Обчислення виділення…",
        "status.wand_discarded": (
            "Виділення палички відхилено – зображення тим часом змінилося"
        ),
        "status.no_selection": (
            "Немає виділення – спочатку виділіть область чарівною паличкою або пензлем"
        ),
        "status.start_hint": (
            "Відкрити зображення: Файл → Відкрити  або  перетягніть на робочу область"
        ),
        "status.quitting": "Завершення…",
        "status.shutdown_failed": (
            "Не вдалося завершити роботу – фоновий процес ще виконується"
        ),
        # Statusleisten-Meldungen mit interpolierten Werten
        "status.loading": "⏳ Завантаження: {name}…",
        "status.load_error": "Помилка завантаження: {msg}",
        "status.file_too_large": "Файл завеликий ({size} МБ) – максимум: {limit} МБ",
        "status.image_too_large": "Зображення завелике – максимум: {limit} Мпкс",
        "status.image_too_large_mp": "Зображення завелике ({mp:.0f} Мпкс) – максимум: {limit} Мпкс",
        "status.file_missing": "Файл більше не існує: {name}",
        "status.open_not_local": "Відкривати можна лише локальні файли.",
        "status.ai_error": "Помилка ШІ: {msg}",
        # Projektdatei (.bgrproj) – Lade-/Speicherfehler
        "project.error.corrupt": "Файл проєкту пошкоджено, або це не дійсний проєкт",
        "project.error.too_large": (
            "Файл проєкту завеликий ({size} МБ) – максимум: {limit} МБ"
        ),
        "project.error.manifest_missing": "Файл проєкту неповний: відсутній manifest.json",
        "project.error.manifest_invalid": "Файл проєкту пошкоджено: недійсний маніфест",
        "project.error.unsupported_version": (
            "Версія формату проєкту {version} не підтримується"
        ),
        "project.error.future_version": (
            "Цей проєкт створено в новішій версії BgRemover (формат v{version}; "
            "підтримується: v{supported}). Оновіть застосунок. Файл не було змінено."
        ),
        "project.error.unexpected_entry": (
            "Файл проєкту відхилено: неочікуваний запис «{name}»"
        ),
        "project.error.entry_too_large": (
            "Файл проєкту відхилено: запис «{name}» завеликий (у розпакованому вигляді)"
        ),
        "project.error.layer_file_missing": (
            "Файл проєкту неповний: відсутнє зображення шару «{file}»"
        ),
        "project.error.layer_too_large": (
            "Шар завеликий ({mp:.0f} Мпкс) – максимум: {limit} Мпкс"
        ),
        "project.error.layer_size_mismatch": (
            "Розмір шару {actual} не відповідає розміру полотна {expected}"
        ),
        "project.error.height16_invalid": (
            "Файл проєкту пошкоджено: 16-бітні дані висот «{file}» недійсні"
        ),
        "project.error.height16_integrity": (
            "Файл проєкту пошкоджено: перевірка цілісності «{file}» не пройдена "
            "(файл обрізано або переплутано)"
        ),
        "project.warning.role_normalized": (
            "Несумісну роль карти висот вилучено: «{name}» не є шаром висот"
        ),
        # EufyMake-Export – Konsistenzbefunde (#354)
        "eufymake.export.color_motif_missing": (
            "Відсутній колірний мотив: немає ролі COLOR_MOTIF і жодного колірного "
            "шару, що бере участь у композиті."
        ),
        "eufymake.export.optional_role_missing": (
            "Вибрана необов'язкова роль «{role_name}» не має шару."
        ),
        "eufymake.export.asset_size_mismatch": (
            "Розмір ресурсу {actual} не відповідає цільовому розміру {expected}."
        ),
        "eufymake.export.invalid_target_params": "Недійсні цільові параметри: {detail}",
        "eufymake.export.height_map_empty": (
            "Карта висот порожня або стала й може не дати рельєфу."
        ),
        "eufymake.export.gloss_mask_empty": (
            "Маска глянцю порожня або стала й може бути марною."
        ),
        "eufymake.export.bit_depth_unconfirmed": (
            "{bits}-бітна карта висот офіційно не підтверджена для EufyMake Studio."
        ),
        "eufymake.export.gloss_ink_mode": (
            "Глянець – лише допоміжний ресурс для імпорту: режим фарби та "
            "призначення шарів виконуються в EufyMake Studio."
        ),
        "eufymake.export.physical_size_unverified": (
            "Фізичний розмір і припущення піксель↔мм/DPI правдоподібні, але не є "
            "підтвердженим контрактом виробника."
        ),
        # Allgemeine Pre-Export-Prüfung (#379)
        "export.checks.dimensions_invalid": (
            "Недійсні розміри: {width}×{height} пкс – ширина та висота мають бути додатними."
        ),
        "export.checks.dimensions_too_large": (
            "Вивід завеликий: {mp} Мпкс перевищують ліміт {limit} Мпкс."
        ),
        "export.checks.color_space_unexpected": (
            "Неочікуваний колірний простір: {actual} (очікувався: {expected})."
        ),
        "export.checks.output_empty": "Порожній вивід: проєкт не містить шарів.",
        "export.checks.resolution_too_low": (
            "Низька роздільність: {dpi} DPI (рекомендований мінімум: {minimum} DPI)."
        ),
        "export.checks.resolution_too_high": (
            "Дуже висока роздільність: {dpi} DPI (рекомендований максимум: {maximum} DPI)."
        ),
        "export.checks.fully_transparent": (
            "Повністю прозоро: у виводі немає видимих пікселів."
        ),
        "export.checks.unexpected_alpha": (
            "Часткова прозорість: {percent}% пікселів напівпрозорі."
        ),
        "export.checks.print_area_exceeded": (
            "Мотив перевищує область друку: "
            "{width}×{height} мм > {medium_w}×{medium_h} мм."
        ),
        # Pre-Export-Prüfung beim normalen Speichern (#380)
        "export.check.error.title": "Зберегти неможливо",
        "export.check.blocked": (
            "Збереження перервано через такі проблеми:\n\n{details}"
        ),
        "export.check.warning.title": "Попередження перед збереженням",
        "export.check.confirm": (
            "Є попередження:\n\n{details}\n\nУсе одно зберегти?"
        ),
        # EufyMake-Export – Menü, Dialog & Meldungen (#355)
        "action.export_eufymake": "Експортувати ресурси для EufyMake Studio…",
        "eufymake.dialog.title": "Експорт ресурсів для EufyMake Studio",
        "eufymake.dialog.intro": (
            "BgRemover записує ресурси для імпорту в EufyMake Studio – не готовий "
            "проєкт «.empf». Потім імпортуйте й розмістіть їх у Studio, призначте "
            "там режими фарби/шари та збережіть проєкт самостійно як «.empf»."
        ),
        "eufymake.dialog.section.assets": "Ресурси",
        "eufymake.dialog.color_motif": "Колірний мотив (обов'язково)",
        "eufymake.dialog.color_motif.hint": (
            "RGBA-PNG з колірного композиту; прозорість зберігається."
        ),
        "eufymake.dialog.height": "Додати карту висот",
        "eufymake.dialog.height.hint": "PNG у відтінках сірого: світле = високо, темне = низько.",
        "eufymake.dialog.height.unavailable": "У проєкті немає шару висот.",
        "eufymake.dialog.gloss": "Додати маску глянцю (експериментально)",
        "eufymake.dialog.gloss.hint": (
            "Необов'язковий допоміжний ресурс. Режим фарби та призначення шарів "
            "виконуються в EufyMake Studio."
        ),
        "eufymake.dialog.gloss.unavailable": "У проєкті немає шару глянцю.",
        "eufymake.dialog.section.target": "Цільові параметри",
        "eufymake.dialog.bit_depth": "Бітність карти висот:",
        "eufymake.dialog.bit_depth.8": "8 біт (стандарт)",
        "eufymake.dialog.bit_depth.16": "16 біт (експериментально, не підтверджено)",
        "eufymake.dialog.size": "Цільовий розмір: {w} × {h} пкс",
        "eufymake.dialog.physical": "Фізичний розмір: {w} × {h} мм ({dpi} dpi)",
        "eufymake.dialog.physical.unset": "Фізичний розмір: не задано",
        "eufymake.dialog.section.dest": "Призначення",
        "eufymake.dialog.dest.label": "Тека експорту:",
        "eufymake.dialog.dest.placeholder": "Теку ще не вибрано",
        "eufymake.dialog.dest.is_file": (
            "Ціль – наявний файл; виберіть, будь ласка, теку."
        ),
        "eufymake.dialog.dest.browse": "Огляд…",
        "eufymake.dialog.dest.dialog_title": "Вибрати теку експорту",
        "eufymake.dialog.section.findings": "Перевірка",
        "eufymake.dialog.findings.ok": "Зауважень немає.",
        "eufymake.dialog.finding.error": "⛔  {msg}",
        "eufymake.dialog.finding.warning": "⚠️  {msg}",
        "eufymake.dialog.confirm_warnings": "Попередження зрозумілі – експортувати все одно",
        "eufymake.dialog.cancel": "Скасувати",
        "eufymake.dialog.export": "Експортувати",
        "eufymake.status.no_project": "Немає проєкту для експорту",
        "eufymake.status.cancelled": "Експорт скасовано",
        "eufymake.status.exported": "✅ Ресурси для EufyMake Studio експортовано: {path}",
        "eufymake.error.title": "Помилка експорту",
        "eufymake.error.write": "Помилка експорту: {error}",
        "eufymake.error.not_directory": (
            "Ціль «{path}» – наявний файл. Виберіть, будь ласка, теку як "
            "призначення експорту."
        ),
        "eufymake.error.blocked": "Експорт заблоковано – спочатку виправте:\n{details}",
        "eufymake.overwrite.title": "Перезаписати теку?",
        "eufymake.overwrite.body": "«{path}» вже існує. Замінити вміст?",
        "eufymake.success.title": "Експорт завершено",
        "eufymake.success.body": (
            "Ресурси для імпорту записано до:\n{path}\n\n"
            "Наступні кроки в EufyMake Studio:\n"
            "1. Імпортуйте та розмістіть ресурси.\n"
            "2. Призначте режими фарби/шари (напр., глянець/лак).\n"
            "3. Збережіть проєкт у Studio як «.empf»."
        ),
        # Ebenen-Panel & Projekt-Aktionen (#334)
        "layers.new_name": "Шар {n}",
        "layers.role.none": "Немає",
        "layers.role.color_motif": "Колірний мотив",
        "layers.role.height_map": "Карта висот",
        "layers.role.gloss": "Глянець",
        "layers.height_name": "Карта висот",
        "history.desc.layer_added": "Шар додано",
        "history.desc.layer_removed": "Шар видалено",
        "history.desc.layer_duplicated": "Шар здубльовано",
        "history.desc.layer_reordered": "Шар переміщено",
        "history.desc.layer_renamed": "Шар перейменовано",
        "history.desc.layer_active": "Активний шар змінено",
        "history.desc.layer_visibility": "Видимість змінено",
        "history.desc.layer_opacity": "Непрозорість змінено",
        "history.desc.layer_role": "Роль змінено",
        "history.desc.height_generated": "Карту висот згенеровано",
        "history.desc.height_imported": "Карту висот імпортовано",
        "history.desc.height_lighten": "Висоту підвищено",
        "history.desc.height_darken": "Висоту знижено",
        "history.desc.height_set": "Висоту задано",
        "history.desc.height_invert": "Висоту інвертовано",
        "history.desc.height_optimized": "Висоту оптимізовано",
        "canvas.layer_added": "Додано новий шар",
        "canvas.height_generated": "Карту висот згенеровано із зображення",
        "canvas.height_imported": "Карту висот імпортовано: {name}",
        "canvas.height_imported_16bit": (
            "Карту висот імпортовано: {name} (нативні 16 біт)"
        ),
        "right_panel.height.depth_info": (
            "Внутрішні дані висот: 16 біт (0–65535)"
        ),
        "eufymake.export.height_precision_loss": (
            "8-бітний експорт контрольовано квантує 16-бітні висоти до 256 "
            "рівнів – для повної точності оберіть 16 біт"
        ),
        "status.height_source_unsupported": (
            "Імпорт висот: режим зображення «{mode}» не підтримується"
        ),
        "status.height_import_failed": "Не вдалося імпортувати висоти",
        "right_panel.height.scale_hint": (
            "Шкала 0–255; пропорційно відображається на 16-бітний діапазон "
            "висот (0–65535)"
        ),
        "canvas.height_lightened": "Висоту підвищено",
        "canvas.height_darkened": "Висоту знижено",
        "canvas.height_set": "Висоту задано",
        "canvas.height_inverted": "Висоту інвертовано",
        "canvas.height_optimized": "Висоту оптимізовано",
        "canvas.height_op_error": "Операція з висотою не вдалася: {error}",
        "canvas.not_height_layer": "Немає активного шару висот",
        "canvas.role_incompatible": (
            "Роль «Карта висот» доступна лише для шарів висот"
        ),
        "canvas.layer_removed": "Шар видалено",
        "canvas.layer_duplicated": "Шар здубльовано",
        "canvas.cannot_delete_last": "Останній шар видалити неможливо",
        "right_panel.tab.layers": "Шари",
        "right_panel.tab.layers.tooltip": "Керування шарами",
        "right_panel.tab.height": "Висота",
        "right_panel.tab.height.tooltip": "Карта висот (рельєф)",
        "right_panel.tab.preview": "Перегляд",
        "right_panel.tab.preview.tooltip": "2D-показ кольору, рельєфу та глянцю",
        "right_panel.preview.section": "Режим 2D-перегляду",
        "right_panel.preview.hint": (
            "Перегляд не залежить від активного шару."
        ),
        "right_panel.preview.mode": "Показ:",
        "right_panel.preview.relief_strength": "Сила рельєфу:  {value} %",
        "right_panel.preview.relief_strength.tooltip": (
            "Сила тіньового відмивання в режимах «Рельєф» і «Комбіновано»"
        ),
        "right_panel.preview.gloss_visible": "Показувати глянець",
        "right_panel.preview.gloss_visible.tooltip": (
            "Показ або приховання полиску в режимах «Глянець» і «Комбіновано»"
        ),
        "right_panel.preview.export_hint": (
            "Лише показ – «Зберегти зображення», як і раніше, експортує тільки "
            "колірний мотив."
        ),
        "right_panel.height.section.acquire": "Отримати",
        "right_panel.height.section.edit": "Редагувати",
        "right_panel.height.section.optimize": "Оптимізувати",
        "right_panel.height.generate": "Згенерувати із зображення",
        "right_panel.height.generate.tooltip": (
            "Згенерувати карту висот із поточного зображення"
        ),
        "right_panel.height.import": "Імпортувати відтінки сірого…",
        "right_panel.height.import.tooltip": (
            "Імпортувати зображення у відтінках сірого як карту висот"
        ),
        "right_panel.height.hint": (
            "Інструменти висоти діють на активний шар висот."
        ),
        "right_panel.height.strength": "Сила",
        "right_panel.height.lighten": "Підвищити",
        "right_panel.height.lighten.tooltip": (
            "Підняти висоту у виділенні (інакше – глобально)"
        ),
        "right_panel.height.darken": "Знизити",
        "right_panel.height.darken.tooltip": (
            "Опустити висоту у виділенні (інакше – глобально)"
        ),
        "right_panel.height.set_value": "Значення",
        "right_panel.height.set": "Задати висоту",
        "right_panel.height.set.tooltip": (
            "Задати висоту на значення (виділення або глобально)"
        ),
        "right_panel.height.invert": "Інвертувати",
        "right_panel.height.invert.tooltip": (
            "Інвертувати висоту (виділення або глобально)"
        ),
        "right_panel.height.levels": "Рівні (чорний/білий)",
        "right_panel.height.gamma": "Гамма",
        "right_panel.height.gaussian": "Гаусове розмиття (радіус)",
        "right_panel.height.median": "Медіанне розмиття (радіус)",
        "right_panel.height.threshold": "Поріг",
        "right_panel.height.steps": "Сходинки",
        "right_panel.height.range": "Діапазон (мін/макс)",
        "right_panel.height.apply": "Застосувати",
        "right_panel.height.apply.tooltip": "Застосувати перегляд до шару висот",
        "right_panel.height.discard_preview": "Відхилити перегляд",
        "right_panel.height.discard_preview.tooltip": (
            "Відхилити перегляд без застосування"
        ),
        "right_panel.layers.section": "Шари",
        "right_panel.layers.add.tooltip": "Новий шар",
        "right_panel.layers.duplicate.tooltip": "Дублювати активний шар",
        "right_panel.layers.delete.tooltip": "Видалити активний шар",
        "right_panel.layers.move_up.tooltip": "Шар вище",
        "right_panel.layers.move_down.tooltip": "Шар нижче",
        "right_panel.layers.rename.tooltip": "Перейменувати активний шар",
        "right_panel.layers.role_label": "Роль:",
        "right_panel.layers.role.tooltip": (
            "Роль активного шару (для майбутніх інструментів УФ-друку)"
        ),
        "right_panel.layers.visible.tooltip": "Перемкнути видимість",
        "right_panel.layers.select.tooltip": "Зробити активним шаром",
        "right_panel.layers.opacity.tooltip": "Непрозорість (застосовується після відпускання)",
        "right_panel.layers.empty": (
            "Проєкт не завантажено – відкрийте зображення або «Новий проєкт»."
        ),
        "menu.project": "Проєкт",
        "action.new_project": "Новий проєкт",
        "action.open_project": "Відкрити проєкт…",
        "action.save_project": "Зберегти проєкт",
        "action.save_project_as": "Зберегти проєкт як…",
        "dialog.open_project.title": "Відкрити проєкт",
        "dialog.open_project.filter": "Проєкт BgRemover (*.bgrproj)",
        "dialog.save_project.title": "Зберегти проєкт",
        "dialog.rename.title": "Перейменувати шар",
        "dialog.rename.label": "Нова назва:",
        "dialog.import_height.title": "Імпортувати карту висот",
        "dialog.project_error.title": "Помилка проєкту",
        "project.new": "Новий проєкт створено",
        "project.saved": "Проєкт збережено: {name}",
        "project.opened": "Проєкт відкрито: {name}",
        "project.no_project": "Немає проєкту для збереження",
        "project.save_failed": "Не вдалося зберегти проєкт: {error}",
        # Main menu
        "menu.file": "Файл",
        "menu.recent_files": "Нещодавно відкриті",
        "menu.edit": "Редагування",
        "menu.view": "Вигляд",
        "menu.preview_mode": "Режим перегляду",
        "menu.extras": "Інструменти",
        "action.open": "Відкрити…",
        "action.save": "Зберегти",
        "action.save_as": "Зберегти як…",
        "action.undo": "Скасувати",
        "action.redo": "Повторити",
        "action.rotate_left_90": "Повернути на 90° ліворуч",
        "action.rotate_right_90": "Повернути на 90° праворуч",
        "action.rotate_180": "Повернути на 180°",
        "action.flip_horizontal": "Віддзеркалити горизонтально",
        "action.flip_vertical": "Віддзеркалити вертикально",
        "action.resize": "Змінити розмір…",
        "action.clear_selection": "Зняти виділення",
        "action.invert_selection": "Інвертувати виділення",
        "action.restore_original": "Відновити оригінал",
        "action.fit_to_view": "За розміром вікна",
        # Verlauf-Popup: Menü-Anker seit #458 (Rail-Button entfallen)
        "action.history": "Історія",
        # Zoom-Kontrolle auf der Arbeitsfläche (#464)
        "zoom.in.tooltip": "Збільшити (+10 %)",
        "zoom.out.tooltip": "Зменшити (−10 %)",
        "zoom.lock.tooltip": "Зафіксувати масштаб (зберегти поточне значення)",
        "zoom.unlock.tooltip": "Зняти фіксацію масштабу",
        "preview.mode.color": "Колір",
        "preview.mode.relief": "Рельєф поверх кольору",
        "preview.mode.height": "Висота (відтінки сірого)",
        "preview.mode.gloss": "Глянець",
        "preview.mode.combined": "Комбіновано",
        # Kurzlabels für das Segmented-Control der 2D-Vorschau (§9 Schritt 6)
        "preview.seg.color": "Колір",
        "preview.seg.relief": "Рельєф",
        "preview.seg.height": "Висота",
        "preview.seg.gloss": "Глянець",
        # 3D-перегляд рельєфу (Epic #582)
        "menu.view.show_3d": "Показати 3D-рельєф",
        "preview3d.section": "3D-перегляд рельєфу",
        "preview3d.display": "Відображення:",
        "preview3d.display.2d": "2D",
        "preview3d.display.3d": "3D",
        "preview3d.display.3d.disabled_tooltip": (
            "Для 3D потрібні карта висот із дійсними даними та OpenGL 2.1."
        ),
        "preview3d.exaggeration": "Перебільшення:  {value}×",
        "preview3d.exaggeration.hint": "Змінює лише відображення, ніколи дані висот.",
        "preview3d.light_azimuth": "Азимут світла:  {value}°",
        "preview3d.light_elevation": "Висота світла:  {value}°",
        "preview3d.quality": "Якість:",
        "preview3d.quality.reduced": "Знижена",
        "preview3d.quality.standard": "Стандартна",
        "preview3d.quality.high": "Висока",
        "preview3d.fit": "Вписати у вигляд",
        "preview3d.reset": "Скинути",
        "preview3d.empty": (
            "Карти висот ще немає. Створіть її на вкладці «Висота», щоб "
            "користуватися 3D-переглядом."
        ),
        "preview3d.unavailable": (
            "3D-перегляд недоступний: це середовище не надає OpenGL 2.1. "
            "2D-перегляд рельєфу залишається доступним."
        ),
        "preview3d.loading": "Обчислення 3D-перегляду…",
        "preview3d.ready_hint": (
            "3D-перегляд активний – збережені зображення та експорти не змінюються."
        ),
        "preview3d.decimated": "Спрощений вигляд 1:{factor}",
        "preview3d.error": (
            "3D-перегляд натрапив на графічну помилку. Ваше редагування, проєкт "
            "та експорт це не зачіпає."
        ),
        "preview3d.error.show_2d": "Показати 2D-рельєф",
        "preview3d.error.retry": "Спробувати ще раз",
        "preview3d.a11y.name": "3D-перегляд рельєфу",
        "preview3d.a11y.desc": (
            "Інтерактивна 3D-поверхня. Перетягуйте для обертання, колесо для "
            "масштабу, Alt+перетягування для панорами; стрілки обертають, Home вписує."
        ),
        # Design-Umschalter (Epic #424, Issue #428)
        "action.light_mode": "Світла тема",
        "theme.switched.light": "Світлу тему ввімкнено.",
        "theme.switched.dark": "Темну тему ввімкнено.",
        "action.settings": "Налаштування…",
        "action.check_for_updates": "Перевірити оновлення…",
        "action.manage_ai_model": "Керувати моделлю ШІ…",
        "action.install_ai_backend": "Встановити видалення фону через ШІ…",
        # App-Update-Check (#565)
        "status.update_check_running": "Перевірка оновлень…",
        "status.update_available_hint": (
            "🆕 Доступне оновлення: {version} – натисніть для деталей"
        ),
        "dialog.update_check.title": "Перевірка оновлень",
        "dialog.update_check.up_to_date.body": (
            "Ви вже використовуєте найновішу версію ({version})."
        ),
        "dialog.update_check.available.body": (
            "Доступна нова версія: {latest} (встановлено: {current})."
        ),
        "dialog.update_check.open_release": "Відкрити сторінку релізу",
        "dialog.update_check.failed.body": (
            "Перевірка оновлень не вдалася. Спробуйте пізніше."
        ),
        # KI-Modell-Verwaltung (#569)
        "ai_model.dialog.title": "Керування моделлю ШІ",
        "ai_model.status.downloaded": "Завантажено ({path}, {size})",
        "ai_model.status.not_downloaded": "Не завантажено",
        "ai_model.status.rembg_unavailable": (
            "Функція ШІ недоступна (rembg не встановлено)"
        ),
        "ai_model.status.python_hint": "Активне середовище Python: {path}",
        "ai_model.dialog.download": "Завантажити зараз",
        "ai_model.dialog.retry": "Повторити спробу",
        "ai_model.dialog.cancel": "Скасувати",
        "ai_model.dialog.close": "Закрити",
        "ai_model.dialog.cancelled": "Завантаження скасовано",
        # KI-Backend nachrüsten (Menü-Aktion ohne Auto-Install)
        "ai_install.dialog.title": "Встановлення видалення фону через ШІ",
        "ai_install.dialog.intro": (
            "У цій установці немає rembg (бекенду ШІ). Додаток нічого не "
            "встановлює автоматично: сучасні Linux-системи блокують pip у "
            "системний Python (PEP 668), а щойно встановлений пакет усе одно "
            "буде видно в запущеному процесі лише після перезапуску. Виконайте "
            "це в терміналі в теці проєкту:"
        ),
        "ai_install.dialog.venv_note": (
            'Уже у власному venv? Достатньо: pip install "rembg[cpu]"'
        ),
        "ai_install.dialog.already_installed": (
            "Примітка: rembg уже встановлено в поточному середовищі виконання."
        ),
        "ai_install.dialog.python_too_old": (
            "⚠ Активний Python {version} застарий для ШІ: rembg/onnxruntime "
            "потребують Python 3.11+. Спочатку встановіть новішу версію Python "
            "(наприклад, через Homebrew/pyenv/apt) і переконайтеся, що "
            "«python3» вказує на неї, перш ніж виконувати команду."
        ),
        "ai_install.dialog.copy": "Скопіювати команду",
        "ai_install.dialog.copied": "Скопійовано в буфер обміну.",
        # Left toolbar
        "toolbar.move.tooltip": (
            "Переміщення / Масштаб\n"
            "Перетягування лівою кнопкою зсуває вид · коліщатко масштабує"
        ),
        "toolbar.wand.tooltip": (
            "Чарівна паличка  (W)\n"
            "Клік виділяє область кольору (заливка)\n"
            "Shift = додати  ·  {modifier} = відняти"
        ),
        "toolbar.brush.tooltip": "Пензель  (B)\nДодавати області до виділення вручну",
        "toolbar.eraser.tooltip": "Гумка  (E)\nВилучати області з виділення",
        "toolbar.lasso.tooltip": (
            "Полігональне ласо  (L)\n"
            "Клік ставить точки · подвійний клік замикає полігон\n"
            "Shift = додати  ·  {modifier} = відняти  ·  Esc = скасувати"
        ),
        "toolbar.height_lighten.tooltip": (
            "Підвищити (вище)\n"
            "Мазок піднімає висоту активного шару висот"
        ),
        "toolbar.height_darken.tooltip": (
            "Знизити (нижче)\n"
            "Мазок опускає висоту активного шару висот"
        ),
        "toolbar.height_tools.disabled.tooltip": (
            "Інструмент висоти\n"
            "Спочатку активуйте шар висот (крок 5: згенеруйте/імпортуйте карту висот)"
        ),
        "toolbar.ai.missing.tooltip": (
            'rembg не встановлено\n→ python3 -m pip install -e ".[ai]"'
        ),
        "toolbar.undo.tooltip": (
            "Скасувати  ({shortcut})\n"
            "Скасувати останній крок редагування"
        ),
        "toolbar.redo.tooltip": (
            "Повторити  ({shortcut})\n"
            "Повторити останній скасований крок"
        ),
        "toolbar.theme.to_light.tooltip": "Перейти до світлої теми",
        "toolbar.theme.to_dark.tooltip": "Перейти до темної теми",
        # Right panel tabs
        "right_panel.tab.selection": "Виділення",
        "right_panel.tab.selection.tooltip": (
            "Виділення – чарівна паличка, пензель, гумка"
        ),
        "right_panel.tab.background": "Фон",
        "right_panel.tab.background.tooltip": (
            "Фон – вилучити, замінити колір"
        ),
        "right_panel.tab.adjust": "Корекція",
        "right_panel.tab.adjust.tooltip": (
            "Корекція кольору – яскравість, контраст, насиченість"
        ),
        "right_panel.tab.transform": "Поворот/Дзеркало",
        "right_panel.tab.transform.tooltip": "Трансформація – поворот, віддзеркалення",
        "right_panel.tab.shape": "Форма",
        "right_panel.tab.shape.tooltip": (
            "Форма й обрізання – заокруглення кутів, вибір формату"
        ),
        # History popup
        "history.window_title": "Історія змін",
        "history.hint": "Подвійний клік на записі → повернутися до цього кроку",
        "history.list.tooltip": (
            "Історія всіх кроків редагування.\n"
            "Подвійний клік на записі повертає до цього кроку."
        ),
        # Crop bar
        "crop_bar.label": "✂  Розмістіть кадр, потім підтвердьте:",
        "crop_bar.confirm": "✓  Застосувати обрізання",
        "crop_bar.cancel": "✗  Скасувати",
        # Right panel — Selection tab contents
        "right_panel.selection.section.settings": "Налаштування інструмента",
        "right_panel.selection.section.select": "Виділення",
        "right_panel.selection.tolerance": "Допуск (чарівна паличка):  {value}",
        "right_panel.selection.tolerance.tooltip": (
            "Керує тим, наскільки схожими мають бути кольори для виділення.\n"
            "Низький = лише дуже схожі кольори · Високий = багато відтінків"
        ),
        "right_panel.selection.brush_size": "Розмір пензля:  {value} пкс",
        "right_panel.selection.brush_size.tooltip": (
            "Розмір інструмента пензель/гумка в пікселях"
        ),
        "right_panel.selection.clear": "Зняти",
        "right_panel.selection.clear.tooltip": (
            "Знімає поточне виділення (також: клавіша Esc)"
        ),
        "right_panel.selection.invert": "Інвертувати",
        "right_panel.selection.invert.tooltip": (
            "Міняє місцями виділені та невиділені області  ({modifier}+Shift+I)"
        ),
        "right_panel.selection.morph.label": "Радіус:",
        "right_panel.selection.morph.tooltip": (
            "Радіус у пікселях для розширення/звуження виділення"
        ),
        "right_panel.selection.expand": "+ Розширити",
        "right_panel.selection.expand.tooltip": (
            "Розширює виділення на заданий радіус"
        ),
        "right_panel.selection.shrink": "− Звузити",
        "right_panel.selection.shrink.tooltip": (
            "Звужує виділення на заданий радіус"
        ),
        # Right panel — Background tab contents
        "right_panel.background.section": "Редагувати фон",
        "right_panel.background.remove": "Вилучити (прозоро)",
        "right_panel.background.remove.tooltip": (
            "Робить виділену область повністю прозорою.\n"
            "Порада: спочатку виділіть фон чарівною паличкою."
        ),
        "right_panel.background.color_label": "Виберіть колір і заповніть виділення:",
        "right_panel.background.color.tooltip": "Клацніть, щоб вибрати колір фону для заміни",
        "right_panel.background.replace": "Замінити колір",
        "right_panel.background.replace.tooltip": (
            "Заповнює виділену область вибраним кольором"
        ),
        "right_panel.background.section.feather": "Згладити край",
        "right_panel.background.feather_hint": (
            "Розмиває край вирізання (лише альфа)."
        ),
        "right_panel.background.feather_radius": "Радіус:  {value} пкс",
        "right_panel.background.feather_radius.tooltip": (
            "Радіус згладжування краю в пікселях (0 = вимкнено)"
        ),
        "right_panel.background.feather": "Згладити край",
        "right_panel.background.feather.tooltip": (
            "Розмити альфа-край активного шару (виділення або глобально)"
        ),
        # Right panel — Transform tab contents
        "right_panel.transform.section.rotate": "Поворот",
        "right_panel.transform.quick_label": "Швидкий поворот:",
        "right_panel.transform.rotate_left_90": "↺ 90° ліворуч",
        "right_panel.transform.rotate_left_90.tooltip": "Повернути на 90° проти годинникової стрілки",
        "right_panel.transform.rotate_right_90": "↻ 90° праворуч",
        "right_panel.transform.rotate_right_90.tooltip": "Повернути на 90° за годинниковою стрілкою",
        "right_panel.transform.rotate_180": "↺ 180°",
        "right_panel.transform.rotate_180.tooltip": "Повернути зображення на 180°",
        "right_panel.transform.rotate_270": "↺ 270°",
        "right_panel.transform.rotate_270.tooltip": "270° проти годинникової (= 90° праворуч)",
        "right_panel.transform.free_label": "Довільний кут:",
        "right_panel.transform.angle_slider.tooltip": "Задати кут повороту: від −180° до +180°",
        "right_panel.transform.angle_spin.tooltip": "Ввести кут повороту напряму",
        "right_panel.transform.apply_angle": "Застосувати кут",
        "right_panel.transform.apply_angle.tooltip": (
            "Повертає зображення на заданий кут.\n"
            "Похилі кути створюють прозорі кути зображення."
        ),
        "right_panel.transform.section.flip": "Віддзеркалення",
        "right_panel.transform.flip_h": "Горизонтально",
        "right_panel.transform.flip_h.tooltip": "Віддзеркалити зображення горизонтально (ліво ↔ право)",
        "right_panel.transform.flip_v": "Вертикально",
        "right_panel.transform.flip_v.tooltip": "Віддзеркалити зображення вертикально (верх ↕ низ)",
        # Größe-ändern-Dialog (#359)
        "resize.title": "Змінити розмір",
        "resize.width": "Ширина",
        "resize.height": "Висота",
        "resize.link_aspect": "Зберігати пропорції",
        "resize.resample.label": "Метод:",
        "resize.resample.lanczos": "Ланцош (найкраща якість)",
        "resize.resample.bicubic": "Бікубічний",
        "resize.resample.bilinear": "Білінійний",
        "resize.resample.nearest": "Найближчий сусід",
        "resize.megapixels": "{mp:.1f} Мпкс (максимум: {maximum} Мпкс)",
        "resize.ok": "Застосувати",
        "resize.cancel": "Скасувати",
        # mm/DPI-Modus + Druckflächenprüfung (#377)
        "resize.mode.label": "Одиниця:",
        "resize.mode.pixel": "Пікселі",
        "resize.mode.mm": "Міліметри (мм + DPI)",
        "resize.width_mm": "Ширина",
        "resize.height_mm": "Висота",
        "resize.dpi": "Роздільність",
        "resize.medium.label": "Цільовий носій:",
        "resize.pixels_result": "Результат: {width}×{height} пкс ({mp} Мпкс)",
        "resize.print_area_ok": "Вміщується на {medium} ({medium_w}×{medium_h} мм).",
        "resize.print_area_exceeded": (
            "⚠ Мотив {width}×{height} мм перевищує {medium} "
            "({medium_w}×{medium_h} мм)."
        ),
        # Right panel — Adjust tab contents (#360)
        "right_panel.adjust.section": "Корекція кольору",
        "right_panel.adjust.hint": "Діє на активний колірний шар.",
        "right_panel.adjust.brightness": "Яскравість:  {value} %",
        "right_panel.adjust.brightness.tooltip": (
            "Яскравість активного колірного шару (100 % = без змін)"
        ),
        "right_panel.adjust.contrast": "Контраст:  {value} %",
        "right_panel.adjust.contrast.tooltip": (
            "Контраст активного колірного шару (100 % = без змін)"
        ),
        "right_panel.adjust.saturation": "Насиченість:  {value} %",
        "right_panel.adjust.saturation.tooltip": (
            "Насиченість активного колірного шару (0 % = відтінки сірого, 100 % = без змін)"
        ),
        "right_panel.adjust.reset": "Скинути",
        "right_panel.adjust.reset.tooltip": (
            "Скинути повзунки на 100 % і відхилити перегляд"
        ),
        "right_panel.adjust.apply": "Застосувати",
        "right_panel.adjust.apply.tooltip": (
            "Застосувати корекцію кольору до активного колірного шару"
        ),
        # Right panel — Shape tab contents
        "right_panel.shape.section.corner": "Заокруглити кути",
        "right_panel.shape.radius": "Радіус:  {value} пкс",
        "right_panel.shape.radius.tooltip": (
            "Радіус заокруглення кутів у пікселях.\n"
            "0 = без заокруглення · 500 = максимально кругло"
        ),
        "right_panel.shape.round": "Заокруглити кути",
        "right_panel.shape.round.tooltip": (
            "Застосовує заокруглення кутів.\n"
            "Результат зберігається як PNG із прозорими кутами."
        ),
        "right_panel.shape.section.resize": "Змінити розмір",
        "right_panel.shape.resize_apply": "Застосувати розмір",
        "right_panel.shape.resize_apply.tooltip": "Масштабувати до введеного розміру",
        "right_panel.shape.section.format": "Формат обрізання",
        "right_panel.shape.circle": "⬤  Коло",
        "right_panel.shape.circle.tooltip": "Розмістити круглий кадр і застосувати обрізання",
        # Settings dialog
        "settings.title": "Налаштування",
        "settings.open_dir.label": "Типова тека для відкриття",
        "settings.save_dir.label": "Типова тека для експорту / збереження",
        "settings.dir.placeholder": "Порожньо = остання використана тека",
        "settings.format.label": "Бажаний формат файлів зображень",
        "settings.log.label": "Файл журналу",
        "settings.log.tooltip": "Шлях до файлу журналу (виділіть, щоб скопіювати)",
        "settings.log.open_button": "Відкрити теку",
        "settings.log.open_failed": "Не вдалося відкрити теку:\n{target}",
        "settings.update.auto_check.label": (
            "Автоматично перевіряти оновлення під час запуску"
        ),
        "settings.cancel": "Скасувати",
        "settings.ok": "OK",
        "settings.pick_open.title": "Вибрати теку для відкриття",
        "settings.pick_save.title": "Вибрати теку для експорту/збереження",
        "settings.invalid_dir.title": "Недійсна тека",
        "settings.invalid_dir.body": "{label} не є наявною текою:\n{value}",
        "settings.language.label": "Мова",
        "settings.language.restart_title": "Потрібен перезапуск",
        "settings.language.restart_hint": (
            "Зміна мови набуде чинності після наступного запуску."
        ),
        # Dialogs (QMessageBox)
        "dialog.ai_error.title": "Помилка ШІ",
        "dialog.ai_error.body": (
            "Помилка під час автоматичного вилучення фону:\n\n{msg}"
        ),
        # Main-window dialogs
        "dialog.unsaved.title": "Незбережені зміни",
        "dialog.unsaved.body": (
            "Зображення було змінено. Зберегти зміни, перш ніж відхилити їх?"
        ),
        "dialog.open.title": "Відкрити зображення",
        "dialog.open.filter": (
            "Зображення (*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.tif *.gif);;"
            "Усі файли (*)"
        ),
        "dialog.save.title": "Зберегти зображення як…",
        "dialog.color.title": "Вибрати колір фону",
        # Canvas status messages
        "canvas.opened": "Відкрито: {name}  ({w} × {h} пкс)",
        "canvas.opened_extra": (
            "Відкрито: {name}  (проігноровано ще файлів: {extra})"
        ),
        "canvas.undo_none": "Більше нічого скасовувати",
        "canvas.undo_done": "↩  Скасовано: {desc}",
        "canvas.redo_none": "Більше нічого повторювати",
        "canvas.redo_done": "↪  Повторено: {desc}",
        "canvas.undo_to": "↩  Скасовано кроків: {steps}  (до: {desc})",
        "canvas.original_restored": "🔄  Оригінал відновлено",
        "canvas.selection_cleared": "Виділення знято",
        "canvas.selection_inverted": "Виділення інвертовано: {pixels:,} пкс",
        "canvas.selection_expanded": "Виділення розширено на {radius} пкс: {pixels:,} пкс",
        "canvas.selection_shrunk": "Виділення звужено на {radius} пкс: {pixels:,} пкс",
        "canvas.bg_removed": "Фон вилучено (прозоро)",
        "canvas.remove_error": "Помилка вилучення: {error}",
        "canvas.bg_replaced": "Фон замінено: {color}",
        "canvas.replace_error": "Помилка заміни: {error}",
        "canvas.ai_done": "✅ Вилучення фону ШІ завершено",
        "canvas.selection_pixels": "Виділення: {pixels:,} пкс",
        "canvas.selection_error": "Помилка виділення: {msg}",
        "canvas.lasso_cancelled": "Полігональне ласо скасовано",
        "canvas.lasso_selected": "Полігональне ласо: виділено {pixels:,} пкс",
        "canvas.lasso_points_one": (
            "Полігональне ласо: {n} точка — подвійний клік завершує · Esc = скасувати"
        ),
        "canvas.lasso_points_many": (
            "Полігональне ласо: точок: {n} — подвійний клік завершує · Esc = скасувати"
        ),
        "canvas.format_unsupported": "Формат не підтримується",
        "canvas.radius_positive": "Радіус має бути > 0",
        "canvas.corners_rounded": "Кути заокруглено: радіус {r} пкс",
        "canvas.rotate_too_large": (
            "Поворот на {degrees}° зробив би зображення завеликим "
            "({mp:.0f} Мпкс) – максимум: {maximum} Мпкс"
        ),
        "canvas.rotated": "{direction} Повернуто: {degrees}°  ({w} × {h} пкс)",
        "canvas.resized": "⇲ Розмір змінено: {w} × {h} пкс",
        "canvas.resize_too_large": (
            "Цільовий розмір {w} × {h} пкс завеликий ({mp:.0f} Мпкс) – максимум: {maximum} Мпкс"
        ),
        "canvas.color_adjusted": "🎨 Корекцію кольору застосовано",
        "canvas.not_color_layer": "Немає активного колірного шару",
        "canvas.feathered": "🪶 Край згладжено: {radius} пкс",
        "canvas.flipped_h": "↔ Віддзеркалено горизонтально",
        "canvas.flipped_v": "↕ Віддзеркалено вертикально",
        "canvas.crop_cancelled": "Обрізання скасовано",
        "canvas.crop_size": "⇲ Розмір: {w} × {h} пкс",
        "canvas.crop_start_circle": (
            "✂  Пересуньте кадр  [коло]  —  потім натисніть ✓ Застосувати"
        ),
        "canvas.crop_start_ratio": (
            "✂  Пересуньте кадр  [{w} × {h} пкс]  —  потім натисніть ✓ Застосувати"
        ),
        "canvas.cropped": "✂  Обрізано: {w} × {h} пкс",
        "canvas.save_failed": "Не вдалося зберегти: {error}",
        "canvas.saved": "💾 Збережено: {name}",
        # History step descriptions
        "history.desc.generic": "Редагування",
        "history.desc.original_restored": "🔄 Оригінал відновлено",
        "history.desc.bg_removed": "Фон вилучено",
        "history.desc.color_replaced": "Колір замінено ({color})",
        "history.desc.ai_bg": "Вилучення фону ШІ",
        "history.desc.round_corners": "Кути заокруглено ({r} пкс)",
        "history.desc.rotated": "{direction} Повернуто {degrees}°",
        "history.desc.resized": "Розмір змінено ({w}×{h} пкс)",
        "history.desc.color_adjusted": "Корекція кольору",
        "history.desc.feathered": "Край згладжено ({radius} пкс)",
        "history.desc.crop_circle": "Формат: коло",
        "history.desc.crop_ratio": "Формат: {w}×{h} пкс",
        # §9-Angleich rechte Spalte – KI/Export/Speichern (#436–#440)
        # Kurzlabel, damit der Primärbutton einzeilig bleibt (§5.4, #515);
        # der volle Wortlaut steht im Tooltip.
        "right_panel.ai.remove": "Вилучити фон (ШІ)",
        "right_panel.ai.remove.tooltip": (
            "Вилучити фон автоматично: відділити мотив від фону за допомогою ШІ"),
        "right_panel.ai.remove.tooltip.warmup": (
            "Завантаження моделі ШІ… – кнопка стане активною незабаром"),
        "right_panel.ai.remove.tooltip.no_image": "Спершу відкрийте зображення",
        "right_panel.ai.remove.tooltip.processing": "ШІ вже обробляє зображення…",
        "right_panel.export.section.save": "Збереження",
        "right_panel.export.format_label": "Формат файлу",
        "right_panel.export.save": "Зберегти зображення",
        "right_panel.export.save.tooltip": "Зберегти колірний мотив як зображення",
        "right_panel.export.section.uvprint": "УФ-друк",
        "right_panel.export.eufymake": "Експортувати ресурси для EufyMake Studio…",
        "right_panel.export.eufymake.tooltip": (
            "Експортувати колір, висоту та глянець для EufyMake Studio"),
        "workflow.open.recent": "Нещодавно відкриті",
        # Geführter Workflow – Schrittleiste, Inspector-Kopf, Navigation (Epic #418)
        "workflow.step.open": "Відкрити",
        "workflow.step.cutout": "Вилучити фон",
        "workflow.step.adjust": "Корекція",
        "workflow.step.shape": "Форма й розміри",
        "workflow.step.relief": "Рельєф і шари",
        "workflow.step.export": "Експорт",
        "workflow.title.open": "Крок 1 · Відкрити",
        "workflow.title.cutout": "Крок 2 · Вилучити фон",
        "workflow.title.adjust": "Крок 3 · Корекція",
        "workflow.title.shape": "Крок 4 · Форма й розміри",
        "workflow.title.relief": "Крок 5 · Рельєф і шари",
        "workflow.title.export": "Крок 6 · Експорт",
        "workflow.desc.open": "Завантажте зображення — перетягуванням, через діалог або з нещодавно відкритих.",
        "workflow.desc.cutout": "Відділіть мотив від фону — автоматично або вручну.",
        "workflow.desc.adjust": "Яскравість, контраст і насиченість із живим переглядом.",
        "workflow.desc.shape": "Поворот, віддзеркалення, заокруглення, обрізання та масштабування.",
        "workflow.desc.relief": "Керуйте шарами та картою висот для рельєфного друку.",
        "workflow.desc.export": "Перевірте результат, збережіть або експортуйте для EufyMake.",
        "workflow.next.open": "Далі: Вилучити фон →",
        "workflow.next.cutout": "Далі: Корекція →",
        "workflow.next.adjust": "Далі: Форма й розміри →",
        "workflow.next.shape": "Далі: Рельєф і шари →",
        "workflow.next.relief": "Далі: Експорт →",
        "workflow.next.export": "Експортувати ✓",
        "workflow.back": "← Назад",
        "workflow.open.drop": "Перетягніть зображення сюди",
        "workflow.open.formats": "PNG · JPEG · WebP · TIFF · BMP · GIF",
        "workflow.open.button": "Відкрити файл…",
        "workflow.locked": "Спочатку відкрийте зображення (крок 1)",
        "workflow.status.step": "Крок {num}/{total}: {title}",
    },
    "zh": {
        # Status bar messages
        "status.no_image_loaded": "未加载图像",
        "status.no_image_to_save": "没有可保存的图像",
        "status.already_loading": "正在加载图像…",
        "status.load_result_discarded": (
            "加载结果已丢弃——图像在此期间已更改"
        ),
        "status.ai_already_running": "AI 已在运行…",
        "status.ai_processing": "AI 正在处理图像…（可能需要几秒钟）",
        "status.ai_ready": "AI 就绪",
        "status.ai_model_loading": "正在加载 AI 模型…",
        "status.ai_warmup_failed": "⚠️ 无法加载 AI 模型",
        "status.ai_warmup_cancelled": "AI 模型下载已取消",
        "status.ai_cancelling": "正在取消——等待运行中的 AI…",
        "status.ai_cancelled": "AI 处理已取消",
        "status.ai_result_discarded": (
            "AI 结果已丢弃——图像在此期间已更改"
        ),
        "status.wand_busy": "魔棒仍在工作…",
        "status.selection_calculating": "⏳ 正在计算选区…",
        "status.wand_discarded": (
            "魔棒选区已丢弃——图像在此期间已更改"
        ),
        "status.no_selection": (
            "没有选区——请先用魔棒或画笔选择一个区域"
        ),
        "status.start_hint": (
            "打开图像：文件 → 打开  或  拖放到工作区"
        ),
        "status.quitting": "正在退出…",
        "status.shutdown_failed": (
            "无法退出——仍有后台进程在运行"
        ),
        # Statusleisten-Meldungen mit interpolierten Werten
        "status.loading": "⏳ 正在加载：{name}…",
        "status.load_error": "加载错误：{msg}",
        "status.file_too_large": "文件过大（{size} MB）——上限：{limit} MB",
        "status.image_too_large": "图像过大——上限：{limit} MP",
        "status.image_too_large_mp": "图像过大（{mp:.0f} MP）——上限：{limit} MP",
        "status.file_missing": "文件已不存在：{name}",
        "status.open_not_local": "只能打开本地文件。",
        "status.ai_error": "AI 错误：{msg}",
        # Projektdatei (.bgrproj) – Lade-/Speicherfehler
        "project.error.corrupt": "项目文件已损坏或不是有效的项目",
        "project.error.too_large": (
            "项目文件过大（{size} MB）——上限：{limit} MB"
        ),
        "project.error.manifest_missing": "项目文件不完整：缺少 manifest.json",
        "project.error.manifest_invalid": "项目文件已损坏：清单无效",
        "project.error.unsupported_version": (
            "不支持项目格式版本 {version}"
        ),
        "project.error.future_version": (
            "此项目由较新版本的 BgRemover 创建（格式 v{version}；支持至 "
            "v{supported}）。请更新应用程序。文件未被修改。"
        ),
        "project.error.unexpected_entry": (
            "项目文件被拒绝：意外条目“{name}”"
        ),
        "project.error.entry_too_large": (
            "项目文件被拒绝：条目“{name}”过大（解压后）"
        ),
        "project.error.layer_file_missing": (
            "项目文件不完整：缺少图层图像“{file}”"
        ),
        "project.error.layer_too_large": (
            "图层过大（{mp:.0f} MP）——上限：{limit} MP"
        ),
        "project.error.layer_size_mismatch": (
            "图层尺寸 {actual} 与画布尺寸 {expected} 不匹配"
        ),
        "project.error.height16_invalid": (
            "项目文件已损坏：16 位高度数据“{file}”无效"
        ),
        "project.error.height16_integrity": (
            "项目文件已损坏：“{file}”的完整性校验失败（文件被截断或调换）"
        ),
        "project.warning.role_normalized": (
            "已移除不兼容的高度图角色：“{name}”不是高度图层"
        ),
        # EufyMake-Export – Konsistenzbefunde (#354)
        "eufymake.export.color_motif_missing": (
            "缺少颜色图案：没有 COLOR_MOTIF 角色，也没有参与合成的颜色图层。"
        ),
        "eufymake.export.optional_role_missing": (
            "所选的可选角色“{role_name}”没有图层。"
        ),
        "eufymake.export.asset_size_mismatch": (
            "素材尺寸 {actual} 与目标尺寸 {expected} 不匹配。"
        ),
        "eufymake.export.invalid_target_params": "目标参数无效：{detail}",
        "eufymake.export.height_map_empty": (
            "高度图为空或恒定，可能不会产生浮雕。"
        ),
        "eufymake.export.gloss_mask_empty": (
            "光泽蒙版为空或恒定，可能没有用处。"
        ),
        "eufymake.export.bit_depth_unconfirmed": (
            "{bits} 位高度图尚未获得 EufyMake Studio 官方确认。"
        ),
        "eufymake.export.gloss_ink_mode": (
            "光泽只是导入辅助素材——墨水模式和图层分配在 EufyMake Studio 中完成。"
        ),
        "eufymake.export.physical_size_unverified": (
            "物理尺寸及像素↔毫米/DPI 假设合理，但并非经确认的厂商约定。"
        ),
        # Allgemeine Pre-Export-Prüfung (#379)
        "export.checks.dimensions_invalid": (
            "尺寸无效：{width}×{height} px——宽度和高度必须为正值。"
        ),
        "export.checks.dimensions_too_large": (
            "输出过大：{mp} MP 超出 {limit} MP 的上限。"
        ),
        "export.checks.color_space_unexpected": (
            "颜色空间异常：{actual}（应为：{expected}）。"
        ),
        "export.checks.output_empty": "输出为空：项目不包含任何图层。",
        "export.checks.resolution_too_low": (
            "分辨率偏低：{dpi} DPI（建议最低：{minimum} DPI）。"
        ),
        "export.checks.resolution_too_high": (
            "分辨率过高：{dpi} DPI（建议最高：{maximum} DPI）。"
        ),
        "export.checks.fully_transparent": (
            "完全透明：输出中没有可见像素。"
        ),
        "export.checks.unexpected_alpha": (
            "部分透明：{percent}% 的像素为半透明。"
        ),
        "export.checks.print_area_exceeded": (
            "图案超出打印区域："
            "{width}×{height} mm > {medium_w}×{medium_h} mm。"
        ),
        # Pre-Export-Prüfung beim normalen Speichern (#380)
        "export.check.error.title": "无法保存",
        "export.check.blocked": (
            "由于以下问题，保存已中止：\n\n{details}"
        ),
        "export.check.warning.title": "保存前的警告",
        "export.check.confirm": (
            "存在警告：\n\n{details}\n\n仍要保存吗？"
        ),
        # EufyMake-Export – Menü, Dialog & Meldungen (#355)
        "action.export_eufymake": "导出 EufyMake Studio 素材…",
        "eufymake.dialog.title": "导出 EufyMake Studio 素材",
        "eufymake.dialog.intro": (
            "BgRemover 写出的是供 EufyMake Studio 导入的素材，而不是成品“.empf”项目。"
            "请随后在 Studio 中导入并摆放这些素材，在那里分配墨水模式/图层，"
            "并自行将项目保存为“.empf”。"
        ),
        "eufymake.dialog.section.assets": "素材",
        "eufymake.dialog.color_motif": "颜色图案（必需）",
        "eufymake.dialog.color_motif.hint": (
            "来自颜色合成的 RGBA PNG；透明度保持不变。"
        ),
        "eufymake.dialog.height": "包含高度图",
        "eufymake.dialog.height.hint": "灰度 PNG：亮 = 高，暗 = 低。",
        "eufymake.dialog.height.unavailable": "项目中没有高度图层。",
        "eufymake.dialog.gloss": "包含光泽蒙版（实验性）",
        "eufymake.dialog.gloss.hint": (
            "可选的辅助素材。墨水模式和图层分配在 EufyMake Studio 中完成。"
        ),
        "eufymake.dialog.gloss.unavailable": "项目中没有光泽图层。",
        "eufymake.dialog.section.target": "目标参数",
        "eufymake.dialog.bit_depth": "高度图位深：",
        "eufymake.dialog.bit_depth.8": "8 位（标准）",
        "eufymake.dialog.bit_depth.16": "16 位（实验性，未经确认）",
        "eufymake.dialog.size": "目标尺寸：{w} × {h} px",
        "eufymake.dialog.physical": "物理尺寸：{w} × {h} mm（{dpi} dpi）",
        "eufymake.dialog.physical.unset": "物理尺寸：未设置",
        "eufymake.dialog.section.dest": "目标位置",
        "eufymake.dialog.dest.label": "导出文件夹：",
        "eufymake.dialog.dest.placeholder": "尚未选择文件夹",
        "eufymake.dialog.dest.is_file": (
            "目标是一个已存在的文件——请选择一个文件夹。"
        ),
        "eufymake.dialog.dest.browse": "浏览…",
        "eufymake.dialog.dest.dialog_title": "选择导出文件夹",
        "eufymake.dialog.section.findings": "检查",
        "eufymake.dialog.findings.ok": "未发现问题。",
        "eufymake.dialog.finding.error": "⛔  {msg}",
        "eufymake.dialog.finding.warning": "⚠️  {msg}",
        "eufymake.dialog.confirm_warnings": "我已了解警告——仍要导出",
        "eufymake.dialog.cancel": "取消",
        "eufymake.dialog.export": "导出",
        "eufymake.status.no_project": "没有可导出的项目",
        "eufymake.status.cancelled": "导出已取消",
        "eufymake.status.exported": "✅ 已为 EufyMake Studio 导出素材：{path}",
        "eufymake.error.title": "导出失败",
        "eufymake.error.write": "导出失败：{error}",
        "eufymake.error.not_directory": (
            "目标“{path}”是一个已存在的文件。请选择一个文件夹作为导出目标。"
        ),
        "eufymake.error.blocked": "导出被阻止——请先修正：\n{details}",
        "eufymake.overwrite.title": "覆盖文件夹？",
        "eufymake.overwrite.body": "“{path}”已存在。要替换其内容吗？",
        "eufymake.success.title": "导出完成",
        "eufymake.success.body": (
            "导入素材已写入：\n{path}\n\n"
            "在 EufyMake Studio 中的后续步骤：\n"
            "1. 导入并摆放素材。\n"
            "2. 分配墨水模式/图层（例如光泽/上光油）。\n"
            "3. 在 Studio 中将项目保存为“.empf”。"
        ),
        # Ebenen-Panel & Projekt-Aktionen (#334)
        "layers.new_name": "图层 {n}",
        "layers.role.none": "无",
        "layers.role.color_motif": "颜色图案",
        "layers.role.height_map": "高度图",
        "layers.role.gloss": "光泽",
        "layers.height_name": "高度图",
        "history.desc.layer_added": "已添加图层",
        "history.desc.layer_removed": "已删除图层",
        "history.desc.layer_duplicated": "已复制图层",
        "history.desc.layer_reordered": "已移动图层",
        "history.desc.layer_renamed": "已重命名图层",
        "history.desc.layer_active": "已切换活动图层",
        "history.desc.layer_visibility": "已更改可见性",
        "history.desc.layer_opacity": "已更改不透明度",
        "history.desc.layer_role": "已更改角色",
        "history.desc.height_generated": "已生成高度图",
        "history.desc.height_imported": "已导入高度图",
        "history.desc.height_lighten": "已调亮高度",
        "history.desc.height_darken": "已调暗高度",
        "history.desc.height_set": "已设置高度",
        "history.desc.height_invert": "已反转高度",
        "history.desc.height_optimized": "已优化高度",
        "canvas.layer_added": "已添加新图层",
        "canvas.height_generated": "已从图像生成高度图",
        "canvas.height_imported": "已导入高度图：{name}",
        "canvas.height_imported_16bit": (
            "已导入高度图：{name}（原生 16 位）"
        ),
        "right_panel.height.depth_info": (
            "内部高度数据：16 位（0–65535）"
        ),
        "eufymake.export.height_precision_loss": (
            "8 位导出会把 16 位高度受控量化为 256 级——如需完整精度请选择 16 位"
        ),
        "status.height_source_unsupported": (
            "高度导入：不支持图像模式“{mode}”"
        ),
        "status.height_import_failed": "高度导入失败",
        "right_panel.height.scale_hint": (
            "0–255 刻度；按比例映射到 16 位高度范围（0–65535）"
        ),
        "canvas.height_lightened": "已调亮高度",
        "canvas.height_darkened": "已调暗高度",
        "canvas.height_set": "已设置高度",
        "canvas.height_inverted": "已反转高度",
        "canvas.height_optimized": "已优化高度",
        "canvas.height_op_error": "高度操作失败：{error}",
        "canvas.not_height_layer": "没有活动的高度图层",
        "canvas.role_incompatible": (
            "“高度图”角色仅适用于高度图层"
        ),
        "canvas.layer_removed": "已删除图层",
        "canvas.layer_duplicated": "已复制图层",
        "canvas.cannot_delete_last": "无法删除最后一个图层",
        "right_panel.tab.layers": "图层",
        "right_panel.tab.layers.tooltip": "管理图层",
        "right_panel.tab.height": "高度",
        "right_panel.tab.height.tooltip": "高度图（浮雕）",
        "right_panel.tab.preview": "预览",
        "right_panel.tab.preview.tooltip": "颜色、浮雕和光泽的 2D 显示",
        "right_panel.preview.section": "2D 预览模式",
        "right_panel.preview.hint": (
            "预览与活动图层无关。"
        ),
        "right_panel.preview.mode": "显示：",
        "right_panel.preview.relief_strength": "浮雕强度：{value} %",
        "right_panel.preview.relief_strength.tooltip": (
            "浮雕与组合模式中山体阴影的强度"
        ),
        "right_panel.preview.gloss_visible": "显示光泽",
        "right_panel.preview.gloss_visible.tooltip": (
            "在光泽与组合模式中显示或隐藏光泽效果"
        ),
        "right_panel.preview.export_hint": (
            "仅用于显示——“保存图像”仍然只导出颜色图案。"
        ),
        "right_panel.height.section.acquire": "获取",
        "right_panel.height.section.edit": "编辑",
        "right_panel.height.section.optimize": "优化",
        "right_panel.height.generate": "从图像生成",
        "right_panel.height.generate.tooltip": (
            "从当前图像生成高度图"
        ),
        "right_panel.height.import": "导入灰度图…",
        "right_panel.height.import.tooltip": (
            "将灰度图像导入为高度图"
        ),
        "right_panel.height.hint": (
            "高度工具作用于活动的高度图层。"
        ),
        "right_panel.height.strength": "强度",
        "right_panel.height.lighten": "调亮",
        "right_panel.height.lighten.tooltip": (
            "提升选区内的高度（否则全局）"
        ),
        "right_panel.height.darken": "调暗",
        "right_panel.height.darken.tooltip": (
            "降低选区内的高度（否则全局）"
        ),
        "right_panel.height.set_value": "数值",
        "right_panel.height.set": "设置高度",
        "right_panel.height.set.tooltip": (
            "将高度设为该数值（选区或全局）"
        ),
        "right_panel.height.invert": "反转",
        "right_panel.height.invert.tooltip": (
            "反转高度（选区或全局）"
        ),
        "right_panel.height.levels": "色阶（黑/白）",
        "right_panel.height.gamma": "伽马",
        "right_panel.height.gaussian": "高斯模糊（半径）",
        "right_panel.height.median": "中值模糊（半径）",
        "right_panel.height.threshold": "阈值",
        "right_panel.height.steps": "阶数",
        "right_panel.height.range": "范围（最小/最大）",
        "right_panel.height.apply": "应用",
        "right_panel.height.apply.tooltip": "将预览应用到高度图层",
        "right_panel.height.discard_preview": "放弃预览",
        "right_panel.height.discard_preview.tooltip": (
            "放弃预览而不应用"
        ),
        "right_panel.layers.section": "图层",
        "right_panel.layers.add.tooltip": "新建图层",
        "right_panel.layers.duplicate.tooltip": "复制活动图层",
        "right_panel.layers.delete.tooltip": "删除活动图层",
        "right_panel.layers.move_up.tooltip": "上移图层",
        "right_panel.layers.move_down.tooltip": "下移图层",
        "right_panel.layers.rename.tooltip": "重命名活动图层",
        "right_panel.layers.role_label": "角色：",
        "right_panel.layers.role.tooltip": (
            "活动图层的角色（用于将来的 UV 打印工具）"
        ),
        "right_panel.layers.visible.tooltip": "切换可见性",
        "right_panel.layers.select.tooltip": "设为活动图层",
        "right_panel.layers.opacity.tooltip": "不透明度（松开时应用）",
        "right_panel.layers.empty": (
            "未加载项目——请打开图像或“新建项目”。"
        ),
        "menu.project": "项目",
        "action.new_project": "新建项目",
        "action.open_project": "打开项目…",
        "action.save_project": "保存项目",
        "action.save_project_as": "项目另存为…",
        "dialog.open_project.title": "打开项目",
        "dialog.open_project.filter": "BgRemover 项目 (*.bgrproj)",
        "dialog.save_project.title": "保存项目",
        "dialog.rename.title": "重命名图层",
        "dialog.rename.label": "新名称：",
        "dialog.import_height.title": "导入高度图",
        "dialog.project_error.title": "项目错误",
        "project.new": "已创建新项目",
        "project.saved": "项目已保存：{name}",
        "project.opened": "项目已打开：{name}",
        "project.no_project": "没有可保存的项目",
        "project.save_failed": "保存项目失败：{error}",
        # Main menu
        "menu.file": "文件",
        "menu.recent_files": "最近打开",
        "menu.edit": "编辑",
        "menu.view": "视图",
        "menu.preview_mode": "预览模式",
        "menu.extras": "工具",
        "action.open": "打开…",
        "action.save": "保存",
        "action.save_as": "另存为…",
        "action.undo": "撤销",
        "action.redo": "重做",
        "action.rotate_left_90": "向左旋转 90°",
        "action.rotate_right_90": "向右旋转 90°",
        "action.rotate_180": "旋转 180°",
        "action.flip_horizontal": "水平翻转",
        "action.flip_vertical": "垂直翻转",
        "action.resize": "调整大小…",
        "action.clear_selection": "取消选区",
        "action.invert_selection": "反选",
        "action.restore_original": "恢复原图",
        "action.fit_to_view": "适应窗口",
        # Verlauf-Popup: Menü-Anker seit #458 (Rail-Button entfallen)
        "action.history": "历史记录",
        # Zoom-Kontrolle auf der Arbeitsfläche (#464)
        "zoom.in.tooltip": "放大（+10 %）",
        "zoom.out.tooltip": "缩小（−10 %）",
        "zoom.lock.tooltip": "锁定缩放（保持当前值）",
        "zoom.unlock.tooltip": "解除缩放锁定",
        "preview.mode.color": "颜色",
        "preview.mode.relief": "颜色上的浮雕",
        "preview.mode.height": "高度（灰度）",
        "preview.mode.gloss": "光泽",
        "preview.mode.combined": "组合",
        # Kurzlabels für das Segmented-Control der 2D-Vorschau (§9 Schritt 6)
        "preview.seg.color": "颜色",
        "preview.seg.relief": "浮雕",
        "preview.seg.height": "高度",
        "preview.seg.gloss": "光泽",
        # 3D 浮雕预览（Epic #582）
        "menu.view.show_3d": "显示 3D 浮雕",
        "preview3d.section": "3D 浮雕预览",
        "preview3d.display": "显示：",
        "preview3d.display.2d": "2D",
        "preview3d.display.3d": "3D",
        "preview3d.display.3d.disabled_tooltip": (
            "3D 需要有效的高度图数据和 OpenGL 2.1。"
        ),
        "preview3d.exaggeration": "高度夸张：  {value}×",
        "preview3d.exaggeration.hint": "仅改变显示，绝不改变高度数据。",
        "preview3d.light_azimuth": "光照方位角：  {value}°",
        "preview3d.light_elevation": "光照仰角：  {value}°",
        "preview3d.quality": "质量：",
        "preview3d.quality.reduced": "降低",
        "preview3d.quality.standard": "标准",
        "preview3d.quality.high": "高",
        "preview3d.fit": "适应视图",
        "preview3d.reset": "重置",
        "preview3d.empty": (
            "尚无高度图。请在“高度”标签页中创建高度图，以使用 3D 预览。"
        ),
        "preview3d.unavailable": (
            "3D 预览不可用：此环境不提供 OpenGL 2.1。2D 浮雕预览仍然可用。"
        ),
        "preview3d.loading": "正在计算 3D 预览…",
        "preview3d.ready_hint": (
            "3D 预览已启用 – 已保存的图像和导出保持不变。"
        ),
        "preview3d.decimated": "简化显示 1:{factor}",
        "preview3d.error": (
            "3D 预览遇到图形错误。您的编辑、项目和导出均不受影响。"
        ),
        "preview3d.error.show_2d": "显示 2D 浮雕",
        "preview3d.error.retry": "重试",
        "preview3d.a11y.name": "3D 浮雕预览",
        "preview3d.a11y.desc": (
            "交互式 3D 表面。拖动旋转，滚轮缩放，Alt+拖动平移；方向键旋转，Home 键适应视图。"
        ),
        # Design-Umschalter (Epic #424, Issue #428)
        "action.light_mode": "浅色主题",
        "theme.switched.light": "已启用浅色主题。",
        "theme.switched.dark": "已启用深色主题。",
        "action.settings": "设置…",
        "action.check_for_updates": "检查更新…",
        "action.manage_ai_model": "管理 AI 模型…",
        "action.install_ai_backend": "安装 AI 背景移除…",
        # App-Update-Check (#565)
        "status.update_check_running": "正在检查更新…",
        "status.update_available_hint": "🆕 有可用更新：{version} —— 点击查看详情",
        "dialog.update_check.title": "更新检查",
        "dialog.update_check.up_to_date.body": "您使用的已是最新版本（{version}）。",
        "dialog.update_check.available.body": "有新版本可用：{latest}（已安装：{current}）。",
        "dialog.update_check.open_release": "打开发布页面",
        "dialog.update_check.failed.body": "更新检查失败，请稍后重试。",
        # KI-Modell-Verwaltung (#569)
        "ai_model.dialog.title": "管理 AI 模型",
        "ai_model.status.downloaded": "已下载（{path}，{size}）",
        "ai_model.status.not_downloaded": "尚未下载",
        "ai_model.status.rembg_unavailable": "AI 功能不可用（未安装 rembg）",
        "ai_model.status.python_hint": "当前 Python 环境：{path}",
        "ai_model.dialog.download": "立即下载",
        "ai_model.dialog.retry": "重试",
        "ai_model.dialog.cancel": "取消",
        "ai_model.dialog.close": "关闭",
        "ai_model.dialog.cancelled": "下载已取消",
        # KI-Backend nachrüsten (Menü-Aktion ohne Auto-Install)
        "ai_install.dialog.title": "安装 AI 背景移除",
        "ai_install.dialog.intro": (
            "此安装未包含 rembg（AI 后端）。应用不会自动安装任何内容——现代 Linux "
            "系统会阻止向系统 Python 执行 pip 安装（PEP 668），而且刚安装的包在当前"
            "进程中也要重启后才能生效。请在项目文件夹的终端中执行："
        ),
        "ai_install.dialog.venv_note": '已经在使用自己的 venv？只需执行：pip install "rembg[cpu]"',
        "ai_install.dialog.already_installed": "提示：rembg 已在当前运行环境中安装。",
        "ai_install.dialog.python_too_old": (
            "⚠ 当前 Python {version} 版本过旧，无法用于 AI：rembg/onnxruntime 需要 "
            "Python 3.11+。请先安装更新的 Python（例如通过 Homebrew/pyenv/apt），"
            "并确保「python3」指向它，然后再执行该命令。"
        ),
        "ai_install.dialog.copy": "复制命令",
        "ai_install.dialog.copied": "已复制到剪贴板。",
        # Left toolbar
        "toolbar.move.tooltip": (
            "移动 / 缩放\n"
            "按住左键拖动可平移视图 · 滚轮缩放"
        ),
        "toolbar.wand.tooltip": (
            "魔棒  (W)\n"
            "单击选择颜色区域（泛洪填充）\n"
            "Shift = 加选  ·  {modifier} = 减选"
        ),
        "toolbar.brush.tooltip": "画笔  (B)\n手动将区域添加到选区",
        "toolbar.eraser.tooltip": "橡皮擦  (E)\n从选区中移除区域",
        "toolbar.lasso.tooltip": (
            "多边形套索  (L)\n"
            "单击放置顶点 · 双击闭合多边形\n"
            "Shift = 加选  ·  {modifier} = 减选  ·  Esc = 取消"
        ),
        "toolbar.height_lighten.tooltip": (
            "调亮（升高）\n"
            "笔触提升活动高度图层的高度"
        ),
        "toolbar.height_darken.tooltip": (
            "调暗（降低）\n"
            "笔触降低活动高度图层的高度"
        ),
        "toolbar.height_tools.disabled.tooltip": (
            "高度工具\n"
            "请先激活一个高度图层（第 5 步：生成/导入高度图）"
        ),
        "toolbar.ai.missing.tooltip": (
            'rembg 未安装\n→ python3 -m pip install -e ".[ai]"'
        ),
        "toolbar.undo.tooltip": (
            "撤销  ({shortcut})\n"
            "撤销上一个编辑步骤"
        ),
        "toolbar.redo.tooltip": (
            "重做  ({shortcut})\n"
            "重做上一个被撤销的步骤"
        ),
        "toolbar.theme.to_light.tooltip": "切换到浅色主题",
        "toolbar.theme.to_dark.tooltip": "切换到深色主题",
        # Right panel tabs
        "right_panel.tab.selection": "选区",
        "right_panel.tab.selection.tooltip": (
            "选区——魔棒、画笔、橡皮擦"
        ),
        "right_panel.tab.background": "背景",
        "right_panel.tab.background.tooltip": (
            "背景——移除、替换颜色"
        ),
        "right_panel.tab.adjust": "调整",
        "right_panel.tab.adjust.tooltip": (
            "色彩校正——亮度、对比度、饱和度"
        ),
        "right_panel.tab.transform": "旋转/翻转",
        "right_panel.tab.transform.tooltip": "变换——旋转、翻转",
        "right_panel.tab.shape": "形状",
        "right_panel.tab.shape.tooltip": (
            "形状与裁剪——圆角、选择版式"
        ),
        # History popup
        "history.window_title": "更改历史",
        "history.hint": "双击条目 → 回到该步骤",
        "history.list.tooltip": (
            "所有编辑步骤的历史。\n"
            "双击条目可回到该步骤。"
        ),
        # Crop bar
        "crop_bar.label": "✂  放置裁剪框，然后确认：",
        "crop_bar.confirm": "✓  应用裁剪",
        "crop_bar.cancel": "✗  取消",
        # Right panel — Selection tab contents
        "right_panel.selection.section.settings": "工具设置",
        "right_panel.selection.section.select": "选区",
        "right_panel.selection.tolerance": "容差（魔棒）：{value}",
        "right_panel.selection.tolerance.tooltip": (
            "控制颜色需要多相似才会被选中。\n"
            "低 = 只选非常相近的颜色 · 高 = 包含更多色调"
        ),
        "right_panel.selection.brush_size": "画笔大小：{value} px",
        "right_panel.selection.brush_size.tooltip": (
            "画笔/橡皮擦工具的大小（像素）"
        ),
        "right_panel.selection.clear": "取消选区",
        "right_panel.selection.clear.tooltip": (
            "取消当前选区（也可按 Esc 键）"
        ),
        "right_panel.selection.invert": "反选",
        "right_panel.selection.invert.tooltip": (
            "交换选中与未选中的区域  ({modifier}+Shift+I)"
        ),
        "right_panel.selection.morph.label": "半径：",
        "right_panel.selection.morph.tooltip": (
            "扩展/收缩选区的半径（像素）"
        ),
        "right_panel.selection.expand": "+ 扩展",
        "right_panel.selection.expand.tooltip": (
            "按设定的半径扩展选区"
        ),
        "right_panel.selection.shrink": "− 收缩",
        "right_panel.selection.shrink.tooltip": (
            "按设定的半径收缩选区"
        ),
        # Right panel — Background tab contents
        "right_panel.background.section": "编辑背景",
        "right_panel.background.remove": "移除（透明）",
        "right_panel.background.remove.tooltip": (
            "使选中的区域完全透明。\n"
            "提示：先用魔棒选择背景。"
        ),
        "right_panel.background.color_label": "选择颜色并填充选区：",
        "right_panel.background.color.tooltip": "单击以选择替换的背景颜色",
        "right_panel.background.replace": "替换颜色",
        "right_panel.background.replace.tooltip": (
            "用所选颜色填充选中的区域"
        ),
        "right_panel.background.section.feather": "平滑边缘",
        "right_panel.background.feather_hint": (
            "柔化抠图边缘（仅 Alpha）。"
        ),
        "right_panel.background.feather_radius": "半径：{value} px",
        "right_panel.background.feather_radius.tooltip": (
            "边缘平滑半径（像素，0 = 关闭）"
        ),
        "right_panel.background.feather": "平滑边缘",
        "right_panel.background.feather.tooltip": (
            "柔化活动图层的 Alpha 边缘（选区或全局）"
        ),
        # Right panel — Transform tab contents
        "right_panel.transform.section.rotate": "旋转",
        "right_panel.transform.quick_label": "快速旋转：",
        "right_panel.transform.rotate_left_90": "↺ 向左 90°",
        "right_panel.transform.rotate_left_90.tooltip": "逆时针旋转 90°",
        "right_panel.transform.rotate_right_90": "↻ 向右 90°",
        "right_panel.transform.rotate_right_90.tooltip": "顺时针旋转 90°",
        "right_panel.transform.rotate_180": "↺ 180°",
        "right_panel.transform.rotate_180.tooltip": "将图像旋转 180°",
        "right_panel.transform.rotate_270": "↺ 270°",
        "right_panel.transform.rotate_270.tooltip": "逆时针 270°（= 向右 90°）",
        "right_panel.transform.free_label": "任意角度：",
        "right_panel.transform.angle_slider.tooltip": "设置旋转角度：−180° 至 +180°",
        "right_panel.transform.angle_spin.tooltip": "直接输入旋转角度",
        "right_panel.transform.apply_angle": "应用角度",
        "right_panel.transform.apply_angle.tooltip": (
            "按设定角度旋转图像。\n"
            "倾斜角度会产生透明的边角。"
        ),
        "right_panel.transform.section.flip": "翻转",
        "right_panel.transform.flip_h": "水平",
        "right_panel.transform.flip_h.tooltip": "水平翻转图像（左 ↔ 右）",
        "right_panel.transform.flip_v": "垂直",
        "right_panel.transform.flip_v.tooltip": "垂直翻转图像（上 ↕ 下）",
        # Größe-ändern-Dialog (#359)
        "resize.title": "调整大小",
        "resize.width": "宽度",
        "resize.height": "高度",
        "resize.link_aspect": "锁定宽高比",
        "resize.resample.label": "方法：",
        "resize.resample.lanczos": "Lanczos（最佳质量）",
        "resize.resample.bicubic": "双三次",
        "resize.resample.bilinear": "双线性",
        "resize.resample.nearest": "最近邻",
        "resize.megapixels": "{mp:.1f} MP（上限：{maximum} MP）",
        "resize.ok": "应用",
        "resize.cancel": "取消",
        # mm/DPI-Modus + Druckflächenprüfung (#377)
        "resize.mode.label": "单位：",
        "resize.mode.pixel": "像素",
        "resize.mode.mm": "毫米（mm + DPI）",
        "resize.width_mm": "宽度",
        "resize.height_mm": "高度",
        "resize.dpi": "分辨率",
        "resize.medium.label": "目标介质：",
        "resize.pixels_result": "结果：{width}×{height} px（{mp} MP）",
        "resize.print_area_ok": "可放入 {medium}（{medium_w}×{medium_h} mm）。",
        "resize.print_area_exceeded": (
            "⚠ 图案 {width}×{height} mm 超出 {medium}"
            "（{medium_w}×{medium_h} mm）。"
        ),
        # Right panel — Adjust tab contents (#360)
        "right_panel.adjust.section": "色彩校正",
        "right_panel.adjust.hint": "作用于活动的颜色图层。",
        "right_panel.adjust.brightness": "亮度：{value} %",
        "right_panel.adjust.brightness.tooltip": (
            "活动颜色图层的亮度（100 % = 不变）"
        ),
        "right_panel.adjust.contrast": "对比度：{value} %",
        "right_panel.adjust.contrast.tooltip": (
            "活动颜色图层的对比度（100 % = 不变）"
        ),
        "right_panel.adjust.saturation": "饱和度：{value} %",
        "right_panel.adjust.saturation.tooltip": (
            "活动颜色图层的饱和度（0 % = 灰度，100 % = 不变）"
        ),
        "right_panel.adjust.reset": "重置",
        "right_panel.adjust.reset.tooltip": (
            "将滑块重置为 100 % 并放弃预览"
        ),
        "right_panel.adjust.apply": "应用",
        "right_panel.adjust.apply.tooltip": (
            "将色彩校正应用到活动的颜色图层"
        ),
        # Right panel — Shape tab contents
        "right_panel.shape.section.corner": "圆角",
        "right_panel.shape.radius": "半径：{value} px",
        "right_panel.shape.radius.tooltip": (
            "圆角半径（像素）。\n"
            "0 = 不圆角 · 500 = 最大圆角"
        ),
        "right_panel.shape.round": "应用圆角",
        "right_panel.shape.round.tooltip": (
            "应用圆角。\n"
            "结果保存为带透明边角的 PNG。"
        ),
        "right_panel.shape.section.resize": "调整大小",
        "right_panel.shape.resize_apply": "应用尺寸",
        "right_panel.shape.resize_apply.tooltip": "缩放到输入的尺寸",
        "right_panel.shape.section.format": "裁剪版式",
        "right_panel.shape.circle": "⬤  圆形",
        "right_panel.shape.circle.tooltip": "放置圆形裁剪框并应用",
        # Settings dialog
        "settings.title": "设置",
        "settings.open_dir.label": "打开文件的默认目录",
        "settings.save_dir.label": "导出 / 保存的默认目录",
        "settings.dir.placeholder": "留空 = 上次使用的目录",
        "settings.format.label": "首选图像文件格式",
        "settings.log.label": "日志文件",
        "settings.log.tooltip": "日志文件路径（选中即可复制）",
        "settings.log.open_button": "打开文件夹",
        "settings.log.open_failed": "无法打开文件夹：\n{target}",
        "settings.update.auto_check.label": "启动时自动检查更新",
        "settings.cancel": "取消",
        "settings.ok": "确定",
        "settings.pick_open.title": "选择打开文件的目录",
        "settings.pick_save.title": "选择导出/保存的目录",
        "settings.invalid_dir.title": "目录无效",
        "settings.invalid_dir.body": "{label} 不是已存在的目录：\n{value}",
        "settings.language.label": "语言",
        "settings.language.restart_title": "需要重新启动",
        "settings.language.restart_hint": (
            "语言更改将在下次启动时生效。"
        ),
        # Dialogs (QMessageBox)
        "dialog.ai_error.title": "AI 错误",
        "dialog.ai_error.body": (
            "自动移除背景时出错：\n\n{msg}"
        ),
        # Main-window dialogs
        "dialog.unsaved.title": "未保存的更改",
        "dialog.unsaved.body": (
            "图像已被编辑。要在丢弃之前保存更改吗？"
        ),
        "dialog.open.title": "打开图像",
        "dialog.open.filter": (
            "图像 (*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.tif *.gif);;"
            "所有文件 (*)"
        ),
        "dialog.save.title": "图像另存为…",
        "dialog.color.title": "选择背景颜色",
        # Canvas status messages
        "canvas.opened": "已打开：{name}  （{w} × {h} px）",
        "canvas.opened_extra": (
            "已打开：{name}  （已忽略另外 {extra} 个文件）"
        ),
        "canvas.undo_none": "没有可撤销的操作了",
        "canvas.undo_done": "↩  已撤销：{desc}",
        "canvas.redo_none": "没有可重做的操作了",
        "canvas.redo_done": "↪  已重做：{desc}",
        "canvas.undo_to": "↩  已撤销 {steps} 步  （至：{desc}）",
        "canvas.original_restored": "🔄  已恢复原图",
        "canvas.selection_cleared": "已取消选区",
        "canvas.selection_inverted": "已反选：{pixels:,} 像素",
        "canvas.selection_expanded": "选区已扩展 {radius} px：{pixels:,} 像素",
        "canvas.selection_shrunk": "选区已收缩 {radius} px：{pixels:,} 像素",
        "canvas.bg_removed": "已移除背景（透明）",
        "canvas.remove_error": "移除时出错：{error}",
        "canvas.bg_replaced": "已替换背景：{color}",
        "canvas.replace_error": "替换时出错：{error}",
        "canvas.ai_done": "✅ AI 背景移除完成",
        "canvas.selection_pixels": "选区：{pixels:,} 像素",
        "canvas.selection_error": "选区错误：{msg}",
        "canvas.lasso_cancelled": "已取消多边形套索",
        "canvas.lasso_selected": "多边形套索：已选择 {pixels:,} 像素",
        "canvas.lasso_points_one": (
            "多边形套索：{n} 个顶点——双击完成 · Esc = 取消"
        ),
        "canvas.lasso_points_many": (
            "多边形套索：{n} 个顶点——双击完成 · Esc = 取消"
        ),
        "canvas.format_unsupported": "不支持的格式",
        "canvas.radius_positive": "半径必须 > 0",
        "canvas.corners_rounded": "已应用圆角：半径 {r} px",
        "canvas.rotate_too_large": (
            "旋转 {degrees}° 会使图像过大"
            "（{mp:.0f} MP）——上限：{maximum} MP"
        ),
        "canvas.rotated": "{direction} 已旋转：{degrees}°  （{w} × {h} px）",
        "canvas.resized": "⇲ 已调整大小：{w} × {h} px",
        "canvas.resize_too_large": (
            "目标尺寸 {w} × {h} px 过大（{mp:.0f} MP）——上限：{maximum} MP"
        ),
        "canvas.color_adjusted": "🎨 已应用色彩校正",
        "canvas.not_color_layer": "没有活动的颜色图层",
        "canvas.feathered": "🪶 已平滑边缘：{radius} px",
        "canvas.flipped_h": "↔ 已水平翻转",
        "canvas.flipped_v": "↕ 已垂直翻转",
        "canvas.crop_cancelled": "已取消裁剪",
        "canvas.crop_size": "⇲ 尺寸：{w} × {h} px",
        "canvas.crop_start_circle": (
            "✂  移动裁剪框  [圆形]  ——  然后点击 ✓ 应用"
        ),
        "canvas.crop_start_ratio": (
            "✂  移动裁剪框  [{w} × {h} px]  ——  然后点击 ✓ 应用"
        ),
        "canvas.cropped": "✂  已裁剪：{w} × {h} px",
        "canvas.save_failed": "保存失败：{error}",
        "canvas.saved": "💾 已保存：{name}",
        # History step descriptions
        "history.desc.generic": "编辑",
        "history.desc.original_restored": "🔄 已恢复原图",
        "history.desc.bg_removed": "已移除背景",
        "history.desc.color_replaced": "已替换颜色（{color}）",
        "history.desc.ai_bg": "AI 背景移除",
        "history.desc.round_corners": "已应用圆角（{r} px）",
        "history.desc.rotated": "{direction} 已旋转 {degrees}°",
        "history.desc.resized": "已调整大小（{w}×{h} px）",
        "history.desc.color_adjusted": "色彩校正",
        "history.desc.feathered": "已平滑边缘（{radius} px）",
        "history.desc.crop_circle": "版式：圆形",
        "history.desc.crop_ratio": "版式：{w}×{h} px",
        # §9-Angleich rechte Spalte – KI/Export/Speichern (#436–#440)
        # Kurzlabel, damit der Primärbutton einzeilig bleibt (§5.4, #515);
        # der volle Wortlaut steht im Tooltip.
        "right_panel.ai.remove": "移除背景（AI）",
        "right_panel.ai.remove.tooltip": (
            "自动移除背景：用 AI 将主体与背景分离"),
        "right_panel.ai.remove.tooltip.warmup": "AI 模型加载中…按钮即将可用",
        "right_panel.ai.remove.tooltip.no_image": "请先打开一张图片",
        "right_panel.ai.remove.tooltip.processing": "AI 正在处理图片…",
        "right_panel.export.section.save": "保存",
        "right_panel.export.format_label": "文件格式",
        "right_panel.export.save": "保存图像",
        "right_panel.export.save.tooltip": "将颜色图案保存为图像",
        "right_panel.export.section.uvprint": "UV 打印",
        "right_panel.export.eufymake": "导出 EufyMake Studio 素材…",
        "right_panel.export.eufymake.tooltip": (
            "为 EufyMake Studio 导出颜色、高度和光泽"),
        "workflow.open.recent": "最近打开",
        # Geführter Workflow – Schrittleiste, Inspector-Kopf, Navigation (Epic #418)
        "workflow.step.open": "打开",
        "workflow.step.cutout": "抠图",
        "workflow.step.adjust": "调整",
        "workflow.step.shape": "形状与尺寸",
        "workflow.step.relief": "浮雕与图层",
        "workflow.step.export": "导出",
        "workflow.title.open": "第 1 步 · 打开",
        "workflow.title.cutout": "第 2 步 · 抠图",
        "workflow.title.adjust": "第 3 步 · 调整",
        "workflow.title.shape": "第 4 步 · 形状与尺寸",
        "workflow.title.relief": "第 5 步 · 浮雕与图层",
        "workflow.title.export": "第 6 步 · 导出",
        "workflow.desc.open": "加载图像——拖放、对话框或最近打开。",
        "workflow.desc.cutout": "将主体与背景分离——自动或手动。",
        "workflow.desc.adjust": "亮度、对比度和饱和度，带实时预览。",
        "workflow.desc.shape": "旋转、翻转、圆角、裁剪和缩放。",
        "workflow.desc.relief": "管理图层以及用于浮雕打印的高度图。",
        "workflow.desc.export": "检查结果、保存或导出到 EufyMake。",
        "workflow.next.open": "下一步：抠图 →",
        "workflow.next.cutout": "下一步：调整 →",
        "workflow.next.adjust": "下一步：形状与尺寸 →",
        "workflow.next.shape": "下一步：浮雕与图层 →",
        "workflow.next.relief": "下一步：导出 →",
        "workflow.next.export": "导出 ✓",
        "workflow.back": "← 返回",
        "workflow.open.drop": "将图像拖到此处",
        "workflow.open.formats": "PNG · JPEG · WebP · TIFF · BMP · GIF",
        "workflow.open.button": "打开文件…",
        "workflow.locked": "请先打开图像（第 1 步）",
        "workflow.status.step": "第 {num}/{total} 步：{title}",
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
