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

### Aún Abierto

- **O1 🟠 — Idiomas runtime adicionales.** Alemán e inglés son seleccionables
  en la app. Los idiomas de documentación es/fr/uk/zh aún no son runtime
  locales; añadirlos clave por clave en `bgremover.i18n` y cubrirlos con tests.
- **O7 ✅ — Subproceso para rembg/ONNX hecho (PR #283, issue #270 cerrado).** La
  inferencia de IA no interrumpible ahora corre en un proceso iniciado con
  `spawn` (`ai_process.py`); `QThread.terminate()` como salida de emergencia de
  IA ha desaparecido. Los hallazgos de seguimiento de robustez/memoria están
  corregidos y cerrados en **#285** (PR #289).

## Issues de GitHub Abiertos — Evaluación de Prioridad (2026-06-19)

A fecha de 2026-06-19 quedan **4** issues abiertos. Desde la evaluación del
2026-06-18, la oleada de endurecimiento de tests/release se integró en gran
parte: **#307, #308, #309, #310** y **#312** ya están **cerrados** (igual que el
meta-issue del snapshot **#313**). Los tres hallazgos de rendimiento
**#277/#278/#279** (benchmark semanal #280) quedan **cerrados** mediante el
endurecimiento del benchmark de este PR (fingerprint de entorno + confirmación
por mediana; reportar solo contra baselines comparables). El PR **#317** (que
cerró #309/#310) generó un nuevo seguimiento **#318** a partir de su revisión de
Codex (overrides de permisos a nivel de job en el guard del workflow
reutilizable). Siguen abiertos **#311** (cuerpo del release), **#318** (guard de
permisos), **#245** (cuota de CI, bloqueado externamente) y el ítem de higiene de
tests de baja prioridad **#299**. El triaje de **#245** generó además tres
seguimientos de endurecimiento del lado del repo, agrupados — **#322** (ruta de
mantenimiento/skip), **#323** (tests del sync de issues de seguridad) y **#324**
(gobernanza del alcance del prompt) —, que cuelgan de #245 hasta restaurar la
cuota en la cuenta. Todos los issues abiertos se reverificaron contra el código
actual.

| # | Título | Relevancia | Complejidad | Recomendación |
|---|--------|------------|-------------|---------------|
| [#311](https://github.com/NikolayDA/picture_helper/issues/311) | Release: rellenar el cuerpo del release desde el CHANGELOG | 🟡 Media | 🟡 Media | **Listo para PR** — bien acotado: rellenar el cuerpo de v2.4.1 a mano; que `release-linux.yml` derive las notas de `## [X.Y.Z]` en vez de un string fijo (también al reusar), con un test de regresión en `test_release_gate.py` |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: respetar overrides de permisos a nivel de job en el WF reutilizable | 🟡 Media | 🟡 Media | **Necesita refinamiento** — primero confirmar la semántica de validación de arranque de GitHub (top-level vs. efectivo-por-job); actualmente es un falso positivo puramente teórico (no hay overrides a nivel de job en `ci.yml`), y el guard OIDC #303 no debe debilitarse |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan falla con "Quota exceeded" | 🟡 Media | 🟢 Baja | **Bloqueado (externo):** restaurar la cuota en la cuenta. El endurecimiento del lado del repo se sigue ahora en **#322–#324** (ruta de mantenimiento/skip, tests del sync, gobernanza del prompt); el skip elegante es la variante B de #322 |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Higiene de tests: asserts débiles/redundancias | 🟢 Baja | 🟢 Baja | Sin bug de corrección; lo de mayor valor primero (mover endpoint, consolidar `set_brush_size`), el resto según haga falta |

### Issues Agrupables

- **#318** es el seguimiento del guard de permisos ya integrado (#309/#310) y se queda separado — primero necesita la semántica de GitHub documentada antes de tocar `_required_permissions`.
- **#311** se queda autónomo porque toca el workflow de release, la extracción del CHANGELOG y las notas de release existentes.
- **#299** es higiene de tests oportunista y solo debería acompañar si ya se toca ese test.

### Orden de PRs Recomendado

1. **#311** — derivar los cuerpos de release desde el CHANGELOG y completar las notas de v2.4.1; bien acotado y visible para el usuario (los fixes ya lanzados son de otro modo invisibles en la página del release).
2. **#318** — refinar el guard de permisos una vez documentada la semántica de GitHub, sin debilitar el caso de regresión OIDC.
3. **#245** — restaurar la cuota externamente; el endurecimiento del lado del repo se sigue en **#322–#324** (ruta de mantenimiento/skip, tests del sync, gobernanza del prompt).
4. **#299** — higiene de tests según haga falta.

## Rondas Anteriores

- **2026-06-01, "modest-shannon" (A–E)** — 5 hallazgos, todos hechos.
- **v2.2, "admiring-mayer" (#1–#15)** — lista externa, completada o descartada donde fue un falso positivo.

Hallazgos históricos y registros de trabajo completos (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).
