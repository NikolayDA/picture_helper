[Deutsch](../../../ANLEITUNG.md) · **English** · [Español](../es/ANLEITUNG.md) · [Français](../fr/ANLEITUNG.md) · [Українська](../uk/ANLEITUNG.md) · [简体中文](../zh/ANLEITUNG.md)

> **Note:** A PDF version of this guide is only generated for the German original
> (`ANLEITUNG.pdf`). No PDF is produced for this translation.

# BgRemover – User Guide

This guide describes, step by step, how to use **BgRemover** — from opening
the first image to saving the finished result. It is aimed at users with no
prior image-editing experience.

> Notes on **installation** are intentionally not included here, but in
> [INSTALL_MAC.md](INSTALL_MAC.md) (macOS) and
> [INSTALL_LINUX.md](INSTALL_LINUX.md) (Linux). This guide assumes the
> application can already be launched.

---

## Table of Contents

1. [What can BgRemover do?](#1-what-can-bgremover-do)
2. [The application window at a glance](#2-the-application-window-at-a-glance)
3. [Quick start in 5 steps](#3-quick-start-in-5-steps)
4. [Step 1 – Open an image](#4-step-1--open-an-image)
5. [The toolbar (left)](#5-the-toolbar-left)
6. [Making a selection](#6-making-a-selection)
7. [Step 2 – Cut out](#7-step-2--cut-out)
8. [Step 3 – Adjust (colour correction)](#8-step-3--adjust-colour-correction)
9. [Step 4 – Shape & Size](#9-step-4--shape--size)
10. [Resize & physical dimensions](#10-resize--physical-dimensions)
11. [Step 5 – Relief & Layers](#11-step-5--relief--layers)
12. [Step 6 – Export](#12-step-6--export)
13. [Settings](#13-settings)
14. [Keyboard shortcuts](#14-keyboard-shortcuts)
15. [Typical workflows](#15-typical-workflows)
16. [Tips & tricks](#16-tips--tricks)
17. [Known limitations](#17-known-limitations)
18. [Troubleshooting & log file](#18-troubleshooting--log-file)
19. [License](#19-license)

---

## 1. What can BgRemover do?

BgRemover is an image-editing tool for **removing, replacing, and editing
backgrounds** — with additional features for simple image optimisation,
layers/projects, and preparing UV-print assets. A **guided 6-step workflow**
(Open → Cut out → Adjust → Shape & Size → Relief & Layers → Export) walks you
through the editing process. The key features:

- **AI background removal** – remove the background automatically with a
  single click.
- **Manual selection** with magic wand, brush, eraser, and polygon lasso.
- **Replace background** – make the selection transparent or fill it with any
  colour.
- **Transform** – rotate (in 90° steps or a free angle) and flip.
- **Shape & crop** – round corners, crop to circle or a fixed aspect ratio.
- **Image optimisation** – adjust brightness, contrast, and saturation, and
  soften the alpha edge (feather).
- **Size & physical dimensions** – change the pixel size or set a print size
  via millimetres and DPI (with a print-area hint).
- **Layers & projects** – manage several layers (colour/height/gloss/generic)
  and save and open the whole thing as a `.bgrproj` project.
- **Height maps** – generate a height map from an image, edit it with sliders
  or directly with the brush, and optimise it.
- **2D preview** – check colour, relief, height, and gloss on screen.
- **EufyMake Studio export** – generate import assets for UV printing.
- **History** with undo/redo and jump to any earlier editing step.
- **Save** as PNG, JPEG, WebP, or TIFF.

---

## 2. The application window at a glance

![BgRemover – main window after launch](../../../app_screenshots/bgremover_complete_20260711_094027/01_main_empty.png)

*The main window right after launch: the menu bar at the top, the toolbar on
the left, the canvas with the transparency checkerboard in the centre, the
stepper above the canvas, the card inspector on the right (here step 1
"Open"), and the status bar at the bottom.*

The window is divided into five areas:

```
┌─────────────────────────────────────────────────────────────┐
│ Menu bar                                                     │
├──────────┬───────────────────────────────┬──────────────────┤
│          │        Stepper (6 steps)                         │
│ Tool-    ├───────────────────────────────┼──────────────────┤
│  bar     │                               │  Card             │
│  (left)  │        Canvas                 │  inspector       │
│          │      (image + selection)      │  (right)         │
│          │                               │                  │
├──────────┴───────────────────────────────┴──────────────────┤
│ Status bar (hints & messages)                                │
└──────────────────────────────────────────────────────────────┘
```

| Area | Purpose |
|---|---|
| **Menu bar** (top) | File, Project, Edit, View, Extras |
| **Stepper** (above the canvas) | Six steps: Open, Cut out, Adjust, Shape & Size, Relief & Layers, Export |
| **Toolbar** (left) | Move/Zoom, contextual selection/height tools, Undo/Redo/Theme |
| **Canvas** (centre) | Shows the image and the current selection; the zoom pill in the bottom right shows and controls the magnification |
| **Card inspector** (right) | Header with the step title/description, the cards of the active step, footer with "Back"/"Next" |
| **Status bar** (bottom) | Hints and feedback from the application |

### Menus "Edit", "View", "Project" & "Extras"

Many actions are also available from the menu bar:

- **Edit** – undo/redo, rotate (90° left/right/180°), flip
  horizontally/vertically, *Resize…*, as well as deselect/invert selection
  and *Restore original*. Handy when you prefer calling a function from the
  menu rather than the toolbar or card inspector.
- **View** – *Fit to View* (⌘0), *History* (opens the same change history as
  the former toolbar button), the *Preview mode* submenu (see
  [section 12](#12-step-6--export)), and *Light theme* to switch the colour
  scheme.
- **Project** – *New project*, *Open project…*, *Save project* / *…as…*
  (`.bgrproj`), and *Export assets for EufyMake Studio…* (see
  [section 11](#11-step-5--relief--layers) and
  [section 12](#12-step-6--export)).
- **Extras** – *Settings…* (see [section 13](#13-settings)).

![The "Edit" menu](../../../app_screenshots/bgremover_complete_20260711_094027/23_menu_edit.png)

*The "Edit" menu groups undo/redo, rotate, flip, and the selection actions.*

### The stepper

Above the canvas, the **stepper** guides you through six stations: **Open →
Cut out → Adjust → Shape & Size → Relief & Layers → Export**. Clicking an
already-reached or unlocked step jumps straight to it; without a loaded image
steps 2–6 stay locked (only step 1 is free). Completed steps show a
checkmark, and the active step is highlighted. At the bottom edge of the card
inspector, **"← Back"** and **"Next: …"** move through the flow; on the last
step the button instead triggers **"Export ✓"** (save).

### Zooming & view

- **Zoom:** use the **mouse wheel** over the canvas to zoom in and out, or
  use the floating **zoom pill** in the bottom right of the canvas
  (**−** / percentage / **+** / lock to fix the current zoom level).
- **Pan:** when the image is larger than the window, pan it with the
  **Move/Zoom** tool (left-click drag) or via the scroll bars.
- **Fit:** `View → Fit to View` (⌘0) scales the image fully back into the
  window. This happens automatically when you load an image.

---

## 3. Quick start in 5 steps

Here is how to remove a background in under a minute:

1. **Open an image** – in the *Open* step drag the image into the drop
   zone, use `File → Open` (⌘O / Ctrl+O), or drop it directly onto the
   canvas.
2. **Run the AI** – in the *Cut out* step click **"Remove background (AI)"**
   at the top. The background is removed automatically.
3. **Touch up (optional)** – use the **eraser** to remove leftover selection
   or the **brush** to add to it.
4. **Check** – press **Undo** (⌘Z) if needed to go back a step.
5. **Save** – in the *Export* step choose format **PNG** (preserves
   transparency) and click **Save**, or use `File → Save` (⌘S).

![Result of the AI background removal](../../../app_screenshots/bgremover_complete_20260711_094027/55_function_ai_result.png)

*After one click on "Remove background (AI)" the background is cut out
automatically – the status bar reports "AI background removal complete", and
the checkerboard pattern marks the transparent areas.*

The following chapters explain each step in detail.

---

## 4. Step 1 – Open an image

There are several ways to load an image:

- **Drop zone (step 1):** drag an image from the file manager directly onto
  the dashed field in the card inspector, or click on it to open the file
  dialog.
- **Menu:** `File → Open…` (⌘O / Ctrl+O).
- **Drag & drop onto the canvas:** drag an image file directly onto the
  canvas. If you drag several files, only the first image is loaded.
- **Recent files:** `File → Recent files` as well as the "Recently opened"
  card in the *Open* step (up to three entries with a thumbnail) list
  recently used entries. These are both images and `.bgrproj` **projects**
  (see [section 11](#11-step-5--relief--layers)); on click, the application
  detects the type and opens it accordingly.
- **Start with an image path:** if the program is started with an image path
  — via the **command line** (`bgremover image.png`) or a **Linux desktop
  launcher** (file association) — it loads that image directly on startup.
- **macOS Finder open:** on macOS an image can also be handed to BgRemover by
  **double-click**, via "Open with…", or through a **file association** in
  the Finder.

All of these paths use the same **validated, asynchronous load path**: the
same format and size checks apply, and large images are loaded in the
background — the status bar shows progress. Once loaded, the stepper
automatically unlocks the next step.

![The "File" menu](../../../app_screenshots/bgremover_complete_20260711_094027/20_menu_file.png)

*The "File" menu groups Open (⌘O), "Recent files", Save (⌘S), and
Save as… (⇧⌘S).*

**Supported input formats** are, bindingly, **PNG, JPEG, WebP, TIFF, BMP, and
GIF**. This list is the current input contract, not an example: other formats
are rejected in a controlled way. In particular, **HEIC/HEIF is currently not
supported by design** – a HEIC/HEIF file is rejected as an unsupported
format. Saving is to PNG, JPEG, WebP, or TIFF (see
[section 12](#12-step-6--export)).

> **Maximum image size: 40 megapixels.** Larger images are rejected with a
> message in the status bar.

---

## 5. The toolbar (left)

The vertical bar on the left edge is **contextual**: it only shows the tools
of the currently active step. From top to bottom:

### Move / Zoom (always available)

| Icon | Tool | Function |
|---|---|---|
| ✥ | **Move / Zoom** | Left-click drag pans the view, the mouse wheel zooms. Active in every step except *Cut out* and *Relief & Layers*. |

### Selection tools (only in the "Cut out" step)

| Icon | Tool | Function |
|---|---|---|
| 🪄 | **Magic wand** | Selects a contiguous area of colour with a single click (flood fill). Adjustable via *Tolerance*. |
| 🖌 | **Brush** | Paint a selection manually. |
| 🧽 | **Eraser** | Remove painted selection. |
| ⬡ | **Polygon lasso** | Click points one after another; **double-click** closes the polygon. **Esc** cancels. |

Quick keyboard switching: **W** magic wand, **B** brush, **E** eraser,
**L** lasso – these shortcuts only work while the *Cut out* step is active.

For all selection tools:

- **Shift + click** → **add** to the selection
- **Ctrl/Cmd + click** → **subtract** from the selection

### Height tools (only in the "Relief & Layers" step)

| Icon | Tool | Function |
|---|---|---|
| ▲ | **Lighten (raise)** | A brush stroke raises the height of the active height layer. |
| ▼ | **Darken (lower)** | A brush stroke lowers the height of the active height layer. |

Both tools are disabled as long as no height layer is active (see
[section 11](#11-step-5--relief--layers)); the tooltip explains why. They
complement the slider-based lighten/darken actions in the card inspector with
a freehand painting tool.

### Toolbar footer: Undo, Redo, Theme

At the bottom of the toolbar, three buttons stay visible regardless of the
current step:

| Icon | Function |
|---|---|
| ↩ | **Undo** (⌘Z) – revert the last step |
| ↪ | **Redo** (⇧⌘Z) – reapply the undone step |
| ◐ | **Toggle light/dark theme** – switches the colour scheme (same action as `View → Light theme`) |

> AI background removal, the change history, and opening/saving images are no
> longer in the toolbar: they are reachable via the card inspector of the
> respective step, the menu, or their keyboard shortcuts (see
> [section 7](#7-step-2--cut-out) and [section 12](#12-step-6--export)).

> **Tip:** hover over an icon to show a brief tooltip.

---

## 6. Making a selection

Almost all edits (make transparent, replace colour) act on the **currently
selected area**. The selection is highlighted on the image in colour. The
selection tools are active in the *Cut out* step.

![A loaded image with an active selection](../../../app_screenshots/bgremover_complete_20260711_094027/02_main_loaded_selection.png)

*A loaded image with an active selection: the selected background area is
highlighted in colour on the canvas.*

### With the magic wand (recommended for solid-colour backgrounds)

1. Choose the magic wand in the toolbar.
2. Click on the background – all similar, contiguous colours are selected.
3. Not enough selected? Use **Shift+click** to add more areas, or increase
   the **Tolerance** (card *Tool settings* in the *Cut out* step).

### With brush & eraser (for fine corrections)

- **Brush:** paint over the desired area to add it to the selection.
- **Eraser:** paint over incorrectly selected areas to remove them.
- Set the **brush size** in the *Tool settings* card.

### With the polygon lasso (for straight edges)

1. Choose the lasso.
2. Click corner by corner around the object.
3. **Double-click** closes the polygon and creates the selection.
4. **Esc** cancels the operation.

---

## 7. Step 2 – Cut out

In the *Cut out* step you separate the subject from the background –
automatically via AI or by hand. The card inspector groups four cards for
this.

![The "Cut out" step](../../../app_screenshots/bgremover_complete_20260711_094027/11_step_2_cutout.png)

*Step 2 "Cut out": the AI button at the top, below it tool settings,
selection actions, and "Edit background".*

### AI background removal

At the top of the card inspector, the **"Remove background (AI)"** button
removes the background fully automatically. On first use, the AI model is
loaded, which can take a moment.

> If the AI component (`rembg`) is not installed, the button is greyed out.
> See the installation guide for setting up the AI feature.

### Tool settings (tolerance & brush size)

| Slider | Range | Effect |
|---|---|---|
| **Tolerance (magic wand)** | 0 – 255 (default: 30) | How similar colours must be to get selected together by the magic wand. **Low** = only very similar colours · **High** = many shades. |
| **Brush size** | 4 – 200 px (default: 30 px) | Diameter of brush and eraser. |

### Selection actions

- **Clear selection** – clears the current selection. **Esc** first cancels
  an active crop or a pending polygon lasso, and only clears the selection
  when neither interaction is active.
- **Invert selection** (⌘⇧I) – swaps selected and unselected areas. Useful:
  first select the *object*, then invert to edit the *background*.
- **Grow / Shrink** – grows or shrinks the selection by the radius set next
  to it (1 – 20 px, default: 2 px). Useful for removing a thin colour fringe
  after cutting out.

### Edit background

| Action | Description |
|---|---|
| **Remove (transparent)** | Makes the selected area completely transparent. Tip: first select the background with the magic wand. |
| **Pick colour** | Opens a colour picker. The small coloured button shows the currently chosen replacement colour. |
| **Replace colour** | Fills the selected area with the chosen colour. |

![Colour picker dialog](../../../app_screenshots/bgremover_complete_20260711_094027/31_dialog_color_picker.png)

*"Pick colour" opens the colour picker; the chosen colour appears in the
swatch and is applied to the selection with "Replace colour".*

**Typical workflow:** select the background with the magic wand/AI →
*Remove (transparent)* for a cut-out PNG, **or** pick a colour and
*Replace colour* for a solid-colour background (e.g. white for ID photos).

### Smooth edge (feather)

In the *Smooth edge* section of the same card you can soften the **alpha
edge** – useful against hard, "cut-out"-looking borders after a removal.

- **Radius:** 0 – 20 px (default: 2 px) sets the width of the soft
  transition.
- **Smooth edge** applies the smoothing. It affects only the **transparency
  channel** (the colours stay unchanged) and, when a selection is active,
  only within the selection.

---

## 8. Step 3 – Adjust (colour correction)

The *Adjust* step contains a simple **colour correction**. It acts on the
**active colour layer** (see [section 11](#11-step-5--relief--layers)) and
leaves the transparency unchanged.

| Slider | Range | Effect |
|---|---|---|
| **Brightness** | 0 – 200 % (default: 100 %) | Brighten or darken the image. |
| **Contrast** | 0 – 200 % (default: 100 %) | Difference between light and dark areas. |
| **Saturation** | 0 – 200 % (default: 100 %) | Colour intensity; 0 % gives grayscale. |

- While you drag the sliders, the canvas shows a **live preview**.
- **Apply** commits the correction (undoable/redoable in the history).
- **Reset** returns all three sliders to 100 % and discards the preview.

---

## 9. Step 4 – Shape & Size

The *Shape & Size* step groups rotate/flip as well as round corners, crop,
and a quick pixel resize.

![The "Shape & Size" step](../../../app_screenshots/bgremover_complete_20260711_094027/13_step_4_shape.png)

*Step 4 "Shape & Size": rotate (quick rotation/free angle), flip, round
corners, and the crop formats at the bottom.*

### Rotate

- **Quick rotation:** buttons for *90° left*, *90° right*, *180°*, and
  *270°*.
- **Free angle:** slider or input field from **−180° to +180°**, then click
  **Apply angle**. Oblique angles produce transparent corners.

> Quick rotation is also available via keyboard: ⌘← (90° left) and
> ⌘→ (90° right).

### Flip

- **Horizontal** – flip left ↔ right.
- **Vertical** – flip top ↕ bottom.

### Round corners

1. Use the **Radius** slider to set the rounding (0 = no rounding, up to
   500 px = maximum rounding).
2. Click **Round corners**.

The result is saved with transparent corners – best as PNG.

### Resize (pixels, directly in the step)

The "Resize" card offers **width × height in pixels** directly in the step:
enter values and click **Apply**. For the linked aspect ratio, the
resampling method, and the physical dimensions (mm/DPI), use the full
dialog from [section 10](#10-resize--physical-dimensions).

### Output format & crop

1. Choose a format – a **frame** appears on the image:
   - **Special format:** ⬤ Circle
   - **Square:** 1:1
   - **Landscape:** 16:9, 4:3
   - **Portrait:** 9:16, 3:4
2. **Move the frame:** click in the centre and drag.
3. **Resize:** drag the corners – the aspect ratio is preserved.
4. A bar appears above the canvas:
   - **✓ Apply crop** – crops the image.
   - **✗ Cancel** – discards the frame.

![Active circle crop with confirmation bar](../../../app_screenshots/bgremover_complete_20260711_094027/63_crop_circle_overlay.png)

*"Circle" example: the crop frame sits over the image with drag handles.
"✓ Apply crop" crops the image, "✗ Cancel" discards the frame.*

---

## 10. Resize & physical dimensions

Via `Edit → Resize…` (Ctrl+R) you open the full resize dialog – with linked
aspect ratio, resampling method, and physical dimensions. For a quick pixel
resize without a dialog, the inline card from
[section 9](#9-step-4--shape--size) is available in the *Shape & Size* step.
The dialog supports two units:

### Resize in pixels

In **Pixel** mode you enter **Width** and **Height** directly in pixels.
With **Link aspect ratio** the ratio is preserved. The resampling method
determines the quality:

| Method | Suitability |
|---|---|
| **Lanczos** | Best quality (default), ideal for downscaling. |
| **Bicubic** | Smooth results, a good all-rounder. |
| **Bilinear** | Faster, slightly softer. |
| **Nearest neighbor** | Keeps hard edges/pixels, no smoothing. |

The dialog shows the resulting megapixel count and respects the limit of
**40 megapixels**.

### Physical dimensions (mm/DPI) & print area

In **Millimeters (mm + DPI)** mode you set **width/height in millimetres**
and a **resolution (DPI)**; the pixel size follows from these. This physical
size is the authoritative print size and is stored in the `.bgrproj`
project.

Via **Target medium** you choose a common print medium (e.g. A4 or A3). If
the motif fits, the dialog confirms this; if it is larger than the medium, a
hint points out that the print area is exceeded.

---

## 11. Step 5 – Relief & Layers

The *Relief & Layers* step groups the layer management and the height-map
workspace into two cards.

### Layer kinds and roles

BgRemover can manage several **layers** in a **project** and save the whole
thing as a `.bgrproj` file. For classic background editing you do not need
to deal with this – a single image behaves like a single colour layer. Each
layer has a **kind** and optionally a **role**. Only **colour layers** feed
into the visible colour image; the other kinds are data layers for print
preparation.

| Kind / role | Meaning |
|---|---|
| **Colour** (colour motif) | The visible image. Several colour layers together form the composite, which is also exported. |
| **Height** (height map) | A grayscale height map for relief/UV printing. |
| **Gloss** (gloss mask) | A mask for gloss effects (experimental). |
| **Generic** | A neutral data layer without a fixed role. |

### Managing layers

In the *Layers* card you manage the layer list:

| Action | Description |
|---|---|
| **New layer / Duplicate / Delete** | Add a layer, copy the active layer, or remove it. |
| **Move up / down** | Change the stacking order of the layers. |
| **Rename** | Rename the active layer. |
| **Role** | Assign a role to the active layer (only matching combinations are allowed). |
| **Visibility** | Show or hide a layer. |
| **Select** | Choose a layer as the **active** layer – tools act on it. |
| **Opacity** | Layer opacity (applied on release). |

### Project files (.bgrproj)

Via the **Project** menu you work with project files:

- **New project** (Ctrl+N), **Open project…** (Ctrl+Shift+O).
- **Save project** (Ctrl+Alt+S) and **Save project as…**
  (Ctrl+Alt+Shift+S).

A `.bgrproj` file is an archive of a **manifest** (order, kinds, roles,
names, physical dimensions) and **one PNG per layer**. This preserves all
layers, including transparency, losslessly. Projects also appear under
"Recent files" (see [section 4](#4-step-1--open-an-image)).

### Height maps: Acquire

A **height map** is a grayscale layer in which brightness represents a
height: **light = high, dark = low**. It is the basis for relief and UV
printing. The *Height* card works on the active **height layer**; the Edit
and Optimise sections are only active when a height layer is active.

- **Generate from image** – deterministically converts the current colour
  image into a height map and creates it as a new height layer.
- **Import grayscale…** – loads a grayscale image as a height map and scales
  it to the project size.

### Height maps: Edit

- **Lighten / Darken** – raises or lowers the height; the **Strength**
  controls how much. For freehand painting, the *Relief & Layers* step also
  offers the same-named brush tools in the toolbar (see
  [section 5](#5-the-toolbar-left)).
- **Set height** – sets the height to a fixed **value**.
- **Invert** – swaps high and low.

When a selection is active, the slider-based actions affect only the
selection, otherwise the whole layer.

### Height maps: Optimise

The optimise operations show a **live preview**; **Apply** commits it
(undoable/redoable), **Discard preview** discards it.

| Operation | Effect |
|---|---|
| **Levels (black/white)** | Set the black and white point of the height. |
| **Gamma** | Pull mid heights brighter/darker. |
| **Gaussian blur (radius)** | Soft, uniform smoothing. |
| **Median blur (radius)** | Smooths while preserving edges. |
| **Threshold** | Split the height into two levels. |
| **Steps** | Quantise the height to a number of levels. |
| **Range (min/max)** | Clamp the height to a value range. |

---

## 12. Step 6 – Export

The final *Export* step groups the 2D preview, saving the image, and the
UV-print export into three cards.

### 2D preview (colour, relief, height, gloss, combined)

The **2D preview** shows different views of the same motif directly on the
canvas. It is a **pure on-screen display** and changes neither the image nor
the export. The *Preview* card offers a segmented control with four modes;
the fifth mode "Combined" is reachable via `View → Preview mode`.

| Mode | Display |
|---|---|
| **Colour** | The normal colour image. |
| **Relief** | A hillshade relief from the height map, multiplied over the colour image. |
| **Height** | The height map as a grayscale image. |
| **Gloss** | The gloss mask as a glossy sheen. |
| **Combined** (only via `View → Preview mode`) | Colour, relief, and gloss together. |

- With **Relief strength** (0 – 100 %, default 70 %) you set the intensity
  of the relief; at 0 % the relief is skipped.
- **Show gloss** toggles the gloss share on or off.

The preview card and the View submenu stay in sync. Hidden data layers are
ignored in the preview.

### Saving

The *Save* card offers a format selector (PNG/JPEG/WebP/TIFF) and the save
button directly in the step; alternatively you can save via the menu:

- **Save:** `File → Save` (⌘S / Ctrl+S)
- **Save as…:** `File → Save as…` (⇧⌘S)

On save, the **colour composite** is always written (regardless of which
layer is currently active or which preview mode is set).

| Format | Properties | Recommendation |
|---|---|---|
| **PNG** | With transparency | For cut-out objects – **recommended default** |
| **JPEG** | No alpha channel, transparent areas become white | For photos with an opaque background |
| **WebP** | Modern web format, transparency possible | For use on the web |
| **TIFF** | Lossless, transparency possible | For archiving/printing |

> To preserve the cut-out, **always choose PNG, WebP, or TIFF** – JPEG fills
> transparent areas with white.

### Export for EufyMake Studio

Via the *UV printing* card in the *Export* step, or `Project → Export assets
for EufyMake Studio…` (Ctrl+Alt+E), BgRemover writes **import assets** for
EufyMake Studio – **not** a finished `.empf` file:

- **Colour motif** (required) as an RGBA PNG – from a layer with the *Colour
  motif* role, or, if none exists, from the colour composite.
- **Height map** (optional) as grayscale with **light = high, dark = low** –
  available only when a layer carries the *Height map* role (e.g. a height
  layer created via "Generate from image"; a plain height layer without
  this role is not exported).
- **Gloss mask** (optional, experimental) as a helper asset – available only
  when a layer carries the *Gloss* role.

In the dialog you choose the export folder, the optional assets, and the
**bit depth** of the height map (8-bit default, 16-bit experimental). A
**pre-export check** runs continuously and reports findings by severity:

- **Errors** (⛔) block the export until they are fixed – e.g. a missing
  colour motif or mismatching sizes.
- **Warnings** (⚠️) must be confirmed deliberately – e.g. empty height/gloss
  data or the unconfirmed 16-bit output.

Afterwards you import and position the assets in EufyMake Studio, assign ink
modes/layers there, and save the Studio project itself as `.empf`.

---

## 13. Settings

Via `Extras → Settings…` (⌘, / Ctrl+,) you can manage the following
settings:

![The settings dialog](../../../app_screenshots/bgremover_complete_20260711_094027/30_dialog_settings.png)

*The settings dialog: language, default open/save directories, preferred
image file format, and the path to the log file with the "Open folder"
button.*

| Setting | Description |
|---|---|
| **Default open directory** | Start folder for the open dialog (empty = last used) |
| **Default export/save directory** | Start folder for the save dialog (empty = last used) |
| **Preferred image file format** | PNG, JPEG, WebP, or TIFF – appears as the first option in the save dialog |
| **Language** | German, English, Spanish, French, Ukrainian, or Chinese; the change takes effect after a restart |
| **Log file** | Shows the path of the log file; the "Open folder" button opens the directory in the file manager |

The directories, the preferred file format, and the language are remembered
across application starts.

---

## 14. Keyboard shortcuts

On macOS the modifier key is **⌘ (Cmd)**, on Linux/Windows **Ctrl**. The
tool shortcuts (W/B/E/L) only work while the *Cut out* step is active;
actions without a shortcut in the table are only reachable via the menu or
the card inspector.

| Action | Shortcut |
|---|---|
| Select magic wand (only in the "Cut out" step) | W |
| Select brush (only in the "Cut out" step) | B |
| Select eraser (only in the "Cut out" step) | E |
| Select polygon lasso (only in the "Cut out" step) | L |
| Open image | ⌘O |
| Save image | ⌘S |
| Save image as… | ⇧⌘S |
| New project | ⌘N |
| Open project… | ⇧⌘O |
| Save project | ⌥⌘S |
| Save project as… | ⇧⌥⌘S |
| Export assets for EufyMake Studio… | ⌥⌘E |
| Undo | ⌘Z |
| Redo | ⇧⌘Z |
| Resize… | ⌘R |
| Rotate 90° left | ⌘← |
| Rotate 90° right | ⌘→ |
| Deselect (when no crop/lasso is active) | Esc |
| Invert selection | ⌘⇧I |
| Fit to View | ⌘0 |
| Open settings | ⌘, |

---

## 15. Typical workflows

### A) Cut out a product photo (transparent background)

1. Open the image.
2. In the *Cut out* step, click **"Remove background (AI)"**.
3. Touch up edges with the **eraser**/**brush**.
4. Optionally **Shrink** (1–2 px) to remove the colour fringe.
5. In the *Export* step, save as **PNG**.

### B) ID photo with a white background

1. Open the image.
2. In the *Cut out* step, click the **magic wand** on the background
   (adjust tolerance).
3. **Pick colour** (white) → **Replace colour**.
4. In the *Shape & Size* step, choose format **1:1**, position the frame,
   **✓ Apply crop**.
5. In the *Export* step, save as **JPEG** or **PNG**.

### C) Round profile picture

1. Open the image.
2. Remove the background via **AI** (optional).
3. In the *Shape & Size* step, choose **⬤ Circle**, drag the frame over the
   face.
4. **✓ Apply crop**.
5. In the *Export* step, save as **PNG** (transparency outside the circle).

### D) Keep the object, only swap the background

1. Open the image, in the *Cut out* step click the **magic wand** on the
   **object**.
2. **Invert selection** (⌘⇧I) → the background is now selected.
3. Pick a colour → **Replace colour**.
4. Save in the *Export* step.

### E) Height-relief asset for EufyMake Studio

1. Open and cut out the image.
2. In the *Relief & Layers* step, click **Generate from image**.
3. Refine the height in the *Optimise* section (e.g. *Levels*, *Blur*) and
   **Apply**.
4. In the *Export* step, choose preview mode **Relief** or, via `View →
   Preview mode`, **Combined** to check.
5. Card *UV printing* → review the findings and export.

---

## 16. Tips & tricks

- **Rough first, then fine:** cut out roughly with AI or the magic wand,
  then correct with brush/eraser.
- **Adjust tolerance:** too much selected → lower the tolerance. Too little
  captured → raise the tolerance or use Shift+click.
- **Get rid of a colour fringe:** after cutting out, in the *Cut out* step
  apply "Shrink" by 1–2 px before removing the background.
- **Soft edges:** with *Smooth edge* (step *Cut out*), cut-out borders look
  less harsh.
- **Step back:** every step lands in the history – via `View → History`,
  double-click to jump back to any earlier state.
- **Nothing works anymore?** `Edit → Restore original` resets the image to
  its loaded state.

---

## 17. Known limitations

- **Maximum image size: 40 megapixels.** Larger images are rejected.
- **Input formats:** PNG, JPEG, WebP, TIFF, BMP, and GIF are supported.
  **HEIC/HEIF is currently not supported** and is rejected in a controlled
  way.
- The **AI feature** requires the optional component `rembg`. Without it
  the AI button is disabled; all manual tools continue to work.
- The **2D preview** is a pure on-screen display; the image export
  unchangedly writes the colour composite.
- The **EufyMake export** only produces import assets, **not** a native
  `.empf` file; the 16-bit height output is experimental.
- The **app bundle** (`BgRemover.app`) is macOS-specific; on Linux the
  application is launched directly. Windows is currently not part of the
  officially tested matrix.

---

## 18. Troubleshooting & log file

If problems occur, check the internal **log file** `bgremover.log`. It is
stored in the app data directory determined by Qt and is created with the
first log entry. The exact path can vary by platform and Qt configuration:

- **macOS (current configuration):**
  `~/Library/Application Support/BgRemover/BgRemover/bgremover.log`
- **Linux:** below `~/.local/share/`

The macOS app-bundle launcher additionally writes startup diagnostics to
`~/Library/Application Support/BgRemover/bgremover.log`.

The internal file contains runtime messages and error details (stack
traces) and is the first port of call for support requests.

The easiest way to find the file is via `Extras → Settings… → Log file`:
the full path is shown there, and the **"Open folder"** button opens the
directory directly in the file manager – ideal for attaching the log file
to a support email.

| Problem | Possible solution |
|---|---|
| AI button greyed out | `rembg` is not installed – see the installation guide |
| Image cannot be opened | Over 40 megapixels? Format supported (no HEIC/HEIF)? Read the status bar |
| AI takes very long | First call loads the model – one-time only, faster afterwards |
| Transparency gone after saving | Saved as JPEG → choose PNG/WebP/TIFF instead |
| Project cannot be opened | Corrupt/incomplete `.bgrproj` file? Read the status bar |

---

## 19. License

BgRemover is released under the **GNU General Public License v3.0 or later**
(`GPL-3.0-or-later`) – see [LICENSE](../../../LICENSE). A complete list of
all libraries used and their licences is in [RESOURCES.md](RESOURCES.md).

---

*This guide is part of the BgRemover project. For questions or suggestions,
please open an issue in the GitHub repository.*
