# ADR (2026-06-21): Projekt-/Ebenen-Datenmodell

Kurz-ADR zum Abschluss des Epics #329 („Projekt-/Ebenen-Datenmodell –
Fundament für Height Map, Gloss & EufyMake-Export"). Hält die getroffenen
Architekturentscheidungen und das Endergebnis fest. Status: **umgesetzt**
(Sub-Issues #330–#335).

## Kontext

Der Editor war *single-layer*: der Canvas hielt genau ein Bild, die Historie
speicherte Einzelbild-Snapshots, gespeichert wurde eine Datei. Für Height Map,
Gloss-/Klarlackmaske, verlustfreie Projektdateien und einen späteren
EufyMake-Export braucht es ein nichtdestruktives Mehr-Ebenen-Projektmodell –
ohne Regressionen im bestehenden Freistellungs-/Bearbeitungs-Workflow.

## Entscheidungen

1. **Modellschnitt:** Qt-freies, strikt getyptes Domänenmodul
   `bgremover/project_model.py` (`Project` + `Layer`), analog zur Typdisziplin
   von `image_ops`/`image_utils` (#330).
2. **Historie:** Ebenenbewusste, Qt-freie Undo/Redo-Historie
   `bgremover/project_history.py`. Speicherstrategie: leichte Struktur-Snapshots
   plus deduplizierender, refgezählter Pixelpool (geteiltes Undo-/Redo-Budget;
   unveränderte Ebenen zählen nur einmal) (#331).
3. **Canvas:** Der Canvas hält ein `Project` und rendert/speichert das
   **Komposit**; Werkzeuge wirken auf die **aktive Ebene**. Einzel-COLOR-Ebene =
   bitgenaue Parität (Schnellpfad erhält RGB unter transparenten Pixeln);
   größenändernde Geometrie (Drehen/Zuschnitt) wirkt einheitlich auf alle Ebenen
   (Invariante: alle Ebenen in Canvas-Größe) (#332).
4. **Dateiformat:** `.bgrproj` = ZIP-Container mit `manifest.json`
   (versioniert) + einer RGBA-PNG je Ebene. Atomar geschrieben
   (`mkstemp`+`os.replace`), defensiv geladen (Größen-/Megapixel-Limits,
   Zip-Bomb-/Zip-Slip-Abwehr), Migrationshaken mit Zukunfts-Version-Schutz.
   Alternativen (Multi-Page-TIFF, Pickle) bewusst verworfen – Pickle aus
   Sicherheitsgründen (#333).
5. **UI:** Ebenen-Panel (5. Tab im rechten Panel, getrieben vom
   `layersChanged`-Signal) + „Projekt"-Menü (Neu/Öffnen/Speichern) mit eigenen,
   dokumentierten Kürzeln; `Ctrl+O`/`Ctrl+S` bleiben den Bild-Workflows (#334).
6. **Integration:** „Bild öffnen"/Drag & Drop erzeugen ein Ein-Ebenen-Projekt;
   „Zuletzt geöffnet" führt Bilder **und** Projekte (Dispatch nach Endung);
   Projektverzeichnis wird gemerkt (additiver Settings-Schlüssel, keine
   Schema-Migration nötig – Zukunfts-Version-Schutz bereits getestet);
   Einzelbild-Export liefert das Komposit; „Original wiederherstellen" liefert
   das Dokument im Ladezustand (#335).

## Ergebnis

Ein bestehendes Bild lässt sich öffnen, bearbeiten, als Projekt speichern,
schließen und verlustfrei wieder öffnen und weiterbearbeiten. Mehrere Ebenen
sind anlegbar, umsortierbar, ein-/ausblendbar; Undo/Redo deckt strukturelle und
Pixel-Änderungen ab. Der bestehende Einzelbild-Export bleibt bitgenau. Neue
Qt-freie Module liegen in der strikten mypy-Liste; i18n de/en in Parität;
`make check` und `make ui` grün.
