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

La lista activa de análisis de código está vacía. La última revisión de
seguimiento está implementada y cubierta por tests; ruff, mypy y la suite local
siguen siendo la baseline antes de nuevos PRs.

### Completado Desde La Última Revisión

- **N1/N2/N4/N5/N6/N7/N8** están hechos: ruta de error de la varita, límite de
  tamaño al rotar, extensiones honestas, guardado atómico, paquetes Qt de CI,
  import perezoso de `rembg` y docstring de `load_image`.
- **O2/O3/O4/O5/O6** están implementados: Linux AppImage/`.deb`, release
  workflow, matriz completa semanal, `ui_smoke` en PR/Full CI y atajos de
  herramientas con indicaciones correctas por plataforma.
- **#164/#167/#168** están hechos (PRs #172/#174/#173); los hallazgos
  restantes ya se completaron también vía #176/#178.
- **Verificado como resuelto limpiamente el 2026-06-06** (PRs #188–#193, cada
  uno con test de regresión, `make check` en verde – 504 passed): **#163**
  (enlaces del CHANGELOG cambiados a SHAs de commit reales y resolubles en
  GitHub; cuatro features 2.3.0 faltantes + entrada idna/urllib3; etiquetas git
  reales no creadas a propósito), **#165/#180** (TESTING.md: filtro `addopts`,
  `ui_smoke`, schedule semanal, shellcheck, `make coverage`), **#184**
  (generación de carga + recheck de `content_revision` contra cargas async
  tardías), **#182** (`PIP_CONSTRAINT` integrado en el build de AppImage),
  **#183** (license-check en solo-lectura + job de comentario aislado), **#177**
  (assertions de comportamiento + nuevo `tests/test_history_popup.py`).

### Aún Abierto

- **O1 🟠 — Idiomas runtime adicionales.** Alemán e inglés son seleccionables
  en la app. Los idiomas existentes en la documentación (es/fr/uk/zh) aún no
  son runtime locales; si hace falta, añadirlos clave por clave en
  `bgremover.i18n` y protegerlos con tests de paridad/smoke.

## Issues de GitHub Abiertos — Evaluación de Prioridad (2026-06-10)

Ahora **tres** issues abiertos. **#176 está resuelto** (lote de calidad de
código vía PRs #198/#214, issue cerrado); antes #166/#178/#185 (PRs #219–#221),
#205/#206 (PR #222) y #199/#200/#201/#202 (PRs #215/#209/#211). Del lote de
`pip-audit` del 2026-06-07 (#200–#206) solo quedan abiertos los puntos de
observación #203/#204; #195 sigue cerrado y verificado.

Triaje del lote de seguridad frente al estado real del proyecto
(`requirements/constraints.txt` + `pyproject.toml`):

- **#200/#201 están hechos (PR #209)** — `setuptools` ahora está fijado a
  `>=78.1.1` en `pyproject.toml` (`[build-system]`) y `constraints.txt`, y
  `wheel` a `==0.46.2`; tests de regresión ligados a CVE lo protegen.
- **#202 (pip) está hecho (PR #211)** — se exige `pip>=26.1.2` en los pasos de
  setup de CI (`ci.yml`/`pr-ci.yml`/`ui-nightly.yml`/`benchmark.yml`/
  `license-check.yml`), el hook SessionStart web y los docs de instalación dev;
  un test de regresión ligado a CVE lo protege.
- **#203 (cryptography)/#204 (pyjwt)** **no** son dependencias del proyecto
  (puramente transitivas/del sistema) → informativo, sin cambio en
  `constraints.txt`.
- **#205 (urllib3)/#206 (idna) están hechos (PR #222)** — el proyecto fija las
  versiones parcheadas (`urllib3==2.7.0`, `idna==3.15`); tests de regresión
  ligados a CVE lo congelan y el hook SessionStart ahora instala con
  constraints.

| # | Título | Relevancia | Complejidad | Recomendación |
|---|--------|------------|-------------|---------------|
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | Auditoría del README: un enlace roto y una referencia interna | 🟡 Media | 🟢 Baja | Bloqueado: jerga "Runde 5" eliminada; solo queda la URL de clonación (decisión del owner sobre visibilidad del repo) |
| [#203](https://github.com/NikolayDA/picture_helper/issues/203) | cryptography 41.0.7 — HIGH/MEDIUM: 6 CVEs | 🟢 Baja | 🟢 Baja | No es dependencia del proyecto (transitiva/sistema) → informativo, sin cambio en `constraints.txt` |
| [#204](https://github.com/NikolayDA/picture_helper/issues/204) | pyjwt 2.7.0 — HIGH/MEDIUM: 5 CVEs | 🟢 Baja | 🟢 Baja | No es dependencia del proyecto → informativo, sin acción del proyecto |

### Orden de PRs Recomendado

1. **#200 hecho (PR #209)** — `setuptools>=78.1.1` fijado en `pyproject.toml` (`[build-system]`) **y** `constraints.txt`; RCE CRITICAL cerrado.
2. **#201 hecho (PR #209)** — `wheel==0.46.2` fijado en `constraints.txt`; agrupado con #200 como un único PR de fijado de cadena de suministro.
3. **#202 hecho (PR #211)** — `pip>=26.1.2` exigido en los pasos de setup de CI, el hook SessionStart + docs de instalación dev; lote de CVE (path traversal/symlink/secuestro de módulos) cerrado.
4. **#176 hecho (PRs #198/#214)** — eliminado el ignore global de `E741`, `check_untyped_defs` activo para `canvas`/`main_window`/`worker_controller`, la espera de cancel_ai es visible vía mensaje de estado, `shutdown_all` anula referencias de hilos; tests dedicados para `app.py`/`main_window.py`. Verificado contra `main` el 2026-06-10 (`make check` en verde).
5. **#199 hecho (PR #215)** — eliminado `_redo_max` (solo de escritura) de `canvas_history.py`; test de regresión `test_redo_stack_capped_by_maxlen`, `make check` en verde.
6. **#166 hecho (PR #219)** — docstrings/comentarios en inglés traducidos al alemán en todo el paquete; comentario "sin copia propia" precisado.
7. **#185 hecho (PR #220)** — el diagnóstico redacta `$HOME`/rutas y solo imprime un resumen filtrado del log; flag `--include-raw-logs` + test de shell.
8. **#178 hecho (PR #221)** — tests pasados a accessors públicos, checks AST sustituidos por tests de comportamiento, tests duplicados eliminados (de #168).
9. **#205/#206 hechos (PR #222)** — fijados limpios congelados con tests de regresión ligados a CVE, el hook SessionStart instala con constraints; issues cerrados.
10. **#203/#204 como puntos de observación** — no son dependencias del proyecto; fijar solo si un futuro feature las incorpora directamente.
11. **#161 aplazado** — "Runde 5" hecho; solo queda la URL de clonación (decisión del owner sobre visibilidad del repo).

## Rondas Anteriores

- **2026-06-01, "modest-shannon" (A–E)** — 5 hallazgos, todos hechos.
- **v2.2, "admiring-mayer" (#1–#15)** — lista externa, hecha o descartada
  donde fue un falso positivo.

Hallazgos históricos y registros de trabajo completos (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).
