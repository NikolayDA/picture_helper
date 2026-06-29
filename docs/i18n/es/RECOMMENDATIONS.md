[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · **Español** · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Análisis de Código y Recomendaciones Priorizadas: BgRemover

## Escala de Prioridad

| Símbolo | Prioridad | Significado |
|---------|-----------|-------------|
| 🔴 | Crítica | Errores, cierres inesperados o pérdida de datos |
| 🟠 | Alta | Impacto claro en fiabilidad o mantenibilidad |
| 🟡 | Media | Mejora útil para calidad, legibilidad o testabilidad |
| 🟢 | Baja | Pulido opcional o mejora de proceso |

## Estado Actual (2026-06-29)

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
  bit el contrato de exportación #363. El seguimiento #397 (PR #398) hace pasar
  las vistas previas transitorias por la misma pipeline, respeta capas de datos
  ocultas y omite eficientemente el relieve con intensidad 0.
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

## Issues de GitHub Abiertos — Estado de Triage (2026-06-29, actualizado)

A 2026-06-29, GitHub muestra **8** issues abiertos: **#245**, **#299**, **#318**,
**#389**, **#392**, **#404**, **#406** y **#408**. Nuevo el mismo día es la
auditoría doc/código **#408** (docs de API/CLI frente a las firmas actuales — sin
drift); los issues de calidad/robustez **#406** y **#404** (nuevos desde la
revisión 2026-06-25) siguen abiertos. Los
paquetes de documentación **#390/#391**, el aviso de apertura **#357** y la
exclusión HEIC **#339** siguen cerrados; en el epic **#389** solo queda **#392**.

**Revisión de comentarios:** Sin comentarios externos nuevos; los de #392/#299/#245 son notas de triage del owner coherentes con el estado actual, y #408 es nuevo y sin comentarios.

**Hallazgos nuevos verificados contra el código:** #406 — `_derive_physical_size`
(`eufymake_export.py:217`) no tiene llamadas (`parse_size_mm` solo allí, además
en `project_model.py`). #404 — `compose_relief`/`compose_gloss`
(`canvas.py:555/564`) lanzan en vez de degradar a COLOR en la ruta de render.
#408 — auditoría sin hallazgos: las firmas de `CLAUDE.md`/`README.md` y la ruta CLI `bgremover imagen.png` coinciden con el código.

### Agrupaciones Recomendadas

- **Paquete release:** **#392** ya está listo; cerrar el epic **#389** tras
  verificar tag, release body y artefactos de macOS/Linux.
- **Victorias rápidas de calidad:** **#406** y **#404** son pequeños, autónomos
  y listos para PR — ideales como PRs de calidad cortos junto a la ruta de
  release, pero separados de ella (módulos distintos, sin diff compartido).
- No mezclar **#299/#318/#245** con la ruta de release: son trabajo de calidad,
  investigación y operación bloqueada externamente.

Evaluación: **Relevancia** = importancia para el roadmap/usuarios,
**Complejidad** = esfuerzo estimado de implementación.

| # | Título | Relevancia | Complejidad | Próximo paso recomendado |
|---|--------|------------|-------------|--------------------------|
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | Lanzar release v2.5.0 (CHANGELOG/versión/tag/artefactos) | 🟠 Alta | 🟡 Media | **Listo** – #390, #391 y #384 están cerrados. |
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | [Epic] Actualizar la documentación de usuario y lanzar release | 🟠 Alta | 🟢 Baja (restante) | **Casi completo** – solo queda #392. |
| [#404](https://github.com/NikolayDA/picture_helper/issues/404) | Vista previa: el desajuste de tamaño no degrada a COLOR | 🟡 Media | 🟢 Baja | **Listo para PR** – encapsular `compose_relief`/`compose_gloss` de forma defensiva y volver a `base` ante un desajuste de tamaño, con test de regresión de render/píxel. Latente pero bien acotado. |
| [#406](https://github.com/NikolayDA/picture_helper/issues/406) | Código muerto: `_derive_physical_size` sin uso en `eufymake_export.py` | 🟢 Baja | 🟢 Baja | **Listo para PR** – eliminar la función, limpiar el import de `parse_size_mm` y actualizar la frase de geometría en CLAUDE.md a la ruta `_derive_target`/modelo de proyecto. Trivial, con criterios de aceptación completos. |
| [#408](https://github.com/NikolayDA/picture_helper/issues/408) | Auditoría doc/código: las docs de API/CLI coinciden con las firmas (sin drift) | 🟢 Baja | 🟢 Baja | **Informativo / cerrable** – auditoría sin hallazgos, sin fix de código/doc necesario. Seguimiento opcional: un `docs/api.md` real vía autodoc para detectar drift futuro automáticamente. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Higiene de tests: aserciones débiles/redundancias | 🟢 Baja | 🟢 Baja | **Tras v2.5.0** – primero lazo, resultado NumPy escribible, máscara wand completa y parametrización brush. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: considerar overrides de permisos a nivel de job en el reusable WF | 🟢 Baja | 🟡 Media | **Necesita refinamiento** – probar primero la semántica; cambiar código solo ante un falso positivo demostrado y conservar #303. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan falla con "Quota exceeded" | 🟡 Media | 🟢 Baja | **Blocked (externo)** – el endurecimiento del repo vía #322/#342 (cerrado) está hecho; el bloqueo restante es la cuota de OpenAI/billing. Tras restaurarla, lanzar el scan programado manualmente una vez y cerrar. |

### Próximo recomendado (orden de PR)

1. Adelantar **#406** y **#404** como PRs de calidad cortos — ambos verificados,
   autónomos y listos para PR (módulos distintos, bajo riesgo).
2. Ejecutar **#392** después y cerrar el epic **#389** cuando tag, release body y
   ambos artefactos estén verificados.
3. Abordar **#299** tras v2.5.0; investigar **#318** solo (necesita refinamiento),
   cerrar **#408** como auditoría informativa sin acción y mantener **#245** bloqueado.

## Rondas Anteriores

- **2026-06-01, "modest-shannon" (A–E)** — 5 hallazgos, todos hechos.
- **v2.2, "admiring-mayer" (#1–#15)** — lista externa, completada o descartada donde fue un falso positivo.

Hallazgos históricos y registros de trabajo completos (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).
