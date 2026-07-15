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

La lista activa de análisis de código está vacía. Ruff, mypy y la suite de pruebas local siguen siendo la base antes de nuevos PR. La versión **v2.5.0** se publicó el 2026-07-11 (PR #538); la ola de rollout **#435/#392/#426/#389** está cerrada, igual que **#299** (PR #539) con el seguimiento N13 **#541** (PR #543), **#318** (PR #540) y la sincronización de instantánea **#542**. Una auditoría del repositorio del 2026-07-12 abrió **#549–#553**; **#552/#549/#553/#550** ya están cerrados vía PR #557–#560. El epic **#563** («comprobación de actualizaciones y gestión del modelo de IA», ocho subincidencias **#564–#571**) quedó completamente implementado y cerrado el 2026-07-13 vía PR #573/#574 (**N14**). Estado en vivo: **18** incidencias abiertas – las ya existentes #245/#551 más tres epics abiertos el 2026-07-15 (**Release v2.6.0** #580, la **canalización de altura de 16 bits** #581, la **vista previa de relieve 3D** #582) con sus subincidencias aún abiertas, más dos hallazgos de cobertura de pruebas **N15/N16** (#597/#598) abiertos el mismo día tras una auditoría de cobertura. También el 2026-07-15 se completaron y cerraron las dos primeras subincidencias: **#583** (scope-freeze de v2.6.0) y **#586** (ADR de 16 bits) – desbloqueando **#584** (gate del candidato) y **#591** (contrato ADR/UX de 3D).

### Completado desde la última revisión

- **Base antigua estable:** **N1/N2/N4/N5/N6/N7/N8** y **O2–O7** siguen hechos; los epics **#329/#344/#358/#384** (N9–N12) más la corrección de exportación **#363** fusionados/archivados; desde el 2026-06-25 también **#404/#406/#408** (PR #412) cerrado.
- **Rediseño y publicación v2.5.0:** núcleo del rediseño/rail/zoom/inspector de tarjetas/Dark Mode/seguimiento de UI (**#413/#414/#455–#464/#474–#489/#499–#501/#503/#509/#510/#514–#517**, **#490**, **#433/#434**) vía PR #412–#522; ola de publicación **#435/#392/#426/#389** (v2.5.0), **#299/#541/#318/#542**, plantilla de PR **#552**, sincronización **#549**, arreglo de SessionStart **#553**, formalización v2.3.0 **#550** – todo cerrado desde el 2026-07-12.
- **N14 — Epic #563 (actualizaciones de la app y gestión del modelo de IA) completamente cerrado:** `app_update.py` (#564), `ai_model_status.py` (#568), integración de menú/diálogo (#565/#569), comprobación automática opcional al iniciar (#566), conexión del warmup con múltiples observadores/cancelación cooperativa (#570) vía PR #573/#574; cierre de documentación (#567/#571).
- **#583/#586 (2026-07-15, mismo día):** la curación del scope-freeze/versión/CHANGELOG de v2.6.0 (#583) y el ADR de HEIGHT de 16 bits (#586) quedan completados y cerrados; #584 y #591 quedan desbloqueados como resultado.

### Aún abierto

- **O8 🟢 — Imprecisión del prototipo:** las herramientas de altura quedan bloqueadas en el mockup tras generarla; solo afecta a la simulación (#347).
- **N15 🟡 — Wiring de diálogo sin probar:** `MainWindow._open_ai_install_dialog` (`main_window.py:1566`) no tiene ninguna prueba dedicada, a diferencia del método hermano estructuralmente idéntico `_open_ai_model_dialog` (#597).
- **N16 🟡 — Conversión no-RGBA sin probar:** las ramas no-RGBA de `pil_to_qpixmap`/`pil_to_numpy_readonly` (`image_utils.py:16`/`:43`) nunca se ejercitan con una imagen de origen RGB/paleta/escala de grises (#598).

## Incidencias abiertas de GitHub — Clasificación (2026-07-15)

Estado en vivo: **18** incidencias abiertas – la misma instantánea de antes, el mismo día, pero con dos subincidencias cerradas mientras tanto (**#583**, **#586**) y comentarios actualizados del propietario en **#245**/**#551**. La revisión de comentarios encontró: #245 y #551 recibieron cada una un nuevo comentario fechado el 2026-07-15 – el propietario los usó para fijar la decisión estratégica de #551 (modelo híbrido: CodeQL automático + Codex solo manual) y acotar el alcance de ambos issues en consecuencia; los cuerpos de ambos issues ya están actualizados, así que no hizo falta ningún comentario adicional de mi parte. Las otras 16 incidencias siguen sin comentarios.

### Agrupaciones sensatas

- **Release v2.6.0** (#580 → #584 → #585; #583 ya está cerrado): publica el estado de actualizaciones/gestión de IA ya construido en `main`; máxima prioridad por su bajo riesgo y valor inmediato para el usuario.
- **Canalización de altura de 16 bits** (#581 → #587 → {#588 ‖ #589} → #590; el ADR #586 ya está cerrado): la implementación que cambia el esquema (#587+) sigue empezando solo tras #585 (mandato de scope-freeze de #580).
- **Vista previa de relieve 3D** (#582 → #591 → #592 → #593 → #594 → #595): #591 ya está desbloqueado porque #586 está cerrado – puede empezar de inmediato en paralelo a la implementación del modelo de 16 bits; #582 sigue siendo el mayor bloque de esfuerzo de esta ronda de todos modos.
- **#245/#551** siguen vinculados, pero la decisión estratégica ya está tomada: #551 solo rastrea la implementación del modelo híbrido (CodeQL automático, Codex manual), #245 solo la prueba externa de cuota de OpenAI.
- **#597/#598** son brechas de cobertura independientes y totalmente especificadas (el boceto de prueba ya está en el issue) – sin cadena, sin dependencia de los tres epics.

Valoración: **Relevancia** = importancia para la hoja de ruta/usuarios, **Complejidad** = esfuerzo estimado, **Modelo/Esfuerzo** = modelo/esfuerzo recomendados.

| # | Título | Relevancia | Complejidad | Modelo/Esfuerzo | Próximo paso recomendado |
|---|--------|------------|-------------|------------------|---------------------------|
| [#580](https://github.com/NikolayDA/picture_helper/issues/580) | [Epic] Release v2.6.0 | 🟠 Alta | 🟠 Alta | – (epic de seguimiento) | **In progress** – avanza vía #584→#585 (#583 cerrado), sin PR propio. |
| [#584](https://github.com/NikolayDA/picture_helper/issues/584) | Release 2.6.0: gate del candidato, cinco artefactos | 🟠 Alta | 🟠 Alta | Sonnet 5 · alta | **Ready for PR** – #583 está cerrado, ya no queda dependencia abierta; los cinco smokes de artefactos encajan bien con orquestación paralela por workflow. |
| [#585](https://github.com/NikolayDA/picture_helper/issues/585) | Release 2.6.0: tag, GitHub Release, comprobación post-release | 🟠 Alta | 🟡 Media | Sonnet 5 · media | **Blocked** – espera a #584. |
| [#587](https://github.com/NikolayDA/picture_helper/issues/587) | [16 bits] Modelo de dominio HEIGHT y ProjectHistory sin pérdida | 🟠 Alta | 🟠 Alta (muy grande) | Opus 4.8 · alta | **Blocked** – #586 está cerrado; ahora solo espera a la publicación de la versión (#585). |
| [#588](https://github.com/NikolayDA/picture_helper/issues/588) | [16 bits] Formato de proyecto v2: persistencia, migración, validación | 🟠 Alta | 🟠 Alta | Opus 4.8 · alta | **Blocked** – espera a #587. |
| [#589](https://github.com/NikolayDA/picture_helper/issues/589) | [16 bits] Importación/generación/operaciones de altura sin cuantización de 8 bits | 🟠 Alta | 🟠 Alta | Opus 4.8 · alta | **Blocked** – espera a #587. |
| [#590](https://github.com/NikolayDA/picture_helper/issues/590) | [16 bits] Vista previa, exportación, UI, aceptación end-to-end | 🟠 Alta | 🟠 Alta | Opus 4.8 · alta | **Blocked** – espera a #588/#589. |
| [#581](https://github.com/NikolayDA/picture_helper/issues/581) | [Epic] Canalización de altura de 16 bits de extremo a extremo | 🟠 Alta | 🟠 Alta (muy grande) | – (epic de seguimiento) | **In progress** – avanza vía #587→(#588‖#589)→#590 (#586 cerrado). |
| [#591](https://github.com/NikolayDA/picture_helper/issues/591) | [3D] ADR/contrato UX: backend de renderizado, fallback, presupuestos | 🟡 Media | 🟠 Alta | Opus 4.8 · alta | **Ready for PR** – #586 está cerrado, ya no queda dependencia abierta; trabajo puro de concepto ADR/UX, puede empezar en paralelo a la implementación del modelo de 16 bits. |
| [#592](https://github.com/NikolayDA/picture_helper/issues/592) | [3D] Pipeline de geometría/normales/decimación sin Qt | 🟡 Media | 🟠 Alta (muy grande) | Opus 4.8 · alta | **Blocked** – espera a #591. |
| [#593](https://github.com/NikolayDA/picture_helper/issues/593) | [3D] Visor interactivo con orbit/pan/zoom, fallback | 🟡 Media | 🟠 Alta (muy grande) | Opus 4.8 · xalta | **Blocked** – espera a #591/#592; la pieza más arriesgada (Qt/OpenGL específico de plataforma). |
| [#594](https://github.com/NikolayDA/picture_helper/issues/594) | [3D] Integración de workflow, estado y caché | 🟡 Media | 🟠 Alta (muy grande) | Opus 4.8 · alta | **Blocked** – espera a #593, #587, #588. |
| [#595](https://github.com/NikolayDA/picture_helper/issues/595) | [3D] Rendimiento, empaquetado, documentación, aceptación end-to-end | 🟡 Media | 🟠 Alta | Sonnet 5 · alta | **Blocked** – espera a #594. |
| [#582](https://github.com/NikolayDA/picture_helper/issues/582) | [Epic] Vista previa de relieve 3D real | 🟡 Media | 🟠 Alta (muy grande) | – (epic de seguimiento) | **In progress** – avanza vía #591→…→#595; #591 ya lista para empezar (#586 cerrado). |
| [#551](https://github.com/NikolayDA/picture_helper/issues/551) | Automatizar CodeQL y ejecutar Codex Security solo de forma manual | 🟡 Media | 🟡 Media | Sonnet 5 · media | **Ready for PR** – decisión estratégica tomada el 2026-07-15 (modelo híbrido: CodeQL automático + Codex manual vía `workflow_dispatch`); el cuerpo del issue ya tiene la lista de verificación completa de implementación. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restaurar la cuota de OpenAI para la comprobación manual de Codex Security | 🟢 Baja | 🟢 Baja | – (sin tarea de código) | **Blocked (external)** – alcance acotado aún más el 2026-07-15: es puramente un tracker externo de facturación/cuota de OpenAI, no bloquea ni CodeQL ni la publicación ni #551. |
| [#597](https://github.com/NikolayDA/picture_helper/issues/597) | test: `_open_ai_install_dialog` sin prueba de wiring (N15) | 🟢 Baja | 🟢 Baja | Sonnet 5 · baja | **Ready for PR** – el boceto de prueba ya está en el issue, sin dependencia. |
| [#598](https://github.com/NikolayDA/picture_helper/issues/598) | test: rutas de conversión no-RGBA en `image_utils.py` sin probar (N16) | 🟢 Baja | 🟢 Baja | Sonnet 5 · baja | **Ready for PR** – el boceto de prueba ya está en el issue, sin dependencia; se podría combinar con #597 en un solo PR. |

### Recomendado a continuación (orden de PR)

1. **#584** — abordar ya el gate del candidato de v2.6.0: #583 está cerrado, ya no queda dependencia abierta; fija el candidato de release sobre los cinco artefactos.
2. **#591** — empezar ya el ADR/contrato UX de 3D en lugar de esperar a que #586 quede «aceptado»: #586 está cerrado, #591 bloquea #592–595 y puede avanzar explícitamente en paralelo a la implementación del modelo de 16 bits (#587+).
3. **#551** — pasar a implementar el modelo híbrido ya decidido (automatizar CodeQL para Python, reducir el workflow de Codex a un `workflow_dispatch` puro); ya no queda ninguna cuestión de estrategia abierta.
4. **#597 + #598** — la victoria de cobertura más rápida de esta ronda, ambos bocetos de prueba ya están en los issues; se pueden resolver en un único PR conjunto.
5. **#585** y todas las subincidencias restantes de 16 bits/3D siguen sus dependencias de forma secuencial – ver la tabla, sin disparador adicional necesario.

*Drift:* reconsultar el número de incidencias abiertas en vivo antes de cada actualización futura, sin arrastrarlo – dentro del mismo día se cerraron dos subincidencias (#583, #586) que desbloquearon dos issues posteriores (#584, #591); una simple instantánea con marca de tiempo no lo habría detectado.

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
