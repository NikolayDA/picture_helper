[Deutsch](../../../RECOMMENDATIONS.md) · **English** · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Code Analysis & Ranked Recommendations: BgRemover

## Rating Scale

| Symbol | Priority | Meaning |
|--------|----------|---------|
| 🔴 | Critical | Bugs, crashes, or data loss |
| 🟠 | High | Clear impact on reliability or maintainability |
| 🟡 | Medium | Useful improvement for quality, readability, or testability |
| 🟢 | Low | Optional polish or process improvement |

## Current Status (2026-07-21)

The active code-analysis list is empty. Ruff, mypy, and the local test suite remain the baseline before new PRs. Since the last snapshot (2026-07-18, 3 open issues), a brand-new epic appeared and was largely implemented within a single day: **#639** (automated release acceptance via self-hosted hardware runners) with sub-issues **#640–#646** and follow-up issue **#648**. Live state per GitHub query: **12** open issues.

### Completed Since The Last Review

- **Old baseline stable:** **N1/N2/N4/N5/N6/N7/N8** and **O2–O7** remain done; epics **#329/#344/#358/#384** (N9–N12) plus export fix **#363** are merged/archived.
- **16-bit height pipeline fully complete:** epic **#581** including **#587/#588** (PR #610), **#589** (PR #612), and **#590** (PR #613) are on `main`; all gates/reviews green, complete acceptance matrix present.
- **Security model & 3D core complete:** **#551** (CodeQL automatic, Codex manual only) via PR #619; **#592–#594** (geometry core, viewer, workflow/cache integration) via PR #620 on `main`. Coverage gaps **#597/#598** closed via PR #615; guide gap **#606** fixed in all six languages via PR #616.
- **Raspberry Pi 5 packaging hardened:** three real startup bugs found and fixed on target hardware — AppImage entry point (PR #627), aarch64 glibc compatibility (PR #627), Qt plugin staging/RUNPATH (PR #631); the app is confirmed to start on the Pi 5 including a working 3D preview.
- **New epic #639 opened AND largely implemented:** ADR + operations docs (#640), workflow skeleton `release-abnahme.yml` (#641), Linux/macOS hardware smokes with GL provenance (#642/#643), E2E release regression test (#644), live-GL performance suite (#645), and vision pre-assessment + acceptance matrix (#646) are fully implemented and verified on `main` via PR #647 and PR #649. They remain listed as open only because the PR descriptions use German phrasing ("Löst #640 …") instead of the English closing keywords GitHub recognizes (see comment on #639 from 2026-07-21).

### Still Open

- **O8 🟢 — Prototype inaccuracy:** height tools stay locked in the mockup after generation; mockup-only, the real app is unaffected (#347).
- **Admin follow-up 🟢 — Four issues are done but not closed:** #640–#643 are fully implemented via PR #647; only the missing English closing keyword in the PR description prevented auto-close (see comment on #639).
- **Documentation gap 🟢 — README.md missing the 3D section:** the 3D relief preview is documented in `ANLEITUNG.md` and `CHANGELOG.md`, but `README.md` still doesn't mention it (feature list, usage step 5, screenshots). This matches the still-open "ANLEITUNG/README/architecture docs updated" criterion in #582/#595.

## Open GitHub Issues — Triage Status (2026-07-21)

Live state: **12** open issues. Rating: **Relevance** = importance to the roadmap/users, **Complexity** = estimated implementation effort, **Model/Effort** = the recommended Claude model and reasoning effort.

### Sensible Bundles

- **Release acceptance automation** (#639 → {#640 ‖ #641} → {#642 ‖ #643} → #644 → #645 → #646): technically already implemented via PR #647/#649; only real hardware-evidence verification (runner dispatch) and the four administrative closures #640–#643 remain.
- **#648** is the only genuine remaining code task in this area: an automation/screenshot mode inside the packaged artifact, so the 3D render proof comes from the real package instead of a source checkout.
- **3D relief preview** (#582 → #595): the functional MVP is done (Go for the automatable scope, see the acceptance report on #582); #595 waits on the same hardware dispatch as above plus #648.
- **#245** remains a purely external OpenAI billing/quota tracker and blocks neither CodeQL, release, nor 3D.

| # | Title | Relevance | Complexity | Model/Effort | Recommended next step |
|---|-------|-----------|------------|---------------|-----------------------|
| [#639](https://github.com/NikolayDA/picture_helper/issues/639) | [Epic] Automated release acceptance | 🟠 High | 🟠 High (very large, largely implemented) | – (tracking epic) | **In progress, nearly done** – #640–#646 technically implemented via PR #647/#649; waits on runner verification + closing the sub-issues; #648 is the only genuine remaining effort. |
| [#640](https://github.com/NikolayDA/picture_helper/issues/640) | ADR + operations/security docs for self-hosted acceptance runners | 🟡 Medium | 🟢 Low (done) | – (no code task) | **Ready to close** – ADR + `RELEASE_AUTOMATION.md` fully present via PR #647; only the closing keyword is missing. |
| [#641](https://github.com/NikolayDA/picture_helper/issues/641) | Workflow `release-abnahme.yml`: skeleton, artifact retrieval, evidence format | 🟠 High | 🟢 Low (done) | – (no code task) | **Ready to close** – workflow + governance test present via PR #647; only the closing keyword is missing. |
| [#642](https://github.com/NikolayDA/picture_helper/issues/642) | Linux smokes (AppImage/.deb) with GL provenance | 🟠 High | 🟡 Medium (core logic done) | – (no code task) | **Ready to close / needs live verification** – `abnahme_smoke.py` + tests present via PR #647; real execution only happens once dispatched on the Pi 5 runner. |
| [#643](https://github.com/NikolayDA/picture_helper/issues/643) | macOS DMG smoke with Retina/HiDPI proof | 🟠 High | 🟡 Medium (core logic done) | – (no code task) | **Ready to close / needs live verification** – same basis as #642, for the M3 runner. |
| [#644](https://github.com/NikolayDA/picture_helper/issues/644) | E2E release regression scenario as a `ui` test | 🟠 High | 🟡 Medium (done) | – (no code task) | **Ready to close / needs live verification** – `tests/test_e2e_release_regression.py` (ui_smoke) present via PR #649; the Ready branch needs a real GL dispatch. |
| [#645](https://github.com/NikolayDA/picture_helper/issues/645) | Live-GL performance suite in the benchmark harness | 🟡 Medium | 🟡 Medium (done) | – (no code task) | **Ready to close / needs live verification** – `preview3d-live` suite in `scripts/benchmark.py` present via PR #649. |
| [#646](https://github.com/NikolayDA/picture_helper/issues/646) | Vision pre-assessment, evidence aggregation, acceptance matrix | 🟡 Medium | 🟡 Medium (done) | – (no code task) | **Ready to close / needs live verification** – `abnahme_vision_check.py`/`abnahme_aggregate.py` present via PR #647/#649; also needs an `ANTHROPIC_API_KEY` secret for real assessment. |
| [#648](https://github.com/NikolayDA/picture_helper/issues/648) | Native 3D render proof of the packaged artifact | 🟡 Medium | 🟡 Medium | Sonnet 5 · medium | **Ready for PR** – a clearly scoped, independent gap (a screenshot automation hook inside the packaged artifact instead of a source checkout); the only genuine remaining code task of the acceptance automation. |
| [#595](https://github.com/NikolayDA/picture_helper/issues/595) | [3D] Performance, packaging, docs, end-to-end acceptance | 🟡 Medium | 🟡 Medium (down, automation now exists) | Sonnet 5 · medium | **Blocked** – waits on the same hardware dispatch as #639 plus #648; README.md also still needs the 3D section. |
| [#582](https://github.com/NikolayDA/picture_helper/issues/582) | [Epic] Real 3D relief preview | 🟡 Medium | 🟠 High (very large, MVP done) | – (tracking epic) | **Blocked** – waits solely on #595. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restore OpenAI quota for the manual Codex security check | 🟢 Low | 🟢 Low | – (no code task) | **Blocked (external)** – unchanged since 2026-07-15: a purely external billing tracker that blocks nothing in the repository. |

### Recommended Next (PR order)

1. **Close #640–#643** — implementation is complete (PR #647); only the owner's manual confirmation is missing.
2. **Implement #648** — the only remaining code task: an automation/screenshot mode inside the packaged artifact for a genuine 3D render proof.
3. **Register self-hosted runners and dispatch `release-abnahme.yml`** — verifies #642–#646 with real hardware evidence and produces the acceptance matrix for #595.
4. **After a green run + #648:** close #595, then #582 (blocked only on #595); add the 3D section to README.md.
5. **#245** stays put — no repository patch can fix the external OpenAI billing blocker.

*Drift note:* this update reconciles the snapshot with the actual `main` state (full git history, previously hidden by a shallow clone) and a live GitHub query; it supersedes the 2026-07-18 state with 3 open issues. Future updates keep rechecking statuses, checklists, and dependencies live instead of carrying a timestamp forward.

## Previous Rounds

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
