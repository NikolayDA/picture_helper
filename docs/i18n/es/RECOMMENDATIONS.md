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

## Issues de GitHub Abiertos — Evaluación de Prioridad (2026-06-18)

A fecha de 2026-06-18 quedan **11** issues abiertos. Desde la última evaluación
(2026-06-15), **#161** (URL de clonado del README) se **cerró** el 2026-06-17; a
la vez, el ciclo de release v2.4.x trajo una oleada de issues de endurecimiento
de tests/release (**#299, #307–#312**). Siguen abiertos los tres hallazgos de
rendimiento **#277/#278/#279** (benchmark semanal #280, según el triage del
owner **aún no** confirmados como regresión de código) y **#245** (cuota de CI,
bloqueado externamente). Todos los issues abiertos se reverificaron contra el
código actual.

| # | Título | Relevancia | Complejidad | Recomendación |
|---|--------|------------|-------------|---------------|
| [#312](https://github.com/NikolayDA/picture_helper/issues/312) | CI: subir actions node20 a Node 24 | 🟠 Alta | 🟢 Baja | GitHub ya fuerza Node 24 con un aviso; subir las actions afectadas (`github-script`, `upload/download-artifact`) a majors node24 de forma uniforme, test guardián opcional |
| [#311](https://github.com/NikolayDA/picture_helper/issues/311) | Release: rellenar el cuerpo del release desde el CHANGELOG | 🟡 Media | 🟡 Media | Rellenar el cuerpo de v2.4.1 a mano; que `release-linux.yml` derive las notas de `## [X.Y.Z]` en vez de un string fijo — también al reusar |
| [#310](https://github.com/NikolayDA/picture_helper/issues/310) | Test: versión de LICENSES.md == pyproject | 🟡 Media | 🟢 Baja | Pytest rápido que compara la versión del título contra `[project].version` — detecta drift de bump antes del pesado License Check |
| [#309](https://github.com/NikolayDA/picture_helper/issues/309) | Test: el caller cubre los permisos del WF reutilizable | 🟡 Media | 🟢 Baja | Generalizar `test_release_gate.py`: el job caller debe conceder cada permiso que declare el workflow llamado (OIDC `id-token: write`) |
| [#308](https://github.com/NikolayDA/picture_helper/issues/308) | Test: cadena de IA importable en el artefacto `--ai` | 🟠 Alta | 🟡 Media | Autotest por spawn sin red en el build `--ai` que cargue los metadatos de `rembg`+`pymatting` (regresión #306) |
| [#307](https://github.com/NikolayDA/picture_helper/issues/307) | Test: lanzar el artefacto construido en headless | 🟠 Alta | 🟡 Media | Lanzar el bundle en headless en el job build (capturar crash de arranque #304 / fork bomb #305); `publish` sigue gateado por `needs: build` |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Higiene de tests: asserts débiles/redundancias | 🟢 Baja | 🟢 Baja | Sin bug de corrección; lo de mayor valor primero (mover endpoint, consolidar `set_brush_size`), el resto según haga falta |
| [#277](https://github.com/NikolayDA/picture_helper/issues/277) | Regresión de rendimiento: JPEG (+38.4%) | 🟡 Media | 🟡 Media | Aún no confirmado como regresión de código. Ampliar el benchmark con fingerprint de entorno + runs de confirmación (mediana); agrupar con #278/#279 |
| [#278](https://github.com/NikolayDA/picture_helper/issues/278) | Regresión de rendimiento: TIFF (+21.8%) | 🟡 Media | 🟡 Media | Como #277: endurecimiento compartido del benchmark; investigar la ruta de encode (`save_image_file`) solo tras un run de confirmación compatible |
| [#279](https://github.com/NikolayDA/picture_helper/issues/279) | Regresión de rendimiento: WebP (+13.7%) | 🟡 Media | 🟡 Media | Como #277/#278: un PR compartido para fingerprint + confirmación por mediana; reportar solo regresiones confirmadas |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan falla con "Quota exceeded" | 🟡 Media | 🟢 Baja | Bloqueado (externo): restaurar la cuota en la cuenta. En el repo solo cabe un manejo más claro del error (skip elegante) + un bump opcional a Node 24 |

### Orden de PRs Recomendado

1. **#307/#308** — smoke-test en headless de los bundles de release (GUI + `--ai`); evita volver a publicar crashes de arranque/fork bombs.
2. **#312** — subir las actions node20 a Node 24 antes de que GitHub retire el fallback.
3. **#309/#310/#311** — guardianes de release/CI: permisos de WF, versión de LICENSES, cuerpo del release desde el CHANGELOG (PRs pequeños aparte).
4. **#277/#278/#279** — un PR compartido: fingerprint del benchmark + confirmación por mediana; reportar una regresión solo contra una baseline compatible.
5. **#245** — restaurar la cuota externamente; endurecimiento opcional del workflow (skip elegante + Node 24).
6. **#299** — higiene de tests según haga falta.

## Rondas Anteriores

- **2026-06-01, "modest-shannon" (A–E)** — 5 hallazgos, todos hechos.
- **v2.2, "admiring-mayer" (#1–#15)** — lista externa, completada o descartada donde fue un falso positivo.

Hallazgos históricos y registros de trabajo completos (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).
