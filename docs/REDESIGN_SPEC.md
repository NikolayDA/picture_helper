# REDESIGN_SPEC — Geführter Workflow (Prototyp A)

Maßgebliche Wertquelle des UI-Redesigns (Epics #413 Karten-Inspector,
#418 Geführter Workflow, #424 Design-System & Theming). Die §-Verweise in
Code-Kommentaren und Tests (z. B. „Spec §6", „§5.3") zeigen auf die
Abschnitte dieser Datei.

> **Herkunft.** Die Werte stammen 1:1 aus dem abgenommenen Browser-Prototyp
> „Prototyp A – Geführter Workflow", der als Standalone-Bundle unter
> `design/Prototyp A - Geführter Workflow.dc.html` im Repository liegt.
> Diese Spezifikation wurde im Epic-Review zu #418 aus der Referenz-
> Implementierung rekonstruiert und beim Einchecken des Prototyps gegen
> dessen Kernwerte geprüft (Layout-Maße, Stepper-Kreise, Radien,
> Schritt-Labels – deckungsgleich). Kanonische Wertquelle bleibt **diese
> Datei**; der Prototyp ist das Referenz-Artefakt. Weicht der Code ab,
> gilt: Code-Änderung nur mit gleichzeitiger Anpassung dieser Datei
> (Drift-Disziplin wie bei der Qt-apt-Paketliste).

## §1 Layout & Raster

Vertikaler Stapel: Menüleiste → **Schrittleiste** (volle Breite) → Body →
Statusleiste. Der Body hat drei Spalten: Werkzeugleiste | Leinwand (flex) |
Inspector.

| Größe | Wert | Konstante |
|---|---|---|
| Fenster-Minimum | 1100 × 720 px | `_WINDOW_MIN_W`/`_WINDOW_MIN_H` |
| Schrittleiste Höhe | 72 px | `Stepper.setFixedHeight` |
| Werkzeugleiste Breite | 62 px | `_TOOLBAR_WIDTH` |
| Werkzeug-Button | 44 × 44 px | `_TOOLBAR_BTN_SIZE` |
| Werkzeug-Icon | 22 px | `_TOOLBAR_ICON_SIZE` |
| Inspector Breite | 332 px | `_RIGHT_PANEL_WIDTH` |
| Crop-Bestätigungsleiste | 46 px | `_CROP_BAR_HEIGHT` |
| Navigations-Fußzeile | 62 px | `right_panel._assemble` |

Scrollbereich der Schritt-Seiten: Innenabstand **18 / 20 / 18 / 18** px
(links/oben/rechts/unten), Abstand zwischen Karten **11 px**. Nutzbare
Kartentextbreite: `332 − 2·18 − 2·14 = 268 px` (`_CARD_TEXT_WIDTH`).

## §2 Farb-Tokens — dunkles Schema (Standard)

Alle Farben laufen über das Token-System `theme.Palette`; direkte Hex-Werte
in Widgets sind untersagt. Werte des dunklen Schemas (`theme.DARK`):

| Token | Wert | Rolle |
|---|---|---|
| `bg` | `#1f242b` | Leinwand-Umfeld |
| `panel` / `inspector` | `#1a1a1a` | Panelflächen |
| `tabbar` | `#141414` | (Alt-)Tab-Leiste |
| `stepper` | `#161a20` | Schrittleiste |
| `nav` | `#20252e` | Navigations-Fußzeile |
| `status` | `#1a1a1a` | Status-/Menüleiste |
| `toolbar` | `#242424` | Werkzeugleiste |
| `border` / `divider` / `hairline` | `#3a3a3a` / `#2a2a2a` / `#333333` | Linien |
| `surface` / `surface_hover` | `#2a2a2a` / `#363636` | Bedienflächen |
| `hover` | `rgba(255,255,255,.06)` | Hover-Schleier |
| `card_bg` / `card_border` | `#22262d` / `rgba(255,255,255,.07)` | Karten |
| `text` / `text2` / `text3` | `#e0e0e0` / `#cdd4de` / `#8b94a2` | aktiver Text |
| `muted` | `#727b89` | **nur** Disabled/Placeholder |
| `accent` / `accent2` | `#4a90d9` / `#3f7fce` | Blau (Aktion) |
| `accent_soft` / `accent_line` | `rgba(74,144,217,.16)` / `rgba(74,144,217,.42)` | Akzentflächen/-linien |
| `accent_text` / `on_accent` | `#9fc0ff` / `#ffffff` | Text auf/zu Akzent |
| `good` / `good_soft` | `#7fe0aa` / `rgba(80,200,140,.16)` | positiv |
| `bad` / `bad_soft` | `#f29aa6` / `rgba(229,104,122,.16)` | negativ |

**Token-Vertrag:** `text`/`text2`/`text3` halten auf ihren Flächen ≥ 4.5:1
(WCAG AA); `muted` ist ausschließlich für Disabled-/Placeholder-Zustände
reserviert (§12).

## §3 Farb-Tokens — helles Schema

Gleiches Token-Set, Ausprägung `theme.LIGHT` (Auszug; vollständig in
`theme.py`): `bg #e9edf3`, `panel #f2f4f8`, `inspector #f5f7fb`,
`stepper #eef1f6`, `nav #eaeef3`, `toolbar #e6eaf1`, `surface #ffffff`,
`card_bg #ffffff`, `text #1b2230`, `text2 #3a4351`, `text3 #59626f`
(bewusst dunkel genug für ≥ 4.5:1 auf der Statusleiste), `muted #8b95a3`,
`accent #3a6fd0`, `accent2 #2f5fcf`, `on_accent #ffffff`,
`good #1f9d63`, `bad #d65060`. Umschaltung: §10.

## §4 Typografie

Systemschrift (Qt-Default), Größen in px:

| Verwendung | Größe / Gewicht |
|---|---|
| Inspector-Kopf: Schritt-Titel | 16 / 700 |
| Inspector-Kopf: Beschreibung | 12 / 400, `text3` |
| Stepper-Label | 13 / 400 (aktiv 700) |
| Stepper-Kreisziffer | 12 / 600 |
| Kartentitel (§5.2) | 11 / 700, VERSALIEN, letter-spacing .05em |
| Buttons | 12–13 / 500–600 |
| Statusleiste | 11 / 400 |

## §5 Komponenten

### §5.1 Karten
Radius **12**, Füllung `card_bg`, Rand 1 px `card_border`, Innenpolster
**14 / 13** px (horizontal/vertikal), Binnenabstand 10 px, Kartenabstand im
Stapel 11 px (§1). Objektname `sectionCard` (bzw. `recentCard`), damit der
Kartenstil nicht auf Kindwidgets kaskadiert.

### §5.2 Sektionsköpfe
Kartentitel in **VERSALIEN**, 11 px/700, letter-spacing .05em, Farbe `text2`,
links ein **3 px blauer Akzentstrich** (`accent`), Padding 2/0/4/8. Immer
Akzentfarbe – keine Amber-/Coral-Sonderfarben (Issue #416).

### §5.3 Sekundärbuttons
Neutrale Fläche `surface`, Text `text2`, 1 px `border`, Radius 8, 12 px,
min-Höhe 34–36 px. **Kein Zeilenumbruch**, außer explizit erlaubt
(EufyMake-Button, fontmetrischer Umbruch auf `_CARD_TEXT_WIDTH`).
Ausgewählter Zustand `.sel`: Fläche `accent_soft`, Text `accent_text`,
1 px `accent`-Rand (z. B. „Anwenden" der Farbkorrektur).

### §5.4 Primärbutton
Blauer Verlauf `accent → accent2`, Text `on_accent`, Radius 9, 13 px/600,
min-Höhe 40 px. Für die hervorgehobene Aktion eines Schritts (Datei
öffnen, KI-Freistellen, Höhenkarte erzeugen).

### §5.5 Slider & Zahlenfelder
Slider: Groove 4 px (`border`-Ton, Radius 2), Griff 14 px `accent`
(Radius 7), Fokus = 2 px Rand am Griff; Klickziel ist der gesamte Groove.
QSpinBox/QComboBox: `surface`, 1 px `border`, Radius 6, 12 px,
min-Höhe 24 px (#441).

### §5.6 Semantische Buttons & Checkboxen
Erweitern/Schrumpfen (`.bs`, §9 Schritt 2) sind die einzige Ausnahme mit
semantischen Tönen: Fläche `good_soft`/`bad_soft`, Text und 1 px Rand
`good`/`bad`, Radius 8, min-Höhe 34 px. Checkboxen folgen der QPalette
(§10) und dem app-weiten Fokusring.

### §5.7 Segmented-Control
Vorschaumodus in Schritt 6: Segmente **Farbe / Relief / Höhe / Gloss** als
zusammenhängende Schaltergruppe; der kombinierte Modus bleibt bewusst
außen vor (nur über das Ansicht-Menü, §9 Schritt 6). Auswahl im
`.sel`-Look (§5.3).

### §5.8 Ablagefeld & Listenzeilen
Ablagefeld (Schritt 1): 2 px **gestrichelter** `border`-Rand, Radius 12,
transparent; Fokus färbt die Strichlinie `accent`. Listenzeilen („Zuletzt
geöffnet", max. 3): transparent, Padding 7/8, Radius 8, Hover `hover`.

### §5.9 Werkzeugleiste
Breite 62 px, Buttons 44 × 44 px (Icons 22 px), ruhen **transparent** in der
Leiste; aktiv nur sanft akzent-getönt (`accent_soft`-Fläche,
`accent_line`-Rand, `accent_text`) – kein voller Farbfüllton.
History-Gruppe (Undo/Redo/Original/Verlauf) auf `surface`, Radius 9.
Trenner zwischen Gruppen: **30 × 1 px**, zentriert, `hairline`.
Reihenfolge von oben: W · B · E · L | Trenner | KI | Trenner |
Undo · Redo · Original · Verlauf | (Dehner) | Öffnen · Speichern.

## §6 Schrittleiste (Stepper)

Sechs Schritte: **Öffnen · Freistellen · Anpassen · Form & Maße ·
Relief & Ebenen · Export**. Leiste 72 px hoch, Fläche `stepper`, 1 px
`border`-Unterkante, seitlicher Rand 26 px; Zellen durch 2 px-Verbinder
getrennt (gefüllt `accent_line` bis einschließlich zum aktiven Schritt,
sonst `hairline` – nicht der dunklere Divider-Ton).

Zelle: Kreis + Label, min-Höhe 32 px (Trefferfläche §12), Innenabstand
6/2, Abstand Kreis↔Label 9 px. Zustände:

| Zustand | Kreis | Label |
|---|---|---|
| **aktiv** | **28 px**, Füllung `accent`, Ziffer `on_accent` 12/600 | `text` 13/700 |
| erledigt | 26 px, `accent_soft`, **✓** `accent_text`, 1 px `accent_line` | `text3` 13 |
| ausstehend | 26 px, transparent, Ziffer `text3`, 1 px `border` | `text3` 13 |
| gesperrt | wie ausstehend, Ziffer `divider` | `muted` |

Der aktive Kreis ist bewusst 2 px größer (Fokusring-Präsenz des Prototyps;
Qt-QSS kennt kein `box-shadow`). **Kein Fokusrahmen / keine Tönung am
aktiven Schritt nach Maus-Klick** (#445) – Fokus-Markierung nur mit
`:focus-visible`-Semantik: ausschließlich Tastatur-Fokus (Tab/Backtab)
zeigt eine akzentgetönte, rahmenlose Fläche (`accent_soft`, Radius 8).
Gesperrte Zellen sind deaktiviert und fallen aus der Tab-Reihenfolge.

## §7 Navigation (Zurück / Weiter)

Fixe Fußzeile des Inspectors, **immer sichtbar** (außerhalb der
Scrollfläche): 62 px hoch, Fläche `nav`, 1 px `border`-Oberkante,
Innenabstand 18 px, Button-Abstand 10 px.

- **Zurück** (sekundär, links): „← Zurück", transparent, 1 px `border`,
  Radius 9, min-Höhe 36 px; in Schritt 1 deaktiviert.
- **Weiter** (primär, füllt den Rest): Fläche `accent`, Text `on_accent`,
  Radius 9, 13/600. Beschriftung nennt das Ziel: „Weiter: Freistellen →",
  „Weiter: Anpassen →", „Weiter: Form & Maße →", „Weiter: Relief &
  Ebenen →", „Weiter: Export →"; in Schritt 6 „**Exportieren ✓**" und löst
  das Speichern aus. In Schritt 1 ohne Bild öffnet „Weiter" den
  Datei-Dialog.

Beide Buttons sind per Tab erreichbar; `&` in Beschriftungen wird als
`&&` escaped (Qt-Mnemonics, §11).

## §8 Werkzeuge je Schritt

Die linke Werkzeugleiste ist kontextuell:

| Werkzeuggruppe | sichtbar/aktiv |
|---|---|
| Auswahl: Zauberstab / Pinsel / Radierer / Lasso (+ Trenner) | **nur Schritt 2 (Freistellen)** |
| KI-Freistellen, Undo/Redo/Original/Verlauf, Öffnen/Speichern | immer |
| Verschieben / Zoom (Canvas-Gesten) | immer |

Regeln:

- Die Kürzel **W/B/E/L** greifen nur, wenn das Werkzeug im aktuellen
  Schritt verfügbar ist – außerhalb von Schritt 2 sind die QShortcuts
  deaktiviert (#422).
- Außerhalb von Schritt 2 ist zusätzlich die Canvas-Werkzeug-Interaktion
  abgeschaltet (`set_tools_enabled(False)`); eine begonnene Crop-/
  Lasso-Interaktion wird dabei verworfen. Pan/Zoom bleiben frei.
- Die Höhen-Werkzeuge (Aufhellen/Abdunkeln/Setzen/Invertieren) liegen
  **nicht** in der linken Leiste, sondern gebündelt als Karten im
  Höhen-Panel von Schritt 5 (bewusste Abweichung vom ursprünglichen
  Issue-Entwurf zu #422: ein Ort für alle Höhen-Aktionen).

## §9 Inspector — Inhalte je Schritt

Kopf jeder Schritt-Seite: Titel „Schritt *n* · *Name*" (16/700) +
einzeilige Beschreibung (12, `text3`). Darunter genau die Karten des
Schritts (ein Scrollbereich pro Seite, kein Doppel-Scroll):

1. **Öffnen** — Ablagefeld (§5.8, Klick/Enter öffnet Dialog),
   Primärbutton „Datei öffnen…", Karte „Zuletzt geöffnet" (max. 3).
2. **Freistellen** — KI-Primärbutton oben; Karten „Werkzeug-Einstellungen"
   (Toleranz, Pinselgröße), „Auswahl" (Invertieren/Aufheben,
   Erweitern/Schrumpfen `.bs` §5.6), „Hintergrund" (Farbe wählen/ersetzen,
   Kantenglättung, Entfernen).
3. **Anpassen** — Karte „Farbkorrektur": Helligkeit/Kontrast/Sättigung
   (0–200 %, neutral 100) mit Live-Vorschau; „Anwenden" im `.sel`-Look,
   „Zurücksetzen" neutral.
4. **Form & Maße** — Karten „Drehen & Spiegeln", „Ecken runden",
   „Größe ändern" (Inline-Felder B × H px + Anwenden), „Zuschnitt-Format"
   (3×2-Raster: Kreis, 1:1, 16:9, 4:3, 9:16, 3:4).
5. **Relief & Ebenen** — Ebenen-Karte (Liste, Sichtbarkeit, Rollen) und
   Höhenkarten-Karte (Beschaffen/Bearbeiten/Optimieren mit Live-Vorschau);
   Primärbutton „Höhenkarte erzeugen".
6. **Export** — Karte „2D-Vorschau" (Segmented §5.7, Relief-Stärke,
   Gloss-Checkbox; „Kombiniert" nur übers Ansicht-Menü), Karte „Speichern"
   (Formatwahl + Speichern), Karte „UV-Druck" (EufyMake-Export;
   Umbruch-Ausnahme §5.3).

## §10 Theming & Umschaltung

Token-basiert (§2/§3): Standard ist das dunkle Schema; „Heller Modus" ist
über das Ansicht-Menü umschaltbar und wird in den QSettings gemerkt
(`THEME_KEY`). Ein Umschalten wirkt live ohne Neustart: `QPalette` +
anwendungsweites QSS (`build_app_stylesheet`) für Standard-Widgets und
Dialoge, gezieltes Restyling der Redesign-Chrome (Schrittleiste,
Werkzeugleiste, Status-/Menüleiste) und Neuaufbau des rechten Panels
(färbt die verschachtelten Karten um) (#428).

## §11 Texte & Beschriftungen

Alle sichtbaren Texte laufen über `tr()` (Runtime-Sprachen de/en).
Kanonische Schrittnamen (de): **Öffnen · Freistellen · Anpassen ·
Form & Maße · Relief & Ebenen · Export**. Kartentitel VERSALIEN (§5.2);
Weiter-Labels im Format „Weiter: *Ziel* →" (§7); Statuszeile beim
Schrittwechsel „Schritt *n*/6: *Name*" (§13). In `QPushButton`-Texten wird
`&` als `&&` escaped, sonst verschluckt Qt das Zeichen als
Mnemonic-Marker („Relief & Ebenen").

## §12 Barrierefreiheit

- **Kontrast:** aktiver Text ≥ 4.5:1 (Token-Vertrag §2); `muted` nur für
  Disabled/Placeholder (WCAG-1.4.3-Ausnahme).
- **Trefferflächen:** ≥ 32 px (Stepper-Zellen min. 32 px – der Kreis ist
  nur Indikator, klickbar ist die ganze Zelle; Werkzeug-Buttons 44 px;
  Zahlenfelder min. 24 px hoch bei voller Zeilenbreite) (#441).
- **Tastatur:** Stepper-Zellen fokussierbar (Tab-Reihenfolge = Schritt-
  folge 1→6), Enter/Leertaste aktiviert; gesperrte Zellen ohne Fokus;
  `:focus-visible`-Semantik (§6); Ablagefeld fokussierbar (Enter/Leertaste
  = Dialog); app-weiter Fokusring 1 px `accent` (#429); Kürzel W/B/E/L nur
  im passenden Schritt (§8), Escape bricht Interaktionen ab.

## §13 Zustandsmodell

Der aktive Schritt lebt im `MainWindow` (`WorkflowStep`, 1-basiert); die
Schrittleiste selbst ist zustandslos.

- **Ohne Bild:** nur Schritt 1 bedienbar; Schritte 2–6 gesperrt
  (Stepper-Zellen deaktiviert). Klick auf einen gesperrten Schritt zeigt
  den Statushinweis „Erst ein Bild öffnen (Schritt 1)" und behält den
  aktiven Schritt. „Weiter" öffnet den Datei-Dialog (§7).
- **Bild geladen** (Bild-Datei oder Projekt mit Bild): alle Schritte frei;
  es geht **immer** automatisch zu Schritt 2 (Freistellen) – auch wenn ein
  späteres Bild einen bereits fortgeschrittenen Schritt ersetzt.
- **Schrittwechsel** (Klick, Zurück/Weiter) aktualisiert atomar:
  Schrittleiste (erledigt/aktiv/ausstehend + Verbinder), Inspector
  (Seite, Kopf, Weiter-Label), Werkzeugleiste inkl. Kürzel (§8),
  Canvas-Werkzeug-Gate und Statuszeile („Schritt *n*/6: *Name*").
- **Schritt 6:** „Exportieren ✓" löst das Speichern aus und bleibt im
  Schritt.
- **Vorschau-Zustand** (Modus/Relief-Stärke/Gloss, Schritt 6) ist reiner
  UI-Zustand: keine History-/Dirty-Revision, der Export schreibt weiterhin
  ausschließlich das COLOR-Komposit (#387/#397).
