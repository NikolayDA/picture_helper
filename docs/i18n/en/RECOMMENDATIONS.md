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

## Open GitHub Issues — Priority Assessment (2026-06-07)

Now **six** open issues: one 🟠 CI blocker (#195) and five 🟡/🟢: two
`documentation` (#161, #166), two `quality/testing` (#176, #178), and one
privacy security finding (#185). #163/#165/#177/#180 plus the three
higher-priority security findings from the Codex scan `8c04b92`
(#182/#183/#184) are closed and verified since the last review.

| # | Title | Relevance | Complexity | Recommendation |
|---|-------|-----------|------------|----------------|
| [#195](https://github.com/NikolayDA/picture_helper/issues/195) | Full-CI blocker (mypy/3.10): `canvas_selection.py` shape-typing – numpy-2.2.6 stubs | 🟠 High | 🟢 Low | Ready for PR; `self._mask: npt.NDArray[np.bool_]` — verified one-liner fix |
| [#176](https://github.com/NikolayDA/picture_helper/issues/176) | Code-review follow-up (Low): E741, check_untyped_defs, cancel_ai UX, shutdown_all | 🟡 Medium | 🟢 Low | Ready for PR (from #167); `E741`/`check_untyped_defs` in `pyproject.toml` still unchanged |
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README audit: one broken external link, one internal-jargon note | 🟡 Medium | 🟢 Low | Partly done: "Runde 5" jargon removed; only clone URL remains (owner decision) |
| [#185](https://github.com/NikolayDA/picture_helper/issues/185) | Security: macOS diagnostics disclose local paths + raw log tail (privacy) | 🟢 Low | 🟡 Medium | Ready for PR; redact `$HOME`/paths + `--include-raw-logs` flag + shell test |
| [#178](https://github.com/NikolayDA/picture_helper/issues/178) | Test-audit follow-up (Low): decouple from private internals + dedupe | 🟢 Low | 🟡 Medium | Ready for PR (from #168) |
| [#166](https://github.com/NikolayDA/picture_helper/issues/166) | Comment audit: language inconsistencies and minor phrasing inaccuracy | 🟢 Low | 🟢 Low | Ready for PR; English docstrings in `right_panel.py`/`main_window.py` |

### Recommended PR Order

1. **#195** — `self._mask: npt.NDArray[np.bool_]` in `canvas_selection.py`; Full-CI Python-3.10 cells green again.
2. **#176** — Code-quality batch from #167: narrow `E741`, `check_untyped_defs` incrementally, cancel_ai UX, null `shutdown_all` thread references.
3. **#185** — Redact macOS diagnostics (`$HOME`/paths) + add `--include-raw-logs` flag + shell test.
4. **#178** — Decouple tests from private internals + reduce duplicate tests (from #168).
5. **#166** — Docstring language cleanup as a small housekeeping PR.
6. **#161 deferred** — "Runde 5" done; only the clone URL remains (owner decision on repo visibility).

## Previous Rounds

- **2026-06-01, "modest-shannon" (A–E)** — 5 findings, all done.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, done or discarded
  where it was a false positive.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
