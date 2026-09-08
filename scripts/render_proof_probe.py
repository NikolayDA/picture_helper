#!/usr/bin/env python3
"""Renderbeweis-Sonde: ``frameSwapped`` je Plattform und Lage messen (#1010).

Der Renderbeweis aus #1004 (``bgremover/viewer_3d.py``) spricht einen
``GLReliefViewer`` frei, sobald Qt ``frameSwapped`` sendet, und stuft ihn nach
``_MAX_REFUSED_PAINTS`` aufeinanderfolgenden Paints ohne Widget-Framebuffer
in den Fehlerzustand [F] ab. Seit PR #1005 liest ``bgremover/screenshot3d.py``
diesen Zustand – der Beweis trägt damit das MUSS-Kriterium
``MACOS-ARM-DMG-01`` mit. Ob ``frameSwapped`` auf einer Plattform **vor** der
Dreierschwelle feuert, ist eine Eigenschaft von Qt und Treiber und lässt sich
nur auf dem Gerät messen.

Die Sonde zählt genau die Größen mit, die der Beweis auswertet, ohne ihn zu
verändern: ``paintEvent``-Aufrufe, ``defaultFramebufferObject()`` **je** Paint
(nur eine 0 lässt die Abweisungszählung anlaufen), ``paintGL``-Aufrufe,
``frameSwapped``-Signale, ``erster_swap`` (nach wie vielen Paints und wie
vielen Millisekunden nach ``show()`` Qt den ersten Frame tauschte) sowie die
Endzähler ``_has_rendered``/``_refused_paints``/``has_failed``/``failure_reason``.
Gemessen wird in drei Lagen: ``sichtbar``, ``verborgen`` (nie gezeigt – Qt
malt dann gar nicht) und ``verdeckt`` (ein zweites Fenster liegt davor;
braucht einen echten Fenstermanager, unter ``xvfb-run`` ohne WM misst die
Lage dasselbe wie ``sichtbar``).

Die Sonde **bewertet nicht**; Exit 0 heißt „gemessen", unabhängig vom Befund.
Unter ``QT_QPA_PLATFORM=offscreen`` ist ``has_failed=True`` mit dem Grund
„Qt hält keinen Widget-Framebuffer" der *richtige* Befund. Die Erwartung je
Lage auf einer renderfähigen Sitzungsplattform und die Lesefallen stehen in
``TESTING.md`` („Renderbeweis-Sonde"); Messwerte je Plattform hält der
ADR-Nachtrag ``docs/history/ADR-2026-3d-reliefvorschau-renderer.md``.

Zwei Wege auf ein Gerät: von Hand gegen den Quellbaum
(``python scripts/render_proof_probe.py``, ohne gesetztes ``QT_QPA_PLATFORM``)
oder über den Heartbeat-Workflow per ``workflow_dispatch`` mit
``render_probe: true`` – er fährt dieselbe Sonde nach dem Preflight auf jedem
aktiven Self-hosted Runner und schreibt Zeilen und Tabelle in Joblog und
Job-Zusammenfassung (``--summary``).

Exit 0 = Messung durchgeführt (Befund steht in den Zeilen; ein Schreibfehler
bei ``--json-out``/``--summary`` ist nur eine Warnung auf stderr), 2 = Sonde
nicht ausführbar (keine ``QApplication``, Viewer nicht konstruierbar, Ausnahme).

Bewusst **nicht** in der mypy-Strengeliste der Skripte (``pyproject.toml``):
Die Sonde überschreibt Qt-Hooks (``paintEvent``) und liest Viewer-Interna,
deren Typen PyQt6 als ``Any`` liefert – ``disallow_untyped_defs`` brächte
hier Annotationen ohne Prüfkraft. Gehalten wird sie stattdessen von ``ruff``
und den Drift-Wächtern in ``tests/test_viewer_3d.py`` (Viewer-API,
Signaturbindung) und ``tests/test_render_proof_probe.py``.
"""
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# Die Laufzeit-Importe stehen unter dem Exit-Vertrag (Codex-Review PR #1029):
# Fehlt PyQt6 – oder darunter ``libGL.so.1`` beim Laden von ``QtWidgets`` –,
# endete das Skript sonst mit rohem Traceback und Exit 1, bevor ``main`` einen
# Handler erreicht. Als Skript gestartet wird daraus der benannte Befund
# „nicht ausführbar" (Exit 2); als Modul importiert (Tests) bleibt es die
# gewöhnliche Ausnahme.
try:
    import numpy as np
    from PyQt6.QtCore import (
        PYQT_VERSION_STR,
        QT_VERSION_STR,
        QElapsedTimer,
        QEventLoop,
        QRect,
        QTimer,
        qVersion,
    )
    from PyQt6.QtWidgets import QApplication, QWidget

    from bgremover.height_map import HEIGHT_MAX_16BIT, HeightField
    from bgremover.relief_mesh import MeshQuality, build_relief_mesh
    from bgremover.viewer_3d import GLReliefViewer
except Exception as exc:  # noqa: BLE001 – jeder Importfehler ist derselbe Befund
    if __name__ != "__main__":
        raise
    print(f"[render-probe] nicht ausführbar: {type(exc).__name__}: {exc}", file=sys.stderr)
    raise SystemExit(2) from None

#: Die drei Lagen der Messung, in dieser Reihenfolge.
LAGEN: tuple[str, ...] = ("sichtbar", "verborgen", "verdeckt")

#: Beobachtungsfenster je Lage – auf ``xcb`` kam der erste Frame-Tausch
#: gemessen nach ~110 ms, zwei Sekunden lassen auch einem trägen Compositor Zeit.
DEFAULT_MS = 2000

#: Schema der JSON-Ausgabe (``--json-out``).
SCHEMA = 1
KIND = "render-proof-probe"

#: Roher ``glGetString``-Name des Renderers (Teil des OpenGL-Vertrags, wie in
#: ``preview3d_capability``/``qt_gl_probe``).
_GL_RENDERER = 0x1F01

#: Fensterlagen: Der Viewer bekommt eine feste Position, der Deckel schließt
#: ihn samt Rahmen ein – sonst platzierte der Fenstermanager beide beliebig,
#: und „verdeckt" verdeckte nichts.
_VIEWER_POS = (120, 120)
_VIEWER_SIZE = (240, 200)
_COVER_RECT = (40, 40, 400, 360)


class Sonde(GLReliefViewer):
    """Zählt mit, was der Renderbeweis auswertet – ohne ihn zu verändern."""

    def __init__(self) -> None:
        super().__init__()
        self.paints = 0
        self.fbos: list[int] = []
        self.gl_paints = 0
        self.swaps = 0
        self.erster_swap: tuple[int, int] | None = None  # (nach wie vielen Paints, ms seit show)
        self.uhr = QElapsedTimer()
        self.frameSwapped.connect(self._zaehle_swap)

    def _zaehle_swap(self) -> None:
        self.swaps += 1
        if self.erster_swap is None:
            self.erster_swap = (self.paints, int(self.uhr.elapsed()))

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt-Override)
        self.paints += 1
        super().paintEvent(event)  # hier entscheidet der Beweis
        self.fbos.append(int(self.defaultFramebufferObject()))

    def paintGL(self) -> None:  # noqa: N802 (Qt-Override)
        self.gl_paints += 1
        super().paintGL()


@dataclass(frozen=True)
class Messung:
    """Endstand einer Lage – die Spalten der Tabelle im ADR-Nachtrag."""

    lage: str
    paint_events: int
    fbos: list[int]
    paint_gl: int
    frame_swapped: int
    erster_swap: tuple[int, int] | None
    has_rendered: bool
    refused_paints: int
    has_failed: bool
    grund: str
    #: Was die Plattform über die Lage weiß – nur für ``verdeckt`` gefüllt
    #: (Codex-Review PR #1029): ob der Deckel den Viewer laut Qt umschließt
    #: und ob dessen Fenster ``exposed`` ist. Unter Wayland bleibt die
    #: Verdeckung unbestätigt, der Compositor setzt Position und Stapelung.
    hinweis: str = ""

    def zeile(self) -> str:
        """Die dokumentierte Ausgabezeile – wörtlich so gehört sie ins Issue."""
        zeile = (
            f"{self.lage:<10} paintEvents={self.paint_events} fbo={self.fbos} "
            f"paintGL={self.paint_gl} frameSwapped={self.frame_swapped} "
            f"erster_swap={self.erster_swap} _has_rendered={self.has_rendered} "
            f"_refused_paints={self.refused_paints} has_failed={self.has_failed} "
            f"grund={self.grund!r}"
        )
        if self.hinweis:
            zeile += f" hinweis={self.hinweis!r}"
        return zeile


def _warte(ms: int) -> None:
    """Wartet ``ms`` im Ereignisdurchlauf – warten, nicht drehen.

    Eine verschachtelte ``QEventLoop`` blockiert, bis der Timer sie beendet.
    Die naheliegende Schleife über ``processEvents(WaitForMoreEvents, ms)``
    tut das **nicht** (Review PR #1029): Die ms-Überladung leitet auf die
    ``QDeadlineTimer``-Variante um, die ``WaitForMoreEvents`` intern abstreift –
    der Hauptthread drehte die vollen ``ms`` bei 100 % CPU durch, und genau
    das verschiebt auf einem Pi, wann Compositor und Treiber den ersten
    Frame-Tausch zustellen: die Größe ``erster_swap``, die die Sonde misst.
    """
    schleife = QEventLoop()
    QTimer.singleShot(ms, schleife.quit)
    schleife.exec()


def _mesh() -> Any:
    rampe = np.tile(np.linspace(0, HEIGHT_MAX_16BIT, 32, dtype=np.uint16), (32, 1))
    feld = HeightField(rampe, np.full((32, 32), 255, np.uint8), HEIGHT_MAX_16BIT)
    return build_relief_mesh(feld, MeshQuality.REDUCED)


def _renderer(viewer: GLReliefViewer) -> str:
    """GL-Renderer aus dem Kontext des Viewers – fail-open, kein zweiter Kontext.

    Liest über denselben GL-2.1-Funktionssatz wie der Viewer selbst
    (``_functions``, Versions-Factory); ein fehlender Kontext oder eine
    Ausnahme ergibt eine leere Provenienz, nie einen Abbruch.
    """
    try:
        if viewer.context() is None or not viewer.isValid():
            return ""
        viewer.makeCurrent()
        try:
            fns = viewer._functions()
            value = fns.glGetString(_GL_RENDERER) if fns is not None else None
        finally:
            viewer.doneCurrent()
    except Exception:  # noqa: BLE001 – Provenienz ist Beiwerk, nie ein Abbruchgrund
        return ""
    if isinstance(value, bytes):
        return value.decode("ascii", "replace")
    return str(value or "")


def _rect(r: QRect) -> str:
    return f"{r.x()},{r.y()} {r.width()}×{r.height()}"


def verdeckung(app: QApplication, viewer: QWidget, deckel: QWidget) -> str:
    """Was die Plattform über die Verdeckung weiß – belegt ist sie nie ganz.

    ``setGeometry``/``raise_`` sind Wünsche an den Fenstermanager (Codex-Review
    PR #1029). Unter Wayland setzt der Compositor Position und Stapelung selbst
    und liefert Qt keine globalen Koordinaten – die Lage ist dort grundsätzlich
    unbestätigt, die Zeile belegt nur „nie ``has_failed``". Sonst wird die
    Rahmengeometrie verglichen; ``isExposed()`` des Viewer-Fensters kommt in
    jedem Fall dazu (auf ``cocoa`` spiegelt es die Occlusion des Systems).
    """
    fenster = viewer.windowHandle()
    exposed = fenster.isExposed() if fenster is not None else None
    if app.platformName().startswith("wayland"):
        return (
            "Verdeckung unbestätigt (Wayland: Compositor setzt Position und Stapelung); "
            f"exposed={exposed}"
        )
    if not deckel.frameGeometry().contains(viewer.frameGeometry()):
        return (
            f"Verdeckung unbestätigt (Deckel {_rect(deckel.frameGeometry())} umschließt "
            f"Viewer {_rect(viewer.frameGeometry())} nicht); exposed={exposed}"
        )
    return (
        f"Deckel {_rect(deckel.frameGeometry())} umschließt Viewer "
        f"{_rect(viewer.frameGeometry())}, Stapelung per raise_() angefordert; "
        f"exposed={exposed}"
    )


def messe(app: QApplication, lage: str, ms: int = DEFAULT_MS) -> tuple[Messung, str]:
    """Misst eine Lage und liefert Endstand plus GL-Renderer (falls lesbar)."""
    if lage not in LAGEN:
        raise ValueError(f"Unbekannte Lage {lage!r}; erlaubt: {', '.join(LAGEN)}")
    v = Sonde()
    v.move(*_VIEWER_POS)
    v.resize(*_VIEWER_SIZE)
    v.set_mesh(_mesh())
    deckel: QWidget | None = None
    v.uhr.start()
    if lage != "verborgen":
        v.show()
    if lage == "verdeckt":  # braucht einen echten Fenstermanager
        deckel = QWidget()
        deckel.setGeometry(*_COVER_RECT)
        deckel.show()
        deckel.raise_()
    _warte(ms)
    messung = Messung(
        lage=lage,
        paint_events=v.paints,
        fbos=list(v.fbos),
        paint_gl=v.gl_paints,
        frame_swapped=v.swaps,
        erster_swap=v.erster_swap,
        has_rendered=bool(v._has_rendered),
        refused_paints=int(v._refused_paints),
        has_failed=bool(v.has_failed),
        grund=str(v.failure_reason),
        hinweis=verdeckung(app, v, deckel) if deckel is not None else "",
    )
    renderer = _renderer(v) if lage != "verborgen" else ""
    v.cleanup_gl()
    if deckel is not None:
        deckel.close()
        deckel.deleteLater()
    v.close()
    v.deleteLater()
    # Fenster und Kontext dieser Lage abräumen, bevor die nächste beginnt –
    # sonst sähe „verborgen" das noch offene Fenster von „sichtbar" neben sich.
    app.processEvents()
    return messung, renderer


def _geraet() -> str:
    """Gerätemodell, fail-open (leer, wenn nicht ermittelbar)."""
    try:
        if sys.platform == "darwin":
            out = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True, text=True, timeout=5, check=False,
            )
            return out.stdout.strip()
        modell = Path("/proc/device-tree/model")
        if modell.exists():
            return modell.read_bytes().rstrip(b"\0").decode("utf-8", "replace").strip()
    except Exception:  # noqa: BLE001
        return ""
    return ""


def _betriebssystem() -> str:
    try:
        if sys.platform == "darwin":
            return f"macOS {platform.mac_ver()[0]}".strip()
        os_release = Path("/etc/os-release")
        if os_release.exists():
            for line in os_release.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"')
        return platform.platform()
    except Exception:  # noqa: BLE001
        return platform.system()


def umgebung(app: QApplication) -> dict[str, str]:
    """Provenienz der Messung – Gerät, OS, Architektur, Qt/PyQt, Qt-Plattform.

    ``qt`` ist die **geladene** Qt-Laufzeit (``qVersion()``), nicht die
    Version, gegen die die Bindings übersetzt wurden (``QT_VERSION_STR``,
    hier als ``qt_bindings``): Die Pins koppeln PyQt6 6.11.0 mit PyQt6-Qt6
    6.11.2, und gemessen wird die Laufzeit (Codex-Review PR #1029).
    """
    return {
        "geraet": _geraet(),
        "os": _betriebssystem(),
        "arch": platform.machine(),
        "qt": qVersion() or "",
        "qt_bindings": QT_VERSION_STR,
        "pyqt": PYQT_VERSION_STR,
        "python": platform.python_version(),
        "plattform": app.platformName(),
    }


def kopfzeile(env: dict[str, str], renderer: str = "") -> str:
    """Die Kopfzeile des dokumentierten Ergebnisformats (TESTING.md)."""
    teile = [
        env.get("geraet") or "unbekanntes Gerät",
        f"{env.get('os', '')} ({env.get('arch', '')})".strip(),
        f"Qt {env.get('qt', '')} / PyQt {env.get('pyqt', '')}",
        f"Plattform {env.get('plattform', '')}",
    ]
    if renderer:
        teile.append(f"Renderer {renderer}")
    return "Gerät · OS · Qt : " + " · ".join(teile)


#: Spaltenkopf der Tabelle – **identisch** mit der Tabelle im ADR-Nachtrag
#: (``docs/history/ADR-2026-3d-reliefvorschau-renderer.md``, Nachtrag #1010),
#: damit eine Zeile der Job-Zusammenfassung wörtlich dorthin übernommen werden
#: kann. Die letzte Spalte „Ergebnis" trägt hier den ``grund`` des Viewers
#: (oder „–"); die Einordnung „gesund" / „kein Urteil" / „[F]" ergänzt der
#: Mensch beim Übernehmen – die Sonde bewertet nicht.
TABELLEN_KOPF = (
    "| Lage | Plattform | paintEvents | `defaultFramebufferObject()` je Paint | `paintGL` "
    "| `frameSwapped` | `erster_swap` (Paint, ms) | `_has_rendered` | `_refused_paints` "
    "| `has_failed` | Ergebnis |"
)


def markdown_tabelle(env: dict[str, str], messungen: list[Messung], renderer: str = "") -> str:
    """Die Tabelle des ADR-Nachtrags im selben Spaltenschema, zeilenweise übernehmbar."""
    zeilen = [
        "### Renderbeweis-Sonde (#1010)",
        "",
        kopfzeile(env, renderer),
        "",
        TABELLEN_KOPF,
        "|" + "---|" * (TABELLEN_KOPF.count("|") - 1),
    ]
    for m in messungen:
        fbos = ", ".join(str(f) for f in m.fbos) if m.fbos else "–"
        erster = f"{m.erster_swap[0]}, {m.erster_swap[1]}" if m.erster_swap else "–"
        zeilen.append(
            f"| {m.lage} | `{env.get('plattform', '')}` | {m.paint_events} | {fbos} | "
            f"{m.paint_gl} | {m.frame_swapped} | {erster} | `{m.has_rendered}` | "
            f"{m.refused_paints} | `{m.has_failed}` | {m.grund or '–'} |"
        )
    zeilen.append("")
    zeilen.append(
        "Spaltenschema wie die Tabelle im ADR-Nachtrag; „Ergebnis“ trägt hier den `grund` "
        "des Viewers (oder –), die Einordnung gesund / kein Urteil / [F] ergänzt der Mensch. "
        "Erwartung je Lage und Lesefallen: `TESTING.md` → Abschnitt „Renderbeweis-Sonde“; "
        "die Sonde bewertet nicht."
    )
    return "\n".join(zeilen) + "\n"


def bericht(env: dict[str, str], messungen: list[Messung], ms: int, renderer: str = "") -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "kind": KIND,
        "umgebung": {**env, "renderer": renderer},
        "fenster_ms": ms,
        "messungen": [asdict(m) for m in messungen],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--lage", action="append", choices=LAGEN, dest="lagen",
        help="nur diese Lage(n) messen (Standard: alle drei, in dokumentierter Reihenfolge)",
    )
    parser.add_argument(
        "--ms", type=int, default=DEFAULT_MS,
        help=f"Beobachtungsfenster je Lage in Millisekunden (Standard {DEFAULT_MS})",
    )
    parser.add_argument("--json-out", type=Path, help="Messung zusätzlich als JSON schreiben")
    parser.add_argument(
        "--summary", type=Path,
        help="Markdown-Tabelle an diese Datei anhängen (z. B. $GITHUB_STEP_SUMMARY)",
    )
    args = parser.parse_args(argv)
    if args.ms <= 0:
        parser.error("--ms muss positiv sein")
    lagen = tuple(args.lagen) if args.lagen else LAGEN

    try:
        app = QApplication.instance()
        if not isinstance(app, QApplication):
            app = QApplication(sys.argv[:1])
        env = umgebung(app)
        messungen: list[Messung] = []
        renderer = ""
        for lage in lagen:
            messung, gesehen = messe(app, lage, args.ms)
            messungen.append(messung)
            renderer = renderer or gesehen
    except Exception as exc:  # noqa: BLE001 – benannter Befund statt Traceback im Joblog
        print(f"[render-probe] nicht ausführbar: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    print(kopfzeile(env, renderer))
    for m in messungen:
        print(m.zeile())
    # Die Messung ist gelungen und steht auf stdout; ein Schreibfehler der
    # Zusatzausgaben (Rechte, volle Platte, leeres $GITHUB_STEP_SUMMARY) ist
    # eine Warnung, kein Exit 1 – sonst würde ein Messerfolg zum Gerätebefund
    # (Review PR #1029).
    if args.json_out is not None:
        _schreibe(
            args.json_out, "--json-out",
            json.dumps(bericht(env, messungen, args.ms, renderer), indent=2, ensure_ascii=False) + "\n",
        )
    if args.summary is not None:
        _schreibe(args.summary, "--summary", markdown_tabelle(env, messungen, renderer), anhaengen=True)
    return 0


def _schreibe(ziel: Path, option: str, inhalt: str, *, anhaengen: bool = False) -> bool:
    """Schreibt fail-open: ``False`` plus Warnung auf stderr statt Ausnahme."""
    try:
        ziel.parent.mkdir(parents=True, exist_ok=True)
        with ziel.open("a" if anhaengen else "w", encoding="utf-8") as fh:
            fh.write(inhalt)
    except OSError as exc:
        print(f"[render-probe] Warnung: {option} {str(ziel)!r} nicht schreibbar: {exc}", file=sys.stderr)
        return False
    return True


if __name__ == "__main__":
    sys.exit(main())
