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
    verwendet die Session über alle Anfragen hinweg wieder (#229).

    Protokoll (Befund #285/3 – große PNGs nicht picklen): Ein kleiner
    Steuer-Frame über ``send``/``recv`` (gepickelt), das große PNG getrennt als
    roher Byte-Frame über ``send_bytes``/``recv_bytes``. Anfragen sind
    ``("warmup",)`` bzw. ``("infer",)`` gefolgt vom Eingabe-PNG als Byte-Frame.
    Antworten sind ``("ok",)`` (Warmup), ``("ok",)`` gefolgt vom Ergebnis-PNG
    als Byte-Frame (Inferenz) oder ``("error", message)``. Backend-Fehler werden
    an den Elternprozess gemeldet, ohne den Prozess zu beenden – so kann ein
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
            operation = message[0]
            # Das große Eingabe-PNG kommt als roher Byte-Frame nach (kein
            # Pickle-Vollkopie, Befund #285/3) und wird sofort wieder
            # freigegeben, sobald es nicht mehr gebraucht wird (Befund #285/2).
            payload: bytes | None = None
            if operation == "infer":
                try:
                    payload = conn.recv_bytes()
                except (EOFError, OSError):
                    return
            try:
                if remove is None:
                    # Erst hier den teuren Import ausführen (Befund N7). Die
                    # Session ZUERST aufbauen und ``remove`` erst danach setzen:
                    # scheitert ``new_session`` transient (Speicherdruck,
                    # Modell-Download), bleibt ``remove`` None und der nächste
                    # Request baut die Session erneut – genau einmal – auf, statt
                    # pro Aufruf mit ``session=None`` neu zu laden (Befund #285/1).
                    from rembg import new_session
                    from rembg import remove as rembg_remove
                    session = new_session()
                    remove = rembg_remove
                if operation == "warmup":
                    remove(_warmup_png(), session=session)
                    conn.send(("ok",))
                elif operation == "infer":
                    result = remove(payload, session=session)
                    payload = None            # Eingabe-PNG sofort freigeben (#285/2)
                    conn.send(("ok",))
                    conn.send_bytes(result)   # Ergebnis als roher Byte-Frame (#285/3)
                    del result
                else:
                    conn.send(("error", f"Unbekannte Operation: {operation!r}"))
            except Exception as exc:  # noqa: BLE001 – an Eltern melden, Prozess weiterlaufen lassen
                conn.send(("error", f"{type(exc).__name__}: {exc}"))
            finally:
                # Vor dem nächsten, blockierenden ``recv()`` alle Puffer der
                # Anfrage freigeben, damit der leerlaufende Kindprozess das
                # letzte PNG nicht dauerhaft hält (Befund #285/2).
                del message, payload
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
        # Schützt NUR die Veröffentlichung/Übernahme von ``_proc``/``_conn``
        # gegen ``request_stop``. Bewusst getrennt vom großen ``_lock``: so muss
        # ``request_stop`` nie auf einen pollenden Worker warten. Stets innerste
        # Sperre und nie über das langsame ``kill()``/``join()`` gehalten.
        self._proc_lock = threading.Lock()
        # Ein ``request_stop``, das eintrifft, BEVOR der frisch gestartete
        # Prozess veröffentlicht ist, wird hier vermerkt und vom Start auf genau
        # diesen Prozess nachgezogen (Befund #285/4).
        self._stop_pending = False

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
        self._request("warmup", None, should_cancel, expects_result=False)

    def infer(
        self, png_bytes: bytes, should_cancel: Callable[[], bool] | None = None,
    ) -> bytes:
        """Entfernt den Hintergrund von *png_bytes* im Kindprozess.

        Blockiert pollend bis zum Ergebnis. Liefert ``should_cancel`` zwischen-
        durch ``True``, wird der Kindprozess beendet und ``InferenceCancelled``
        geworfen. Stirbt der Prozess unerwartet, kommt ``InferenceError``.
        """
        result = self._request("infer", png_bytes, should_cancel, expects_result=True)
        if not isinstance(result, bytes):
            raise InferenceError(
                f"Unerwartete Antwort des Inferenzprozesses: {type(result).__name__}"
            )
        return result

    def _request(
        self,
        op: str,
        payload: bytes | None,
        should_cancel: Callable[[], bool] | None,
        *,
        expects_result: bool,
    ) -> bytes | None:
        cancelled = should_cancel or (lambda: False)
        with self._lock:
            self._ensure_started()
            conn = self._conn
            assert conn is not None  # _ensure_started garantiert die Verbindung
            try:
                # Kleiner Steuer-Frame gepickelt; das große PNG getrennt als
                # roher Byte-Frame, der nicht durch Pickle vollkopiert wird
                # (Befund #285/3).
                conn.send((op,))
                if payload is not None:
                    conn.send_bytes(payload)
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
                    response = conn.recv()
                    status = response[0]
                    # Das Ergebnis-PNG folgt nur bei Erfolg einer Inferenz und
                    # wird als roher Byte-Frame eingelesen (Befund #285/3).
                    result = conn.recv_bytes() if status == "ok" and expects_result else None
                except (EOFError, OSError) as exc:
                    # EOFError: Gegenseite sauber geschlossen. OSError (z. B.
                    # ConnectionResetError): Prozess starb mitten in der Antwort.
                    self._cleanup()
                    raise InferenceError(
                        f"Inferenzprozess hat die Verbindung geschlossen: {exc}"
                    ) from exc
                if status == "ok":
                    return result
                raise InferenceError(str(response[1]))

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
        with self._proc_lock:
            self._proc = proc
            self._conn = parent_conn
            # Einen genau während ``proc.start()`` eingetroffenen Stop auf den
            # frischen Prozess nachziehen (Befund #285/4): ``request_stop`` sah
            # ``_proc`` evtl. noch als None und hätte ihn sonst verfehlt.
            stop_pending, self._stop_pending = self._stop_pending, False
        if stop_pending:
            with contextlib.suppress(Exception):
                proc.kill()

    def request_stop(self) -> None:
        """Beendet den Kindprozess sofort per ``SIGKILL`` (aus jedem Thread sicher).

        Entwertet eine laufende, nicht unterbrechbare Inferenz, sodass der
        wartende Worker-Thread seinen Poll-Loop verlässt. Verändert bewusst die
        Python-Handles NICHT – das Aufräumen übernimmt der Anfrage-Thread (unter
        ``_lock``) bzw. ``shutdown``. Damit gibt es keinen Daten-Race auf
        ``_proc``/``_conn`` zwischen UI- und Worker-Thread.

        Trifft der Stop GENAU während ``proc.start()`` ein (``_proc`` noch nicht
        veröffentlicht), greift er den Prozess nicht direkt; das Setzen von
        ``_stop_pending`` unter ``_proc_lock`` sorgt dafür, dass der Start ihn
        nachzieht und den frischen Prozess killt (Befund #285/4).
        """
        with self._proc_lock:
            self._stop_pending = True
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
        # Einen evtl. noch ausstehenden Stop zurücksetzen: der Prozess wird hier
        # ohnehin beendet, und ein späterer Neustart (Wiederverwendung) darf den
        # frischen Prozess nicht fälschlich sofort killen (Befund #285/4).
        with self._proc_lock:
            self._stop_pending = False
        self._cleanup()

    def _cleanup(self) -> None:
        """Schließt die Verbindung und beendet/erntet den Kindprozess (idempotent)."""
        # Handles unter ``_proc_lock`` atomar entnehmen (gegen ``request_stop``),
        # das langsame ``kill()``/``join()`` aber außerhalb der Sperre fahren,
        # damit ``request_stop`` nie darauf wartet.
        with self._proc_lock:
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


# ─────────────────────────────────────────────────────────────────────────
# KI-Selbsttest für gebaute --ai-Artefakte (Befund #308)
# ─────────────────────────────────────────────────────────────────────────

def _ai_selfcheck_child(conn: Connection) -> None:
    """Kindprozess des KI-Selbsttests: importiert die komplette rembg-Kette.

    Der Import löst u. a. den ``pymatting``-Metadaten-Read aus – genau der Pfad,
    der im gebauten ``--ai``-``.dmg`` mit ``PackageNotFoundError: No package
    metadata was found for pymatting`` starb (#306), weil ``collect_all`` Code,
    aber nicht die ``*.dist-info``-Metadaten der Transitiv-Deps mitnimmt. Bewusst
    KEIN ``new_session()``-Aufruf: der lüde ein Modell aus dem Netz; hier zählt
    nur Import + Metadaten-Auflösung, damit der Test ohne Netz CI-stabil bleibt.

    Top-Level-Funktion, damit ``spawn`` sie über das Modul picklen/importieren
    kann (wie ``_serve``).
    """
    try:
        from rembg import new_session  # noqa: F401 – Import löst die Metadaten-Auflösung aus
        conn.send(("ok",))
    except BaseException as exc:  # noqa: BLE001 – jeder Import-/Metadatenfehler ist ein Fail
        conn.send(("error", f"{type(exc).__name__}: {exc}"))
    finally:
        conn.close()


def run_ai_selfcheck(
    *,
    target: Callable[[Connection], None] = _ai_selfcheck_child,
    timeout: float = 120.0,
) -> tuple[bool, str]:
    """Prüft headless, dass die rembg-Kette im Spawn-Kindprozess importierbar ist.

    Startet – wie die echte Inferenz – einen per ``spawn`` erzeugten Kindprozess
    (im eingefrorenen Bundle relauncht das dieselbe Binärdatei) und lässt ihn die
    rembg-Kette importieren. So wird der TATSÄCHLICH gescheiterte Pfad aus #306
    über den Spawn-Kindprozess geübt, nicht nur ein In-Process-Import. Kein
    Netz/Modell-Download. *target* ist für Tests injizierbar.

    Gibt ``(ok, meldung)`` zurück.
    """
    ctx = multiprocessing.get_context("spawn")
    parent_conn, child_conn = ctx.Pipe()
    proc = ctx.Process(target=target, args=(child_conn,), daemon=True)
    proc.start()
    # Das Kind-Ende gehört dem Kindprozess; im Eltern schließen, damit ein
    # Prozesstod hier als EOF sichtbar wird.
    child_conn.close()
    response: tuple[object, ...] | None = None
    try:
        if parent_conn.poll(timeout):
            received = parent_conn.recv()
            response = received if isinstance(received, tuple) else (received,)
    except (EOFError, OSError) as exc:
        return False, f"KI-Selbsttest: Kindprozess ohne Antwort beendet ({exc})"
    finally:
        with contextlib.suppress(OSError):
            parent_conn.close()
        with contextlib.suppress(Exception):
            if proc.is_alive():
                proc.kill()
            proc.join(_KILL_JOIN_TIMEOUT_S)
    if response is None:
        return False, (
            f"KI-Selbsttest: Zeitüberschreitung nach {timeout:.0f}s "
            "(kein Import-Ergebnis)"
        )
    if response and response[0] == "ok":
        return True, "KI-Selbsttest: rembg-Kette inkl. Metadaten importierbar"
    message = response[1] if len(response) > 1 else "unbekannter Fehler"
    return False, f"KI-Selbsttest fehlgeschlagen: {message}"
