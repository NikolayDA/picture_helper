[Deutsch](../../../RECOMMENDATIONS.md) · **English** · [Español](../es/RECOMMENDATIONS.md) · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Code Analysis & Ranked Recommendations: BgRemover

## Rating Scale

| Symbol | Priority | Meaning |
|--------|----------|---------|
| 🔴 | Critical | Bugs, crashes, or data loss |
| 🟠 | High | Clear impact on reliability or maintainability |
| 🟡 | Medium | Useful improvement for quality, readability, or testability |
| 🟢 | Low | Optional polish or process improvement |

## Current Status (2026-06-29)

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

## Open GitHub Issues — Triage Status (2026-06-29, updated)

As of 2026-06-29, GitHub shows **8** open issues: **#245**, **#299**, **#318**,
**#389**, **#392**, **#404**, **#406**, and **#408**. New on the same day is the
doc/code audit **#408** (API/CLI docs against the current signatures — no drift);
the quality/robustness issues **#406** and **#404** (new since the 2026-06-25
review) remain open. Documentation
bundles **#390/#391**, startup-path note **#357**, and the HEIC exclusion
**#339** remain closed; only release step **#392** is left in epic **#389**.

**Comment pass:** No new external comments; the existing ones on #392/#299/#245
are owner triage notes consistent with the current state, and #408 is new with no
comments — no issue update needed.

**New findings verified against the code:** #406 — `_derive_physical_size`
(`eufymake_export.py:217`) has no caller (`parse_size_mm` imported only there,
still used in `project_model.py`). #404 — `compose_relief`/`compose_gloss`
(`canvas.py:555/564`) raise instead of degrading to COLOR in the render path.
#408 — audit with no findings: the signatures in `CLAUDE.md`/`README.md` and the `bgremover image.png` CLI path match the code.

### Sensible Bundles

- **Release bundle:** **#392** is ready now; close epic **#389** after the tag,
  release body, and macOS/Linux artifacts are verified.
- **Quality quick wins:** **#406** and **#404** are small, self-contained, and
  ready for PR — ideal as short quality PRs alongside the release path, but kept
  separate from it (different modules, no shared diff).
- Do not mix **#299/#318/#245** into the release path; they are independent
  quality, research, and externally blocked operational work.

Rating: **Relevance** = importance to the roadmap/users, **Complexity** =
estimated implementation effort.

| # | Title | Relevance | Complexity | Recommended next step |
|---|-------|-----------|------------|-----------------------|
| [#392](https://github.com/NikolayDA/picture_helper/issues/392) | Cut release v2.5.0 (CHANGELOG/version/tag/artifacts) | 🟠 High | 🟡 Medium | **Ready** – #390, #391, and #384 are closed. |
| [#389](https://github.com/NikolayDA/picture_helper/issues/389) | [Epic] Update user docs & cut release | 🟠 High | 🟢 Low (remaining) | **Nearly complete** – only #392 remains open. |
| [#404](https://github.com/NikolayDA/picture_helper/issues/404) | Preview render: size mismatch does not degrade to COLOR | 🟡 Medium | 🟢 Low | **Ready for PR** – wrap `compose_relief`/`compose_gloss` defensively and fall back to `base` on a size mismatch, with a render/pixel regression test. Latent but clearly scoped. |
| [#406](https://github.com/NikolayDA/picture_helper/issues/406) | Dead code: unused `_derive_physical_size` in `eufymake_export.py` | 🟢 Low | 🟢 Low | **Ready for PR** – remove the function, clean up the `parse_size_mm` import, and update the CLAUDE.md geometry sentence to the `_derive_target`/project-model path. Trivial, with full acceptance criteria. |
| [#408](https://github.com/NikolayDA/picture_helper/issues/408) | Doc/code audit: API/CLI docs match the function signatures (no drift) | 🟢 Low | 🟢 Low | **Informational / closeable** – audit with no findings, no code/doc fix needed. Optional follow-up: a real `docs/api.md` via autodoc so future drift is caught automatically. |
| [#299](https://github.com/NikolayDA/picture_helper/issues/299) | Test hygiene: weak assertions/redundancies | 🟢 Low | 🟢 Low | **After v2.5.0** – highest impact first (lasso endpoint, writable NumPy result, full wand mask, brush parametrization). |
| [#318](https://github.com/NikolayDA/picture_helper/issues/318) | Test: respect job-level permission overrides in reusable WF | 🟢 Low | 🟡 Medium | **Needs refinement** – prove GitHub semantics first; change code only for a demonstrated false positive and preserve #303. |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | CI: Codex Security Scan fails with "Quota exceeded" | 🟡 Medium | 🟢 Low | **Blocked (external)** – repo-side hardening via #322/#342 (closed) is done; the remaining blocker is OpenAI/billing quota. After the quota is restored, trigger the scheduled scan once manually, then close. |

### Recommended Next (PR order)

1. Pull **#406** and **#404** forward as short quality PRs — both are verified,
   self-contained, and ready for PR (different modules, low risk).
2. Run **#392** next, then close epic **#389** once the tag, release body, and
   both artifacts are verified.
3. Tackle **#299** after v2.5.0; research **#318** only (needs refinement), close
   **#408** as an informational audit with no action, and keep **#245** blocked.

## Previous Rounds

- **2026-06-01, "modest-shannon" (A–E)** — 5 findings, all done.
- **v2.2, "admiring-mayer" (#1–#15)** — external list, completed or discarded where it was a false positive.

Full historical findings and work logs (rounds 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.en.md).
