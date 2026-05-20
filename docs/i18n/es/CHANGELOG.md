[Deutsch](../../../CHANGELOG.md) · [English](../en/CHANGELOG.md) · **Español** · [Français](../fr/CHANGELOG.md) · [Українська](../uk/CHANGELOG.md) · [简体中文](../zh/CHANGELOG.md)

# Changelog

Todos los cambios destacables en BgRemover se documentan en este
archivo. El formato se basa en
[Keep a Changelog](https://keepachangelog.com/de/1.1.0/); el proyecto
sigue [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

### Corregido

- **Rutas de inicio en macOS funcionando de nuevo.** Tras el corte de
  paquete (ronda 5), `BgRemover.command` seguía buscando el archivo
  `BgRemover.py` ya inexistente y abortaba con «no encontrado»; el
  `INSTALL_MAC.md` alemán y las versiones i18n de `INSTALL_LINUX.md` y
  `README.md` también conservaban algunos comandos antiguos (el paso
  15 de la ronda 5 había omitido el `INSTALL_MAC.md` alemán y la
  documentación de instalación i18n en el glob, además de
  `Exec=python3 /RUTA/.../BgRemover.py` en los fragmentos `.desktop`
  i18n). Efecto neto: en macOS ninguna de las tres vías de inicio
  documentadas (paquete app, doble clic en `.command`, terminal) era
  utilizable de forma fiable. Ahora `BgRemover.command` arranca vía
  `python3 -m bgremover` y comprueba previamente `import bgremover`
  (de lo contrario muestra una indicación clara hacia
  `create_BgRemover_app.sh`). INSTALL_MAC + todos los documentos i18n
  reflejan el modelo de paquete actual (incluida la instalación no
  editable del paquete en el venv de la app y la búsqueda de recursos
  vía `importlib.resources`).
- **`create_BgRemover_app.sh`: el venv existente se migra
  correctamente.** Un venv de la era monolito (con PyQt6/Pillow/numpy
  instalados, pero, por supuesto, todavía sin `bgremover`) se trataba
  erróneamente como «listo» porque la comprobación de configuración
  `has_deps` no testeaba `bgremover`. Al reejecutar, la instalación
  del paquete se omitía — y el launcher de la app informaba luego en
  tiempo de ejecución «Falta el paquete bgremover en el venv». La
  comprobación incluye ahora también `import bgremover`; además hay
  un camino rápido: si el venv de la app ya tiene PyQt6/Pillow/numpy,
  solo se añade `pip install ".[ai]"` (segundos) en lugar de
  reconstruir el venv con todas las dependencias (minutos).

### Cambiado

- **Monolito → paquete (ronda 5).** El archivo único `BgRemover.py`
  (3026 líneas) se ha dividido en el paquete instalable `bgremover/`
  (14 módulos: `constants`, `image_utils`, `icons`, `theme`, `workers`,
  `crop`, `canvas`, `widgets`, `settings_dialog`, `logging_config`,
  `main_window`, `app`, `__main__`, `__init__`). Se lanza con
  `python -m bgremover` o con el script de consola `bgremover`; la
  forma antigua `python BgRemover.py` se elimina sin sustituto.
  `BgRemover.py` está borrado. Realizado en **13 pasos mecánicos**,
  cada uno con el oráculo verde como compuerta (140 unit + 16 UI
  tests, ruff, mypy). El único cambio de código intencional y neutral
  en comportamiento: `make_tool_icon` resuelve los iconos vía
  `importlib.resources` desde los datos del paquete
  (`bgremover/icons/`) en lugar de `__file__`/`sys.argv`/`cwd` —
  contrato sin cambios. `pyproject.toml`, `Makefile`, workflow de CI y
  el script de build de macOS (`create_BgRemover_app.sh`) se han
  adaptado en el mismo corte; la venv instala el paquete no editable
  (incl. package-data), lo que hace que la app sea independiente del
  directorio del proyecto.
- Los re-exports transitorios en `BgRemover.py` (fase B) y todas las
  importaciones `BgRemover` de los tests se han migrado al paquete en
  el paso final.

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
