[Deutsch](../../../RECOMMENDATIONS.md) · **English** · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Code Analysis & Ranked Recommendations: BgRemover

## Rating Scale

| Symbol | Priority | Meaning |
|--------|----------|---------|
| 🔴 | Critical | Bugs, crashes, or data loss |
| 🟠 | High | Clear impact on reliability or maintainability |
| 🟡 | Medium | Useful improvement for quality, readability, or testability |
| 🟢 | Low | Optional polish or process improvement |

## Current Status (2026-06-24)

The active code-analysis list is empty. Ruff, mypy, and the local test suite
remain the baseline before new PRs.

### Completed Since The Last Review

- **N1/N2/N4/N5/N6/N7/N8** are done: error paths, size limit, file
  extensions, atomic save, CI Qt packages, lazy import, and docstring.
- **O2/O3/O4/O5/O6** are implemented: Linux packages, release workflow,
  full matrix, `ui_smoke`, and platform-correct tool shortcuts.
- Older closed findings (incl. EufyMake epic **#351/#352–#355** and the rembg/ONNX subprocess **#270/#285/#286**) are done in the documented PRs, covered by tests/CI, and archived.

- **N9 ✅ — Project/layer data model (epic #329) delivered.** Qt-free domain
  model (#330), layer-aware history (#331), composite canvas (#332), `.bgrproj`
  format (#333), layer panel/project menu (#334) and migration/integration
  (#335) — single-image parity preserved, `make check`/`make ui` green.
- **N10 ✅ — Height-map workspace (epic #344) delivered.** Qt-free height
  representation and 2D visualization (#345), algorithmic generation and
  grayscale import (#346), height editing (#347), `height_ops` optimization
  with live preview (#348), and the mode-aware Height tab (#349).
- **N11 ✅ — Phase-0 polish (epic #358) delivered.** Target-size project resize
  (#359), alpha-preserving brightness/contrast/saturation with live preview
  (#360), and selection-bounded alpha-edge feathering (#361), all undoable and
  persisted losslessly in `.bgrproj` (PR #362).
- **N12 ✅ — Combined 2D preview (epic #384) delivered.** Qt-free relief/gloss
  renderers (#385/#386), explicit active-layer-independent canvas modes with a
  bounded cache (#387), and a synchronized View menu/Preview panel with live
  strength and gloss toggle (#388); the full mode×layer matrix keeps the #363
  export contract bit-exact. Review follow-up #397 (PR #398) routes transient
  color/height previews through the same pipeline, honors hidden data roles, and
  efficiently skips zero-strength relief.
- **#363 ✅ — Export regression fixed (PR #367).** Save Image once again writes
  the COLOR composite regardless of the active layer; display and export
  rendering are separated, covered by a pixel regression test.

### Still Open

- **O1 🟠 — Additional runtime languages.** German and English are switchable
  in the app. The documentation languages es/fr/uk/zh are not runtime locales;
  add them key-for-key in `bgremover.i18n` if needed and cover them with tests.
- **O7 ✅ — Subprocess for rembg/ONNX done (PR #283, issue #270 closed).** The
  non-interruptible AI inference now runs in a `spawn`-started process
  (`ai_process.py`); `QThread.terminate()` as the AI emergency exit is gone.
  The robustness/memory follow-up findings are fixed and closed in **#285**
  (PR #289).

## Open GitHub Issues — Triage Status (2026-06-24, updated)

As of 2026-06-24, after #384/#387/#388 and P2 review follow-up **#397**
(PR #398), GitHub shows **9** open issues. Epics **#375** (physical mm/DPI
output + export validation) and **#384** (combined 2D preview) are complete and
closed. The remaining roadmap epic is:

- **#389 – Update user docs & cut release v2.5.0** with sub-issues **#390** (the
  ANLEITUNG user guide, 6 languages — also closes **#357**), **#391** (README +
  screenshots + i18n) and **#392** (release v2.5.0).

The docs gaps **#357** (now covered by #390) and **#339** plus the test/CI
findings **#318**, **#299** and **#245** also remain.

**Comment review (2026-06-24):** The comments on **#245**, **#299** and **#339**
all come from the maintainer (triage) and confirm the documented status: #245
stays externally blocked on quota/billing, #299 stays low-priority test hygiene,
and #339 is confirmed as a deliberate HEIC exclusion. No comment requires a
substantive issue update; #397 is already closed by PR #398.

### Sensible Bundles

- **Guide bundle:** **#390 + #357** plus the ANLEITUNG part of **#339**.
- **README bundle:** **#391** plus the README part of **#339** and current screenshots.
- **Release bundle:** keep **#392** separate and start it only after both docs PRs.
- Do not mix **#299/#318/#245** into the release path; they are independent
  quality, research, and externally blocked operational work.

Rating: **Relevance** = importance to the roadmap/users, **Complexity** =
estimated implementation effort.

| # | Title | Relevance | Complexity | Recommended next step |
|---|-------|-----------|------------|-----------------------|
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | [Epic] Update user docs & cut release | 🟠 High | 🟡 Medium (epic) | **Ready to start (epic)** – two parallel docs bundles, then #392. |
| [#390](https://github.com/NikolayDA/picture_helper/issues/390) | Update ANLEITUNG user guide (+ 5 i18n) for the new features | 🟠 High | 🔴 High (L, 6 languages) | **Bundle A** – include **#357** and the ANLEITUNG part of **#339**. |
| [#391](https://github.com/NikolayDA/picture_helper/issues/391) | Update README + screenshots + i18n | 🟡 Medium–High | 🟡 Medium | **Bundle B** – include the README part of **#339** and capture current screenshots. |
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | Cut release v2.5.0 (CHANGELOG/version/tag/artifacts) | 🟠 High | 🟡 Medium | **Blocked** – needs #390 + #391. |
| [#357](https://github.com/NikolayDA/picture_helper/issues/357) | Docs: startup-path/Finder opening is missing from ANLEITUNG §4 | 🟢 Low | 🟢 Low | **Part of bundle A** – do not handle separately; close with #390. |
| [#339](https://github.com/NikolayDA/picture_helper/issues/339) | HEIC/HEIF is not supported as an input format | 🟢 Low | 🟢 Low | **Split across A/B** – ANLEITUNG in #390, README in #391; close only after both. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test hygiene: weak assertions/redundancies | 🟢 Low | 🟢 Low | **After v2.5.0** – highest impact first (lasso endpoint, writable NumPy result, full wand mask, brush parametrization). |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: respect job-level permission overrides in reusable WF | 🟢 Low | 🟡 Medium | **Parallel research** – prove GitHub semantics first; change code only for a demonstrated false positive and preserve #303. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan fails with "Quota exceeded" | 🟡 Medium | 🟢 Low | **Blocked (external)** – repo-side hardening via #322/#342 (closed) is done; the remaining blocker is OpenAI/billing quota. After the quota is restored, trigger the scheduled scan once manually, then close. |

### Recommended Next (PR order)

1. Deliver **bundle A (#390 + #357 + ANLEITUNG part of #339)** and **bundle B
   (#391 + README part of #339)** in parallel; close #339 only after both.
2. Run **#392** after both docs bundles, then close epic **#389** once the tag,
   release body, and both artifacts are verified.
3. Tackle **#299** after v2.5.0; research **#318** in parallel without coding
   before evidence, and keep **#245** blocked until the external quota returns.

## Previous Rounds

- **2026-06-01, "modest-shannon" (A–E)** — 5 findings, all done.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, completed or discarded where it was a false positive.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
