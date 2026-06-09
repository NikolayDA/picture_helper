[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · **Українська** · [简体中文](../zh/RECOMMENDATIONS.md)

# Аналіз Коду та Пріоритетні Рекомендації: BgRemover

## Шкала Пріоритетів

| Символ | Пріоритет | Значення |
|--------|-----------|----------|
| 🔴 | Критичний | Помилки, аварійні завершення або втрата даних |
| 🟠 | Високий | Чіткий вплив на надійність або підтримуваність |
| 🟡 | Середній | Корисне покращення якості, читабельності або тестованості |
| 🟢 | Низький | Опційне полірування або процесне покращення |

## Поточний Стан (2026-06-04)

Активний список аналізу коду порожній. Останню follow-up перевірку реалізовано
й покрито тестами; ruff, mypy та локальна suite залишаються baseline перед
новими PRs.

### Завершено З Останнього Review

- **N1/N2/N4/N5/N6/N7/N8** завершено: error path чарівної палички, ліміт
  розміру обертання, чесні розширення файлів, атомарне збереження, Qt-пакети
  CI, lazy import `rembg` і docstring `load_image`.
- **O2/O3/O4/O5/O6** реалізовано: Linux AppImage/`.deb`, release workflow,
  щотижнева повна матриця, `ui_smoke` у PR/Full CI та shortcuts інструментів
  із платформними підказками.
- **#164/#167/#168** завершено (PRs #172/#174/#173); решта триває сфокусовано
  в #176/#178.
- **2026-06-06 верифіковано як чисто закрите** (PRs #188–#193, кожен із
  регресійним тестом, `make check` зелений – 504 passed): **#163** (посилання
  CHANGELOG переведено на реальні, доступні на GitHub commit-SHA; додано чотири
  відсутні features 2.3.0 + запис idna/urllib3; реальні git-теги свідомо не
  створено), **#165/#180** (TESTING.md: фільтр `addopts`, `ui_smoke`,
  щотижневий schedule, shellcheck, `make coverage`), **#184** (load generation +
  повторна перевірка `content_revision` проти запізнілих async-loads), **#182**
  (`PIP_CONSTRAINT` вбудовано у збірку AppImage), **#183** (license-check лише
  для читання + ізольований job коментаря), **#177** (поведінкові assertions +
  новий `tests/test_history_popup.py`).

### Ще Відкрито

- **O1 🟠 — Додаткові runtime-мови.** Німецьку й англійську можна перемикати
  в app. Наявні мови документації (es/fr/uk/zh) ще не є runtime locales; за
  потреби додати їх key-by-key у `bgremover.i18n` і захистити parity/smoke
  tests.

## Відкриті GitHub-Issues — Оцінка Пріоритетів (2026-06-09)

Тепер **тринадцять** відкритих issues. Нове з останнього review: батч безпеки
`pip-audit` від 2026-06-07 (#200–#206) та знахідка мертвого коду (#199);
#195 закрито й верифіковано.

Тріаж батчу безпеки відносно реального стану проєкту
(`requirements/constraints.txt` + `pyproject.toml`):

- **#200 (setuptools) — єдина 🟠-знахідка** — `setuptools>=61` є **прямою
  build-залежністю** (`pyproject.toml`) і **не** запінено в `constraints.txt`.
  CRITICAL RCE.
- **#201 (wheel)/#202 (pip)** реально дієві: `wheel` не запінено,
  `pip` потрапляє в CI/dev безконтрольно.
- **#203 (cryptography)/#204 (pyjwt)** **не** є залежностями проєкту (суто
  транзитивні/системні) → інформативно, без зміни `constraints.txt`.
- **#205 (urllib3)/#206 (idna)** у проєкті вже **запінено чисто**
  (`urllib3==2.7.0`, `idna==3.15`); знахідка лише на рівні системи → закриваємо.

| # | Назва | Релевантність | Складність | Рекомендація |
|---|-------|---------------|------------|--------------|
| [#200](https://github.com/NikolayDA/picture_helper/issues/200) | setuptools 68.1.2 — CRITICAL/HIGH: RCE + path traversal | 🟠 Висока | 🟢 Низька | Готово до PR; пряма build-залежність — запінити `setuptools>=78.1.1` у `pyproject.toml` + `constraints.txt` |
| [#201](https://github.com/NikolayDA/picture_helper/issues/201) | wheel 0.42.0 — HIGH: path traversal (права файлів) | 🟡 Середня | 🟢 Низька | Готово до PR; запінити `wheel==0.46.2` у `constraints.txt` (об'єднати з #200) |
| [#202](https://github.com/NikolayDA/picture_helper/issues/202) | pip 24.0 — HIGH/MEDIUM: 5 CVE (path traversal, symlink) | 🟡 Середня | 🟢 Низька | Готово до PR; вимагати `pip>=26.1.2` у кроках setup CI + dev-доці |
| [#176](https://github.com/NikolayDA/picture_helper/issues/176) | Продовження код-рев'ю (Low): E741, check_untyped_defs, UX cancel_ai, shutdown_all | 🟡 Середня | 🟢 Низька | Готово до PR (з #167); `E741`/`check_untyped_defs` у `pyproject.toml` ще без змін |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | Аудит README: зламане посилання та внутрішній жаргон | 🟡 Середня | 🟢 Низька | Заблоковано: жаргон «Runde 5» прибрано; лишається лише URL клонування (рішення власника щодо видимості репо) |
| [#199](https://github.com/NikolayDA/picture_helper/issues/199) | Мертвий код (Low): `_redo_max` лише на запис у `canvas_history.py` | 🟢 Низька | 🟢 Низька | Готово до PR; видалити один рядок (модуль строго типізований — `make check`) |
| [#185](https://github.com/NikolayDA/picture_helper/issues/185) | Безпека: macOS-діагностика розкриває локальні шляхи + сирий хвіст логу (приватність) | 🟢 Низька | 🟡 Середня | Готово до PR; редагувати `$HOME`/шляхи + прапорець `--include-raw-logs` + shell-тест |
| [#178](https://github.com/NikolayDA/picture_helper/issues/178) | Продовження тест-аудиту (Low): відв'язати від приватних internals + дедуплікація | 🟢 Низька | 🟡 Середня | Готово до PR (з #168) |
| [#166](https://github.com/NikolayDA/picture_helper/issues/166) | Аудит коментарів: мовні невідповідності та дрібна неточність | 🟢 Низька | 🟢 Низька | Готово до PR; англійські docstrings у `right_panel.py`/`main_window.py` |
| [#203](https://github.com/NikolayDA/picture_helper/issues/203) | cryptography 41.0.7 — HIGH/MEDIUM: 6 CVE | 🟢 Низька | 🟢 Низька | Не залежність проєкту (транзитивна/системна) → інформативно, без зміни `constraints.txt` |
| [#204](https://github.com/NikolayDA/picture_helper/issues/204) | pyjwt 2.7.0 — HIGH/MEDIUM: 5 CVE | 🟢 Низька | 🟢 Низька | Не залежність проєкту → інформативно, без дії проєкту |
| [#205](https://github.com/NikolayDA/picture_helper/issues/205) | urllib3 2.6.3 — MEDIUM: 2 CVE | 🟢 Низька | 🟢 Низька | Без дії; проєкт уже пінить `urllib3==2.7.0` (чисто) → закриваємо |
| [#206](https://github.com/NikolayDA/picture_helper/issues/206) | idna 3.11 — MEDIUM: DoS через `idna.encode()` | 🟢 Низька | 🟢 Низька | Без дії; проєкт уже пінить `idna==3.15` (чисто) → закриваємо |

### Рекомендований Порядок PR

1. **#200** — запінити `setuptools>=78.1.1` у `pyproject.toml` (`[build-system]`) **та** `constraints.txt`. Найвищий пріоритет: CRITICAL RCE у прямій build-залежності.
2. **#201** — запінити `wheel==0.46.2` у `constraints.txt`; об'єднати з #200 в один PR пінінгу ланцюга постачання.
3. **#202** — вимагати `pip>=26.1.2` у кроках setup CI + dev-доці встановлення.
4. **#176** — Набір якості коду з #167: звузити `E741`, `check_untyped_defs` поступово, UX cancel_ai, обнулити thread-посилання у `shutdown_all`.
5. **#199** — видалити `_redo_max` (лише на запис) з `canvas_history.py` (тривіальний fix, регресія через `make check`).
6. **#166** — Мовне очищення docstrings як невеликий PR технічного обслуговування.
7. **#185** — Редагувати macOS-діагностику (`$HOME`/шляхи) + прапорець `--include-raw-logs` + shell-тест.
8. **#178** — Відв'язати тести від приватних internals + зменшити дублікати (з #168).
9. **#205/#206 закриваємо** — пінінг проєкту вже коректний (`urllib3==2.7.0`, `idna==3.15`); знахідки лише на рівні системи.
10. **#203/#204 як спостережні пункти** — не залежності проєкту; пінити лише якщо майбутня фіча введе їх напряму.
11. **#161 відкладено** — «Runde 5» зроблено; лишається тільки URL клонування (рішення власника щодо видимості репо).

## Попередні Раунди

- **2026-06-01, «modest-shannon» (A–E)** — 5 знахідок, усі завершені.
- **v2.2, «admiring-mayer» (#1–#15)** — зовнішній список, завершений або
  відхилений там, де це було хибне спрацювання.

Повні історичні знахідки та робочі журнали (раунди 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.uk.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.uk.md).
