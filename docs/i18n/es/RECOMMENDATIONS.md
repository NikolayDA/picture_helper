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

La lista activa de análisis de código está vacía. Ruff, mypy y la suite local
de tests siguen siendo la baseline antes de nuevos PRs.

### Completado Desde La Última Revisión

- **N1/N2/N4/N5/N6/N7/N8** están hechos: rutas de error, límite de tamaño,
  extensiones, guardado atómico, paquetes Qt de CI, import perezoso y docstring.
- **O2/O3/O4/O5/O6** están implementados: paquetes Linux, workflow de release,
  matriz completa, `ui_smoke` y atajos correctos por plataforma.
- Los hallazgos **#163–#206** se cerraron en los PRs documentados y quedaron
  protegidos por tests de regresión o comprobaciones de CI.
- Los PR **#263–#269** cerraron **#257, #258, #234 + #259, #248 + #260, #231**
  y **#249**; **#261** se resolvió con el PR #268 y se cerró.
- El PR **#274** cerró **#232**: `import bgremover` ya no carga el stack Qt
  gracias a exports perezosos PEP 562; un test de regresión en subproceso lo cubre.
- La oleada de PR **#280–#284** integró el benchmark semanal, implementó tres
  hallazgos — **#235** (presupuesto compartido undo/redo, PR #281), **#275**
  (mensaje de megapíxeles localizado, PR #282) y **#270** (subproceso rembg/ONNX
  vía `ai_process.py`, PR #283) — y actualizó la hoja de ruta (PR #284). **#235,
  #270 y #275 ya están cerrados.**
- Los dos hallazgos de seguimiento de Codex posteriores al merge de #283 y #264
  también están corregidos **y cerrados**: **#285** (robustez/memoria del
  subproceso rembg, PR #289) y **#286** (picos de memoria en la lectura de
  archivo limitada, PR #290).

- **N9 ✅ — Modelo de datos de proyecto/capas (epic #329) entregado.** Modelo de
  dominio sin Qt (#330), historial con reconocimiento de capas (#331), lienzo de
  composición (#332), formato `.bgrproj` (#333), panel de capas/menú de proyecto
  (#334) y migración/integración (#335) — paridad de imagen única conservada,
  `make check`/`make ui` en verde.

### Aún Abierto

- **O1 🟠 — Idiomas runtime adicionales.** Alemán e inglés son seleccionables
  en la app. Los idiomas de documentación es/fr/uk/zh aún no son runtime
  locales; añadirlos clave por clave en `bgremover.i18n` y cubrirlos con tests.
- **O7 ✅ — Subproceso para rembg/ONNX hecho (PR #283, issue #270 cerrado).** La
  inferencia de IA no interrumpible ahora corre en un proceso iniciado con
  `spawn` (`ai_process.py`); `QThread.terminate()` como salida de emergencia de
  IA ha desaparecido. Los hallazgos de seguimiento de robustez/memoria están
  corregidos y cerrados en **#285** (PR #289).

## Issues de GitHub Abiertos — Estado de Triage (2026-06-22)

A 2026-06-22, GitHub muestra **9** issues abiertos. Nuevo es el **épic de
exportación EufyMake #351** con los sub-issues **#352–#355** (rango #3 del
roadmap). La ruta de mantenimiento/skip antes listada, **#322**, se entregó vía
**#342** y ahora está **cerrada**; los issues de proyecto/capas y pruebas de
seguridad **#323/#324/#326** y **#329–#335** siguen completados en
**#337/#338/#340**.

Evaluación: **Relevancia** = importancia para el roadmap/usuarios,
**Complejidad** = esfuerzo estimado de implementación.

| # | Título | Relevancia | Complejidad | Próximo paso recomendado |
|---|--------|------------|-------------|--------------------------|
| [#351](https://github.com/NikolayDA/picture_helper/issues/351) | [Épic] Paquete de exportación EufyMake consistente | 🟠 Alta | 🔴 Alta (épic) | **Needs refinement** – según la deep research (comentario del issue), afinar el alcance a "assets de importación robustos para EufyMake Studio"; la generación nativa de `.empf` **no** es el objetivo por defecto. Se aborda vía #352–#355. |
| [#352](https://github.com/NikolayDA/picture_helper/issues/352) | Modelo de datos de exportación y definición de paquete (sin Qt) + ADR | 🟠 Alta | 🟡 Media | **Ready for PR** – tarea de investigación hecha, la decisión del ADR está en los comentarios. `eufymake_export.py` sin Qt con `ExportPlan`/`ExportAsset` (motivo de color PNG+alfa, altura en grises claro=alto, máscara de gloss); marcar 16 bits/semántica de gloss/`.empf` nativo como "abierto". Base — desbloquea #353–#355. |
| [#353](https://github.com/NikolayDA/picture_helper/issues/353) | Renderizado de assets y escritura atómica del paquete | 🟠 Alta | 🟡 Media | **Blocked** – necesita #352; bien acotado después (renderizado + escritura atómica). |
| [#354](https://github.com/NikolayDA/picture_helper/issues/354) | Comprobación de consistencia previa a la exportación | 🟠 Alta | 🟡 Media | **Blocked** – necesita #352. Mantener reutilizables los bloques de comprobación (sinergia con la comprobación general de errores previa a la exportación). |
| [#355](https://github.com/NikolayDA/picture_helper/issues/355) | UI: diálogo de exportación EufyMake + menú + i18n + ajustes | 🟠 Alta | 🟡 Media | **Blocked** – necesita #352–#354. Texto de UI según la deep research: "preparar assets para EufyMake Studio", no "producir un proyecto terminado". |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan falla con "Quota exceeded" | 🟡 Media | 🟢 Baja | **Blocked (externo)** – el endurecimiento del repo vía #322/#342 (cerrado) está hecho; el bloqueo restante es la cuota de OpenAI/billing. Tras restaurarla, lanzar el scan programado manualmente una vez y cerrar. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: considerar overrides de permisos a nivel de job en el reusable WF | 🟢 Baja | 🟡 Media | **Needs refinement** – primero documentar la semántica de GitHub (top-level vs. efectivo-por-job); no debilitar el guard OIDC #303. |
| [#339](https://github.com/NikolayDA/picture_helper/issues/339) | HEIC/HEIF no está soportado como formato de entrada | 🟢 Baja | 🟢 Baja | **Ready for PR (docs)** – el maintainer **excluyó HEIC deliberadamente** (comentario 2026-06-21). Solo aclarar README/ANLEITUNG, luego cerrar. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Higiene de tests: aserciones débiles/redundancias | 🟢 Baja | 🟢 Baja | **Ready for PR (oportunista)** – no bloquea producto ni CI; lo de mayor valor primero (asertar el endpoint del lazo, la línea de `test_helpers`, consolidar los tests de `set_brush_size`). |

### Próximo recomendado (orden de PR)

1. **#352** primero — base del épic, bien acotado tras el refinamiento del ADR;
   desbloquea #353/#354.
2. **#353** y **#354** en paralelo una vez que entre #352.
3. **#355** para cerrar el épic.
4. **#339** (PR pequeña de docs) y **#299** (cleanup de tests) como rellenos de
   baja prioridad en el ínterin.
5. Posponer **#318** hasta documentar la semántica de permisos de GitHub.
6. Mantener **#245** bloqueado externamente (ningún patch del repo restaura la
   cuota).

## Rondas Anteriores

- **2026-06-01, "modest-shannon" (A–E)** — 5 hallazgos, todos hechos.
- **v2.2, "admiring-mayer" (#1–#15)** — lista externa, completada o descartada donde fue un falso positivo.

Hallazgos históricos y registros de trabajo completos (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).
