"""Tests für den Secret-/Entwicklerpfad-Scan gebauter Release-Artefakte (#584).

Deckt insbesondere die Codex-Review-Befunde auf PR #608 ab: Geheimnisse
dürfen nicht im Klartext geloggt werden (nur Fingerprint), komprimierte
Nutzdaten (AppImage/`.deb`/`.dmg`) müssen vor dem Scan entpackt werden, und
ein unbekannter Entwicklerpfad **im eigenen bgremover-Paket** muss den Scan
hart fehlschlagen lassen. Derselbe Fund in einer Drittanbieter-Abhängigkeit
ist dagegen nur informativ (nicht blockierend) – reale CI-Läufe zeigten, dass
numpy/numba/networkx/PyQt6-sip u. a. eigene, harmlose ``/home``/``/Users``-
Beispielpfade mitbringen (Docstrings, Kommentare, Zitat-URLs, vom Hersteller
einkompilierte Build-Pfade), die sich mit jedem Versions-Bump unvorhersehbar
ändern und kein Signal für einen Leak unserer Build-Umgebung sind.
"""
from __future__ import annotations

import importlib.util
import inspect
import json
import re
import shutil
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT = _ROOT / "scripts" / "scan_release_artifacts.py"

_spec = importlib.util.spec_from_file_location("scan_release_artifacts", _SCRIPT)
assert _spec is not None and _spec.loader is not None
scan_release_artifacts = importlib.util.module_from_spec(_spec)
# Ohne Eintrag in sys.modules kann @dataclass seinen Namensraum nicht aufloesen
sys.modules["scan_release_artifacts"] = scan_release_artifacts
_spec.loader.exec_module(scan_release_artifacts)

_AWS_KEY = b"AKIAIOSFODNN7EXAMPLE"  # oeffentliches AWS-Beispiel, kein echtes Secret.

# Frueher ein modulweiter Skip. Seit #920 enthaelt das Modul auch Bericht-,
# Register- und Summary-Tests, die kein dpkg-deb brauchen und deshalb auch auf
# den macOS-Legs der Full-CI laufen sollen – ein modulweiter Skip haette sie
# dort stillschweigend mituebersprungen. ``_build_deb`` selbst ueberspringt
# zusaetzlich zur Laufzeit, damit ein vergessener Marker nie zu einem
# Fehlschlag statt zu einem Skip fuehrt.
_needs_dpkg = pytest.mark.skipif(
    shutil.which("dpkg-deb") is None, reason="dpkg-deb not available"
)


def _build_deb(stage: Path, out: Path, payload_files: dict[str, bytes]) -> None:
    """Baut ein reales .deb (nur fuer Tests) mit den gegebenen Nutzdateien."""
    if shutil.which("dpkg-deb") is None:  # pragma: no cover - plattformabhaengig
        pytest.skip("dpkg-deb not available")
    (stage / "DEBIAN").mkdir(parents=True, exist_ok=True)
    (stage / "DEBIAN" / "control").write_text(
        "Package: test\nVersion: 1.0\nArchitecture: amd64\n"
        "Maintainer: test <test@example.com>\nDescription: test\n"
    )
    for rel, content in payload_files.items():
        target = stage / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    subprocess.run(
        ["dpkg-deb", "--build", "--root-owner-group", str(stage), str(out)],
        check=True, capture_output=True,
    )


def test_script_exists() -> None:
    assert _SCRIPT.is_file()


# ── scan_bytes: Muster-Erkennung ohne Geheimnis-Leck ins Log ────────────

def test_scan_bytes_clean_data_has_no_findings() -> None:
    assert scan_release_artifacts.scan_bytes(b"just a harmless blob") == []


def test_scan_bytes_detects_aws_access_key() -> None:
    findings = scan_release_artifacts.scan_bytes(b"...%s..." % _AWS_KEY)
    assert any("AWS Access Key ID" in f for f in findings)


def test_scan_bytes_finding_never_contains_the_raw_secret() -> None:
    """Codex P1: das Log darf das Geheimnis nicht im Klartext enthalten."""
    findings = scan_release_artifacts.scan_bytes(b"token=%s" % _AWS_KEY)
    joined = " ".join(findings)
    assert _AWS_KEY.decode() not in joined
    assert "Fingerprint" in joined
    assert "Position" in joined


def test_scan_bytes_detects_github_token() -> None:
    findings = scan_release_artifacts.scan_bytes(b"ghp_" + b"a1b2c3" * 7)
    assert any("GitHub-Token" in f for f in findings)


def test_scan_bytes_detects_pem_private_key() -> None:
    body = b"MIIEowIBAAKCAQEA1234567890abcdefABCDEF" * 3
    findings = scan_release_artifacts.scan_bytes(
        b"-----BEGIN RSA PRIVATE KEY-----\n%s\n-----END RSA PRIVATE KEY-----" % body
    )
    assert any("PEM-Schlüssel" in f for f in findings)


def test_scan_bytes_ignores_pem_header_without_key_body() -> None:
    """Codex-Nachbesserung (#608): OpenSSLs eigene, in Qt6/libqopensslbackend
    einkompilierte Typtabelle listet alle PEM-Kopfzeilen als NUL-separierte
    Strings ohne jeden Schluesselkoerper – das darf nicht als Fund gelten
    (empirisch aus den echten PyQt6-Qt6-Binaries nachgebildet)."""
    findings = scan_release_artifacts.scan_bytes(
        b"-----BEGIN PRIVATE KEY-----\x00-----END PUBLIC KEY-----"
        b"\x00-----END RSA PRIVATE KEY-----\x00-----END DSA PRIVATE KEY-----"
    )
    assert findings == []


def test_scan_bytes_pem_header_followed_by_short_garbage_is_ignored() -> None:
    findings = scan_release_artifacts.scan_bytes(b"-----BEGIN EC PRIVATE KEY-----\x00\x00abc")
    assert findings == []


def test_scan_bytes_finds_every_occurrence_not_just_the_first() -> None:
    """Ein frueherer Treffer (z. B. ein zugelassener Fehlalarm) darf einen
    zweiten, andersartigen Fund desselben Musters nicht verdecken (#608:
    reale CI-Artefakte zeigten mehrere unabhaengige Treffer pro Muster)."""
    other_key = b"AKIAZZZZZZZZZZZZZZZZ"
    assert other_key != _AWS_KEY
    findings = scan_release_artifacts.scan_bytes(b"%s ... %s" % (_AWS_KEY, other_key))
    fingerprints = {f.split("Fingerprint ")[1].rstrip(")") for f in findings}
    assert len(fingerprints) == 2


def test_scan_bytes_deduplicates_repeated_identical_matches() -> None:
    findings = scan_release_artifacts.scan_bytes(b"%s ... %s" % (_AWS_KEY, _AWS_KEY))
    assert len(findings) == 1


def test_scan_bytes_ignores_aws_key_embedded_mid_identifier() -> None:
    """Codex-Nachbesserung (#608): Pillows ``PIL/ImageFont.py`` enthaelt eine
    Base64-kodierte Schriftmetrik-Tabelle, in der "AKIA" + 16 passende Zeichen
    zufaellig vorkommt – aber eingebettet mitten in einem laengeren
    Base64-Lauf, nie als eigenstaendiger Wert. Ein echter Schluessel steht
    immer freistehend (Anfuehrungszeichen/Gleichheitszeichen/Leerraum davor
    und danach)."""
    findings = scan_release_artifacts.scan_bytes(b"AwAaAKIAAQAAAAAABAAHAM0AAQAAAAAABQA8AU8AAQAA")
    assert findings == []


def test_scan_bytes_ignores_github_token_embedded_mid_identifier() -> None:
    """Codex-Nachbesserung (#608): scipys HiGHS-Solver-Bindung
    (``scipy/optimize/_highspy/_core*.so``) benennt jede exportierte
    C-API-Funktion "Highs_...", was im C++-Mangling "ghs_..." als
    Teilzeichenkette ergibt – bei 43 verschiedenen Funktionsnamen in
    derselben Datei ist ein Fingerprint-Allowlist-Eintrag pro Symbol nicht
    wartbar. Die Wortgrenzen-Anker greifen strukturell fuer die gesamte
    Namensfamilie."""
    findings = scan_release_artifacts.scan_bytes(
        b"hi" + b"ghs_setCallbackP5HighsSt8functionIFviRKNSt7"
    )
    assert findings == []


def test_scan_bytes_detects_github_token_with_realistic_boundaries() -> None:
    """Ein echtes Token in typischem Kontext (z. B. in JSON gequotet) muss
    trotz der Wortgrenzen-Anker weiterhin erkannt werden."""
    findings = scan_release_artifacts.scan_bytes(b'{"token": "ghp_' + b"a1b2c3" * 7 + b'"}')
    assert any("GitHub-Token" in f for f in findings)


# ── dev_path_users: Allowlist ────────────────────────────────────────────

def test_dev_path_users_allows_known_ci_and_build_infra_users() -> None:
    data = (
        b"/home/runner/work/x /Users/default/Desktop "
        b"/home/qt/work/qt/qtbase /root/build"
    )
    assert scan_release_artifacts.dev_path_users(data) == set()


def test_dev_path_users_flags_unknown_user() -> None:
    assert scan_release_artifacts.dev_path_users(b"/Users/alice/dev/project") == {"alice"}


# ── _is_own_package_path: Geltungsbereich fuer den Hart-Fehlschlag ──────

def test_is_own_package_path_true_for_bgremover_member() -> None:
    path = Path("site-packages/bgremover/canvas.py")
    assert scan_release_artifacts._is_own_package_path(path) is True


def test_is_own_package_path_false_for_third_party_dependency() -> None:
    path = Path("site-packages/numpy/lib/_datasource.py")
    assert scan_release_artifacts._is_own_package_path(path) is False


# ── extract_payload: reales .deb (echtes dpkg-deb) ───────────────────────

@_needs_dpkg
def test_extract_payload_deb_recovers_compressed_payload(tmp_path: Path) -> None:
    """Codex P2: ein Secret in einer normalen Payload-Datei darf nicht durch
    die .deb-Kompression verdeckt werden."""
    stage = tmp_path / "stage"
    deb = tmp_path / "test.deb"
    _build_deb(stage, deb, {"opt/test/secret.txt": _AWS_KEY})

    # Die rohen .deb-Bytes enthalten das Secret NICHT im Klartext (komprimiert).
    assert _AWS_KEY not in deb.read_bytes()

    dest = tmp_path / "out"
    scan_release_artifacts.extract_payload(deb, dest)
    extracted = dest / "opt" / "test" / "secret.txt"
    assert extracted.is_file()
    assert extracted.read_bytes() == _AWS_KEY


def test_extract_payload_unknown_suffix_raises(tmp_path: Path) -> None:
    stray = tmp_path / "stray.bin"
    stray.write_bytes(b"nothing")
    with pytest.raises(ValueError, match="unbekanntes Artefaktformat"):
        scan_release_artifacts.extract_payload(stray, tmp_path / "out")


# ── extract_payload: AppImage/.dmg über gemockte Subprozesse ────────────
# (Weder ein echtes AppImage-Runtime noch macOS/hdiutil sind in dieser
# Sandbox verfuegbar; die Orchestrierung wird an der Subprozess-Grenze
# getestet, ``dpkg-deb`` bleibt echt.)

def test_extract_payload_appimage_invokes_extract_flag(tmp_path, monkeypatch) -> None:
    appimage = tmp_path / "Fake-ai.AppImage"
    appimage.write_bytes(b"#!/bin/sh\nexit 0\n")
    calls = []

    def fake_run(cmd, check=True, capture_output=True, **kwargs):
        calls.append((cmd, kwargs.get("cwd")))
        cwd = Path(kwargs["cwd"])
        (cwd / "squashfs-root").mkdir(parents=True, exist_ok=True)
        (cwd / "squashfs-root" / "embedded.txt").write_bytes(_AWS_KEY)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(scan_release_artifacts.subprocess, "run", fake_run)
    dest = tmp_path / "out"
    scan_release_artifacts.extract_payload(appimage, dest)

    assert len(calls) == 1
    cmd, cwd = calls[0]
    assert cmd[-1] == "--appimage-extract"
    assert Path(cwd) == dest
    assert (dest / "squashfs-root" / "embedded.txt").read_bytes() == _AWS_KEY


@_needs_dpkg
def test_extract_payload_deb_recurses_into_wrapped_appimage(tmp_path, monkeypatch) -> None:
    """Eine in der .deb gewrappte AppImage wird ebenfalls entpackt (#584)."""
    real_run = subprocess.run

    def fake_run(cmd, check=True, capture_output=True, **kwargs):
        if cmd[0] == "dpkg-deb":
            return real_run(cmd, check=check, capture_output=capture_output, **kwargs)
        assert cmd[-1] == "--appimage-extract"
        cwd = Path(kwargs["cwd"])
        (cwd / "squashfs-root").mkdir(parents=True, exist_ok=True)
        (cwd / "squashfs-root" / "site-packages.txt").write_bytes(_AWS_KEY)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(scan_release_artifacts.subprocess, "run", fake_run)

    stage = tmp_path / "stage"
    deb = tmp_path / "wrapper.deb"
    _build_deb(stage, deb, {"opt/BgRemover/BgRemover.AppImage": b"#!/bin/sh\nexit 0\n"})

    dest = tmp_path / "out"
    scan_release_artifacts.extract_payload(deb, dest)

    nested = (
        dest / "opt" / "BgRemover" / "BgRemover.AppImage.extracted"
        / "squashfs-root" / "site-packages.txt"
    )
    assert nested.read_bytes() == _AWS_KEY


def test_extract_payload_dmg_mounts_copies_and_always_detaches(tmp_path, monkeypatch) -> None:
    dmg = tmp_path / "Fake.dmg"
    dmg.write_bytes(b"not a real dmg")
    detach_calls = []

    def fake_run(cmd, check=True, capture_output=True, **kwargs):
        if cmd[0] == "hdiutil" and cmd[1] == "attach":
            mount_point = Path(cmd[cmd.index("-mountpoint") + 1])
            (mount_point / "BgRemover.app").mkdir(parents=True, exist_ok=True)
            (mount_point / "BgRemover.app" / "secret.txt").write_bytes(_AWS_KEY)
            return subprocess.CompletedProcess(cmd, 0)
        if cmd[0] == "hdiutil" and cmd[1] == "detach":
            detach_calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0)
        raise AssertionError(f"unexpected command: {cmd}")

    monkeypatch.setattr(scan_release_artifacts.subprocess, "run", fake_run)
    dest = tmp_path / "out"
    scan_release_artifacts.extract_payload(dmg, dest)

    assert len(detach_calls) == 1
    copied = dest / "contents" / "BgRemover.app" / "secret.txt"
    assert copied.read_bytes() == _AWS_KEY


def test_extract_payload_dmg_detaches_even_if_copy_fails(tmp_path, monkeypatch) -> None:
    dmg = tmp_path / "Fake.dmg"
    dmg.write_bytes(b"not a real dmg")
    detach_calls = []

    def fake_run(cmd, check=True, capture_output=True, **kwargs):
        if cmd[0] == "hdiutil" and cmd[1] == "attach":
            mount_point = Path(cmd[cmd.index("-mountpoint") + 1])
            (mount_point / "file.txt").write_bytes(b"data")
            return subprocess.CompletedProcess(cmd, 0)
        if cmd[0] == "hdiutil" and cmd[1] == "detach":
            detach_calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0)
        raise AssertionError(f"unexpected command: {cmd}")

    def fake_copy2(src: Path, dst: Path) -> None:
        raise OSError("simulierter Kopierfehler")

    monkeypatch.setattr(scan_release_artifacts.subprocess, "run", fake_run)
    monkeypatch.setattr(scan_release_artifacts.shutil, "copy2", fake_copy2)
    with pytest.raises(OSError):
        scan_release_artifacts.extract_payload(dmg, tmp_path / "out")
    assert len(detach_calls) == 1, "hdiutil detach muss auch bei einem Fehler laufen"


# ── main(): Ende-zu-Ende über ein reales .deb ───────────────────────────

@_needs_dpkg
def test_main_passes_for_clean_deb(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    dist = tmp_path / "dist"
    _build_deb(
        tmp_path / "stage", dist_deb := tmp_path / "clean.deb",
        {"opt/test/readme.txt": b"nothing interesting here"},
    )
    dist.mkdir()
    shutil.copy2(dist_deb, dist / "clean.deb")
    assert scan_release_artifacts.main([str(dist)]) == 0


@_needs_dpkg
def test_main_fails_for_deb_with_secret(tmp_path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    _build_deb(tmp_path / "stage", dist / "leaky.deb", {"opt/test/secret.txt": _AWS_KEY})
    assert scan_release_artifacts.main([str(dist)]) == 1


@_needs_dpkg
def test_main_fails_for_deb_with_unknown_dev_path_in_own_package(tmp_path) -> None:
    """Codex P2: ein unbekannter Entwicklerpfad im eigenen bgremover-Paket
    muss den Scan fehlschlagen lassen."""
    dist = tmp_path / "dist"
    dist.mkdir()
    _build_deb(
        tmp_path / "stage", dist / "leaky.deb",
        {"opt/test/bgremover/canvas.py": b"# built at /Users/alice/dev/picture_helper/bgremover"},
    )
    assert scan_release_artifacts.main([str(dist)]) == 1


@_needs_dpkg
def test_main_passes_for_deb_with_unknown_dev_path_in_third_party_dependency(tmp_path) -> None:
    """Derselbe unbekannte Pfad-Benutzer in einer Drittanbieter-Abhaengigkeit
    (kein bgremover-Pfad) ist nur informativ – reale CI-Laeufe zeigten, dass
    z. B. numpy/numba/networkx/PyQt6-sip eigene, harmlose Beispielpfade
    mitbringen (#608, s. Modul-Docstring)."""
    dist = tmp_path / "dist"
    dist.mkdir()
    _build_deb(
        tmp_path / "stage", dist / "clean.deb",
        {"opt/test/numpy/lib/_datasource.py": b"local files : '/home/guido/src/local/data.txt'"},
    )
    assert scan_release_artifacts.main([str(dist)]) == 0


def test_main_returns_one_for_empty_directory(tmp_path: Path) -> None:
    rc = scan_release_artifacts.main([str(tmp_path)])
    assert rc == 1


@_needs_dpkg
def test_main_with_clamav_scans_each_raw_deb_and_its_extracted_payload(
    tmp_path: Path, monkeypatch,
) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    _build_deb(
        tmp_path / "stage", dist / "clean.deb",
        {"opt/test/readme.txt": b"nothing interesting here"},
    )
    database = tmp_path / "clamav-db"
    database.mkdir()
    (database / "daily.cvd").write_bytes(b"test database marker")
    scanned = []

    monkeypatch.setattr(
        scan_release_artifacts, "verify_clamav_eicar", lambda db, workdir: True,
    )

    def fake_scan(artifact: Path, extracted: Path, db: Path):
        scanned.append((artifact, extracted, db))
        assert (extracted / "opt" / "test" / "readme.txt").is_file()
        return scan_release_artifacts.ArtifactMalwareResult(ok=True, detail="ok", targets=())

    monkeypatch.setattr(scan_release_artifacts, "scan_artifact_with_clamav", fake_scan)
    assert scan_release_artifacts.main(
        ["--clamav-database", str(database), str(dist)],
    ) == 0
    assert scanned == [
        (dist / "clean.deb", scanned[0][1], database),
    ]


# ── #920: Anomalie-Register ─────────────────────────────────────────────

_REGISTER_PATH = _ROOT / "release" / "build-anomalies.json"
_FINGERPRINT = (
    "bgremover.ai_process.InferenceError: Inferenzprozess hat die Verbindung geschlossen:"
)
_MACOS_LOG = (
    "Traceback (most recent call last):\n"
    '  File "bgremover/ai_process.py", line 294, in _request\n'
    "    raise InferenceError(\n"
    f"{_FINGERPRINT} \n"
    "smoke_launch OK: sauber gestartet\n"
)


def _register(**overrides: object) -> str:
    entry: dict = {
        "id": "beispiel",
        "fingerprint": "x" * scan_release_artifacts.MIN_FINGERPRINT_LENGTH,
        "platforms": ["macos-arm64"],
        "phases": ["smoke-launch-macos-app"],
        "reason": "Begruendung",
        "owner": "Release-Owner",
        "reference": "https://github.com/NikolayDA/picture_helper/issues/881",
        "expires": "2099-01-01",
    }
    entry.update(overrides.pop("entry", {}))  # type: ignore[arg-type]
    payload: dict = {
        "schema": scan_release_artifacts.REGISTER_SCHEMA,
        "kind": scan_release_artifacts.REGISTER_KIND,
        "register_version": 1,
        "entries": [entry],
    }
    payload.update(overrides)
    return json.dumps(payload, ensure_ascii=False)


def test_shipped_register_is_valid_and_starts_with_the_rembg_warmup_entry() -> None:
    """Akzeptanzkriterium #920: erster Eintrag = rembg-Warmup-Meldung (#881)."""
    register = scan_release_artifacts.load_register(_REGISTER_PATH)
    assert register.version >= 1
    first = register.entries[0]
    assert first.fingerprint == _FINGERPRINT
    assert first.reference.endswith("/881")
    assert first.owner
    assert first.reason
    assert first.expires > date(2026, 8, 31)
    assert first.platforms == ("macos-arm64",)
    assert first.phases == ("smoke-launch-macos-app",)


def test_shipped_register_entries_are_not_expired_today() -> None:
    """Ein bereits abgelaufener Eintrag waere ab dem naechsten Lauf wirkungslos."""
    register = scan_release_artifacts.load_register(_REGISTER_PATH)
    stale = scan_release_artifacts.expired_entries(
        register, today=datetime.now(timezone.utc).date()
    )
    assert stale == [], f"abgelaufene Registereintraege: {[e.entry_id for e in stale]}"


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (json.dumps({"schema": 2, "kind": "release-build-anomalies", "entries": []}), "Schema"),
        (json.dumps({"schema": 1, "kind": "etwas-anderes", "entries": []}), "Art"),
        ("{kein json", "JSON"),
        (json.dumps({"schema": 1, "kind": "release-build-anomalies",
                     "register_version": 0, "entries": []}), "register_version"),
    ],
)
def test_register_rejects_malformed_documents(payload: str, message: str) -> None:
    with pytest.raises(scan_release_artifacts.RegisterError, match=message):
        scan_release_artifacts.parse_register(payload)


def test_register_rejects_a_fingerprint_short_enough_to_act_as_a_broad_filter() -> None:
    """#920-Nicht-Ziel: keine breiten Suppressionen, nur exakte Fingerprints."""
    with pytest.raises(scan_release_artifacts.RegisterError, match="zu kurz"):
        scan_release_artifacts.parse_register(_register(entry={"fingerprint": "Error:"}))


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("platforms", ["windows-x86_64"], "unbekannte platforms"),
        ("phases", ["smoke-lunch-macos-app"], "unbekannte phases"),
        ("platforms", [], "nichtleere Liste"),
        ("reference", "https://example.invalid/issues/1", "reference"),
        ("expires", "irgendwann", "ISO-Datum"),
        ("owner", "", "owner"),
        ("reason", "   ", "reason"),
    ],
)
def test_register_rejects_incomplete_or_unknown_entry_fields(
    field: str, value: object, message: str
) -> None:
    with pytest.raises(scan_release_artifacts.RegisterError, match=message):
        scan_release_artifacts.parse_register(_register(entry={field: value}))


def test_register_rejects_duplicate_entry_ids() -> None:
    payload = json.loads(_register())
    payload["entries"].append(dict(payload["entries"][0]))
    with pytest.raises(scan_release_artifacts.RegisterError, match="doppelte"):
        scan_release_artifacts.parse_register(json.dumps(payload))


def test_missing_register_file_is_an_error_not_an_empty_register(tmp_path: Path) -> None:
    with pytest.raises(scan_release_artifacts.RegisterError, match="nicht lesbar"):
        scan_release_artifacts.load_register(tmp_path / "fehlt.json")


def test_main_refuses_to_run_with_an_unreadable_register(tmp_path: Path, capsys) -> None:
    """Fail-closed: ein kaputtes Register darf nicht als "nichts bekannt" gelten."""
    broken = tmp_path / "register.json"
    broken.write_text("{", encoding="utf-8")
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "x.AppImage").write_bytes(b"egal")
    assert scan_release_artifacts.main([
        "--anomaly-register", str(broken), "--platform", "macos-arm64", str(dist),
    ]) == 1
    assert "Anomalie-Register ungueltig" in capsys.readouterr().out


# ── #920: Anomalie-Erkennung in den Phasen-Logs ─────────────────────────

def test_traceback_is_reported_through_its_exception_line_only() -> None:
    """Die Kopfzeile allein traegt keine Meldung, an der ein Eintrag ansetzt."""
    found = scan_release_artifacts.detect_log_anomalies(
        _MACOS_LOG, phase="smoke-launch-macos-app"
    )
    assert [item.text for item in found] == [_FINGERPRINT]
    assert found[0].kind == "traceback"


def test_truncated_traceback_still_reports_its_header() -> None:
    found = scan_release_artifacts.detect_log_anomalies(
        "Traceback (most recent call last):\n  File \"x.py\", line 1\n", phase="deb-install-smoke",
    )
    assert [item.text for item in found] == ["Traceback (most recent call last):"]


def test_repeated_identical_anomalies_are_counted_not_repeated() -> None:
    found = scan_release_artifacts.detect_log_anomalies(
        "ValueError: doppelt\nharmlos\nValueError: doppelt\n", phase="smoke-launch-appimage",
    )
    assert len(found) == 1 and found[0].occurrences == 2


def test_a_clean_log_produces_no_anomalies() -> None:
    assert scan_release_artifacts.detect_log_anomalies(
        "smoke_launch OK: sauber gestartet (peak Instanzen=2, erlaubt=5)\n",
        phase="smoke-launch-appimage",
    ) == []


def test_annotation_and_fatal_lines_count_as_anomalies() -> None:
    found = scan_release_artifacts.detect_log_anomalies(
        "::warning::etwas\nFatal Python error: Segmentation fault\n",
        phase="smoke-launch-appimage",
    )
    assert {item.kind for item in found} == {"annotation", "fatal"}


# ── #920: bekannt vs. unbekannt, Ablaufdatum ────────────────────────────

def _classify(today: date, *, platform: str = "macos-arm64", expires: str = "2099-01-01"):
    register = scan_release_artifacts.parse_register(_register(
        entry={"fingerprint": _FINGERPRINT, "expires": expires}
    ))
    anomalies = scan_release_artifacts.detect_log_anomalies(
        _MACOS_LOG, phase="smoke-launch-macos-app"
    )
    return register, scan_release_artifacts.classify_anomalies(
        anomalies, register, platform=platform, today=today,
    )


def test_a_matching_entry_annotates_instead_of_hiding() -> None:
    _, (known, unknown) = _classify(date(2026, 8, 31))
    assert unknown == []
    assert len(known) == 1
    assert known[0]["entry_id"] == "beispiel"
    assert known[0]["text"] == _FINGERPRINT      # Wortlaut bleibt sichtbar
    assert known[0]["reference"].endswith("/881")


def test_an_entry_does_not_apply_to_another_platform() -> None:
    _, (known, unknown) = _classify(date(2026, 8, 31), platform="linux-x86_64")
    assert known == [] and len(unknown) == 1


def test_an_expired_entry_stops_annotating_and_is_reported_visibly() -> None:
    """#920: abgelaufen heisst Warnung statt stiller Weitergeltung."""
    register, (known, unknown) = _classify(date(2026, 8, 31), expires="2026-08-30")
    assert known == [], "ein abgelaufener Eintrag darf nicht mehr annotieren"
    assert len(unknown) == 1
    stale = scan_release_artifacts.expired_entries(register, today=date(2026, 8, 31))
    assert [entry.entry_id for entry in stale] == ["beispiel"]


def test_the_expiry_boundary_day_still_annotates() -> None:
    _, (known, _) = _classify(date(2026, 8, 30), expires="2026-08-30")
    assert len(known) == 1


# ── #920: Register unterdrueckt niemals Scanner-Befunde ─────────────────

def test_overall_verdict_takes_no_register_argument_at_all() -> None:
    """Struktureller Beleg der Invariante: das Verdikt kann das Register nicht sehen."""
    parameters = inspect.signature(scan_release_artifacts.overall_verdict).parameters
    assert list(parameters) == ["hard_findings", "unavailable"]
    assert scan_release_artifacts.overall_verdict(["ein Fund"], []) == "FAIL"
    assert scan_release_artifacts.overall_verdict([], ["kein Scanner"]) == "UNAVAILABLE"
    assert scan_release_artifacts.overall_verdict([], []) == "PASS"


def test_a_register_entry_matching_a_secret_finding_never_suppresses_it(
    tmp_path: Path, capsys
) -> None:
    """Das Register annotiert Log-Muster, keine Befunde – auch nicht zufaellig.

    Der Eintrag hier traegt den Wortlaut des Secret-Befundes als Fingerprint
    und die passende Plattform. Trotzdem muss der Fund hart bleiben: Exit 1,
    Verdikt FAIL, Eintrag unter ``hard_findings`` – und nichts davon in
    ``anomalies.known``.
    """
    dist = tmp_path / "dist"
    dist.mkdir()
    leaky = dist / "leaky.AppImage"
    leaky.write_bytes(b"header " + _AWS_KEY + b" tail")
    register = tmp_path / "register.json"
    register.write_text(_register(entry={
        "fingerprint": "AWS Access Key ID (Position 7, Fingerprint",
        "platforms": ["macos-arm64"],
    }), encoding="utf-8")
    report = tmp_path / "report.json"

    def fake_extract(archive: Path, dest: Path) -> None:
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "inner.bin").write_bytes(b"harmlos")

    original = scan_release_artifacts.extract_payload
    scan_release_artifacts.extract_payload = fake_extract  # type: ignore[assignment]
    try:
        code = scan_release_artifacts.main([
            "--anomaly-register", str(register), "--platform", "macos-arm64",
            "--report", str(report), str(dist),
        ])
    finally:
        scan_release_artifacts.extract_payload = original  # type: ignore[assignment]

    assert code == 1
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["verdict"] == "FAIL"
    assert payload["counts"]["secrets"] == 1
    assert any("AWS Access Key ID" in item for item in payload["hard_findings"])
    assert payload["anomalies"]["known"] == []
    assert "möglicher Fund" in capsys.readouterr().out


# ── #920: Berichtsformat ────────────────────────────────────────────────

def _run_report(tmp_path: Path, *extra: str, logs: dict[str, str] | None = None):
    dist = tmp_path / "dist"
    dist.mkdir(exist_ok=True)
    artifact = dist / "BgRemover-9.9.9-macos-arm64-ai.AppImage"
    artifact.write_bytes(b"a" * 64)
    log_dir = tmp_path / "build-logs"
    log_dir.mkdir(exist_ok=True)
    for phase, text in (logs or {}).items():
        (log_dir / f"{phase}.log").write_text(text, encoding="utf-8")
    report = tmp_path / "security-scan-report.json"
    summary = tmp_path / "security-scan-summary.md"

    def fake_extract(archive: Path, dest: Path) -> None:
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "inner.bin").write_bytes(b"b" * 100)

    original = scan_release_artifacts.extract_payload
    scan_release_artifacts.extract_payload = fake_extract  # type: ignore[assignment]
    try:
        code = scan_release_artifacts.main([
            "--report", str(report), "--summary", str(summary),
            "--anomaly-register", str(_REGISTER_PATH), "--platform", "macos-arm64",
            "--build-log-dir", str(log_dir), *extra, str(dist),
        ])
    finally:
        scan_release_artifacts.extract_payload = original  # type: ignore[assignment]
    return code, json.loads(report.read_text(encoding="utf-8")), summary.read_text(
        encoding="utf-8"
    )


def test_report_holds_every_field_the_runbook_step_needs(tmp_path: Path) -> None:
    code, report, _ = _run_report(tmp_path, logs={"smoke-launch-macos-app": _MACOS_LOG})
    assert code == 0
    assert report["schema"] == scan_release_artifacts.REPORT_SCHEMA
    assert report["kind"] == scan_release_artifacts.REPORT_KIND
    assert report["platform"] == "macos-arm64"
    # Ohne Signaturcache ist nur der Malware-Teil unbekannt, nicht der Scan.
    assert report["verdict"] == "UNAVAILABLE"
    assert report["malware_scan"]["status"] == "UNAVAILABLE"
    assert report["eicar_selftest"]["status"] == "UNAVAILABLE"
    assert set(report["counts"]) == {
        "secrets", "dev_paths_blocking", "dev_paths_informational",
        "malware_infected", "malware_failed_artifacts", "scan_errors",
    }
    assert report["limit_warnings"] == []
    assert report["signature_database"]["max_age_days"] == 14
    assert report["register"]["entries"] >= 1
    assert report["register"]["expired"] == []


def test_report_counts_raw_and_payload_bytes_separately(tmp_path: Path) -> None:
    """Runbook-Schritt 4 verlangt beide Teilmengen getrennt, nicht als Summe."""
    _, report, _ = _run_report(tmp_path)
    (artifact,) = report["artifacts"]
    assert artifact["raw_bytes"] == 64
    assert artifact["payload_bytes"] == 100
    assert artifact["payload_files"] == 1


def test_unavailable_malware_scan_is_visible_but_never_blocking(tmp_path: Path) -> None:
    code, report, summary = _run_report(tmp_path, "--malware-unavailable", "kein Cache-Treffer")
    assert code == 0, "UNAVAILABLE darf den Kandidatenbau nicht faellen"
    assert report["verdict"] == "UNAVAILABLE"
    assert any("kein Cache-Treffer" in item for item in report["unavailable"])
    assert "kein Cache-Treffer" in summary


def test_report_and_summary_exist_even_when_the_scan_fails(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "leaky.AppImage").write_bytes(b" " + _AWS_KEY + b" ")
    report = tmp_path / "report.json"
    summary = tmp_path / "summary.md"

    def fake_extract(archive: Path, dest: Path) -> None:
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "inner.bin").write_bytes(b"harmlos")

    original = scan_release_artifacts.extract_payload
    scan_release_artifacts.extract_payload = fake_extract  # type: ignore[assignment]
    try:
        code = scan_release_artifacts.main(
            ["--report", str(report), "--summary", str(summary), str(dist)]
        )
    finally:
        scan_release_artifacts.extract_payload = original  # type: ignore[assignment]
    assert code == 1
    assert json.loads(report.read_text(encoding="utf-8"))["verdict"] == "FAIL"
    assert "Harte Befunde" in summary.read_text(encoding="utf-8")


def test_summary_separates_known_from_unknown_so_nothing_familiar_hides_it(
    tmp_path: Path,
) -> None:
    """Akzeptanzkriterium: nichts Bekanntes darf etwas Neues verdecken."""
    _, report, summary = _run_report(tmp_path, logs={
        "smoke-launch-macos-app": _MACOS_LOG + "RuntimeError: etwas voellig Neues\n",
    })
    for heading in (
        "### 1. Harte Befunde",
        "### 2. `UNAVAILABLE`-Zustände",
        "### 3. Als bekannt annotierte Anomalien",
        "### 4. Unbekannte Auffälligkeiten",
    ):
        assert heading in summary, heading
    known = [item["text"] for item in report["anomalies"]["known"]]
    unknown = [item["text"] for item in report["anomalies"]["unknown"]]
    assert known == [_FINGERPRINT]
    assert unknown == ["RuntimeError: etwas voellig Neues"]
    assert "RuntimeError: etwas voellig Neues" in summary.split("### 4.")[1]


def test_expired_entry_produces_a_visible_warning_in_log_report_and_summary(
    tmp_path: Path, capsys
) -> None:
    register = tmp_path / "register.json"
    register.write_text(
        _register(entry={"fingerprint": _FINGERPRINT, "expires": "2000-01-01"}),
        encoding="utf-8",
    )
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "x.AppImage").write_bytes(b"harmlos")
    log_dir = tmp_path / "build-logs"
    log_dir.mkdir()
    (log_dir / "smoke-launch-macos-app.log").write_text(_MACOS_LOG, encoding="utf-8")
    report = tmp_path / "report.json"
    summary = tmp_path / "summary.md"

    def fake_extract(archive: Path, dest: Path) -> None:
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "inner.bin").write_bytes(b"harmlos")

    original = scan_release_artifacts.extract_payload
    scan_release_artifacts.extract_payload = fake_extract  # type: ignore[assignment]
    try:
        code = scan_release_artifacts.main([
            "--anomaly-register", str(register), "--platform", "macos-arm64",
            "--build-log-dir", str(log_dir), "--report", str(report),
            "--summary", str(summary), str(dist),
        ])
    finally:
        scan_release_artifacts.extract_payload = original  # type: ignore[assignment]

    assert code == 0, "ein abgelaufener Eintrag warnt, blockiert aber nicht"
    assert "::warning::Registereintrag 'beispiel' ist am 2000-01-01 abgelaufen" in (
        capsys.readouterr().out
    )
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert [item["id"] for item in payload["register"]["expired"]] == ["beispiel"]
    assert payload["anomalies"]["known"] == []
    assert len(payload["anomalies"]["unknown"]) == 1
    assert "Abgelaufene Einträge" in summary.read_text(encoding="utf-8")


# ── #920: ClamAV-Kennzahlen im Bericht ──────────────────────────────────

@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Data scanned: 1.28 GiB\n", int(1.28 * 1024**3)),
        ("Data scanned: 68 B\n", 68),
        ("Data scanned: 2.00 MB\n", 2_000_000),
        ("Data read: 1.00 MiB (ratio 1.00:1)\n", None),
    ],
)
def test_parse_scanned_bytes_covers_the_units_clamav_emits(
    text: str, expected: int | None
) -> None:
    assert scan_release_artifacts.parse_scanned_bytes(text) == expected


def test_signature_state_reports_age_and_staleness(monkeypatch, tmp_path: Path) -> None:
    """Frueher ein YAML-Heredoc im Workflow, seit #920 getestete Funktion."""
    def fake_run(cmd, **kwargs):
        assert cmd[:2] == ["clamscan", "--database"]
        return subprocess.CompletedProcess(
            cmd, 0, stdout="ClamAV 1.4.3/27812/Fri Aug 14 08:32:01 2026\n"
        )

    monkeypatch.setattr(scan_release_artifacts.subprocess, "run", fake_run)
    state = scan_release_artifacts.clamav_signature_state(
        tmp_path, now=datetime(2026, 8, 31, tzinfo=timezone.utc)
    )
    assert state["age_days"] == 16
    assert state["stale"] is True
    assert state["signature_date"].startswith("2026-08-14")


def test_signature_state_survives_an_unparsable_version_line(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        scan_release_artifacts.subprocess, "run",
        lambda cmd, **kwargs: subprocess.CompletedProcess(cmd, 0, stdout="ClamAV 1.4.3\n"),
    )
    state = scan_release_artifacts.clamav_signature_state(tmp_path)
    assert state["age_days"] is None and state["stale"] is False


# ── #920: Drift gegen den Kandidatenbau ─────────────────────────────────

def test_known_platforms_match_the_release_matrix() -> None:
    """Ein Tippfehler machte einen Registereintrag sonst still wirkungslos."""
    yaml = pytest.importorskip("yaml")
    workflow = yaml.safe_load(
        (_ROOT / ".github" / "workflows" / "release-linux.yml").read_text(encoding="utf-8")
    )
    tags = {
        leg["platform_tag"]
        for leg in workflow["jobs"]["build"]["strategy"]["matrix"]["include"]
    }
    assert set(scan_release_artifacts.KNOWN_PLATFORMS) == tags


def test_known_phases_match_the_logs_the_workflow_actually_writes() -> None:
    yaml = pytest.importorskip("yaml")
    workflow = yaml.safe_load(
        (_ROOT / ".github" / "workflows" / "release-linux.yml").read_text(encoding="utf-8")
    )
    written = set()
    for step in workflow["jobs"]["build"]["steps"]:
        for match in re.finditer(r'phase_log="build-logs/([\w-]+)\.log"', step.get("run", "")):
            written.add(match.group(1))
    assert set(scan_release_artifacts.KNOWN_PHASES) == written


def test_summary_surfaces_warnings_that_are_neither_findings_nor_gaps(tmp_path: Path) -> None:
    """Eine unbekannte Log-Phase darf nicht nur im JSON stehen."""
    _, report, summary = _run_report(tmp_path, logs={"smoke-launch-des-nachbarn": "alles ok\n"})
    assert any("smoke-launch-des-nachbarn" in item for item in report["warnings"])
    assert "Hinweise" in summary
    assert "smoke-launch-des-nachbarn" in summary


# ── #920-Review: Nachtrag im Fehlerfall (--logs-only) ───────────────────

def test_logs_only_classifies_the_phase_logs_without_touching_dist(tmp_path: Path) -> None:
    """Faellt ein Build-/Smoke-Schritt, laeuft der Artefaktscan nicht mehr.

    Genau dann liegen die Phasen-Logs aber vor – und genau dann ist die
    Unterscheidung "bekannte kosmetische Meldung vs. der eigentliche Fehler"
    am wertvollsten. ``dist/`` existiert in diesem Fall womoeglich gar nicht.
    """
    log_dir = tmp_path / "build-logs"
    log_dir.mkdir()
    (log_dir / "smoke-launch-macos-app.log").write_text(
        _MACOS_LOG + "RuntimeError: Prozessbaum musste hart beendet werden\n",
        encoding="utf-8",
    )
    report = tmp_path / "report.json"
    summary = tmp_path / "summary.md"

    code = scan_release_artifacts.main([
        "--logs-only", "--report", str(report), "--summary", str(summary),
        "--anomaly-register", str(_REGISTER_PATH), "--platform", "macos-arm64",
        "--build-log-dir", str(log_dir), str(tmp_path / "gibt-es-nicht"),
    ])

    assert code == 0
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["verdict"] == "UNAVAILABLE"
    assert payload["artifacts"] == []
    assert any("--logs-only" in item for item in payload["unavailable"])
    assert [item["entry_id"] for item in payload["anomalies"]["known"]] == [
        "rembg-warmup-connection-closed"
    ]
    assert [item["text"] for item in payload["anomalies"]["unknown"]] == [
        "RuntimeError: Prozessbaum musste hart beendet werden"
    ]


def test_logs_only_never_claims_artifacts_were_clean(tmp_path: Path, capsys) -> None:
    """Ein Erfolgssatz ueber ungescannte Artefakte waere schlicht unwahr."""
    log_dir = tmp_path / "build-logs"
    log_dir.mkdir()
    (log_dir / "smoke-launch-appimage.log").write_text("alles ok\n", encoding="utf-8")
    assert scan_release_artifacts.main([
        "--logs-only", "--build-log-dir", str(log_dir), str(tmp_path / "nichts"),
    ]) == 0
    output = capsys.readouterr().out
    assert "keine hochkonfidenten Funde in allen" not in output
    assert "Nur Phasen-Logs ausgewertet" in output


def test_an_empty_dist_stays_a_hard_error_without_logs_only(tmp_path: Path, capsys) -> None:
    """Das ist die Eigenschaft, wegen der der Scan-Schritt kein always() traegt."""
    dist = tmp_path / "dist"
    dist.mkdir()
    assert scan_release_artifacts.main([str(dist)]) == 1
    assert "Keine Dateien in" in capsys.readouterr().out


def test_logs_only_and_clamav_are_mutually_exclusive(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        scan_release_artifacts.main(
            ["--logs-only", "--clamav-database", str(tmp_path), str(tmp_path)]
        )
