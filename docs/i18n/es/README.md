[Deutsch](../../../README.md) · [English](../en/README.md) · **Español** · [Français](../fr/README.md) · [Українська](../uk/README.md) · [简体中文](../zh/README.md)

# BgRemover

Una herramienta de edición de imágenes para macOS para **eliminar, reemplazar y editar fondos**: con recorte automático basado en IA, selección con varita mágica, pincel/borrador, recorte en distintos formatos, rotación, reflejo y redondeo de esquinas.

## Funciones

- **🤖 Eliminación de fondo con IA** mediante [rembg](https://github.com/danielgatis/rembg): un clic y listo.
- **🪄 Varita mágica**: selecciona áreas de color contiguas mediante relleno por difusión (flood-fill) (con control deslizante de tolerancia).
- **🖌 Pincel / Borrador**: dibuja o elimina la selección manualmente.
- **🎨 Reemplazar fondo**: rellena la selección con cualquier color o establécela como transparente.
- **✂ Recorte** con rejilla de la regla de los tercios: círculo, 1:1, 16:9, 4:3, 3:2, 2:1, 14:9, 9:16, 3:4.
- **⟲ Rotar** en pasos de 90° o en cualquier ángulo; **↔ Reflejar** horizontal/vertical.
- **⬤ Redondear esquinas** con radio ajustable.
- **↩ Historial** con Deshacer y salto a cualquier paso anterior.
- **📥 Arrastrar y soltar** imágenes directamente a la ventana.
- Guardar como **PNG** (con transparencia), **JPEG** (sobre fondo blanco), **WebP** o **TIFF**.
- **⚙ Ajustes persistentes**: los directorios predeterminados y el formato de archivo preferido se mantienen guardados.

## Capturas de pantalla

<!--
  Antes del lanzamiento, coloca una captura de pantalla/GIF en docs/screenshot.png
  y descomenta la siguiente línea (el marcador de posición no renderiza
  intencionadamente ninguna imagen rota mientras falte el archivo):

![BgRemover – Ventana principal](../../screenshot.png)
-->

> _Captura de pantalla pendiente._ Antes de la publicación debería ir
> aquí una imagen de la ventana principal (barra de herramientas, lienzo
> con selección, panel de pestañas a la derecha) — ruta recomendada
> `docs/screenshot.png`.

## Requisitos

- **macOS** (el paquete de aplicación incluido usa herramientas específicas de macOS como `iconutil`)
- **Python 3.10 o posterior** (el código usa anotaciones de tipo PEP-604
  como `QThread | None` directamente en las firmas — Python 3.9 falla)
- Las dependencias (`PyQt6`, `Pillow`, `numpy`, opcionalmente `rembg` para
  la función de IA) se instalan mediante `pyproject.toml`.

## Instalación

**Recomendado (macOS): compilar el paquete de aplicación.** El script crea
automáticamente un venv aislado, instala todas las dependencias (incl.
`onnxruntime` para la IA), maneja correctamente Apple Silicon y genera
un `BgRemover.app` independiente:

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
bash create_BgRemover_app.sh
```

Confirma con **Enter** ante el aviso del venv. Después, inicia
`BgRemover.app` (en `~/Applications`) con doble clic — funcionalmente
idéntico al **`BgRemover.command`** incluido. El proyecto puede
permanecer en `~/Documents` (la app se compila de forma independiente).

**Alternativamente, directamente en el terminal** — en macOS moderno
dentro de un venv, ya que el Python del sistema bloquea `pip install`
según el PEP 668:

```bash
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install -e ".[ai]"
python3 -m bgremover
```

`.[ai]` incluye las dependencias de IA (`rembg[cpu]` incl. `onnxruntime`);
sin la función de IA basta con `python3 -m pip install -e .`.

**Linux:** No hay paquete de aplicación; la aplicación se ejecuta
mediante el inicio directo desde un venv:

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install -e ".[ai]"
python3 -m bgremover
```

Previamente se necesitan algunas bibliotecas de sistema de Qt — para más
detalles consulta **[INSTALL_LINUX.md](INSTALL_LINUX.md)**.

En **Raspberry Pi OS (Desktop)** es especialmente sencillo — sin ningún
venv/pip (PyQt6, Pillow, numpy como paquetes de sistema vía `apt`);
consulta la sección de Raspberry Pi en
**[INSTALL_LINUX.md](INSTALL_LINUX.md)**.

> Las instrucciones detalladas — incluida la **instalación desde una
> rama** (para probar pull requests abiertos) y la **resolución de
> problemas** — están en **[INSTALL_MAC.md](INSTALL_MAC.md)** (macOS) o
> **[INSTALL_LINUX.md](INSTALL_LINUX.md)** (Linux).

## Uso

1. **Abre una imagen** mediante `Archivo → Abrir` (⌘O) o arrastrando y soltando en la ventana.
2. **Realiza una selección** con la varita mágica, el pincel o el borrador (pestaña *🎯 Selección*).
   - `Shift+clic` añade a la selección, `Ctrl+clic` resta.
3. **Edita el fondo** (pestaña *🖼 Fondo*): hazlo transparente o reemplaza el color — o directamente con **IA** en la barra de herramientas.
4. **Transforma la imagen** (pestaña *⟲ Trans.*): rota, refleja.
5. **Forma y recorte** (pestaña *⬤ Forma*): redondea esquinas o recorta a un formato — mueve/escala el marco, luego ✓ Aplicar.
6. **Guarda** mediante `Archivo → Guardar` (⌘S) como PNG, JPEG, WebP o TIFF.

### Ajustes

Mediante `Herramientas → Ajustes…` (⌘,) se pueden guardar de forma permanente tres preferencias de usuario:

| Ajuste | Descripción |
|---|---|
| Directorio predeterminado para abrir | Directorio inicial del diálogo de apertura; vacío = último directorio utilizado |
| Directorio predeterminado para exportar/guardar | Directorio inicial del diálogo de guardado; vacío = último directorio utilizado |
| Formato de archivo de imagen preferido | PNG, JPEG, WebP o TIFF – aparece como primera opción en el diálogo de guardado |

Los ajustes se guardan de forma persistente mediante **QSettings** y se restauran automáticamente en el siguiente inicio del programa.

### Atajos de teclado

| Acción | Atajo |
|--------|----------|
| Abrir imagen | ⌘O |
| Guardar imagen | ⌘S |
| Guardar imagen como… | ⇧⌘S |
| Deshacer | ⌘Z |
| Rehacer | ⇧⌘Z |
| Rotar 90° a la izquierda | ⌘← |
| Rotar 90° a la derecha | ⌘→ |
| Anular selección | Esc |
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
pip install ".[test]"
make check
```

La suite de pruebas se ejecuta sin interfaz gráfica (plataforma Qt
`offscreen`) y verifica las operaciones de imagen, la geometría del
recorte y la lógica de guardado. Los pull requests ejecutan una CI
ligera en GitHub (Ubuntu, Python 3.12, `make check`). La matriz completa
en Linux/macOS con Python 3.10 y 3.12 se ejecuta al publicar un release
o manualmente. Consulta [TESTING.md](../../../TESTING.md) para el flujo
completo de pruebas.

Comprobación del estilo de código y verificación estática de tipos:

```bash
make lint
make type
```

## Arquitectura (resumen breve)

Desde la ronda 5, BgRemover es un paquete instalable (`bgremover/`,
iniciado vía `python -m bgremover` o el script de consola `bgremover`):

- **`ImageCanvas`** (QGraphicsView) mantiene el estado de la imagen, la
  máscara de selección, las pilas de Deshacer/Rehacer y las herramientas
  (varita mágica, pincel, lazo, recorte).
- **`MainWindow`** construye la barra de herramientas, el panel de
  pestañas a la derecha (cuatro constructores `_build_tab_*`), el menú y
  conecta todo con el lienzo.
- Los **Worker** (`ImageLoadWorker`, `AIWorker`, `RembgWarmupWorker`) se
  ejecutan en sus propios `QThread`s; `_launch_worker()` encapsula el
  ciclo de vida del hilo.
- Un **contador de versión** monótono en el lienzo descarta resultados
  de IA obsoletos si entretanto se cargó otra imagen.
- La pila de Deshacer no está limitada por `maxlen`, sino por un
  **límite de memoria** (`_UNDO_MEMORY_LIMIT`); una suma de bytes en
  curso evacúa las entradas más antiguas.

## Limitaciones conocidas

- **Tamaño máximo de imagen: 40 megapíxeles.** Las imágenes más grandes
  se rechazan con un mensaje de estado. La selección con varita mágica
  (flood-fill) se ejecuta de forma síncrona en el hilo de la interfaz;
  más allá de este límite, incluso la variante vectorizada provocaría un
  retraso notable. Pillow está además protegido contra imágenes de tipo
  «bomba de descompresión».
- La **compilación del paquete de aplicación** es específica de macOS; en
  Linux/Windows la aplicación se ejecuta mediante el inicio directo
  `python -m bgremover`.

## Archivo de registro

Al iniciar el programa se crea un archivo de registro `bgremover.log` en
el directorio de datos de la aplicación específico de la plataforma
(macOS: `~/Library/Application Support/BgRemover/`,
Linux: `~/.local/share/BgRemover/`). Contiene trazas de pila y mensajes
de estado y es el primer punto de consulta ante problemas.

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
