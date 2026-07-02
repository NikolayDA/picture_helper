[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · **Español** · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Análisis de código y recomendaciones priorizadas: BgRemover

## Escala de valoración

| Símbolo | Prioridad | Significado |
|---------|-----------|-------------|
| 🔴 | Crítica | Errores, cierres inesperados o pérdida de datos |
| 🟠 | Alta | Impacto claro en la fiabilidad o el mantenimiento |
| 🟡 | Media | Mejora útil de calidad, legibilidad o testabilidad |
| 🟢 | Baja | Pulido opcional o mejora de proceso |

## Estado actual (2026-07-02)

La lista activa de análisis de código está vacía. Ruff, mypy y la suite de
pruebas local siguen siendo la base antes de nuevos PR. Novedad de esta ronda:
la clasificación de incidencias abiertas se ha puesto al día (18 abiertas).

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
  `tests/test_workflow.py`); solo queda el pulido (véase la clasificación).

### Aún abierto

- **O1 🟠 — Más idiomas en tiempo de ejecución.** Alemán e inglés son
  conmutables; es/fr/uk/zh aún no son locales de ejecución. Coincide con la
  incidencia de rediseño **#430** — añadirlos clave por clave en `bgremover.i18n`
  y cubrirlos con pruebas.

## Incidencias abiertas de GitHub — Clasificación (2026-07-02)

A fecha del 2026-07-02, GitHub muestra **18** incidencias abiertas. La instantánea
del 2026-06-29 está obsoleta: #404/#406/#408 están cerradas (PR #412) y la **ola
de rediseño (flujo guiado)** es la hoja de ruta activa. Su núcleo ya se entregó;
queda el pulido (**#414**), i18n/docs (epic **#425**: #430/#431/#432), QA/despliegue
(epic **#426**: #433/#434/#435), la publicación pendiente **#392** y los puntos
independientes **#299/#318/#245**. **#442** rastrea exactamente esta actualización
de documentación.

**Repaso de comentarios:** Sin comentarios externos nuevos. Las notas del
propietario en #245/#299/#392 coinciden con el estado actual; #442 (2026-07-02)
recoge esta auditoría — no se necesita actualizar incidencias.

### Agrupaciones sensatas

- **Epics casi terminados:** #418 y #424 tienen **todas** las sub-incidencias
  cerradas → verificar y cerrar. #413 solo tiene #414 abierto; sus tokens ya
  están en `theme.py` — añadir el estilo de tarjeta claro y luego cerrarlo.
- **i18n/docs (#425):** #430 (ES/FR/UK/ZH) desbloquea las pruebas de paridad; #431
  (docs) y #432 (capturas) siguen cuando la UI sea visualmente definitiva.
- **QA/despliegue (#426):** #433 está muy cubierto por PR #423 (revisar el hueco,
  cerrar); #434 está listo para PR; alinear #435 (CHANGELOG/versión) con #392.
- **Publicación:** decidir si el rediseño sale en **v2.5.0** (#392/#435 juntos)
  o en un incremento posterior.

Valoración: **Relevancia** = importancia para la hoja de ruta/usuarios,
**Complejidad** = esfuerzo de implementación estimado.

| # | Título | Relevancia | Complejidad | Próximo paso recomendado |
|---|--------|------------|-------------|--------------------------|
| [#418](https://github.com/NikolayDA/picture_helper/issues/418) | EPIC: Flujo guiado – barra de pasos y navegación | 🟠 Alta | 🟢 Baja | **Verificar y cerrar** – sub-incidencias cerradas (PR #423). |
| [#413](https://github.com/NikolayDA/picture_helper/issues/413) | EPIC: Inspector de tarjetas – columna derecha | 🟠 Alta | 🟢 Baja | **Casi hecho** – solo #414 abierto. |
| [#414](https://github.com/NikolayDA/picture_helper/issues/414) | Centralizar contenedor de tarjeta y tokens de acento | 🟡 Media | 🟢 Baja | **Listo para PR** – tokens ya existen; falta estilo claro. |
| [#424](https://github.com/NikolayDA/picture_helper/issues/424) | EPIC: Sistema de diseño unificado y theming | 🟠 Alta | 🟢 Baja | **Verificar y cerrar** – sub-incidencias cerradas. |
| [#425](https://github.com/NikolayDA/picture_helper/issues/425) | EPIC: Internacionalización y documentación | 🟠 Alta | 🟡 Media | **En curso** – #430/#431/#432 abiertos. |
| [#430](https://github.com/NikolayDA/picture_helper/issues/430) | Nuevas cadenas de UI (pasos/tarjetas/navegación) | 🟠 Alta | 🟡 Media | **Listo para PR** – ES/FR/UK/ZH; DE/EN vía PR #423. |
| [#431](https://github.com/NikolayDA/picture_helper/issues/431) | Actualizar ANLEITUNG y README al flujo guiado | 🟡 Media | 🟡 Media | **Tras congelar la UI** – espejo en 6 idiomas. |
| [#432](https://github.com/NikolayDA/picture_helper/issues/432) | Rehacer capturas de la app para el rediseño | 🟢 Baja | 🟢 Baja | **Bloqueado** – solo con la UI visualmente final. |
| [#426](https://github.com/NikolayDA/picture_helper/issues/426) | EPIC: QA y despliegue del rediseño | 🟠 Alta | 🟢 Baja | **En curso** – #433/#434/#435 abiertos. |
| [#433](https://github.com/NikolayDA/picture_helper/issues/433) | Pruebas de humo pasos/tarjetas/navegación | 🟡 Media | 🟢 Baja | **Revisar el hueco** – muy cubierto por PR #423. |
| [#434](https://github.com/NikolayDA/picture_helper/issues/434) | Regresión de visibilidad y cableado de acciones | 🟡 Media | 🟢 Baja | **Listo para PR** – callbacks de acción por paso. |
| [#435](https://github.com/NikolayDA/picture_helper/issues/435) | CHANGELOG y subida de versión del rediseño | 🟡 Media | 🟢 Baja | **Alinear con #392** – definir la secuencia. |
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | Publicar la versión v2.5.0 | 🟠 Alta | 🟡 Media | **Lista** – decidir la secuencia con el rediseño. |
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | EPIC: Actualizar docs de usuario y publicar | 🟠 Alta | 🟢 Baja | **Cerrar tras #392** – solo queda publicar. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Higiene de pruebas: aserciones débiles/redundancias | 🟢 Baja | 🟢 Baja | **Tras la publicación** – mayor impacto primero. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Overrides de permisos por job en WF reutilizable | 🟢 Baja | 🟡 Media | **Necesita refinamiento** – probar semántica GitHub. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan «Quota exceeded» | 🟡 Media | 🟢 Baja | **Bloqueado (externo)** – facturación/cuota OpenAI. |
| [#442](https://github.com/NikolayDA/picture_helper/issues/442) | RECOMMENDATIONS.md está desactualizado | 🟡 Media | 🟢 Baja | **Resuelto con esta actualización** – cerrable. |

### Recomendado a continuación (orden de PR)

1. **Mantenimiento:** verificar las sub-incidencias y cerrar los epics casi
   terminados **#418** y **#424**; terminar **#414** (estilo claro) y cerrar **#413**.
2. Adelantar **#430** (cadenas ES/FR/UK/ZH) — desbloquea la paridad i18n; luego
   **#431**/**#432** cuando la UI sea definitiva.
3. Implementar **#434** (regresión); confirmar la cobertura de **#433** de PR #423
   y cerrarla.
4. **Publicación:** ejecutar **#435** + **#392** de forma coordinada, luego cerrar
   los epics **#426** y **#389**.
5. **#299** tras la publicación; investigar solo **#318** (necesita refinamiento);
   mantener **#245** bloqueado; cerrar **#442** cuando aterrice esta actualización.

## Rondas anteriores

- **Clasificación 2026-06-29** — #404/#406/#408 completados (PR #412), ola de rediseño abierta.
- **v2.2, «admiring-mayer» (#1–#15)** — lista externa, completada o descartada donde era un falso positivo.

Hallazgos históricos y registros de trabajo (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).
