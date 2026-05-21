[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · **Español** · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Análisis de código y recomendaciones evaluadas: BgRemover

## Escala de evaluación

| Símbolo | Prioridad | Significado |
|--------|-----------|-----------|
| 🔴 | Crítico | Debe corregirse – provoca errores, fallos o inconsistencias |
| 🟠 | Alta | Debería corregirse pronto – afecta considerablemente la fiabilidad o el mantenimiento |
| 🟡 | Media | Recomendado – mejora la calidad del código, la legibilidad o la testabilidad |
| 🟢 | Baja | Opcional – pulido, mejoras complementarias |

---

## Resumen priorizado

| # | Recomendación | Prioridad | Esfuerzo |
|---|-----------|-----------|---------|
| 1 | ~~Conflicto de versión de Python en los type hints~~ | ✅ Corregido | – |
| 2 | ~~Captura de excepciones demasiado amplia en la importación de rembg~~ | ✅ Corregido | – |
| 3 | ~~Condiciones de carrera en los hilos de worker~~ | ✅ Corregido | – |
| 4 | ~~Validación del tamaño de imagen al cargar~~ | ✅ Corregido | – |
| 5 | ~~Consumo de memoria de la pila de Deshacer~~ | ✅ Corregido | – |
| 6 | ~~Dividir las clases dios~~ | ✅ Corregido | – |
| 7 | ~~Refactorizar métodos demasiado largos~~ | ✅ Corregido | – |
| 8 | ~~Reemplazar números mágicos~~ | ✅ Corregido | – |
| 9 | ~~Pruebas para escenarios de hilos~~ | ✅ Corregido | – |
| 10 | ~~Añadir type hints de retorno~~ | ✅ Corregido | – |
| 11 | ~~Añadir docstrings~~ | ✅ Corregido | – |
| 12 | ~~Ruta del archivo de registro independiente de la plataforma~~ | ✅ Corregido | – |
| 13 | ~~Deduplicar el boilerplate de hilos~~ | ✅ Corregido | – |

---

## Recomendaciones en detalle

### ✅ 1. Conflicto de versión de Python en los type hints *(corregido)*

**Archivo**: `pyproject.toml`

`requires-python` se elevó a `>=3.10`, `ruff target-version` se actualizó a `py310`. La sintaxis `X | Y` (PEP 604) utilizada en el código queda así cubierta por los requisitos mínimos declarados.

---

### ✅ 2. Captura de excepciones demasiado amplia en la importación de rembg *(corregido)*

**Archivo**: `BgRemover.py` (línea 41)

`except BaseException:` se reemplazó por `except (ImportError, RuntimeError, OSError, SystemExit):`. `KeyboardInterrupt` y otras señales críticas ya no se capturan. `SystemExit` se mantiene explícitamente incluida, ya que versiones conocidas de rembg/onnxruntime pueden lanzarla durante la importación.

---

### ✅ 3. Condiciones de carrera en los hilos de worker *(corregido)*

**Archivo**: `BgRemover.py`

- El nuevo helper `_launch_worker()` en `MainWindow` encapsula el boilerplate de hilos idéntico (estaba triplicado). Los tres flujos (Image Load, AI, Warmup) lo usan ahora.
- La comprobación de obsolescencia en `_on_ai_done()` usa ahora `_canvas._version` (contador entero monótono que se incrementa en cada cambio de imagen en `apply_loaded_image()`) en lugar de la frágil comparación de identidad de objeto con `is`. `_ai_input_version` en `MainWindow` guarda el valor al iniciar la IA.

---

### ✅ 4. Falta de validación del tamaño de imagen al cargar *(corregido)*

**Archivo**: `BgRemover.py`

Se introdujo la constante `_MAX_MEGAPIXELS = 100`. Comprobación tras el `Image.open()` perezoso en dos lugares:
- `ImageLoadWorker.run()`: emite la señal `error` con mensaje de error (ruta del diálogo de archivo)
- `ImageCanvas.load_image()`: emite `statusMsg` y aborta (ruta de arrastrar y soltar)

---

### ✅ 5. Alto consumo de memoria de la pila de Deshacer *(corregido)*

**Archivo**: `BgRemover.py`

Se introdujo la constante `_UNDO_MEMORY_LIMIT = 256 MB`. La pila de Deshacer ya no tiene un `maxlen` rígido – en su lugar, tras cada push se calcula el tamaño total (estimado como `width × height × 4` bytes por imagen RGBA) y se eliminan las entradas más antiguas mientras se supere el límite.

---

### ✅ 6. Dividir las clases dios *(corregido)*

**Archivo**: `BgRemover.py`

Las 6 funciones helper anidadas de `_build_right_panel()` (`sec`, `lbl`, `hdivider`, `scroll_tab`, `btn`, `slider_row`) se extrajeron como métodos de clase `@staticmethod` de `MainWindow`: `_make_section`, `_make_label`, `_make_hdivider`, `_make_scroll_tab`, `_make_panel_btn`, `_make_slider`. `_TAB_STYLE` se externalizó como atributo de clase.

---

### ✅ 7. Refactorizar métodos demasiado largos *(corregido)*

**Archivo**: `BgRemover.py`

Las 8 ramas de dibujo de iconos de `make_tool_icon()` (175 líneas, cascada if-elif) se extrajeron como funciones de módulo propias: `_draw_wand_icon`, `_draw_brush_icon`, `_draw_eraser_icon`, `_draw_ai_icon`, `_draw_open_icon`, `_draw_save_icon`, `_draw_undo_icon`, `_draw_restore_icon`. `make_tool_icon()` es ahora un dispatcher ligero sobre un `dict`.

---

### ✅ 8. Reemplazar números mágicos por constantes con nombre *(corregido)*

**Archivo**: `BgRemover.py`

Nuevo bloque de constantes en la cabecera del módulo:
- Diseño de la interfaz: `_TOOLBAR_WIDTH`, `_TOOLBAR_BTN_SIZE`, `_TOOLBAR_ICON_SIZE`, `_RIGHT_PANEL_WIDTH`, `_CROP_BAR_HEIGHT`, `_HISTORY_LIST_H`, `_COLOR_BTN_SIZE`, `_TAB_ICON_PX`, `_WINDOW_MIN_W/H`
- Valores por defecto del lienzo: `_DEFAULT_TOLERANCE`, `_DEFAULT_BRUSH_RADIUS`, `_ZOOM_FACTOR`
- Color de superposición: `_OVERLAY_COLOR`

Todos los puntos de uso en el código se cambiaron a las constantes.

---

### ✅ 9. Pruebas para las rutas de error de los worker *(corregido)*

**Archivo**: `tests/test_workers.py` (nuevo, 9 pruebas)

Nuevas pruebas:
- `ImageLoadWorker`: archivo faltante, archivo corrupto, imagen sobredimensionada (vía Mock)
- `ImageLoadWorker`: caso normal (no se espera error)
- `ImageCanvas.load_image()`: imagen sobredimensionada (ruta de arrastrar y soltar)
- `AIWorker`: señal de error ante excepción de `rembg_remove`, caso de éxito (vía Mock)
- Contador `_version` del lienzo: se incrementa en `apply_loaded_image`, sin cambios al deshacer

---

### ✅ 10. Type hints de retorno añadidos *(corregido)*

**Archivo**: `BgRemover.py`

77 funciones y métodos sin anotación de retorno se proveyeron con `-> None` (o un tipo específico). Además se añadió `QFont` a la importación de PyQt6 (necesaria para `_text_font() -> QFont`).

---

### ✅ 11. Falta de docstrings en métodos auxiliares *(corregido)*

**Archivo**: `BgRemover.py`

Se añadieron docstrings de una línea a `_make_label`, `_make_hdivider`, `_make_panel_btn` y `_make_slider`. Los generadores de cursor (`make_wand_cursor`, `make_brush_cursor`, `make_eraser_cursor`) ya tenían docstrings.

---

### ✅ 12. Hacer la ruta del archivo de registro independiente de la plataforma *(corregido)*

**Archivo**: `BgRemover.py`

Se añadió `QStandardPaths` a las importaciones de PyQt6. La ruta de registro se cambió de `Path.home() / ".bgremover.log"` a `QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation) / "bgremover.log"` (Linux: `~/.local/share/BgRemover/`, macOS: `~/Library/Application Support/BgRemover/`).

---

### ✅ 13. Deduplicar el boilerplate de hilos duplicado *(corregido)*

**Archivo**: `BgRemover.py`

El helper `_launch_worker()` ya se introdujo como parte de la corrección #3 (condiciones de carrera). Los tres flujos de worker (Image Load, AI, Warmup) lo usan desde entonces.

---

## Ronda 2 – Revisión de seguimiento (código, pruebas, documentación, licencia)

> Corrección a la ronda 1: Los puntos **#6 (clases dios)** y **#8
> (números mágicos)** estaban marcados como ✅, pero solo aplicaban
> _parcialmente_ (`MainWindow`/`_build_right_panel` se mantenía en
> ~300 líneas; bastantes números de stylesheet/diseño quedaron inline).
> La ronda 2 aborda los puntos restantes.

| # | Recomendación | Prioridad | Estado |
|---|-----------|-----------|--------|
| R1 | Configuración de logging: llamada antes de `QApplication`, directorio no creado | 🔴 | ✅ Corregido |
| R2 | El flood-fill bloquea la interfaz; el límite de 100 MP es demasiado alto | 🟠 | ✅ Corregido |
| R3 | Arrastrar y soltar / «Abiertos recientemente» eludían el worker asíncrono | 🟠 | ✅ Corregido |
| R4 | Ruptura de encapsulación (`_pil`/`_version`/`_img_item`/`_cx…`) | 🟡 | ✅ Corregido |
| R5 | `undo_to` inconsistente (no restaurable) | 🟡 | ✅ Corregido |
| R6 | `MainWindow` objeto dios / `_build_right_panel` | 🟡 | ✅ Corregido |
| R7 | Sin comprobación de tipos en el CI | 🟡 | ✅ Corregido |
| R8 | `pyproject` ignoraba `F401` globalmente | 🟢 | ✅ Corregido |
| R9 | `make_tool_icon`: importación en bucle, `except` silencioso | 🟢 | ✅ Corregido |
| R10 | `_apply_pil` sumaba la pila de Deshacer O(n) por acción | 🟢 | ✅ Corregido |
| R11 | Sin protección contra bomba de descompresión | 🟡 | ✅ Corregido |
| R12 | Lagunas en las pruebas (evicción de Deshacer, geometría, lazo, drop) | 🔴/🟠 | ✅ Corregido |
| R13 | Documentación: versión de Python incorrecta, licencia faltante | 🟠 | ✅ Corregido |

**R1** — El logging se externalizó a `_setup_logging()`; se invoca en
`__main__` **después** de `QApplication` +
`setApplicationName/​setOrganizationName`. El directorio de destino se
crea vía `mkdir(parents=True, exist_ok=True)` (fallback `~/.bgremover`).

**R2** — `flood_fill` está vectorizado (máscara de similitud en pocas
operaciones de NumPy, luego crecimiento de región); `_MAX_MEGAPIXELS` de
100 → 40.

**R3** — Nueva señal `ImageCanvas.loadRequested`; `dropEvent` y
`_open_recent` se ejecutan ahora mediante `_load_image_async` (ruta del
worker). `load_image` se mantiene como ruta síncrona para
pruebas/fallback de drop.

**R4** — Accesores públicos: `ImageCanvas.image/has_image/version/
fit_to_view()` y `CropOverlayItem.top_left/size`. `MainWindow` e
`ImageCanvas` ya no acceden a los privados entre clases.

**R5** — `undo_to()` se comporta como múltiples `undo()` (cada paso a la
pila de Rehacer) y es así restaurable mediante `redo()`; además, guarda
de recorte como en `undo()`.

**R6** — `_build_right_panel()` es un dispatcher ligero; cuatro
constructores `_build_tab_selection/background/transform/shape` añaden
cada uno una pestaña (índice de pestaña de `addTab()`).

**R7** — `mypy` configurado en `pyproject.toml` (de forma pragmática:
ruido de override de Qt y lambda de tupla silenciado vía
`disable_error_code`) y añadido como paso del CI.

**R8/R9/R10/R11** — Se eliminó el ignore de `F401`, se borraron dos
importaciones no usadas; `make_tool_icon` usa la importación de `Image`
del módulo y registra los fallos con `logger.debug`; suma de bytes de
Deshacer en curso `_undo_bytes` (O(1)); `Image.MAX_IMAGE_PIXELS`
acoplado a `_MAX_MEGAPIXELS`.

**R12** — Nuevas pruebas (81 → 108): evicción del límite de memoria de
Deshacer + seguimiento de bytes, `tests/test_geometry.py`
(rotar/reflejar/esquinas/recorte), lazo + `_paint_brush` +
`apply_remove/replace` caso de éxito, `tests/test_drop_and_history.py`
(drop asíncrono, `undo_to`-redo), creación de directorio de
`_setup_logging`.

**R13** — README/INSTALL_MAC: Python **3.10+**; README ampliado con
arquitectura, limitaciones conocidas, ruta de registro correcta y
**sección de licencia**; se añadió `LICENSE` (GPL-3.0); `pyproject.toml`
con `license`/`authors`/`urls`/`classifiers`. Recomendación de licencia:
**GPL-3.0-or-later** (concuerda con la obligación GPL de PyQt6;
permisiva solo con cambio a PySide6).

---

## Ronda 3 – Antes de la ampliación de funciones

> Dos rondas de optimización están completas; la ronda 3 reúne las
> limpiezas de bajo riesgo que conviene hacer antes de una ampliación
> de funciones prevista. La recomendación **#1 (monolito → paquete)**
> se aplaza deliberadamente: prioridad alta, pero también esfuerzo/
> riesgo altos y en conflicto con la decisión de diseño de archivo
> único documentada — una decisión aparte. La columna de estado
> referencia el PR que la implementa.

| # | Recomendación | Prioridad | Esfuerzo | Estado |
|---|-----------|-----------|---------|--------|
| 1 | Monolito → paquete (`bgremover/` con módulos) | 🟠 Alta | Alto | ✅ resuelto (ronda 5) |
| 2 | ~~`save_image()` sin manejo de errores~~ | 🟡 Media | Bajo | ✅ #48 |
| 3 | ~~Duplicación de estado en `undo/redo/undo_to/restore_original/_apply_pil`~~ | 🟡 Media | Bajo | ✅ #52 |
| 4 | ~~Hojas de estilo en línea dispersas, sin módulo de tema~~ | 🟡 Media | Medio | ✅ #53 |
| 5 | ~~Sin hook SessionStart para Claude Code on the web~~ | 🟡 Media | Bajo | ✅ #51 |
| 6 | ~~Guardas repetidas de "ninguna imagen cargada" (~8×)~~ | 🟢 Baja | Bajo | ✅ 2.1.0 |
| 7 | ~~Repetición de worker (try/except/log/emit) → clase base~~ | 🟢 Baja | Bajo | ✅ 2.1.0 |
| 8 | ~~Mantener `CHANGELOG [Unreleased]`~~ | 🟢 Baja | Bajo | ✅ continuo |
| 9 | ~~`mypy` muy permisivo (7 códigos desactivados)~~ | 🟢 Baja | Medio | ✅ ronda 4 #4 |

**#1** — `BgRemover.py` sigue siendo un archivo único (~3000 líneas:
ayudantes, worker, lienzo, IU, diálogos, registro, main). La mayor
palanca para el crecimiento de funciones, pero el mayor riesgo (riesgo:
alto) y en conflicto con la decisión de archivo único documentada.
**Abierto — aplazado deliberadamente**, requiere una decisión de diseño
aparte.

→ **Resuelto en la ronda 5** (decisión de diseño: corte limpio a paquete – ver abajo).

**#2** — Resuelto en **PR #48**: `save_image()` devuelve `bool` y
envuelve las operaciones de escritura en `try/except` (registro +
mensaje de estado), coherente con `apply_remove/replace`; «Guardar
como…» ya no recuerda una ruta fallida como destino de guardado rápido
(`BgRemover.py:1080–1113`).

**#3** — Resuelto en **PR #52** (originalmente #49, recreado de forma
limpia tras un conflicto de fusión): el bloque de estado de imagen
idéntico se unificó en los ayudantes `_set_image_state()` /
`_emit_history()`; comportamiento sin cambios (`BgRemover.py:877`,
`:891`).

**#4** — Resuelto en **PR #53** (originalmente #50): una paleta de
colores `_Theme` central a la que referencian las plantillas
reutilizadas (verificado byte a byte, 218 hojas de estilo, sin
diferencia visual). Constantes muertas `BTN_STYLE`/`GRP_STYLE`
eliminadas (`BgRemover.py:1547`).

**#5** — Resuelto en **PR #51**: un hook `SessionStart` síncrono
(`.claude/hooks/session-start.sh`, modo git 100755) instala las
bibliotecas de sistema de Qt + el proyecto y establece
`QT_QPA_PLATFORM=offscreen` de forma persistente; registrado en
`.claude/settings.json`.

**#6** — **✅ Hecho (2.1.0).** El retorno temprano de "ninguna imagen
cargada" de los cinco métodos `ImageCanvas` afectados está consolidado
en el decorador `@_requires_image` (`bgremover/canvas.py`).

**#7** — **✅ Hecho (2.1.0).** `AIWorker` e `ImageLoadWorker` comparten
la clase base `_Worker`, que encapsula el flujo
`try/except → logger.exception → error.emit` (`bgremover/workers.py`);
`RembgWarmupWorker` permanece deliberadamente independiente.

**#8** — Cumplido: los PR de la ronda 3 #48/#52/#53 mantienen cada uno
la sección `CHANGELOG [Unreleased]`; esta entrada documenta además la
propia ronda 3. Una práctica continua en lugar de un PR único.

**#9** — **✅ Hecho (ronda 4 #4).** `disable_error_code` se eliminó por
completo de `pyproject.toml` – las antes 8 clases de error
desactivadas están todas activas (detalles: ver ronda 4 #4 abajo).

---

## Ronda 4 – Diagnóstico y siguiente paso

> Estado del análisis: `ruff` limpio, `mypy` limpio, **140 pruebas en
> verde** (16 pruebas de UI deseleccionadas a propósito). La calidad
> del código es alta – la ronda 4 prioriza por tanto **qué abordar a
> continuación de forma concreta**, en lugar de buscar nuevos defectos.

| # | Recomendación | Prioridad | Esfuerzo | Estado |
|---|---------------|-----------|----------|--------|
| 1 | ~~Corte de versión 2.1.0 + etiqueta git~~ | 🟠 Alta | Bajo | ✅ Hecho (etiqueta tras merge) |
| 2 | ~~Ayudante de guarda "ninguna imagen" (ronda 3 #6)~~ | 🟢 Baja | Bajo | ✅ Hecho |
| 3 | ~~Clase base de worker (ronda 3 #7)~~ | 🟢 Baja | Bajo | ✅ Hecho |
| 4 | ~~Endurecer `mypy` paso a paso (ronda 3 #9)~~ | 🟢 Baja | Medio | ✅ Hecho (los 8 códigos activos) |
| 5 | Monolito → paquete (ronda 3 #1) | 🟠 Alta | Alto | ✅ resuelto (ronda 5) |

### ✅ 1. Corte de versión 2.1.0 + etiqueta git *(hecho)*

**Hecho en este PR:** `pyproject.toml` y el fallback de `__version__`
(`BgRemover.py`) subidos a `2.1.0`; el bloque `[Unreleased]` en
`CHANGELOG.md` (+ i18n en/es/fr/uk/zh) fechado como
`[2.1.0] – 2026-05-19` y añadido un nuevo bloque `[Unreleased]` vacío.
La `git tag v2.1.0` **deliberadamente no** se crea en la rama de
funcionalidad; corresponde al commit de merge en `main` tras el merge
(ver la descripción del PR).

**Hallazgo (para el registro):** **no existía ni una sola etiqueta
git** (`git tag -l` vacío), aunque el CHANGELOG afirma una "primera
versión etiquetada públicamente 2.0.0". Desde 2.0.0 el bloque
`[Unreleased]` había acumulado cambios sustanciales (PR #48 manejo de
errores al guardar, #52 deduplicación de estado, #53 `_Theme`,
documentación INSTALL_LINUX, #55 ejecutor de pruebas local), mientras
`pyproject.toml` y el fallback de `__version__` seguían en `2.0.0`.

### ✅ 2. Ayudante de guarda "ninguna imagen cargada" *(hecho, ronda 3 #6)*

El retorno temprano byte-idéntico `if self._pil is None:
self.statusMsg.emit("Kein Bild geladen"); return` de los cinco métodos
de `ImageCanvas` `apply_round_corners`, `apply_rotate`, `apply_flip`,
`start_crop_circle`, `start_crop_ratio` está consolidado en el
decorador `@_requires_image`. Comportamiento sin cambios (140 unitarias
+ 16 de UI en verde). Las tres guardas `has_image` de `MainWindow`
permanecen deliberadamente en línea: mensajes distintos y
comprobaciones secundarias dependientes del orden – consolidarlas allí
añadiría más riesgo que valor.

### ✅ 3. Clase base de worker *(hecho, ronda 3 #7)*

`AIWorker` e `ImageLoadWorker` ahora heredan de la clase base
`_Worker`, que encapsula el flujo idéntico
`try/except → logger.exception → error.emit`; las subclases solo
implementan `_work()`. `RembgWarmupWorker` permanece deliberadamente
independiente (sin señal `error`, `finished` siempre en `finally` –
contrato distinto).

### ✅ 4. Endurecer `mypy` paso a paso *(ronda 3 #9 / ronda 4 #4 – hecho)*

**Todas las clases de error previamente deshabilitadas están ahora
activas.** Tras el corte monolito → paquete (ronda 5), los seis
códigos restantes pudieron activarse archivo por archivo:

| Código | Antes | Estrategia |
|--------|-------|------------|
| `arg-type` | 2 | invariante `_pil`/`_arr` por doble guarda + `assert` en bucle |
| `attr-defined` | 2 | `setattr(thread, "_worker", ...)`; parámetro `_Worker \| RembgWarmupWorker` |
| `assignment` | 4 | anotaciones explícitas iniciales (`Image.Image`, `RankFilter`, `QMenu \| None`) |
| `func-returns-value` | 4 | tuplas lambda de UI → `def` locales |
| `override` | 7 | firmas alineadas con los stubs de PyQt6 (`QPainter \| None` etc.) |
| `union-attr` | 67 | barra de estado/menú y viewport en caché; asserts puntuales |

En `pyproject.toml` solo queda `check_untyped_defs = false` como
amortiguador pragmático del ruido Qt (cubre las firmas Qt override
event/option/widget).

### 🟠 5. Monolito → paquete *(ronda 3 #1, aplazado a propósito)*

`BgRemover.py` sigue siendo un único archivo con **3003 líneas**. La
mayor palanca para el crecimiento de funcionalidades, pero el mayor
riesgo y en conflicto con la decisión de diseño de archivo único
documentada. Sigue siendo una decisión arquitectónica deliberada y
separada – a reconsiderar a más tardar antes de la próxima expansión
mayor de funcionalidades. Los quick wins #2/#3 ya reducen ligeramente
el archivo y preparan una división posterior.

→ **Resuelto en la ronda 5** (decisión de diseño: corte limpio a paquete – ver abajo).

---

## Ronda 5 – Decisión de diseño: monolito → paquete (resuelta)

> La "decisión de diseño aparte" exigida explícitamente en la ronda 3 #1
> y la ronda 4 #5 se toma aquí y queda así resuelta. La decisión de
> diseño de archivo único documentada se **revierte deliberadamente**.

**Decisión.** `BgRemover.py` (3026 líneas) se divide en un paquete Python
`bgremover/`. Módulos: `constants`, `image_utils`, `icons`, `theme`,
`workers`, `crop`, `canvas`, `widgets`, `settings_dialog`,
`logging_config`, `main_window`, `app`, `__main__`, `__init__`.

**Corte limpio a paquete (sin shim de compatibilidad).** `BgRemover.py`
se elimina por completo. La app se lanza mediante el script de consola
`bgremover` **y** `python -m bgremover`. El modo anterior
`python -m bgremover` se **descarta deliberadamente**; los scripts de
construcción (`create_BgRemover_app.sh`, `BgRemover.command`),
`pyproject.toml`, Makefile/CI, pruebas y documentación (incl. i18n) se
migran en el mismo corte.

**Justificación.** Según la ronda 3 #1 / ronda 4 #5, el archivo único
era la mayor palanca para el crecimiento de funciones; el único
bloqueador era la decisión de archivo único documentada – que aquí se
revierte explícitamente. El riesgo sigue siendo alto pero está
controlado por el método.

**Método.** Por fases con una compuerta dura: **Fase A** (preparación –
este ADR + disposición/diseño, sin mover código) → **Compuerta** (línea
base verde capturada: `ruff`/`mypy` limpios, **140 pruebas unitarias +
16 de IU en verde**) → **Fase B** (división puramente mecánica e
idéntica a nivel de bytes; código movido literalmente, solo se ajustan
los imports; las pruebas siguen en verde). El único cambio de código
intencionado: la resolución de recursos en `make_tool_icon`
(`importlib.resources` en lugar de `__file__`/`argv`/`cwd`), sin
cambio de comportamiento.

**Orden / trabajo previo.** Condición previa cumplida: `git tag v2.1.0`
está puesto (en el merge del PR #60) y publicado como prerelease de
GitHub – el último estado puro de archivo único queda así marcado
(ronda 4 #1). Que el tag esté unos commits por detrás de `main` HEAD es
una decisión de release opcional del mantenedor e irrelevante para el
corte.

**Deliberadamente después, no antes.** El endurecimiento gradual de
mypy (ronda 4 #4, 6 `disable_error_code` restantes) se hace **después**
de la división – un movimiento grande invalida el progreso de tipos por
archivo. Las limpiezas internas (consolidación de guard/worker) también
quedan fuera de este corte.

**Impacto en el estado.** La ronda 3 #1 y la ronda 4 #5 quedan
**resueltas** con esta decisión; las columnas de estado de las tablas
respectivas se actualizan en consecuencia.

**Fase B completada.** El corte mecánico aterrizó (13 pasos, cada uno
con el oráculo verde como compuerta: `make test` 140, `make ui` 16,
`make type`, `make lint`; ambos puntos de entrada `python -m bgremover`
y `bgremover` arrancan estables). `BgRemover.py` está eliminado. El
paquete consta de 14 módulos en `bgremover/`; los iconos viajan como
`package-data` (`bgremover/icons/`). El único cambio de código
intencional siguió siendo el prometido: resolución de recursos vía
`importlib.resources` en `make_tool_icon` (contrato sin cambios).
Script de build, Makefile/CI y documentación (incluida i18n) se han
adaptado.

**Próximo paso recomendado.** Con el layout basado en archivos, la
ronda 4 #4 (endurecimiento incremental de mypy) tiene sentido ahora:
quitar un `disable_error_code` por módulo, corregir, repetir. Las
limpiezas internas marcadas opcionales en rondas 3/4 (unificación de
guards/workers) también son menos arriesgadas por archivo.
