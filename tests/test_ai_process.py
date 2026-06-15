"""Tests für die Out-of-Process-Inferenz (``bgremover.ai_process``, Befund #270).

Zwei Ebenen:

* ``_serve`` (die Kindprozess-Schleife) wird **in-process** in einem Thread mit
  einem gefälschten ``rembg``-Modul geprüft – hermetisch, ohne onnxruntime: Lädt
  die Session genau einmal (#229) und meldet Backend-Fehler, ohne zu sterben.
* ``InferenceProcess`` wird mit **echten spawn-Subprozessen** geprüft (Echo-,
  Block- und Crash-Server statt rembg): Abbruch und Schließen beenden einen
  laufenden – auch hängenden – Prozess hart und beschränkt, und nach einem Kill
  startet die nächste Anfrage einen frischen Prozess.
"""
from __future__ import annotations

import contextlib
import multiprocessing
import os
import subprocess
import sys
import threading
import time
import types
from collections.abc import Callable, Iterator
from multiprocessing.connection import Connection
from unittest.mock import patch

import pytest

from bgremover.ai_process import (
    InferenceCancelled,
    InferenceError,
    InferenceProcess,
    _serve,
)

# ─────────────────────────────────────────────────────────────
# Top-Level-Server für echte spawn-Subprozesse (müssen importierbar sein)
# ─────────────────────────────────────────────────────────────

def _echo_server(conn: Connection) -> None:
    """Beantwortet Anfragen ohne rembg: gibt Inferenz-Bytes unverändert zurück."""
    while True:
        try:
            message = conn.recv()
        except EOFError:
            return
        if message is None:
            return
        operation = message[0]
        if operation == "warmup":
            conn.send(("ok", None))
        elif operation == "infer":
            conn.send(("ok", message[1]))
        else:
            conn.send(("error", f"unknown {operation!r}"))


def _blocking_server(conn: Connection) -> None:
    """Nimmt die erste Anfrage an und antwortet NIE – simuliert eine nicht
    unterbrechbare native Inferenz, die nur per Prozess-Kill endet."""
    conn.recv()
    while True:
        time.sleep(3600)


def _crashing_server(conn: Connection) -> None:
    """Stirbt nach der ersten Anfrage hart (simuliert ein abstürzendes Backend)."""
    conn.recv()
    os._exit(1)


@contextlib.contextmanager
def _running(target: Callable[[Connection], None]) -> Iterator[InferenceProcess]:
    """Liefert eine ``InferenceProcess`` mit *target* und beendet sie zuverlässig."""
    proc = InferenceProcess(target=target)
    try:
        yield proc
    finally:
        proc.shutdown()


def _run_infer_in_thread(
    proc: InferenceProcess,
    should_cancel: Callable[[], bool] | None = None,
) -> tuple[threading.Thread, dict[str, object]]:
    """Startet ``proc.infer`` in einem Thread und sammelt das Ergebnis."""
    outcome: dict[str, object] = {}

    def run() -> None:
        try:
            outcome["result"] = proc.infer(b"payload", should_cancel=should_cancel)
        except InferenceCancelled:
            outcome["cancelled"] = True
        except InferenceError as exc:
            outcome["error"] = exc

    thread = threading.Thread(target=run)
    thread.start()
    return thread, outcome


# ─────────────────────────────────────────────────────────────
# _serve – Kindprozess-Schleife, in-process mit gefälschtem rembg
# ─────────────────────────────────────────────────────────────

def _fake_rembg(
    remove_impl: Callable[..., bytes],
    new_session_impl: Callable[..., object],
) -> types.ModuleType:
    module = types.ModuleType("rembg")
    module.remove = remove_impl  # type: ignore[attr-defined]
    module.new_session = new_session_impl  # type: ignore[attr-defined]
    return module


def test_serve_loads_session_once_and_reuses_it() -> None:
    """#229: Der Warmup erzeugt genau EINE Session; jeder ``remove``-Aufruf
    (Warmup + Inferenzen) bekommt dieselbe Instanz – über die gesamte
    Prozess-Lebenszeit nur ein ``new_session()``."""
    new_session_calls: list[object] = []
    seen_sessions: list[object] = []
    sentinel = object()

    def fake_new_session(*_a: object, **_k: object) -> object:
        new_session_calls.append(sentinel)
        return sentinel

    def fake_remove(payload: bytes, session: object = None) -> bytes:
        seen_sessions.append(session)
        return b"out:" + payload

    parent_conn, child_conn = multiprocessing.Pipe()
    thread = threading.Thread(target=_serve, args=(child_conn,))
    with patch.dict(sys.modules, {"rembg": _fake_rembg(fake_remove, fake_new_session)}):
        thread.start()
        try:
            parent_conn.send(("warmup",))
            assert parent_conn.recv() == ("ok", None)
            parent_conn.send(("infer", b"abc"))
            assert parent_conn.recv() == ("ok", b"out:abc")
            parent_conn.send(("infer", b"xyz"))
            assert parent_conn.recv() == ("ok", b"out:xyz")
        finally:
            parent_conn.send(None)  # Sentinel → _serve kehrt zurück
            thread.join(timeout=5)

    assert not thread.is_alive()
    assert len(new_session_calls) == 1            # Session genau einmal erzeugt
    assert len(seen_sessions) == 3                # Warmup + zwei Inferenzen
    assert all(s is sentinel for s in seen_sessions)


def test_serve_reports_backend_error_and_keeps_serving() -> None:
    """Ein Backend-Fehler wird als ``("error", …)`` gemeldet, ohne den Prozess
    zu beenden – ein Folgeauftrag wird weiter bedient."""
    def fake_remove(payload: bytes, session: object = None) -> bytes:
        if payload == b"boom":
            raise RuntimeError("backend kaputt")
        return b"ok"

    parent_conn, child_conn = multiprocessing.Pipe()
    thread = threading.Thread(target=_serve, args=(child_conn,))
    with patch.dict(sys.modules, {"rembg": _fake_rembg(fake_remove, lambda *a, **k: object())}):
        thread.start()
        try:
            parent_conn.send(("infer", b"boom"))
            status, message = parent_conn.recv()
            assert status == "error"
            assert "backend kaputt" in message
            parent_conn.send(("infer", b"fine"))   # Prozess lebt weiter
            assert parent_conn.recv() == ("ok", b"ok")
        finally:
            parent_conn.send(None)
            thread.join(timeout=5)
    assert not thread.is_alive()


def test_serve_reports_unknown_operation() -> None:
    parent_conn, child_conn = multiprocessing.Pipe()
    thread = threading.Thread(target=_serve, args=(child_conn,))
    with patch.dict(sys.modules, {"rembg": _fake_rembg(lambda *a, **k: b"", lambda *a, **k: object())}):
        thread.start()
        try:
            parent_conn.send(("bogus",))
            status, message = parent_conn.recv()
            assert status == "error"
            assert "bogus" in message
        finally:
            parent_conn.send(None)
            thread.join(timeout=5)
    assert not thread.is_alive()


# ─────────────────────────────────────────────────────────────
# InferenceProcess – echte spawn-Subprozesse
# ─────────────────────────────────────────────────────────────

def test_infer_through_real_subprocess_echoes_and_reuses() -> None:
    """Ende-zu-Ende über einen echten Subprozess: Inferenz liefert ein Ergebnis,
    und der Prozess bleibt für die Wiederverwendung am Leben."""
    with _running(_echo_server) as proc:
        assert proc.infer(b"hello") == b"hello"
        assert proc.is_alive
        assert proc.infer(b"world") == b"world"
        assert proc.is_alive


def test_warmup_then_infer_uses_same_process() -> None:
    with _running(_echo_server) as proc:
        proc.warmup()
        assert proc.is_alive
        first_pid = proc._proc.pid  # type: ignore[union-attr]
        assert proc.infer(b"data") == b"data"
        assert proc._proc.pid == first_pid  # type: ignore[union-attr]


def test_cancel_during_blocked_inference_kills_process() -> None:
    """Akzeptanzkriterium „Cancel“ + „blockierter nativer Aufruf“: Ein Abbruch
    beendet die hängende Inferenz hart, der Worker kehrt mit
    ``InferenceCancelled`` zurück und die Prozessressourcen sind frei."""
    with _running(_blocking_server) as proc:
        cancel = threading.Event()
        thread, outcome = _run_infer_in_thread(proc, should_cancel=cancel.is_set)
        time.sleep(0.2)                       # Worker hängt im Poll-Loop
        assert proc.is_alive
        cancel.set()
        thread.join(timeout=5)
        assert not thread.is_alive()
        assert outcome.get("cancelled") is True
        assert not proc.is_alive              # Prozess beendet → Ressourcen frei


def test_request_stop_unblocks_running_inference() -> None:
    """Akzeptanzkriterium „Schließen während laufender Inferenz“: ``request_stop``
    (aus dem UI-Thread) beendet den hängenden Prozess, der wartende Worker löst
    sich auf, ohne den GUI-Prozess zu gefährden."""
    with _running(_blocking_server) as proc:
        thread, outcome = _run_infer_in_thread(proc)
        time.sleep(0.2)
        assert proc.is_alive
        started = time.monotonic()
        proc.request_stop()
        thread.join(timeout=5)
        elapsed = time.monotonic() - started
        assert not thread.is_alive()
        assert outcome.get("error") is not None   # Prozesstod wird als Fehler gemeldet
        assert not proc.is_alive
        assert elapsed < 2.0                       # beschränkt, kein Hänger


def test_crashed_process_reports_error_without_hanging() -> None:
    with _running(_crashing_server) as proc:
        with pytest.raises(InferenceError):
            proc.infer(b"x")
        assert not proc.is_alive


def test_process_restarts_after_shutdown() -> None:
    """Nach einem Kill (Abbruch/Schließen räumt die Handles ab) startet die
    nächste Anfrage lazy einen frischen Prozess – die KI bleibt funktional."""
    proc = InferenceProcess(target=_echo_server)
    try:
        assert proc.infer(b"a") == b"a"
        first_pid = proc._proc.pid  # type: ignore[union-attr]
        proc.shutdown()                           # killt + räumt Handles ab
        assert not proc.is_alive
        assert proc.infer(b"b") == b"b"            # frischer Prozess
        assert proc.is_alive
        assert proc._proc.pid != first_pid  # type: ignore[union-attr]
    finally:
        proc.shutdown()


def test_shutdown_is_idempotent_and_kills_process() -> None:
    proc = InferenceProcess(target=_echo_server)
    assert proc.infer(b"a") == b"a"
    assert proc.is_alive
    proc.shutdown()
    assert not proc.is_alive
    proc.shutdown()                                # zweiter Aufruf wirft nicht
    assert not proc.is_alive


def test_importing_ai_process_does_not_import_rembg() -> None:
    """N7-Analog: ``import bgremover.ai_process`` darf weder ``rembg`` noch
    ``onnxruntime`` laden – der teure Import lebt nur im Kindprozess."""
    code = (
        "import sys, bgremover.ai_process; "
        "assert 'rembg' not in sys.modules, 'rembg eager-importiert'; "
        "assert 'onnxruntime' not in sys.modules, 'onnxruntime eager-importiert'; "
        "print('OK')"
    )
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(p for p in sys.path if p))
    result = subprocess.run([sys.executable, "-c", code], env=env,
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0 and "OK" in result.stdout, (
        f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )
