[Deutsch](../../../RECOMMENDATIONS.md) · **English** · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Code Analysis & Ranked Recommendations: BgRemover

## Rating Scale

| Symbol | Priority | Meaning |
|--------|----------|---------|
| 🔴 | Critical | Bugs, crashes, or data loss |
| 🟠 | High | Clear impact on reliability or maintainability |
| 🟡 | Medium | Useful improvement for quality, readability, or testability |
| 🟢 | Low | Optional polish or process improvement |

## Current Status (2026-07-15)

The active code-analysis list is empty. Ruff, mypy, and the local test suite remain the baseline before new PRs. Release **v2.5.0** was cut on 2026-07-11 (PR #538); the rollout wave **#435/#392/#426/#389** is closed, as is **#299** (PR #539) with N13 follow-up **#541** (PR #543), **#318** (PR #540), and the snapshot sync **#542**. A repo audit on 2026-07-12 filed **#549–#553**; **#552/#549/#553/#550** are now closed via PR #557–#560. Epic **#563** ("app update check & AI model management", eight sub-issues **#564–#571**) was fully implemented and closed on 2026-07-13 via PR #573/#574 (**N14**). Live state: **20** open issues – the pre-existing #245/#551 plus three epics newly filed on 2026-07-15 (**Release v2.6.0** #580 with sub-issues #583–#585, the **16-bit height pipeline** #581 with sub-issues #586–#590, the **3D relief preview** #582 with sub-issues #591–#595) plus two test-coverage findings **N15/N16** (#597/#598) filed the same day from a coverage audit.

### Completed Since The Last Review

- **Old baseline stable:** **N1/N2/N4/N5/N6/N7/N8** and **O2–O7** remain done; epics **#329/#344/#358/#384** (N9–N12) plus export fix **#363** are merged/archived; since 2026-06-25 also **#404/#406/#408** (PR #412) closed.
- **Redesign & release v2.5.0:** redesign core/rail/zoom/card inspector/Dark Mode/UI follow-up (**#413/#414/#455–#464/#474–#489/#499–#501/#503/#509/#510/#514–#517**, **#490**, **#433/#434**) via PR #412–#522; release wave **#435/#392/#426/#389** (v2.5.0), **#299/#541/#318/#542**, PR template **#552**, snapshot sync **#549**, SessionStart fix **#553**, v2.3.0 formalization **#550** – all closed since 2026-07-12.
- **N14 — Epic #563 (app update & AI model management) fully closed:** `app_update.py` (#564), `ai_model_status.py` (#568), menu/dialog integration (#565/#569), optional automatic startup check (#566), warmup wiring with multiple observers/cooperative cancellation (#570) via PR #573/#574; docs wrap-up (#567/#571).

### Still Open

- **O8 🟢 — Prototype inaccuracy:** height tools stay locked in the mockup after generation; mockup-only, the real app is unaffected (#347).
- **N15 🟡 — Untested dialog wiring:** `MainWindow._open_ai_install_dialog` (`main_window.py:1566`) has no dedicated test, unlike the structurally identical sibling method `_open_ai_model_dialog` (#597).
- **N16 🟡 — Untested non-RGBA conversion:** the non-RGBA branches in `pil_to_qpixmap`/`pil_to_numpy_readonly` (`image_utils.py:16`/`:43`) are never exercised with an RGB/palette/grayscale source image (#598).

## Open GitHub Issues — Triage Status (2026-07-15)

Live state: **20** open issues – a further increase from **18**: on top of the three epics, two test-coverage findings from a 2026-07-15 coverage audit were filed (**#597**/**#598**, matching **N15**/**N16** above). The comment check found nothing needing a response: #245 was last commented on 2026-06-19 (status still accurate), and all other 19 issues have no comments.

### Sensible Bundles

- **Release v2.6.0** (#580 → #583 → #584 → #585, strictly sequential): ships the already-built update/AI-management state from `main`; top priority given low risk and immediate user value.
- **16-bit height pipeline** (#581 → #586 → #587 → {#588 ‖ #589} → #590): #586 (ADR) is explicitly allowed to proceed in parallel with the release, but schema-changing implementation (#587+) only starts after #585 (per #580's scope-freeze mandate).
- **3D relief preview** (#582 → #591 → #592 → #593 → #594 → #595): #591 additionally depends on #586 (it consumes the same HEIGHT contract) – so #582 is effectively downstream of the 16-bit chain and the largest effort block this round.
- **#245/#551** remain linked (Codex scan: account action vs. strategic decision).
- **#597/#598** are independent, fully specified coverage gaps (test sketch already in the issue) – no chain, no dependency on the three epics.

Rating: **Relevance** = importance to the roadmap/users, **Complexity** = estimated implementation effort, **Model/Effort** = the recommended Claude model and reasoning effort.

| # | Title | Relevance | Complexity | Model/Effort | Recommended next step |
|---|-------|-----------|------------|---------------|-----------------------|
| [#580](https://github.com/NikolayDA/picture_helper/issues/580) | [Epic] Release v2.6.0 | 🟠 High | 🟠 High | – (tracking epic) | **In progress** – runs via #583→#584→#585, no PR of its own. |
| [#583](https://github.com/NikolayDA/picture_helper/issues/583) | Release 2.6.0: scope freeze, version, CHANGELOG | 🟠 High | 🟡 Medium | Sonnet 5 · medium | **Ready for PR** – no open dependency, locks in already-built user value at low risk. |
| [#584](https://github.com/NikolayDA/picture_helper/issues/584) | Release 2.6.0: candidate gate, five artifacts | 🟠 High | 🟠 High | Sonnet 5 · high | **Blocked** – waits on #583; the five artifact smokes fit well-suited parallel workflow orchestration. |
| [#585](https://github.com/NikolayDA/picture_helper/issues/585) | Release 2.6.0: tag, GitHub release, post-release check | 🟠 High | 🟡 Medium | Sonnet 5 · medium | **Blocked** – waits on #584. |
| [#586](https://github.com/NikolayDA/picture_helper/issues/586) | [16-bit] ADR: canonical HEIGHT data contract, migration, memory budget | 🟠 High | 🟠 High | Opus 4.8 · high | **Ready for PR** – pure analysis/ADR work, may proceed in parallel with the release; blocks #587–590 and #591. |
| [#587](https://github.com/NikolayDA/picture_helper/issues/587) | [16-bit] HEIGHT domain model & ProjectHistory, lossless | 🟠 High | 🟠 High (very large) | Opus 4.8 · high | **Blocked** – waits on #586 and the release being published (#585). |
| [#588](https://github.com/NikolayDA/picture_helper/issues/588) | [16-bit] Project format v2: persistence, migration, validation | 🟠 High | 🟠 High | Opus 4.8 · high | **Blocked** – waits on #586/#587. |
| [#589](https://github.com/NikolayDA/picture_helper/issues/589) | [16-bit] Import/generation/height ops without 8-bit quantization | 🟠 High | 🟠 High | Opus 4.8 · high | **Blocked** – waits on #586/#587. |
| [#590](https://github.com/NikolayDA/picture_helper/issues/590) | [16-bit] Preview, export, UI, end-to-end acceptance | 🟠 High | 🟠 High | Opus 4.8 · high | **Blocked** – waits on #588/#589. |
| [#581](https://github.com/NikolayDA/picture_helper/issues/581) | [Epic] Full 16-bit height pipeline | 🟠 High | 🟠 High (very large) | – (tracking epic) | **In progress** – runs via #586→#587→(#588‖#589)→#590. |
| [#591](https://github.com/NikolayDA/picture_helper/issues/591) | [3D] ADR/UX contract: renderer backend, fallback, budgets | 🟡 Medium | 🟠 High | Opus 4.8 · high | **Blocked** – waits on #586 being accepted. |
| [#592](https://github.com/NikolayDA/picture_helper/issues/592) | [3D] Qt-free geometry/normal/decimation pipeline | 🟡 Medium | 🟠 High (very large) | Opus 4.8 · high | **Blocked** – waits on #586/#591. |
| [#593](https://github.com/NikolayDA/picture_helper/issues/593) | [3D] Interactive viewer with orbit/pan/zoom, fallback | 🟡 Medium | 🟠 High (very large) | Opus 4.8 · xhigh | **Blocked** – waits on #591/#592; the riskiest piece (platform-specific Qt/OpenGL). |
| [#594](https://github.com/NikolayDA/picture_helper/issues/594) | [3D] Workflow, state, and cache integration | 🟡 Medium | 🟠 High (very large) | Opus 4.8 · high | **Blocked** – waits on #593, #587, #588. |
| [#595](https://github.com/NikolayDA/picture_helper/issues/595) | [3D] Performance, packaging, docs, end-to-end acceptance | 🟡 Medium | 🟠 High | Sonnet 5 · high | **Blocked** – waits on #594. |
| [#582](https://github.com/NikolayDA/picture_helper/issues/582) | [Epic] Real 3D relief preview | 🟡 Medium | 🟠 High (very large) | – (tracking epic) | **In progress** – runs via #591→…→#595; blocked on #586. |
| [#551](https://github.com/NikolayDA/picture_helper/issues/551) | Codex Security Scan strategy decision (reactivate/decommission/replace) | 🟡 Medium | 🟡 Medium | Sonnet 5 · medium | **Ready for PR** – recommendation remains option 2 (decommission/disable), now 5+ weeks externally blocked. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Codex Security Scan "Quota exceeded" | 🟢 Low | 🟢 Low | – (no code task) | **Blocked (external)** – restoring OpenAI billing/quota is an account action, not a PR. |
| [#597](https://github.com/NikolayDA/picture_helper/issues/597) | test: `_open_ai_install_dialog` has no wiring test (N15) | 🟢 Low | 🟢 Low | Sonnet 5 · low | **Ready for PR** – test sketch already in the issue, no dependency. |
| [#598](https://github.com/NikolayDA/picture_helper/issues/598) | test: non-RGBA conversion paths in `image_utils.py` untested (N16) | 🟢 Low | 🟢 Low | Sonnet 5 · low | **Ready for PR** – test sketch already in the issue, no dependency; could be bundled with #597 in one PR. |

### Recommended Next (PR order)

1. **#583** — tackle the v2.6.0 scope freeze first: no open dependency, locks in already-built user value at low risk.
2. **#586** — start the 16-bit ADR now rather than after #585: it blocks two full epics (#581 directly, #582 indirectly via #591) and is explicitly allowed to run in parallel with the release.
3. **#551** — resolve the short, independent strategy decision; the recommendation remains option 2 (decommission/disable).
4. **#597 + #598** — the fastest coverage win this round, both test sketches are already in the issue bodies; can be done as one shared PR.
5. **#584/#585** and every 16-bit/3D sub-issue follow their dependencies sequentially – see the table, no extra trigger needed.

*Drift note:* re-check the live open-issue count before every future update instead of carrying it forward – this round's jump from 2 to 18 plus the two coverage issues (#597/#598) filed shortly after show how fast the snapshot goes stale.

## Previous Rounds

- **2026-07-14** — live state still 2 open issues (#245, #551), unchanged since the epic completion the day before.
- **2026-07-13 (epic completion)** — epic **#563** fully closed: all eight sub-issues (**#564–#571**) closed through PR #573/#574; snapshot reduced to 2.
- **2026-07-13 (issue audit)** — epic **#563** + eight sub-issues filed, all 11 open issues re-assessed, owner comments taken into account; no issue closed; snapshot updated to 11.
- **2026-07-12** — v2.3.0 formalization (#550), SessionStart hook fix (#553), snapshot sync (#549, PR template #552 via PR #557), issue audit (#542 closed, #549–#553 filed), and release **v2.5.0** (rollout wave #435/#392/#426/#389, #299/#541/#318).
- **2026-07-11** — epic #425 fully closed (#430 PR #526, full runtime i18n ES/FR/UK/ZH, **O1** done; #431/#432 PR #529; final follow-up #530/#531 PR #533/#535).
- **2026-07-05–10** — #509/#510/#514–#517 (PR #520–#522), #490, Dark Mode/rail-icon wave, card inspector (#413/#414), #499–#501/#503, icon/status-bar polish.
- **2026-06-29** — #404/#406/#408 completed (PR #412), redesign wave opened.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, completed or discarded where it was a false positive.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
