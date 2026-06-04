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

## Issues de GitHub Abiertos — Evaluación de Prioridad (2026-06-04)

| # | Título | Relevancia | Complejidad | Recomendación |
|---|--------|------------|-------------|---------------|
| [#168](https://github.com/NikolayDA/picture_helper/issues/168) | Auditoría de la suite de tests: tests obsoletos, assertions faltantes, acoplamiento privado, brechas de cobertura | 🔴 Alta | 🔴 Alta | Hallazgos 🔴 → en PR #173; resto: dividir y refinar |
| [#167](https://github.com/NikolayDA/picture_helper/issues/167) | Revisión de código: calidad, mantenibilidad y problemas menores | 🔴 Alta | 🟡 Media | Hallazgos Medium (race, TOCTOU) → Listos para PR; hallazgos Low: agrupar |
| [#164](https://github.com/NikolayDA/picture_helper/issues/164) | Revisión de docs: INSTALL_MAC.md & INSTALL_LINUX.md — 4 issues | 🔴 Alta | 🟢 Baja | PR #172 abierto |
| [#163](https://github.com/NikolayDA/picture_helper/issues/163) | CHANGELOG.md: enlaces de versión rotos + entradas 2.3.0 faltantes | 🔴 Alta | 🟡 Media | Cambios de contenido → Listos para PR; etiquetas git necesitan refinamiento |
| [#165](https://github.com/NikolayDA/picture_helper/issues/165) | TESTING.md: tres inexactitudes respecto al código actual | 🟡 Media | 🟢 Baja | Listo para PR |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | Auditoría del README: un enlace roto y una referencia interna | 🟡 Media | 🟢 Baja | Corrección de "Runde 5" → Listo para PR; URL de clonación → Bloqueado (decisión de visibilidad del repo) |
| [#166](https://github.com/NikolayDA/picture_helper/issues/166) | Auditoría de comentarios: inconsistencias de idioma e imprecisión menor | 🟢 Baja | 🟢 Baja | Listo para PR |

### Orden de PRs Recomendado

1. **#164** — Docs de instalación (aviso Python 3.11/IA, enlace a releases + cadenas UI localizadas): implementado en **PR #172** (las seis versiones de idioma; merge pendiente).
2. **#168 🔴** — `test_canvas_events.py:174` (assertion de locale ya rota en CI) y `test_async_load.py:34` (assertion OR débil): implementado en **PR #173** (merge pendiente; resto de hallazgos #168 aparte).
3. **#167 Medium** — Double-checked lock en `_ensure_rembg_remove()` + ventana TOCTOU en `open_validated_image`: PR de bugfix limpio.
4. **#165** — Correcciones de TESTING.md: bajo riesgo y bien delimitado.
5. **#163 contenido** — Añadir features 2.3.0 faltantes + entradas `[Unreleased]` en CHANGELOG; gestionar etiquetas git por separado.
6. **#161 parcial** — Eliminar la jerga "Runde 5" del texto de arquitectura del README (corrección de URL de clonación requiere decisión sobre visibilidad del repo).
7. **#166** — Limpieza de idioma en docstrings como PR de mantenimiento menor.

## Rondas Anteriores

- **2026-06-01, "modest-shannon" (A–E)** — 5 hallazgos, todos hechos.
- **v2.2, "admiring-mayer" (#1–#15)** — lista externa, hecha o descartada
  donde fue un falso positivo.

Hallazgos históricos y registros de trabajo completos (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).
