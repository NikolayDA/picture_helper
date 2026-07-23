[Deutsch](../../../README.md) · [English](../en/README.md) · **Español** · [Français](../fr/README.md) · [Українська](../uk/README.md) · [简体中文](../zh/README.md)

# BgRemover

[![CI](https://github.com/NikolayDA/picture_helper/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/NikolayDA/picture_helper/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/NikolayDA/picture_helper/branch/main/graph/badge.svg)](https://codecov.io/gh/NikolayDA/picture_helper)
[![License Check](https://github.com/NikolayDA/picture_helper/actions/workflows/license-check.yml/badge.svg?branch=main)](https://github.com/NikolayDA/picture_helper/actions/workflows/license-check.yml)
[![Latest release](https://img.shields.io/github/v/release/NikolayDA/picture_helper)](https://github.com/NikolayDA/picture_helper/releases/latest)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![License: GPL v3](https://img.shields.io/github/license/NikolayDA/picture_helper)](https://github.com/NikolayDA/picture_helper/blob/main/LICENSE)
[![Platform: macOS | Linux](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey)](https://github.com/NikolayDA/picture_helper)
[![Code style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)

Una herramienta de edición de imágenes para macOS y Linux para **recortar, editar y preparar motivos para impresión**: desde la eliminación de fondo con IA pasando por capas, proyectos y mapas de altura hasta la **exportación de activos para impresión UV (EufyMake Studio)**. Con varita mágica, pincel/borrador, lazo poligonal, recorte en distintos formatos, rotación, reflejo, redondeo de esquinas y corrección de color.

## Funciones

- **🤖 Eliminación de fondo con IA** mediante [rembg](https://github.com/danielgatis/rembg): un clic y listo.
- **🪄 Varita mágica**: selecciona áreas de color contiguas mediante relleno por difusión (flood-fill) (con control deslizante de tolerancia).
- **🖌 Pincel / Borrador**: dibuja o elimina la selección manualmente.
- **➰ Lazo poligonal**: delimita la selección con precisión mediante puntos de esquina.
- **🎨 Reemplazar fondo**: rellena la selección con cualquier color o establécela como transparente.
- **✂ Recorte** con rejilla de la regla de los tercios: círculo, 1:1, 16:9, 4:3, 9:16, 3:4.
- **⟲ Rotar** en pasos de 90° o en cualquier ángulo; **↔ Reflejar** horizontal/vertical.
- **⬤ Redondear esquinas** con radio ajustable.
- **📐 Tamaño y dimensiones físicas** – escala a una resolución objetivo en píxeles **o** mediante milímetros y DPI (vincular relación de aspecto, método de remuestreo seleccionable); con comprobación del área de impresión frente a un medio objetivo (p. ej. A4/A3).
- **🎚 Corrección de color** – brillo, contraste y saturación de la capa activa con vista previa en vivo (preserva el alfa).
- **🪶 Suavizar borde** – borde de recorte suave (desvanecido del alfa), limitado por la selección, tras el recorte por IA o manual.
- **🗂 Capas y proyectos** – gestiona varias capas (color, altura, brillo, genérica) con roles y guarda y abre todo sin pérdidas como un proyecto `.bgrproj`.
- **🏔 Mapas de altura** – genera, edita y optimiza un mapa de altura en escala de grises a partir de una imagen (claro = alto): la base para el relieve y la impresión UV.
- **👁 Vista previa 2D** – comprueba color, relieve sobre color, altura y brillo en pantalla; solo visualización, la exportación de imagen sigue siendo el motivo de color.
- **🧊 Vista previa de relieve 3D** – inspecciona el mapa de altura activo como una superficie giratoria con órbita, desplazamiento, zoom, exageración, iluminación y calidad seleccionable; solo visualización, sin modificar los datos de altura ni la exportación. Si no hay OpenGL 2.1, la vista previa 2D sigue disponible.
- **↩ Historial** con Deshacer y salto a cualquier paso anterior.
- **📥 Arrastrar y soltar** imágenes directamente a la ventana.
- **📂 Formatos de entrada** – abre **PNG, JPEG, WebP, TIFF, BMP y GIF**. **HEIC/HEIF no es compatible actualmente.**
- Guardar como **PNG** (con transparencia), **JPEG** (sobre fondo blanco), **WebP** o **TIFF**.
- **⚙ Ajustes persistentes**: los directorios predeterminados y el formato de archivo preferido se mantienen guardados; desde los ajustes se puede localizar el archivo de registro y abrir su carpeta.
- **🖨 Exportación para EufyMake Studio**: escribe activos de importación (motivo de color como PNG RGBA, mapa de altura opcional con claro = alto, máscara de brillo opcional) con una comprobación previa y los siguientes pasos en Studio. BgRemover **no** crea un archivo `.empf` nativo: la importación, el posicionamiento y la asignación del modo de tinta se hacen en EufyMake Studio.

## Capturas de pantalla

![BgRemover – paso «Relieve y capas» con la tarjeta de capas](../../screenshot.png)

*El paso guiado «Relieve y capas»: la tarjeta de capas (derecha) muestra un
proyecto formado por una capa de motivo de color y una capa de altura, con
asignación de roles.*

![Espacio de trabajo de mapa de altura](../../screenshot_height.png)

*El mismo paso con las tarjetas «Obtener» y «Editar»: genera un mapa de altura
a partir de la imagen o impórtalo, luego ajústalo – la semántica de altura es
claro = alto.*

![Vista previa 2D: relieve y brillo sobre color](../../screenshot_preview.png)

*Paso «Exportar»: la vista previa 2D combinada superpone relieve y brillo sobre
el motivo de color – solo visualización, la exportación no cambia.*

![Vista previa de relieve 3D con controles de visualización](../../../app_screenshots/bgremover_complete_20260722_171622/77_function_preview3d_adjusted.png)

*Paso «Relieve y capas»: inspecciona el mapa de altura activo como una
superficie 3D giratoria. La exageración, la iluminación y la calidad solo
afectan a la visualización; un aviso indica la representación simplificada de
las imágenes grandes.*

![Diálogo de exportación para EufyMake Studio](../../screenshot_export.png)

*El diálogo de exportación produce activos de importación (motivo de color, mapa
de altura y máscara de brillo opcionales) con una comprobación previa – **no** un
archivo `.empf` nativo.*

## Requisitos

- **macOS** o un **entorno de escritorio Linux** (el paquete de aplicación
  opcional usa herramientas específicas de macOS como `iconutil`)
- **Python 3.10 o posterior** (el código usa anotaciones de tipo PEP-604
  como `QThread | None` directamente en las firmas — Python 3.9 falla)
- Las dependencias (`PyQt6`, `Pillow`, `numpy`, opcionalmente `rembg` para
  la función de IA) se instalan mediante `pyproject.toml`.

Para el snapshot reproducible de IA/app se recomienda **Python 3.11 o
posterior**: algunas dependencias transitivas actuales de IA ya no están
disponibles en Python 3.10. La aplicación base sin IA sigue admitiendo
Python 3.10.

## Instalación

**La vía más rápida: descargas listas para usar.** La
[página de Releases](https://github.com/NikolayDA/picture_helper/releases/latest)
ofrece artefactos listos para ejecutar con **IA ya incluida**, sin necesidad de
instalar Python localmente:

- **macOS** (Apple Silicon/arm64): descarga el `.dmg` y arrastra `BgRemover.app`
  a *Aplicaciones*. El paquete está de momento **sin firmar**: en el primer
  inicio, confírmalo con **clic derecho → «Abrir»** ([INSTALL_MAC.md](INSTALL_MAC.md)).
- **Linux / Raspberry Pi OS** (x86_64 y aarch64): un **AppImage** portable o un
  **`.deb`** instalable ([INSTALL_LINUX.md](INSTALL_LINUX.md)).

Para compilar desde el código fuente o para desarrollo, continúa más abajo.

**Desde el código fuente (macOS): compilar el paquete de aplicación.** El script crea
automáticamente un venv aislado para la app, intenta instalar las
dependencias de IA incluido `onnxruntime`, maneja correctamente Apple
Silicon y genera un lanzador `BgRemover.app`:

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
bash create_BgRemover_app.sh
```

Si se crea un nuevo venv para la app, confirma el aviso con **Enter**.
Después, inicia `BgRemover.app` (en `~/Applications`) con doble clic —
funcionalmente idéntico al **`BgRemover.command`** incluido. El lanzador
usa el venv instalado por separado en
`~/Library/Application Support/BgRemover/venv`, por lo que el proyecto
puede permanecer en `~/Documents`. Sin embargo, la app y su venv forman
una unidad: el archivo `.app` no es portátil por sí solo. Si falla la
instalación de las dependencias de IA, el script genera una app utilizable
sin IA.

Después de una actualización o un cambio de rama, vuelve a ejecutar
`bash create_BgRemover_app.sh`. El script instala el checkout actual de
forma no editable sobre el venv existente de la app y vuelve a generar el
lanzador.

**Alternativamente, directamente en el terminal** — en macOS moderno
dentro de un venv, ya que el Python del sistema bloquea `pip install`
según el PEP 668:

```bash
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install --upgrade "pip>=26.1.2"
python3 -m pip install -c requirements/constraints.txt -e ".[ai]"
python3 -m bgremover
```

`.[ai]` incluye las dependencias de IA (`rembg[cpu]` incl. `onnxruntime`);
sin la función de IA basta con `python3 -m pip install -c requirements/constraints.txt -e .`.

**Linux:** Para usuarios finales se recomiendan los artefactos de release:
un **AppImage** portable y un **`.deb`** instalable (ambos para x86_64 y
aarch64/Raspberry Pi OS). Consulta **[INSTALL_LINUX.md](INSTALL_LINUX.md)**
para la instalación y **[packaging/linux/README.md](../../../packaging/linux/README.md)**
para detalles de build/paquetización. Tales artefactos existen a partir de
**v2.4.0**; para **macOS** se añade un **`.dmg`** (Apple Silicon/arm64): consulta
**[INSTALL_MAC.md](INSTALL_MAC.md)**.

El inicio directo desde un venv sigue siendo la mejor vía para desarrollo,
pruebas de ramas y cambios locales:

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install --upgrade "pip>=26.1.2"
python3 -m pip install -c requirements/constraints.txt -e ".[ai]"
python3 -m bgremover
```

Antes del inicio desde venv se necesitan algunas bibliotecas de sistema de Qt —
consulta **[INSTALL_LINUX.md](INSTALL_LINUX.md)**. En **Raspberry Pi OS
(Desktop)** también es posible sin venv/pip (PyQt6, Pillow, numpy como paquetes
de sistema vía `apt`); consulta igualmente **[INSTALL_LINUX.md](INSTALL_LINUX.md)**.

> Las instrucciones detalladas — incluida la **instalación desde una
> rama** (para probar pull requests abiertos) y la **resolución de
> problemas** — están en **[INSTALL_MAC.md](INSTALL_MAC.md)** (macOS) o
> **[INSTALL_LINUX.md](INSTALL_LINUX.md)** (Linux).

## Uso

Un **flujo guiado de 6 pasos** (barra de pasos sobre el lienzo + tarjetas de
inspector a la derecha) conduce la edición:

1. **Abrir** – carga una imagen arrastrándola a la zona de destino, mediante `Archivo → Abrir` (⌘O), arrastrando y soltando en la ventana o con una ruta de inicio (CLI / Finder).
2. **Quitar fondo** – el botón **IA** en el inspector de tarjetas, o la varita mágica, el pincel, el borrador o el lazo poligonal; luego hazlo transparente, reemplaza el color o suaviza el borde.
   - `Shift+clic` añade a la selección; `⌘+clic` (macOS) o `Ctrl+clic` (Linux) resta.
   - Cambia de herramienta con el teclado: `W` varita, `B` pincel, `E` borrador, `L` lazo (solo activo en este paso).
3. **Ajustar** – brillo/contraste/saturación con vista previa en vivo.
4. **Forma y medidas** – rota, refleja, redondea esquinas, elige un formato de recorte (mueve/escala el marco, luego ✓ Aplicar) y cambia el tamaño.
5. **Relieve y capas** – gestiona las capas del proyecto y genera/edita/optimiza un mapa de altura. Con un mapa de altura válido, cambia entre **2D** y **3D** en **Visualización**; en 3D, arrastra con el botón izquierdo para orbitar, usa el botón central o `Alt`+arrastrar para desplazar y la rueda para acercar. Sin OpenGL 2.1, la vista previa de relieve 2D sigue disponible.
6. **Exportar** – comprueba el resultado como color/relieve/altura/brillo/combinado, guarda mediante `Archivo → Guardar` (⌘S) como PNG, JPEG, WebP o TIFF — o `Proyecto → Exportar activos para EufyMake Studio…` para la impresión UV.

### Ajustes

Mediante `Herramientas → Ajustes…` (⌘,) se pueden gestionar los siguientes ajustes:

| Ajuste | Descripción |
|---|---|
| Directorio predeterminado para abrir | Directorio inicial del diálogo de apertura; vacío = último directorio utilizado |
| Directorio predeterminado para exportar/guardar | Directorio inicial del diálogo de guardado; vacío = último directorio utilizado |
| Formato de archivo de imagen preferido | PNG, JPEG, WebP o TIFF – aparece como primera opción en el diálogo de guardado |
| Idioma | Alemán o inglés; el cambio se aplica después de reiniciar |
| Archivo de registro | Muestra la ruta del archivo de registro; el botón «Abrir carpeta» abre el directorio en el gestor de archivos |
| Buscar actualizaciones automáticamente al iniciar | Desactivado por defecto; si se activa, se ejecuta una comprobación silenciosa poco después de iniciar (ver más abajo) |

Los directorios, el formato preferido, el idioma y la comprobación
automática de actualizaciones se guardan de forma persistente mediante
**QSettings** y se restauran automáticamente en el siguiente inicio del
programa.

### Actualizaciones y gestión del modelo de IA

El menú `Herramientas` ofrece tres opciones más:

- **"Buscar actualizaciones…"** consulta la última versión de GitHub sin
  bloquear y muestra un diálogo según el resultado: versión actual, una
  nueva versión con un enlace a la página de la versión, o un mensaje de
  error comprensible. Si "Buscar actualizaciones automáticamente al
  iniciar" está activado, una nueva versión también muestra un aviso
  discreto y clicable en la barra de estado que abre el mismo diálogo –
  sin otra solicitud de red.
- **"Gestionar modelo de IA…"** muestra si `rembg` está disponible y si el
  modelo por defecto de rembg ya está en caché local, y permite una
  descarga/reintento explícitos con indicador de progreso y botón de
  cancelar – como alternativa a la descarga automática al iniciar la app
  (ver la guía de instalación, p. ej. `INSTALL_MAC.md`).
- **"Instalar eliminación de fondo por IA…"** muestra el comando adecuado
  para añadir el backend rembg, con botón para copiarlo al portapapeles. La
  app no instala nada automáticamente de forma deliberada; tras la
  instalación hay que reiniciarla para que el proceso en ejecución vea el
  paquete nuevo.

### Atajos de teclado

En macOS la tecla modificadora es **⌘ (Cmd)**; en Linux, **Ctrl**. Los
atajos de herramienta (W/B/E/L) solo funcionan mientras el paso *Quitar
fondo* está activo.

| Acción | Atajo |
|--------|----------|
| Seleccionar varita mágica | W |
| Seleccionar pincel | B |
| Seleccionar borrador | E |
| Seleccionar lazo poligonal | L |
| Abrir imagen | ⌘O |
| Guardar imagen | ⌘S |
| Guardar imagen como… | ⇧⌘S |
| Nuevo proyecto | ⌘N |
| Abrir proyecto… | ⇧⌘O |
| Guardar proyecto | ⌥⌘S |
| Cambiar tamaño… | ⌘R |
| Exportar activos para EufyMake Studio… | ⌥⌘E |
| Deshacer | ⌘Z |
| Rehacer | ⇧⌘Z |
| Rotar 90° a la izquierda | ⌘← |
| Rotar 90° a la derecha | ⌘→ |
| Anular selección (si no hay recorte/lazo activo) | Esc |
| Invertir selección | ⌘⇧I |
| Fit to View | ⌘0 |
| Abrir ajustes | ⌘, |

En el menú Archivo hay además un submenú **«Abiertos recientemente»** con
las 10 últimas imágenes cargadas — el estado se persiste junto con los
demás ajustes mediante QSettings.

## Desarrollo y pruebas

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m venv .venv
source .venv/bin/activate
make pr-check
```

La suite de pruebas se ejecuta sin interfaz gráfica (plataforma Qt
`offscreen`) y verifica las operaciones de imagen, la geometría del
recorte y la lógica de guardado. Los pull requests ejecutan una CI
ligera en GitHub (Ubuntu, Python 3.12, `make pr-check`). La matriz completa
en Linux/macOS con Python 3.10, 3.11, 3.12 y 3.13 se ejecuta como gate de
release: al enviar un tag de versión, el workflow de release la invoca antes
de publicar; además se ejecuta semanalmente (domingos) y manualmente. Todas
las instalaciones locales/CI de prueba usan
`requirements/constraints.txt`; si hace falta, se puede sobrescribir con
`make PIP_CONSTRAINT=/ruta/al/archivo pr-check`. Consulta
[TESTING.md](../../../TESTING.md) para el flujo completo de pruebas.

Comprobación del estilo de código y verificación estática de tipos:

```bash
make lint
make type
```

### Regenerar capturas de la interfaz

El conjunto completo de capturas para revisión y documentación se puede
reproducir en modo headless:

```bash
make screenshots
```

El generador escribe en `app_screenshots/bgremover_complete_<timestamp>/`,
usa Qt `offscreen`, sustituye QSettings por almacenamiento en memoria y
simula la vista de resultado de IA sin ejecutar realmente el modelo `rembg`.
Los subdirectorios transitorios `_runtime/` y `_exports/` permanecen locales
gracias a `.gitignore`; los PNG numerados y `manifest.md` son los artefactos
que se pueden commitear.

Para acceptance runs de la vista 3D real en hardware grafico local, el target
hibrido crea primero el mismo conjunto headless y despues superpone los estados
3D ready/display desde el visor nativo Qt/OpenGL:

```bash
make screenshots-live-3d
```

Ese run falla intencionadamente si no hay un renderer compatible con OpenGL 2.1;
el camino regular de CI/documentacion `make screenshots` no cambia.

### Regenerar el PDF de la guía

`ANLEITUNG.pdf` se genera desde `ANLEITUNG.md` (Markdown a HTML a PDF
con WeasyPrint). Tras cambiar la fuente Markdown, vuelve a generar el
PDF de forma reproducible. En Linux se necesitan las fuentes DejaVu y
los paquetes de distribución Pango/Cairo/GDK-Pixbuf. En macOS el
generador usa las fuentes del sistema Arial/Courier New; instala Pango
con `brew install pango`:

```bash
pip install -e ".[docs]"
python scripts/generate_anleitung_pdf.py
```

## Arquitectura (resumen breve)

BgRemover es un paquete instalable (`bgremover/`, iniciado vía
`python -m bgremover` o el script de consola `bgremover`):

- **`ImageCanvas`** (QGraphicsView) mantiene el estado de la imagen, la
  máscara de selección, las pilas de Deshacer/Rehacer y las herramientas
  (varita mágica, pincel, lazo, recorte).
- **`MainWindow`** construye la barra de herramientas, la barra de estado/
  recorte y conecta el lienzo, menús, panel derecho y workers;
  `_apply_toolbar_for_step` cambia la barra de herramientas contextual según
  el paso activo.
- **`stepper`** es la barra de 6 pasos sin estado (Abrir/Quitar fondo/
  Ajustar/Forma y medidas/Relieve y capas/Exportar); **`right_panel`**
  construye a partir de ella el inspector de tarjetas (cabecera,
  `QStackedWidget` con una página por paso, pie de navegación) y le asigna
  los ocho bloques de pestañas existentes de `right_panel_tabs` (Vista
  previa, Selección, Fondo, Ajustar, Rotar/Voltear, Forma, Capas, Altura);
  `project_model`/`height_map` aportan el modelo de capas y altura sin Qt.
- **`menu_actions`** construye la barra de menú, acciones y atajos;
  `MainWindow` solo aporta callbacks.
- **`RecentFiles`** encapsula persistencia, deduplicación y el adaptador
  de menú de "Abrir reciente", de modo que `MainWindow` solo delega la ruta
  de carga.
- Los **Worker** (`ImageLoadWorker`, `AIWorker`, `RembgWarmupWorker`,
  `FloodFillWorker`) se
  ejecutan en sus propios `QThread`s; `WorkerController` encapsula el
  arranque, las referencias fuertes a workers, `deleteLater` y el shutdown.
- Un **contador de versión** monótono en el lienzo descarta resultados
  obsoletos de IA y flood-fill si entretanto se cargó otra imagen o cambió
  el estado de la imagen.
- Deshacer y Rehacer comparten un **límite de memoria**
  (`_HISTORY_MEMORY_LIMIT`); las sumas de bytes en curso expulsan las entradas
  más antiguas del historial. La imagen original y el estado actual del lienzo
  quedan fuera de este presupuesto de forma intencionada.

## Limitaciones conocidas

- **Formatos de entrada:** se admiten **PNG, JPEG, WebP, TIFF, BMP y GIF**.
  **HEIC/HEIF no es compatible actualmente** (sin `pillow-heif`); esos archivos
  se rechazan de forma controlada como formato no admitido.
- **Tamaño máximo de imagen: 40 megapíxeles.** Las imágenes más grandes
  se rechazan con un mensaje de estado para limitar el uso de memoria y el
  tiempo de procesamiento. La selección con varita mágica (flood-fill) se
  ejecuta de forma asíncrona en su propio `QThread`, de modo que la
  interfaz sigue respondiendo durante el cálculo. Pillow está además
  protegido contra imágenes de tipo «bomba de descompresión».
- La **compilación del paquete de aplicación** es específica de macOS; en
  Linux la aplicación se ejecuta mediante el inicio directo
  `python -m bgremover`. Windows no forma parte actualmente de la matriz
  probada oficialmente.

## Archivo de registro

El logger interno de la aplicación usa un archivo `bgremover.log` en el
directorio de datos determinado por Qt. La ruta exacta depende de la
plataforma y la configuración de Qt; con la configuración actual de macOS
es `~/Library/Application Support/BgRemover/BgRemover/bgremover.log`, y
en Linux el archivo se encuentra bajo `~/.local/share/`. Contiene mensajes
de ejecución y trazas de pila de los errores registrados y se crea con la
primera entrada de log.

El lanzador del paquete de aplicación de macOS también escribe diagnósticos
de inicio en `~/Library/Application Support/BgRemover/bgremover.log`.

La ruta interna exacta aparece en `Herramientas → Ajustes… → Archivo de
registro`; el botón «Abrir carpeta» abre directamente el directorio en el
gestor de archivos.

## Licencia

BgRemover está bajo la **GNU General Public License v3.0 o posterior**
(`GPL-3.0-or-later`) — consulta [LICENSE](../../../LICENSE).

Una lista completa de todas las bibliotecas, herramientas y recursos
utilizados junto con sus licencias está en
**[RESOURCES.md](RESOURCES.md)**.

> **Nota sobre PyQt6:** La dependencia de la GUI PyQt6 (Riverbank) está
> ella misma licenciada bajo GPL-v3 (o de forma comercial). Se eligió
> deliberadamente la GPL-3.0 para que la aplicación distribuida — en
> particular el `BgRemover.app` empaquetado — cumpla con la licencia.
> Quien aspire a un modelo permisivo (MIT/Apache-2.0) tendría que
> reemplazar PyQt6 por el **PySide6** licenciado bajo LGPL.
