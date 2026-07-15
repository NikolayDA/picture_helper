[Deutsch](../../../RECOMMENDATIONS.md) · **English** · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Code Analysis & Ranked Recommendations: BgRemover

## Rating Scale

| Symbol | Priority | Meaning |
|--------|----------|---------|
| 🔴 | Critical | Bugs, crashes, or data loss |
| 🟠 | High | Clear impact on reliability or maintainability |
| 🟡 | Medium | Useful improvement for quality, readability, or testability |
| 🟢 | Low | Optional polish or process improvement |

## Current Status (2026-07-16)

The active code-analysis list is empty. Ruff, mypy, and the local test suite remain the baseline before new PRs. Release **v2.5.0** was cut on 2026-07-11 (PR #538); the rollout wave **#435/#392/#426/#389** is closed, as is **#299** (PR #539) with N13 follow-up **#541** (PR #543), **#318** (PR #540), and the snapshot sync **#542**. A repo audit on 2026-07-12 filed **#549–#553**; **#552/#549/#553/#550** are now closed via PR #557–#560. Epic **#563** ("app update check & AI model management", eight sub-issues **#564–#571**) was fully implemented and closed on 2026-07-13 via PR #573/#574 (**N14**). Live state: **17** open issues – the pre-existing #245/#551 plus three epics filed on 2026-07-15 (**Release v2.6.0** #580, the **16-bit height pipeline** #581, the **3D relief preview** #582) with their remaining open sub-issues, plus two test-coverage findings **N15/N16** (#597/#598). **#583** (v2.6.0 scope freeze), **#586** (16-bit ADR), and **#591** (3D ADR/UX contract, PR #603) are complete. **#584** was reopened in the 2026-07-16 live audit: PRs #601–#604 harden artifact naming and release reuse, but the actual candidate gate with a final SHA, five real artifacts, checksums, platform smokes, and a Go/No-Go decision is still outstanding.

### Completed Since The Last Review

- **Old baseline stable:** **N1/N2/N4/N5/N6/N7/N8** and **O2–O7** remain done; epics **#329/#344/#358/#384** (N9–N12) plus export fix **#363** are merged/archived; since 2026-06-25 also **#404/#406/#408** (PR #412) closed.
- **Redesign & release v2.5.0:** redesign core/rail/zoom/card inspector/Dark Mode/UI follow-up (**#413/#414/#455–#464/#474–#489/#499–#501/#503/#509/#510/#514–#517**, **#490**, **#433/#434**) via PR #412–#522; release wave **#435/#392/#426/#389** (v2.5.0), **#299/#541/#318/#542**, PR template **#552**, snapshot sync **#549**, SessionStart fix **#553**, v2.3.0 formalization **#550** – all closed since 2026-07-12.
- **N14 — Epic #563 (app update & AI model management) fully closed:** `app_update.py` (#564), `ai_model_status.py` (#568), menu/dialog integration (#565/#569), optional automatic startup check (#566), warmup wiring with multiple observers/cooperative cancellation (#570) via PR #573/#574; docs wrap-up (#567/#571).
- **#583/#586/#591 complete, #584 reopened:** the v2.6.0 scope freeze/version/CHANGELOG curation (#583), 16-bit HEIGHT ADR (#586), and 3D ADR/UX contract (#591, PR #603) are complete. #584 remains open until the full candidate gate is evidenced.

### Still Open

- **Release gate #584 🟠:** record the final candidate SHA, build five real artifacts in the non-publishing workflow, document checksums and platform smokes, and make the Go/No-Go decision.
- **O8 🟢 — Prototype inaccuracy:** height tools stay locked in the mockup after generation; mockup-only, the real app is unaffected (#347).
- **N15 🟡 — Untested dialog wiring:** `MainWindow._open_ai_install_dialog` (`main_window.py:1566`) has no dedicated test, unlike the structurally identical sibling method `_open_ai_model_dialog` (#597).
- **N16 🟡 — Untested non-RGBA conversion:** the non-RGBA branches in `pil_to_qpixmap`/`pil_to_numpy_readonly` (`image_utils.py:16`/`:43`) are never exercised with an RGB/palette/grayscale source image (#598).

## Open GitHub Issues — Triage Status (2026-07-16)

Live state: **17** open issues. **#591** is complete through PR #603; **#584** was reopened after the audit because the full candidate gate remains outstanding, and **#585** therefore stays blocked. The 2026-07-15 owner comments on **#245**/**#551** and their tightened issue bodies remain current.

### Sensible Bundles

- **Release v2.6.0** (#580 → #584 → #585; #583 is already closed): ships the already-built update/AI-management state from `main`; top priority given low risk and immediate user value.
- **16-bit height pipeline** (#581 → #587 → {#588 ‖ #589} → #590; the #586 ADR is already closed): schema-changing implementation (#587+) still only starts after #585 (per #580's scope-freeze mandate).
- **3D relief preview** (#582 → #592 → #593 → #594 → #595; #591 is complete): the Qt-free geometry pipeline #592 can now start in parallel with the 16-bit model work; #582 remains the largest effort block this round regardless.
- **#245/#551** remain linked, but the strategic decision is now made: #551 tracks only the implementation of the hybrid model (CodeQL automatic, Codex manual), #245 tracks only the external OpenAI quota proof.
- **#597/#598** are independent, fully specified coverage gaps (test sketch already in the issue) – no chain, no dependency on the three epics.

Rating: **Relevance** = importance to the roadmap/users, **Complexity** = estimated implementation effort, **Model/Effort** = the recommended Claude model and reasoning effort.

| # | Title | Relevance | Complexity | Model/Effort | Recommended next step |
|---|-------|-----------|------------|---------------|-----------------------|
| [#580](https://github.com/NikolayDA/picture_helper/issues/580) | [Epic] Release v2.6.0 | 🟠 High | 🟠 High | – (tracking epic) | **In progress** – runs via #584→#585 (#583 closed), no PR of its own. |
| [#584](https://github.com/NikolayDA/picture_helper/issues/584) | Release 2.6.0: candidate gate, five artifacts | 🟠 High | 🟠 High | Sonnet 5 · high | **In progress (reopened)** – fix the final candidate SHA, run the non-publishing five-artifact build with checksums/smokes, and document Go/No-Go. |
| [#585](https://github.com/NikolayDA/picture_helper/issues/585) | Release 2.6.0: tag, GitHub release, post-release check | 🟠 High | 🟡 Medium | Sonnet 5 · medium | **Blocked** – waits on #584. |
| [#587](https://github.com/NikolayDA/picture_helper/issues/587) | [16-bit] HEIGHT domain model & ProjectHistory, lossless | 🟠 High | 🟠 High (very large) | Opus 4.8 · high | **Blocked** – #586 is closed; now only waits on the release being published (#585). |
| [#588](https://github.com/NikolayDA/picture_helper/issues/588) | [16-bit] Project format v2: persistence, migration, validation | 🟠 High | 🟠 High | Opus 4.8 · high | **Blocked** – waits on #587. |
| [#589](https://github.com/NikolayDA/picture_helper/issues/589) | [16-bit] Import/generation/height ops without 8-bit quantization | 🟠 High | 🟠 High | Opus 4.8 · high | **Blocked** – waits on #587. |
| [#590](https://github.com/NikolayDA/picture_helper/issues/590) | [16-bit] Preview, export, UI, end-to-end acceptance | 🟠 High | 🟠 High | Opus 4.8 · high | **Blocked** – waits on #588/#589. |
| [#581](https://github.com/NikolayDA/picture_helper/issues/581) | [Epic] Full 16-bit height pipeline | 🟠 High | 🟠 High (very large) | – (tracking epic) | **In progress** – runs via #587→(#588‖#589)→#590 (#586 closed). |
| [#592](https://github.com/NikolayDA/picture_helper/issues/592) | [3D] Qt-free geometry/normal/decimation pipeline | 🟡 Medium | 🟠 High (very large) | Opus 4.8 · high | **Ready for PR** – #586 and #591 are complete; no open dependency remains. |
| [#593](https://github.com/NikolayDA/picture_helper/issues/593) | [3D] Interactive viewer with orbit/pan/zoom, fallback | 🟡 Medium | 🟠 High (very large) | Opus 4.8 · xhigh | **Blocked** – waits on #592; the riskiest piece (platform-specific Qt/OpenGL). |
| [#594](https://github.com/NikolayDA/picture_helper/issues/594) | [3D] Workflow, state, and cache integration | 🟡 Medium | 🟠 High (very large) | Opus 4.8 · high | **Blocked** – waits on #593, #587, #588. |
| [#595](https://github.com/NikolayDA/picture_helper/issues/595) | [3D] Performance, packaging, docs, end-to-end acceptance | 🟡 Medium | 🟠 High | Sonnet 5 · high | **Blocked** – waits on #594. |
| [#582](https://github.com/NikolayDA/picture_helper/issues/582) | [Epic] Real 3D relief preview | 🟡 Medium | 🟠 High (very large) | – (tracking epic) | **In progress** – runs via #592→…→#595; #591 is complete. |
| [#551](https://github.com/NikolayDA/picture_helper/issues/551) | Automate CodeQL, run Codex Security manually only | 🟡 Medium | 🟡 Medium | Sonnet 5 · medium | **Ready for PR** – strategic decision made on 2026-07-15 (hybrid model: CodeQL automatic + Codex manual via `workflow_dispatch`); the issue body already has the full implementation checklist. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restore OpenAI quota for the manual Codex security check | 🟢 Low | 🟢 Low | – (no code task) | **Blocked (external)** – scope narrowed further on 2026-07-15: purely an external OpenAI billing/quota tracker, blocks neither CodeQL nor the release nor #551. |
| [#597](https://github.com/NikolayDA/picture_helper/issues/597) | test: `_open_ai_install_dialog` has no wiring test (N15) | 🟢 Low | 🟢 Low | Sonnet 5 · low | **Ready for PR** – test sketch already in the issue, no dependency. |
| [#598](https://github.com/NikolayDA/picture_helper/issues/598) | test: non-RGBA conversion paths in `image_utils.py` untested (N16) | 🟢 Low | 🟢 Low | Sonnet 5 · low | **Ready for PR** – test sketch already in the issue, no dependency; could be bundled with #597 in one PR. |

### Recommended Next (PR order)

1. **#584** — fully complete the reopened candidate gate: evidence the final SHA, five real artifacts, checksums, platform smokes, and Go/No-Go.
2. **#592** — start the 3D geometry pipeline now: #586 and #591 are complete, so no dependency remains open.
3. **#551** — move on to implementing the already-decided hybrid model (automate CodeQL for Python, reduce the Codex workflow to pure `workflow_dispatch`); no open strategy question remains.
4. **#597 + #598** — the fastest coverage win this round, both test sketches are already in the issue bodies; can be done as one shared PR.
5. **#585** and every remaining 16-bit/3D sub-issue follow their dependencies sequentially – see the table, no extra trigger needed.

*Drift note:* the live follow-up exposed the premature closure of #584 and the actual completion of #591. #584 is reopened; future updates must recheck statuses, checklists, and dependencies live instead of carrying a timestamp forward.

## Previous Rounds

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
