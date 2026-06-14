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
- Los PR **#263–#269** cerraron **#257, #258, #234 + #259, #248 + #260, #231**
  y **#249**; **#261** se resolvió con el PR #268 y se cerró.

### Aún Abierto

- **O1 🟠 — Idiomas runtime adicionales.** Alemán e inglés son seleccionables
  en la app. Los idiomas de documentación es/fr/uk/zh aún no son runtime
  locales; añadirlos clave por clave en `bgremover.i18n` y cubrirlos con tests.
- **O7 🟠 — Subproceso para rembg/ONNX (derivado de #231, seguido en #270).**
  El PR #267 limitó el fallback de cierre, pero el trabajo de IA no
  interrumpible sigue en el hilo con `terminate()` como salida de emergencia.
  La solución completa mueve rembg/ONNX a un subproceso.

## Issues de GitHub Abiertos — Evaluación de Prioridad (2026-06-14, triage de cierre)

Tras fusionarse los PR **#263–#269** y cerrarse **#261** (resuelto por el PR
#268), quedan **5** issues abiertos. Nueve issues antes abiertos — **#231, #234,
#248, #249, #257, #258, #259, #260** y **#261** — se cerraron vía los PRs
fusionados. El follow-up de arquitectura aplazado de #231 (subproceso
rembg/ONNX, hoja de ruta **O7**) se registró como **#270**. Todos los issues
abiertos se reverificaron contra el código actual.

| # | Título | Relevancia | Complejidad | Recomendación |
|---|--------|------------|-------------|---------------|
| [#270](https://github.com/NikolayDA/picture_helper/issues/270) | Mover la inferencia rembg/ONNX a un subproceso (derivado de #231) | 🟠 Alta | 🟡 Media | PR de arquitectura propio: el PR #267 solo limitó el cierre. Mover rembg/ONNX a un subproceso para que `terminate()` deje de ser la salida de emergencia de IA; tests de cierre/cancelación/llamada bloqueada |
| [#232](https://github.com/NikolayDA/picture_helper/issues/232) | `import bgremover` carga toda la GUI PyQt6 | 🟡 Media | 🟡 Media | Listo para PR: conservar la API pública con exports perezosos PEP 562 y añadir un test de regresión de imports. Código sin cambios: `__init__.py:15-43` sigue re-exportando la GUI |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan falla con "Quota exceeded" | 🟡 Media | 🟢 Baja | Corregir cuota en la cuenta; en el repo solo mejorar el error y un bump opcional a Node 24, no un cambio forzado de `setup-node` |
| [#235](https://github.com/NikolayDA/picture_helper/issues/235) | El límite de memoria de undo excluye el stack de redo | 🟢 Baja | 🟡 Media | Presupuesto compartido undo/redo; solo medir original/memoria Qt. Código sin cambios: `canvas_history.py` solo cuenta `_undo_bytes`, redo limitado solo por `maxlen` |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README: la URL de clonación devuelve 404 a usuarios anónimos | 🟢 Baja | 🟢 Baja | «Ronda 5» ya está corregido; decidir público vs. privado/invitación primero, luego actualizar la guía o cerrar |

### Orden de PRs Recomendado

1. **#232** — imports ligeros mediante lazy exports PEP 562.
2. **#245** — restaurar cuota externamente; endurecimiento opcional del workflow (Node 24) aparte.
3. **#235** — implementar presupuesto compartido undo/redo.
4. **#161** — decidir el modelo de publicación, luego actualizar docs o cerrar.
5. **#270** — planificar el subproceso rembg/ONNX como PR de arquitectura propio (derivado de #231).

## Rondas Anteriores

- **2026-06-01, "modest-shannon" (A–E)** — 5 hallazgos, todos hechos.
- **v2.2, "admiring-mayer" (#1–#15)** — lista externa, completada o descartada donde fue un falso positivo.

Hallazgos históricos y registros de trabajo completos (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).
