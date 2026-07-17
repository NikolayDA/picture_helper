**Deutsch** · [English](docs/i18n/en/RECOMMENDATIONS.md) · [Español](docs/i18n/es/RECOMMENDATIONS.md) · [Français](docs/i18n/fr/RECOMMENDATIONS.md) · [Українська](docs/i18n/uk/RECOMMENDATIONS.md) · [简体中文](docs/i18n/zh/RECOMMENDATIONS.md)

# Codeanalyse & bewertete Empfehlungen: BgRemover

## Bewertungsskala

| Symbol | Priorität | Bedeutung |
|--------|-----------|-----------|
| 🔴 | Kritisch | Fehler, Abstürze oder Datenverlust |
| 🟠 | Hoch | Spürbarer Einfluss auf Zuverlässigkeit oder Wartbarkeit |
| 🟡 | Mittel | Sinnvolle Verbesserung für Qualität, Lesbarkeit oder Testbarkeit |
| 🟢 | Niedrig | Optionales Polishing oder Prozessverbesserung |

## Aktueller Stand (2026-07-17)

Die laufende Codeanalyse-Liste ist leer. Ruff, mypy und die lokale Testsuite bleiben die maßgebliche Baseline vor neuen PRs. Release **v2.6.0** ist am 2026-07-16 aus dem freigegebenen Commit `f24cef69829da8e37aa400dad471dc4d607b89b3` veröffentlicht worden: Tag-Workflow [29531147950](https://github.com/NikolayDA/picture_helper/actions/runs/29531147950), öffentlicher [GitHub Release](https://github.com/NikolayDA/picture_helper/releases/tag/v2.6.0), fünf erneut heruntergeladene und per SHA-256 geprüfte Anwendungsartefakte sowie grüne native Plattform-Smokes für Linux x86_64/aarch64 und macOS arm64. Die Release-Issues **#580/#583/#584/#585**, der Snapshot-Befund **#607** und die vollständige 16-Bit-Höhenpipeline **#581/#587–#590** sind abgeschlossen. Live-Stand: **10** offene Issues – #245/#551, das 3D-Epic **#582** mit #592–#595, die Coverage-Befunde **N15/N16** (#597/#598) sowie die Anleitungslücke **#606**.

### Erledigt seit dem letzten Review

- **Alt-Baseline stabil:** **N1/N2/N4/N5/N6/N7/N8** und **O2–O7** erledigt; Epics **#329/#344/#358/#384** (N9–N12) + Export-Fix **#363** gemergt/archiviert; seit 2026-06-25 zusätzlich **#404/#406/#408** (PR #412) geschlossen.
- **Redesign & Release v2.5.0:** Redesign-Kern/Rail/Zoom/Karten-Inspector/Dark Mode/UI-Nacharbeit (**#413/#414/#455–#464/#474–#489/#499–#501/#503/#509/#510/#514–#517**, **#490**, **#433/#434**) über PR #412–#522; Release-Welle **#435/#392/#426/#389** (v2.5.0), **#299/#541/#318/#542**, PR-Template **#552**, Snapshot-Sync **#549**, SessionStart-Fix **#553**, v2.3.0-Formalisierung **#550** – alles seit 2026-07-12 geschlossen.
- **N14 — Epic #563 (App-Update & KI-Modell-Verwaltung) komplett abgeschlossen:** `app_update.py` (#564), `ai_model_status.py` (#568), Menü-/Dialog-Integration (#565/#569), optionaler automatischer Start-Check (#566), Warmup-Verdrahtung mit Mehrfach-Beobachtern/kooperativem Abbruch (#570) über PR #573/#574; Doku-Abschluss (#567/#571).
- **Release v2.6.0 vollständig abgeschlossen:** Scope-Freeze (#583), Kandidaten-Gate auf dem finalen `main`-SHA (#584), Tag/Release/Post-Release-Prüfung (#585) und Tracking-Epic #580 sind erledigt; der Snapshot-Drift #607 wird mit diesem Nachzug behoben. Das 16-Bit-HEIGHT-ADR (#586) und der 3D-ADR/UX-Vertrag (#591, PR #603) bleiben ebenfalls abgeschlossen.
- **16-Bit-Höhenpipeline vollständig abgeschlossen:** Domänenmodell/History und Projektformat v2 (#587/#588, PR #610), Import/Erzeugung/Operationen (#589, PR #612) sowie Preview/Export/UI/E2E (#590, PR #613) sind in `main`; Epic #581 ist nach grünen PR-Gates, aufgelösten Reviews und vollständiger Abnahmematrix geschlossen.

### Noch offen

- **O8 🟢 — Prototyp-Ungenauigkeit:** Höhen-Werkzeuge bleiben im Mockup nach Erzeugung gesperrt; betrifft nur die Simulation, nicht die echte App (#347).
- **N15 🟡 — Ungetestetes Dialog-Wiring:** `MainWindow._open_ai_install_dialog` (`main_window.py:1566`) hat keinen dedizierten Test, anders als die strukturell identische Schwester-Methode `_open_ai_model_dialog` (#597).
- **N16 🟡 — Ungetestete Nicht-RGBA-Konvertierung:** Die Nicht-RGBA-Zweige in `pil_to_qpixmap`/`pil_to_numpy_readonly` (`image_utils.py:16`/`:43`) werden nie mit RGB-/Palette-/Graustufenbildern getroffen (#598).
- **Doku-Lücke 🟢 — Neue Extras-/Einstellungsfunktionen fehlen in der Anleitung:** Der Update-Check, die KI-Modellverwaltung/-Installation und die Auto-Update-Einstellung sind in allen sechs ANLEITUNG-Fassungen nachzuziehen (#606).

## Offene GitHub-Issues – Triage-Stand (2026-07-17)

Live-Stand nach Abschluss der 16-Bit-Höhenpipeline: **10** offene Issues. **#581/#587–#590** sind über PR #610/#612/#613 abgeschlossen. Die Owner-Kommentare vom 2026-07-15 auf **#245**/**#551** und die entsprechend geschärften Issue-Bodys bleiben aktuell.

### Sinnvolle Bündelung

- **3D-Reliefvorschau** (#582 → #592 → #593 → #594 → #595; #591 und die 16-Bit-Voraussetzungen sind abgeschlossen): #592 ist der nächste ausführbare Schritt; #594 wartet nur noch auf #593.
- **#245/#551** bleiben gekoppelt, aber die Grundsatzentscheidung ist jetzt getroffen: #551 verfolgt nur noch die Umsetzung des hybriden Modells (CodeQL automatisch, Codex manuell), #245 ausschließlich den externen OpenAI-Quota-Nachweis.
- **#597/#598** sind unabhängige, vollständig spezifizierte Coverage-Lücken; **#606** ist eine ebenso klar umrissene, unabhängige Doku-Lücke in den sechs ANLEITUNG-Fassungen.

Bewertung: **Relevanz** = Roadmap-/Nutzerbedeutung, **Komplexität** = Umsetzungsaufwand, **Modell/Aufwand** = empfohlenes Claude-Modell + Reasoning-Effort.

| # | Titel | Relevanz | Komplexität | Modell/Aufwand | Empfohlener nächster Schritt |
|---|-------|----------|-------------|-----------------|------------------------------|
| [#592](https://github.com/NikolayDA/picture_helper/issues/592) | [3D] Qt-freie Geometrie-/Normalen-/Decimation-Pipeline | 🟡 Mittel | 🟠 Hoch (sehr groß) | Opus 4.8 · hoch | **Ready for PR** – #586 und #591 sind abgeschlossen; keine offene Abhängigkeit mehr. |
| [#593](https://github.com/NikolayDA/picture_helper/issues/593) | [3D] Interaktiver Viewer mit Orbit/Pan/Zoom, Fallback | 🟡 Mittel | 🟠 Hoch (sehr groß) | Opus 4.8 · xhoch | **Blocked** – wartet auf #592; riskantester Teil (plattformspezifisches Qt/OpenGL). |
| [#594](https://github.com/NikolayDA/picture_helper/issues/594) | [3D] Workflow-, State- und Cache-Integration | 🟡 Mittel | 🟠 Hoch (sehr groß) | Opus 4.8 · hoch | **Blocked** – wartet auf #593; die 16-Bit-Voraussetzungen #587/#588 sind abgeschlossen. |
| [#595](https://github.com/NikolayDA/picture_helper/issues/595) | [3D] Performance, Packaging, Doku, End-to-End-Abnahme | 🟡 Mittel | 🟠 Hoch | Sonnet 5 · hoch | **Blocked** – wartet auf #594. |
| [#582](https://github.com/NikolayDA/picture_helper/issues/582) | [Epic] Echte 3D-Reliefvorschau | 🟡 Mittel | 🟠 Hoch (sehr groß) | – (Tracking-Epic) | **In Arbeit** – läuft über #592→…→#595; #591 ist abgeschlossen. |
| [#551](https://github.com/NikolayDA/picture_helper/issues/551) | CodeQL automatisieren, Codex Security nur noch manuell ausführen | 🟡 Mittel | 🟡 Mittel | Sonnet 5 · mittel | **Ready for PR** – Grundsatzentscheidung am 2026-07-15 getroffen (hybrides Modell: CodeQL automatisch + Codex nur manuell via `workflow_dispatch`); Issue-Body enthält bereits die vollständige Umsetzungs-Checkliste. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | OpenAI-Quota für manuelle Codex-Security-Prüfung wiederherstellen | 🟢 Niedrig | 🟢 Niedrig | – (kein Code-Task) | **Blocked (extern)** – Scope am 2026-07-15 weiter geschärft: reiner externer Tracker für OpenAI-Billing/Quota, blockiert weder CodeQL noch Release noch #551. |
| [#597](https://github.com/NikolayDA/picture_helper/issues/597) | test: `_open_ai_install_dialog` ohne Wiring-Test (N15) | 🟢 Niedrig | 🟢 Niedrig | Sonnet 5 · niedrig | **Ready for PR** – Testskizze bereits im Issue, keine Abhängigkeit. |
| [#598](https://github.com/NikolayDA/picture_helper/issues/598) | test: Nicht-RGBA-Konvertierungspfade in `image_utils.py` ungetestet (N16) | 🟢 Niedrig | 🟢 Niedrig | Sonnet 5 · niedrig | **Ready for PR** – Testskizze bereits im Issue, keine Abhängigkeit; ließe sich mit #597 in einem PR bündeln. |
| [#606](https://github.com/NikolayDA/picture_helper/issues/606) | docs: Update-Check/KI-Modell-Verwaltung fehlen in ANLEITUNG | 🟢 Niedrig | 🟢 Niedrig | Sonnet 5 · niedrig | **Ready for PR** – vollständige Doku-Checkliste im Issue, sechs Sprachfassungen synchron nachziehen. |

### Als Nächstes empfohlen

1. **#592** — die 3D-Geometrie-Pipeline starten; #586, #591 und die 16-Bit-Voraussetzungen sind abgeschlossen.
2. **#606** — die neue Update-/KI-Bedienung in allen sechs ANLEITUNG-Fassungen nachziehen.
3. **#551** — das beschlossene Hybridmodell umsetzen (CodeQL automatisch, Codex nur manuell via `workflow_dispatch`).
4. **#597 + #598** — die beiden unabhängigen Coverage-Lücken in einem kleinen gemeinsamen PR schließen.

*Drift-Hinweis:* Dieser Nachzug entfernt die abgeschlossene 16-Bit-Issue-Kette aus der offenen Triage, korrigiert den Live-Zähler auf 10 und löst die überholten 3D-Abhängigkeiten auf. Künftige Updates prüfen Status, Checklisten und Abhängigkeiten weiterhin live statt nur einen Zeitstempel fortzuschreiben.

## Vorige Runden

- **2026-07-17 (16-Bit-Epic-Abschluss)** — #581/#587–#590 über PR #610/#612/#613 abgeschlossen; alle PR-Gates und Reviews grün, Abnahmematrix vorhanden, Live-Stand 10.
- **2026-07-16 (Release v2.6.0)** — Tag auf `f24cef69829da8e37aa400dad471dc4d607b89b3`, Release-Lauf 29531147950 grün, fünf öffentliche Artefakte erneut heruntergeladen und per SHA-256 verifiziert; #580/#585/#607 geschlossen, Live-Stand 15.
- **2026-07-16 (Kandidaten-Gate)** — #584 durch echten Fünf-Artefakt-Gate geschlossen (finaler Gate-Lauf 29529595934 auf `f24cef69829da8e37aa400dad471dc4d607b89b3`, SHA-256 + Secret-Scan je Artefakt, native Plattform-Smokes); #585 entsperrt.
- **2026-07-15/16 (Audit-Nachzug)** — #583/#586/#591 abgeschlossen; #584 nach Nachweis des offenen Kandidaten-Gates wieder geöffnet; Live-Stand 17.
- **2026-07-14** — Live-Stand weiterhin 2 offene Issues (#245, #551), unverändert seit dem Epic-Abschluss vom Vortag.
- **2026-07-13 (Epic-Abschluss)** — Epic **#563** komplett abgeschlossen: alle acht Sub-Issues (**#564–#571**) über PR #573/#574 geschlossen; Snapshot auf 2 reduziert.
- **2026-07-13 (Issue-Audit)** — Epic **#563** + acht Sub-Issues erfasst, alle 11 offenen Issues neu bewertet, Owner-Kommentare berücksichtigt; kein Issue geschlossen; Snapshot auf 11.
- **2026-07-12** — v2.3.0-Formalisierung (#550), SessionStart-Hook-Fix (#553), Snapshot-Sync (#549, PR-Template #552 via PR #557), Issue-Audit (#542 geschlossen, #549–#553 erfasst) und Release **v2.5.0** (Rollout-Welle #435/#392/#426/#389, #299/#541/#318).
- **2026-07-11** — Epic #425 komplett abgeschlossen (#430 PR #526, Laufzeit-i18n ES/FR/UK/ZH vollständig, **O1** erledigt; #431/#432 PR #529; finaler Nachzug #530/#531 PR #533/#535).
- **2026-07-05–10** — #509/#510/#514–#517 (PR #520–#522), #490, Dark-Mode-/Rail-Icon-Welle, Karten-Inspector (#413/#414), #499–#501/#503, Icon-/Statuszeilen-Feinschliff.
- **2026-06-29** — #404/#406/#408 (PR #412), Redesign-Welle eröffnet.
- **v2.2, „admiring-mayer" (#1–#15)** — externe Liste, erledigt oder bei Fehlalarm verworfen.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
