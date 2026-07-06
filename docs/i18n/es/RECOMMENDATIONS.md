[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · **Español** · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Análisis de código y recomendaciones priorizadas: BgRemover

## Escala de valoración

| Símbolo | Prioridad | Significado |
|---------|-----------|-------------|
| 🔴 | Crítica | Errores, cierres inesperados o pérdida de datos |
| 🟠 | Alta | Impacto claro en la fiabilidad o el mantenimiento |
| 🟡 | Media | Mejora útil de calidad, legibilidad o testabilidad |
| 🟢 | Baja | Pulido opcional o mejora de proceso |

## Estado actual (2026-07-06)

La lista activa de análisis de código está vacía. Ruff, mypy y la suite de
pruebas local siguen siendo la base antes de nuevos PR. Desde la instantánea
del 2026-07-05, la corrección de instantánea Recommendations **#490** está
cerrada. La verificación de hoy sobre los epics de rediseño
(#413/#418/#424/#455/#463/#474/#483) encontró tres hallazgos nuevos: **#499**
(esquema claro aún no 1:1 con el prototipo), **#500** (script de capturas
roto, bloquea #432) y **#501** (widget muerto `TopIconTab*`). GitHub muestra
actualmente **14** incidencias abiertas.

### Completado desde la última revisión

- **Base antigua estable:** **N1/N2/N4/N5/N6/N7/N8** y **O2–O7** siguen
  hechos; los epics **#329/#344/#358/#384** (N9–N12) más la corrección de
  exportación **#363** están fusionados y archivados.
- **Cerrados desde la revisión del 2026-06-25:** **#404/#406/#408** (PR #412)
  — hallazgos de vista previa/código muerto/auditoría hechos.
- **Núcleo del rediseño, rail/zoom, inspector de tarjetas, Dark Mode:**
  **#413/#414/#455–#464/#474–#489** llegaron con PR #412/#423/#466/#467/#473/
  #482/#489 (barra de pasos, tokens de diseño, alineación Dark Mode, iconos
  vectoriales).
- **#490 y #433/#434 completados:** drift de instantánea corregido; smoke
  tests/regresión llegaron con PR #423 — el epic **#426** ahora solo depende
  de **#435**.

### Nuevo desde la última revisión

- **#499 🟡:** `theme.LIGHT` difiere del prototipo en varios tokens (mismo
  patrón que #474–#480, prueba ya en `tests/test_theme.py`).
- **#500 🟠:** `scripts/generate_app_screenshots.py` busca un `QTabWidget`
  que ya no existe; bloquea **#432**.
- **#501 🟢:** `TopIconTabBar`/`TopIconTabWidget` en `widgets.py` son widgets
  muertos desde el cambio a stepper.

### Aún abierto

- **O1 🟠 — Más idiomas en tiempo de ejecución.** DE/EN son conmutables;
  es/fr/uk/zh aún faltan como locales de ejecución (coincide con **#430**).
- **O8 🟢 — Imprecisión del prototipo:** las herramientas de altura quedan
  bloqueadas en el mockup tras generarla; solo afecta a la simulación (#347).

## Incidencias abiertas de GitHub — Clasificación (2026-07-06)

A fecha del 2026-07-06, GitHub muestra **14** incidencias abiertas: tres
seguimientos de rediseño (**#499/#500/#501**), i18n/docs
(**#425/#430/#431/#432**), rollout/publicación (**#426/#435/#392/#389**) y
backlog/puntos externos (**#299/#318/#245**).

### Agrupaciones sensatas

- **Seguimiento de rediseño:** #499/#500/#501 son independientes y de bajo
  riesgo; **#500** primero porque desbloquea **#432**.
- **i18n/docs:** #430 desbloquea las pruebas de paridad; #431/#432 siguen
  tras el UI freeze **y** #500.
- **Rollout/publicación:** #426 depende solo de #435; coordinar con #392 y
  luego cerrar #426/#389.
- **Backlog:** #299 tras la publicación; refinar #318 primero; #245 sigue
  bloqueado externamente.

Valoración: **Relevancia** = importancia para la hoja de ruta/usuarios,
**Complejidad** = esfuerzo de implementación estimado.

| # | Título | Relevancia | Complejidad | Próximo paso recomendado |
|---|--------|------------|-------------|--------------------------|
| [#500](https://github.com/NikolayDA/picture_helper/issues/500) | Script de capturas roto tras el rediseño (bloquea #432) | 🟠 Alta | 🟢 Baja | **Listo para PR** – pasar la navegación a `Stepper`. |
| [#499](https://github.com/NikolayDA/picture_helper/issues/499) | Alinear esquema claro 1:1 con el Prototipo A | 🟡 Media | 🟢 Baja | **Listo para PR** – mismo patrón que #474–#480. |
| [#501](https://github.com/NikolayDA/picture_helper/issues/501) | Eliminar widgets `TopIconTab*` huérfanos | 🟢 Baja | 🟢 Baja | **Listo para PR** – limpieza pura, 3 archivos. |
| [#425](https://github.com/NikolayDA/picture_helper/issues/425) | EPIC: Internacionalización y documentación | 🟠 Alta | 🟡 Media | **En curso** – #430/#431/#432 abiertos. |
| [#430](https://github.com/NikolayDA/picture_helper/issues/430) | Nuevas cadenas de UI (pasos/tarjetas/navegación) | 🟠 Alta | 🟡 Media | **Listo para PR** – ES/FR/UK/ZH; DE/EN vía PR #423. |
| [#431](https://github.com/NikolayDA/picture_helper/issues/431) | Actualizar ANLEITUNG y README al flujo guiado | 🟡 Media | 🟡 Media | **Tras congelar la UI** – espejo en 6 idiomas. |
| [#432](https://github.com/NikolayDA/picture_helper/issues/432) | Rehacer capturas de la app para el rediseño | 🟢 Baja | 🟢 Baja | **Bloqueado** – necesita UI final **y** #500. |
| [#426](https://github.com/NikolayDA/picture_helper/issues/426) | EPIC: QA y despliegue del rediseño | 🟠 Alta | 🟢 Baja | **Casi hecho** – solo #435 queda abierto. |
| [#435](https://github.com/NikolayDA/picture_helper/issues/435) | CHANGELOG y subida de versión del rediseño | 🟡 Media | 🟢 Baja | **Alinear con #392** – definir la secuencia. |
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | Publicar la versión v2.5.0 | 🟠 Alta | 🟡 Media | **Lista** – decidir la secuencia con el rediseño. |
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | EPIC: Actualizar docs de usuario y publicar | 🟠 Alta | 🟢 Baja | **Cerrar tras #392** – solo queda publicar. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Higiene de pruebas: aserciones débiles/redundancias | 🟢 Baja | 🟢 Baja | **Tras la publicación** – mayor impacto primero. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Overrides de permisos por job en WF reutilizable | 🟢 Baja | 🟡 Media | **Necesita refinamiento** – probar semántica GitHub. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan «Quota exceeded» | 🟡 Media | 🟢 Baja | **Bloqueado (externo)** – facturación/cuota OpenAI. |

### Recomendado a continuación (orden de PR)

1. **#500** primero — desbloquea **#432**; **#499**/**#501** en el mismo PR o
   en uno inmediatamente posterior.
2. Adelantar **#430** — desbloquea la paridad i18n; luego **#431**/**#432**.
3. **Publicación:** ejecutar **#435** + **#392** de forma coordinada, luego
   cerrar **#426**/**#389**.
4. **#299** tras la publicación; investigar solo **#318**; mantener **#245**
   bloqueado externamente.

## Rondas anteriores

- **2026-07-05** — #490 (drift de instantánea) en curso, ola de Dark
  Mode/iconos rail e inspector de tarjetas (#413/#414) completados.
- **2026-06-29** — #404/#406/#408 completados (PR #412), ola de rediseño abierta.
- **v2.2, «admiring-mayer» (#1–#15)** — lista externa, completada o descartada donde era un falso positivo.

Hallazgos históricos y registros de trabajo (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).
