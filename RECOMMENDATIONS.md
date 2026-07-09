**Deutsch** · [English](docs/i18n/en/RECOMMENDATIONS.md) · [Español](docs/i18n/es/RECOMMENDATIONS.md) · [Français](docs/i18n/fr/RECOMMENDATIONS.md) · [Українська](docs/i18n/uk/RECOMMENDATIONS.md) · [简体中文](docs/i18n/zh/RECOMMENDATIONS.md)

# Codeanalyse & bewertete Empfehlungen: BgRemover

## Bewertungsskala

| Symbol | Priorität | Bedeutung |
|--------|-----------|-----------|
| 🔴 | Kritisch | Fehler, Abstürze oder Datenverlust |
| 🟠 | Hoch | Spürbarer Einfluss auf Zuverlässigkeit oder Wartbarkeit |
| 🟡 | Mittel | Sinnvolle Verbesserung für Qualität, Lesbarkeit oder Testbarkeit |
| 🟢 | Niedrig | Optionales Polishing oder Prozessverbesserung |

## Aktueller Stand (2026-07-09)

Die laufende Codeanalyse-Liste ist leer. Ruff, mypy und die lokale Testsuite
bleiben die maßgebliche Baseline vor neuen PRs. Seit dem Snapshot vom
2026-07-06 sind alle drei Redesign-Nacharbeiten **#499/#500/#501** (PR #504)
sowie der Tote-Code-Befund **#503** (PR #506; #505 war ein versehentlicher
Leer-Diff-Merge, der Inhalt kam über #506) geschlossen; dazu der Icon-/
Statuszeilen-Feinschliff **PR #507/#508**. Neu sind der UI-Bug **#509**
(Werkzeug-Cursor ignoriert Canvas-Zoom) und **#510** (dieser
Snapshot-Refresh). GitHub zeigt aktuell **13** offene Issues.

### Erledigt seit dem letzten Review

- **Alt-Baseline stabil:** **N1/N2/N4/N5/N6/N7/N8** und **O2–O7** bleiben
  erledigt; Epics **#329/#344/#358/#384** (N9–N12) samt Export-Fix **#363**
  sind gemergt und archiviert.
- **Seit 2026-06-25 geschlossen:** **#404/#406/#408** (PR #412) – Vorschau-/
  Dead-Code-/Audit-Befunde erledigt.
- **Redesign-Kern, Rail/Zoom, Karten-Inspector, Dark Mode:** **#413/#414/
  #455–#464/#474–#489** sind über PR #412/#423/#466/#467/#473/#482/#489
  abgeschlossen; **#490** und **#433/#434** ebenso (Epic **#426** hängt nur
  noch an **#435**).
- **Seit 2026-07-06 geschlossen:** **#499/#500/#501** (PR #504 – helles
  Schema am Prototyp, Screenshot-Generator repariert, tote Widgets entfernt;
  der #500-Blocker vor **#432** ist damit gefallen) und **#503** (PR #506 –
  `CanvasHistory`/`_make_panel_btn`/tote Theme-Konstanten entfernt).

### Neu seit dem letzten Review

- **#509 🟠:** Pinsel-/Radiergummi-Cursor skaliert nicht mit dem Canvas-Zoom
  – angezeigte Werkzeuggröße ≠ tatsächliche Wirkfläche (betrifft auch die
  Höhen-Pinsel; Ursache in `set_tool`/`set_brush_size` präzise lokalisiert).
- **#510 🟢:** Triage-Snapshot war vom 30 Minuten später gemergten PR #504
  überholt – mit diesem Update erledigt.

### Noch offen

- **O1 🟠 — Weitere Runtime-Sprachen.** DE/EN sind umschaltbar; es/fr/uk/zh
  fehlen noch als Runtime-Locales (deckt sich mit **#430**).
- **O8 🟢 — Prototyp-Ungenauigkeit:** Höhen-Werkzeuge bleiben im Mockup nach
  Erzeugung gesperrt; betrifft nur die Simulation, nicht die echte App (#347).

## Offene GitHub-Issues – Triage-Stand (2026-07-09)

Stand 2026-07-09 zeigt GitHub **13** offene Issues: UI-Bug (**#509**),
dieser Doku-Snapshot (**#510**), i18n/Doku (**#425/#430/#431/#432**),
Rollout/Release (**#426/#435/#392/#389**) und Backlog/Externe Punkte
(**#299/#318/#245**).

### Sinnvolle Bündelung

- **UI-Bug:** #509 ist präzise lokalisiert (Cursor wird bei `zoomChanged`
  nie neu berechnet) und der einzige offene Code-Befund – guter nächster PR.
- **i18n/Doku:** #430 entsperrt die Paritätstests; #431/#432 folgen nach
  UI-Freeze (der #500-Blocker vor #432 ist mit PR #504 gefallen).
- **Rollout/Release:** #426 hängt nur an #435; mit #392 koordinieren, dann
  #426/#389 schließen.
- **Backlog:** #299 nach dem Release; #318 erst schärfen; #245 extern
  blockiert.

Bewertung: **Relevanz** = Bedeutung für Roadmap/Nutzer, **Komplexität** =
geschätzter Umsetzungsaufwand.

| # | Titel | Relevanz | Komplexität | Empfohlener nächster Schritt |
|---|-------|----------|-------------|------------------------------|
| [#509](https://github.com/NikolayDA/picture_helper/issues/509) | Pinsel-/Radiergummi-Cursor ignoriert Canvas-Zoom | 🟠 Hoch | 🟡 Mittel | **Ready for PR** – Cursor bei `zoomChanged`/Größenwahl mitskalieren. |
| [#510](https://github.com/NikolayDA/picture_helper/issues/510) | Triage-Snapshot veraltet (Stand 2026-07-06) | 🟢 Niedrig | 🟢 Niedrig | **In Arbeit** – dieser Snapshot erledigt es. |
| [#425](https://github.com/NikolayDA/picture_helper/issues/425) | EPIC: Internationalisierung & Dokumentation | 🟠 Hoch | 🟡 Mittel | **In Arbeit** – #430/#431/#432 offen. |
| [#430](https://github.com/NikolayDA/picture_helper/issues/430) | Neue UI-Strings (Schritte/Karten/Navigation) | 🟠 Hoch | 🟡 Mittel | **Ready for PR** – ES/FR/UK/ZH; DE/EN via PR #423 da. |
| [#431](https://github.com/NikolayDA/picture_helper/issues/431) | ANLEITUNG & README auf geführten Workflow | 🟡 Mittel | 🟡 Mittel | **Nach UI-Freeze** – 6-Sprachen-Spiegel, Link-Tests. |
| [#432](https://github.com/NikolayDA/picture_helper/issues/432) | App-Screenshots des Redesigns neu erstellen | 🟢 Niedrig | 🟢 Niedrig | **Nach UI-Freeze** – #500-Blocker gefallen (PR #504). |
| [#426](https://github.com/NikolayDA/picture_helper/issues/426) | EPIC: Qualitätssicherung & Rollout | 🟠 Hoch | 🟢 Niedrig | **Fast fertig** – nur #435 bleibt offen. |
| [#435](https://github.com/NikolayDA/picture_helper/issues/435) | CHANGELOG & Versionsanhebung für das Redesign | 🟡 Mittel | 🟢 Niedrig | **Mit #392 abstimmen** – Release-Sequenz klären. |
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | Release v2.5.0 schneiden | 🟠 Hoch | 🟡 Mittel | **Startbereit** – Sequenz mit Redesign entscheiden. |
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | EPIC: Nutzer-Doku aktualisieren & Release | 🟠 Hoch | 🟢 Niedrig | **Nach #392 schließen** – nur Release offen. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test-Hygiene: schwache Assertions/Redundanzen | 🟢 Niedrig | 🟢 Niedrig | **Nach der Release** – höchste Wirkung zuerst. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Job-Level-Permission-Overrides im Reusable-WF | 🟢 Niedrig | 🟡 Mittel | **Needs refinement** – GitHub-Semantik belegen. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan „Quota exceeded" | 🟡 Mittel | 🟢 Niedrig | **Blockiert (extern)** – OpenAI-Billing/Quota. |

### Als Nächstes empfohlen (PR-Reihenfolge)

1. **#509** zuerst – einziger offener Code-Bug, Ursache bereits lokalisiert.
2. **#430** vorziehen – entsperrt die i18n-Parität; danach **#431**/**#432**.
3. **Release:** **#435** + **#392** koordiniert fahren, dann **#426**/**#389**
   schließen.
4. **#299** nach der Release; **#318** nur erforschen; **#245** extern
   blockiert.

## Vorige Runden

- **2026-07-06** — #499/#500/#501 (PR #504) und #503 (PR #506) abgeschlossen;
  Icon-/Statuszeilen-Feinschliff über PR #507/#508.
- **2026-07-05** — #490 (Snapshot-Drift) in Bearbeitung, Dark-Mode-/Rail-
  Icon-Welle und Karten-Inspector (#413/#414) abgeschlossen.
- **2026-06-29** — #404/#406/#408 abgeschlossen (PR #412), Redesign-Welle eröffnet.
- **v2.2, „admiring-mayer" (#1–#15)** — externe Liste, erledigt oder bei Fehlalarm verworfen.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
