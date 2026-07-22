[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · **Español** · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Análisis de código y recomendaciones priorizadas: BgRemover

## Escala de valoración

| Símbolo | Prioridad | Significado |
|---------|-----------|-------------|
| 🔴 | Crítica | Errores, cierres inesperados o pérdida de datos |
| 🟠 | Alta | Impacto claro en la fiabilidad o el mantenimiento |
| 🟡 | Media | Mejora útil de calidad, legibilidad o testabilidad |
| 🟢 | Baja | Pulido opcional o mejora de proceso |

## Estado actual (2026-07-22)

Ruff, mypy y la suite de pruebas local siguen siendo la base antes de nuevos PR. Desde la última ronda, **#640–#645** y **#648** se han aceptado y cerrado por completo (evidencia de hardware del despacho de `release-abnahme.yml` del 2026-07-21; el comentario de matriz de aceptación en #595 muestra los smokes de macOS-arm64 y Pi-5, el E2E 3D nativo y el rendimiento GL en vivo todos **✅ cumplidos**). Estado en vivo: **6** incidencias abiertas — el nivel más bajo desde que comenzó el epic 3D.

### Resultado de la revisión

- **Base antigua estable:** **N1/N2/N4/N5/N6/N7/N8**, **O1–O7** y todo lo completado desde el **2026-06-25** sigue hecho.
- El epic **#639** tiene 7 de sus 8 incidencias secundarias resueltas; la lista de verificación del cuerpo de la incidencia seguía con todas las casillas sin marcar aunque #640–#645/#648 llevaban tiempo cerradas — conciliado hoy (comentario + edición del cuerpo en #639), sin afectar código.
- **Ninguna incidencia califica actualmente como "lista para PR"** en el sentido clásico: las seis incidencias abiertas restantes son tareas puramente externas/operativas (configurar un secreto, resolver facturación) o epics bloqueados exclusivamente por esas mismas tareas externas. No hay ninguna tarea abierta sin atender en el lado del código.
- El único bloqueo restante de toda la cadena: falta el secreto del repositorio `ANTHROPIC_API_KEY` (**#656**), por lo que la fila de la matriz de aceptación "Screenshots (evaluación previa por visión)" sigue mostrando `❓ sin evaluar` en lugar de veredictos reales. El camino a prueba de fallos en sí funciona exactamente como se diseñó.

## Incidencias abiertas de GitHub — Clasificación (2026-07-22)

| # | Título | Relevancia | Complejidad | Modelo recomendado (esfuerzo) | Próximo paso |
|---|--------|------------|-------------|--------------------------------|--------------|
| [#656](https://github.com/NikolayDA/picture_helper/issues/656) | Activar el secreto ANTHROPIC_API_KEY para la evaluación previa por visión | 🟠 Alta (último bloqueo de toda la cadena de aceptación) | 🟢 Baja (puramente operativo, sin código) | – (sin agente; propietario del repo: Settings → Secrets) | Bloqueada (externa) – configurar el secreto y luego revisar el despacho |
| [#646](https://github.com/NikolayDA/picture_helper/issues/646) | Evaluación previa por visión, agregación de evidencia, matriz de aceptación | 🟠 Alta (última incidencia secundaria abierta del epic #639) | 🟢 Baja (código/pruebas ya fusionados en PR #649) | Sonnet 5 (bajo) – solo verificación, no se espera código nuevo | Necesita verificación – tras #656, comprobar un despacho real con visión y luego cerrar |
| [#639](https://github.com/NikolayDA/picture_helper/issues/639) | [Epic] Aceptación automatizada de releases | 🟠 Alta (epic, 7/8 incidencias secundarias hechas) | 🟢 Baja (solo queda #646) | – (epic, sin uso directo de agente) | Bloqueada – se cierra automáticamente con #646 |
| [#595](https://github.com/NikolayDA/picture_helper/issues/595) | [3D] Rendimiento, empaquetado, documentación, aceptación end-to-end | 🟠 Alta (puerta de aceptación del epic #582) | 🟢 Baja (todos los criterios cumplidos salvo la fila de visión) | – (sin tarea de código) | Bloqueada – espera a #646/#656, luego cerrar |
| [#582](https://github.com/NikolayDA/picture_helper/issues/582) | [Epic] Vista previa de relieve 3D real | 🟠 Alta (epic grande, casi terminado) | 🟢 Baja (solo queda #595) | – (epic, sin uso directo de agente) | Bloqueada – se cierra automáticamente con #595 |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restaurar la cuota de OpenAI para la comprobación manual de Codex Security | 🟢 Baja (solo bloquea un escaneo manual opcional) | 🟢 Baja (puramente operativo, sin código) | – (sin agente; propietario del repo: facturación) | Bloqueada (externa) – resolver facturación/cuota en el proyecto de la plataforma OpenAI |

### Recomendado a continuación

1. Resolver primero **#656** (configurar el secreto del repositorio `ANTHROPIC_API_KEY`) — la única palanca restante que desbloquea toda la cadena #646 → #639 → #595 → #582.
2. Después, despachar `release-abnahme.yml` de nuevo mediante `workflow_dispatch` y comprobar si la fila de visión de la matriz de aceptación muestra veredictos reales en lugar de `sin evaluar` (contrastar un par manualmente contra las capturas, como exige #656).
3. Con la fila de visión en verde, cerrar **#646**; eso encadena el cierre de **#639**, **#595** y **#582** (revisar brevemente cada una antes de cerrarla manualmente).
4. Dejar **#245** como tracker puramente externo de facturación/cuota; no hay ninguna acción posible ni necesaria en el repositorio.
5. Actualmente **no** hay ninguna incidencia abierta que justifique un nuevo PR de código — la siguiente tarea sensata para un agente es la verificación tras #656, no una nueva implementación.

## Rondas anteriores

- **2026-07-22 (revisión de incidencias)** — reevaluación completa de todas las incidencias abiertas: #640–#645 y #648 ya se habían aceptado y cerrado mediante el despacho de aceptación del 2026-07-21, pero la lista de verificación de incidencias secundarias del epic #639 no se había conciliado (corregido hoy mediante edición del cuerpo + comentario, sin afectar código). Nuevo bloqueo **#656** (falta el secreto `ANTHROPIC_API_KEY`) identificado como la única palanca restante para #646/#639/#595/#582. Estado en vivo: 6 incidencias abiertas — el nivel más bajo desde el epic #582.
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
