"""Qt-freie Tests für die rembg-Modell-Statuserkennung (#568).

Alle drei Status werden über `tmp_path`/`monkeypatch` von `U2NET_HOME`
reproduziert, ohne echten Download und ohne `rembg`-Import vorauszusetzen.
"""
from __future__ import annotations

from unittest.mock import patch

from bgremover.ai_model_status import ModelStatus, get_model_status


def test_not_downloaded_when_cache_dir_missing(tmp_path, monkeypatch) -> None:
    cache_dir = tmp_path / "missing_u2net"
    monkeypatch.setenv("U2NET_HOME", str(cache_dir))
    with patch("bgremover.ai_model_status._rembg_available", return_value=True):
        result = get_model_status()
    assert result.status == ModelStatus.NOT_DOWNLOADED
    assert result.model_path == cache_dir / "u2net.onnx"
    assert result.size_bytes is None


def test_not_downloaded_when_model_file_missing(tmp_path, monkeypatch) -> None:
    cache_dir = tmp_path / "u2net"
    cache_dir.mkdir()
    monkeypatch.setenv("U2NET_HOME", str(cache_dir))
    with patch("bgremover.ai_model_status._rembg_available", return_value=True):
        result = get_model_status()
    assert result.status == ModelStatus.NOT_DOWNLOADED


def test_not_downloaded_when_model_file_is_empty(tmp_path, monkeypatch) -> None:
    cache_dir = tmp_path / "u2net"
    cache_dir.mkdir()
    (cache_dir / "u2net.onnx").write_bytes(b"")
    monkeypatch.setenv("U2NET_HOME", str(cache_dir))
    with patch("bgremover.ai_model_status._rembg_available", return_value=True):
        result = get_model_status()
    assert result.status == ModelStatus.NOT_DOWNLOADED


def test_downloaded_when_model_file_present_and_nonempty(tmp_path, monkeypatch) -> None:
    cache_dir = tmp_path / "u2net"
    cache_dir.mkdir()
    model_file = cache_dir / "u2net.onnx"
    model_file.write_bytes(b"fake-onnx-bytes")
    monkeypatch.setenv("U2NET_HOME", str(cache_dir))
    with patch("bgremover.ai_model_status._rembg_available", return_value=True):
        result = get_model_status()
    assert result.status == ModelStatus.DOWNLOADED
    assert result.model_path == model_file
    assert result.size_bytes == len(b"fake-onnx-bytes")


def test_rembg_unavailable_takes_precedence(tmp_path, monkeypatch) -> None:
    cache_dir = tmp_path / "u2net"
    cache_dir.mkdir()
    (cache_dir / "u2net.onnx").write_bytes(b"fake-onnx-bytes")
    monkeypatch.setenv("U2NET_HOME", str(cache_dir))
    with patch("bgremover.ai_model_status._rembg_available", return_value=False):
        result = get_model_status()
    assert result.status == ModelStatus.REMBG_UNAVAILABLE


def test_default_cache_dir_is_home_u2net_without_override(monkeypatch) -> None:
    monkeypatch.delenv("U2NET_HOME", raising=False)
    with patch("bgremover.ai_model_status._rembg_available", return_value=True):
        result = get_model_status()
    from pathlib import Path

    assert result.model_path == Path.home() / ".u2net" / "u2net.onnx"
