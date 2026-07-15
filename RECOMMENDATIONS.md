**Deutsch** · [English](docs/i18n/en/RECOMMENDATIONS.md) · [Español](docs/i18n/es/RECOMMENDATIONS.md) · [Français](docs/i18n/fr/RECOMMENDATIONS.md) · [Українська](docs/i18n/uk/RECOMMENDATIONS.md) · [简体中文](docs/i18n/zh/RECOMMENDATIONS.md)

# Codeanalyse & bewertete Empfehlungen: BgRemover

## Bewertungsskala

| Symbol | Priorität | Bedeutung |
|--------|-----------|-----------|
| 🔴 | Kritisch | Fehler, Abstürze oder Datenverlust |
| 🟠 | Hoch | Spürbarer Einfluss auf Zuverlässigkeit oder Wartbarkeit |
| 🟡 | Mittel | Sinnvolle Verbesserung für Qualität, Lesbarkeit oder Testbarkeit |
| 🟢 | Niedrig | Optionales Polishing oder Prozessverbesserung |

## Aktueller Stand (2026-07-15)

Die laufende Codeanalyse-Liste ist leer. Ruff, mypy und die lokale Testsuite bleiben die maßgebliche Baseline vor neuen PRs. Release **v2.5.0** ist am 2026-07-11 geschnitten (PR #538); die Rollout-Welle **#435/#392/#426/#389** ist geschlossen, ebenso **#299** (PR #539) mit N13-Follow-up **#541** (PR #543), **#318** (PR #540) und Snapshot-Sync **#542**. Ein Repo-Audit vom 2026-07-12 hat **#549–#553** erfasst; **#552/#549/#553/#550** sind über PR #557–#560 geschlossen. Epic **#563** („App-Update-Prüfung & KI-Modell-Verwaltung", acht Sub-Issues **#564–#571**) ist am 2026-07-13 vollständig über PR #573/#574 umgesetzt und geschlossen worden (**N14**). Live-Stand: **18** offene Issues – die bestehenden #245/#551 plus drei am 2026-07-15 neu erfasste Epics (**Release v2.6.0** #580, **16-Bit-Höhenpipeline** #581, **3D-Reliefvorschau** #582) mit ihren verbleibenden offenen Teil-Issues sowie zwei am selben Tag aus einem Coverage-Audit nachgereichte Testabdeckungs-Befunde **N15/N16** (#597/#598). Noch am 2026-07-15 wurden die ersten beiden Teil-Issues abgeschlossen und geschlossen: **#583** (Scope-Freeze v2.6.0) und **#586** (16-Bit-ADR) – damit sind **#584** (Kandidaten-Gate) und **#591** (3D-ADR/UX-Vertrag) jetzt unblockiert.

### Erledigt seit dem letzten Review

- **Alt-Baseline stabil:** **N1/N2/N4/N5/N6/N7/N8** und **O2–O7** erledigt; Epics **#329/#344/#358/#384** (N9–N12) + Export-Fix **#363** gemergt/archiviert; seit 2026-06-25 zusätzlich **#404/#406/#408** (PR #412) geschlossen.
- **Redesign & Release v2.5.0:** Redesign-Kern/Rail/Zoom/Karten-Inspector/Dark Mode/UI-Nacharbeit (**#413/#414/#455–#464/#474–#489/#499–#501/#503/#509/#510/#514–#517**, **#490**, **#433/#434**) über PR #412–#522; Release-Welle **#435/#392/#426/#389** (v2.5.0), **#299/#541/#318/#542**, PR-Template **#552**, Snapshot-Sync **#549**, SessionStart-Fix **#553**, v2.3.0-Formalisierung **#550** – alles seit 2026-07-12 geschlossen.
- **N14 — Epic #563 (App-Update & KI-Modell-Verwaltung) komplett abgeschlossen:** `app_update.py` (#564), `ai_model_status.py` (#568), Menü-/Dialog-Integration (#565/#569), optionaler automatischer Start-Check (#566), Warmup-Verdrahtung mit Mehrfach-Beobachtern/kooperativem Abbruch (#570) über PR #573/#574; Doku-Abschluss (#567/#571).
- **#583/#586 (2026-07-15, selber Tag):** Scope-Freeze/Version/CHANGELOG für v2.6.0 (#583) und das 16-Bit-HEIGHT-ADR (#586) sind abgeschlossen und geschlossen; #584 und #591 sind dadurch unblockiert.

### Noch offen

- **O8 🟢 — Prototyp-Ungenauigkeit:** Höhen-Werkzeuge bleiben im Mockup nach Erzeugung gesperrt; betrifft nur die Simulation, nicht die echte App (#347).
- **N15 🟡 — Ungetestetes Dialog-Wiring:** `MainWindow._open_ai_install_dialog` (`main_window.py:1566`) hat keinen dedizierten Test, anders als die strukturell identische Schwester-Methode `_open_ai_model_dialog` (#597).
- **N16 🟡 — Ungetestete Nicht-RGBA-Konvertierung:** Die Nicht-RGBA-Zweige in `pil_to_qpixmap`/`pil_to_numpy_readonly` (`image_utils.py:16`/`:43`) werden nie mit RGB-/Palette-/Graustufenbildern getroffen (#598).

## Offene GitHub-Issues – Triage-Stand (2026-07-15)

Live-Stand: **18** offene Issues – dieselbe Erfassung wie zuvor am selben Tag, jedoch mit zwei zwischenzeitlich geschlossenen Teil-Issues (**#583**, **#586**) und aktualisierten Owner-Kommentaren auf **#245**/**#551**. Die Kommentar-Prüfung ergab: #245 und #551 haben je einen neuen Kommentar vom 2026-07-15 erhalten – der Owner hat darin die Grundsatzentscheidung aus #551 getroffen (hybrides Modell: CodeQL automatisch + Codex nur manuell über `workflow_dispatch`) und den Scope beider Issues entsprechend geschärft; beide Issue-Bodys sind bereits aktualisiert, ein zusätzlicher Kommentar meinerseits war nicht nötig. Alle übrigen 16 Issues bleiben ohne Kommentare.

### Sinnvolle Bündelung

- **Release v2.6.0** (#580 → #584 → #585; #583 ist bereits abgeschlossen): veröffentlicht den bereits gebauten Update-/KI-Betrieb-Stand aus `main`; höchste Priorität dank geringem Risiko und unmittelbarem Nutzerwert.
- **16-Bit-Höhenpipeline** (#581 → #587 → {#588 ∥ #589} → #590; #586-ADR ist bereits abgeschlossen): die schema-ändernde Umsetzung (#587+) beginnt weiterhin erst nach #585 (Scope-Freeze-Vorgabe von #580).
- **3D-Reliefvorschau** (#582 → #591 → #592 → #593 → #594 → #595): #591 ist jetzt unblockiert, da #586 abgeschlossen ist – kann sofort parallel zur 16-Bit-Modellumsetzung starten; #582 bleibt trotzdem der größte Effort-Block dieser Runde.
- **#245/#551** bleiben gekoppelt, aber die Grundsatzentscheidung ist jetzt getroffen: #551 verfolgt nur noch die Umsetzung des hybriden Modells (CodeQL automatisch, Codex manuell), #245 ausschließlich den externen OpenAI-Quota-Nachweis.
- **#597/#598** sind unabhängige, vollständig spezifizierte Coverage-Lücken (Testskizze bereits im Issue) – keine Kette, keine Abhängigkeit zu den drei Epics.

Bewertung: **Relevanz** = Roadmap-/Nutzerbedeutung, **Komplexität** = Umsetzungsaufwand, **Modell/Aufwand** = empfohlenes Claude-Modell + Reasoning-Effort.

| # | Titel | Relevanz | Komplexität | Modell/Aufwand | Empfohlener nächster Schritt |
|---|-------|----------|-------------|-----------------|------------------------------|
| [#580](https://github.com/NikolayDA/picture_helper/issues/580) | [Epic] Release v2.6.0 | 🟠 Hoch | 🟠 Hoch | – (Tracking-Epic) | **In Arbeit** – läuft über #584→#585 (#583 abgeschlossen), kein eigener PR. |
| [#584](https://github.com/NikolayDA/picture_helper/issues/584) | Release 2.6.0: Kandidaten-Gate, fünf Artefakte | 🟠 Hoch | 🟠 Hoch | Sonnet 5 · hoch | **Ready for PR** – #583 ist abgeschlossen, keine offene Abhängigkeit mehr; fünf Artefakt-Smokes eignen sich für parallele Workflow-Orchestrierung. |
| [#585](https://github.com/NikolayDA/picture_helper/issues/585) | Release 2.6.0: Tag, GitHub Release, Post-Release | 🟠 Hoch | 🟡 Mittel | Sonnet 5 · mittel | **Blocked** – wartet auf #584. |
| [#587](https://github.com/NikolayDA/picture_helper/issues/587) | [16-Bit] HEIGHT-Domänenmodell & ProjectHistory verlustfrei | 🟠 Hoch | 🟠 Hoch (sehr groß) | Opus 4.8 · hoch | **Blocked** – #586 ist abgeschlossen; wartet jetzt nur noch auf die Release-Veröffentlichung (#585). |
| [#588](https://github.com/NikolayDA/picture_helper/issues/588) | [16-Bit] Projektformat v2: Persistenz, Migration, Validierung | 🟠 Hoch | 🟠 Hoch | Opus 4.8 · hoch | **Blocked** – wartet auf #587. |
| [#589](https://github.com/NikolayDA/picture_helper/issues/589) | [16-Bit] Import/Erzeugung/Height-Ops ohne 8-Bit-Quantisierung | 🟠 Hoch | 🟠 Hoch | Opus 4.8 · hoch | **Blocked** – wartet auf #587. |
| [#590](https://github.com/NikolayDA/picture_helper/issues/590) | [16-Bit] Preview, Export, UI, End-to-End-Abnahme | 🟠 Hoch | 🟠 Hoch | Opus 4.8 · hoch | **Blocked** – wartet auf #588/#589. |
| [#581](https://github.com/NikolayDA/picture_helper/issues/581) | [Epic] Durchgängige 16-Bit-Höhenpipeline | 🟠 Hoch | 🟠 Hoch (sehr groß) | – (Tracking-Epic) | **In Arbeit** – läuft über #587→(#588∥#589)→#590 (#586 abgeschlossen). |
| [#591](https://github.com/NikolayDA/picture_helper/issues/591) | [3D] ADR/UX-Vertrag: Renderer-Backend, Fallback, Budgets | 🟡 Mittel | 🟠 Hoch | Opus 4.8 · hoch | **Ready for PR** – #586 ist abgeschlossen, keine offene Abhängigkeit mehr; reine ADR-/UX-Konzeptarbeit, kann parallel zur 16-Bit-Modellumsetzung starten. |
| [#592](https://github.com/NikolayDA/picture_helper/issues/592) | [3D] Qt-freie Geometrie-/Normalen-/Decimation-Pipeline | 🟡 Mittel | 🟠 Hoch (sehr groß) | Opus 4.8 · hoch | **Blocked** – wartet auf #591. |
| [#593](https://github.com/NikolayDA/picture_helper/issues/593) | [3D] Interaktiver Viewer mit Orbit/Pan/Zoom, Fallback | 🟡 Mittel | 🟠 Hoch (sehr groß) | Opus 4.8 · xhoch | **Blocked** – wartet auf #591/#592; riskantester Teil (plattformspezifisches Qt/OpenGL). |
| [#594](https://github.com/NikolayDA/picture_helper/issues/594) | [3D] Workflow-, State- und Cache-Integration | 🟡 Mittel | 🟠 Hoch (sehr groß) | Opus 4.8 · hoch | **Blocked** – wartet auf #593, #587, #588. |
| [#595](https://github.com/NikolayDA/picture_helper/issues/595) | [3D] Performance, Packaging, Doku, End-to-End-Abnahme | 🟡 Mittel | 🟠 Hoch | Sonnet 5 · hoch | **Blocked** – wartet auf #594. |
| [#582](https://github.com/NikolayDA/picture_helper/issues/582) | [Epic] Echte 3D-Reliefvorschau | 🟡 Mittel | 🟠 Hoch (sehr groß) | – (Tracking-Epic) | **In Arbeit** – läuft über #591→…→#595; #591 jetzt startbereit (#586 abgeschlossen). |
| [#551](https://github.com/NikolayDA/picture_helper/issues/551) | CodeQL automatisieren, Codex Security nur noch manuell ausführen | 🟡 Mittel | 🟡 Mittel | Sonnet 5 · mittel | **Ready for PR** – Grundsatzentscheidung am 2026-07-15 getroffen (hybrides Modell: CodeQL automatisch + Codex nur manuell via `workflow_dispatch`); Issue-Body enthält bereits die vollständige Umsetzungs-Checkliste. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | OpenAI-Quota für manuelle Codex-Security-Prüfung wiederherstellen | 🟢 Niedrig | 🟢 Niedrig | – (kein Code-Task) | **Blocked (extern)** – Scope am 2026-07-15 weiter geschärft: reiner externer Tracker für OpenAI-Billing/Quota, blockiert weder CodeQL noch Release noch #551. |
| [#597](https://github.com/NikolayDA/picture_helper/issues/597) | test: `_open_ai_install_dialog` ohne Wiring-Test (N15) | 🟢 Niedrig | 🟢 Niedrig | Sonnet 5 · niedrig | **Ready for PR** – Testskizze bereits im Issue, keine Abhängigkeit. |
| [#598](https://github.com/NikolayDA/picture_helper/issues/598) | test: Nicht-RGBA-Konvertierungspfade in `image_utils.py` ungetestet (N16) | 🟢 Niedrig | 🟢 Niedrig | Sonnet 5 · niedrig | **Ready for PR** – Testskizze bereits im Issue, keine Abhängigkeit; ließe sich mit #597 in einem PR bündeln. |

### Als Nächstes empfohlen

1. **#584** — Kandidaten-Gate v2.6.0 jetzt angehen: #583 ist abgeschlossen, keine offene Abhängigkeit mehr; sichert den Release-Kandidaten über fünf Artefakte ab.
2. **#591** — 3D-ADR/UX-Vertrag jetzt beginnen statt erst nach akzeptiertem #586: #586 ist abgeschlossen, #591 blockiert #592–595 und darf explizit parallel zur 16-Bit-Modellumsetzung (#587+) laufen.
3. **#551** — Umsetzung des bereits getroffenen hybriden Modells angehen (CodeQL für Python automatisieren, Codex-Workflow auf reinen `workflow_dispatch` reduzieren); keine offene Grundsatzfrage mehr.
4. **#597 + #598** — schnellster Coverage-Gewinn dieser Runde, beide Testskizzen liegen bereits im Issue vor; lässt sich in einem gemeinsamen PR erledigen.
5. **#585** sowie alle verbleibenden 16-Bit-/3D-Teil-Issues folgen sequentiell ihren Abhängigkeiten – siehe Tabelle, kein zusätzlicher Trigger nötig.

*Drift-Hinweis:* Die Anzahl offener Issues vor jeder künftigen Aktualisierung erneut live abfragen statt fortzuschreiben – schon innerhalb desselben Tages sind hier zwei Teil-Issues (#583, #586) geschlossen worden und haben zwei nachfolgende Issues (#584, #591) unblockiert; ein reiner Zeitstempel-Snapshot hätte das verpasst.

## Vorige Runden

- **2026-07-14** — Live-Stand weiterhin 2 offene Issues (#245, #551), unverändert seit dem Epic-Abschluss vom Vortag.
- **2026-07-13 (Epic-Abschluss)** — Epic **#563** komplett abgeschlossen: alle acht Sub-Issues (**#564–#571**) über PR #573/#574 geschlossen; Snapshot auf 2 reduziert.
- **2026-07-13 (Issue-Audit)** — Epic **#563** + acht Sub-Issues erfasst, alle 11 offenen Issues neu bewertet, Owner-Kommentare berücksichtigt; kein Issue geschlossen; Snapshot auf 11.
- **2026-07-12** — v2.3.0-Formalisierung (#550), SessionStart-Hook-Fix (#553), Snapshot-Sync (#549, PR-Template #552 via PR #557), Issue-Audit (#542 geschlossen, #549–#553 erfasst) und Release **v2.5.0** (Rollout-Welle #435/#392/#426/#389, #299/#541/#318).
- **2026-07-11** — Epic #425 komplett abgeschlossen (#430 PR #526, Laufzeit-i18n ES/FR/UK/ZH vollständig, **O1** erledigt; #431/#432 PR #529; finaler Nachzug #530/#531 PR #533/#535).
- **2026-07-05–10** — #509/#510/#514–#517 (PR #520–#522), #490, Dark-Mode-/Rail-Icon-Welle, Karten-Inspector (#413/#414), #499–#501/#503, Icon-/Statuszeilen-Feinschliff.
- **2026-06-29** — #404/#406/#408 (PR #412), Redesign-Welle eröffnet.
- **v2.2, „admiring-mayer" (#1–#15)** — externe Liste, erledigt oder bei Fehlalarm verworfen.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
