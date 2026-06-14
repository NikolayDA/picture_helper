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

Tras la triage quedan **13** issues abiertos. **#203/#204** se cerraron como
`not planned` porque no son dependencias del proyecto; **#226/#244** ya estaban
resueltos por los PR #246 y #256. Once issues tienen alcance implementable en
el repositorio. #161 requiere decidir el modelo de publicación y #245 exige
principalmente corregir la cuota/facturación de la cuenta.

| # | Título | Relevancia | Complejidad | Recomendación |
|---|--------|------------|-------------|---------------|
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README: la URL de clonación devuelve 404 a usuarios anónimos | 🟢 Baja | 🟢 Baja | «Ronda 5» ya está corregido; decidir público vs. privado/invitación antes de cambiar la guía de clonación |
| [#231](https://github.com/NikolayDA/picture_helper/issues/231) | `QThread.terminate()` puede abortar workers de forma insegura | 🟠 Alta | 🟡 Media | Primer PR: limitar el segundo wait, registrar y probar el error; tratar el subproceso por separado |
| [#232](https://github.com/NikolayDA/picture_helper/issues/232) | `import bgremover` carga toda la GUI PyQt6 | 🟡 Media | 🟡 Media | Listo para PR: conservar la API pública con exports perezosos PEP 562 y añadir un test de regresión de imports |
| [#234](https://github.com/NikolayDA/picture_helper/issues/234) | Una migración faltante sube igualmente `schema_version` | 🟡 Media | 🟢 Baja | Agrupar con #259: una migración faltante no debe marcar ni modificar los settings |
| [#235](https://github.com/NikolayDA/picture_helper/issues/235) | El límite de memoria de undo excluye el stack de redo | 🟢 Baja | 🟡 Media | Presupuesto compartido undo/redo; solo medir/documentar imagen original y memoria Qt |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan falla con "Quota exceeded" | 🟡 Media | 🟢 Baja | Corregir cuota en la cuenta; en el repo solo mejorar el error, no `setup-node` |
| [#248](https://github.com/NikolayDA/picture_helper/issues/248) | Escape borra la selección en vez de cancelar el lazo poligonal | 🟡 Media | 🟡 Media | Agrupar con #260: prioridad central crop → lazo → deshacer selección |
| [#249](https://github.com/NikolayDA/picture_helper/issues/249) | Las asociaciones de archivo pasan rutas pero la app no las abre | 🟡 Media | 🟡 Media | Listo para PR: abrir rutas de arranque y el `QFileOpenEvent` de macOS por la ruta de carga validada |
| [#257](https://github.com/NikolayDA/picture_helper/issues/257) | Follow-ups de release: contexto, tag gate y artefactos de re-run | 🟠 Alta | 🟡 Media | PR prioritario independiente antes del próximo tag; cambiar workflow, docs y tests juntos |
| [#258](https://github.com/NikolayDA/picture_helper/issues/258) | El límite de carga puede preasignar 512 MiB | 🟠 Alta | 🟡 Media | PR independiente: lectura por chunks, error localizado y límite preciso |
| [#259](https://github.com/NikolayDA/picture_helper/issues/259) | Recent Files modifica un schema futuro | 🟠 Alta | 🟡 Media | Agrupar con #234: mantener schemas futuros en modo solo lectura |
| [#260](https://github.com/NikolayDA/picture_helper/issues/260) | Descartar crop deja un cursor de herramienta incorrecto | 🟡 Media | 🟢 Baja | Agrupar con #248 y probar cancelación central más restauración del cursor |
| [#261](https://github.com/NikolayDA/picture_helper/issues/261) | El overlay del pincel escanea toda la máscara en cada movimiento | 🟡 Media | 🟡 Media | PR de rendimiento independiente con contador de píxeles y spy test |

### Orden de PRs Recomendado

1. **#257** — hacer fiable el workflow de release antes del próximo tag.
2. **#258** — eliminar la preasignación y corregir los errores de tamaño.
3. **#234 + #259** — migración QSettings y protección de schema futuro.
4. **#248 + #260** — cancelación central Escape/crop y cursor correcto.
5. **#231** — entregar fallback limitado; subproceso en un trabajo posterior.
6. **#261** — quitar el escaneo O(tamaño de imagen) del camino del pincel.
7. **#249** — procesar asociaciones de archivos y eventos open de macOS.
8. **#232** — imports ligeros mediante lazy exports PEP 562.
9. **#235** — implementar presupuesto compartido undo/redo.
10. **#245** — restaurar cuota externamente; endurecimiento del workflow aparte.
11. **#161** — decidir publicación y después actualizar docs o cerrar.

## Rondas Anteriores

- **2026-06-01, "modest-shannon" (A–E)** — 5 hallazgos, todos hechos.
- **v2.2, "admiring-mayer" (#1–#15)** — lista externa, completada o descartada donde fue un falso positivo.

Hallazgos históricos y registros de trabajo completos (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).
