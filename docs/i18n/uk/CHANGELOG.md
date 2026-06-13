[Deutsch](../../../CHANGELOG.md) · [English](../en/CHANGELOG.md) · [Español](../es/CHANGELOG.md) · [Français](../fr/CHANGELOG.md) · **Українська** · [简体中文](../zh/CHANGELOG.md)

# Changelog

Усі помітні зміни в BgRemover задокументовано в цьому
файлі. Формат орієнтується на
[Keep a Changelog](https://keepachangelog.com/de/1.1.0/); проєкт
дотримується [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

### Додано

- **Бенчмарк продуктивності конвеєра обробки зображень.**
  `scripts/benchmark.py` вимірює час обробки для кожного вихідного формату
  (PNG/JPEG/WebP/TIFF) реальними шляхами `image_ops`, зберігає датовані
  результати в `benchmarks/results/` і порівнює послідовні запуски; формати з
  регресією понад 10 % позначаються та за потреби повідомляються як issue на
  GitHub (`make bench` / `make bench-compare`). Щотижневий CI-workflow
  (`.github/workflows/benchmark.yml`) виконує запуск і порівняння на сталому
  обладнанні та записує результат назад як наступну базову лінію.

### Змінено

- **Оновлено залежності.** `idna` піднято до 3.15, а `urllib3` до 2.7.0;
  `LICENSES.md` синхронізовано з новим dependency snapshot.
- **Складальний бекенд закріплено проти CVE ланцюга постачання.** `setuptools`
  піднято до `>=78.1.1` у `pyproject.toml` (`[build-system]`) та
  `requirements/constraints.txt` (CVE-2024-6345 RCE, CVE-2025-47273 path
  traversal), а `wheel` до `==0.46.2` у `constraints.txt` (CVE-2026-24049). Тож
  ізольований збір wheel більше не може підтягнути вразливі складальні
  інструменти (#200, #201).
- **pip піднято до виправленої версії в CI/dev.** CI-воркфлоу, що
  встановлюють через pip (`ci.yml`, `pr-ci.yml`, `ui-nightly.yml`,
  `benchmark.yml`, `license-check.yml`), та веб-хук SessionStart піднімають
  `pip` до `>=26.1.2` перед встановленням, так само як dev-документація зі
  встановлення (`README.md`/`INSTALL_MAC.md`/`INSTALL_LINUX.md`). Закриває батч
  `pip-audit` із CVE path traversal, symlink і захоплення модулів; pip — це сам
  інструмент встановлення, тож його не можна закріпити через
  `constraints.txt` (#202).
- **Діагностика macOS редагує чутливі шляхи.** `diagnose_mac.sh` тепер типово
  замінює `$HOME` на `~`, скорочує решту шляхів `/Users/<name>` і замість
  останніх 40 сирих рядків логу виводить відфільтроване зведення помилок із
  редагованими шляхами — вивід можна безпечно додавати до баг-репортів. Повну
  діагностику (разом із сирим логом) дає новий прапорець
  `--include-raw-logs`; shell-тест (`tests/test_diagnose_mac.py`) гарантує,
  що домашній каталог і шляхи зображень не потрапляють до типового
  виводу (#185).

### Виправлено

- **Ліміт розміру вхідного файлу перед читанням.** `open_validated_image`
  тепер перевіряє вхідний файл через `os.fstat()` проти задокументованого
  байтового ліміту (`_MAX_INPUT_FILE_BYTES`, 512 МБ) **перш ніж** його вміст
  повністю читається в пам'ять; додатковий обмежений `read()` захищає від
  незвичних файлових об'єктів і зміни розміру між `fstat()` та `read()`
  (TOCTOU). Повідомлення розрізняє розмір файлу (МБ) і ліміт мегапікселів (MP).
  Синхронний та асинхронний шляхи завантаження використовують ту саму
  перевірку; наявний ліміт мегапікселів і захист TOCTOU збережено (#230).
- **Сесія інференсу rembg повторно використовується.** Warmup тепер створює
  рівно одну rembg/ONNX-сесію через `new_session()` і зберігає її на рівні
  модуля; кожен подальший `AIWorker` передає її в `remove(..., session=...)`
  замість повторної ініціалізації моделі. Створення потокобезпечне завдяки
  double-checked locking і виконується щонайбільше один раз упродовж кількох
  KI-викликів; невдала ініціалізація все одно повідомляє помилку worker і не
  лишає хибно «готового» стану. Оманливий коментар (нібито фіктивний `remove()`
  кешує сесію) виправлено принагідно (#229).

### Видалено

## [2.3.0] – 2026-06-04


### Додано

- **Покриття тестами збільшено до 88 % (друга хвиля, раніше 82 %).** Новий файл
  `tests/test_canvas_events.py` покриває обробники подій і логіку `canvas.py`:
  мишу, клавіатуру, колесо, drag, потоки результатів чарівної палички,
  налаштування інструментів, undo/redo/undo-to під час активного crop і guards
  без завантаженого зображення. `canvas.py` зростає з 64 % до 99 %, а
  `fail_under` — з 80 до 86.
- **Покриття тестами збільшено до 82 % (раніше 74 %).** Нові поведінкові тести
  покривають `tests/test_lasso.py`, `tests/test_canvas_crop.py`,
  `tests/test_viewport.py`, `tests/test_crop_overlay.py`,
  `tests/test_settings_schema.py` і `tests/test_settings_dialog.py`. Кілька
  модулів мають 100 %, `canvas_crop.py` — 98 %, а `fail_under` піднято з 68 до
  80.
- **i18n для ANLEITUNG.md.** Додано п'ять перекладів німецького посібника в
  `docs/i18n/{en,es,fr,uk,zh}/ANLEITUNG.md`; `tests/test_i18n_docs.py` тепер
  містить `"ANLEITUNG.md"`, а кожен i18n-заголовок пояснює, що `ANLEITUNG.pdf`
  генерується лише для німецького оригіналу.
- **Soft-drift тест `tests/test_i18n_sync.py`.** Порівнює ієрархію заголовків і
  кількість code-блоків у `CHANGELOG.md`, `INSTALL_MAC.md` і `INSTALL_LINUX.md`
  з німецькими оригіналами; відхилення дають читабельні попередження замість
  жорсткого падіння тестів.
- **`bgremover/status_messages.py` – централізовані status-повідомлення.** Усі
  видимі користувачу status-рядки з `canvas.py`, `canvas_crop.py` і
  `main_window.py` перенесено до `StatusMessages` як підготовку до майбутньої
  локалізації.
- **Runtime-i18n з підтримкою англійської.** Німецьку й англійську можна
  перемикати під час роботи; діалог налаштувань містить персистентний вибір
  мови з підказкою про перезапуск, а UI-рядки canvas, діалогів і правої панелі
  проходять через центральний шар перекладу.
- **Клавіатурні shortcuts для інструментів.** Інструменти редагування тепер
  можна перемикати з клавіатури; toolbar-tooltips і документація показують
  платформно коректні комбінації.
- **Linux AppImage packaging.** Release build створює AppImage як
  рекомендований шлях для кінцевих Linux-користувачів, включно зі скриптами
  пакування, CI-покриттям і нотатками встановлення.
- **Linux `.deb`, aarch64/Raspberry Pi і release workflow.** Linux-пакування
  розширено Debian-пакетами, підтримкою aarch64/Pi і відповідним release
  workflow.
- **Версія схеми QSettings.** Новий `bgremover/settings_schema.py` із
  `SCHEMA_VERSION = 1` і `migrate(settings)`; `MainWindow.__init__` запускає
  міграцію після створення `QSettings`. Покрито downgrade-захист, пошкоджені
  значення й тести в `tests/test_settings_schema.py`.
- **Runtime-тест для `RembgWarmupWorker`.** Нові тести в `tests/test_workers.py`
  і `tests/test_worker_controller.py` перевіряють, що warmup завжди емітить
  `finished`, а lifecycle thread завершується навіть коли `rembg_remove` падає
  при першому запуску.

### Змінено

- Очищено документацію й коментарі коду: застарілі PR/round-маркери прибрано
  з живих документів, macOS-нотатки встановлення оновлено, а рекомендації
  скорочено до поточного review/roadmap-стану.
- Версію проєкту піднято до 2.3.0 у метаданих пакета, AppStream, оглядах
  ліцензій і changelog-посиланнях.

- **Мову docstring уніфіковано.** `bgremover/image_ops.py`,
  `bgremover/recent_files.py` і `bgremover/worker_controller.py` переведено з
  англійських docstring на німецькі, узгоджено з рештою проєкту.
- **Документацію користувача для Linux-пакетів і налаштування мови оновлено.**
  README, `INSTALL_LINUX.md` і `ANLEITUNG.md` називають AppImage/`.deb`
  рекомендованим шляхом для Linux-користувачів і документують персистентну мову
  з підказкою про перезапуск; i18n-копії синхронізовано.
- **Хвиля code hygiene.** Version fallback читає `pyproject.toml`,
  `_paint_brush` отримує `additive` явно, `apply_remove`/`apply_replace` ловлять
  лише очікувані помилки, задокументовано глобальні ефекти й QSettings-випадки,
  `make clean` чистить більше артефактів, а опис проєкту відображає підтримку
  macOS/Linux.
- **Виділення чарівною паличкою більше не заморожує UI.** Flood-fill перенесено
  у `FloodFillWorker` на короткий `QThread` зі stale-перевіркою через
  `content_revision`; pan/zoom залишаються реактивними, а паралельний клік
  палички блокується status-повідомленням.
- **CI-матрицю розширено.** Full CI перевіряє Python 3.10, 3.11, 3.12 і 3.13 на
  Ubuntu та macOS.
- **`RembgWarmupWorker` успадковується від `_Worker`.** Спільний boilerplate
  перенесено в базу з hook `_always_finished()`, збережено контракт `finished` і
  уніфіковано logging, помилки та анотації `WorkerController`.
- **Canvas-субмодулі використовують публічну edit-API.** `CanvasCrop` і
  `CanvasTransform` використовують `apply_edit(...)` і
  `ImageCanvas.current_tool`; кілька selection-операцій переходять на
  `_requires_image`, а порожній стан повідомляє про відсутність зображення.
- **Публічну API пакета спрощено.** Приватні символи більше не re-export із
  `bgremover`; споживачі мають імпортувати їх із підмодулів. `logger`,
  `LOG_FILENAME`, `REMBG_AVAILABLE` і `current_log_file` залишаються публічними;
  тестовий край `MainWindow._recent_paths()` видалено.

### Виправлено

- **`apply_remove`/`apply_replace` більше не приховують справжні bugs.** Вузький
  фільтр пропускає `AttributeError`, `AssertionError` тощо, але очікувані
  image/IO-помилки й надалі перетворює на status-повідомлення.
- **Синхронний шлях завантаження використовує ті самі safeguards, що й worker.**
  `ImageCanvas.load_image` тепер викликає `open_validated_image`, тому
  пошкоджені файли й непідтримувані формати в drag & drop завершуються чистим
  status-повідомленням.
- **License check стабілізовано.** `coverage` зафіксовано в
  `requirements/constraints.txt` (`==7.14.0`), щоб upstream-релізи не ламали
  drift-порівняння `LICENSES.md`.
- **License check захищено від timezone drift.** `actions/checkout` використовує
  `fetch-depth: 0`, а дата рахується з `TZ=UTC` і `--date=short-local`, щоб
  знайти справжній commit і форматувати дату детерміновано.

### Видалено

- **Мертвий код видалено з Canvas, Lasso і MainWindow.** Видалено
  `ImageCanvas._version`, `CanvasLasso.close_to_mask` і `MainWindow._btn_grp`.

## [2.2.0] – 2026-05-25

### Додано

- **Відтворюваний snapshot залежностей**
  (`requirements/constraints.txt`). Makefile, license workflow і macOS
  app build використовують один і той самий зафіксований набір constraints
  для test-, CI-, license- та App Bundle-встановлень.
- **Локальний doctor тестового середовища** (`make doctor`,
  `scripts/check_test_env.py`). Перевіряє версію Python, залежності
  `[test]`, не-editable встановлення пакета, console-script `bgremover`
  і Qt `offscreen`, перш ніж локальний запуск впаде глибоко в pytest.
- **CI-smoke-тест запуску застосунку** (`tests/test_app_smoke.py`).
  Наявні UI-тести виключені з CI через `-m 'not ui'`, тож CI ніколи
  не перевіряла, чи застосунок взагалі запускається – саме та
  прогалина, через яку прослизнули збої запуску на macOS. Нове, без
  маркера `ui` (тобто виконується в CI): `python -m bgremover` і
  console-script `bgremover` повністю стартують з нейтрального
  робочого каталогу (новий hook самотестування `BGREMOVER_SMOKE_TEST`
  завершує після першого проходу event loop з кодом 0); перевіряється,
  що налаштування Qt-плагінів дає коректний шлях;
  перевіряється shell-синтаксис стартових скриптів
  (`create_BgRemover_app.sh`, `BgRemover.command`, `diagnose_mac.sh`)
  та лаунчера, вбудованого в App-бандл. Для цього в Linux-CI-job
  встановлюється `zsh`.

### Змінено

- **MainWindow додатково модульовано.** Персистентність і семантика меню
  «Відкрити нещодавні» тепер живуть у `bgremover/recent_files.py`;
  `MainWindow` лише делегує завантаження, повідомлення стану та
  інтеграцію в меню Файл.
- **Побудову меню/actions винесено з `MainWindow`.**
  `bgremover/menu_actions.py` будує рядок меню, `QAction`-и, shortcuts
  і підменю recent files; `MainWindow` лише передає доменні callbacks.
- **Праву панель вкладок винесено з `MainWindow`.**
  `bgremover/right_panel.py` будує вкладки вибору, фону, трансформації
  та форми, включно зі sliders, spinboxes і кнопками панелі; `MainWindow`
  лише передає callbacks полотна.
- **Оркестрацію worker-ів винесено з `MainWindow`.**
  `bgremover/worker_controller.py` тепер володіє потоками завантаження,
  ШІ та warmup, включно із сильними посиланнями на worker-и,
  `deleteLater`-зв'язками та спільним shutdown.

### Виправлено

- **Виправлено release/changelog-посилання на реальні refs.**
  `[Unreleased]` тепер порівнює від `v2.1.0`; `[2.1.0]` використовує
  документований 2.0.0 release-commit як базу, бо в репозиторії немає
  історичного тегу `v2.0.0`.
- **App-бандл: розпізнавання `bgremover` у setup більше не залежить
  від робочого каталогу.** `create_BgRemover_app.sh` вважав venv
  «готовим», хоча `bgremover` там не був встановлений: перевірка
  `has_deps` виконувалася з `cwd` у каталозі проєкту, а Python
  автоматично додає поточний каталог до `sys.path[0]` – тож
  `import bgremover` знаходив **каталог-джерело** `bgremover/` репо
  замість справжнього встановлення у venv. Лаунчер застосунку
  стартує з іншим `cwd`, не бачить каталог-джерело і тому повідомляв
  «Пакет bgremover відсутній у venv». `has_deps` і фінальна перевірка
  тепер виконуються з `$HOME` (підоболонка `cd "$HOME"`), тобто
  перевіряють ту саму реальність, що й лаунчер; якщо пакета бракує,
  спрацьовує швидкий шлях pip install. `diagnose_mac.sh` також тестує
  з `$HOME` і додатково показує `pip show bgremover` для venv
  застосунку (cwd-незалежний доказ, чи/куди встановлено пакет).
- **Шляхи запуску на macOS знову працюють.** Після зрізу на пакет
  (раунд 5) `BgRemover.command` все ще шукав уже відсутній файл
  `BgRemover.py` і виходив із «не знайдено»; німецький
  `INSTALL_MAC.md`, а також i18n-версії `INSTALL_LINUX.md` і
  `README.md` ще тримали частково старі команди (крок 15 раунду 5
  пропустив у glob-і німецький `INSTALL_MAC.md` та i18n-installation-
  доку, а також `Exec=python3 /ШЛЯХ/.../BgRemover.py` у i18n
  `.desktop`-фрагментах). Внаслідок цього на macOS жоден з трьох
  задокументованих шляхів запуску (App-бандл, подвійний клік на
  `.command`, термінал) не був надійно придатний до використання.
  Тепер `BgRemover.command` запускається через `python3 -m bgremover`
  і попередньо перевіряє `import bgremover` (інакше виводить чітку
  підказку щодо `create_BgRemover_app.sh`). INSTALL_MAC + всі i18n-
  документи відображають поточну модель пакета (включно з
  не-editable встановленням пакета у venv застосунку та пошуком
  ресурсів через `importlib.resources`).
- **`create_BgRemover_app.sh`: наявний venv мігрується чисто.** venv
  з епохи моноліту (з PyQt6/Pillow/numpy, але звичайно ще без
  `bgremover`) хибно вважався «ready», бо перевірка налаштування
  `has_deps` не тестувала `bgremover`. При повторному запуску
  встановлення пакета пропускалося — і лаунчер застосунку потім
  повідомляв під час виконання «Пакет bgremover відсутній у venv».
  Перевірка тепер також включає `import bgremover`; крім того, є
  швидкий шлях: якщо venv застосунку вже має PyQt6/Pillow/numpy,
  додається лише `pip install ".[ai]"` (секунди) замість того, щоб
  перебудовувати venv з усіма залежностями (хвилини).

### Змінено

- **Pure image-операції винесено з `ImageCanvas`.**
  `bgremover/image_ops.py` тепер містить видалення/заміну фону,
  збереження, обертання, віддзеркалення, заокруглення кутів і crop-
  маскування як Qt-free PIL/NumPy-функції. `ImageCanvas` зберігає UI-
  стан, undo/redo, сигнали та overlays; `tests/test_image_ops.py`
  перевіряє pixel-операції напряму без `QApplication`.
- **Документацію рекомендацій оновлено до поточного стану.**
  `RECOMMENDATIONS.md` та i18n-версії тепер містять status block раунду
  6 для нещодавньої серії PR (#70, #72–#78) і явно позначають старі
  висновки щодо моноліту як історичний контекст.
  `tests/test_recommendations_docs.py` захищає цей блок.
- **Синхронізовано документацію ресурсів.** `RESOURCES.md` та i18n-
  версії тепер відображають layout пакета (`bgremover/` замість
  `BgRemover.py`), package-data під `bgremover/icons/`, відтворюваний
  constraints snapshot і PR/full/license workflows. Статичний тест
  захищає ці посилання від повторного застарівання.
- **`make pr-check` робить локальну PR-перевірку надійнішою.** Target
  заново встановлює пакет із `[test]`, запускає doctor, а потім `ruff`,
  `mypy` і `pytest`. Makefile автоматично знаходить `.venv/bin/python`,
  а якщо його немає, переходить до `python`/`python3`; GitHub PR CI та
  Full CI використовують той самий target. Спільне налаштування Qt-
  плагінів за потреби копіює platform plugins у системний temp-каталог,
  щоб локальні headless-запуски на macOS не падали через listing
  plugins усередині шляху проєкту.
- **Додано легку PR CI та синхронізовано документацію тестів.** Pull
  request-и тепер отримують дешевий workflow Ubuntu/Python 3.12 з
  `make pr-check`; повна матриця Linux/macOS залишається для release та
  ручних запусків. Тестові workflow встановлюють пакет не-editable, щоб
  app smoke tests перевіряли встановлену реальність із чужого `cwd`.
  `README`, i18n README, `TESTING.md` і `Makefile` тепер описують один
  і той самий процес.
- **Моноліт → пакет (раунд 5).** Однофайловий `BgRemover.py`
  (3026 рядків) розділено на встановлюваний пакет `bgremover/`
  (14 модулів: `constants`, `image_utils`, `icons`, `theme`,
  `workers`, `crop`, `canvas`, `widgets`, `settings_dialog`,
  `logging_config`, `main_window`, `app`, `__main__`, `__init__`).
  Запуск через `python -m bgremover` або console-script
  `bgremover`; стара форма `python BgRemover.py` усунена без
  заміни. `BgRemover.py` видалено. Виконано в **13 механічних
  кроках**, кожен зі зеленим тестовим оракулом як шлюзом (140 unit
  + 16 UI тестів, ruff, mypy). Єдина навмисна, поведінково-нейтральна
  зміна коду: `make_tool_icon` тепер розв'язує іконки через
  `importlib.resources` із даних пакета (`bgremover/icons/`) замість
  `__file__`/`sys.argv`/`cwd` — контракт без змін. `pyproject.toml`,
  `Makefile`, CI workflow та macOS-скрипт збірки
  (`create_BgRemover_app.sh`) пристосовані у тому самому зрізі; venv
  встановлює пакет у режимі не-editable (зокрема package-data), тому
  застосунок незалежний від каталогу проєкту.
- Перехідні ре-експорти в `BgRemover.py` (фаза B) та всі імпорти
  `BgRemover` у тестах переведено на пакет у фінальному кроці.

## [2.1.0] – 2026-05-19

### Змінено

- Guard раннього виходу «зображення не завантажено» п'яти методів
  `ImageCanvas` (`apply_round_corners`, `apply_rotate`, `apply_flip`,
  `start_crop_circle`, `start_crop_ratio`) об'єднано в декоратор
  `@_requires_image` – раніше побайтово ідентичний блок зникає;
  поведінка незмінна (захищена наявним набором тестів).
- Фонові worker-и `AIWorker` та `ImageLoadWorker` тепер мають спільний
  базовий клас `_Worker`, який інкапсулює ідентичний потік
  `try/except → logger.exception → error.emit`; підкласи реалізують
  лише `_work()`. `RembgWarmupWorker` свідомо залишається самостійним
  (без сигналу `error`, `finished` завжди у `finally`).
- Зріз версії **2.1.0**: `pyproject.toml` і резервний `__version__` у
  `BgRemover.py` піднято до `2.1.0`; зміни, раніше зібрані під
  `[Unreleased]` (#48/#52/#53, INSTALL_LINUX, раунди 3/4), цим датовано
  як 2.1.0.

### Видалено

- Видалено мертві stylesheet-константи `BTN_STYLE` і `GRP_STYLE`.

### Виправлено

- `save_image()` тепер повідомляє про помилки вводу/виводу як статусне
  повідомлення, а не пропускає їх необробленими.

### Документація

- Додано інструкцію зі встановлення для Linux (`INSTALL_LINUX.md`):
  системні пакети для кожного дистрибутива (apt/dnf/pacman), налаштування venv,
  стартовий скрипт або запис `.desktop` та усунення несправностей; з посиланням у README.
  Включно з особливо простим способом для Raspberry Pi OS (Desktop)
  без venv/pip (PyQt6/Pillow/numpy як системні пакети через `apt`), з
  опційним кроком дооснащення ШІ.

## [2.0.0] – 2026-05-17

Перший задокументований release-стан 2.0.0. У репозиторії немає
історичного Git-тегу `v2.0.0`.

### Функції

- Видалення фону за допомогою ШІ через `rembg` (опційний extra `ai`) включно з
  фоновим прогріванням, щоб перший клік не блокував.
- Інструменти виділення: чарівна паличка (векторизований flood-fill із
  повзунком допуску), пензель, гумка та полігональне ласо; Shift/Ctrl
  для додавання чи віднімання виділення.
- Зробити фон прозорим або замінити кольором.
- Трансформації: обертання (кроки 90° та довільний кут), віддзеркалення,
  заокруглення кутів, обрізання в кількох форматах із сіткою за правилом третин.
- Історія зі скасуванням/повторенням (кнопки на панелі інструментів) і переходом до будь-якого
  попереднього кроку через плаваюче спливне вікно історії.
- Перетягування (Drag & Drop) та «Нещодавно відкриті» (10 записів), обидва через
  асинхронний worker завантаження — без зависання UI.
- Збереження у форматі PNG, JPEG, WebP або TIFF.
- Постійні налаштування (стандартні каталоги, бажаний
  формат файлів) через `QSettings`.
- Збірка App-бандла для macOS (`create_BgRemover_app.sh`) включно з ізольованим
  venv, обробкою Apple Silicon і встановленням іконок; підтримує Python
  3.10–3.15.

### Стабільність і якість

- Захищено потоки worker'ів (немає передчасного GC worker'а,
  чисте завершення потоку в `closeEvent`, race ШІ через монотонний
  лічильник версій полотна).
- Ліміт розміру зображення (40 МП) і захист від decompression bomb під час завантаження.
- Стек скасування з обмеженням пам'яті (256 МБ) з відстеженням байтів за O(1).
- Платформонезалежний шлях журналу (`bgremover.log` у каталозі даних застосунку).
- 108 тестів; `ruff` і `mypy` як кроки CI; CI на Ubuntu та macOS
  з Python 3.10 та 3.12.
- `__version__` зчитується з метаданих пакета (Single Source);
  версія з'являється в заголовку вікна.

### Документація та ліцензія

- Ліцензія **GPL-3.0-or-later** (`LICENSE`); зумовлена
  ліцензованим за GPL біндингом PyQt6.
- `RESOURCES.md` (усі бібліотеки/інструменти/ресурси разом із ліцензіями),
  `LICENSES.md` та автоматизований робочий процес ліцензій/відповідності.
- README з архітектурою, відомими обмеженнями та інструкцією зі
  встановлення; докладний `INSTALL_MAC.md`.

[Unreleased]: https://github.com/NikolayDA/picture_helper/compare/5fa8025dbabd997484e4739b1f547e9c59aed319...HEAD
[2.3.0]: https://github.com/NikolayDA/picture_helper/compare/da7186869e63cf9612897b31d80a84c1cc409062...5fa8025dbabd997484e4739b1f547e9c59aed319
[2.2.0]: https://github.com/NikolayDA/picture_helper/compare/4f4bfc2a3adf154d86d4aa2f46b0149bb863bc66...da7186869e63cf9612897b31d80a84c1cc409062
[2.1.0]: https://github.com/NikolayDA/picture_helper/compare/3eeb11c5783d5fc7ff4f6f945d2a407f8bb318b1...4f4bfc2a3adf154d86d4aa2f46b0149bb863bc66
[2.0.0]: https://github.com/NikolayDA/picture_helper/tree/3eeb11c5783d5fc7ff4f6f945d2a407f8bb318b1
