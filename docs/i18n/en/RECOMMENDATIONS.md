[Deutsch](../../../RECOMMENDATIONS.md) · **English** · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Code Analysis & Ranked Recommendations: BgRemover

## Rating Scale

| Symbol | Priority | Meaning |
|--------|----------|---------|
| 🔴 | Critical | Bugs, crashes, or data loss |
| 🟠 | High | Clear impact on reliability or maintainability |
| 🟡 | Medium | Useful improvement for quality, readability, or testability |
| 🟢 | Low | Optional polish or process improvement |

## Current Status (2026-07-02)

The active code-analysis list is empty. Ruff, mypy, and the local test suite
remain the baseline before new PRs. New this round: the open-issue triage is
brought up to the real state (18 open issues).

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
  landed via PR #412/#423 (DE/EN strings, `tests/test_workflow.py`); only the
  polish remains (see triage).

### Still Open

- **O1 🟠 — Additional runtime languages.** German and English are switchable;
  es/fr/uk/zh are not runtime locales yet. This matches redesign issue **#430** —
  add them key-for-key in `bgremover.i18n` and cover them with tests.

## Open GitHub Issues — Triage Status (2026-07-02)

As of 2026-07-02, GitHub shows **18** open issues. The 2026-06-29 snapshot is
stale: #404/#406/#408 are closed (PR #412), and the **redesign wave (guided
workflow)** is the active roadmap. Its core already shipped; what remains is
polish (**#414**), i18n/docs (epic **#425**: #430/#431/#432), QA/rollout (epic
**#426**: #433/#434/#435), the standing release **#392**, and the independent
items **#299/#318/#245**. **#442** tracks exactly this doc refresh.

**Comment pass:** No new external comments. The owner notes on #245/#299/#392
match the current state; #442 (2026-07-02) records this audit — no issue update
needed.

### Sensible Bundles

- **Nearly finished epics:** #418 and #424 have **all** sub-issues closed →
  verify and close. #413 has only #414 left; its tokens already live in
  `theme.py` — add the light-scheme card style, then close it.
- **i18n/docs (#425):** #430 (ES/FR/UK/ZH) unblocks the parity tests; #431 (docs)
  and #432 (screenshots) follow once the UI is visually final.
- **QA/rollout (#426):** #433 is largely covered by PR #423 (check the gap, close
  it); #434 is ready for PR; align #435 (CHANGELOG/version) with #392.
- **Release:** decide whether the redesign ships in **v2.5.0** (#392/#435
  together) or in a later bump.

Rating: **Relevance** = importance to the roadmap/users, **Complexity** =
estimated implementation effort.

| # | Title | Relevance | Complexity | Recommended next step |
|---|-------|-----------|------------|-----------------------|
| [#418](https://github.com/NikolayDA/picture_helper/issues/418) | EPIC: Guided workflow – stepper & navigation | 🟠 High | 🟢 Low | **Verify & close** – all sub-issues closed (PR #423). |
| [#413](https://github.com/NikolayDA/picture_helper/issues/413) | EPIC: Card inspector – right column as cards | 🟠 High | 🟢 Low | **Nearly done** – only #414 open. |
| [#414](https://github.com/NikolayDA/picture_helper/issues/414) | Centralize card container & accent tokens | 🟡 Medium | 🟢 Low | **Ready for PR** – tokens exist; add the light card style. |
| [#424](https://github.com/NikolayDA/picture_helper/issues/424) | EPIC: Unified design system & theming | 🟠 High | 🟢 Low | **Verify & close** – all sub-issues closed. |
| [#425](https://github.com/NikolayDA/picture_helper/issues/425) | EPIC: Internationalization & documentation | 🟠 High | 🟡 Medium | **In progress** – #430/#431/#432 open. |
| [#430](https://github.com/NikolayDA/picture_helper/issues/430) | New UI strings (steps/cards/navigation) | 🟠 High | 🟡 Medium | **Ready for PR** – ES/FR/UK/ZH; DE/EN via PR #423. |
| [#431](https://github.com/NikolayDA/picture_helper/issues/431) | Update ANLEITUNG & README to guided workflow | 🟡 Medium | 🟡 Medium | **After UI freeze** – 6-language mirror, link tests. |
| [#432](https://github.com/NikolayDA/picture_helper/issues/432) | Recreate app screenshots for the redesign | 🟢 Low | 🟢 Low | **Blocked** – only once the UI is visually final. |
| [#426](https://github.com/NikolayDA/picture_helper/issues/426) | EPIC: QA & rollout of the redesign | 🟠 High | 🟢 Low | **In progress** – #433/#434/#435 open. |
| [#433](https://github.com/NikolayDA/picture_helper/issues/433) | Smoke tests stepper/cards/navigation | 🟡 Medium | 🟢 Low | **Check the gap** – largely covered by PR #423. |
| [#434](https://github.com/NikolayDA/picture_helper/issues/434) | Regression for visibility & action wiring | 🟡 Medium | 🟢 Low | **Ready for PR** – action callbacks per step. |
| [#435](https://github.com/NikolayDA/picture_helper/issues/435) | CHANGELOG & version bump for the redesign | 🟡 Medium | 🟢 Low | **Align with #392** – settle the release sequence. |
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | Cut release v2.5.0 | 🟠 High | 🟡 Medium | **Ready** – decide the sequence with the redesign. |
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | EPIC: Update user docs & cut release | 🟠 High | 🟢 Low | **Close after #392** – only the release remains. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test hygiene: weak assertions/redundancies | 🟢 Low | 🟢 Low | **After the release** – highest impact first. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Job-level permission overrides in reusable WF | 🟢 Low | 🟡 Medium | **Needs refinement** – prove GitHub semantics. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan "Quota exceeded" | 🟡 Medium | 🟢 Low | **Blocked (external)** – OpenAI billing/quota. |
| [#442](https://github.com/NikolayDA/picture_helper/issues/442) | RECOMMENDATIONS.md is outdated | 🟡 Medium | 🟢 Low | **Resolved by this update** – closeable. |

### Recommended Next (PR order)

1. **Housekeeping:** verify the sub-issues and close the nearly finished epics
   **#418** and **#424**; finish **#414** (light card style), then close **#413**.
2. Pull **#430** forward (UI strings ES/FR/UK/ZH) — it unblocks i18n parity; then
   **#431**/**#432** once the UI is final.
3. Implement **#434** (regression); confirm **#433** coverage from PR #423 and
   close it.
4. **Release:** run **#435** + **#392** in a coordinated way, then close epics
   **#426** and **#389**.
5. **#299** after the release; research **#318** only (needs refinement); keep
   **#245** externally blocked; close **#442** once this refresh lands.

## Previous Rounds

- **2026-06-29 triage** — #404/#406/#408 completed (PR #412), redesign wave opened.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, completed or discarded where it was a false positive.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
