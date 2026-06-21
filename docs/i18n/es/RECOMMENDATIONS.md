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

## Issues de GitHub Abiertos — Estado de Triage (2026-06-21)

A 2026-06-21, GitHub aún muestra **5** issues abiertos: **#245**, **#299**,
**#318**, **#322** y **#339**. Los issues de proyecto/capas y pruebas de
seguridad listados antes, **#323**, **#324**, **#326** y **#329–#335**, están
completados en los merge commits **#337**, **#338** y **#340**. **#322** ahora
también tiene **#342** y debería comentarse y cerrarse tras verificar el merge.

| # | Título | Recomendación de labels/estado | Propuesta de comentario/estado |
|---|--------|--------------------------------|--------------------------------|
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan falla con "Quota exceeded" | `security`; **mantener abierto / bloqueado externamente** | Comentar que el endurecimiento del repo queda cubierto por #323/#324 y #322/#342; el bloqueo restante es la cuota de OpenAI/billing. Tras restaurarla, lanzar el scan programado manualmente una vez y cerrar. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Higiene de tests: aserciones débiles/redundancias | `quality`, `testing`; **abierto / baja prioridad** | Comentar que no bloquea producto ni CI; agruparlo como limpieza oportunista cuando se toquen esos tests. Sin cambio de estado. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: considerar overrides de permisos a nivel de job en el reusable WF | `enhancement`, `testing`; **needs refinement** | Comentar que antes de cambiar código hay que documentar la semántica de GitHub para permisos top-level vs. job-level en el workflow llamado; no debilitar el guard OIDC #303. |
| [#322](https://github.com/NikolayDA/picture_helper/issues/322) | CI: ruta de mantenimiento/skip para el Codex Security Scan programado | `security`; **cerrar después de #342** | Comentar que #342 implementa el interruptor manual conservador (`CODEX_SECURITY_SCAN_ENABLED=false`) con salida de skip y tests de regresión; cerrar tras verificar el merge. |
| [#339](https://github.com/NikolayDA/picture_helper/issues/339) | HEIC/HEIF no está soportado como formato de entrada | **Añadir labels:** `enhancement`, `documentation` (o `question` si existe); **needs decision** | Comentar que se necesita una decisión de producto: documentar explícitamente que HEIC no está soportado, o planear `pillow-heif`/allowlist `HEIF` opcional con test de carga. Mantener abierto hasta decidir. |

### Acciones recomendadas para issues

1. Comentar y cerrar **#322** cuando se verifique el merge de #342 a `main`.
2. Etiquetar **#339** y tomar una decisión de producto explícita (aclaración de
   documentación vs. feature HEIC).
3. Mantener **#245** abierto pero marcado como bloqueado externamente; enlazar
   #322/#342 como parte de repo completada.
4. No implementar **#318** todavía; primero documentar la semántica de permisos
   de GitHub.
5. Mantener **#299** como cleanup de tests de baja prioridad.

## Rondas Anteriores

- **2026-06-01, "modest-shannon" (A–E)** — 5 hallazgos, todos hechos.
- **v2.2, "admiring-mayer" (#1–#15)** — lista externa, completada o descartada donde fue un falso positivo.

Hallazgos históricos y registros de trabajo completos (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).
