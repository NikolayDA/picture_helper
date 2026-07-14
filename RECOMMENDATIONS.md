**Deutsch** · [English](docs/i18n/en/RECOMMENDATIONS.md) · [Español](docs/i18n/es/RECOMMENDATIONS.md) · [Français](docs/i18n/fr/RECOMMENDATIONS.md) · [Українська](docs/i18n/uk/RECOMMENDATIONS.md) · [简体中文](docs/i18n/zh/RECOMMENDATIONS.md)

# Codeanalyse & bewertete Empfehlungen: BgRemover

## Bewertungsskala

| Symbol | Priorität | Bedeutung |
|--------|-----------|-----------|
| 🔴 | Kritisch | Fehler, Abstürze oder Datenverlust |
| 🟠 | Hoch | Spürbarer Einfluss auf Zuverlässigkeit oder Wartbarkeit |
| 🟡 | Mittel | Sinnvolle Verbesserung für Qualität, Lesbarkeit oder Testbarkeit |
| 🟢 | Niedrig | Optionales Polishing oder Prozessverbesserung |

## Aktueller Stand (2026-07-14)

Die laufende Codeanalyse-Liste ist leer. Ruff, mypy und die lokale Testsuite
bleiben die maßgebliche Baseline vor neuen PRs. Release **v2.5.0** ist am
2026-07-11 geschnitten (PR #538); die Rollout-Welle **#435/#392/#426/#389**
ist geschlossen, ebenso **#299** (PR #539) mit N13-Follow-up **#541**
(PR #543), **#318** (PR #540) und Snapshot-Sync **#542**. Ein Repo-Audit vom
2026-07-12 hat **#549–#553** erfasst; **#552/#549/#553/#550** sind über
PR #557–#560 geschlossen. Epic **#563** („App-Update-Prüfung &
KI-Modell-Verwaltung", acht Sub-Issues **#564–#571**) ist am 2026-07-13
vollständig über PR #573/#574 umgesetzt und geschlossen worden (**N14**).
Live-Stand: **2** offene Issues – #245, #551.

### Erledigt seit dem letzten Review

- **Alt-Baseline stabil:** **N1/N2/N4/N5/N6/N7/N8** und **O2–O7** erledigt;
  Epics **#329/#344/#358/#384** (N9–N12) + Export-Fix **#363** gemergt/
  archiviert. Seit 2026-06-25 zusätzlich **#404/#406/#408** (PR #412)
  geschlossen.
- **Redesign & Release:** Redesign-Kern/Rail/Zoom/Karten-Inspector/Dark
  Mode/UI-Nacharbeit (**#413/#414/#455–#464/#474–#489/#499–#501/#503/#509/
  #510/#514–#517**, **#490**, **#433/#434**) über PR #412–#522
  abgeschlossen. Release-Welle **#435/#392/#426/#389** (v2.5.0),
  **#299/#541/#318/#542**, PR-Template **#552**, Snapshot-Sync **#549**,
  SessionStart-Fix **#553**, v2.3.0-Formalisierung **#550** – alles seit
  2026-07-12 geschlossen.
- **N14 — Epic #563 (App-Update & KI-Modell-Verwaltung) komplett
  abgeschlossen:** Update-Check-Kernlogik `app_update.py` (#564) und
  Modellstatus-Kernlogik `ai_model_status.py` (#568) – beide Qt-frei,
  strikt getypt, in der mypy-Strict-Liste (PR #573). Menü-/Dialog-
  Integration „Nach Updates suchen…"/„KI-Modell verwalten…" (#565/#569,
  PR #573). Optionaler automatischer Start-Check samt Einstellung
  (#566) und echte Verdrahtung des Modell-Downloads mit dem bestehenden
  Warmup-Mechanismus inkl. Mehrfach-Beobachter/kooperativem Abbruch
  (#570, PR #574, inkl. dreier Codex-Review-Fixes: on_success/on_finished
  getrennt, manueller Check hängt sich an einen laufenden Start-Check an,
  Race-Schutz beim Anhängen). Doku-Abschluss (README/CLAUDE.md/CHANGELOG/
  RESOURCES/INSTALL_\*, alle sechs Sprachen) über #567/#571.

### Noch offen

- **O8 🟢 — Prototyp-Ungenauigkeit:** Höhen-Werkzeuge bleiben im Mockup nach
  Erzeugung gesperrt; betrifft nur die Simulation, nicht die echte App (#347).

## Offene GitHub-Issues – Triage-Stand (2026-07-14)

Live-Stand: **2** offene Issues – beide bestehende CI-/Security-Issues,
unverändert gegenüber der letzten Runde (Epic #563 mit allen acht
Sub-Issues ist zwischenzeitlich komplett geschlossen worden).

### Sinnvolle Bündelung

#245/#551 hängen zusammen (Codex-Scan: Account-Aktion vs.
Grundsatzentscheidung).

Bewertung: **Relevanz** = Roadmap-/Nutzerbedeutung, **Komplexität** =
Umsetzungsaufwand, **Modell/Aufwand** = empfohlenes Claude-Modell +
Reasoning-Effort.

| # | Titel | Relevanz | Komplexität | Modell/Aufwand | Empfohlener nächster Schritt |
|---|-------|----------|-------------|-----------------|------------------------------|
| [#551](https://github.com/NikolayDA/picture_helper/issues/551) | Grundsatzentscheidung Codex Security Scan (reaktivieren/zurückbauen/ersetzen) | 🟡 Mittel | 🟡 Mittel | Sonnet 5 · mittel | **Needs refinement** – Entscheidung zwischen drei Optionen; Empfehlung: Option 2 (Zurückbauen/Deaktivieren) angesichts wochenlanger externer Blockade und Redundanz zu pip-audit/license/CI. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan „Quota exceeded" | 🟡 Mittel | 🟢 Niedrig | – (kein Code-Task) | **Blockiert (extern)** – OpenAI-Billing/Quota-Wiederherstellung ist eine Account-Aktion, kein PR. |

### Als Nächstes empfohlen

1. **#551** — Entscheidung zur Scan-Strategie einholen (an #245 gekoppelt),
   dann Workflow anpassen.
2. **#245** — bleibt extern blockiert; erst nach Wiederherstellung der
   OpenAI-Quota manuell verifizieren.

*Drift-Hinweis:* Die Anzahl offener Issues vor jeder künftigen
Aktualisierung erneut live abfragen statt fortzuschreiben (#542 → #549
zeigten dasselbe Off-by-one).

## Vorige Runden

- **2026-07-13 (Epic-Abschluss)** — Epic **#563** komplett abgeschlossen:
  alle acht Sub-Issues (**#564–#571**) über PR #573 (#564/#565/#568/#569)
  und PR #574 (#566/#570 + Doku-Abschluss #567/#571) geschlossen. Snapshot
  auf 2 (#245, #551) reduziert.
- **2026-07-13 (Issue-Audit)** — Epic **#563** + acht Sub-Issues
  (**#564–#571**) erfasst; alle 11 offenen Issues neu bewertet,
  Owner-Kommentare berücksichtigt. Kein Issue geschlossen. Empfehlung:
  #564/#568 zuerst. Snapshot auf 11.
- **2026-07-12** — v2.3.0-Formalisierung (**#550**), SessionStart-Hook-Fix
  (**#553**), Snapshot-Sync (**#549**, PR-Template **#552** via PR #557),
  Issue-Audit (**#542** geschlossen, #549–#553 erfasst) und Release
  **v2.5.0** (Rollout-Welle #435/#392/#426/#389, #299/#541/#318) – Snapshot
  zwischenzeitlich auf 2 (#245, #551) reduziert.
- **2026-07-11** — Epic #425 komplett abgeschlossen (#430 PR #526,
  Laufzeit-i18n ES/FR/UK/ZH vollständig, O1 erledigt; #431/#432 PR #529;
  finaler Nachzug #530/#531 PR #533/#535).
- **2026-07-05–10** — #509/#510/#514–#517 (PR #520–#522), #490,
  Dark-Mode-/Rail-Icon-Welle, Karten-Inspector (#413/#414), #499–#501/#503,
  Icon-/Statuszeilen-Feinschliff.
- **2026-06-29** — #404/#406/#408 (PR #412), Redesign-Welle eröffnet.
- **v2.2, „admiring-mayer" (#1–#15)** — externe Liste, erledigt oder bei
  Fehlalarm verworfen.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
