[Deutsch](../../../RECOMMENDATIONS.md) · **English** · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Code Analysis & Ranked Recommendations: BgRemover

## Rating Scale

| Symbol | Priority | Meaning |
|--------|----------|---------|
| 🔴 | Critical | Bugs, crashes, or data loss |
| 🟠 | High | Clear impact on reliability or maintainability |
| 🟡 | Medium | Useful improvement for quality, readability, or testability |
| 🟢 | Low | Optional polish or process improvement |

## Current Status (2026-07-22)

Ruff, mypy, and the local test suite remain the baseline before new PRs. Since the last round, **#640–#645** and **#648** have been fully accepted and closed (hardware evidence from the 2026-07-21 `release-abnahme.yml` dispatch; the acceptance-matrix comment on #595 shows macOS-arm64 and Pi-5 smokes, native 3D E2E, and live GL performance all **✅ met**). Live state per GitHub query: **6** open issues — the lowest since the 3D epic began.

### Review Result

- **Old baseline stable:** **N1/N2/N4/N5/N6/N7/N8**, **O1–O7**, and everything completed since **2026-06-25** remain done.
- Epic **#639** is done for 7 of its 8 sub-issues; its issue-body checklist still had every box unchecked even though #640–#645/#648 had long been closed — reconciled today (comment + body edit on #639), no code affected.
- **No issue currently qualifies as "ready for PR"** in the classic sense: all six remaining open issues are either purely external/operational tasks (set a secret, resolve billing) or epics that are blocked exclusively on those same external tasks. There is no open, code-side-unaddressed task right now.
- The one remaining blocker for the entire chain: repository secret `ANTHROPIC_API_KEY` is missing (**#656**), so the acceptance-matrix row "Screenshots (vision pre-assessment)" still shows `❓ unassessed` instead of real verdicts. The fail-safe path itself works exactly as designed.

## Open GitHub Issues — Triage Status (2026-07-22)

| # | Title | Relevance | Complexity | Recommended model (effort) | Next step |
|---|-------|-----------|------------|------------------------------|-----------|
| [#656](https://github.com/NikolayDA/picture_helper/issues/656) | Enable ANTHROPIC_API_KEY secret for the vision pre-assessment | 🟠 High (last blocker of the whole acceptance chain) | 🟢 Low (purely operational, no code) | – (no agent; repo owner: Settings → Secrets) | Blocked (external) – set the secret, then re-check the dispatch |
| [#646](https://github.com/NikolayDA/picture_helper/issues/646) | Vision pre-assessment, evidence aggregation, acceptance matrix | 🟠 High (last open sub-issue of epic #639) | 🟢 Low (code/tests already merged in PR #649) | Sonnet 5 (low) – verification only, no new code expected | Needs verification – after #656, check a real vision dispatch, then close |
| [#639](https://github.com/NikolayDA/picture_helper/issues/639) | [Epic] Automated release acceptance | 🟠 High (epic, 7/8 sub-issues done) | 🟢 Low (only #646 remains) | – (epic, no direct agent use) | Blocked – closes automatically with #646 |
| [#595](https://github.com/NikolayDA/picture_helper/issues/595) | [3D] Performance, packaging, docs, end-to-end acceptance | 🟠 High (acceptance gate for epic #582) | 🟢 Low (all criteria met except the vision row) | – (no code task) | Blocked – waits on #646/#656, then close |
| [#582](https://github.com/NikolayDA/picture_helper/issues/582) | [Epic] Real 3D relief preview | 🟠 High (large, nearly finished feature epic) | 🟢 Low (only #595 remains) | – (epic, no direct agent use) | Blocked – closes automatically with #595 |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restore OpenAI quota for the manual Codex security check | 🟢 Low (blocks only an optional manual scan) | 🟢 Low (purely operational, no code) | – (no agent; repo owner: billing) | Blocked (external) – resolve billing/quota on the OpenAI platform project |

### Recommended Next

1. Resolve **#656** first (set repository secret `ANTHROPIC_API_KEY`) — the single remaining lever that unblocks the whole chain #646 → #639 → #595 → #582.
2. Then dispatch `release-abnahme.yml` again via `workflow_dispatch` and check whether the acceptance matrix's vision row shows real verdicts instead of `unassessed` (spot-check a couple against the screenshots, as #656 requires).
3. Once the vision row is green, close **#646**; that cascades to close **#639**, **#595**, and **#582** (briefly re-verify each before closing manually).
4. Leave **#245** as a purely external billing/quota tracker; no action possible or needed in the repository.
5. There is currently **no** open issue that justifies a new code PR — the next sensible agent task is verification after #656, not new implementation.

## Previous Rounds

- **2026-07-22 (issue review)** — full reassessment of all open issues: #640–#645 and #648 had already been accepted and closed via the 2026-07-21 acceptance dispatch, but epic #639's sub-issue checklist had not been reconciled (fixed today via issue edit + comment, no code affected). New blocker **#656** (missing `ANTHROPIC_API_KEY` secret) identified as the sole remaining lever for #646/#639/#595/#582. Live state 6 open issues — the lowest since epic #582.
- **2026-07-21 (release acceptance automation, epic #639)** — epic #639 opened and largely implemented within a single day: ADR/docs (#640), workflow skeleton (#641), Linux/macOS hardware smokes (#642/#643), E2E regression test (#644), live-GL performance suite (#645), vision pre-assessment + acceptance matrix (#646) — all merged via PR #647/#649 but not auto-closed due to German closing keywords; follow-up issue #648 (native 3D render proof) remains the only open code task. Live state 12 open issues.
- **2026-07-20 (Pi 5 hardware smoke)** — three real packaging bugs found and fixed on Raspberry Pi 5 (PR #627/#631); the app is confirmed to start including the 3D preview.
- **2026-07-18 (post-merge audit)** — confirmed #551 and #592–#594 complete; reopened #582/#595 for missing packaging/platform, performance, and screenshot evidence; live state 3.
- **2026-07-18 (audit follow-up #614–#616)** — recorded future-version hardening from PR #614; #597/#598 completed through PR #615 and #606 through PR #616; live state 7.
- **2026-07-17 (16-bit epic completion)** — #581/#587–#590 completed through PR #610/#612/#613; all PR gates and reviews green, acceptance matrix present, live state 10.
- **2026-07-16 (release v2.6.0)** — tag on `f24cef69829da8e37aa400dad471dc4d607b89b3`, release run 29531147950 green, five public artifacts freshly downloaded and verified by SHA-256; #580/#585/#607 closed, live state 15.
- **2026-07-16 (candidate gate)** — #584 closed through the real five-artifact gate (final gate run 29529595934 on `f24cef69829da8e37aa400dad471dc4d607b89b3`, SHA-256 + secret scan per artifact, native platform smokes); #585 unblocked.
- **2026-07-15/16 (audit follow-up)** — #583/#586/#591 completed; #584 reopened after confirming that the candidate gate is still outstanding; live state 17.
- **2026-07-14** — live state still 2 open issues (#245, #551), unchanged since the epic completion the day before.
- **2026-07-13 (epic completion)** — epic **#563** fully closed: all eight sub-issues (**#564–#571**) closed through PR #573/#574; snapshot reduced to 2.
- **2026-07-13 (issue audit)** — epic **#563** + eight sub-issues filed, all 11 open issues re-assessed, owner comments taken into account; no issue closed; snapshot updated to 11.
- **2026-07-12** — v2.3.0 formalization (#550), SessionStart hook fix (#553), snapshot sync (#549, PR template #552 via PR #557), issue audit (#542 closed, #549–#553 filed), and release **v2.5.0** (rollout wave #435/#392/#426/#389, #299/#541/#318).
- **2026-07-11** — epic #425 fully closed (#430 PR #526, full runtime i18n ES/FR/UK/ZH, **O1** done; #431/#432 PR #529; final follow-up #530/#531 PR #533/#535).
- **2026-07-05–10** — #509/#510/#514–#517 (PR #520–#522), #490, Dark Mode/rail-icon wave, card inspector (#413/#414), #499–#501/#503, icon/status-bar polish.
- **2026-06-29** — #404/#406/#408 completed (PR #412), redesign wave opened.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, completed or discarded where it was a false positive.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
