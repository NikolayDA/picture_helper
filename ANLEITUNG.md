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
9. [Tab „Drehen/Spiegeln"](#9-tab-drehenspiegeln)
10. [Tab „Form" – Ecken & Zuschnitt](#10-tab-form--ecken--zuschnitt)
11. [Bild speichern](#11-bild-speichern)
12. [Einstellungen](#12-einstellungen)
13. [Tastatur-Kürzel](#13-tastatur-kürzel)
14. [Typische Arbeitsabläufe](#14-typische-arbeitsabläufe)
15. [Tipps & Tricks](#15-tipps--tricks)
16. [Bekannte Einschränkungen](#16-bekannte-einschränkungen)
17. [Fehlerbehebung & Log-Datei](#17-fehlerbehebung--log-datei)
18. [Lizenz](#18-lizenz)

---

## 1. Was kann BgRemover?

BgRemover ist ein Bildbearbeitungs-Werkzeug zum **Entfernen, Ersetzen
und Bearbeiten von Hintergründen**. Die wichtigsten Funktionen:

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
- **Verlauf** mit Rückgängig/Wiederherstellen und Sprung zu jedem
  früheren Bearbeitungsschritt.
- **Speichern** als PNG, JPEG, WebP oder TIFF.

---

## 2. Die Programmoberfläche im Überblick

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
| **Menüleiste** (oben) | Datei, Bearbeiten, Ansicht, Extras |
| **Werkzeugleiste** (links) | Auswahl-Werkzeuge, KI, Verlauf, Öffnen/Speichern |
| **Arbeitsfläche** (Mitte) | Zeigt das Bild und die aktuelle Auswahl |
| **Tab-Panel** (rechts) | Vier Reiter: Auswahl, Hintergrund, Drehen/Spiegeln, Form |
| **Statusleiste** (unten) | Hinweise und Rückmeldungen des Programms |

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

Die folgenden Kapitel erklären jeden Schritt im Detail.

---

## 4. Bild öffnen

Es gibt drei Wege, ein Bild zu laden:

- **Menü:** `Datei → Öffnen…` (⌘O / Strg+O).
- **Drag & Drop:** Eine Bilddatei aus dem Dateimanager direkt auf die
  Arbeitsfläche ziehen.
- **Zuletzt geöffnet:** `Datei → Zuletzt geöffnet` listet die letzten
  10 geladenen Bilder auf.

Unterstützt werden gängige Formate wie PNG, JPEG, WebP, TIFF und BMP.
Große Bilder werden im Hintergrund geladen – die Statusleiste zeigt den
Fortschritt an.

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

Der erste Reiter im rechten Panel steuert das Auswahlverhalten.

### Werkzeug-Hinweise

Oben werden die vier Auswahl-Werkzeuge mit Kurzbeschreibung und den
Modifikatortasten (Shift = addieren, Ctrl/Cmd = subtrahieren)
aufgelistet.

### Einstellungen

| Regler | Bereich | Wirkung |
|---|---|---|
| **Toleranz (Zauberstab)** | 0 – 255 | Wie ähnlich Farben sein müssen, um mit dem Zauberstab gemeinsam ausgewählt zu werden. **Niedrig** = nur sehr ähnliche Farben · **Hoch** = viele Farbtöne. |
| **Pinselgröße** | 4 – 200 px | Durchmesser von Pinsel und Radiergummi. |

### Auswahl-Aktionen

- **Auswahl aufheben** – hebt die aktuelle Auswahl auf (auch mit der
  **Esc**-Taste).
- **Auswahl invertieren** (⌘⇧I) – tauscht ausgewählte und nicht
  ausgewählte Bereiche. Praktisch: erst das *Objekt* auswählen, dann
  invertieren, um den *Hintergrund* zu bearbeiten.
- **Erweitern / Schrumpfen** – vergrößert bzw. verkleinert die Auswahl
  um den daneben eingestellten Radius (1 – 20 px). Nützlich, um einen
  schmalen Farbsaum nach der Freistellung zu entfernen.

---

## 8. Tab „Hintergrund"

Hier wird die getroffene Auswahl tatsächlich verändert.

| Aktion | Beschreibung |
|---|---|
| **Entfernen (transparent)** | Macht den ausgewählten Bereich vollständig durchsichtig. Tipp: zuerst mit dem Zauberstab den Hintergrund auswählen. |
| **Farbe wählen** | Öffnet einen Farbwähler. Die kleine farbige Schaltfläche zeigt die aktuell gewählte Ersatzfarbe. |
| **Farbe ersetzen** | Füllt den ausgewählten Bereich mit der gewählten Farbe. |

**Typischer Ablauf:** Hintergrund mit Zauberstab/KI auswählen →
*Entfernen (transparent)* für eine freigestellte PNG-Datei, **oder** eine
Farbe wählen und *Farbe ersetzen* für einen einfarbigen Hintergrund
(z. B. weiß für Passfotos).

---

## 9. Tab „Drehen/Spiegeln"

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
> ⌘→ (90° rechts).

---

## 10. Tab „Form" – Ecken & Zuschnitt

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
4. Unter der Arbeitsfläche erscheint eine Leiste:
   - **✓ Zuschnitt anwenden** – schneidet das Bild zu.
   - **✗ Abbrechen** – verwirft den Rahmen.

---

## 11. Bild speichern

- **Speichern:** `Datei → Speichern` (⌘S / Strg+S)
- **Speichern unter…:** `Datei → Speichern unter…` (⇧⌘S)

Wählen Sie im Dialog das gewünschte **Dateiformat**:

| Format | Eigenschaften | Empfehlung |
|---|---|---|
| **PNG** | Mit Transparenz | Für freigestellte Objekte – **Standardempfehlung** |
| **JPEG** | Kein Transparenz-Kanal, transparente Bereiche werden weiß | Für Fotos mit deckendem Hintergrund |
| **WebP** | Modernes Web-Format, Transparenz möglich | Für die Verwendung im Web |
| **TIFF** | Verlustfrei, Transparenz möglich | Für Archivierung/Druck |

> Soll die Freistellung erhalten bleiben, **immer PNG, WebP oder TIFF**
> wählen – JPEG füllt transparente Stellen weiß.

---

## 12. Einstellungen

Über `Extras → Einstellungen…` (⌘, / Strg+,) lassen sich drei
Vorgaben dauerhaft speichern:

| Einstellung | Beschreibung |
|---|---|
| **Standard-Verzeichnis zum Öffnen** | Startordner des Öffnen-Dialogs (leer = zuletzt verwendet) |
| **Standard-Verzeichnis für Export/Speichern** | Startordner des Speichern-Dialogs (leer = zuletzt verwendet) |
| **Bevorzugtes Bilddateiformat** | PNG, JPEG, WebP oder TIFF – erscheint als erste Option im Speichern-Dialog |

Die Einstellungen bleiben über Programmstarts hinweg erhalten.

---

## 13. Tastatur-Kürzel

Unter macOS ist die Modifikatortaste **⌘ (Cmd)**, unter Linux/Windows
**Strg**.

| Aktion | Shortcut |
|---|---|
| Bild öffnen | ⌘O |
| Bild speichern | ⌘S |
| Bild speichern unter… | ⇧⌘S |
| Rückgängig | ⌘Z |
| Wiederherstellen | ⇧⌘Z |
| 90° links drehen | ⌘← |
| 90° rechts drehen | ⌘→ |
| Auswahl aufheben | Esc |
| Auswahl invertieren | ⌘⇧I |
| An Fenster anpassen (Fit to View) | ⌘0 |
| Einstellungen öffnen | ⌘, |

---

## 14. Typische Arbeitsabläufe

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

---

## 15. Tipps & Tricks

- **Erst grob, dann fein:** Mit KI oder Zauberstab grob freistellen,
  danach mit Pinsel/Radiergummi korrigieren.
- **Toleranz anpassen:** Wird zu viel ausgewählt → Toleranz senken.
  Wird zu wenig erfasst → Toleranz erhöhen oder Shift+Klick nutzen.
- **Farbsaum loswerden:** Nach dem Freistellen im Tab *Auswahl*
  „Schrumpfen" um 1–2 px anwenden, bevor der Hintergrund entfernt wird.
- **Schritt zurück:** Jeder Schritt landet im Verlauf – über die
  **Änderungshistorie** (🕘) per Doppelklick zu jedem früheren Zustand
  zurückspringen.
- **Nichts geht mehr?** **Original wiederherstellen** setzt das Bild auf
  den Ladezustand zurück.

---

## 16. Bekannte Einschränkungen

- **Maximale Bildgröße: 40 Megapixel.** Größere Bilder werden abgelehnt.
- Die **KI-Funktion** benötigt die optionale Komponente `rembg`. Ohne
  sie ist die KI-Schaltfläche deaktiviert; alle manuellen Werkzeuge
  funktionieren weiterhin.
- Das **App-Bundle** (`BgRemover.app`) ist macOS-spezifisch; unter
  Linux/Windows läuft die Anwendung über den direkten Programmstart.

---

## 17. Fehlerbehebung & Log-Datei

Bei Problemen lohnt ein Blick in die **Log-Datei** `bgremover.log`. Sie
wird beim Programmstart im plattformspezifischen App-Datenverzeichnis
angelegt:

- **macOS:** `~/Library/Application Support/BgRemover/`
- **Linux:** `~/.local/share/BgRemover/`

Die Datei enthält Status-Meldungen und Fehlerdetails (Stacktraces) und
ist bei Support-Anfragen die erste Anlaufstelle.

| Problem | Mögliche Lösung |
|---|---|
| KI-Schaltfläche ausgegraut | `rembg` ist nicht installiert – siehe Installationsanleitung |
| Bild lässt sich nicht öffnen | Über 40 Megapixel? Format unterstützt? Statusleiste lesen |
| KI dauert sehr lange | Erster Aufruf lädt das Modell – einmalig, danach schneller |
| Transparenz weg nach Speichern | Als JPEG gespeichert → stattdessen PNG/WebP/TIFF wählen |

---

## 18. Lizenz

BgRemover steht unter der **GNU General Public License v3.0 oder später**
(`GPL-3.0-or-later`) – siehe [LICENSE](LICENSE). Eine vollständige
Auflistung aller verwendeten Bibliotheken und Lizenzen steht in
[RESOURCES.md](RESOURCES.md).

---

*Diese Anleitung gehört zum Projekt BgRemover. Bei Fragen oder
Verbesserungsvorschlägen bitte ein Issue im GitHub-Repository erstellen.*
