"""Tests für Recent-Files und Quick-Save (A5 + A9).

QSettings wird per ``setPath`` auf ein temporäres Verzeichnis umgeleitet,
damit die Tests nicht den realen Nutzer-Cache verändern.
"""
from pathlib import Path

import pytest
from PIL import Image
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QMenu

from bgremover.recent_files import (
    RECENT_MAX,
    SETTINGS_RECENT_KEY,
    RecentFiles,
    RecentFilesMenu,
)


@pytest.fixture
def isolated_settings(tmp_path, monkeypatch):
    """Isoliert QSettings in einem temporären Verzeichnis."""
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(QSettings.Format.IniFormat,
                      QSettings.Scope.UserScope, str(tmp_path))
    yield tmp_path


# ── A9: Recent-Files ────────────────────────────────────────────────────

def _settings() -> QSettings:
    return QSettings("BgRemover", "BgRemover")


def test_recent_files_helper_dedups_and_caps(isolated_settings):
    recent = RecentFiles(_settings(), limit=3)
    recent.clear()

    a = isolated_settings / "a.png"
    b = isolated_settings / "b.png"
    c = isolated_settings / "c.png"
    d = isolated_settings / "d.png"

    recent.add(str(a))
    recent.add(str(b))
    recent.add(str(c))
    recent.add(str(a))
    paths = recent.add(str(d))

    assert len(paths) == 3
    assert paths[0] == str(d.resolve())
    assert paths[1] == str(a.resolve())
    assert paths[2] == str(c.resolve())


def test_recent_files_helper_removes_missing_entry(isolated_settings):
    recent = RecentFiles(_settings(), limit=5)
    recent.clear()
    a = str((isolated_settings / "a.png").resolve())
    b = str((isolated_settings / "b.png").resolve())
    recent.add(a)
    recent.add(b)

    paths = recent.remove(b)

    assert paths == [a]


def test_recent_files_menu_opens_existing_and_removes_missing(qapp, isolated_settings):
    recent = RecentFiles(_settings(), limit=5)
    recent.clear()
    menu = QMenu()
    opened: list[str] = []
    missing: list[str] = []
    adapter = RecentFilesMenu(menu, menu, recent, opened.append, missing.append)

    existing = isolated_settings / "exists.png"
    existing.write_text("x", encoding="utf-8")
    absent = str((isolated_settings / "missing.png").resolve())
    adapter.add(str(existing))
    adapter.add(absent)

    adapter.open(str(existing.resolve()))
    adapter.open(absent)

    assert opened == [str(existing.resolve())]
    assert missing == [absent]
    assert adapter.paths() == [str(existing.resolve())]
    assert [action.text() for action in menu.actions()] == [existing.name]


def test_recent_files_menu_silently_filters_missing_on_rebuild(qapp, isolated_settings):
    """rebuild() entfernt nicht-existente Pfade stumm aus der Liste und dem Menue."""
    recent = RecentFiles(_settings(), limit=5)
    recent.clear()
    existing = isolated_settings / "alive.png"
    existing.write_text("x", encoding="utf-8")
    absent = str((isolated_settings / "ghost.png").resolve())
    # QSettings direkt vorbereiten – damit umgehen wir den add()-Pfad und
    # zwingen rebuild(), eine bereits stale Persistenz zu finden.
    recent._settings.setValue(recent.key, [absent, str(existing.resolve())])

    menu = QMenu()
    opened: list[str] = []
    missing: list[str] = []
    adapter = RecentFilesMenu(menu, menu, recent, opened.append, missing.append)

    assert absent not in adapter.paths()
    assert adapter.paths() == [str(existing.resolve())]
    assert [action.text() for action in menu.actions()] == [existing.name]
    # Stummer Pfad: missing_path-Callback bleibt aktiven Klicks vorbehalten.
    assert missing == []


def test_recent_list_dedups_and_caps(qapp, isolated_settings):
    from bgremover import MainWindow
    w = MainWindow()
    # Erst Liste explizit leeren (in case)
    w._settings.setValue(SETTINGS_RECENT_KEY, [])
    # rebuild() filtert inzwischen geloeschte Pfade stumm aus – die Test-
    # dateien muessen daher real existieren, damit Dedup/Cap testbar bleibt.
    for i in range(12):
        p = isolated_settings / f"img{i}.png"
        p.write_text("x", encoding="utf-8")
        w._add_recent(str(p))
    paths = w._recent_files.paths()
    assert len(paths) == RECENT_MAX
    # Letzter eingefügter Eintrag steht vorn
    assert Path(paths[0]).name == "img11.png"


def test_recent_brings_existing_to_front(qapp, isolated_settings):
    from bgremover import MainWindow
    w = MainWindow()
    w._settings.setValue(SETTINGS_RECENT_KEY, [])
    a_path = isolated_settings / "a.png"
    b_path = isolated_settings / "b.png"
    a_path.write_text("x", encoding="utf-8")
    b_path.write_text("x", encoding="utf-8")
    a = str(a_path)
    b = str(b_path)
    w._add_recent(a)
    w._add_recent(b)
    w._add_recent(a)             # a wieder nach vorn
    paths = w._recent_files.paths()
    assert paths[0] == str(Path(a).resolve())
    # Insgesamt nur 2 Einträge (keine Duplikate)
    assert len(paths) == 2


def test_recent_persists_after_image_load(qapp, isolated_settings, tmp_path):
    from bgremover import MainWindow
    w = MainWindow()
    w._settings.setValue(SETTINGS_RECENT_KEY, [])
    img_path = tmp_path / "x.png"
    Image.new("RGB", (8, 8), (1, 2, 3)).save(img_path)
    w._canvas.load_image(str(img_path))
    paths = w._recent_files.paths()
    assert len(paths) == 1
    assert Path(paths[0]).resolve() == img_path.resolve()


# ── #233: paths() ist defensiv gegen beschädigte QSettings-Werte ─────────

class _FakeSettings:
    """Minimaler QSettings-Ersatz, der Rohwerte unverändert zurückgibt.

    QSettings im INI-Format serialisiert alles zu Strings (eine gespeicherte
    Ganzzahl käme als ``"42"`` zurück) – über echtes QSettings ließen sich die
    geforderten Roh-Typen (int, None, tuple, dict) gar nicht prüfen. Dieser
    Fake liefert exakt den hinterlegten Python-Wert und zählt Schreibzugriffe.
    """

    def __init__(self, raw: object) -> None:
        self._raw = raw
        self.writes = 0

    def value(self, _key: str, default: object = None) -> object:
        return self._raw

    def setValue(self, _key: str, value: object) -> None:
        self._raw = value
        self.writes += 1


@pytest.mark.parametrize("raw, expected", [
    ("single.png", ["single.png"]),                          # QSettings-Ein-Element-String
    (["a.png", "b.png"], ["a.png", "b.png"]),                # Liste gültiger Strings
    (("a.png", "b.png"), ["a.png", "b.png"]),                # Tupel gültiger Strings
    (42, []),                                                # nicht iterierbarer Wert (Integer)
    (None, []),                                              # None
    (["a.png", 5, "", None, "b.png"], ["a.png", "b.png"]),  # gemischte Liste
    ([], []),                                                # leere Liste
    ("", []),                                                # leerer String
    ([""], []),                                              # Liste nur mit leerem String
    ({"a": 1}, []),                                          # dict – ebenfalls kein TypeError
])
def test_paths_sanitizes_raw_settings_values(raw, expected):
    """paths() ist robust gegen jeden Roh-Typ: gültige, nicht-leere Strings
    bleiben erhalten, alles Übrige wird ignoriert – ohne Exception
    (Akzeptanzkriterien #233)."""
    recent = RecentFiles(_FakeSettings(raw))
    assert recent.paths() == expected


def test_sanitize_persists_cleaned_value_and_warns(caplog):
    """sanitize() schreibt die bereinigte Liste zurück und loggt einmalig eine
    Warnung, wenn der Rohwert wirklich beschädigt war."""
    fake = _FakeSettings(["a.png", 5, "", "b.png"])
    recent = RecentFiles(fake)

    with caplog.at_level("WARNING"):
        cleaned = recent.sanitize()

    assert cleaned == ["a.png", "b.png"]
    assert fake._raw == ["a.png", "b.png"]   # zurückpersistiert
    assert fake.writes == 1
    assert any("bereinigt" in r.message for r in caplog.records)


def test_sanitize_leaves_valid_list_untouched(caplog):
    """Eine bereits saubere Liste löst weder Schreibzugriff noch Warnung aus."""
    fake = _FakeSettings(["a.png", "b.png"])
    recent = RecentFiles(fake)

    with caplog.at_level("WARNING"):
        cleaned = recent.sanitize()

    assert cleaned == ["a.png", "b.png"]
    assert fake.writes == 0
    assert caplog.records == []


def test_sanitize_keeps_single_string_quirk_silent(caplog):
    """Der harmlose QSettings-Ein-Element-String gilt nicht als Beschädigung:
    keine Warnung, kein Schreibzugriff."""
    fake = _FakeSettings("only.png")
    recent = RecentFiles(fake)

    with caplog.at_level("WARNING"):
        cleaned = recent.sanitize()

    assert cleaned == ["only.png"]
    assert fake.writes == 0
    assert caplog.records == []


def test_rebuild_survives_corrupt_settings(qapp):
    """Ein beschädigter Wert (hier: Integer) darf den Menüaufbau nicht
    abbrechen – das Menü zeigt einfach „(keine)" (Akzeptanzkriterium #233)."""
    recent = RecentFiles(_FakeSettings(42))
    menu = QMenu()
    # Darf NICHT werfen (rebuild() läuft im Konstruktor):
    RecentFilesMenu(menu, menu, recent, lambda _p: None)
    assert [action.text() for action in menu.actions()] == ["(keine)"]


def test_read_only_recent_files_never_persist_mutations(tmp_path):
    """Future-Schemas schützen alle mutierenden Recent-Files-Pfade."""
    existing = tmp_path / "existing.png"
    existing.write_text("x", encoding="utf-8")
    original = ["missing.png", str(existing)]
    fake = _FakeSettings(original.copy())
    recent = RecentFiles(fake, read_only=True)

    assert recent.sanitize() == original
    recent.add("new.png")
    recent.remove("missing.png")
    recent.clear()

    assert fake._raw == original
    assert fake.writes == 0


def test_future_schema_menu_build_is_read_only(qapp, tmp_path, monkeypatch):
    """Der Menüaufbau filtert nur die Anzeige und löst keinerlei Cleanup aus."""
    existing = tmp_path / "existing.png"
    existing.write_text("x", encoding="utf-8")
    stale = str(tmp_path / "missing.png")
    raw = [stale, str(existing)]
    fake = _FakeSettings(raw.copy())
    recent = RecentFiles(fake, read_only=True)
    remove_calls: list[str] = []
    sanitize_calls: list[bool] = []
    monkeypatch.setattr(
        recent, "remove", lambda path: remove_calls.append(path) or [])
    monkeypatch.setattr(
        recent, "sanitize", lambda: sanitize_calls.append(True) or [])

    menu = QMenu()
    RecentFilesMenu(menu, menu, recent, lambda _path: None)

    assert [action.text() for action in menu.actions()] == [existing.name]
    assert sanitize_calls == []
    assert remove_calls == []
    assert fake._raw == raw
    assert fake.writes == 0


# ── A5: Quick-Save ──────────────────────────────────────────────────────

def test_quick_save_writes_to_known_path(qapp, isolated_settings, tmp_path):
    from bgremover import MainWindow
    w = MainWindow()
    w._canvas.apply_loaded_image(Image.new("RGBA", (8, 8), (10, 20, 30, 255)), "seed.png")
    target = tmp_path / "out.png"
    w._save_path = str(target)
    w._save()
    assert target.exists()


def test_load_clears_save_path(qapp, isolated_settings, tmp_path):
    from bgremover import MainWindow
    w = MainWindow()
    w._save_path = "/tmp/somewhere.png"
    img_path = tmp_path / "fresh.png"
    Image.new("RGB", (8, 8), (1, 2, 3)).save(img_path)
    w._canvas.load_image(str(img_path))
    assert w._save_path is None


def test_mainwindow_keeps_future_recent_files_byte_identical(
    qapp, isolated_settings, monkeypatch,
):
    """Bei einem ZUKUENFTIGEN Schema darf der Start recent_files NICHT
    umschreiben – auch nicht indirekt beim Aufbau des Menüs (#259)."""
    from bgremover import MainWindow
    from bgremover.settings_schema import SCHEMA_VERSION, SCHEMA_VERSION_KEY

    sanitize_calls: list[int] = []
    remove_calls: list[str] = []
    monkeypatch.setattr(
        RecentFiles, "sanitize", lambda self: sanitize_calls.append(1) or [])
    original_remove = RecentFiles.remove

    def record_remove(self, path):
        remove_calls.append(path)
        return original_remove(self, path)

    monkeypatch.setattr(RecentFiles, "remove", record_remove)
    future = _settings()
    stale_paths = ["/future/missing-a.png", "/future/missing-b.png"]
    future.setValue(SCHEMA_VERSION_KEY, SCHEMA_VERSION + 1)
    future.setValue(SETTINGS_RECENT_KEY, stale_paths)
    future.sync()
    settings_file = Path(future.fileName())
    before = settings_file.read_bytes()

    window = MainWindow()
    window._settings.sync()
    window.close()

    assert sanitize_calls == []
    assert remove_calls == []
    assert _settings().value(SETTINGS_RECENT_KEY) == stale_paths
    assert settings_file.read_bytes() == before


def test_mainwindow_keeps_normal_recent_cleanup(
    qapp, isolated_settings, monkeypatch,
):
    """Für kompatible Schemas bleiben Sanitize und Stale-Path-Cleanup aktiv."""
    from bgremover import MainWindow
    from bgremover.settings_schema import SCHEMA_VERSION, SCHEMA_VERSION_KEY

    sanitize_calls: list[int] = []
    original_sanitize = RecentFiles.sanitize

    def record_sanitize(self):
        sanitize_calls.append(1)
        return original_sanitize(self)

    monkeypatch.setattr(RecentFiles, "sanitize", record_sanitize)
    compatible = _settings()
    compatible.setValue(SCHEMA_VERSION_KEY, SCHEMA_VERSION)
    compatible.setValue(SETTINGS_RECENT_KEY, ["/missing.png"])
    compatible.sync()

    window = MainWindow()
    window._settings.sync()
    window.close()

    assert sanitize_calls == [1]
    assert _settings().value(SETTINGS_RECENT_KEY) == []
