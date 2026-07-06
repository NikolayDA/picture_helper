[Deutsch](../../../RECOMMENDATIONS.md) · **English** · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Code Analysis & Ranked Recommendations: BgRemover

## Rating Scale

| Symbol | Priority | Meaning |
|--------|----------|---------|
| 🔴 | Critical | Bugs, crashes, or data loss |
| 🟠 | High | Clear impact on reliability or maintainability |
| 🟡 | Medium | Useful improvement for quality, readability, or testability |
| 🟢 | Low | Optional polish or process improvement |

## Current Status (2026-07-06)

The active code-analysis list is empty. Ruff, mypy, and the local test suite
remain the baseline before new PRs. Since the 2026-07-05 snapshot, the
Recommendations snapshot fix **#490** is closed. Today's verification pass
over the redesign epics (#413/#418/#424/#455/#463/#474/#483) turned up three
new, well-scoped findings: **#499** (light theme not yet 1:1 with the
prototype), **#500** (screenshot script broken, blocking #432), and **#501**
(dead widget `TopIconTab*`). GitHub currently shows **14** open issues.

### Completed Since The Last Review

- **Old baseline stable:** **N1/N2/N4/N5/N6/N7/N8** and **O2–O7** remain done;
  epics **#329/#344/#358/#384** (N9–N12) plus export fix **#363** are merged
  and archived.
- **Closed since the 2026-06-25 review:** **#404/#406/#408** (PR #412) —
  preview/dead-code/audit findings done.
- **Redesign core, rail/zoom, card inspector, Dark Mode:** **#413/#414/
  #455–#464/#474–#489** landed via PR #412/#423/#466/#467/#473/#482/#489
  (stepper, design tokens, Dark Mode alignment, vector icons).
- **#490 and #433/#434 completed:** snapshot drift fixed; smoke tests/
  regression landed via PR #423 — epic **#426** now hinges only on **#435**.

### New Since The Last Review

- **#499 🟡:** `theme.LIGHT` diverges from the prototype across several
  tokens (same pattern as #474–#480, test already in `tests/test_theme.py`).
- **#500 🟠:** `scripts/generate_app_screenshots.py` looks up a `QTabWidget`
  that no longer exists; blocks **#432**.
- **#501 🟢:** `TopIconTabBar`/`TopIconTabWidget` in `widgets.py` are dead
  widgets since the stepper switch.

### Still Open

- **O1 🟠 — Additional runtime languages.** DE/EN are switchable; es/fr/uk/zh
  are still missing as runtime locales (matches **#430**).
- **O8 🟢 — Prototype inaccuracy:** height tools stay locked in the mockup
  after generation; mockup-only, the real app is unaffected (#347).

## Open GitHub Issues — Triage Status (2026-07-06)

As of 2026-07-06, GitHub shows **14** open issues: three redesign follow-ups
(**#499/#500/#501**), i18n/docs (**#425/#430/#431/#432**), rollout/release
(**#426/#435/#392/#389**), and backlog/external items (**#299/#318/#245**).

### Sensible Bundles

- **Redesign follow-up:** #499/#500/#501 are independent and low-risk;
  **#500** first because it unblocks **#432**.
- **i18n/docs:** #430 unblocks the parity tests; #431/#432 follow after the
  UI freeze **and** #500.
- **Rollout/release:** #426 hinges only on #435; coordinate with #392, then
  close #426/#389.
- **Backlog:** #299 after the release; refine #318 first; #245 stays
  externally blocked.

Rating: **Relevance** = importance to the roadmap/users, **Complexity** =
estimated implementation effort.

| # | Title | Relevance | Complexity | Recommended next step |
|---|-------|-----------|------------|-----------------------|
| [#500](https://github.com/NikolayDA/picture_helper/issues/500) | Screenshot script broken after redesign (blocks #432) | 🟠 High | 🟢 Low | **Ready for PR** – switch navigation to `Stepper`. |
| [#499](https://github.com/NikolayDA/picture_helper/issues/499) | Align light theme 1:1 with Prototype A | 🟡 Medium | 🟢 Low | **Ready for PR** – same pattern as #474–#480. |
| [#501](https://github.com/NikolayDA/picture_helper/issues/501) | Remove orphaned `TopIconTab*` widgets | 🟢 Low | 🟢 Low | **Ready for PR** – pure cleanup, 3 files. |
| [#425](https://github.com/NikolayDA/picture_helper/issues/425) | EPIC: Internationalization & documentation | 🟠 High | 🟡 Medium | **In progress** – #430/#431/#432 open. |
| [#430](https://github.com/NikolayDA/picture_helper/issues/430) | New UI strings (steps/cards/navigation) | 🟠 High | 🟡 Medium | **Ready for PR** – ES/FR/UK/ZH; DE/EN via PR #423. |
| [#431](https://github.com/NikolayDA/picture_helper/issues/431) | Update ANLEITUNG & README to guided workflow | 🟡 Medium | 🟡 Medium | **After UI freeze** – 6-language mirror, link tests. |
| [#432](https://github.com/NikolayDA/picture_helper/issues/432) | Recreate app screenshots for the redesign | 🟢 Low | 🟢 Low | **Blocked** – needs UI freeze **and** #500. |
| [#426](https://github.com/NikolayDA/picture_helper/issues/426) | EPIC: QA & rollout of the redesign | 🟠 High | 🟢 Low | **Nearly done** – only #435 remains open. |
| [#435](https://github.com/NikolayDA/picture_helper/issues/435) | CHANGELOG & version bump for the redesign | 🟡 Medium | 🟢 Low | **Align with #392** – settle the release sequence. |
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | Cut release v2.5.0 | 🟠 High | 🟡 Medium | **Ready** – decide the sequence with the redesign. |
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | EPIC: Update user docs & cut release | 🟠 High | 🟢 Low | **Close after #392** – only the release remains. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test hygiene: weak assertions/redundancies | 🟢 Low | 🟢 Low | **After the release** – highest impact first. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Job-level permission overrides in reusable WF | 🟢 Low | 🟡 Medium | **Needs refinement** – prove GitHub semantics. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan "Quota exceeded" | 🟡 Medium | 🟢 Low | **Blocked (external)** – OpenAI billing/quota. |

### Recommended Next (PR order)

1. **#500** first — unblocks **#432**; **#499**/**#501** in the same or a
   direct follow-up PR.
2. Pull **#430** forward — unblocks i18n parity; then **#431**/**#432**.
3. **Release:** run **#435** + **#392** in a coordinated way, then close
   **#426**/**#389**.
4. **#299** after the release; research **#318** only; keep **#245**
   externally blocked.

## Previous Rounds

- **2026-07-05** — #490 (snapshot drift) in progress, Dark Mode/rail-icon
  wave and card inspector (#413/#414) completed.
- **2026-06-29** — #404/#406/#408 completed (PR #412), redesign wave opened.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, completed or discarded where it was a false positive.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
