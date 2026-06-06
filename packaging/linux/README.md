# Linux packaging — BgRemover

Ships BgRemover to Linux as self-contained, no-`pip`/no-venv artifacts,
analogous to the macOS `.app` bundle:

- **AppImage** (primary) — one portable file that runs on Debian/Ubuntu, Fedora
  and Raspberry Pi OS.
- **`.deb`** (second format) — wraps the AppImage for apt users (menu
  integration, clean install/remove on Debian/Ubuntu/Raspberry Pi OS).

A GitHub Actions **release workflow** builds both for **x86_64 and aarch64**
(Raspberry Pi OS / arm64) on every `v*` tag and attaches them to the release.

> **Status:** AppImage, `.deb`, aarch64/Pi builds and release publishing are
> implemented and covered by smoke tests.

## Files

| File | Purpose |
|------|---------|
| `de.bgremover.app.desktop` | Freedesktop desktop entry (menu item, icon, MIME types) |
| `de.bgremover.app.metainfo.xml` | AppStream metadata (software centers, release info) |
| `build_appimage.sh` | Builds the AppImage via `python-appimage` |
| `build_deb.sh` | Wraps a built AppImage into a `.deb` |
| `../../.github/workflows/release-linux.yml` | Builds + publishes both, per arch |

The application id `de.bgremover.app` matches the macOS bundle identifier and is
used identically as the desktop-file id, the AppStream component id and the icon
name. The icon source is the repository-root `BgRemover_icon.png`.

## Building locally

Build on a Linux host of the **same architecture** you target (build the Pi
variant on a Pi or an arm64 host). Needs `python3` + `pip` and network access:

```bash
# 1) AppImage (GUI only; add --ai to also bundle rembg, or PYVER=3.12 to choose Python)
./packaging/linux/build_appimage.sh

# 2) .deb wrapping the AppImage just built (needs dpkg-dev)
./packaging/linux/build_deb.sh
```

Outputs land in `build/appimage/BgRemover-<version>-<arch>.AppImage` and
`build/deb/BgRemover-<version>-<arch>.deb`.

`build_appimage.sh` applies the committed
`requirements/constraints.txt` snapshot to both its own `pip` calls and the
dependency resolver run by `python-appimage`. The build stops if that file is
missing. Set `PIP_CONSTRAINT=/path/to/constraints.txt` only when intentionally
testing a different dependency snapshot.

## Architectures / Raspberry Pi OS

`uname -m` selects the architecture automatically: `x86_64` and `aarch64`
(Raspberry Pi OS 64-bit) are supported; the `.deb` maps these to `amd64` /
`arm64`. The release workflow builds both on native runners
(`ubuntu-24.04` and `ubuntu-24.04-arm`), so no cross-compilation/QEMU is needed.

## Installing

```bash
# AppImage — make executable and run (double-click also works)
chmod +x BgRemover-*-x86_64.AppImage
./BgRemover-*-x86_64.AppImage          # or: ... --appimage-extract-and-run  (no FUSE)

# .deb — apt resolves the FUSE dependency
sudo apt install ./BgRemover-*-amd64.deb
```

## Validation

`tests/test_linux_packaging.py` runs in normal PR CI **without external tools**:
it keeps the desktop entry, AppStream metadata, the build scripts and the
release workflow self-consistent and in sync with the project (app id, license,
version, the `bgremover` entry point), and — where `dpkg-deb` is available —
actually builds a `.deb` from a stub AppImage and inspects it. To additionally
lint with the upstream validators (optional, not required by CI):

```bash
desktop-file-validate packaging/linux/de.bgremover.app.desktop
appstreamcli validate  packaging/linux/de.bgremover.app.metainfo.xml
```
