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
- **Security batch from 2026-06-07 completed** (#200/#201/#202/#205/#206 via
  PRs #209/#211/#222): setuptools/wheel/pip/urllib3/idna pinned or enforced,
  each guarded by a CVE-tied regression test.

### Still Open

- **O1 🟠 — Additional runtime languages.** German and English are switchable
  in the app. The existing documentation languages (es/fr/uk/zh) are not yet
  runtime locales; add them key-for-key in `bgremover.i18n` if needed and
  protect them with parity/smoke tests.

## Open GitHub Issues — Priority Assessment (2026-06-12)

Now **14** open issues: the watch items #203/#204, the deferred #161, the
docs/audit findings #218/#226/#227/#236, plus the code-quality batch
#229–#235 from the 2026-06-11 audit. #203/#204 are not project dependencies
(purely transitive/system) → informational, no `constraints.txt` change.

| # | Title | Relevance | Complexity | Recommendation |
|---|-------|-----------|------------|----------------|
| [#161](https://github.com/NikolayDA/picture_helper/issues/161) | README audit: clone URL leads nowhere | 🟡 Medium | 🟢 Low | Blocked (owner decision on repo visibility) |
| [#203](https://github.com/NikolayDA/picture_helper/issues/203) | cryptography 41.0.7 — 6 CVEs | 🟢 Low | 🟢 Low | Watch item, no project action |
| [#204](https://github.com/NikolayDA/picture_helper/issues/204) | pyjwt 2.7.0 — 5 CVEs | 🟢 Low | 🟢 Low | Watch item, no project action |
| [#218](https://github.com/NikolayDA/picture_helper/issues/218) | CHANGELOG: `[Unreleased]` entries missing | 🟡 Medium | 🟢 Low | Ready for PR (add the seven entries in the existing style) |
| [#226](https://github.com/NikolayDA/picture_helper/issues/226) | INSTALL review: points to empty releases + two minor items | 🟡 Medium | 🟢 Low | Ready for PR (doc fixes); release-artifacts note depends on the tagging decision |
| [#227](https://github.com/NikolayDA/picture_helper/issues/227) | RECOMMENDATIONS audit: issue overview stale | 🟡 Medium | 🟢 Low | Resolved by this update → close the issue |
| [#229](https://github.com/NikolayDA/picture_helper/issues/229) | rembg warmup creates no reusable inference session | 🟠 High | 🟡 Medium | Ready for PR (cache a session via `new_session`) |
| [#230](https://github.com/NikolayDA/picture_helper/issues/230) | File fully read into memory before size check | 🟠 High | 🟢 Low | Ready for PR (byte limit before the `read()`) |
| [#231](https://github.com/NikolayDA/picture_helper/issues/231) | `QThread.terminate()` can abort workers unsafely | 🟡 Medium | 🟠 High | Needs refinement (decide option A/B/C; short-term option C) |
| [#232](https://github.com/NikolayDA/picture_helper/issues/232) | `import bgremover` loads the full PyQt6 GUI | 🟡 Medium | 🟡 Medium | Ready for PR (lazy exports via PEP 562) |
| [#233](https://github.com/NikolayDA/picture_helper/issues/233) | Corrupt recent_files settings break menu build | 🟡 Medium | 🟢 Low | Ready for PR (defensive `paths()` + parameterized tests) |
| [#234](https://github.com/NikolayDA/picture_helper/issues/234) | Missing migration still bumps `schema_version` | 🟢 Low | 🟢 Low | Ready for PR (before the first real migration) |
| [#235](https://github.com/NikolayDA/picture_helper/issues/235) | Undo limit ignores redo/original image | 🟢 Low | 🟡 Medium | Needs refinement (decide docs-only vs. shared budget) |
| [#236](https://github.com/NikolayDA/picture_helper/issues/236) | session-start.sh comment: `benchmark.yml` missing | 🟢 Low | 🟢 Low | Ready for PR (one-line comment fix) |

### Recommended PR Order

1. **#230** — highest relevance at low complexity: file-size limit before reading, covers the sync and async paths centrally.
2. **#229** — reuse the warmup session; biggest win for the AI pipeline, and the incorrect comment gets fixed along the way.
3. **#233** — defensive `paths()` with parameterized tests; matches the robustness goal of the settings schema.
4. **#236 + #218** — small comment/docs fixes, ideally bundled; **#227** is resolved by this update and can be closed.
5. **#232** — lazy exports via PEP 562; medium scope due to test/import migration.
6. **#234** — small fix; schedule it before the first real schema migration at the latest.
7. **#226** — doc fixes now; the release-artifacts note depends on the owner's tagging decision.
8. **#235** — decide the semantics first (docs-only vs. shared budget), then implement.
9. **#231** — short term option C (bounded waits + logging), evaluate option B (subprocess) long term.
10. **#203/#204** remain watch items; **#161** remains blocked (owner decision).

## Previous Rounds

- **2026-06-01, "modest-shannon" (A–E)** — 5 findings, all done.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, done or discarded
  where it was a false positive.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
