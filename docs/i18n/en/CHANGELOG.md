[Deutsch](../../../CHANGELOG.md) · **English** · [Español](../es/CHANGELOG.md) · [Français](../fr/CHANGELOG.md) · [Українська](../uk/CHANGELOG.md) · [简体中文](../zh/CHANGELOG.md)

# Changelog

All notable changes to BgRemover are documented in this file. The format
is based on [Keep a Changelog](https://keepachangelog.com/de/1.1.0/);
the project follows [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

### Added

- **Light theme & design tokens (UI redesign, epic #424).** A central,
  token-based theming system (a `Palette` with a light and a dark scheme) colors
  the entire interface through a `QPalette` and an application-wide stylesheet.
  “View → Light theme” switches between light and dark at runtime; the choice is
  remembered in the settings and applied at startup. Accessibility: every
  interactive element shows a visible focus ring (also after switching themes),
  the step bar is keyboard-operable (Tab + Enter/Space), all controls meet
  minimum hit-target sizes, and a WCAG AA contrast matrix permanently guards
  both color schemes (#427–#429, #441).
- **Guided workflow with card inspector (UI redesign, epics #413/#418).** The right
  column now guides editing in six clear steps (Open · Cut out · Adjust · Shape &
  Size · Relief & Layers · Export): a step bar on top, an inspector with a step
  header and a fixed Back/Next navigation, plus a contextual tool rail (selection
  tools only in the cut-out step). Steps 2–6 stay locked until an image is loaded;
  loading advances to the cut-out step automatically. The existing action wiring
  (`RightPanelActions`/`LayerPanelActions`/`HeightMapActions`) is unchanged
  (#419–#422, #415–#417).

- **User-selectable combined 2D preview (phase-1 completion).** The canvas now
  offers explicit modes for Color, Relief over color, Height (grayscale), Gloss,
  and the Combined view, independent of the active layer. A one-image cache is
  invalidated by content revision, mode, and display settings; the View menu and
  new Preview tab stay synchronized, while relief strength and gloss visibility
  update live. A clear notice and a mode×layer test matrix preserve the #363
  contract: “Save image” still exports the COLOR composite only (#387, #388;
  completes epic #384).
- **Qt-free relief and gloss renderers for the combined 2D preview.** The new,
  strictly typed `bgremover/relief_preview.py` and `bgremover/gloss_preview.py`
  modules produce deterministic directional hillshade from `HeightField`
  (equivalent for 8-/16-bit data) and a visible gloss sheen. Both compose their
  effect over an RGBA color motif with size validation, preserve its alpha channel
  bit-for-bit, and provide true neutral no-ops; pure pixel/boundary tests cover light
  direction, coverage, strength, and alpha (#385, #386).
- **Pre-export checks on a normal save.** “Save”/“Save as…” now runs the general
  check (#379) on the project before writing and shows the findings just like the
  EufyMake flow: **errors block** saving with a clear message (no write call),
  **warnings** require a deliberate confirmation. Cancelling is side-effect-free (no
  write, no temporary files). Partial transparency is deliberately **not** flagged –
  it is the normal output of a background-removal tool. All strings de/en; the finding
  display reuses the same `format_finding` render logic as the EufyMake display (#380).
  This completes epic #375 (dimension-accurate output + export checks).
- **mm/DPI mode in the “Resize…” dialog + print-area check.** The resize dialog now
  offers two units: pixels (as before) and **millimeters + DPI**. In mm mode you enter
  width/height in mm and the DPI, the resulting **pixel size** is shown live via the
  shared geometry (#376), and the aspect ratio can optionally be locked. A
  **print-area check** compares the motif against a selectable target medium
  (A3/A4/A5/Letter) and warns clearly when it is exceeded. On apply, the physical
  target size (mm) is anchored in the project via the `project_model` setters
  (canonical; DPI follows from mm + pixel size) and survives the `.bgrproj` round-trip;
  the resampling itself stays purely pixel-based (`Project.resize`). All strings de/en
  (#377).
- **General, Qt-free pre-export checks (shared framework).** A new, strictly typed
  module `bgremover/export_checks.py` lifts the finding framework from
  `eufymake_validate` (#354) onto a shared base: a generic `Finding`/`CheckCode`/
  `Severity` contract with stable codes, i18n keys (`export.checks.*`, de/en) and
  deterministic ordering. It implements format-independent checks for dimensions
  (px > 0, megapixel limit), resolution plausibility (DPI from #376), color space
  (expected RGBA), transparency (fully transparent / unexpected partial alpha), empty
  output and the print-area/margin check (physical size against the target medium).
  `eufymake_validate` now builds on the shared base (re-exporting `Severity`/
  `has_blocking_errors`/`split_findings`); EufyMake-specific codes stay there and all
  prior EufyMake tests stay unchanged green (#379).
- **Anchor DPI/resolution in outputs.** When saving raster images,
  `image_ops.save_image_file` now optionally embeds the project DPI (#376) as pure
  metadata – PNG (`pHYs`), JPEG (JFIF density) and TIFF
  (`Resolution`/`ResolutionUnit`); WebP carries no DPI. The canvas save path passes
  the resolution derived from physical size + pixel size; without a project DPI the
  behavior is unchanged and the pixels/alpha are never touched (the bit-exact
  single-COLOR export is preserved). The EufyMake export now feeds its `ExportTarget`
  from the model mm/DPI getters instead of an export-local derivation (#378).
- **mm/DPI as a project property + shared Qt-free geometry.** A new, strictly
  typed module `bgremover/units.py` bundles all px↔mm↔DPI math in one place: from any
  two known quantities it derives the third deterministically (`MM_PER_INCH = 25.4`),
  validates inputs and reports invalid values (≤ 0, non-numeric, wrong shape) as
  structured `UnitsError` errors instead of silently correcting them. `Project` gains
  validated setters/getters for the physical target size (mm) and the resolution (DPI) –
  the physical size is the canonical source, the DPI is derived from it and the pixel
  size (no drift) and survives the `.bgrproj` round-trip value-equal. The EufyMake export
  now uses the same geometry (`_derive_physical_size`/`_derive_dpi`/`MM_PER_INCH`) with
  no behavioral change (#376).
- **EufyMake Studio import: menu, dialog, check display & settings.** A new menu
  action “Export assets for EufyMake Studio…” (Project menu, Ctrl+Alt+E) opens a Qt
  dialog (`eufymake_export_dialog.py`): the color motif is mandatory, the height
  map/gloss mask are selectable only when the project supports them (gloss visibly
  marked experimental), bit depth 8/16 (16 marked unconfirmed), derived target/
  physical size, and a **live findings display** from the check (#354): errors
  block, warnings require explicit confirmation. Writing is atomic via
  `write_export`; cancel/errors change neither the project nor the target, and an
  overwrite prompt protects existing folders. The success dialog shows the target
  path and the next Studio steps (import, positioning, ink-mode/layer assignment,
  saving as `.empf`). The export folder and general options are remembered in the
  versioned QSettings (schema v2, additive keys with migration).
  `build_export_plan`/`write_export` gained `optional_roles`/`bit_depth` for the UI
  selection. All strings in de/en; the UI consistently talks about import assets,
  never a finished `.empf` project (#355).
- **EufyMake export: rendering, atomic writing & consistency check (Qt-free).**
  Two new strictly typed modules build on the plan from #352:
  `bgremover/eufymake_validate.py` (`validate_export`) collects deterministically
  sorted, structured findings (stable code, `error`/`warning`, role, i18n key);
  hard errors (missing color motif, missing selected role, size mismatch, invalid
  target parameters) block, while warnings (empty/constant height/gloss data,
  unconfirmed 16-bit, gloss as an ink-mode helper asset, physical size without a
  vendor contract) allow the export only after confirmation – all messages in
  de/en (#354). `bgremover/eufymake_writer.py` (`render_export`/`write_export`)
  renders the color motif (= composite, RGBA alpha-preserving), the height map
  (grayscale light = high, 8/16-bit) and the optional gloss mask at target size
  together with `manifest.json`, and writes them **atomically** (render into a temp
  directory, publish in one `os.replace` step; a failure preserves an existing
  target, temp data is cleaned up; collision behavior via `overwrite`). No native
  `.empf` (#353).
- **EufyMake export: data model & planning (Qt-free).** New strictly typed
  module `bgremover/eufymake_export.py`: `build_export_plan(project)` maps the
  layer roles deterministically onto an `ExportPlan` of `ExportAsset`s – the color
  motif as an RGBA PNG is **required** (explicit `COLOR_MOTIF` role or the COLOR
  composite), the height map and gloss mask are **optional** grayscale PNGs (gloss
  experimental). File names, profile version, and defaults are documented
  **BgRemover conventions** (not an official EufyMake specification); the height
  semantics **light = high** are fixed in the type contract, while open bit-depth/
  gloss questions and the deliberate absence of a native `.empf` stay explicitly
  marked. Physical size, DPI, and bit depth are derived reproducibly from project
  metadata or defaults; invalid values yield structured errors. A pure data model
  with no rendering/writing/UI (follows in #353–#355) (#352).
- **EufyMake export package ADR.** A new architecture decision documents the
  import-oriented package convention for #352/#351: the color motif as an RGBA
  PNG, the height map as a grayscale PNG with light = high, an optional gloss
  mask, and open questions around 16-bit data, gloss semantics, and the native
  `.empf` format.
- **Cut-out polish: edge smoothing / feather.** New Qt-free, strictly typed
  `feather_alpha(img, radius, *, mask=None)` in `image_ops.py`: a Gaussian blur of
  **the alpha channel only** (RGB preserved bit-for-bit; `radius = 0` = no-op;
  fully opaque layers stay artifact-free at the border). The canvas wires it up as
  `feather_active_edges(radius)` on the active layer – **selection-bounded** (an
  existing selection) and **undo-/redoable** via the existing apply path. UI: a
  radius slider + “Smooth edge” button in the Background tab (next to the cut-out).
  All new strings in de/en parity (#361).
- **Color correction of the active color layer (brightness/contrast/saturation).**
  New Qt-free, strictly typed `bgremover/color_ops.py` module with `adjust_color`
  (Pillow `ImageEnhance`, **alpha channel exactly preserved**, neutral values =
  bit-identical no-op) – a reusable tone primitive for the later shared engine
  (rank #6). The canvas provides a generic **live preview**
  (`preview_color_op`/`cancel_color_preview`, transient without model changes; the
  preview takes precedence in `_refresh_image`) and an undo-/redoable commit
  (`apply_color_op`) on the active **COLOR** layer (no effect on non-COLOR
  layers). A new “Adjust” tab in the right panel offers brightness/contrast/
  saturation sliders with **Reset** and **Apply**. All new strings in de/en parity
  (#360).
- **Resize / scale to a target size (resampling).** New Qt-free, strictly typed
  image operations `resize_image`/`resized_size` in `image_ops.py` (no-op on
  equal size; aspect-ratio/megapixel-gate helper) plus `Project.resize` in
  `project_model.py`, which resamples **all layers** and the canvas size
  consistently (COLOR via the chosen method, HEIGHT losslessly via the height
  representation; the color composite stays aligned). The canvas wires this up
  undo-/redoable with a megapixel gate (clear, translated rejection on
  oversize, without allocating the oversized buffer); a new “Resize…” dialog
  (width/height in px, **link aspect ratio**, resampling method) is reachable via
  the “Edit” menu (Ctrl+R) and the Transform tab. The reserved physical size
  (`META_PHYSICAL_SIZE_MM`) stays untouched (mm/DPI is left to later ranks). All
  new strings in de/en parity (#359).
- **Height representation & 2D visualization (height-map foundation).** New
  Qt-free, strictly typed `bgremover/height_map.py` module: lossless conversion
  height ↔ grayscale array (`HeightField`, convention `R==G==B==height`,
  `A==coverage`), normalization of arbitrary values onto the height range and
  canvas-size validation – stored internally as `uint16` and thus
  16-bit-extensible (`max_value`). The canvas now displays an **active HEIGHT
  layer** in grayscale; the color composite stays unchanged (parity)
  (#345, #344).
- **Generate & import a height map (no AI).** `bgremover/height_map.py` gains
  `generate_from_image`: it **deterministically** builds a height map from a
  color image (channel weighting/luminance → tone curve → gamma → invert). The
  canvas wires this up undo-/redoable as a new active HEIGHT layer with role
  `HEIGHT_MAP`: `generate_height_map` from the active COLOR layer or the
  composite, and `import_height_map` loads a grayscale file validated through
  `open_validated_image` (format/file-size/megapixel guard, clear translated
  error message) and scales it to the canvas size (#346, #344).
- **Height-map editor (lighten/darken/set/invert).**
  `bgremover/height_map.py` gains selection-aware, lossless height operations
  (`adjust_height`, `set_height`, `invert_height`; clamped, input left
  untouched). The canvas wires them to the **active HEIGHT layer**
  (`lighten_/darken_/set_/invert_active_height`): they respect an existing
  selection (otherwise global), are undo-/redoable and deliberately do nothing
  on COLOR layers (no regression in color editing). Maximal reuse of the
  existing brush/selection/history paths (#347, #344).
- **Height-map optimization (`height_ops`).** New Qt-free, strictly typed,
  16-bit-capable `bgremover/height_ops.py` module with pure, deterministic
  operations on height fields: tone (`levels`/`gamma`), smoothing
  (`gaussian_blur` separable, `median_blur` edge-preserving – pure numpy, no new
  dependency), `threshold`, step reduction (`quantize`) and height-range clamp
  (`clamp_range`) – the same tone/grayscale primitives that later ranks share.
  The canvas adds a generic **live preview** for them
  (`preview_height_op`/`cancel_height_preview`, transient without model changes)
  and an undo-/redoable commit (`apply_height_op`) on the active HEIGHT layer
  (#348, #344).
- **Height-map workspace usable (UI) – epic completed.** New “Height” tab in the
  right-hand panel (`height_map_panel.py`): **generate** a height map from the
  image or **import** a grayscale, **edit** it with lighten/darken/set/invert, and
  **optimize** it via levels/gamma/smoothing (Gaussian, median)/threshold/steps/
  range with a live preview. Edit and optimize are **mode-contextual** – only
  active when the active layer is a HEIGHT layer or carries the `HEIGHT_MAP` role;
  color editing stays unchanged. The whole flow (generate → paint → optimize →
  invert → save/reload losslessly in `.bgrproj`) is now usable from the UI. All
  new strings via `i18n.py` (de/en parity); completes the height-map epic
  (#349, #344).
- **Qt-free project/layer data model.** New, strictly typed
  `bgremover/project_model.py` module with `Project` and `Layer` (`LayerKind`
  color/height/gloss/generic, project-wide unique roles) as the foundation of
  the layer epic: ordered layers, exactly one active layer, pure operations
  (add/remove/reorder/duplicate/rename, visibility/opacity/lock/roles) and an
  alpha composite of the visible color layers — without any Qt, render,
  persistence or history wiring (#330, #329).
- **Layer-aware, Qt-free undo/redo history.** New, strictly typed
  `bgremover/project_history.py` module (`ProjectHistory`) lifts undo/redo from a
  single image to the project model: it covers structural changes (add/remove/
  reorder/duplicate a layer, active layer, visibility/opacity/lock/role) and
  per-layer pixel changes. Memory strategy: lightweight structural snapshots plus
  a deduplicating pixel pool that counts unchanged layers only once across the
  shared undo/redo budget (the original and current state stay outside the
  budget); `descriptions()`/`undo_to()`/“restore original” are preserved. Not yet
  wired into the canvas (#331, #329; follows in #332).
- **`.bgrproj` project file format (lossless save/load).** New Qt-free modules
  `bgremover/project_io.py` and `bgremover/project_schema.py` write/read a complete
  multi-layer project as a ZIP container (`manifest.json` with format version,
  canvas size, ordered layer list incl. roles/metadata + one RGBA PNG per layer).
  Saving is atomic (`mkstemp`+`os.replace`), loading validates defensively (file
  size limit, per-layer megapixel cap, defense against zip-slip/unexpected entries,
  clear translated error messages). The schema is versioned with migration hooks:
  older versions migrate, newer ones are left untouched (warning only). Not yet
  wired into menus/dialogs (#333, #329; follows in #334/#335).
- **Layer panel and project menu.** The right-hand panel gains a new “Layers”
  tab: create layers, select (the active edit layer), toggle visibility, change
  opacity, reorder up/down, duplicate, delete, rename, and assign a role
  (color motif/height map/gloss) — all changes apply to the canvas composite
  (#332) and are undoable/redoable (#331). A new “Project” menu adds “New project”
  (`Ctrl+N`), “Open project…” (`Ctrl+Shift+O`), “Save project” (`Ctrl+Alt+S`) and
  “Save project as…” (`Ctrl+Alt+Shift+S`), wired to the `.bgrproj` format (#333);
  `Ctrl+O`/`Ctrl+S` stay reserved for the image workflows. Load/save errors are
  shown as clear, translated messages. All new strings go through `i18n.py`
  (de/en in parity) (#334, #329; image→project migration follows in #335).

### Changed

- **Image→project integration and “Recently opened” for projects.** “Open image”
  and drag & drop now create a single-layer project (validated loading via
  `image_loading` unchanged); “Recently opened” lists images **and** `.bgrproj`
  projects and opens each type correctly (dispatch by extension). The last-used
  project directory is remembered (additive settings key; no schema migration
  needed — the future-version protection is already tested). The single-image
  export still writes the composite (single-layer project bit-for-bit as before),
  and “restore original” returns the document in its loaded state. Closes the
  layer epic (#335, #329).
- **The editor is now layer-based (composite rendering + active layer).** The
  canvas holds a `Project` (#330) instead of a single image and displays/saves the
  **composite** of the visible layers (order/visibility/opacity); all tools (magic
  wand/selection, brush/eraser, lasso, AI cutout, replace background, flip, round
  corners) act on the **active layer**, and the selection mask refers to it.
  Size-changing geometry (rotate, crop) is applied uniformly to all layers to keep
  the model invariant. Undo/redo and “restore original” run through the
  layer-aware `ProjectHistory` (#331). A project with exactly one COLOR layer
  behaves bit-for-bit as before (parity, including RGB values preserved under
  transparent pixels on save); the AI cancel path stays free of
  `QThread.terminate()` regressions (#332, #329; the layer panel UI follows in #334).
- **GitHub release notes now come from the CHANGELOG.** The release workflow
  (`release-linux.yml`) derives the release body for a `vX.Y.Z` tag from the
  `## [X.Y.Z]` section of `CHANGELOG.md` and passes it via `--notes-file` to
  `gh release` — including when reusing an existing release (`gh release edit`),
  not just on first creation. The hardcoded “Automated build…” text is gone; if
  the matching section is missing, the publish job fails loudly (no silent
  fallback) (#311).
- **The weekly benchmark no longer reports environment artifacts as
  regressions.** Every result (`benchmarks/results/`) now carries an environment
  fingerprint (Python/Pillow/NumPy version, architecture, CPU count, runner); the
  comparison skips baselines that are not comparable (missing fingerprint,
  differing versions or benchmark parameters) and confirms a suspicious value in
  the same run across several repetitions (median) before opening an issue
  (#277, #278, #279).

### Fixed

- **Dark theme background colors aligned with the prototype.** Dark Mode
  background surfaces (`theme.DARK`: inspector panel, stepper bar, toolbar,
  navigation footer, status bar, controls and cards) now use the cool
  blue-gray tone of the approved prototype
  (`design/Prototyp A - Geführter Workflow.dc.html`) instead of a neutral
  near-black. `card_bg` is deliberately kept one step darker than the
  prototype value so `text3` on cards (and on inactive layer names in the
  layer panel) still meets the WCAG AA contrast contract of ≥ 4.5:1 (#441);
  `docs/REDESIGN_SPEC.md` §2 documents the new values and this one
  intentional deviation (#475).
- **Dark theme borders are soft overlays instead of hard gray tones.**
  `border` and `hairline` are now translucent white overlays like in the
  prototype (they settle differently depending on the surface underneath
  instead of looking equally hard everywhere); a new `border_2` token covers
  the secondary border tone of neutral secondary buttons (crop format, save
  format, etc., `panel_btn_style`). The menu bar now shares the `toolbar`
  tone with the toolbar instead of the status bar, matching the prototype
  where the menu bar and toolbar carry the same color (#476).
- **Dark theme accent blue aligned with the prototype.** `accent`/`accent2`
  (and the derived `accent_soft`/`accent_line`/`accent_shadow` surfaces) are
  now the prototype's brighter, periwinkle-ish blue instead of a duller tone
  — visible in the primary button gradient, the "Next" button, active tools,
  the active stepper circle, and the slider handle. `accent_text` already
  matched the prototype value exactly; `accent_shadow` remains a plain color
  value without a glow effect (Qt QSS has no `box-shadow`, #477).
- **Preview segmented control (step 6) now uses the correct prototype
  surface.** The "Color/Relief/Height/Gloss" container (`_ModeSegments`) was
  incorrectly backed by the `tabbar` tone; checking the prototype's actual
  CSS rules (not just the `:root` variables) showed the recessed `--inset`
  surface was the correct value — added as a new `inset` token and wired up.
  Two more tokens declared but unused in the prototype (`label`,
  `good_line`) were added to `Palette` for completeness, without a current
  consumer; a `bad_line` counterpart doesn't exist in the prototype and was
  therefore not invented (#479).
- **Canvas transparency checkerboard now follows the active theme.** The
  checkerboard pattern behind transparent image areas was hardcoded to
  light gray (`QColor(170,170,170)`/`(210,210,210)`) and looked like a
  bright patch in the middle of the canvas in Dark Mode. `checker_a`/
  `checker_b` fix this via the palette (dark: `#2c313a`/`#353b45`, light:
  `#dde2ea`/`#eef1f5`); `make_checker_brush` now takes the active palette,
  and `ImageCanvas.apply_palette` refreshes the pattern live when the theme
  is switched — no app restart needed (#478).
- **Fixed REDESIGN_SPEC.md color tables + added a drift regression test.**
  The docs claimed to be copied 1:1 from the prototype, but by their own
  provenance note had never actually been checked against the real color
  values — a line-by-line comparison uncovered documentation drift of its
  own, independent of `theme.py` (missing `checker_a`/`checker_b`, `inset`,
  `label`, `good_line`, `border_2`; the light scheme was only a prose
  excerpt instead of a table). §2/§3 are now complete tables that match
  `theme.DARK`/`theme.LIGHT` exactly; remaining light-scheme drift from the
  prototype that's deliberately out of scope for this epic is now spelled
  out instead of silently omitted. Two new tests in `tests/test_theme.py`
  guard this permanently: one compares the spec tables against the
  palettes, a second additionally checks `theme.DARK` directly against the
  CSS variables embedded in the prototype bundle — both fail the moment
  code and documentation drift apart again (#480, closes epic #474).
- **Live preview degrades to COLOR for size-mismatched data layers.** When a
  HEIGHT/GLOSS layer's pixel size (an anomalous or foreign project state) no longer
  matches the base, `_render_preview_uncached` now treats that layer like a missing
  role in **every** preview mode and falls back to the COLOR composite instead of
  showing a wrong-sized view or aborting the render path with an exception —
  mirroring the existing "missing/invisible role = degrade" rule. Render/pixel
  regression tests push a size-mismatched HEIGHT/GLOSS layer through
  `HEIGHT`/`RELIEF`/`GLOSS`/`COMBINED` and assert the COLOR result (#404).
- **Removed a dead geometry path in the EufyMake export.** The private
  `_derive_physical_size` helper — orphaned since the switch to the project-model
  getters (#377/#378) — and its sole-use `parse_size_mm` import are gone;
  `_derive_target` still derives physical size and DPI from
  `project.physical_size_mm`/`project.dpi`. No behavior change; the CLAUDE.md
  geometry description now points at the path actually used (#406).
- **Consistent canvas preview after the phase-1 completion.** Color and height
  live previews now pass through the selected mode pipeline as temporary layer
  contents, so mode, relief strength, and the gloss toggle update immediately
  without changing the model or export. Hidden height/gloss role layers are no
  longer rendered, and relief strength 0 skips the expensive hillshade entirely
  (#397, follow-up to #396).
- **Image export with an active height layer.** “Save Image” once again writes
  the COLOR composite regardless of the active editing layer. The grayscale
  HEIGHT view remains canvas-only and can no longer be silently exported as a
  normal image; bit-exact single-COLOR export, including RGB below transparent
  pixels, remains intact (#363).
- **Height-map median filter is memory-bounded.** `height_ops.median_blur` no
  longer materializes a full `(2r+1)² × H × W` window stack (which would have been
  ~33 GiB at 40 MP/radius 10); it now processes the image in **row bands** with a
  per-band stack hard-capped via `_MEDIAN_MAX_TEMP_BYTES`. The extra memory is
  therefore independent of the image size and no longer scales with the radius,
  while the result stays **bit-exact** (same edge handling, `coverage`,
  `max_value`, 16-bit). `gaussian_blur`, as a separable convolution, is already
  `O(H × W)` and radius-independent — evaluated in its docstring. Regression
  tests cover full-stack equivalence across all UI radii and the memory budget
  for the 40-MP case (#365).
- **Height context: model, UI and canvas follow one contract.** A layer is now
  height-capable *exactly when* `kind == LayerKind.HEIGHT`; the `HEIGHT_MAP` role
  may only sit on a HEIGHT layer. A new central, Qt-free rule
  (`role_allowed_for_kind`) is the single source of truth: model APIs (`Layer`,
  `assign_role`) reject `HEIGHT_MAP` on COLOR/GLOSS/GENERIC with
  `IncompatibleRoleError`, the layer panel offers the role only for HEIGHT
  layers, and the height-map tab enables its tools only for an active HEIGHT
  layer — so the UI no longer promises an operation the canvas then refuses.
  Loading a historically incompatible project losslessly drops only the invalid
  role (kind, name, pixels, order and metadata stay equal) and shows a
  translated warning (#364).

## [2.4.1] – 2026-06-17

### Fixed

- **macOS download app (`.dmg`) opened endless new windows after launch.**
  In the frozen bundle the AI inference starts its child process via
  multiprocessing "spawn", which relaunches the app binary itself; without
  `multiprocessing.freeze_support()` in the bundle entry point each child ran
  the GUI again → a fork bomb of 100+ windows that only a reboot stopped. The
  PyInstaller entry point now calls `freeze_support()` first, so the inference
  child boots correctly instead of opening the GUI.

- **macOS download app (`.dmg`) failed to launch.** The frozen bundle aborted
  right at `import bgremover` with `PackageNotFoundError` followed by
  `FileNotFoundError`, because PyInstaller did not include the package metadata
  and the bundle has no `pyproject.toml` fallback — the icon only flashed
  briefly, then nothing happened. The PyInstaller spec now bundles the
  `*.dist-info` metadata (`copy_metadata`), and version lookup can no longer
  abort startup (defensive fallback instead of an unhandled exception).

- **AI background removal in the `.dmg` failed to load.** The inference child
  process died on `import rembg` with `PackageNotFoundError` ("No package
  metadata was found for pymatting"): PyInstaller bundles the rembg
  dependencies' code but not their `*.dist-info` metadata, yet `pymatting` reads
  its own version at import. The spec now bundles the metadata of the whole
  rembg dependency chain (`copy_metadata(…, recursive=True)`).

## [2.4.0] – 2026-06-15

### Added

- **macOS app as a download (`.dmg`).** A self-contained `BgRemover.app`
  bundle (PyInstaller, Apple Silicon/arm64) is built as a `.dmg` and attached
  to the GitHub release — analogous to the Linux AppImage and without a local
  Python install. The bundle is **unsigned** for now: on first launch open it
  once via right-click → “Open”. Built via `packaging/mac/build_macos.sh`.
- **Download artifacts now include AI background removal.** The Linux AppImage
  and the macOS `.dmg` bundle `rembg`/`onnxruntime`, so the one-click AI works
  without any extra install (artifacts are correspondingly larger).
- **Release workflow builds cross-platform.** `release-linux.yml` now also
  produces a macOS arm64 `.dmg` alongside the Linux AppImage and `.deb`
  (x86_64 + aarch64/Raspberry Pi OS) for the `vX.Y.Z` tag and publishes all
  artifacts together.
- **Open images via file association and the command line.** `bgremover image.png`
  and `python -m bgremover image.png` open the path after the window is built,
  through the same validated, asynchronous load path as the file dialog, Recent
  Files and drag & drop; the Linux desktop entry (`%F`) and macOS
  `QFileOpenEvent`s (Finder “Open With”, double-click) are handled too. Multiple
  paths: the first is opened, the rest ignored with their count in the status
  bar; missing, unsupported or non-local paths are rejected in a controlled way
  instead of aborting startup, and the unsaved-changes prompt applies before
  replacing an edited image. Running worker threads are also shut down cleanly on
  app quit (#249).
- **Image-pipeline performance benchmark.** `scripts/benchmark.py` measures
  processing time per output format (PNG/JPEG/WebP/TIFF) through the real
  `image_ops` paths, stores dated results under `benchmarks/results/` and
  compares consecutive runs; formats that regress by more than 10% are flagged
  and optionally reported as GitHub issues (`make bench` / `make bench-compare`).
  A weekly CI workflow (`.github/workflows/benchmark.yml`) runs and compares on
  consistent hardware and commits the result back as the next baseline.
- **Behavioral tests hardened.** Behavioral test coverage for previously patchy
  paths was expanded (#177, #192).
- **Dedicated unit tests for `app.py` and `main_window.py`.** Coverage of
  `app.py` 0% → 100% and `main_window.py` 68% → 100%; overall coverage rose to
  94% (#214).

### Changed

- **Dependencies updated.** `idna` was raised to 3.15 and `urllib3` to 2.7.0;
  `LICENSES.md` is synchronized with the new dependency snapshot.
- **Build backend pinned against supply-chain CVEs.** `setuptools` is raised to
  `>=78.1.1` in `pyproject.toml` (`[build-system]`) and
  `requirements/constraints.txt` (CVE-2024-6345 RCE, CVE-2025-47273 path
  traversal), and `wheel` to `==0.46.2` in `constraints.txt` (CVE-2026-24049).
  The isolated wheel build can no longer pull vulnerable build tools (#200, #201).
- **pip raised to a patched release in CI/dev.** The pip-installing CI workflows
  (`ci.yml`, `pr-ci.yml`, `ui-nightly.yml`, `benchmark.yml`, `license-check.yml`)
  and the web SessionStart hook upgrade `pip` to `>=26.1.2` before installing, as
  do the dev install docs (`README.md`/`INSTALL_MAC.md`/`INSTALL_LINUX.md`).
  Closes the `pip-audit` batch of path-traversal, symlink and module-hijacking
  CVEs; pip is the installer itself and therefore cannot be pinned via
  `constraints.txt` (#202).
- **macOS diagnostics redact sensitive paths.** `diagnose_mac.sh` now replaces
  `$HOME` with `~` by default, shortens remaining `/Users/<name>` paths, and
  prints a filtered error summary with redacted paths instead of the raw last
  40 log lines — the output can safely be attached to bug reports. The new
  `--include-raw-logs` flag provides the full diagnostics (including the raw
  log); a shell test (`tests/test_diagnose_mac.py`) ensures the home directory
  and image paths never reach the default output (#185).
- **AppImage release dependencies pinned.** A `requirements/constraints.txt`
  snapshot fixes the versions for the AppImage build workflow (#182, #191).
- **License workflow permissions hardened.** The workflow now runs with minimal
  permissions (#183, #193).
- **`CanvasHistory._redo_max` removed.** The write-only attribute was never read;
  the redo limit is enforced solely via `deque(maxlen=…)` (#199, #215).
- **`import bgremover` no longer loads the Qt stack.** The package entry point
  (`bgremover/__init__.py`) now exports only lightweight metadata (`__version__`,
  `get_version`) directly; the established GUI/Qt re-exports (`ImageCanvas`,
  `MainWindow`, workers …) stay compatible but are loaded lazily via a PEP 562
  `__getattr__` on first attribute access. Version and metadata lookups now work
  headless without PyQt6; a subprocess regression test ensures a lightweight
  import pulls neither `bgremover.canvas`/`main_window` nor PyQt6 into
  `sys.modules` (#232).

### Fixed

- **rembg subprocess hardened (robustness & memory).** Four follow-up findings
  from the Codex review of #283 in `bgremover/ai_process.py`: after a transient
  `new_session()` failure the rembg session is rebuilt — exactly once — on the
  next request instead of falling back to `remove(..., session=None)` and
  reloading the model on every call (the #229 guarantee is preserved); the idle
  child process releases the last input PNG immediately instead of holding it;
  input and result PNGs travel as raw byte frames (`send_bytes`/`recv_bytes`)
  rather than pickled through the pipe, eliminating the memory peaks and OOM risk
  on large images (up to 40 MP); and a `request_stop()` arriving exactly during
  process startup is carried onto the fresh process via a
  `_proc_lock`/`_stop_pending` pair. Regression tests cover all four paths
  (#285).
- **Memory peaks in the capped file read mitigated.** Two follow-up findings from
  the Codex review of #264 in `bgremover/image_loading._read_capped`: instead of
  `b"".join(chunks)` (which held the chunks **and** the result at once, ~1 GiB
  near the 512 MiB limit), the content is assembled into a single pre-sized
  `bytearray` and passed through directly — no more ~2× peak. The first read is
  also bounded by the size known from `fstat()`, so a small file no longer
  requests ~8 MiB of headroom; a small follow-up read still detects growth
  between `fstat()` and reading (TOCTOU) or an unreliable `st_size`
  (pipes/sockets). The limit/overflow detection (`None`) is unchanged; regression
  tests cover both paths (#286).
- **Input file-size limit before reading.** `open_validated_image` now checks
  the input file via `os.fstat()` against a documented byte limit
  (`_MAX_INPUT_FILE_BYTES`, 512 MB) **before** its contents are fully read into
  memory; an additional bounded `read()` guards against unusual file objects and
  a size change between `fstat()` and `read()` (TOCTOU). The message
  distinguishes file size (MB) from the megapixel limit (MP). The synchronous
  and asynchronous load paths share the same check; the existing megapixel limit
  and TOCTOU protection are preserved (#230).
- **rembg inference session is reused.** The warmup now creates exactly one
  rembg/ONNX session via `new_session()` and stores it module-wide; every later
  `AIWorker` passes it to `remove(..., session=...)` instead of re-initializing
  the model. Creation is thread-safe via double-checked locking and runs at most
  once across multiple AI calls; a failed init still reports the worker error and
  leaves no falsely "ready" state behind. The misleading comment (claiming a
  dummy `remove()` caches the session) is corrected too (#229).
- **`recent_files` is robust against corrupt settings.** `RecentFiles.paths()`
  now handles every stored raw type defensively: a single string stays one
  entry, lists/tuples are filtered element-wise to non-empty strings, and any
  other value (e.g. integer, `None`) yields an empty list instead of a
  `TypeError`. The new `sanitize()` writes a genuinely corrupt value back once
  at startup in cleaned form (with a log warning); the harmless QSettings
  single-element string is left untouched. A hand-edited or outdated
  `recent_files` value therefore no longer aborts the menu or app build; a newer (future) schema is also left
  untouched to avoid downgrade data loss (#233, #240).
- **Double-checked lock for the rembg lazy import and TOCTOU protection in
  `open_validated_image`.** Two threads could enter the import simultaneously
  (race), and the file was opened twice (TOCTOU window); both are covered by
  regression tests (#174).
- **Stale asynchronous image-load results are discarded.** A monotonic
  `_load_generation` counter in `MainWindow` prevents a late load callback from
  overwriting a newer image (analogous to the AI stale check) (#190).
- **Canvas selection mask typing fixed.** An incorrect type caused a mypy error
  in the full CI run (#196, #197).
- **CI workflow YAML repaired.** The unquoted name of the pip upgrade step broke
  workflow parsing (#213).
- **Active crop no longer survives an image-state change.** Every visible image
  change (rotate, flip, AI result, undo/redo, restore-original, crop confirm) now
  discards an active crop overlay and a pending lasso centrally in
  `_set_image_state` and emits `cropModeChanged(False)` exactly once. A stale crop
  rectangle can therefore no longer be applied to the new image and can no longer
  produce transparent padding pixels (#247).
- **Release workflow only publishes after a green Full-CI gate.**
  `release-linux.yml` now calls the authoritative Full-CI matrix (`ci.yml`) as a
  reusable workflow and binds build and publish to it via `needs`; a separate
  `verify-tag` job fails when the tag does not match `vX.Y.Z` or diverges from
  `project.version`. AppImage/`.deb` are checked for name, architecture,
  executability and Debian metadata before upload, and `gh release create` errors
  are no longer swallowed with `|| true` (an existing release is reused
  explicitly). No artifacts from a commit with red tests or a mismatched version
  reach a release anymore (#250).
- **Empty selection frees the overlay pixmap immediately.** `_refresh_overlay`
  now checks the mask's empty state **before** the incremental dirty path. When
  the eraser removes the last selected pixel, `_overlay_pixmap` and the
  `QGraphicsPixmapItem` are cleared right away instead of holding a transparent
  full-image QPixmap (~160 MiB at 40 MP) until the next full rebuild. Partial
  erasing still updates only the dirty rectangle (#251).
- **Release-workflow follow-ups hardened.** The publish job now sets `GH_REPO`
  so `gh release` targets the right repository without a checkout; the reusable
  test job depends on `verify-tag`, so an invalid or version-mismatched tag no
  longer starts the matrix at all; and `download-artifact` fetches the artifacts
  via `run-id`/`github-token` (with `actions: read`) from the whole run, so
  "Re-run failed jobs" no longer loses artifacts from an earlier attempt.
  README/RESOURCES (incl. translations) no longer describe the removed
  `release: published` trigger (#257).
- **Image-load limit without 512 MiB pre-allocation and localized.**
  `open_validated_image` now reads the file content in 8 MiB chunks (instead of
  `read(limit + 1)`, which on CPython's buffered reader immediately reserves
  ~512 MiB and can make a small file fail with `MemoryError` under tight memory);
  growth between `fstat()` and reading is still detected via `limit + 1`. The
  size message goes through the `status.file_too_large` translation key (fully
  localized de/en instead of a mixed message) and rounds the actual value up and
  the limit down, so it is visibly larger at "limit + 1 byte" (e.g. "513 MB" at a
  maximum of "512 MB", instead of both showing "512 MB" with `.0f`) (#258).
- **QSettings schema migration is downgrade-safe.** A missing migration no longer
  bumps `schema_version` to the current value unchecked, and a future, higher
  schema is no longer written back while building the recent-files menu — an
  accidental downgrade therefore loses no settings (#234, #259).
- **Escape cancels an in-progress lasso first; tool cursor restored after crop.**
  An in-progress polygon lasso is now cancelled by Escape before the selection is
  cleared (order crop > lasso > selection). When an active crop is auto-discarded,
  `_finish_mode` restores the active tool's cursor instead of keeping the crop
  cursor (#248, #260).
- **Worker shutdown is time-bounded.** On app close the `WorkerController` now
  waits only briefly on `quit()`/`wait()` before falling back to `terminate()`
  with another bounded `wait()`; an unresponsive worker no longer blocks the close
  indefinitely, and the error path is logged. The actual `terminate()` risk for
  native ONNX work was then resolved by moving the rembg/ONNX inference into its
  own `spawn`-started process (`ai_process`): the AI worker only polls for the
  result and is cooperatively stoppable, cancel and app close terminate the
  inference process hard, and `terminate()` is no longer the emergency exit for
  AI work (#270, follow-up from #231).
- **Brush overlay avoids a full mask scan per mouse move.** `canvas_selection`
  keeps the selection counter incrementally and uses the bounding box of the
  change instead of scanning the whole mask on every brush/eraser move;
  `has_selection` is therefore O(1). This keeps large images smooth while drawing
  quickly (#261).

### Removed

- **Dead code removed (#244).** The never-called `ImageCanvas._zoom` method and
  the production-unused `WorkerController.launch_worker` wrapper were removed;
  the thread-lifecycle tests now exercise the actually-used `_build_thread` path.

## [2.3.0] – 2026-06-04


### Added

- **Test coverage increased to 88% (second round, previously 82%).** New file
  `tests/test_canvas_events.py` covers previously untested event handlers and
  `canvas.py` control logic: mouse, keyboard, wheel and drag handlers (via
  synthetic Qt events, intentionally without the `ui` marker so they count
  toward CI coverage), magic-wand result flows (hit, stale revision,
  inactive), tool settings, undo/redo/undo-to during active crop, and guard
  paths without a loaded image. This raises `canvas.py` from 64% to 99%; the
  coverage threshold `fail_under` was raised from 80 to 86.
- **Test coverage increased to 82% (previously 74%).** New behavior-based tests
  cover logic modules that had only thin coverage so far: `tests/test_lasso.py`
  (polygon-lasso state, preview line, double-click duplicate, polygon→mask),
  `tests/test_canvas_crop.py` (crop gestures press/move/release, guards without
  loaded image), and `tests/test_viewport.py` (zoom limits, pan routing,
  scrollbar movement). `tests/test_crop_overlay.py` now covers resizing from all
  four corners, `inside`/properties and the `paint` path (offscreen);
  `tests/test_settings_schema.py` covers the migration-step path and
  `tests/test_settings_dialog.py` covers directory/log-folder selection. As a
  result, `crop.py`, `canvas_lasso.py`, `canvas_viewport.py`,
  `settings_schema.py` and `settings_dialog.py` are at 100%, and
  `canvas_crop.py` is at 98%. The coverage threshold `fail_under` was raised
  from 68 to 80.
- **ANLEITUNG.md i18n.** Added five translations of the German user guide:
  `docs/i18n/{en,es,fr,uk,zh}/ANLEITUNG.md`. The `DOC_NAMES` tuple in
  `tests/test_i18n_docs.py` now includes `"ANLEITUNG.md"`, so the structural
  synchronization check automatically covers all five copies. A note in each
  i18n header explains that `ANLEITUNG.pdf` is generated only for the German
  original.
- **Soft-drift test `tests/test_i18n_sync.py`.** Compares heading hierarchy and
  number of code blocks in `CHANGELOG.md`, `INSTALL_MAC.md` and
  `INSTALL_LINUX.md` against the German originals. Differences produce readable
  warnings instead of hard test failures, keeping CI green while making drift
  visible.
- **`bgremover/status_messages.py` – centralized status messages.** All
  user-visible status strings from `canvas.py`, `canvas_crop.py` and
  `main_window.py` were moved into the new `StatusMessages` class. This is not
  an i18n framework yet, just a central collection point preparing future
  localization.
- **Runtime i18n with English support.** German and English can be switched at
  runtime; the Settings dialog includes a persistent language selector with a
  restart hint, and UI strings in the canvas, dialogs and right panel use the
  central translation layer.
- **Tool keyboard shortcuts.** Editing tools can now be switched from the
  keyboard; toolbar tooltips and documentation list the platform-appropriate
  shortcuts.
- **Linux AppImage packaging.** The release build now produces an AppImage as
  the recommended Linux end-user path, with packaging scripts, CI coverage and
  installation notes.
- **Linux `.deb`, aarch64/Raspberry Pi and release workflow.** Linux packaging
  was extended with Debian packages, aarch64/Pi support and the associated
  release workflow.
- **Introduced QSettings schema version.** New helper
  `bgremover/settings_schema.py` with `SCHEMA_VERSION = 1` and
  `migrate(settings)`; `MainWindow.__init__` runs the migration directly after
  constructing `QSettings`. Currently only initialization is active; future
  format changes (for example the layout of the `recent_files` list) can hook
  into this central place without old saved values crashing startup. Future
  versions are not written back (downgrade protection) and only logged; a
  non-numeric `schema_version` value is treated as "unset". Tests in
  `tests/test_settings_schema.py` cover initialization, pre-schema upgrade
  without data loss, idempotence, future-version warning and corrupt values.
- **Runtime test for `RembgWarmupWorker`.** Two new tests in
  `tests/test_workers.py` verify the always-emit-`finished` contract (success
  and failure of warmup) with patched `rembg_remove`. A new controller test in
  `tests/test_worker_controller.py` additionally verifies that
  `WorkerController` completes the thread lifecycle (worker released,
  `warmup_done` set, `on_finished` called) even when `rembg_remove` raises on
  first start; otherwise bootstrap would hang if the ONNX model cannot be
  loaded offline.

### Changed

- Documentation and code comments were cleaned up: stale PR/round markers were
  removed from living docs, macOS install notes were updated, and the
  recommendation docs were reduced to the current review/roadmap state.
- The project version was raised to 2.3.0 in package metadata, AppStream
  metadata, license overviews, and changelog links.

- **Docstring language unified.** `bgremover/image_ops.py`,
  `bgremover/recent_files.py` and `bgremover/worker_controller.py` had English
  module and method docstrings; all three now use German, consistent with the
  rest of the project.
- **User documentation for Linux packages and the language setting updated.**
  README, `INSTALL_LINUX.md` and `ANLEITUNG.md` now list AppImage/`.deb` as the
  recommended Linux end-user path and document the persistent language setting
  including the restart hint; the i18n copies are synchronized accordingly.
- **Code-hygiene collection round (small independent cleanups).**
  - `bgremover/__init__.py` + new `bgremover/_version.py`: the source-run
    fallback for `__version__` now reads `pyproject.toml` directly (`tomllib`
    from Py3.11, regex on Py3.10) instead of a hard-coded version literal;
    pyproject.toml is therefore the single source of truth and a version bump
    can no longer forget the fallback. `tests/test_version.py` validates the new
    behavior.
  - `bgremover/canvas.py`: `_paint_brush(cx, cy)` no longer reads
    `self._tool` internally; the caller passes the `additive` flag explicitly
    (keyword-only), and tests were adjusted accordingly.
  - `bgremover/canvas.py`: `apply_remove`/`apply_replace` now catch only
    `OSError`/`ValueError`/`PIL.UnidentifiedImageError` instead of `Exception`;
    real bugs (AttributeError, IndexError, …) propagate visibly again instead
    of being swallowed as status messages.
  - `bgremover/constants.py`: the `init_runtime` docstring explicitly names the
    process-wide side effect on `Image.MAX_IMAGE_PIXELS`; a comment next to the
    central `logger` object also documents the recommendation to use
    `logging.getLogger(__name__)` in new submodule code.
  - `bgremover/recent_files.py`: a comment explains the QSettings special case
    where a one-element list comes back as a raw string.
  - `Makefile`: `make clean` now also removes `*.egg-info/`, `build/` and
    `dist/` (leftovers from `pip install -e .`).
  - `pyproject.toml`: `description` reflects the documented Linux support
    ("macOS and Linux") instead of only macOS.
- **Magic-wand selection no longer freezes the UI.** The flood fill for
  magic-wand selection previously ran synchronously in the UI thread; with
  40-MP images containing large solid-color areas the click became noticeably
  laggy. The computation now runs in the new `FloodFillWorker` on a short-lived
  `QThread` (analogous to `ImageLoadWorker`); the result returns via a
  `finished` signal and is discarded via a stale check on `content_revision` if
  the user has changed or edited the image in the meantime. Panning/zooming
  stays responsive during calculation; only a parallel wand click is blocked
  with a status message.
- **CI test matrix expanded.** The Full CI workflow now checks Python 3.10,
  3.11, 3.12 and 3.13 on Ubuntu and macOS.
- **`RembgWarmupWorker` now inherits from `_Worker`.** The warmup worker used to
  be the only worker with its own `try/except/finally` boilerplate outside the
  shared base. `_Worker.run` now has an `_always_finished()` hook in the
  `finally` branch (default no-op), which `RembgWarmupWorker` overrides so its
  parameterless `finished` signal still fires on both success and failure – the
  `WorkerController` needs this to finish the thread lifecycle. Logging/error
  semantics are now consistent (`_error_context = "rembg warmup"`), and
  `WorkerController` type annotations were unified (`_Worker | RembgWarmupWorker`
  → `_Worker`).
- **Canvas submodules use the public edit API.** `CanvasCrop` and
  `CanvasTransform` previously called `ImageCanvas._apply_pil(...)` directly
  even though `ImageCanvas` exposes the public entry point
  `apply_edit(img, desc=...)`; similarly, `CanvasCrop.cancel` accessed the
  private `_tool`. Both submodules now use `apply_edit(...)` or the new read-only
  property `ImageCanvas.current_tool`. `_apply_pil` remains internal for
  `apply_loaded_image`/`apply_edit`/undo/AI paths. In addition,
  `clear_selection`, `invert_selection`, `expand_selection` and
  `shrink_selection` now use the existing `_requires_image` decorator instead
  of four different inline guards; `clear_selection` now reports "No image
  loaded" consistently in the empty state instead of staying silent.
- **Public package API slimmed down (small breaking change for external
  consumers).** Private vocabulary is no longer re-exported from the
  `bgremover` top level: `_MAX_MEGAPIXELS`, `_THREAD_SHUTDOWN_MS`,
  `_UNDO_MEMORY_LIMIT`, `_Theme`, `_setup_logging` and `_resolve_log_dir` were
  removed from `bgremover/__init__.py` (import block and `__all__`). Code that
  needs these symbols should import directly from the submodules
  (`bgremover.constants`, `bgremover.theme`, `bgremover.logging_config`).
  `logger`, `LOG_FILENAME`, `REMBG_AVAILABLE` and `current_log_file` remain
  legitimate public API. The test-only edge `MainWindow._recent_paths()` also
  disappears; the three tests in `tests/test_recent_files.py` now access
  `w._recent_files.paths()` directly.

### Fixed

- **`apply_remove`/`apply_replace` no longer swallow real bugs.** The previous
  `except Exception` swallowed `AttributeError` and `AssertionError` among
  others – exactly the class of errors that should stay visible as bugs. The
  new narrow filter (`OSError`, `ValueError`, `PIL.UnidentifiedImageError`)
  lets those bugs propagate again while still catching expected image/I/O
  errors as status messages.
- **Synchronous loading path uses the same safeguards as the worker.**
  `ImageCanvas.load_image` (drag & drop, tests) previously bypassed structural
  `verify()`, the format whitelist (`_ALLOWED_IMAGE_FORMATS`) and the clean
  decode-error path already provided by `ImageLoadWorker` after the
  format/structure hardening – only the megapixel check was shared. Both paths
  now call the new helper `bgremover.image_loading.open_validated_image`, so
  manipulated files and unsupported formats also end via status message on
  drag & drop instead of unhandled PIL exceptions.
- **License check stabilized.** `coverage` is now pinned in
  `requirements/constraints.txt` (`==7.14.0`) so a new upstream `coverage`
  release no longer turns the `LICENSES.md` drift comparison red.
- **License check hardened against timezone drift.** The `gen_date` from
  `git log -1 --format=%cs -- LICENSES.md` otherwise formats the date in the
  committer timezone of the affected commit; a merge commit with a `+02:00`
  offset (web-flow + CEST region) shifted the date by one position when the UTC
  time was just before midnight (example: `2026-05-26T23:10:10Z` ≡
  `2026-05-27T01:10:10+02:00` → `%cs` = `2026-05-27`). The date of the merge
  commit also became relevant because `actions/checkout@v5` checks out the
  synthetic `refs/pull/N/merge` commit shallowly for `pull_request` events by
  default – without the parent, `git log -- LICENSES.md` compares nothing and
  the merge commit appears as the "last change". Fix: `fetch-depth: 0` in
  `actions/checkout` plus `TZ=UTC` and `--date=short-local` for the `git log`
  call, so the real edit commit is found and the date is formatted
  deterministically in UTC.

### Removed

- **Removed dead code from Canvas, Lasso and MainWindow.** The unused shadow
  counter `ImageCanvas._version`, the no-longer referenced method
  `CanvasLasso.close_to_mask`, and the unused toolbar button-group reference
  `MainWindow._btn_grp` were removed without replacement.

## [2.2.0] – 2026-05-25

### Added

- **Reproducible dependency snapshot** (`requirements/constraints.txt`).
  The Makefile, license workflow, and macOS app build use the same
  committed constraint set for test, CI, license, and app-bundle installs.
- **Local test-environment doctor** (`make doctor`,
  `scripts/check_test_env.py`). Checks the Python version, `[test]`
  dependencies, non-editable package installation, the `bgremover`
  console script, and Qt `offscreen` before a local run fails deep in
  pytest.
- **CI smoke test for application start** (`tests/test_app_smoke.py`).
  The existing UI tests are excluded from CI via `-m 'not ui'`, so CI
  never checked whether the application starts up at all – exactly the
  gap that let the macOS start failures slip through. New, without the
  `ui` marker (so it runs in CI): `python -m bgremover` and the
  `bgremover` console script are fully started from a neutral working
  directory (new self-test hook `BGREMOVER_SMOKE_TEST` quits after the
  first event-loop tick with exit code 0); the Qt plugin setup is
  checked to yield a valid plugin path; the starter scripts
  (`create_BgRemover_app.sh`, `BgRemover.command`, `diagnose_mac.sh`)
  and the launcher baked into the app bundle are shell-syntax checked.
  `zsh` is installed in the Linux CI job for this.

### Changed

- **MainWindow modularized further.** Persistence and menu semantics for
  "Open Recent" now live in `bgremover/recent_files.py`; `MainWindow`
  only delegates loading, status messages, and File-menu integration.
- **Menu/action construction extracted from `MainWindow`.**
  `bgremover/menu_actions.py` builds the menu bar, `QAction`s, shortcuts,
  and Recent-Files submenu; `MainWindow` only passes domain callbacks.
- **Right-side tab panel extracted from `MainWindow`.**
  `bgremover/right_panel.py` builds the Selection, Background, Transform,
  and Shape tabs including sliders, spin boxes, and panel buttons;
  `MainWindow` only passes canvas callbacks.
- **Worker orchestration encapsulated out of `MainWindow`.**
  `bgremover/worker_controller.py` now owns load, AI, and warmup threads,
  including strong worker references, `deleteLater` wiring, and shared
  shutdown.

### Fixed

- **Release/changelog links corrected to real refs.** `[Unreleased]`
  now compares from `v2.1.0`; `[2.1.0]` uses the documented 2.0.0
  release commit as its base because the repository has no historical
  `v2.0.0` tag.
- **App bundle: `bgremover` detection in setup independent of the
  working directory.** `create_BgRemover_app.sh` treated the venv as
  “ready” even though `bgremover` was not installed there: the
  `has_deps` check ran with `cwd` inside the project folder, and
  Python automatically prepends the current directory to
  `sys.path[0]` – so `import bgremover` found the repo's `bgremover/`
  **source directory** instead of a real venv installation. The app
  launcher starts with a different `cwd`, does not see the source
  directory, and therefore reported “The bgremover package is missing
  in the venv”. `has_deps` and the final sanity check now run from
  `$HOME` (subshell `cd "$HOME"`), so they check the same reality as
  the launcher; if the package is missing, the pip-install fast path
  kicks in. `diagnose_mac.sh` also tests from `$HOME` and additionally
  shows `pip show bgremover` of the app venv (cwd-independent proof of
  whether/where the package is installed).
- **macOS launch paths working again.** After the package cut (round
  5), `BgRemover.command` was still looking for the no-longer-existing
  `BgRemover.py` and bailed out with “not found”; the German
  `INSTALL_MAC.md` plus the i18n versions of `INSTALL_LINUX.md` and
  `README.md` also kept some old commands (round-5 step 15 had missed
  the German `INSTALL_MAC.md` and the i18n install docs in the glob,
  plus `Exec=python3 /PATH/.../BgRemover.py` in the i18n `.desktop`
  snippets). Net effect: on macOS none of the three documented launch
  paths (app bundle, double-click `.command`, terminal) was reliably
  usable. `BgRemover.command` now starts via `python3 -m bgremover`
  and pre-checks `import bgremover` (otherwise prints a clear hint to
  `create_BgRemover_app.sh`). INSTALL_MAC + all i18n docs reflect the
  current package model (incl. non-editable install of the package
  into the app venv and `importlib.resources` asset lookup).
- **`create_BgRemover_app.sh`: existing venv migrated cleanly.** A
  venv from the monolith era (PyQt6/Pillow/numpy installed, but of
  course not yet `bgremover`) was wrongly treated as “ready” because
  the setup check `has_deps` did not test `bgremover`. On re-run, the
  package install was therefore skipped — and the app launcher then
  reported at runtime “The bgremover package is missing in the venv”.
  The check now also includes `import bgremover`; additionally there
  is a fast path: if the app venv already has PyQt6/Pillow/numpy,
  only `pip install ".[ai]"` is added (seconds) instead of rebuilding
  the venv with all dependencies (minutes).

### Changed

- **Pure image operations extracted from `ImageCanvas`.**
  `bgremover/image_ops.py` now owns background remove/replace, saving,
  rotation, flipping, rounded corners, and crop masking as Qt-free
  PIL/NumPy functions. `ImageCanvas` keeps UI state, undo/redo, signals,
  and overlays; `tests/test_image_ops.py` checks the pixel operations
  directly without a `QApplication`.
- **Recommendations documentation brought up to current status.**
  `RECOMMENDATIONS.md` and the i18n versions now include a round-6
  status block for the latest PR series (#70, #72–#78) and explicitly
  mark the old monolith findings as historical context.
  `tests/test_recommendations_docs.py` guards this block.
- **Resource documentation synchronized.** `RESOURCES.md` and the i18n
  versions now reflect the package layout (`bgremover/` instead of
  `BgRemover.py`), package data under `bgremover/icons/`, the
  reproducible constraints snapshot, and PR/full/license workflows. A
  static test guards those references against becoming stale again.
- **`make pr-check` makes the local PR check more robust.** The target
  refreshes the `[test]` package installation, runs the doctor, and then
  starts `ruff`, `mypy`, and `pytest`. The Makefile finds
  `.venv/bin/python` automatically and otherwise falls back to
  `python`/`python3`; GitHub PR CI and Full CI use the same target. The
  shared Qt plugin setup stages platform plugins into the system temp
  directory when needed so local macOS headless runs do not fail on Qt
  plugin listing issues inside the project path.
- **Lightweight PR CI added and testing docs synchronized.** Pull
  requests now get a cheap Ubuntu/Python 3.12 workflow with
  `make pr-check`; the full Linux/macOS matrix remains reserved for
  release and manual runs. The test workflows install the package
  non-editably so the app smoke tests check the installed reality from
  a foreign `cwd`. `README`, i18n READMEs, `TESTING.md`, and `Makefile`
  now describe the same workflow.
- **Monolith → package (round 5).** The single-file `BgRemover.py`
  (3026 lines) has been split into the installable package `bgremover/`
  (14 modules: `constants`, `image_utils`, `icons`, `theme`, `workers`,
  `crop`, `canvas`, `widgets`, `settings_dialog`, `logging_config`,
  `main_window`, `app`, `__main__`, `__init__`). Launched via
  `python -m bgremover` or the `bgremover` console script; the old
  `python BgRemover.py` form is removed without replacement.
  `BgRemover.py` is deleted. Performed in **13 mechanical steps**,
  each gated on the green test oracle (140 unit + 16 UI tests, ruff,
  mypy). The single intentional, behaviour-neutral code change:
  `make_tool_icon` now resolves icons via `importlib.resources` from
  package data (`bgremover/icons/`) instead of `__file__`/`sys.argv`/
  `cwd` – contract unchanged. `pyproject.toml`, `Makefile`, CI workflow
  and the macOS build script (`create_BgRemover_app.sh`) followed in
  the same cut; the venv installs the package non-editably (incl.
  package-data), making the app independent of the project folder.
- Transitional re-exports in `BgRemover.py` (phase B) and all
  `BgRemover` test imports were switched to the package in the final
  step.

## [2.1.0] – 2026-05-19

### Changed

- Consolidated the "no image loaded" early-return guard of the five
  `ImageCanvas` methods (`apply_round_corners`, `apply_rotate`,
  `apply_flip`, `start_crop_circle`, `start_crop_ratio`) into the
  `@_requires_image` decorator – the previously byte-identical block is
  gone; behavior unchanged (defended by the existing test suite).
- Background workers `AIWorker` and `ImageLoadWorker` now share the
  common base class `_Worker`, which encapsulates the identical
  `try/except → logger.exception → error.emit` flow; subclasses only
  implement `_work()`. `RembgWarmupWorker` intentionally stays
  standalone (no `error` signal, `finished` always in `finally`).
- Version cut **2.1.0**: `pyproject.toml` and the `__version__`
  fallback in `BgRemover.py` bumped to `2.1.0`; the changes previously
  collected under `[Unreleased]` (#48/#52/#53, INSTALL_LINUX, rounds
  3/4) are hereby dated as 2.1.0.

### Removed

- Removed dead stylesheet constants `BTN_STYLE` and `GRP_STYLE`.

### Fixed

- `save_image()` now reports I/O failures as a status message instead
  of propagating them unhandled.

### Documentation

- Added an installation guide for Linux (`INSTALL_LINUX.md`):
  system packages per distribution (apt/dnf/pacman), venv setup,
  starter script or `.desktop` entry, and troubleshooting; linked from
  the README. Including a particularly simple path for Raspberry Pi OS
  (Desktop) without venv/pip (PyQt6/Pillow/numpy as system packages via
  `apt`), with an optional AI add-on step.

## [2.0.0] – 2026-05-17

First documented 2.0.0 release state. The repository has no historical
`v2.0.0` Git tag.

### Features

- AI background removal via `rembg` (optional `ai` extra) including a
  background warmup so that the first click does not block.
- Selection tools: magic wand (vectorized flood fill with a tolerance
  slider), brush, eraser, and polygon lasso; Shift/Ctrl for additive
  or subtractive selection.
- Make the background transparent or replace it with a color.
- Transformations: rotate (90° steps and free angle), flip,
  round corners, crop in several formats with a rule-of-thirds grid.
- History with undo/redo (toolbar buttons) and jumping to any earlier
  step via a floating history popup.
- Drag & drop as well as "Open Recent" (10 entries), both via the
  asynchronous loading worker – no UI freeze.
- Save as PNG, JPEG, WebP, or TIFF.
- Persistent settings (default directories, preferred file format)
  via `QSettings`.
- macOS app bundle build (`create_BgRemover_app.sh`) including an
  isolated venv, Apple Silicon handling, and icon assignment; supports
  Python 3.10–3.15.

### Stability & quality

- Worker threads hardened (no premature GC of the worker,
  clean thread shutdown in `closeEvent`, AI race handled via a monotonic
  canvas version counter).
- Image-size limit (40 MP) and decompression-bomb protection on load.
- Memory-limited undo stack (256 MB) with O(1) byte tracking.
- Platform-independent log path (`bgremover.log` in the app data directory).
- 108 tests; `ruff` and `mypy` as CI steps; CI on Ubuntu and macOS
  under Python 3.10 and 3.12.
- `__version__` is read from the package metadata (single source);
  the version appears in the window title.

### Documentation & license

- License **GPL-3.0-or-later** (`LICENSE`); required by the
  GPL-licensed PyQt6 binding.
- `RESOURCES.md` (all libraries/tools/assets along with their licenses),
  `LICENSES.md`, and an automated license/compliance workflow.
- README with architecture, known limitations, and installation
  instructions; detailed `INSTALL_MAC.md`.

[Unreleased]: https://github.com/NikolayDA/picture_helper/compare/v2.4.1...HEAD
[2.4.1]: https://github.com/NikolayDA/picture_helper/compare/v2.4.0...v2.4.1
[2.4.0]: https://github.com/NikolayDA/picture_helper/compare/64c1f4c87af2a41e82122b361855f0021ec62cf3...v2.4.0
[2.3.0]: https://github.com/NikolayDA/picture_helper/compare/79f61c5514f283fae31ce9d21f31786a3acfbe16...64c1f4c87af2a41e82122b361855f0021ec62cf3
[2.2.0]: https://github.com/NikolayDA/picture_helper/compare/666d4a3932f70eabaafde8de4bfc2a0574be5d16...79f61c5514f283fae31ce9d21f31786a3acfbe16
[2.1.0]: https://github.com/NikolayDA/picture_helper/compare/d80067dbc064a8eab5774457eaaffab733c4cab6...666d4a3932f70eabaafde8de4bfc2a0574be5d16
[2.0.0]: https://github.com/NikolayDA/picture_helper/tree/d80067dbc064a8eab5774457eaaffab733c4cab6
