# Linux packaging — BgRemover

Ships BgRemover to Linux as self-contained, no-`pip`/no-venv artifacts,
analogous to the macOS `.app` bundle:

- **AppImage** (primary) — one portable file that runs on Debian/Ubuntu, Fedora
  and Raspberry Pi OS.
- **`.deb`** (second format) — wraps the AppImage for apt users (menu
  integration, clean install/remove on Debian/Ubuntu/Raspberry Pi OS).

A GitHub Actions **release workflow** builds both for **x86_64 and aarch64**
(Raspberry Pi OS / arm64) on every `v*` tag and attaches them to the release.
The same workflow also builds the macOS `.dmg` (Apple Silicon/arm64) — see
[`../mac/README.md`](../mac/README.md).

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

Outputs land in `build/appimage/BgRemover-<version>-<platform-tag>[-ai].AppImage`
and `build/deb/BgRemover-<version>-<platform-tag>[-ai].deb`, where
`<platform-tag>` is `linux-x86_64` or `linux-raspberrypi-arm64` — an explicit
OS+device tag instead of a bare architecture, so it can't be confused with the
macOS `.dmg`'s `arm64` (#584). `-ai` is only appended when the build actually
bundles rembg/onnxruntime.

`build_appimage.sh` applies the committed
`requirements/constraints.txt` snapshot to both its own `pip` calls and the
dependency resolver run by `python-appimage`. The build stops if that file is
missing. Set `PIP_CONSTRAINT=/path/to/constraints.txt` only when intentionally
testing a different dependency snapshot.

## Architectures / Raspberry Pi OS

`uname -m` selects the architecture automatically: `x86_64` and `aarch64`
(Raspberry Pi OS 64-bit) are supported. The artifact filename's
`<platform-tag>` is `linux-x86_64` / `linux-raspberrypi-arm64`; the `.deb`'s
internal `Architecture:` control field still uses the Debian codes `amd64` /
`arm64` that apt expects (independent of the human-readable filename). The
release workflow builds both on native runners (`ubuntu-24.04` and
`ubuntu-24.04-arm`), so no cross-compilation/QEMU is needed.

## Installing

```bash
# AppImage — make executable and run (double-click also works)
chmod +x BgRemover-*-linux-x86_64-ai.AppImage
./BgRemover-*-linux-x86_64-ai.AppImage          # or: ... --appimage-extract-and-run  (no FUSE)

# .deb — apt resolves the FUSE dependency
sudo apt install ./BgRemover-*-linux-x86_64-ai.deb
```

## Release verification (headless smoke launch)

Building the AppImage is not enough — `tests/test_app_smoke.py` only launches the
**source** app (`python -m bgremover`) and cannot see *frozen-only* failures
(missing metadata → start crash #304, missing `freeze_support()` → fork bomb
#305, a broken bundled AI chain → #306). The release workflow therefore
**launches the freshly built AppImage headlessly** in the `build` job, gated
before `publish` (`needs: build`):

- **Start + fork-bomb guard (#307):** `scripts/smoke_launch.py` runs
  `BgRemover-*.AppImage --appimage-extract-and-run` with
  `QT_QPA_PLATFORM=offscreen` + `BGREMOVER_SMOKE_TEST=1` (the app self-quits after
  the first event-loop tick) and fails on a non-zero exit (start crash) or a
  timeout (a non-terminating launch). The job first installs the Qt runtime libs
  the `offscreen` plugin links (`libegl1 libgl1 libfontconfig1 libxkbcommon0
  libdbus-1-3`) — without them the bundled Qt aborts with `libGL.so.1: cannot
  open shared object file`.
- **AI self-check (#308):** for `--ai` builds the workflow runs the AppImage once
  with `BGREMOVER_AI_SELFCHECK=1`. That spawns the real inference child via
  `spawn` and imports the full `rembg` chain (resolving the `pymatting` metadata
  from #306) — **no** model download, **no** network. Exit 0/non-zero.

## Release notes (from the CHANGELOG)

The GitHub Release **body** is derived from the matching `CHANGELOG.md` section,
not from a hardcoded string (#311). On a `vX.Y.Z` tag the `publish` job runs
`scripts/extract_release_notes.py X.Y.Z`, which extracts everything between the
`## [X.Y.Z]` heading and the next `## [` heading and passes it via `--notes-file`
to `gh release create` (new release) **or** `gh release edit` (reuse of an
existing release — e.g. on a re-run, so a corrected body actually lands).

If no `## [X.Y.Z]` section exists for the tag, the script exits non-zero and the
`publish` job fails loudly — there is **no** silent generic fallback. So before
tagging a release, add its dated `## [X.Y.Z] – YYYY-MM-DD` section to
`CHANGELOG.md` (and mirror it in `docs/i18n/*/CHANGELOG.md`).

To backfill the body of an already-published release by hand, run the same
extraction locally and feed it to `gh`:

```bash
python3 scripts/extract_release_notes.py 2.4.1 > /tmp/notes.md
gh release edit v2.4.1 --notes-file /tmp/notes.md
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
