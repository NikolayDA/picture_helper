**Deutsch** · [English](docs/i18n/en/RECOMMENDATIONS.md) · [Español](docs/i18n/es/RECOMMENDATIONS.md) · [Français](docs/i18n/fr/RECOMMENDATIONS.md) · [Українська](docs/i18n/uk/RECOMMENDATIONS.md) · [简体中文](docs/i18n/zh/RECOMMENDATIONS.md)

# Codeanalyse & bewertete Empfehlungen: BgRemover

## Bewertungsskala

| Symbol | Priorität | Bedeutung |
|--------|-----------|-----------|
| 🔴 | Kritisch | Fehler, Abstürze oder Datenverlust |
| 🟠 | Hoch | Spürbarer Einfluss auf Zuverlässigkeit oder Wartbarkeit |
| 🟡 | Mittel | Sinnvolle Verbesserung für Qualität, Lesbarkeit oder Testbarkeit |
| 🟢 | Niedrig | Optionales Polishing oder Prozessverbesserung |

## Aktueller Stand (2026-07-12)

Die laufende Codeanalyse-Liste ist leer. Ruff, mypy und die lokale Testsuite
bleiben die maßgebliche Baseline vor neuen PRs. Release **v2.5.0** ist am
2026-07-11 geschnitten (CHANGELOG kuratiert, Version angehoben – PR #538). Die
gesamte Rollout-/Release-Welle ist damit geschlossen: **#435** (PR #538),
**#392**, **#426** und **#389**. Ebenfalls geschlossen: **#299** (PR #539) mit
dem separat nachgezogenen N13-Testhygiene-Follow-up **#541** (PR #543), sowie
**#318** (PR #540) und die Recommendations-Snapshot-Synchronisation **#542**.
Ein Repo-Audit vom 2026-07-12 hat fünf neue Befunde erfasst (**#549–#553**);
**#552**, **#549**, **#553** und **#550** sind inzwischen geschlossen
(PR #557, #558, #559 und #560). Live-Stand (erneut abgefragt): **2** offene
Issues – **#245** und **#551**.

### Erledigt seit dem letzten Review

- **Alt-Baseline stabil:** **N1/N2/N4/N5/N6/N7/N8** und **O2–O7** bleiben
  erledigt; Epics **#329/#344/#358/#384** (N9–N12) samt Export-Fix **#363**
  sind gemergt und archiviert.
- **Seit 2026-06-25 geschlossen:** **#404/#406/#408** (PR #412) – Vorschau-/
  Dead-Code-/Audit-Befunde erledigt.
- **Redesign-Kern, Rail/Zoom, Karten-Inspector, Dark Mode, UI-Nacharbeit:**
  **#413/#414/#455–#464/#474–#489/#499–#501/#503/#509/#510/#514–#517** sind
  über PR #412/#423/#466/#467/#473/#482/#489/#504/#506/#512/#513/#518/#519
  sowie PR #520/#521/#522 abgeschlossen; **#490** und **#433/#434** ebenso.
- **Seit 2026-07-12 geschlossen:** Release-Welle **#435/#392/#426/#389**
  (v2.5.0, PR #538) sowie **#299** (PR #539), das Testhygiene-Follow-up
  **#541** (PR #543), **#318** (PR #540), die Recommendations-Snapshot-
  Synchronisation **#542**, das PR-Template **#552** (PR #557), der
  Snapshot-Sync **#549**, der SessionStart-Hook-Fix **#553** und die
  v2.3.0-Tag-/Release-Formalisierung **#550**. Damit sind alle Redesign-/
  Release-/Backlog-Punkte des letzten Snapshots abgearbeitet.

### Noch offen

- **O8 🟢 — Prototyp-Ungenauigkeit:** Höhen-Werkzeuge bleiben im Mockup nach
  Erzeugung gesperrt; betrifft nur die Simulation, nicht die echte App (#347).

## Offene GitHub-Issues – Triage-Stand (2026-07-12)

Live-Stand direkt vor dieser Bearbeitung: **#552**, **#549**, **#553** und
**#550** sind geschlossen. Es verbleiben **2** offene Issues: **#245**
(Quota-/Billing-Blocker) und **#551** (Grundsatzentscheidung Codex Security
Scan).

### Sinnvolle Bündelung

#245 und #551 hängen inhaltlich zusammen (Codex-Scan): #245 ist eine reine
Account-Aktion, #551 braucht dagegen eine eigene Grundsatzentscheidung
(reaktivieren/zurückbauen/ersetzen).

Bewertung: **Relevanz** = Bedeutung für Roadmap/Nutzer, **Komplexität** =
geschätzter Umsetzungsaufwand, **Modell/Aufwand** = empfohlenes
Claude-Modell und Reasoning-Effort für die Umsetzung durch Claude Code.

| # | Titel | Relevanz | Komplexität | Modell/Aufwand | Empfohlener nächster Schritt |
|---|-------|----------|-------------|-----------------|------------------------------|
| [#551](https://github.com/NikolayDA/picture_helper/issues/551) | Grundsatzentscheidung Codex Security Scan (reaktivieren/zurückbauen/ersetzen) | 🟡 Mittel | 🟡 Mittel | Sonnet 5 · mittel | **Needs refinement** – erfordert eine bewusste Entscheidung zwischen drei Optionen; Empfehlung: Option 2 (Zurückbauen/Deaktivieren) angesichts wochenlanger externer Blockade und Redundanz zu pip-audit/license/CI. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan „Quota exceeded" | 🟡 Mittel | 🟢 Niedrig | – (kein Code-Task) | **Blockiert (extern)** – OpenAI-Billing/Quota-Wiederherstellung ist eine Account-Aktion, kein PR. |

### Als Nächstes empfohlen (PR-Reihenfolge)

1. **#551** — Entscheidung zur Scan-Strategie einholen (an #245 gekoppelt),
   dann Workflow anpassen.
2. **#245** — bleibt extern blockiert; erst nach Wiederherstellung der
   OpenAI-Quota manuell verifizieren.

*Drift-Hinweis:* Die Anzahl offener Issues vor jeder künftigen
Aktualisierung erneut live abfragen statt fortzuschreiben (#542 → #549
zeigten dasselbe Off-by-one).

## Vorige Runden

- **2026-07-12 (#550)** — v2.3.0-Tag und GitHub-Release nachträglich
  formalisiert; CHANGELOG-Footer in allen sechs Sprachen nutzt jetzt
  `v2.3.0` statt roher Commit-SHAs. Open-Issue-Snapshot auf 2 reduziert
  (#245, #551).
- **2026-07-12 (#553)** — SessionStart-Hook-Fix: fehlgeschlagenes
  `pip install --upgrade pip` (Debian-Paket ohne RECORD-Datei) brach den
  Hook unter `set -e` vor dem eigentlichen `.[test]`-Install ab; behoben mit
  `--ignore-installed`, plus idempotente Vorprüfung und Fehler-Trap.
  Open-Issue-Snapshot auf 3 reduziert (#245, #550, #551).
- **2026-07-12 (Snapshot-Sync #549)** — #552 (PR-Template) über PR #557
  geschlossen; #549 (Recommendations-Sync) ebenfalls abgeschlossen.
- **2026-07-12 (Issue-Audit)** — #542 geschlossen; Repo-Audit hat fünf neue
  Issues erfasst (#549–#553); Open-Issue-Snapshot auf 6 aktualisiert
  (#245 + #549–#553).
- **2026-07-12** — Release **v2.5.0** geschnitten; Rollout-Welle
  #435/#392/#426/#389 geschlossen; #299 (PR #539), N13-Follow-up #541
  (PR #543) und #318 (PR #540) geschlossen; Open-Issue-Snapshot auf #245 +
  #542 reduziert.
- **2026-07-11 (finaler Nachzug)** — #425 formal geschlossen; #530/#531 über
  PR #533/#535 geschlossen; Open-Issue-Snapshot auf 7 verbleibende Issues
  aktualisiert.
- **2026-07-11 (2. Triage)** — #431/#432 geschlossen (PR #529); Epic #425
  vollständig erledigt. Neue Issues #530/#531 erfasst.
- **2026-07-11** — #430 geschlossen (PR #526, Laufzeit-i18n ES/FR/UK/ZH
  vollständig, O1 erledigt); Epic #425 hing danach nur noch an #431/#432.
- **2026-07-10** — #509/#510 geschlossen, #514–#517 erledigt, rechte-Spalte-
  Nacharbeit über PR #520/#521/#522 abgeschlossen.
- **2026-07-05/06** — #490, Dark-Mode-/Rail-Icon-Welle, Karten-Inspector
  (#413/#414), #499–#501/#503 (PR #504/#506) sowie Icon-/Statuszeilen-
  Feinschliff (PR #507/#508) abgeschlossen.
- **2026-06-29** — #404/#406/#408 abgeschlossen (PR #412), Redesign-Welle eröffnet.
- **v2.2, „admiring-mayer" (#1–#15)** — externe Liste, erledigt oder bei Fehlalarm verworfen.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
