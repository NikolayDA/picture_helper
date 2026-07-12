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
dem separat nachgezogenen N13-Testhygiene-Follow-up **#541** (PR #543) sowie
**#318** (PR #540). GitHub zeigt aktuell nur noch **2** offene Issues.

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
  **#541** (PR #543) und **#318** (PR #540). Damit sind alle Redesign-/
  Release-/Backlog-Punkte des letzten Snapshots abgearbeitet.

### Noch offen

- **O8 🟢 — Prototyp-Ungenauigkeit:** Höhen-Werkzeuge bleiben im Mockup nach
  Erzeugung gesperrt; betrifft nur die Simulation, nicht die echte App (#347).

## Offene GitHub-Issues – Triage-Stand (2026-07-12)

Stand 2026-07-12 zeigt GitHub nur noch **2** offene Issues: den externen
Quota-/Billing-Blocker **#245** und diese Doku-Synchronisation **#542**.

### Sinnvolle Bündelung

- **Extern blockiert:** #245 hängt an der OpenAI-Billing/Quota – eine
  Account-Aktion, kein Repo-PR.
- **Doku:** #542 gleicht die sechs Recommendations-Spiegel an den Live-Stand
  an und wird durch den zugehörigen PR erledigt.

Bewertung: **Relevanz** = Bedeutung für Roadmap/Nutzer, **Komplexität** =
geschätzter Umsetzungsaufwand, **Modell/Aufwand** = empfohlenes
Claude-Modell und Reasoning-Effort für die Umsetzung durch Claude Code.

| # | Titel | Relevanz | Komplexität | Modell/Aufwand | Empfohlener nächster Schritt |
|---|-------|----------|-------------|-----------------|------------------------------|
| [#542](https://github.com/NikolayDA/picture_helper/issues/542) | Recommendations-Snapshot nach v2.5.0 aktualisieren | 🟢 Niedrig | 🟢 Niedrig | Sonnet 5 · niedrig | **In Arbeit** – dieser PR gleicht alle sechs Spiegel struktursynchron an den Live-Stand an. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan „Quota exceeded" | 🟡 Mittel | 🟢 Niedrig | – (kein Code-Task) | **Blockiert (extern)** – OpenAI-Billing/Quota-Wiederherstellung ist eine Account-Aktion, kein PR. |

### Als Nächstes empfohlen (PR-Reihenfolge)

1. **#542** mit diesem PR abschließen (struktursynchroner Snapshot-Sync über
   alle sechs Spiegel).
2. **#245** bleibt extern blockiert – kein Repo-PR möglich; erst nach
   Wiederherstellung der OpenAI-Quota manuell verifizieren.

## Vorige Runden

- **2026-07-12** — Release **v2.5.0** geschnitten; Rollout-Welle
  #435/#392/#426/#389 geschlossen; #299 (PR #539), N13-Follow-up #541
  (PR #543) und #318 (PR #540) geschlossen; Open-Issue-Snapshot auf #245 +
  #542 reduziert.
- **2026-07-11 (finaler Nachzug)** — #425 formal geschlossen; #530/#531 über
  PR #533/#535 geschlossen; Open-Issue-Snapshot auf 7 verbleibende Issues
  aktualisiert.
- **2026-07-11 (2. Triage)** — #431/#432 geschlossen (PR #529, ANLEITUNG/
  README/Screenshots auf den 6-Schritte-Workflow); Epic #425 vollständig
  erledigt. Neue Issues #530/#531 aus einem KI-Warmup-Support-Fall erfasst.
- **2026-07-11** — #430 geschlossen (PR #526, Laufzeit-i18n ES/FR/UK/ZH
  vollständig, O1 erledigt); Epic #425 hing danach nur noch an #431/#432.
- **2026-07-10** — #509/#510 geschlossen, #514–#517 erledigt, rechte-Spalte-
  Nacharbeit über PR #520/#521/#522 abgeschlossen; Benchmark-Baseline-Workflow
  auf PR statt Direkt-Push umgestellt.
- **2026-07-06** — #499/#500/#501 (PR #504) und #503 (PR #506) abgeschlossen;
  Icon-/Statuszeilen-Feinschliff über PR #507/#508.
- **2026-07-05** — #490 (Snapshot-Drift) in Bearbeitung, Dark-Mode-/Rail-
  Icon-Welle und Karten-Inspector (#413/#414) abgeschlossen.
- **2026-06-29** — #404/#406/#408 abgeschlossen (PR #412), Redesign-Welle eröffnet.
- **v2.2, „admiring-mayer" (#1–#15)** — externe Liste, erledigt oder bei Fehlalarm verworfen.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
