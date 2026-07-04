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
| Werkzeug-Icon | 20 px (Rail-Fuß 18 px) | `_TOOLBAR_ICON_SIZE` / `_FOOT_ICON_SIZE` |
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
| `panel` / `inspector` | `#272d36` | Panelflächen |
| `tabbar` | `#141414` | (Alt-)Tab-Leiste |
| `stepper` | `#1c2128` | Schrittleiste |
| `nav` | `#222831` | Navigations-Fußzeile |
| `status` | `#1a1e24` | Status-/Menüleiste |
| `toolbar` | `#242a32` | Werkzeugleiste |
| `border` / `border_2` | `rgba(255,255,255,.06)` / `rgba(255,255,255,.12)` | Ränder (Standard/sekundär) |
| `divider` / `hairline` | `#2a2a2a` / `rgba(255,255,255,.1)` | Trennlinien |
| `surface` / `surface_hover` | `#30373f` / `#3a424c` | Bedienflächen |
| `hover` | `rgba(255,255,255,.05)` | Hover-Schleier |
| `card_bg` / `card_border` | `#262b33` / `rgba(255,255,255,.07)` | Karten |
| `glass` | `rgba(26,30,37,.82)` | schwebende Canvas-Overlays (Zoom-Pille §14) |
| `text` / `text2` / `text3` | `#e9edf3` / `#cdd4de` / `#8b94a2` | aktiver Text |
| `muted` | `#727b89` | **nur** Disabled/Placeholder |
| `accent` / `accent2` | `#4a90d9` / `#3f7fce` | Blau (Aktion) |
| `accent_soft` / `accent_line` | `rgba(74,144,217,.16)` / `rgba(74,144,217,.42)` | Akzentflächen/-linien |
| `accent_text` / `on_accent` | `#9fc0ff` / `#ffffff` | Text auf/zu Akzent |
| `good` / `good_soft` | `#7fe0aa` / `rgba(80,200,140,.16)` | positiv |
| `bad` / `bad_soft` | `#f29aa6` / `rgba(229,104,122,.16)` | negativ |

**Token-Vertrag:** `text`/`text2`/`text3` halten auf ihren Flächen ≥ 4.5:1
(WCAG AA); `muted` ist ausschließlich für Disabled-/Placeholder-Zustände
reserviert (§12).

**Herkunft der Werte (#475/#476).** Die Hintergrund-/Flächen- und Randwerte
sind 1:1 aus den CSS-Variablen des dunklen `:root`-Blocks im Prototyp-Bundle
(`design/Prototyp A - Geführter Workflow.dc.html`) übernommen, mit zwei
dokumentierten, bewussten Abweichungen:

- **`status` deckt nur die Statusleiste ab.** Die Menüleiste teilt sich
  stattdessen den `toolbar`-Ton (`menu_style`) – wie im Prototyp, wo
  `--menubar` und `--rail` denselben Wert tragen. Eine reine
  Fenster-Titelleiste (Prototyp: `--titlebar`) entfällt ohne Ersatz-Token, da
  die App das native Fenster-Chrome von macOS/Linux nutzt.
- **`card_bg` ist dunkler als der Prototyp-Wert `#2e353f`.** Bei der
  Prototyp-Helligkeit unterschreitet `text3` (`#8b94a2`) auf Karten den
  WCAG-AA-Kontraktrag von ≥ 4.5:1 (§12, `test_palettes_meet_wcag_contrast_matrix`).
  `#262b33` ist der hellstmögliche Wert in Richtung des Prototyps, der den
  Kontrakt noch einhält – der Prototyp selbst ist kein kontrastgeprüftes
  Artefakt und geht in diesem einen Fall nicht vor Barrierefreiheit. Aus
  demselben Grund bezieht `LayerPanel` inaktive Zeilennamen (`text3`) auf
  `card_bg` statt auf das hellere `surface`.

`border`/`hairline` sind bewusst teiltransparente Weiß-Overlays statt
opaker Grautöne: Sie setzen sich je nach Untergrund (Karte, Panel,
Glas-Pille …) unterschiedlich ab, statt auf jeder Fläche gleich hart zu
wirken. `border_2` ist der sekundäre Rand-Ton für neutrale Sekundärbuttons
(§5.3, Prototyp-Klasse `.bs`) und im hellen Schema bereits 1:1 der
Prototyp-Wert (`rgba(22,32,52,.16)`); `border`/`hairline` selbst bleiben im
hellen Schema vorerst unverändert (siehe #480).

## §3 Farb-Tokens — helles Schema

Gleiches Token-Set, Ausprägung `theme.LIGHT` (Auszug; vollständig in
`theme.py`): `bg #e9edf3`, `panel #f2f4f8`, `inspector #f5f7fb`,
`stepper #eef1f6`, `nav #eaeef3`, `toolbar #e6eaf1`, `surface #ffffff`,
`card_bg #ffffff`, `glass rgba(255,255,255,.86)`,
`text #1b2230`, `text2 #3a4351`, `text3 #59626f`
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
Neutrale Fläche `surface`, Text `text2`, 1 px `border_2`, Radius 8, 12 px,
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
Breite 62 px, Buttons 44 × 44 px (Icons 20 px, Rail-Fuß 18 px – seit
Epic #455 an den Prototyp angeglichen, vorher 22 px), ruhen **transparent**
in der Leiste; aktiv nur sanft akzent-getönt (`accent_soft`-Fläche,
`accent_line`-Rand, `accent_text`) – kein voller Farbfüllton. Auch die
Rail-Fuß-Aktionen nutzen diesen Werkzeug-Look (Prototyp-Klasse `.tool`);
die frühere `surface`-History-Gruppe ist entfallen.
Trenner zwischen Gruppen: **30 × 1 px**, zentriert, `hairline`.

Reihenfolge von oben (Epic #455): **Verschieben / Zoom** (permanent, #456)
| Trenner + W · B · E · L (nur Schritt 2) | Trenner + Aufhellen · Abdunkeln
(nur Schritt 5, #457) | (Dehner) | **Rail-Fuß** (#458): Trenner + Rückgängig ·
Wiederholen · Theme-Umschalter – bedingungslos an den unteren Rand gepinnt
und in **allen** Schritten sichtbar. KI, Original wiederherstellen, Verlauf
sowie Öffnen/Speichern liegen **nicht** in der Rail: KI ist der
Schritt-2-Primärbutton (#437), Original wiederherstellen liegt im Menü
„Bearbeiten", der Verlauf öffnet über „Ansicht → Verlauf" (Popup ankert an
der Rail), Öffnen/Speichern über Menü „Datei" (⌘O/⌘S) bzw. Schritt 1/6 des
Inspectors. Rückgängig/Wiederholen sind deaktiviert, wenn nichts
rückgängig-/wiederherstellbar ist; der Theme-Umschalter löst dieselbe
Aktion wie „Ansicht → Helles Design" aus und bleibt mit dem Menü-Häkchen
synchron.

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

Die linke Werkzeugleiste ist kontextuell (Rail-Inhalt 1:1 zum Prototyp,
Epic #455):

| Schritt | Rail-Inhalt (von oben) | Rail-Fuß (unten, alle Schritte) |
|---|---|---|
| 1 · Öffnen | Verschieben/Zoom | Trenner · Rückgängig, Wiederholen, Theme-Umschalter |
| 2 · Freistellen | Verschieben/Zoom · Trenner · Zauberstab, Pinsel, Radiergummi, Lasso | Trenner · Rückgängig, Wiederholen, Theme-Umschalter |
| 3 · Anpassen | Verschieben/Zoom | Trenner · Rückgängig, Wiederholen, Theme-Umschalter |
| 4 · Form & Maße | Verschieben/Zoom | Trenner · Rückgängig, Wiederholen, Theme-Umschalter |
| 5 · Relief & Ebenen | Verschieben/Zoom · Trenner · Aufhellen (höher), Abdunkeln (tiefer) | Trenner · Rückgängig, Wiederholen, Theme-Umschalter |
| 6 · Export | Verschieben/Zoom | Trenner · Rückgängig, Wiederholen, Theme-Umschalter |

Regeln:

- **Verschieben / Zoom** (#456) ist ein echtes, wählbares Werkzeug mit
  `.on`-Zustand: aktiv pannt Linksklick-Ziehen den Ausschnitt, das Mausrad
  zoomt; Auswahl-/Mal-Interaktion ist im Move-Modus nicht möglich. Die
  mittlere Maustaste (bzw. Alt+Linksklick) pannt in **jedem** Modus.
- Die Kürzel **W/B/E/L** greifen nur, wenn das Werkzeug im aktuellen
  Schritt verfügbar ist – außerhalb von Schritt 2 sind die QShortcuts
  deaktiviert (#422).
- Außerhalb der Schritte 2 und 5 ist zusätzlich die Canvas-Werkzeug-
  Interaktion abgeschaltet (`set_tools_enabled(False)`); eine begonnene
  Crop-/Lasso-Interaktion (oder ein laufender Höhen-Malstrich) wird dabei
  verworfen. Pan/Zoom bleiben frei.
- **Aufhellen (höher) / Abdunkeln (tiefer)** (#457) sind malende
  Rail-Werkzeuge auf der aktiven HEIGHT-Ebene: Strich mit Pinselradius
  (geteilte Pinselgröße aus Schritt 2), Stärke `_DEFAULT_HEIGHT_STEP`,
  Werte geklemmt/verlustfrei (`adjust_height`-Semantik, jedes Pixel genau
  einmal pro Strich), genau **ein** Undo-Schritt je Strich. Ohne aktive
  HEIGHT-Ebene sind die Buttons deaktiviert (Tooltip nennt den Grund); auf
  COLOR-Ebenen bleiben sie wirkungslos (Kind↔Rollen-Vertrag #364). Die
  gebündelten One-Shot-Aktionen im Höhen-Panel (Aufhellen/Abdunkeln/Setzen/
  Invertieren, Auswahl bzw. global) bleiben unverändert zusätzlich bestehen.

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
  Canvas-Werkzeug-Gate, Werkzeugwahl und Statuszeile
  („Schritt *n*/6: *Name*").
- **Werkzeugwahl je Schritt (#456):** Beim Wechsel in einen Schritt ohne
  Auswahl-/Höhen-Werkzeuge (1/3/4/6) wird „Verschieben / Zoom" sichtbar
  das aktive Werkzeug (`.on`). Zurück in „Freistellen" reaktiviert das
  zuletzt gewählte Auswahlwerkzeug (Default Zauberstab). Der Eintritt in
  „Relief & Ebenen" startet ebenfalls mit Move – die Höhen-Werkzeuge sind
  bewusst Opt-in per Klick (kein versehentliches Malen). Verliert die
  aktive Ebene den HEIGHT-Typ, während ein Höhen-Werkzeug gewählt ist,
  fällt die Wahl sichtbar auf Move zurück.
- **Schritt 6:** „Exportieren ✓" löst das Speichern aus und bleibt im
  Schritt.
- **Vorschau-Zustand** (Modus/Relief-Stärke/Gloss, Schritt 6) ist reiner
  UI-Zustand: keine History-/Dirty-Revision, der Export schreibt weiterhin
  ausschließlich das COLOR-Komposit (#387/#397). Gleiches gilt für den
  Zoom-Zustand samt Fixier-Lock (§14).

## §14 Arbeitsfläche: Zoom-Kontrolle

Unten rechts auf der Arbeitsfläche schwebt – sobald ein Bild geladen ist –
**immer** eine interaktive Zoom-Kontrolle (#464, 1:1 zum Prototyp): eine
Glas-Pille (`glass`-Fläche, `card_border`-Haarlinie, Radius 10, Abstand
14 px zur unteren/rechten Kante) mit „−" · Live-Prozentwert · „+" ·
Fixier-Schloss.

- **Wertebereich/Schrittweite:** „+"/„−" ändern den Zoom in
  10-%-Schritten, geklemmt auf **25–300 %** (`zoomBy`-Logik des
  Prototyps; Konstanten `_ZOOM_CTRL_*`). Der Mausrad-Zoom behält seine
  weiteren technischen Grenzen (`ZOOM_MIN`/`ZOOM_MAX`); die Prozentanzeige
  aktualisiert live für **jede** Zoom-Quelle (Buttons, Mausrad,
  Fit-to-View).
- **Fixier-Lock:** friert den aktuellen Zoomwert ein – Mausrad-Zoom und
  „+"/„−" sind wirkungslos (Buttons deaktiviert, Schloss zeigt den
  aktiven `.on`-Zustand), bis erneut geklickt wird.
- **Zustandsmodell:** Zoomwert und Lock sind reiner UI-State – kein
  Undo-/Redo-Eintrag, keine Dirty-Revision (§13).

**Entscheidung zu #465 (zusätzliche Zoom-Platzierung):** Die
Canvas-Kontrolle macht Zoom bereits jederzeit sichtbar und bedienbar;
eine zusätzliche Spiegelung in einer dedizierten Toolbar-Zeile oder der
Statusleiste wäre Redundanz ohne klaren Zusatznutzen. Es entsteht daher
**keine** neue Chrome-Fläche: keine dedizierte Toolbar-Zeile zwischen
Menü- und Schrittleiste, die Statusleiste bleibt reiner Text. Diese
Entscheidung ist bewusst dokumentiert, damit die Frage nicht erneut
aufkommt (#463/#465).
