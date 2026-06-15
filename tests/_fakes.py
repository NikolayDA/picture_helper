"""Test-Doubles für die Out-of-Process-Inferenz.

``FakeInference`` ersetzt ``bgremover.ai_process.InferenceProcess`` in
Controller-/Lifecycle-Tests durch eine In-Process-Variante (kein echter
Subprozess): schnell, hermetisch und ohne rembg. Es bildet die für die
Thread-Lifecycle-Buchhaltung relevante Semantik nach – ``infer`` pollt
``should_cancel`` und bricht mit ``InferenceCancelled`` ab, ``request_stop``
entwertet eine laufende Inferenz mit ``InferenceError``. Das echte
Prozess-/Kill-Verhalten prüft ``tests/test_ai_process.py`` mit echten
spawn-Subprozessen.
"""
from __future__ import annotations

import io
import threading
from collections.abc import Callable

from PIL import Image

from bgremover.ai_process import InferenceCancelled, InferenceError


def tiny_png() -> bytes:
    """Gültige PNG-Bytes, die ``AIWorker`` zu einem RGBA-Bild dekodieren kann."""
    buf = io.BytesIO()
    Image.new("RGBA", (4, 4), (0, 0, 0, 0)).save(buf, format="PNG")
    return buf.getvalue()


class FakeInference:
    """In-Process-Ersatz für ``InferenceProcess`` (siehe Modul-Docstring)."""

    def __init__(
        self,
        *,
        result: bytes | None = None,
        warmup_error: Exception | None = None,
        infer_error: Exception | None = None,
        gate: threading.Event | None = None,
        poll: float = 0.01,
    ) -> None:
        self._result = result if result is not None else tiny_png()
        self._warmup_error = warmup_error
        self._infer_error = infer_error
        # Optionales Tor: ``infer`` blockiert pollend, bis es gesetzt wird.
        self._gate = gate
        self._poll = poll
        self._stopped = threading.Event()
        self.alive = False
        self.warmup_calls = 0
        self.infer_calls = 0
        self.stop_calls = 0
        self.shutdown_calls = 0

    @property
    def is_alive(self) -> bool:
        return self.alive

    def warmup(self, should_cancel: Callable[[], bool] | None = None) -> None:
        self.warmup_calls += 1
        self.alive = True
        if self._warmup_error is not None:
            raise self._warmup_error

    def infer(
        self, png_bytes: bytes, should_cancel: Callable[[], bool] | None = None,
    ) -> bytes:
        self.infer_calls += 1
        self.alive = True
        cancelled = should_cancel or (lambda: False)
        while True:
            if cancelled():
                self.alive = False
                raise InferenceCancelled
            if self._stopped.is_set():
                self.alive = False
                raise InferenceError("Inferenzprozess beendet")
            if self._gate is None or self._gate.is_set():
                break
            threading.Event().wait(self._poll)
        if self._infer_error is not None:
            raise self._infer_error
        return self._result

    def request_stop(self) -> None:
        self.stop_calls += 1
        self._stopped.set()
        self.alive = False

    def shutdown(self) -> None:
        self.shutdown_calls += 1
        self._stopped.set()
        self.alive = False
