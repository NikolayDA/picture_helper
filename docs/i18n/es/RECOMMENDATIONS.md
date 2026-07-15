[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · **Español** · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Análisis de código y recomendaciones priorizadas: BgRemover

## Escala de valoración

| Símbolo | Prioridad | Significado |
|---------|-----------|-------------|
| 🔴 | Crítica | Errores, cierres inesperados o pérdida de datos |
| 🟠 | Alta | Impacto claro en la fiabilidad o el mantenimiento |
| 🟡 | Media | Mejora útil de calidad, legibilidad o testabilidad |
| 🟢 | Baja | Pulido opcional o mejora de proceso |

## Estado actual (2026-07-15)

La lista activa de análisis de código está vacía. Ruff, mypy y la suite de pruebas local siguen siendo la base antes de nuevos PR. La versión **v2.5.0** se publicó el 2026-07-11 (PR #538); la ola de rollout **#435/#392/#426/#389** está cerrada, igual que **#299** (PR #539) con el seguimiento N13 **#541** (PR #543), **#318** (PR #540) y la sincronización de instantánea **#542**. Una auditoría del repositorio del 2026-07-12 abrió **#549–#553**; **#552/#549/#553/#550** ya están cerrados vía PR #557–#560. El epic **#563** («comprobación de actualizaciones y gestión del modelo de IA», ocho subincidencias **#564–#571**) quedó completamente implementado y cerrado el 2026-07-13 vía PR #573/#574 (**N14**). Estado en vivo: **18** incidencias abiertas – las ya existentes #245/#551 más tres epics abiertos el 2026-07-15: **Release v2.6.0** (#580, subincidencias #583–#585), la **canalización de altura de 16 bits** (#581, subincidencias #586–#590) y la **vista previa de relieve 3D** (#582, subincidencias #591–#595).

### Completado desde la última revisión

- **Base antigua estable:** **N1/N2/N4/N5/N6/N7/N8** y **O2–O7** siguen hechos; los epics **#329/#344/#358/#384** (N9–N12) más la corrección de exportación **#363** fusionados/archivados; desde el 2026-06-25 también **#404/#406/#408** (PR #412) cerrado.
- **Rediseño y publicación v2.5.0:** núcleo del rediseño/rail/zoom/inspector de tarjetas/Dark Mode/seguimiento de UI (**#413/#414/#455–#464/#474–#489/#499–#501/#503/#509/#510/#514–#517**, **#490**, **#433/#434**) vía PR #412–#522; ola de publicación **#435/#392/#426/#389** (v2.5.0), **#299/#541/#318/#542**, plantilla de PR **#552**, sincronización **#549**, arreglo de SessionStart **#553**, formalización v2.3.0 **#550** – todo cerrado desde el 2026-07-12.
- **N14 — Epic #563 (actualizaciones de la app y gestión del modelo de IA) completamente cerrado:** `app_update.py` (#564), `ai_model_status.py` (#568), integración de menú/diálogo (#565/#569), comprobación automática opcional al iniciar (#566), conexión del warmup con múltiples observadores/cancelación cooperativa (#570) vía PR #573/#574; cierre de documentación (#567/#571).

### Aún abierto

- **O8 🟢 — Imprecisión del prototipo:** las herramientas de altura quedan bloqueadas en el mockup tras generarla; solo afecta a la simulación (#347).

## Incidencias abiertas de GitHub — Clasificación (2026-07-15)

Estado en vivo: **18** incidencias abiertas – un salto respecto a las **2** anteriores: la persona propietaria del repositorio abrió el 2026-07-14/15 tres nuevos epics con doce subincidencias para el próximo ciclo de versión/funcionalidades (Release v2.6.0, canalización de altura de 16 bits, vista previa de relieve 3D). La revisión de comentarios no encontró nada que requiera acción: #245 se comentó por última vez el 2026-06-19 (estado aún válido, sin reacción nueva necesaria), y #551 más las 16 incidencias nuevas no tienen comentarios.

### Agrupaciones sensatas

- **Release v2.6.0** (#580 → #583 → #584 → #585, estrictamente secuencial): publica el estado de actualizaciones/gestión de IA ya construido en `main`; máxima prioridad por su bajo riesgo y valor inmediato para el usuario.
- **Canalización de altura de 16 bits** (#581 → #586 → #587 → {#588 ‖ #589} → #590): #586 (ADR) puede avanzar explícitamente en paralelo a la publicación, pero la implementación que cambia el esquema (#587+) solo empieza tras #585 (mandato de scope-freeze de #580).
- **Vista previa de relieve 3D** (#582 → #591 → #592 → #593 → #594 → #595): #591 depende además de #586 (consume el mismo contrato HEIGHT), así que #582 queda de facto detrás de la cadena de 16 bits y es el mayor bloque de esfuerzo de esta ronda.
- **#245/#551** siguen vinculados (scan Codex: acción de cuenta vs. decisión estratégica).

Valoración: **Relevancia** = importancia para la hoja de ruta/usuarios, **Complejidad** = esfuerzo estimado, **Modelo/Esfuerzo** = modelo/esfuerzo recomendados.

| # | Título | Relevancia | Complejidad | Modelo/Esfuerzo | Próximo paso recomendado |
|---|--------|------------|-------------|------------------|---------------------------|
| [#580](https://github.com/NikolayDA/picture_helper/issues/580) | [Epic] Release v2.6.0 | 🟠 Alta | 🟠 Alta | – (epic de seguimiento) | **In progress** – avanza vía #583→#584→#585, sin PR propio. |
| [#583](https://github.com/NikolayDA/picture_helper/issues/583) | Release 2.6.0: scope-freeze, versión, CHANGELOG | 🟠 Alta | 🟡 Media | Sonnet 5 · media | **Ready for PR** – sin dependencia abierta, fija el valor de usuario ya construido con bajo riesgo. |
| [#584](https://github.com/NikolayDA/picture_helper/issues/584) | Release 2.6.0: gate del candidato, cinco artefactos | 🟠 Alta | 🟠 Alta | Sonnet 5 · alta | **Blocked** – espera a #583; los cinco smokes de artefactos encajan bien con orquestación paralela por workflow. |
| [#585](https://github.com/NikolayDA/picture_helper/issues/585) | Release 2.6.0: tag, GitHub Release, comprobación post-release | 🟠 Alta | 🟡 Media | Sonnet 5 · media | **Blocked** – espera a #584. |
| [#586](https://github.com/NikolayDA/picture_helper/issues/586) | [16 bits] ADR: contrato de datos HEIGHT canónico, migración, presupuesto de memoria | 🟠 Alta | 🟠 Alta | Opus 4.8 · alta | **Ready for PR** – trabajo puro de análisis/ADR, puede avanzar en paralelo a la publicación; bloquea #587–590 y #591. |
| [#587](https://github.com/NikolayDA/picture_helper/issues/587) | [16 bits] Modelo de dominio HEIGHT y ProjectHistory sin pérdida | 🟠 Alta | 🟠 Alta (muy grande) | Opus 4.8 · alta | **Blocked** – espera a #586 y a la publicación de la versión (#585). |
| [#588](https://github.com/NikolayDA/picture_helper/issues/588) | [16 bits] Formato de proyecto v2: persistencia, migración, validación | 🟠 Alta | 🟠 Alta | Opus 4.8 · alta | **Blocked** – espera a #586/#587. |
| [#589](https://github.com/NikolayDA/picture_helper/issues/589) | [16 bits] Importación/generación/operaciones de altura sin cuantización de 8 bits | 🟠 Alta | 🟠 Alta | Opus 4.8 · alta | **Blocked** – espera a #586/#587. |
| [#590](https://github.com/NikolayDA/picture_helper/issues/590) | [16 bits] Vista previa, exportación, UI, aceptación end-to-end | 🟠 Alta | 🟠 Alta | Opus 4.8 · alta | **Blocked** – espera a #588/#589. |
| [#581](https://github.com/NikolayDA/picture_helper/issues/581) | [Epic] Canalización de altura de 16 bits de extremo a extremo | 🟠 Alta | 🟠 Alta (muy grande) | – (epic de seguimiento) | **In progress** – avanza vía #586→#587→(#588‖#589)→#590. |
| [#591](https://github.com/NikolayDA/picture_helper/issues/591) | [3D] ADR/contrato UX: backend de renderizado, fallback, presupuestos | 🟡 Media | 🟠 Alta | Opus 4.8 · alta | **Blocked** – espera a que #586 quede aceptado. |
| [#592](https://github.com/NikolayDA/picture_helper/issues/592) | [3D] Pipeline de geometría/normales/decimación sin Qt | 🟡 Media | 🟠 Alta (muy grande) | Opus 4.8 · alta | **Blocked** – espera a #586/#591. |
| [#593](https://github.com/NikolayDA/picture_helper/issues/593) | [3D] Visor interactivo con orbit/pan/zoom, fallback | 🟡 Media | 🟠 Alta (muy grande) | Opus 4.8 · xalta | **Blocked** – espera a #591/#592; la pieza más arriesgada (Qt/OpenGL específico de plataforma). |
| [#594](https://github.com/NikolayDA/picture_helper/issues/594) | [3D] Integración de workflow, estado y caché | 🟡 Media | 🟠 Alta (muy grande) | Opus 4.8 · alta | **Blocked** – espera a #593, #587, #588. |
| [#595](https://github.com/NikolayDA/picture_helper/issues/595) | [3D] Rendimiento, empaquetado, documentación, aceptación end-to-end | 🟡 Media | 🟠 Alta | Sonnet 5 · alta | **Blocked** – espera a #594. |
| [#582](https://github.com/NikolayDA/picture_helper/issues/582) | [Epic] Vista previa de relieve 3D real | 🟡 Media | 🟠 Alta (muy grande) | – (epic de seguimiento) | **In progress** – avanza vía #591→…→#595; bloqueado por #586. |
| [#551](https://github.com/NikolayDA/picture_helper/issues/551) | Decisión de estrategia para Codex Security Scan (reactivar/retirar/reemplazar) | 🟡 Media | 🟡 Media | Sonnet 5 · media | **Ready for PR** – la recomendación sigue siendo la opción 2 (retirar/deshabilitar), ya con más de 5 semanas de bloqueo externo. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan «Quota exceeded» | 🟢 Baja | 🟢 Baja | – (sin tarea de código) | **Blocked (external)** – restaurar la facturación/cuota de OpenAI es una acción de cuenta, no un PR. |

### Recomendado a continuación (orden de PR)

1. **#583** — abordar primero el scope-freeze de v2.6.0: sin dependencia abierta, fija el valor de usuario ya construido con bajo riesgo.
2. **#586** — empezar ya el ADR de 16 bits en lugar de esperar a #585: bloquea dos epics completos (#581 directamente, #582 indirectamente vía #591) y puede avanzar explícitamente en paralelo a la publicación.
3. **#551** — resolver la decisión de estrategia, corta e independiente; la recomendación sigue siendo la opción 2 (retirar/deshabilitar).
4. **#584/#585** y todas las subincidencias de 16 bits/3D siguen sus dependencias de forma secuencial – ver la tabla, sin disparador adicional necesario.

*Drift:* reconsultar el número de incidencias abiertas en vivo antes de cada actualización futura, sin arrastrarlo – el salto de 2 a 18 en esta ronda muestra lo rápido que se desactualiza la instantánea.

## Rondas anteriores

- **2026-07-14** — estado en vivo aún con 2 incidencias abiertas (#245, #551), sin cambios desde el cierre del epic del día anterior.
- **2026-07-13 (cierre del epic)** — epic **#563** completamente cerrado: las ocho subincidencias (**#564–#571**) cerradas vía PR #573/#574; instantánea reducida a 2.
- **2026-07-13 (auditoría de issues)** — epic **#563** + ocho subincidencias abiertas, las 11 incidencias abiertas reevaluadas, comentarios del propietario considerados; ninguna cerrada; instantánea actualizada a 11.
- **2026-07-12** — formalización v2.3.0 (#550), arreglo del hook SessionStart (#553), sincronización (#549, plantilla de PR #552 vía PR #557), auditoría (#542 cerrado, #549–#553 abiertas) y versión **v2.5.0** (ola #435/#392/#426/#389, #299/#541/#318).
- **2026-07-11** — epic #425 completado (#430 PR #526, i18n en tiempo de ejecución ES/FR/UK/ZH completa, **O1** hecho; #431/#432 PR #529; seguimiento final #530/#531 PR #533/#535).
- **2026-07-05–10** — #509/#510/#514–#517 (PR #520–#522), #490, ola de Dark Mode/iconos rail, inspector de tarjetas (#413/#414), #499–#501/#503, pulido de iconos/barra de estado.
- **2026-06-29** — #404/#406/#408 completados (PR #412), rediseño abierto.
- **v2.2, «admiring-mayer» (#1–#15)** — lista externa, completada o descartada donde era un falso positivo.

Hallazgos históricos y registros de trabajo (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).
