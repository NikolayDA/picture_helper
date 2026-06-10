"""Redaktions-Tests für ``diagnose_mac.sh`` (Befund #185).

Das Diagnose-Skript wird mit kontrolliertem ``HOME`` (Wegwerf-Verzeichnis
mit präparierter Log-Datei) ausgeführt. Standardmäßig dürfen weder das
Home-Verzeichnis noch Bild-/Nutzerpfade aus dem Log in der Ausgabe
auftauchen; ``--include-raw-logs`` liefert bewusst die volle Diagnose.
Wie ``test_app_smoke`` bewusst ohne ``ui``-Marker, läuft also in der CI.
"""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "diagnose_mac.sh"

# Geplante sensible Inhalte der präparierten Log-Datei – exakt das, was
# laut Befund #185 nicht in einer teilbaren Diagnose landen darf.
SENSITIVE_USER = "testnutzer"
SENSITIVE_IMAGE = "geheimes-urlaubsfoto.png"


def _prepare_home(tmp_path: Path) -> Path:
    """Baut ein Fake-``HOME`` mit Log-Datei am macOS-AppData-Pfad."""
    home = tmp_path / "home"
    log_dir = home / "Library" / "Application Support" / "BgRemover"
    log_dir.mkdir(parents=True)
    log_lines = [
        "2026-06-08 10:00:00,123 INFO BgRemover: Anwendung gestartet",
        "2026-06-08 10:00:01,456 ERROR BgRemover: Speichern fehlgeschlagen: "
        f"/Users/{SENSITIVE_USER}/Bilder/{SENSITIVE_IMAGE}",
        f"2026-06-08 10:00:02,789 WARNING BgRemover: Ladefehler: {home}/Pictures/{SENSITIVE_IMAGE}",
    ]
    (log_dir / "bgremover.log").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    return home


def _run_diagnose(home: Path, *args: str) -> subprocess.CompletedProcess:
    """Führt das Skript mit Fake-``HOME`` und neutralem cwd aus.

    Neutrales ``cwd`` (das Fake-Home) hält die ``./.venv``-Kandidaten des
    Repos aus dem Lauf heraus – die Pfad-Assertions hängen sonst an der
    lokalen venv-Aufstellung.
    """
    env = dict(os.environ, HOME=str(home))
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        cwd=home, env=env, capture_output=True, text=True, timeout=180,
    )


@pytest.fixture()
def fake_home(tmp_path: Path) -> Path:
    if shutil.which("bash") is None:
        pytest.skip("bash nicht verfügbar")
    return _prepare_home(tmp_path)


def test_default_output_redacts_home_and_log_paths(fake_home):
    """Standardlauf: kein Home-Pfad, kein Nutzername, kein Bildpfad im Output."""
    r = _run_diagnose(fake_home)
    assert r.returncode == 0, (
        f"diagnose_mac.sh endete mit {r.returncode}\n"
        f"--- stdout ---\n{r.stdout}\n--- stderr ---\n{r.stderr}"
    )
    out = r.stdout
    assert str(fake_home) not in out, "eigenes HOME muss zu '~' redaktiert sein"
    assert SENSITIVE_USER not in out, "/Users/<name> aus Log-Zeilen muss redaktiert sein"
    assert SENSITIVE_IMAGE not in out, "Bildpfade aus dem Log müssen redaktiert sein"
    # Redaktion sichtbar statt Information stillschweigend weg:
    assert "Log: ~/Library" in out
    assert "<pfad redaktiert>" in out
    assert "--include-raw-logs" in out, "Hinweis auf die Voll-Diagnose fehlt"
    # Die Zusammenfassung behält die Fehlermeldung selbst und filtert INFO:
    assert "Speichern fehlgeschlagen:" in out
    assert "Anwendung gestartet" not in out


def test_include_raw_logs_keeps_full_paths(fake_home):
    """``--include-raw-logs`` liefert bewusst den unredaktierten Log-Tail."""
    r = _run_diagnose(fake_home, "--include-raw-logs")
    assert r.returncode == 0, (
        f"diagnose_mac.sh endete mit {r.returncode}\n"
        f"--- stdout ---\n{r.stdout}\n--- stderr ---\n{r.stderr}"
    )
    out = r.stdout
    assert f"/Users/{SENSITIVE_USER}/Bilder/{SENSITIVE_IMAGE}" in out
    assert f"{fake_home}/Pictures/{SENSITIVE_IMAGE}" in out
    assert "UNREDAKTIERTE" in out, "Warnhinweis im Fußteil fehlt"


def test_unknown_option_fails_with_usage(fake_home):
    """Unbekannte Optionen brechen mit Exit-Code 2 und Usage-Hinweis ab."""
    r = _run_diagnose(fake_home, "--unbekannt")
    assert r.returncode == 2
    assert "Aufruf:" in r.stderr
