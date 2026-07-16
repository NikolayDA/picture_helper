[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · **Español** · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Análisis de código y recomendaciones priorizadas: BgRemover

## Escala de valoración

| Símbolo | Prioridad | Significado |
|---------|-----------|-------------|
| 🔴 | Crítica | Errores, cierres inesperados o pérdida de datos |
| 🟠 | Alta | Impacto claro en la fiabilidad o el mantenimiento |
| 🟡 | Media | Mejora útil de calidad, legibilidad o testabilidad |
| 🟢 | Baja | Pulido opcional o mejora de proceso |

## Estado actual (2026-07-16)

La lista activa de análisis de código está vacía. Ruff, mypy y la suite de pruebas local siguen siendo la base antes de nuevos PR. La versión **v2.5.0** se publicó el 2026-07-11 (PR #538); la ola de rollout **#435/#392/#426/#389** está cerrada, igual que **#299** (PR #539) con el seguimiento N13 **#541** (PR #543), **#318** (PR #540) y la sincronización de instantánea **#542**. Una auditoría del repositorio del 2026-07-12 abrió **#549–#553**; **#552/#549/#553/#550** ya están cerrados vía PR #557–#560. El epic **#563** («comprobación de actualizaciones y gestión del modelo de IA», ocho subincidencias **#564–#571**) quedó completamente implementado y cerrado el 2026-07-13 vía PR #573/#574 (**N14**). Estado en vivo: **16** incidencias abiertas – las ya existentes #245/#551 más tres epics abiertos el 2026-07-15 (**Release v2.6.0** #580, la **canalización de altura de 16 bits** #581, la **vista previa de relieve 3D** #582) con sus subincidencias aún abiertas, más dos hallazgos de cobertura **N15/N16** (#597/#598). **#583** (scope-freeze de v2.6.0), **#586** (ADR de 16 bits) y **#591** (contrato ADR/UX de 3D, PR #603) están completados. **#584** se reabrió primero en la auditoría en vivo del 2026-07-16 (los PR #601–#604 solo reforzaron los nombres de artefactos y la reutilización del release) y ahora está cerrado mediante el gate real del candidato: cinco artefactos reales, un SHA-256 por artefacto, smokes de plataforma nativos (Linux x86_64/aarch64, macOS arm64) y una decisión Go documentada sobre el commit `427725477d` (detalles: [`docs/history/RELEASE-2.6.0-candidate-gate.md`](../../history/RELEASE-2.6.0-candidate-gate.md)); **#585** queda desbloqueado.

### Completado desde la última revisión

- **Base antigua estable:** **N1/N2/N4/N5/N6/N7/N8** y **O2–O7** siguen hechos; los epics **#329/#344/#358/#384** (N9–N12) más la corrección de exportación **#363** fusionados/archivados; desde el 2026-06-25 también **#404/#406/#408** (PR #412) cerrado.
- **Rediseño y publicación v2.5.0:** núcleo del rediseño/rail/zoom/inspector de tarjetas/Dark Mode/seguimiento de UI (**#413/#414/#455–#464/#474–#489/#499–#501/#503/#509/#510/#514–#517**, **#490**, **#433/#434**) vía PR #412–#522; ola de publicación **#435/#392/#426/#389** (v2.5.0), **#299/#541/#318/#542**, plantilla de PR **#552**, sincronización **#549**, arreglo de SessionStart **#553**, formalización v2.3.0 **#550** – todo cerrado desde el 2026-07-12.
- **N14 — Epic #563 (actualizaciones de la app y gestión del modelo de IA) completamente cerrado:** `app_update.py` (#564), `ai_model_status.py` (#568), integración de menú/diálogo (#565/#569), comprobación automática opcional al iniciar (#566), conexión del warmup con múltiples observadores/cancelación cooperativa (#570) vía PR #573/#574; cierre de documentación (#567/#571).
- **#583/#586/#591/#584 completados:** el scope-freeze/versión/CHANGELOG de v2.6.0 (#583), el ADR de HEIGHT de 16 bits (#586), el contrato ADR/UX de 3D (#591, PR #603) y el gate del candidato v2.6.0 (#584: cinco artefactos reales, SHA-256, smokes de plataforma nativos, decisión Go, commit `427725477d`) están completados; **#585** queda desbloqueado.

### Aún abierto

- **O8 🟢 — Imprecisión del prototipo:** las herramientas de altura quedan bloqueadas en el mockup tras generarla; solo afecta a la simulación (#347).
- **N15 🟡 — Wiring de diálogo sin probar:** `MainWindow._open_ai_install_dialog` (`main_window.py:1566`) no tiene ninguna prueba dedicada, a diferencia del método hermano estructuralmente idéntico `_open_ai_model_dialog` (#597).
- **N16 🟡 — Conversión no-RGBA sin probar:** las ramas no-RGBA de `pil_to_qpixmap`/`pil_to_numpy_readonly` (`image_utils.py:16`/`:43`) nunca se ejercitan con una imagen de origen RGB/paleta/escala de grises (#598).

## Incidencias abiertas de GitHub — Clasificación (2026-07-16)

Estado en vivo: **16** incidencias abiertas. **#591** está completado mediante PR #603; **#584** está cerrado tras el gate real del candidato (cinco artefactos, SHA-256, smokes nativos), por lo que **#585** queda desbloqueado. Los comentarios del propietario del 2026-07-15 en **#245**/**#551** y sus cuerpos acotados siguen vigentes.

### Agrupaciones sensatas

- **Release v2.6.0** (#580 → #585; #583/#584 ya están cerrados): publica el estado de actualizaciones/gestión de IA ya construido en `main`; máxima prioridad por su bajo riesgo y valor inmediato para el usuario.
- **Canalización de altura de 16 bits** (#581 → #587 → {#588 ‖ #589} → #590; el ADR #586 ya está cerrado): la implementación que cambia el esquema (#587+) sigue empezando solo tras #585 (mandato de scope-freeze de #580).
- **Vista previa de relieve 3D** (#582 → #592 → #593 → #594 → #595; #591 está completado): la canalización geométrica sin Qt #592 puede empezar ya en paralelo a la implementación del modelo de 16 bits; #582 sigue siendo el mayor bloque de esfuerzo de esta ronda.
- **#245/#551** siguen vinculados, pero la decisión estratégica ya está tomada: #551 solo rastrea la implementación del modelo híbrido (CodeQL automático, Codex manual), #245 solo la prueba externa de cuota de OpenAI.
- **#597/#598** son brechas de cobertura independientes y totalmente especificadas (el boceto de prueba ya está en el issue) – sin cadena, sin dependencia de los tres epics.

Valoración: **Relevancia** = importancia para la hoja de ruta/usuarios, **Complejidad** = esfuerzo estimado, **Modelo/Esfuerzo** = modelo/esfuerzo recomendados.

| # | Título | Relevancia | Complejidad | Modelo/Esfuerzo | Próximo paso recomendado |
|---|--------|------------|-------------|------------------|---------------------------|
| [#580](https://github.com/NikolayDA/picture_helper/issues/580) | [Epic] Release v2.6.0 | 🟠 Alta | 🟠 Alta | – (epic de seguimiento) | **In progress** – avanza vía #585 (#583/#584 cerrados), sin PR propio. |
| [#585](https://github.com/NikolayDA/picture_helper/issues/585) | Release 2.6.0: tag, GitHub Release, comprobación post-release | 🟠 Alta | 🟡 Media | Sonnet 5 · media | **Ready for PR** – #584 está completado, no queda ninguna dependencia abierta. |
| [#587](https://github.com/NikolayDA/picture_helper/issues/587) | [16 bits] Modelo de dominio HEIGHT y ProjectHistory sin pérdida | 🟠 Alta | 🟠 Alta (muy grande) | Opus 4.8 · alta | **Blocked** – #586 está cerrado; ahora solo espera a la publicación de la versión (#585). |
| [#588](https://github.com/NikolayDA/picture_helper/issues/588) | [16 bits] Formato de proyecto v2: persistencia, migración, validación | 🟠 Alta | 🟠 Alta | Opus 4.8 · alta | **Blocked** – espera a #587. |
| [#589](https://github.com/NikolayDA/picture_helper/issues/589) | [16 bits] Importación/generación/operaciones de altura sin cuantización de 8 bits | 🟠 Alta | 🟠 Alta | Opus 4.8 · alta | **Blocked** – espera a #587. |
| [#590](https://github.com/NikolayDA/picture_helper/issues/590) | [16 bits] Vista previa, exportación, UI, aceptación end-to-end | 🟠 Alta | 🟠 Alta | Opus 4.8 · alta | **Blocked** – espera a #588/#589. |
| [#581](https://github.com/NikolayDA/picture_helper/issues/581) | [Epic] Canalización de altura de 16 bits de extremo a extremo | 🟠 Alta | 🟠 Alta (muy grande) | – (epic de seguimiento) | **In progress** – avanza vía #587→(#588‖#589)→#590 (#586 cerrado). |
| [#592](https://github.com/NikolayDA/picture_helper/issues/592) | [3D] Pipeline de geometría/normales/decimación sin Qt | 🟡 Media | 🟠 Alta (muy grande) | Opus 4.8 · alta | **Ready for PR** – #586 y #591 están completados; no queda ninguna dependencia abierta. |
| [#593](https://github.com/NikolayDA/picture_helper/issues/593) | [3D] Visor interactivo con orbit/pan/zoom, fallback | 🟡 Media | 🟠 Alta (muy grande) | Opus 4.8 · xalta | **Blocked** – espera a #592; la pieza más arriesgada (Qt/OpenGL específico de plataforma). |
| [#594](https://github.com/NikolayDA/picture_helper/issues/594) | [3D] Integración de workflow, estado y caché | 🟡 Media | 🟠 Alta (muy grande) | Opus 4.8 · alta | **Blocked** – espera a #593, #587, #588. |
| [#595](https://github.com/NikolayDA/picture_helper/issues/595) | [3D] Rendimiento, empaquetado, documentación, aceptación end-to-end | 🟡 Media | 🟠 Alta | Sonnet 5 · alta | **Blocked** – espera a #594. |
| [#582](https://github.com/NikolayDA/picture_helper/issues/582) | [Epic] Vista previa de relieve 3D real | 🟡 Media | 🟠 Alta (muy grande) | – (epic de seguimiento) | **In progress** – avanza vía #592→…→#595; #591 está completado. |
| [#551](https://github.com/NikolayDA/picture_helper/issues/551) | Automatizar CodeQL y ejecutar Codex Security solo de forma manual | 🟡 Media | 🟡 Media | Sonnet 5 · media | **Ready for PR** – decisión estratégica tomada el 2026-07-15 (modelo híbrido: CodeQL automático + Codex manual vía `workflow_dispatch`); el cuerpo del issue ya tiene la lista de verificación completa de implementación. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restaurar la cuota de OpenAI para la comprobación manual de Codex Security | 🟢 Baja | 🟢 Baja | – (sin tarea de código) | **Blocked (external)** – alcance acotado aún más el 2026-07-15: es puramente un tracker externo de facturación/cuota de OpenAI, no bloquea ni CodeQL ni la publicación ni #551. |
| [#597](https://github.com/NikolayDA/picture_helper/issues/597) | test: `_open_ai_install_dialog` sin prueba de wiring (N15) | 🟢 Baja | 🟢 Baja | Sonnet 5 · baja | **Ready for PR** – el boceto de prueba ya está en el issue, sin dependencia. |
| [#598](https://github.com/NikolayDA/picture_helper/issues/598) | test: rutas de conversión no-RGBA en `image_utils.py` sin probar (N16) | 🟢 Baja | 🟢 Baja | Sonnet 5 · baja | **Ready for PR** – el boceto de prueba ya está en el issue, sin dependencia; se podría combinar con #597 en un solo PR. |

### Recomendado a continuación (orden de PR)

1. **#585** — crear el tag `v2.6.0` y publicar el release de GitHub: #584 está completado, no queda ninguna dependencia abierta.
2. **#592** — iniciar ya la canalización geométrica 3D: #586 y #591 están completados, sin dependencias abiertas.
3. **#551** — pasar a implementar el modelo híbrido ya decidido (automatizar CodeQL para Python, reducir el workflow de Codex a un `workflow_dispatch` puro); ya no queda ninguna cuestión de estrategia abierta.
4. **#597 + #598** — la victoria de cobertura más rápida de esta ronda, ambos bocetos de prueba ya están en los issues; se pueden resolver en un único PR conjunto.
5. Todas las subincidencias restantes de 16 bits/3D siguen sus dependencias de forma secuencial (a la espera de #585) – ver la tabla, sin disparador adicional necesario.

*Drift:* el seguimiento en vivo del 2026-07-16 detectó el cierre prematuro de #584 y el cierre real de #591; #584 se reabrió como consecuencia y ahora está cerrado con evidencia del gate real de cinco artefactos. Las próximas actualizaciones siguen consultando estados, checklists y dependencias en vivo, no arrastrando una marca de tiempo.

## Rondas anteriores

- **2026-07-16 (gate del candidato)** — #584 cerrado mediante el gate real de cinco artefactos (SHA `427725477d`, ejecución de CI 29488035790, SHA-256 + escaneo de secretos por artefacto, smokes de plataforma nativos); #585 desbloqueado; estado en vivo 16.
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
