[Deutsch](../../../INSTALL_LINUX.md) · [English](../en/INSTALL_LINUX.md) · [Español](../es/INSTALL_LINUX.md) · [Français](../fr/INSTALL_LINUX.md) · **Українська** · [简体中文](../zh/INSTALL_LINUX.md)

# BgRemover – встановлення під Linux

Коротка інструкція зі встановлення та запуску BgRemover із GitHub —
як із гілки `main`, так і з гілки функції (наприклад,
щоб протестувати відкритий pull request перед злиттям).

> App-бандл macOS (`create_BgRemover_app.sh`) специфічний для macOS.
> Під Linux BgRemover працює через прямий запуск
> `python3 -m bgremover` з віртуального середовища (venv) — опційно
> з десктопним стартером для подвійного кліку (див. нижче).

## Вимоги

> **Raspberry Pi OS (Desktop)?** Тоді скористайтеся значно простішим способом
> [нижче](#raspberry-pi-os-desktop--простий-спосіб) —
> повністю без venv і pip. Наступний розділ стосується загального
> Linux.

- **Дистрибутив Linux із десктопом** (X11 або Wayland)
- **Python 3.10 або новіший** — перевірте за допомогою:
  ```bash
  python3 --version
  ```
- **git** і модуль **venv** (`python3-venv`)
- **Системні бібліотеки Qt** для PyQt6 — wheels PyQt6 містять сам Qt,
  але потребують деяких системних бібліотек X11/XCB. Без них
  GUI запускається з помилкою *«qt.qpa.plugin: Could not load the Qt
  platform plugin xcb»*.

### Встановлення системних пакетів

**Debian / Ubuntu / Linux Mint** (`apt`):
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git \
  libegl1 libgl1 libfontconfig1 libxkbcommon0 libxkbcommon-x11-0 \
  libdbus-1-3 libxcb-cursor0 libxcb-icccm4 libxcb-image0 \
  libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 \
  libxcb-xinerama0 libxcb-xkb1
```
(`libxcb-cursor0` потрібен Qt 6.5+ для плагіна `xcb`, зокрема під
Ubuntu 24.04.)

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

## Raspberry Pi OS (Desktop) — простий спосіб

На **Raspberry Pi OS «Bookworm» Desktop** (Debian 12, рекомендовано 64-бітний)
встановлення значно простіше: PyQt6, Pillow та
numpy доступні як готові системні пакети через `apt`. **Не потрібні
venv, `pip` та editable-встановлення** — BgRemover працює
безпосередньо з клону. Пакет `python3-pyqt6` автоматично підтягує потрібні
бібліотеки Qt6/XCB як залежність (довгий
список XCB вище не потрібен).

```bash
sudo apt update
sudo apt install -y git python3-pyqt6 python3-numpy python3-pil
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m bgremover
```

Ось і все — головне вікно відкриється. Ручні інструменти
(чарівна паличка, пензель/гумка, обрізання, обертання, віддзеркалення, заокруглення
кутів) працюють повністю. **Видалення фону за допомогою ШІ
в цьому мінімальному встановленні вимкнено** (кнопка ШІ
неактивна) — за потреби можна опційно дооснастити (див. нижче).

Оновлювати пізніше просто через `git pull` у теці проєкту;
повторний крок встановлення не потрібен.

### Опційно: запуск із меню застосунків

Створіть файл `~/.local/share/applications/bgremover.desktop` і
замініть `/PFAD/ZU/picture_helper` на абсолютний шлях до проєкту:
```ini
[Desktop Entry]
Type=Application
Name=BgRemover
Comment=Hintergrund entfernen und Bilder bearbeiten
Exec=python3 -m bgremover
Path=/PFAD/ZU/picture_helper
Icon=/PFAD/ZU/picture_helper/BgRemover_icon.png
Categories=Graphics;Photography;
Terminal=false
```
Після цього BgRemover з'являється в меню застосунків і запускається по кліку —
без venv чи скрипта-обгортки.

### Опційно: дооснащення видалення фону за допомогою ШІ

> **Примітка:** На Raspberry Pi ШІ (`rembg` +
> `onnxruntime`) **значно повільніший і вимагає більше пам'яті**. Рекомендовано
> лише на **64-бітному Raspberry Pi OS** (`uname -m` → `aarch64`) і
> Pi 4/5 з достатньою кількістю RAM (≥ 4 ГБ). На 32-бітному (`armv7l`/armhf), як правило,
> немає відповідних wheels `onnxruntime` — там ШІ краще
> не використовувати.

Оскільки `rembg` доустановлюється через pip, для цього використовуйте venv **з доступом
до системних пакетів Qt**:
```bash
cd picture_helper
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install "rembg[cpu]"
python3 -m bgremover
```
`--system-site-packages` робить встановлені через `apt`
PyQt6/Pillow/numpy видимими у venv, тож доустановлюються лише `rembg` і
`onnxruntime`. Під час найпершого кліку ШІ `rembg` одноразово завантажує
свою модель (кілька сотень МБ, кеш у `~/.u2net`).
Майбутні запуски тоді з venv: `source .venv/bin/activate` і
`python3 -m bgremover`.

## Швидкий старт із `main`

На сучасному Linux системні встановлення Python блокують `pip install`
згідно з PEP 668 («externally-managed-environment»). Тому встановлення відбувається в
ізольованому venv:

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install -e ".[ai]"
python3 -m bgremover
```

- `.[ai]` встановлює `rembg[cpu]` включно з `onnxruntime`
  (видалення фону за допомогою ШІ).
- Без функції ШІ достатньо: `python3 -m pip install -e .`

У новій оболонці перед запуском знову активуйте venv:
```bash
cd picture_helper
source .venv/bin/activate
python3 -m bgremover
```

## Варіанти запуску

| Варіант | Команда / дія | Результат |
|----------|-----------------|----------|
| **A – термінал (рекомендовано)** | активувати venv, потім `python3 -m bgremover` | Прямий запуск із каталогу проєкту. |
| **B – стартовий скрипт** | `./bgremover.sh` (див. нижче) | Автоматично активує venv і запускає застосунок. |
| **C – меню застосунків** | запис `.desktop` (див. нижче) | Запуск подвійним кліком / з меню застосунків. |

### B – стартовий скрипт

Створіть файл `bgremover.sh` у каталозі проєкту:
```bash
#!/usr/bin/env bash
cd "$(dirname "$0")" || exit 1
source .venv/bin/activate
exec python3 -m bgremover "$@"
```
Зробіть виконуваним і запустіть:
```bash
chmod +x bgremover.sh
./bgremover.sh
```

### C – запис Desktop (меню застосунків)

Створіть файл `~/.local/share/applications/bgremover.desktop` і
замініть `/PFAD/ZU/picture_helper` на абсолютний шлях до проєкту:
```ini
[Desktop Entry]
Type=Application
Name=BgRemover
Comment=Hintergrund entfernen und Bilder bearbeiten
Exec=/PFAD/ZU/picture_helper/bgremover.sh
Icon=/PFAD/ZU/picture_helper/BgRemover_icon.png
Categories=Graphics;Photography;
Terminal=false
```
Потім оновіть базу даних desktop (опційно):
```bash
update-desktop-database ~/.local/share/applications 2>/dev/null || true
```
Тепер BgRemover з'являється в меню застосунків.

## Встановлення з гілки (тестування відкритих PR)

Назви PR-гілок наведено у відповідному pull request на GitHub
(«… wants to merge … from **`<branch>`**»).

**Варіант 1 – у наявному каталозі клону:**
```bash
cd picture_helper
git fetch origin
git branch -r                       # показати доступні гілки
git checkout <branch>
source .venv/bin/activate
# потрібно лише, якщо змінилися залежності:
python3 -m pip install -e ".[ai]"
python3 -m bgremover
```

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
`pyproject.toml` змінилися.

## Усунення несправностей

- **`qt.qpa.plugin: Could not load the Qt platform plugin "xcb"`** →
  Відсутні системні бібліотеки Qt. Доустановіть пакети з розділу
  *«Встановлення системних пакетів»* (зокрема
  `libxcb-cursor0` під Ubuntu 24.04). Яка саме бібліотека відсутня,
  покаже:
  ```bash
  QT_DEBUG_PLUGINS=1 python3 -m bgremover 2>&1 | grep -i "cannot\|not found"
  ```
- **`error: externally-managed-environment` при `pip install`** → PEP
  668: не встановлюйте в системний Python, а у venv (див.
  Швидкий старт). Модуль venv відсутній? → `sudo apt install python3-venv`.
- **«python3: command not found» або версія < 3.10** → встановіть актуальний
  Python через менеджер пакетів дистрибутива (код
  використовує анотації типів PEP-604, як-от `QThread | None`; Python 3.9
  не спрацює).
- **Wayland: вікно/масштабування виглядає неправильно** → для проби перейдіть на
  плагін X11 (XWayland):
  ```bash
  QT_QPA_PLATFORM=xcb python3 -m bgremover
  ```
- **Помилка pip під час встановлення** → в активному venv спершу оновіть
  pip, потім повторіть команду встановлення:
  ```bash
  python3 -m pip install --upgrade pip
  ```
- **Перший клік ШІ триває довго** → Найпершого разу `rembg`
  завантажує свою модель (кілька сотень МБ, одноразово, кеш у
  `~/.u2net`). Рядок стану показує «🤖 Завантаження моделі ШІ…»
  а потім «🤖 ШІ готовий».
- **Застосунок запускається без ШІ / «No onnxruntime backend found»** →
  Extra `ai` не було встановлено. Доустановіть у venv:
  ```bash
  python3 -m pip install "rembg[cpu]"
  ```
- **Raspberry Pi: `Unable to locate package python3-pyqt6`** → Старіші
  версії Raspberry Pi OS (Bullseye) постачають лише PyQt5. Оновіть до
  «Bookworm» (або новішої) — або скористайтеся загальним
  шляхом venv/pip вище.
- **Raspberry Pi OS «Bookworm» (Pi 4/5) використовує Wayland** → У разі проблем
  із вікном чи масштабуванням для проби перейдіть на плагін X11:
  `QT_QPA_PLATFORM=xcb python3 -m bgremover` (див. примітку про Wayland
  вище).
- **Діагностика помилок** → Перегляньте файл журналу
  `~/.local/share/BgRemover/bgremover.log` (трасування стека та
  повідомлення про стан). Під час запуску з термінала повідомлення про
  помилку додатково з'являється безпосередньо в консолі.
