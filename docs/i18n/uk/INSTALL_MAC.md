[Deutsch](../../../INSTALL_MAC.md) · [English](../en/INSTALL_MAC.md) · [Español](../es/INSTALL_MAC.md) · [Français](../fr/INSTALL_MAC.md) · **Українська** · [简体中文](../zh/INSTALL_MAC.md)

# BgRemover – встановлення на Mac

Коротка інструкція зі встановлення та запуску BgRemover із GitHub —
як із гілки `main`, так і з гілки функції (наприклад,
щоб протестувати відкритий pull request перед злиттям).

## Вимоги

- **macOS**
- **Python 3.10 або новіший** — перевірте за допомогою:
  ```bash
  python3 --version
  ```
- **git**

> **Примітка щодо ШІ:** Основний застосунок працює на Python 3.10+.
> Видалення фону за допомогою ШІ (`.[ai]`) потребує **Python 3.11 або новішого**
> (поточні builds `onnxruntime` та `rembg` орієнтовані на Python 3.11+).

Якщо Python або git відсутні, найпростіше через [Homebrew](https://brew.sh):
```bash
brew install python git
```

## Швидкий старт із `main`

**Рекомендовано** скрипт App-бандла — він використовує окреме venv
застосунку, встановлює туди поточний checkout у не-editable режимі
(включно з іконками панелі інструментів), коректно обробляє Apple
Silicon і намагається встановити також залежності для ШІ:

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
bash create_BgRemover_app.sh
```

Якщо створюється нове venv застосунку, підтвердьте повідомлення
клавішею **Enter**; після цього запустіть `BgRemover.app` у
`~/Applications` подвійним кліком.

**Прямий запуск із термінала** — на сучасному macOS у venv, оскільки
системний Python блокує `pip install` згідно з PEP 668:

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install --upgrade "pip>=26.1.2"
python3 -m pip install -c requirements/constraints.txt -e ".[ai]"
python3 -m bgremover
```

- `.[ai]` встановлює `rembg[cpu]` включно з `onnxruntime` (видалення фону за допомогою ШІ).
- Без функції ШІ достатньо: `python3 -m pip install -c requirements/constraints.txt -e .`

## Варіанти запуску

Після встановлення є три способи запустити програму:

| Варіант | Команда / дія | Результат |
|----------|-----------------|----------|
| **A – застосунок macOS (рекомендовано)** | `bash create_BgRemover_app.sh` | Підтримує окреме venv застосунку, встановлює туди поточний checkout у не-editable режимі, намагається встановити залежності для ШІ, копіює іконки та створює самостійний `BgRemover.app` у `~/Applications`. Карантин видаляється автоматично; проєкт може залишатися в `~/Documents`. |
| **B – подвійний клік** | подвійний клік на `BgRemover.command` у Finder | Запускається у вікні термінала; автоматично використовує створене скриптом App-venv (файл уже виконуваний). |
| **C – термінал** | у venv: `python3 -m bgremover` | Прямий запуск (налаштування venv див. у Швидкому старті вище). |

## Встановлення з гілки (тестування відкритих PR)

Назви PR-гілок наведено у відповідному pull request на GitHub
(«… wants to merge … from **`<branch>`**»).

**Варіант 1 – у наявному каталозі клону:**
```bash
cd picture_helper
git fetch origin
git branch -r                       # показати доступні гілки
git checkout <branch>
# у venv (див. Швидкий старт); потрібно лише, якщо змінилися залежності:
python3 -m pip install --upgrade "pip>=26.1.2"
python3 -m pip install -c requirements/constraints.txt -e ".[ai]"
python3 -m bgremover
```

Альтернативно на гілці можна просто виконати
`bash create_BgRemover_app.sh` — це повторно встановить поточний
checkout у venv застосунку й автоматично подбає про залежності.

**Варіант 2 – клонувати гілку напряму:**
```bash
git clone --branch <branch-name> \
  https://github.com/NikolayDA/picture_helper.git
```

## Оновлення / зміна гілки

```bash
git checkout main && git pull          # найновіша головна версія
git checkout <branch> && git pull      # оновити певну гілку
```

Editable-встановлення (`pip install -e`) **не** потрібно
виконувати повторно після `git pull` — окрім випадку, коли залежності в
`pyproject.toml` або `requirements/constraints.txt` змінилися.

Якщо ви використовуєте `BgRemover.app`, після оновлення або зміни гілки
повторно виконайте `bash create_BgRemover_app.sh`. Скрипт автоматично
оновить копію пакета в окремому venv застосунку.

## Усунення несправностей

- **Застосунок не запускається / подвійний клік нічого не дає** → Починаючи з v3
  застосунок показує діалог помилки з «Відкрити журнал». Найчастіша причина:
  `PyQt6` не встановлено в тому Python, який використовує застосунок
  (наприклад, тому що `pip install` пішов у venv чи інший Python,
  або Homebrew-Python блокує `pip install` згідно з PEP 668). Розв'язання:
  виконайте `bash create_BgRemover_app.sh` повторно і дозвольте створити venv
  (підтвердьте пропозицію клавішею Enter) — скрипт тоді встановить
  залежності у venv під
  `~/Library/Application Support/BgRemover/venv` і запече цей Python
  у застосунок.
- **`[Errno 1] Operation not permitted` під час доступу до проєкту**
  → Захист даних macOS (TCC). Якщо проєкт лежить у `~/Documents`,
  `~/Desktop`, `~/Downloads` або iCloud Drive, запущений із
  Finder `.app` не може там читати. Пакетний layout це вирішує:
  `create_BgRemover_app.sh` встановлює пакет
  `bgremover` **не-editable** у venv під
  `~/Library/Application Support/BgRemover/venv` (власна копія коду
  разом із `icons/` як package-data), застосунок таким чином не
  залежить від каталогу проєкту. Fix: виконайте
  `bash create_BgRemover_app.sh` один раз знову. (Альтернативно
  перемістіть проєкт, наприклад, у `~/picture_helper` і виконайте
  скрипт там знову.)
- **`numpy ... incompatible architecture (have 'arm64', need 'x86_64')`**
  → Apple Silicon: у `~/Library/Python/...` лежить пакет чужої архітектури,
  який «протікає» в Python з невідповідною архітектурою. Лаунчер
  встановлює `PYTHONNOUSERSITE=1` (user-site
  ігнорується), примусово застосовує нативну архітектуру CPU і обов'язково
  використовується ізольоване venv. Розв'язання: найкраще спершу встановити нативний
  Python, потім зібрати наново:
  ```bash
  brew install python
  bash create_BgRemover_app.sh   # підтвердьте запит про venv клавішею Enter
  ```
- **Побачити помилку напряму (ручна діагностика)** → Запустіть лаунчер у терміналі,
  тоді з'явиться справжнє повідомлення про помилку:
  ```bash
  ~/Applications/BgRemover.app/Contents/MacOS/BgRemover
  ```
  Очікувано за відсутніх пакетів: `ModuleNotFoundError: No module named 'PyQt6'`.
- **«python3: command not found»** → `brew install python`
- **Помилка pip під час встановлення** → спершу оновіть pip:
  ```bash
  python3 -m pip install --upgrade "pip>=26.1.2"
  ```
  потім виконайте команду встановлення повторно.
- **Перший клік ШІ триває довго** → Найпершого разу `rembg`
  завантажує свою модель (кілька сотень МБ, одноразово, кеш у
  `~/.u2net`). Рядок стану показує «🤖 Завантаження моделі ШІ…»
  а потім «🤖 ШІ готовий».
- **Gatekeeper: «неперевірений розробник»** → Клік правою кнопкою на
  `BgRemover.app` → **Відкрити**. Скрипт збірки вже видаляє
  карантин через `xattr`, втім, у разі сумніву все одно достатньо
  відкриття правою кнопкою.
- **Застосунок аварійно завершується з «No onnxruntime backend found»** → Новіші
  версії `rembg` більше не постачають backend. Наразі виправлено
  (extra `ai` підтягує `rembg[cpu]`/`onnxruntime`; якщо його все одно немає,
  застосунок запускається без ШІ замість аварійного завершення). Розв'язання: один раз
  зберіть наново `bash create_BgRemover_app.sh` — або доустановіть у venv:
  `"~/Library/Application Support/BgRemover/venv/bin/python3" -m pip install "rembg[cpu]"`.
- **`.app` виглядає інакше, ніж `BgRemover.command`** → Старіший бандл
  без іконок панелі інструментів (застосунок використовував намальовані
  замінні іконки). Іконки є `package-data` у `bgremover/icons/`, тож
  автоматично потрапляють у venv при `pip install` і завантажуються через
  `importlib.resources`; один
  раз зберіть наново `bash create_BgRemover_app.sh`.
- **Діагностика помилок** → Лаунчер бандла записує діагностику запуску в
  `~/Library/Application Support/BgRemover/bgremover.log`. Внутрішній
  журнал виконання може лежати у вкладеному каталозі; точний шлях
  показано в `Інструменти → Налаштування… → Файл журналу`.
