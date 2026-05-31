**Deutsch** · [English](docs/i18n/en/RECOMMENDATIONS.md) · [Español](docs/i18n/es/RECOMMENDATIONS.md) · [Français](docs/i18n/fr/RECOMMENDATIONS.md) · [Українська](docs/i18n/uk/RECOMMENDATIONS.md) · [简体中文](docs/i18n/zh/RECOMMENDATIONS.md)

# Codeanalyse & bewertete Empfehlungen: BgRemover

## Bewertungsskala

| Symbol | Priorität | Bedeutung |
|--------|-----------|-----------|
| 🔴 | Kritisch | Muss behoben werden – führt zu Fehlern, Abstürzen oder Inkonsistenzen |
| 🟠 | Hoch | Sollte bald behoben werden – beeinträchtigt Zuverlässigkeit oder Wartbarkeit erheblich |
| 🟡 | Mittel | Empfohlen – verbessert Code-Qualität, Lesbarkeit oder Testbarkeit |
| 🟢 | Niedrig | Optional – Polishing, ergänzende Verbesserungen |

---

## Aktueller Stand (2026, Review „admiring-mayer")

Review einer extern eingereichten Empfehlungsliste (15 Befunde) gegen die tatsächliche Codebasis. Ergebnis: **14 bestätigt, 1 Fehlalarm** (#4). Die bestätigten Befunde sind unten in **sechs Umsetzungspakete** gebündelt; die Paketreihenfolge ist zugleich die empfohlene Bearbeitungsfolge. Jeder Eintrag hält den ursprünglichen Befund, Beleg (`datei:zeile`) und die Stoßrichtung fest; für den aktuellen Umsetzungsstand gilt die nachfolgende Tabelle. Die Nummerierung (#1–#15) entspricht der Original-Reviewliste.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).

### Erledigungsstand (Abgleich 2026-05-31)

| Status | Punkte |
|--------|--------|
| ✅ Erledigt | #1, #2, #8, #10, #11, #14, #15 |
| 🟡 Teilweise erledigt | #13 – fünf von sechs geforderten dynamischen Testbereichen sind abgedeckt; der Restore-Budget-Test fehlt noch |
| ⬜ Offen | #3, #5, #6, #7, #12 |
| ➖ Verworfen | #4 – Fehlalarm |

---

## Empfehlungspakete

**Paket 1 — Sofort umsetzen** 🔴

- **#1 KI-Abbruch muss den Thread abschließen.** `AIWorker._work` (`bgremover/workers.py:74`) kehrt bei Abbruch ohne Signal zurück; `quit_on=(finished, error)` (`bgremover/worker_controller.py:152`) feuert dann nie → der QThread läuft weiter, `ai_thread`/`ai_worker` bleiben gesetzt, und der KI-Button bleibt die restliche Session deaktiviert (Trigger: „Bild laden während die KI rechnet"). Fix: parameterloses `done`-Signal im `finally`-Zweig (`_always_finished`) emittieren und in `quit_on` aufnehmen — die Infrastruktur dafür existiert bereits (Warmup-Worker). **In diesem PR umgesetzt, inkl. Cancel-Lebenszyklus-Test.**

**Paket 2 — Schnelle, sichere Wins (erledigt)** 🟠 🟡

- **#2 Transienten Canvas-Zustand zentral zurücksetzen.** `apply_loaded_image` (`canvas.py:234`) ruft `cancel_overlay_only()` ohne `cropModeChanged(False)` und bricht das Lasso nicht ab → Crop-Signalfolge bleibt `[True]`, alte Lasso-Punkte überleben. Eine `_reset_transient_state()`-Methode einführen.
- **#11 Logging unabhängig von Fremd-Handlern.** `logging.basicConfig()` (`logging_config.py:61`) ist ein No-op, sobald der Root-Logger bereits Handler hat → angezeigter Logpfad ≠ tatsächlich beschriebener. Den benannten `BgRemover`-Logger explizit konfigurieren (sauberer als `force=True`).
- **#10 Diagnose-Skript auf aktuellen Logpfad bringen.** `diagnose_mac.sh:178` liest noch `~/.bgremover.log`; real schreibt der Logger nach `~/Library/Application Support/BgRemover/bgremover.log` (QStandardPaths). Pfad angleichen.
- **#8 Exportformat robust normalisieren.** `_save_as` (`main_window.py:304`) verwirft den gewählten Dialogfilter; `save_image_file` (`image_ops.py:46`) speichert bei fehlender Endung still als PNG. Zentrales Formatmodell mit Default-Suffix; die duplizierten Format-Dicts (Dialog vs. MainWindow) zusammenführen. *(Der gemeldete EXR-`KeyError` ist nur über manipulierte Settings/Dict-Drift erreichbar — der Endungs-Fall ist der nutzerseitige Kern.)*
- **#14 CI- und Doku-Checks synchronisieren.** `RESOURCES.md:102` und `TESTING.md:10` nennen noch „3.10/3.12" (real 3.10–3.13); `ui-nightly.yml` fehlt in den Workflow-Listen und in `test_resource_docs.py:35`. Workflow-Liste und Python-Matrix mitprüfen.
- **#15 Release-CI als echtes Gate.** `ci.yml` startet die Vollmatrix erst bei `release: published` (zu spät als Gate); `ui-nightly.yml:18` `continue-on-error: true` maskiert Fehler. Tag-/Pre-Release-Kandidatenlauf vorsehen und Nightly-Fehler sichtbar eskalieren lassen.

**Paket 3 — Substanz mit Messung** 🟠

- **#5 Overlay nicht bei jeder Pinselbewegung neu allokieren.** `_refresh_overlay` (`canvas.py:263`) → `mask_to_overlay` baut ein volles RGBA-Overlay (40 MP ≈ 160 MiB) — sogar bei leerer Maske und bei jeder Mausbewegung. Lazy erzeugen, Dirty-Region aktualisieren oder Events bündeln.
- **#6 Zauberstab begrenzen, abbrechbar machen, benchmarken.** `flood_fill` (`image_utils.py:48`) wächst die Region in Python; nachgemessen ≈ 3,3 s bei 2,25 MP (→ zweistellige Sekunden bei 40 MP). Scanline-/native Implementierung (z. B. `scipy.ndimage.label`) und Abbruchpfad ergänzen.
- **#7 rembg-Warmup und KI-Aufruf serialisieren.** `_on_warmup_done` (`main_window.py:270`) zeigt auch nach Warmup-Fehlern „KI bereit"; der KI-Button bleibt während des Warmups nutzbar → paralleler Modell-Init. Erfolg/Fehler trennen, Button bis Warmup-Ende gaten.
- **#3 Speicherbudget des Verlaufs durchsetzen.** `restore` (`canvas_history.py:81`) und `redo` (`:47`) hängen an den Undo-Stapel an, umgehen aber die Eviction aus `push` → wiederholtes Wiederherstellen wächst unbeschränkt. Gemeinsamen Trim-Helper nutzen und Gesamtbudget testen.

**Paket 4 — Sicherheit** 🟡

- **#12 Temporäres Qt-Plugin-Staging härten.** `qt_plugins.py` (Z. 26/29/48) nutzt unter macOS einen vorhersagbaren Pfad in `/private/tmp`, feste `.tmp`-Dateien und nur einen Größenvergleich. Da dort ausführbare Qt-Plugins geladen werden, ist Pre-Seeding ein lokaler Code-Injection-Vektor. Nutzerspezifisches `0700`-Verzeichnis, eindeutige Temp-Dateien und Inhalts-/Hash-Prüfung.

**Paket 5 — Tests & Methodik** 🟡

- **#13 Tests auf Verhalten statt Quelltext ausrichten.** Die AST-Checks in `test_static_checks.py` prüfen nur String-Vorkommen und erkennen den KI-Abbruchfehler (#1) nicht. Dynamische Tests ergänzen für Cancel-Lebenszyklus, Laden während Crop/Lasso, Warmup-Fehler, unbekanntes Exportformat, Logging mit bestehendem Handler und Speicherbudget nach Restore.

**Paket 6 — Verwerfen / Umwidmen** 🟢

- **#4 Cmd-Subtraktion macOS — Fehlalarm.** Ohne `AA_MacDontSwapCtrlAndMeta` (nirgends gesetzt) mappt Qt unter macOS Cmd→`ControlModifier`; die Prüfung in `canvas.py:80` reagiert also bereits korrekt auf Cmd+Klick, und der UI-Text stimmt. Zusätzlich `MetaModifier` zu akzeptieren würde fälschlich die physische Control-Taste an „subtrahieren" binden. **Code-Änderung verwerfen**; sinnvoll ist höchstens ein Plattformtest, der das Qt-Mapping festschreibt.
