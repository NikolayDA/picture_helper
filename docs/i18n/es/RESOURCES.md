[Deutsch](../../../RESOURCES.md) · [English](../en/RESOURCES.md) · **Español** · [Français](../fr/RESOURCES.md) · [Українська](../uk/RESOURCES.md) · [简体中文](../zh/RESOURCES.md)

# Recursos utilizados

Este documento enumera **todos los recursos externos** que BgRemover
utiliza o necesita: bibliotecas (paquetes de Python), otro software y
herramientas, código de terceros así como recursos propios del
proyecto — cada uno con su propósito, licencia y fuente de obtención.

> Indicaciones de versión: «Mín.» proviene de `pyproject.toml`
> (requisito mínimo vinculante), «comprobado» es la versión instalada en
> el entorno actual de desarrollo/CI. Lo determinante es siempre el
> texto de licencia incluido con cada paquete.

---

## 1. Dependencias de tiempo de ejecución (paquetes de Python)

Declaradas en `pyproject.toml` bajo `[project] dependencies`.

| Paquete | Propósito en el programa | Mín. | Comprobado | Licencia |
|-------|-------------------|------|---------|--------|
| **PyQt6** | GUI completa (ventana, lienzo, widgets, eventos, QSettings, QThread) | `>=6.5` | 6.11.0 | **GPL v3** o licencia comercial de Riverbank |
| **Pillow** (PIL) | E/S de imagen, EXIF-Transpose, rotar/reflejar, máscaras/alfa, guardar (PNG/JPEG/WebP/TIFF) | `>=10` | 12.2.0 | HPND (también «MIT-CMU»; licencia PIL de código abierto) |
| **NumPy** | Arrays de píxeles, flood-fill, operaciones de máscara | `>=1.24` | 2.4.5 | BSD-3-Clause |

Mediante PyQt6 se vincula además el framework **Qt 6** (The Qt Company).
Qt en sí está bajo LGPL v3 / GPL / licencia comercial; el **binding
PyQt6** es GPL v3 — ver la sección 8.

## 2. Dependencia opcional de IA

Declarada bajo `[project.optional-dependencies] ai` — solo necesaria
para la eliminación automática de fondo (herramienta `rembg`):

| Recurso | Propósito | Mín. | Licencia | Obtención |
|-----------|-------|------|--------|-------|
| **rembg[cpu]** | Eliminación de fondo asistida por IA (`rembg.remove`) | `>=2.0` | MIT | PyPI |
| **onnxruntime** | Backend de inferencia ONNX (dependencia transitiva de `rembg[cpu]`) | (transitiva) | MIT (Microsoft) | PyPI |
| **Modelo U²-Net** (`u2net.onnx`) | Modelo de segmentación estándar que rembg **descarga en tiempo de ejecución** (no incluido en el repositorio) | – | Apache-2.0 (proyecto *U-2-Net*) | Descarga por rembg al directorio de caché del usuario |

Sin los extras `ai`, el programa se inicia con normalidad; el botón de
IA está entonces desactivado (`REMBG_AVAILABLE = False`).

## 3. Biblioteca estándar de Python

Parte de CPython, **no se necesita ninguna instalación adicional**
(licencia: PSF License Agreement):

`sys`, `os`, `io`, `logging`, `collections.deque`, `pathlib.Path`.

## 4. Herramientas de desarrollo y pruebas

Declaradas bajo `[project.optional-dependencies] test`:

| Herramienta | Propósito | Mín. | Comprobado | Licencia |
|----------|-------|------|---------|--------|
| **pytest** | Ejecutor de pruebas | `>=8` | 9.0.3 | MIT |
| **pytest-qt** | Fixtures de Qt (`offscreen` sin interfaz gráfica) | `>=4.4` | 4.5.0 | MIT |
| **ruff** | Linting / comprobación de estilo | `>=0.6` | 0.15.13 | MIT |
| **mypy** | Verificación estática de tipos (paso del CI) | `>=1.10` | 2.1.0 | MIT |

## 5. Herramientas de compilación y distribución (macOS)

Necesarias para el script del paquete de aplicación
`create_BgRemover_app.sh`. **No** empaqueta ninguno de estos programas,
sino que los invoca a través del sistema:

| Herramienta | Propósito | Origen |
|----------|-------|----------|
| `python3` + `venv` + `pip` | Crear un venv aislado, instalar dependencias | Python / PyPA |
| `setuptools` (backend de compilación) | Empaquetado según `[build-system]` (`>=61`) | MIT |
| `/usr/bin/arch`, `uname` | Forzar la arquitectura de CPU nativa (Apple Silicon) | macOS |
| `iconutil` | Generar el icono de app `.icns` a partir del iconset (fallback: PNG) | macOS |
| `osascript` | Mostrar los mensajes de error del launcher de la app | macOS |
| Herramientas de shell estándar | `mkdir`, `cp`, `cat`, `command` entre otras | POSIX/macOS |

`BgRemover.command` es el lanzador de doble clic incluido (código propio
del proyecto).

## 6. Integración continua

Definida en `.github/workflows/ci.yml` (se ejecuta en los runners de
GitHub Actions Ubuntu + macOS, Python 3.10/3.12):

| Recurso | Propósito | Licencia |
|-----------|-------|--------|
| `actions/checkout@v4` | Hacer checkout del repositorio | MIT |
| `actions/setup-python@v5` | Configurar Python + caché de pip | MIT |
| Bibliotecas de sistema de Qt vía `apt` (Linux) | Tiempo de ejecución de Qt sin interfaz gráfica: `libegl1`, `libfontconfig1`, `libxkbcommon0`, `libdbus-1-3`, `libxcb-*` | empaquetadas por la distribución, diversas licencias permisivas/copyleft (Mesa, fontconfig, libxkbcommon, libxcb, dbus …) |

## 7. Recursos propios del proyecto

Obra propia del proyecto, cubierta por la licencia del proyecto
(GPL-3.0-or-later, ver `LICENSE`):

- **Código fuente**: `BgRemover.py` así como la suite de pruebas bajo `tests/`.
- **Iconos de barra de herramientas/pestañas**: `icons/*.png` (`ai`, `bg`, `brush`,
  `clear_sel`, `close`, `eraser`, `form`, `open`, `redo`, `restore`,
  `save`, `transparency`, `undo`, `wand`). Los carga `make_tool_icon()`.
- **Iconos vectoriales dibujados**: Si falla un PNG, `make_tool_icon()`
  dibuja el icono programáticamente con `QPainter`
  (funciones `_draw_*_icon`) — sin recurso externo.
- **Icono de la app**: `BgRemover_icon.png` (fuente para el `.icns` de macOS).
- **Cursores**: dibujados en tiempo de ejecución (`make_wand_cursor`,
  `make_brush_cursor`, `make_eraser_cursor`) — sin archivos externos.

**No hay ningún código fuente de terceros** incrustado en el repositorio
(ningún `vendor/` ni `third_party/`); la funcionalidad externa se
obtiene exclusivamente a través de los paquetes listados arriba.

## 8. Compatibilidad de licencias (nota)

BgRemover está bajo **GPL-3.0-or-later** (`LICENSE`). Esta elección está
condicionada por **PyQt6**: el binding está licenciado bajo GPL-v3 (o de
forma comercial), por lo que la aplicación distribuida como un todo — en
particular el `BgRemover.app` empaquetado — debe cumplir con la GPL. Las
demás dependencias de tiempo de ejecución/IA (Pillow HPND, NumPy BSD,
rembg MIT, onnxruntime MIT, U²-Net Apache-2.0) son compatibles con
GPL-v3.

Un modelo de licencia **permisivo** (MIT/Apache-2.0) solo sería posible
si PyQt6 fuera reemplazado por el **PySide6** licenciado bajo LGPL-v3.

---

*Nota de mantenimiento:* Ante cambios en `pyproject.toml`,
`.github/workflows/ci.yml` o `create_BgRemover_app.sh`, actualiza
también este documento.
