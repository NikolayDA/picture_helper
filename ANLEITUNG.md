# BgRemover – Anleitung für die Nutzung

**Deutsch** · [README](README.md) · [Installation macOS](INSTALL_MAC.md) · [Installation Linux](INSTALL_LINUX.md)

Diese Anleitung beschreibt Schritt für Schritt, wie das Programm
**BgRemover** bedient wird – von der ersten Bildöffnung bis zum
Speichern des fertigen Ergebnisses. Sie richtet sich an Anwenderinnen
und Anwender ohne Vorkenntnisse in der Bildbearbeitung.

> Hinweise zur **Installation** stehen bewusst nicht hier, sondern in
> [INSTALL_MAC.md](INSTALL_MAC.md) (macOS) bzw.
> [INSTALL_LINUX.md](INSTALL_LINUX.md) (Linux). Diese Anleitung setzt
> voraus, dass das Programm bereits gestartet werden kann.

---

## Inhaltsverzeichnis

1. [Was kann BgRemover?](#1-was-kann-bgremover)
2. [Die Programmoberfläche im Überblick](#2-die-programmoberfläche-im-überblick)
3. [Schnellstart in 5 Schritten](#3-schnellstart-in-5-schritten)
4. [Bild öffnen](#4-bild-öffnen)
5. [Die Werkzeugleiste (links)](#5-die-werkzeugleiste-links)
6. [Eine Auswahl treffen](#6-eine-auswahl-treffen)
7. [Tab „Auswahl"](#7-tab-auswahl)
8. [Tab „Hintergrund"](#8-tab-hintergrund)
9. [Tab „Anpassen" – Farbkorrektur](#9-tab-anpassen--farbkorrektur)
10. [Tab „Drehen/Spiegeln"](#10-tab-drehenspiegeln)
11. [Tab „Form" – Ecken & Zuschnitt](#11-tab-form--ecken--zuschnitt)
12. [Größe ändern & physische Maße](#12-größe-ändern--physische-maße)
13. [Ebenen & Projekte](#13-ebenen--projekte)
14. [Höhenkarten-Arbeitsbereich](#14-höhenkarten-arbeitsbereich)
15. [2D-Vorschau (Farbe, Relief, Höhe, Gloss)](#15-2d-vorschau-farbe-relief-höhe-gloss)
16. [Bild speichern & Export](#16-bild-speichern--export)
17. [Einstellungen](#17-einstellungen)
18. [Tastatur-Kürzel](#18-tastatur-kürzel)
19. [Typische Arbeitsabläufe](#19-typische-arbeitsabläufe)
20. [Tipps & Tricks](#20-tipps--tricks)
21. [Bekannte Einschränkungen](#21-bekannte-einschränkungen)
22. [Fehlerbehebung & Log-Datei](#22-fehlerbehebung--log-datei)
23. [Lizenz](#23-lizenz)

---

## 1. Was kann BgRemover?

BgRemover ist ein Bildbearbeitungs-Werkzeug zum **Entfernen, Ersetzen
und Bearbeiten von Hintergründen** – mit zusätzlichen Funktionen für
einfache Bildoptimierung, Ebenen/Projekte und die Vorbereitung von
UV-Druck-Assets. Die wichtigsten Funktionen:

- **KI-Hintergrundentfernung** – Hintergrund mit einem Klick automatisch
  freistellen.
- **Manuelle Auswahl** mit Zauberstab, Pinsel, Radiergummi und
  Polygon-Lasso.
- **Hintergrund ersetzen** – Auswahl transparent machen oder mit einer
  beliebigen Farbe füllen.
- **Transformieren** – Drehen (in 90°-Schritten oder freiem Winkel) und
  Spiegeln.
- **Form & Zuschnitt** – Ecken abrunden, auf Kreis oder ein festes
  Seitenverhältnis zuschneiden.
- **Bildoptimierung** – Helligkeit, Kontrast und Sättigung anpassen sowie
  die Alphakante glätten (Feather).
- **Größe & physische Maße** – Pixelgröße ändern oder über Millimeter und
  DPI eine Druckgröße festlegen (mit Druckflächen-Hinweis).
- **Ebenen & Projekte** – mehrere Ebenen (Farbe/Höhe/Gloss/Generisch)
  verwalten und das Ganze als `.bgrproj`-Projekt speichern und öffnen.
- **Höhenkarten** – aus einem Bild eine Höhenkarte erzeugen, bearbeiten
  und optimieren.
- **2D-Vorschau** – Farbe, Relief, Höhe und Gloss am Bildschirm prüfen.
- **EufyMake-Studio-Export** – Import-Assets für den UV-Druck erzeugen.
- **Verlauf** mit Rückgängig/Wiederherstellen und Sprung zu jedem
  früheren Bearbeitungsschritt.
- **Speichern** als PNG, JPEG, WebP oder TIFF.

---

## 2. Die Programmoberfläche im Überblick

![BgRemover – Hauptfenster nach dem Start](app_screenshots/bgremover_complete_20260528_214013/01_main_empty.png)

*Das Hauptfenster direkt nach dem Start: Werkzeugleiste links, Arbeitsfläche
mit Transparenz-Schachbrett in der Mitte, Tab-Panel rechts (hier der Tab
„Auswahl") und die Statusleiste unten.*

Das Fenster ist in vier Bereiche aufgeteilt:

```
┌──────────┬───────────────────────────────┬──────────────────┐
│          │                               │                  │
│ Werkzeug-│        Arbeitsfläche          │   Tab-Panel      │
│  leiste  │      (Bild + Auswahl)         │  (Einstellungen) │
│  (links) │                               │   (rechts)       │
│          │                               │                  │
├──────────┴───────────────────────────────┴──────────────────┤
│ Statusleiste (Hinweise & Meldungen)                          │
└──────────────────────────────────────────────────────────────┘
```

| Bereich | Zweck |
|---|---|
| **Menüleiste** (oben) | Datei, Projekt, Bearbeiten, Ansicht, Extras |
| **Werkzeugleiste** (links) | Auswahl-Werkzeuge, KI, Verlauf, Öffnen/Speichern |
| **Arbeitsfläche** (Mitte) | Zeigt das Bild und die aktuelle Auswahl |
| **Tab-Panel** (rechts) | Acht Reiter: Vorschau, Auswahl, Hintergrund, Anpassen, Drehen/Spiegeln, Form, Ebenen, Höhe |
| **Statusleiste** (unten) | Hinweise und Rückmeldungen des Programms |

### Menüs „Bearbeiten", „Ansicht" & „Projekt"

Viele Aktionen sind zusätzlich über die Menüleiste erreichbar:

- **Bearbeiten** – Rückgängig/Wiederherstellen, Drehen (90° links/rechts),
  Horizontal/Vertikal spiegeln, *Größe ändern…* sowie Auswahl aufheben/
  invertieren und *Original wiederherstellen*. Praktisch, wenn Sie eine
  Funktion lieber über das Menü als über Werkzeugleiste oder Tab aufrufen.
- **Ansicht** – *Fit to View* (⌘0) und das Untermenü *Vorschaumodus* (siehe
  [Abschnitt 15](#15-2d-vorschau-farbe-relief-höhe-gloss)); siehe auch
  „Zoomen & Ansicht" unten.
- **Projekt** – *Neues Projekt*, *Projekt öffnen…*, *Projekt speichern* /
  *…unter…* (`.bgrproj`) sowie *Assets für EufyMake Studio exportieren…*
  (siehe [Abschnitt 13](#13-ebenen--projekte) und
  [Abschnitt 16](#16-bild-speichern--export)).

![Menü „Bearbeiten"](app_screenshots/bgremover_complete_20260528_214013/22_menu_edit.png)

*Das Menü „Bearbeiten" bündelt Rückgängig/Wiederherstellen, Drehen, Spiegeln
und die Auswahl-Aktionen.*

### Zoomen & Ansicht

- **Zoomen:** Mit dem **Mausrad** über der Arbeitsfläche vergrößern bzw.
  verkleinern Sie die Ansicht.
- **Verschieben:** Ist das Bild größer als das Fenster, navigieren Sie
  über die **Bildlaufleisten** am rechten und unteren Rand.
- **Einpassen:** `Ansicht → Fit to View` (⌘0) passt das Bild wieder
  vollständig ins Fenster ein. Beim Laden eines Bildes geschieht das
  automatisch.

---

## 3. Schnellstart in 5 Schritten

So entfernen Sie einen Hintergrund in unter einer Minute:

1. **Bild öffnen** – `Datei → Öffnen` (⌘O / Strg+O) oder das Bild per
   Drag & Drop ins Fenster ziehen.
2. **KI starten** – in der Werkzeugleiste links auf das **KI-Symbol**
   klicken. Der Hintergrund wird automatisch entfernt.
3. **Nachbessern (optional)** – mit dem **Radiergummi** Reste der
   Auswahl entfernen oder mit dem **Pinsel** ergänzen.
4. **Kontrolle** – ggf. mit **Rückgängig** (⌘Z) einen Schritt
   zurückgehen.
5. **Speichern** – `Datei → Speichern` (⌘S), Format **PNG** wählen
   (behält die Transparenz).

![Ergebnis der KI-Hintergrundentfernung](app_screenshots/bgremover_complete_20260528_214013/54_function_ai_result.png)

*Nach einem Klick auf das KI-Symbol ist der Hintergrund automatisch
freigestellt – die Statusleiste meldet „KI-Hintergrundentfernung
abgeschlossen", freie Bereiche zeigt das Schachbrettmuster an.*

Die folgenden Kapitel erklären jeden Schritt im Detail.

---

## 4. Bild öffnen

Es gibt mehrere Wege, ein Bild zu laden:

- **Menü:** `Datei → Öffnen…` (⌘O / Strg+O).
- **Drag & Drop:** Eine Bilddatei aus dem Dateimanager direkt auf die
  Arbeitsfläche ziehen. Beim Ziehen mehrerer Dateien wird nur das erste
  Bild geladen.
- **Zuletzt geöffnet:** `Datei → Zuletzt geöffnet` listet die letzten
  10 geöffneten Einträge auf. Das sind sowohl Bilder als auch
  `.bgrproj`-**Projekte** (siehe [Abschnitt 13](#13-ebenen--projekte)); beim
  Anklicken erkennt das Programm den Typ und öffnet ihn passend.
- **Start mit Bildpfad:** Wird das Programm mit einem Bildpfad gestartet –
  über die **Kommandozeile** (`bgremover bild.png`) oder eine **Linux-
  Desktop-Verknüpfung** (Dateizuordnung) –, lädt es dieses Bild direkt
  beim Start.
- **macOS Finder-Öffnen:** Auf macOS lässt sich ein Bild auch per
  **Doppelklick**, über „Öffnen mit…" oder eine **Dateizuordnung** im
  Finder an BgRemover übergeben.

Alle Wege nutzen denselben **validierten, asynchronen Ladepfad**: Es gelten
dieselben Format- und Größenprüfungen, und große Bilder werden im
Hintergrund geladen – die Statusleiste zeigt den Fortschritt an.

![Das Menü „Datei"](app_screenshots/bgremover_complete_20260528_214013/20_menu_file.png)

*Das Menü „Datei" bündelt Öffnen (⌘O), „Zuletzt geöffnet", Speichern (⌘S)
und Speichern unter… (⇧⌘S).*

**Unterstützte Eingabeformate** sind verbindlich **PNG, JPEG, WebP, TIFF,
BMP und GIF**. Diese Liste ist der aktuelle Eingabevertrag, kein Beispiel:
Andere Formate werden kontrolliert abgelehnt. Insbesondere wird
**HEIC/HEIF derzeit bewusst nicht unterstützt** – eine HEIC-/HEIF-Datei
wird als nicht unterstütztes Format abgewiesen. Gespeichert wird in PNG,
JPEG, WebP oder TIFF (siehe [Abschnitt 16](#16-bild-speichern--export)).

> **Maximale Bildgröße: 40 Megapixel.** Größere Bilder werden mit einer
> Hinweismeldung in der Statusleiste abgelehnt.

---

## 5. Die Werkzeugleiste (links)

Die senkrechte Leiste am linken Rand enthält von oben nach unten:

### Auswahl-Werkzeuge

| Symbol | Werkzeug | Funktion |
|---|---|---|
| 🪄 | **Zauberstab** | Wählt mit einem Klick eine zusammenhängende Farbfläche aus (Flood-Fill). Über die *Toleranz* steuerbar. |
| 🖌 | **Pinsel** | Auswahl manuell „aufmalen". |
| 🧽 | **Radiergummi** | Aufgemalte Auswahl wieder entfernen. |
| ⬡ | **Polygon-Lasso** | Punkte nacheinander anklicken; **Doppelklick** schließt das Polygon. **Esc** bricht ab. |

Schnellwechsel per Tastatur: **W** Zauberstab, **B** Pinsel,
**E** Radiergummi, **L** Lasso.

Bei allen Auswahl-Werkzeugen gilt:

- **Shift + Klick** → zur Auswahl **hinzufügen**
- **Ctrl/Cmd + Klick** → von der Auswahl **abziehen**

### KI-Hintergrundentfernung

| Symbol | Funktion |
|---|---|
| ✨ | **KI** – entfernt den Hintergrund vollautomatisch. Beim ersten Aufruf wird das KI-Modell geladen, das kann einen Moment dauern. |

> Ist die KI-Komponente (`rembg`) nicht installiert, ist die Schaltfläche
> ausgegraut. Siehe Installationsanleitung für die Einrichtung der
> KI-Funktion.

### Verlauf

| Symbol | Funktion |
|---|---|
| ↩ | **Rückgängig** (⌘Z) – letzten Schritt zurücknehmen |
| ↪ | **Wiederherstellen** (⇧⌘Z) – rückgängig gemachten Schritt erneut anwenden |
| ⟲ | **Original wiederherstellen** – alle Bearbeitungen verwerfen |
| 🕘 | **Änderungshistorie** – Liste aller Schritte; **Doppelklick** auf einen Eintrag springt zu diesem Zustand zurück |

![Popup „Änderungshistorie"](app_screenshots/bgremover_complete_20260528_214013/40_popup_history.png)

*Die Änderungshistorie listet jeden Bearbeitungsschritt auf; ein Doppelklick
auf einen Eintrag springt zu genau diesem Zustand zurück.*

### Datei

| Symbol | Funktion |
|---|---|
| 📂 | **Bild öffnen** (⌘O) |
| 💾 | **Bild speichern** (⌘S) |

> **Tipp:** Fahren Sie mit der Maus über ein Symbol, um einen kurzen
> Hilfetext (Tooltip) anzuzeigen.

---

## 6. Eine Auswahl treffen

Fast alle Bearbeitungen (transparent machen, Farbe ersetzen) wirken auf
den **aktuell ausgewählten Bereich**. Die Auswahl wird auf dem Bild
farblich hervorgehoben.

![Geladenes Bild mit aktiver Auswahl](app_screenshots/bgremover_complete_20260528_214013/02_main_loaded_selection.png)

*Ein geladenes Bild mit aktiver Auswahl: Der ausgewählte Hintergrundbereich
ist auf der Arbeitsfläche farblich hervorgehoben.*

### Mit dem Zauberstab (empfohlen für einfarbige Hintergründe)

1. Zauberstab in der Werkzeugleiste wählen.
2. Auf den Hintergrund klicken – alle ähnlichen, zusammenhängenden
   Farben werden ausgewählt.
3. Reicht die Auswahl nicht? Mit **Shift+Klick** weitere Flächen
   hinzunehmen oder die **Toleranz** erhöhen (Tab *Auswahl*).

### Mit Pinsel & Radiergummi (für feine Korrekturen)

- **Pinsel:** über den gewünschten Bereich malen, um ihn zur Auswahl
  hinzuzufügen.
- **Radiergummi:** über fälschlich ausgewählte Bereiche malen, um sie
  zu entfernen.
- Die **Pinselgröße** stellen Sie im Tab *Auswahl* ein.

### Mit dem Polygon-Lasso (für gerade Kanten)

1. Lasso wählen.
2. Eckpunkt für Eckpunkt um das Objekt klicken.
3. **Doppelklick** schließt das Polygon und erzeugt die Auswahl.
4. **Esc** bricht den Vorgang ab.

---

## 7. Tab „Auswahl"

Der erste Bearbeitungs-Reiter im rechten Panel steuert das Auswahlverhalten – er ist
im Überblick oben ([Abschnitt 2](#2-die-programmoberfläche-im-überblick)) und in der Abbildung in [Abschnitt 6](#6-eine-auswahl-treffen)
bereits zu sehen.

### Werkzeug-Hinweise

Oben werden die vier Auswahl-Werkzeuge mit Kurzbeschreibung und den
Modifikatortasten (Shift = addieren, Ctrl/Cmd = subtrahieren)
aufgelistet.

### Einstellungen

| Regler | Bereich | Wirkung |
|---|---|---|
| **Toleranz (Zauberstab)** | 0 – 255 (Standard: 30) | Wie ähnlich Farben sein müssen, um mit dem Zauberstab gemeinsam ausgewählt zu werden. **Niedrig** = nur sehr ähnliche Farben · **Hoch** = viele Farbtöne. |
| **Pinselgröße** | 4 – 200 px (Standard: 30 px) | Durchmesser von Pinsel und Radiergummi. |

### Auswahl-Aktionen

- **Auswahl aufheben** – hebt die aktuelle Auswahl auf. **Esc** bricht zuerst
  einen aktiven Zuschnitt oder ein begonnenes Polygon-Lasso ab und hebt die
  Auswahl nur auf, wenn keine solche Interaktion aktiv ist.
- **Auswahl invertieren** (⌘⇧I) – tauscht ausgewählte und nicht
  ausgewählte Bereiche. Praktisch: erst das *Objekt* auswählen, dann
  invertieren, um den *Hintergrund* zu bearbeiten.
- **Erweitern / Schrumpfen** – vergrößert bzw. verkleinert die Auswahl
  um den daneben eingestellten Radius (1 – 20 px, Standard: 2 px). Nützlich, um einen
  schmalen Farbsaum nach der Freistellung zu entfernen.

---

## 8. Tab „Hintergrund"

Hier wird die getroffene Auswahl tatsächlich verändert.

![Der Tab „Hintergrund"](app_screenshots/bgremover_complete_20260528_214013/11_tab_background.png)

*Der Tab „Hintergrund": „Entfernen (transparent)" macht die Auswahl
durchsichtig; das Farbfeld und „Farbe ersetzen" füllen sie mit einer Farbe.*

| Aktion | Beschreibung |
|---|---|
| **Entfernen (transparent)** | Macht den ausgewählten Bereich vollständig durchsichtig. Tipp: zuerst mit dem Zauberstab den Hintergrund auswählen. |
| **Farbe wählen** | Öffnet einen Farbwähler. Die kleine farbige Schaltfläche zeigt die aktuell gewählte Ersatzfarbe. |
| **Farbe ersetzen** | Füllt den ausgewählten Bereich mit der gewählten Farbe. |

![Farbwähler-Dialog](app_screenshots/bgremover_complete_20260528_214013/31_dialog_color_picker.png)

*Über „Farbe wählen" öffnet sich der Farbwähler; die gewählte Farbe landet
im Farbfeld und wird mit „Farbe ersetzen" auf die Auswahl angewendet.*

**Typischer Ablauf:** Hintergrund mit Zauberstab/KI auswählen →
*Entfernen (transparent)* für eine freigestellte PNG-Datei, **oder** eine
Farbe wählen und *Farbe ersetzen* für einen einfarbigen Hintergrund
(z. B. weiß für Passfotos).

### Kante glätten (Feather)

Im Abschnitt *Kante glätten* desselben Tabs lässt sich die **Alphakante**
weicher zeichnen – nützlich gegen harte, „ausgeschnitten" wirkende Ränder
nach einer Freistellung.

- **Radius:** 0 – 20 px (Standard: 2 px) stellt die Breite des weichen
  Übergangs ein.
- **Kante glätten** wendet die Glättung an. Sie betrifft nur den
  **Transparenz-Kanal** (die Farben bleiben unverändert) und wirkt – wenn
  eine Auswahl aktiv ist – nur innerhalb der Auswahl.

---

## 9. Tab „Anpassen" – Farbkorrektur

Der Tab *Anpassen* enthält eine einfache **Farbkorrektur**. Sie wirkt auf
die **aktive Farbebene** (siehe [Abschnitt 13](#13-ebenen--projekte)) und
lässt die Transparenz unverändert.

| Regler | Bereich | Wirkung |
|---|---|---|
| **Helligkeit** | 0 – 200 % (Standard: 100 %) | Bild aufhellen oder abdunkeln. |
| **Kontrast** | 0 – 200 % (Standard: 100 %) | Unterschied zwischen hellen und dunklen Bereichen. |
| **Sättigung** | 0 – 200 % (Standard: 100 %) | Farbintensität; 0 % ergibt Graustufen. |

- Während Sie an den Reglern ziehen, zeigt die Arbeitsfläche eine
  **Live-Vorschau**.
- **Anwenden** übernimmt die Korrektur (undo-/redobar im Verlauf).
- **Zurücksetzen** stellt alle drei Regler wieder auf 100 % und verwirft
  die Vorschau.

---

## 10. Tab „Drehen/Spiegeln"

![Der Tab „Drehen/Spiegeln"](app_screenshots/bgremover_complete_20260528_214013/12_tab_transform.png)

*Der Tab „Drehen/Spiegeln" mit Schnell-Drehung (90°/180°/270°), freiem
Winkel und den Schaltflächen zum horizontalen und vertikalen Spiegeln.*

### Drehen

- **Schnell-Drehung:** Schaltflächen für *90° links*, *90° rechts*,
  *180°* und *270°*.
- **Freier Winkel:** Regler oder Eingabefeld von **−180° bis +180°**,
  anschließend **Winkel anwenden**. Bei schrägen Winkeln entstehen
  transparente Ecken.

### Spiegeln

- **Horizontal** – links ↔ rechts spiegeln.
- **Vertikal** – oben ↕ unten spiegeln.

> Schnelles Drehen geht auch per Tastatur: ⌘← (90° links) und
> ⌘→ (90° rechts). Ganz unten im Tab führt **Größe ändern…** zum
> Dialog aus [Abschnitt 12](#12-größe-ändern--physische-maße).

---

## 11. Tab „Form" – Ecken & Zuschnitt

![Der Tab „Form"](app_screenshots/bgremover_complete_20260528_214013/13_tab_shape_crop.png)

*Der Tab „Form": oben „Ecken abrunden" mit Radius-Regler, darunter die
Zuschnitt-Formate (Sonderformate, Quer- und Hochformat).*

### Ecken abrunden

1. Mit dem Regler **Radius** den Rundungsgrad einstellen (0 = keine
   Rundung, bis 500 px = maximal rund).
2. **Ecken abrunden** anklicken.

Das Ergebnis wird mit transparenten Ecken gespeichert – am besten als
PNG.

### Ausgabe-Format & Zuschnitt

1. Ein Format wählen – es erscheint ein **Rahmen** auf dem Bild:
   - **Sonderformate:** ⬤ Kreis, ■ 1:1 (Quadrat)
   - **Querformat:** 16:9, 4:3, 3:2, 2:1, 7:4.5 (14:9)
   - **Hochformat:** 9:16, 3:4
2. **Rahmen verschieben:** in die Mitte klicken und ziehen.
3. **Größe ändern:** an den Ecken ziehen – das Seitenverhältnis bleibt
   erhalten.
4. Oberhalb der Arbeitsfläche erscheint eine Leiste:
   - **✓ Zuschnitt anwenden** – schneidet das Bild zu.
   - **✗ Abbrechen** – verwirft den Rahmen.

![Aktiver Kreis-Zuschnitt mit Bestätigungsleiste](app_screenshots/bgremover_complete_20260528_214013/61_crop_circle_overlay.png)

*Beispiel „Kreis": Der Zuschnitt-Rahmen liegt mit Anfasspunkten über dem
Bild. Über „✓ Zuschnitt anwenden" wird zugeschnitten, „✗ Abbrechen" verwirft
den Rahmen.*

---

## 12. Größe ändern & physische Maße

Über `Bearbeiten → Größe ändern…` (Strg+R), die Schaltfläche **Größe
ändern…** im Tab *Drehen/Spiegeln* skalieren Sie das Bild auf eine neue
Zielgröße. Der Dialog kennt zwei Maßeinheiten:

### Pixelgröße ändern

Im Modus **Pixel** geben Sie **Breite** und **Höhe** direkt in Pixeln an.
Mit **Seitenverhältnis koppeln** bleibt das Verhältnis erhalten. Das
Resampling-Verfahren bestimmt die Qualität:

| Verfahren | Eignung |
|---|---|
| **Lanczos** | Beste Qualität (Standard), ideal zum Verkleinern. |
| **Bikubisch** | Glatte Ergebnisse, guter Allrounder. |
| **Bilinear** | Schneller, etwas weicher. |
| **Nächster Nachbar** | Erhält harte Kanten/Pixel, kein Glätten. |

Der Dialog zeigt die resultierende Megapixel-Zahl an und respektiert das
Limit von **40 Megapixeln**.

### Physische Maße (mm/DPI) & Druckfläche

Im Modus **Millimeter (mm + DPI)** legen Sie **Breite/Höhe in Millimetern**
und eine **Auflösung (DPI)** fest; daraus ergibt sich die Pixelgröße. Diese
physische Größe ist die maßgebliche Druckgröße und wird im
`.bgrproj`-Projekt gespeichert.

Über **Zielmedium** wählen Sie ein gängiges Druckmedium (z. B. A4 oder A3).
Passt das Motiv darauf, bestätigt der Dialog dies; ist es größer als das
Medium, weist ein Hinweis auf die Überschreitung der Druckfläche hin.

---

## 13. Ebenen & Projekte

BgRemover kann mehrere **Ebenen** in einem **Projekt** verwalten und das
Ganze als `.bgrproj`-Datei speichern. Für die klassische
Hintergrundbearbeitung müssen Sie sich damit nicht befassen – ein einzelnes
Bild verhält sich wie eine einzige Farbebene.

### Ebenen-Arten und Rollen

Jede Ebene hat eine **Art** und optional eine **Rolle**. Nur **Farb-Ebenen**
fließen in das sichtbare Farbbild ein; die übrigen Arten sind Datenebenen
für die Druckvorbereitung.

| Art / Rolle | Bedeutung |
|---|---|
| **Farbe** (Farbmotiv) | Das sichtbare Bild. Mehrere Farb-Ebenen ergeben zusammen das Komposit, das auch exportiert wird. |
| **Höhe** (Height Map) | Eine Graustufen-Höhenkarte für Relief/UV-Druck (siehe [Abschnitt 14](#14-höhenkarten-arbeitsbereich)). |
| **Gloss** (Gloss-Maske) | Eine Maske für Glanzeffekte (experimentell). |
| **Generisch** | Eine neutrale Datenebene ohne feste Rolle. |

### Der Tab „Ebenen"

Im Tab *Ebenen* verwalten Sie die Ebenenliste:

| Aktion | Beschreibung |
|---|---|
| **Neue Ebene / Duplizieren / Löschen** | Ebene hinzufügen, die aktive Ebene kopieren oder entfernen. |
| **Nach oben / unten** | Stapelreihenfolge der Ebenen ändern. |
| **Umbenennen** | Die aktive Ebene umbenennen. |
| **Rolle** | Der aktiven Ebene eine Rolle zuweisen (nur passende Kombinationen sind erlaubt). |
| **Sichtbarkeit** | Eine Ebene ein- oder ausblenden. |
| **Auswählen** | Eine Ebene als **aktive** Ebene wählen – Werkzeuge wirken auf sie. |
| **Opazität** | Deckkraft der Ebene (wird beim Loslassen übernommen). |

### Projektdateien (.bgrproj)

Über das **Projekt**-Menü arbeiten Sie mit Projektdateien:

- **Neues Projekt** (Strg+N), **Projekt öffnen…** (Strg+Umschalt+O).
- **Projekt speichern** (Strg+Alt+S) und **Projekt speichern unter…**
  (Strg+Alt+Umschalt+S).

Eine `.bgrproj`-Datei ist ein Archiv aus einem **Manifest** (Reihenfolge,
Arten, Rollen, Namen, physische Maße) und **je einem PNG pro Ebene**. So
bleiben alle Ebenen samt Transparenz verlustfrei erhalten. Projekte
erscheinen zusätzlich unter „Zuletzt geöffnet" (siehe
[Abschnitt 4](#4-bild-öffnen)).

---

## 14. Höhenkarten-Arbeitsbereich

Eine **Höhenkarte** ist eine Graustufen-Ebene, in der die Helligkeit eine
Höhe darstellt: **hell = hoch, dunkel = niedrig**. Sie ist die Grundlage
für Relief und UV-Druck. Der Tab *Höhe* ist in drei Abschnitte gegliedert
und arbeitet auf der aktiven **Höhen-Ebene**; die Bearbeiten- und
Optimieren-Funktionen sind nur aktiv, wenn eine Höhen-Ebene aktiv ist.

### Beschaffen

- **Aus Bild erzeugen** – wandelt das aktuelle Farbbild deterministisch in
  eine Höhenkarte um und legt sie als neue Höhen-Ebene an.
- **Graustufe importieren…** – lädt ein Graustufenbild als Höhenkarte und
  skaliert es auf die Projektgröße.

### Bearbeiten

- **Aufhellen / Abdunkeln** – hebt die Höhe an oder senkt sie ab; die
  **Stärke** steuert, wie stark.
- **Höhe setzen** – setzt die Höhe auf einen festen **Wert**.
- **Invertieren** – kehrt hoch und niedrig um.

Ist eine Auswahl aktiv, wirken diese Aktionen nur innerhalb der Auswahl,
sonst auf die ganze Ebene.

### Optimieren

Die Optimieren-Operationen zeigen eine **Live-Vorschau**; **Anwenden**
übernimmt sie (undo-/redobar), **Vorschau verwerfen** verwirft sie.

| Operation | Wirkung |
|---|---|
| **Tonwert (Schwarz/Weiß)** | Schwarz- und Weißpunkt der Höhe setzen. |
| **Gamma** | Mittlere Höhen heller/dunkler ziehen. |
| **Gauß-Glättung (Radius)** | Weiche, gleichmäßige Glättung. |
| **Median-Glättung (Radius)** | Glättet und erhält dabei Kanten. |
| **Schwelle** | Höhe in zwei Stufen aufteilen. |
| **Stufen** | Höhe auf eine Anzahl Stufen quantisieren. |
| **Bereich (Min/Max)** | Höhe auf einen Wertebereich begrenzen. |

---

## 15. 2D-Vorschau (Farbe, Relief, Höhe, Gloss)

Die **2D-Vorschau** zeigt verschiedene Ansichten desselben Motivs direkt
auf der Arbeitsfläche. Sie ist eine **reine Bildschirmanzeige** und ändert
weder das Bild noch den Export. Den Modus wählen Sie im Tab *Vorschau* oder
über `Ansicht → Vorschaumodus`.

| Modus | Anzeige |
|---|---|
| **Farbe** | Das normale Farbbild. |
| **Relief über Farbe** | Ein Schummerungs-Relief aus der Höhenkarte, multiplikativ über das Farbbild gelegt. |
| **Höhe (Graustufe)** | Die Höhenkarte als Graustufenbild. |
| **Gloss** | Die Gloss-Maske als Glanz-Sheen. |
| **Kombiniert** | Farbe, Relief und Gloss zusammen. |

- Mit **Relief-Stärke** stellen Sie die Intensität des Reliefs ein; bei 0 %
  wird das Relief übersprungen.
- **Gloss anzeigen** blendet den Glanzanteil ein oder aus.

Der Vorschau-Tab und das Ansicht-Untermenü bleiben synchron. Unsichtbare
Datenebenen werden in der Vorschau ignoriert.

---

## 16. Bild speichern & Export

- **Speichern:** `Datei → Speichern` (⌘S / Strg+S)
- **Speichern unter…:** `Datei → Speichern unter…` (⇧⌘S)

Beim Speichern wird stets das **Farb-Komposit** geschrieben (unabhängig
davon, welche Ebene gerade aktiv ist oder welcher Vorschaumodus eingestellt
ist). Wählen Sie im Dialog das gewünschte **Dateiformat**:

| Format | Eigenschaften | Empfehlung |
|---|---|---|
| **PNG** | Mit Transparenz | Für freigestellte Objekte – **Standardempfehlung** |
| **JPEG** | Kein Transparenz-Kanal, transparente Bereiche werden weiß | Für Fotos mit deckendem Hintergrund |
| **WebP** | Modernes Web-Format, Transparenz möglich | Für die Verwendung im Web |
| **TIFF** | Verlustfrei, Transparenz möglich | Für Archivierung/Druck |

> Soll die Freistellung erhalten bleiben, **immer PNG, WebP oder TIFF**
> wählen – JPEG füllt transparente Stellen weiß.

### Export für EufyMake Studio

Über `Projekt → Assets für EufyMake Studio exportieren…` (Strg+Alt+E) schreibt
BgRemover **Import-Assets** für EufyMake Studio – **keine** fertige `.empf`-Datei:

- **Farbmotiv** (Pflicht) als RGBA-PNG – aus einer Ebene mit Rolle *Farbmotiv*
  oder, falls keine vorhanden ist, aus dem Farbkomposit.
- **Höhenkarte** (optional) als Graustufe mit **hell = hoch, dunkel = niedrig** –
  nur verfügbar, wenn eine Ebene die Rolle *Height Map* trägt (z. B. eine über
  „Aus Bild erzeugen" angelegte Höhenebene; eine bloße Höhen-Ebene ohne diese
  Rolle wird nicht exportiert).
- **Gloss-Maske** (optional, experimentell) als Hilfsasset – nur verfügbar, wenn
  eine Ebene die Rolle *Gloss* trägt.

Im Dialog wählen Sie den Exportordner, die optionalen Assets und die
**Bittiefe** der Höhenkarte (8 Bit Standard, 16 Bit experimentell). Eine
**Pre-Export-Prüfung** läuft fortlaufend mit und meldet Befunde nach
Schweregrad:

- **Fehler** (⛔) blockieren den Export, bis sie behoben sind – z. B. ein
  fehlendes Farbmotiv oder nicht zusammenpassende Größen.
- **Warnungen** (⚠️) müssen bewusst bestätigt werden – z. B. leere Höhen-/
  Gloss-Daten oder die unbestätigte 16-Bit-Ausgabe.

Danach importieren und positionieren Sie die Assets in EufyMake Studio,
weisen dort Ink-Modi/Layer zu und speichern das Studio-Projekt selbst als
`.empf`.

---

## 17. Einstellungen

Über `Extras → Einstellungen…` (⌘, / Strg+,) lassen sich folgende
Einstellungen verwalten:

![Der Einstellungen-Dialog](app_screenshots/bgremover_complete_20260528_214013/30_dialog_settings.png)

*Der Einstellungen-Dialog: Sprache, Standard-Verzeichnisse zum Öffnen und
Speichern, bevorzugtes Bilddateiformat sowie der Pfad zur Protokolldatei mit
dem Knopf „Ordner öffnen".*

| Einstellung | Beschreibung |
|---|---|
| **Standard-Verzeichnis zum Öffnen** | Startordner des Öffnen-Dialogs (leer = zuletzt verwendet) |
| **Standard-Verzeichnis für Export/Speichern** | Startordner des Speichern-Dialogs (leer = zuletzt verwendet) |
| **Bevorzugtes Bilddateiformat** | PNG, JPEG, WebP oder TIFF – erscheint als erste Option im Speichern-Dialog |
| **Sprache** | Deutsch oder Englisch; die Änderung wird nach einem Neustart wirksam |
| **Protokolldatei** | Zeigt den Pfad der Log-Datei; Knopf „Ordner öffnen" öffnet das Verzeichnis im Dateimanager |

Die Verzeichnisse, das bevorzugte Dateiformat und die Sprache bleiben über
Programmstarts hinweg erhalten.

---

## 18. Tastatur-Kürzel

Unter macOS ist die Modifikatortaste **⌘ (Cmd)**, unter Linux/Windows
**Strg**.

| Aktion | Shortcut |
|---|---|
| Zauberstab wählen | W |
| Pinsel wählen | B |
| Radiergummi wählen | E |
| Polygon-Lasso wählen | L |
| Bild öffnen | ⌘O |
| Bild speichern | ⌘S |
| Bild speichern unter… | ⇧⌘S |
| Neues Projekt | ⌘N |
| Projekt öffnen… | ⇧⌘O |
| Projekt speichern | ⌥⌘S |
| Projekt speichern unter… | ⇧⌥⌘S |
| Assets für EufyMake Studio exportieren… | ⌥⌘E |
| Rückgängig | ⌘Z |
| Wiederherstellen | ⇧⌘Z |
| Größe ändern… | ⌘R |
| 90° links drehen | ⌘← |
| 90° rechts drehen | ⌘→ |
| Auswahl aufheben (wenn kein Crop/Lasso aktiv ist) | Esc |
| Auswahl invertieren | ⌘⇧I |
| An Fenster anpassen (Fit to View) | ⌘0 |
| Einstellungen öffnen | ⌘, |

---

## 19. Typische Arbeitsabläufe

### A) Produktfoto freistellen (transparenter Hintergrund)

1. Bild öffnen.
2. **KI** in der Werkzeugleiste klicken.
3. Mit **Radiergummi**/**Pinsel** Ränder nachbessern.
4. Im Tab *Auswahl* ggf. **Schrumpfen** (1–2 px), um den Farbsaum zu
   entfernen.
5. Als **PNG** speichern.

### B) Passfoto mit weißem Hintergrund

1. Bild öffnen.
2. **Zauberstab** auf den Hintergrund klicken (Toleranz anpassen).
3. Tab *Hintergrund* → **Farbe wählen** (Weiß) → **Farbe ersetzen**.
4. Tab *Form* → Format **1:1** wählen, Rahmen positionieren,
   **✓ Zuschnitt anwenden**.
5. Als **JPEG** oder **PNG** speichern.

### C) Rundes Profilbild

1. Bild öffnen.
2. Hintergrund per **KI** entfernen (optional).
3. Tab *Form* → **⬤ Kreis** wählen, Rahmen über das Gesicht ziehen.
4. **✓ Zuschnitt anwenden**.
5. Als **PNG** speichern (Transparenz außerhalb des Kreises).

### D) Objekt behalten, nur Hintergrund tauschen

1. Bild öffnen, **Zauberstab** auf das **Objekt** klicken.
2. Tab *Auswahl* → **Auswahl invertieren** (⌘⇧I) → jetzt ist der
   Hintergrund ausgewählt.
3. Tab *Hintergrund* → Farbe wählen → **Farbe ersetzen**.
4. Speichern.

### E) Höhenrelief-Asset für EufyMake Studio

1. Bild öffnen und freistellen.
2. Tab *Höhe* → **Aus Bild erzeugen**.
3. Höhe im Abschnitt *Optimieren* nachschärfen (z. B. *Tonwert*, *Glättung*)
   und **Anwenden**.
4. In der *2D-Vorschau* den Modus **Relief über Farbe** oder **Kombiniert**
   zur Kontrolle wählen.
5. `Projekt → Assets für EufyMake Studio exportieren…`, Befunde prüfen und
   exportieren.

---

## 20. Tipps & Tricks

- **Erst grob, dann fein:** Mit KI oder Zauberstab grob freistellen,
  danach mit Pinsel/Radiergummi korrigieren.
- **Toleranz anpassen:** Wird zu viel ausgewählt → Toleranz senken.
  Wird zu wenig erfasst → Toleranz erhöhen oder Shift+Klick nutzen.
- **Farbsaum loswerden:** Nach dem Freistellen im Tab *Auswahl*
  „Schrumpfen" um 1–2 px anwenden, bevor der Hintergrund entfernt wird.
- **Weiche Kanten:** Mit *Kante glätten* (Tab *Hintergrund*) wirken
  freigestellte Ränder weniger hart.
- **Schritt zurück:** Jeder Schritt landet im Verlauf – über die
  **Änderungshistorie** (🕘) per Doppelklick zu jedem früheren Zustand
  zurückspringen.
- **Nichts geht mehr?** **Original wiederherstellen** setzt das Bild auf
  den Ladezustand zurück.

---

## 21. Bekannte Einschränkungen

- **Maximale Bildgröße: 40 Megapixel.** Größere Bilder werden abgelehnt.
- **Eingabeformate:** Unterstützt werden PNG, JPEG, WebP, TIFF, BMP und GIF.
  **HEIC/HEIF wird derzeit nicht unterstützt** und kontrolliert abgewiesen.
- Die **KI-Funktion** benötigt die optionale Komponente `rembg`. Ohne
  sie ist die KI-Schaltfläche deaktiviert; alle manuellen Werkzeuge
  funktionieren weiterhin.
- Die **2D-Vorschau** ist eine reine Bildschirmanzeige; der Bildexport
  schreibt unverändert das Farb-Komposit.
- Der **EufyMake-Export** erzeugt nur Import-Assets, **keine** native
  `.empf`-Datei; die 16-Bit-Höhenausgabe ist experimentell.
- Das **App-Bundle** (`BgRemover.app`) ist macOS-spezifisch; unter Linux
  läuft die Anwendung über den direkten Programmstart. Windows gehört
  derzeit nicht zur offiziell getesteten Matrix.

---

## 22. Fehlerbehebung & Log-Datei

Bei Problemen lohnt ein Blick in die interne **Log-Datei**
`bgremover.log`. Sie liegt im von Qt ermittelten App-Datenverzeichnis
und wird beim ersten Log-Eintrag angelegt. Der genaue Pfad kann je nach
Plattform und Qt-Konfiguration variieren:

- **macOS (aktuelle Konfiguration):**
  `~/Library/Application Support/BgRemover/BgRemover/bgremover.log`
- **Linux:** unter `~/.local/share/`

Der macOS-App-Bundle-Launcher schreibt Startdiagnosen zusätzlich nach
`~/Library/Application Support/BgRemover/bgremover.log`.

Die interne Datei enthält Laufzeitmeldungen und Fehlerdetails
(Stacktraces) und ist bei Support-Anfragen die erste Anlaufstelle.

Am einfachsten finden Sie die Datei über `Extras → Einstellungen… →
Protokolldatei`: Dort wird der vollständige Pfad angezeigt, und der
Knopf **„Ordner öffnen"** öffnet das Verzeichnis direkt im Dateimanager
– ideal, um die Log-Datei an eine Support-Mail anzuhängen.

| Problem | Mögliche Lösung |
|---|---|
| KI-Schaltfläche ausgegraut | `rembg` ist nicht installiert – siehe Installationsanleitung |
| Bild lässt sich nicht öffnen | Über 40 Megapixel? Format unterstützt (kein HEIC/HEIF)? Statusleiste lesen |
| KI dauert sehr lange | Erster Aufruf lädt das Modell – einmalig, danach schneller |
| Transparenz weg nach Speichern | Als JPEG gespeichert → stattdessen PNG/WebP/TIFF wählen |
| Projekt lässt sich nicht öffnen | Beschädigte/unvollständige `.bgrproj`-Datei? Statusleiste lesen |

---

## 23. Lizenz

BgRemover steht unter der **GNU General Public License v3.0 oder später**
(`GPL-3.0-or-later`) – siehe [LICENSE](LICENSE). Eine vollständige
Auflistung aller verwendeten Bibliotheken und Lizenzen steht in
[RESOURCES.md](RESOURCES.md).

---

*Diese Anleitung gehört zum Projekt BgRemover. Bei Fragen oder
Verbesserungsvorschlägen bitte ein Issue im GitHub-Repository erstellen.*
