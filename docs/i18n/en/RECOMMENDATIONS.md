[Deutsch](../../../RECOMMENDATIONS.md) · **English** · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Code Analysis & Ranked Recommendations: BgRemover

## Rating Scale

| Symbol | Priority | Meaning |
|--------|----------|---------|
| 🔴 | Critical | Bugs, crashes, or data loss |
| 🟠 | High | Clear impact on reliability or maintainability |
| 🟡 | Medium | Useful improvement for quality, readability, or testability |
| 🟢 | Low | Optional polish or process improvement |

## Current Status (2026-07-13)

The active code-analysis list is empty. Ruff, mypy, and the local test suite
remain the baseline before new PRs. Release **v2.5.0** was cut on 2026-07-11
(PR #538); the rollout wave **#435/#392/#426/#389** is closed, as is **#299**
(PR #539) with N13 follow-up **#541** (PR #543), **#318** (PR #540), and the
snapshot sync **#542**. A repo audit on 2026-07-12 filed **#549–#553**;
**#552/#549/#553/#550** are now closed via PR #557–#560. Since the last
snapshot (#245, #551), epic **#563** ("app update check & AI model
management") with eight sub-issues (**#564–#571**) was filed on 2026-07-13.
Live state: **11** open issues – #245, #551, #563–#571.

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

### Still Open

- **O8 🟢 — Prototype inaccuracy:** height tools stay locked in the mockup
  after generation; mockup-only, the real app is unaffected (#347).

## Open GitHub Issues — Triage Status (2026-07-13)

Live state: **11** open issues – two pre-existing CI/security issues
(**#245**, **#551**) plus epic **#563** with eight sub-issues
(**#564–#571**) for two independent groups: app update (#564–#567) and AI
model management (#568–#571). All comments reviewed – existing owner triage
notes from 2026-07-13 already cover ordering/scope; no issue description
needed editing.

### Sensible Bundles

#245/#551 are linked (Codex scan: account action vs. strategic decision).
The eight #563 sub-issues form two internally sequential but mutually
independent chains: **app update** (#564→#565→#566→#567) and **AI model
download** (#568→#569→#570→#571) – confirmed by the issue author on
2026-07-13 (comments on #563/#569/#570).

Rating: **Relevance** = importance to the roadmap/users, **Complexity** =
estimated implementation effort, **Model/Effort** = the recommended Claude
model and reasoning effort.

| # | Title | Relevance | Complexity | Model/Effort | Recommended next step |
|---|-------|-----------|------------|---------------|-----------------------|
| [#563](https://github.com/NikolayDA/picture_helper/issues/563) | Epic: menu extension app update & AI model management | 🟠 High | 🟠 High (8 sub-issues) | – (pure tracking) | **Blocked (on sub-issues)** – closes automatically with #564–#571; order captured in the owner comment from 2026-07-13. |
| [#564](https://github.com/NikolayDA/picture_helper/issues/564) | App update: update-check core logic (`app_update.py`) | 🟠 High | 🟢 Low (size S, no dependencies) | Sonnet 5 · low–medium | **Ready for PR** – Qt-free, strictly typed, clear acceptance criteria. |
| [#565](https://github.com/NikolayDA/picture_helper/issues/565) | App update: menu/dialog integration "Check for updates…" | 🟠 High | 🟡 Medium (size S–M, async QThread + i18n) | Sonnet 5 · medium | **Needs #564** – ready for a PR right after. |
| [#566](https://github.com/NikolayDA/picture_helper/issues/566) | App update: optional automatic startup check | 🟡 Medium | 🟢 Low (size S) | Sonnet 5 · low | **Needs #564+#565**. |
| [#567](https://github.com/NikolayDA/picture_helper/issues/567) | App update: docs wrap-up + i18n governance | 🟢 Low | 🟢 Low (size XS) | Sonnet 5 · low | **Needs #564–#566 merged**. |
| [#568](https://github.com/NikolayDA/picture_helper/issues/568) | AI model download: status detection (Qt-free) | 🟠 High | 🟢 Low (size S, no dependencies) | Sonnet 5 · low–medium | **Ready for PR** – Qt-free, strictly typed, clear acceptance criteria. |
| [#569](https://github.com/NikolayDA/picture_helper/issues/569) | AI model download: menu/dialog integration "Manage AI model…" | 🟠 High | 🟡 Medium (size M, dialog+progress+cancel mocked) | Sonnet 5 · medium | **Needs #568** – a mocked download/cancel path is sufficient (2026-07-13 scope clarification). |
| [#570](https://github.com/NikolayDA/picture_helper/issues/570) | AI model download: wiring into existing warmup/WorkerController | 🟠 High | 🟡 Medium–High (size S–M, new `cancel_warmup()` hook needed) | Sonnet 5 · medium–high | **Needs #568+#569**. |
| [#571](https://github.com/NikolayDA/picture_helper/issues/571) | AI model download: docs wrap-up + i18n governance | 🟢 Low | 🟢 Low (size XS) | Sonnet 5 · low | **Needs #568–#570 merged**. |
| [#551](https://github.com/NikolayDA/picture_helper/issues/551) | Codex Security Scan strategy decision (reactivate/decommission/replace) | 🟡 Medium | 🟡 Medium | Sonnet 5 · medium | **Needs refinement** – choice among three options; recommendation: option 2 (decommission/disable) given weeks of external blockage and redundancy with pip-audit/license/CI. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan "Quota exceeded" | 🟡 Medium | 🟢 Low | – (no code task) | **Blocked (external)** – restoring OpenAI billing/quota is an account action, not a PR. |

### Recommended Next (PR order)

1. **#564+#568** — implement the Qt-free core logic first & in parallel
   (mutually independent, no open dependencies, fully PR-ready).
2. **#565+#569** — menu/dialog integration per group once the core logic
   merges (a mocked download/check path is sufficient).
3. **#566+#570** — startup check / warmup wiring respectively; #570 also
   needs a new `cancel_warmup()` hook per the owner comment (2026-07-13).
4. **#567+#571** — docs wrap-up per group (XS, trivial).
5. **#551** — get a decision on the scan strategy (linked to #245), then
   adjust the workflow.
6. **#245** — stays externally blocked; verify manually only after the
   OpenAI quota is restored.

*Drift note:* re-check the live open-issue count before every future update
instead of carrying it forward (#542 → #549 hit the same off-by-one).

## Previous Rounds

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
