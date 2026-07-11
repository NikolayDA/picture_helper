[Deutsch](../../../RECOMMENDATIONS.md) · **English** · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Code Analysis & Ranked Recommendations: BgRemover

## Rating Scale

| Symbol | Priority | Meaning |
|--------|----------|---------|
| 🔴 | Critical | Bugs, crashes, or data loss |
| 🟠 | High | Clear impact on reliability or maintainability |
| 🟡 | Medium | Useful improvement for quality, readability, or testability |
| 🟢 | Low | Optional polish or process improvement |

## Current Status (2026-07-11)

The active code-analysis list is empty. Ruff, mypy, and the local test suite
remain the baseline before new PRs. **#431/#432** merged via PR #529 and are
closed — ANLEITUNG/README and every screenshot now reflect the guided
6-step workflow. That makes epic **#425** fully complete (all three
sub-issues #430/#431/#432 closed). Two new issues from a support case on
2026-07-11 were filed (**#530**/**#531**). GitHub still shows **10** open
issues.

### Completed Since The Last Review

- **Old baseline stable:** **N1/N2/N4/N5/N6/N7/N8** and **O2–O7** remain done;
  epics **#329/#344/#358/#384** (N9–N12) plus export fix **#363** are merged
  and archived.
- **Closed since 2026-06-25:** **#404/#406/#408** (PR #412) — preview/
  dead-code/audit findings done.
- **Redesign core, rail/zoom, card inspector, Dark Mode, UI follow-up:**
  **#413/#414/#455–#464/#474–#489/#499–#501/#503/#509/#510/#514–#517** landed
  via PR #412/#423/#466/#467/#473/#482/#489/#504/#506/#512/#513/#518/#519 and
  PR #520/#521/#522; **#490** and **#433/#434** likewise.
- **Closed since 2026-07-11:** **#430** (PR #526) — runtime i18n for
  ES/FR/UK/ZH fully maintained and parity-checked; **#431/#432** (PR #529) —
  ANLEITUNG/README/screenshots brought to the guided 6-step workflow.
  **Epic #425 is now content-complete** and can be closed.

### Still Open

- **O8 🟢 — Prototype inaccuracy:** height tools stay locked in the mockup
  after generation; mockup-only, the real app is unaffected (#347).

## Open GitHub Issues — Triage Status (2026-07-11)

As of 2026-07-11, GitHub shows **10** open issues: the i18n/docs epic
(**#425**, ready to close), rollout/release (**#426/#435/#392/#389**),
backlog/external items (**#299/#318/#245**), and two new AI-warmup findings
from the same support case (**#530/#531**).

### Sensible Bundles

- **i18n/docs:** #425 is fully done via #430/#431/#432 — only formal closing
  remains.
- **Rollout/release:** #426 hinges only on #435; coordinate with #392, then
  close #426/#389.
- **AI warmup support case (2026-07-11):** #530 (doc fix, mechanical) and
  #531 (tooltip/status-text UX) are independently shippable; #530 is the
  faster, lower-risk fix and can go first.
- **Backlog:** #299 after the release; refine #318 first; #245 stays
  externally blocked.

Rating: **Relevance** = importance to the roadmap/users, **Complexity** =
estimated implementation effort, **Model/Effort** = the recommended Claude
model and reasoning effort for Claude Code to implement it.

| # | Title | Relevance | Complexity | Model/Effort | Recommended next step |
|---|-------|-----------|------------|---------------|-----------------------|
| [#435](https://github.com/NikolayDA/picture_helper/issues/435) | CHANGELOG & version bump for the redesign | 🟡 Medium | 🟢 Low | Sonnet 5 · low | **Ready for PR** – mechanical, well-scoped; blocks #426 and #392. |
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | Cut release v2.5.0 | 🟠 High | 🟡 Medium | Sonnet 5 · medium | **Ready** – sequence after #435; #431/#432 are no longer a blocker; the macOS `.dmg` build needs a local/macOS runner outside this remote container. |
| [#530](https://github.com/NikolayDA/picture_helper/issues/530) | INSTALL_LINUX/MAC.md: AI download starts at app launch, not first click | 🟡 Medium | 🟢 Low | Sonnet 5 · low | **Ready for PR** – pure text fix across 2 files + 5 i18n mirrors; the exact code lines are already cited in the issue. |
| [#531](https://github.com/NikolayDA/picture_helper/issues/531) | AI button: surface warmup/loading state | 🟡 Medium | 🟡 Medium | Sonnet 5 · medium | **Ready for PR** – clear acceptance criteria including a qtbot-test requirement; tooltip text needs adding in 6 languages, `can_enable` logic stays unchanged. |
| [#425](https://github.com/NikolayDA/picture_helper/issues/425) | EPIC: Internationalization & documentation | 🟠 High | 🟢 Low | – (tracking issue) | **Ready to close** – #430/#431/#432 all done (PR #526/#529). |
| [#426](https://github.com/NikolayDA/picture_helper/issues/426) | EPIC: QA & rollout of the redesign | 🟠 High | 🟢 Low | – (tracking issue) | **Nearly done** – only #435 remains open. |
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | EPIC: Update user docs & cut release | 🟠 High | 🟢 Low | – (tracking issue) | **Close after #392** – only the release remains. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test hygiene: weak assertions/redundancies | 🟢 Low | 🟡 Medium | Sonnet 5 · medium | **Ready for PR** – catalog plus the N13 follow-ups from the 2026-07-08 triage are documented; prioritize after the release. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Job-level permission overrides in reusable WF | 🟢 Low | 🟡 Medium | Opus 4.8 · high | **Needs refinement** – prove the GitHub semantics (top-level vs. effective-per-job) first; must not weaken the OIDC regression guard. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan "Quota exceeded" | 🟡 Medium | 🟢 Low | – (no code task) | **Blocked (external)** – restoring OpenAI billing/quota is an account action, not a PR. |

### Recommended Next (PR order)

1. **#530** – fastest, lowest-risk fix; can run right away in parallel.
2. **Release:** run **#435** + **#392** in a coordinated way, then close
   **#426**/**#389** and **#425**.
3. **#531** – UX fix for the same support case as #530.
4. **#299** after the release; research **#318** only; keep **#245**
   externally blocked.

## Previous Rounds

- **2026-07-11 (2nd triage)** — #431/#432 closed (PR #529, ANLEITUNG/README/
  screenshots brought to the guided 6-step workflow); epic #425 is fully
  done. New issues #530/#531 filed from an AI-warmup support case.
- **2026-07-11** — #430 closed (PR #526, full runtime i18n ES/FR/UK/ZH; O1
  done); epic #425 then hinged only on #431/#432.
- **2026-07-10** — #509/#510 closed, #514–#517 completed, right-column
  follow-up finished through PR #520/#521/#522; benchmark-baseline workflow
  switched to PRs instead of direct pushes.
- **2026-07-06** — #499/#500/#501 (PR #504) and #503 (PR #506) completed;
  icon/status-bar polish via PR #507/#508.
- **2026-07-05** — #490 (snapshot drift) in progress, Dark Mode/rail-icon
  wave and card inspector (#413/#414) completed.
- **2026-06-29** — #404/#406/#408 completed (PR #412), redesign wave opened.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, completed or discarded where it was a false positive.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
