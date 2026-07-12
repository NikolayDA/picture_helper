[Deutsch](../../../RECOMMENDATIONS.md) · **English** · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Code Analysis & Ranked Recommendations: BgRemover

## Rating Scale

| Symbol | Priority | Meaning |
|--------|----------|---------|
| 🔴 | Critical | Bugs, crashes, or data loss |
| 🟠 | High | Clear impact on reliability or maintainability |
| 🟡 | Medium | Useful improvement for quality, readability, or testability |
| 🟢 | Low | Optional polish or process improvement |

## Current Status (2026-07-12)

The active code-analysis list is empty. Ruff, mypy, and the local test suite
remain the baseline before new PRs. Release **v2.5.0** was cut on 2026-07-11
(CHANGELOG curated, version bumped — PR #538). The entire rollout/release
wave is therefore closed: **#435** (PR #538), **#392**, **#426**, and
**#389**. Also closed: **#299** (PR #539) together with the separately
tracked N13 test-hygiene follow-up **#541** (PR #543), plus **#318**
(PR #540). GitHub currently shows only **2** open issues.

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
- **Closed since 2026-07-12:** release wave **#435/#392/#426/#389** (v2.5.0,
  PR #538) plus **#299** (PR #539), the test-hygiene follow-up **#541**
  (PR #543), and **#318** (PR #540). All redesign/release/backlog items from
  the last snapshot are thereby cleared.

### Still Open

- **O8 🟢 — Prototype inaccuracy:** height tools stay locked in the mockup
  after generation; mockup-only, the real app is unaffected (#347).

## Open GitHub Issues — Triage Status (2026-07-12)

As of 2026-07-12, GitHub shows only **2** open issues: the external
quota/billing blocker **#245** and this docs synchronization **#542**.

### Sensible Bundles

- **Externally blocked:** #245 hinges on OpenAI billing/quota — an account
  action, not a repo PR.
- **Docs:** #542 aligns the six recommendations mirrors with the live state
  and is resolved by the accompanying PR.

Rating: **Relevance** = importance to the roadmap/users, **Complexity** =
estimated implementation effort, **Model/Effort** = the recommended Claude
model and reasoning effort for Claude Code to implement it.

| # | Title | Relevance | Complexity | Model/Effort | Recommended next step |
|---|-------|-----------|------------|---------------|-----------------------|
| [#542](https://github.com/NikolayDA/picture_helper/issues/542) | Refresh recommendations snapshot after v2.5.0 | 🟢 Low | 🟢 Low | Sonnet 5 · low | **In progress** – this PR aligns all six mirrors with the live state, structurally in sync. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan "Quota exceeded" | 🟡 Medium | 🟢 Low | – (no code task) | **Blocked (external)** – restoring OpenAI billing/quota is an account action, not a PR. |

### Recommended Next (PR order)

1. Close **#542** with this PR (structurally synchronized snapshot sync
   across all six mirrors).
2. **#245** stays externally blocked — no repo PR is possible; verify
   manually only after the OpenAI quota is restored.

## Previous Rounds

- **2026-07-12** — release **v2.5.0** cut; rollout wave #435/#392/#426/#389
  closed; #299 (PR #539), N13 follow-up #541 (PR #543), and #318 (PR #540)
  closed; open-issue snapshot reduced to #245 + #542.
- **2026-07-11 (final follow-up)** — #425 formally closed; #530/#531 closed
  through PR #533/#535; open-issue snapshot updated to 7 remaining issues.
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
