**Deutsch** · [English](docs/i18n/en/RECOMMENDATIONS.md) · [Español](docs/i18n/es/RECOMMENDATIONS.md) · [Français](docs/i18n/fr/RECOMMENDATIONS.md) · [Українська](docs/i18n/uk/RECOMMENDATIONS.md) · [简体中文](docs/i18n/zh/RECOMMENDATIONS.md)

# Codeanalyse & bewertete Empfehlungen: BgRemover

## Bewertungsskala

| Symbol | Priorität | Bedeutung |
|--------|-----------|-----------|
| 🔴 | Kritisch | Fehler, Abstürze oder Datenverlust |
| 🟠 | Hoch | Spürbarer Einfluss auf Zuverlässigkeit oder Wartbarkeit |
| 🟡 | Mittel | Sinnvolle Verbesserung für Qualität, Lesbarkeit oder Testbarkeit |
| 🟢 | Niedrig | Optionales Polishing oder Prozessverbesserung |

## Aktueller Stand (2026-07-22, korrigiert nach Codex-Review)

Ruff, mypy und die lokale Testsuite bleiben die Baseline vor neuen PRs. Seit der letzten Runde wurden **#640–#645** und **#648** geschlossen. Eine erste Fassung dieses Updates stützte sich dabei allein auf den `release-abnahme.yml`-Dispatch vom 2026-07-21 (Commit `fa2241d`) und erklärte die Vision-Zeile (#656) fälschlich zum einzigen Blocker der Kette – der PR-Review (Codex) hat vier Punkte davon widerlegt, die hier korrigiert sind:

1. **Dispatch-Evidenz war bereits veraltet.** PR #657 (löst #642, gemergt `521bd63`, nach `fa2241d`) macht `waechter_ergebnisse` zum Pflichtfeld in `abnahme_aggregate.py::validate_evidence` und PR #658 (löst #644, gemergt `4416e80`) ergänzt fehlende E2E-Prüfungen. Der zitierte Dispatch lief **vor** beiden Fixes – seine „✅ erfüllt"-Zeilen belegen also nicht den aktuellen Code. Ein frischer Dispatch nach `main`-Stand ist nötig, bevor die Matrix als gültiger Nachweis zitiert werden darf.
2. **Vision-Vorbewertung ist beratend, kein Blocker.** `abnahme_aggregate.py::has_blocking_gaps` lässt ausdrücklich nur die Zeile „Screenshots (Vision-Vorbewertung)" `unbewertet` bleiben, ohne den Lauf zu blockieren (`docs/RELEASE_AUTOMATION.md` §4: „fehlt [`ANTHROPIC_API_KEY`], bleibt jedes Kriterium unbewertet und blockiert nie"). **#656** ist damit eine sinnvolle Verbesserung der Evidenzqualität, aber **kein** Blocker für #646, #639, #595 oder #582.
3. **Linux x86_64 bleibt ein offenes, nicht nur pausiertes Kriterium.** Laut ADR/`RELEASE_AUTOMATION.md` §5 gilt der pausierte x86_64-Hardware-Smoke für Release-Entscheidungen ausdrücklich als „offen deklariert, nicht erfüllt" – das ist ein bewusst akzeptierter, aber weiterhin offener Punkt, keine erledigte Zeile.
4. **Kein Auto-Close der Epics.** Schließt jemand #646, aktualisiert GitHub nur den Sub-Issue-Fortschritt von #639; #639, #595 und #582 müssen jeweils einzeln manuell geprüft und geschlossen werden.

Live-Stand nach GitHub-Abfrage: **6** offene Issues.

### Ergebnis der Nachprüfung

- **Alt-Baseline stabil:** **N1/N2/N4/N5/N6/N7/N8**, **O1–O7** und alle seit
  **2026-06-25** abgeschlossenen Punkte bleiben erledigt.
- Epic **#639** ist mit 7 von 8 Teil-Issues fertig; die Teil-Issue-Checkliste im Issue-Text war noch unverändert (alle Kästchen leer), obwohl #640–#645/#648 längst geschlossen waren – nachgetragen (Kommentar + Body-Edit in #639); der Body-Edit überschätzte allerdings ebenfalls die Dispatch-Evidenz und wird separat per Kommentar korrigiert.
- **Kein Issue ist aktuell „ready for PR"** im klassischen Sinn: Alle sechs verbleibenden offenen Issues sind entweder reine externe/operative Aufgaben (Secret setzen, Billing klären) oder Epics, die im Kern auf einen frischen, validen Abnahme-Dispatch sowie die dokumentierte x86_64-Pause warten.
- Der eigentliche verbleibende Arbeitsschritt ist **kein** fehlendes Secret, sondern ein erneuter `release-abnahme.yml`-Dispatch auf dem aktuellen `main` (nach #657/#658), dessen Matrix dann gegen die #595-Kriterien inklusive der bewusst offenen x86_64-Zeile geprüft werden muss.

## Offene GitHub-Issues – Triage-Stand (2026-07-22)

| # | Titel | Relevanz | Komplexität | Empfohlenes Modell (Aufwand) | Nächster Schritt |
|---|-------|----------|--------------|-------------------------------|-------------------|
| [#646](https://github.com/NikolayDA/picture_helper/issues/646) | Vision-Vorbewertung, Evidenz-Aggregation, Abschlussmatrix | 🟠 Hoch (letztes offenes Teil-Issue von Epic #639) | 🟢 Niedrig (Code/Tests bereits gemergt in PR #647/#649/#657) | Sonnet 5 (low) – nur Verifikation gegen einen frischen Dispatch, kein neuer Code erwartet | Needs verification – eigene Akzeptanzkriterien hängen **nicht** an #656 (Vision-Fail-safe ist bereits belegt); nach frischem Dispatch schließen |
| [#639](https://github.com/NikolayDA/picture_helper/issues/639) | [Epic] Automatisierte Release-Abnahme | 🟠 Hoch (Epic, 7/8 Teil-Issues fertig) | 🟢 Niedrig (nur noch #646 offen) | – (Epic, kein direkter Agent-Einsatz) | Blocked – schließt **nicht automatisch** mit #646; nach #646-Abschluss einzeln manuell prüfen und schließen |
| [#595](https://github.com/NikolayDA/picture_helper/issues/595) | [3D] Performance-/Packaging-/Doku-/E2E-Abnahme | 🟠 Hoch (Abnahme-Gate für Epic #582) | 🟡 Mittel (Vision ist beratend erfüllt, x86_64-Kriterium bleibt aber offen deklariert) | – (kein Code-Task) | Blocked – wartet auf einen frischen, validen Dispatch nach #657/#658 und eine explizite Entscheidung zur x86_64-Pause |
| [#582](https://github.com/NikolayDA/picture_helper/issues/582) | [Epic] Echte 3D-Reliefvorschau | 🟠 Hoch (großes, fast fertiges Feature-Epic) | 🟢 Niedrig (nur noch #595 offen) | – (Epic, kein direkter Agent-Einsatz) | Blocked – schließt **nicht automatisch** mit #595; danach einzeln manuell prüfen und schließen |
| [#656](https://github.com/NikolayDA/picture_helper/issues/656) | ANTHROPIC_API_KEY-Secret für Vision-Vorbewertung aktivieren | 🟡 Mittel (verbessert nur Evidenzqualität, kein Blocker laut Vertrag) | 🟢 Niedrig (rein operativ, kein Code) | – (kein Agent; Repo-Owner: Settings → Secrets) | Blocked (extern) – unabhängig vom Rest der Kette erledigbar |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | OpenAI-Quota für manuellen Codex-Scan wiederherstellen | 🟢 Niedrig (blockiert nur einen optionalen manuellen Scan) | 🟢 Niedrig (rein operativ, kein Code) | – (kein Agent; Repo-Owner: Billing) | Blocked (extern) – Billing/Quota beim OpenAI-Platform-Projekt klären |

### Als Nächstes empfohlen

1. Einen frischen `release-abnahme.yml`-Dispatch auf dem aktuellen `main` (nach #657/#658) auslösen – die zuvor zitierte Matrix vom 2026-07-21 belegt den heutigen Code nicht mehr.
2. Die neue Matrix gegen **alle** #595-Kriterien prüfen, inklusive der bewusst offenen x86_64-Zeile (bleibt „pausiert/offen deklariert", auch wenn alles andere grün ist) – dafür ggf. explizit klären, ob #595 mit dokumentierter x86_64-Pause schließen darf (wie es #639 bereits für sich selbst vorsieht) oder ob das eine separate Freigabe braucht.
3. **#646** anhand seiner eigenen Akzeptanzkriterien prüfen (Fail-safe-Verhalten ist bereits belegt, hängt nicht an #656) und bei Erfüllung schließen; danach **#639** separat und manuell prüfen/schließen, ebenso im Anschluss **#595** und **#582** – kein Issue schließt automatisch mit einem anderen.
4. **#656** unabhängig davon erledigen, wenn echte Vision-Verdikte gewünscht sind – es ist eine Qualitätsverbesserung, kein Blocker.
5. **#245** bleibt separat als rein externer Billing-/Quota-Tracker liegen; keine Aktion im Repository möglich oder nötig.
6. Es gibt aktuell **keinen** offenen Issue, der eine neue Code-PR rechtfertigt – die nächste sinnvolle Agent-Aufgabe ist die Verifikation nach einem frischen Dispatch, nicht neue Implementierung.

## Vorige Runden

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
