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

Ruff, mypy und die lokale Testsuite bleiben die Baseline vor neuen PRs. Heute wurden PR **#647**, **#649**, **#650**, **#651** und **#652** gemergt. Damit sind ADR, Workflow, Plattform-Smokes, Source-E2E, Live-GL, Aggregation und der native Screenshot-Hook im gepackten Artefakt in `main`. **#640** und **#641** sind geschlossen. **#648** wurde nach der Nachprüfung wieder geöffnet, weil noch kein erfolgreicher Hardwarelauf mit getrennten Nachweisen für AppImage, installiertes `.deb` und DMG vorliegt. Live-Stand nach GitHub-Abfrage: **10** offene Issues.

### Ergebnis der Nachprüfung

- **Alt-Baseline stabil:** **N1/N2/N4/N5/N6/N7/N8**, **O1–O7** und die seit
  **2026-06-25** abgeschlossenen Punkte bleiben erledigt.
- Die gemergten Änderungen sind strukturell sauber; alle PR-Gates und Review-Threads waren grün bzw. aufgelöst.
- Der Code-Nachzug schließt die gefundenen Restlücken: eigener nativer 3D-Nachweis je Paketklasse, grafische Runner-Preflights, erneuter 3D-Nachweis nach Save/Open, drei Live-GL-Wiederholungen mit Rohwerten und echter Prozess-RSS-High-Water-Mark sowie ein validierbares `target_issue`-Dispatch-Eingabefeld.
- Der verbleibende Blocker ist operativ: Ohne registrierte Runner in einer echten grafischen Sitzung und einen erfolgreichen `release-abnahme.yml`-Dispatch gibt es noch keine belastbare Zielhardware-Evidenz. Deshalb bleiben **#642–#646** und **#648** offen.

## Offene GitHub-Issues – Triage-Stand (2026-07-21)

| # | Status | Empfohlener nächster Schritt |
|---|--------|------------------------------|
| [#639](https://github.com/NikolayDA/picture_helper/issues/639) | 🟠 Epic fast fertig | Runner konfigurieren, vollständigen Abnahme-Dispatch ausführen und Evidenz prüfen. |
| [#642](https://github.com/NikolayDA/picture_helper/issues/642) | 🟡 Code fertig, Live-Nachweis offen | Pi-5-Job: AppImage und installiertes `.deb` jeweils nativ prüfen. |
| [#643](https://github.com/NikolayDA/picture_helper/issues/643) | 🟡 Code fertig, Live-Nachweis offen | M3-Job: DMG, Retina und nativen 3D-Frame prüfen. |
| [#644](https://github.com/NikolayDA/picture_helper/issues/644) | 🟡 Code fertig, Live-Nachweis offen | E2E auf Hardware bis zum erneuten 3D-Ready nach Save/Open ausführen. |
| [#645](https://github.com/NikolayDA/picture_helper/issues/645) | 🟡 Code fertig, Live-Nachweis offen | Dreifache 1-/16-/40-MP-Live-GL-Messung auf Zielhardware ausführen. |
| [#646](https://github.com/NikolayDA/picture_helper/issues/646) | 🟡 Code fertig, Live-Nachweis offen | Abschlussmatrix erzeugen und an das gewählte Ziel-Issue posten. |
| [#648](https://github.com/NikolayDA/picture_helper/issues/648) | 🟡 Wieder geöffnet | Erst nach nativen Paketnachweisen für AppImage, `.deb` und DMG schließen. |
| [#595](https://github.com/NikolayDA/picture_helper/issues/595) | 🟡 Blockiert | Wartet auf die grüne Hardware-Abnahme aus #639. |
| [#582](https://github.com/NikolayDA/picture_helper/issues/582) | 🟡 Blockiert | Nach #595 abschließen. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | 🟢 Extern blockiert | OpenAI-Billing/Quota außerhalb des Repositories klären. |

### Als Nächstes empfohlen

1. Diesen Audit-Nachzug mergen und die Runner gemäß `docs/RELEASE_AUTOMATION.md` in der grafischen Benutzer-Sitzung konfigurieren.
2. `release-abnahme.yml` mit Release-Tag oder Build-Run-ID, allen verfügbaren Plattformen und dem gewünschten `target_issue` auslösen.
3. Nur bei vollständiger grüner Evidenz **#642–#646** und **#648** schließen; danach **#595** und **#582**.
4. **#245** separat als externen Billing-/Quota-Tracker behandeln.

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
