[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · **Español** · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Análisis de código y recomendaciones priorizadas: BgRemover

## Escala de valoración

| Símbolo | Prioridad | Significado |
|---------|-----------|-------------|
| 🔴 | Crítica | Errores, cierres inesperados o pérdida de datos |
| 🟠 | Alta | Impacto claro en la fiabilidad o el mantenimiento |
| 🟡 | Media | Mejora útil de calidad, legibilidad o testabilidad |
| 🟢 | Baja | Pulido opcional o mejora de proceso |

## Estado actual (2026-07-12)

La lista activa de análisis de código está vacía. Ruff, mypy y la suite de
pruebas local siguen siendo la base antes de nuevos PR. La versión **v2.5.0**
se publicó el 2026-07-11 (CHANGELOG curado, versión subida — PR #538). Toda la
ola de rollout/publicación queda así cerrada: **#435** (PR #538), **#392**,
**#426** y **#389**. También cerrado: **#299** (PR #539) junto con el
seguimiento de higiene de pruebas N13 rastreado por separado **#541**
(PR #543), más **#318** (PR #540). GitHub muestra ahora solo **2**
incidencias abiertas.

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
- **Cerrado desde el 2026-07-12:** la ola de publicación **#435/#392/#426/
  #389** (v2.5.0, PR #538) más **#299** (PR #539), el seguimiento de higiene
  de pruebas **#541** (PR #543) y **#318** (PR #540). Con ello se despachan
  todos los puntos de rediseño/publicación/backlog de la última instantánea.

### Aún abierto

- **O8 🟢 — Imprecisión del prototipo:** las herramientas de altura quedan
  bloqueadas en el mockup tras generarla; solo afecta a la simulación (#347).

## Incidencias abiertas de GitHub — Clasificación (2026-07-12)

A fecha del 2026-07-12, GitHub muestra solo **2** incidencias abiertas: el
bloqueo externo de cuota/facturación **#245** y esta sincronización de
documentación **#542**.

### Agrupaciones sensatas

- **Bloqueado externamente:** #245 depende de la facturación/cuota de OpenAI
  — una acción de cuenta, no un PR del repo.
- **Documentación:** #542 alinea los seis espejos de recomendaciones con el
  estado en vivo y se resuelve con el PR asociado.

Valoración: **Relevancia** = importancia para la hoja de ruta/usuarios,
**Complejidad** = esfuerzo de implementación estimado, **Modelo/Esfuerzo** =
modelo de Claude y esfuerzo de razonamiento recomendados para que Claude Code
lo implemente.

| # | Título | Relevancia | Complejidad | Modelo/Esfuerzo | Próximo paso recomendado |
|---|--------|------------|-------------|------------------|---------------------------|
| [#542](https://github.com/NikolayDA/picture_helper/issues/542) | Actualizar la instantánea de recomendaciones tras v2.5.0 | 🟢 Baja | 🟢 Baja | Sonnet 5 · baja | **En curso** – este PR alinea los seis espejos con el estado en vivo, estructuralmente sincronizados. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan «Quota exceeded» | 🟡 Media | 🟢 Baja | – (sin tarea de código) | **Bloqueado (externo)** – restaurar la facturación/cuota de OpenAI es una acción de cuenta, no un PR. |

### Recomendado a continuación (orden de PR)

1. Cerrar **#542** con este PR (sincronización estructural de la instantánea
   en los seis espejos).
2. **#245** sigue bloqueado externamente — no es posible un PR del repo;
   verificar manualmente solo tras restaurar la cuota de OpenAI.

## Rondas anteriores

- **2026-07-12** — versión **v2.5.0** publicada; ola de rollout
  #435/#392/#426/#389 cerrada; #299 (PR #539), seguimiento N13 #541 (PR #543)
  y #318 (PR #540) cerrados; instantánea de issues abiertos reducida a #245 +
  #542.
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
