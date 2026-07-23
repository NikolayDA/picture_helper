**Deutsch** · [English](docs/i18n/en/RECOMMENDATIONS.md) · [Español](docs/i18n/es/RECOMMENDATIONS.md) · [Français](docs/i18n/fr/RECOMMENDATIONS.md) · [Українська](docs/i18n/uk/RECOMMENDATIONS.md) · [简体中文](docs/i18n/zh/RECOMMENDATIONS.md)

# Codeanalyse & bewertete Empfehlungen: BgRemover

## Bewertungsskala

| Symbol | Priorität | Bedeutung |
|--------|-----------|-----------|
| 🔴 | Kritisch | Fehler, Abstürze oder Datenverlust |
| 🟠 | Hoch | Spürbarer Einfluss auf Zuverlässigkeit oder Wartbarkeit |
| 🟡 | Mittel | Sinnvolle Verbesserung für Qualität, Lesbarkeit oder Testbarkeit |
| 🟢 | Niedrig | Optionales Polishing oder Prozessverbesserung |

## Aktueller Stand (2026-07-22, vor Release-Vorbereitung)

Ruff, mypy und die lokale Testsuite bleiben die Baseline vor neuen PRs. Seit der letzten Runde wurden beide zuvor offenen Audit-Issues einzeln abgeschlossen:

1. **#660** — der bereits fertige TESTING.md-Fix (Branch `claude/festive-gates-4dkzds`, Commit `80b7aa0`) ist über PR #664 (Commit `92c14ba`) gemergt: kurzer Absatz zum `gl_smoke`-Marker ergänzt.
2. **#659** — Owner-Zustimmung zu **N9**/**O8** liegt vor; alle neun Punkte der Umsetzungsliste sind über PR #665 (Commit `c4ab92a`) umgesetzt: `tests/test_i18n_sync.py` als redundantes Soft-Gate entfernt (durch den harten `test_i18n_docs.py`-Test weiter abgedeckt), tautologische/bedingt leerlaufende `test_viewer_3d.py`-Assertions durch deterministische Prüfungen ersetzt, Maus-/Wheel-/Tastatur-Dispatch sowie negative Post-ready-Zweige in `screenshot3d.py`/`viewer_3d.py`/`preview3d_capability.py`/`height_map.py` isoliert getestet, bestätigte Copy-Paste-Duplikate entfernt, redundante Release-/EufyMake-Prüfungen konsolidiert. `make check`: 1995 passed/5 skipped (Baseline 1962/5); `make coverage`: 93 % (Baseline 92 %, Gate `fail_under=86`). Das vermutete Big-Endian-Problem in `gloss_preview.py` wurde **nicht** bestätigt (kein Produktionsfehler).

Zusätzlich sind zwei rein assetbezogene PRs gemerged, die noch **keinen CHANGELOG-Eintrag** haben: **#666** (kompletter neuer Screenshot-Satz inkl. nativer 3D-Zustände, Apple-M3-Max-Renderer-Provenance) und **#667** (neues App-Icon „Liquid Glass", 1024×1024 RGBA – macOS `.icns`, AppImage- und `.deb`-Icon leiten alle vom selben `BgRemover_icon.png`-Master ab; Linux-Packaging-Tests um Dimensions-/Alpha-Kanal-Prüfung erweitert).

Live-Stand nach GitHub-Abfrage: **2** offene Issues – niedrigster Stand seit Beginn dieser Aufzeichnung.

### Ergebnis der Nachprüfung

- **Alt-Baseline stabil:** **N1/N2/N4/N5/N6/N7/N8**, **O1–O7** und alle seit
  **2026-06-25** abgeschlossenen Punkte bleiben erledigt.
- **#660/#659 sind jetzt verifiziert und geschlossen**, beide über eigene PRs (#664/#665), keine Auto-Close-Domino. **N9**/**O8** sind damit als abgeschlossen zu behandeln.
- **Kein Code-Blocker offen:** Die beiden verbleibenden Issues (#656, #245) sind laut eigener Akzeptanzkriterien-Liste rein extern/operativ (Secret setzen bzw. Billing/Quota) und explizit **kein Release-Blocker**.
- **Neu identifiziert (dieser Nachprüfung):** Für die anstehende Release-Vorbereitung ist der `[Unreleased]`-Abschnitt in `CHANGELOG.md` bereits gut gefüllt (16-Bit-Höhenpipeline #581, 3D-Reliefvorschau #582, CodeQL/Codex-Umbau #551), aber `pyproject.toml`/`LICENSES.md`/`de.bgremover.app.metainfo.xml` stehen weiterhin auf `2.6.0` – Versions-Bump und CHANGELOG-Umhängen sind vor dem nächsten Tag nötig. Die #666/#667-Assets (Icon/Screenshots) haben noch keine CHANGELOG-Zeile.

## Offene GitHub-Issues – Triage-Stand (2026-07-22)

| # | Titel | Relevanz | Komplexität | Empfohlenes Modell (Aufwand) | Nächster Schritt |
|---|-------|----------|--------------|-------------------------------|-------------------|
| [#656](https://github.com/NikolayDA/picture_helper/issues/656) | ANTHROPIC_API_KEY-Secret für Vision-Vorbewertung aktivieren | 🟡 Mittel (verbessert nur Evidenzqualität, kein Blocker laut Vertrag) | 🟢 Niedrig (rein operativ, kein Code) | – (kein Agent; Repo-Owner: Settings → Secrets) | Blocked (extern) – unabhängig erledigbar |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | OpenAI-Quota für manuellen Codex-Scan wiederherstellen | 🟢 Niedrig (blockiert nur einen optionalen manuellen Scan) | 🟢 Niedrig (rein operativ, kein Code) | – (kein Agent; Repo-Owner: Billing) | Blocked (extern) – Billing/Quota beim OpenAI-Platform-Projekt klären |

### Als Nächstes empfohlen

1. **#656** unabhängig erledigen, wenn echte Vision-Verdikte gewünscht sind – Qualitätsverbesserung, kein Blocker.
2. **#245** bleibt separat als rein externer Billing-/Quota-Tracker liegen; keine Aktion im Repository möglich oder nötig.
3. Der Abnahme-/3D-/Test-Audit-Strang (#646/#639/#595/#582/#659/#660) ist vollständig abgeschlossen und braucht keine weitere Aktion.
4. Für den nächsten Release: Versions-Bump (`pyproject.toml` + `CHANGELOG.md`/`LICENSES.md` + Übersetzungen + `de.bgremover.app.metainfo.xml`), `[Unreleased]` in einen neuen Versionsabschnitt umhängen, Kandidaten-Gate (`make pr-check`/`coverage`/`ui` + volle CI-Matrix) und einen frischen `release-abnahme.yml`-Dispatch gegen den tatsächlichen Ziel-Commit (der letzte Lauf, Run #4/Commit `9165c00`, liegt vor dem Icon-Wechsel #667).

## Vorige Runden

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
