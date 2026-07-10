[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · **Español** · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Análisis de código y recomendaciones priorizadas: BgRemover

## Escala de valoración

| Símbolo | Prioridad | Significado |
|---------|-----------|-------------|
| 🔴 | Crítica | Errores, cierres inesperados o pérdida de datos |
| 🟠 | Alta | Impacto claro en la fiabilidad o el mantenimiento |
| 🟡 | Media | Mejora útil de calidad, legibilidad o testabilidad |
| 🟢 | Baja | Pulido opcional o mejora de proceso |

## Estado actual (2026-07-10)

La lista activa de análisis de código está vacía. Ruff, mypy y la suite de
pruebas local siguen siendo la base antes de nuevos PR. Desde la instantánea
del 2026-07-09, **#509** (zoom del cursor, PR #513) y **#510** (instantánea,
PR #512) están cerrados; después llegó la ola de seguimiento UI **#514–#517**
vía PR #518/#519 y el pulido de inspector/pista de scroll vía PR
#520/#521/#522. El benchmark del 2026-07-06 fue estable en lo técnico, pero
falló al hacer push directo al `main` protegido; este PR lo cambia a PRs de
baseline de benchmark. GitHub muestra actualmente **11** incidencias abiertas.

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
- **Cerrados desde el 2026-07-09:** **#509/#510** (PR #512/#513),
  **#514–#517** (PR #518/#519 — stepper, botón IA, steppers de SpinBox,
  segmentos de vista previa) y PR #520/#521/#522 (líneas del inspector,
  columna derecha, prueba de píxeles de la pista de scroll).

### Nuevo desde la última revisión

- **CI de benchmark 🟢:** El run semanal produjo un resultado estable, pero
  falló cuando un `git push` directo a `main` chocó con la protección de rama.
  El workflow ahora abre una rama de PR para nuevos JSON de baseline.

### Aún abierto

- **O1 🟠 — Más idiomas en tiempo de ejecución.** DE/EN son conmutables;
  es/fr/uk/zh aún faltan como locales de ejecución (coincide con **#430**).
- **O8 🟢 — Imprecisión del prototipo:** las herramientas de altura quedan
  bloqueadas en el mockup tras generarla; solo afecta a la simulación (#347).

## Incidencias abiertas de GitHub — Clasificación (2026-07-10)

A fecha del 2026-07-10, GitHub muestra **11** incidencias abiertas:
i18n/docs (**#425/#430/#431/#432**), rollout/publicación
(**#426/#435/#392/#389**) y backlog/puntos externos (**#299/#318/#245**).

### Agrupaciones sensatas

- **i18n/docs:** #430 desbloquea las pruebas de paridad; #431/#432 siguen
  tras el UI freeze (los bloqueos #500/#509/#514–#517 ya cayeron).
- **Rollout/publicación:** #426 depende solo de #435; coordinar con #392 y
  luego cerrar #426/#389.
- **Backlog:** #299 tras la publicación; refinar #318 primero; #245 sigue
  bloqueado externamente.

Valoración: **Relevancia** = importancia para la hoja de ruta/usuarios,
**Complejidad** = esfuerzo de implementación estimado.

| # | Título | Relevancia | Complejidad | Próximo paso recomendado |
|---|--------|------------|-------------|--------------------------|
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

1. Adelantar **#430** — desbloquea la paridad i18n; luego **#431**/**#432**.
2. **Publicación:** ejecutar **#435** + **#392** de forma coordinada, luego
   cerrar **#426**/**#389**.
3. **#299** tras la publicación; investigar solo **#318**; mantener **#245**
   bloqueado externamente.

## Rondas anteriores

- **2026-07-10** — #509/#510 cerrados, #514–#517 completados, seguimiento de
  la columna derecha cerrado vía PR #520/#521/#522; workflow de baseline de
  benchmark cambiado a PRs en vez de push directo.
- **2026-07-06** — #499/#500/#501 (PR #504) y #503 (PR #506) completados;
  pulido de iconos/barra de estado vía PR #507/#508.
- **2026-07-05** — #490 (drift de instantánea) en curso, ola de Dark
  Mode/iconos rail e inspector de tarjetas (#413/#414) completados.
- **2026-06-29** — #404/#406/#408 completados (PR #412), ola de rediseño abierta.
- **v2.2, «admiring-mayer» (#1–#15)** — lista externa, completada o descartada donde era un falso positivo.

Hallazgos históricos y registros de trabajo (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).
