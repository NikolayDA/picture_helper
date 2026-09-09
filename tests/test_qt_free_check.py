"""Der geteilte Qt-frei-Wächter selbst (#1044): Positiv- und Negativkontrolle.

Vier Tests nennen dem Helfer nur noch ihr Modul; wäre die Regel im Helfer
still kaputt (etwa ein leerer Binding-Satz), blieben alle vier grün. Deshalb
hier ein Modul, das Qt sicher importiert, als Gegenprobe.
"""

from __future__ import annotations

import pytest

import bgremover.height_map as height_map
import bgremover.viewer_3d as viewer_3d
from tests._qt_free_check import QT_BINDINGS, assert_module_is_qt_free, imported_top_level_names


def test_qt_free_module_passes() -> None:
    assert_module_is_qt_free(height_map)


def test_qt_module_is_rejected_with_module_name_and_binding() -> None:
    assert "PyQt6" in imported_top_level_names(viewer_3d)
    with pytest.raises(
        AssertionError, match=r"bgremover\.viewer_3d importiert Qt-Bindings: \['PyQt6'\]"
    ):
        assert_module_is_qt_free(viewer_3d)


def test_one_qt_module_fails_the_whole_group() -> None:
    with pytest.raises(AssertionError, match="viewer_3d"):
        assert_module_is_qt_free(height_map, viewer_3d)


def test_binding_set_covers_the_three_known_bindings() -> None:
    assert {"PyQt6", "PyQt5", "PySide6"} == QT_BINDINGS
