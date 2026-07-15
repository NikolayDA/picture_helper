# ADR (2026-07-15): 3D-Reliefvorschau – Renderer-Backend, Fallback und Ressourcenbudgets

ADR zu #591 („[3D] ADR/UX-Vertrag: Renderer-Backend, Fallback und
Ressourcenbudgets") im Epic #582 („Echte 3D-Reliefvorschau"). Baut auf dem
kanonischen HEIGHT-Datenvertrag aus
[ADR-2026-height-16bit-datenvertrag.md](ADR-2026-height-16bit-datenvertrag.md)
(#586) auf. Der zugehörige UX-Vertrag liegt in
[../UX_3D_PREVIEW.md](../UX_3D_PREVIEW.md).
Status: **beschlossen, Implementierung folgt** (#592–#595).

## Kontext

Die bestehende Reliefvorschau ist ein Qt-freies 2D-Hillshade
(`relief_preview.py`, #385): deterministisch, robust, headless-tauglich –
aber nicht räumlich. Eine echte 3D-Ansicht braucht Geometrie, Kamera,
interaktives Rendering, Ressourcensteuerung und einen belastbaren Pfad für
Systeme ohne funktionierenden Grafik-Kontext. Dieses ADR legt Backend,
Abhängigkeitsstrategie, Budgets, Datenfluss, Cache-Regeln, Fallback und
Teststrategie verbindlich fest, bevor #592–#595 implementieren.

Rahmenbedingungen des Repos, die die Entscheidung prägen:

- Die **gesamte Testsuite** läuft headless mit `QT_QPA_PLATFORM=offscreen`
  (Makefile, `tests/conftest.py`, CI); ohne X-Display existiert dort **kein**
  OpenGL-Kontext (siehe Evidenz unten).
- Der Code ist reines **PyQt6-Widgets**-UI mit strikt getypten, Qt-freien
  Logikmodulen; es gibt keine QML-Schicht.
- HEIGHT liest 3D ausschließlich über den Vertrag aus #586:
  `HeightField` (`values: uint16 (H, W)`, `coverage: uint8 (H, W)`,
  `max_value ∈ {255, 65535}`); ein zweites Höhenmodell ist ausgeschlossen.
- Fünf Release-Artefaktklassen: Linux x86_64/aarch64 je AppImage + DEB,
  macOS arm64 DMG.

## Prototypische Evidenz (Messumgebung)

Alle Messungen vom 2026-07-15 in der Standard-Web-/CI-Umgebung dieses Repos:
Linux x86_64 (Container), Python 3.11.15, PyQt6 6.11.0 / Qt 6.11.1,
Mesa 25.2.8 (llvmpipe, Software-Rasterizer), `QT_QPA_PLATFORM=offscreen`,
Xvfb verfügbar. Messmethode: eigenständige Probe-Skripte (Kern unten als
Code wiedergegeben), Zeiten via `time.perf_counter()`, Pixel-Asserts über
FBO-Readback.

1. **Ohne X-Display liefert das `offscreen`-Plugin keinen GL-Kontext:**
   `QOpenGLContext.create()` → `False`. Capability-Erkennung zur Laufzeit
   ist damit zwingend; reine Offscreen-CI kann kein 3D rendern.
2. **Mit Xvfb + `offscreen`-Plugin** entsteht ein GLX-Kontext
   „OpenGL 4.5 Compatibility (llvmpipe)". Der Qt-native Prototyp
   (Option A) rendert ein indiziertes Grid-Mesh korrekt (Pixelprobe exakt
   erwartungsgemäß); Importkosten der GL-Module ≈ 26 ms, erster Draw
   (inkl. llvmpipe-Shader-JIT) ≈ 134 ms.
3. **PyQt6 bindet keine generische `QOpenGLContext.functions()`-API.**
   Verfügbar sind `QOpenGLFunctions_2_0/2_1/4_1_Core` über
   `QOpenGLVersionFunctionsFactory` (4.1 Core = macOS-Maximum) sowie
   `QOpenGLShaderProgram`/`QOpenGLBuffer`/`QOpenGLVertexArrayObject`/
   `QOpenGLFramebufferObject`/`QOpenGLTexture`. Rohes Desktop-GL geht also
   **ohne** neue Abhängigkeit; ein reiner-ES-Kontext ist mit den
   gebundenen Funktionsklassen nicht ansprechbar (→ Mindestvoraussetzung
   Desktop-GL, sonst 2D-Fallback).
4. **QtQuick3D (Option B) rendert nicht auf dem `offscreen`-Plugin:**
   `View3D` verlangt einen RHI-basierten Scenegraph, `grabWindow()` fällt
   dort auf den Software-Scenegraph zurück („The View3D item is not going
   to display anything"). Unter echtem X (xcb + Xvfb + llvmpipe) rendert
   dieselbe Szene korrekt – aber erst nach Installation von 7 zusätzlichen
   Systempaketen (`libxcb-cursor0`, `libxkbcommon-x11-0`, …), die weder CI
   noch `session-start.sh` heute vorsehen.
5. **Mesh-Build (numpy, deterministisch, Container-CPU):**
   Grid 512×512 ≈ 37 ms, 1024×1024 ≈ 310–370 ms, 1448×1448 ≈ 1,3 s
   (Positionen + zentrale-Differenzen-Normalen + uint32-Indizes).
6. **llvmpipe-Draw-Baseline (800×600-FBO, ein Frame):** Grid 64² ≈ 42 ms
   (JIT-Anteil), 256² (0,13 M Dreiecke) ≈ 21 ms, 512² (0,52 M) ≈ 79 ms.
   Software-GL ist also für kleine Smokes und sogar als reduzierte
   interaktive Stufe nutzbar.
7. **Wheel-Lage (PyPI, Stand 2026-07-15):** PyQt6 6.11.0 deckt
   manylinux x86_64 + aarch64 und macOS universal2 ab. Kandidaten als
   *neue* Abhängigkeiten: pyqtgraph 0.14.0 (1,9 MB, braucht zusätzlich
   PyOpenGL 3.1.10, 3,2 MB), vispy 0.16.2 (1,9 MB, C-Extensions),
   moderngl 5.12.0 (0,1 MB, eigenes Kontextmodell), matplotlib 3.11.0
   (≈ 11 MB, kein Echtzeit-3D).

## Optionen

### Option A: Qt-nativer OpenGL-Viewer (`QOpenGLWidget` + PyQt6-GL-Klassen)

Ein `QOpenGLWidget` rendert das vom Qt-freien Geometriekern (#592)
gelieferte Grid-Mesh über `QOpenGLShaderProgram`, `QOpenGLBuffer` (VBO/IBO),
VAO und `QOpenGLVersionFunctionsFactory` (GL 2.1-Pfad; 4.1 Core optional).
Kamera-/Orbit-Mathematik liegt als Qt-freie, strikt getypte Logik neben dem
Geometriekern. Keine neue Laufzeitabhängigkeit.

### Option B: QtQuick3D (`View3D` via `QQuickWidget`)

Deklarative Szene (Kamera, Licht, Material) in QML; Mesh als
`QQuick3DGeometry` aus Python. Bibliotheken liegen bereits im PyQt6-Wheel
(`libQt6Quick3D*` ≈ 19 MB + `libQt6ShaderTools` 5,7 MB), rendert über RHI
(Metal auf macOS, GL/Vulkan auf Linux).

### Option C: pyqtgraph.opengl (`GLSurfacePlotItem`)

Fertiges Surface-Plot-Widget; zieht **zwei neue Laufzeitabhängigkeiten**
(pyqtgraph MIT + PyOpenGL BSD) in Install und alle fünf Artefaktklassen.

### Option D: vispy / moderngl

Generische GPU-Visualisierungs-Frameworks; neue Abhängigkeiten mit
C-Extensions bzw. eigenem Kontextmodell außerhalb des Qt-Lifecycles.

### Option E: matplotlib `plot_surface`

Software-Rendering ohne interaktive Framerate-Perspektive bei ≥ 0,5 M
Dreiecken; neue ≈ 11-MB-Abhängigkeit. **Verworfen ohne Detailvergleich** –
erfüllt das Interaktionsziel des Epics per Konstruktion nicht.

### Bewertung

| Kriterium | A: Qt-natives GL | B: QtQuick3D | C: pyqtgraph.opengl | D: vispy/moderngl |
|---|---|---|---|---|
| Neue Laufzeitabhängigkeit | **keine** | keine (im Wheel enthalten) | pyqtgraph + PyOpenGL | vispy bzw. moderngl (+ Kontextmodell) |
| Linux x86_64/aarch64 | PyQt6-Wheels vorhanden; GL via Treiber/llvmpipe | wie A, plus QML-/Shader-Assets | py3-none-any, läuft wo PyOpenGL läuft | Wheels vorhanden |
| macOS arm64 | CGL/OpenGL 4.1 – von Apple deprecated, aber in macOS 15 funktional | **Metal via RHI** (zukunftssicherste Grafikschicht) | OpenGL (wie A) | OpenGL (wie A) |
| Paketgröße | +0 | +0 im Wheel; AppImage/DMG müssen QML-Module + ShaderTools mitliefern | +5,1 MB pip | +2 MB pip |
| Build-/Packaging-Komplexität | unverändert | QML-Import-Pfade in AppImage/DMG bündeln und testen | Lizenz-/NOTICE-Pflege + Packaging | wie C, plus Kontext-Sonderwege |
| Startzeit | GL-Module-Import ≈ 26 ms (gemessen) | QML-Engine + Typregistrierung ≈ 50 ms Import + Engine-Start (gemessen: erster Frame 0,3 s unter xcb) | Import pyqtgraph ≈ 10² ms (Erfahrungswert) | ähnlich |
| Grafiktreiber-Anforderung | Desktop-GL ≥ 2.1 (llvmpipe genügt) | RHI-fähiger Kontext; **kein** Rendern auf `offscreen`-Plugin (belegt) | Desktop-GL ≥ 2.0 | GL ≥ 3.3 (moderngl) |
| Lizenz | PyQt6 GPLv3 (bestehend) | wie A | + MIT + BSD (NOTICE-Pflege) | + BSD/MIT |
| Wartbarkeit | ~wenige 100 Zeilen eigener Shader-/Kamera-Code, voll typisiert, `mypy`-prüfbar | QML-Schicht ist un-typisiert, bricht die reine Widgets-Architektur, Debugging über zwei Sprachgrenzen | fremdes Szenen-API, GL-Teil von pyqtgraph historisch dünn gepflegt | mächtig, aber deutlich größere API-Oberfläche als der Anwendungsfall |
| Qt-/Event-Loop-Integration | nativ: `initializeGL/resizeGL/paintGL` im UI-Thread, Kontext an Widget-Lifecycle gebunden | Scenegraph-Render-Thread + `QQuickWidget`-Brücke; Ressourcen-Lifecycle opak | eigener Timer-/Update-Zyklus | Framework-eigene Loops |
| High-DPI / Theme | `devicePixelRatioF()` direkt; Clear-Farbe aus `theme.active_palette()` | High-DPI ok; Theme-Sync QML↔Widgets manuell | begrenzt | manuell |
| Headless-/Offscreen-Testbarkeit | **rendert auf `offscreen` + Xvfb/llvmpipe (belegt)**; Fallback-Pfad ist ohne GL exakt der CI-Standardfall | **rendert nicht auf `offscreen`** (belegt); CI bräuchte xcb + Zusatzpakete in allen sechs Qt-Paketlisten (Befund N6) | wie A, plus Fremdcode | wie A, plus Fremdcode |

### Verworfene Optionen und Gründe

- **Option B (QtQuick3D):** (1) rendert nachweislich nicht auf dem
  `offscreen`-Plugin – der komplette Test-/CI-Pfad dieses Repos könnte den
  Viewer nie ausführen, Render-Smokes erforderten einen zweiten
  Plattform-Stack (xcb + 7 Systempakete in sechs Dateien, Befund N6);
  (2) QML bricht die strikt getypte, reine Widgets-Architektur (mypy-blind);
  (3) AppImage-/DMG-Packaging müsste QML-Module + ShaderTools korrekt
  bündeln – neue Fehlerklasse in allen fünf Artefaktklassen. Der
  Metal-Vorteil auf macOS bleibt als Beobachtungspunkt (siehe Risiken),
  rechtfertigt diese Kosten für **einen** Grid-Mesh-Anwendungsfall aber
  nicht.
- **Option C (pyqtgraph):** zwei neue Laufzeitabhängigkeiten ohne belegten
  Mehrwert gegenüber Qt-Bordmitteln (Leitplanke aus #591); der
  GL-Teil von pyqtgraph bietet weder Coverage-Löcher noch unsere
  Budget-/Cache-Verträge, sodass der Geometriekern trotzdem selbst
  entstünde – es bliebe nur ein fremdes Anzeige-Widget.
- **Option D (vispy/moderngl):** wie C; zusätzlich eigenes Kontext-/
  Loop-Modell neben dem Qt-Lifecycle (moderngl) bzw. große API-Oberfläche
  (vispy) für denselben einen Anwendungsfall.
- **Option E (matplotlib):** siehe oben.

## Entscheidung

**Option A: Qt-nativer OpenGL-Viewer** (`QOpenGLWidget` +
`QOpenGLShaderProgram`/`QOpenGLBuffer`/VAO über die PyQt6-Bindings) mit
einem **Qt-freien, rendererunabhängigen Geometriekern** (#592) davor.

Tragende Gründe: keine neue Laufzeitabhängigkeit (Leitplanke), belegte
Funktion auf dem Repo-Standard-Testpfad (`offscreen` + Xvfb/llvmpipe),
voller Durchgriff auf Budgets und Buffer-Lifecycle, native Widgets-/
High-DPI-/Theme-Integration, strikt typisierbarer Python-Code. Der
Geometriekern ist bewusst **backend-neutral** (reine numpy-Arrays als
Ausgabeformat): sollte Apple OpenGL tatsächlich entfernen oder Qt den
GL-Pfad deprecaten, ist ausschließlich das Viewer-Widget (#593)
auszutauschen (z. B. gegen ein QtQuick3D- oder QRhi-Backend), nicht die
Pipeline.

### Mindestvoraussetzungen und Capability-Erkennung

- **Mindestvoraussetzung:** Desktop-OpenGL ≥ 2.1 (llvmpipe genügt);
  optionaler 4.1-Core-Pfad, wenn verfügbar. Reine-ES-Kontexte gelten als
  „nicht 3D-fähig" (PyQt6 bindet keine ES-Funktionssätze) → 2D-Fallback.
- **Laufzeit-Probe** (`probe_3d_capability()`, Qt-frei testbar gekapselt):
  erzeugt lazy – erst beim ersten 3D-Wunsch, nie beim App-Start –
  `QOpenGLContext` (Format 2.1) + `QOffscreenSurface`, prüft `create()`,
  `makeCurrent()`, `isOpenGLES()` und die Verfügbarkeit der
  Versionsfunktionen; Ergebnis ist ein strukturiertes
  `RendererCapability` (ok, GL-Vendor/-Renderer/-Version als
  Diagnosestring, sonst Fehlerklasse + i18n-Key). Das Ergebnis wird je
  Sitzung gecacht; „Erneut versuchen" (UX-Vertrag) verwirft den Cache
  kontrolliert.
- Diagnose-Logs nennen Backend, erkannte Capability und Fehlerklasse
  (`logging_config`-Logger), aber keine Bild-/Nutzerdaten.

### Verbindlicher Fallback

| Auslöser | Verhalten |
|---|---|
| Probe scheitert (kein Kontext, ES-only, fehlende Funktionen) | 3D-Umschalter deaktiviert mit erklärendem Text; 2D-Vorschau (alle fünf `PreviewMode`) bleibt der garantierte Pfad |
| Fehler bei Viewer-Init (`initializeGL`, Shader-Compile, Buffer-Alloc) | Viewer zeigt den Fehlerzustand aus dem UX-Vertrag mit Aktionen „2D-Relief anzeigen" und „Erneut versuchen"; kein Auto-Retry-Loop (Retry nur je expliziter Nutzeraktion) |
| Kontextverlust/Treiberabsturz zur Laufzeit | wie Init-Fehler; CPU-Meshkopie erlaubt Re-Upload nach erfolgreichem Retry |
| Ressourcenmangel (Budget-Ablehnung, Alloc-Fehler) | automatisch eine Qualitätsstufe herab; unterhalb der kleinsten Stufe → Fehlerzustand |
| Jeder der Fälle | Projektbearbeitung, Undo/Redo, Speichern und Export laufen unverändert weiter: der Viewer ist reiner Konsument, alle GL-Aufrufe der Widget-Hooks sind gekapselt und propagieren keine Exceptions in den Event-Loop |

Die 2D-Hillshade-Vorschau bleibt unverändert bestehen (Nicht-Ziel:
keine Ablösung); Export schreibt weiterhin ausschließlich das
COLOR-Komposit bzw. die EufyMake-Assets – **kein** 3D-Zustand beeinflusst
das Exportergebnis, der Viewer hat keinerlei Schreibpfad ins Modell.

## Geometrie- und Ressourcenvertrag

### Koordinatensystem und HEIGHT→Z

- Rechtshändiges System: **+X** = Bildspalten nach rechts, **+Y** = Bild-
  „oben" (Zeile 0 hat den größten Y-Wert), **+Z** = aus der Ebene zum
  Betrachter; **hell = hoch = +Z** (konsistent zu `HeightSemantics`).
- Ursprung im Zentrum der Grundfläche. Die längere Bildseite spannt das
  Weltmaß 1,0 auf; die kürzere folgt dem **Seitenverhältnis** (bei
  gesetzter physischer Größe `project.physical_size_mm` deren Verhältnis,
  sonst das Pixelverhältnis). Grid-Vertices liegen auf Pixel-/Zellzentren
  des decimierten Felds; Ränder sind die äußersten Zellzentren.
- `z_norm = values / max_value ∈ [0, 1]` (float32; funktioniert für
  `max_value` 255 **und** 65535 äquivalent – kein fester 0..255-Bereich).
  `z_welt = z_norm × 0,1 × Überhöhung` (bei Überhöhung 1,0 entspricht der
  volle Höhenumfang 10 % der längeren Grundkante – flaches Druckrelief als
  neutraler Standard). Überhöhung ist **reiner Anzeigeparameter**
  (Uniform bzw. Rebuild-freier Faktor); kanonische Werte werden nie
  verändert.
- Dreieck-Winding: **CCW von +Z** betrachtet; gerendert wird doppelseitig
  (kein Backface-Culling – Nutzer dürfen unter das Relief orbiten, das
  Budget trägt das).

### Transparenz/„kein Material"

- Die decimierte Coverage wird pro Grid-Vertex mit fester Schwelle
  binärisiert: gültig ⇔ `coverage_dez ≥ 128`. Ein Dreieck entsteht nur,
  wenn **alle drei** Vertices gültig sind → echte Löcher, keine
  Brückendreiecke über ungedeckte Bereiche.
- Randflächen („Skirts") sind **kein** MVP-Bestandteil (Stretch-Ziel);
  Löcher zeigen die Hintergrundfarbe. Kleine Inseln unterhalb einer
  Grid-Zelle können durch Decimation verschwinden – dokumentierte,
  deterministische Regel; das pixelgenaue Referenzbild bleibt die
  2D-Vorschau.

### Harte Budgets

Alle Grenzen gelten **nach** Decimation und sind von der Quellauflösung
unabhängig; ein 40-MP-Bild erzeugt zu keinem Zeitpunkt ein
Vollauflösungs-Mesh (Decimation läuft **vor** jeder float-Expansion auf dem
`uint16`-Feld).

| Qualitätsstufe | Grid (längere Seite) | max. Vertices | max. Dreiecke | VBO (32 B/V) | IBO (12 B/△) |
|---|---|---|---|---|---|
| Hoch | ≤ 1024 | ≤ 1 048 576 | ≤ 2 093 058 | ≤ 33,6 MB | ≤ 25,2 MB |
| Standard (Default) | ≤ 512 | ≤ 262 144 | ≤ 522 242 | ≤ 8,4 MB | ≤ 6,3 MB |
| Reduziert (Software-GL/CI) | ≤ 256 | ≤ 65 536 | ≤ 130 050 | ≤ 2,1 MB | ≤ 1,6 MB |

- **GPU-Budget gesamt:** ≤ 80 MB (VBO + IBO + optionale COLOR-Textur
  ≤ 2048×2048 RGBA = 16,8 MB + Framebuffer). Übergroße Uploads werden vom
  Viewer kontrolliert abgelehnt (Fallback-Tabelle).
- **CPU-Zwischenarrays (Mesh-Build):** ≤ 128 MB transient am
  Hoch-Budget (Herleitung 1024²: z 4 MB + Gitterkoordinaten 8 MB +
  Positionen 12 MB + Gradienten 8 MB + Normalen 12 MB + Normierung 4 MB +
  Indizes 25 MB + Interleave 34 MB ≈ 107 MB). Das Downsampling des
  `uint16`-Quellfelds arbeitet zeilenbandweise mit hartem 64-MiB-Deckel
  (Muster von `height_ops._MEDIAN_MAX_TEMP_BYTES`, #365).
- **CPU-Mesh-Kopie:** genau **eine** persistente Kopie des aktuellen
  Meshes (≤ 60 MB bei „Hoch") für Re-Upload nach Kontextverlust; wird beim
  Qualitäts-/Projektwechsel ersetzt, nie akkumuliert.
- **Cache:** genau **ein** gültiges Mesh (das aktuelle) + höchstens ein im
  Bau befindliches; keine Mesh-Historie. Zusammen mit den
  HEIGHT-Budgets aus #586 (40 MP: 280 MB je Ebene inkl. Ansicht) bleibt
  der 3D-Zusatz ≤ 128 MB CPU + ≤ 80 MB GPU.

### Herleitung für 1/16/40 MP

| Quelle | Beispielmaß | Grid „Standard" | Vertices | Bemerkung |
|---|---|---|---|---|
| 1 MP | 1000×1000 | 512×512 | 0,26 M | Downsample ×~2 |
| 16 MP | 4000×4000 | 512×512 | 0,26 M | Downsample ×~8 |
| 40 MP | 7746×5164 | 512×341 | 0,17 M | längere Seite 512, Seitenverhältnis erhalten |
| 40 MP, „Hoch" | 7746×5164 | 1024×683 | 0,70 M | bleibt unter dem 1,05-M-Deckel |

Die Vertexzahl ist damit **bildmaßunabhängig** gedeckelt; gemessene
Build-Zeiten (Evidenz Nr. 5) liegen bei ≈ 37 ms (512²) bzw.
≈ 310–370 ms (1024²) auf Container-CPU.

### Decimation

- Verfahren: **Block-Mittelung** (Area-Downsampling) des `uint16`-Felds auf
  das Zielgrid – deterministisch, seitenverhältnis- und randerhaltend
  (äußerste Zellzentren bleiben Randpunkte), `rint`-Rundung nach
  #586-Regel. Coverage wird identisch gemittelt und erst am Vertex
  binärisiert (s. o.).
- Kanten-/Reliefcharakter: Block-Mittelung wirkt als Anti-Alias-Filter;
  als messbares Abnahmekriterium (#592) gilt der Erhalt synthetischer
  Referenzen (Stufe, Spitze/Impuls, Rampe, Schachbrett): Rampen bleiben
  monoton, Stufenlage verschiebt sich ≤ 1 Grid-Zelle, globales
  Min/Max des decimierten Felds weicht ≤ 1 Quantisierungsstufe vom
  blockgemittelten Ideal ab. Ein kantenerhaltendes Verfahren (z. B.
  Min/Max-Pyramide) ist Stretch-Ziel, nicht MVP.

### Datenfluss und Kopieninventar

```
Layer.height_data (HeightField, kanonisch, unveränderlich  – #586)
  │  (1) Block-Mittelung uint16 → Zielgrid   [zeilenbandweise, ≤ 64 MiB Temp]
  ▼
decimiertes Feld (uint16 + coverage, ≤ Grid-Budget)
  │  (2) Geometriekern #592: float32-Positionen, -Normalen, uint32-Indizes
  ▼
Mesh-DTO (numpy, backend-neutral, frozen)                    [≤ 60 MB]
  │  (3) genau ein Upload je Mesh-Revision → VBO/IBO(/Textur)
  ▼
GPU-Puffer im QOpenGLWidget-Kontext                          [≤ 80 MB]
```

Erlaubte Vollkopien je Aktualisierung: (1) decimiertes Feld, (2) Mesh-DTO,
(3) GPU-Upload – **drei**, inventarisierbar; die Quell-Payload wird nie
kopiert oder mutiert (Tests prüfen Wertgleichheit vor/nach, #592).
Kamera, Licht und Überhöhung sind Uniforms und erzeugen **keine** Kopie.

### Cache-Invalidierung und Debounce

- **Mesh-Key** = (Content-Revision der aktiven HEIGHT-Payload,
  Canvas-Größe, Seitenverhältnis-Quelle [px oder mm], Qualitätsstufe,
  Coverage-Schwelle [konstant im MVP]). Ändert sich ein Bestandteil →
  Rebuild; sonst Wiederverwendung. Kamera, Licht, Überhöhung und
  Theme sind **nicht** Teil des Keys (reine Uniforms/UI-Zustand, analog
  Relief-Stärke in #397 – keine History-/Dirty-Revision).
- **Textur-Key** (Stretch-Stufe COLOR-Bezug) = Revision des
  COLOR-Komposits; unabhängig vom Mesh-Key.
- **Invalidierungsauslöser:** Höhen-Edit/Op-Apply, Undo/Redo auf einen
  anderen Payload-Stand, Layerwechsel der aktiven HEIGHT-Ebene,
  `Project.resize`, Projekt Neu/Öffnen/Schließen, Qualitätswechsel.
  Unveränderte Undo/Redo-Stände (gleiche Payload-Referenz, #586-Ownership)
  dürfen den Cache-Treffer wiederverwenden.
- **Debounce:** 200 ms nach der letzten geometriewirksamen Änderung startet
  genau ein Build mit **Generation-ID**; ein bereits laufender Build wird
  kooperativ abgebrochen (Cancel-Token, Reaktionsbudget ≤ 100 ms an den
  Bandgrenzen des Downsamplings). Ergebnisse mit veralteter Generation-ID
  werden verworfen, nie angezeigt (#594 testet erzwungene
  Out-of-Order-Abschlüsse). Live-Vorschauen (`preview_height_op`) triggern
  keinen 3D-Rebuild; erst der Commit (`apply_height_op`) erhöht die
  Content-Revision.

## Messziele und Referenzumgebung

| Metrik | Zielwert | Umgebung |
|---|---|---|
| Zeit bis erste 3D-Vorschau (Klick → erster Frame, 40-MP-Quelle, Standard-Qualität) | ≤ 1,5 s | Referenz-HW |
| Interaktion Orbit/Pan/Zoom (Standard-Qualität) | ≥ 30 fps | Referenz-HW |
| Aktualisierung nach Höhen-Edit (Debounce-Ende → Frame) | ≤ 500 ms | Referenz-HW |
| Peak-Zusatzspeicher 3D (CPU) | ≤ 128 MB | überall |
| GPU-Puffer gesamt | ≤ 80 MB | überall |
| CI-Render-Smoke (llvmpipe, Grid ≤ 64²) | ≤ 500 ms/Frame | CI-Container |

- **Referenz-HW:** integrierte GPU ab ~2018 (Intel UHD 620 / Apple M1,
  8 GB RAM) – bewusst konservativ; llvmpipe-Messwerte dieses ADRs bilden
  die untere Schranke (0,52 M Dreiecke ≈ 12 fps in Software → Hardware-GL
  liegt um Größenordnungen darüber, die reduzierte Stufe bleibt selbst in
  Software interaktiv).
- **CI-Messumgebung:** dieser Container (Werte oben); Benchmarks laufen
  über die bestehende `benchmark.yml`-Infrastruktur (Baseline als
  Workflow-Artefakt, #546) und werden in #595 als Abnahmeprotokoll
  festgehalten. Messmethode: `time.perf_counter()`-Probes wie im Anhang.

## Headless-/Offscreen-Teststrategie

Drei Schichten (Marker-Modell analog `ui`/`ui_smoke`):

1. **Logiktests (überall, `make test`):** Geometriekern #592 (Qt-frei,
   kein GL, deterministisch – Ebene/Rampen/Stufe/Impuls/Masken-Inseln,
   Property-Tests, Budget-Grenzen), Kamera-/Orbit-Mathematik,
   Capability-Gate mit gemockter Probe, Zustandsmaschine des Viewers.
   Der Repo-Standardpfad (`offscreen` ohne GL) testet den
   **Fallback-Zweig unverfälscht echt** – genau dort liefert
   `QOpenGLContext.create()` real `False` (Evidenz Nr. 1).
2. **Offscreen-Render-Smokes (neuer Marker `gl_smoke`, nightly + lokal
   optional):** Xvfb + `offscreen`-Plugin + llvmpipe (belegt
   funktionsfähig); initialisiert Backend, lädt ein ≤ 64²-Mesh, rendert
   einen Frame in ein FBO, prüft **strukturelle Invarianten** statt
   Golden-Pixeln (lichtzugewandte Rampenseite heller als abgewandte,
   Loch-Pixel = Hintergrund, flaches Feld uniform) und gibt Ressourcen
   frei. Solche Asserts sind treibertolerant per Konstruktion –
   pixelgenaue Goldens über Treibergrenzen sind ausdrücklich
   ausgeschlossen; wo Bildvergleiche nötig werden, gelten
   Toleranzen auf Aggregatwerte (mittlere Helligkeit ± 10 %), nie
   Bitgleichheit.
3. **Manuelle Plattform-Smokes (#595):** Checkliste je Artefaktklasse
   (AppImage/DEB × x86_64/aarch64, DMG arm64): 3D öffnen, Orbit, Fallback
   erzwingen (`QT_OPENGL`-Override bzw. VM ohne GL), High-DPI-Probe.
- **Fehler-Injection:** Probe-Mock (kein Kontext/ES-only), Shader-Compile-
  Fehler (defekter Quelltext-Hook), Buffer-Alloc-Fehler (Budget künstlich
  klein), Kontextverlust (Injektionspunkt im Widget), abgebrochener
  Mesh-Build (Cancel-Token mitten im Banddurchlauf).
- **Packaging-Smokes:** alle fünf Artefaktklassen erhalten im
  Abnahmeplan (#595) einen 3D-Start-Smoke **und** einen erzwungenen
  Fallback-Smoke; Offscreen-Start ohne GL bleibt Pflichtpfad (CI-Realität).

## Konsequenzen und stufenweiser Umsetzungsplan

- **#592 – Geometriekern:** setzt „Koordinatensystem/HEIGHT→Z",
  „Transparenz", „Budgets", „Decimation", „Datenfluss" um; Qt-frei,
  strikt getypt (`disallow_untyped_defs`), Ausgabeformat = frozen
  numpy-DTO dieses ADRs; Cache-Key + Cancel-Token + Referenz-/Property-
  Tests.
- **#593 – Viewer:** `QOpenGLWidget`-Widget, GL-2.1-Pfad (+ 4.1-Core
  optional), Capability-Probe, Fallback-Tabelle, Kamera-/Input-Vertrag
  aus [UX_3D_PREVIEW.md](../UX_3D_PREVIEW.md), Ressourcen-Lifecycle
  (`aboutToBeDestroyed`, Re-Upload nach Kontextverlust), `gl_smoke`-Marker.
- **#594 – Integration:** Einbauort/Umschalter gemäß UX-Vertrag,
  Debounce/Generation-IDs, Cache-Invalidierungsmatrix, i18n-Keys
  (`preview3d.*`), QSettings nur für UI-Präferenzen (Qualität,
  Überhöhung; keine Meshes).
- **#595 – Abnahme:** Benchmarks gegen die Zieltabelle, fünf
  Packaging-Smokes, Doku/Screenshots/i18n, Abschlussmatrix.
- 2D-Pipeline (`PreviewMode`, `relief_preview`, Export) bleibt in allen
  Stufen unverändert und regressionsgetestet.

## Offene Risiken und Stretch-Ziele

- **Apple-OpenGL-Deprecation:** GL 4.1/CGL ist auf macOS 15 (arm64)
  funktional, aber deprecated. Absicherung: backend-neutraler
  Geometriekern + Capability-Probe + 2D-Fallback; Beobachtungspunkt je
  macOS-Major-Release im Release-Smoke (#595). Ein späterer
  Viewer-Tausch auf QtQuick3D/QRhi bliebe auf #593-Umfang begrenzt.
- **llvmpipe-Verfügbarkeit aarch64:** Mesa/llvmpipe existiert für
  aarch64-Ubuntu; der native aarch64-Smoke (#595) verifiziert das
  real – bis dahin gilt der Fallback-Pfad als Abnahmekriterium.
- **Treiber-Zoo unter Linux:** abgefangen durch Probe + Fehlerzustände
  statt Annahmen; Diagnosestring (Vendor/Renderer/Version) landet im Log.
- **Stretch-Ziele (blockieren den MVP nicht):** COLOR-Komposit als
  Textur (eigener Textur-Key, Options-Gating), Skirts an Coverage-
  Rändern, kantenerhaltende Decimation (Min/Max-Pyramide),
  Drahtgitter-Modus, Pinch-Gesten, 4.1-Core-Only-Optimierungen.

## Anhang: Messmethode (Kurzfassung)

Capability-/Render-Probe (Kern; vollständige Skripte im Issue-Verlauf):

```python
fmt = QSurfaceFormat(); fmt.setVersion(2, 1)
ctx = QOpenGLContext(); ctx.setFormat(fmt)
ok = ctx.create()                      # offscreen ohne X: False (Evidenz 1)
surface = QOffscreenSurface(); surface.setFormat(ctx.format()); surface.create()
ctx.makeCurrent(surface)
profile = QOpenGLVersionProfile(); profile.setVersion(2, 1)
funcs = QOpenGLVersionFunctionsFactory.get(profile, ctx)  # 2.1er-Funktionssatz
```

Mesh-Build-Benchmark: `uint16`-Zufallsfeld → float32-`z`, `np.gradient`-
Normalen, uint32-Grid-Indizes; llvmpipe-Draw: interleaved VBO (pos+normal,
24 B/Vertex), Lambert-Fragment-Shader, `glDrawElements` + `glFinish` in ein
800×600-FBO mit Depth-Attachment; Zeiten `time.perf_counter()`.
