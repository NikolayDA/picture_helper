**Deutsch** · [English](docs/i18n/en/RECOMMENDATIONS.md) · [Español](docs/i18n/es/RECOMMENDATIONS.md) · [Français](docs/i18n/fr/RECOMMENDATIONS.md) · [Українська](docs/i18n/uk/RECOMMENDATIONS.md) · [简体中文](docs/i18n/zh/RECOMMENDATIONS.md)

# Codeanalyse & bewertete Empfehlungen: BgRemover

## Bewertungsskala

| Symbol | Priorität | Bedeutung |
|--------|-----------|-----------|
| 🔴 | Kritisch | Fehler, Abstürze oder Datenverlust |
| 🟠 | Hoch | Spürbarer Einfluss auf Zuverlässigkeit oder Wartbarkeit |
| 🟡 | Mittel | Sinnvolle Verbesserung für Qualität, Lesbarkeit oder Testbarkeit |
| 🟢 | Niedrig | Optionales Polishing oder Prozessverbesserung |

## Aktueller Stand (2026-07-23, #668/#669 abgeschlossen)

Ruff, mypy und die lokale Testsuite bleiben die Baseline vor neuen PRs. Seit der letzten Runde wurden beide zuletzt offenen Audit-Issues abgeschlossen:

- **#669** (Live-Stand veraltet) — direkt geschlossen: Der vorherige RECOMMENDATIONS-Reconcile (PR #671) hatte den Inhalt bereits vollständig aktuell gemacht (#659/#660 korrekt als geschlossen geführt, #668 bereits aufgenommen); eine zusätzliche No-Op-PR war nicht nötig.
- **#668** (Screenshot-Set-Referenzen veraltet) — mit diesem Update behoben: `ANLEITUNG.md` und `README.md` (je inkl. aller fünf Übersetzungen) zeigen jetzt auf das aktuelle Set `bgremover_complete_20260722_171622`. `docs/history/EPIC-582-ABNAHME.md` bleibt bewusst beim Set vom 2026-07-19 — dort ist es die tatsächliche Abnahme-Evidenz (GPU-/OS-/Renderer-Provenienz im Manifest), ein Umstellen hätte die dokumentierte Evidenz verfälscht; ein erklärender Hinweis wurde ergänzt, das alte Verzeichnis bleibt entsprechend erhalten. Ein neuer Governance-Test (`tests/test_screenshot_references.py::test_docs_reference_latest_screenshot_set`) fängt künftig eine erneute stille Drift ab.

Live-Stand nach GitHub-Abfrage: **2** offene Issues (#656, #245) — beide rein extern/operativ, kein Code-Blocker.

### Ergebnis der Nachprüfung

- **PR-/Issue-Audit vom 22.–23.07. vollständig:** Die Merge-Stände #657/#658, #661–#665 und #670–#673 wurden gegen ihre beschriebenen Ziele und Akzeptanzkriterien nachgeprüft. Die Abnahme-Automatisierung enthält die fehlenden strukturierten Wächter- und E2E-Nachweise, die Test-/Doku-Nachzüge decken ihre jeweiligen Regressionen ab, und der Release-/Screenshot-Nachzug ist einschließlich generierter Artefakte und Governance-Test konsistent. Es blieb kein reproduzierbarer Code-, Test- oder Dokumentationsrest, der einen neuen Issue oder einen Ergänzungskommentar an einem geschlossenen Issue rechtfertigt.
- **Alt-Baseline stabil:** **N1/N2/N4/N5/N6/N7/N8/N9**, **O1–O8** und alle seit
  **2026-06-25** abgeschlossenen Punkte bleiben erledigt.
- **Release v2.7.0 vollständig abgeschlossen und verifiziert:** Tag, Veröffentlichung und alle drei Gate-Stufen (CI-Matrix, Kandidaten-Build, Hardware-Abnahme) sind gegen genau den tatsächlich getaggten Commit `6f103ed` gelaufen – keine Drift zwischen geprüftem und veröffentlichtem Stand.
- **#669/#668 abgeschlossen** — niedrigster Live-Stand seit Beginn dieser Aufzeichnung.
- **#656/#245** bleiben unverändert rein externe/operative Tracker ohne Code-Bezug.

## Offene GitHub-Issues – Triage-Stand (2026-07-23)

| # | Titel | Relevanz | Komplexität | Empfohlenes Modell (Aufwand) | Nächster Schritt |
|---|-------|----------|--------------|-------------------------------|-------------------|
| [#656](https://github.com/NikolayDA/picture_helper/issues/656) | ANTHROPIC_API_KEY-Secret für Vision-Vorbewertung aktivieren | 🟡 Mittel (verbessert nur Evidenzqualität, kein Blocker laut Vertrag) | 🟢 Niedrig (rein operativ, kein Code) | – (kein Agent; Repo-Owner: Settings → Secrets) | Blocked (extern) – unabhängig erledigbar |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | OpenAI-Quota für manuellen Codex-Scan wiederherstellen | 🟢 Niedrig (blockiert nur einen optionalen manuellen Scan) | 🟢 Niedrig (rein operativ, kein Code) | – (kein Agent; Repo-Owner: Billing) | Blocked (extern) – Billing/Quota beim OpenAI-Platform-Projekt klären |

### Als Nächstes empfohlen

1. **#656** unabhängig erledigen, wenn echte Vision-Verdikte gewünscht sind – Qualitätsverbesserung, kein Blocker.
2. **#245** bleibt separat als rein externer Billing-/Quota-Tracker liegen; keine Aktion im Repository möglich oder nötig.
3. Release v2.7.0 ist vollständig veröffentlicht — kein weiterer releasebezogener Schritt nötig.

## Vorige Runden

- **2026-07-23 (#668/#669 abgeschlossen)** — #669 (Doku-Live-Stand veraltet) direkt geschlossen, da bereits durch PR #671 vollständig aufgelöst, keine weitere Code-/Doku-Änderung nötig. #668 (`ANLEITUNG.md`/`README.md` verweisen auf das verwaiste Screenshot-Set vom 2026-07-19) über einen eigenständigen PR behoben: lebende Doku-Referenzen (je 6 Sprachen) auf das aktuelle Set vom 2026-07-22 migriert; die Abnahme-Evidenz in `docs/history/EPIC-582-ABNAHME.md` bewusst unangetastet gelassen (erklärender Hinweis ergänzt, altes Verzeichnis bleibt erhalten); neuer Governance-Test gegen künftige Screenshot-Drift ergänzt. Live-Stand 2 offene Issues (beide extern/operativ, kein Blocker) – niedrigster Stand seit Beginn dieser Aufzeichnung.
- **2026-07-23 (Release v2.7.0)** — PR #670 (Versions-Bump + CHANGELOG-Umhängen + Icon-Eintrag) gemergt (`6f103ed`); kompletter Gate erneut gegen den neuen Merge-Commit durchlaufen (CI-Matrix, Kandidaten-Build, Hardware-Abnahme, alle grün); Tag `v2.7.0` gesetzt und veröffentlicht (fünf Artefakte). Zwei neue Audit-Issues erfasst: #669 (Doku-Live-Stand veraltet, mit diesem Update behoben) und #668 (verwaistes Screenshot-Set in ANLEITUNG.md, kleine Repo-Hygiene). Live-Stand 4 offene Issues, alle Doku-Hygiene oder extern, kein Code-Blocker.
- **2026-07-22 (Test-Audit-Abschluss)** — Beide zuvor offenen Audit-Issues geschlossen: #660 über PR #664 (Commit `92c14ba`, `gl_smoke`-Marker in TESTING.md dokumentiert), #659 über PR #665 (Commit `c4ab92a`, N9/O8 vollständig umgesetzt, `make check` 1995/5, `make coverage` 93 %). Zusätzlich zwei assetbezogene PRs gemergt (#666 Screenshot-Satz, #667 neues App-Icon), beide noch ohne CHANGELOG-Eintrag. Live-Stand 2 offene Issues (beide extern/operativ, kein Blocker) – niedrigster Stand seit Beginn dieser Aufzeichnung.
- **2026-07-22 (Abnahme-Abschluss)** — Frischer `release-abnahme.yml`-Dispatch (Run #4, Commit `9165c00`) ausgelöst; Matrix gegen #595 geprüft (x86_64 bleibt dokumentiert pausiert, blockiert aber nicht); #595, #646, #639, #582 nacheinander einzeln gegen ihre eigenen Akzeptanzkriterien verifiziert und geschlossen. Einziger echter Rest (mypy-Strenge für `scripts/abnahme_vision_check.py`/`abnahme_aggregate.py`, #646) über PR #662 behoben und gemergt. Zwei neue Audit-Issues erfasst: #660 mit fertigem, ungemergtem Fix (ready for PR), #659 wartet auf eine echte Owner-Entscheidung zu neuen Befund-Vorschlägen. Live-Stand 4 offene Issues.
- **2026-07-22 (Issue-Review, nach Codex-Korrektur)** — Vollständige Neubewertung aller offenen Issues; eine erste Fassung überschätzte die Aussagekraft des 2026-07-21-Dispatches (inzwischen durch PR #657/#658 überholt) und stufte die beratende Vision-Zeile (#656) fälschlich als Blocker ein. Nach PR-Review (Codex) korrigiert: #656 ist unabhängig erledigbar, Linux x86_64 bleibt ein offen deklariertes Kriterium, und #639/#595/#582 schließen nicht automatisch mit ihren jeweiligen Sub-Issues. Live-Stand 6 offene Issues – niedrigster Stand seit Epic #582.
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
