"""Qt-freie Tests für die Update-Check-Kernlogik (#564).

HTTP-Layer vollständig gemockt – kein echter Netzzugriff. Deckt alle drei
Status ab (UP_TO_DATE, UPDATE_AVAILABLE, CHECK_FAILED) sowie Timeout,
HTTP-Fehler, ungültiges JSON und unparsebares Tag-Format.
"""
from __future__ import annotations

import http.client
import json
import urllib.error
from unittest.mock import patch

from bgremover.app_update import UpdateStatus, check_for_update


def _fake_response(payload: dict) -> object:
    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return json.dumps(payload).encode("utf-8")

    return _Resp()


def test_up_to_date_when_versions_match() -> None:
    with patch(
        "urllib.request.urlopen",
        return_value=_fake_response({"tag_name": "v1.2.3", "html_url": "https://example/v1.2.3"}),
    ):
        result = check_for_update("1.2.3")
    assert result.status == UpdateStatus.UP_TO_DATE
    assert result.latest_version is None
    assert result.error is None


def test_up_to_date_when_local_version_is_newer() -> None:
    with patch(
        "urllib.request.urlopen",
        return_value=_fake_response({"tag_name": "v1.2.3", "html_url": "https://example/v1.2.3"}),
    ):
        result = check_for_update("1.9.0")
    assert result.status == UpdateStatus.UP_TO_DATE


def test_update_available_with_correct_metadata() -> None:
    with patch(
        "urllib.request.urlopen",
        return_value=_fake_response({"tag_name": "v2.0.0", "html_url": "https://example/v2.0.0"}),
    ):
        result = check_for_update("1.2.3")
    assert result.status == UpdateStatus.UPDATE_AVAILABLE
    assert result.latest_version == "v2.0.0"
    assert result.release_url == "https://example/v2.0.0"
    assert result.error is None


def test_update_available_prefers_release_over_prerelease_suffix() -> None:
    with patch(
        "urllib.request.urlopen",
        return_value=_fake_response({"tag_name": "v1.2.3", "html_url": "https://example/v1.2.3"}),
    ):
        result = check_for_update("1.2.3-rc1")
    assert result.status == UpdateStatus.UPDATE_AVAILABLE
    assert result.latest_version == "v1.2.3"


def test_check_failed_on_http_error() -> None:
    with patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.HTTPError("url", 404, "Not Found", {}, None),
    ):
        result = check_for_update("1.2.3")
    assert result.status == UpdateStatus.CHECK_FAILED
    assert result.error
    assert result.latest_version is None


def test_check_failed_on_timeout() -> None:
    with patch("urllib.request.urlopen", side_effect=TimeoutError("timed out")):
        result = check_for_update("1.2.3", timeout=0.01)
    assert result.status == UpdateStatus.CHECK_FAILED
    assert result.error


def test_check_failed_on_connection_error() -> None:
    with patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.URLError("no route to host"),
    ):
        result = check_for_update("1.2.3")
    assert result.status == UpdateStatus.CHECK_FAILED
    assert result.error


def test_check_failed_on_incomplete_read() -> None:
    with patch(
        "urllib.request.urlopen",
        side_effect=http.client.IncompleteRead(b""),
    ):
        result = check_for_update("1.2.3")
    assert result.status == UpdateStatus.CHECK_FAILED
    assert result.error


def test_check_failed_on_invalid_json() -> None:
    class _BadResp:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return b"not json"

    with patch("urllib.request.urlopen", return_value=_BadResp()):
        result = check_for_update("1.2.3")
    assert result.status == UpdateStatus.CHECK_FAILED
    assert result.error


def test_check_failed_on_unparsable_local_version() -> None:
    with patch(
        "urllib.request.urlopen",
        return_value=_fake_response({"tag_name": "v1.2.3", "html_url": "https://example/v1.2.3"}),
    ):
        result = check_for_update("not-a-version")
    assert result.status == UpdateStatus.CHECK_FAILED
    assert result.error


def test_check_failed_on_unparsable_remote_tag() -> None:
    with patch(
        "urllib.request.urlopen",
        return_value=_fake_response({"tag_name": "release-latest", "html_url": "https://example"}),
    ):
        result = check_for_update("1.2.3")
    assert result.status == UpdateStatus.CHECK_FAILED
    assert result.error


def test_check_failed_on_missing_fields() -> None:
    with patch("urllib.request.urlopen", return_value=_fake_response({"foo": "bar"})):
        result = check_for_update("1.2.3")
    assert result.status == UpdateStatus.CHECK_FAILED
    assert result.error
