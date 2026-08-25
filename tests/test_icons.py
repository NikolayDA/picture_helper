"""Schützt die Rail-Icons gegen die in #484/#485/#486/#487 behobenen Regressionen.

Drei Kontrakte: (1) jeder von der Werkzeugleiste verwendete Icon-Name hat
einen Vektor-Fallback (kein stilles Blank-Icon wie beim einst fehlenden
``redo``-Eintrag), (2) die Icon-Farbe kommt aus einem Parameter statt aus
fest kodierten ``QColor``-Werten, (3) die fünf einst mehrfarbigen
Glanz-Clipart-PNGs bleiben entfernt.
"""
import importlib.resources
import os
import subprocess
import sys

import pytest
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QColor, QIcon

import bgremover.icons as icons
from bgremover.icons import (
    _ICON_DRAW,
    make_app_icon,
    make_stateful_tool_icon,
    make_tool_icon,
)
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


def test_app_icon_asset_exists_and_is_square():
    """Das Anwendungs-Icon liegt als Paketdaten-PNG bei – Voraussetzung dafür,
    dass der laufende Prozess (App-Umschalter/Stage-Manager-Seitenleiste auf
    macOS) das App-Icon statt des Python-Raketen-Icons zeigt."""
    from PIL import Image

    res = importlib.resources.files("bgremover") / "icons" / "app_icon.png"
    with importlib.resources.as_file(res) as png_path:
        assert png_path.is_file(), "app_icon.png fehlt in den Paketdaten"
        with Image.open(png_path) as img:
            width, height = img.size
    assert width == height, "App-Icon muss quadratisch sein"
    assert width >= 256, "App-Icon braucht genug Auflösung für Dock/Umschalter"


def test_make_app_icon_renders_visible_pixmap(qapp):
    """``make_app_icon`` liefert ein nicht-leeres, renderbares Icon –
    ``QApplication.setWindowIcon`` bekommt damit echte Pixel statt eines
    stillen Blank-Icons."""
    icon = make_app_icon()
    assert not icon.isNull()
    pm = icon.pixmap(64, 64)
    assert not pm.isNull()
    img = pm.toImage()
    assert any(
        img.pixelColor(x, y).alpha() > 0
        for x in range(0, 64, 8) for y in range(0, 64, 8)
    ), "App-Icon-Pixmap ist vollständig transparent"


def test_make_app_icon_without_gui_application_returns_empty_icon():
    """Ohne laufende ``QGuiApplication`` liefert ``make_app_icon`` ein leeres
    Icon statt des harten QPixmap-Aborts – der Eager-Pixel-Pfad (Review-Fund
    PR #864: lazy ``QIcon(pfad)`` wäre bei zip-Import ein stilles Blank-Icon)
    ist entsprechend geguardet. Eigener Subprozess, weil die Test-Session
    selbst eine ``QApplication`` hält."""
    code = (
        "from bgremover.icons import make_app_icon; "
        "icon = make_app_icon(); "
        "assert icon.isNull(), 'ohne QGuiApplication muss das Icon leer sein'; "
        "print('ok')"
    )
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    r = subprocess.run([sys.executable, "-c", code],
                       capture_output=True, text=True, timeout=60, env=env)
    assert r.returncode == 0 and "ok" in r.stdout, (
        f"--- stdout ---\n{r.stdout}\n--- stderr ---\n{r.stderr}"
    )


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


def test_rail_icon_names_are_vector_only():
    """Alle zehn Rail-Icons sind vektoriell – Voraussetzung dafür, dass stale
    package-data PNGs aus alten macOS-App-venvs die Rail nicht zurück auf
    alte Raster-Icons ziehen können (der eigentliche PNG-Lookup-Verzicht wird
    stellvertretend für "undo" in ``test_icon_prefers_vector_path_even_if_png_resource_exists``
    geprüft)."""
    assert _RAIL_ICON_NAMES <= icons._VECTOR_ONLY_ICON_NAMES


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


def test_ai_icon_has_no_png_asset():
    """Das alte mehrfarbige Gehirn-PNG ist entfernt – Variante A ersetzt es
    vollständig durch den Vektor-Sparkle."""
    res = importlib.resources.files("bgremover") / "icons" / "ai.png"
    with importlib.resources.as_file(res) as png_path:
        assert not png_path.is_file(), "ai.png sollte entfernt sein (Variante A)"


def test_transparency_icon_has_no_png_asset():
    """Der nie verdrahtete Platzhalter ``transparency.png`` ist entfernt – ic-r1
    wird ausschließlich vektoriell gerendert."""
    res = importlib.resources.files("bgremover") / "icons" / "transparency.png"
    with importlib.resources.as_file(res) as png_path:
        assert not png_path.is_file(), "transparency.png sollte entfernt sein (Variante A)"


@pytest.mark.parametrize("name", [
    "undo", "ai", "transparency", "replace_color", "feather",
    "round_corners", "height_import",
])
def test_icon_prefers_vector_path_even_if_png_resource_exists(name, monkeypatch, qapp):
    """Stale package-data PNGs aus alten macOS-App-venvs dürfen currentColor-
    Icons nicht zurück auf einen PNG-Lookup ziehen – weder das Rail-Icon
    ``undo`` (#484/#485) noch die Variante-A-Icons ``ai``/``transparency``/
    ``replace_color``/``feather``/``round_corners``/``height_import``."""
    assert name in icons._VECTOR_ONLY_ICON_NAMES

    def fail_if_png_resource_is_consulted(_package):
        raise AssertionError(f"{name}-Icon muss aus dem Vektorpfad rendern statt PNG-Lookup")

    monkeypatch.setattr(icons.importlib.resources, "files", fail_if_png_resource_is_consulted)

    grey = make_tool_icon(name, 24)
    blue = make_tool_icon(name, 24, QColor(40, 90, 240))
    assert not grey.pixmap(24, 24).isNull()
    assert not blue.pixmap(24, 24).isNull()
    assert grey.pixmap(24, 24).toImage() != blue.pixmap(24, 24).toImage()
