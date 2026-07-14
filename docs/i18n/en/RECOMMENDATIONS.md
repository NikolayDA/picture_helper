[Deutsch](../../../RECOMMENDATIONS.md) · **English** · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Code Analysis & Ranked Recommendations: BgRemover

## Rating Scale

| Symbol | Priority | Meaning |
|--------|----------|---------|
| 🔴 | Critical | Bugs, crashes, or data loss |
| 🟠 | High | Clear impact on reliability or maintainability |
| 🟡 | Medium | Useful improvement for quality, readability, or testability |
| 🟢 | Low | Optional polish or process improvement |

## Current Status (2026-07-14)

The active code-analysis list is empty. Ruff, mypy, and the local test suite
remain the baseline before new PRs. Release **v2.5.0** was cut on 2026-07-11
(PR #538); the rollout wave **#435/#392/#426/#389** is closed, as is **#299**
(PR #539) with N13 follow-up **#541** (PR #543), **#318** (PR #540), and the
snapshot sync **#542**. A repo audit on 2026-07-12 filed **#549–#553**;
**#552/#549/#553/#550** are now closed via PR #557–#560. Epic **#563**
("app update check & AI model management", eight sub-issues **#564–#571**)
was fully implemented and closed on 2026-07-13 via PR #573/#574 (**N14**).
Live state: **2** open issues – #245, #551.

### Completed Since The Last Review

- **Old baseline stable:** **N1/N2/N4/N5/N6/N7/N8** and **O2–O7** remain
  done; epics **#329/#344/#358/#384** (N9–N12) plus export fix **#363** are
  merged/archived. Since 2026-06-25 also **#404/#406/#408** (PR #412) closed.
- **Redesign & release:** redesign core/rail/zoom/card inspector/Dark
  Mode/UI follow-up (**#413/#414/#455–#464/#474–#489/#499–#501/#503/#509/
  #510/#514–#517**, **#490**, **#433/#434**) landed via PR #412–#522.
  Release wave **#435/#392/#426/#389** (v2.5.0), **#299/#541/#318/#542**, PR
  template **#552**, snapshot sync **#549**, SessionStart fix **#553**,
  v2.3.0 formalization **#550** – all closed since 2026-07-12.
- **N14 — Epic #563 (app update & AI model management) fully closed:**
  update-check core logic `app_update.py` (#564) and model-status core logic
  `ai_model_status.py` (#568) – both Qt-free, strictly typed, and in the
  mypy strict list (PR #573). Menu/dialog integration "Check for updates…"/
  "Manage AI model…" (#565/#569, PR #573). Optional automatic startup check
  (#566) and real wiring of model download into the existing warmup mechanism
  with multiple observers/cooperative cancellation (#570, PR #574, including
  three Codex review fixes: separate on_success/on_finished callbacks,
  manual check attaches to a running startup check, race protection while
  attaching). Docs wrap-up (README/CLAUDE.md/CHANGELOG/RESOURCES/INSTALL_*,
  all six languages) via #567/#571.

### Still Open

- **O8 🟢 — Prototype inaccuracy:** height tools stay locked in the mockup
  after generation; mockup-only, the real app is unaffected (#347).

## Open GitHub Issues — Triage Status (2026-07-14)

Live state: **2** open issues – both pre-existing CI/security issues,
unchanged from the previous round (epic #563 and all eight sub-issues have
since been fully closed).

### Sensible Bundles

#245/#551 are linked (Codex scan: account action vs. strategic decision).

Rating: **Relevance** = importance to the roadmap/users, **Complexity** =
estimated implementation effort, **Model/Effort** = the recommended Claude
model and reasoning effort.

| # | Title | Relevance | Complexity | Model/Effort | Recommended next step |
|---|-------|-----------|------------|---------------|-----------------------|
| [#551](https://github.com/NikolayDA/picture_helper/issues/551) | Codex Security Scan strategy decision (reactivate/decommission/replace) | 🟡 Medium | 🟡 Medium | Sonnet 5 · medium | **Needs refinement** – choice among three options; recommendation: option 2 (decommission/disable) given weeks of external blockage and redundancy with pip-audit/license/CI. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan "Quota exceeded" | 🟡 Medium | 🟢 Low | – (no code task) | **Blocked (external)** – restoring OpenAI billing/quota is an account action, not a PR. |

### Recommended Next (PR order)

1. **#551** — get a decision on the scan strategy (linked to #245), then
   adjust the workflow.
2. **#245** — stays externally blocked; verify manually only after the
   OpenAI quota is restored.

*Drift note:* re-check the live open-issue count before every future update
instead of carrying it forward (#542 → #549 hit the same off-by-one).

## Previous Rounds

- **2026-07-13 (epic completion)** — epic **#563** fully closed: all eight
  sub-issues (**#564–#571**) closed through PR #573 (#564/#565/#568/#569)
  and PR #574 (#566/#570 + docs wrap-up #567/#571). Snapshot reduced to 2
  (#245, #551).
- **2026-07-13 (issue audit)** — epic **#563** + eight sub-issues
  (**#564–#571**) filed; all 11 open issues re-assessed, owner comments
  taken into account. No issue closed. Recommendation: #564/#568 first.
  Snapshot updated to 11.
- **2026-07-12** — v2.3.0 formalization (**#550**), SessionStart hook fix
  (**#553**), snapshot sync (**#549**, PR template **#552** via PR #557),
  issue audit (**#542** closed, #549–#553 filed), and release **v2.5.0**
  (rollout wave #435/#392/#426/#389, #299/#541/#318) – snapshot temporarily
  reduced to 2 (#245, #551).
- **2026-07-11** — epic #425 fully closed (#430 PR #526, full runtime i18n
  ES/FR/UK/ZH, O1 done; #431/#432 PR #529; final follow-up #530/#531
  PR #533/#535).
- **2026-07-05–10** — #509/#510/#514–#517 (PR #520–#522), #490, Dark
  Mode/rail-icon wave, card inspector (#413/#414), #499–#501/#503,
  icon/status-bar polish.
- **2026-06-29** — #404/#406/#408 completed (PR #412), redesign wave opened.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, completed or
  discarded where it was a false positive.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
