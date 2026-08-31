#!/usr/bin/env python3
"""Minimale Qt-/GL-Sonde fuer den Runner-Preflight (#934, Epic #914).

Bis #934 pruefte der Preflight nur, ob ``libGL.so.1`` bzw. das
macOS-OpenGL-Framework **ladbar** ist. Das faengt den real beobachteten Fehler
"GL-Bibliothek fehlt", belegt aber nicht, dass PyQt6 mit dem vorgesehenen
Qt laedt, dass das **native** Platform-Plugin in der angemeldeten Sitzung
startet, dass ein ``QOpenGLContext`` wirklich aktuell wird und dass der
Kontext auf echter Hardware statt auf einem Software-Rasterizer laeuft. Ein so
defekter Runner bestand den schnellen Preflight und fiel erst Minuten spaeter
im schweren Plattform-Job aus.

Diese Sonde laeuft deshalb in der **schlanken Preflight-Runtime** (nur PyQt6),
nicht im Release-venv: Sie beruehrt denselben GUI-/Renderer-Pfad, ohne je
Heartbeat ein vollstaendiges ``.[test]`` neu zu installieren.

Bewusst **kein** ``offscreen``/``minimal``: Der Releasepfad braucht das native
Sitzungs-Plugin (native Screenshots, echter Renderer). Ein Headless-Ausweichweg
wuerde genau den Ausfall verstecken, den diese Sonde finden soll.

Das Ergebnis geht als **eine** JSON-Zeile auf stdout. Jeder Fehlerzustand
traegt eine benannte ``stage``, damit der Preflight ihn als eigenen Befund
melden kann statt als "irgendwas mit Qt":

``import``    PyQt-/Qt-Runtime fehlt oder ist unbrauchbar
``plugin``    natives Platform-Plugin nicht verfuegbar (oder Headless erzwungen)
``kontext``   kein gueltiger, aktueller GL-Kontext
``renderer``  Kontext laeuft auf einem Software-Rasterizer

Ein Abbruch **ohne** JSON-Zeile ist ebenfalls ein Befund: Qt beendet den
Prozess bei fehlendem Platform-Plugin hart (``qFatal``), statt eine Ausnahme
zu werfen. Der Preflight wertet das als ``plugin`` und haengt stderr an.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent

#: Benannte Fehlerzustaende (Reihenfolge = Pruefreihenfolge).
STAGES: tuple[str, ...] = ("import", "plugin", "kontext", "renderer")

#: Plattform-Plugins, die keine echte Sitzung belegen. Sie sind hier kein
#: Ausweichweg, sondern ein Befund (Nicht-Ziel des Issues).
HEADLESS_PLATFORMS: tuple[str, ...] = ("offscreen", "minimal")

#: Rohe ``glGetString``-Namen (Teil des OpenGL-Vertrags, nicht der Bindings).
#: Identisch zu ``preview3d_capability``; ``tests/test_qt_gl_probe.py`` haelt
#: beide Saetze gegeneinander, damit die Sonde nicht andere Werte liest als
#: der Produktivpfad.
GL_VENDOR = 0x1F00
GL_RENDERER = 0x1F01
GL_VERSION = 0x1F02


def load_software_renderer_rule() -> Callable[[str], bool]:
    """``is_software_renderer`` aus dem Checkout laden – ohne das Paket zu importieren.

    Die Regel ist die geteilte Quelle der Wahrheit (#642, ADR #639) und selbst
    Qt- und abhaengigkeitsfrei. ``import bgremover.renderer_provenance`` zoege
    dagegen ueber ``bgremover.constants`` Pillow nach, das die schlanke
    Preflight-Runtime bewusst nicht hat. Der Dateipfad umgeht genau das, ohne
    die Regel zu kopieren.
    """
    path = REPO_ROOT / "bgremover" / "renderer_provenance.py"
    spec = importlib.util.spec_from_file_location("renderer_provenance", path)
    if spec is None or spec.loader is None:  # pragma: no cover - Pfad existiert im Repo
        raise ImportError(f"renderer_provenance nicht ladbar: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rule: Callable[[str], bool] = module.is_software_renderer
    return rule


def _fail(stage: str, detail: str, **extra: Any) -> dict[str, Any]:
    return {"ok": False, "stage": stage, "detail": detail, **extra}


def probe(env: dict[str, str] | None = None) -> dict[str, Any]:
    """Fuehrt den Qt-/GL-Smoke aus und liefert das strukturierte Ergebnis.

    Wirft nie: Jeder Fehler wird zu einem benannten ``stage``. Ein stiller
    Skip existiert bewusst nicht – ein nicht durchgefuehrter Nachweis ist ein
    Fehler, keine Auslassung.
    """
    environment = os.environ if env is None else env
    try:
        from PyQt6.QtGui import (
            QGuiApplication,
            QOffscreenSurface,
            QOpenGLContext,
            QSurfaceFormat,
        )
        from PyQt6.QtOpenGL import (
            QOpenGLVersionFunctionsFactory,
            QOpenGLVersionProfile,
        )
    except Exception as exc:  # noqa: BLE001 - jede Importstoerung ist derselbe Befund
        return _fail("import", f"{type(exc).__name__}: {exc}")

    requested = environment.get("QT_QPA_PLATFORM", "")
    if requested in HEADLESS_PLATFORMS:
        return _fail(
            "plugin",
            f"QT_QPA_PLATFORM={requested!r} erzwingt ein Headless-Plugin – der "
            "Releasepfad braucht das native Sitzungs-Plugin.",
        )

    try:
        # Referenz halten: Ohne laufende Anwendung scheitert ctx.create()
        # mangels Plattformintegration lautlos (live auf Mac- und Pi-Runnern
        # beobachtet, siehe abnahme_probe.py).
        existing = QGuiApplication.instance()
        app = (
            existing
            if isinstance(existing, QGuiApplication)
            else QGuiApplication(sys.argv[:1])
        )
    except Exception as exc:  # noqa: BLE001
        return _fail("plugin", f"QGuiApplication: {type(exc).__name__}: {exc}")

    platform_name = str(app.platformName() or "")
    if not platform_name or platform_name in HEADLESS_PLATFORMS:
        return _fail(
            "plugin",
            f"Qt startete mit Platform-Plugin {platform_name!r} statt mit dem "
            "nativen Sitzungs-Plugin.",
        )

    fmt = QSurfaceFormat()
    fmt.setVersion(2, 1)
    fmt.setRenderableType(QSurfaceFormat.RenderableType.OpenGL)
    ctx = QOpenGLContext()
    ctx.setFormat(fmt)
    if not ctx.create():
        return _fail(
            "kontext", "QOpenGLContext.create() fehlgeschlagen", platform=platform_name
        )
    surface = QOffscreenSurface()
    surface.setFormat(ctx.format())
    surface.create()
    if not surface.isValid() or not ctx.makeCurrent(surface):
        return _fail(
            "kontext", "Kein aktueller Offscreen-Kontext", platform=platform_name
        )
    try:
        profile = QOpenGLVersionProfile()
        profile.setVersion(2, 1)
        fns = QOpenGLVersionFunctionsFactory.get(profile, ctx)
        if fns is None:
            return _fail(
                "kontext", "Keine GL-2.1-Versionsfunktionen", platform=platform_name
            )
        vendor = _gl_string(fns, GL_VENDOR)
        renderer = _gl_string(fns, GL_RENDERER)
        version = _gl_string(fns, GL_VERSION)
        diagnostic = f"{vendor} / {renderer} / {version}".strip(" /")
        if not diagnostic:
            return _fail(
                "kontext", "GL-Strings leer – Kontext unbrauchbar", platform=platform_name
            )
        if load_software_renderer_rule()(diagnostic):
            return _fail(
                "renderer",
                f"Software-Renderer statt Hardware: {diagnostic}",
                platform=platform_name,
                vendor=vendor,
                renderer=renderer,
                version=version,
            )
        return {
            "ok": True,
            "stage": "",
            "detail": "",
            "platform": platform_name,
            "vendor": vendor,
            "renderer": renderer,
            "version": version,
            "diagnostic": diagnostic,
        }
    finally:
        ctx.doneCurrent()


def _gl_string(fns: object, name: int) -> str:
    """Liest einen ``glGetString``-Wert defensiv als Text (leer bei Fehler)."""
    try:
        value = fns.glGetString(name)  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        return ""
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("ascii", "replace")
    return str(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    result = probe()
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":  # pragma: no cover - CLI-Einstieg
    sys.exit(main())
