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

Actualmente hay **8** issues abiertos. La revisión de descripciones, código,
tests y documentación confirma cinco hallazgos accionables. Tres issues
(#161/#203/#204) no demuestran una tarea del repositorio sin más evidencia y
deben cerrarse o aportar una ruta concreta de reproducción.

| # | Título | Relevancia | Complejidad | Recomendación |
|---|--------|------------|-------------|---------------|
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README: la URL de clonación devuelve 404 a usuarios anónimos | 🟢 Baja | 🟢 Baja | La URL HTTPS es correcta; cerrar como `not planned` mientras el repo sea privado o definir la vía de publicación |
| [#203](https://github.com/NikolayDA/picture_helper/issues/203) | cryptography 41.0.7 — colección de CVEs | 🟢 Baja | 🟢 Baja | No aparece en el snapshot del proyecto; cerrar como `not planned` sin una ruta reproducible y no conservar severidades incorrectas |
| [#204](https://github.com/NikolayDA/picture_helper/issues/204) | PyJWT 2.7.0 — colección de CVEs | 🟢 Baja | 🟢 Baja | No aparece en el snapshot; cerrar como `not planned` sin una ruta reproducible y corregir severidades y el enlace GHSA roto |
| [#226](https://github.com/NikolayDA/picture_helper/issues/226) | Revisión de INSTALL: releases, Raspberry Pi y diagnóstico macOS | 🟡 Media | 🟢 Baja | Los tres hallazgos siguen vigentes; actualizar el documento raíz y cinco traducciones con una nota honesta sobre artefactos |
| [#231](https://github.com/NikolayDA/picture_helper/issues/231) | `QThread.terminate()` puede abortar workers de forma insegura | 🟡 Media | 🟠 Alta | Hallazgo relevante de seguridad/estabilidad; las llamadas nativas bloqueantes requieren decisión de arquitectura y el test actual conserva el fallo |
| [#232](https://github.com/NikolayDA/picture_helper/issues/232) | `import bgremover` carga toda la GUI PyQt6 | 🟡 Media | 🟡 Media | Correcto, suficientemente documentado y listo para PR; conservar la API pública con exports perezosos PEP 562 |
| [#234](https://github.com/NikolayDA/picture_helper/issues/234) | Una migración faltante sube igualmente `schema_version` | 🟡 Media | 🟢 Baja | Bug confirmado; invertir el test y definir explícitamente la semántica de la versión 0 antes de migraciones reales |
| [#235](https://github.com/NikolayDA/picture_helper/issues/235) | El límite de memoria de undo excluye el stack de redo | 🟢 Baja | 🟡 Media | Limitar el alcance a un presupuesto compartido undo/redo; incluir imagen original y memoria Qt solo después de medir |

### Orden de PRs Recomendado

1. **#226** — pequeño fix de documentación confirmado en los seis idiomas; decidir o limitar claramente la disponibilidad de releases.
2. **#232** — exports perezosos PEP 562 con tests de regresión de imports; no requiere más aclaración.
3. **#234** — impedir el avance de versión si falta una migración y corregir el test que hoy espera lo contrario.
4. **#231** — decidir primero el modelo de cancelación; un subproceso es la opción robusta para llamadas nativas bloqueadas permanentemente.
5. **#235** — implementar opcionalmente un presupuesto compartido undo/redo tras definir el alcance.
6. **#161/#203/#204** — cerrar como `not planned` salvo que se aporte una vía concreta de publicación o dependencia.

## Rondas Anteriores

- **2026-06-01, "modest-shannon" (A–E)** — 5 hallazgos, todos hechos.
- **v2.2, "admiring-mayer" (#1–#15)** — lista externa, completada o descartada donde fue un falso positivo.

Hallazgos históricos y registros de trabajo completos (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).
