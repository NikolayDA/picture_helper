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
remain the baseline before new PRs. **#430** (runtime i18n for ES/FR/UK/ZH)
merged via PR #526 and is closed — verified: `bgremover/i18n.py::_TRANSLATIONS`
now carries `de/en/es/fr/uk/zh`, each with 494 keys in full parity. That also
closes out **O1** (additional runtime languages). GitHub currently shows
**10** open issues.

### Completed Since The Last Review

- **Old baseline stable:** **N1/N2/N4/N5/N6/N7/N8** and **O2–O7** remain done;
  epics **#329/#344/#358/#384** (N9–N12) plus export fix **#363** are merged
  and archived.
- **Closed since 2026-06-25:** **#404/#406/#408** (PR #412) — preview/
  dead-code/audit findings done.
- **Redesign core, rail/zoom, card inspector, Dark Mode, UI follow-up:**
  **#413/#414/#455–#464/#474–#489/#499–#501/#503/#509/#510/#514–#517** landed
  via PR #412/#423/#466/#467/#473/#482/#489/#504/#506/#512/#513/#518/#519 and
  PR #520/#521/#522; **#490** and **#433/#434** likewise (epic **#426** now
  hinges only on **#435**).
- **Closed since 2026-07-11:** **#430** (PR #526) — runtime i18n for
  ES/FR/UK/ZH fully maintained and parity-checked; **O1** is done (epic
  **#425** now hinges only on **#431**/**#432**).

### Still Open

- **O8 🟢 — Prototype inaccuracy:** height tools stay locked in the mockup
  after generation; mockup-only, the real app is unaffected (#347).

## Open GitHub Issues — Triage Status (2026-07-11)

As of 2026-07-11, GitHub shows **10** open issues: i18n/docs
(**#425/#431/#432**), rollout/release (**#426/#435/#392/#389**), and
backlog/external items (**#299/#318/#245**).

### Sensible Bundles

- **i18n/docs:** #430 is done; #431/#432 are now ready to implement (the UI
  freeze blocker is gone per the 2026-07-09 #431 audit).
- **Rollout/release:** #426 hinges only on #435; coordinate with #392, then
  close #426/#389.
- **Backlog:** #299 after the release; refine #318 first; #245 stays
  externally blocked.

Rating: **Relevance** = importance to the roadmap/users, **Complexity** =
estimated implementation effort, **Model/Effort** = the recommended Claude
model and reasoning effort for Claude Code to implement it.

| # | Title | Relevance | Complexity | Model/Effort | Recommended next step |
|---|-------|-----------|------------|---------------|-----------------------|
| [#425](https://github.com/NikolayDA/picture_helper/issues/425) | EPIC: Internationalization & documentation | 🟠 High | 🟢 Low | – (tracking issue) | **In progress** – #431/#432 open, #430 done. |
| [#431](https://github.com/NikolayDA/picture_helper/issues/431) | Update ANLEITUNG & README to guided workflow | 🟡 Medium | 🟡 Medium | Sonnet 5 · medium | **Ready for PR** – 2026-07-09 audit already done (includes fixing the 6-format crop-ratio list). |
| [#432](https://github.com/NikolayDA/picture_helper/issues/432) | Recreate app screenshots for the redesign | 🟢 Low | 🟢 Low | Sonnet 5 · low | **Ready for PR** – #500 blocker gone (PR #504); a visual sanity check by the user is worthwhile. |
| [#426](https://github.com/NikolayDA/picture_helper/issues/426) | EPIC: QA & rollout of the redesign | 🟠 High | 🟢 Low | – (tracking issue) | **Nearly done** – only #435 remains open. |
| [#435](https://github.com/NikolayDA/picture_helper/issues/435) | CHANGELOG & version bump for the redesign | 🟡 Medium | 🟢 Low | Sonnet 5 · low | **Ready for PR** – mechanical, well-scoped. |
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | Cut release v2.5.0 | 🟠 High | 🟡 Medium | Sonnet 5 · medium | **Ready** – sequence after #435; the macOS `.dmg` build needs a local/macOS runner outside this remote container. |
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | EPIC: Update user docs & cut release | 🟠 High | 🟢 Low | – (tracking issue) | **Close after #392** – only the release remains. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test hygiene: weak assertions/redundancies | 🟢 Low | 🟡 Medium | Sonnet 5 · medium | **Ready for PR** – catalog plus the N13 follow-ups from the 2026-07-08 triage are documented; prioritize after the release. |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Job-level permission overrides in reusable WF | 🟢 Low | 🟡 Medium | Opus 4.8 · high | **Needs refinement** – prove the GitHub semantics (top-level vs. effective-per-job) first; must not weaken the OIDC regression guard. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan "Quota exceeded" | 🟡 Medium | 🟢 Low | – (no code task) | **Blocked (external)** – restoring OpenAI billing/quota is an account action, not a PR. |

### Recommended Next (PR order)

1. **#431**/**#432** — both ready to implement, no blocker left.
2. **Release:** run **#435** + **#392** in a coordinated way, then close
   **#426**/**#389**.
3. **#299** after the release; research **#318** only; keep **#245**
   externally blocked.

## Previous Rounds

- **2026-07-11** — #430 closed (PR #526, full runtime i18n ES/FR/UK/ZH; O1
  done); epic #425 now hinges only on #431/#432.
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
