# Linux packaging — BgRemover

Foundation for shipping BgRemover to Linux as a portable **AppImage** — a
single self-contained file that runs on Debian/Ubuntu, Fedora and Raspberry Pi
OS without a venv or `pip`, analogous to the macOS `.app` bundle.

> **Scope (PR 5 — foundation):** target artifact decided (AppImage), desktop
> entry + AppStream metadata + icon, a reproducible build script, and a CI
> smoke test that validates the metadata. Building the artifact in release CI,
> the Raspberry Pi (aarch64) variant and an optional second package format are
> the follow-up (**PR 6**).

## Files

| File | Purpose |
|------|---------|
| `de.bgremover.app.desktop` | Freedesktop desktop entry (menu item, icon, MIME types) |
| `de.bgremover.app.metainfo.xml` | AppStream metadata (software centers, release info) |
| `build_appimage.sh` | Builds the AppImage via `python-appimage` |

The application id `de.bgremover.app` matches the macOS bundle identifier and is
used identically as the desktop-file id, the AppStream component id and the icon
name. The icon source is the repository-root `BgRemover_icon.png`.

## Building

Run on a Linux host of the **same architecture** you target (build the Pi
variant on a Pi). Needs `python3` + `pip` and network access:

```bash
./packaging/linux/build_appimage.sh          # GUI only (smaller)
./packaging/linux/build_appimage.sh --ai      # also bundle rembg (AI removal; large)
PYVER=3.12 ./packaging/linux/build_appimage.sh
```

The result lands in `build/appimage/BgRemover-<version>-<arch>.AppImage`. Make
it executable and run it (double-click, or from a terminal). On hosts without
FUSE, run with `--appimage-extract-and-run`.

## Validation

`tests/test_linux_packaging.py` keeps the metadata self-consistent and in sync
with the project (app id, license, version, the `bgremover` entry point) and
checks that the desktop entry and AppStream XML are well-formed. It needs no
external tooling, so it runs in the normal PR CI. To additionally lint with the
upstream validators (optional, not required by CI):

```bash
desktop-file-validate packaging/linux/de.bgremover.app.desktop
appstreamcli validate  packaging/linux/de.bgremover.app.metainfo.xml
```
