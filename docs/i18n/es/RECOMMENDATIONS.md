[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · **Español** · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Análisis de código y recomendaciones priorizadas: BgRemover

## Escala de valoración

| Símbolo | Prioridad | Significado |
|---------|-----------|-------------|
| 🔴 | Crítica | Errores, cierres inesperados o pérdida de datos |
| 🟠 | Alta | Impacto claro en la fiabilidad o el mantenimiento |
| 🟡 | Media | Mejora útil de calidad, legibilidad o testabilidad |
| 🟢 | Baja | Pulido opcional o mejora de proceso |

## Estado actual (2026-07-21)

La lista activa de análisis de código está vacía. Ruff, mypy y la suite de pruebas local siguen siendo la base antes de nuevos PR. Desde la última instantánea (2026-07-18, 3 incidencias abiertas), apareció un epic completamente nuevo que se implementó en gran medida en un solo día: **#639** (aceptación automatizada de releases mediante runners de hardware autoalojados) con las subincidencias **#640–#646** y la incidencia de seguimiento **#648**. Estado en vivo según la consulta a GitHub: **12** incidencias abiertas.

### Completado desde la última revisión

- **Base antigua estable:** **N1/N2/N4/N5/N6/N7/N8** y **O2–O7** siguen hechos; los epics **#329/#344/#358/#384** (N9–N12) más la corrección de exportación **#363** están fusionados/archivados.
- **Canalización de altura de 16 bits completamente cerrada:** el epic **#581**, incluidos **#587/#588** (PR #610), **#589** (PR #612) y **#590** (PR #613), está en `main`; todos los gates/reviews en verde, matriz de aceptación completa presente.
- **Modelo de seguridad y núcleo 3D completos:** **#551** (CodeQL automático, Codex solo manual) mediante PR #619; **#592–#594** (núcleo de geometría, visor, integración de flujo de trabajo/caché) mediante PR #620 en `main`. Las brechas de cobertura **#597/#598** se cerraron mediante PR #615; la brecha de la guía **#606** se corrigió en los seis idiomas mediante PR #616.
- **Empaquetado para Raspberry Pi 5 reforzado:** se encontraron y corrigieron tres errores de arranque reales en el hardware de destino — punto de entrada del AppImage (PR #627), compatibilidad glibc en aarch64 (PR #627), preparación de plugins Qt/RUNPATH (PR #631); se confirmó que la app arranca en la Pi 5, incluida una vista previa 3D funcional.
- **Nuevo epic #639 abierto Y en gran parte implementado:** el ADR + documentación operativa (#640), el esqueleto del workflow `release-abnahme.yml` (#641), los smokes de hardware Linux/macOS con procedencia de GL (#642/#643), la prueba de regresión E2E de release (#644), la suite de rendimiento con GL en vivo (#645) y la evaluación previa por visión + matriz de aceptación (#646) están totalmente implementados y verificados en `main` mediante PR #647 y PR #649. Siguen figurando como abiertos únicamente porque las descripciones de los PR usan formulaciones en alemán («Löst #640 …») en lugar de las palabras clave de cierre en inglés que GitHub reconoce (véase el comentario en #639 del 2026-07-21).

### Aún abierto

- **O8 🟢 — Imprecisión del prototipo:** las herramientas de altura quedan bloqueadas en el mockup tras la generación; solo afecta a la simulación, la app real no se ve afectada (#347).
- **Seguimiento administrativo 🟢 — Cuatro incidencias están hechas pero no cerradas:** #640–#643 están totalmente implementadas mediante PR #647; solo la falta de la palabra clave de cierre en inglés en la descripción del PR impidió el cierre automático (véase el comentario en #639).
- **Brecha de documentación 🟢 — Al README.md le falta la sección 3D:** la vista previa de relieve 3D está documentada en `ANLEITUNG.md` y `CHANGELOG.md`, pero `README.md` todavía no la menciona (lista de funciones, paso 5 de uso, capturas). Esto coincide con el criterio aún abierto «documentación de ANLEITUNG/README/arquitectura actualizada» en #582/#595.

## Incidencias abiertas de GitHub — Clasificación (2026-07-21)

Estado en vivo: **12** incidencias abiertas. Valoración: **Relevancia** = importancia para la hoja de ruta/usuarios, **Complejidad** = esfuerzo de implementación estimado, **Modelo/Esfuerzo** = modelo de Claude y esfuerzo de razonamiento recomendados.

### Agrupaciones sensatas

- **Automatización de aceptación de releases** (#639 → {#640 ‖ #641} → {#642 ‖ #643} → #644 → #645 → #646): técnicamente ya implementada mediante PR #647/#649; solo quedan la verificación real con evidencia de hardware (despacho de runners) y los cuatro cierres administrativos #640–#643.
- **#648** es la única tarea de código genuina que queda en esta área: un modo de automatización/captura de pantalla dentro del artefacto empaquetado, de modo que la prueba de renderizado 3D provenga del paquete real en lugar de un checkout del código fuente.
- **Vista previa de relieve 3D** (#582 → #595): el MVP funcional está hecho (Go para el alcance automatizable, véase el informe de aceptación en #582); #595 espera el mismo despacho de hardware indicado arriba más #648.
- **#245** sigue siendo un tracker puramente externo de facturación/cuota de OpenAI y no bloquea ni CodeQL, ni la publicación, ni el 3D.

| # | Título | Relevancia | Complejidad | Modelo/Esfuerzo | Próximo paso recomendado |
|---|--------|------------|-------------|------------------|---------------------------|
| [#639](https://github.com/NikolayDA/picture_helper/issues/639) | [Epic] Aceptación automatizada de releases | 🟠 Alta | 🟠 Alta (muy grande, en gran parte implementada) | – (epic de seguimiento) | **In progress, nearly done** – #640–#646 técnicamente implementados mediante PR #647/#649; falta la verificación de los runners y el cierre de las subincidencias; #648 es el único esfuerzo genuino restante. |
| [#640](https://github.com/NikolayDA/picture_helper/issues/640) | ADR + documentación operativa/de seguridad para runners de aceptación autoalojados | 🟡 Media | 🟢 Baja (hecho) | – (sin tarea de código) | **Ready to close** – el ADR + `RELEASE_AUTOMATION.md` están completamente presentes mediante PR #647; solo falta la palabra clave de cierre. |
| [#641](https://github.com/NikolayDA/picture_helper/issues/641) | Workflow `release-abnahme.yml`: esqueleto, obtención de artefactos, formato de evidencia | 🟠 Alta | 🟢 Baja (hecho) | – (sin tarea de código) | **Ready to close** – el workflow + la prueba de gobernanza están presentes mediante PR #647; solo falta la palabra clave de cierre. |
| [#642](https://github.com/NikolayDA/picture_helper/issues/642) | Smokes de Linux (AppImage/.deb) con procedencia de GL | 🟠 Alta | 🟡 Media (lógica principal hecha) | – (sin tarea de código) | **Ready to close / needs live verification** – `abnahme_smoke.py` + las pruebas están presentes mediante PR #647; la ejecución real solo se produce una vez despachada en el runner de la Pi 5. |
| [#643](https://github.com/NikolayDA/picture_helper/issues/643) | Smoke de DMG de macOS con prueba Retina/HiDPI | 🟠 Alta | 🟡 Media (lógica principal hecha) | – (sin tarea de código) | **Ready to close / needs live verification** – misma base que #642, para el runner M3. |
| [#644](https://github.com/NikolayDA/picture_helper/issues/644) | Escenario de regresión E2E de release como prueba `ui` | 🟠 Alta | 🟡 Media (hecho) | – (sin tarea de código) | **Ready to close / needs live verification** – `tests/test_e2e_release_regression.py` (ui_smoke) presente mediante PR #649; la rama Ready necesita un despacho real con GL. |
| [#645](https://github.com/NikolayDA/picture_helper/issues/645) | Suite de rendimiento con GL en vivo en el arnés de benchmark | 🟡 Media | 🟡 Media (hecho) | – (sin tarea de código) | **Ready to close / needs live verification** – la suite `preview3d-live` en `scripts/benchmark.py` está presente mediante PR #649. |
| [#646](https://github.com/NikolayDA/picture_helper/issues/646) | Evaluación previa por visión, agregación de evidencia, matriz de aceptación | 🟡 Media | 🟡 Media (hecho) | – (sin tarea de código) | **Ready to close / needs live verification** – `abnahme_vision_check.py`/`abnahme_aggregate.py` presentes mediante PR #647/#649; también necesita un secreto `ANTHROPIC_API_KEY` para la evaluación real. |
| [#648](https://github.com/NikolayDA/picture_helper/issues/648) | Prueba nativa de renderizado 3D del artefacto empaquetado | 🟡 Media | 🟡 Media | Sonnet 5 · media | **Ready for PR** – una brecha claramente delimitada e independiente (un gancho de automatización de capturas dentro del artefacto empaquetado en lugar de un checkout del código fuente); la única tarea de código genuina que queda de la automatización de aceptación. |
| [#595](https://github.com/NikolayDA/picture_helper/issues/595) | [3D] Rendimiento, empaquetado, documentación, aceptación end-to-end | 🟡 Media | 🟡 Media (reducida, ahora existe automatización) | Sonnet 5 · media | **Blocked** – espera el mismo despacho de hardware que #639, más #648; `README.md` también sigue necesitando la sección 3D. |
| [#582](https://github.com/NikolayDA/picture_helper/issues/582) | [Epic] Vista previa de relieve 3D real | 🟡 Media | 🟠 Alta (muy grande, MVP hecho) | – (epic de seguimiento) | **Blocked** – espera únicamente a #595. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restaurar la cuota de OpenAI para la comprobación manual de Codex Security | 🟢 Baja | 🟢 Baja | – (sin tarea de código) | **Blocked (external)** – sin cambios desde el 2026-07-15: un tracker puramente externo de facturación que no bloquea nada en el repositorio. |

### Recomendado a continuación (orden de PR)

1. **Cerrar #640–#643** — la implementación está completa (PR #647); solo falta la confirmación manual del propietario.
2. **Implementar #648** — la única tarea de código restante: un modo de automatización/captura de pantalla dentro del artefacto empaquetado para una prueba genuina de renderizado 3D.
3. **Registrar los runners autoalojados y despachar `release-abnahme.yml`** — verifica #642–#646 con evidencia real de hardware y produce la matriz de aceptación para #595.
4. **Tras una ejecución en verde + #648:** cerrar #595 y luego #582 (bloqueado solo por #595); añadir la sección 3D a `README.md`.
5. **#245 se mantiene sin cambios** — ningún parche del repositorio puede arreglar el bloqueo externo de facturación de OpenAI.

*Nota de deriva:* esta actualización concilia la instantánea con el estado real de `main` (historial completo de git, antes oculto por un clon superficial) y una consulta en vivo a GitHub; sustituye el estado del 2026-07-18 con 3 incidencias abiertas. Las próximas actualizaciones seguirán revisando en vivo estados, listas de verificación y dependencias, en lugar de arrastrar una marca de tiempo.

## Rondas anteriores

- **2026-07-21 (automatización de aceptación de releases, epic #639)** — el epic #639 se abrió y se implementó en gran parte en un solo día: ADR/documentación (#640), esqueleto del workflow (#641), smokes de hardware Linux/macOS (#642/#643), prueba de regresión E2E (#644), suite de rendimiento con GL en vivo (#645), evaluación previa por visión + matriz de aceptación (#646) — todo fusionado mediante PR #647/#649 pero sin cierre automático debido a palabras clave de cierre en alemán; la incidencia de seguimiento #648 (prueba nativa de renderizado 3D del artefacto empaquetado) sigue siendo la única tarea de código abierta. Estado en vivo: 12 incidencias abiertas.
- **2026-07-20 (smoke de hardware en la Pi 5)** — se encontraron y corrigieron tres errores reales de empaquetado en la Raspberry Pi 5 (PR #627/#631); se confirmó que la app arranca, incluida la vista previa 3D.
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
