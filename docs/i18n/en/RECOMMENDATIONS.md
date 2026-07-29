[Deutsch](../../../RECOMMENDATIONS.md) · **English** · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Code Analysis & Ranked Recommendations: BgRemover

## Rating Scale

| Symbol | Priority | Meaning |
|--------|----------|---------|
| 🔴 | Critical | Bugs, crashes, or data loss |
| 🟠 | High | Clear impact on reliability or maintainability |
| 🟡 | Medium | Useful improvement for quality, readability, or testability |
| 🟢 | Low | Optional polish or process improvement |

## Current Status (2026-07-29, follow-up: #710/#711 closed, #685 ready to start)

Follow-up on 2026-07-29: the two follow-ups filed the previous day as release-blocking, **#711** (GL probe/QOpenGLBuffer detection) and **#710** (freeze update/SHA contract), are both closed (#711 via PR #713, #710 via PR #714). During the #710 review, Codex additionally found a deadlock in the release gate introduced by PR #709 (`GITHUB_SHA == candidate` would have structurally blocked every future candidate build); **PR #715** reverted that step and restored the originally intended contract (`--require-pin` passing is enough, on the candidate or a pure protocol commit above it).

Current candidate for 2.7.1: `adb2205960619b9b5c29a9a05feda163310782a6` (21 commits in the window; `python scripts/verify_release_freeze.py --require-pin` → 0 errors/0 warnings). **#685 is therefore technically unblocked and, per its own status comment, ready to start** — only the genuinely manual/hardware-bound parts remain (candidate build, install/launch on target hardware, signing/notarization check, acceptance matrix, go/no-go). #686 stays blocked until #685 is done.

Live state after the GitHub query: **17** open issues (#710/#711 dropped out of the count on closing; 15 remain from #680–#696, plus the unchanged external #656/#245).

### Review and Definition Audit Result

- ✅ **#711 closed** (PR #713): failed `QOpenGLBuffer.create()`/`bind()` calls are now detected and partial resources are released cleanly, exactly once.
- ✅ **#710 closed** (PR #714, plus fix-up PR #715): the freeze document now pins candidate `adb2205960619b9b5c29a9a05feda163310782a6`; the deadlock in the build/tag contract introduced by #709 was fixed by #715.
- ✅ **#685 is now ready to start:** per its own current status comment, the candidate build plus hardware acceptance can begin.
- 🟠 **EufyMake definitions unchanged:** #681/#687–#691 still describe TIFF criteria against a real PNG asset package; #687 remains not ready to start until this is resolved.
- **No new comments** on #245/#656 or on the COLOR (#682/#692–#696) and remaining EufyMake sub-issues (#688–#690) since the last round – no update needed.
- **Old baseline still stable:** **N1/N2/N4/N5/N6/N7/N8/N9**, **O1–O8**, everything completed since **2026-06-25**, and release v2.7.0 (tag/publication/all three gate stages against commit `6f103ed`) remain unchanged and done.

## Open GitHub Issues — Triage Status (2026-07-29)

| # | Title | Relevance | Complexity | Recommended model (effort) | Next step |
|---|-------|-----------|------------|------------------------------|-----------|
| [#680](https://github.com/NikolayDA/picture_helper/issues/680) | [Epic] v2.7.x stabilization – ship the GL fix | 🟠 High | 🟠 High | – (epic; Sonnet, medium for tracking) | In progress – #685 is ready, order #685 → #686 |
| [#685](https://github.com/NikolayDA/picture_helper/issues/685) | Build candidate artifacts + hardware acceptance against the exact commit | 🟠 High | 🟠 High | Sonnet, medium (build); no agent for hardware smokes | **Ready** – candidate `adb2205960619b9b5c29a9a05feda163310782a6`, blockers #710/#711 resolved |
| [#686](https://github.com/NikolayDA/picture_helper/issues/686) | Tag, publish, post-release verification | 🟠 High (makes the fix available to users) | 🟢 Low (established release process since v2.6.0/v2.7.0) | Sonnet, low | Blocked – waits on #685 |
| [#681](https://github.com/NikolayDA/picture_helper/issues/681) | [Epic] EufyMake target profile – validate Height/Gloss/mm-DPI | 🟠 High (correctness of the main export target) | 🔴 High (5 sub-issues, needs physical hardware) | – (epic) | **Fix the definition** – criteria describe TIFF, the export writes PNG assets |
| [#687](https://github.com/NikolayDA/picture_helper/issues/687) | Assumption inventory, manufacturer sources, test matrix | 🟠 High (binding foundation for #688–#691) | 🟡 Medium (research/docs, no hardware access needed) | Sonnet, medium | Not ready – the container/format question must become the first inventory item |
| [#688](https://github.com/NikolayDA/picture_helper/issues/688) | Validate HEIGHT bit depth/semantics on real hardware | 🟠 High (directly affects relief height) | 🔴 High (physical printer, fixtures, measurement log) | – (no agent; needs real EufyMake hardware) | Blocked (external + definition) – generate fixtures in the right format |
| [#689](https://github.com/NikolayDA/picture_helper/issues/689) | Validate mm/DPI, target size, positioning contract | 🟠 High (print size/registration) | 🔴 High (physical measurements, control motifs) | – (no agent; needs real hardware) | Blocked (external + definition) – settle the mm/DPI transport path first (N10) |
| [#690](https://github.com/NikolayDA/picture_helper/issues/690) | Validate gloss/clear-coat semantics | 🟡 Medium (gloss is already flagged "experimental" in code) | 🔴 High (physical prints, material consumption) | – (no agent; needs real hardware) | Blocked (external + definition) |
| [#691](https://github.com/NikolayDA/picture_helper/issues/691) | Integrate versioned target profile into validator/writer/dialog/docs | 🟠 High (hardens the production export path) | 🟠 High (cross-cutting across eufymake_export/_validate/_writer + UI) | Opus, high | Blocked – waits on #688–#690; the writer criterion names TIFF tags/IFDs |
| [#682](https://github.com/NikolayDA/picture_helper/issues/682) | [Epic] COLOR tonal/grayscale engine | 🟡 Medium-high (roadmap foundation for laser, not an active bug) | 🔴 High (5 sub-issues, ADR→core→UI→integration→acceptance) | – (epic) | In progress – start #692 first |
| [#692](https://github.com/NikolayDA/picture_helper/issues/692) | ADR + data contract for tone/histogram/grayscale ops | 🟠 High (sets the contract for the whole epic) | 🟡 Medium (architecture decision, no implementation) | Opus, high | Ready to start |
| [#693](https://github.com/NikolayDA/picture_helper/issues/693) | Qt-free core: histogram/grayscale/levels/gamma | 🟡 Medium-high | 🟡 Medium (extends `color_ops.py`, well isolated and testable) | Sonnet, high | Blocked – waits on ADR #692 |
| [#694](https://github.com/NikolayDA/picture_helper/issues/694) | Live preview + UI for histogram/levels/gamma | 🟡 Medium | 🟡 Medium-high (Qt UI, debounce/generation guard like the height preview) | Sonnet, high | Blocked – waits on core #693 |
| [#695](https://github.com/NikolayDA/picture_helper/issues/695) | Layer/selection/history/project integration | 🟡 Medium | 🟠 High (many state transitions: undo/redo, selection, dirty state) | Opus, high | Blocked – waits on #693/#694 |
| [#696](https://github.com/NikolayDA/picture_helper/issues/696) | Performance/E2E/docs/laser-interface acceptance | 🟡 Medium (closeout gate, not a new feature) | 🟠 High (benchmark suite, E2E, docs, adapter contract) | Opus, high | Blocked – closeout issue after #695 |
| [#656](https://github.com/NikolayDA/picture_helper/issues/656) | Enable ANTHROPIC_API_KEY secret for the vision pre-assessment | 🟡 Medium (only improves evidence quality; not a blocker per contract) | 🟢 Low (purely operational, no code) | – (no agent; repo owner: Settings → Secrets) | Blocked (external) – can be done independently |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restore OpenAI quota for the manual Codex security check | 🟢 Low (blocks only an optional manual scan) | 🟢 Low (purely operational, no code) | – (no agent; repo owner: billing) | Blocked (external) – resolve billing/quota on the OpenAI platform project |

### Recommended Next

1. Run **#685** now – build candidate artifacts from `adb2205960619b9b5c29a9a05feda163310782a6` and accept them on real target hardware.
2. **#686** follows afterward for tag/publish.
3. **#692** can start independently in parallel.
4. Correct **#681/#687–#691** before #687; #688–#690 still need real EufyMake hardware.
5. **#656/#245** remain external secret/billing trackers.

## Previous Rounds

- **2026-07-29 (follow-up: #710/#711 closed, #685 ready)** — both previously open release blockers are closed (#711 via PR #713, #710 via PR #714); a deadlock in the build/tag contract (introduced by #709, found by Codex during the #710 review) was reverted via PR #715. Current candidate `adb2205960619b9b5c29a9a05feda163310782a6`, `verify_release_freeze.py --require-pin` 0 errors/0 warnings. #685 is now ready to start (only hardware-bound steps remain), #686 still waits on #685. No new comments on the other 12 open issues. Live state 17.
- **2026-07-28 (review of #701/#703–#709 and #684/#699/#702)** — eight PR heads passed CI/CodeQL/dependency/license checks and all review threads were resolved. #702 is fixed by #708; #684 remains a sound instrumented proof with the real GPU smoke in #685. Filed #711 (silent QOpenGLBuffer failure can false-green) and #710 (freeze/SHA contract stale after #708/#709; locally 4 errors/1 warning). Updated #680/#685; reliable order #711 → #710 → #685 → #686. Live state 19.
- **2026-07-27 (issue definition audit)** — all 19 open issues read against the code. Main finding: epic #681 and its five sub-issues state their acceptance criteria against a TIFF package, while the export writes PNG assets plus `manifest.json` — documented on #681, with a heads-up on #687. New code finding **N10** (image assets without `pHYs`; mm/DPI only in the manifest, whose handling by Studio is unverified). Smaller inaccuracies in #685 (a non-existent "TIFF check") and the stale sub-issue checklist on #680. The remaining 13 issues are correctly defined; #702 was verified against the code and is accurate. Live state 19.
- **2026-07-27 (follow-up on #678/#679/#697/#698/#700/#701/#703 and #677/#683/#699)** — all seven PR heads had green CI/CodeQL/dependency/license runs; #677 is cleanly complete. The initial freeze defect from #683/#698 was corrected through #699/#701/#703, including two review rounds and a hard release gate; final candidate `480a5fc0008ded401b02b15373d8474d67c83382`, gate on `main` 0/0. #685 now waits only on #684, and #686 on #685. New docs issue #702 was expanded to all six README languages and given acceptance criteria. Live state 19.
- **2026-07-26 (PR/issue follow-up #678/#679/#697/#698)** — all four PR gates were green; #678/#679 are sound and #697's review findings were fixed. #683 closed through #698, but the documented freeze commit `ba7e7cd` still contains version 2.7.0 rather than the scope cut; a full SHA and submitted independent review are also missing. Follow-up #699 was filed with acceptance criteria; #685/#686 remain blocked until corrected. Live state 19.
- **2026-07-26 (issue audit: three new epics)** — the repo owner filed epics #680 (v2.7.x stabilization/2.7.1), #681 (EufyMake target profile), and #682 (COLOR tonal engine) with 14 sub-issues; #677 was filed and closed again in the same window. #245/#656 had no new comments and remained external. At that point #683, #684, #692, and the scaffolding of #687 were ready to start without external dependencies. Live state rose from 2 to 19 open issues.
- **2026-07-23 (#668/#669 closed out)** — #669 (stale doc live state) closed directly, since PR #671 had already fully resolved it, no further code/doc change needed. #668 (`ANLEITUNG.md`/`README.md` referencing the orphaned 2026-07-19 screenshot set) fixed via a standalone PR: living doc references (6 languages each) migrated to the current 2026-07-22 set; the acceptance evidence in `docs/history/EPIC-582-ABNAHME.md` deliberately left untouched (explanatory note added, old directory kept); new governance test added against future screenshot drift. Live state 2 open issues (both external/operational, not a blocker) — the lowest since this log began.
- **2026-07-23 (release v2.7.0)** — PR #670 (version bump + CHANGELOG cutover + icon entry) merged (`6f103ed`); the complete gate was re-run against the new merge commit (CI matrix, candidate build, hardware acceptance, all green); tag `v2.7.0` set and published (five artifacts). Two new audit issues filed: #669 (stale doc live state, fixed by this update) and #668 (orphaned screenshot set in ANLEITUNG.md, small repo hygiene). Live state 4 open issues, all doc hygiene or external, no code blocker.
- **2026-07-22 (test-audit closeout)** — both previously open audit issues closed: #660 via PR #664 (commit `92c14ba`, documented the `gl_smoke` marker in TESTING.md), #659 via PR #665 (commit `c4ab92a`, N9/O8 fully implemented, `make check` 1995/5, `make coverage` 93%). Also merged two asset-related PRs (#666 screenshot set, #667 new app icon), both still without a CHANGELOG entry. Live state 2 open issues (both external/operational, not a blocker) — the lowest since this log began.
- **2026-07-22 (acceptance closeout)** — triggered a fresh `release-abnahme.yml` dispatch (run #4, commit `9165c00`); checked the matrix against #595 (x86_64 stays documented-paused but doesn't block); individually verified and closed #595, #646, #639, #582 against their own acceptance criteria. The one real gap found (mypy strictness for `scripts/abnahme_vision_check.py`/`abnahme_aggregate.py`, #646) was fixed and merged via PR #662. Two new audit issues filed: #660 with a finished, unmerged fix (ready for PR), #659 awaiting a genuine owner decision on newly proposed findings. Live state 4 open issues.
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
