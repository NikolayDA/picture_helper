# Codeanalyse & bewertete Empfehlungen: BgRemover

Befunde und ihre Triage leben in den
[GitHub-Issues](https://github.com/NikolayDA/picture_helper/issues) (#1032,
#1033, #1040). Diese Datei ist nur noch ein kurzer Index; sie führt keinen
Kurzstatus und keine Tabelle offener Issues mehr und hat keine Übersetzungen.

## Bewertungsskala

| Symbol | Priorität | Bedeutung |
|--------|-----------|-----------|
| 🔴 | Kritisch | Fehler, Abstürze oder Datenverlust |
| 🟠 | Hoch | Spürbarer Einfluss auf Zuverlässigkeit oder Wartbarkeit |
| 🟡 | Mittel | Sinnvolle Verbesserung für Qualität, Lesbarkeit oder Testbarkeit |
| 🟢 | Niedrig | Optionales Polishing oder Prozessverbesserung |

## Offener Bestand

- Jedes offene Issue trägt genau ein Label `prio:now`, `prio:next` oder
  `prio:later`; interne Blocker sind native Abhängigkeiten („blocked by"),
  externe tragen `blocked:extern` plus eine Kommentarzeile. Regeln:
  [`CONTRIBUTING.md`](CONTRIBUTING.md), Abschnitt „Issue-Triage".
- Neue Befunde entstehen als Issue (Vorlagen im Repository) oder über die
  Analyse-Routinen unter `.claude/commands/`, die Befunde direkt als
  Issue-Entwürfe vorschlagen.
- Der einmalige Cutover der früheren Tabelle in die Issues lief über
  `scripts/triage_issue_cutover.py` (#1033).

## Historische Berichte

- [Runden seit v2.2 bis v2.9 samt letztem Kurzstatus](docs/history/RECOMMENDATIONS-2026-v2.2-v2.9.md)
- [Historische Befunde und Arbeitsprotokolle (Runden 1–5)](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md)
