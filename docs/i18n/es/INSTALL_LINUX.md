[Deutsch](../../../INSTALL_LINUX.md) · [English](../en/INSTALL_LINUX.md) · **Español** · [Français](../fr/INSTALL_LINUX.md) · [Українська](../uk/INSTALL_LINUX.md) · [简体中文](../zh/INSTALL_LINUX.md)

# BgRemover – Instalación en Linux

Guía breve para instalar e iniciar BgRemover desde GitHub — tanto desde
la rama `main` como desde una rama de funcionalidad (p. ej. para probar
un pull request abierto antes del merge).

> El paquete de aplicación de macOS (`create_BgRemover_app.sh`) es
> específico de macOS. En Linux, AppImage y `.deb` son los artefactos
> recomendados para usuarios finales; el inicio directo desde un venv queda
> documentado para desarrollo, pruebas de ramas y cambios locales.

## Recomendado: usar artefactos de release

Para una instalación normal en Linux, los artefactos de release son la vía más
cómoda — **sin venv, sin pip y sin checkout de Git**:

> **Nota sobre la disponibilidad:** Los artefactos AppImage/`.deb` listos
> existen a partir de **v2.3.0**. Las releases anteriores (p. ej. v2.2.0) aún
> no incluyen tales assets — mientras no haya nada que descargar en la página
> de releases, usa la vía venv/Git más abajo.

- **AppImage:** archivo único portable; hazlo ejecutable y ejecútalo.
- **`.deb`:** paquete instalable para Debian/Ubuntu/Raspberry Pi OS con entrada
  de menú y desinstalación limpia vía apt/dpkg.

Descarga el artefacto adecuado desde la [página de releases de GitHub](https://github.com/NikolayDA/picture_helper/releases):

```bash
# AppImage (ejemplo x86_64)
chmod +x BgRemover-*-x86_64.AppImage
./BgRemover-*-x86_64.AppImage

# .deb (ejemplo amd64; apt instala la dependencia FUSE)
sudo apt install ./BgRemover-*-amd64.deb
```

Hay builds para **x86_64** y **aarch64/Raspberry Pi OS 64-bit**. Las
instrucciones venv/Git siguientes siguen siendo útiles si quieres probar desde
`main`, desde una rama de funcionalidad o con cambios locales.

## Requisitos

> **¿Raspberry Pi OS (Desktop)?** Entonces toma la vía claramente más
> sencilla [más abajo](#raspberry-pi-os-desktop--la-forma-sencilla) —
> sin ningún venv ni pip. La siguiente sección aplica a Linux en
> general.

- **Una distribución de Linux con escritorio** (X11 o Wayland)
- **Python 3.10 o posterior** — comprueba con:
  ```bash
  python3 --version
  ```
- **git** y el módulo **venv** (`python3-venv`)
- **Bibliotecas de sistema de Qt** para PyQt6 — los wheels de PyQt6
  contienen Qt en sí, pero necesitan algunas bibliotecas de sistema
  X11/XCB. Sin ellas, la GUI se inicia con el error *«qt.qpa.plugin:
  Could not load the Qt platform plugin xcb»*.

> **Nota sobre la IA:** La app principal funciona con Python 3.10+. La
> eliminación de fondo con IA (`.[ai]`) requiere **Python 3.11 o posterior**
> (los builds actuales de `onnxruntime` y `rembg` apuntan a Python 3.11+).

### Instalar paquetes de sistema

**Debian / Ubuntu / Linux Mint** (`apt`):
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git \
  libegl1 libgl1 libfontconfig1 libxkbcommon0 libxkbcommon-x11-0 \
  libdbus-1-3 libxcb-cursor0 libxcb-icccm4 libxcb-image0 \
  libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 \
  libxcb-xinerama0 libxcb-xkb1
```
(`libxcb-cursor0` lo necesita Qt 6.5+ para el plugin `xcb`, entre otros
en Ubuntu 24.04.)

**Fedora / RHEL** (`dnf`):
```bash
sudo dnf install -y python3 python3-pip git \
  libxcb xcb-util-cursor xcb-util-image xcb-util-keysyms \
  xcb-util-renderutil xcb-util-wm libxkbcommon-x11 \
  fontconfig mesa-libGL mesa-libEGL dbus-libs
```

**Arch / Manjaro** (`pacman`):
```bash
sudo pacman -S --needed python python-pip git \
  libxcb xcb-util-cursor xcb-util-image xcb-util-keysyms \
  xcb-util-renderutil xcb-util-wm libxkbcommon-x11 \
  fontconfig mesa
```

## Raspberry Pi OS (Desktop) – la forma sencilla

En **Raspberry Pi OS «Bookworm» Desktop** (Debian 12) o más reciente
(p. ej. «Trixie»/Debian 13, se recomienda 64 bits) la instalación es
claramente más sencilla: PyQt6, Pillow y
numpy están disponibles como paquetes de sistema listos vía `apt`. **No
se necesita ningún venv, ningún `pip` ni ninguna instalación editable** —
BgRemover se ejecuta directamente desde el clon. El paquete
`python3-pyqt6` incluye automáticamente como dependencia las bibliotecas
Qt6/XCB necesarias (la larga lista de XCB de arriba ya no hace falta).

```bash
sudo apt update
sudo apt install -y git python3-pyqt6 python3-numpy python3-pil
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m bgremover
```

Eso es todo — la ventana principal se abre. Las herramientas manuales
(varita mágica, pincel/borrador, recorte, rotar, reflejar, redondear
esquinas) funcionan completamente. La **eliminación de fondo con IA está
desactivada en esta instalación mínima** (el botón de IA está
atenuado) — opcionalmente se puede añadir si es necesario (ver más
abajo).

Para actualizar más adelante, basta con `git pull` en la carpeta del
proyecto; no hace falta repetir ningún paso de instalación.

### Opcional: iniciar desde el menú de aplicaciones

Crea un archivo `~/.local/share/applications/bgremover.desktop` y
reemplaza `/PFAD/ZU/picture_helper` por la ruta absoluta del proyecto:
```ini
[Desktop Entry]
Type=Application
Name=BgRemover
Comment=Quitar el fondo y editar imágenes
Exec=python3 -m bgremover
Path=/PFAD/ZU/picture_helper
Icon=/PFAD/ZU/picture_helper/BgRemover_icon.png
Categories=Graphics;Photography;
Terminal=false
```
BgRemover aparece después en el menú de aplicaciones y se inicia con un
clic — sin venv ni script wrapper.

### Opcional: añadir la eliminación de fondo con IA

> **Nota:** En la Raspberry Pi la IA (`rembg` + `onnxruntime`) es
> **claramente más lenta y consume más memoria**. Se recomienda solo en
> **Raspberry Pi OS de 64 bits** (`uname -m` → `aarch64`) y en una
> Pi 4/5 con suficiente RAM (≥ 4 GB). En 32 bits (`armv7l`/armhf) por lo
> general no hay wheels de `onnxruntime` adecuados — ahí es mejor
> prescindir de la IA.

Como `rembg` se instala posteriormente vía pip, usa para ello un venv
**con acceso a los paquetes Qt del sistema**:
```bash
cd picture_helper
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install "rembg[cpu]"
python3 -m bgremover
```
`--system-site-packages` hace visibles en el venv los PyQt6/Pillow/numpy
instalados vía `apt`, de modo que solo se descargan adicionalmente
`rembg` y `onnxruntime`. En el primerísimo clic de IA, `rembg` descarga
su modelo una sola vez (algunos cientos de MB, caché en `~/.u2net`).
Inicios posteriores entonces desde el venv: `source .venv/bin/activate`
y `python3 -m bgremover`.

## Inicio rápido desde `main`

En Linux moderno, las instalaciones del Python del sistema bloquean
`pip install` según el PEP 668 («externally-managed-environment»). Por
eso se instala en un venv aislado:

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install --upgrade "pip>=26.1.2"
python3 -m pip install -c requirements/constraints.txt -e ".[ai]"
python3 -m bgremover
```

- `.[ai]` instala `rembg[cpu]` incl. `onnxruntime` (eliminación de fondo
  con IA).
- Sin la función de IA basta con: `python3 -m pip install -c requirements/constraints.txt -e .`

En una shell nueva, vuelve a activar el venv antes de iniciar:
```bash
cd picture_helper
source .venv/bin/activate
python3 -m bgremover
```

## Variantes de inicio

| Variante | Comando / Acción | Resultado |
|----------|-----------------|----------|
| **A – Terminal (recomendado)** | activar el venv, luego `python3 -m bgremover` | Inicio directo desde el directorio del proyecto. |
| **B – Script de arranque** | `./bgremover.sh` (ver más abajo) | Activa el venv automáticamente e inicia la app. |
| **C – Menú de aplicaciones** | entrada `.desktop` (ver más abajo) | Inicio con doble clic / desde el menú de aplicaciones. |

### B – Script de arranque

Crea un archivo `bgremover.sh` en el directorio del proyecto:
```bash
#!/usr/bin/env bash
cd "$(dirname "$0")" || exit 1
source .venv/bin/activate
exec python3 -m bgremover "$@"
```
Hazlo ejecutable e inícialo:
```bash
chmod +x bgremover.sh
./bgremover.sh
```

### C – Entrada de escritorio (menú de aplicaciones)

Crea un archivo `~/.local/share/applications/bgremover.desktop` y
reemplaza `/PFAD/ZU/picture_helper` por la ruta absoluta del proyecto:
```ini
[Desktop Entry]
Type=Application
Name=BgRemover
Comment=Quitar el fondo y editar imágenes
Exec=/PFAD/ZU/picture_helper/bgremover.sh
Icon=/PFAD/ZU/picture_helper/BgRemover_icon.png
Categories=Graphics;Photography;
Terminal=false
```
Después, actualiza la base de datos de escritorio (opcional):
```bash
update-desktop-database ~/.local/share/applications 2>/dev/null || true
```
BgRemover aparece ahora en el menú de aplicaciones.

## Instalación desde una rama (probar PRs abiertos)

Los nombres de las ramas de PR están en el respectivo pull request en
GitHub («… wants to merge … from **`<branch>`**»).

**Variante 1 – en el directorio del clon existente:**
```bash
cd picture_helper
git fetch origin
git branch -r                       # mostrar ramas disponibles
git checkout <branch>
source .venv/bin/activate
# solo necesario si han cambiado las dependencias:
python3 -m pip install --upgrade "pip>=26.1.2"
python3 -m pip install -c requirements/constraints.txt -e ".[ai]"
python3 -m bgremover
```

**Variante 2 – clonar una rama directamente:**
```bash
git clone --branch <branch-name> \
  https://github.com/NikolayDA/picture_helper.git
```

## Actualizar / cambiar de rama

```bash
git checkout main && git pull          # versión principal más reciente
git checkout <branch> && git pull      # actualizar una rama concreta
```

La instalación editable (`pip install -e`) **no** hay que volver a
ejecutarla tras `git pull` — salvo que hayan cambiado las dependencias
en `pyproject.toml` o `requirements/constraints.txt`.

## Resolución de problemas

- **`qt.qpa.plugin: Could not load the Qt platform plugin "xcb"`** →
  Faltan bibliotecas de sistema de Qt. Instala adicionalmente los
  paquetes de la sección *«Instalar paquetes de sistema»* (en
  particular `libxcb-cursor0` en Ubuntu 24.04). Qué biblioteca falta
  exactamente lo muestra:
  ```bash
  QT_DEBUG_PLUGINS=1 python3 -m bgremover 2>&1 | grep -i "cannot\|not found"
  ```
- **`error: externally-managed-environment` en `pip install`** → PEP
  668: no instales en el Python del sistema, sino en un venv (ver
  Inicio rápido). ¿Falta el módulo venv? → `sudo apt install python3-venv`.
- **«python3: command not found» o versión < 3.10** → instala un Python
  actual mediante el gestor de paquetes de la distribución (el código
  usa anotaciones de tipo PEP-604 como `QThread | None`; Python 3.9
  falla).
- **Wayland: la ventana/escalado parece defectuosa** → cambia a modo de
  prueba al plugin X11 (XWayland):
  ```bash
  QT_QPA_PLATFORM=xcb python3 -m bgremover
  ```
- **Error de pip al instalar** → en el venv activo, actualiza primero
  pip, luego repite el comando de instalación:
  ```bash
  python3 -m pip install --upgrade "pip>=26.1.2"
  ```
- **El primer clic de IA tarda mucho** → La primerísima vez, `rembg`
  descarga su modelo (algunos cientos de MB, una sola vez, caché en
  `~/.u2net`). La barra de estado muestra «🤖 Cargando modelo de IA…»
  y luego «🤖 IA lista».
- **La app se inicia sin IA / «No onnxruntime backend found»** → No se
  instaló el extra `ai`. Instálalo adicionalmente en el venv:
  ```bash
  python3 -m pip install "rembg[cpu]"
  ```
- **Raspberry Pi: `Unable to locate package python3-pyqt6`** → Las
  versiones más antiguas de Raspberry Pi OS (Bullseye) solo traen
  PyQt5. Actualiza a «Bookworm» (o más nuevo) — o sigue la vía general
  de venv/pip de arriba.
- **Raspberry Pi OS «Bookworm» (Pi 4/5) usa Wayland** → Ante problemas
  de ventana o escalado, cambia a modo de prueba al plugin X11:
  `QT_QPA_PLATFORM=xcb python3 -m bgremover` (ver la nota sobre Wayland
  más arriba).
- **Diagnóstico ante errores** → La ruta exacta del registro interno de
  ejecución aparece en `Extras → Ajustes… → Archivo de registro`; en
  Linux se encuentra en el directorio determinado por Qt bajo
  `~/.local/share/`. Al iniciar desde el terminal, el mensaje de error
  aparece además directamente en la consola.
