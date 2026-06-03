[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · **Español** · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Análisis de Código y Recomendaciones Priorizadas: BgRemover

## Escala de Prioridad

| Símbolo | Prioridad | Significado |
|---------|-----------|-------------|
| 🔴 | Crítica | Errores, cierres inesperados o pérdida de datos |
| 🟠 | Alta | Impacto claro en fiabilidad o mantenibilidad |
| 🟡 | Media | Mejora útil para calidad, legibilidad o testabilidad |
| 🟢 | Baja | Pulido opcional o mejora de proceso |

## Estado Actual (2026-06-04)

La lista activa de análisis de código está vacía. La última revisión de
seguimiento está implementada y cubierta por tests; ruff, mypy y la suite local
siguen siendo la baseline antes de nuevos PRs.

### Completado Desde La Última Revisión

- **N1/N2/N4/N5/N6/N7/N8** están hechos: ruta de error de la varita, límite de
  tamaño al rotar, extensiones honestas, guardado atómico, paquetes Qt de CI,
  import perezoso de `rembg` y docstring de `load_image`.
- **O2/O3/O4/O5/O6** están implementados: Linux AppImage/`.deb`, release
  workflow, matriz completa semanal, `ui_smoke` en PR/Full CI y atajos de
  herramientas con indicaciones correctas por plataforma.

### Aún Abierto

- **O1 🟠 — Idiomas runtime adicionales.** Alemán e inglés son seleccionables
  en la app. Los idiomas existentes en la documentación (es/fr/uk/zh) aún no
  son runtime locales; si hace falta, añadirlos clave por clave en
  `bgremover.i18n` y protegerlos con tests de paridad/smoke.

## Rondas Anteriores

- **2026-06-01, "modest-shannon" (A–E)** — 5 hallazgos, todos hechos.
- **v2.2, "admiring-mayer" (#1–#15)** — lista externa, hecha o descartada
  donde fue un falso positivo.

Hallazgos históricos y registros de trabajo completos (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).
