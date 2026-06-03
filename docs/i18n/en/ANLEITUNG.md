[Deutsch](../../../ANLEITUNG.md) · **English** · [Español](../es/ANLEITUNG.md) · [Français](../fr/ANLEITUNG.md) · [Українська](../uk/ANLEITUNG.md) · [简体中文](../zh/ANLEITUNG.md)

> **Note:** A PDF version of this guide is only generated for the German original
> (`ANLEITUNG.pdf`). No PDF is produced for this translation.

# BgRemover – User Guide

This guide walks you step by step through how to use **BgRemover** — from
opening your first image to saving the finished result. It is aimed at users
with no prior image-editing experience.

> Notes on **installation** are intentionally not included here; see
> [INSTALL_MAC.md](INSTALL_MAC.md) (macOS) or
> [INSTALL_LINUX.md](INSTALL_LINUX.md) (Linux). This guide assumes the
> application can already be launched.

---

## Table of Contents

1. [What can BgRemover do?](#1-what-can-bgremover-do)
2. [The application window at a glance](#2-the-application-window-at-a-glance)
3. [Quick start in 5 steps](#3-quick-start-in-5-steps)
4. [Opening an image](#4-opening-an-image)
5. [The toolbar (left)](#5-the-toolbar-left)
6. [Making a selection](#6-making-a-selection)
7. [Tab "Selection"](#7-tab-selection)
8. [Tab "Background"](#8-tab-background)
9. [Tab "Rotate/Flip"](#9-tab-rotateflip)
10. [Tab "Shape" – Corners & Crop](#10-tab-shape--corners--crop)
11. [Saving an image](#11-saving-an-image)
12. [Settings](#12-settings)
13. [Keyboard shortcuts](#13-keyboard-shortcuts)
14. [Typical workflows](#14-typical-workflows)
15. [Tips & tricks](#15-tips--tricks)
16. [Known limitations](#16-known-limitations)
17. [Troubleshooting & log file](#17-troubleshooting--log-file)
18. [License](#18-license)

---

## 1. What can BgRemover do?

BgRemover is an image-editing tool for **removing, replacing, and editing
backgrounds**. The key features:

- **AI background removal** – remove the background automatically with a
  single click.
- **Manual selection** with magic wand, brush, eraser, and polygon lasso.
- **Replace background** – make the selection transparent or fill it with any
  colour.
- **Transform** – rotate (in 90° steps or a free angle) and flip.
- **Shape & crop** – round corners, crop to circle or a fixed aspect ratio.
- **History** with undo/redo and jump to any earlier editing step.
- **Save** as PNG, JPEG, WebP, or TIFF.

---

## 2. The application window at a glance

![BgRemover – main window after launch](../../../app_screenshots/bgremover_complete_20260528_214013/01_main_empty.png)

*The main window right after launch: the toolbar on the left, the canvas with
the transparency checkerboard in the centre, the tab panel on the right (here
the "Selection" tab), and the status bar at the bottom. The screenshots show
the German interface — the labels correspond to the terms used in this guide.*

The window is divided into four areas:

```
┌──────────┬───────────────────────────────┬──────────────────┐
│          │                               │                  │
│ Tool-    │        Canvas                 │   Tab panel      │
│  bar     │      (image + selection)      │  (settings)      │
│  (left)  │                               │   (right)        │
│          │                               │                  │
├──────────┴───────────────────────────────┴──────────────────┤
│ Status bar (hints & messages)                                │
└──────────────────────────────────────────────────────────────┘
```

| Area | Purpose |
|---|---|
| **Menu bar** (top) | File, Edit, View, Extras |
| **Toolbar** (left) | Selection tools, AI, history, open/save |
| **Canvas** (centre) | Displays the image and the current selection |
| **Tab panel** (right) | Four tabs: Selection, Background, Rotate/Flip, Shape |
| **Status bar** (bottom) | Hints and feedback from the application |

### Menus "Edit" & "View"

Many actions are also available from the menu bar:

- **Edit** – undo/redo, rotate (90° left/right), flip horizontally/vertically,
  as well as deselect/invert selection and *Restore original*. Handy when you
  prefer the menu over the toolbar or a tab.
- **View** – *Fit to view* (⌘0); see "Zooming & view" below.

![The "Edit" menu](../../../app_screenshots/bgremover_complete_20260528_214013/22_menu_edit.png)

*The "Edit" menu groups undo/redo, rotate, flip, and the selection actions.*

### Zooming & view

- **Zoom:** use the **mouse wheel** over the canvas to zoom in and out.
- **Pan:** when the image is larger than the window, navigate with the
  **scroll bars** on the right and bottom edges.
- **Fit:** `View → Fit to view` (⌘0) scales the image fully back into the
  window. This also happens automatically when you load an image.

---

## 3. Quick start in 5 steps

Remove a background in under a minute:

1. **Open an image** – `File → Open` (⌘O / Ctrl+O) or drag & drop the image
   into the window.
2. **Run AI** – click the **AI icon** in the left toolbar. The background is
   removed automatically.
3. **Touch up (optional)** – use the **eraser** to remove leftover selection
   or the **brush** to add to it.
4. **Check** – press **Undo** (⌘Z) if needed to go back a step.
5. **Save** – `File → Save` (⌘S), choose **PNG** format (preserves
   transparency).

![Result of the AI background removal](../../../app_screenshots/bgremover_complete_20260528_214013/54_function_ai_result.png)

*After one click on the AI icon the background is cut out automatically; the
status bar confirms the AI background removal is complete, and the checkerboard
pattern marks the transparent areas.*

The following sections explain each step in detail.

---

## 4. Opening an image

There are three ways to load an image:

- **Menu:** `File → Open…` (⌘O / Ctrl+O).
- **Drag & Drop:** drag an image file from the file manager directly onto the
  canvas. If you drag several files, only the first image is loaded.
- **Recent files:** `File → Recent files` lists the last 10 opened images.

![The "File" menu](../../../app_screenshots/bgremover_complete_20260528_214013/20_menu_file.png)

*The "File" menu groups Open (⌘O), "Recent files", Save (⌘S), and
Save as… (⇧⌘S).*

When opening, common formats such as PNG, JPEG, WebP, TIFF, BMP, and GIF
are supported; saving is to PNG, JPEG, WebP, or TIFF. Large
images are loaded in the background — the status bar shows progress.

> **Maximum image size: 40 megapixels.** Larger images are rejected with a
> message in the status bar.

---

## 5. The toolbar (left)

The vertical bar on the left edge contains, from top to bottom:

### Selection tools

| Icon | Tool | Function |
|---|---|---|
| 🪄 | **Magic wand** | Selects a contiguous area of similar colour with a single click (flood fill). Adjustable via *Tolerance*. |
| 🖌 | **Brush** | Paint a selection manually. |
| 🧽 | **Eraser** | Remove painted selection. |
| ⬡ | **Polygon lasso** | Click points one by one; **double-click** closes the polygon. **Esc** cancels. |

Quick keyboard switching: **W** magic wand, **B** brush,
**E** eraser, **L** lasso.

For all selection tools:

- **Shift + click** → **add** to selection
- **Ctrl/Cmd + click** → **subtract** from selection

### AI background removal

| Icon | Function |
|---|---|
| ✨ | **AI** – removes the background fully automatically. The AI model is loaded on first use, which may take a moment. |

> If the AI component (`rembg`) is not installed, the button is greyed out.
> See the installation guide for setting up the AI feature.

### History

| Icon | Function |
|---|---|
| ↩ | **Undo** (⌘Z) – revert the last step |
| ↪ | **Redo** (⇧⌘Z) – reapply the undone step |
| ⟲ | **Restore original** – discard all edits |
| 🕘 | **Edit history** – list of all steps; **double-click** an entry to jump to that state |

![The "Edit history" popup](../../../app_screenshots/bgremover_complete_20260528_214013/40_popup_history.png)

*The edit history lists every editing step; double-clicking an entry jumps back
to exactly that state.*

### File

| Icon | Function |
|---|---|
| 📂 | **Open image** (⌘O) |
| 💾 | **Save image** (⌘S) |

> **Tip:** Hover over an icon to show a brief tooltip.

---

## 6. Making a selection

Almost all edits (make transparent, replace colour) act on the **currently
selected area**. The selection is highlighted on the image in colour.

![A loaded image with an active selection](../../../app_screenshots/bgremover_complete_20260528_214013/02_main_loaded_selection.png)

*A loaded image with an active selection: the selected background area is
highlighted in colour on the canvas.*

### With the magic wand (recommended for solid-colour backgrounds)

1. Choose the magic wand in the toolbar.
2. Click on the background – all similar, contiguous colours are selected.
3. Not enough? Use **Shift+click** to add more areas or increase the
   **Tolerance** (tab *Selection*).

### With brush & eraser (for fine corrections)

- **Brush:** paint over the desired area to add it to the selection.
- **Eraser:** paint over incorrectly selected areas to remove them.
- Set the **brush size** in the *Selection* tab.

### With the polygon lasso (for straight edges)

1. Choose the lasso.
2. Click corner by corner around the object.
3. **Double-click** closes the polygon and creates the selection.
4. **Esc** cancels the operation.

---

## 7. Tab "Selection"

The first tab in the right panel controls selection behaviour – it can already
be seen in the overview above ([section 2](#2-the-application-window-at-a-glance)) and in the figure in [section 6](#6-making-a-selection).

### Tool hints

At the top, the four selection tools are listed with a short description and
the modifier keys (Shift = add, Ctrl/Cmd = subtract).

### Settings

| Slider | Range | Effect |
|---|---|---|
| **Tolerance (magic wand)** | 0 – 255 (default: 30) | How similar colours must be to be selected together. **Low** = only very similar colours · **High** = many shades. |
| **Brush size** | 4 – 200 px (default: 30 px) | Diameter of brush and eraser. |

### Selection actions

- **Deselect** – clears the current selection (also with the **Esc** key).
- **Invert selection** (⌘⇧I) – swaps selected and unselected areas. Useful:
  first select the *object*, then invert to edit the *background*.
- **Expand / Shrink** – grows or shrinks the selection by the adjacent radius
  (1 – 20 px, default: 2 px). Useful for removing a thin colour fringe after cutting out.

---

## 8. Tab "Background"

Here the current selection is actually changed.

![The "Background" tab](../../../app_screenshots/bgremover_complete_20260528_214013/11_tab_background.png)

*The "Background" tab: "Remove (transparent)" makes the selection see-through;
the colour swatch and "Replace colour" fill it with a colour.*

| Action | Description |
|---|---|
| **Remove (transparent)** | Makes the selected area completely transparent. Tip: first select the background with the magic wand. |
| **Pick colour** | Opens a colour picker. The small coloured button shows the currently chosen replacement colour. |
| **Replace colour** | Fills the selected area with the chosen colour. |

![Colour picker dialog](../../../app_screenshots/bgremover_complete_20260528_214013/31_dialog_color_picker.png)

*"Pick colour" opens the colour picker; the chosen colour appears in the swatch
and is applied to the selection with "Replace colour".*

**Typical workflow:** select background with magic wand/AI →
*Remove (transparent)* for a cut-out PNG, **or** pick a colour and
*Replace colour* for a solid background (e.g. white for ID photos).

---

## 9. Tab "Rotate/Flip"

![The "Rotate/Flip" tab](../../../app_screenshots/bgremover_complete_20260528_214013/12_tab_transform.png)

*The "Rotate/Flip" tab with quick rotation (90°/180°/270°), a free angle, and
the buttons for horizontal and vertical flipping.*

### Rotate

- **Quick rotation:** buttons for *90° left*, *90° right*, *180°*, and *270°*.
- **Free angle:** slider or input field from **−180° to +180°**, then click
  **Apply angle**. Oblique angles produce transparent corners.

### Flip

- **Horizontal** – flip left ↔ right.
- **Vertical** – flip top ↕ bottom.

> Quick rotation is also available via keyboard: ⌘← (90° left) and
> ⌘→ (90° right).

---

## 10. Tab "Shape" – Corners & Crop

![The "Shape" tab](../../../app_screenshots/bgremover_complete_20260528_214013/13_tab_shape_crop.png)

*The "Shape" tab: "Round corners" with a radius slider at the top, the crop
formats (special, landscape, and portrait) below.*

### Round corners

1. Use the **Radius** slider to set the rounding (0 = no rounding,
   up to 500 px = maximum).
2. Click **Round corners**.

The result is saved with transparent corners — best as PNG.

### Output format & crop

1. Choose a format – a **frame** appears on the image:
   - **Special formats:** ⬤ Circle, ■ 1:1 (Square)
   - **Landscape:** 16:9, 4:3, 3:2, 2:1, 7:4.5 (14:9)
   - **Portrait:** 9:16, 3:4
2. **Move frame:** click in the centre and drag.
3. **Resize:** drag the corners – the aspect ratio is preserved.
4. A bar appears above the canvas:
   - **✓ Apply crop** – crops the image.
   - **✗ Cancel** – discards the frame.

![Active circle crop with confirmation bar](../../../app_screenshots/bgremover_complete_20260528_214013/61_crop_circle_overlay.png)

*"Circle" example: the crop frame sits over the image with drag handles.
"✓ Apply crop" crops the image, "✗ Cancel" discards the frame.*

---

## 11. Saving an image

- **Save:** `File → Save` (⌘S / Ctrl+S)
- **Save as…:** `File → Save as…` (⇧⌘S)

Choose the desired **file format** in the dialog:

| Format | Properties | Recommendation |
|---|---|---|
| **PNG** | With transparency | For cut-out objects – **recommended default** |
| **JPEG** | No alpha channel; transparent areas become white | For photos with an opaque background |
| **WebP** | Modern web format, transparency supported | For use on the web |
| **TIFF** | Lossless, transparency supported | For archiving/printing |

> To preserve the cut-out, **always choose PNG, WebP, or TIFF** — JPEG fills
> transparent areas with white.

---

## 12. Settings

Via `Extras → Settings…` (⌘, / Ctrl+,) you can manage the following settings:

![The settings dialog](../../../app_screenshots/bgremover_complete_20260528_214013/30_dialog_settings.png)

*The settings dialog: language, default open/save directories, preferred image
format, and the path to the log file with the "Open folder" button.*

| Setting | Description |
|---|---|
| **Default open directory** | Start folder for the open dialog (empty = last used) |
| **Default export/save directory** | Start folder for the save dialog (empty = last used) |
| **Preferred image format** | PNG, JPEG, WebP, or TIFF – appears as the first option in the save dialog |
| **Language** | German or English; the change takes effect after a restart |
| **Log file** | Shows the path of the log file; the "Open folder" button opens the directory in the file manager |

The directories, preferred format, and language are remembered across
application restarts.

---

## 13. Keyboard shortcuts

On macOS the modifier key is **⌘ (Cmd)**, on Linux/Windows **Ctrl**.

| Action | Shortcut |
|---|---|
| Select magic wand | W |
| Select brush | B |
| Select eraser | E |
| Select polygon lasso | L |
| Open image | ⌘O |
| Save image | ⌘S |
| Save image as… | ⇧⌘S |
| Undo | ⌘Z |
| Redo | ⇧⌘Z |
| Rotate 90° left | ⌘← |
| Rotate 90° right | ⌘→ |
| Deselect | Esc |
| Invert selection | ⌘⇧I |
| Fit to view | ⌘0 |
| Open settings | ⌘, |

---

## 14. Typical workflows

### A) Cut out a product photo (transparent background)

1. Open the image.
2. Click **AI** in the toolbar.
3. Refine edges with **eraser**/**brush**.
4. In the *Selection* tab, optionally **Shrink** (1–2 px) to remove the colour
   fringe.
5. Save as **PNG**.

### B) ID photo with white background

1. Open the image.
2. Click the **magic wand** on the background (adjust tolerance).
3. *Background* tab → **Pick colour** (white) → **Replace colour**.
4. *Shape* tab → choose format **1:1**, position the frame, click
   **✓ Apply crop**.
5. Save as **JPEG** or **PNG**.

### C) Round profile picture

1. Open the image.
2. Remove the background with **AI** (optional).
3. *Shape* tab → choose **⬤ Circle**, drag the frame over the face.
4. Click **✓ Apply crop**.
5. Save as **PNG** (transparent outside the circle).

### D) Keep object, replace only the background

1. Open the image, click the **magic wand** on the **object**.
2. *Selection* tab → **Invert selection** (⌘⇧I) → the background is now
   selected.
3. *Background* tab → pick a colour → **Replace colour**.
4. Save.

---

## 15. Tips & tricks

- **Rough first, then fine:** cut out roughly with AI or magic wand, then
  correct with brush/eraser.
- **Adjust tolerance:** if too much is selected → lower tolerance. If too
  little → raise tolerance or use Shift+click.
- **Remove colour fringe:** after cutting out, apply "Shrink" by 1–2 px in
  the *Selection* tab before removing the background.
- **Step back:** every step is recorded in the history — double-click any
  entry in the **Edit history** (🕘) to jump back to that state.
- **Stuck?** **Restore original** resets the image to its loaded state.

---

## 16. Known limitations

- **Maximum image size: 40 megapixels.** Larger images are rejected.
- The **AI feature** requires the optional component `rembg`. Without it the
  AI button is disabled; all manual tools continue to work.
- The **app bundle** (`BgRemover.app`) is macOS-specific; on Linux the
  application is launched directly. Windows is currently not part of
  the officially tested matrix.

---

## 17. Troubleshooting & log file

If problems arise, check the internal **log file** `bgremover.log`. It is
stored in the app data directory determined by Qt and is created with the
first log entry. The exact path can vary by platform and Qt configuration:

- **macOS (current configuration):**
  `~/Library/Application Support/BgRemover/BgRemover/bgremover.log`
- **Linux:** below `~/.local/share/`

The macOS app bundle launcher additionally writes startup diagnostics to
`~/Library/Application Support/BgRemover/bgremover.log`.

The internal file contains runtime messages and error details (stack traces)
and is the first port of call for support requests.

The easiest way to find the file is via `Extras → Settings… → Log file`:
the full path is shown there, and the **"Open folder"** button opens the
directory directly in the file manager — ideal for attaching the log file
to a support email.

| Problem | Possible solution |
|---|---|
| AI button greyed out | `rembg` is not installed – see installation guide |
| Image cannot be opened | Over 40 megapixels? Format supported? Read the status bar |
| AI takes very long | First call loads the model – one-time only, faster afterwards |
| Transparency gone after saving | Saved as JPEG → choose PNG/WebP/TIFF instead |

---

## 18. License

BgRemover is released under the **GNU General Public License v3.0 or later**
(`GPL-3.0-or-later`) – see [LICENSE](../../../LICENSE). A complete list of
all libraries used and their licences is in [RESOURCES.md](RESOURCES.md).

---

*This guide is part of the BgRemover project. For questions or suggestions,
please open an issue in the GitHub repository.*
