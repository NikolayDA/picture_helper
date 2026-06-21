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

## Issues de GitHub Abiertos — Evaluación de Prioridad (2026-06-20)

A fecha de 2026-06-20 quedan **14** issues abiertos. Desde la evaluación del
2026-06-19, **#311** (cuerpo del release) se cerró. Las novedades son el épico
**#329** (modelo de datos de proyecto/capas — base para mapa de altura, brillo y
exportación EufyMake) con sus seis sub-issues **#330–#335**, además del hallazgo
de cobertura de tests **#326** (GIF declarado como formato de entrada pero sin
test). El épico de capas es el puesto #1 priorizado de la hoja de ruta: **#330**
(modelo de dominio sin Qt) es la piedra angular sin dependencias y realizable de
inmediato, mientras que los demás sub-issues están bloqueados a lo largo de la
cadena de dependencias (#330 → #331 → #332/#333 → #334 → #335). Siguen abiertos
de la ronda anterior: **#318** (guard de permisos), **#245** (cuota de CI,
bloqueado externamente), los tres seguimientos de endurecimiento de **#245**
**#322–#324** y el ítem de higiene de tests de baja prioridad **#299**. Todos los
issues abiertos se reverificaron contra el código actual.

| # | Título | Relevancia | Complejidad | Recomendación |
|---|--------|------------|-------------|---------------|
| [#329](https://github.com/NikolayDA/picture_helper/issues/329) | [Épico] Modelo de datos de proyecto/capas (base para mapa de altura/brillo/EufyMake) | 🟠 Alta | 🟠 Alta | **Épico / tracking** — puesto #1 de la hoja de ruta; trabajar a través de los seis sub-issues, no como PR propio |
| [#330](https://github.com/NikolayDA/picture_helper/issues/330) | Modelo de dominio `Project` + `Layer` (sin Qt) | 🟠 Alta | 🟡 Media | **Listo para PR** — piedra angular sin dependencias; sin Qt, tipado estricto, compositing/roles, `tests/test_project_model.py`. Punto de partida del épico |
| [#331](https://github.com/NikolayDA/picture_helper/issues/331) | Undo/redo a nivel de proyecto (historial consciente de capas) | 🟠 Alta | 🟠 Alta | **Bloqueado por #330** — historial consciente de capas, testeable de forma aislada antes del cableado del canvas |
| [#332](https://github.com/NikolayDA/picture_helper/issues/332) | Canvas: renderizado compuesto + capa activa | 🟠 Alta | 🟠 Alta | **Bloqueado por #330/#331** — el bloque más grande; cambio de comportamiento a basado en capas, paridad de una sola capa |
| [#333](https://github.com/NikolayDA/picture_helper/issues/333) | Formato de archivo de proyecto: guardar/cargar (versionado, atómico, validado) | 🟠 Alta | 🟠 Alta | **Bloqueado por #330** (en paralelo a #332) — contenedor ZIP `.bgrproj`, atómico/validado/versionado |
| [#334](https://github.com/NikolayDA/picture_helper/issues/334) | UI: panel de capas + menú de proyecto + i18n | 🟠 Alta | 🟠 Alta | **Bloqueado por #330/#332/#333** — panel + acciones de menú, paridad i18n de/en |
| [#335](https://github.com/NikolayDA/picture_helper/issues/335) | Migración e integración (imagen→proyecto, recientes, ajustes, exportación) | 🟠 Alta | 🟡 Media | **Bloqueado por #330/#332/#333/#334** — issue de cierre del épico; sin regresiones en los flujos existentes |
| [#326](https://github.com/NikolayDA/picture_helper/issues/326) | Tests: el formato de entrada GIF está declarado pero sin test | 🟡 Media | 🟢 Baja | **Listo para PR, realizable ya** — un test de carga vía `ImageLoadWorker` cubre el gate `_ALLOWED_IMAGE_FORMATS` para GIF; sin guardado/exportación |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: respetar overrides de permisos a nivel de job en el WF reutilizable | 🟡 Media | 🟡 Media | **Necesita refinamiento** — primero confirmar la semántica de validación de arranque de GitHub (top-level vs. efectivo-por-job); actualmente es un falso positivo puramente teórico (no hay overrides a nivel de job en `ci.yml`), y el guard OIDC #303 no debe debilitarse |
| [#322](https://github.com/NikolayDA/picture_helper/issues/322) | CI: añadir una ruta de mantenimiento/skip para el Codex Security Scan programado | 🟡 Media | 🟡 Media | **Seguimiento de #245** — decisión de alcance interruptor manual vs. auto-skip elegante visible (vs. ambos); gate en el job `cadence`, "disabled → skipped, no failed", mantener mínimo privilegio (sin `issues: write` en el job de scan), test estático |
| [#323](https://github.com/NikolayDA/picture_helper/issues/323) | Tests: cubrir el sync de issues de seguridad para el filtro de severidad y findings vacíos | 🟢 Baja | 🟢 Baja | **Seguimiento de #245, realizable ya** — tests de regresión para `reportable: false`, el umbral de severidad y "No reportable findings"; sin red vía `--dry-run`/llamadas directas |
| [#324](https://github.com/NikolayDA/picture_helper/issues/324) | Security: test de gobernanza de docs para el prompt del Codex scan vs. alcance del repo | 🟢 Baja | 🟢 Baja | **Seguimiento de #245, realizable ya** — test estático de que el prompt sigue nombrando las superficies de seguridad de alto nivel actuales; complementa las assertions de prompt existentes |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Higiene de tests: asserts débiles/redundancias | 🟢 Baja | 🟢 Baja | Sin bug de corrección; lo de mayor valor primero (mover endpoint, consolidar `set_brush_size`), el resto según haga falta |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan falla con "Quota exceeded" | 🟡 Media | 🟢 Baja | **Bloqueado (externo):** restaurar la cuota en la cuenta. El endurecimiento del lado del repo se sigue en **#322–#324**; el skip elegante es la variante B de #322 |

### Issues Agrupables

- El épico de capas **#329** se trabaja a través de sus sub-issues en el orden prescrito; **#332** y **#333** pueden paralelizarse después de #330.
- **#323/#324** (ambos seguimientos de #245, tests estáticos sin red del security scan) pueden agruparse en un único PR.
- **#318** se queda separado — primero necesita la semántica de GitHub documentada antes de tocar `_required_permissions`.
- **#299** es higiene de tests oportunista y solo debería acompañar si ya se toca ese test.

### Orden de PRs Recomendado

1. **#330** — la piedra angular sin dependencias del épico de capas; desbloquea #331/#332/#333.
2. **#326** — victoria rápida y bien acotada (test de carga de GIF) que cierra un hueco de cobertura.
3. **#323 / #324** — endurecimiento sin red del security scan, realizable en cualquier momento.
4. **#331 → #332 / #333 → #334 → #335** — el épico de capas a lo largo de su cadena de dependencias.
5. **#322** — ruta de mantenimiento/skip tras una decisión deliberada auto/manual (seguimiento de #245).
6. **#318** — refinar el guard de permisos una vez documentada la semántica de GitHub, sin debilitar el caso de regresión OIDC.
7. **#245** — restaurar la cuota en la cuenta (bloqueado externamente).
8. **#299** — higiene de tests según haga falta.

## Rondas Anteriores

- **2026-06-01, "modest-shannon" (A–E)** — 5 hallazgos, todos hechos.
- **v2.2, "admiring-mayer" (#1–#15)** — lista externa, completada o descartada donde fue un falso positivo.

Hallazgos históricos y registros de trabajo completos (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).
