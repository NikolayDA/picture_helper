[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · **Español** · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Análisis de código y recomendaciones priorizadas: BgRemover

## Escala de valoración

| Símbolo | Prioridad | Significado |
|---------|-----------|-------------|
| 🔴 | Crítica | Errores, cierres inesperados o pérdida de datos |
| 🟠 | Alta | Impacto claro en la fiabilidad o el mantenimiento |
| 🟡 | Media | Mejora útil de calidad, legibilidad o testabilidad |
| 🟢 | Baja | Pulido opcional o mejora de proceso |

## Estado actual (2026-07-23, #668/#669 cerradas)

Ruff, mypy y la suite de pruebas local siguen siendo la base antes de nuevos PR. Desde la última ronda se cerraron las dos incidencias de auditoría que quedaban abiertas:

- **#669** (estado en vivo desactualizado) — cerrada directamente: la conciliación anterior de RECOMMENDATIONS (PR #671) ya había puesto el contenido totalmente al día (#659/#660 listadas correctamente como cerradas, #668 ya incluida); no hizo falta un PR adicional sin cambios.
- **#668** (referencias al conjunto de capturas desactualizadas) — corregida con esta actualización: `ANLEITUNG.md` y `README.md` (cada uno con sus cinco traducciones) ahora apuntan al conjunto actual `bgremover_complete_20260722_171622`. `docs/history/EPIC-582-ABNAHME.md` mantiene deliberadamente el conjunto del 2026-07-19 — ahí es la evidencia real de aceptación (procedencia de GPU/SO/renderizador registrada en el manifiesto), y cambiarlo habría falseado la evidencia documentada; se añadió una nota explicativa y el directorio antiguo se conserva en consecuencia. Una nueva prueba de gobernanza (`tests/test_screenshot_references.py::test_docs_reference_latest_screenshot_set`) detectará en el futuro una repetición de esta deriva silenciosa.

Estado en vivo: **2** incidencias abiertas (#656, #245) — ambas puramente externas/operativas, ningún bloqueo de código.

### Resultado de la revisión

- **Auditoría de PR/issues del 22–23 de julio completada:** Se comprobaron los estados fusionados #657/#658, #661–#665 y #670–#673 frente a sus objetivos y criterios de aceptación. La automatización de aceptación contiene las evidencias estructuradas de guardas y E2E que faltaban, los seguimientos de pruebas/documentación cubren sus regresiones respectivas y el seguimiento de release/capturas es coherente, incluidos los artefactos generados y la prueba de gobernanza. No quedó ningún resto reproducible de código, pruebas o documentación que justifique un issue nuevo o un comentario adicional en un issue cerrado.
- **Base antigua estable:** **N1/N2/N4/N5/N6/N7/N8/N9**, **O1–O8** y todo lo completado desde el **2026-06-25** sigue hecho.
- **El release v2.7.0 está completamente cerrado y verificado:** la etiqueta, la publicación y las tres etapas del gate (matriz de CI, build de candidato, aceptación de hardware) se ejecutaron contra el commit realmente etiquetado `6f103ed` — sin deriva entre lo verificado y lo publicado.
- **#669/#668 cerradas** — el nivel más bajo desde que existe este registro.
- **#656/#245** siguen siendo, sin cambios, trackers puramente externos/operativos sin relación con el código.

## Incidencias abiertas de GitHub — Clasificación (2026-07-23)

| # | Título | Relevancia | Complejidad | Modelo recomendado (esfuerzo) | Próximo paso |
|---|--------|------------|-------------|--------------------------------|--------------|
| [#656](https://github.com/NikolayDA/picture_helper/issues/656) | Activar el secreto ANTHROPIC_API_KEY para la evaluación previa por visión | 🟡 Media (solo mejora la calidad de la evidencia; no es un bloqueo según el contrato) | 🟢 Baja (puramente operativo, sin código) | – (sin agente; propietario del repo: Settings → Secrets) | Bloqueada (externa) – se puede hacer de forma independiente |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restaurar la cuota de OpenAI para la comprobación manual de Codex Security | 🟢 Baja (solo bloquea un escaneo manual opcional) | 🟢 Baja (puramente operativo, sin código) | – (sin agente; propietario del repo: facturación) | Bloqueada (externa) – resolver facturación/cuota en el proyecto de la plataforma OpenAI |

### Recomendado a continuación

1. Gestionar **#656** de forma independiente si se desean veredictos de visión reales — es una mejora de calidad, no un bloqueo.
2. Dejar **#245** como tracker puramente externo de facturación/cuota; no hay ninguna acción posible ni necesaria en el repositorio.
3. El release v2.7.0 está completamente publicado — no hace falta ningún paso adicional relacionado con el release.

## Rondas anteriores

- **2026-07-23 (#668/#669 cerradas)** — #669 (estado en vivo desactualizado) se cerró directamente, ya que el PR #671 ya la había resuelto por completo, sin necesidad de más cambios de código o documentación. #668 (`ANLEITUNG.md`/`README.md` referenciando el conjunto de capturas huérfano del 2026-07-19) se corrigió mediante un PR independiente: las referencias documentales vivas (6 idiomas cada una) se migraron al conjunto actual del 2026-07-22; la evidencia de aceptación en `docs/history/EPIC-582-ABNAHME.md` se dejó deliberadamente intacta (se añadió una nota explicativa, se conservó el directorio antiguo); se añadió una nueva prueba de gobernanza contra futuras derivas de capturas. Estado en vivo: 2 incidencias abiertas (ambas externas/operativas, no un bloqueo) — el nivel más bajo desde que existe este registro.
- **2026-07-23 (release v2.7.0)** — se fusionó el PR #670 (incremento de versión + traslado de CHANGELOG + entrada del icono) (`6f103ed`); se repitió el gate completo contra el nuevo commit de fusión (matriz de CI, build de candidato, aceptación de hardware, todo en verde); se creó y publicó la etiqueta `v2.7.0` (cinco artefactos). Se registraron dos nuevas incidencias de auditoría: #669 (estado en vivo desactualizado, corregido con esta actualización) y #668 (conjunto de capturas huérfano en ANLEITUNG.md, higiene menor de repositorio). Estado en vivo: 4 incidencias abiertas, todas de higiene documental o externas, ningún bloqueo de código.
- **2026-07-22 (cierre de la auditoría de pruebas)** — se cerraron las dos incidencias de auditoría antes abiertas: #660 mediante el PR #664 (commit `92c14ba`, se documentó el marcador `gl_smoke` en TESTING.md), #659 mediante el PR #665 (commit `c4ab92a`, N9/O8 completamente implementados, `make check` 1995/5, `make coverage` 93 %). También se fusionaron dos PR relacionados con activos (#666 conjunto de capturas, #667 nuevo icono de la app), ambos aún sin entrada en el CHANGELOG. Estado en vivo: 2 incidencias abiertas (ambas externas/operativas, no son un bloqueo) — el nivel más bajo desde que existe este registro.
- **2026-07-22 (cierre de la aceptación)** — se lanzó un despacho nuevo de `release-abnahme.yml` (ejecución #4, commit `9165c00`); se contrastó la matriz con #595 (x86_64 sigue documentada como pausada pero no bloquea); se verificaron y cerraron individualmente #595, #646, #639 y #582 contra sus propios criterios de aceptación. La única laguna real encontrada (rigor de mypy para `scripts/abnahme_vision_check.py`/`abnahme_aggregate.py`, #646) se corrigió y fusionó mediante el PR #662. Se registraron dos incidencias nuevas de auditoría: #660 con un arreglo terminado sin fusionar (lista para PR), #659 a la espera de una decisión genuina del propietario sobre los hallazgos propuestos. Estado en vivo: 4 incidencias abiertas.
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
