"""Einstiegspunkt für das PyInstaller-macOS-Bundle (siehe ``bgremover.spec``).

Das Bundle startet diese Datei statt ``python -m bgremover``; sie ruft die
etablierte ``main()``-Fassade des Pakets auf, damit der Start-Code (Qt-Plugin-
Pfad, Logging, ``QFileOpenEvent``) identisch zum normalen Start bleibt.

WICHTIG – ``multiprocessing.freeze_support()`` MUSS hier als Allererstes laufen:
Die KI-Inferenz (``bgremover.ai_process``) startet ihren Kindprozess per
multiprocessing-„spawn". Im eingefrorenen PyInstaller-Bundle relauncht „spawn"
dieselbe App-Binärdatei. Ohne ``freeze_support()`` würde der Kindprozess erneut
die GUI-``main()`` ausführen statt der Inferenz-Bootstrap – jedes neue Fenster
startet wieder den Warmup, spawnt erneut … eine exponentielle Fork-Bomb (100+
Fenster, nur per Neustart stoppbar). ``freeze_support()`` (von PyInstallers
multiprocessing-Runtime-Hook plattformübergreifend bereitgestellt) fängt den
Kindprozess-Start ab, führt dessen Bootstrap aus und beendet ihn; bei einem
normalen Start ist es ein No-op. Der GUI-Import erfolgt bewusst erst DANACH,
damit der Inferenz-Kindprozess den Qt-Stack gar nicht erst lädt.
"""
import multiprocessing

if __name__ == "__main__":
    multiprocessing.freeze_support()

    from bgremover.app import main

    main()
