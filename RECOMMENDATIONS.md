**Deutsch** · [English](docs/i18n/en/RECOMMENDATIONS.md) · [Español](docs/i18n/es/RECOMMENDATIONS.md) · [Français](docs/i18n/fr/RECOMMENDATIONS.md) · [Українська](docs/i18n/uk/RECOMMENDATIONS.md) · [简体中文](docs/i18n/zh/RECOMMENDATIONS.md)

# Codeanalyse & bewertete Empfehlungen: BgRemover

## Bewertungsskala

| Symbol | Priorität | Bedeutung |
|--------|-----------|-----------|
| 🔴 | Kritisch | Muss behoben werden – führt zu Fehlern, Abstürzen oder Inkonsistenzen |
| 🟠 | Hoch | Sollte bald behoben werden – beeinträchtigt Zuverlässigkeit oder Wartbarkeit erheblich |
| 🟡 | Mittel | Empfohlen – verbessert Code-Qualität, Lesbarkeit oder Testbarkeit |
| 🟢 | Niedrig | Optional – Polishing, ergänzende Verbesserungen |

---

## Aktueller Stand (2026, post-Runde-5)

Der Monolith→Paket-Schnitt ist abgeschlossen: `BgRemover.py` ist durch das Paket `bgremover/` ersetzt. Die Canvas-Zustände sind in `CanvasHistory`, `CanvasLasso` und `CanvasSelection` gekapselt; `MainWindow` ist in Toolbar, History-Popup, Worker-Controller, RightPanel, MenuActions und RecentFiles aufgespalten. Tests koppeln nicht mehr an Canvas-Privates, und mypy läuft ohne die früheren per-Code deaktivierten Fehlerklassen.

Die vollständigen historischen Befunde und Arbeitsprotokolle aus Runden 1-5 liegen im Archiv: [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).

---

## Offene Polish-Punkte

| Prio | Empfehlung | Aufwand | Status |
|------|------------|---------|--------|
| 🟡 | i18n-Drift-Test: `CHANGELOG`/`INSTALL` strukturell synchron halten | Mittel | Offen |
| 🟢 | Doku-Sprache vereinheitlichen, wo Module DE/EN mischen | Mittel | Offen |
