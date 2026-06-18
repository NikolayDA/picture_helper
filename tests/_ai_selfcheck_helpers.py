"""Importierbare Spawn-Ziele für die KI-Selbsttest-Tests (#308).

Bewusst OHNE ``test_``-Präfix: pytest sammelt die Datei nicht als Testmodul,
aber der per ``spawn`` gestartete Kindprozess kann die Ziel-Funktionen über
ihren Modulnamen importieren (``spawn`` picklet Funktionen by-reference). Die
Funktionen ahmen die Antworten von ``bgremover.ai_process._ai_selfcheck_child``
nach, ohne ``rembg`` zu benötigen.
"""
from __future__ import annotations

import time
from multiprocessing.connection import Connection


def ok_target(conn: Connection) -> None:
    """Meldet Erfolg (wie ein geglückter rembg-Import)."""
    conn.send(("ok",))
    conn.close()


def error_target(conn: Connection) -> None:
    """Meldet einen kontrollierten Fehler (wie ein PackageNotFoundError)."""
    conn.send(("error", "absichtlicher Fehler"))
    conn.close()


def raising_target(conn: Connection) -> None:
    """Stirbt ohne Antwort → der Eltern-Prozess sieht EOF."""
    raise RuntimeError("boom")


def slow_target(conn: Connection) -> None:
    """Antwortet erst nach langer Zeit → löst die Timeout-Behandlung aus."""
    time.sleep(60)
    conn.send(("ok",))
    conn.close()
