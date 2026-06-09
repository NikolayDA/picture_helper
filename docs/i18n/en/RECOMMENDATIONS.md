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

Now **thirteen** open issues. New since the last review: a `pip-audit` security
batch from 2026-06-07 (#200–#206) plus a dead-code finding (#199); #195 is
closed and verified.

Triage of the security batch against the project's actual state
(`requirements/constraints.txt` + `pyproject.toml`):

- **#200 (setuptools) is the only 🟠 finding** — `setuptools>=61` is a **direct
  build dependency** (`pyproject.toml`) and is **not** pinned in
  `constraints.txt`. CRITICAL RCE.
- **#201 (wheel)/#202 (pip)** are genuinely actionable: `wheel` is unpinned,
  `pip` ships uncontrolled in CI/dev.
- **#203 (cryptography)/#204 (pyjwt)** are **not** project dependencies (purely
  transitive/system) → informational, no `constraints.txt` change.
- **#205 (urllib3)/#206 (idna)** are **already pinned clean** in the project
  (`urllib3==2.7.0`, `idna==3.15`); system-only finding → closable.

| # | Title | Relevance | Complexity | Recommendation |
|---|-------|-----------|------------|----------------|
| [#200](https://github.com/NikolayDA/picture_helper/issues/200) | setuptools 68.1.2 — CRITICAL/HIGH: RCE + path traversal | 🟠 High | 🟢 Low | Ready for PR; direct build dependency — pin `setuptools>=78.1.1` in `pyproject.toml` + `constraints.txt` |
| [#201](https://github.com/NikolayDA/picture_helper/issues/201) | wheel 0.42.0 — HIGH: path traversal (file permissions) | 🟡 Medium | 🟢 Low | Ready for PR; pin `wheel==0.46.2` in `constraints.txt` (bundle with #200) |
| [#202](https://github.com/NikolayDA/picture_helper/issues/202) | pip 24.0 — HIGH/MEDIUM: 5 CVEs (path traversal, symlink) | 🟡 Medium | 🟢 Low | Ready for PR; require `pip>=26.1.2` in CI setup steps + dev docs |
| [#176](https://github.com/NikolayDA/picture_helper/issues/176) | Code-review follow-up (Low): E741, check_untyped_defs, cancel_ai UX, shutdown_all | 🟡 Medium | 🟢 Low | Ready for PR (from #167); `E741`/`check_untyped_defs` in `pyproject.toml` still unchanged |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README audit: one broken external link, one internal-jargon note | 🟡 Medium | 🟢 Low | Blocked: "Runde 5" jargon removed; only clone URL remains (owner decision on repo visibility) |
| [#199](https://github.com/NikolayDA/picture_helper/issues/199) | Dead code (Low): write-only `_redo_max` in `canvas_history.py` | 🟢 Low | 🟢 Low | Ready for PR; delete one line (module is strictly typed — `make check`) |
| [#185](https://github.com/NikolayDA/picture_helper/issues/185) | Security: macOS diagnostics disclose local paths + raw log tail (privacy) | 🟢 Low | 🟡 Medium | Ready for PR; redact `$HOME`/paths + `--include-raw-logs` flag + shell test |
| [#178](https://github.com/NikolayDA/picture_helper/issues/178) | Test-audit follow-up (Low): decouple from private internals + dedupe | 🟢 Low | 🟡 Medium | Ready for PR (from #168) |
| [#166](https://github.com/NikolayDA/picture_helper/issues/166) | Comment audit: language inconsistencies and minor phrasing inaccuracy | 🟢 Low | 🟢 Low | Ready for PR; English docstrings in `right_panel.py`/`main_window.py` |
| [#203](https://github.com/NikolayDA/picture_helper/issues/203) | cryptography 41.0.7 — HIGH/MEDIUM: 6 CVEs | 🟢 Low | 🟢 Low | Not a project dependency (transitive/system) → informational, no `constraints.txt` change |
| [#204](https://github.com/NikolayDA/picture_helper/issues/204) | pyjwt 2.7.0 — HIGH/MEDIUM: 5 CVEs | 🟢 Low | 🟢 Low | Not a project dependency → informational, no project action |
| [#205](https://github.com/NikolayDA/picture_helper/issues/205) | urllib3 2.6.3 — MEDIUM: 2 CVEs | 🟢 Low | 🟢 Low | No action; project already pins `urllib3==2.7.0` (clean) → closable |
| [#206](https://github.com/NikolayDA/picture_helper/issues/206) | idna 3.11 — MEDIUM: DoS via `idna.encode()` | 🟢 Low | 🟢 Low | No action; project already pins `idna==3.15` (clean) → closable |

### Recommended PR Order

1. **#200** — pin `setuptools>=78.1.1` in `pyproject.toml` (`[build-system]`) **and** `constraints.txt`. Top priority: CRITICAL RCE in a direct build dependency.
2. **#201** — pin `wheel==0.46.2` in `constraints.txt`; bundle with #200 as a single supply-chain pinning PR.
3. **#202** — require `pip>=26.1.2` in the CI setup steps + dev install docs.
4. **#176** — Code-quality batch from #167: narrow `E741`, `check_untyped_defs` incrementally, cancel_ai UX, null `shutdown_all` thread references.
5. **#199** — remove the write-only `_redo_max` from `canvas_history.py` (trivial fix, regression covered by `make check`).
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
