[Deutsch](../../../CHANGELOG.md) · [English](../en/CHANGELOG.md) · **Español** · [Français](../fr/CHANGELOG.md) · [Українська](../uk/CHANGELOG.md) · [简体中文](../zh/CHANGELOG.md)

# Changelog

Todos los cambios destacables en BgRemover se documentan en este
archivo. El formato se basa en
[Keep a Changelog](https://keepachangelog.com/de/1.1.0/); el proyecto
sigue [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

## [2.1.0] – 2026-05-19

### Cambiado

- Guarda de retorno temprano "ninguna imagen cargada" de los cinco
  métodos de `ImageCanvas` (`apply_round_corners`, `apply_rotate`,
  `apply_flip`, `start_crop_circle`, `start_crop_ratio`) consolidada en
  el decorador `@_requires_image` – el bloque antes byte-idéntico
  desaparece; comportamiento sin cambios (defendido por la suite de
  pruebas existente).
- Los workers de segundo plano `AIWorker` e `ImageLoadWorker` ahora
  comparten la clase base común `_Worker`, que encapsula el flujo
  idéntico `try/except → logger.exception → error.emit`; las subclases
  solo implementan `_work()`. `RembgWarmupWorker` permanece
  deliberadamente independiente (sin señal `error`, `finished` siempre
  en `finally`).
- Corte de versión **2.1.0**: `pyproject.toml` y el fallback de
  `__version__` en `BgRemover.py` subidos a `2.1.0`; los cambios antes
  recopilados bajo `[Unreleased]` (#48/#52/#53, INSTALL_LINUX, rondas
  3/4) quedan fechados como 2.1.0.

### Documentación

- Se añadió la guía de instalación para Linux (`INSTALL_LINUX.md`):
  paquetes de sistema por distribución (apt/dnf/pacman), configuración
  del venv, script de arranque o entrada `.desktop` y resolución de
  problemas; enlazada en el README. Incluye una vía especialmente
  sencilla para Raspberry Pi OS (Desktop) sin venv/pip (PyQt6/Pillow/numpy
  como paquetes de sistema vía `apt`), con un paso opcional para añadir
  la IA.

## [2.0.0] – 2026-05-17

Primera publicación etiquetada públicamente.

### Funciones

- Eliminación de fondo con IA mediante `rembg` (extra `ai` opcional)
  incl. precalentamiento en segundo plano para que el primer clic no se
  bloquee.
- Herramientas de selección: varita mágica (flood-fill vectorizado con
  control deslizante de tolerancia), pincel, borrador y lazo poligonal;
  Shift/Ctrl para selección aditiva o sustractiva.
- Establecer el fondo como transparente o reemplazarlo con un color.
- Transformaciones: rotar (pasos de 90° y ángulo libre), reflejar,
  redondear esquinas, recorte en varios formatos con rejilla de la regla
  de los tercios.
- Historial con Deshacer/Rehacer (botones de la barra de herramientas) y
  salto a cualquier paso anterior mediante un popup de historial
  flotante.
- Arrastrar y soltar así como «Abiertos recientemente» (10 entradas),
  ambos mediante el worker de carga asíncrono — sin congelación de la
  interfaz.
- Guardar como PNG, JPEG, WebP o TIFF.
- Ajustes persistentes (directorios predeterminados, formato de archivo
  preferido) vía `QSettings`.
- Compilación del paquete de aplicación de macOS
  (`create_BgRemover_app.sh`) incl. venv aislado, manejo de Apple
  Silicon y asignación de icono; compatible con Python 3.10–3.15.

### Estabilidad y calidad

- Hilos de worker protegidos (sin GC prematuro del worker, apagado
  limpio del hilo en `closeEvent`, condición de carrera de IA mediante
  contador de versión monótono del lienzo).
- Límite de tamaño de imagen (40 MP) y protección contra bomba de
  descompresión al cargar.
- Pila de Deshacer limitada por memoria (256 MB) con seguimiento de
  bytes O(1).
- Ruta de registro independiente de la plataforma (`bgremover.log` en el
  directorio de datos de la aplicación).
- 108 pruebas; `ruff` y `mypy` como pasos del CI; CI en Ubuntu y macOS
  con Python 3.10 y 3.12.
- `__version__` se lee de los metadatos del paquete (fuente única); la
  versión aparece en el título de la ventana.

### Documentación y licencia

- Licencia **GPL-3.0-or-later** (`LICENSE`); condicionada por el binding
  PyQt6 licenciado bajo GPL.
- `RESOURCES.md` (todas las bibliotecas/herramientas/recursos junto con
  sus licencias), `LICENSES.md` y flujo de trabajo automatizado de
  licencias/cumplimiento.
- README con arquitectura, limitaciones conocidas e instrucciones de
  instalación; `INSTALL_MAC.md` detallado.

[Unreleased]: https://github.com/NikolayDA/picture_helper/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/NikolayDA/picture_helper/releases/tag/v2.0.0
