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

Todos los puntos de pulido anotados anteriormente han sido resueltos. El
proyecto no tiene actualmente ninguna recomendación abierta.
