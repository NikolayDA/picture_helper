[Deutsch](../../../RESOURCES.md) · [English](../en/RESOURCES.md) · [Español](../es/RESOURCES.md) · [Français](../fr/RESOURCES.md) · **Українська** · [简体中文](../zh/RESOURCES.md)

# Використані ресурси

Цей документ перелічує **всі зовнішні ресурси**, які BgRemover
використовує або потребує: бібліотеки (пакети Python), інше програмне забезпечення
та інструменти, сторонній код, а також власні ресурси проєкту — кожен
із призначенням, ліцензією та джерелом отримання.

> Відомості про версії: «Мін.» походить із `pyproject.toml` (обов'язкова
> мінімальна вимога), «перевірено» — це базовий набір Python 3.12,
> зафіксований у `requirements/constraints.txt` для поточних локальних/CI
> перевірок. Визначальним завжди є відповідний доданий текст ліцензії
> пакета.

---

## 1. Залежності часу виконання (пакети Python)

Оголошено в `pyproject.toml` під `[project] dependencies`.

| Пакет | Призначення у програмі | Мін. | Перевірено | Ліцензія |
|-------|-------------------|------|---------|--------|
| **PyQt6** | Повний GUI (вікно, полотно, віджети, події, QSettings, QThread) | `>=6.5` | 6.11.0 | **GPL v3** або комерційна ліцензія Riverbank |
| **Pillow** (PIL) | Введення/виведення зображень, EXIF-transpose, обертання/віддзеркалення, маски/альфа, збереження (PNG/JPEG/WebP/TIFF) | `>=10` | 12.2.0 | HPND (також «MIT-CMU»; ліцензія PIL з відкритим кодом) |
| **NumPy** | Масиви пікселів, flood-fill, операції з масками | `>=1.24` | 2.4.5 | BSD-3-Clause |

Через PyQt6 додатково прив'язується фреймворк **Qt 6** (The Qt Company).
Сам Qt поширюється за LGPL v3 / GPL / комерційною ліцензією;
**біндинг PyQt6** — це GPL v3 — див. розділ 8.

## 2. Опційна залежність ШІ

Оголошено під `[project.optional-dependencies] ai` — потрібно лише для
автоматичного видалення фону (інструмент `rembg`):

| Ресурс | Призначення | Мін. | Перевірено | Ліцензія | Джерело |
|-----------|-------|------|---------|--------|-------|
| **rembg[cpu]** | Видалення фону на основі ШІ (`rembg.remove`) | `>=2.0` | 2.0.75 | MIT | PyPI |
| **onnxruntime** | Backend інференсу ONNX (транзитивна залежність `rembg[cpu]`) | (транзитивно) | 1.26.0 | MIT (Microsoft) | PyPI |
| **Модель U²-Net** (`u2net.onnx`) | Стандартна модель сегментації, яку rembg **завантажує під час виконання** (не входить до репозиторію) | – | – | Apache-2.0 (проєкт *U-2-Net*) | Завантаження rembg у каталог кешу користувача |

Без extras `ai` програма запускається нормально; кнопка ШІ тоді
вимкнена (`REMBG_AVAILABLE = False`).

## 3. Стандартна бібліотека Python

Частина CPython, **додаткове встановлення не потрібне**
(ліцензія: PSF License Agreement):

`sys`, `os`, `io`, `logging`, `collections.deque`, `pathlib.Path`,
`importlib.metadata`, `importlib.resources`, `contextlib`, `tempfile`.

## 4. Інструменти розробки та тестування

Оголошено під `[project.optional-dependencies] test`:

| Інструмент | Призначення | Мін. | Перевірено | Ліцензія |
|----------|-------|------|---------|--------|
| **pytest** | Запускач тестів | `>=8` | 9.0.3 | MIT |
| **pytest-qt** | Qt-фікстури (headless `offscreen`) | `>=4.4` | 4.5.0 | MIT |
| **ruff** | Лінтинг / перевірка стилю | `>=0.6` | 0.15.13 | MIT |
| **mypy** | Статична перевірка типів (крок CI) | `>=1.10` | 2.1.0 | MIT |
| **packaging** | Розбір dependency constraints у тестах | `>=24` | 24.0 | Apache-2.0 або BSD-2-Clause |

Опційні інструменти документації/PDF оголошені під
`[project.optional-dependencies] docs`:

| Інструмент | Призначення | Мін. | Ліцензія |
|----------|-------|------|--------|
| **Markdown** | Markdown → HTML для `ANLEITUNG.pdf` | `>=3.5` | BSD |
| **WeasyPrint** | PDF-рендеринг з HTML/CSS | `>=61` | BSD-3-Clause |
| **fonttools** | Інспекція шрифтів для генерації PDF | `>=4.0` | MIT |

У Linux генерація PDF також потребує шрифтів DejaVu та
Pango/Cairo/GDK-Pixbuf (пакети дистрибутива). У macOS генератор
використовує системні шрифти Arial/Courier New; встановіть Pango
командою `brew install pango`.

## 5. Інструменти збірки та розповсюдження (macOS)

Потрібні скрипту App-бандла `create_BgRemover_app.sh`. Він **не**
бандлить жодну з цих програм, а викликає їх через систему:

| Інструмент | Призначення | Походження |
|----------|-------|----------|
| `python3` + `venv` + `pip` | Створити ізольоване venv, встановити залежності з `requirements/constraints.txt` | Python / PyPA |
| `setuptools` (build-backend) | Пакування згідно з `[build-system]` (`>=61`) | MIT |
| `/usr/bin/arch`, `uname` | Примусово застосувати нативну архітектуру CPU (Apple Silicon) | macOS |
| `iconutil` | Створити іконку застосунку `.icns` з iconset (резерв: PNG) | macOS |
| `osascript` | Показати повідомлення про помилки лаунчера застосунку | macOS |
| Стандартні інструменти оболонки | `mkdir`, `cp`, `cat`, `command` тощо | POSIX/macOS |

`BgRemover.command` — це доданий стартер подвійного кліку (власний
код проєкту).

## 6. Continuous Integration

Визначено у `.github/workflows/pr-ci.yml`, `.github/workflows/ci.yml`,
`.github/workflows/ui-nightly.yml` та `.github/workflows/license-check.yml`.
Pull request запускає легкий job на Ubuntu/Python 3.12; повна матриця
працює на Ubuntu + macOS з Python 3.10–3.13 на тезі версії (кандидат на
release), при release або вручну; `ui-nightly.yml` щоночі запускає
UI-тести взаємодії; workflow ліцензій генерує звіт про залежності/ліцензії.

| Ресурс | Призначення | Ліцензія |
|-----------|-------|--------|
| `actions/checkout@v5` | Вивантаження репозиторію | MIT |
| `actions/setup-python@v6` | Налаштування Python + кеш Pip | MIT |
| `actions/upload-artifact@v4` | Завантаження артефактів звіту про ліцензії | MIT |
| `actions/github-script@v7` | Коментування короткого звіту про ліцензії в pull request | MIT |
| `pip-licenses` | Сирий dump ліцензій установлених пакетів | MIT |
| `requirements/constraints.txt` | Відтворюваний dependency snapshot для локальних перевірок, CI, звіту ліцензій та App Bundle | Файл проєкту |
| Системні бібліотеки Qt через `apt` (Linux) | Headless-середовище виконання Qt: `libegl1`, `libfontconfig1`, `libxkbcommon0`, `libdbus-1-3`, `libxcb-*` | спаковані дистрибутивом, різні пермісивні/copyleft-ліцензії (Mesa, fontconfig, libxkbcommon, libxcb, dbus …) |

## 7. Власні ресурси проєкту

Власна робота проєкту, охоплена ліцензією проєкту
(GPL-3.0-or-later, див. `LICENSE`):

- **Вихідний код**: інстальований пакет `bgremover/`, набір тестів під
  `tests/` та скрипти проєкту під `scripts/`.
- **Іконки панелі інструментів/вкладок**: `bgremover/icons/*.png` (`ai`, `bg`, `brush`,
  `clear_sel`, `close`, `eraser`, `form`, `open`, `redo`, `restore`,
  `save`, `transparency`, `undo`, `wand`). Завантажуються функцією
  `make_tool_icon()` через `importlib.resources` як дані пакета.
- **Намальовані векторні іконки**: Якщо PNG не вдається, `make_tool_icon()`
  програмно малює іконку за допомогою `QPainter`
  (функції `_draw_*_icon`) — без зовнішнього ресурсу.
- **Іконка застосунку**: `BgRemover_icon.png` (джерело для macOS-`.icns`).
- **Курсори**: малюються під час виконання (`make_wand_cursor`,
  `make_brush_cursor`, `make_eraser_cursor`) — без зовнішніх файлів.

У репозиторій **не вбудовано стороннього вихідного коду**
(немає `vendor/` чи `third_party/`); зовнішня функціональність
отримується винятково через перелічені вище пакети.

## 8. Сумісність ліцензій (примітка)

BgRemover розповсюджується за **GPL-3.0-or-later** (`LICENSE`). Цей вибір
зумовлений **PyQt6**: біндинг ліцензований за GPL-v3 (або
комерційно), тому застосунок, що розповсюджується як ціле —
особливо зібраний `BgRemover.app` — має відповідати GPL.
Решта залежностей часу виконання/ШІ (Pillow HPND, NumPy BSD, rembg MIT,
onnxruntime MIT, U²-Net Apache-2.0) сумісні з GPL-v3.

**Пермісивна** модель ліцензування (MIT/Apache-2.0) була б можлива лише, якби
PyQt6 замінили на ліцензований за LGPL-v3 **PySide6**.

---

*Примітка щодо супроводу:* У разі змін у `pyproject.toml`,
`requirements/constraints.txt`, `.github/workflows/pr-ci.yml`,
`.github/workflows/ci.yml`, `.github/workflows/ui-nightly.yml`, `.github/workflows/license-check.yml`,
`create_BgRemover_app.sh` або даних пакета під `bgremover/icons/`
оновлюйте, будь ласка, цей документ разом із ними.
