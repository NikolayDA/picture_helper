"""Schützt die Rail-Icons gegen die in #484/#485/#486/#487 behobenen Regressionen.

Drei Kontrakte: (1) jeder von der Werkzeugleiste verwendete Icon-Name hat
einen Vektor-Fallback (kein stilles Blank-Icon wie beim einst fehlenden
``redo``-Eintrag), (2) die Icon-Farbe kommt aus einem Parameter statt aus
fest kodierten ``QColor``-Werten, (3) die fünf einst mehrfarbigen
Glanz-Clipart-PNGs bleiben entfernt.
"""
import importlib.resources

from PyQt6.QtCore import QSize
from PyQt6.QtGui import QColor, QIcon

from bgremover.icons import _ICON_DRAW, make_stateful_tool_icon, make_tool_icon
from bgremover.main_toolbar import ToolbarActions, build_toolbar

_RAIL_ICON_NAMES = {
    "move", "wand", "brush", "eraser", "lasso",
    "height_lighten", "height_darken", "undo", "redo", "theme",
}


def _build_toolbar():
    actions = ToolbarActions(
        set_tool=lambda _t: None, undo=lambda: None, redo=lambda: None,
        toggle_theme=lambda: None,
    )
    return build_toolbar(actions)


def test_rail_icon_names_have_vector_fallback(qapp):
    """Jeder von der Rail tatsächlich verwendete Icon-Name hat einen Eintrag
    in ``_ICON_DRAW`` – verhindert die in #485 gefundene fehlende
    ``redo``-Zuordnung (sonst rendert ``make_tool_icon`` ein Blank-Icon)."""
    toolbar = _build_toolbar()
    used_names = {name for _, name in toolbar.checkable_icons}
    used_names |= {name for _, name in toolbar.foot_icons}
    assert used_names == _RAIL_ICON_NAMES
    for name in used_names:
        assert name in _ICON_DRAW, f"Kein Vektor-Fallback für Rail-Icon {name!r}"


def test_make_tool_icon_color_changes_pixels():
    """``make_tool_icon`` mit unterschiedlichen Farben liefert unterschiedliche
    Pixel – verhindert den Rückfall auf hartkodierte Farben (#486)."""
    grey = make_tool_icon("wand", 24, QColor(200, 200, 200))
    blue = make_tool_icon("wand", 24, QColor(40, 90, 240))
    assert grey.pixmap(24, 24).toImage() != blue.pixmap(24, 24).toImage()


def test_make_tool_icon_without_color_uses_a_default():
    """Ohne ``color`` bleibt ``make_tool_icon`` nutzbar (Nicht-Rail-Aufrufer
    wie ``right_panel_tabs``/``zoom_control`` übergeben weiterhin keine Farbe)."""
    icon = make_tool_icon("lock", 22)
    assert not icon.pixmap(22, 22).isNull()


def test_make_stateful_tool_icon_off_on_pixels_differ():
    """Aus-/An-Zustand eines checkbaren Werkzeug-Icons unterscheiden sich
    sichtbar – Qt wählt die Variante automatisch über ``QToolButton.isChecked``
    (#486, ``QIcon.State.Off``/``.On``)."""
    icon = make_stateful_tool_icon("wand", 24, QColor(140, 140, 140), QColor(60, 110, 240))
    off = icon.pixmap(QSize(24, 24), QIcon.Mode.Normal, QIcon.State.Off)
    on = icon.pixmap(QSize(24, 24), QIcon.Mode.Normal, QIcon.State.On)
    assert off.toImage() != on.toImage()


def test_toolbar_checked_tool_shows_on_state_icon(qapp):
    """Der beim Aufbau vorausgewählte Zauberstab zeigt tatsächlich die
    An-Pixmap seines Icons (End-to-End-Beleg für #486, nicht nur die
    isolierte Icon-Fabrik)."""
    toolbar = _build_toolbar()
    assert toolbar.btn_wand.isChecked()
    icon = toolbar.btn_wand.icon()
    off = icon.pixmap(QSize(20, 20), QIcon.Mode.Normal, QIcon.State.Off)
    on = icon.pixmap(QSize(20, 20), QIcon.Mode.Normal, QIcon.State.On)
    assert off.toImage() != on.toImage()


def test_rail_icons_have_no_png_assets():
    """Keiner der zehn Rail-Namen hat mehr ein PNG-Asset – sonst überdeckt
    ``make_tool_icon`` den (seit #484/#485 korrekten) Vektor-Fallback wieder
    mit dem alten Glanz-Clipart (#487)."""
    for name in _RAIL_ICON_NAMES:
        res = importlib.resources.files("bgremover") / "icons" / f"{name}.png"
        with importlib.resources.as_file(res) as png_path:
            assert not png_path.is_file(), f"{name}.png sollte entfernt sein (#487)"
