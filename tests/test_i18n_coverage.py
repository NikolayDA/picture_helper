"""Coverage guards for the runtime-i18n string table (PR 4a).

PR 4a routes the right-panel tab contents, the settings dialog and the
remaining ``QMessageBox`` dialogs through :func:`bgremover.i18n.tr`. These
tests keep the central table in sync with the call sites and verify that the
German strings still render byte-for-byte after the refactor.
"""
from __future__ import annotations

import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PyQt6.QtCore import QSettings

import bgremover.i18n as i18n
from bgremover.i18n import DEFAULT_LOCALE, configure_locale

_SRC_DIR = Path(i18n.__file__).resolve().parent
# Standalone ``tr("…")`` calls only – the lookbehind avoids matching method
# calls or identifiers that merely end in ``tr`` (e.g. ``attr(``).
_TR_KEY_RE = re.compile(r'(?<![\w.])tr\(\s*"([^"]+)"')


def _referenced_keys() -> set[str]:
    keys: set[str] = set()
    for path in _SRC_DIR.glob("*.py"):
        for match in _TR_KEY_RE.finditer(path.read_text(encoding="utf-8")):
            keys.add(match.group(1))
    return keys


@pytest.fixture(autouse=True)
def reset_locale():
    configure_locale(DEFAULT_LOCALE)
    yield
    configure_locale(DEFAULT_LOCALE)


def test_every_referenced_key_exists_in_table() -> None:
    table = set(i18n._TRANSLATIONS[DEFAULT_LOCALE])
    missing = sorted(_referenced_keys() - table)
    assert not missing, f"tr()-Keys ohne Tabelleneintrag: {missing}"


def test_no_unused_keys_in_table() -> None:
    table = set(i18n._TRANSLATIONS[DEFAULT_LOCALE])
    unused = sorted(table - _referenced_keys())
    assert not unused, f"Tabellen-Keys ohne Verwendung: {unused}"


def test_right_panel_tabs_build_and_render_german(qapp) -> None:
    from bgremover.right_panel_tabs import (
        BackgroundTab,
        SelectionTab,
        ShapeTab,
        TransformTab,
    )

    built = {
        Tab.__name__: Tab(MagicMock()).build()
        for Tab in (SelectionTab, BackgroundTab, TransformTab, ShapeTab)
    }
    for name, (widget, _refs) in built.items():
        assert widget is not None, name

    # Dynamic labels with their initial values + tricky double spaces.
    _w, sel = built["SelectionTab"]
    assert sel["tolerance_label"].text() == "Toleranz (Zauberstab):  30"
    assert sel["brush_label"].text() == "Pinselgröße:  30 px"
    _w2, shape = built["ShapeTab"]
    assert shape["corner_label"].text() == "Radius:  0 px"


def test_settings_dialog_builds_in_german(qapp, tmp_path) -> None:
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(
        QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path))
    from bgremover.settings_dialog import SettingsDialog

    dlg = SettingsDialog(QSettings("BgRemover", "BgRemover"))
    try:
        assert dlg.windowTitle() == "Einstellungen"
    finally:
        dlg.close()


def test_panel_label_is_runtime_translated(qapp, monkeypatch) -> None:
    monkeypatch.setitem(
        i18n._TRANSLATIONS,
        "zz",
        {"right_panel.selection.tolerance": "Tolerance:  {value}"},
    )
    configure_locale("zz")
    from bgremover.right_panel_tabs import SelectionTab

    _widget, refs = SelectionTab(MagicMock()).build()
    # Unmapped keys still fall back to German; the mapped one is translated.
    assert refs["tolerance_label"].text() == "Tolerance:  30"
