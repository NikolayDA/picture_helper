[Deutsch](../../../INSTALL_MAC.md) · **English** · [Español](../es/INSTALL_MAC.md) · [Français](../fr/INSTALL_MAC.md) · [Українська](../uk/INSTALL_MAC.md) · [简体中文](../zh/INSTALL_MAC.md)

# BgRemover – Installation on the Mac

A quick guide to installing and starting BgRemover from GitHub —
both from the `main` branch and from a feature branch (e.g.
to test an open pull request before merging).

## Requirements

- **macOS**
- **Python 3.10 or newer** — check with:
  ```bash
  python3 --version
  ```
- **git**

If Python or git are missing, the easiest way is via [Homebrew](https://brew.sh):
```bash
brew install python git
```

## Quick start from `main`

**Recommended** is the app bundle script — it automatically creates an
isolated venv, installs all dependencies (including
`onnxruntime` for the AI), handles Apple Silicon correctly, and copies
the toolbar icons into the bundle:

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
bash create_BgRemover_app.sh
```

Confirm the venv prompt with **Enter**; afterwards, double-click
`BgRemover.app` under `~/Applications` to start it.

**Direct terminal start** — on modern macOS in a venv, since
system Python blocks `pip install` via PEP 668:

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install -e ".[ai]"
python3 BgRemover.py
```

- `.[ai]` installs `rembg[cpu]` including `onnxruntime` (AI background removal).
- Without the AI feature, this is sufficient: `python3 -m pip install -e .`

## Start variants

After installation there are three ways to start the program:

| Variant | Command / action | Result |
|----------|-----------------|----------|
| **A – macOS app (recommended)** | `bash create_BgRemover_app.sh` | Creates an isolated venv, installs all dependencies (including `onnxruntime`), copies the icons, and produces a standalone `BgRemover.app` under `~/Applications`. Quarantine is removed automatically; the project may stay in `~/Documents`. |
| **B – Double-click** | double-click `BgRemover.command` in the Finder | Starts in a terminal window; automatically uses the app venv created by the script (the file is already executable). |
| **C – Terminal** | in a venv: `python3 BgRemover.py` | Direct start (for venv setup see Quick start above). |

## Installation from a branch (testing open PRs)

PR branch names are listed in the respective pull request on GitHub
("… wants to merge … from **`<branch>`**").

**Variant 1 – in the existing clone directory:**
```bash
cd picture_helper
git fetch origin
git branch -r                       # show available branches
git checkout <branch>
# in a venv (see Quick start); only needed if dependencies have changed:
python3 -m pip install -e ".[ai]"
python3 BgRemover.py
```

Alternatively, you can also simply run `bash create_BgRemover_app.sh`
on a branch — this handles the venv and dependencies automatically.

**Variant 2 – cloning a branch directly:**
```bash
git clone --branch <branch-name> \
  https://github.com/NikolayDA/picture_helper.git
```

## Updating / switching branch

```bash
git checkout main && git pull          # latest main version
git checkout <branch> && git pull      # update a specific branch
```

The editable install (`pip install -e`) does **not** need to be run
again after `git pull` — unless the dependencies in
`pyproject.toml` have changed.

## Troubleshooting

- **App does not start / double-click does nothing** → Since v3 the
  app shows an error dialog with "Open log". The most common cause:
  `PyQt6` is not installed in the Python that the app uses
  (e.g. because `pip install` went into a venv or a different Python,
  or Homebrew Python blocks `pip install` via PEP 668). Solution:
  run `bash create_BgRemover_app.sh` again and let it create the venv
  (confirm the prompt with Enter) — the script then installs the
  dependencies into a venv under
  `~/Library/Application Support/BgRemover/venv` and bakes this Python
  into the app.
- **`[Errno 1] Operation not permitted` when opening `BgRemover.py`**
  → macOS privacy (TCC). If the project is in `~/Documents`,
  `~/Desktop`, `~/Downloads`, or iCloud Drive, an `.app` started from
  the Finder is not allowed to read there. Since v3 this is resolved:
  `BgRemover.py` is copied into the app bundle and the venv is located in
  Application Support — run `bash create_BgRemover_app.sh` once more.
  (Alternatively, move the project to e.g. `~/picture_helper`
  and run the script there again.)
- **`numpy ... incompatible architecture (have 'arm64', need 'x86_64')`**
  → Apple Silicon: an architecture-foreign package is located in
  `~/Library/Python/...` that "bleeds through" into a mismatched Python.
  Since v3.1 this is resolved: the launcher sets `PYTHONNOUSERSITE=1`
  (user-site is ignored), enforces the native CPU architecture, and an
  isolated venv is mandatorily used. Solution: best to first install a
  native Python, then rebuild:
  ```bash
  brew install python
  bash create_BgRemover_app.sh   # confirm the venv prompt with Enter
  ```
- **See the error directly (manual diagnosis)** → Start the launcher in
  the terminal, then the real error message appears:
  ```bash
  ~/Applications/BgRemover.app/Contents/MacOS/BgRemover
  ```
  Expected with missing packages: `ModuleNotFoundError: No module named 'PyQt6'`.
- **"python3: command not found"** → `brew install python`
- **pip error during installation** → first update pip:
  ```bash
  python3 -m pip install --upgrade pip
  ```
  then run the install command again.
- **First AI click takes a long time** → On the very first time, `rembg`
  downloads its model (a few hundred MB, one-time, cached in
  `~/.u2net`). The status bar shows "🤖 KI-Modell wird geladen…"
  and then "🤖 KI bereit".
- **Gatekeeper: "unverified developer"** → Right-click on
  `BgRemover.app` → **Open**. The build script already removes the
  quarantine via `xattr`; a right-click open is enough in any
  case nonetheless.
- **App crashes with "No onnxruntime backend found"** → Newer
  `rembg` versions no longer ship the backend. Currently fixed
  (the `ai` extra pulls in `rembg[cpu]`/`onnxruntime`; if it is still
  missing, the app starts without AI instead of crashing). Solution: run
  `bash create_BgRemover_app.sh` once to rebuild — or install it afterwards into the venv:
  `"~/Library/Application Support/BgRemover/venv/bin/python3" -m pip install "rembg[cpu]"`.
- **`.app` looks different from `BgRemover.command`** → Older bundle
  without toolbar icons (the app used drawn fallback icons). Currently
  fixed — the script copies `icons/` into the bundle; run
  `bash create_BgRemover_app.sh` once to rebuild.
- **Diagnosing errors** → Check the log file `~/.bgremover.log`.
