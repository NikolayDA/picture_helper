"""Tests für das gehärtete Qt-Plugin-Staging.

Geprüft werden die drei Sicherheitsanforderungen:
* nutzerspezifisches ``0700``-Staging-Verzeichnis (kein welt-schreibbarer,
  vorhersagbarer Pfad → kein Pre-Seeding fremder Plugin-Dylibs),
* Inhalts-(SHA-256-)Vergleich statt reinem Größenvergleich,
* eindeutige Zwischendatei statt festem ``.tmp``-Namen.

Reine Dateisystem-Logik – keine QApplication nötig.
"""
from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from bgremover import qt_plugins

_POSIX = os.name == "posix"


# ── _secure_stage_root ─────────────────────────────────────────────────

def test_secure_stage_root_creates_0700_versioned_dir(tmp_path):
    staged = qt_plugins._secure_stage_root(tmp_path, "6_9_9")
    assert staged is not None
    assert staged.is_dir()
    assert staged.name == "6_9_9"
    root = staged.parent
    # Verzeichnisname trägt die UID → pro Nutzer getrennt.
    if _POSIX:
        assert root.name == f"bgremover_qt_plugins_{os.geteuid()}"
        assert stat.S_IMODE(root.stat().st_mode) == 0o700
        assert stat.S_IMODE(staged.stat().st_mode) == 0o700


@pytest.mark.skipif(not _POSIX, reason="POSIX-Rechtemodell erforderlich")
def test_secure_stage_root_rejects_world_writable_root(tmp_path):
    """Ein bereits vorhandenes, zu offenes Staging-Root wird abgelehnt."""
    uid = os.geteuid()
    root = tmp_path / f"bgremover_qt_plugins_{uid}"
    root.mkdir(mode=0o777)
    os.chmod(root, 0o777)  # welt-schreibbar – mkdir-mode wird von umask maskiert
    # chmod im Code zieht auf 0700 nach; danach ist es sicher und wird
    # akzeptiert. Prüfe, dass das Ergebnis NICHT welt-schreibbar bleibt.
    staged = qt_plugins._secure_stage_root(tmp_path, "v1")
    assert staged is not None
    assert stat.S_IMODE(root.stat().st_mode) == 0o700


@pytest.mark.skipif(not _POSIX, reason="POSIX-Symlink-Semantik erforderlich")
def test_secure_dir_rejects_symlink(tmp_path):
    real = tmp_path / "real"
    real.mkdir(mode=0o700)
    link = tmp_path / "link"
    link.symlink_to(real)
    # Symlink (auch auf ein sicheres Ziel) gilt als unsicher.
    assert qt_plugins._secure_dir(link) is False
    assert qt_plugins._secure_dir(real) is True


@pytest.mark.skipif(not _POSIX, reason="POSIX-Rechtemodell erforderlich")
def test_secure_dir_rejects_group_or_other_permissions(tmp_path):
    d = tmp_path / "d"
    d.mkdir(mode=0o700)
    os.chmod(d, 0o750)  # Gruppenrechte → unsicher
    assert qt_plugins._secure_dir(d) is False


# ── _copy_if_needed: Inhaltsvergleich + eindeutige Temp-Datei ──────────

def test_copy_if_needed_copies_when_absent(tmp_path):
    src = tmp_path / "src.bin"
    src.write_bytes(b"hello-plugin")
    dst = tmp_path / "dst.bin"
    qt_plugins._copy_if_needed(src, dst)
    assert dst.read_bytes() == b"hello-plugin"


def test_copy_if_needed_refreshes_on_content_change_same_size(tmp_path):
    """Gleiche Größe, anderer Inhalt: muss neu kopiert werden."""
    src = tmp_path / "src.bin"
    dst = tmp_path / "dst.bin"
    src.write_bytes(b"AAAA")
    dst.write_bytes(b"BBBB")  # identische Länge, anderer Inhalt
    qt_plugins._copy_if_needed(src, dst)
    assert dst.read_bytes() == b"AAAA"


def test_copy_if_needed_skips_identical_content(tmp_path):
    src = tmp_path / "src.bin"
    dst = tmp_path / "dst.bin"
    src.write_bytes(b"same-bytes")
    dst.write_bytes(b"same-bytes")
    mtime_before = dst.stat().st_mtime_ns
    qt_plugins._copy_if_needed(src, dst)
    # Inhalt gleich → kein Rewrite (mtime unverändert).
    assert dst.stat().st_mtime_ns == mtime_before


def test_copy_if_needed_leaves_no_temp_files(tmp_path):
    src = tmp_path / "src.bin"
    src.write_bytes(b"payload")
    dst = tmp_path / "platforms" / "libqcocoa.bin"
    dst.parent.mkdir()
    qt_plugins._copy_if_needed(src, dst)
    # Nur die Zieldatei bleibt übrig – keine .tmp-/mkstemp-Reste.
    assert [p.name for p in dst.parent.iterdir()] == ["libqcocoa.bin"]


# ── _stage_platform_plugins (Ende-zu-Ende, ohne Qt) ────────────────────

def test_stage_platform_plugins_round_trip(tmp_path, monkeypatch):
    # Original-Layout: <pkg>/Qt6/{plugins/platforms,lib} – wie bei PyQt6.
    qt6 = tmp_path / "Qt6"
    plugins = qt6 / "plugins" / "platforms"
    plugins.mkdir(parents=True)
    (plugins / "libqoffscreen.so").write_bytes(b"\x7fELF-fake")
    (plugins / "libqxcb.so").write_bytes(b"\x7fELF-fake-2")
    real_lib = qt6 / "lib"
    real_lib.mkdir()
    (real_lib / "libQt6XcbQpa.so.6").write_bytes(b"\x7fELF-lib")

    staged_base = tmp_path / "tmp"
    staged_base.mkdir()
    monkeypatch.setattr(qt_plugins.tempfile, "gettempdir", lambda: str(staged_base))
    # Den macOS-/private/tmp-Zweig neutralisieren, damit der Test plattform-
    # unabhängig die gettempdir-Basis nutzt.
    monkeypatch.setattr(qt_plugins.sys, "platform", "linux")

    result = qt_plugins._stage_platform_plugins(plugins)
    assert result is not None
    staged_plugins, staged_platforms = result
    names = sorted(p.name for p in staged_platforms.iterdir())
    assert names == ["libqoffscreen.so", "libqxcb.so"]
    assert (staged_platforms / "libqxcb.so").read_bytes() == b"\x7fELF-fake-2"

    # Das einkompilierte RUNPATH $ORIGIN/../../lib der gestagten Plugins
    # muss auf ein echtes lib-Verzeichnis mit der Original-Bibliothek
    # zeigen, nicht ins Leere laufen (Raspberry-Pi-Regressionsfall).
    resolved_lib = (staged_platforms / ".." / ".." / "lib").resolve()
    assert resolved_lib.is_dir()
    assert (resolved_lib / "libQt6XcbQpa.so.6").read_bytes() == b"\x7fELF-lib"
    assert staged_plugins.name == "plugins"


def test_stage_platform_plugins_empty_dir_returns_none(tmp_path):
    plugins = tmp_path / "platforms"
    plugins.mkdir()
    assert qt_plugins._stage_platform_plugins(plugins) is None


def test_stage_platform_plugins_aborts_when_root_insecure(tmp_path, monkeypatch):
    """Lässt sich das Staging-Root nicht absichern, unterbleibt das Staging
    (Rückgabe None) – der Aufrufer nutzt dann den Original-Pluginpfad."""
    plugins = tmp_path / "platforms"
    plugins.mkdir()
    (plugins / "libqxcb.so").write_bytes(b"x")
    monkeypatch.setattr(qt_plugins.tempfile, "gettempdir", lambda: str(tmp_path))
    monkeypatch.setattr(qt_plugins.sys, "platform", "linux")
    monkeypatch.setattr(qt_plugins, "_secure_stage_root", lambda *a: None)
    assert qt_plugins._stage_platform_plugins(plugins) is None


def test_stage_platform_plugins_aborts_when_lib_symlink_fails(tmp_path, monkeypatch):
    """Scheitert der RUNPATH-Symlink, wird das Staging verworfen statt einen
    Baum mit fehlendem lib-Ziel als nutzbar zu melden (Codex-Review-Fund
    #631)."""
    qt6 = tmp_path / "Qt6"
    plugins = qt6 / "plugins" / "platforms"
    plugins.mkdir(parents=True)
    (plugins / "libqxcb.so").write_bytes(b"x")
    (qt6 / "lib").mkdir()

    monkeypatch.setattr(qt_plugins.tempfile, "gettempdir", lambda: str(tmp_path / "tmp"))
    (tmp_path / "tmp").mkdir()
    monkeypatch.setattr(qt_plugins.sys, "platform", "linux")
    monkeypatch.setattr(qt_plugins, "_ensure_lib_symlink", lambda *a: False)

    assert qt_plugins._stage_platform_plugins(plugins) is None


def test_stage_platform_plugins_isolates_concurrent_sources(tmp_path, monkeypatch):
    """Zwei gleichzeitig 'laufende' Instanzen derselben Qt6-Version, aber aus
    unterschiedlichen Quellpfaden (z. B. zwei parallel gemountete AppImages),
    dürfen sich nicht denselben Qt6/lib-Symlink teilen – sonst überschreibt
    eine Instanz den RUNPATH-Ziel-Symlink der anderen (Codex-Review-Fund
    #631)."""
    staged_base = tmp_path / "tmp"
    staged_base.mkdir()
    monkeypatch.setattr(qt_plugins.tempfile, "gettempdir", lambda: str(staged_base))
    monkeypatch.setattr(qt_plugins.sys, "platform", "linux")
    monkeypatch.setattr(qt_plugins, "_dist_version", lambda name: "6_7_3")

    def _make_source(name: str) -> Path:
        qt6 = tmp_path / name / "Qt6"
        plugins = qt6 / "plugins" / "platforms"
        plugins.mkdir(parents=True)
        (plugins / "libqxcb.so").write_bytes(name.encode())
        real_lib = qt6 / "lib"
        real_lib.mkdir()
        (real_lib / "libQt6XcbQpa.so.6").write_bytes(name.encode())
        return plugins

    plugins_a = _make_source("mount_a")
    plugins_b = _make_source("mount_b")

    result_a = qt_plugins._stage_platform_plugins(plugins_a)
    result_b = qt_plugins._stage_platform_plugins(plugins_b)
    assert result_a is not None and result_b is not None
    staged_plugins_a, staged_platforms_a = result_a
    staged_plugins_b, staged_platforms_b = result_b

    # Unterschiedliche Quellen -> getrennte Staging-Bäume, kein gemeinsamer
    # Qt6/lib-Symlink, der sich gegenseitig überschreiben könnte.
    assert staged_plugins_a.parent != staged_plugins_b.parent

    lib_a = (staged_platforms_a / ".." / ".." / "lib").resolve()
    lib_b = (staged_platforms_b / ".." / ".." / "lib").resolve()
    assert (lib_a / "libQt6XcbQpa.so.6").read_bytes() == b"mount_a"
    assert (lib_b / "libQt6XcbQpa.so.6").read_bytes() == b"mount_b"


# ── _ensure_lib_symlink (RUNPATH-Regression) ───────────────────────────

@pytest.mark.skipif(not _POSIX, reason="POSIX-Symlink-Semantik erforderlich")
def test_ensure_lib_symlink_creates_link(tmp_path):
    staged_qt6 = tmp_path / "staged" / "Qt6"
    staged_qt6.mkdir(parents=True)
    real_lib = tmp_path / "real" / "lib"
    real_lib.mkdir(parents=True)
    (real_lib / "libQt6XcbQpa.so.6").write_bytes(b"lib-bytes")

    assert qt_plugins._ensure_lib_symlink(staged_qt6, real_lib) is True

    link = staged_qt6 / "lib"
    assert link.is_symlink()
    assert Path(os.readlink(link)) == real_lib
    assert (link / "libQt6XcbQpa.so.6").read_bytes() == b"lib-bytes"


@pytest.mark.skipif(not _POSIX, reason="POSIX-Symlink-Semantik erforderlich")
def test_ensure_lib_symlink_refreshes_stale_link(tmp_path):
    """Ein Symlink von einer älteren Qt6-Version wird auf das aktuelle
    lib-Verzeichnis nachgezogen, statt veraltet stehen zu bleiben."""
    staged_qt6 = tmp_path / "staged" / "Qt6"
    staged_qt6.mkdir(parents=True)
    old_lib = tmp_path / "old" / "lib"
    old_lib.mkdir(parents=True)
    (staged_qt6 / "lib").symlink_to(old_lib)

    new_lib = tmp_path / "new" / "lib"
    new_lib.mkdir(parents=True)
    (new_lib / "libQt6XcbQpa.so.6").write_bytes(b"new-lib")

    assert qt_plugins._ensure_lib_symlink(staged_qt6, new_lib) is True

    link = staged_qt6 / "lib"
    assert Path(os.readlink(link)) == new_lib
    assert (link / "libQt6XcbQpa.so.6").read_bytes() == b"new-lib"


@pytest.mark.skipif(not _POSIX, reason="POSIX-Symlink-Semantik erforderlich")
def test_ensure_lib_symlink_noop_when_already_current(tmp_path):
    staged_qt6 = tmp_path / "staged" / "Qt6"
    staged_qt6.mkdir(parents=True)
    real_lib = tmp_path / "real" / "lib"
    real_lib.mkdir(parents=True)
    link = staged_qt6 / "lib"
    link.symlink_to(real_lib)

    # Darf keinen Fehler werfen und den bestehenden, korrekten Link nicht
    # anfassen (keine neue mkstemp-Zwischendatei nötig).
    assert qt_plugins._ensure_lib_symlink(staged_qt6, real_lib) is True
    assert sorted(p.name for p in staged_qt6.iterdir()) == ["lib"]


def test_ensure_lib_symlink_skips_missing_real_lib(tmp_path):
    """Kein ``lib``-Verzeichnis in der Quelle (z. B. manche macOS-Layouts) ist
    kein Fehler – das RUNPATH-Problem betrifft nur ELF-Plugins."""
    staged_qt6 = tmp_path / "staged" / "Qt6"
    staged_qt6.mkdir(parents=True)
    missing_lib = tmp_path / "does-not-exist"

    assert qt_plugins._ensure_lib_symlink(staged_qt6, missing_lib) is True

    assert list(staged_qt6.iterdir()) == []


@pytest.mark.skipif(not _POSIX, reason="POSIX-Symlink-Semantik erforderlich")
def test_ensure_lib_symlink_reports_failure_when_symlink_cannot_be_created(tmp_path, monkeypatch):
    """Scheitert die Symlink-Erstellung (z. B. kein Symlink-Support), muss
    der Aufrufer das erfahren, statt einen kaputten Baum als gültig
    zu erhalten (Codex-Review-Fund #631)."""
    staged_qt6 = tmp_path / "staged" / "Qt6"
    staged_qt6.mkdir(parents=True)
    real_lib = tmp_path / "real" / "lib"
    real_lib.mkdir(parents=True)

    def _boom(*args, **kwargs):
        raise OSError("no symlink support")

    monkeypatch.setattr(qt_plugins.os, "symlink", _boom)
    assert qt_plugins._ensure_lib_symlink(staged_qt6, real_lib) is False
    # Keine Zwischendatei bleibt zurück.
    assert list(staged_qt6.iterdir()) == []
