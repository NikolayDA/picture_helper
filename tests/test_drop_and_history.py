"""Verhaltenstests für den asynchronen Drop-Ladepfad und ``undo_to``.

* ``dropEvent`` lädt nicht mehr synchron, sondern emittiert
  ``loadRequested`` (MainWindow lädt im Worker → keine UI-Freezes).
* ``undo_to`` verhält sich wie mehrfaches ``undo()`` und ist damit
  über ``redo()`` wiederherstellbar (vorher wurde Redo verworfen).

Hinweis: ``QDropEvent`` übernimmt KEIN Ownership des ``QMimeData``.
Das Mime-Objekt muss bis nach ``dropEvent`` referenziert bleiben –
sonst sammelt der GC es ein und Qt dereferenziert einen Dangling
Pointer (Segfault). Deshalb wird hier nichts in einen Helper
ausgelagert, der das Objekt fallen lassen würde.
"""
import numpy as np
from PIL import Image
from PyQt6.QtCore import Qt, QPointF, QMimeData, QUrl
from PyQt6.QtGui import QDropEvent

from bgremover import ImageCanvas


def test_drop_emits_load_requested_and_does_not_load_sync(qapp, tmp_path):
    p = tmp_path / "img.png"
    Image.new("RGB", (10, 10), (1, 2, 3)).save(p)
    c = ImageCanvas()
    requested: list[str] = []
    c.loadRequested.connect(requested.append)

    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(p))])
    ev = QDropEvent(QPointF(1, 1), Qt.DropAction.CopyAction, mime,
                    Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    c.dropEvent(ev)

    assert requested == [str(p)]
    assert c.image is None         # NICHT synchron geladen → kein Freeze


def test_drop_unsupported_format_reports_status(qapp, tmp_path):
    bad = tmp_path / "note.txt"
    bad.write_text("x")
    c = ImageCanvas()
    msgs: list[str] = []
    c.statusMsg.connect(msgs.append)

    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(bad))])
    ev = QDropEvent(QPointF(0, 0), Qt.DropAction.CopyAction, mime,
                    Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    c.dropEvent(ev)

    assert any("nicht unterstützt" in m for m in msgs)


def test_drop_multifile_reports_ignored_extras(qapp, tmp_path):
    a = tmp_path / "a.png"
    b = tmp_path / "b.png"
    Image.new("RGB", (4, 4), (0, 0, 0)).save(a)
    Image.new("RGB", (4, 4), (0, 0, 0)).save(b)
    c = ImageCanvas()
    requested: list[str] = []
    msgs: list[str] = []
    c.loadRequested.connect(requested.append)
    c.statusMsg.connect(msgs.append)

    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(a)), QUrl.fromLocalFile(str(b))])
    ev = QDropEvent(QPointF(0, 0), Qt.DropAction.CopyAction, mime,
                    Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    c.dropEvent(ev)

    assert requested == [str(a)]               # nur die erste Datei
    assert any("weitere" in m for m in msgs)   # Rest wird gemeldet


def test_undo_to_is_redoable(qapp):
    c = ImageCanvas()
    img = Image.new("RGBA", (8, 8), (255, 0, 0, 255))
    c.apply_loaded_image(img, "seed.png")
    c.apply_edit(Image.new("RGBA", (8, 8), (0, 255, 0, 255)), desc="grün")
    c.apply_edit(Image.new("RGBA", (8, 8), (0, 0, 255, 255)), desc="blau")

    c.undo_to(2)                                   # zwei Schritte zurück
    assert c.image is not None
    assert np.array(c.image)[0, 0].tolist() == [255, 0, 0, 255]

    # Anders als früher (Redo verworfen) ist der Sprung wiederherstellbar
    c.redo()
    assert c.image is not None
    assert np.array(c.image)[0, 0].tolist() == [0, 255, 0, 255]
    c.redo()
    assert c.image is not None
    assert np.array(c.image)[0, 0].tolist() == [0, 0, 255, 255]
