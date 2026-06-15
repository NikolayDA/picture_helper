"""rembg/ONNX-Inferenz in einem separaten Prozess (Befund #270).

Die native ONNX-Inferenz ist nicht kooperativ unterbrechbar. Lief sie – wie
früher – in einem ``QThread``, blieb beim Schließen nur ``QThread.terminate()``
als Notausgang. ``terminate()`` beendet den Thread an beliebiger Stelle und kann
nativen Code (onnxruntime) in undefiniertem Zustand hinterlassen – bis hin zu
Abstürzen oder beschädigten Locks. Genau das Risiko, das dieses Modul beseitigt.

Stattdessen läuft die Inferenz hier in einem eigenen, per ``spawn`` gestarteten
Prozess (``InferenceProcess``):

* Der Kindprozess lädt die rembg-Session **einmalig** und bedient darüber alle
  Anfragen wieder (wie zuvor im Thread, #229).
* Der Eltern-Worker (im ``QThread``) sendet nur eine Anfrage und **pollt** auf
  das Ergebnis – ein kooperativ unterbrechbarer Python-Loop, kein blockierender
  C-Aufruf. Damit ist der Worker-Thread jederzeit sauber beendbar.
* Beim Abbruch oder Schließen wird der Kindprozess **hart beendet**
  (``SIGKILL``). Da die native onnxruntime nur in diesem Prozess lebt, gefährdet
  das den GUI-Prozess samt seiner nativen Bibliotheken nicht.

``spawn`` wird plattformübergreifend erzwungen (macOS + Linux): ``fork`` würde
den kompletten GUI-Prozess samt Qt-/Thread-Zustand kopieren und kann in einer
laufenden Qt-Anwendung deadlocken. Der teure ``rembg``/``onnxruntime``-Import
läuft bewusst erst im Kindprozess – ``import bgremover.ai_process`` zieht weder
rembg noch onnxruntime (Start-Latenz, Befund N7).
"""
from __future__ import annotations

import contextlib
import io
import multiprocessing
import threading
from collections.abc import Callable
from multiprocessing.connection import Connection
from multiprocessing.process import BaseProcess

from PIL import Image

# Poll-Intervall (Sekunden), in dem der wartende Worker-Thread das Ergebnis
# abfragt und dazwischen Abbruch/Prozesstod prüft. Klein genug, dass ein
# Abbruch praktisch sofort greift und der kooperative ``QThread``-Shutdown lange
# vor dem terminate()-Fallback (5 s) gelingt; groß genug, um nicht heißzulaufen.
_POLL_INTERVAL_S = 0.05
# Obergrenze (Sekunden) für das Einsammeln (``join``) eines beendeten
# Kindprozesses nach ``SIGKILL``. SIGKILL wirkt sofort; der Wert ist nur ein
# Sicherheitsnetz, damit ein hängendes ``join`` den Aufrufer nicht blockiert.
_KILL_JOIN_TIMEOUT_S = 2.0


class InferenceError(RuntimeError):
    """Inferenz fehlgeschlagen (Import-/Init-Fehler, Prozesstod, Backendfehler)."""


class InferenceCancelled(Exception):
    """Die Inferenz wurde über ``should_cancel`` abgebrochen.

    Kein Fehler, sondern der reguläre Abbruchpfad: Der Worker fängt diese
    Ausnahme und kehrt still zurück (kein ``error``-Signal).
    """


def _warmup_png() -> bytes:
    """Kleines RGBA-PNG für die Probe-Inferenz des Warmups."""
    buf = io.BytesIO()
    Image.new("RGBA", (16, 16), (0, 0, 0, 255)).save(buf, format="PNG")
    return buf.getvalue()


def _serve(conn: Connection) -> None:
    """Einstiegspunkt des Inferenz-Kindprozesses.

    Läuft, bis die Verbindung schließt (``EOFError``) oder ein Sentinel
    (``None``) kommt. Lädt rembg + Session **lazy beim ersten Bedarf** und
    verwendet die Session über alle Anfragen hinweg wieder (#229). Anfragen
    sind ``("warmup",)`` und ``("infer", png_bytes)``; geantwortet wird mit
    ``("ok", payload)`` oder ``("error", message)``. Backend-Fehler werden an
    den Elternprozess gemeldet, ohne den Prozess zu beenden – so kann ein
    Folgeversuch sauber neu beginnen.

    Top-Level-Funktion, damit ``spawn`` sie über das Modul picklen/importieren
    kann.
    """
    session: object | None = None
    remove: Callable[..., bytes] | None = None
    try:
        while True:
            try:
                message = conn.recv()
            except EOFError:
                return  # Elternprozess hat die Verbindung geschlossen
            if message is None:
                return  # Sentinel: sauberes Beenden
            try:
                if remove is None:
                    # Erst hier den teuren Import ausführen (Befund N7).
                    from rembg import new_session
                    from rembg import remove as rembg_remove
                    remove = rembg_remove
                    session = new_session()
                operation = message[0]
                if operation == "warmup":
                    remove(_warmup_png(), session=session)
                    conn.send(("ok", None))
                elif operation == "infer":
                    conn.send(("ok", remove(message[1], session=session)))
                else:
                    conn.send(("error", f"Unbekannte Operation: {operation!r}"))
            except Exception as exc:  # noqa: BLE001 – an Eltern melden, Prozess weiterlaufen lassen
                conn.send(("error", f"{type(exc).__name__}: {exc}"))
    finally:
        conn.close()


class InferenceProcess:
    """Besitzt den Inferenz-Kindprozess und vermittelt Anfragen thread-sicher.

    Genau eine Anfrage ist gleichzeitig unterwegs (ein Worker-Thread); ein
    ``Lock`` serialisiert Warmup/Inferenz gegen die Anfragen aus dem Worker.
    ``request_stop``/``shutdown`` beenden den Kindprozess hart und sind aus dem
    UI-Thread sicher aufrufbar.
    """

    def __init__(
        self,
        *,
        target: Callable[[Connection], None] = _serve,
        poll_interval: float = _POLL_INTERVAL_S,
        kill_join_timeout: float = _KILL_JOIN_TIMEOUT_S,
    ) -> None:
        # ``spawn`` erzwingen: ein frischer Prozess ohne Kopie des Qt-/Thread-
        # Zustands des GUI-Prozesses (``fork`` kann dort deadlocken).
        self._ctx = multiprocessing.get_context("spawn")
        self._target = target
        self._poll_interval = poll_interval
        self._kill_join_timeout = kill_join_timeout
        self._proc: BaseProcess | None = None
        self._conn: Connection | None = None
        # Serialisiert ``_request`` (send→poll→recv) und das Aufräumen der
        # Python-Handles. ``request_stop`` umgeht den Lock bewusst (nur SIGKILL).
        self._lock = threading.Lock()

    @property
    def is_alive(self) -> bool:
        proc = self._proc
        return proc is not None and proc.is_alive()

    def warmup(self, should_cancel: Callable[[], bool] | None = None) -> None:
        """Startet den Prozess (falls nötig) und führt eine Probe-Inferenz aus.

        Lädt im Kindprozess die Session einmalig; spätere ``infer``-Aufrufe
        nutzen sie wieder. Fehler (z. B. rembg nicht installierbar) propagieren
        als ``InferenceError``.
        """
        self._request(("warmup",), should_cancel)

    def infer(
        self, png_bytes: bytes, should_cancel: Callable[[], bool] | None = None,
    ) -> bytes:
        """Entfernt den Hintergrund von *png_bytes* im Kindprozess.

        Blockiert pollend bis zum Ergebnis. Liefert ``should_cancel`` zwischen-
        durch ``True``, wird der Kindprozess beendet und ``InferenceCancelled``
        geworfen. Stirbt der Prozess unerwartet, kommt ``InferenceError``.
        """
        result = self._request(("infer", png_bytes), should_cancel)
        if not isinstance(result, bytes):
            raise InferenceError(
                f"Unerwartete Antwort des Inferenzprozesses: {type(result).__name__}"
            )
        return result

    def _request(
        self,
        message: tuple[object, ...],
        should_cancel: Callable[[], bool] | None,
    ) -> object:
        cancelled = should_cancel or (lambda: False)
        with self._lock:
            self._ensure_started()
            conn = self._conn
            assert conn is not None  # _ensure_started garantiert die Verbindung
            try:
                conn.send(message)
            except (OSError, ValueError) as exc:
                self._cleanup()
                raise InferenceError(f"Inferenzprozess nicht erreichbar: {exc}") from exc

            while True:
                if cancelled():
                    # Abbruch: die laufende, nicht unterbrechbare Inferenz nur
                    # per Prozess-Kill stoppen – das gibt zugleich die Ressourcen
                    # frei (Befund #270, Akzeptanzkriterium „Cancel“).
                    self._cleanup()
                    raise InferenceCancelled
                proc = self._proc
                if proc is None or not proc.is_alive():
                    self._cleanup()
                    raise InferenceError("Inferenzprozess unerwartet beendet")
                try:
                    ready = conn.poll(self._poll_interval)
                except OSError as exc:
                    self._cleanup()
                    raise InferenceError(
                        f"Verbindung zum Inferenzprozess verloren: {exc}"
                    ) from exc
                if not ready:
                    continue
                try:
                    status, payload = conn.recv()
                except (EOFError, OSError) as exc:
                    # EOFError: Gegenseite sauber geschlossen. OSError (z. B.
                    # ConnectionResetError): Prozess starb mitten in der Antwort.
                    self._cleanup()
                    raise InferenceError(
                        f"Inferenzprozess hat die Verbindung geschlossen: {exc}"
                    ) from exc
                if status == "ok":
                    return payload
                raise InferenceError(str(payload))

    def _ensure_started(self) -> None:
        """Startet den Kindprozess, falls (noch) keiner lebt."""
        if self._proc is not None and self._proc.is_alive():
            return
        self._cleanup()  # toten Prozess/Verbindung sauber abräumen
        parent_conn, child_conn = self._ctx.Pipe()
        proc = self._ctx.Process(target=self._target, args=(child_conn,), daemon=True)
        proc.start()
        # Das Kind-Ende gehört dem Kindprozess; im Eltern schließen, damit ein
        # Prozesstod hier als EOF/poll-Ende sichtbar wird.
        child_conn.close()
        self._proc = proc
        self._conn = parent_conn

    def request_stop(self) -> None:
        """Beendet den Kindprozess sofort per ``SIGKILL`` (aus jedem Thread sicher).

        Entwertet eine laufende, nicht unterbrechbare Inferenz, sodass der
        wartende Worker-Thread seinen Poll-Loop verlässt. Verändert bewusst die
        Python-Handles NICHT – das Aufräumen übernimmt der Anfrage-Thread (unter
        ``_lock``) bzw. ``shutdown``. Damit gibt es keinen Daten-Race auf
        ``_proc``/``_conn`` zwischen UI- und Worker-Thread.
        """
        proc = self._proc
        if proc is not None:
            with contextlib.suppress(Exception):
                proc.kill()

    def shutdown(self) -> None:
        """Beendet den Kindprozess endgültig und räumt die Handles ab.

        Idempotent. Erwartet, dass laufende Anfrage-Threads bereits beendet sind
        (der WorkerController joined die Worker-Threads vor diesem Aufruf), und
        umgeht daher den ``_lock``, um nie auf einen pollenden Worker zu warten.
        """
        self._cleanup()

    def _cleanup(self) -> None:
        """Schließt die Verbindung und beendet/erntet den Kindprozess (idempotent)."""
        conn, proc = self._conn, self._proc
        self._conn, self._proc = None, None
        if conn is not None:
            with contextlib.suppress(OSError):
                conn.close()
        if proc is not None:
            with contextlib.suppress(Exception):
                if proc.is_alive():
                    proc.kill()
                proc.join(self._kill_join_timeout)
