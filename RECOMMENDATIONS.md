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
Ein Repo-Audit vom 2026-07-12 hat fünf neue Befunde als Issues erfasst
(**#549–#553**); GitHub zeigt damit aktuell **6** offene Issues: **#245**
sowie **#549–#553**.

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
  **#541** (PR #543), **#318** (PR #540) und die Recommendations-Snapshot-
  Synchronisation **#542**. Damit sind alle Redesign-/Release-/Backlog-Punkte
  des letzten Snapshots abgearbeitet.

### Noch offen

- **O8 🟢 — Prototyp-Ungenauigkeit:** Höhen-Werkzeuge bleiben im Mockup nach
  Erzeugung gesperrt; betrifft nur die Simulation, nicht die echte App (#347).

## Offene GitHub-Issues – Triage-Stand (2026-07-12)

Stand 2026-07-12 zeigt GitHub **6** offene Issues: den externen
Quota-/Billing-Blocker **#245** sowie fünf neue Befunde aus dem laufenden
Repo-Audit – **#549** (Recommendations-Snapshot), **#550** (v2.3.0-Tag-/
Release-Konsistenz), **#551** (Grundsatzentscheidung Codex Security Scan),
**#552** (PR-Template) und **#553** (SessionStart-Hook-Verifikation).

### Sinnvolle Bündelung

#245 und #551 hängen inhaltlich zusammen (Codex-Scan): #245 ist eine reine
Account-Aktion, #551 braucht dagegen eine eigene Grundsatzentscheidung
(reaktivieren/zurückbauen/ersetzen). #550 braucht ebenfalls zuerst eine
Entscheidung (Tag+Release vs. nur Doku-Klarstellung). #549 (dieser PR), #552
und #553 sind unabhängig und sofort umsetzbar.

Bewertung: **Relevanz** = Bedeutung für Roadmap/Nutzer, **Komplexität** =
geschätzter Umsetzungsaufwand, **Modell/Aufwand** = empfohlenes
Claude-Modell und Reasoning-Effort für die Umsetzung durch Claude Code.

| # | Titel | Relevanz | Komplexität | Modell/Aufwand | Empfohlener nächster Schritt |
|---|-------|----------|-------------|-----------------|------------------------------|
| [#552](https://github.com/NikolayDA/picture_helper/issues/552) | PR-Template mit Standard-Gate-Checkliste | 🟡 Mittel | 🟢 Niedrig | Sonnet 5 · niedrig | **Ready for PR** – eine neue Datei, keine Abhängigkeiten. |
| [#553](https://github.com/NikolayDA/picture_helper/issues/553) | SessionStart-Hook-Zuverlässigkeit in Web-Sessions verifizieren | 🟡 Mittel | 🟡 Mittel | Sonnet 5 · mittel | **Ready for PR** – Reproduktion in frischer Web-Session, danach ggf. Fix + Doku. |
| [#549](https://github.com/NikolayDA/picture_helper/issues/549) | Recommendations-Snapshot auf Live-Stand aktualisieren | 🟢 Niedrig | 🟢 Niedrig | Sonnet 5 · niedrig | **Ready for PR** – wird durch diesen Snapshot-Sync abgedeckt. |
| [#550](https://github.com/NikolayDA/picture_helper/issues/550) | v2.3.0: Tag-/Release-Konsistenz im CHANGELOG herstellen | 🟡 Mittel | 🟡 Mittel | Sonnet 5 · mittel | **Needs refinement** – Variante A (Tag+Release) vs. B (nur Doku-Klarstellung) erfordert eine Entscheidung vor der Umsetzung. |
| [#551](https://github.com/NikolayDA/picture_helper/issues/551) | Grundsatzentscheidung Codex Security Scan (reaktivieren/zurückbauen/ersetzen) | 🟡 Mittel | 🟡 Mittel | Sonnet 5 · mittel | **Needs refinement** – erfordert eine bewusste Entscheidung zwischen drei Optionen; Empfehlung: Option 2 (Zurückbauen/Deaktivieren) angesichts wochenlanger externer Blockade und Redundanz zu pip-audit/license/CI. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan „Quota exceeded" | 🟡 Mittel | 🟢 Niedrig | – (kein Code-Task) | **Blockiert (extern)** – OpenAI-Billing/Quota-Wiederherstellung ist eine Account-Aktion, kein PR. |

### Als Nächstes empfohlen (PR-Reihenfolge)

1. **#552** — PR-Template ergänzen (eigenständig, geringes Risiko).
2. **#549** — mit diesem PR abschließen (Snapshot-Sync über alle sechs
   Spiegel, inkl. #550–#553).
3. **#553** — SessionStart-Hook in frischer Web-Session reproduzieren und
   ggf. beheben.
4. **#550** — Entscheidung Variante A/B einholen, dann CHANGELOG/Tag/Release
   anpassen.
5. **#551** — Entscheidung zur Scan-Strategie einholen (an #245 gekoppelt),
   dann Workflow anpassen.
6. **#245** — bleibt extern blockiert; erst nach Wiederherstellung der
   OpenAI-Quota manuell verifizieren.

## Vorige Runden

- **2026-07-12 (Issue-Audit)** — #542 (Recommendations-Snapshot) geschlossen;
  Repo-Audit hat fünf neue Issues erfasst (#549–#553: Doku-Snapshot,
  Release-Tag-Konsistenz, Security-Scan-Grundsatzentscheidung, PR-Template,
  SessionStart-Hook-Verifikation); Open-Issue-Snapshot auf 6 aktualisiert
  (#245 + #549–#553).
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
- **2026-07-05/06** — #490 (Snapshot-Drift), Dark-Mode-/Rail-Icon-Welle,
  Karten-Inspector (#413/#414), #499–#501/#503 (PR #504/#506) sowie Icon-/
  Statuszeilen-Feinschliff (PR #507/#508) abgeschlossen.
- **2026-06-29** — #404/#406/#408 abgeschlossen (PR #412), Redesign-Welle eröffnet.
- **v2.2, „admiring-mayer" (#1–#15)** — externe Liste, erledigt oder bei Fehlalarm verworfen.

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
