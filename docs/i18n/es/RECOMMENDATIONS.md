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
  #270 y #275 ya están cerrados.** El review de Codex posterior al merge de #283
  y #264 produjo dos issues de seguimiento: **#285** y **#286**.

### Aún Abierto

- **O1 🟠 — Idiomas runtime adicionales.** Alemán e inglés son seleccionables
  en la app. Los idiomas de documentación es/fr/uk/zh aún no son runtime
  locales; añadirlos clave por clave en `bgremover.i18n` y cubrirlos con tests.
- **O7 ✅ — Subproceso para rembg/ONNX hecho (PR #283, issue #270 cerrado).** La
  inferencia de IA no interrumpible ahora corre en un proceso iniciado con
  `spawn` (`ai_process.py`); `QThread.terminate()` como salida de emergencia de
  IA ha desaparecido. Los hallazgos de seguimiento de robustez/memoria están en **#285**.

## Issues de GitHub Abiertos — Evaluación de Prioridad (2026-06-15)

Tras la oleada de PR **#280–#284**, quedan **7** issues abiertos. **#235**
(PR #281), **#270** (PR #283) y **#275** (PR #282) están implementados **y
cerrados**. El review de Codex posterior al merge de dos PR produjo dos issues
de seguimiento: **#285** (robustez/memoria del subproceso rembg, derivado de
#283) y **#286** (picos de memoria en la lectura de archivo limitada, derivado
de #264). Además, tres hallazgos de rendimiento — **#277/#278/#279** — del run de
benchmark semanal (#280); según el triage del owner **aún no** confirmados como
regresión de código, porque la baseline del 2026-06-08 no lleva fingerprint de
entorno. Todos los issues abiertos se reverificaron contra el código actual.

| # | Título | Relevancia | Complejidad | Recomendación |
|---|--------|------------|-------------|---------------|
| [#285](https://github.com/NikolayDA/picture_helper/issues/285) | Robustez y memoria del subproceso rembg (`ai_process.py`, derivado de #283) | 🟠 Alta | 🟡 Media | Cuatro hallazgos de Codex tras el merge: reinicio de sesión tras un fallo transitorio, liberación del payload en reposo, sobrecoste de pickle de PNG por la pipe (riesgo de OOM con imágenes grandes), carrera de stop durante el arranque del proceso. Agrupar y cubrir con tests |
| [#286](https://github.com/NikolayDA/picture_helper/issues/286) | Picos de memoria en la lectura de archivo limitada (`image_loading._read_capped`, derivado de #264) | 🟡 Media | 🟢 Baja | Dos hallazgos de Codex: `b"".join(chunks)` duplica el búfer (~1 GiB, P1), la primera lectura ignora el tamaño de `fstat()` (8 MiB, P2). `bytearray.extend` + primera lectura acotada por tamaño |
| [#277](https://github.com/NikolayDA/picture_helper/issues/277) | Regresión de rendimiento: JPEG (+38.4%) | 🟡 Media | 🟡 Media | Refinamiento: aún no confirmado como regresión de código. Ampliar el benchmark con fingerprint de entorno + runs de confirmación (mediana), y solo entonces comparar contra una baseline compatible. Agrupar con #278/#279 |
| [#278](https://github.com/NikolayDA/picture_helper/issues/278) | Regresión de rendimiento: TIFF (+21.8%) | 🟡 Media | 🟡 Media | Como #277: endurecimiento compartido del benchmark; investigar la ruta de encode (`save_image_file`) solo tras un run de confirmación compatible |
| [#279](https://github.com/NikolayDA/picture_helper/issues/279) | Regresión de rendimiento: WebP (+13.7%) | 🟡 Media | 🟡 Media | Como #277/#278: un PR compartido para fingerprint + confirmación por mediana; reportar solo regresiones confirmadas |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan falla con "Quota exceeded" | 🟡 Media | 🟢 Baja | Bloqueado (externo): restaurar la cuota en la cuenta. En el repo solo cabe un manejo más claro del error (skip elegante) + un bump opcional a Node 24, no un cambio forzado de `setup-node` |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README: la URL de clonación devuelve 404 a usuarios anónimos | 🟢 Baja | 🟢 Baja | Decisión necesaria: público vs. privado/invitación, luego actualizar la guía de clonado o cerrar («Ronda 5» ya está corregido) |

### Orden de PRs Recomendado

1. **#285** — agrupar los cuatro hallazgos de seguimiento de Codex sobre el subproceso rembg (riesgo de memoria/OOM con imágenes grandes primero), con tests de regresión.
2. **#286** — mitigar la lectura de archivo limitada (`bytearray` en vez de `b"".join`, primera lectura acotada por tamaño). Pequeño y bien acotado.
3. **#277/#278/#279** — un PR compartido: ampliar el benchmark con fingerprint de entorno y runs de confirmación (mediana); reportar una regresión solo contra una baseline compatible.
4. **#245** — restaurar la cuota externamente; endurecimiento opcional del workflow (skip elegante + Node 24) como PR pequeño aparte.
5. **#161** — decidir el modelo de publicación, luego actualizar docs o cerrar.

## Rondas Anteriores

- **2026-06-01, "modest-shannon" (A–E)** — 5 hallazgos, todos hechos.
- **v2.2, "admiring-mayer" (#1–#15)** — lista externa, completada o descartada donde fue un falso positivo.

Hallazgos históricos y registros de trabajo completos (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).
