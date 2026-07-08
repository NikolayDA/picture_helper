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

import bgremover.icons as icons
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


def test_rail_icons_prefer_vector_paths_even_if_png_resource_exists(monkeypatch, qapp):
    """Stale package-data PNGs aus alten macOS-App-venvs dürfen die Rail nicht
    zurück auf alte Raster-Icons ziehen."""
    assert _RAIL_ICON_NAMES <= icons._VECTOR_ONLY_ICON_NAMES

    def fail_if_png_resource_is_consulted(_package):
        raise AssertionError("Rail icons must render from vector paths before PNG lookup")

    monkeypatch.setattr(icons.importlib.resources, "files", fail_if_png_resource_is_consulted)

    grey = make_tool_icon("undo", 24)
    blue = make_tool_icon("undo", 24, QColor(40, 90, 240))
    assert not grey.pixmap(24, 24).isNull()
    assert not blue.pixmap(24, 24).isNull()
    assert grey.pixmap(24, 24).toImage() != blue.pixmap(24, 24).toImage()


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


def test_ai_icon_prefers_vector_path_even_if_png_resource_exists(monkeypatch, qapp):
    """Das KI-Icon (Inspector-Primärbutton, kein Rail-Icon) ist seit Variante A
    ebenfalls ein currentColor-Sparkle – wie bei der Rail darf kein stales
    ``ai.png`` aus alten Paketdaten den Theme-Farbpfad überdecken."""
    assert "ai" in icons._VECTOR_ONLY_ICON_NAMES

    def fail_if_png_resource_is_consulted(_package):
        raise AssertionError("ai-Icon muss aus dem Vektorpfad rendern statt PNG-Lookup")

    monkeypatch.setattr(icons.importlib.resources, "files", fail_if_png_resource_is_consulted)

    grey = make_tool_icon("ai", 24)
    blue = make_tool_icon("ai", 24, QColor(40, 90, 240))
    assert not grey.pixmap(24, 24).isNull()
    assert not blue.pixmap(24, 24).isNull()
    assert grey.pixmap(24, 24).toImage() != blue.pixmap(24, 24).toImage()


def test_ai_icon_has_no_png_asset():
    """Das alte mehrfarbige Gehirn-PNG ist entfernt – Variante A ersetzt es
    vollständig durch den Vektor-Sparkle."""
    res = importlib.resources.files("bgremover") / "icons" / "ai.png"
    with importlib.resources.as_file(res) as png_path:
        assert not png_path.is_file(), "ai.png sollte entfernt sein (Variante A)"


def test_transparency_icon_prefers_vector_path_even_if_png_resource_exists(monkeypatch, qapp):
    """Das Transparenz-Schachbrett von „Entfernen (transparent)" (ic-r1) ist
    ebenfalls ein currentColor-Icon – kein stales PNG darf den Theme-Farbpfad
    überdecken."""
    assert "transparency" in icons._VECTOR_ONLY_ICON_NAMES

    def fail_if_png_resource_is_consulted(_package):
        raise AssertionError(
            "transparency-Icon muss aus dem Vektorpfad rendern statt PNG-Lookup")

    monkeypatch.setattr(icons.importlib.resources, "files", fail_if_png_resource_is_consulted)

    grey = make_tool_icon("transparency", 24)
    blue = make_tool_icon("transparency", 24, QColor(40, 90, 240))
    assert not grey.pixmap(24, 24).isNull()
    assert not blue.pixmap(24, 24).isNull()
    assert grey.pixmap(24, 24).toImage() != blue.pixmap(24, 24).toImage()


def test_transparency_icon_has_no_png_asset():
    """Der nie verdrahtete Platzhalter ``transparency.png`` ist entfernt – ic-r1
    wird ausschließlich vektoriell gerendert."""
    res = importlib.resources.files("bgremover") / "icons" / "transparency.png"
    with importlib.resources.as_file(res) as png_path:
        assert not png_path.is_file(), "transparency.png sollte entfernt sein (Variante A)"


def test_replace_color_icon_prefers_vector_path_even_if_png_resource_exists(monkeypatch, qapp):
    """Der Farbeimer von „Farbe ersetzen" (ic-f1) ist ebenfalls ein
    currentColor-Icon – kein PNG-Lookup darf den Theme-Farbpfad überdecken."""
    assert "replace_color" in icons._VECTOR_ONLY_ICON_NAMES

    def fail_if_png_resource_is_consulted(_package):
        raise AssertionError(
            "replace_color-Icon muss aus dem Vektorpfad rendern statt PNG-Lookup")

    monkeypatch.setattr(icons.importlib.resources, "files", fail_if_png_resource_is_consulted)

    grey = make_tool_icon("replace_color", 24)
    blue = make_tool_icon("replace_color", 24, QColor(40, 90, 240))
    assert not grey.pixmap(24, 24).isNull()
    assert not blue.pixmap(24, 24).isNull()
    assert grey.pixmap(24, 24).toImage() != blue.pixmap(24, 24).toImage()


def test_feather_icon_prefers_vector_path_even_if_png_resource_exists(monkeypatch, qapp):
    """Die ausklingenden Striche von „Kante glätten" (ic-e1) sind ebenfalls ein
    currentColor-Icon – kein PNG-Lookup darf den Theme-Farbpfad überdecken."""
    assert "feather" in icons._VECTOR_ONLY_ICON_NAMES

    def fail_if_png_resource_is_consulted(_package):
        raise AssertionError(
            "feather-Icon muss aus dem Vektorpfad rendern statt PNG-Lookup")

    monkeypatch.setattr(icons.importlib.resources, "files", fail_if_png_resource_is_consulted)

    grey = make_tool_icon("feather", 24)
    blue = make_tool_icon("feather", 24, QColor(40, 90, 240))
    assert not grey.pixmap(24, 24).isNull()
    assert not blue.pixmap(24, 24).isNull()
    assert grey.pixmap(24, 24).toImage() != blue.pixmap(24, 24).toImage()


def test_round_corners_icon_prefers_vector_path_even_if_png_resource_exists(monkeypatch, qapp):
    """Das Rundrechteck von „Ecken abrunden" (ic-c2) ist ebenfalls ein
    currentColor-Icon – kein PNG-Lookup darf den Theme-Farbpfad überdecken."""
    assert "round_corners" in icons._VECTOR_ONLY_ICON_NAMES

    def fail_if_png_resource_is_consulted(_package):
        raise AssertionError(
            "round_corners-Icon muss aus dem Vektorpfad rendern statt PNG-Lookup")

    monkeypatch.setattr(icons.importlib.resources, "files", fail_if_png_resource_is_consulted)

    grey = make_tool_icon("round_corners", 24)
    blue = make_tool_icon("round_corners", 24, QColor(40, 90, 240))
    assert not grey.pixmap(24, 24).isNull()
    assert not blue.pixmap(24, 24).isNull()
    assert grey.pixmap(24, 24).toImage() != blue.pixmap(24, 24).toImage()


def test_height_import_icon_prefers_vector_path_even_if_png_resource_exists(monkeypatch, qapp):
    """Die Berg-Silhouette mit Import-Pfeil von „Graustufe importieren…" (ic-h2)
    ist ebenfalls ein currentColor-Icon – kein PNG-Lookup darf den Theme-
    Farbpfad überdecken."""
    assert "height_import" in icons._VECTOR_ONLY_ICON_NAMES

    def fail_if_png_resource_is_consulted(_package):
        raise AssertionError(
            "height_import-Icon muss aus dem Vektorpfad rendern statt PNG-Lookup")

    monkeypatch.setattr(icons.importlib.resources, "files", fail_if_png_resource_is_consulted)

    grey = make_tool_icon("height_import", 24)
    blue = make_tool_icon("height_import", 24, QColor(40, 90, 240))
    assert not grey.pixmap(24, 24).isNull()
    assert not blue.pixmap(24, 24).isNull()
    assert grey.pixmap(24, 24).toImage() != blue.pixmap(24, 24).toImage()
