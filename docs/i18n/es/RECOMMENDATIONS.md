[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · **Español** · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Análisis de código y recomendaciones priorizadas: BgRemover

## Escala de valoración

| Símbolo | Prioridad | Significado |
|---------|-----------|-------------|
| 🔴 | Crítica | Errores, cierres inesperados o pérdida de datos |
| 🟠 | Alta | Impacto claro en la fiabilidad o el mantenimiento |
| 🟡 | Media | Mejora útil de calidad, legibilidad o testabilidad |
| 🟢 | Baja | Pulido opcional o mejora de proceso |

## Estado actual (2026-07-22, corregido tras la revisión de Codex)

Ruff, mypy y la suite de pruebas local siguen siendo la base antes de nuevos PR. Desde la última ronda, **#640–#645** y **#648** se han cerrado. Una versión anterior de esta actualización se apoyaba únicamente en el despacho de `release-abnahme.yml` del 2026-07-21 (commit `fa2241d`) y calificaba erróneamente la fila de visión (#656) como el único bloqueo de la cadena — una revisión del PR (Codex) refutó cuatro puntos de eso, corregidos aquí:

1. **La evidencia del despacho ya estaba desactualizada.** El PR #657 (resuelve #642, fusionado en `521bd63`, después de `fa2241d`) convierte `waechter_ergebnisse` en campo obligatorio en `abnahme_aggregate.py::validate_evidence`, y el PR #658 (resuelve #644, fusionado en `4416e80`) añade comprobaciones E2E que faltaban. El despacho citado se ejecutó **antes** de ambos arreglos, así que sus filas "✅ cumplido" no evidencian el código actual. Se necesita un despacho nuevo contra el `main` actual antes de poder citar la matriz como prueba válida.
2. **La evaluación previa por visión es consultiva, no un bloqueo.** `abnahme_aggregate.py::has_blocking_gaps` exime explícitamente solo a la fila "Screenshots (evaluación previa por visión)" de bloquear cuando está `sin evaluar` (`docs/RELEASE_AUTOMATION.md` §4: "sin `ANTHROPIC_API_KEY`, todo criterio permanece sin evaluar y nunca bloquea"). **#656** es una mejora valiosa de la calidad de la evidencia, pero **no** es un bloqueo para #646, #639, #595 ni #582.
3. **Linux x86_64 sigue siendo un criterio abierto, no solo pausado.** Según el ADR/`RELEASE_AUTOMATION.md` §5, el smoke de hardware x86_64 pausado se trata explícitamente como "declarado abierto, no cumplido" para las decisiones de publicación — un punto deliberadamente aceptado pero aún abierto, no una fila completada.
4. **Ningún epic se cierra automáticamente.** Cerrar #646 solo actualiza el progreso de incidencias secundarias de #639 en GitHub; #639, #595 y #582 deben revisarse y cerrarse manualmente cada uno por separado.

Estado en vivo: **6** incidencias abiertas.

### Resultado de la revisión

- **Base antigua estable:** **N1/N2/N4/N5/N6/N7/N8**, **O1–O7** y todo lo completado desde el **2026-06-25** sigue hecho.
- El epic **#639** tiene 7 de sus 8 incidencias secundarias resueltas; la lista de verificación del cuerpo de la incidencia seguía con todas las casillas sin marcar aunque #640–#645/#648 llevaban tiempo cerradas — conciliado (comentario + edición del cuerpo en #639); esa edición del cuerpo también sobrestimó la evidencia del despacho y se corrige mediante un comentario de seguimiento.
- **Ninguna incidencia califica actualmente como "lista para PR"** en el sentido clásico: las seis incidencias abiertas restantes son tareas puramente externas/operativas (configurar un secreto, resolver facturación) o epics que en el fondo esperan un despacho de aceptación nuevo y válido más la pausa documentada de x86_64.
- El paso real que queda **no** es un secreto ausente — es un despacho nuevo de `release-abnahme.yml` contra el `main` actual (tras #657/#658), cuya matriz debe entonces contrastarse con los criterios de #595, incluida la fila de x86_64 deliberadamente abierta.

## Incidencias abiertas de GitHub — Clasificación (2026-07-22)

| # | Título | Relevancia | Complejidad | Modelo recomendado (esfuerzo) | Próximo paso |
|---|--------|------------|-------------|--------------------------------|--------------|
| [#646](https://github.com/NikolayDA/picture_helper/issues/646) | Evaluación previa por visión, agregación de evidencia, matriz de aceptación | 🟠 Alta (última incidencia secundaria abierta del epic #639) | 🟢 Baja (código/pruebas ya fusionados en PR #647/#649/#657) | Sonnet 5 (bajo) – solo verificación contra un despacho nuevo, no se espera código nuevo | Necesita verificación – sus propios criterios de aceptación **no** dependen de #656 (el fail-safe de visión ya está evidenciado); cerrar tras un despacho nuevo |
| [#639](https://github.com/NikolayDA/picture_helper/issues/639) | [Epic] Aceptación automatizada de releases | 🟠 Alta (epic, 7/8 incidencias secundarias hechas) | 🟢 Baja (solo queda #646) | – (epic, sin uso directo de agente) | Bloqueada – **no** se cierra automáticamente con #646; revisar y cerrar manualmente cuando #646 esté hecho |
| [#595](https://github.com/NikolayDA/picture_helper/issues/595) | [3D] Rendimiento, empaquetado, documentación, aceptación end-to-end | 🟠 Alta (puerta de aceptación del epic #582) | 🟡 Media (la visión está satisfecha de forma consultiva, pero el criterio x86_64 sigue declarado abierto) | – (sin tarea de código) | Bloqueada – espera un despacho nuevo y válido tras #657/#658 y una decisión explícita sobre la pausa de x86_64 |
| [#582](https://github.com/NikolayDA/picture_helper/issues/582) | [Epic] Vista previa de relieve 3D real | 🟠 Alta (epic grande, casi terminado) | 🟢 Baja (solo queda #595) | – (epic, sin uso directo de agente) | Bloqueada – **no** se cierra automáticamente con #595; revisar y cerrar manualmente después |
| [#656](https://github.com/NikolayDA/picture_helper/issues/656) | Activar el secreto ANTHROPIC_API_KEY para la evaluación previa por visión | 🟡 Media (solo mejora la calidad de la evidencia; no es un bloqueo según el contrato) | 🟢 Baja (puramente operativo, sin código) | – (sin agente; propietario del repo: Settings → Secrets) | Bloqueada (externa) – se puede hacer con independencia del resto de la cadena |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restaurar la cuota de OpenAI para la comprobación manual de Codex Security | 🟢 Baja (solo bloquea un escaneo manual opcional) | 🟢 Baja (puramente operativo, sin código) | – (sin agente; propietario del repo: facturación) | Bloqueada (externa) – resolver facturación/cuota en el proyecto de la plataforma OpenAI |

### Recomendado a continuación

1. Lanzar un despacho nuevo de `release-abnahme.yml` contra el `main` actual (tras #657/#658) — la matriz del 2026-07-21 citada previamente ya no evidencia el código actual.
2. Comprobar la nueva matriz contra **todos** los criterios de #595, incluida la fila x86_64 deliberadamente abierta (sigue "pausada/declarada abierta" aunque todo lo demás esté en verde) — aclarar explícitamente si #595 puede cerrarse con una pausa x86_64 documentada (como ya permite #639 para sí mismo) o necesita una aprobación aparte.
3. Comprobar **#646** contra sus propios criterios de aceptación (el comportamiento fail-safe ya está evidenciado y no depende de #656) y cerrarlo si se cumplen; después revisar y cerrar **#639** por separado y de forma manual, seguido de **#595** y **#582** — ninguna incidencia se cierra automáticamente con otra.
4. Gestionar **#656** de forma independiente si se desean veredictos de visión reales — es una mejora de calidad, no un bloqueo.
5. Dejar **#245** como tracker puramente externo de facturación/cuota; no hay ninguna acción posible ni necesaria en el repositorio.
6. Actualmente **no** hay ninguna incidencia abierta que justifique un nuevo PR de código — la siguiente tarea sensata para un agente es la verificación tras un despacho nuevo, no una nueva implementación.

## Rondas anteriores

- **2026-07-22 (revisión de incidencias, corregida tras revisión de Codex)** — reevaluación completa de todas las incidencias abiertas; una versión anterior sobrestimó lo que probaba el despacho del 2026-07-21 (desde entonces superado por los PR #657/#658) y calificó erróneamente la fila consultiva de visión (#656) como un bloqueo. Corregido tras la revisión del PR (Codex): #656 puede resolverse de forma independiente, Linux x86_64 sigue siendo un criterio declarado abierto, y #639/#595/#582 no se cierran automáticamente con sus incidencias secundarias. Estado en vivo: 6 incidencias abiertas — el nivel más bajo desde el epic #582.
- **2026-07-21 (automatización de aceptación de releases, epic #639)** — el epic #639 se abrió y se implementó en gran parte en un solo día: ADR/documentación (#640), esqueleto del workflow (#641), smokes de hardware Linux/macOS (#642/#643), prueba de regresión E2E (#644), suite de rendimiento con GL en vivo (#645), evaluación previa por visión + matriz de aceptación (#646) — todo fusionado mediante PR #647/#649 pero sin cierre automático debido a palabras clave de cierre en alemán; la incidencia de seguimiento #648 (prueba nativa de renderizado 3D del artefacto empaquetado) sigue siendo la única tarea de código abierta. Estado en vivo: 12 incidencias abiertas.
- **2026-07-20 (smoke de hardware en la Pi 5)** — se encontraron y corrigieron tres errores reales de empaquetado en la Raspberry Pi 5 (PR #627/#631); se confirmó que la app arranca, incluida la vista previa 3D.
- **2026-07-18 (auditoría posterior al merge)** — #551 y #592–#594 confirmados; #582/#595 reabiertos por pruebas pendientes; estado en vivo 3.
- **2026-07-18 (seguimiento de auditoría #614–#616)** — registrada la protección frente a versiones futuras de PR #614; #597/#598 completadas mediante PR #615 y #606 mediante PR #616; estado en vivo 7.
- **2026-07-17 (cierre del epic de 16 bits)** — #581/#587–#590 completados mediante PR #610/#612/#613; todos los gates y reviews verdes, matriz de aceptación presente, estado en vivo 10.
- **2026-07-16 (release v2.6.0)** — tag sobre `f24cef69829da8e37aa400dad471dc4d607b89b3`, ejecución 29531147950 verde, cinco artefactos públicos descargados de nuevo y verificados por SHA-256; #580/#585/#607 cerrados, estado en vivo 15.
- **2026-07-16 (gate del candidato)** — #584 cerrado mediante el gate real de cinco artefactos (ejecución final 29529595934 sobre `f24cef69829da8e37aa400dad471dc4d607b89b3`, SHA-256 + escaneo de secretos por artefacto, smokes de plataforma nativos); #585 desbloqueado.
- **2026-07-15/16 (seguimiento de auditoría)** — #583/#586/#591 completados; #584 reabierto al confirmar que el gate del candidato sigue pendiente; estado en vivo 17.
- **2026-07-14** — estado en vivo aún con 2 incidencias abiertas (#245, #551), sin cambios desde el cierre del epic del día anterior.
- **2026-07-13 (cierre del epic)** — epic **#563** completamente cerrado: las ocho subincidencias (**#564–#571**) cerradas vía PR #573/#574; instantánea reducida a 2.
- **2026-07-13 (auditoría de issues)** — epic **#563** + ocho subincidencias abiertas, las 11 incidencias abiertas reevaluadas, comentarios del propietario considerados; ninguna cerrada; instantánea actualizada a 11.
- **2026-07-12** — formalización v2.3.0 (#550), arreglo del hook SessionStart (#553), sincronización (#549, plantilla de PR #552 vía PR #557), auditoría (#542 cerrado, #549–#553 abiertas) y versión **v2.5.0** (ola #435/#392/#426/#389, #299/#541/#318).
- **2026-07-11** — epic #425 completado (#430 PR #526, i18n en tiempo de ejecución ES/FR/UK/ZH completa, **O1** hecho; #431/#432 PR #529; seguimiento final #530/#531 PR #533/#535).
- **2026-07-05–10** — #509/#510/#514–#517 (PR #520–#522), #490, ola de Dark Mode/iconos rail, inspector de tarjetas (#413/#414), #499–#501/#503, pulido de iconos/barra de estado.
- **2026-06-29** — #404/#406/#408 completados (PR #412), rediseño abierto.
- **v2.2, «admiring-mayer» (#1–#15)** — lista externa, completada o descartada donde era un falso positivo.

Hallazgos históricos y registros de trabajo (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).
