"""Tests für ``scripts/update_probe_cli.py`` (#748).

Der eigentliche Witz dieses Skripts ist, unter einem BELIEBIGEN Interpreter zu
laufen (insbesondere dem einer bereits veröffentlichten AppImage) und dabei
ausschließlich ``bgremover.app_update``/``bgremover._version`` zu importieren.
Hier läuft es unter dem Test-Interpreter selbst; die HTTP-Schicht bleibt über
``bgremover.app_update.check_for_update`` gemockt (siehe
``tests/test_app_update.py``).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent


def _load(name: str, filename: str):  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


update_probe_cli = _load("update_probe_cli", "update_probe_cli.py")


def _fake_response(payload: dict) -> object:
    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return json.dumps(payload).encode("utf-8")

    return _Resp()


def test_cli_writes_update_available_and_exits_zero(tmp_path: Path) -> None:
    target = tmp_path / "evidenz.json"
    # Ein Fake-Tag, garantiert neuer als jede reale bgremover-Paketversion in
    # dieser Testumgebung (pyproject.toml steht ansonsten auf derselben
    # Version wie ein evtl. echtes Release-Tag – dann läge UP_TO_DATE vor).
    with patch(
        "urllib.request.urlopen",
        return_value=_fake_response({"tag_name": "v999.0.0", "html_url": "https://example/v999.0.0"}),
    ):
        rc = update_probe_cli.main(["--output", str(target)])

    assert rc == 0
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["status"] == "UPDATE_AVAILABLE"
    assert payload["latest_version"] == "v999.0.0"
    assert payload["interpreter"] == sys.executable


def test_cli_exits_nonzero_on_check_failed(tmp_path: Path) -> None:
    import urllib.error

    target = tmp_path / "evidenz.json"
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("kein Netz")):
        rc = update_probe_cli.main(["--output", str(target)])

    assert rc == 1
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["status"] == "CHECK_FAILED"
    assert payload["error"]
