[Deutsch](../../../RECOMMENDATIONS.md) · **English** · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Code Analysis & Ranked Recommendations: BgRemover

## Rating Scale

| Symbol | Priority | Meaning |
|--------|----------|---------|
| 🔴 | Critical | Bugs, crashes, or data loss |
| 🟠 | High | Clear impact on reliability or maintainability |
| 🟡 | Medium | Useful improvement for quality, readability, or testability |
| 🟢 | Low | Optional polish or process improvement |

## Current Status (2026-07-22, after acceptance closeout)

Ruff, mypy, and the local test suite remain the baseline before new PRs. The fresh `release-abnahme.yml` dispatch requested in the last round was triggered (run [#4](https://github.com/NikolayDA/picture_helper/actions/runs/29908256619), commit `9165c00`, post #657/#658) and produced a fully green matrix except for the deliberately paused Linux x86_64 row. Building on that, all four previously blocked issues were **individually checked against their own acceptance criteria and closed** — no issue auto-closed with another:

1. **#595** — every item on the "still open" list is satisfied; the Linux x86_64 row stays "paused/declared open" but, per an explicit decision, does not block closing (mirroring #639's own acceptance criterion).
2. **#646** — five of six criteria were already met; a real gap was found: `scripts/abnahme_vision_check.py`/`abnahme_aggregate.py` were entirely excluded from `make type`/`make check`, and a strict trial run surfaced a genuine `union-attr` error. Fixed and merged via PR #662 (commit `f47445f`).
3. **#639** — with #646 closed, all eight sub-issues are now closed; the issue-body checklist has been reconciled.
4. **#582** — all five sub-issues are closed; the required texture stretch-goal decision already exists in the ADR, the README gap from the 2026-07-20 audit is fixed, and `make ui` is confirmed green.

In addition, two new issues from automated audits appeared since the last round (**#659**, **#660**), still awaiting a decision.

Live state per GitHub query: **4** open issues.

### Review Result

- **Old baseline stable:** **N1/N2/N4/N5/N6/N7/N8**, **O1–O7**, and everything completed since **2026-06-25** remain done.
- **#646/#639/#595/#582 have now been individually verified and closed** (no auto-close domino); the one real gap found along the way (mypy strictness for the acceptance scripts, #646) was fixed and merged via PR #662.
- **#659/#660 are new and still undecided:** #660 already has a finished but unmerged fix on branch `claude/festive-gates-4dkzds` (commit `80b7aa0`); #659 is a pure analysis with no code change, proposing two new finding IDs (**N9**/**O8**) that still await owner sign-off.
- The remaining step is therefore **no longer** an acceptance topic — it's opening/merging a PR for #660 and getting a decision on the findings proposed in #659.

## Open GitHub Issues — Triage Status (2026-07-22)

| # | Title | Relevance | Complexity | Recommended model (effort) | Next step |
|---|-------|-----------|------------|------------------------------|-----------|
| [#660](https://github.com/NikolayDA/picture_helper/issues/660) | TESTING.md audit: current, one small gap fixed (`gl_smoke` marker undocumented) | 🟢 Low (pure doc accuracy, no functional impact) | 🟢 Low (one short paragraph, already implemented) | – (no agent needed; fix already on branch `claude/festive-gates-4dkzds`, commit `80b7aa0`) | Ready for PR – just open/merge it, then close the issue |
| [#659](https://github.com/NikolayDA/picture_helper/issues/659) | Test suite audit: minor quality gaps across 6 batches (`test_i18n_sync`, `test_viewer_3d`, etc.) | 🟡 Medium (test quality/coverage, not a blocker) | 🟡 Medium (mix of trivial deletions/fixes and real coverage gaps across several modules) | Sonnet 5 (medium) – if adopted as N9/O8 | Needs decision – proposal not yet adopted into the findings list; owner sign-off pending, then implement as its own PR |
| [#656](https://github.com/NikolayDA/picture_helper/issues/656) | Enable ANTHROPIC_API_KEY secret for the vision pre-assessment | 🟡 Medium (only improves evidence quality; not a blocker per contract) | 🟢 Low (purely operational, no code) | – (no agent; repo owner: Settings → Secrets) | Blocked (external) – can be done independently |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restore OpenAI quota for the manual Codex security check | 🟢 Low (blocks only an optional manual scan) | 🟢 Low (purely operational, no code) | – (no agent; repo owner: billing) | Blocked (external) – resolve billing/quota on the OpenAI platform project |

### Recommended Next

1. **#660**: open a PR for the already-committed TESTING.md fix (branch `claude/festive-gates-4dkzds`, commit `80b7aa0`) and merge it; then close the issue.
2. **#659**: decide whether to adopt the proposed findings **N9** (remove/merge the dead-weight `test_i18n_sync.py`) and **O8** (tautological `viewer_3d` assertions plus coverage gaps in `screenshot3d.py`/`viewer_3d.py`/`preview3d_capability.py`/`height_map.py`/`gloss_preview.py`); implement as its own PR if agreed.
3. Handle **#656** independently if real vision verdicts are wanted — it's a quality improvement, not a blocker.
4. Leave **#245** as a purely external billing/quota tracker; no action possible or needed in the repository.
5. The acceptance/3D-epic chain (#646/#639/#595/#582) is fully closed and needs no further action.

## Previous Rounds

- **2026-07-22 (acceptance closeout)** — triggered a fresh `release-abnahme.yml` dispatch (run #4, commit `9165c00`); checked the matrix against #595 (x86_64 stays documented-paused but doesn't block); individually verified and closed #595, #646, #639, #582 against their own acceptance criteria. The one real gap found (mypy strictness for `scripts/abnahme_vision_check.py`/`abnahme_aggregate.py`, #646) was fixed and merged via PR #662. Two new audit issues (#659/#660) filed, still undecided. Live state 4 open issues — the lowest since this log began.
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
