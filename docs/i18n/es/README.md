[Deutsch](../../../README.md) · [English](../en/README.md) · **Español** · [Français](../fr/README.md) · [Українська](../uk/README.md) · [简体中文](../zh/README.md)

# BgRemover

Una herramienta de edición de imágenes para macOS y Linux para **eliminar, reemplazar y editar fondos**: con recorte automático basado en IA, selección con varita mágica, pincel/borrador, lazo poligonal, recorte en distintos formatos, rotación, reflejo y redondeo de esquinas.

## Funciones

- **🤖 Eliminación de fondo con IA** mediante [rembg](https://github.com/danielgatis/rembg): un clic y listo.
- **🪄 Varita mágica**: selecciona áreas de color contiguas mediante relleno por difusión (flood-fill) (con control deslizante de tolerancia).
- **🖌 Pincel / Borrador**: dibuja o elimina la selección manualmente.
- **➰ Lazo poligonal**: delimita la selección con precisión mediante puntos de esquina.
- **🎨 Reemplazar fondo**: rellena la selección con cualquier color o establécela como transparente.
- **✂ Recorte** con rejilla de la regla de los tercios: círculo, 1:1, 16:9, 4:3, 3:2, 2:1, 14:9, 9:16, 3:4.
- **⟲ Rotar** en pasos de 90° o en cualquier ángulo; **↔ Reflejar** horizontal/vertical.
- **⬤ Redondear esquinas** con radio ajustable.
- **↩ Historial** con Deshacer y salto a cualquier paso anterior.
- **📥 Arrastrar y soltar** imágenes directamente a la ventana.
- Guardar como **PNG** (con transparencia), **JPEG** (sobre fondo blanco), **WebP** o **TIFF**.
- **⚙ Ajustes persistentes**: los directorios predeterminados y el formato de archivo preferido se mantienen guardados; desde los ajustes se puede localizar el archivo de registro y abrir su carpeta.

## Capturas de pantalla

![BgRemover – Ventana principal](../../screenshot.png)

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

**Recomendado (macOS): compilar el paquete de aplicación.** El script crea
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
**v2.3.0** — hasta entonces usa la vía venv de abajo.

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

1. **Abre una imagen** mediante `Archivo → Abrir` (⌘O) o arrastrando y soltando en la ventana.
2. **Realiza una selección** con la varita mágica, el pincel, el borrador o el lazo poligonal (pestaña *🎯 Selección*).
   - `Shift+clic` añade a la selección; `⌘+clic` (macOS) o `Ctrl+clic` (Linux) resta.
   - Cambia de herramienta con el teclado: `W` varita, `B` pincel, `E` borrador, `L` lazo.
3. **Edita el fondo** (pestaña *🖼 Fondo*): hazlo transparente o reemplaza el color — o directamente con **IA** en la barra de herramientas.
4. **Transforma la imagen** (pestaña *⟲ Trans.*): rota, refleja.
5. **Forma y recorte** (pestaña *⬤ Forma*): redondea esquinas o recorta a un formato — mueve/escala el marco, luego ✓ Aplicar.
6. **Guarda** mediante `Archivo → Guardar` (⌘S) como PNG, JPEG, WebP o TIFF.

### Ajustes

Mediante `Herramientas → Ajustes…` (⌘,) se pueden gestionar los siguientes ajustes:

| Ajuste | Descripción |
|---|---|
| Directorio predeterminado para abrir | Directorio inicial del diálogo de apertura; vacío = último directorio utilizado |
| Directorio predeterminado para exportar/guardar | Directorio inicial del diálogo de guardado; vacío = último directorio utilizado |
| Formato de archivo de imagen preferido | PNG, JPEG, WebP o TIFF – aparece como primera opción en el diálogo de guardado |
| Idioma | Alemán o inglés; el cambio se aplica después de reiniciar |
| Archivo de registro | Muestra la ruta del archivo de registro; el botón «Abrir carpeta» abre el directorio en el gestor de archivos |

Los directorios, el formato preferido y el idioma se guardan de forma
persistente mediante **QSettings** y se restauran automáticamente en el
siguiente inicio del programa.

### Atajos de teclado

En macOS la tecla modificadora es **⌘ (Cmd)**; en Linux, **Ctrl**.

| Acción | Atajo |
|--------|----------|
| Seleccionar varita mágica | W |
| Seleccionar pincel | B |
| Seleccionar borrador | E |
| Seleccionar lazo poligonal | L |
| Abrir imagen | ⌘O |
| Guardar imagen | ⌘S |
| Guardar imagen como… | ⇧⌘S |
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
  recorte y conecta el lienzo, menús, panel derecho y workers.
- **`right_panel`** construye las cuatro pestañas derechas de selección,
  fondo, giro/espejo y forma/recorte a partir de un conjunto de callbacks.
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
- La pila de Deshacer no está limitada por `maxlen`, sino por un
  **límite de memoria** (`_UNDO_MEMORY_LIMIT`); una suma de bytes en
  curso evacúa las entradas más antiguas.

## Limitaciones conocidas

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
