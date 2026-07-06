**Deutsch** · [English](docs/i18n/en/RECOMMENDATIONS.md) · [Español](docs/i18n/es/RECOMMENDATIONS.md) · [Français](docs/i18n/fr/RECOMMENDATIONS.md) · [Українська](docs/i18n/uk/RECOMMENDATIONS.md) · [简体中文](docs/i18n/zh/RECOMMENDATIONS.md)

# Codeanalyse & bewertete Empfehlungen: BgRemover

## Bewertungsskala

| Symbol | Priorität | Bedeutung |
|--------|-----------|-----------|
| 🔴 | Kritisch | Fehler, Abstürze oder Datenverlust |
| 🟠 | Hoch | Spürbarer Einfluss auf Zuverlässigkeit oder Wartbarkeit |
| 🟡 | Mittel | Sinnvolle Verbesserung für Qualität, Lesbarkeit oder Testbarkeit |
| 🟢 | Niedrig | Optionales Polishing oder Prozessverbesserung |

## Aktueller Stand (2026-07-06)

Die laufende Codeanalyse-Liste ist leer. Ruff, mypy und die lokale Testsuite
bleiben die maßgebliche Baseline vor neuen PRs. Seit dem Snapshot vom
2026-07-05 ist der Recommendations-Snapshot-Fix **#490** geschlossen. Die
heutige Verifikation der Redesign-Epics (#413/#418/#424/#455/#463/#474/#483)
brachte drei neue, klar umrissene Befunde: **#499** (helles Schema noch nicht
1:1 am Prototyp), **#500** (Screenshot-Skript kaputt, blockiert #432) und
**#501** (totes Widget `TopIconTab*`). GitHub zeigt aktuell **14** offene
Issues.

### Erledigt seit dem letzten Review

- **Alt-Baseline stabil:** **N1/N2/N4/N5/N6/N7/N8** und **O2–O7** bleiben
  erledigt; Epics **#329/#344/#358/#384** (N9–N12) samt Export-Fix **#363**
  sind gemergt und archiviert.
- **Seit 2026-06-25 geschlossen:** **#404/#406/#408** (PR #412) – Vorschau-/
  Dead-Code-/Audit-Befunde erledigt.
- **Redesign-Kern, Rail/Zoom, Karten-Inspector, Dark Mode:** **#413/#414/
  #455–#464/#474–#489** sind über PR #412/#423/#466/#467/#473/#482/#489
  abgeschlossen (Schrittleiste, Design-Tokens, Dark-Mode-Angleichung,
  Vektor-Icons).
- **#490 und #433/#434 abgeschlossen:** Snapshot-Drift behoben; Smoke-Tests/
  Regression über PR #423 gelandet – Epic **#426** hängt nur noch an **#435**.

### Neu seit dem letzten Review

- **#499 🟡:** `theme.LIGHT` weicht in mehreren Tokens vom Prototyp ab
  (Muster wie #474–#480, Test in `tests/test_theme.py` vorhanden).
- **#500 🟠:** `scripts/generate_app_screenshots.py` sucht ein nicht mehr
  existierendes `QTabWidget`; blockiert **#432**.
- **#501 🟢:** `TopIconTabBar`/`TopIconTabWidget` in `widgets.py` sind seit
  der Stepper-Umstellung tote Widgets.

### Noch offen

- **O1 🟠 — Weitere Runtime-Sprachen.** DE/EN sind umschaltbar; es/fr/uk/zh
  fehlen noch als Runtime-Locales (deckt sich mit **#430**).
- **O8 🟢 — Prototyp-Ungenauigkeit:** Höhen-Werkzeuge bleiben im Mockup nach
  Erzeugung gesperrt; betrifft nur die Simulation, nicht die echte App (#347).

## Offene GitHub-Issues – Triage-Stand (2026-07-06)

Stand 2026-07-06 zeigt GitHub **14** offene Issues: drei Redesign-
Nacharbeiten (**#499/#500/#501**), i18n/Doku (**#425/#430/#431/#432**),
Rollout/Release (**#426/#435/#392/#389**) und Backlog/Externe Punkte
(**#299/#318/#245**).

### Sinnvolle Bündelung

- **Redesign-Nacharbeit:** #499/#500/#501 sind unabhängig und risikoarm;
  **#500** zuerst, weil es **#432** entsperrt.
- **i18n/Doku:** #430 entsperrt die Paritätstests; #431/#432 folgen nach
  UI-Freeze **und** #500.
- **Rollout/Release:** #426 hängt nur an #435; mit #392 koordinieren, dann
  #426/#389 schließen.
- **Backlog:** #299 nach dem Release; #318 erst schärfen; #245 extern
  blockiert.

Bewertung: **Relevanz** = Bedeutung für Roadmap/Nutzer, **Komplexität** =
geschätzter Umsetzungsaufwand.

| # | Titel | Relevanz | Komplexität | Empfohlener nächster Schritt |
|---|-------|----------|-------------|------------------------------|
| [#500](https://github.com/NikolayDA/picture_helper/issues/500) | Screenshot-Skript nach Redesign kaputt (blockiert #432) | 🟠 Hoch | 🟢 Niedrig | **Ready for PR** – Navigation auf `Stepper` umstellen. |
| [#499](https://github.com/NikolayDA/picture_helper/issues/499) | Helles Schema 1:1 an Prototyp A angleichen | 🟡 Mittel | 🟢 Niedrig | **Ready for PR** – gleiches Muster wie #474–#480. |
| [#501](https://github.com/NikolayDA/picture_helper/issues/501) | Verwaiste `TopIconTab*`-Widgets entfernen | 🟢 Niedrig | 🟢 Niedrig | **Ready for PR** – reines Aufräumen, 3 Dateien. |
| [#425](https://github.com/NikolayDA/picture_helper/issues/425) | EPIC: Internationalisierung & Dokumentation | 🟠 Hoch | 🟡 Mittel | **In Arbeit** – #430/#431/#432 offen. |
| [#430](https://github.com/NikolayDA/picture_helper/issues/430) | Neue UI-Strings (Schritte/Karten/Navigation) | 🟠 Hoch | 🟡 Mittel | **Ready for PR** – ES/FR/UK/ZH; DE/EN via PR #423 da. |
| [#431](https://github.com/NikolayDA/picture_helper/issues/431) | ANLEITUNG & README auf geführten Workflow | 🟡 Mittel | 🟡 Mittel | **Nach UI-Freeze** – 6-Sprachen-Spiegel, Link-Tests. |
| [#432](https://github.com/NikolayDA/picture_helper/issues/432) | App-Screenshots des Redesigns neu erstellen | 🟢 Niedrig | 🟢 Niedrig | **Blockiert** – braucht UI-Freeze **und** #500. |
| [#426](https://github.com/NikolayDA/picture_helper/issues/426) | EPIC: Qualitätssicherung & Rollout | 🟠 Hoch | 🟢 Niedrig | **Fast fertig** – nur #435 bleibt offen. |
| [#435](https://github.com/NikolayDA/picture_helper/issues/435) | CHANGELOG & Versionsanhebung für das Redesign | 🟡 Mittel | 🟢 Niedrig | **Mit #392 abstimmen** – Release-Sequenz klären. |
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | Release v2.5.0 schneiden | 🟠 Hoch | 🟡 Mittel | **Startbereit** – Sequenz mit Redesign entscheiden. |
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | EPIC: Nutzer-Doku aktualisieren & Release | 🟠 Hoch | 🟢 Niedrig | **Nach #392 schließen** – nur Release offen. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test-Hygiene: schwache Assertions/Redundanzen | 🟢 Niedrig | 🟢 Niedrig | **Nach der Release** – höchste Wirkung zuerst. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Job-Level-Permission-Overrides im Reusable-WF | 🟢 Niedrig | 🟡 Mittel | **Needs refinement** – GitHub-Semantik belegen. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan „Quota exceeded" | 🟡 Mittel | 🟢 Niedrig | **Blockiert (extern)** – OpenAI-Billing/Quota. |

### Als Nächstes empfohlen (PR-Reihenfolge)

1. **#500** zuerst – entsperrt **#432**; **#499**/**#501** im selben oder
   einem direkt folgenden PR.
2. **#430** vorziehen – entsperrt die i18n-Parität; danach **#431**/**#432**.
3. **Release:** **#435** + **#392** koordiniert fahren, dann **#426**/**#389**
   schließen.
4. **#299** nach der Release; **#318** nur erforschen; **#245** extern
   blockiert.

## Vorige Runden

- **2026-07-05** — #490 (Snapshot-Drift) in Bearbeitung, Dark-Mode-/Rail-
  Icon-Welle und Karten-Inspector (#413/#414) abgeschlossen.
- **2026-06-29** — #404/#406/#408 abgeschlossen (PR #412), Redesign-Welle eröffnet.
- **v2.2, „admiring-mayer" (#1–#15)** — externe Liste, erledigt oder bei Fehlalarm verworfen.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
