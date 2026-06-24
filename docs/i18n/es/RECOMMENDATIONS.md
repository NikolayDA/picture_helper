[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · **Español** · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Análisis de Código y Recomendaciones Priorizadas: BgRemover

## Escala de Prioridad

| Símbolo | Prioridad | Significado |
|---------|-----------|-------------|
| 🔴 | Crítica | Errores, cierres inesperados o pérdida de datos |
| 🟠 | Alta | Impacto claro en fiabilidad o mantenibilidad |
| 🟡 | Media | Mejora útil para calidad, legibilidad o testabilidad |
| 🟢 | Baja | Pulido opcional o mejora de proceso |

## Estado Actual (2026-06-24)

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

## Issues de GitHub Abiertos — Estado de Triage (2026-06-24, actualizado)

A 2026-06-24, tras #384/#387/#388 y el seguimiento P2 **#397** (PR #398),
GitHub muestra **9** issues abiertos. Los epics **#375** (salida física mm/DPI +
validación de exportación) y **#384** (vista previa 2D combinada) están completos
y cerrados. El epic de roadmap restante es:

- **#389 – Actualizar la documentación de usuario y lanzar la release v2.5.0** con
  sub-issues **#390** (la guía de usuario ANLEITUNG, 6 idiomas — también cierra
  **#357**), **#391** (README + capturas + i18n) y **#392** (release v2.5.0).

Los huecos de documentación **#357** (ahora cubierto por #390) y **#339** más los
hallazgos de test/CI **#318**, **#299** y **#245** siguen abiertos.

**Revisión de comentarios (2026-06-24):** El maintainer confirma que #245 sigue
bloqueado por cuota/billing, #299 es higiene de tests de baja prioridad y #339
es una exclusión HEIC deliberada. No hace falta actualizar esos issues; #397 ya
está cerrado por PR #398.

### Agrupaciones Recomendadas

- **Paquete de guía:** **#390 + #357** y la parte ANLEITUNG de **#339**.
- **Paquete README:** **#391**, la parte README de **#339** y capturas actuales.
- **Paquete release:** mantener **#392** separado y empezarlo tras ambos PRs de docs.
- No mezclar **#299/#318/#245** con la ruta de release: son trabajo de calidad,
  investigación y operación bloqueada externamente.

Evaluación: **Relevancia** = importancia para el roadmap/usuarios,
**Complejidad** = esfuerzo estimado de implementación.

| # | Título | Relevancia | Complejidad | Próximo paso recomendado |
|---|--------|------------|-------------|--------------------------|
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | [Epic] Actualizar la documentación de usuario y lanzar release | 🟠 Alta | 🟡 Media (epic) | **Listo para empezar** – dos paquetes de docs en paralelo, luego #392. |
| [#390](https://github.com/NikolayDA/picture_helper/issues/390) | Actualizar la guía de usuario ANLEITUNG (+ 5 i18n) para las nuevas funciones | 🟠 Alta | 🔴 Alta (L, 6 idiomas) | **Paquete A** – incluir **#357** y la parte ANLEITUNG de **#339**. |
| [#391](https://github.com/NikolayDA/picture_helper/issues/391) | Actualizar README + capturas + i18n | 🟡 Media–Alta | 🟡 Media | **Paquete B** – incluir la parte README de **#339** y capturas actuales. |
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | Lanzar release v2.5.0 (CHANGELOG/versión/tag/artefactos) | 🟠 Alta | 🟡 Media | **Blocked** – necesita #390 + #391. |
| [#357](https://github.com/NikolayDA/picture_helper/issues/357) | Docs: falta apertura por ruta inicial/Finder en ANLEITUNG §4 | 🟢 Baja | 🟢 Baja | **Parte del paquete A** – no tratar por separado; cerrar con #390. |
| [#339](https://github.com/NikolayDA/picture_helper/issues/339) | HEIC/HEIF no está soportado como formato de entrada | 🟢 Baja | 🟢 Baja | **Dividir entre A/B** – ANLEITUNG en #390 y README en #391; cerrar tras ambos. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Higiene de tests: aserciones débiles/redundancias | 🟢 Baja | 🟢 Baja | **Tras v2.5.0** – primero lazo, resultado NumPy escribible, máscara wand completa y parametrización brush. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: considerar overrides de permisos a nivel de job en el reusable WF | 🟢 Baja | 🟡 Media | **Investigación paralela** – probar primero la semántica; cambiar código solo ante un falso positivo demostrado y conservar #303. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan falla con "Quota exceeded" | 🟡 Media | 🟢 Baja | **Blocked (externo)** – el endurecimiento del repo vía #322/#342 (cerrado) está hecho; el bloqueo restante es la cuota de OpenAI/billing. Tras restaurarla, lanzar el scan programado manualmente una vez y cerrar. |

### Próximo recomendado (orden de PR)

1. Entregar en paralelo el **paquete A (#390 + #357 + parte ANLEITUNG de #339)**
   y el **paquete B (#391 + parte README de #339)**; cerrar #339 tras ambos.
2. Ejecutar **#392** después y cerrar el epic **#389** cuando tag, release body y
   ambos artefactos estén verificados.
3. Abordar **#299** tras v2.5.0; investigar **#318** en paralelo sin codificar sin
   evidencia y mantener **#245** bloqueado hasta recuperar la cuota externa.

## Rondas Anteriores

- **2026-06-01, "modest-shannon" (A–E)** — 5 hallazgos, todos hechos.
- **v2.2, "admiring-mayer" (#1–#15)** — lista externa, completada o descartada donde fue un falso positivo.

Hallazgos históricos y registros de trabajo completos (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).
