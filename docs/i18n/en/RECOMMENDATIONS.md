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
  continue focused in #176/#178.
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

## Open GitHub Issues — Priority Assessment (2026-06-09)

Now **nine** open issues. **#199/#200/#201/#202 are resolved** (dead-code
removal via PR #215, build backend pinned via PR #209, pip pin via PR #211). The
`pip-audit` security batch from 2026-06-07 (#200–#206) remains triaged; #195 is
closed and verified.

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
- **#205 (urllib3)/#206 (idna)** are **already pinned clean** in the project
  (`urllib3==2.7.0`, `idna==3.15`); system-only finding → closable.

| # | Title | Relevance | Complexity | Recommendation |
|---|-------|-----------|------------|----------------|
| [#176](https://github.com/NikolayDA/picture_helper/issues/176) | Code-review follow-up (Low): E741, check_untyped_defs, cancel_ai UX, shutdown_all | 🟡 Medium | 🟢 Low | Ready for PR (from #167); `E741`/`check_untyped_defs` in `pyproject.toml` still unchanged |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README audit: one broken external link, one internal-jargon note | 🟡 Medium | 🟢 Low | Blocked: "Runde 5" jargon removed; only clone URL remains (owner decision on repo visibility) |
| [#185](https://github.com/NikolayDA/picture_helper/issues/185) | Security: macOS diagnostics disclose local paths + raw log tail (privacy) | 🟢 Low | 🟡 Medium | Ready for PR; redact `$HOME`/paths + `--include-raw-logs` flag + shell test |
| [#178](https://github.com/NikolayDA/picture_helper/issues/178) | Test-audit follow-up (Low): decouple from private internals + dedupe | 🟢 Low | 🟡 Medium | Ready for PR (from #168) |
| [#166](https://github.com/NikolayDA/picture_helper/issues/166) | Comment audit: language inconsistencies and minor phrasing inaccuracy | 🟢 Low | 🟢 Low | Ready for PR; English docstrings in `right_panel.py`/`main_window.py` |
| [#203](https://github.com/NikolayDA/picture_helper/issues/203) | cryptography 41.0.7 — HIGH/MEDIUM: 6 CVEs | 🟢 Low | 🟢 Low | Not a project dependency (transitive/system) → informational, no `constraints.txt` change |
| [#204](https://github.com/NikolayDA/picture_helper/issues/204) | pyjwt 2.7.0 — HIGH/MEDIUM: 5 CVEs | 🟢 Low | 🟢 Low | Not a project dependency → informational, no project action |
| [#205](https://github.com/NikolayDA/picture_helper/issues/205) | urllib3 2.6.3 — MEDIUM: 2 CVEs | 🟢 Low | 🟢 Low | No action; project already pins `urllib3==2.7.0` (clean) → closable |
| [#206](https://github.com/NikolayDA/picture_helper/issues/206) | idna 3.11 — MEDIUM: DoS via `idna.encode()` | 🟢 Low | 🟢 Low | No action; project already pins `idna==3.15` (clean) → closable |

### Recommended PR Order

1. **#200 done (PR #209)** — pinned `setuptools>=78.1.1` in `pyproject.toml` (`[build-system]`) **and** `constraints.txt`; CRITICAL RCE closed.
2. **#201 done (PR #209)** — pinned `wheel==0.46.2` in `constraints.txt`; bundled with #200 as a single supply-chain pinning PR.
3. **#202 done (PR #211)** — `pip>=26.1.2` enforced in the CI setup steps, the SessionStart hook + dev install docs; CVE batch (path traversal/symlink/module hijacking) closed.
4. **#176** — Code-quality batch from #167: narrow `E741`, `check_untyped_defs` incrementally, cancel_ai UX, null `shutdown_all` thread references.
5. **#199 done (PR #215)** — removed the write-only `_redo_max` from `canvas_history.py`; regression test `test_redo_stack_capped_by_maxlen`, `make check` green.
6. **#166** — Docstring language cleanup as a small housekeeping PR.
7. **#185** — Redact macOS diagnostics (`$HOME`/paths) + add `--include-raw-logs` flag + shell test.
8. **#178** — Decouple tests from private internals + reduce duplicate tests (from #168).
9. **#205/#206 closable** — project pinning already correct (`urllib3==2.7.0`, `idna==3.15`); system-only findings.
10. **#203/#204 as watch items** — not project dependencies; pin only if a future feature pulls them in directly.
11. **#161 deferred** — "Runde 5" done; only the clone URL remains (owner decision on repo visibility).

## Previous Rounds

- **2026-06-01, "modest-shannon" (A–E)** — 5 findings, all done.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, done or discarded
  where it was a false positive.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
