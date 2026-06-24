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
- Los hallazgos cerrados anteriores (incl. el epic EufyMake **#351**/**#352–#355**
  y el subproceso rembg/ONNX **#270**/**#285**/**#286**) están hechos en los PRs
  documentados, cubiertos por tests/CI y archivados.

- **N9 ✅ — Modelo de datos de proyecto/capas (epic #329) entregado.** Modelo de
  dominio sin Qt (#330), historial con reconocimiento de capas (#331), lienzo de
  composición (#332), formato `.bgrproj` (#333), panel de capas/menú de proyecto
  (#334) y migración/integración (#335) — paridad de imagen única conservada,
  `make check`/`make ui` en verde.
- **N10 ✅ — Espacio de trabajo Height Map (epic #344) entregado.** Representación
  de altura y vista 2D sin Qt (#345), generación/importación (#346), edición
  (#347), optimización `height_ops` con vista previa (#348) y pestaña contextual
  de altura (#349).
- **N11 ✅ — Pulido de fase 0 (epic #358) entregado.** Redimensionado del proyecto
  (#359), brillo/contraste/saturación conservando alfa (#360) y feather del borde
  alfa limitado por selección (#361), con undo/redo y persistencia `.bgrproj`.
- **N12 ✅ — Vista previa 2D combinada (epic #384) entregada.** Renderizadores de
  relieve/gloss sin Qt (#385/#386), modos explícitos e independientes de la capa
  activa con caché acotada (#387), y menú Ver/panel Vista previa sincronizados con
  intensidad en vivo y toggle de gloss (#388); la matriz modo×capa conserva bit a
  bit el contrato de exportación #363.
- **#363 ✅ — Regresión de exportación corregida (PR #367).** Guardar imagen
  vuelve a escribir el compuesto COLOR sin importar la capa activa; el renderizado
  de pantalla y el de exportación están separados, cubiertos por un test de
  regresión de píxeles.

### Aún Abierto

- **O1 🟠 — Idiomas runtime adicionales.** Alemán e inglés son seleccionables
  en la app. Los idiomas de documentación es/fr/uk/zh aún no son runtime
  locales; añadirlos clave por clave en `bgremover.i18n` y cubrirlos con tests.
- **O7 ✅ — Subproceso para rembg/ONNX hecho (PR #283, issue #270 cerrado).** La
  inferencia de IA no interrumpible ahora corre en un proceso iniciado con
  `spawn` (`ai_process.py`); `QThread.terminate()` como salida de emergencia de
  IA ha desaparecido. Los hallazgos de seguimiento de robustez/memoria están
  corregidos y cerrados en **#285** (PR #289).

## Issues de GitHub Abiertos — Estado de Triage (2026-06-24, actualizado)

A 2026-06-24, tras completar #384/#387/#388, GitHub muestra **9** issues
abiertos. Los epics **#375** (salida física mm/DPI + validación de exportación) y
**#384** (vista previa 2D combinada) están completos y cerrados. El epic de roadmap
restante es:

- **#389 – Actualizar la documentación de usuario y lanzar la release v2.5.0** con
  sub-issues **#390** (la guía de usuario ANLEITUNG, 6 idiomas — también cierra
  **#357**), **#391** (README + capturas + i18n) y **#392** (release v2.5.0).

Los huecos de documentación **#357** (ahora cubierto por #390) y **#339** más los
hallazgos de test/CI **#318**, **#299** y **#245** siguen abiertos.

**Revisión de comentarios (2026-06-24):** Los comentarios en **#245**, **#299** y
**#339** vienen todos del maintainer (triage) y confirman el estado documentado:
#245 sigue bloqueado externamente por cuota/billing, #299 sigue siendo higiene de
tests de baja prioridad, y #339 está confirmado como una exclusión deliberada de
HEIC. Ningún comentario requiere una actualización sustancial; no hacen falta
nuevos issues de seguimiento.

Evaluación: **Relevancia** = importancia para el roadmap/usuarios,
**Complejidad** = esfuerzo estimado de implementación.

| # | Título | Relevancia | Complejidad | Próximo paso recomendado |
|---|--------|------------|-------------|--------------------------|
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | [Epic] Actualizar la documentación de usuario y lanzar release | 🟠 Alta | 🟡 Media (epic) | **En progreso (epic)** – #390/#391 en paralelo → #392. |
| [#390](https://github.com/NikolayDA/picture_helper/issues/390) | Actualizar la guía de usuario ANLEITUNG (+ 5 i18n) para las nuevas funciones | 🟠 Alta | 🔴 Alta (L, 6 idiomas) | **Ready for PR** – bien acotado pero grande; también cierra **#357**. |
| [#391](https://github.com/NikolayDA/picture_helper/issues/391) | Actualizar README + capturas + i18n | 🟡 Media–Alta | 🟡 Media | **Ready for PR (con salvedad)** – la parte de texto es inmediatamente abordable; las capturas necesitan una ejecución actual de la app. |
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | Lanzar release v2.5.0 (CHANGELOG/versión/tag/artefactos) | 🟠 Alta | 🟡 Media | **Blocked** – necesita #390 + #391. |
| [#357](https://github.com/NikolayDA/picture_helper/issues/357) | Docs: falta apertura por ruta inicial/Finder en ANLEITUNG §4 | 🟢 Baja | 🟢 Baja | **Fusionado en #390** – aún posible como pequeño PR independiente, pero normalmente se cerrará junto con #390. |
| [#339](https://github.com/NikolayDA/picture_helper/issues/339) | HEIC/HEIF no está soportado como formato de entrada | 🟢 Baja | 🟢 Baja | **Ready for PR (docs)** – HEIC excluido deliberadamente (comentario 2026-06-21). Solo aclarar README/ANLEITUNG, luego cerrar. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Higiene de tests: aserciones débiles/redundancias | 🟢 Baja | 🟢 Baja | **Ready for PR (oportunista)** – no bloquea producto ni CI; lo de mayor valor primero (asertar el endpoint del lazo, la línea de `test_helpers`, consolidar los tests de `set_brush_size`). |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: considerar overrides de permisos a nivel de job en el reusable WF | 🟢 Baja | 🟡 Media | **Needs refinement** – primero documentar la semántica de GitHub (top-level vs. efectivo-por-job); no debilitar el guard OIDC #303. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan falla con "Quota exceeded" | 🟡 Media | 🟢 Baja | **Blocked (externo)** – el endurecimiento del repo vía #322/#342 (cerrado) está hecho; el bloqueo restante es la cuota de OpenAI/billing. Tras restaurarla, lanzar el scan programado manualmente una vez y cerrar. |

### Próximo recomendado (orden de PR)

1. Integrar **#390** y **#391** en paralelo como PRs de docs (también cierra
   **#357**); encajar **#339** como un pequeño PR independiente.
2. Lanzar **#392** (release v2.5.0) solo tras #390/#391.
3. Limpiar **#299** oportunísticamente; aplazar **#318** hasta evidenciar la
   semántica y mantener **#245** bloqueado externamente.

## Rondas Anteriores

- **2026-06-01, "modest-shannon" (A–E)** — 5 hallazgos, todos hechos.
- **v2.2, "admiring-mayer" (#1–#15)** — lista externa, completada o descartada donde fue un falso positivo.

Hallazgos históricos y registros de trabajo completos (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).
