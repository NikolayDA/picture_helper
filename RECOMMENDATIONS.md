**Deutsch** · [English](docs/i18n/en/RECOMMENDATIONS.md) · [Español](docs/i18n/es/RECOMMENDATIONS.md) · [Français](docs/i18n/fr/RECOMMENDATIONS.md) · [Українська](docs/i18n/uk/RECOMMENDATIONS.md) · [简体中文](docs/i18n/zh/RECOMMENDATIONS.md)

# Codeanalyse & bewertete Empfehlungen: BgRemover

## Bewertungsskala

| Symbol | Priorität | Bedeutung |
|--------|-----------|-----------|
| 🔴 | Kritisch | Fehler, Abstürze oder Datenverlust |
| 🟠 | Hoch | Spürbarer Einfluss auf Zuverlässigkeit oder Wartbarkeit |
| 🟡 | Mittel | Sinnvolle Verbesserung für Qualität, Lesbarkeit oder Testbarkeit |
| 🟢 | Niedrig | Optionales Polishing oder Prozessverbesserung |

## Aktueller Stand (2026-07-22, nach Abnahme-Abschluss)

Ruff, mypy und die lokale Testsuite bleiben die Baseline vor neuen PRs. Der in der letzten Runde geforderte frische `release-abnahme.yml`-Dispatch wurde ausgelöst (Run [#4](https://github.com/NikolayDA/picture_helper/actions/runs/29908256619), Commit `9165c00`, nach #657/#658) und lieferte eine vollständig grüne Matrix bis auf die bewusst pausierte Linux-x86_64-Zeile. Darauf aufbauend wurden alle vier zuvor blockierten Issues **einzeln gegen ihre eigenen Akzeptanzkriterien geprüft und geschlossen** – kein Issue wurde automatisch mit einem anderen mitgeschlossen:

1. **#595** — alle Kriterien aus der „Weiterhin offen"-Liste erfüllt **außer** der bewusst pausierten Linux-x86_64-Zeile: Die bleibt laut ADR/`RELEASE_AUTOMATION.md` weiterhin „offen deklariert, nicht erfüllt" – für diesen Abschluss wurde sie explizit als Ausnahme (Waiver) behandelt statt fälschlich als erfüllt umgedeutet (analog zu #639s eigenem Akzeptanzkriterium).
2. **#646** — fünf von sechs Kriterien direkt erfüllt; ein echter Rest wurde gefunden: `scripts/abnahme_vision_check.py`/`abnahme_aggregate.py` waren komplett von `make type`/`make check` ausgenommen, ein strikter Probelauf deckte einen echten `union-attr`-Fehler auf. Behoben und über PR #662 (Commit `f47445f`) gemergt.
3. **#639** — nach Abschluss von #646 sind alle acht Teil-Issues geschlossen; Checkliste im Issue-Body nachgezogen.
4. **#582** — alle fünf Sub-Issues geschlossen; die geforderte Textur-Stretch-Entscheidung liegt bereits im ADR vor, die README-Lücke aus dem Audit vom 2026-07-20 ist behoben, `make ui` läuft grün.

Zusätzlich sind seit der letzten Runde zwei neue Issues aus automatisierten Audits hinzugekommen: **#660** ist bereits fertig und nur noch ein Merge entfernt, **#659** wartet dagegen noch auf eine echte Owner-Entscheidung.

Live-Stand nach GitHub-Abfrage: **4** offene Issues.

### Ergebnis der Nachprüfung

- **Alt-Baseline stabil:** **N1/N2/N4/N5/N6/N7/N8**, **O1–O7** und alle seit
  **2026-06-25** abgeschlossenen Punkte bleiben erledigt.
- **#646/#639/#595/#582 sind jetzt einzeln verifiziert und geschlossen** (kein Auto-Close-Domino); der einzige dabei gefundene echte Rest (mypy-Strenge für die Abnahme-Skripte, #646) ist über PR #662 behoben und gemergt.
- **#659/#660 sind neu:** #660 ist **ready for PR** – ein fertiger, aber ungemergter Fix liegt auf Branch `claude/festive-gates-4dkzds` (Commit `80b7aa0`), hier ist nur noch zu mergen, nichts mehr zu entscheiden. #659 ist dagegen tatsächlich **noch unentschieden** – eine reine Analyse ohne Code-Änderung, die zwei neue Befund-IDs (**N9**/**O8**) vorschlägt und noch auf Owner-Zustimmung wartet.
- Der verbleibende Arbeitsschritt ist damit **kein** Abnahme-Thema mehr, sondern: PR für #660 öffnen/mergen sowie eine Entscheidung zu den in #659 vorgeschlagenen Befunden einholen.

## Offene GitHub-Issues – Triage-Stand (2026-07-22)

| # | Titel | Relevanz | Komplexität | Empfohlenes Modell (Aufwand) | Nächster Schritt |
|---|-------|----------|--------------|-------------------------------|-------------------|
| [#660](https://github.com/NikolayDA/picture_helper/issues/660) | TESTING.md-Audit: aktuell, eine kleine Lücke behoben (`gl_smoke`-Marker undokumentiert) | 🟢 Niedrig (reine Doku-Genauigkeit, keine funktionale Auswirkung) | 🟢 Niedrig (ein kurzer Absatz, bereits umgesetzt) | – (kein Agent nötig; Fix liegt bereits auf Branch `claude/festive-gates-4dkzds`, Commit `80b7aa0`) | Ready for PR – nur noch öffnen/mergen, danach Issue schließen |
| [#659](https://github.com/NikolayDA/picture_helper/issues/659) | Test-Suite-Audit: kleinere Qualitätslücken in 6 Batches (`test_i18n_sync`, `test_viewer_3d` u. a.) | 🟡 Mittel (Testqualität/Coverage, kein Blocker) | 🟡 Mittel (Mix aus trivialen Löschungen/Fixes und echten Coverage-Lücken über mehrere Module) | Sonnet 5 (medium) – bei Zustimmung zur Übernahme als N9/O8 | Needs decision – Vorschlag noch nicht in die Befund-Liste übernommen; Owner-Zustimmung ausstehend, danach Umsetzung als eigener PR |
| [#656](https://github.com/NikolayDA/picture_helper/issues/656) | ANTHROPIC_API_KEY-Secret für Vision-Vorbewertung aktivieren | 🟡 Mittel (verbessert nur Evidenzqualität, kein Blocker laut Vertrag) | 🟢 Niedrig (rein operativ, kein Code) | – (kein Agent; Repo-Owner: Settings → Secrets) | Blocked (extern) – unabhängig erledigbar |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | OpenAI-Quota für manuellen Codex-Scan wiederherstellen | 🟢 Niedrig (blockiert nur einen optionalen manuellen Scan) | 🟢 Niedrig (rein operativ, kein Code) | – (kein Agent; Repo-Owner: Billing) | Blocked (extern) – Billing/Quota beim OpenAI-Platform-Projekt klären |

### Als Nächstes empfohlen

1. **#660**: PR für den bereits committeten TESTING.md-Fix öffnen (Branch `claude/festive-gates-4dkzds`, Commit `80b7aa0`) und mergen; danach Issue schließen.
2. **#659**: Entscheiden, ob die vorgeschlagenen Befunde **N9** (totes Testgewicht `test_i18n_sync.py` entfernen/mergen) und **O8** (tautologische `viewer_3d`-Assertions + Coverage-Lücken in `screenshot3d.py`/`viewer_3d.py`/`preview3d_capability.py`/`height_map.py`/`gloss_preview.py`) übernommen werden; bei Zustimmung als eigenen PR umsetzen.
3. **#656** unabhängig davon erledigen, wenn echte Vision-Verdikte gewünscht sind – es ist eine Qualitätsverbesserung, kein Blocker.
4. **#245** bleibt separat als rein externer Billing-/Quota-Tracker liegen; keine Aktion im Repository möglich oder nötig.
5. Der Abnahme-/3D-Epic-Strang (#646/#639/#595/#582) ist vollständig abgeschlossen und braucht keine weitere Aktion.

## Vorige Runden

- **2026-07-22 (Abnahme-Abschluss)** — Frischer `release-abnahme.yml`-Dispatch (Run #4, Commit `9165c00`) ausgelöst; Matrix gegen #595 geprüft (x86_64 bleibt dokumentiert pausiert, blockiert aber nicht); #595, #646, #639, #582 nacheinander einzeln gegen ihre eigenen Akzeptanzkriterien verifiziert und geschlossen. Einziger echter Rest (mypy-Strenge für `scripts/abnahme_vision_check.py`/`abnahme_aggregate.py`, #646) über PR #662 behoben und gemergt. Zwei neue Audit-Issues erfasst: #660 mit fertigem, ungemergtem Fix (ready for PR), #659 wartet auf eine echte Owner-Entscheidung zu neuen Befund-Vorschlägen. Live-Stand 4 offene Issues – niedrigster Stand seit Beginn dieser Aufzeichnung.
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
