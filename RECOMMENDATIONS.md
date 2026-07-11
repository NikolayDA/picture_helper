**Deutsch** · [English](docs/i18n/en/RECOMMENDATIONS.md) · [Español](docs/i18n/es/RECOMMENDATIONS.md) · [Français](docs/i18n/fr/RECOMMENDATIONS.md) · [Українська](docs/i18n/uk/RECOMMENDATIONS.md) · [简体中文](docs/i18n/zh/RECOMMENDATIONS.md)

# Codeanalyse & bewertete Empfehlungen: BgRemover

## Bewertungsskala

| Symbol | Priorität | Bedeutung |
|--------|-----------|-----------|
| 🔴 | Kritisch | Fehler, Abstürze oder Datenverlust |
| 🟠 | Hoch | Spürbarer Einfluss auf Zuverlässigkeit oder Wartbarkeit |
| 🟡 | Mittel | Sinnvolle Verbesserung für Qualität, Lesbarkeit oder Testbarkeit |
| 🟢 | Niedrig | Optionales Polishing oder Prozessverbesserung |

## Aktueller Stand (2026-07-11)

Die laufende Codeanalyse-Liste ist leer. Ruff, mypy und die lokale Testsuite
bleiben die maßgebliche Baseline vor neuen PRs. **#431/#432** wurden über PR
#529 gemergt und geschlossen – ANLEITUNG/README und alle Screenshots spiegeln
jetzt den geführten 6-Schritte-Workflow. Damit ist Epic **#425** vollständig
erledigt (alle drei Sub-Issues #430/#431/#432 geschlossen). Zwei neue Issues
aus einem Support-Fall vom 2026-07-11 kamen hinzu (**#530**/**#531**). GitHub
zeigt aktuell weiterhin **10** offene Issues.

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
- **Seit 2026-07-11 geschlossen:** **#430** (PR #526) – Laufzeit-i18n
  ES/FR/UK/ZH vollständig gepflegt und parität-geprüft; **#431/#432** (PR
  #529) – ANLEITUNG/README/Screenshots auf den 6-Schritte-Workflow gebracht.
  **Epic #425 ist damit inhaltlich vollständig** und kann geschlossen werden.

### Noch offen

- **O8 🟢 — Prototyp-Ungenauigkeit:** Höhen-Werkzeuge bleiben im Mockup nach
  Erzeugung gesperrt; betrifft nur die Simulation, nicht die echte App (#347).

## Offene GitHub-Issues – Triage-Stand (2026-07-11)

Stand 2026-07-11 zeigt GitHub **10** offene Issues: i18n/Doku-Epic
(**#425**, bereit zum Schließen), Rollout/Release (**#426/#435/#392/#389**),
Backlog/Externe Punkte (**#299/#318/#245**) und zwei neue KI-Warmup-Befunde
aus demselben Support-Fall (**#530/#531**).

### Sinnvolle Bündelung

- **i18n/Doku:** #425 ist mit #430/#431/#432 vollständig erledigt – nur noch
  formal schließen.
- **Rollout/Release:** #426 hängt nur an #435; mit #392 koordinieren, dann
  #426/#389 schließen.
- **KI-Warmup-Support-Fall (2026-07-11):** #530 (Doku-Korrektur, mechanisch)
  und #531 (Tooltip-/Statustext-UX) sind unabhängig voneinander umsetzbar;
  #530 ist der schnellere, risikoärmere Fix und kann zuerst laufen.
- **Backlog:** #299 nach dem Release; #318 erst schärfen; #245 extern
  blockiert.

Bewertung: **Relevanz** = Bedeutung für Roadmap/Nutzer, **Komplexität** =
geschätzter Umsetzungsaufwand, **Modell/Aufwand** = empfohlenes
Claude-Modell und Reasoning-Effort für die Umsetzung durch Claude Code.

| # | Titel | Relevanz | Komplexität | Modell/Aufwand | Empfohlener nächster Schritt |
|---|-------|----------|-------------|-----------------|------------------------------|
| [#435](https://github.com/NikolayDA/picture_helper/issues/435) | CHANGELOG & Versionsanhebung für das Redesign | 🟡 Mittel | 🟢 Niedrig | Sonnet 5 · niedrig | **Ready for PR** – mechanisch, klar umrissen; blockiert #426 und #392. |
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | Release v2.5.0 schneiden | 🟠 Hoch | 🟡 Mittel | Sonnet 5 · mittel | **Startbereit** – nach #435 sequenzieren; #431/#432 sind jetzt kein Blocker mehr; macOS-`.dmg`-Build braucht eine lokale/macOS-Runner-Umgebung außerhalb des Remote-Containers. |
| [#530](https://github.com/NikolayDA/picture_helper/issues/530) | INSTALL_LINUX/MAC.md: KI-Download startet beim App-Start, nicht beim ersten Klick | 🟡 Mittel | 🟢 Niedrig | Sonnet 5 · niedrig | **Ready for PR** – reine Textkorrektur in 2 Dateien + 5 i18n-Spiegeln, Code-Zeilen bereits im Issue belegt. |
| [#531](https://github.com/NikolayDA/picture_helper/issues/531) | KI-Button: Warmup-/Ladezustand sichtbar machen | 🟡 Mittel | 🟡 Mittel | Sonnet 5 · mittel | **Ready for PR** – klare Akzeptanzkriterien inkl. qtbot-Test-Vorgabe; Tooltip-Text in 6 Sprachen zu ergänzen, `can_enable`-Logik bleibt unverändert. |
| [#425](https://github.com/NikolayDA/picture_helper/issues/425) | EPIC: Internationalisierung & Dokumentation | 🟠 Hoch | 🟢 Niedrig | – (Tracking-Issue) | **Bereit zum Schließen** – #430/#431/#432 alle erledigt (PR #526/#529). |
| [#426](https://github.com/NikolayDA/picture_helper/issues/426) | EPIC: Qualitätssicherung & Rollout | 🟠 Hoch | 🟢 Niedrig | – (Tracking-Issue) | **Fast fertig** – nur #435 bleibt offen. |
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | EPIC: Nutzer-Doku aktualisieren & Release | 🟠 Hoch | 🟢 Niedrig | – (Tracking-Issue) | **Nach #392 schließen** – nur Release offen. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test-Hygiene: schwache Assertions/Redundanzen | 🟢 Niedrig | 🟡 Mittel | Sonnet 5 · mittel | **Ready for PR** – Katalog + N13-Nachträge aus Triage 2026-07-08 liegen vor; nach der Release priorisieren. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Job-Level-Permission-Overrides im Reusable-WF | 🟢 Niedrig | 🟡 Mittel | Opus 4.8 · hoch | **Needs refinement** – GitHub-Semantik (Top-Level vs. effektiv-per-Job) zuerst belegen, OIDC-Regressionsguard darf nicht aufweichen. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan „Quota exceeded" | 🟡 Mittel | 🟢 Niedrig | – (kein Code-Task) | **Blockiert (extern)** – OpenAI-Billing/Quota-Wiederherstellung ist eine Account-Aktion, kein PR. |

### Als Nächstes empfohlen (PR-Reihenfolge)

1. **#530** – schnellster, risikoärmster Fix; kann sofort parallel laufen.
2. **Release:** **#435** + **#392** koordiniert fahren, dann **#426**/**#389**
   sowie **#425** schließen.
3. **#531** – UX-Fix zum selben Support-Fall wie #530.
4. **#299** nach der Release; **#318** nur erforschen; **#245** extern
   blockiert.

## Vorige Runden

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
