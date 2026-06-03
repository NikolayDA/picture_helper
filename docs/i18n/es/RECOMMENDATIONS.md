[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · **Español** · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Análisis de código y recomendaciones valoradas: BgRemover

## Escala de valoración

| Símbolo | Prioridad | Significado |
|---------|-----------|-------------|
| 🔴 | Crítica | Debe corregirse: provoca errores, bloqueos o inconsistencias |
| 🟠 | Alta | Debe corregirse pronto: afecta de forma importante a la fiabilidad o mantenibilidad |
| 🟡 | Media | Recomendado: mejora calidad de código, legibilidad o testabilidad |
| 🟢 | Baja | Opcional: pulido y mejoras complementarias |

---

## Estado actual (2026-06-02, revisión «adoring-johnson»)

Revisión de seguimiento tras «modest-shannon», centrada en las rutas de guardado, carga y CI. **8 puntos (N1–N8):** 7 corregidos con tests de regresión, fusionados vía **PR #142** (N1), **#143** (N6, N8), **#144** (N4, N5) y **#148** (N2, N7); 1 ya cubierto (N3). Base sigue verde: ruff/mypy limpios, suite verde.

### Estado de finalización

| Estado | Puntos |
|--------|--------|
| ✅ Hecho | N1, N2, N4, N5, N6, N7, N8 |
| ⏳ Abierto | – |

### Hallazgos

- **N1 🟠 — Liberar el cierre de la varita mágica en la ruta de error** (PR #142). Seguimiento de «modest-shannon» B: al cambiar de imagen, `_load_image_async` cancela el flood fill, que entonces no emite ni `finished` ni `error`. El reinicio del cierre solo ocurría en la ruta de éxito (`apply_loaded_image`): si la carga fallaba, `_wand_busy` quedaba activo y la varita bloqueada sobre la imagen anterior. Nueva `reset_pending_wand()` silenciosa justo al lado de `cancel_flood_fill()`.
- **N2 🟡 — Límite de tamaño en la rotación** (PR #148). `rotate_image` (`image_ops.py`) rota con `expand=True`; la protección de megapíxeles solo aplicaba en la carga (`Image.MAX_IMAGE_PIXELS`), no al resultado: una imagen apenas dentro del límite podía inflarse a ~2× a ~45°. Ahora `rotated_size()` estima de antemano la bounding box expandida; `apply_rotate` rechaza los resultados que superan el límite con un mensaje de estado.
- **N3 ➖ — Presupuesto de memoria del historial** (ya cubierto). `CanvasHistory` (`canvas_history.py`) impone desde hace tiempo el presupuesto de deshacer vía `_trim()`/`_UNDO_MEMORY_LIMIT`, con rehacer limitado por `_REDO_MAX_ENTRIES`. Sin acción necesaria.
- **N4 🟢 — Honestidad de extensión al guardar** (PR #144). `save_image_file` escribía silenciosamente bytes PNG para extensiones desconocidas; ahora un rechazo claro con `ValueError`, mientras que una extensión vacía sigue siendo el PNG por defecto.
- **N5 🟡 — Guardado atómico** (PR #144). Escribir directamente al destino destruía el archivo existente si se abortaba. Ahora `mkstemp` → `os.replace` en el directorio de destino (el patrón de `qt_plugins._copy_if_needed`), conservando permisos y limpiando el temporal.
- **N6 🟡 — `libgl1` en la matriz completa de CI + test de deriva** (PR #143). La matriz completa no instalaba `libgl1` (a diferencia de las otras fuentes de paquetes Qt) → `import PyQt6` arriesgaba `libGL.so.1`. Añadido; el nuevo `test_ci_qt_packages.py` mantiene consistentes las cuatro listas de paquetes.
- **N7 🟢 — Importaciones tempranas** (PR #148). `workers.py` importaba `rembg` (que arrastra onnxruntime) a nivel de módulo; como `main_window` carga `workers`, el coste de importación se pagaba al arrancar, incluso sin usar la IA. Ahora una sonda `find_spec` para `REMBG_AVAILABLE` más una importación diferida de `rembg` solo en el hilo del worker (warmup/primer clic de IA).
- **N8 🟢 — Docstring obsoleta de `load_image`** (PR #143). Nombraba la ruta de drop como invocador síncrono, aunque arrastrar y soltar lleva tiempo siendo asíncrono. Corregido.

---

## Recomendaciones abiertas

Mejoras surgidas del segundo análisis aún no implementadas (producto/proceso):

- **O1 🟠 — Localización de la app.** i18n en tiempo de ejecución implementada: `bgremover.i18n` con una tabla central de cadenas y un fallback estable al alemán; **alemán e inglés** se pueden cambiar en tiempo de ejecución (selector de idioma en el diálogo de ajustes con aviso de reinicio). Toda la superficie visible —incluidos los mensajes de estado del lienzo, las entradas del historial y los diálogos— pasa por `tr()`, protegida por una comprobación AST contra nuevos literales sin traducir. Abierto: los demás idiomas de documentación existentes (es/fr/uk/zh) como locales de tiempo de ejecución (**PR 4c**).
- **O2 🟡 — App de Linux / empaquetado.** No hay bundle para Linux; arranque solo vía `python -m bgremover` desde una venv. Un paquete instalable (AppImage/Flatpak/`.deb`) para **Raspberry Pi OS** y grandes distribuciones (Debian/Ubuntu/Fedora) reduce la barrera de entrada para quienes no programan, análogo al bundle `.app` de macOS.
**✅ Hecho:** O4/O6 — cambio de herramienta con una tecla (`W`/`B`/`E`/`L`) e indicaciones `Cmd`/`Ctrl` por plataforma (PR #146, `test_tool_shortcuts.py`); O3 — matriz completa además semanal por cron (PR #149); O5 — el subconjunto `ui_smoke` corre en PR/Full CI, la suite qtbot completa sigue nightly (PR #149).

## Plan de implementación por paquetes de PR (desde 2026-06-02)

- **PR 0 — Endurecimiento del código (N2 + N7).** ✅ Hecho (PR #148). N2 — aplicar la barrera de megapíxeles también al resultado de la rotación (`rotated_size()` estima el tamaño objetivo de antemano, `apply_rotate` rechaza los resultados sobre el límite con un mensaje de estado); N7 — importar `rembg` de forma diferida y sondear `REMBG_AVAILABLE` con `find_spec` (el manejo de fallo de warmup existente cubre un backend defectuoso).
- **PR 1 — Atajos de herramientas e indicaciones.** ✅ Hecho (PR #146). O4 + O6: cambio con una tecla (`W`/`B`/`E`/`L`), estado marcado de la toolbar sincronizado, tooltips/README/manual actualizados, test de regresión para el cableado de atajos.
- **PR 2 — CI antes y con más cobertura.** ✅ Hecho (PR #149). O3 — matriz completa además semanal (cron); O5 — subconjunto `ui_smoke` en PR/Full CI, Nightly UI conserva la suite completa.
- **PR 3 — Base de i18n.** ✅ Hecho. O1 preparado: `bgremover.i18n` con locale/fallback en runtime, alemán como default estable, primera tabla central de strings para mensajes de estado, menú, toolbar, pestañas, historial y barra de recorte; tests de regresión para normalización de locale, fallback y wiring UI.
- **PR 4 — Despliegue i18n.** ✅ Hecho. O1 hecho usable: **4a** — cobertura `tr()` extendida al panel derecho, el diálogo de ajustes y todos los diálogos (alemán byte-idéntico, verificado con golden diff); **4b** — tabla inglesa completa + selector de idioma (persistencia, aviso de reinicio); **4b.1** — mensajes de estado del lienzo, descripciones del historial y diálogos de `main_window` (abrir/guardar/color/sin guardar) vía `tr()`, más un guard AST contra nuevos literales sin traducir en los puntos visibles al usuario. Probadas la paridad de claves/marcadores y el smoke de UI por locale.
- **PR 4c — i18n más idiomas (opcional, aplazado).** Si hace falta, añadir es/fr/uk/zh como locales de runtime (reflejar las tablas clave por clave — paridad/smoke/guard se aplican entonces automáticamente). Actualmente sin planificar.
- **PR 5 — Base de empaquetado Linux.** Iniciar O2: elegir artefacto objetivo (AppImage/`.deb`/Flatpak), desktop file/icono/metadatos AppStream y smoke de build Linux.
- **PR 6 — Ampliación del empaquetado Linux.** Completar O2: variante para Raspberry Pi OS, segunda forma de paquete opcional y workflow de release para artefactos Linux.

---

## Rondas anteriores

- **2026-06-01, «modest-shannon» (A–E)** — 5 hallazgos, todos hechos (PR #135/#136); entre ellos el manejo de bombas de descompresión y el ciclo de vida de la varita que N1 completa ahora en la ruta de error.
- **v2.2, «admiring-mayer» (#1–#15)** — lista externa, #1–#15 hechos, #4 descartado (falso positivo).

Hallazgos históricos y registros de trabajo completos (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).
