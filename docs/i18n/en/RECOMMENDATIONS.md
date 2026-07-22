[Deutsch](../../../RECOMMENDATIONS.md) · **English** · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Code Analysis & Ranked Recommendations: BgRemover

## Rating Scale

| Symbol | Priority | Meaning |
|--------|----------|---------|
| 🔴 | Critical | Bugs, crashes, or data loss |
| 🟠 | High | Clear impact on reliability or maintainability |
| 🟡 | Medium | Useful improvement for quality, readability, or testability |
| 🟢 | Low | Optional polish or process improvement |

## Current Status (2026-07-22, corrected after Codex review)

Ruff, mypy, and the local test suite remain the baseline before new PRs. Since the last round, **#640–#645** and **#648** have been closed. An earlier version of this update relied solely on the 2026-07-21 `release-abnahme.yml` dispatch (commit `fa2241d`) and wrongly framed the vision row (#656) as the sole blocker of the chain — a PR review (Codex) refuted four points of that, corrected here:

1. **The dispatch evidence was already stale.** PR #657 (resolves #642, merged `521bd63`, after `fa2241d`) makes `waechter_ergebnisse` a required field in `abnahme_aggregate.py::validate_evidence`, and PR #658 (resolves #644, merged `4416e80`) adds missing E2E assertions. The cited dispatch ran **before** both fixes, so its "✅ met" rows do not evidence today's code. A fresh dispatch against current `main` is needed before the matrix can be cited as valid proof.
2. **Vision pre-assessment is advisory, not a blocker.** `abnahme_aggregate.py::has_blocking_gaps` explicitly exempts only the "Screenshots (vision pre-assessment)" row from blocking when `unassessed` (`docs/RELEASE_AUTOMATION.md` §4: "without `ANTHROPIC_API_KEY`, every criterion stays unassessed and never blocks"). **#656** is a worthwhile evidence-quality improvement, but **not** a blocker for #646, #639, #595, or #582.
3. **Linux x86_64 remains an open criterion, not merely a paused one.** Per the ADR/`RELEASE_AUTOMATION.md` §5, the paused x86_64 hardware smoke is explicitly treated as "declared open, not met" for release decisions — a deliberately accepted but still-open item, not a completed row.
4. **No epic auto-closes.** Closing #646 only updates #639's sub-issue progress on GitHub; #639, #595, and #582 each need to be manually reviewed and closed individually.

Live state per GitHub query: **6** open issues.

### Review Result

- **Old baseline stable:** **N1/N2/N4/N5/N6/N7/N8**, **O1–O7**, and everything completed since **2026-06-25** remain done.
- Epic **#639** is done for 7 of its 8 sub-issues; its issue-body checklist still had every box unchecked even though #640–#645/#648 had long been closed — reconciled (comment + body edit on #639); that body edit also overstated the dispatch evidence and is being corrected via a follow-up comment.
- **No issue currently qualifies as "ready for PR"** in the classic sense: all six remaining open issues are either purely external/operational tasks (set a secret, resolve billing) or epics that fundamentally wait on a fresh, valid acceptance dispatch and the documented x86_64 pause.
- The actual remaining step is **not** a missing secret — it's a fresh `release-abnahme.yml` dispatch against current `main` (post #657/#658), whose matrix then needs to be checked against #595's criteria including the deliberately open x86_64 row.

## Open GitHub Issues — Triage Status (2026-07-22)

| # | Title | Relevance | Complexity | Recommended model (effort) | Next step |
|---|-------|-----------|------------|------------------------------|-----------|
| [#646](https://github.com/NikolayDA/picture_helper/issues/646) | Vision pre-assessment, evidence aggregation, acceptance matrix | 🟠 High (last open sub-issue of epic #639) | 🟢 Low (code/tests already merged in PR #647/#649/#657) | Sonnet 5 (low) – verification against a fresh dispatch only, no new code expected | Needs verification – its own acceptance criteria do **not** depend on #656 (the vision fail-safe is already evidenced); close after a fresh dispatch |
| [#639](https://github.com/NikolayDA/picture_helper/issues/639) | [Epic] Automated release acceptance | 🟠 High (epic, 7/8 sub-issues done) | 🟢 Low (only #646 remains) | – (epic, no direct agent use) | Blocked – does **not** auto-close with #646; review and close manually once #646 is done |
| [#595](https://github.com/NikolayDA/picture_helper/issues/595) | [3D] Performance, packaging, docs, end-to-end acceptance | 🟠 High (acceptance gate for epic #582) | 🟡 Medium (vision is advisory-satisfied, but the x86_64 criterion remains declared open) | – (no code task) | Blocked – waits on a fresh, valid dispatch post #657/#658 and an explicit decision on the x86_64 pause |
| [#582](https://github.com/NikolayDA/picture_helper/issues/582) | [Epic] Real 3D relief preview | 🟠 High (large, nearly finished feature epic) | 🟢 Low (only #595 remains) | – (epic, no direct agent use) | Blocked – does **not** auto-close with #595; review and close manually afterward |
| [#656](https://github.com/NikolayDA/picture_helper/issues/656) | Enable ANTHROPIC_API_KEY secret for the vision pre-assessment | 🟡 Medium (only improves evidence quality; not a blocker per contract) | 🟢 Low (purely operational, no code) | – (no agent; repo owner: Settings → Secrets) | Blocked (external) – can be done independently of the rest of the chain |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restore OpenAI quota for the manual Codex security check | 🟢 Low (blocks only an optional manual scan) | 🟢 Low (purely operational, no code) | – (no agent; repo owner: billing) | Blocked (external) – resolve billing/quota on the OpenAI platform project |

### Recommended Next

1. Trigger a fresh `release-abnahme.yml` dispatch against current `main` (post #657/#658) — the previously cited 2026-07-21 matrix no longer evidences today's code.
2. Check the new matrix against **all** of #595's criteria, including the deliberately open x86_64 row (stays "paused/declared open" even if everything else is green) — clarify explicitly whether #595 may close with a documented x86_64 pause (as #639 already allows for itself) or needs a separate sign-off.
3. Check **#646** against its own acceptance criteria (the fail-safe behavior is already evidenced and does not depend on #656) and close it if met; then review and close **#639** separately and manually, followed by **#595** and **#582** — no issue auto-closes with another.
4. Handle **#656** independently if real vision verdicts are wanted — it's a quality improvement, not a blocker.
5. Leave **#245** as a purely external billing/quota tracker; no action possible or needed in the repository.
6. There is currently **no** open issue that justifies a new code PR — the next sensible agent task is verification after a fresh dispatch, not new implementation.

## Previous Rounds

- **2026-07-22 (issue review, corrected after Codex review)** — full reassessment of all open issues; an earlier version overstated what the 2026-07-21 dispatch proved (since superseded by PR #657/#658) and wrongly framed the advisory vision row (#656) as a blocker. Corrected after PR review (Codex): #656 can be resolved independently, Linux x86_64 remains a declared-open criterion, and #639/#595/#582 do not auto-close with their sub-issues. Live state 6 open issues — the lowest since epic #582.
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
