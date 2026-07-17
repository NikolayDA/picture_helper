[Deutsch](../../../RECOMMENDATIONS.md) · **English** · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Code Analysis & Ranked Recommendations: BgRemover

## Rating Scale

| Symbol | Priority | Meaning |
|--------|----------|---------|
| 🔴 | Critical | Bugs, crashes, or data loss |
| 🟠 | High | Clear impact on reliability or maintainability |
| 🟡 | Medium | Useful improvement for quality, readability, or testability |
| 🟢 | Low | Optional polish or process improvement |

## Current Status (2026-07-18)

The active code-analysis list is empty. Ruff, mypy, and the local test suite remain the baseline before new PRs. Release **v2.6.0** was published on 2026-07-16 from approved commit `f24cef69829da8e37aa400dad471dc4d607b89b3`: tag workflow [29531147950](https://github.com/NikolayDA/picture_helper/actions/runs/29531147950), public [GitHub release](https://github.com/NikolayDA/picture_helper/releases/tag/v2.6.0), five freshly downloaded application artifacts verified by SHA-256, and green native platform smokes for Linux x86_64/aarch64 and macOS arm64. Release issues **#580/#583/#584/#585**, stale-snapshot finding **#607**, and the full 16-bit height pipeline **#581/#587–#590** are complete. The live state is **7** open issues: #245/#551 and 3D epic **#582** with #592–#595.

### Completed Since The Last Review

- **Old baseline stable:** **N1/N2/N4/N5/N6/N7/N8** and **O2–O7** remain done; epics **#329/#344/#358/#384** (N9–N12) plus export fix **#363** are merged/archived; since 2026-06-25 also **#404/#406/#408** (PR #412) closed.
- **Redesign & release v2.5.0:** redesign core/rail/zoom/card inspector/Dark Mode/UI follow-up (**#413/#414/#455–#464/#474–#489/#499–#501/#503/#509/#510/#514–#517**, **#490**, **#433/#434**) via PR #412–#522; release wave **#435/#392/#426/#389** (v2.5.0), **#299/#541/#318/#542**, PR template **#552**, snapshot sync **#549**, SessionStart fix **#553**, v2.3.0 formalization **#550** – all closed since 2026-07-12.
- **N14 — Epic #563 (app update & AI model management) fully closed:** `app_update.py` (#564), `ai_model_status.py` (#568), menu/dialog integration (#565/#569), optional automatic startup check (#566), warmup wiring with multiple observers/cooperative cancellation (#570) via PR #573/#574; docs wrap-up (#567/#571).
- **Release v2.6.0 fully complete:** scope freeze (#583), candidate gate on the final `main` SHA (#584), tag/release/post-release verification (#585), and tracking epic #580 are done; this update resolves snapshot drift #607. The 16-bit HEIGHT ADR (#586) and 3D ADR/UX contract (#591, PR #603) also remain complete.
- **16-bit height pipeline fully complete:** domain model/history and project format v2 (#587/#588, PR #610), import/generation/operations (#589, PR #612), and preview/export/UI/E2E (#590, PR #613) are on `main`; epic #581 is closed after green PR gates, resolved reviews, and a complete acceptance matrix.
- **Audit follow-up #614–#616 complete:** future versions now fail closed (#588, PR #614), coverage gaps #597/#598 are closed through PR #615, and guide gap #606 is fixed in all six language versions through PR #616.

### Still Open

- **O8 🟢 — Prototype inaccuracy:** height tools stay locked in the mockup after generation; mockup-only, the real app is unaffected (#347).

## Open GitHub Issues — Triage Status (2026-07-18)

Live state after merging PR #614/#615/#616: **7** open issues. **#581/#587–#590**, **#597/#598**, and **#606** are complete. The 2026-07-15 owner comments on **#245**/**#551** and their tightened issue bodies remain current.

### Sensible Bundles

- **3D relief preview** (#582 → #592 → #593 → #594 → #595; #591 and the 16-bit prerequisites are complete): #592 is the next executable step; #594 now waits only on #593.
- **#245/#551** remain linked, but the strategic decision is now made: #551 tracks only the implementation of the hybrid model (CodeQL automatic, Codex manual), #245 tracks only the external OpenAI quota proof.

Rating: **Relevance** = importance to the roadmap/users, **Complexity** = estimated implementation effort, **Model/Effort** = the recommended Claude model and reasoning effort.

| # | Title | Relevance | Complexity | Model/Effort | Recommended next step |
|---|-------|-----------|------------|---------------|-----------------------|
| [#592](https://github.com/NikolayDA/picture_helper/issues/592) | [3D] Qt-free geometry/normal/decimation pipeline | 🟡 Medium | 🟠 High (very large) | Opus 4.8 · high | **Ready for PR** – #586 and #591 are complete; no open dependency remains. |
| [#593](https://github.com/NikolayDA/picture_helper/issues/593) | [3D] Interactive viewer with orbit/pan/zoom, fallback | 🟡 Medium | 🟠 High (very large) | Opus 4.8 · xhigh | **Blocked** – waits on #592; the riskiest piece (platform-specific Qt/OpenGL). |
| [#594](https://github.com/NikolayDA/picture_helper/issues/594) | [3D] Workflow, state, and cache integration | 🟡 Medium | 🟠 High (very large) | Opus 4.8 · high | **Blocked** – waits on #593; the 16-bit prerequisites #587/#588 are complete. |
| [#595](https://github.com/NikolayDA/picture_helper/issues/595) | [3D] Performance, packaging, docs, end-to-end acceptance | 🟡 Medium | 🟠 High | Sonnet 5 · high | **Blocked** – waits on #594. |
| [#582](https://github.com/NikolayDA/picture_helper/issues/582) | [Epic] Real 3D relief preview | 🟡 Medium | 🟠 High (very large) | – (tracking epic) | **In progress** – runs via #592→…→#595; #591 is complete. |
| [#551](https://github.com/NikolayDA/picture_helper/issues/551) | Automate CodeQL, run Codex Security manually only | 🟡 Medium | 🟡 Medium | Sonnet 5 · medium | **Ready for PR** – strategic decision made on 2026-07-15 (hybrid model: CodeQL automatic + Codex manual via `workflow_dispatch`); the issue body already has the full implementation checklist. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restore OpenAI quota for the manual Codex security check | 🟢 Low | 🟢 Low | – (no code task) | **Blocked (external)** – scope narrowed further on 2026-07-15: purely an external OpenAI billing/quota tracker, blocks neither CodeQL nor the release nor #551. |

### Recommended Next (PR order)

1. **#592** — start the 3D geometry pipeline; #586, #591, and the 16-bit prerequisites are complete.
2. **#551** — implement the agreed hybrid model (CodeQL automatic, Codex manual only via `workflow_dispatch`).

*Drift note:* this update removes #597/#598/#606 from open triage after PR #615/#616 merged and corrects the live count to 7. Future updates keep rechecking statuses, checklists, and dependencies live instead of carrying a timestamp forward.

## Previous Rounds

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
