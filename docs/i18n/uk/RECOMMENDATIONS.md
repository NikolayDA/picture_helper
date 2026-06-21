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

Активний список аналізу коду порожній. Ruff, mypy та локальний набір тестів
залишаються базовою перевіркою перед новими PR.

### Завершено З Останнього Review

- **N1/N2/N4/N5/N6/N7/N8** завершено: шляхи помилок, ліміт розміру,
  розширення, атомарне збереження, Qt-пакети CI, lazy import і docstring.
- **O2/O3/O4/O5/O6** реалізовано: Linux-пакети, release workflow, повна
  матриця, `ui_smoke` і платформні shortcuts.
- Знахідки **#163–#206** закрито в задокументованих PR і захищено
  регресійними тестами або перевірками CI.
- PR **#263–#269** закрили **#257, #258, #234 + #259, #248 + #260, #231** і
  **#249**; **#261** вирішено через PR #268 і закрито.
- PR **#274** закрив **#232**: `import bgremover` більше не завантажує Qt-стек
  завдяки lazy exports PEP 562; це покриває регресійний тест у підпроцесі.
- Хвиля PR **#280–#284** додала тижневий benchmark, реалізувала три знахідки —
  **#235** (спільний бюджет undo/redo, PR #281), **#275** (локалізоване
  повідомлення про мегапікселі, PR #282) і **#270** (підпроцес rembg/ONNX через
  `ai_process.py`, PR #283) — і оновила дорожню карту (PR #284). **#235, #270 і
  #275 вже закрито.**
- Два post-merge Codex-наслідки з #283 і #264 також виправлені **й закриті**:
  **#285** (надійність/пам'ять підпроцесу rembg, PR #289) і **#286** (піки
  пам'яті в обмеженому читанні файлу, PR #290).

- **N9 ✅ — Проєктно-шарова модель даних (епік #329) реалізована.** Qt-незалежна
  доменна модель (#330), шароусвідомлена історія (#331), композитне полотно
  (#332), формат `.bgrproj` (#333), панель шарів/меню проєкту (#334) та міграція/
  інтеграція (#335) — паритет одного зображення збережено, `make check`/`make ui`
  зелені.

### Ще Відкрито

- **O1 🟠 — Додаткові runtime-мови.** Німецьку й англійську можна перемикати
  в застосунку. Мови документації es/fr/uk/zh ще не є runtime locales;
  за потреби додати їх key-by-key у `bgremover.i18n` і покрити тестами.
- **O7 ✅ — Підпроцес для rembg/ONNX виконано (PR #283, issue #270 закрито).**
  Неперериваний AI-інференс тепер працює в процесі, запущеному через `spawn`
  (`ai_process.py`); `QThread.terminate()` як AI-аварійний вихід прибрано.
  Наслідкові знахідки щодо надійності/пам'яті виправлено й закрито в **#285**
  (PR #289).

## Відкриті GitHub-Issues — Стан Triage (2026-06-21)

Станом на 2026-06-21 GitHub ще показує **5** відкритих issues: **#245**,
**#299**, **#318**, **#322** і **#339**. Раніше перелічені issues щодо
проєкту/шарів і security-тестів, **#323**, **#324**, **#326** та **#329–#335**,
завершені в merge commits **#337**, **#338** і **#340**. Для **#322** тепер також
є **#342**; issue слід прокоментувати й закрити після перевірки merge.

| # | Назва | Рекомендація labels/status | Пропозиція коментаря/status |
|---|-------|----------------------------|-----------------------------|
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan падає з "Quota exceeded" | `security`; **залишити відкритим / blocked external** | Додати коментар, що repo-side hardening покрито #323/#324 і #322/#342; залишився блокер OpenAI/billing quota. Після відновлення quota один раз вручну запустити scheduled scan і закрити. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test hygiene: слабкі assertions/надлишковість | `quality`, `testing`; **open / low priority** | Додати коментар, що це не product/CI blocker; виконувати як opportunistic cleanup, коли зачіпаються відповідні tests. Status не змінювати. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: врахувати job-level permission overrides у reusable WF | `enhancement`, `testing`; **needs refinement** | Додати коментар, що перед змінами треба задокументувати GitHub semantics для top-level vs. job-level permissions у called workflow; не послаблювати OIDC guard #303. |
| [#322](https://github.com/NikolayDA/picture_helper/issues/322) | CI: maintenance/skip path для scheduled Codex Security Scan | `security`; **закрити після #342** | Додати коментар, що #342 реалізує conservative manual switch (`CODEX_SECURITY_SCAN_ENABLED=false`) зі skip output і regression tests; закрити після verified merge. |
| [#339](https://github.com/NikolayDA/picture_helper/issues/339) | HEIC/HEIF не підтримується як input format | **Додати labels:** `enhancement`, `documentation` (або `question`, якщо є); **needs decision** | Додати коментар про потребу product decision: явно задокументувати, що HEIC не підтримується, або спланувати optional `pillow-heif`/`HEIF` allowlist і load test. Тримати відкритим до рішення. |

### Рекомендовані дії для issues

1. Прокоментувати й закрити **#322**, коли merge #342 у `main` буде перевірено.
2. Додати labels до **#339** і ухвалити явне product decision (documentation
   clarification vs. HEIC feature).
3. Залишити **#245** відкритим, але позначити як externally blocked; додати
   посилання на #322/#342 як завершену repo-side частину.
4. Не реалізовувати **#318** одразу; спершу задокументувати GitHub permission
   semantics.
5. Залишити **#299** як low-priority test cleanup.

## Попередні Раунди

- **2026-06-01, «modest-shannon» (A–E)** — 5 знахідок, усі завершені.
- **v2.2, «admiring-mayer» (#1–#15)** — зовнішній список, завершений або відхилений там, де це було хибне спрацювання.

Повні історичні знахідки та робочі журнали (раунди 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.uk.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.uk.md).
