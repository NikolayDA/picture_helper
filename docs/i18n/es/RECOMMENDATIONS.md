[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · **Español** · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Análisis de código y recomendaciones priorizadas: BgRemover

## Escala de valoración

| Símbolo | Prioridad | Significado |
|---------|-----------|-------------|
| 🔴 | Crítica | Errores, cierres inesperados o pérdida de datos |
| 🟠 | Alta | Impacto claro en la fiabilidad o el mantenimiento |
| 🟡 | Media | Mejora útil de calidad, legibilidad o testabilidad |
| 🟢 | Baja | Pulido opcional o mejora de proceso |

## Estado actual (2026-07-04)

La lista activa de análisis de código está vacía. Ruff, mypy y la suite de
pruebas local siguen siendo la base antes de nuevos PR. Novedad de esta ronda:
**#461**, **#414** y el epic **#413** quedan cerrados. El PR #473 centraliza las
métricas de tarjeta y elimina el último hex de acento fuera de `theme.py`.
El nuevo grupo abierto de alineación Dark Mode/prototipo es **#474–#480**.
GitHub muestra ahora **18** incidencias abiertas de roadmap/backlog.

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
  PR #466, y **#465** está intencionadamente como `not_planned`. El PR #467
  cierra los tres P2 tardíos de #466 (dirección de zoom, anclaje al viewport,
  vista previa de dabs de altura) y actualizó la instantánea de triage.
- **#461 cerrada (2026-07-04):** La instantánea actualizada por el PR #467
  coincide con el estado real de GitHub; la incidencia en sí quedó abierta tras
  la fusión y se cierra en esta ronda.
- **Inspector de tarjetas completado:** **#414** llegó con PR #473 (tokens
  `CARD_*` centrales, estilo de tarjeta claro/oscuro, guard contra hex de
  acento). Con ello también queda completado el epic **#413**.

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

## Incidencias abiertas de GitHub — Clasificación (2026-07-04)

A fecha del 2026-07-04, GitHub muestra **18** incidencias abiertas de
roadmap/backlog: alineación Dark Mode/prototipo
(**#474/#475/#476/#477/#478/#479/#480**), i18n/docs (**#425/#430/#431/#432**),
rollout/publicación (**#426/#435/#392/#389**) y los puntos independientes
**#299/#318/#245**. **#461** era la deriva de instantánea ya resuelta; **#414**
y **#413** también quedan cerrados tras PR #473.

### Agrupaciones sensatas

- **Dark Mode 1:1 (#474):** agrupar #475/#476/#477/#479 como ola de tokens, #478
  como arreglo del checker de canvas y #480 como cierre spec/test de drift.
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
| [#474](https://github.com/NikolayDA/picture_helper/issues/474) | EPIC: Dark Mode 1:1 con Prototipo A | 🟠 Alta | 🟡 Media | **Nuevo** – agrupar #475–#480. |
| [#475](https://github.com/NikolayDA/picture_helper/issues/475) | Dark: alinear superficies de fondo | 🟠 Alta | 🟢 Baja | **Empezar aquí** – bases primero. |
| [#476](https://github.com/NikolayDA/picture_helper/issues/476) | Dark: bordes/hairlines transparentes | 🟡 Media | 🟢 Baja | **Con #475** – tokens de borde. |
| [#477](https://github.com/NikolayDA/picture_helper/issues/477) | Dark: alinear acentos/botones | 🟠 Alta | 🟢 Baja | **Con #475** – colores interactivos. |
| [#478](https://github.com/NikolayDA/picture_helper/issues/478) | Checker del canvas ignora el tema | 🟡 Media | 🟡 Media | **Tras tokens** – paleta + cambio de tema. |
| [#479](https://github.com/NikolayDA/picture_helper/issues/479) | Añadir tokens de color faltantes | 🟡 Media | 🟡 Media | **Con spec** – solo tokens probados. |
| [#480](https://github.com/NikolayDA/picture_helper/issues/480) | Tablas de color REDESIGN_SPEC + test drift | 🟡 Media | 🟡 Media | **Cierre final** – tras #475–#479. |
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

1. Agrupar **#474**: ola de tokens #475/#476/#477/#479, luego #478 y #480.
2. Adelantar **#430** (cadenas ES/FR/UK/ZH) — desbloquea la paridad i18n; luego
   **#431**/**#432** cuando la UI sea definitiva.
3. **Publicación:** ejecutar **#435** + **#392** de forma coordinada, luego cerrar
   los epics **#426** y **#389**.
4. **#299** tras la publicación; investigar solo **#318** (necesita refinamiento);
   mantener **#245** bloqueado externamente.

## Rondas anteriores

- **Clasificación 2026-06-29** — #404/#406/#408 completados (PR #412), ola de rediseño abierta.
- **v2.2, «admiring-mayer» (#1–#15)** — lista externa, completada o descartada donde era un falso positivo.

Hallazgos históricos y registros de trabajo (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).
