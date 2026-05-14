"""Gemeinsame pytest-Fixtures.

Setzt das Qt-Platform-Plugin auf ``offscreen``, damit die Tests headless
laufen (CI, lokale Server ohne Display) und stellt eine geteilte
``QApplication`` als Session-Fixture bereit.
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Repo-Root in sys.path aufnehmen, damit ``import BgRemover`` funktioniert,
# wenn das Paket nicht per ``pip install -e .`` installiert wurde.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app
