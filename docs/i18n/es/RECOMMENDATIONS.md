[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · **Español** · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Análisis de código y recomendaciones valoradas: BgRemover

## Escala de valoración

| Símbolo | Prioridad | Significado |
|---------|-----------|-------------|
| 🔴 | Crítica | Debe corregirse: provoca errores, bloqueos o inconsistencias |
| 🟠 | Alta | Debe corregirse pronto: afecta de forma importante a la fiabilidad o mantenibilidad |
| 🟡 | Media | Recomendado: mejora calidad de código, legibilidad o testabilidad |
| 🟢 | Baja | Opcional: pulido y mejoras complementarias |

---

## Estado actual (2026, pos-ronda-5)

El corte monolito→paquete está completado: `BgRemover.py` fue sustituido por el paquete `bgremover/`. El estado del canvas está encapsulado en `CanvasHistory`, `CanvasLasso` y `CanvasSelection`; `MainWindow` se dividió en toolbar, popup de historial, worker controller, RightPanel, MenuActions y RecentFiles. Los tests ya no dependen de privados del Canvas, y mypy se ejecuta sin las antiguas clases de error desactivadas por código.

Los hallazgos históricos y registros de trabajo completos de las rondas 1-5 están archivados en [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).

---

## Puntos de pulido abiertos

| Prioridad | Recomendación | Esfuerzo | Estado |
|-----------|---------------|----------|--------|
| 🟢 | Añadir classifiers de Python 3.11/3.13 | Bajo | Abierto |
| 🟡 | Revisar el alcance idiomático de `CHANGELOG.md`; alternativa: mantener canónico solo DE/EN y enlazar los demás idiomas, porque los changelogs derivan rápido | Bajo | Abierto |
| 🟢 | Unificar el idioma de la documentación donde los módulos mezclan DE/EN | Medio | Abierto |
