[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · **Español** · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Análisis de código y recomendaciones priorizadas: BgRemover

## Escala de valoración

| Símbolo | Prioridad | Significado |
|---------|-----------|-------------|
| 🔴 | Crítica | Errores, cierres inesperados o pérdida de datos |
| 🟠 | Alta | Impacto claro en la fiabilidad o el mantenimiento |
| 🟡 | Media | Mejora útil de calidad, legibilidad o testabilidad |
| 🟢 | Baja | Pulido opcional o mejora de proceso |

## Estado actual (2026-07-23, release v2.7.0 publicado)

Ruff, mypy y la suite de pruebas local siguen siendo la base antes de nuevos PR. Desde la última ronda se ha completado por entero el ciclo de release v2.7.0:

1. **PR #670** (incremento de versión de `pyproject.toml`/`LICENSES.md`/`de.bgremover.app.metainfo.xml` a 2.7.0, traslado del CHANGELOG `[Unreleased]` → `[2.7.0]`, entrada del icono #667, conciliación de RECOMMENDATIONS) se fusionó (commit squash `6f103ed` en `main`).
2. Como la fusión squash produjo un SHA de commit **nuevo** (distinto del `245f727` ya validado), el gate de candidato completo se **repitió** contra `6f103ed` — exactamente la regla documentada en `docs/history/RELEASE-2.6.0-candidate-gate.md` («nota para #585»): matriz de CI completa (ejecución [29989059554](https://github.com/NikolayDA/picture_helper/actions/runs/29989059554), en verde), build de candidato (ejecución [29990198925](https://github.com/NikolayDA/picture_helper/actions/runs/29990198925), las tres plataformas en verde, escaneo de secretos limpio), aceptación de hardware (ejecución [29991314117](https://github.com/NikolayDA/picture_helper/actions/runs/29991314117): macOS arm64 ✅, Linux aarch64 ✅, x86_64 documentado como pausado, matriz de aceptación publicada en #595).
3. Se creó y empujó la etiqueta `v2.7.0` sobre `6f103ed` (tuvo que hacerlo el propio propietario del repositorio — el proxy de git de esta sesión solo permite empujar hacia la rama de trabajo asignada, no etiquetas ni `main`). La ejecución del workflow de release [29998307692](https://github.com/NikolayDA/picture_helper/actions/runs/29998307692) quedó en verde, el job `Publish GitHub Release` tuvo éxito: **[v2.7.0](https://github.com/NikolayDA/picture_helper/releases/tag/v2.7.0)** publicado con los cinco artefactos (AppImage + `.deb` de Linux x86_64/aarch64, `.dmg` de macOS arm64).

Además, desde el último snapshot han aparecido dos nuevas incidencias de auditoría automatizada:

- **#669** — señala con razón que el estado en vivo anterior de este documento estaba desactualizado (aún listaba #659/#660 como abiertas, faltaba #668). Corregido con esta actualización.
- **#668** — `ANLEITUNG.md` todavía referencia el conjunto de capturas del 2026-07-19 en lugar del actual del 2026-07-22 (una laguna derivada de #666); pura higiene de repositorio, sin error de contenido en la guía en sí. **Corrección (revisión de Codex en el PR #671):** el conjunto no está totalmente huérfano — `README.md` (en los seis idiomas) y `docs/history/EPIC-582-ABNAHME.md` también referencian archivos en él; un arreglo debe migrar todas las referencias restantes o conservar el directorio antiguo, no simplemente eliminarlo.

Estado en vivo: **4** incidencias abiertas (#669, #668, #656, #245) — las cuatro son de higiene documental o puramente externas/operativas, ningún bloqueo de código.

### Resultado de la revisión

- **Base antigua estable:** **N1/N2/N4/N5/N6/N7/N8/N9**, **O1–O8** y todo lo completado desde el **2026-06-25** sigue hecho.
- **El release v2.7.0 está completamente cerrado y verificado:** la etiqueta, la publicación y las tres etapas del gate (matriz de CI, build de candidato, aceptación de hardware) se ejecutaron contra el commit realmente etiquetado `6f103ed` — sin deriva entre lo verificado y lo publicado.
- **#669 queda resuelta con esta actualización**; **#668** es una pequeña tarea de limpieza documental bien acotada (fecha incorrecta del conjunto de capturas en una referencia, análoga a la ya resuelta #638), no es un bloqueo.
- **#656/#245** siguen siendo, sin cambios, trackers puramente externos/operativos sin relación con el código.

## Incidencias abiertas de GitHub — Clasificación (2026-07-23)

| # | Título | Relevancia | Complejidad | Modelo recomendado (esfuerzo) | Próximo paso |
|---|--------|------------|-------------|--------------------------------|--------------|
| [#669](https://github.com/NikolayDA/picture_helper/issues/669) | Estado en vivo de RECOMMENDATIONS.md desactualizado (#659/#660 aún listadas como abiertas, faltaba #668) | 🟢 Baja (pura precisión documental, sin impacto funcional) | 🟢 Baja (corregido con esta actualización) | – (no hace falta agente) | Hecho con esta actualización — la incidencia puede cerrarse |
| [#668](https://github.com/NikolayDA/picture_helper/issues/668) | ANLEITUNG.md referencia un conjunto de capturas desactualizado (20260719 en vez de 20260722) | 🟢 Baja (higiene de repositorio, sin error de contenido) | 🟢 Baja (consolidar referencias en ANLEITUNG.md **y** README.md/EPIC-582-ABNAHME.md; eliminar el conjunto solo tras una migración completa — según la revisión de Codex no está totalmente huérfano) | Sonnet 5 (baja) | Ready for PR – arreglo pequeño e independiente posible |
| [#656](https://github.com/NikolayDA/picture_helper/issues/656) | Activar el secreto ANTHROPIC_API_KEY para la evaluación previa por visión | 🟡 Media (solo mejora la calidad de la evidencia; no es un bloqueo según el contrato) | 🟢 Baja (puramente operativo, sin código) | – (sin agente; propietario del repo: Settings → Secrets) | Bloqueada (externa) – se puede hacer de forma independiente |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restaurar la cuota de OpenAI para la comprobación manual de Codex Security | 🟢 Baja (solo bloquea un escaneo manual opcional) | 🟢 Baja (puramente operativo, sin código) | – (sin agente; propietario del repo: facturación) | Bloqueada (externa) – resolver facturación/cuota en el proyecto de la plataforma OpenAI |

### Recomendado a continuación

1. Cerrar **#669** — el estado en vivo está al día tras esta actualización.
2. Implementar **#668** como un PR pequeño e independiente: migrar todas las referencias restantes al conjunto del 2026-07-19 (`ANLEITUNG.md` + traducciones, pero también `README.md` + traducciones y `docs/history/EPIC-582-ABNAHME.md`) al conjunto del 2026-07-22 antes de eliminar el antiguo — no está totalmente huérfano (corrección tras la revisión de Codex en el PR #671).
3. Gestionar **#656** de forma independiente si se desean veredictos de visión reales — es una mejora de calidad, no un bloqueo.
4. Dejar **#245** como tracker puramente externo de facturación/cuota; no hay ninguna acción posible ni necesaria en el repositorio.
5. El release v2.7.0 está completamente publicado — no hace falta ningún paso adicional relacionado con el release.

## Rondas anteriores

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
