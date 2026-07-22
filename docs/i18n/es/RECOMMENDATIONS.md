[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · **Español** · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Análisis de código y recomendaciones priorizadas: BgRemover

## Escala de valoración

| Símbolo | Prioridad | Significado |
|---------|-----------|-------------|
| 🔴 | Crítica | Errores, cierres inesperados o pérdida de datos |
| 🟠 | Alta | Impacto claro en la fiabilidad o el mantenimiento |
| 🟡 | Media | Mejora útil de calidad, legibilidad o testabilidad |
| 🟢 | Baja | Pulido opcional o mejora de proceso |

## Estado actual (2026-07-22, tras el cierre de la aceptación)

Ruff, mypy y la suite de pruebas local siguen siendo la base antes de nuevos PR. El despacho nuevo de `release-abnahme.yml` solicitado en la ronda anterior se lanzó (ejecución [#4](https://github.com/NikolayDA/picture_helper/actions/runs/29908256619), commit `9165c00`, tras #657/#658) y produjo una matriz totalmente en verde salvo la fila Linux x86_64 deliberadamente pausada. A partir de ahí, las cuatro incidencias antes bloqueadas se **verificaron y cerraron individualmente contra sus propios criterios de aceptación** — ninguna se cerró automáticamente junto con otra:

1. **#595** — se cumplen todos los puntos de la lista "sigue abierto" **excepto** la fila Linux x86_64 deliberadamente pausada: según el ADR/`RELEASE_AUTOMATION.md` sigue "declarada abierta, no cumplida" — para este cierre se trató explícitamente como una excepción dispensada (waiver), no como si se hubiera cumplido (reflejando el propio criterio de aceptación de #639).
2. **#646** — cinco de seis criterios ya se cumplían; se encontró una laguna real: `scripts/abnahme_vision_check.py`/`abnahme_aggregate.py` estaban completamente excluidos de `make type`/`make check`, y una ejecución estricta de prueba reveló un error `union-attr` genuino. Corregido y fusionado mediante el PR #662 (commit `f47445f`).
3. **#639** — con #646 cerrado, las ocho incidencias secundarias están cerradas; la lista de verificación del cuerpo se ha conciliado.
4. **#582** — las cinco incidencias secundarias están cerradas; la decisión requerida sobre la textura como objetivo opcional ya existe en el ADR, la laguna del README de la auditoría del 2026-07-20 está corregida, y se confirmó que `make ui` está en verde.

Además, desde la última ronda han aparecido dos incidencias nuevas de auditorías automatizadas: **#660** ya está terminada y solo falta fusionarla, mientras que **#659** sí espera genuinamente una decisión del propietario.

Estado en vivo: **4** incidencias abiertas.

### Resultado de la revisión

- **Base antigua estable:** **N1/N2/N4/N5/N6/N7/N8**, **O1–O7** y todo lo completado desde el **2026-06-25** sigue hecho.
- **#646/#639/#595/#582 ya están verificadas individualmente y cerradas** (sin efecto dominó de cierre automático); la única laguna real encontrada en el proceso (rigor de mypy para los scripts de aceptación, #646) se corrigió y fusionó mediante el PR #662.
- **#659/#660 son nuevas:** #660 está **lista para PR** – ya tiene un arreglo terminado pero sin fusionar en la rama `claude/festive-gates-4dkzds` (commit `80b7aa0`); ahí no queda nada por decidir, solo por fusionar. #659, en cambio, sí sigue **genuinamente sin decidir**: un análisis puro sin cambios de código que propone dos identificadores de hallazgo nuevos (**N9**/**O8**), aún pendientes de aprobación del propietario.
- El paso restante ya **no** es un tema de aceptación — es abrir/fusionar un PR para #660 y obtener una decisión sobre los hallazgos propuestos en #659.

## Incidencias abiertas de GitHub — Clasificación (2026-07-22)

| # | Título | Relevancia | Complejidad | Modelo recomendado (esfuerzo) | Próximo paso |
|---|--------|------------|-------------|--------------------------------|--------------|
| [#660](https://github.com/NikolayDA/picture_helper/issues/660) | Auditoría de TESTING.md: actualizado, una pequeña laguna corregida (marcador `gl_smoke` sin documentar) | 🟢 Baja (pura precisión documental, sin impacto funcional) | 🟢 Baja (un párrafo breve, ya implementado) | – (no hace falta agente; el arreglo ya está en la rama `claude/festive-gates-4dkzds`, commit `80b7aa0`) | Ready for PR – solo falta abrirlo/fusionarlo y cerrar la incidencia |
| [#659](https://github.com/NikolayDA/picture_helper/issues/659) | Auditoría de la suite de pruebas: pequeñas lagunas de calidad en 6 lotes (`test_i18n_sync`, `test_viewer_3d`, etc.) | 🟡 Media (calidad/cobertura de pruebas, no es un bloqueo) | 🟡 Media (mezcla de eliminaciones/arreglos triviales y lagunas de cobertura reales en varios módulos) | Sonnet 5 (medio) – si se adopta como N9/O8 | Needs decision – la propuesta aún no se ha incorporado a la lista de hallazgos; pendiente de aprobación del propietario, después implementar como PR propio |
| [#656](https://github.com/NikolayDA/picture_helper/issues/656) | Activar el secreto ANTHROPIC_API_KEY para la evaluación previa por visión | 🟡 Media (solo mejora la calidad de la evidencia; no es un bloqueo según el contrato) | 🟢 Baja (puramente operativo, sin código) | – (sin agente; propietario del repo: Settings → Secrets) | Bloqueada (externa) – se puede hacer de forma independiente |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restaurar la cuota de OpenAI para la comprobación manual de Codex Security | 🟢 Baja (solo bloquea un escaneo manual opcional) | 🟢 Baja (puramente operativo, sin código) | – (sin agente; propietario del repo: facturación) | Bloqueada (externa) – resolver facturación/cuota en el proyecto de la plataforma OpenAI |

### Recomendado a continuación

1. **#660**: abrir un PR para el arreglo de TESTING.md ya confirmado (rama `claude/festive-gates-4dkzds`, commit `80b7aa0`) y fusionarlo; después cerrar la incidencia.
2. **#659**: decidir si se adoptan los hallazgos propuestos **N9** (eliminar/fusionar el peso muerto `test_i18n_sync.py`) y **O8** (aserciones tautológicas en `viewer_3d` más lagunas de cobertura en `screenshot3d.py`/`viewer_3d.py`/`preview3d_capability.py`/`height_map.py`/`gloss_preview.py`); implementar como PR propio si se aprueba.
3. Gestionar **#656** de forma independiente si se desean veredictos de visión reales — es una mejora de calidad, no un bloqueo.
4. Dejar **#245** como tracker puramente externo de facturación/cuota; no hay ninguna acción posible ni necesaria en el repositorio.
5. La cadena de aceptación/epic 3D (#646/#639/#595/#582) está completamente cerrada y no necesita ninguna acción adicional.

## Rondas anteriores

- **2026-07-22 (cierre de la aceptación)** — se lanzó un despacho nuevo de `release-abnahme.yml` (ejecución #4, commit `9165c00`); se contrastó la matriz con #595 (x86_64 sigue documentada como pausada pero no bloquea); se verificaron y cerraron individualmente #595, #646, #639 y #582 contra sus propios criterios de aceptación. La única laguna real encontrada (rigor de mypy para `scripts/abnahme_vision_check.py`/`abnahme_aggregate.py`, #646) se corrigió y fusionó mediante el PR #662. Se registraron dos incidencias nuevas de auditoría: #660 con un arreglo terminado sin fusionar (lista para PR), #659 a la espera de una decisión genuina del propietario sobre los hallazgos propuestos. Estado en vivo: 4 incidencias abiertas — el nivel más bajo desde que existe este registro.
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
