[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · **Español** · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Análisis de código y recomendaciones priorizadas: BgRemover

## Escala de valoración

| Símbolo | Prioridad | Significado |
|---------|-----------|-------------|
| 🔴 | Crítica | Errores, cierres inesperados o pérdida de datos |
| 🟠 | Alta | Impacto claro en la fiabilidad o el mantenimiento |
| 🟡 | Media | Mejora útil de calidad, legibilidad o testabilidad |
| 🟢 | Baja | Pulido opcional o mejora de proceso |

## Estado actual (2026-07-18)

La lista activa de análisis de código está vacía. Ruff, mypy y la suite de pruebas local siguen siendo la base antes de nuevos PR. La versión **v2.6.0** se publicó el 2026-07-16 desde el commit aprobado `f24cef69829da8e37aa400dad471dc4d607b89b3`: workflow del tag [29531147950](https://github.com/NikolayDA/picture_helper/actions/runs/29531147950), [release público de GitHub](https://github.com/NikolayDA/picture_helper/releases/tag/v2.6.0), cinco artefactos de aplicación descargados de nuevo y verificados por SHA-256, y smokes nativos verdes para Linux x86_64/aarch64 y macOS arm64. Las incidencias de release **#580/#583/#584/#585**, el hallazgo **#607**, la canalización de altura de 16 bits completa **#581/#587–#590** y el modelo de seguridad híbrido **#551** están cerrados. Estado en vivo: **3** incidencias abiertas — #245 y los reabiertos **#582/#595**.

### Completado desde la última revisión

- **Base antigua estable:** **N1/N2/N4/N5/N6/N7/N8** y **O2–O7** siguen hechos; los epics **#329/#344/#358/#384** (N9–N12) más la corrección de exportación **#363** fusionados/archivados; desde el 2026-06-25 también **#404/#406/#408** (PR #412) cerrado.
- **Rediseño y publicación v2.5.0:** núcleo del rediseño/rail/zoom/inspector de tarjetas/Dark Mode/seguimiento de UI (**#413/#414/#455–#464/#474–#489/#499–#501/#503/#509/#510/#514–#517**, **#490**, **#433/#434**) vía PR #412–#522; ola de publicación **#435/#392/#426/#389** (v2.5.0), **#299/#541/#318/#542**, plantilla de PR **#552**, sincronización **#549**, arreglo de SessionStart **#553**, formalización v2.3.0 **#550** – todo cerrado desde el 2026-07-12.
- **N14 — Epic #563 (actualizaciones de la app y gestión del modelo de IA) completamente cerrado:** `app_update.py` (#564), `ai_model_status.py` (#568), integración de menú/diálogo (#565/#569), comprobación automática opcional al iniciar (#566), conexión del warmup con múltiples observadores/cancelación cooperativa (#570) vía PR #573/#574; cierre de documentación (#567/#571).
- **Release v2.6.0 completamente cerrado:** scope-freeze (#583), gate del candidato sobre el SHA final de `main` (#584), tag/release/verificación post-release (#585) y epic de seguimiento #580 están hechos; esta actualización resuelve la deriva #607. El ADR HEIGHT de 16 bits (#586) y el contrato ADR/UX 3D (#591, PR #603) también siguen completados.
- **Canalización de altura de 16 bits completamente cerrada:** modelo de dominio/history y formato de proyecto v2 (#587/#588, PR #610), importación/generación/operaciones (#589, PR #612) y preview/exportación/UI/E2E (#590, PR #613) están en `main`; el epic #581 está cerrado tras gates verdes, reviews resueltas y una matriz de aceptación completa.
- **Seguimiento de auditoría #614–#616 cerrado:** las versiones futuras se rechazan de forma segura (#588, PR #614), las brechas de cobertura #597/#598 se cerraron mediante PR #615 y la brecha de la guía #606 se corrigió en los seis idiomas mediante PR #616.
- **Modelo de seguridad y núcleo 3D implementados:** #551 se completó mediante PR #619; #592–#594 están en `main` mediante PR #620. La auditoría posterior reabrió #582/#595 porque aún faltan pruebas de empaquetado/plataforma, aceptación completa de rendimiento y capturas.

### Aún abierto

- **O8 🟢 — Imprecisión del prototipo:** las herramientas de altura quedan bloqueadas en el mockup tras generarla; solo afecta a la simulación (#347).

## Incidencias abiertas de GitHub — Clasificación (2026-07-18)

Estado en vivo tras integrar PR #619/#620 y la auditoría posterior: **3** incidencias abiertas. **#551** y **#592–#594** están cerrados; **#582/#595** se reabrieron para completar la aceptación final.

### Agrupaciones sensatas

- **Aceptación final 3D** (#582 → #595): #592–#594 están completos; #595 rastrea las pruebas de empaquetado/plataforma, rendimiento completo, capturas y matriz final.
- **#245** sigue siendo un tracker externo de cuota OpenAI y no bloquea CodeQL, la publicación ni 3D.

Valoración: **Relevancia** = importancia para la hoja de ruta/usuarios, **Complejidad** = esfuerzo estimado, **Modelo/Esfuerzo** = modelo/esfuerzo recomendados.

| # | Título | Relevancia | Complejidad | Modelo/Esfuerzo | Próximo paso recomendado |
|---|--------|------------|-------------|------------------|---------------------------|
| [#595](https://github.com/NikolayDA/picture_helper/issues/595) | [3D] Rendimiento, empaquetado, documentación, aceptación end-to-end | 🟡 Media | 🟠 Alta | Sonnet 5 · alta | **In progress** – faltan pruebas de empaquetado/plataforma, rendimiento completo, capturas y matriz final. |
| [#582](https://github.com/NikolayDA/picture_helper/issues/582) | [Epic] Vista previa de relieve 3D real | 🟡 Media | 🟠 Alta (muy grande) | – (epic de seguimiento) | **In progress** – #591–#594 completos; espera solo a #595. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restaurar la cuota de OpenAI para la comprobación manual de Codex Security | 🟢 Baja | 🟢 Baja | – (sin tarea de código) | **Blocked (external)** – alcance acotado aún más el 2026-07-15: es puramente un tracker externo de facturación/cuota de OpenAI, no bloquea ni CodeQL ni la publicación ni #551. |

### Recomendado a continuación (orden de PR)

1. **#595** — completar las pruebas pendientes antes de cerrar #582.

*Drift:* esta actualización elimina #551/#592–#594 de la clasificación abierta, reabre #582/#595 por pruebas de aceptación pendientes y corrige el contador a 3.

## Rondas anteriores

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
