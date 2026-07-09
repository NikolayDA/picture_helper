[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · **Español** · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Análisis de código y recomendaciones priorizadas: BgRemover

## Escala de valoración

| Símbolo | Prioridad | Significado |
|---------|-----------|-------------|
| 🔴 | Crítica | Errores, cierres inesperados o pérdida de datos |
| 🟠 | Alta | Impacto claro en la fiabilidad o el mantenimiento |
| 🟡 | Media | Mejora útil de calidad, legibilidad o testabilidad |
| 🟢 | Baja | Pulido opcional o mejora de proceso |

## Estado actual (2026-07-09)

La lista activa de análisis de código está vacía. Ruff, mypy y la suite de
pruebas local siguen siendo la base antes de nuevos PR. Desde la instantánea
del 2026-07-06 se cerraron los tres seguimientos de rediseño
**#499/#500/#501** (PR #504) y el hallazgo de código muerto **#503** (PR
#506; #505 fue un merge accidental con diff vacío, el contenido llegó con
#506); además, el pulido de iconos/barra de estado **PR #507/#508**. Son
nuevos el bug de UI **#509** (el cursor de herramienta ignora el zoom del
lienzo) y **#510** (este refresco de instantánea). GitHub muestra
actualmente **13** incidencias abiertas.

### Completado desde la última revisión

- **Base antigua estable:** **N1/N2/N4/N5/N6/N7/N8** y **O2–O7** siguen
  hechos; los epics **#329/#344/#358/#384** (N9–N12) más la corrección de
  exportación **#363** están fusionados y archivados.
- **Cerrados desde la revisión del 2026-06-25:** **#404/#406/#408** (PR #412)
  — hallazgos de vista previa/código muerto/auditoría hechos.
- **Núcleo del rediseño, rail/zoom, inspector de tarjetas, Dark Mode:**
  **#413/#414/#455–#464/#474–#489** llegaron con PR #412/#423/#466/#467/#473/
  #482/#489; **#490** y **#433/#434** también (el epic **#426** ahora solo
  depende de **#435**).
- **Cerrados desde el 2026-07-06:** **#499/#500/#501** (PR #504 — esquema
  claro alineado al prototipo, generador de capturas reparado, widgets
  muertos eliminados; el bloqueo de #500 ante **#432** ha caído) y **#503**
  (PR #506 — `CanvasHistory`/`_make_panel_btn`/constantes de tema muertas
  eliminadas).

### Nuevo desde la última revisión

- **#509 🟠:** el cursor de pincel/goma no escala con el zoom del lienzo —
  tamaño mostrado ≠ área realmente afectada (también afecta a los pinceles
  de altura; causa localizada en `set_tool`/`set_brush_size`).
- **#510 🟢:** la instantánea de triaje quedó superada por el PR #504
  fusionado 30 minutos después — resuelto con esta actualización.

### Aún abierto

- **O1 🟠 — Más idiomas en tiempo de ejecución.** DE/EN son conmutables;
  es/fr/uk/zh aún faltan como locales de ejecución (coincide con **#430**).
- **O8 🟢 — Imprecisión del prototipo:** las herramientas de altura quedan
  bloqueadas en el mockup tras generarla; solo afecta a la simulación (#347).

## Incidencias abiertas de GitHub — Clasificación (2026-07-09)

A fecha del 2026-07-09, GitHub muestra **13** incidencias abiertas: bug de
UI (**#509**), esta instantánea de docs (**#510**), i18n/docs
(**#425/#430/#431/#432**), rollout/publicación (**#426/#435/#392/#389**) y
backlog/puntos externos (**#299/#318/#245**).

### Agrupaciones sensatas

- **Bug de UI:** #509 está localizado con precisión (el cursor nunca se
  recalcula en `zoomChanged`) y es el único hallazgo de código abierto —
  buen próximo PR.
- **i18n/docs:** #430 desbloquea las pruebas de paridad; #431/#432 siguen
  tras el UI freeze (el bloqueo de #500 ante #432 cayó con el PR #504).
- **Rollout/publicación:** #426 depende solo de #435; coordinar con #392 y
  luego cerrar #426/#389.
- **Backlog:** #299 tras la publicación; refinar #318 primero; #245 sigue
  bloqueado externamente.

Valoración: **Relevancia** = importancia para la hoja de ruta/usuarios,
**Complejidad** = esfuerzo de implementación estimado.

| # | Título | Relevancia | Complejidad | Próximo paso recomendado |
|---|--------|------------|-------------|--------------------------|
| [#509](https://github.com/NikolayDA/picture_helper/issues/509) | El cursor de pincel/goma ignora el zoom del lienzo | 🟠 Alta | 🟡 Media | **Listo para PR** – reescalar el cursor en `zoomChanged`/cambios de tamaño. |
| [#510](https://github.com/NikolayDA/picture_helper/issues/510) | Instantánea de triaje desactualizada (2026-07-06) | 🟢 Baja | 🟢 Baja | **En curso** – esta instantánea lo resuelve. |
| [#425](https://github.com/NikolayDA/picture_helper/issues/425) | EPIC: Internacionalización y documentación | 🟠 Alta | 🟡 Media | **En curso** – #430/#431/#432 abiertos. |
| [#430](https://github.com/NikolayDA/picture_helper/issues/430) | Nuevas cadenas de UI (pasos/tarjetas/navegación) | 🟠 Alta | 🟡 Media | **Listo para PR** – ES/FR/UK/ZH; DE/EN vía PR #423. |
| [#431](https://github.com/NikolayDA/picture_helper/issues/431) | Actualizar ANLEITUNG y README al flujo guiado | 🟡 Media | 🟡 Media | **Tras congelar la UI** – espejo en 6 idiomas. |
| [#432](https://github.com/NikolayDA/picture_helper/issues/432) | Rehacer capturas de la app para el rediseño | 🟢 Baja | 🟢 Baja | **Tras congelar la UI** – bloqueo de #500 caído (PR #504). |
| [#426](https://github.com/NikolayDA/picture_helper/issues/426) | EPIC: QA y despliegue del rediseño | 🟠 Alta | 🟢 Baja | **Casi hecho** – solo #435 queda abierto. |
| [#435](https://github.com/NikolayDA/picture_helper/issues/435) | CHANGELOG y subida de versión del rediseño | 🟡 Media | 🟢 Baja | **Alinear con #392** – definir la secuencia. |
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | Publicar la versión v2.5.0 | 🟠 Alta | 🟡 Media | **Lista** – decidir la secuencia con el rediseño. |
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | EPIC: Actualizar docs de usuario y publicar | 🟠 Alta | 🟢 Baja | **Cerrar tras #392** – solo queda publicar. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Higiene de pruebas: aserciones débiles/redundancias | 🟢 Baja | 🟢 Baja | **Tras la publicación** – mayor impacto primero. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Overrides de permisos por job en WF reutilizable | 🟢 Baja | 🟡 Media | **Necesita refinamiento** – probar semántica GitHub. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan «Quota exceeded» | 🟡 Media | 🟢 Baja | **Bloqueado (externo)** – facturación/cuota OpenAI. |

### Recomendado a continuación (orden de PR)

1. **#509** primero — único bug de código abierto, causa ya localizada.
2. Adelantar **#430** — desbloquea la paridad i18n; luego **#431**/**#432**.
3. **Publicación:** ejecutar **#435** + **#392** de forma coordinada, luego
   cerrar **#426**/**#389**.
4. **#299** tras la publicación; investigar solo **#318**; mantener **#245**
   bloqueado externamente.

## Rondas anteriores

- **2026-07-06** — #499/#500/#501 (PR #504) y #503 (PR #506) completados;
  pulido de iconos/barra de estado vía PR #507/#508.
- **2026-07-05** — #490 (drift de instantánea) en curso, ola de Dark
  Mode/iconos rail e inspector de tarjetas (#413/#414) completados.
- **2026-06-29** — #404/#406/#408 completados (PR #412), ola de rediseño abierta.
- **v2.2, «admiring-mayer» (#1–#15)** — lista externa, completada o descartada donde era un falso positivo.

Hallazgos históricos y registros de trabajo (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).
