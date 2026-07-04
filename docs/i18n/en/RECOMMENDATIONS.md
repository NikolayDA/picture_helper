[Deutsch](../../../RECOMMENDATIONS.md) · **English** · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Code Analysis & Ranked Recommendations: BgRemover

## Rating Scale

| Symbol | Priority | Meaning |
|--------|----------|---------|
| 🔴 | Critical | Bugs, crashes, or data loss |
| 🟠 | High | Clear impact on reliability or maintainability |
| 🟡 | Medium | Useful improvement for quality, readability, or testability |
| 🟢 | Low | Optional polish or process improvement |

## Current Status (2026-07-04)

The active code-analysis list is empty. Ruff, mypy, and the local test suite
remain the baseline before new PRs. New this round: **#461**, **#414**, and
epic **#413** are closed. PR #473 centralizes the card metrics and removes the
last accent hex outside `theme.py`. The new open Dark Mode prototype-alignment
cluster is **#474–#480**. GitHub now shows **18** open roadmap/backlog issues.

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
  PR #466, and **#465** is intentionally `not_planned`. PR #467 closes the
  three late #466 P2s (zoom direction, viewport anchor, height-dab preview) and
  refreshed the triage snapshot.
- **#461 closed (2026-07-04):** The snapshot refreshed by PR #467 matches the
  live GitHub state; the issue itself stayed open after the merge and is closed
  in this round.
- **Card inspector completed:** **#414** landed via PR #473 (central `CARD_*`
  tokens, light/dark card style, accent-hex guard). That also completes epic
  **#413**.

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

## Open GitHub Issues — Triage Status (2026-07-04)

As of 2026-07-04, GitHub shows **18** open roadmap/backlog issues: Dark Mode
prototype alignment (**#474/#475/#476/#477/#478/#479/#480**), i18n/docs
(**#425/#430/#431/#432**), rollout/release (**#426/#435/#392/#389**), and the
independent items **#299/#318/#245**. **#461** was the completed snapshot drift;
**#414** and **#413** are also closed after PR #473.

### Sensible Bundles

- **Dark Mode 1:1 (#474):** bundle #475/#476/#477/#479 as the token wave, #478
  as the canvas-checker fix, and #480 as the final spec/drift-test pass.
- **i18n/docs (#425):** #430 (ES/FR/UK/ZH) unblocks the parity tests; #431 (docs)
  and #432 (screenshots) follow once the UI is visually final.
- **Rollout/release:** #426 remains open only through #435; coordinate #435 with
  #392, then close #426/#389.
- **Backlog:** handle #299 after the release; refine #318 first; #245 stays
  externally blocked by OpenAI billing/quota.

Rating: **Relevance** = importance to the roadmap/users, **Complexity** =
estimated implementation effort.

| # | Title | Relevance | Complexity | Recommended next step |
|---|-------|-----------|------------|-----------------------|
| [#474](https://github.com/NikolayDA/picture_helper/issues/474) | EPIC: Align Dark Mode 1:1 with Prototype A | 🟠 High | 🟡 Medium | **New** – bundle #475–#480. |
| [#475](https://github.com/NikolayDA/picture_helper/issues/475) | Dark scheme: align background surfaces | 🟠 High | 🟢 Low | **Start here** – base surfaces first. |
| [#476](https://github.com/NikolayDA/picture_helper/issues/476) | Dark scheme: transparent borders/hairlines | 🟡 Medium | 🟢 Low | **With #475** – fix border tokens. |
| [#477](https://github.com/NikolayDA/picture_helper/issues/477) | Dark scheme: align accent/button colors | 🟠 High | 🟢 Low | **With #475** – interactive colors. |
| [#478](https://github.com/NikolayDA/picture_helper/issues/478) | Canvas checker ignores current theme | 🟡 Medium | 🟡 Medium | **After tokens** – palette + theme switch. |
| [#479](https://github.com/NikolayDA/picture_helper/issues/479) | Add missing color tokens from the prototype | 🟡 Medium | 🟡 Medium | **With spec pass** – only proven tokens. |
| [#480](https://github.com/NikolayDA/picture_helper/issues/480) | REDESIGN_SPEC color tables + drift test | 🟡 Medium | 🟡 Medium | **Final pass** – after #475–#479. |
| [#425](https://github.com/NikolayDA/picture_helper/issues/425) | EPIC: Internationalization & documentation | 🟠 High | 🟡 Medium | **In progress** – #430/#431/#432 open. |
| [#430](https://github.com/NikolayDA/picture_helper/issues/430) | New UI strings (steps/cards/navigation) | 🟠 High | 🟡 Medium | **Ready for PR** – ES/FR/UK/ZH; DE/EN via PR #423. |
| [#431](https://github.com/NikolayDA/picture_helper/issues/431) | Update ANLEITUNG & README to guided workflow | 🟡 Medium | 🟡 Medium | **After UI freeze** – 6-language mirror, link tests. |
| [#432](https://github.com/NikolayDA/picture_helper/issues/432) | Recreate app screenshots for the redesign | 🟢 Low | 🟢 Low | **Blocked** – only once the UI is visually final. |
| [#426](https://github.com/NikolayDA/picture_helper/issues/426) | EPIC: QA & rollout of the redesign | 🟠 High | 🟢 Low | **Nearly done** – only #435 remains open. |
| [#435](https://github.com/NikolayDA/picture_helper/issues/435) | CHANGELOG & version bump for the redesign | 🟡 Medium | 🟢 Low | **Align with #392** – settle the release sequence. |
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | Cut release v2.5.0 | 🟠 High | 🟡 Medium | **Ready** – decide the sequence with the redesign. |
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | EPIC: Update user docs & cut release | 🟠 High | 🟢 Low | **Close after #392** – only the release remains. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test hygiene: weak assertions/redundancies | 🟢 Low | 🟢 Low | **After the release** – highest impact first. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Job-level permission overrides in reusable WF | 🟢 Low | 🟡 Medium | **Needs refinement** – prove GitHub semantics. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan "Quota exceeded" | 🟡 Medium | 🟢 Low | **Blocked (external)** – OpenAI billing/quota. |

### Recommended Next (PR order)

1. Bundle **#474**: #475/#476/#477/#479 token wave, then #478 and #480.
2. Pull **#430** forward (UI strings ES/FR/UK/ZH) — it unblocks i18n parity; then
   **#431**/**#432** once the UI is final.
3. **Release:** run **#435** + **#392** in a coordinated way, then close epics
   **#426** and **#389**.
4. **#299** after the release; research **#318** only (needs refinement); keep
   **#245** externally blocked.

## Previous Rounds

- **2026-06-29 triage** — #404/#406/#408 completed (PR #412), redesign wave opened.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, completed or discarded where it was a false positive.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
