[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · **Español** · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Análisis de código y recomendaciones priorizadas: BgRemover

## Escala de valoración

| Símbolo | Prioridad | Significado |
|---------|-----------|-------------|
| 🔴 | Crítica | Errores, cierres inesperados o pérdida de datos |
| 🟠 | Alta | Impacto claro en la fiabilidad o el mantenimiento |
| 🟡 | Media | Mejora útil de calidad, legibilidad o testabilidad |
| 🟢 | Baja | Pulido opcional o mejora de proceso |

## Estado actual (2026-07-14)

La lista activa de análisis de código está vacía. Ruff, mypy y la suite de
pruebas local siguen siendo la base antes de nuevos PR. La versión **v2.5.0**
se publicó el 2026-07-11 (PR #538); la ola de rollout **#435/#392/#426/#389**
está cerrada, igual que **#299** (PR #539) con el seguimiento N13 **#541**
(PR #543), **#318** (PR #540) y la sincronización de instantánea **#542**.
Una auditoría del repositorio del 2026-07-12 abrió **#549–#553**;
**#552/#549/#553/#550** ya están cerrados vía PR #557–#560. El epic **#563**
(«comprobación de actualizaciones y gestión del modelo de IA», ocho
subincidencias **#564–#571**) quedó completamente implementado y cerrado el
2026-07-13 vía PR #573/#574 (**N14**). Estado en vivo: **2** incidencias
abiertas – #245, #551.

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
- **N14 — Epic #563 (actualizaciones de la app y gestión del modelo de IA)
  completamente cerrado:** lógica base de comprobación `app_update.py` (#564)
  y lógica base de estado del modelo `ai_model_status.py` (#568) – ambas sin
  Qt, estrictamente tipadas y en la lista mypy strict (PR #573). Integración
  de menú/diálogo «Buscar actualizaciones…»/«Gestionar modelo de IA…»
  (#565/#569, PR #573). Comprobación automática opcional al iniciar (#566) y
  conexión real de la descarga del modelo con el warmup existente, con
  múltiples observadores/cancelación cooperativa (#570, PR #574, incluidos
  tres arreglos de review Codex: separar on_success/on_finished, unir una
  comprobación manual a una comprobación de inicio en curso, protección de
  carrera al adjuntarse). Cierre de documentación
  (README/CLAUDE.md/CHANGELOG/RESOURCES/INSTALL_*, seis idiomas) vía
  #567/#571.

### Aún abierto

- **O8 🟢 — Imprecisión del prototipo:** las herramientas de altura quedan
  bloqueadas en el mockup tras generarla; solo afecta a la simulación (#347).

## Incidencias abiertas de GitHub — Clasificación (2026-07-14)

Estado en vivo: **2** incidencias abiertas – ambas son incidencias de CI/
seguridad preexistentes, sin cambios frente a la ronda anterior (el epic
#563 con sus ocho subincidencias ya quedó completamente cerrado).

### Agrupaciones sensatas

#245/#551 están vinculados (scan Codex: acción de cuenta vs. decisión
estratégica).

Valoración: **Relevancia** = importancia para la hoja de ruta/usuarios,
**Complejidad** = esfuerzo estimado, **Modelo/Esfuerzo** = modelo/esfuerzo recomendados.

| # | Título | Relevancia | Complejidad | Modelo/Esfuerzo | Próximo paso recomendado |
|---|--------|------------|-------------|------------------|---------------------------|
| [#551](https://github.com/NikolayDA/picture_helper/issues/551) | Decisión de estrategia para Codex Security Scan (reactivar/retirar/reemplazar) | 🟡 Media | 🟡 Media | Sonnet 5 · media | **Needs refinement** – elegir entre tres opciones; recomendación: opción 2 (retirar/deshabilitar) dado el bloqueo externo de semanas y la redundancia con pip-audit/license/CI. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan «Quota exceeded» | 🟡 Media | 🟢 Baja | – (sin tarea de código) | **Bloqueado (externo)** – restaurar la facturación/cuota de OpenAI es una acción de cuenta, no un PR. |

### Recomendado a continuación (orden de PR)

1. **#551** — decisión sobre la estrategia del scan (vinculada a #245), luego
   ajustar el workflow.
2. **#245** — sigue bloqueado externamente; verificar solo tras restaurar la
   cuota de OpenAI.

*Drift:* reconsultar el número de incidencias abiertas en vivo, sin
arrastrarlo (#542 → #549: mismo desfase).

## Rondas anteriores

- **2026-07-13 (cierre del epic)** — epic **#563** completamente cerrado:
  las ocho subincidencias (**#564–#571**) cerradas vía PR #573
  (#564/#565/#568/#569) y PR #574 (#566/#570 + cierre de documentación
  #567/#571). Instantánea reducida a 2 (#245, #551).
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
