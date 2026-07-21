**Deutsch** · [English](docs/i18n/en/RECOMMENDATIONS.md) · [Español](docs/i18n/es/RECOMMENDATIONS.md) · [Français](docs/i18n/fr/RECOMMENDATIONS.md) · [Українська](docs/i18n/uk/RECOMMENDATIONS.md) · [简体中文](docs/i18n/zh/RECOMMENDATIONS.md)

# Codeanalyse & bewertete Empfehlungen: BgRemover

## Bewertungsskala

| Symbol | Priorität | Bedeutung |
|--------|-----------|-----------|
| 🔴 | Kritisch | Fehler, Abstürze oder Datenverlust |
| 🟠 | Hoch | Spürbarer Einfluss auf Zuverlässigkeit oder Wartbarkeit |
| 🟡 | Mittel | Sinnvolle Verbesserung für Qualität, Lesbarkeit oder Testbarkeit |
| 🟢 | Niedrig | Optionales Polishing oder Prozessverbesserung |

## Aktueller Stand (2026-07-21)

Die laufende Codeanalyse-Liste ist leer. Ruff, mypy und die lokale Testsuite bleiben die maßgebliche Baseline vor neuen PRs. Seit dem letzten Snapshot (2026-07-18, 3 offene Issues) ist ein komplett neues Epic entstanden und binnen eines Tages größtenteils umgesetzt worden: **#639** (Automatisierte Release-Abnahme über Self-hosted Hardware-Runner) mit den Teil-Issues **#640–#646** sowie dem Folge-Issue **#648**. Live-Stand nach GitHub-Abfrage: **12** offene Issues.

### Erledigt seit dem letzten Review

- **Alt-Baseline stabil:** **N1/N2/N4/N5/N6/N7/N8** und **O2–O7** erledigt; Epics **#329/#344/#358/#384** (N9–N12) + Export-Fix **#363** gemergt/archiviert; seit 2026-06-25 zusätzlich **#404/#406/#408** (PR #412) geschlossen.
- **16-Bit-Höhenpipeline komplett abgeschlossen:** Epic **#581** inkl. **#587/#588** (PR #610), **#589** (PR #612) und **#590** (PR #613) sind in `main`; alle Gates/Reviews grün, vollständige Abnahmematrix vorhanden.
- **Sicherheitsmodell & 3D-Kern abgeschlossen:** **#551** (CodeQL automatisch, Codex nur manuell) über PR #619; **#592–#594** (Geometriekern, Viewer, Workflow-/Cache-Integration) über PR #620 in `main`. Coverage-Lücken **#597/#598** über PR #615 geschlossen, Anleitungslücke **#606** über PR #616 in allen sechs Sprachen behoben.
- **Raspberry-Pi-5-Packaging gehärtet:** drei reale Startfehler auf Zielhardware gefunden und behoben – AppImage-Entry-Point (PR #627), aarch64-glibc-Kompatibilität (PR #627), Qt-Plugin-Staging/RUNPATH (PR #631); App startet bestätigt auf dem Pi 5 inkl. funktionierender 3D-Vorschau.
- **Neues Epic #639 eröffnet UND größtenteils umgesetzt:** ADR + Betriebsdoku (#640), Workflow-Gerüst `release-abnahme.yml` (#641), Linux-/macOS-Hardware-Smokes mit GL-Provenance (#642/#643), E2E-Release-Regressionstest (#644), Live-GL-Performance-Suite (#645) und Vision-Vorbewertung + Abschlussmatrix (#646) sind über PR #647 und PR #649 vollständig implementiert und auf `main` verifiziert. **#640–#643** bleiben nur deshalb als offene Issues gelistet, weil die PR-Beschreibung deutsche Formulierungen („Löst #640 …") statt der von GitHub erkannten englischen Schließen-Schlüsselwörter verwendet – reiner Auto-Close-Formfehler, keine inhaltliche Lücke. **#644–#646** sind ebenfalls technisch fertig, sollen aber bewusst erst nach einem echten Hardware-Dispatch (Runner-Evidenz) geschlossen werden (siehe Kommentar in #639 vom 2026-07-21).

### Noch offen

- **O8 🟢 — Prototyp-Ungenauigkeit:** Höhen-Werkzeuge bleiben im Mockup nach Erzeugung gesperrt; betrifft nur die Simulation, nicht die echte App (#347).
- **Admin-Nachzug 🟢 — Vier Issues sind fertig, aber nicht geschlossen:** #640–#643 sind über PR #647 vollständig umgesetzt; nur der fehlende englische Schließen-Schlüsselwort in der PR-Beschreibung hat den Auto-Close verhindert (siehe Kommentar in #639).

## Offene GitHub-Issues – Triage-Stand (2026-07-21)

Live-Stand: **12** offene Issues. Bewertung: **Relevanz** = Roadmap-/Nutzerbedeutung, **Komplexität** = Umsetzungsaufwand, **Modell/Aufwand** = empfohlenes Claude-Modell + Reasoning-Effort.

### Sinnvolle Bündelung

- **Release-Abnahme-Automatisierung** (#639 → {#640 ∥ #641} → {#642 ∥ #643} → #644 → #645 → #646): technisch bereits über PR #647/#649 umgesetzt; verbleibt nur die Verifikation mit echter Hardware-Evidenz (Runner-Dispatch) und die vier administrativen Schließungen #640–#643.
- **#648** ist die einzige echte verbleibende Codeaufgabe dieses Bereichs: ein Automations-/Screenshot-Modus im gepackten Artefakt, damit der 3D-Render-Nachweis nicht mehr aus dem Source-Checkout, sondern aus dem echten Paket stammt.
- **3D-Reliefvorschau** (#582 → #595): funktionaler MVP ist fertig (Go für den automatisierbaren Umfang, siehe Abnahmeprotokoll in #582); #595 wartet auf denselben Hardware-Dispatch wie oben plus #648.
- **#245** bleibt ein rein externer Tracker für OpenAI-Billing/Quota und blockiert weder CodeQL noch Release noch 3D.

| # | Titel | Relevanz | Komplexität | Modell/Aufwand | Empfohlener nächster Schritt |
|---|-------|----------|-------------|-----------------|------------------------------|
| [#639](https://github.com/NikolayDA/picture_helper/issues/639) | [Epic] Automatisierte Release-Abnahme | 🟠 Hoch | 🟠 Hoch (sehr groß, größtenteils umgesetzt) | – (Tracking-Epic) | **In Arbeit, fast fertig** – #640–#646 technisch über PR #647/#649 umgesetzt; wartet auf Runner-Verifikation + Schließen der Teil-Issues; #648 ist der einzige echte Restaufwand. |
| [#640](https://github.com/NikolayDA/picture_helper/issues/640) | ADR + Betriebs-/Sicherheitsdoku für Self-hosted Abnahme-Runner | 🟡 Mittel | 🟢 Niedrig (erledigt) | – (kein Code-Task) | **Ready to close** – ADR + `RELEASE_AUTOMATION.md` vollständig über PR #647 vorhanden; nur Auto-Close-Schlüsselwort fehlt. |
| [#641](https://github.com/NikolayDA/picture_helper/issues/641) | Workflow `release-abnahme.yml`: Gerüst, Artefaktbezug, Evidenzformat | 🟠 Hoch | 🟢 Niedrig (erledigt) | – (kein Code-Task) | **Ready to close** – Workflow + Governance-Test über PR #647 vorhanden; nur Auto-Close-Schlüsselwort fehlt. |
| [#642](https://github.com/NikolayDA/picture_helper/issues/642) | Linux-Smokes (AppImage/.deb) mit GL-Provenance | 🟠 Hoch | 🟡 Mittel (Kernlogik erledigt) | – (kein Code-Task) | **Ready to close / needs live verification** – `abnahme_smoke.py` + Tests über PR #647 vorhanden; reale Ausführung erst beim Dispatch auf dem Pi-5-Runner. |
| [#643](https://github.com/NikolayDA/picture_helper/issues/643) | macOS-DMG-Smoke mit Retina-/High-DPI-Nachweis | 🟠 Hoch | 🟡 Mittel (Kernlogik erledigt) | – (kein Code-Task) | **Ready to close / needs live verification** – gleiche Basis wie #642, für den M3-Runner. |
| [#644](https://github.com/NikolayDA/picture_helper/issues/644) | E2E-Release-Regressionsszenario als `ui`-Test | 🟠 Hoch | 🟡 Mittel (erledigt) | – (kein Code-Task) | **Ready to close / needs live verification** – `tests/test_e2e_release_regression.py` (ui_smoke) über PR #649 vorhanden; Ready-Zweig braucht echten GL-Dispatch. |
| [#645](https://github.com/NikolayDA/picture_helper/issues/645) | Live-GL-Performance-Suite im Benchmark-Harness | 🟡 Mittel | 🟡 Mittel (erledigt) | – (kein Code-Task) | **Ready to close / needs live verification** – `preview3d-live`-Suite in `scripts/benchmark.py` über PR #649 vorhanden. |
| [#646](https://github.com/NikolayDA/picture_helper/issues/646) | Vision-Vorbewertung, Evidenz-Aggregation, Abschlussmatrix | 🟡 Mittel | 🟡 Mittel (erledigt) | – (kein Code-Task) | **Ready to close / needs live verification** – `abnahme_vision_check.py`/`abnahme_aggregate.py` über PR #647/#649 vorhanden; braucht zusätzlich `ANTHROPIC_API_KEY`-Secret für echte Bewertung. |
| [#648](https://github.com/NikolayDA/picture_helper/issues/648) | Nativer 3D-Render-Nachweis des gepackten Artefakts | 🟡 Mittel | 🟡 Mittel | Sonnet 5 · mittel | **Ready for PR** – klar umrissene, unabhängige Lücke (Screenshot-Automations-Hook im gepackten Artefakt statt Source-Checkout); einzige echte verbleibende Codeaufgabe der Abnahme-Automatisierung. |
| [#595](https://github.com/NikolayDA/picture_helper/issues/595) | [3D] Performance, Packaging, Doku, End-to-End-Abnahme | 🟡 Mittel | 🟡 Mittel (gesunken, Automatisierung existiert) | Sonnet 5 · mittel | **Blocked** – wartet auf denselben Hardware-Dispatch wie #639 sowie #648. |
| [#582](https://github.com/NikolayDA/picture_helper/issues/582) | [Epic] Echte 3D-Reliefvorschau | 🟡 Mittel | 🟠 Hoch (sehr groß, MVP fertig) | – (Tracking-Epic) | **Blocked** – wartet nur noch auf #595. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | OpenAI-Quota für manuelle Codex-Security-Prüfung wiederherstellen | 🟢 Niedrig | 🟢 Niedrig | – (kein Code-Task) | **Blocked (extern)** – unverändert seit 2026-07-15: reiner externer Billing-Tracker, blockiert nichts im Repository. |

### Als Nächstes empfohlen

1. **#640–#643 schließen** — Umsetzung ist vollständig (PR #647), es fehlt nur die manuelle Bestätigung durch den Owner.
2. **#648 umsetzen** — die einzige verbleibende Codeaufgabe: Automations-/Screenshot-Modus im gepackten Artefakt für einen echten 3D-Render-Nachweis.
3. **Self-hosted Runner registrieren und `release-abnahme.yml` per `workflow_dispatch` auslösen** — verifiziert #642–#646 mit echter Hardware-Evidenz und liefert die Abschlussmatrix für #595.
4. **Nach grünem Lauf + #648:** #595 schließen, danach #582 (nur noch von #595 blockiert).
5. **#245** bleibt liegen — kein Repository-Patch kann den externen OpenAI-Billing-Blocker beheben.

*Drift-Hinweis:* Dieser Nachzug gleicht den Snapshot mit dem tatsächlichen `main`-Stand (ungekürzte Git-Historie, zuvor durch einen Shallow-Clone verdeckt) und einer Live-GitHub-Abfrage ab; er ersetzt den 2026-07-18-Stand mit 3 offenen Issues. Künftige Updates prüfen Status, Checklisten und Abhängigkeiten weiterhin live statt nur einen Zeitstempel fortzuschreiben.

## Vorige Runden

- **2026-07-21 (Abnahme-Automatisierung, Epic #639)** — Epic #639 eröffnet und binnen eines Tages größtenteils umgesetzt: ADR/Doku (#640), Workflow-Gerüst (#641), Linux-/macOS-Hardware-Smokes (#642/#643), E2E-Regressionstest (#644), Live-GL-Performance-Suite (#645), Vision-Vorbewertung + Abschlussmatrix (#646) – alle über PR #647/#649 gemergt, aber wegen deutscher Schließen-Schlüsselwörter nicht automatisch geschlossen; Folge-Issue #648 (nativer 3D-Render-Nachweis) bleibt die einzige offene Codeaufgabe. Live-Stand 12 offene Issues.
- **2026-07-20 (Pi-5-Hardware-Smoke)** — drei reale Packaging-Bugs auf Raspberry Pi 5 gefunden und behoben (PR #627/#631); App startet bestätigt inkl. 3D-Vorschau.
- **2026-07-18 (Post-Merge-Nachprüfung)** — #551 und #592–#594 als erledigt bestätigt; #582/#595 wegen offener Packaging-/Plattform-, Performance- und Screenshot-Nachweise wieder geöffnet; Live-Stand 3.
- **2026-07-18 (Audit-Nachzug #614–#616)** — Future-Version-Härtung aus PR #614 nachgetragen; #597/#598 über PR #615 und #606 über PR #616 abgeschlossen; Live-Stand 7.
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
