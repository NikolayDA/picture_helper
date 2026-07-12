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
(PR #540) and the recommendations-snapshot sync **#542**. A repo audit on
2026-07-12 filed five new findings as issues (**#549–#553**); GitHub
currently shows **6** open issues: **#245** plus **#549–#553**.

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
  (PR #543), **#318** (PR #540), and the recommendations-snapshot sync
  **#542**. All redesign/release/backlog items from the last snapshot are
  thereby cleared.

### Still Open

- **O8 🟢 — Prototype inaccuracy:** height tools stay locked in the mockup
  after generation; mockup-only, the real app is unaffected (#347).

## Open GitHub Issues — Triage Status (2026-07-12)

As of 2026-07-12, GitHub shows **6** open issues: the external
quota/billing blocker **#245** plus five new findings from the ongoing repo
audit — **#549** (recommendations snapshot), **#550** (v2.3.0 tag/release
consistency), **#551** (Codex Security Scan strategy decision), **#552**
(PR template), and **#553** (SessionStart hook verification).

### Sensible Bundles

#245 and #551 are content-linked (Codex scan): #245 is a pure account
action, while #551 needs its own strategic decision
(reactivate/decommission/replace). #550 also needs a decision first
(tag+release vs. docs-only clarification). #549 (this PR), #552, and #553
are independent and can proceed right away.

Rating: **Relevance** = importance to the roadmap/users, **Complexity** =
estimated implementation effort, **Model/Effort** = the recommended Claude
model and reasoning effort for Claude Code to implement it.

| # | Title | Relevance | Complexity | Model/Effort | Recommended next step |
|---|-------|-----------|------------|---------------|-----------------------|
| [#552](https://github.com/NikolayDA/picture_helper/issues/552) | Add PR template with standard-gate checklist | 🟡 Medium | 🟢 Low | Sonnet 5 · low | **Ready for PR** – a single new file, no dependencies. |
| [#553](https://github.com/NikolayDA/picture_helper/issues/553) | Verify SessionStart hook reliability in web sessions | 🟡 Medium | 🟡 Medium | Sonnet 5 · medium | **Ready for PR** – reproduce in a fresh web session, then fix + document as needed. |
| [#549](https://github.com/NikolayDA/picture_helper/issues/549) | Refresh recommendations snapshot to the live state | 🟢 Low | 🟢 Low | Sonnet 5 · low | **Ready for PR** – covered by this snapshot sync. |
| [#550](https://github.com/NikolayDA/picture_helper/issues/550) | v2.3.0: reconcile CHANGELOG with tag/release history | 🟡 Medium | 🟡 Medium | Sonnet 5 · medium | **Needs refinement** – variant A (tag+release) vs. B (docs-only clarification) needs a decision before implementation. |
| [#551](https://github.com/NikolayDA/picture_helper/issues/551) | Codex Security Scan strategy decision (reactivate/decommission/replace) | 🟡 Medium | 🟡 Medium | Sonnet 5 · medium | **Needs refinement** – needs a deliberate choice among three options; recommendation: option 2 (decommission/disable) given weeks of external blockage and redundancy with pip-audit/license/CI. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan "Quota exceeded" | 🟡 Medium | 🟢 Low | – (no code task) | **Blocked (external)** – restoring OpenAI billing/quota is an account action, not a PR. |

### Recommended Next (PR order)

1. **#552** — add the PR template (self-contained, low risk).
2. **#549** — close with this PR (snapshot sync across all six mirrors,
   including #550–#553).
3. **#553** — reproduce the SessionStart hook behavior in a fresh web
   session and fix as needed.
4. **#550** — get a decision on variant A/B, then adjust the
   CHANGELOG/tag/release.
5. **#551** — get a decision on the scan strategy (linked to #245), then
   adjust the workflow.
6. **#245** — stays externally blocked; verify manually only after the
   OpenAI quota is restored.

## Previous Rounds

- **2026-07-12 (issue audit)** — #542 (recommendations snapshot) closed; a
  repo audit filed five new issues (#549–#553: docs snapshot, release tag
  consistency, security-scan strategy decision, PR template, SessionStart
  hook verification); open-issue snapshot updated to 6 (#245 + #549–#553).
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
- **2026-07-05/06** — #490 (snapshot drift), Dark Mode/rail-icon wave, card
  inspector (#413/#414), #499–#501/#503 (PR #504/#506), and icon/status-bar
  polish (PR #507/#508) completed.
- **2026-06-29** — #404/#406/#408 completed (PR #412), redesign wave opened.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, completed or discarded where it was a false positive.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
