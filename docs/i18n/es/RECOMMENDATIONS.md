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
(PR #543), más **#318** (PR #540) y la sincronización de la instantánea de
recomendaciones **#542**. Una auditoría del repositorio del 2026-07-12 abrió
cinco nuevos hallazgos como incidencias (**#549–#553**); **#552** ya está
cerrado vía PR #557 y **#549** se cierra con este PR. Estado en vivo
(reconsultado): **4** incidencias abiertas – **#245**, **#550**, **#551**,
**#553**.

### Completado desde la última revisión

- **Base antigua estable:** **N1/N2/N4/N5/N6/N7/N8** y **O2–O7** siguen
  hechos; los epics **#329/#344/#358/#384** (N9–N12) más la corrección de
  exportación **#363** están fusionados y archivados.
- **Cerrado desde el 2026-06-25:** **#404/#406/#408** (PR #412) — hallazgos
  de vista previa/código muerto/auditoría hechos.
- **Núcleo del rediseño, rail/zoom, inspector de tarjetas, Dark Mode,
  seguimiento de UI:** **#413/#414/#455–#464/#474–#489/#499–#501/#503/#509/
  #510/#514–#517** llegaron vía PR #412/#423/#466/#467/#473/#482/#489/#504/
  #506/#512/#513/#518/#519 y PR #520/#521/#522; **#490** y **#433/#434** también.
- **Cerrado desde el 2026-07-12:** la ola de publicación **#435/#392/#426/
  #389** (v2.5.0, PR #538) más **#299** (PR #539), el seguimiento de higiene
  de pruebas **#541** (PR #543), **#318** (PR #540), la sincronización de la
  instantánea de recomendaciones **#542**, la plantilla de PR **#552**
  (PR #557) y esta sincronización de instantánea **#549**. Con ello se
  despachan todos los puntos de rediseño/publicación/backlog de la última
  instantánea.

### Aún abierto

- **O8 🟢 — Imprecisión del prototipo:** las herramientas de altura quedan
  bloqueadas en el mockup tras generarla; solo afecta a la simulación (#347).

## Incidencias abiertas de GitHub — Clasificación (2026-07-12)

Estado en vivo justo antes de esta edición: **#552** está cerrado vía
PR #557, **#549** se cierra con este PR. Quedan **4** incidencias abiertas:
**#245** (bloqueo de cuota/facturación), **#550** (consistencia de
tag/release de v2.3.0), **#551** (decisión de estrategia para Codex Security
Scan) y **#553** (verificación del hook SessionStart).

### Agrupaciones sensatas

#245 y #551 están vinculados en contenido (scan Codex): #245 es una acción de
cuenta pura, mientras que #551 requiere su propia decisión estratégica
(reactivar/retirar/reemplazar). #550 también requiere primero una decisión
(tag+release frente a solo aclaración en docs). #553 es independiente y
puede avanzar de inmediato.

Valoración: **Relevancia** = importancia para la hoja de ruta/usuarios,
**Complejidad** = esfuerzo de implementación estimado, **Modelo/Esfuerzo** =
modelo de Claude y esfuerzo de razonamiento recomendados para que Claude Code
lo implemente.

| # | Título | Relevancia | Complejidad | Modelo/Esfuerzo | Próximo paso recomendado |
|---|--------|------------|-------------|------------------|---------------------------|
| [#553](https://github.com/NikolayDA/picture_helper/issues/553) | Verificar la fiabilidad del hook SessionStart en sesiones web | 🟡 Media | 🟡 Media | Sonnet 5 · media | **Ready for PR** – reproducir en una sesión web nueva, luego corregir/documentar según haga falta. |
| [#550](https://github.com/NikolayDA/picture_helper/issues/550) | v2.3.0: conciliar el CHANGELOG con el historial de tag/release | 🟡 Media | 🟡 Media | Sonnet 5 · media | **Needs refinement** – la variante A (tag+release) frente a B (aclaración solo en docs) requiere una decisión antes de implementar. |
| [#551](https://github.com/NikolayDA/picture_helper/issues/551) | Decisión de estrategia para Codex Security Scan (reactivar/retirar/reemplazar) | 🟡 Media | 🟡 Media | Sonnet 5 · media | **Needs refinement** – requiere elegir deliberadamente entre tres opciones; recomendación: opción 2 (retirar/deshabilitar) dado el bloqueo externo de semanas y la redundancia con pip-audit/license/CI. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan «Quota exceeded» | 🟡 Media | 🟢 Baja | – (sin tarea de código) | **Bloqueado (externo)** – restaurar la facturación/cuota de OpenAI es una acción de cuenta, no un PR. |

### Recomendado a continuación (orden de PR)

1. **#553** — reproducir el comportamiento del hook SessionStart en una
   sesión web nueva y corregir según haga falta.
2. **#550** — obtener una decisión sobre la variante A/B, luego ajustar el
   CHANGELOG/tag/release.
3. **#551** — obtener una decisión sobre la estrategia del scan (vinculada a
   #245), luego ajustar el workflow.
4. **#245** — sigue bloqueado externamente; verificar manualmente solo tras
   restaurar la cuota de OpenAI.

*Drift:* reconsultar el número de incidencias abiertas en vivo, sin
arrastrarlo (#542 → #549: mismo desfase).

## Rondas anteriores

- **2026-07-12 (sincronización #549)** — #552 (plantilla de PR) cerrado vía
  PR #557; este PR cierra #549. Instantánea reducida a 4 (#245, #550, #551,
  #553).
- **2026-07-12 (auditoría de issues)** — #542 cerrado; auditoría del repo
  abrió cinco nuevas incidencias (#549–#553); instantánea de issues
  abiertos actualizada a 6 (#245 + #549–#553).
- **2026-07-12** — versión **v2.5.0** publicada; ola de rollout
  #435/#392/#426/#389 cerrada; #299 (PR #539), seguimiento N13 #541 (PR #543)
  y #318 (PR #540) cerrados; instantánea de issues abiertos reducida a #245 +
  #542.
- **2026-07-11 (seguimiento final)** — #425 cerrado formalmente; #530/#531
  cerrados mediante PR #533/#535; instantánea actualizada a 7 restantes.
- **2026-07-11 (2.ª clasificación)** — #431/#432 cerrados (PR #529); epic
  #425 completo. Nuevas incidencias #530/#531 de un caso de soporte de IA.
  #430 cerrado (PR #526, i18n ES/FR/UK/ZH completa; O1 hecho).
- **2026-07-10** — #509/#510 cerrados, #514–#517 completados, seguimiento de
  la columna derecha cerrado vía PR #520/#521/#522.
- **2026-07-05/06** — #490, ola de Dark Mode/iconos rail, inspector de
  tarjetas (#413/#414), #499–#501/#503 (PR #504/#506) y pulido de iconos/
  barra de estado (PR #507/#508).
- **2026-06-29** — #404/#406/#408 completados (PR #412), ola de rediseño abierta.
- **v2.2, «admiring-mayer» (#1–#15)** — lista externa, completada o descartada donde era un falso positivo.

Hallazgos históricos y registros de trabajo (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).
