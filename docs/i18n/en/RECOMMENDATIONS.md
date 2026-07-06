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
Recommendations snapshot fix **#490** is closed. Today's verification pass over
the redesign epics (#413/#418/#424/#455/#463/#474/#483) turned up three new,
well-scoped findings: **#499** (light theme not yet 1:1 with the prototype),
**#500** (screenshot script broken after the redesign, blocking #432), and
**#501** (dead pre-redesign widget `TopIconTab*`). GitHub currently shows
**14** open issues.

### Completed Since The Last Review

- **Old baseline stable:** **N1/N2/N4/N5/N6/N7/N8** and **O2–O7** remain done;
  epics **#329/#344/#358/#384** (N9–N12) plus export fix **#363** are merged,
  covered by tests/CI, and archived.
- **Closed since the 2026-06-25 review:** **#404**, **#406**, and **#408**
  (PR #412) — the previously listed preview/dead-code/audit findings are done;
  `_derive_physical_size` no longer exists, and the render path degrades to
  COLOR on a size mismatch.
- **Redesign core shipped:** the stepper/`stepper.py`, card inspector, guided
  navigation, contextual tools, and the design tokens (`ACCENT`/`CARD_STYLE`)
  landed via PR #412/#423 (DE/EN strings, `tests/test_workflow.py`).
- **Rail/zoom wave completed:** **#455/#456/#457/#458/#463/#464** landed via
  PR #466, and **#465** is intentionally `not_planned`; PR #467 closed the
  three #466 P2s and refreshed the triage snapshot.
- **Card inspector completed:** **#414** landed via PR #473 (central `CARD_*`
  tokens, light/dark card style, accent-hex guard). That also completes epic
  **#413**.
- **Dark Mode and rail icons completed:** PR #482 closed **#474–#480** (dark
  surfaces, hairlines, accents, checkerboard, missing tokens, REDESIGN_SPEC
  drift test); PR #489 closed **#483–#488** (vector icons, state/theme colors,
  removed PNG fallbacks, docs/tests/review fix).
- **#490 completed:** The Recommendations snapshot drift after PR #482/#489
  is fixed; all six language mirrors were in sync.
- **Smoke tests/regression completed:** **#433/#434** landed via PR #423
  (stepper/card/navigation smoke tests, action wiring); epic **#426** now
  hinges only on **#435**.

### New Since The Last Review

- **#499 🟡 Bug/design system:** `theme.LIGHT` diverges from the embedded CSS
  in `design/Prototyp A - Geführter Workflow.dc.html` across several tokens
  (`stepper`/`border`/`hairline`/`hover`/`card_border`/accent family) — the
  same pattern as the already-completed Dark Mode alignment **#474–#480**,
  with the same test scaffold (`tests/test_theme.py`) already in place.
- **#500 🟠 Bug:** `scripts/generate_app_screenshots.py` looks up a right
  column via `findChild(QTabWidget)` that no longer exists since PR #412/#423
  (now a `Stepper` card sequence). Blocks **#432** (recreate screenshots) and
  any automated visual check against the prototype; no test coverage so far,
  cleanly reproducible.
- **#501 🟢 Quality:** `TopIconTabBar`/`TopIconTabWidget` in `widgets.py` are
  dead widgets since the stepper switch (only a lazy export in `__init__.py`
  plus an import mention in `tests/test_package_imports.py` remain). Low-risk
  cleanup, no functional change.

### Still Open

- **O1 🟠 — Additional runtime languages.** German and English are switchable;
  es/fr/uk/zh are not runtime locales yet. This matches redesign issue **#430** —
  add them key-for-key in `bgremover.i18n` and cover them with tests.
- **O8 🟢 — Prototype inaccuracy: height tools stay locked after generation.**
  In `design/Prototyp A - Geführter Workflow.dc.html`, "Generate height map
  from image" only sets `heightGen` without switching the active layer to
  role `Höhe` — `heightDisabled` stays tied to the previous role (review
  finding on PR #460). Mockup-only; the real app already activates the new
  HEIGHT layer automatically (#347).

## Open GitHub Issues — Triage Status (2026-07-06)

As of 2026-07-06, GitHub shows **14** open issues: three fresh redesign
follow-ups (**#499/#500/#501**), i18n/docs (**#425/#430/#431/#432**),
rollout/release (**#426/#435/#392/#389**), and backlog/external items
(**#299/#318/#245**).

### Sensible Bundles

- **Redesign follow-up (#499/#500/#501):** all three are independent,
  low-risk, and fit a single cleanup PR; **#500** takes priority because it
  unblocks **#432**.
- **i18n/docs (#425):** #430 (ES/FR/UK/ZH) unblocks the parity tests; #431 (docs)
  and #432 (screenshots) follow once the UI is visually final **and** #500
  makes the screenshot script runnable again.
- **Rollout/release:** #426 remains open only through #435; coordinate #435 with
  #392, then close #426/#389.
- **Backlog:** handle #299 after the release; refine #318 first; #245 stays
  externally blocked by OpenAI billing/quota.

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

1. **#500** first (fix the screenshot script) — unblocks **#432**; **#499** and
   **#501** can ride along in the same PR or a direct follow-up.
2. Pull **#430** forward (UI strings ES/FR/UK/ZH) — it unblocks i18n parity; then
   **#431**/**#432** once the UI is final.
3. **Release:** run **#435** + **#392** in a coordinated way, then close epics
   **#426** and **#389**.
4. **#299** after the release; research **#318** only (needs refinement); keep
   **#245** externally blocked.

## Previous Rounds

- **2026-07-05 triage** — #490 (snapshot drift) in progress, Dark Mode/rail-icon
  wave (#474–#488) and card inspector (#413/#414) completed.
- **2026-06-29 triage** — #404/#406/#408 completed (PR #412), redesign wave opened.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, completed or discarded where it was a false positive.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
