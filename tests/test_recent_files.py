"""Tests für Recent-Files und Quick-Save (A5 + A9).

QSettings wird per ``setPath`` auf ein temporäres Verzeichnis umgeleitet,
damit die Tests nicht den realen Nutzer-Cache verändern.
"""
from pathlib import Path

import pytest
from PIL import Image
from PyQt6.QtCore import QSettings


@pytest.fixture
def isolated_settings(tmp_path, monkeypatch):
    """Isoliert QSettings in einem temporären Verzeichnis."""
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(QSettings.Format.IniFormat,
                      QSettings.Scope.UserScope, str(tmp_path))
    yield tmp_path


# ── A9: Recent-Files ────────────────────────────────────────────────────

def test_recent_list_dedups_and_caps(qapp, isolated_settings):
    from BgRemover import MainWindow
    w = MainWindow()
    # Erst Liste explizit leeren (in case)
    w._settings.setValue(MainWindow.SETTINGS_RECENT_KEY, [])
    for i in range(12):
        w._add_recent(str(isolated_settings / f"img{i}.png"))
    paths = w._recent_paths()
    assert len(paths) == MainWindow.RECENT_MAX
    # Letzter eingefügter Eintrag steht vorn
    assert Path(paths[0]).name == "img11.png"


def test_recent_brings_existing_to_front(qapp, isolated_settings):
    from BgRemover import MainWindow
    w = MainWindow()
    w._settings.setValue(MainWindow.SETTINGS_RECENT_KEY, [])
    a = str(isolated_settings / "a.png")
    b = str(isolated_settings / "b.png")
    w._add_recent(a)
    w._add_recent(b)
    w._add_recent(a)             # a wieder nach vorn
    paths = w._recent_paths()
    assert paths[0] == str(Path(a).resolve())
    # Insgesamt nur 2 Einträge (keine Duplikate)
    assert len(paths) == 2


def test_recent_persists_after_image_load(qapp, isolated_settings, tmp_path):
    from BgRemover import MainWindow
    w = MainWindow()
    w._settings.setValue(MainWindow.SETTINGS_RECENT_KEY, [])
    img_path = tmp_path / "x.png"
    Image.new("RGB", (8, 8), (1, 2, 3)).save(img_path)
    w._canvas.load_image(str(img_path))
    paths = w._recent_paths()
    assert len(paths) == 1
    assert Path(paths[0]).resolve() == img_path.resolve()


# ── A5: Quick-Save ──────────────────────────────────────────────────────

def test_quick_save_writes_to_known_path(qapp, isolated_settings, tmp_path):
    from BgRemover import MainWindow
    w = MainWindow()
    w._canvas._pil = Image.new("RGBA", (8, 8), (10, 20, 30, 255))
    target = tmp_path / "out.png"
    w._save_path = str(target)
    w._save()
    assert target.exists()


def test_load_clears_save_path(qapp, isolated_settings, tmp_path):
    from BgRemover import MainWindow
    w = MainWindow()
    w._save_path = "/tmp/somewhere.png"
    img_path = tmp_path / "fresh.png"
    Image.new("RGB", (8, 8), (1, 2, 3)).save(img_path)
    w._canvas.load_image(str(img_path))
    assert w._save_path is None
