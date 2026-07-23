[Deutsch](../../../RECOMMENDATIONS.md) · **English** · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Code Analysis & Ranked Recommendations: BgRemover

## Rating Scale

| Symbol | Priority | Meaning |
|--------|----------|---------|
| 🔴 | Critical | Bugs, crashes, or data loss |
| 🟠 | High | Clear impact on reliability or maintainability |
| 🟡 | Medium | Useful improvement for quality, readability, or testability |
| 🟢 | Low | Optional polish or process improvement |

## Current Status (2026-07-23, #668/#669 closed out)

Ruff, mypy, and the local test suite remain the baseline before new PRs. Since the last round, both previously open audit issues were closed out:

- **#669** (stale live state) — closed directly: the earlier RECOMMENDATIONS reconcile (PR #671) had already brought the content fully up to date (#659/#660 correctly listed as closed, #668 already included); an additional no-op PR wasn't needed.
- **#668** (stale screenshot-set references) — fixed by this update: `ANLEITUNG.md` and `README.md` (each including all five translations) now point at the current set `bgremover_complete_20260722_171622`. `docs/history/EPIC-582-ABNAHME.md` deliberately keeps the 2026-07-19 set — there it is the actual acceptance evidence (GPU/OS/renderer provenance recorded in the manifest), and switching it would have misrepresented the documented evidence; an explanatory note was added and the old directory is kept accordingly. A new governance test (`tests/test_screenshot_references.py::test_docs_reference_latest_screenshot_set`) now catches a repeat of this silent drift.

Live state per GitHub query: **2** open issues (#656, #245) — both purely external/operational, no code blocker.

### Review Result

- **Old baseline stable:** **N1/N2/N4/N5/N6/N7/N8/N9**, **O1–O8**, and everything completed since **2026-06-25** remain done.
- **Release v2.7.0 fully completed and verified:** the tag, publication, and all three gate stages (CI matrix, candidate build, hardware acceptance) ran against the actual tagged commit `6f103ed` — no drift between what was gated and what was published.
- **#669/#668 closed out** — the lowest live state since this log began.
- **#656/#245** remain unchanged, purely external/operational trackers with no code relation.

## Open GitHub Issues — Triage Status (2026-07-23)

| # | Title | Relevance | Complexity | Recommended model (effort) | Next step |
|---|-------|-----------|------------|------------------------------|-----------|
| [#656](https://github.com/NikolayDA/picture_helper/issues/656) | Enable ANTHROPIC_API_KEY secret for the vision pre-assessment | 🟡 Medium (only improves evidence quality; not a blocker per contract) | 🟢 Low (purely operational, no code) | – (no agent; repo owner: Settings → Secrets) | Blocked (external) – can be done independently |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restore OpenAI quota for the manual Codex security check | 🟢 Low (blocks only an optional manual scan) | 🟢 Low (purely operational, no code) | – (no agent; repo owner: billing) | Blocked (external) – resolve billing/quota on the OpenAI platform project |

### Recommended Next

1. Handle **#656** independently if real vision verdicts are wanted — it's a quality improvement, not a blocker.
2. Leave **#245** as a purely external billing/quota tracker; no action possible or needed in the repository.
3. Release v2.7.0 is fully published — no further release-related step is needed.

## Previous Rounds

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
