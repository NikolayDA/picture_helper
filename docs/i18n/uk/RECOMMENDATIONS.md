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

## Відкриті GitHub-Issues — Оцінка Пріоритетів (2026-06-21)

As of 2026-06-21, only **4** roadmap/follow-up issues remain open after
reviewing yesterday's and today's PRs. Merge commits **#337**, **#338**, and
**#340** cleanly complete the items that were still open yesterday: **#326**,
**#329–#335**, **#323**, and **#324**. The GIF load path is regression-tested,
the project/layer epic is implemented end-to-end from the domain model through
UI/integration, and the security-scan tests cover severity filtering, empty
findings, and prompt scope. The remaining open items are **#322**
(maintenance/skip path for the scheduled Codex Security Scan), **#318**
(permission-guard semantics), **#245** (externally blocked quota), and **#299**
(test hygiene).

| # | Title | Relevance | Complexity | Recommendation |
|---|-------|-----------|------------|----------------|
| [#322](https://github.com/NikolayDA/picture_helper/issues/322) | CI: add a maintenance/skip path for the scheduled Codex Security Scan | 🟡 Medium | 🟡 Medium | **Next repo-side step for #245** — choose manual switch, visible auto graceful-skip, or both; gate in the `cadence` job, "disabled → skipped, not failed", keep least privilege and add a static test |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: respect job-level permission overrides in reusable WF | 🟡 Medium | 🟡 Medium | **Needs refinement** — first document GitHub's startup-validation semantics (top-level vs. effective-per-job); no observed repo failure right now, and OIDC guard #303 must not be weakened |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan fails with "Quota exceeded" | 🟡 Medium | 🟢 Low | **Externally blocked** — restore quota account-side; #323/#324 are complete repo-side, #322 remains open as maintenance/skip hardening |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test hygiene: weak assertions/redundancies | 🟢 Low | 🟢 Low | No correctness bug; improve opportunistically when related tests are touched (highest value: endpoint move, consolidate `set_brush_size`) |

### Issues, які можна обʼєднати

- **#322** can be implemented as a standalone CI-hardening PR and complements
  the already completed #323/#324.
- **#318** stays separate because GitHub's semantics must be documented before
  changing code.
- **#299** should only ride along when an affected test is already being edited.

### Рекомендований порядок PR

1. **#322** — final repo-side #245 follow-up with direct operational value.
2. **#318** — refine the permission guard once semantics are documented, without
   weakening the OIDC regression case.
3. **#245** — restore quota account-side (externally blocked).
4. **#299** — test hygiene as needed.

## Попередні Раунди

- **2026-06-01, «modest-shannon» (A–E)** — 5 знахідок, усі завершені.
- **v2.2, «admiring-mayer» (#1–#15)** — зовнішній список, завершений або відхилений там, де це було хибне спрацювання.

Повні історичні знахідки та робочі журнали (раунди 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.uk.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.uk.md).
