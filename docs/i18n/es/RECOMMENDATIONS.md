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
- **#164/#167/#168** están hechos (PRs #172/#174/#173); el resto continúa de
  forma enfocada en #176/#178.
- **Verificado como resuelto limpiamente el 2026-06-06** (PRs #188–#193, cada
  uno con test de regresión, `make check` en verde – 504 passed): **#163**
  (enlaces del CHANGELOG cambiados a SHAs de commit reales y resolubles en
  GitHub; cuatro features 2.3.0 faltantes + entrada idna/urllib3; etiquetas git
  reales no creadas a propósito), **#165/#180** (TESTING.md: filtro `addopts`,
  `ui_smoke`, schedule semanal, shellcheck, `make coverage`), **#184**
  (generación de carga + recheck de `content_revision` contra cargas async
  tardías), **#182** (`PIP_CONSTRAINT` integrado en el build de AppImage),
  **#183** (license-check en solo-lectura + job de comentario aislado), **#177**
  (assertions de comportamiento + nuevo `tests/test_history_popup.py`).

### Aún Abierto

- **O1 🟠 — Idiomas runtime adicionales.** Alemán e inglés son seleccionables
  en la app. Los idiomas existentes en la documentación (es/fr/uk/zh) aún no
  son runtime locales; si hace falta, añadirlos clave por clave en
  `bgremover.i18n` y protegerlos con tests de paridad/smoke.

## Issues de GitHub Abiertos — Evaluación de Prioridad (2026-06-06)

Solo quedan **cinco** issues abiertos, todos 🟡/🟢: dos `documentation` (#161,
#166), dos `quality/testing` (#176, #178) y un hallazgo de seguridad/privacidad
(#185). #163/#165/#177/#180 y los tres hallazgos de seguridad de mayor prioridad
del escaneo Codex `8c04b92` (#182/#183/#184) están cerrados y verificados desde
la última revisión. **No queda ningún hallazgo 🔴/🟠 abierto.**

| # | Título | Relevancia | Complejidad | Recomendación |
|---|--------|------------|-------------|---------------|
| [#176](https://github.com/NikolayDA/picture_helper/issues/176) | Seguimiento de revisión de código (Low): E741, check_untyped_defs, UX de cancel_ai, shutdown_all | 🟡 Media | 🟢 Baja | Listo para PR (de #167); `E741`/`check_untyped_defs` en `pyproject.toml` aún sin cambios |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | Auditoría del README: un enlace roto y una referencia interna | 🟡 Media | 🟢 Baja | Parcialmente hecho: jerga "Runde 5" eliminada; solo queda la URL de clonación (decisión del owner) |
| [#185](https://github.com/NikolayDA/picture_helper/issues/185) | Seguridad: el diagnóstico de macOS revela rutas locales + cola de log en bruto (privacidad) | 🟢 Baja | 🟡 Media | Listo para PR; redactar `$HOME`/rutas + flag `--include-raw-logs` + test de shell |
| [#178](https://github.com/NikolayDA/picture_helper/issues/178) | Seguimiento de auditoría de tests (Low): desacoplar de internals privados + deduplicar | 🟢 Baja | 🟡 Media | Listo para PR (de #168) |
| [#166](https://github.com/NikolayDA/picture_helper/issues/166) | Auditoría de comentarios: inconsistencias de idioma e imprecisión menor | 🟢 Baja | 🟢 Baja | Listo para PR; docstrings en inglés en `right_panel.py`/`main_window.py` |

### Orden de PRs Recomendado

1. **#176** — Lote de calidad de código de #167: acotar `E741`, `check_untyped_defs` de forma incremental, UX de cancel_ai, anular referencias de hilos en `shutdown_all`.
2. **#185** — Redactar el diagnóstico de macOS (`$HOME`/rutas) + flag `--include-raw-logs` + test de shell.
3. **#178** — Desacoplar tests de internals privados + reducir tests duplicados (de #168).
4. **#166** — Limpieza de idioma en docstrings como PR de mantenimiento menor.
5. **#161 aplazado** — "Runde 5" hecho; solo queda la URL de clonación (decisión del owner sobre visibilidad del repo).

## Rondas Anteriores

- **2026-06-01, "modest-shannon" (A–E)** — 5 hallazgos, todos hechos.
- **v2.2, "admiring-mayer" (#1–#15)** — lista externa, hecha o descartada
  donde fue un falso positivo.

Hallazgos históricos y registros de trabajo completos (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).
