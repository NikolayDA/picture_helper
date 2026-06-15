"""Einstiegspunkt für das PyInstaller-macOS-Bundle (siehe ``bgremover.spec``).

Das Bundle startet diese Datei statt ``python -m bgremover``; sie ruft nur die
etablierte ``main()``-Fassade des Pakets auf, damit der Start-Code (Qt-Plugin-
Pfad, Logging, ``QFileOpenEvent``) identisch zum normalen Start bleibt.
"""
from bgremover.app import main

if __name__ == "__main__":
    main()
