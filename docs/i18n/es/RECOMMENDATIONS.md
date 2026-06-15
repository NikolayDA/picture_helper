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
- La oleada de PR **#280–#283** integró el benchmark semanal e implementó tres
  hallazgos: **#235** (presupuesto compartido undo/redo, PR #281, cerrado),
  **#275** (mensaje de megapíxeles localizado, PR #282) y **#270** (subproceso
  rembg/ONNX vía `ai_process.py`, PR #283). #275 y #270 están hechos en el
  código y solo falta cerrar sus issues.

### Aún Abierto

- **O1 🟠 — Idiomas runtime adicionales.** Alemán e inglés son seleccionables
  en la app. Los idiomas de documentación es/fr/uk/zh aún no son runtime
  locales; añadirlos clave por clave en `bgremover.i18n` y cubrirlos con tests.
- **O7 ✅ — Subproceso para rembg/ONNX hecho (PR #283, issue #270).** La
  inferencia de IA no interrumpible ahora corre en un proceso iniciado con
  `spawn` (`ai_process.py`); `QThread.terminate()` como salida de emergencia de
  IA ha desaparecido. El issue #270 solo falta cerrarlo.

## Issues de GitHub Abiertos — Evaluación de Prioridad (2026-06-15)

Tras la oleada de PR **#280–#283**, quedan **7** issues abiertos. **#235** se
cerró vía el PR #281. **#270** (PR #283) y **#275** (PR #282) ya están
implementados en el código y solo falta cerrar sus issues. Nuevos son tres
hallazgos de rendimiento — **#277/#278/#279** — del run de benchmark semanal
(#280); según el triage del owner **aún no** están confirmados como regresión
de código, porque la baseline del 2026-06-08 no lleva fingerprint de entorno.
Todos los issues abiertos se reverificaron contra el código actual.

| # | Título | Relevancia | Complejidad | Recomendación |
|---|--------|------------|-------------|---------------|
| [#270](https://github.com/NikolayDA/picture_helper/issues/270) | Mover la inferencia rembg/ONNX a un subproceso (derivado de #231) | 🟠 Alta | 🟡 Media | **Hecho en el código (PR #283, `ai_process.py`).** Verificar y cerrar el issue; hoja de ruta O7 completada |
| [#277](https://github.com/NikolayDA/picture_helper/issues/277) | Regresión de rendimiento: JPEG (+38.4%) | 🟡 Media | 🟡 Media | Refinamiento: aún no confirmado como regresión de código. Ampliar el benchmark con fingerprint de entorno + runs de confirmación (mediana), y solo entonces comparar contra una baseline compatible. Agrupar con #278/#279 |
| [#278](https://github.com/NikolayDA/picture_helper/issues/278) | Regresión de rendimiento: TIFF (+21.8%) | 🟡 Media | 🟡 Media | Como #277: endurecimiento compartido del benchmark; investigar la ruta de encode (`save_image_file`) solo tras un run de confirmación compatible |
| [#279](https://github.com/NikolayDA/picture_helper/issues/279) | Regresión de rendimiento: WebP (+13.7%) | 🟡 Media | 🟡 Media | Como #277/#278: un PR compartido para fingerprint + confirmación por mediana; reportar solo regresiones confirmadas |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan falla con "Quota exceeded" | 🟡 Media | 🟢 Baja | Bloqueado (externo): restaurar la cuota en la cuenta. En el repo solo cabe un manejo más claro del error (skip elegante) + un bump opcional a Node 24, no un cambio forzado de `setup-node` |
| [#275](https://github.com/NikolayDA/picture_helper/issues/275) | El mensaje de megapíxeles «imagen demasiado grande» no está localizado | 🟢 Baja | 🟢 Baja | **Hecho en el código (PR #282).** `_too_large_message` ahora pasa por `tr("status.image_too_large[_mp]", …)` (de/en); verificar y cerrar el issue |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README: la URL de clonación devuelve 404 a usuarios anónimos | 🟢 Baja | 🟢 Baja | Decisión necesaria: público vs. privado/invitación, luego actualizar la guía de clonado o cerrar («Ronda 5» ya está corregido) |

### Orden de PRs Recomendado

1. **#270 + #275** — ambos están hechos en el código (PR #283 / #282): verificar y cerrar los issues.
2. **#277/#278/#279** — un PR compartido: ampliar el benchmark con fingerprint de entorno y runs de confirmación (mediana); reportar una regresión solo contra una baseline compatible. Bien acotado, listo para PR.
3. **#245** — restaurar la cuota externamente; endurecimiento opcional del workflow (skip elegante + Node 24) como PR pequeño aparte.
4. **#161** — decidir el modelo de publicación, luego actualizar docs o cerrar.

## Rondas Anteriores

- **2026-06-01, "modest-shannon" (A–E)** — 5 hallazgos, todos hechos.
- **v2.2, "admiring-mayer" (#1–#15)** — lista externa, completada o descartada donde fue un falso positivo.

Hallazgos históricos y registros de trabajo completos (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).
