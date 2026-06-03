"""Coverage-Guards für die Runtime-i18n-Stringtabelle.

Die Tests halten die zentrale Tabelle mit den Aufrufstellen synchron und
prüfen, dass die deutschen Referenzstrings unverändert gerendert werden.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PyQt6.QtCore import QSettings

import bgremover.i18n as i18n
from bgremover.i18n import DEFAULT_LOCALE, configure_locale, tr

_SRC_DIR = Path(i18n.__file__).resolve().parent
# Nur eigenständige ``tr("…")``-Aufrufe; der Lookbehind vermeidet Treffer
# auf Methoden oder Bezeichner, die nur auf ``tr`` enden (z. B. ``attr(``).
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

    # Dynamische Labels mit Startwerten und absichtlich doppelten Leerzeichen.
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
    # Nicht gemappte Keys fallen weiter auf Deutsch zurück.
    assert refs["tolerance_label"].text() == "Tolerance:  30"


# ── Guard gegen neue unübersetzte nutzerseitige Literale ───────────────
#
# Die Key-Hygiene-Tests oben sehen nur *referenzierte* Keys. Dieser AST-Guard
# findet Strings, die ``tr()`` gar nicht erreichen: Canvas-Statussignal,
# native Qt-Dialoge und History-``desc=``. Literale mit Buchstaben müssen an
# diesen Stellen über ``tr(...)`` oder bereits übersetzte Variablen laufen.

# Qt-Static-Method-Senken: Empfängerklasse -> {Methode: Positionsargumente
# mit übersetzbarem Text}.
_QT_SINKS = {
    "QMessageBox": {
        "warning": (1, 2), "information": (1, 2),
        "critical": (1, 2), "question": (1, 2),
    },
    "QFileDialog": {
        "getOpenFileName": (1,), "getSaveFileName": (1,),
        "getExistingDirectory": (1,),
    },
    "QColorDialog": {"getColor": (2,)},
}


def _carries_text(node: ast.expr | None) -> bool:
    """True if *node* is a string literal / f-string containing letters."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return any(ch.isalpha() for ch in node.value)
    if isinstance(node, ast.JoinedStr):  # f-string
        return any(
            isinstance(part, ast.Constant)
            and isinstance(part.value, str)
            and any(ch.isalpha() for ch in part.value)
            for part in node.values
        )
    return False


def _untranslated_sink_literals() -> list[str]:
    hits: list[str] = []
    for path in _SRC_DIR.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not isinstance(func, ast.Attribute):
                continue
            # 1) <...>.statusMsg.emit(<text>)
            if (func.attr == "emit"
                    and isinstance(func.value, ast.Attribute)
                    and func.value.attr == "statusMsg"
                    and node.args and _carries_text(node.args[0])):
                hits.append(f"{path.name}:{node.lineno}: statusMsg.emit")
            # 2) QMessageBox/QFileDialog/QColorDialog static dialogs
            if (isinstance(func.value, ast.Name)
                    and func.value.id in _QT_SINKS
                    and func.attr in _QT_SINKS[func.value.id]):
                for idx in _QT_SINKS[func.value.id][func.attr]:
                    if idx < len(node.args) and _carries_text(node.args[idx]):
                        hits.append(
                            f"{path.name}:{node.lineno}: "
                            f"{func.value.id}.{func.attr} arg{idx}")
            # 3) history ``desc=`` keyword on edits
            for kw in node.keywords:
                if kw.arg == "desc" and _carries_text(kw.value):
                    hits.append(f"{path.name}:{node.lineno}: desc=")
    return hits


def test_no_untranslated_literals_at_user_facing_sinks() -> None:
    hits = _untranslated_sink_literals()
    assert not hits, (
        "Unübersetzte Literale an Nutzer-Senken (müssen über tr() laufen):\n"
        + "\n".join(hits)
    )


def test_representative_german_strings_unchanged() -> None:
    """Lock tricky German values moved into the table during the canvas/dialog
    rollout (symbols, double spaces, numeric format specs) so they cannot drift.
    """
    configure_locale("de")
    cases = [
        (tr("canvas.opened", name="foo.png", w=10, h=20),
         "Geöffnet: foo.png  (10 × 20 px)"),
        (tr("canvas.undo_done"), "↩  Rückgängig: {desc}"),
        (tr("canvas.original_restored"), "🔄  Original wiederhergestellt"),
        (tr("canvas.flipped_h"), "↔ Horizontal gespiegelt"),
        (tr("canvas.rotated", direction="↺", degrees=90, w=10, h=20),
         "↺ Gedreht: 90°  (10 × 20 px)"),
        (tr("canvas.selection_inverted", pixels=1234),
         "Auswahl invertiert: 1,234 Pixel"),
        (tr("canvas.crop_start_circle"),
         "✂  Ausschnitt verschieben  [Kreis]  —  dann ✓ Anwenden klicken"),
        (tr("canvas.saved", name="a.png"), "💾 Gespeichert: a.png"),
        (tr("history.desc.rotated", direction="↻", degrees=90), "↻ Gedreht 90°"),
        (tr("dialog.unsaved.title"), "Ungespeicherte Änderungen"),
        (tr("dialog.color.title"), "Hintergrundfarbe wählen"),
    ]
    for actual, expected in cases:
        assert actual == expected, f"{actual!r} != {expected!r}"
