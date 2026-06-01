"""Tests für das gehärtete Qt-Plugin-Staging (Fix #12).

Geprüft werden die drei Härtungen gegenüber dem früheren Stand:
* nutzerspezifisches ``0700``-Staging-Verzeichnis (kein welt-schreibbarer,
  vorhersagbarer Pfad → kein Pre-Seeding fremder Plugin-Dylibs),
* Inhalts-(SHA-256-)Vergleich statt reinem Größenvergleich,
* eindeutige Zwischendatei statt festem ``.tmp``-Namen.

Reine Dateisystem-Logik – keine QApplication nötig.
"""
from __future__ import annotations

import os
import stat

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
    """Gleiche Größe, anderer Inhalt: muss neu kopiert werden (früher wurde
    nur die Größe verglichen → untergeschobene Datei blieb stehen)."""
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
    plugins = tmp_path / "platforms"
    plugins.mkdir()
    (plugins / "libqoffscreen.so").write_bytes(b"\x7fELF-fake")
    (plugins / "libqxcb.so").write_bytes(b"\x7fELF-fake-2")

    staged_base = tmp_path / "tmp"
    staged_base.mkdir()
    monkeypatch.setattr(qt_plugins.tempfile, "gettempdir", lambda: str(staged_base))
    # Den macOS-/private/tmp-Zweig neutralisieren, damit der Test plattform-
    # unabhängig die gettempdir-Basis nutzt.
    monkeypatch.setattr(qt_plugins.sys, "platform", "linux")

    result = qt_plugins._stage_platform_plugins(plugins)
    assert result is not None
    staged_root, staged_platforms = result
    names = sorted(p.name for p in staged_platforms.iterdir())
    assert names == ["libqoffscreen.so", "libqxcb.so"]
    assert (staged_platforms / "libqxcb.so").read_bytes() == b"\x7fELF-fake-2"


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
