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
- **#164/#167/#168** están hechos (PRs #172/#174/#173); los hallazgos
  restantes ya se completaron también vía #176/#178.
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
- **Lote de seguridad del 2026-06-07 completado** (#200/#201/#202/#205/#206
  vía PRs #209/#211/#222): setuptools/wheel/pip/urllib3/idna fijados o
  exigidos, cada uno protegido por un test de regresión ligado a CVE.

### Aún Abierto

- **O1 🟠 — Idiomas runtime adicionales.** Alemán e inglés son seleccionables
  en la app. Los idiomas existentes en la documentación (es/fr/uk/zh) aún no
  son runtime locales; si hace falta, añadirlos clave por clave en
  `bgremover.i18n` y protegerlos con tests de paridad/smoke.

## Issues de GitHub Abiertos — Evaluación de Prioridad (2026-06-12)

Ahora **14** issues abiertos: los puntos de observación #203/#204, el aplazado
#161, los hallazgos de docs/auditoría #218/#226/#227/#236, más el lote de
calidad de código #229–#235 de la auditoría del 2026-06-11. #203/#204 no son
dependencias del proyecto (puramente transitivas/del sistema) → informativo,
sin cambio en `constraints.txt`.

| # | Título | Relevancia | Complejidad | Recomendación |
|---|--------|------------|-------------|---------------|
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | Auditoría del README: la URL de clonación no lleva a ninguna parte | 🟡 Media | 🟢 Baja | Bloqueado (decisión del owner sobre visibilidad del repo) |
| [#203](https://github.com/NikolayDA/picture_helper/issues/203) | cryptography 41.0.7 — 6 CVEs | 🟢 Baja | 🟢 Baja | Punto de observación, sin acción del proyecto |
| [#204](https://github.com/NikolayDA/picture_helper/issues/204) | pyjwt 2.7.0 — 5 CVEs | 🟢 Baja | 🟢 Baja | Punto de observación, sin acción del proyecto |
| [#218](https://github.com/NikolayDA/picture_helper/issues/218) | CHANGELOG: faltan entradas en `[Unreleased]` | 🟡 Media | 🟢 Baja | Listo para PR (añadir las siete entradas en el estilo existente) |
| [#226](https://github.com/NikolayDA/picture_helper/issues/226) | Revisión de INSTALL: apunta a releases vacíos + dos detalles | 🟡 Media | 🟢 Baja | Listo para PR (fixes de docs); la nota de artefactos depende de la decisión de etiquetado |
| [#227](https://github.com/NikolayDA/picture_helper/issues/227) | Auditoría de RECOMMENDATIONS: resumen de issues desactualizado | 🟡 Media | 🟢 Baja | Resuelto por esta actualización → cerrar el issue |
| [#229](https://github.com/NikolayDA/picture_helper/issues/229) | El warmup de rembg no crea una sesión de inferencia reutilizable | 🟠 Alta | 🟡 Media | Listo para PR (cachear una sesión vía `new_session`) |
| [#230](https://github.com/NikolayDA/picture_helper/issues/230) | El archivo se lee entero en memoria antes del check de tamaño | 🟠 Alta | 🟢 Baja | Listo para PR (límite de bytes antes del `read()`) |
| [#231](https://github.com/NikolayDA/picture_helper/issues/231) | `QThread.terminate()` puede abortar workers de forma insegura | 🟡 Media | 🟠 Alta | Necesita refinamiento (decidir opción A/B/C; a corto plazo opción C) |
| [#232](https://github.com/NikolayDA/picture_helper/issues/232) | `import bgremover` carga toda la GUI PyQt6 | 🟡 Media | 🟡 Media | Listo para PR (exports perezosos vía PEP 562) |
| [#233](https://github.com/NikolayDA/picture_helper/issues/233) | Settings de recent_files corruptos rompen el menú | 🟡 Media | 🟢 Baja | Listo para PR (`paths()` defensivo + tests parametrizados) |
| [#234](https://github.com/NikolayDA/picture_helper/issues/234) | Una migración faltante sube igualmente `schema_version` | 🟢 Baja | 🟢 Baja | Listo para PR (antes de la primera migración real) |
| [#235](https://github.com/NikolayDA/picture_helper/issues/235) | El límite de undo ignora redo/imagen original | 🟢 Baja | 🟡 Media | Necesita refinamiento (decidir solo-docs vs. presupuesto compartido) |
| [#236](https://github.com/NikolayDA/picture_helper/issues/236) | Comentario de session-start.sh: falta `benchmark.yml` | 🟢 Baja | 🟢 Baja | Listo para PR (fix de comentario de una línea) |

### Orden de PRs Recomendado

1. **#230** — máxima relevancia con baja complejidad: límite de tamaño de archivo antes de leer, cubre los caminos sync y async de forma central.
2. **#229** — reutilizar la sesión del warmup; la mayor ganancia para el pipeline de IA, y de paso se corrige el comentario incorrecto.
3. **#233** — `paths()` defensivo con tests parametrizados; encaja con el objetivo de robustez del esquema de settings.
4. **#236 + #218** — fixes pequeños de comentario/docs, idealmente agrupados; **#227** queda resuelto por esta actualización y puede cerrarse.
5. **#232** — exports perezosos vía PEP 562; alcance medio por la migración de tests/imports.
6. **#234** — fix pequeño; planificarlo como muy tarde antes de la primera migración real del esquema.
7. **#226** — fixes de docs ahora; la nota de artefactos de release depende de la decisión de etiquetado del owner.
8. **#235** — decidir primero la semántica (solo docs vs. presupuesto compartido), luego implementar.
9. **#231** — a corto plazo opción C (esperas acotadas + logging), evaluar a largo plazo la opción B (subproceso).
10. **#203/#204** siguen como puntos de observación; **#161** sigue bloqueado (decisión del owner).

## Rondas Anteriores

- **2026-06-01, "modest-shannon" (A–E)** — 5 hallazgos, todos hechos.
- **v2.2, "admiring-mayer" (#1–#15)** — lista externa, hecha o descartada
  donde fue un falso positivo.

Hallazgos históricos y registros de trabajo completos (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).
