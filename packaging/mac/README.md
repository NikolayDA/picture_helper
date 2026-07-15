# macOS packaging — BgRemover

Ships BgRemover to macOS as a self-contained, no-`pip`/no-venv artifact — the
counterpart to the Linux [AppImage](../linux/README.md):

- **`.dmg`** containing a relocatable **`BgRemover.app`** bundle built with
  [PyInstaller](https://pyinstaller.org/). The bundle ships its own CPython plus
  PyQt6/Pillow/numpy (and, with `--ai`, `rembg`/`onnxruntime`), so it runs
  without a system Python install.

The GitHub Actions **release workflow** builds the `.dmg` on a native Apple
Silicon runner as one leg of the cross-platform `build` matrix and attaches it
to the GitHub Release on every `v*` tag, next to the Linux artifacts. See
[`../../.github/workflows/release-linux.yml`](../../.github/workflows/release-linux.yml).

> **Architecture:** the build is **arm64-only** (Apple Silicon, macOS 11+).
> Intel Macs are not produced yet.

> **Signing:** the bundle is currently **unsigned** (only ad-hoc `codesign -s -`
> so Gatekeeper does not flag the arm64 app as "damaged"). It is **not**
> Developer-ID signed or notarized, so on first launch users open it once via
> **right-click → Open**. Developer-ID signing + notarization can be added later
> without changing the build itself.

## Files

| File | Purpose |
|------|---------|
| `bgremover_launcher.py` | PyInstaller entry point (calls `bgremover.app:main`) |
| `bgremover.spec` | PyInstaller spec: `BgRemover.app` bundle id, icon, version, document types, optional AI collection |
| `build_macos.sh` | Builds `BgRemover.app` via PyInstaller and wraps it into a `.dmg` |

The application id `de.bgremover.app` matches the Linux packaging and the
existing macOS bundle identifier. The icon source is the repository-root
`BgRemover_icon.png` (converted to `.icns` via `iconutil`).

## Building locally

Build on an Apple Silicon Mac with the Xcode command line tools installed
(`iconutil`, `hdiutil`, `codesign`). Needs `python3` + `pip` and network access:

```bash
# GUI only (smaller); add --ai to also bundle rembg/onnxruntime
./packaging/mac/build_macos.sh --ai
```

The output lands in `build/macos/BgRemover-<version>-macos-arm64[-ai].dmg` — an
explicit OS+device tag rather than a bare architecture, since a lone `arm64`
could otherwise be confused with the Linux/Raspberry-Pi `.deb` of the same
name; `-ai` is only appended when `--ai` actually bundles rembg/onnxruntime
(#584). Like the Linux build, the script applies the committed
`requirements/constraints.txt` snapshot to its `pip` calls; set
`PIP_CONSTRAINT=/path/to/constraints.txt` only when intentionally testing a
different dependency snapshot.

## Installing

```bash
# Mount the .dmg (double-click) and drag BgRemover.app to Applications, then:
# first launch only — right-click the app -> Open (unsigned build), confirm once.
xattr -dr com.apple.quarantine /Applications/BgRemover.app   # alternative to right-click
```

## Relationship to `create_BgRemover_app.sh`

The repository-root `create_BgRemover_app.sh` builds a `.app` **locally** around
a per-user virtual environment and still requires a Python install on the user's
machine. This packaging instead produces a **downloadable, self-contained**
`.dmg` (bundled Python) that needs nothing pre-installed — the same philosophy as
the Linux AppImage.

## Release verification (headless smoke launch)

Building a bundle is not enough — `tests/test_app_smoke.py` only launches the
**source** app (`python -m bgremover`) and cannot see *frozen-only* failures:
missing `*.dist-info` metadata (start crash #304), a missing `freeze_support()`
(fork bomb #305) or a broken bundled AI chain (#306). The release workflow
therefore **launches the freshly built `BgRemover.app` headlessly** in the
`build` job, gated before `publish` (`needs: build`), so a bad bundle is never
released:

- **Start + fork-bomb guard (#307):** `scripts/smoke_launch.py` starts the app
  with `QT_QPA_PLATFORM=offscreen` + `BGREMOVER_SMOKE_TEST=1` (the app self-quits
  after the first event-loop tick) and fails on a non-zero exit (start crash), on
  a process-count explosion of the bundle binary (fork bomb — the macOS `.dmg`
  was the original vector) or on a timeout (the "endless windows" symptom).
- **AI self-check (#308):** for `--ai` builds the workflow runs the app once with
  `BGREMOVER_AI_SELFCHECK=1`. That spawns the real inference child process via
  `spawn` and imports the full `rembg` chain (resolving the `pymatting`
  `*.dist-info` metadata that #306 was missing) — **no** model download, **no**
  network. Exit 0 on success, non-zero with the error otherwise.

The `--ai` smoke launch deliberately allows a few concurrent bundle instances
(the legitimate AI warmup child plus the multiprocessing resource tracker); a
real fork bomb grows explosively past that and is caught immediately.

## Validation

`tests/test_macos_packaging.py` runs in normal PR CI **without external tools**:
it keeps the spec, the build script and the release workflow self-consistent and
in sync with the project (app id, version source, the arm64 target, AI bundling
and the `.dmg` artifact name). `tests/test_smoke_launch.py`,
`tests/test_ai_selfcheck.py` and `tests/test_release_smoke.py` cover the
watchdog launcher, the AI self-check and the workflow wiring.
