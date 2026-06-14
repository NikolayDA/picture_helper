[Deutsch](../../../CHANGELOG.md) · [English](../en/CHANGELOG.md) · **Español** · [Français](../fr/CHANGELOG.md) · [Українська](../uk/CHANGELOG.md) · [简体中文](../zh/CHANGELOG.md)

# Changelog

Todos los cambios destacables en BgRemover se documentan en este
archivo. El formato se basa en
[Keep a Changelog](https://keepachangelog.com/de/1.1.0/); el proyecto
sigue [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

### Añadido

- **Benchmark de rendimiento de la canalización de imágenes.**
  `scripts/benchmark.py` mide el tiempo de procesamiento por formato de salida
  (PNG/JPEG/WebP/TIFF) a través de las rutas reales de `image_ops`, guarda
  resultados fechados en `benchmarks/results/` y compara ejecuciones
  consecutivas; los formatos que empeoran más de un 10 % se marcan y se informan
  opcionalmente como incidencias de GitHub (`make bench` / `make bench-compare`).
  Un flujo de CI semanal (`.github/workflows/benchmark.yml`) ejecuta y compara en
  hardware constante y vuelve a registrar el resultado como próxima referencia.
- **Tests de comportamiento reforzados.** Se amplió la cobertura de tests de
  comportamiento para rutas hasta ahora incompletas (#177, #192).
- **Tests unitarios dedicados para `app.py` y `main_window.py`.** Cobertura de
  `app.py` 0 % → 100 % y `main_window.py` 68 % → 100 %; la cobertura total subió
  al 94 % (#214).

### Cambiado

- **Dependencias actualizadas.** `idna` sube a 3.15 y `urllib3` a 2.7.0;
  `LICENSES.md` queda sincronizado con el nuevo snapshot de dependencias.
- **Backend de compilación fijado frente a CVE de cadena de suministro.**
  `setuptools` sube a `>=78.1.1` en `pyproject.toml` (`[build-system]`) y en
  `requirements/constraints.txt` (CVE-2024-6345 RCE, CVE-2025-47273 path
  traversal), y `wheel` a `==0.46.2` en `constraints.txt` (CVE-2026-24049). Así
  la compilación aislada del wheel ya no puede traer herramientas de compilación
  vulnerables (#200, #201).
- **pip elevado a una versión parcheada en CI/dev.** Los workflows de CI que
  instalan con pip (`ci.yml`, `pr-ci.yml`, `ui-nightly.yml`, `benchmark.yml`,
  `license-check.yml`) y el hook SessionStart web suben `pip` a `>=26.1.2` antes
  de instalar, igual que la documentación de instalación para dev
  (`README.md`/`INSTALL_MAC.md`/`INSTALL_LINUX.md`). Cierra el lote de
  `pip-audit` de CVE de path traversal, symlink y secuestro de módulos; pip es
  la propia herramienta de instalación y por eso no se puede fijar vía
  `constraints.txt` (#202).
- **El diagnóstico de macOS redacta rutas sensibles.** `diagnose_mac.sh`
  sustituye ahora `$HOME` por `~` de forma predeterminada, acorta las demás
  rutas `/Users/<name>` e imprime un resumen filtrado de errores con rutas
  redactadas en lugar de las últimas 40 líneas crudas del log — la salida
  puede adjuntarse sin riesgo a los informes de errores. La nueva opción
  `--include-raw-logs` ofrece el diagnóstico completo (incluido el log crudo);
  una prueba de shell (`tests/test_diagnose_mac.py`) garantiza que el
  directorio home y las rutas de imágenes no lleguen a la salida
  predeterminada (#185).
- **Dependencias del release AppImage fijadas.** Un snapshot de
  `requirements/constraints.txt` fija las versiones para el workflow de
  compilación AppImage (#182, #191).
- **Permisos del workflow de licencias reforzados.** El workflow se ejecuta
  ahora con permisos mínimos (#183, #193).
- **`CanvasHistory._redo_max` eliminado.** El atributo de solo escritura nunca
  se leía; el límite de rehacer se aplica únicamente vía `deque(maxlen=…)`
  (#199, #215).

### Corregido

- **Límite de tamaño de archivo de entrada antes de leer.**
  `open_validated_image` ahora comprueba el archivo de entrada con `os.fstat()`
  frente a un límite de bytes documentado (`_MAX_INPUT_FILE_BYTES`, 512 MB)
  **antes** de leer su contenido completo en memoria; un `read()` acotado
  adicional protege frente a objetos de archivo inusuales y a un cambio de
  tamaño entre `fstat()` y `read()` (TOCTOU). El mensaje distingue el tamaño de
  archivo (MB) del límite de megapíxeles (MP). Las rutas de carga síncrona y
  asíncrona comparten la misma comprobación; se conservan el límite de
  megapíxeles existente y la protección TOCTOU (#230).
- **La sesión de inferencia de rembg se reutiliza.** El warmup ahora crea
  exactamente una sesión rembg/ONNX mediante `new_session()` y la guarda a nivel
  de módulo; cada `AIWorker` posterior la pasa a `remove(..., session=...)` en
  lugar de reinicializar el modelo. La creación es thread-safe mediante
  double-checked locking y se ejecuta como mucho una vez a lo largo de varias
  llamadas de IA; un init fallido sigue informando el error del worker y no deja
  un estado falsamente «listo». El comentario engañoso (que un `remove()` dummy
  cachea la sesión) queda corregido (#229).
- **`recent_files` es robusto frente a ajustes corruptos.**
  `RecentFiles.paths()` ahora maneja cada tipo bruto almacenado de forma
  defensiva: un solo string sigue siendo una entrada, las listas/tuplas se
  filtran elemento a elemento a strings no vacíos, y cualquier otro valor
  (p. ej. entero, `None`) produce una lista vacía en lugar de un `TypeError`.
  El nuevo `sanitize()` reescribe una vez al inicio un valor realmente corrupto
  ya limpio (con aviso de log); el inofensivo string de un elemento de QSettings
  se deja intacto. Así, un valor `recent_files` editado a mano o desactualizado
  ya no aborta el menú ni el arranque de la app; un esquema más nuevo (futuro)
  también se deja intacto para evitar pérdida de datos en un downgrade (#233, #240).
- **Double-checked lock para el import perezoso de rembg y protección TOCTOU en
  `open_validated_image`.** Dos hilos podían entrar al import a la vez (race) y
  el archivo se abría dos veces (ventana TOCTOU); ambos están cubiertos por
  tests de regresión (#174).
- **Los resultados obsoletos de carga asíncrona de imágenes se descartan.** Un
  contador monótono `_load_generation` en `MainWindow` evita que un callback de
  carga tardío sobrescriba una imagen más nueva (análogo al stale-check de IA)
  (#190).
- **Tipado de la máscara de selección del canvas corregido.** Un tipo incorrecto
  provocaba un error de mypy en la ejecución de CI completa (#196, #197).
- **YAML del workflow de CI reparado.** El nombre sin comillas del paso de
  actualización de pip rompía el parseo del workflow (#213).
- **Un recorte activo ya no sobrevive a un cambio de estado de imagen.** Cada
  cambio visible de imagen (rotar, voltear, resultado de IA, deshacer/rehacer,
  restaurar original, confirmar recorte) ahora descarta de forma central en
  `_set_image_state` un overlay de recorte activo y un lazo en curso, y emite
  `cropModeChanged(False)` exactamente una vez. Así, un rectángulo de recorte
  obsoleto ya no puede aplicarse a la nueva imagen ni generar píxeles de relleno
  transparentes (#247).
- **El workflow de release solo publica tras un gate de Full CI en verde.**
  `release-linux.yml` ahora invoca la matriz Full CI de referencia (`ci.yml`)
  como workflow reutilizable y ata build y publish a ella mediante `needs`; un
  job `verify-tag` aparte falla si el tag no cumple `vX.Y.Z` o difiere de
  `project.version`. AppImage/`.deb` se comprueban en nombre, arquitectura,
  ejecutabilidad y metadatos Debian antes de subirlos, y los errores de
  `gh release create` ya no se ocultan con `|| true` (un release existente se
  reutiliza explícitamente). Así, ningún artefacto de un commit con tests en rojo
  o versión discrepante llega ya a un release (#250).
- **Una selección vacía libera el pixmap del overlay de inmediato.**
  `_refresh_overlay` ahora comprueba el estado vacío de la máscara **antes** del
  camino incremental (dirty). Cuando la goma borra el último píxel seleccionado,
  `_overlay_pixmap` y el `QGraphicsPixmapItem` se vacían enseguida en lugar de
  retener una QPixmap transparente del tamaño completo de la imagen (~160 MiB a
  40 MP) hasta la siguiente reconstrucción completa. El borrado parcial sigue
  actualizando solo el rectángulo sucio (#251).

### Eliminado

## [2.3.0] – 2026-06-04


### Añadido

- **Cobertura de pruebas aumentada al 88 % (segunda ronda; antes 82 %).** La
  nueva `tests/test_canvas_events.py` cubre manejadores de eventos y lógica de
  `canvas.py`: ratón, teclado, rueda, arrastre, flujos de resultado de la varita,
  ajustes de herramientas, undo/redo/undo-to durante crop activo y guards sin
  imagen cargada. `canvas.py` sube de 64 % a 99 % y `fail_under` pasa de 80 a 86.
- **Cobertura de pruebas aumentada al 82 % (antes 74 %).** Nuevas pruebas de
  comportamiento cubren `tests/test_lasso.py`, `tests/test_canvas_crop.py`,
  `tests/test_viewport.py`, `tests/test_crop_overlay.py`,
  `tests/test_settings_schema.py` y `tests/test_settings_dialog.py`. Con ello
  varios módulos quedan al 100 %, `canvas_crop.py` al 98 %, y `fail_under` sube
  de 68 a 80.
- **i18n de ANLEITUNG.md.** Se añadieron cinco traducciones de la guía alemana
  en `docs/i18n/{en,es,fr,uk,zh}/ANLEITUNG.md`; `tests/test_i18n_docs.py`
  incluye ahora `"ANLEITUNG.md"` y cada traducción indica que `ANLEITUNG.pdf`
  solo se genera desde el original alemán.
- **Prueba soft-drift `tests/test_i18n_sync.py`.** Compara jerarquía de títulos
  y número de bloques de código en `CHANGELOG.md`, `INSTALL_MAC.md` e
  `INSTALL_LINUX.md` contra los originales alemanes; las diferencias generan
  advertencias legibles en lugar de fallos duros.
- **`bgremover/status_messages.py` – mensajes de estado centralizados.** Los
  textos visibles de estado de `canvas.py`, `canvas_crop.py` y `main_window.py`
  pasan a la clase `StatusMessages`, como preparación para futura localización.
- **i18n runtime con soporte de inglés.** Alemán e inglés pueden cambiarse en
  runtime; el diálogo de ajustes incluye un selector persistente de idioma con
  aviso de reinicio, y los textos UI de canvas, diálogos y panel derecho usan
  la capa central de traducción.
- **Atajos de teclado para herramientas.** Las herramientas de edición pueden
  cambiarse desde el teclado; los tooltips de la toolbar y la documentación
  indican los atajos adecuados por plataforma.
- **Paquetización Linux AppImage.** El build de release genera un AppImage como
  ruta recomendada para usuarios finales Linux, con scripts de empaquetado,
  cobertura CI y notas de instalación.
- **Linux `.deb`, aarch64/Raspberry Pi y workflow de release.** La
  paquetización Linux se amplía con paquetes Debian, soporte aarch64/Pi y el
  workflow de release correspondiente.
- **Versión de esquema para QSettings.** Nuevo `bgremover/settings_schema.py`
  con `SCHEMA_VERSION = 1` y `migrate(settings)`; `MainWindow.__init__` ejecuta
  la migración al crear `QSettings`. Hay protección ante downgrade, valores
  corruptos y pruebas en `tests/test_settings_schema.py`.
- **Prueba de runtime para `RembgWarmupWorker`.** Nuevas pruebas en
  `tests/test_workers.py` y `tests/test_worker_controller.py` verifican que el
  warmup siempre emite `finished` y que el lifecycle del thread se cierra incluso
  si `rembg_remove` falla al primer arranque.

### Cambiado

- Documentación y comentarios de código limpiados: se retiraron marcadores
  obsoletos de PR/rondas en la documentación viva, se actualizaron las notas
  de instalación de macOS y las recomendaciones quedaron como estado actual
  breve de review/roadmap.
- La versión del proyecto subió a 2.3.0 en metadatos del paquete, AppStream,
  resúmenes de licencias y enlaces del changelog.

- **Idioma de docstrings unificado.** `bgremover/image_ops.py`,
  `bgremover/recent_files.py` y `bgremover/worker_controller.py` pasan de
  docstrings en inglés a alemán, coherente con el resto del proyecto.
- **Documentación de usuario para paquetes Linux e idioma actualizada.** README,
  `INSTALL_LINUX.md` y `ANLEITUNG.md` mencionan AppImage/`.deb` como ruta
  recomendada para usuarios Linux y documentan la preferencia persistente de
  idioma con aviso de reinicio; las copias i18n quedan sincronizadas.
- **Ronda de higiene de código.** La versión fallback lee `pyproject.toml`,
  `_paint_brush` recibe `additive` explícitamente, `apply_remove`/`apply_replace`
  capturan solo errores esperados, se documentan efectos globales y casos
  QSettings, `make clean` limpia artefactos extra y la descripción del proyecto
  refleja soporte macOS/Linux.
- **La selección de varita ya no congela la UI.** El flood-fill se mueve a
  `FloodFillWorker` en un `QThread` corto con comprobación stale por
  `content_revision`; panning/zoom siguen reactivos y solo se bloquea un clic de
  varita paralelo con mensaje de estado.
- **Matriz de CI ampliada.** Full CI comprueba Python 3.10, 3.11, 3.12 y 3.13 en
  Ubuntu y macOS.
- **`RembgWarmupWorker` hereda de `_Worker`.** El boilerplate común pasa a la
  base con hook `_always_finished()`, conservando el contrato de `finished` y
  unificando logging, errores y anotaciones de `WorkerController`.
- **Submódulos de Canvas usan la API pública de edición.** `CanvasCrop` y
  `CanvasTransform` usan `apply_edit(...)` y `ImageCanvas.current_tool`; varias
  operaciones de selección pasan a `_requires_image` y el estado vacío informa
  de forma consistente.
- **API pública del paquete reducida.** Símbolos privados dejan de reexportarse
  desde `bgremover`; consumidores externos deben importarlos desde submódulos.
  `logger`, `LOG_FILENAME`, `REMBG_AVAILABLE` y `current_log_file` siguen siendo
  API pública; se elimina también la arista de test `MainWindow._recent_paths()`.

### Corregido

- **`apply_remove`/`apply_replace` ya no ocultan bugs reales.** El filtro estrecho
  deja propagar `AttributeError`, `AssertionError` y similares, pero sigue
  convirtiendo errores esperados de imagen/IO en mensajes de estado.
- **La ruta de carga síncrona usa las mismas protecciones que el worker.**
  `ImageCanvas.load_image` llama ahora a `open_validated_image`, de modo que
  archivos manipulados o formatos no soportados también terminan limpiamente con
  mensaje de estado en drag & drop.
- **License check estabilizado.** `coverage` queda fijado en
  `requirements/constraints.txt` (`==7.14.0`) para evitar drift de `LICENSES.md`
  por releases upstream.
- **License check endurecido contra drift de zona horaria.** `actions/checkout`
  usa `fetch-depth: 0` y el cálculo de fecha usa `TZ=UTC` con
  `--date=short-local`, encontrando el commit real y formateando la fecha de
  forma determinista.

### Eliminado

- **Código muerto eliminado de Canvas, Lasso y MainWindow.** Se eliminan
  `ImageCanvas._version`, `CanvasLasso.close_to_mask` y `MainWindow._btn_grp`.

## [2.2.0] – 2026-05-25

### Añadido

- **Snapshot reproducible de dependencias**
  (`requirements/constraints.txt`). El Makefile, el workflow de licencias
  y el build de la app macOS usan el mismo conjunto de constraints
  commiteado para instalaciones de tests, CI, licencias y App Bundle.
- **Doctor local del entorno de pruebas** (`make doctor`,
  `scripts/check_test_env.py`). Comprueba la versión de Python, las
  dependencias `[test]`, la instalación no editable del paquete, el
  console-script `bgremover` y Qt `offscreen` antes de que un fallo local
  aparezca tarde dentro de pytest.
- **Smoke test de CI para el arranque de la app**
  (`tests/test_app_smoke.py`). Las pruebas de UI existentes quedan
  excluidas de la CI vía `-m 'not ui'`, así que la CI nunca comprobaba
  si la aplicación llega a arrancar – justo la brecha por la que se
  colaron los fallos de inicio en macOS. Nuevo, sin el marcador `ui`
  (por lo que sí corre en la CI): `python -m bgremover` y el script de
  consola `bgremover` arrancan por completo desde un directorio de
  trabajo neutral (el nuevo hook de autotest `BGREMOVER_SMOKE_TEST`
  termina tras el primer ciclo del event loop con código 0); se
  comprueba que la configuración de plugins Qt produzca una ruta válida;
  se verifica la sintaxis shell de los scripts de arranque
  (`create_BgRemover_app.sh`, `BgRemover.command`, `diagnose_mac.sh`) y
  del lanzador incrustado en el paquete de app. Para ello se instala
  `zsh` en el job de CI de Linux.

### Cambiado

- **MainWindow se modulariza más.** La persistencia y la semántica de
  menú de "Abrir reciente" viven ahora en `bgremover/recent_files.py`;
  `MainWindow` solo delega la carga, los mensajes de estado y la
  integración en el menú Archivo.
- **Construcción de menú/acciones extraída de `MainWindow`.**
  `bgremover/menu_actions.py` construye la barra de menú, los `QAction`,
  los atajos y el submenú de archivos recientes; `MainWindow` solo
  entrega callbacks de dominio.
- **Panel derecho de pestañas extraído de `MainWindow`.**
  `bgremover/right_panel.py` construye las pestañas de selección,
  fondo, transformación y forma, incluyendo sliders, spinboxes y botones
  de panel; `MainWindow` solo entrega callbacks del canvas.
- **Orquestación de workers encapsulada fuera de `MainWindow`.**
  `bgremover/worker_controller.py` posee ahora los hilos de carga, IA y
  warmup, incluyendo referencias fuertes a workers, cableado `deleteLater`
  y shutdown compartido.

### Corregido

- **Enlaces de release/changelog corregidos a refs reales.**
  `[Unreleased]` ahora compara desde `v2.1.0`; `[2.1.0]` usa como base
  el commit de release 2.0.0 documentado, porque el repositorio no tiene
  un tag histórico `v2.0.0`.
- **Paquete de app: la detección de `bgremover` en el setup ya no
  depende del directorio de trabajo.** `create_BgRemover_app.sh`
  consideraba el venv como «listo» aunque `bgremover` no estuviera
  instalado allí: la comprobación `has_deps` se ejecutaba con `cwd`
  dentro de la carpeta del proyecto, y Python antepone automáticamente
  el directorio actual a `sys.path[0]` – así `import bgremover`
  encontraba el **directorio de fuentes** `bgremover/` del repo en
  lugar de una instalación real en el venv. El lanzador de la app
  arranca con otro `cwd`, no ve el directorio de fuentes y por eso
  informaba «Falta el paquete bgremover en el venv». `has_deps` y la
  comprobación final se ejecutan ahora desde `$HOME` (subshell
  `cd "$HOME"`), comprobando la misma realidad que el lanzador; si
  falta el paquete, se activa el camino rápido de pip install.
  `diagnose_mac.sh` también testea desde `$HOME` y muestra además
  `pip show bgremover` del venv de la app (prueba independiente del
  cwd de si/dónde está instalado el paquete).
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

- **Operaciones puras de imagen extraídas de `ImageCanvas`.**
  `bgremover/image_ops.py` contiene ahora eliminar/reemplazar fondo,
  guardar, rotar, reflejar, redondear esquinas y máscaras de crop como
  funciones PIL/NumPy sin Qt. `ImageCanvas` conserva estado de UI,
  undo/redo, señales y overlays; `tests/test_image_ops.py` comprueba
  directamente las operaciones de píxeles sin `QApplication`.
- **Documentación de recomendaciones actualizada al estado actual.**
  `RECOMMENDATIONS.md` y las versiones i18n incluyen ahora un bloque de
  estado de la ronda 6 para la serie reciente de PRs (#70, #72–#78) y
  marcan explícitamente los hallazgos antiguos del monolito como
  contexto histórico. `tests/test_recommendations_docs.py` protege este
  bloque.
- **Documentación de recursos sincronizada.** `RESOURCES.md` y las
  versiones i18n reflejan ahora el layout de paquete (`bgremover/` en
  lugar de `BgRemover.py`), los package-data bajo `bgremover/icons/`,
  el snapshot reproducible de constraints y los workflows de PR/full/
  licencias. Un test estático protege estas referencias para que no
  vuelvan a quedar obsoletas.
- **`make pr-check` hace más robusta la comprobación local de PR.** El
  target reinstala el paquete con `[test]`, ejecuta el doctor y después
  arranca `ruff`, `mypy` y `pytest`. El Makefile encuentra
  `.venv/bin/python` automáticamente y, si no existe, usa
  `python`/`python3`; GitHub PR CI y Full CI usan el mismo target. La
  configuración compartida de plugins Qt copia los plugins de plataforma
  al directorio temporal del sistema cuando hace falta, para que los
  runs headless locales en macOS no fallen al listar plugins dentro del
  path del proyecto.
- **CI ligera para PR añadida y documentación de pruebas sincronizada.**
  Los pull requests tienen ahora un workflow barato en Ubuntu/Python
  3.12 con `make pr-check`; la matriz completa Linux/macOS queda reservada
  para releases y ejecuciones manuales. Los workflows de pruebas
  instalan el paquete no editable para que los smoke tests de la app
  verifiquen la realidad instalada desde un `cwd` ajeno. `README`,
  READMEs i18n, `TESTING.md` y `Makefile` describen ahora el mismo
  flujo.
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

### Eliminado

- Eliminadas las constantes de stylesheet muertas `BTN_STYLE` y
  `GRP_STYLE`.

### Corregido

- `save_image()` ahora informa los fallos de E/S como mensaje de estado
  en lugar de propagarlos sin manejar.

### Documentación

- Se añadió la guía de instalación para Linux (`INSTALL_LINUX.md`):
  paquetes de sistema por distribución (apt/dnf/pacman), configuración
  del venv, script de arranque o entrada `.desktop` y resolución de
  problemas; enlazada en el README. Incluye una vía especialmente
  sencilla para Raspberry Pi OS (Desktop) sin venv/pip (PyQt6/Pillow/numpy
  como paquetes de sistema vía `apt`), con un paso opcional para añadir
  la IA.

## [2.0.0] – 2026-05-17

Primer estado de release 2.0.0 documentado. El repositorio no tiene un
tag Git histórico `v2.0.0`.

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

[Unreleased]: https://github.com/NikolayDA/picture_helper/compare/5fa8025dbabd997484e4739b1f547e9c59aed319...HEAD
[2.3.0]: https://github.com/NikolayDA/picture_helper/compare/da7186869e63cf9612897b31d80a84c1cc409062...5fa8025dbabd997484e4739b1f547e9c59aed319
[2.2.0]: https://github.com/NikolayDA/picture_helper/compare/4f4bfc2a3adf154d86d4aa2f46b0149bb863bc66...da7186869e63cf9612897b31d80a84c1cc409062
[2.1.0]: https://github.com/NikolayDA/picture_helper/compare/3eeb11c5783d5fc7ff4f6f945d2a407f8bb318b1...4f4bfc2a3adf154d86d4aa2f46b0149bb863bc66
[2.0.0]: https://github.com/NikolayDA/picture_helper/tree/3eeb11c5783d5fc7ff4f6f945d2a407f8bb318b1
