**Deutsch** · [English](docs/i18n/en/RECOMMENDATIONS.md) · [Español](docs/i18n/es/RECOMMENDATIONS.md) · [Français](docs/i18n/fr/RECOMMENDATIONS.md) · [Українська](docs/i18n/uk/RECOMMENDATIONS.md) · [简体中文](docs/i18n/zh/RECOMMENDATIONS.md)

# Codeanalyse & bewertete Empfehlungen: BgRemover

## Bewertungsskala

| Symbol | Priorität | Bedeutung |
|--------|-----------|-----------|
| 🔴 | Kritisch | Fehler, Abstürze oder Datenverlust |
| 🟠 | Hoch | Spürbarer Einfluss auf Zuverlässigkeit oder Wartbarkeit |
| 🟡 | Mittel | Sinnvolle Verbesserung für Qualität, Lesbarkeit oder Testbarkeit |
| 🟢 | Niedrig | Optionales Polishing oder Prozessverbesserung |

## Aktueller Stand (2026-07-03)

Die laufende Codeanalyse-Liste ist leer. Ruff, mypy und die lokale Testsuite
bleiben die maßgebliche Baseline vor neuen PRs. Neu in dieser Runde: die offene
GitHub-Triage ist nach den Rail-/Zoom-Follow-ups auf den aktuellen Stand
gebracht. Vor diesem PR zeigt GitHub 14 offene Issues; nach Abschluss von
**#461** bleiben 13 Roadmap-/Backlog-Issues.

### Erledigt seit dem letzten Review

- **Alt-Baseline stabil:** **N1/N2/N4/N5/N6/N7/N8** und **O2–O7** bleiben
  erledigt; die Epics **#329/#344/#358/#384** (N9–N12) samt Export-Fix **#363**
  sind gemergt, durch Tests/CI abgesichert und archiviert.
- **Seit dem Review 2026-06-25 geschlossen:** **#404**, **#406** und **#408**
  (PR #412) – die zuvor gelisteten Vorschau-/Dead-Code-/Audit-Befunde sind
  erledigt; `_derive_physical_size` existiert nicht mehr, und der Renderpfad
  degradiert bei Größen-Mismatch auf COLOR.
- **Redesign-Kern ausgeliefert:** Schrittleiste/`stepper.py`, Karten-Inspector,
  geführte Navigation, kontextuelle Werkzeuge und die Design-Tokens
  (`ACCENT`/`CARD_STYLE`) sind über PR #412/#423 gelandet (DE/EN-Strings,
  `tests/test_workflow.py`).
- **Rail-/Zoom-Welle abgeschlossen:** **#455/#456/#457/#458/#463/#464** sind über
  PR #466 gelandet, **#465** ist bewusst `not_planned`. Dieser Follow-up-PR
  schließt die drei nachträglichen #466-P2s (Zoom-Richtung, Viewport-Anker,
  Höhen-Dab-Preview) und aktualisiert **#461**.

### Noch offen

- **O1 🟠 — Weitere Runtime-Sprachen.** Deutsch und Englisch sind umschaltbar;
  es/fr/uk/zh sind noch keine Runtime-Locales. Deckt sich mit dem Redesign-Issue
  **#430** – dort key-für-key in `bgremover.i18n` ergänzen und mit Tests absichern.
- **O8 🟢 — Prototyp-Ungenauigkeit: Höhen-Werkzeuge nach Erzeugung gesperrt.**
  In `design/Prototyp A - Geführter Workflow.dc.html` setzt „Höhenkarte aus
  Bild erzeugen" nur `heightGen`, ohne die aktive Ebene auf Rolle `Höhe` zu
  schalten – `heightDisabled` bleibt an der vorherigen Rolle hängen (Review-
  Fund auf PR #460). Betrifft nur die Mockup-Simulation; die echte App
  aktiviert die neue HEIGHT-Ebene bereits automatisch (#347).

## Offene GitHub-Issues – Triage-Stand (2026-07-03)

Stand 2026-07-03 zeigt GitHub **14** offene Issues vor Merge dieses Follow-ups.
**#461** ist genau dieser Snapshot-Drift und wird durch den PR geschlossen. Für
die weitere Planung bleiben danach **13** offene Roadmap-/Backlog-Issues: die
rechte-Spalte-Politur (**#413/#414**), i18n/Doku (**#425/#430/#431/#432**),
Rollout/Release (**#426/#435/#392/#389**) und die unabhängigen Punkte
**#299/#318/#245**.

**Kommentar-Durchsicht:** Die drei nachträglichen P2-Kommentare auf PR #466 sind
als echte Restarbeit bestätigt und in diesem PR adressiert. Der P2 auf PR #460
bleibt als Mockup-only-Fund **O8** dokumentiert; die echte App aktiviert
HEIGHT-Ebenen bereits automatisch.

### Sinnvolle Bündelung

- **Fast fertiges Epic:** #413 hat nur noch #414 offen; dessen Tokens liegen
  schon in `theme.py` – Karten-Stil für das helle Schema ergänzen, dann schließen.
- **i18n/Doku (#425):** #430 (ES/FR/UK/ZH) entsperrt die Paritätstests; #431 (Doku)
  und #432 (Screenshots) folgen, sobald die UI optisch final ist.
- **Rollout/Release:** #426 bleibt nur noch über #435 offen; #435 mit #392
  koordinieren und danach #426/#389 schließen.
- **Backlog:** #299 nach dem Release angehen; #318 erst semantisch schärfen;
  #245 bleibt extern durch OpenAI-Billing/Quota blockiert.

Bewertung: **Relevanz** = Bedeutung für Roadmap/Nutzer, **Komplexität** =
geschätzter Umsetzungsaufwand.

| # | Titel | Relevanz | Komplexität | Empfohlener nächster Schritt |
|---|-------|----------|-------------|------------------------------|
| [#413](https://github.com/NikolayDA/picture_helper/issues/413) | EPIC: Karten-Inspector – rechte Spalte als Karten | 🟠 Hoch | 🟢 Niedrig | **Fast fertig** – nur #414 offen. |
| [#414](https://github.com/NikolayDA/picture_helper/issues/414) | Karten-Container & Akzent-Tokens zentralisieren | 🟡 Mittel | 🟢 Niedrig | **Ready for PR** – Tokens da; hellen Karten-Stil ergänzen. |
| [#425](https://github.com/NikolayDA/picture_helper/issues/425) | EPIC: Internationalisierung & Dokumentation | 🟠 Hoch | 🟡 Mittel | **In Arbeit** – #430/#431/#432 offen. |
| [#430](https://github.com/NikolayDA/picture_helper/issues/430) | Neue UI-Strings (Schritte/Karten/Navigation) | 🟠 Hoch | 🟡 Mittel | **Ready for PR** – ES/FR/UK/ZH; DE/EN via PR #423 da. |
| [#431](https://github.com/NikolayDA/picture_helper/issues/431) | ANLEITUNG & README auf geführten Workflow | 🟡 Mittel | 🟡 Mittel | **Nach UI-Freeze** – 6-Sprachen-Spiegel, Link-Tests. |
| [#432](https://github.com/NikolayDA/picture_helper/issues/432) | App-Screenshots des Redesigns neu erstellen | 🟢 Niedrig | 🟢 Niedrig | **Blockiert** – erst wenn die UI optisch final ist. |
| [#426](https://github.com/NikolayDA/picture_helper/issues/426) | EPIC: Qualitätssicherung & Rollout | 🟠 Hoch | 🟢 Niedrig | **Fast fertig** – nur #435 bleibt offen. |
| [#435](https://github.com/NikolayDA/picture_helper/issues/435) | CHANGELOG & Versionsanhebung für das Redesign | 🟡 Mittel | 🟢 Niedrig | **Mit #392 abstimmen** – Release-Sequenz klären. |
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | Release v2.5.0 schneiden | 🟠 Hoch | 🟡 Mittel | **Startbereit** – Sequenz mit Redesign entscheiden. |
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | EPIC: Nutzer-Doku aktualisieren & Release | 🟠 Hoch | 🟢 Niedrig | **Nach #392 schließen** – nur Release offen. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test-Hygiene: schwache Assertions/Redundanzen | 🟢 Niedrig | 🟢 Niedrig | **Nach der Release** – höchste Wirkung zuerst. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Job-Level-Permission-Overrides im Reusable-WF | 🟢 Niedrig | 🟡 Mittel | **Needs refinement** – GitHub-Semantik belegen. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan „Quota exceeded" | 🟡 Mittel | 🟢 Niedrig | **Blockiert (extern)** – OpenAI-Billing/Quota. |
| [#461](https://github.com/NikolayDA/picture_helper/issues/461) | Triage-Snapshot nach Rail-Follow-ups aktualisieren | 🟡 Mittel | 🟢 Niedrig | **Durch diesen PR erledigt** – wird geschlossen. |

### Als Nächstes empfohlen (PR-Reihenfolge)

1. **#414** (heller Karten-Stil) abschließen und danach Epic **#413** schließen.
2. **#430** (UI-Strings ES/FR/UK/ZH) vorziehen – entsperrt die i18n-Parität;
   danach **#431**/**#432**, sobald die UI final ist.
3. **Release:** **#435** + **#392** koordiniert fahren, dann Epics **#426** und
   **#389** schließen.
4. **#299** nach der Release; **#318** nur erforschen (Needs refinement); **#245**
   extern blockiert.

## Vorige Runden

- **2026-06-29-Triage** — #404/#406/#408 abgeschlossen (PR #412), Redesign-Welle eröffnet.
- **v2.2, „admiring-mayer" (#1–#15)** — externe Liste, erledigt oder bei Fehlalarm verworfen.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
