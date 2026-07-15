# UX-Vertrag: 3D-Reliefvorschau (Epic #582, Issue #591)

Verbindlicher UX-Flow für die interaktive 3D-Reliefvorschau. Gehört zum
Architektur-ADR
[ADR-2026-3d-reliefvorschau-renderer.md](history/ADR-2026-3d-reliefvorschau-renderer.md);
Begriffe (Budgets, Qualitätsstufen, Fallback-Auslöser) sind dort definiert.
Design-Tokens, Komponenten und A11y-Grundregeln folgen der
[REDESIGN_SPEC.md](REDESIGN_SPEC.md) (§-Verweise unten).

## §1 Einbauort und Umschaltlogik

Die 3D-Ansicht ist eine **Darstellung** der aktiven HEIGHT-Daten – kein
sechster `PreviewMode`. Die 2D-Vorschaupipeline (Farbe/Relief/Höhe/Gloss/
Kombiniert) bleibt semantisch unverändert; 3D liegt als eigene Ebene
**darüber**:

- **Ort:** Workflow-Schritt 5 (**RELIEF**, `stepper.py`). Im Vorschau-Tab
  des rechten Panels erscheint oberhalb der bestehenden Modus-Segmente
  (§5.7) eine neue Zeile **„Darstellung"** mit den Segmenten **[2D] [3D]**.
- **Menü:** Ansicht → neuer checkbarer Eintrag **„3D-Relief anzeigen"**
  (ohne Shortcut im MVP; hält sich signalbasiert mit dem Segment synchron,
  wie das bestehende Vorschau-Untermenü, #388).
- **Canvas-Bereich:** Ein Stack wechselt zwischen `ImageCanvas` (2D) und
  dem 3D-Viewer-Widget. Stepper, Menüs und rechtes Panel bleiben stehen.
  Im 3D-Modus sind die 2D-Werkzeuge der Toolbar und die 2D-Modus-Segmente
  deaktiviert (Tooltip: „Im 3D-Modus nicht verfügbar – zurück zu 2D
  wechseln"); die schwebende Zoom-Pille (§14) ist ausgeblendet, da das
  Mausrad die 3D-Kamera zoomt.
- **Gating:** Das 3D-Segment ist nur aktiv, wenn (a) eine HEIGHT-Ebene mit
  gültigen Daten existiert und (b) die Capability-Probe des ADR nicht
  fehlgeschlagen ist. Sonst bleibt es deaktiviert mit erklärendem Text
  (Zustände E/U unten). **2D bleibt immer direkt erreichbar** – auch ohne
  3D-fähige Hardware ändert sich am bestehenden Workflow nichts.
- **Moduswechsel** mutiert nie Bild-/Höhendaten und beeinflusst nie den
  Export; der 2D-Zoomzustand bleibt beim Rückwechsel erhalten.

## §2 Wireflow

```
                         Schritt 5 · RELIEF
                                │
              ┌─────────────────┼──────────────────┐
   Darstellung [2D]     Darstellung [3D]     Ansicht-Menü
        │                       │            „3D-Relief anzeigen“
        ▼                       ▼                  │ (synchron)
┌───────────────┐      Capability-Probe ◄──────────┘
│ 2D-Canvas     │        │ ok        │ fehlgeschlagen
│ COLOR/RELIEF/ │        ▼           ▼
│ HEIGHT/GLOSS/ │   HEIGHT-Ebene   [U] Nicht verfügbar
│ COMBINED      │    vorhanden?      (3D-Segment deaktiviert,
└───────▲───────┘     │ ja  │ nein    Hinweistext, Retry-Link)
        │             ▼     ▼
        │        [L] Laden  [E] Empty State
        │             │      („HEIGHT-Ebene erzeugen“)
        │             ▼
        │        [R] 3D bereit ──── Höhen-Edit ──► [A] Aktualisieren
        │             │                                 (altes Mesh
        │             │ GL-Fehler                        bleibt stehen)
        │             ▼
        └──────── [F] Fehlerzustand
           „2D-Relief anzeigen“ · „Erneut versuchen“
```

Wireframe des 3D-Zustands (Karten-/Token-Sprache aus §2/§5 der Spec):

```
┌──────────────────────────────────────────────┬──────────────────────┐
│  ┌────────────────────────────────────────┐  │ Vorschau-Tab         │
│  │ [Vereinfacht 1:8]              (Badge) │  │ Darstellung  [2D|3D] │
│  │                                        │  │ ──────────────────── │
│  │            3D-Viewport                 │  │ Überhöhung   ●──── 1,0│
│  │      (Orbit/Pan/Zoom, Fokusrahmen)     │  │ Licht-Azimut ───● 315°│
│  │                                        │  │ Licht-Höhe   ──●   45°│
│  │                                        │  │ Qualität [Standard ▾]│
│  └────────────────────────────────────────┘  │ [Einpassen] [Reset]  │
│  Statusleiste: „3D-Vorschau aktiv – Export   │ Hinweis: Überhöhung  │
│  bleibt unverändert.“                        │ ändert nur Anzeige   │
└──────────────────────────────────────────────┴──────────────────────┘
```

## §3 Interaktionen (Maus, Trackpad, Tastatur)

Alle Zuordnungen gelten nur bei Fokus/Zeiger im 3D-Viewport; globale
Kürzel des Hauptfensters bleiben unberührt. Kollisionen mit bestehenden
Canvas-Gesten sind ausgeschlossen, weil 2D-Werkzeuge im 3D-Modus inaktiv
sind und die Pan-Gesten bewusst **identisch** zur 2D-Konvention liegen.

| Aktion | Maus/Trackpad | Tastatur (Viewer-Fokus) |
|---|---|---|
| Orbit (Drehen um Fokuspunkt) | Linke Taste ziehen | Pfeiltasten |
| Pan (Fokuspunkt verschieben) | Mittlere Taste **oder** Alt+Linke Taste ziehen (wie 2D-Canvas) | Umschalt+Pfeiltasten |
| Zoom | Mausrad / Trackpad-Scrollen (Grenzen: Nah-/Fernklemme) | `+` / `−` |
| Einpassen (Fit-to-view) | Button „Einpassen" | `Pos1`; zusätzlich global `Strg+0` (gleiche Semantik wie 2D-„Einpassen", kontextabhängig geroutet) |
| Ansicht zurücksetzen (Kamera + Überhöhung + Licht auf Defaults) | Button „Zurücksetzen" | `Umschalt+Pos1` |
| Fokus verlassen | – | `Esc` / `Tab` (kein Fokus-Traps; `Esc` bricht zuvor eine laufende Drag-Geste ab, wie im 2D-Canvas) |

- Orbit klemmt die Polhöhe (±88°) gegen Kamerasprünge; Zoomgrenzen
  verhindern Durchdringen bzw. Verlieren des Modells.
- Keine neuen globalen Shortcuts im MVP (belegte Kürzel wie `Strg+←/→`
  [Drehen], `Strg+R` [Skalieren], `Strg+0` [Einpassen] bleiben exakt wie
  dokumentiert).
- Hohe Eingaberaten werden auf einen Frame je Renderzyklus
  zusammengefasst (keine wachsende Ereigniswarteschlange).

## §4 Parameter: Überhöhung, Licht, Qualität

| Parameter | Bereich | Default | Verhalten |
|---|---|---|---|
| Überhöhung | 0,1×–10× (logarithmischer Slider) | 1,0× | rein visuell (Uniform, kein Mesh-Rebuild); Hinweistext unter dem Slider: „Verändert nur die Anzeige, nie die Höhendaten." |
| Licht-Azimut | 0–360° | 315° (wie 2D-Hillshade) | Uniform, kein Rebuild |
| Licht-Elevation | 15–90° | 45° (wie 2D-Hillshade) | Uniform, kein Rebuild |
| Qualität | Reduziert / Standard / Hoch (ADR-Budgets) | Standard | löst Rebuild aus; Software-GL startet automatisch in „Reduziert" |

„Zurücksetzen" stellt alle vier Werte und die Kamera auf die Tabelle
zurück. Werte sind Sitzungs-/UI-Präferenzen (QSettings), nie Projektdaten.

## §5 Zustände und UX-Texte

Alle Texte laufen über `tr()` (Runtime de/en, literale Keys
`preview3d.*`); der Status ist stets als **Text** sichtbar, nie nur als
Farbe oder Spinner. Verbindliche Formulierungen (de / en):

| Zustand | Key (Vorschlag) | Text de | Text en |
|---|---|---|---|
| [E] Keine HEIGHT-Ebene | `preview3d.empty` | „Keine Höhenkarte vorhanden. Erzeugen Sie im Höhen-Tab eine Höhenkarte, um die 3D-Vorschau zu nutzen." | "No height map yet. Create a height map in the Height tab to use the 3D preview." |
| [U] Nicht verfügbar (Capability) | `preview3d.unavailable` | „3D-Vorschau nicht verfügbar: Diese Umgebung bietet kein OpenGL 2.1. Die 2D-Reliefvorschau steht weiterhin zur Verfügung." | "3D preview unavailable: this environment does not provide OpenGL 2.1. The 2D relief preview remains available." |
| [L] Laden (erster Aufbau, erst nach 300 ms sichtbar) | `preview3d.loading` | „3D-Vorschau wird berechnet…" | "Computing 3D preview…" |
| [A] Aktualisieren (Rebuild; altes Mesh bleibt sichtbar) | `preview3d.updating` | „Aktualisieren…" | "Updating…" |
| [R] Bereit (Statusleiste, einmalig je Wechsel) | `preview3d.ready_hint` | „3D-Vorschau aktiv – gespeicherte Bilder und Exporte bleiben unverändert." | "3D preview active – saved images and exports remain unchanged." |
| Decimation-Badge (Viewport oben links) | `preview3d.decimated` | „Vereinfachte Darstellung 1:{factor}" | "Simplified view 1:{factor}" |
| [F] Fehler | `preview3d.error` | „Die 3D-Vorschau ist auf einen Grafikfehler gestoßen. Ihre Bearbeitung, das Projekt und der Export sind davon nicht betroffen." | "The 3D preview hit a graphics error. Your edits, project, and export are not affected." |
| [F] Aktion 1 | `preview3d.error.show_2d` | „2D-Relief anzeigen" | "Show 2D relief" |
| [F] Aktion 2 | `preview3d.error.retry` | „Erneut versuchen" | "Try again" |

- Der Ladezustand erscheint erst nach 300 ms (kein Flackern bei
  Cache-Treffern); [A] zeigt das **alte** Mesh weiter (kein Schwarzbild).
- Das Decimation-Badge erscheint immer, wenn das Grid kleiner als die
  Quellauflösung ist (`factor` = gerundetes Verhältnis längere Quellseite ÷
  Gridseite); pixelgenau bleibt die 2D-Vorschau.
- [F] loggt die Fehlerklasse + Diagnosestring (ADR), zeigt aber nie rohe
  Tracebacks. „Erneut versuchen" verwirft den Capability-Cache genau
  einmal je Klick (kein Auto-Retry-Loop).

## §6 COLOR-Bezug (spätere Stufe)

Das Farbmotiv als Oberflächentextur ist eine **optionale spätere Stufe**
(Stretch im ADR): eigene Checkbox „Farbmotiv anzeigen" im Vorschau-Tab,
eigener Textur-Cache-Key, Options-Gating wie Height/Gloss im
EufyMake-Dialog. **HEIGHT-only ist vollständig nutzbar**: Ohne COLOR-Bezug
rendert der Viewer neutralgrau schattiert (Lambert); kein Kriterium dieses
Vertrags hängt an der Textur-Stufe.

## §7 Zugänglichkeit

- **Namen:** Viewer `accessibleName` „3D-Reliefvorschau" +
  `accessibleDescription` mit Bedienhinweis (Orbit/Pan/Zoom-Tasten); alle
  Controls (Slider, Buttons, Segmente) mit zugänglichen Namen – Tooltip
  ist nie der einzige Informationsträger (Regel aus #575).
- **Fokus:** Viewer ist per `Tab` erreichbar (StrongFocus), sichtbarer
  akzentfarbener Fokusrahmen (§12 der Spec, `:focus-visible`-Semantik wie
  Stepper #441); `Esc`/`Tab` verlassen den Viewer immer (kein Trap).
- **Kontrast:** Statustexte und Badge nutzen die Token-Paare aus §2/§3
  der Spec (helles und dunkles Schema); der Viewport-Hintergrund kommt
  aus `theme.active_palette()`, damit Fokusrahmen und Badge in beiden
  Themes ≥ 4,5:1 Kontrast halten.
- **Bewegungsreduktion:** Es gibt **keine** automatischen Kamera-
  Animationen – Einpassen/Zurücksetzen springen ohne Übergang, nichts
  rotiert selbsttätig. Aktualisierungen erfolgen nur nach Debounce
  (ruhiger Modus per Konstruktion).
- **Status nicht nur farblich:** alle Zustände aus §5 sind Textzustände.

## §8 Abgrenzung

Rohbild- und 2D-Relief-Ansicht, Exportverträge, Projektpersistenz und
Undo/Redo-Semantik bleiben unverändert; der Viewer besitzt keinerlei
Schreibpfad ins Modell. Nicht-Ziele des Epics (Mesh-Editor, STL/OBJ-Export,
fotorealistisches Rendering) gelten unverändert.
