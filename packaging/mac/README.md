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

The output lands in `build/macos/BgRemover-<version>-arm64.dmg`. Like the Linux
build, the script applies the committed `requirements/constraints.txt` snapshot
to its `pip` calls; set `PIP_CONSTRAINT=/path/to/constraints.txt` only when
intentionally testing a different dependency snapshot.

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

## Validation

`tests/test_macos_packaging.py` runs in normal PR CI **without external tools**:
it keeps the spec, the build script and the release workflow self-consistent and
in sync with the project (app id, version source, the arm64 target, AI bundling
and the `.dmg` artifact name).
