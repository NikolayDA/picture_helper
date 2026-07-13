[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · **Español** · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Análisis de código y recomendaciones priorizadas: BgRemover

## Escala de valoración

| Símbolo | Prioridad | Significado |
|---------|-----------|-------------|
| 🔴 | Crítica | Errores, cierres inesperados o pérdida de datos |
| 🟠 | Alta | Impacto claro en la fiabilidad o el mantenimiento |
| 🟡 | Media | Mejora útil de calidad, legibilidad o testabilidad |
| 🟢 | Baja | Pulido opcional o mejora de proceso |

## Estado actual (2026-07-13)

La lista activa de análisis de código está vacía. Ruff, mypy y la suite de
pruebas local siguen siendo la base antes de nuevos PR. La versión **v2.5.0**
se publicó el 2026-07-11 (PR #538); la ola de rollout **#435/#392/#426/#389**
está cerrada, igual que **#299** (PR #539) con el seguimiento N13 **#541**
(PR #543), **#318** (PR #540) y la sincronización de instantánea **#542**.
Una auditoría del repositorio del 2026-07-12 abrió **#549–#553**;
**#552/#549/#553/#550** ya están cerrados vía PR #557–#560. Desde la última
instantánea (#245, #551), el 2026-07-13 se abrió el epic **#563**
(«comprobación de actualizaciones y gestión del modelo de IA») con ocho
subincidencias (**#564–#571**). Estado en vivo: **11** incidencias abiertas
– #245, #551, #563–#571.

### Completado desde la última revisión

- **Base antigua estable:** **N1/N2/N4/N5/N6/N7/N8** y **O2–O7** siguen
  hechos; los epics **#329/#344/#358/#384** (N9–N12) más la corrección de
  exportación **#363** fusionados/archivados. Desde el 2026-06-25 también
  **#404/#406/#408** (PR #412) cerrado.
- **Rediseño y publicación:** núcleo del rediseño/rail/zoom/inspector de
  tarjetas/Dark Mode/seguimiento de UI (**#413/#414/#455–#464/#474–#489/
  #499–#501/#503/#509/#510/#514–#517**, **#490**, **#433/#434**) vía
  PR #412–#522. Ola de publicación **#435/#392/#426/#389** (v2.5.0),
  **#299/#541/#318/#542**, plantilla de PR **#552**, sincronización **#549**,
  arreglo de SessionStart **#553**, formalización v2.3.0 **#550** – todo
  cerrado desde el 2026-07-12.

### Aún abierto

- **O8 🟢 — Imprecisión del prototipo:** las herramientas de altura quedan
  bloqueadas en el mockup tras generarla; solo afecta a la simulación (#347).

## Incidencias abiertas de GitHub — Clasificación (2026-07-13)

Estado en vivo: **11** incidencias abiertas – dos incidencias de CI/
seguridad preexistentes (**#245**, **#551**) más el epic **#563** con ocho
subincidencias (**#564–#571**) para dos grupos independientes: comprobación
de actualizaciones (#564–#567) y gestión del modelo de IA (#568–#571). Se
revisaron todos los comentarios – las notas de clasificación del propietario
del 2026-07-13 ya cubren orden/alcance; ninguna descripción de incidencia
necesitó edición.

### Agrupaciones sensatas

#245/#551 están vinculados (scan Codex: acción de cuenta vs. decisión
estratégica). Las ocho subincidencias de #563 forman dos cadenas
internamente secuenciales pero mutuamente independientes: **comprobación de
actualizaciones** (#564→#565→#566→#567) y **descarga del modelo de IA**
(#568→#569→#570→#571) – confirmado por el autor el 2026-07-13 (comentarios
en #563/#569/#570).

Valoración: **Relevancia** = importancia para la hoja de ruta/usuarios,
**Complejidad** = esfuerzo estimado, **Modelo/Esfuerzo** = modelo/esfuerzo recomendados.

| # | Título | Relevancia | Complejidad | Modelo/Esfuerzo | Próximo paso recomendado |
|---|--------|------------|-------------|------------------|---------------------------|
| [#563](https://github.com/NikolayDA/picture_helper/issues/563) | Epic: ampliación de menú, actualizaciones de la app y gestión del modelo de IA | 🟠 Alta | 🟠 Alta (8 subincidencias) | – (solo seguimiento) | **Blocked (on sub-issues)** – se cierra con #564–#571; orden en el comentario del propietario del 2026-07-13. |
| [#564](https://github.com/NikolayDA/picture_helper/issues/564) | Actualizaciones de la app: lógica base de comprobación (`app_update.py`) | 🟠 Alta | 🟢 Baja (tamaño S, sin dependencias) | Sonnet 5 · baja–media | **Ready for PR** – sin Qt, estrictamente tipado, criterios de aceptación claros. |
| [#565](https://github.com/NikolayDA/picture_helper/issues/565) | Actualizaciones de la app: integración de menú/diálogo «Buscar actualizaciones…» | 🟠 Alta | 🟡 Media (tamaño S–M, QThread async + i18n) | Sonnet 5 · media | **Needs #564** – listo para PR justo después. |
| [#566](https://github.com/NikolayDA/picture_helper/issues/566) | Actualizaciones de la app: comprobación automática opcional al iniciar | 🟡 Media | 🟢 Baja (tamaño S) | Sonnet 5 · baja | **Needs #564+#565**. |
| [#567](https://github.com/NikolayDA/picture_helper/issues/567) | Actualizaciones de la app: cierre de documentación + gobernanza i18n | 🟢 Baja | 🟢 Baja (tamaño XS) | Sonnet 5 · baja | **Needs #564–#566 mergeados**. |
| [#568](https://github.com/NikolayDA/picture_helper/issues/568) | Descarga del modelo de IA: detección de estado (sin Qt) | 🟠 Alta | 🟢 Baja (tamaño S, sin dependencias) | Sonnet 5 · baja–media | **Ready for PR** – sin Qt, estrictamente tipado, criterios de aceptación claros. |
| [#569](https://github.com/NikolayDA/picture_helper/issues/569) | Descarga del modelo de IA: integración de menú/diálogo «Gestionar modelo de IA…» | 🟠 Alta | 🟡 Media (tamaño M, diálogo+progreso+cancelación simulados) | Sonnet 5 · media | **Needs #568** – ruta simulada basta (aclaración de alcance 2026-07-13). |
| [#570](https://github.com/NikolayDA/picture_helper/issues/570) | Descarga del modelo de IA: conexión con el warmup/WorkerController existente | 🟠 Alta | 🟡 Media–Alta (tamaño S–M, requiere nuevo hook `cancel_warmup()`) | Sonnet 5 · media–alta | **Needs #568+#569**. |
| [#571](https://github.com/NikolayDA/picture_helper/issues/571) | Descarga del modelo de IA: cierre de documentación + gobernanza i18n | 🟢 Baja | 🟢 Baja (tamaño XS) | Sonnet 5 · baja | **Needs #568–#570 mergeados**. |
| [#551](https://github.com/NikolayDA/picture_helper/issues/551) | Decisión de estrategia para Codex Security Scan (reactivar/retirar/reemplazar) | 🟡 Media | 🟡 Media | Sonnet 5 · media | **Needs refinement** – elegir entre tres opciones; recomendación: opción 2 (retirar/deshabilitar) dado el bloqueo externo de semanas y la redundancia con pip-audit/license/CI. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan «Quota exceeded» | 🟡 Media | 🟢 Baja | – (sin tarea de código) | **Bloqueado (externo)** – restaurar la facturación/cuota de OpenAI es una acción de cuenta, no un PR. |

### Recomendado a continuación (orden de PR)

1. **#564+#568** — lógica base sin Qt primero y en paralelo (independientes,
   listas para PR).
2. **#565+#569** — integración de menú/diálogo por grupo tras fusionar la
   lógica base (ruta simulada basta).
3. **#566+#570** — comprobación al iniciar / conexión con el warmup; #570
   necesita además el nuevo hook `cancel_warmup()` (comentario 2026-07-13).
4. **#567+#571** — cierre de documentación por grupo (XS, trivial).
5. **#551** — decisión sobre la estrategia del scan (vinculada a #245), luego
   ajustar el workflow.
6. **#245** — sigue bloqueado externamente; verificar solo tras restaurar la
   cuota de OpenAI.

*Drift:* reconsultar el número de incidencias abiertas en vivo, sin
arrastrarlo (#542 → #549: mismo desfase).

## Rondas anteriores

- **2026-07-13 (auditoría de issues)** — epic **#563** + ocho subincidencias
  (**#564–#571**) abiertas; las 11 incidencias abiertas reevaluadas,
  comentarios del propietario considerados. Ninguna cerrada. Recomendación:
  #564/#568 primero. Instantánea actualizada a 11.
- **2026-07-12** — formalización v2.3.0 (**#550**), arreglo del hook
  SessionStart (**#553**), sincronización (**#549**, plantilla **#552** vía
  PR #557), auditoría (**#542** cerrado, #549–#553 abiertas) y versión
  **v2.5.0** (ola #435/#392/#426/#389, #299/#541/#318) – reducida a 2.
- **2026-07-11** — epic #425 completado (#430 PR #526, i18n ES/FR/UK/ZH
  completa, O1 hecho; #431/#432 PR #529; seguimiento final #530/#531
  PR #533/#535).
- **2026-07-05–10** — #509/#510/#514–#517 (PR #520–#522), #490, ola de Dark
  Mode/iconos rail, inspector de tarjetas (#413/#414), #499–#501/#503, pulido
  de iconos/barra de estado.
- **2026-06-29** — #404/#406/#408 completados (PR #412), rediseño abierto.
- **v2.2, «admiring-mayer» (#1–#15)** — lista externa, completada o
  descartada donde era un falso positivo.

Hallazgos históricos y registros de trabajo (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).
