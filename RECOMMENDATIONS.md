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

Die laufende Codeanalyse-Liste ist leer. Ruff, mypy und die lokale Testsuite bleiben die maßgebliche Baseline vor neuen PRs. Release **v2.5.0** ist am 2026-07-11 geschnitten (PR #538); die Rollout-Welle **#435/#392/#426/#389** ist geschlossen, ebenso **#299** (PR #539) mit N13-Follow-up **#541** (PR #543), **#318** (PR #540) und Snapshot-Sync **#542**. Ein Repo-Audit vom 2026-07-12 hat **#549–#553** erfasst; **#552/#549/#553/#550** sind über PR #557–#560 geschlossen. Epic **#563** („App-Update-Prüfung & KI-Modell-Verwaltung", acht Sub-Issues **#564–#571**) ist am 2026-07-13 vollständig über PR #573/#574 umgesetzt und geschlossen worden (**N14**). Live-Stand: **20** offene Issues – die bestehenden #245/#551 plus drei am 2026-07-15 neu erfasste Epics (**Release v2.6.0** #580 mit Teil-Issues #583–#585, **16-Bit-Höhenpipeline** #581 mit Teil-Issues #586–#590, **3D-Reliefvorschau** #582 mit Teil-Issues #591–#595) sowie zwei am selben Tag aus einem Coverage-Audit nachgereichte Testabdeckungs-Befunde **N15/N16** (#597/#598).

### Erledigt seit dem letzten Review

- **Alt-Baseline stabil:** **N1/N2/N4/N5/N6/N7/N8** und **O2–O7** erledigt; Epics **#329/#344/#358/#384** (N9–N12) + Export-Fix **#363** gemergt/archiviert; seit 2026-06-25 zusätzlich **#404/#406/#408** (PR #412) geschlossen.
- **Redesign & Release v2.5.0:** Redesign-Kern/Rail/Zoom/Karten-Inspector/Dark Mode/UI-Nacharbeit (**#413/#414/#455–#464/#474–#489/#499–#501/#503/#509/#510/#514–#517**, **#490**, **#433/#434**) über PR #412–#522; Release-Welle **#435/#392/#426/#389** (v2.5.0), **#299/#541/#318/#542**, PR-Template **#552**, Snapshot-Sync **#549**, SessionStart-Fix **#553**, v2.3.0-Formalisierung **#550** – alles seit 2026-07-12 geschlossen.
- **N14 — Epic #563 (App-Update & KI-Modell-Verwaltung) komplett abgeschlossen:** `app_update.py` (#564), `ai_model_status.py` (#568), Menü-/Dialog-Integration (#565/#569), optionaler automatischer Start-Check (#566), Warmup-Verdrahtung mit Mehrfach-Beobachtern/kooperativem Abbruch (#570) über PR #573/#574; Doku-Abschluss (#567/#571).

### Noch offen

- **O8 🟢 — Prototyp-Ungenauigkeit:** Höhen-Werkzeuge bleiben im Mockup nach Erzeugung gesperrt; betrifft nur die Simulation, nicht die echte App (#347).
- **N15 🟡 — Ungetestetes Dialog-Wiring:** `MainWindow._open_ai_install_dialog` (`main_window.py:1566`) hat keinen dedizierten Test, anders als die strukturell identische Schwester-Methode `_open_ai_model_dialog` (#597).
- **N16 🟡 — Ungetestete Nicht-RGBA-Konvertierung:** Die Nicht-RGBA-Zweige in `pil_to_qpixmap`/`pil_to_numpy_readonly` (`image_utils.py:16`/`:43`) werden nie mit RGB-/Palette-/Graustufenbildern getroffen (#598).

## Offene GitHub-Issues – Triage-Stand (2026-07-15)

Live-Stand: **20** offene Issues – ein weiterer Zuwachs von **18**: Zusätzlich zu den drei Epics sind zwei Testabdeckungs-Befunde aus einem Coverage-Audit vom 2026-07-15 hinzugekommen (**#597**/**#598**, entsprechen **N15**/**N16** oben). Keine Kommentar-Prüfung ergab Handlungsbedarf: #245 zuletzt am 2026-06-19 kommentiert (Status weiterhin gültig), alle übrigen 19 Issues ohne Kommentare.

### Sinnvolle Bündelung

- **Release v2.6.0** (#580 → #583 → #584 → #585, streng sequentiell): veröffentlicht den bereits gebauten Update-/KI-Betrieb-Stand aus `main`; höchste Priorität dank geringem Risiko und unmittelbarem Nutzerwert.
- **16-Bit-Höhenpipeline** (#581 → #586 → #587 → {#588 ∥ #589} → #590): #586 (ADR) darf ausdrücklich parallel zum Release entstehen, schema-ändernde Umsetzung (#587+) beginnt aber erst nach #585 (Scope-Freeze-Vorgabe von #580).
- **3D-Reliefvorschau** (#582 → #591 → #592 → #593 → #594 → #595): #591 hängt zusätzlich an #586 (konsumiert denselben HEIGHT-Vertrag) – #582 ist damit faktisch der 16-Bit-Kette nachgeordnet und der größte Effort-Block dieser Runde.
- **#245/#551** bleiben gekoppelt (Codex-Scan: Account-Aktion vs. Grundsatzentscheidung).
- **#597/#598** sind unabhängige, vollständig spezifizierte Coverage-Lücken (Testskizze bereits im Issue) – keine Kette, keine Abhängigkeit zu den drei Epics.

Bewertung: **Relevanz** = Roadmap-/Nutzerbedeutung, **Komplexität** = Umsetzungsaufwand, **Modell/Aufwand** = empfohlenes Claude-Modell + Reasoning-Effort.

| # | Titel | Relevanz | Komplexität | Modell/Aufwand | Empfohlener nächster Schritt |
|---|-------|----------|-------------|-----------------|------------------------------|
| [#580](https://github.com/NikolayDA/picture_helper/issues/580) | [Epic] Release v2.6.0 | 🟠 Hoch | 🟠 Hoch | – (Tracking-Epic) | **In Arbeit** – läuft über #583→#584→#585, kein eigener PR. |
| [#583](https://github.com/NikolayDA/picture_helper/issues/583) | Release 2.6.0: Scope-Freeze, Version, CHANGELOG | 🟠 Hoch | 🟡 Mittel | Sonnet 5 · mittel | **Ready for PR** – keine offene Abhängigkeit, sichert den fertigen Update-/KI-Stand mit geringem Risiko. |
| [#584](https://github.com/NikolayDA/picture_helper/issues/584) | Release 2.6.0: Kandidaten-Gate, fünf Artefakte | 🟠 Hoch | 🟠 Hoch | Sonnet 5 · hoch | **Blocked** – wartet auf #583; fünf Artefakt-Smokes eignen sich für parallele Workflow-Orchestrierung. |
| [#585](https://github.com/NikolayDA/picture_helper/issues/585) | Release 2.6.0: Tag, GitHub Release, Post-Release | 🟠 Hoch | 🟡 Mittel | Sonnet 5 · mittel | **Blocked** – wartet auf #584. |
| [#586](https://github.com/NikolayDA/picture_helper/issues/586) | [16-Bit] ADR: HEIGHT-Datenvertrag, Migration, Speicherbudget | 🟠 Hoch | 🟠 Hoch | Opus 4.8 · hoch | **Ready for PR** – reine Analyse-/ADR-Arbeit, darf parallel zum Release entstehen; blockiert #587–590 und #591. |
| [#587](https://github.com/NikolayDA/picture_helper/issues/587) | [16-Bit] HEIGHT-Domänenmodell & ProjectHistory verlustfrei | 🟠 Hoch | 🟠 Hoch (sehr groß) | Opus 4.8 · hoch | **Blocked** – wartet auf #586 und Release-Veröffentlichung (#585). |
| [#588](https://github.com/NikolayDA/picture_helper/issues/588) | [16-Bit] Projektformat v2: Persistenz, Migration, Validierung | 🟠 Hoch | 🟠 Hoch | Opus 4.8 · hoch | **Blocked** – wartet auf #586/#587. |
| [#589](https://github.com/NikolayDA/picture_helper/issues/589) | [16-Bit] Import/Erzeugung/Height-Ops ohne 8-Bit-Quantisierung | 🟠 Hoch | 🟠 Hoch | Opus 4.8 · hoch | **Blocked** – wartet auf #586/#587. |
| [#590](https://github.com/NikolayDA/picture_helper/issues/590) | [16-Bit] Preview, Export, UI, End-to-End-Abnahme | 🟠 Hoch | 🟠 Hoch | Opus 4.8 · hoch | **Blocked** – wartet auf #588/#589. |
| [#581](https://github.com/NikolayDA/picture_helper/issues/581) | [Epic] Durchgängige 16-Bit-Höhenpipeline | 🟠 Hoch | 🟠 Hoch (sehr groß) | – (Tracking-Epic) | **In Arbeit** – läuft über #586→#587→(#588∥#589)→#590. |
| [#591](https://github.com/NikolayDA/picture_helper/issues/591) | [3D] ADR/UX-Vertrag: Renderer-Backend, Fallback, Budgets | 🟡 Mittel | 🟠 Hoch | Opus 4.8 · hoch | **Blocked** – wartet auf akzeptiertes #586. |
| [#592](https://github.com/NikolayDA/picture_helper/issues/592) | [3D] Qt-freie Geometrie-/Normalen-/Decimation-Pipeline | 🟡 Mittel | 🟠 Hoch (sehr groß) | Opus 4.8 · hoch | **Blocked** – wartet auf #586/#591. |
| [#593](https://github.com/NikolayDA/picture_helper/issues/593) | [3D] Interaktiver Viewer mit Orbit/Pan/Zoom, Fallback | 🟡 Mittel | 🟠 Hoch (sehr groß) | Opus 4.8 · xhoch | **Blocked** – wartet auf #591/#592; riskantester Teil (plattformspezifisches Qt/OpenGL). |
| [#594](https://github.com/NikolayDA/picture_helper/issues/594) | [3D] Workflow-, State- und Cache-Integration | 🟡 Mittel | 🟠 Hoch (sehr groß) | Opus 4.8 · hoch | **Blocked** – wartet auf #593, #587, #588. |
| [#595](https://github.com/NikolayDA/picture_helper/issues/595) | [3D] Performance, Packaging, Doku, End-to-End-Abnahme | 🟡 Mittel | 🟠 Hoch | Sonnet 5 · hoch | **Blocked** – wartet auf #594. |
| [#582](https://github.com/NikolayDA/picture_helper/issues/582) | [Epic] Echte 3D-Reliefvorschau | 🟡 Mittel | 🟠 Hoch (sehr groß) | – (Tracking-Epic) | **In Arbeit** – läuft über #591→…→#595; blockiert an #586. |
| [#551](https://github.com/NikolayDA/picture_helper/issues/551) | Grundsatzentscheidung Codex Security Scan (reaktivieren/zurückbauen/ersetzen) | 🟡 Mittel | 🟡 Mittel | Sonnet 5 · mittel | **Ready for PR** – Empfehlung weiterhin Option 2 (Zurückbauen/Deaktivieren), jetzt 5+ Wochen extern blockiert. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan „Quota exceeded" | 🟢 Niedrig | 🟢 Niedrig | – (kein Code-Task) | **Blocked (extern)** – OpenAI-Billing/Quota-Wiederherstellung ist eine Account-Aktion, kein PR. |
| [#597](https://github.com/NikolayDA/picture_helper/issues/597) | test: `_open_ai_install_dialog` ohne Wiring-Test (N15) | 🟢 Niedrig | 🟢 Niedrig | Sonnet 5 · niedrig | **Ready for PR** – Testskizze bereits im Issue, keine Abhängigkeit. |
| [#598](https://github.com/NikolayDA/picture_helper/issues/598) | test: Nicht-RGBA-Konvertierungspfade in `image_utils.py` ungetestet (N16) | 🟢 Niedrig | 🟢 Niedrig | Sonnet 5 · niedrig | **Ready for PR** – Testskizze bereits im Issue, keine Abhängigkeit; ließe sich mit #597 in einem PR bündeln. |

### Als Nächstes empfohlen

1. **#583** — Scope-Freeze v2.6.0 zuerst angehen: keine offene Abhängigkeit, sichert bereits gebauten Nutzerwert mit geringem Risiko.
2. **#586** — 16-Bit-ADR jetzt beginnen statt erst nach #585: blockiert zwei komplette Epics (#581 direkt, #582 indirekt über #591) und darf explizit parallel zum Release laufen.
3. **#551** — kurze, unabhängige Grundsatzentscheidung treffen; Empfehlung bleibt Option 2 (Zurückbauen/Deaktivieren).
4. **#597 + #598** — schnellster Coverage-Gewinn dieser Runde, beide Testskizzen liegen bereits im Issue vor; lässt sich in einem gemeinsamen PR erledigen.
5. **#584/#585** sowie alle 16-Bit-/3D-Teil-Issues folgen sequentiell ihren Abhängigkeiten – siehe Tabelle, kein zusätzlicher Trigger nötig.

*Drift-Hinweis:* Die Anzahl offener Issues vor jeder künftigen Aktualisierung erneut live abfragen statt fortzuschreiben – der Sprung von 2 auf 18 und die zwei kurzfristig nachgereichten Coverage-Issues (#597/#598) in dieser Runde zeigen, wie schnell der Snapshot veraltet.

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
