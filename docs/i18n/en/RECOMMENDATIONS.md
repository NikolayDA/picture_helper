[Deutsch](../../../RECOMMENDATIONS.md) · **English** · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Code Analysis & Ranked Recommendations: BgRemover

## Rating Scale

| Symbol | Priority | Meaning |
|--------|----------|---------|
| 🔴 | Critical | Bugs, crashes, or data loss |
| 🟠 | High | Clear impact on reliability or maintainability |
| 🟡 | Medium | Useful improvement for quality, readability, or testability |
| 🟢 | Low | Optional polish or process improvement |

## Current Status (2026-06-04)

The active code-analysis list is empty. The latest follow-up review has been
implemented and covered by tests; ruff, mypy, and the local suite remain the
baseline before new PRs.

### Completed Since The Last Review

- **N1/N2/N4/N5/N6/N7/N8** are done: magic-wand error path, rotation size
  limit, honest file extensions, atomic save, CI Qt packages, lazy `rembg`
  import, and the `load_image` docstring.
- **O2/O3/O4/O5/O6** are implemented: Linux AppImage/`.deb`, release workflow,
  weekly full matrix, `ui_smoke` in PR/Full CI, and tool shortcuts with
  platform-correct hints.
- **#164/#167/#168** are done (PRs #172/#174/#173); the remaining findings
  have since been completed via #176/#178 as well.
- **Verified cleanly resolved on 2026-06-06** (PRs #188–#193, each with a
  regression test, `make check` green – 504 passed): **#163** (CHANGELOG links
  switched to real, GitHub-resolvable commit SHAs; four missing 2.3.0 features +
  idna/urllib3 entry added; real git tags intentionally not created),
  **#165/#180** (TESTING.md: `addopts` filter, `ui_smoke`, weekly schedule,
  shellcheck, `make coverage`), **#184** (load generation +
  `content_revision` recheck against late async loads), **#182**
  (`PIP_CONSTRAINT` wired into the AppImage build), **#183** (license-check
  read-only + isolated comment job), **#177** (behavioral assertions + new
  `tests/test_history_popup.py`).

### Still Open

- **O1 🟠 — Additional runtime languages.** German and English are switchable
  in the app. The existing documentation languages (es/fr/uk/zh) are not yet
  runtime locales; add them key-for-key in `bgremover.i18n` if needed and
  protect them with parity/smoke tests.

## Open GitHub Issues — Priority Assessment (2026-06-11)

Now **five** open issues: the watch items #203/#204, the deferred #161, plus
the documentation findings #218 (CHANGELOG gaps) and #226 (INSTALL review).
**#176 is resolved** (code-quality batch via
PRs #198/#214, issue closed); previously #166/#178/#185 (PRs #219–#221),
#205/#206 (PR #222) and #199/#200/#201/#202 (PRs #215/#209/#211). Of the
`pip-audit` batch from 2026-06-07 (#200–#206) only the watch items #203/#204
remain open; #195 stays closed and verified.

Triage of the security batch against the project's actual state
(`requirements/constraints.txt` + `pyproject.toml`):

- **#200/#201 are done (PR #209)** — `setuptools` is now pinned to `>=78.1.1` in
  `pyproject.toml` (`[build-system]`) and `constraints.txt`, and `wheel` to
  `==0.46.2`; CVE-tied regression tests guard against regressions.
- **#202 (pip) is done (PR #211)** — `pip>=26.1.2` is enforced in the CI setup
  steps (`ci.yml`/`pr-ci.yml`/`ui-nightly.yml`/`benchmark.yml`/
  `license-check.yml`), the web SessionStart hook and the dev install docs; a
  CVE-tied regression test guards it.
- **#203 (cryptography)/#204 (pyjwt)** are **not** project dependencies (purely
  transitive/system) → informational, no `constraints.txt` change.
- **#205 (urllib3)/#206 (idna) are done (PR #222)** — the project pins the
  patched releases (`urllib3==2.7.0`, `idna==3.15`); CVE-tied regression tests
  freeze them and the SessionStart hook now installs with constraints.

| # | Title | Relevance | Complexity | Recommendation |
|---|-------|-----------|------------|----------------|
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README audit: one broken external link, one internal-jargon note | 🟡 Medium | 🟢 Low | Blocked: "Runde 5" jargon removed; only clone URL remains (owner decision on repo visibility) |
| [#203](https://github.com/NikolayDA/picture_helper/issues/203) | cryptography 41.0.7 — HIGH/MEDIUM: 6 CVEs | 🟢 Low | 🟢 Low | Not a project dependency (transitive/system) → informational, no `constraints.txt` change |
| [#204](https://github.com/NikolayDA/picture_helper/issues/204) | pyjwt 2.7.0 — HIGH/MEDIUM: 5 CVEs | 🟢 Low | 🟢 Low | Not a project dependency → informational, no project action |
| [#218](https://github.com/NikolayDA/picture_helper/issues/218) | CHANGELOG: several `[Unreleased]` entries missing (PRs #174, #190–#215) | 🟡 Medium | 🟢 Low | Add the seven missing entries via a docs PR in the existing style |
| [#226](https://github.com/NikolayDA/picture_helper/issues/226) | INSTALL review: release-artifacts section points to empty releases + two minor items | 🟡 Medium | 🟢 Low | Add an "artifacts from v2.3.0" note (or tag v2.3.0, owner decision); "Bookworm or newer" + `diagnose_mac.sh` reference via docs PR |

### Recommended PR Order

1. **#200 done (PR #209)** — pinned `setuptools>=78.1.1` in `pyproject.toml` (`[build-system]`) **and** `constraints.txt`; CRITICAL RCE closed.
2. **#201 done (PR #209)** — pinned `wheel==0.46.2` in `constraints.txt`; bundled with #200 as a single supply-chain pinning PR.
3. **#202 done (PR #211)** — `pip>=26.1.2` enforced in the CI setup steps, the SessionStart hook + dev install docs; CVE batch (path traversal/symlink/module hijacking) closed.
4. **#176 done (PRs #198/#214)** — blanket `E741` ignore removed, `check_untyped_defs` active for `canvas`/`main_window`/`worker_controller`, cancel_ai wait made visible via status message, `shutdown_all` nulls thread references; dedicated tests for `app.py`/`main_window.py`. Verified against `main` on 2026-06-10 (`make check` green).
5. **#199 done (PR #215)** — removed the write-only `_redo_max` from `canvas_history.py`; regression test `test_redo_stack_capped_by_maxlen`, `make check` green.
6. **#166 done (PR #219)** — English docstrings/comments translated to German package-wide; "no own copy" comment made precise.
7. **#185 done (PR #220)** — diagnostics redact `$HOME`/paths and print a filtered log summary only; `--include-raw-logs` flag + shell test.
8. **#178 done (PR #221)** — tests moved to public accessors, AST checks replaced by behavioral tests, duplicate tests removed (from #168).
9. **#205/#206 done (PR #222)** — clean pins frozen by CVE-tied regression tests, SessionStart hook installs with constraints; issues closed.
10. **#203/#204 as watch items** — not project dependencies; pin only if a future feature pulls them in directly.
11. **#161 deferred** — "Runde 5" done; only the clone URL remains (owner decision on repo visibility).
12. **#218 as the next docs PR** — add the seven missing `[Unreleased]` entries to the CHANGELOG.
13. **#226 after that** — update the INSTALL guides; the release-artifacts note depends on the owner's tagging decision.

## Previous Rounds

- **2026-06-01, "modest-shannon" (A–E)** — 5 findings, all done.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, done or discarded
  where it was a false positive.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
