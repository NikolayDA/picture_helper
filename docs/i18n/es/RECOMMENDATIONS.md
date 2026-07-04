[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · **Español** · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Análisis de código y recomendaciones priorizadas: BgRemover

## Escala de valoración

| Símbolo | Prioridad | Significado |
|---------|-----------|-------------|
| 🔴 | Crítica | Errores, cierres inesperados o pérdida de datos |
| 🟠 | Alta | Impacto claro en la fiabilidad o el mantenimiento |
| 🟡 | Media | Mejora útil de calidad, legibilidad o testabilidad |
| 🟢 | Baja | Pulido opcional o mejora de proceso |

## Estado actual (2026-07-05)

La lista activa de análisis de código está vacía. Ruff, mypy y la suite de
pruebas local siguen siendo la base antes de nuevos PR. Desde la instantánea
del 2026-07-04, el grupo Dark Mode/prototipo **#474–#480** (PR #482) y la ola de
iconos del rail/colores de estado **#483–#488** (PR #489) están cerrados.
Antes de este seguimiento, GitHub muestra **12** incidencias abiertas incluida
**#490**; tras fusionar/cerrar esta corrección de instantánea quedarán **11**
incidencias de roadmap/backlog.

### Completado desde la última revisión

- **Base antigua estable:** **N1/N2/N4/N5/N6/N7/N8** y **O2–O7** siguen hechos;
  los epics **#329/#344/#358/#384** (N9–N12) más la corrección de exportación
  **#363** están fusionados, cubiertos por pruebas/CI y archivados.
- **Cerrados desde la revisión del 2026-06-25:** **#404**, **#406** y **#408**
  (PR #412) — los hallazgos de vista previa/código muerto/auditoría ya están
  hechos; `_derive_physical_size` ya no existe y la ruta de render degrada a
  COLOR ante un desajuste de tamaño.
- **Núcleo del rediseño entregado:** la barra de pasos/`stepper.py`, el inspector
  de tarjetas, la navegación guiada, las herramientas contextuales y los tokens
  de diseño (`ACCENT`/`CARD_STYLE`) llegaron con PR #412/#423 (cadenas DE/EN,
  `tests/test_workflow.py`).
- **Ola rail/zoom completada:** **#455/#456/#457/#458/#463/#464** llegaron con
  PR #466, y **#465** está intencionadamente como `not_planned`; PR #467 cerró
  los tres P2 de #466 y actualizó la instantánea de triage.
- **Inspector de tarjetas completado:** **#414** llegó con PR #473 (tokens
  `CARD_*` centrales, estilo de tarjeta claro/oscuro, guard contra hex de
  acento). Con ello también queda completado el epic **#413**.
- **Dark Mode e iconos rail completados:** PR #482 cerró **#474–#480**
  (fondos dark, hairlines, acentos, checkerboard, tokens faltantes, drift-test
  de REDESIGN_SPEC); PR #489 cerró **#483–#488** (iconos vectoriales,
  colores de estado/tema, PNG fallback eliminados, docs/tests/revisión).
- **#490 en curso:** Este PR corrige el drift de la instantánea Recommendations
  tras PR #482/#489 y mantiene sincronizados los seis espejos de idioma.

### Aún abierto

- **O1 🟠 — Más idiomas en tiempo de ejecución.** Alemán e inglés son
  conmutables; es/fr/uk/zh aún no son locales de ejecución. Coincide con la
  incidencia de rediseño **#430** — añadirlos clave por clave en `bgremover.i18n`
  y cubrirlos con pruebas.
- **O8 🟢 — Imprecisión del prototipo: las herramientas de altura quedan
  bloqueadas tras generarla.** En `design/Prototyp A - Geführter Workflow.dc.html`,
  «Generar mapa de altura desde la imagen» solo activa `heightGen` sin cambiar
  la capa activa al rol `Höhe` — `heightDisabled` sigue dependiendo del rol
  anterior (hallazgo de revisión en el PR #460). Solo afecta a la simulación
  del mockup; la app real ya activa automáticamente la nueva capa HEIGHT (#347).

## Incidencias abiertas de GitHub — Clasificación (2026-07-05)

A fecha del 2026-07-05, GitHub muestra **12** incidencias abiertas antes de
este PR, incluida **#490**. Tras fusionar/cerrar este seguimiento quedarán
**11** incidencias de roadmap/backlog: i18n/docs (**#425/#430/#431/#432**),
rollout/publicación (**#426/#435/#392/#389**) y backlog/puntos externos
(**#299/#318/#245**).

### Agrupaciones sensatas

- **#490:** Este PR cierra el drift de instantánea tras PR #482/#489; no queda
  un ticket de implementación derivado.
- **i18n/docs (#425):** #430 (ES/FR/UK/ZH) desbloquea las pruebas de paridad; #431
  (docs) y #432 (capturas) siguen cuando la UI sea visualmente definitiva.
- **Rollout/publicación:** #426 queda abierto solo por #435; coordinar #435 con
  #392 y después cerrar #426/#389.
- **Backlog:** abordar #299 tras la publicación; refinar primero #318; #245
  sigue bloqueado externamente por billing/cuota de OpenAI.

Valoración: **Relevancia** = importancia para la hoja de ruta/usuarios,
**Complejidad** = esfuerzo de implementación estimado.

| # | Título | Relevancia | Complejidad | Próximo paso recomendado |
|---|--------|------------|-------------|--------------------------|
| [#490](https://github.com/NikolayDA/picture_helper/issues/490) | Actualizar snapshot de triage tras Dark Mode e iconos rail | 🟡 Media | 🟢 Baja | **Este PR** – cerrar tras merge. |
| [#425](https://github.com/NikolayDA/picture_helper/issues/425) | EPIC: Internacionalización y documentación | 🟠 Alta | 🟡 Media | **En curso** – #430/#431/#432 abiertos. |
| [#430](https://github.com/NikolayDA/picture_helper/issues/430) | Nuevas cadenas de UI (pasos/tarjetas/navegación) | 🟠 Alta | 🟡 Media | **Listo para PR** – ES/FR/UK/ZH; DE/EN vía PR #423. |
| [#431](https://github.com/NikolayDA/picture_helper/issues/431) | Actualizar ANLEITUNG y README al flujo guiado | 🟡 Media | 🟡 Media | **Tras congelar la UI** – espejo en 6 idiomas. |
| [#432](https://github.com/NikolayDA/picture_helper/issues/432) | Rehacer capturas de la app para el rediseño | 🟢 Baja | 🟢 Baja | **Bloqueado** – solo con la UI visualmente final. |
| [#426](https://github.com/NikolayDA/picture_helper/issues/426) | EPIC: QA y despliegue del rediseño | 🟠 Alta | 🟢 Baja | **Casi hecho** – solo #435 queda abierto. |
| [#435](https://github.com/NikolayDA/picture_helper/issues/435) | CHANGELOG y subida de versión del rediseño | 🟡 Media | 🟢 Baja | **Alinear con #392** – definir la secuencia. |
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | Publicar la versión v2.5.0 | 🟠 Alta | 🟡 Media | **Lista** – decidir la secuencia con el rediseño. |
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | EPIC: Actualizar docs de usuario y publicar | 🟠 Alta | 🟢 Baja | **Cerrar tras #392** – solo queda publicar. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Higiene de pruebas: aserciones débiles/redundancias | 🟢 Baja | 🟢 Baja | **Tras la publicación** – mayor impacto primero. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Overrides de permisos por job en WF reutilizable | 🟢 Baja | 🟡 Media | **Necesita refinamiento** – probar semántica GitHub. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan «Quota exceeded» | 🟡 Media | 🟢 Baja | **Bloqueado (externo)** – facturación/cuota OpenAI. |

### Recomendado a continuación (orden de PR)

1. Adelantar **#430** (cadenas ES/FR/UK/ZH) — desbloquea la paridad i18n; luego
   **#431**/**#432** cuando la UI sea definitiva.
2. **Publicación:** ejecutar **#435** + **#392** de forma coordinada, luego cerrar
   los epics **#426** y **#389**.
3. **#299** tras la publicación; investigar solo **#318** (necesita refinamiento);
   mantener **#245** bloqueado externamente.

## Rondas anteriores

- **Clasificación 2026-06-29** — #404/#406/#408 completados (PR #412), ola de rediseño abierta.
- **v2.2, «admiring-mayer» (#1–#15)** — lista externa, completada o descartada donde era un falso positivo.

Hallazgos históricos y registros de trabajo (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).
