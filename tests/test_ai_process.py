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
import gc
import multiprocessing
import os
import subprocess
import sys
import threading
import time
import types
import weakref
from collections.abc import Callable, Iterator
from multiprocessing.connection import Connection
from unittest.mock import patch

import pytest

from bgremover.ai_process import (
    InferenceCancelled,
    InferenceError,
    InferenceProcess,
    _get_spawn_context,
    _serve,
)

# ─────────────────────────────────────────────────────────────
# Top-Level-Server für echte spawn-Subprozesse (müssen importierbar sein)
# ─────────────────────────────────────────────────────────────

def _echo_server(conn: Connection) -> None:
    """Beantwortet Anfragen ohne rembg im #285-Protokoll: kleiner Steuer-Frame
    plus rohen Byte-Frame; gibt das Inferenz-PNG unverändert zurück."""
    while True:
        try:
            message = conn.recv()
        except EOFError:
            return
        if message is None:
            return
        operation = message[0]
        if operation == "warmup":
            conn.send(("ok",))
        elif operation == "infer":
            payload = conn.recv_bytes()
            conn.send(("ok",))
            conn.send_bytes(payload)
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


def _error_server(conn: Connection) -> None:
    """Meldet auf jede Anfrage einen Backend-Fehler, ohne den Prozess zu beenden."""
    while True:
        try:
            message = conn.recv()
        except EOFError:
            return
        if message is None:
            return
        if message[0] == "infer":
            conn.recv_bytes()   # Eingabe-Frame konsumieren, Protokoll synchron halten
        conn.send(("error", "backend boom"))


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
            assert parent_conn.recv() == ("ok",)
            parent_conn.send(("infer",))
            parent_conn.send_bytes(b"abc")
            assert parent_conn.recv() == ("ok",)
            assert parent_conn.recv_bytes() == b"out:abc"
            parent_conn.send(("infer",))
            parent_conn.send_bytes(b"xyz")
            assert parent_conn.recv() == ("ok",)
            assert parent_conn.recv_bytes() == b"out:xyz"
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
            parent_conn.send(("infer",))
            parent_conn.send_bytes(b"boom")
            status, message = parent_conn.recv()
            assert status == "error"
            assert "backend kaputt" in message
            parent_conn.send(("infer",))           # Prozess lebt weiter
            parent_conn.send_bytes(b"fine")
            assert parent_conn.recv() == ("ok",)
            assert parent_conn.recv_bytes() == b"ok"
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


def test_serve_rebuilds_session_after_transient_new_session_error() -> None:
    """Befund #285/1: Scheitert ``new_session()`` einmal transient, baut der
    nächste Request die Session NEU und GENAU EINMAL auf. ``remove`` wird erst
    nach einer gültigen Session gesetzt – nie mit ``session=None`` aufgerufen
    (sonst lüde rembg das Modell pro Aufruf neu, die #229-Garantie ginge verloren)."""
    new_session_calls: list[object] = []
    seen_sessions: list[object] = []
    sentinel = object()

    def flaky_new_session(*_a: object, **_k: object) -> object:
        new_session_calls.append(object())
        if len(new_session_calls) == 1:
            raise RuntimeError("transienter Init-Fehler")
        return sentinel

    def fake_remove(payload: bytes, session: object = None) -> bytes:
        seen_sessions.append(session)
        return b"out"

    parent_conn, child_conn = multiprocessing.Pipe()
    thread = threading.Thread(target=_serve, args=(child_conn,))
    with patch.dict(sys.modules, {"rembg": _fake_rembg(fake_remove, flaky_new_session)}):
        thread.start()
        try:
            # Erster Versuch: new_session scheitert → Fehler, KEIN remove-Aufruf.
            parent_conn.send(("infer",))
            parent_conn.send_bytes(b"a")
            status, message = parent_conn.recv()
            assert status == "error"
            assert "transienter Init-Fehler" in message
            # Zweiter Versuch: Session wird neu aufgebaut, remove läuft korrekt.
            parent_conn.send(("infer",))
            parent_conn.send_bytes(b"b")
            assert parent_conn.recv() == ("ok",)
            assert parent_conn.recv_bytes() == b"out"
            # Dritter Versuch: Session wird wiederverwendet (kein erneuter Aufbau).
            parent_conn.send(("infer",))
            parent_conn.send_bytes(b"c")
            assert parent_conn.recv() == ("ok",)
            assert parent_conn.recv_bytes() == b"out"
        finally:
            parent_conn.send(None)
            thread.join(timeout=5)

    assert not thread.is_alive()
    assert len(new_session_calls) == 2              # 1× Fehler + 1× erfolgreich
    assert seen_sessions == [sentinel, sentinel]    # nie remove(session=None)


class _Trackable:
    """Weakref-fähiger Stellvertreter eines ``recv_bytes``-Payloads.

    ``bytes`` selbst unterstützen keine Weakrefs und werden nicht vom GC
    erfasst; der gefälschte ``remove`` ignoriert den Inhalt ohnehin."""
    __slots__ = ("data", "__weakref__")

    def __init__(self, data: bytes) -> None:
        self.data = data


class _PayloadTrackingConn:
    """Verbindungs-Wrapper, der jedes ``recv_bytes``-Payload in ein
    weakref-fähiges Objekt hüllt, um seine Freigabe nachweisen zu können."""

    def __init__(self, conn: Connection) -> None:
        self._conn = conn
        self.payload_refs: list[weakref.ref[_Trackable]] = []

    def recv(self) -> object:
        return self._conn.recv()

    def recv_bytes(self) -> _Trackable:
        wrapped = _Trackable(self._conn.recv_bytes())
        self.payload_refs.append(weakref.ref(wrapped))
        return wrapped

    def send(self, obj: object) -> None:
        self._conn.send(obj)

    def send_bytes(self, buf: bytes) -> None:
        self._conn.send_bytes(buf)

    def close(self) -> None:
        self._conn.close()


def test_serve_releases_input_payload_when_idle() -> None:
    """Befund #285/2: Im Leerlauf (blockierend im nächsten ``recv()``) hält die
    Schleife das Eingabe-PNG der letzten Anfrage nicht mehr – die Payload ist
    freigegeben, statt >100 MiB dauerhaft zu binden."""
    def fake_remove(payload: object, session: object = None) -> bytes:
        return b"out"

    parent_conn, child_conn = multiprocessing.Pipe()
    tracking = _PayloadTrackingConn(child_conn)
    thread = threading.Thread(target=_serve, args=(tracking,))
    with patch.dict(sys.modules, {"rembg": _fake_rembg(fake_remove, lambda *a, **k: object())}):
        thread.start()
        try:
            parent_conn.send(("infer",))
            parent_conn.send_bytes(b"A" * 4096)
            assert parent_conn.recv() == ("ok",)
            assert parent_conn.recv_bytes() == b"out"
            # Das Kind läuft danach in den nächsten, blockierenden recv(); dort
            # darf das Eingabe-PNG nicht mehr referenziert sein.
            deadline = time.monotonic() + 5.0
            released = False
            while time.monotonic() < deadline:
                gc.collect()
                if tracking.payload_refs and tracking.payload_refs[0]() is None:
                    released = True
                    break
                time.sleep(0.01)
            assert tracking.payload_refs, "recv_bytes wurde nie aufgerufen"
            assert released, "Eingabe-PNG bleibt im Leerlauf referenziert (#285/2)"
        finally:
            parent_conn.send(None)
            thread.join(timeout=5)
    assert not thread.is_alive()


# ─────────────────────────────────────────────────────────────
# InferenceProcess – echte spawn-Subprozesse
# ─────────────────────────────────────────────────────────────

def test_appimage_spawn_uses_bundled_python(monkeypatch, tmp_path) -> None:
    """#633: python-appimage setzt ``sys.executable`` auf die äußere
    AppImage. Spawn muss stattdessen den eingebetteten Python-Wrapper nutzen,
    damit das AppImage nicht rekursiv neu startet."""
    appimage = tmp_path / "BgRemover.AppImage"
    bundled_python = tmp_path / "usr" / "bin" / (
        f"python{sys.version_info.major}.{sys.version_info.minor}"
    )
    bundled_python.parent.mkdir(parents=True)
    bundled_python.touch()
    expected_context = object()
    selected: list[str] = []

    monkeypatch.setenv("APPDIR", str(tmp_path))
    monkeypatch.setenv("APPIMAGE_COMMAND", str(appimage))
    monkeypatch.setattr(sys, "executable", str(appimage))
    monkeypatch.setattr(multiprocessing, "set_executable", selected.append)
    monkeypatch.setattr(
        multiprocessing,
        "get_context",
        lambda method: expected_context if method == "spawn" else None,
    )

    assert _get_spawn_context() is expected_context
    assert selected == [str(bundled_python)]


def test_appimage_spawn_override_requires_python_appimage_patch(
    monkeypatch, tmp_path,
) -> None:
    """Bloße, fremde AppImage-Umgebungsvariablen dürfen einen normalen
    Python-Prozess nicht auf einen anderen Interpreter umlenken."""
    bundled_python = tmp_path / "usr" / "bin" / (
        f"python{sys.version_info.major}.{sys.version_info.minor}"
    )
    bundled_python.parent.mkdir(parents=True)
    bundled_python.touch()
    selected: list[str] = []

    monkeypatch.setenv("APPDIR", str(tmp_path))
    monkeypatch.setenv("APPIMAGE_COMMAND", str(tmp_path / "BgRemover.AppImage"))
    monkeypatch.setattr(multiprocessing, "set_executable", selected.append)
    monkeypatch.setattr(multiprocessing, "get_context", lambda method: method)

    assert _get_spawn_context() == "spawn"
    assert selected == []

def test_infer_through_real_subprocess_echoes_and_reuses() -> None:
    """Ende-zu-Ende über einen echten Subprozess: Inferenz liefert ein Ergebnis,
    und der Prozess bleibt für die Wiederverwendung am Leben."""
    with _running(_echo_server) as proc:
        assert proc.infer(b"hello") == b"hello"
        assert proc.is_alive
        assert proc.infer(b"world") == b"world"
        assert proc.is_alive


def test_infer_roundtrips_large_payload_via_raw_byte_frames() -> None:
    """Befund #285/3: Große PNGs reisen als rohe Byte-Frames (kein
    Pickle-Vollkopie) korrekt durch die Pipe – auch ein mehrere MiB großes
    Bild kommt unversehrt zurück."""
    big = bytes(range(256)) * (4 * 1024)   # ~1 MiB, nicht trivial komprimierbar
    with _running(_echo_server) as proc:
        assert proc.infer(big) == big
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


def test_pending_stop_is_carried_onto_freshly_started_process() -> None:
    """Befund #285/4: Ein ``request_stop``, das eintrifft, BEVOR der frische
    Prozess veröffentlicht ist, wird vom Start nachgezogen – die nächste Anfrage
    trifft keinen lebenden Prozess an, statt den frischen Prozess zu verfehlen."""
    proc = InferenceProcess(target=_blocking_server)
    try:
        # Stop vormerken, solange noch kein Prozess existiert (simuliert das enge
        # Fenster, in dem ``request_stop`` ``_proc`` noch als None sähe).
        proc.request_stop()
        # Der nächste Request startet einen Prozess, der den nachgezogenen Stop
        # sofort kassiert → kein endloser Poll, sondern ein gemeldeter Fehler.
        with pytest.raises(InferenceError):
            proc.infer(b"x")
        assert not proc.is_alive
    finally:
        proc.shutdown()


def test_shutdown_clears_pending_stop_for_reuse() -> None:
    """Befund #285/4: ``shutdown`` setzt einen ausstehenden Stop zurück, damit
    ein wiederverwendeter ``InferenceProcess`` den nächsten frischen Prozess
    nicht fälschlich sofort killt."""
    proc = InferenceProcess(target=_echo_server)
    try:
        proc.request_stop()   # markiert ausstehenden Stop (kein Prozess da)
        proc.shutdown()       # muss die Markierung löschen
        assert proc.infer(b"z") == b"z"   # frischer Prozess überlebt
        assert proc.is_alive
    finally:
        proc.shutdown()


def test_crashed_process_reports_error_without_hanging() -> None:
    with _running(_crashing_server) as proc:
        with pytest.raises(InferenceError):
            proc.infer(b"x")
        assert not proc.is_alive


def test_backend_error_surfaces_and_keeps_process_alive() -> None:
    """Ein gemeldeter Backend-Fehler (``("error", …)``) wird als
    ``InferenceError`` an den Aufrufer durchgereicht, ohne den Kindprozess zu
    beenden – ein Folgeauftrag wird weiter bedient."""
    with _running(_error_server) as proc:
        with pytest.raises(InferenceError, match="backend boom"):
            proc.infer(b"x")
        assert proc.is_alive
        with pytest.raises(InferenceError, match="backend boom"):
            proc.warmup()
        assert proc.is_alive


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
