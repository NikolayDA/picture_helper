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
- **#164** está hecho y mergeado (PR #172): aviso Python 3.11/IA, enlace a
  releases y cadenas UI localizadas en las guías de instalación.
- **#167 / #168** están cerrados: los hallazgos High/Medium se entregaron vía
  PR #173/#174; el resto continúa de forma enfocada en #176/#177/#178.

### Aún Abierto

- **O1 🟠 — Idiomas runtime adicionales.** Alemán e inglés son seleccionables
  en la app. Los idiomas existentes en la documentación (es/fr/uk/zh) aún no
  son runtime locales; si hace falta, añadirlos clave por clave en
  `bgremover.i18n` y protegerlos con tests de paridad/smoke.

## Issues de GitHub Abiertos — Evaluación de Prioridad (2026-06-04)

| # | Título | Relevancia | Complejidad | Recomendación |
|---|--------|------------|-------------|---------------|
| [#163](https://github.com/NikolayDA/picture_helper/issues/163) | CHANGELOG.md: enlaces de versión rotos + entradas 2.3.0 faltantes | 🔴 Alta | 🟡 Media | Cambios de contenido → Listos para PR; etiquetas git necesitan refinamiento |
| [#177](https://github.com/NikolayDA/picture_helper/issues/177) | Seguimiento de auditoría de tests (Medium): assertions de comportamiento + brechas de cobertura | 🟠 Alta | 🟡 Media | Listo para PR (de #168) |
| [#165](https://github.com/NikolayDA/picture_helper/issues/165) | TESTING.md: tres inexactitudes respecto al código actual | 🟡 Media | 🟢 Baja | Listo para PR |
| [#176](https://github.com/NikolayDA/picture_helper/issues/176) | Seguimiento de revisión de código (Low): E741, check_untyped_defs, UX de cancel_ai, shutdown_all | 🟡 Media | 🟢 Baja | Listo para PR (de #167) |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | Auditoría del README: un enlace roto y una referencia interna | 🟡 Media | 🟢 Baja | Jerga "Runde 5" corregida; URL de clonación aplazada (decisión del owner) |
| [#178](https://github.com/NikolayDA/picture_helper/issues/178) | Seguimiento de auditoría de tests (Low): desacoplar de internals privados + deduplicar | 🟢 Baja | 🟡 Media | Listo para PR (de #168) |
| [#166](https://github.com/NikolayDA/picture_helper/issues/166) | Auditoría de comentarios: inconsistencias de idioma e imprecisión menor | 🟢 Baja | 🟢 Baja | Listo para PR |

### Orden de PRs Recomendado

1. **#165** — Correcciones de TESTING.md: bajo riesgo y bien delimitado.
2. **#163 contenido** — Añadir features 2.3.0 faltantes + entradas `[Unreleased]` en CHANGELOG; gestionar etiquetas git por separado.
3. **#177** — Endurecer tests: añadir assertions de comportamiento + cerrar brechas de cobertura (de #168).
4. **#176** — Lote de calidad de código de #167: E741, check_untyped_defs, UX de cancel_ai, shutdown_all.
5. **#178** — Desacoplar tests de internals privados + reducir tests duplicados (de #168).
6. **#166** — Limpieza de idioma en docstrings como PR de mantenimiento menor.
7. **#161 aplazado** — "Runde 5" hecho; solo queda la URL de clonación (decisión del owner sobre visibilidad del repo).

## Rondas Anteriores

- **2026-06-01, "modest-shannon" (A–E)** — 5 hallazgos, todos hechos.
- **v2.2, "admiring-mayer" (#1–#15)** — lista externa, hecha o descartada
  donde fue un falso positivo.

Hallazgos históricos y registros de trabajo completos (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).
