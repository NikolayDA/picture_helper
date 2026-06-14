[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · **Español** · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Análisis de Código y Recomendaciones Priorizadas: BgRemover

## Escala de Prioridad

| Símbolo | Prioridad | Significado |
|---------|-----------|-------------|
| 🔴 | Crítica | Errores, cierres inesperados o pérdida de datos |
| 🟠 | Alta | Impacto claro en fiabilidad o mantenibilidad |
| 🟡 | Media | Mejora útil para calidad, legibilidad o testabilidad |
| 🟢 | Baja | Pulido opcional o mejora de proceso |

## Estado Actual (2026-06-04)

La lista activa de análisis de código está vacía. Ruff, mypy y la suite local
de tests siguen siendo la baseline antes de nuevos PRs.

### Completado Desde La Última Revisión

- **N1/N2/N4/N5/N6/N7/N8** están hechos: rutas de error, límite de tamaño,
  extensiones, guardado atómico, paquetes Qt de CI, import perezoso y docstring.
- **O2/O3/O4/O5/O6** están implementados: paquetes Linux, workflow de release,
  matriz completa, `ui_smoke` y atajos correctos por plataforma.
- Los hallazgos **#163–#206** se cerraron en los PRs documentados y quedaron
  protegidos por tests de regresión o comprobaciones de CI.

### Aún Abierto

- **O1 🟠 — Idiomas runtime adicionales.** Alemán e inglés son seleccionables
  en la app. Los idiomas de documentación es/fr/uk/zh aún no son runtime
  locales; añadirlos clave por clave en `bgremover.i18n` y cubrirlos con tests.

## Issues de GitHub Abiertos — Evaluación de Prioridad (2026-06-14)

Actualmente hay **15** issues abiertos. La revisión de descripciones, código,
tests y documentación muestra: **nueve** hallazgos están bien delimitados y
listos para PR, dos (#231/#235) requieren antes una decisión de arquitectura o
alcance, #245 es un problema de infraestructura/facturación (no un defecto de
código) y tres (#161/#203/#204) no demuestran una tarea del repositorio sin más
evidencia.

| # | Título | Relevancia | Complejidad | Recomendación |
|---|--------|------------|-------------|---------------|
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README: la URL de clonación devuelve 404 a usuarios anónimos | 🟢 Baja | 🟢 Baja | La URL HTTPS es correcta; cerrar como `not planned` mientras el repo sea privado o definir la vía de publicación |
| [#203](https://github.com/NikolayDA/picture_helper/issues/203) | cryptography 41.0.7 — colección de CVEs | 🟢 Baja | 🟢 Baja | No aparece en el snapshot del proyecto; cerrar como `not planned` sin una ruta reproducible y no conservar severidades incorrectas |
| [#204](https://github.com/NikolayDA/picture_helper/issues/204) | PyJWT 2.7.0 — colección de CVEs | 🟢 Baja | 🟢 Baja | No aparece en el snapshot; cerrar como `not planned` sin una ruta reproducible y corregir severidades y el enlace GHSA roto |
| [#226](https://github.com/NikolayDA/picture_helper/issues/226) | Revisión de INSTALL: releases, Raspberry Pi y diagnóstico macOS | 🟡 Media | 🟢 Baja | Listo para PR: los tres hallazgos siguen vigentes; actualizar el documento raíz y cinco traducciones con una nota honesta sobre artefactos |
| [#231](https://github.com/NikolayDA/picture_helper/issues/231) | `QThread.terminate()` puede abortar workers de forma insegura | 🟡 Media | 🟠 Alta | Necesita refinamiento: las llamadas nativas bloqueantes requieren decisión de arquitectura (subproceso); el test actual conserva el fallo |
| [#232](https://github.com/NikolayDA/picture_helper/issues/232) | `import bgremover` carga toda la GUI PyQt6 | 🟡 Media | 🟡 Media | Listo para PR: conservar la API pública con exports perezosos PEP 562 y añadir un test de regresión de imports |
| [#234](https://github.com/NikolayDA/picture_helper/issues/234) | Una migración faltante sube igualmente `schema_version` | 🟡 Media | 🟢 Baja | Listo para PR: impedir el avance de versión, invertir el test y definir la semántica de la versión 0 |
| [#235](https://github.com/NikolayDA/picture_helper/issues/235) | El límite de memoria de undo excluye el stack de redo | 🟢 Baja | 🟡 Media | Necesita refinamiento: limitar el alcance a un presupuesto compartido undo/redo; incluir imagen original y memoria Qt solo tras medir |
| [#244](https://github.com/NikolayDA/picture_helper/issues/244) | Código muerto: `ImageCanvas._zoom` y el wrapper `launch_worker` sin uso | 🟢 Baja | 🟢 Baja | Listo para PR: eliminar `_zoom`, decidir eliminar vs. API documentada para `launch_worker`; pequeño PR de limpieza |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan falla con "Quota exceeded" | 🟡 Media | 🟢 Baja | Infraestructura/facturación: restaurar la cuota de OpenAI a nivel de cuenta; hacer el workflow resiliente a cortes de cuota y subir `setup-node` a Node 24 |
| [#247](https://github.com/NikolayDA/picture_helper/issues/247) | Un crop activo sobrevive a transformaciones y produce píxeles erróneos | 🟠 Alta | 🟡 Media | Listo para PR (prioritario): resetear el estado transitorio en cada cambio de imagen; test de regresión (400×200 + rotación 90°) descrito en el issue |
| [#248](https://github.com/NikolayDA/picture_helper/issues/248) | Escape borra la selección en vez de cancelar el lazo poligonal | 🟡 Media | 🟡 Media | Listo para PR: prioridad de Escape crop → lazo → deshacer selección; comparte el contrato de estado transitorio con #247 |
| [#249](https://github.com/NikolayDA/picture_helper/issues/249) | Las asociaciones de archivo pasan rutas pero la app no las abre | 🟡 Media | 🟡 Media | Listo para PR: abrir rutas de arranque y el `QFileOpenEvent` de macOS por la ruta de carga validada |
| [#250](https://github.com/NikolayDA/picture_helper/issues/250) | El workflow de release publica artefactos sin gate de CI completo | 🟠 Alta | 🟡 Media | Listo para PR (antes del próximo tag): forzar CI completa con `needs`, verificar tag/`project.version`, eliminar `\|\| true` |
| [#251](https://github.com/NikolayDA/picture_helper/issues/251) | Una selección vacía conserva la QPixmap de overlay tras borrar | 🟡 Media | 🟢 Baja | Listo para PR (rápido): liberar la pixmap de overlay cuando la máscara queda vacía; parche exacto en el issue |

### Orden de PRs Recomendado

1. **#247** — Alta: bug de corrección/datos (un rectángulo de crop obsoleto genera píxeles transparentes); totalmente delimitado, con test de regresión.
2. **#250** — Alta antes del próximo tag de release: forzar el gate de CI completa con `needs`, conciliar tag/versión, eliminar `|| true`.
3. **#251** — fix rápido de memoria: una máscara vacía libera la pixmap de overlay; el parche exacto está en el issue.
4. **#244** — limpieza de código muerto (eliminar `_zoom`, decidir sobre `launch_worker`); PR pequeño y de bajo riesgo.
5. **#234** — impedir el avance de versión si falta una migración y corregir el test que hoy espera lo contrario.
6. **#248** — prioridad de Escape crop → lazo → deshacer selección; comparte el contrato de estado transitorio con #247 y se puede agrupar.
7. **#232** — exports perezosos PEP 562 con un test de regresión de imports.
8. **#249** — abrir rutas de arranque y el `QFileOpenEvent` de macOS por la ruta de carga validada.
9. **#226** — fix de documentación en los seis idiomas; documentar honestamente la disponibilidad de releases.
10. **#245** — restaurar la facturación de OpenAI a nivel de cuenta; hacer el workflow del scan resiliente a cortes de cuota y subir `setup-node` a Node 24.
11. **#231** — decidir primero el modelo de cancelación (subproceso para llamadas nativas bloqueadas permanentemente), luego implementar.
12. **#235** — implementar un presupuesto compartido de memoria undo/redo solo tras definir el alcance.
13. **#161/#203/#204** — cerrar como `not planned` salvo que se aporte una vía concreta de publicación o dependencia.

## Rondas Anteriores

- **2026-06-01, "modest-shannon" (A–E)** — 5 hallazgos, todos hechos.
- **v2.2, "admiring-mayer" (#1–#15)** — lista externa, completada o descartada donde fue un falso positivo.

Hallazgos históricos y registros de trabajo completos (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).
