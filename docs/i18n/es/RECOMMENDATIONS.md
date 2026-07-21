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

Ruff, mypy y la suite de pruebas local siguen siendo la base antes de nuevos PR. Hoy se fusionaron los PR **#647**, **#649**, **#650**, **#651** y **#652**. El ADR, el workflow, los smokes, el E2E, GL en vivo, la agregación y el gancho nativo del artefacto están en `main`. **#640** y **#641** están cerradas. **#648** se reabrió porque aún no existe una ejecución de hardware correcta con evidencia separada para AppImage, `.deb` instalado y DMG. Estado en vivo: **10** incidencias abiertas.

### Resultado de la revisión

- **Base antigua estable:** **N1/N2/N4/N5/N6/N7/N8** y **O2–O7** siguen hechos; los epics **#329/#344/#358/#384** (N9–N12) más la corrección de exportación **#363** están fusionados/archivados; desde el 2026-06-25 también **#404/#406/#408** (PR #412) cerrado.
- **Canalización de altura de 16 bits completamente cerrada:** el epic **#581**, incluidos **#587/#588** (PR #610), **#589** (PR #612) y **#590** (PR #613), está en `main`; todos los gates/reviews en verde, matriz de aceptación completa presente.
- **Modelo de seguridad y núcleo 3D completos:** **#551** (CodeQL automático, Codex solo manual) mediante PR #619; **#592–#594** (núcleo de geometría, visor, integración de flujo de trabajo/caché) mediante PR #620 en `main`. Las brechas de cobertura **#597/#598** se cerraron mediante PR #615; la brecha de la guía **#606** se corrigió en los seis idiomas mediante PR #616.
- **Empaquetado para Raspberry Pi 5 reforzado:** se encontraron y corrigieron tres errores de arranque reales en el hardware de destino — punto de entrada del AppImage (PR #627), compatibilidad glibc en aarch64 (PR #627), preparación de plugins Qt/RUNPATH (PR #631); se confirmó que la app arranca en la Pi 5, incluida una vista previa 3D funcional.
- **Código de aceptación completo; evidencia de hardware pendiente:** este seguimiento añade capturas separadas por paquete, preflight de sesión gráfica, una nueva prueba 3D tras Save/Open, tres muestras GL con RSS real del proceso y una entrada `target_issue` validada.

- **Evidencia operativa 🟡:** #642–#646 y la reabierta #648 siguen abiertas hasta que los runners completen un despacho gráfico real.
- **Tracker externo 🟢:** #245 sigue siendo un asunto de facturación/cuota de OpenAI fuera del repositorio.

## Incidencias abiertas de GitHub — Clasificación (2026-07-21)

Estado en vivo: **10** incidencias abiertas. Valoración: **Relevancia** = importancia para la hoja de ruta/usuarios, **Complejidad** = esfuerzo de implementación estimado, **Modelo/Esfuerzo** = modelo de Claude y esfuerzo de razonamiento recomendados.

- **Automatización de aceptación** (#639 → #642–#646 + #648): los caminos de código existen; el cierre exige evidencia completa del hardware de destino.
- **#648** está reabierta por evidencia, no por falta del gancho: AppImage, `.deb` instalado y DMG deben producir cada uno captura 3D nativa y procedencia.
- **Vista previa de relieve 3D** (#582 → #595): el MVP está hecho; #595 espera la misma aceptación de hardware en verde.
- **#245** sigue siendo un tracker puramente externo de facturación/cuota de OpenAI y no bloquea ni CodeQL, ni la publicación, ni el 3D.

| # | Título | Relevancia | Complejidad | Modelo/Esfuerzo | Próximo paso recomendado |
|---|--------|------------|-------------|------------------|---------------------------|
| [#639](https://github.com/NikolayDA/picture_helper/issues/639) | [Epic] Aceptación automatizada de releases | 🟠 Alta | 🟠 Alta (código casi terminado) | – (epic de seguimiento) | **En curso** – configurar runners, despachar el workflow y revisar la evidencia. |
| [#642](https://github.com/NikolayDA/picture_helper/issues/642) | Smokes de Linux (AppImage/.deb) con procedencia de GL | 🟠 Alta | 🟡 Media (lógica principal hecha) | – (sin tarea de código) | **Ready to close / needs live verification** – `abnahme_smoke.py` + las pruebas están presentes mediante PR #647; la ejecución real solo se produce una vez despachada en el runner de la Pi 5. |
| [#643](https://github.com/NikolayDA/picture_helper/issues/643) | Smoke de DMG de macOS con prueba Retina/HiDPI | 🟠 Alta | 🟡 Media (lógica principal hecha) | – (sin tarea de código) | **Ready to close / needs live verification** – misma base que #642, para el runner M3. |
| [#644](https://github.com/NikolayDA/picture_helper/issues/644) | Escenario de regresión E2E de release como prueba `ui` | 🟠 Alta | 🟡 Media (hecho) | – (sin tarea de código) | **Ready to close / needs live verification** – `tests/test_e2e_release_regression.py` (ui_smoke) presente mediante PR #649; la rama Ready necesita un despacho real con GL. |
| [#645](https://github.com/NikolayDA/picture_helper/issues/645) | Suite de rendimiento con GL en vivo en el arnés de benchmark | 🟡 Media | 🟡 Media (hecho) | – (sin tarea de código) | **Ready to close / needs live verification** – la suite `preview3d-live` en `scripts/benchmark.py` está presente mediante PR #649. |
| [#646](https://github.com/NikolayDA/picture_helper/issues/646) | Evaluación previa por visión, agregación de evidencia, matriz de aceptación | 🟡 Media | 🟡 Media (hecho) | – (sin tarea de código) | **Ready to close / needs live verification** – `abnahme_vision_check.py`/`abnahme_aggregate.py` presentes mediante PR #647/#649; también necesita un secreto `ANTHROPIC_API_KEY` para la evaluación real. |
| [#648](https://github.com/NikolayDA/picture_helper/issues/648) | Prueba nativa de renderizado 3D del artefacto empaquetado | 🟡 Media | 🟡 Media (código hecho) | – (tarea de evidencia) | **Reabierta** – cerrar solo tras evidencias nativas de AppImage, `.deb` instalado y DMG. |
| [#595](https://github.com/NikolayDA/picture_helper/issues/595) | [3D] Rendimiento, empaquetado, documentación, aceptación end-to-end | 🟡 Media | 🟡 Media | – (tarea de evidencia) | **Bloqueada** – espera el despacho de hardware en verde de #639. |
| [#582](https://github.com/NikolayDA/picture_helper/issues/582) | [Epic] Vista previa de relieve 3D real | 🟡 Media | 🟠 Alta (muy grande, MVP hecho) | – (epic de seguimiento) | **Blocked** – espera únicamente a #595. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restaurar la cuota de OpenAI para la comprobación manual de Codex Security | 🟢 Baja | 🟢 Baja | – (sin tarea de código) | **Blocked (external)** – sin cambios desde el 2026-07-15: un tracker puramente externo de facturación que no bloquea nada en el repositorio. |

### Recomendado a continuación (orden de PR)

1. Fusionar este seguimiento y configurar los runners en sus sesiones gráficas según `docs/RELEASE_AUTOMATION.md`.
2. Despachar `release-abnahme.yml` con tag o ID de build, todas las plataformas disponibles y el `target_issue` deseado.
3. Cerrar **#642–#646** y **#648** solo con evidencia verde completa; después **#595** y **#582**.
4. Mantener **#245** separado como tracker externo de facturación/cuota.

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
