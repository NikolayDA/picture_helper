[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · **Español** · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Análisis de código y recomendaciones priorizadas: BgRemover

## Escala de valoración

| Símbolo | Prioridad | Significado |
|---------|-----------|-------------|
| 🔴 | Crítica | Errores, cierres inesperados o pérdida de datos |
| 🟠 | Alta | Impacto claro en la fiabilidad o el mantenimiento |
| 🟡 | Media | Mejora útil de calidad, legibilidad o testabilidad |
| 🟢 | Baja | Pulido opcional o mejora de proceso |

## Estado actual (2026-07-11)

La lista activa de análisis de código está vacía. Ruff, mypy y la suite de
pruebas local siguen siendo la base antes de nuevos PR. **#431/#432** se
fusionaron vía PR #529 y están cerrados — ANLEITUNG/README y todas las
capturas reflejan ahora el flujo guiado de 6 pasos. Con ello el epic
**#425** queda completo en contenido (sus tres sub-incidencias
#430/#431/#432 cerradas) y se cerró el 2026-07-11. Las dos incidencias de
warmup de IA abiertas después, **#530**/**#531**, también están cerradas por
PR #533/#535. GitHub muestra ahora **7** incidencias abiertas.

### Completado desde la última revisión

- **Base antigua estable:** **N1/N2/N4/N5/N6/N7/N8** y **O2–O7** siguen
  hechos; los epics **#329/#344/#358/#384** (N9–N12) más la corrección de
  exportación **#363** están fusionados y archivados.
- **Cerrado desde el 2026-06-25:** **#404/#406/#408** (PR #412) — hallazgos
  de vista previa/código muerto/auditoría hechos.
- **Núcleo del rediseño, rail/zoom, inspector de tarjetas, Dark Mode,
  seguimiento de UI:** **#413/#414/#455–#464/#474–#489/#499–#501/#503/#509/
  #510/#514–#517** llegaron vía PR #412/#423/#466/#467/#473/#482/#489/#504/
  #506/#512/#513/#518/#519 y PR #520/#521/#522; **#490** y **#433/#434**
  también.
- **Cerrado desde el 2026-07-11:** **#430** (PR #526) — i18n en tiempo de
  ejecución para ES/FR/UK/ZH mantenido por completo y verificado en paridad;
  **#431/#432** (PR #529) — ANLEITUNG/README/capturas llevados al flujo
  guiado de 6 pasos. **#425** queda cerrado como epic i18n/docs completado;
  **#530** (PR #533) y **#531** (PR #535) cierran el caso de soporte de
  warmup de IA.

### Aún abierto

- **O8 🟢 — Imprecisión del prototipo:** las herramientas de altura quedan
  bloqueadas en el mockup tras generarla; solo afecta a la simulación (#347).

## Incidencias abiertas de GitHub — Clasificación (2026-07-11)

A fecha del 2026-07-11, GitHub muestra **7** incidencias abiertas:
rollout/publicación (**#426/#435/#392/#389**) y backlog/puntos externos
(**#299/#318/#245**).

### Agrupaciones sensatas

- **Rollout/publicación:** #426 depende solo de #435; coordinar con #392 y
  luego cerrar #426/#389.
- **Backlog:** #299 tras la publicación; refinar #318 primero; #245 sigue
  bloqueado externamente.

Valoración: **Relevancia** = importancia para la hoja de ruta/usuarios,
**Complejidad** = esfuerzo de implementación estimado, **Modelo/Esfuerzo** =
modelo de Claude y esfuerzo de razonamiento recomendados para que Claude Code
lo implemente.

| # | Título | Relevancia | Complejidad | Modelo/Esfuerzo | Próximo paso recomendado |
|---|--------|------------|-------------|------------------|---------------------------|
| [#435](https://github.com/NikolayDA/picture_helper/issues/435) | CHANGELOG y subida de versión del rediseño | 🟡 Media | 🟢 Baja | Sonnet 5 · baja | **Listo para PR** – mecánico, bien acotado; bloquea #426 y #392. |
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | Publicar la versión v2.5.0 | 🟠 Alta | 🟡 Media | Sonnet 5 · media | **Lista** – secuenciar tras #435; #431/#432 ya no bloquean; el build de `.dmg` de macOS necesita un runner local/macOS fuera de este contenedor remoto. |
| [#426](https://github.com/NikolayDA/picture_helper/issues/426) | EPIC: QA y despliegue del rediseño | 🟠 Alta | 🟢 Baja | – (issue de seguimiento) | **Casi hecho** – solo #435 queda abierto. |
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | EPIC: Actualizar docs de usuario y publicar | 🟠 Alta | 🟢 Baja | – (issue de seguimiento) | **Cerrar tras #392** – solo queda publicar. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Higiene de pruebas: aserciones débiles/redundancias | 🟢 Baja | 🟡 Media | Sonnet 5 · media | **Listo para PR** – catálogo más los seguimientos N13 de la clasificación del 2026-07-08 ya documentados; priorizar tras la publicación. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Overrides de permisos por job en WF reutilizable | 🟢 Baja | 🟡 Media | Opus 4.8 · alta | **Necesita refinamiento** – probar primero la semántica de GitHub (nivel superior vs. efectiva por job); no debe debilitar la protección de regresión OIDC. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan «Quota exceeded» | 🟡 Media | 🟢 Baja | – (sin tarea de código) | **Bloqueado (externo)** – restaurar la facturación/cuota de OpenAI es una acción de cuenta, no un PR. |

### Recomendado a continuación (orden de PR)

1. **Publicación:** ejecutar **#435** + **#392** de forma coordinada, luego
   cerrar **#426**/**#389**.
2. **#299** tras la publicación; investigar solo **#318**; mantener **#245**
   bloqueado externamente.

## Rondas anteriores

- **2026-07-11 (seguimiento final)** — #425 cerrado formalmente; #530/#531
  cerrados mediante PR #533/#535; instantánea de issues abiertos actualizada
  a 7 issues restantes.
- **2026-07-11 (2.ª clasificación)** — #431/#432 cerrados (PR #529,
  ANLEITUNG/README/capturas llevados al flujo guiado de 6 pasos); el epic
  #425 queda completo. Nuevas incidencias #530/#531 abiertas por un caso de
  soporte de warmup de IA.
- **2026-07-11** — #430 cerrado (PR #526, i18n en tiempo de ejecución
  ES/FR/UK/ZH completa; O1 hecho); el epic #425 pasó a depender solo de
  #431/#432.
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
