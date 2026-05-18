[Deutsch](../../../INSTALL_MAC.md) · [English](../en/INSTALL_MAC.md) · **Español** · [Français](../fr/INSTALL_MAC.md) · [Українська](../uk/INSTALL_MAC.md) · [简体中文](../zh/INSTALL_MAC.md)

# BgRemover – Instalación en el Mac

Guía breve para instalar e iniciar BgRemover desde GitHub — tanto desde
la rama `main` como desde una rama de funcionalidad (p. ej. para probar
un pull request abierto antes del merge).

## Requisitos

- **macOS**
- **Python 3.10 o posterior** — comprueba con:
  ```bash
  python3 --version
  ```
- **git**

Si faltan Python o git, lo más sencillo es mediante [Homebrew](https://brew.sh):
```bash
brew install python git
```

## Inicio rápido desde `main`

**Recomendado** es el script del paquete de aplicación — crea
automáticamente un venv aislado, instala todas las dependencias (incl.
`onnxruntime` para la IA), maneja correctamente Apple Silicon y copia
los iconos de la barra de herramientas al bundle:

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
bash create_BgRemover_app.sh
```

Confirma con **Enter** ante el aviso del venv; después, inicia
`BgRemover.app` en `~/Applications` con doble clic.

**Inicio directo en el terminal** — en macOS moderno dentro de un venv,
ya que el Python del sistema bloquea `pip install` según el PEP 668:

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install -e ".[ai]"
python3 BgRemover.py
```

- `.[ai]` instala `rembg[cpu]` incl. `onnxruntime` (eliminación de fondo con IA).
- Sin la función de IA basta con: `python3 -m pip install -e .`

## Variantes de inicio

Tras la instalación hay tres formas de iniciar el programa:

| Variante | Comando / Acción | Resultado |
|----------|-----------------|----------|
| **A – App de macOS (recomendado)** | `bash create_BgRemover_app.sh` | Crea un venv aislado, instala todas las dependencias (incl. `onnxruntime`), copia los iconos y genera un `BgRemover.app` independiente en `~/Applications`. La cuarentena se elimina automáticamente; el proyecto puede permanecer en `~/Documents`. |
| **B – Doble clic** | doble clic en `BgRemover.command` en el Finder | Se inicia en la ventana del terminal; usa automáticamente el venv de la app creado por el script (el archivo ya es ejecutable). |
| **C – Terminal** | en un venv: `python3 BgRemover.py` | Inicio directo (configuración del venv: ver Inicio rápido arriba). |

## Instalación desde una rama (probar PRs abiertos)

Los nombres de las ramas de PR están en el respectivo pull request en
GitHub («… wants to merge … from **`<branch>`**»).

**Variante 1 – en el directorio del clon existente:**
```bash
cd picture_helper
git fetch origin
git branch -r                       # mostrar ramas disponibles
git checkout <branch>
# en un venv (ver Inicio rápido); solo necesario si han cambiado las dependencias:
python3 -m pip install -e ".[ai]"
python3 BgRemover.py
```

Alternativamente, en una rama también puedes simplemente ejecutar
`bash create_BgRemover_app.sh` — eso se encarga del venv y las
dependencias automáticamente.

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
en `pyproject.toml`.

## Resolución de problemas

- **La app no se inicia / el doble clic no hace nada** → Desde la v3, la
  app muestra un diálogo de error con «Abrir registro». Causa más
  frecuente: `PyQt6` no está instalado en el Python que usa la app
  (p. ej. porque `pip install` fue a un venv o a otro Python, o porque
  el Python de Homebrew bloquea `pip install` según el PEP 668).
  Solución: vuelve a ejecutar `bash create_BgRemover_app.sh` y deja que
  cree el venv (confirma la propuesta con Enter) — el script instala
  entonces las dependencias en un venv bajo
  `~/Library/Application Support/BgRemover/venv` y empaqueta ese Python
  en la app.
- **`[Errno 1] Operation not permitted` al abrir `BgRemover.py`**
  → Privacidad de macOS (TCC). Si el proyecto está en `~/Documents`,
  `~/Desktop`, `~/Downloads` o iCloud Drive, una `.app` iniciada desde
  el Finder no puede leer ahí. Desde la v3 esto está resuelto:
  `BgRemover.py` se copia al paquete de aplicación y el venv reside en
  Application Support — ejecuta `bash create_BgRemover_app.sh` una vez
  de nuevo. (Alternativamente, mueve el proyecto a p. ej.
  `~/picture_helper` y ejecuta el script allí de nuevo.)
- **`numpy ... incompatible architecture (have 'arm64', need 'x86_64')`**
  → Apple Silicon: en `~/Library/Python/...` hay un paquete de otra
  arquitectura que se «filtra» a un Python con arquitectura no
  coincidente. Desde la v3.1 esto está resuelto: el launcher establece
  `PYTHONNOUSERSITE=1` (el user-site se ignora), fuerza la arquitectura
  de CPU nativa y se usa obligatoriamente un venv aislado. Solución: lo
  mejor es instalar primero un Python nativo, luego recompilar:
  ```bash
  brew install python
  bash create_BgRemover_app.sh   # confirma la pregunta del venv con Enter
  ```
- **Ver el error directamente (diagnóstico manual)** → Inicia el
  launcher en el terminal; entonces aparece el mensaje de error real:
  ```bash
  ~/Applications/BgRemover.app/Contents/MacOS/BgRemover
  ```
  Esperable ante paquetes faltantes: `ModuleNotFoundError: No module named 'PyQt6'`.
- **«python3: command not found»** → `brew install python`
- **Error de pip al instalar** → actualiza primero pip:
  ```bash
  python3 -m pip install --upgrade pip
  ```
  luego ejecuta de nuevo el comando de instalación.
- **El primer clic de IA tarda mucho** → La primerísima vez, `rembg`
  descarga su modelo (algunos cientos de MB, una sola vez, caché en
  `~/.u2net`). La barra de estado muestra «🤖 Cargando modelo de IA…»
  y luego «🤖 IA lista».
- **Gatekeeper: «desarrollador no verificado»** → Clic derecho sobre
  `BgRemover.app` → **Abrir**. El script de compilación ya elimina la
  cuarentena mediante `xattr`; aun así, en caso de duda, abrir con clic
  derecho es suficiente.
- **La app se cierra con «No onnxruntime backend found»** → Las
  versiones más nuevas de `rembg` ya no incluyen el backend. Actualmente
  resuelto (el extra `ai` incluye `rembg[cpu]`/`onnxruntime`; si aun así
  falta, la app se inicia sin IA en lugar de cerrarse). Solución:
  recompila una vez con `bash create_BgRemover_app.sh` — o instálalo
  adicionalmente en el venv:
  `"~/Library/Application Support/BgRemover/venv/bin/python3" -m pip install "rembg[cpu]"`.
- **La `.app` se ve distinta a `BgRemover.command`** → Bundle antiguo
  sin los iconos de la barra de herramientas (la app usaba iconos de
  reemplazo dibujados). Actualmente resuelto — el script copia `icons/`
  al bundle; recompila una vez con `bash create_BgRemover_app.sh`.
- **Diagnóstico ante errores** → Consulta el archivo de registro `~/.bgremover.log`.
