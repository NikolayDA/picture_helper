**Deutsch** · [English](docs/i18n/en/RECOMMENDATIONS.md) · [Español](docs/i18n/es/RECOMMENDATIONS.md) · [Français](docs/i18n/fr/RECOMMENDATIONS.md) · [Українська](docs/i18n/uk/RECOMMENDATIONS.md) · [简体中文](docs/i18n/zh/RECOMMENDATIONS.md)

# Codeanalyse & bewertete Empfehlungen: BgRemover

## Bewertungsskala

| Symbol | Priorität | Bedeutung |
|--------|-----------|-----------|
| 🔴 | Kritisch | Fehler, Abstürze oder Datenverlust |
| 🟠 | Hoch | Spürbarer Einfluss auf Zuverlässigkeit oder Wartbarkeit |
| 🟡 | Mittel | Sinnvolle Verbesserung für Qualität, Lesbarkeit oder Testbarkeit |
| 🟢 | Niedrig | Optionales Polishing oder Prozessverbesserung |

## Aktueller Stand (2026-07-22)

Ruff, mypy und die lokale Testsuite bleiben die Baseline vor neuen PRs. Seit der letzten Runde wurden **#640–#645** und **#648** vollständig abgenommen und geschlossen (Hardware-Evidenz aus dem `release-abnahme.yml`-Dispatch vom 2026-07-21, Abschlussmatrix-Kommentar in #595: macOS-arm64- und Pi-5-Smokes, native 3D-E2E und Live-GL-Performance zeigen durchgehend **✅ erfüllt**). Live-Stand nach GitHub-Abfrage: **6** offene Issues – der niedrigste Stand seit Beginn des 3D-Epics.

### Ergebnis der Nachprüfung

- **Alt-Baseline stabil:** **N1/N2/N4/N5/N6/N7/N8**, **O1–O7** und alle seit
  **2026-06-25** abgeschlossenen Punkte bleiben erledigt.
- Epic **#639** ist mit 7 von 8 Teil-Issues fertig; die Teil-Issue-Checkliste im Issue-Text war noch unverändert (alle Kästchen leer), obwohl #640–#645/#648 längst geschlossen waren – heute nachgetragen (Kommentar + Body-Edit in #639), kein Code betroffen.
- **Kein Issue ist aktuell „ready for PR"** im klassischen Sinn: Alle sechs verbleibenden offenen Issues sind entweder reine externe/operative Aufgaben (Secret setzen, Billing klären) oder Epics, die ausschließlich auf genau diese externen Aufgaben warten. Es gibt derzeit keinen offenen, code-seitig unbearbeiteten Task.
- Einziger verbleibender Blocker der gesamten Kette: Repository-Secret `ANTHROPIC_API_KEY` fehlt (**#656**), daher zeigt die Abschlussmatrix-Zeile „Screenshots (Vision-Vorbewertung)" durchgehend `❓ unbewertet` statt echter Verdikte. Der Fail-safe-Pfad selbst funktioniert nachweislich wie vorgesehen.

## Offene GitHub-Issues – Triage-Stand (2026-07-22)

| # | Titel | Relevanz | Komplexität | Empfohlenes Modell (Aufwand) | Nächster Schritt |
|---|-------|----------|--------------|-------------------------------|-------------------|
| [#656](https://github.com/NikolayDA/picture_helper/issues/656) | ANTHROPIC_API_KEY-Secret für Vision-Vorbewertung aktivieren | 🟠 Hoch (letzter Blocker der gesamten Abnahme-Kette) | 🟢 Niedrig (rein operativ, kein Code) | – (kein Agent; Repo-Owner: Settings → Secrets) | Blocked (extern) – Secret hinterlegen, dann Dispatch erneut prüfen |
| [#646](https://github.com/NikolayDA/picture_helper/issues/646) | Vision-Vorbewertung, Evidenz-Aggregation, Abschlussmatrix | 🟠 Hoch (letztes offenes Teil-Issue von Epic #639) | 🟢 Niedrig (Code/Tests bereits gemergt in PR #649) | Sonnet 5 (low) – nur Verifikation, kein neuer Code erwartet | Needs verification – nach #656 realen Vision-Dispatch prüfen, dann schließen |
| [#639](https://github.com/NikolayDA/picture_helper/issues/639) | [Epic] Automatisierte Release-Abnahme | 🟠 Hoch (Epic, 7/8 Teil-Issues fertig) | 🟢 Niedrig (nur noch #646 offen) | – (Epic, kein direkter Agent-Einsatz) | Blocked – schließt automatisch mit #646 |
| [#595](https://github.com/NikolayDA/picture_helper/issues/595) | [3D] Performance-/Packaging-/Doku-/E2E-Abnahme | 🟠 Hoch (Abnahme-Gate für Epic #582) | 🟢 Niedrig (alle Kriterien bis auf Vision-Zeile ✅) | – (kein Code-Task) | Blocked – wartet auf #646/#656, danach schließen |
| [#582](https://github.com/NikolayDA/picture_helper/issues/582) | [Epic] Echte 3D-Reliefvorschau | 🟠 Hoch (großes, fast fertiges Feature-Epic) | 🟢 Niedrig (nur noch #595 offen) | – (Epic, kein direkter Agent-Einsatz) | Blocked – schließt automatisch mit #595 |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | OpenAI-Quota für manuellen Codex-Scan wiederherstellen | 🟢 Niedrig (blockiert nur einen optionalen manuellen Scan) | 🟢 Niedrig (rein operativ, kein Code) | – (kein Agent; Repo-Owner: Billing) | Blocked (extern) – Billing/Quota beim OpenAI-Platform-Projekt klären |

### Als Nächstes empfohlen

1. **#656** zuerst erledigen (Repository-Secret `ANTHROPIC_API_KEY` setzen) – das ist der einzige verbleibende Hebel, der die gesamte Kette #646 → #639 → #595 → #582 entsperrt.
2. Danach `release-abnahme.yml` erneut per `workflow_dispatch` auslösen und prüfen, ob die Vision-Zeile der Abschlussmatrix echte Verdikte statt `unbewertet` zeigt (mit kurzer Stichprobenkontrolle gegen die Screenshots, wie in #656 gefordert).
3. Bei grüner Vision-Zeile **#646** schließen; damit schließen **#639**, **#595** und **#582** in Kaskade (jeweils kurz gegenprüfen, bevor manuell geschlossen wird).
4. **#245** bleibt separat als rein externer Billing-/Quota-Tracker liegen; keine Aktion im Repository möglich oder nötig.
5. Es gibt aktuell **keinen** offenen Issue, der eine neue Code-PR rechtfertigt – die nächste sinnvolle Agent-Aufgabe ist die Verifikation nach #656, nicht neue Implementierung.

## Vorige Runden

- **2026-07-22 (Issue-Review)** — Vollständige Neubewertung aller offenen Issues: #640–#645 und #648 waren bereits über den Abnahme-Dispatch vom 2026-07-21 abgenommen und geschlossen worden, die Teil-Issue-Checkliste in Epic #639 war dabei nicht nachgezogen worden (heute per Issue-Edit + Kommentar nachgetragen, kein Code betroffen). Neuer Blocker **#656** (fehlendes `ANTHROPIC_API_KEY`-Secret) identifiziert als einziger verbleibender Hebel für #646/#639/#595/#582. Live-Stand 6 offene Issues – niedrigster Stand seit Epic #582.
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
