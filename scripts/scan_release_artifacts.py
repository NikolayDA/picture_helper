#!/usr/bin/env python3
"""Sekret-/Entwicklerpfad-Scan für gebaute Release-Artefakte (#584).

Entpackt jedes Artefakt in einem Verzeichnis (z. B. ``dist/``) – AppImage
(``--appimage-extract``), ``.deb`` (``dpkg-deb -x``, rekursiv für die darin
gewrappte AppImage) bzw. ``.dmg`` (``hdiutil attach``/``detach``) – und prüft
sowohl die Rohdatei als auch jede entpackte Datei binär auf hochkonfidente
Geheimnis-Muster (AWS-Keys, GitHub-Tokens, private PEM-Schlüssel). Ein reiner
Scan der komprimierten Container-Bytes würde eingebettete Geheimnisse in den
komprimierten Nutzdaten (SquashFS/data.tar/UDZO) verfehlen. Ein Treffer beendet
den Scan mit Exit 1 – geloggt wird nur ein nicht umkehrbares Fingerprint, nie
das Geheimnis selbst, damit der Scan keine Geheimnisse in die CI-Logs kopiert.

Absolute Pfade unter ``/home/<user>`` bzw. ``/Users/<user>`` mit einem
Benutzernamen außerhalb der expliziten Allowlist (CI-Konten plus bekannte
Drittanbieter-Build-Infrastruktur) gelten als Leak einer echten
Entwicklermaschine und lassen den Scan ebenfalls fehlschlagen.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

_SECRET_PATTERNS: dict[str, re.Pattern[bytes]] = {
    "AWS Access Key ID": re.compile(rb"AKIA[0-9A-Z]{16}"),
    "GitHub-Token": re.compile(rb"gh[oprsu]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,}"),
    "privater PEM-Schlüssel": re.compile(
        rb"-----BEGIN (RSA |EC |OPENSSH |DSA |ENCRYPTED |)PRIVATE KEY-----"
    ),
    "Slack-Token": re.compile(rb"xox[baprs]-[0-9A-Za-z-]{10,}"),
}
_DEV_PATH = re.compile(rb"/(?:home|Users)/([A-Za-z0-9_.-]+)/")
# "qt" stammt aus dem oeffentlich bekannten Build-Pfad-Muster der Qt-eigenen
# CI (/home/qt/work/...) in den gebuendelten PyQt6/Qt-Bibliotheken; "default"
# aus dem macOS-Standardbenutzer-Vorlagenverzeichnis /Users/default/..., Teil
# des Betriebssystems bzw. der Xcode-Toolchain. Beides ist wiederholt in
# sauberen CI-Builds beobachtet worden (kein Leak einer echten
# Entwicklermaschine) und daher explizit zugelassen; jeder andere Benutzername
# laesst den Scan fehlschlagen.
_ALLOWED_PATH_USERS = {"runner", "root", "qt", "default"}


def scan_bytes(data: bytes) -> list[str]:
    """Sucht Geheimnis-Muster in *data*; liefert redigierte Fund-Beschreibungen.

    Loggt nie das Geheimnis selbst – nur Label, Byte-Position und einen
    SHA-256-Fingerprint der ersten 12 Hex-Zeichen, ausreichend zur
    Korrelation ("ist das derselbe Fund wie vorhin"), aber nicht umkehrbar.
    """
    findings = []
    for label, pattern in _SECRET_PATTERNS.items():
        match = pattern.search(data)
        if match:
            fingerprint = hashlib.sha256(match.group(0)).hexdigest()[:12]
            findings.append(f"{label} (Position {match.start()}, Fingerprint {fingerprint})")
    return findings


def dev_path_users(data: bytes) -> set[str]:
    """Liefert alle in *data* gefundenen Pfad-Benutzer außerhalb der Allowlist."""
    users = {m.group(1).decode("ascii", errors="replace") for m in _DEV_PATH.finditer(data)}
    return users - _ALLOWED_PATH_USERS


def _run(cmd: list[str], **kwargs: object) -> None:
    subprocess.run(cmd, check=True, capture_output=True, **kwargs)  # type: ignore[arg-type]


def extract_payload(archive: Path, dest: Path) -> None:
    """Entpackt *archive* (AppImage/.deb/.dmg) nach *dest*.

    Fuer ``.deb`` rekursiv: das Paket wrappt selbst wieder eine AppImage
    (``/opt/BgRemover/BgRemover.AppImage``), die ebenfalls entpackt wird, sonst
    bliebe ihr komprimierter SquashFS-Inhalt ungeprueft.
    """
    dest.mkdir(parents=True, exist_ok=True)
    suffix = archive.suffix.lower()
    if suffix == ".appimage":
        archive.chmod(archive.stat().st_mode | 0o111)
        _run([str(archive.resolve()), "--appimage-extract"], cwd=dest)
    elif suffix == ".deb":
        _run(["dpkg-deb", "-x", str(archive.resolve()), str(dest)])
        for inner in list(dest.rglob("*.AppImage")):
            extract_payload(inner, inner.parent / f"{inner.name}.extracted")
    elif suffix == ".dmg":
        mount_point = dest / "mnt"
        mount_point.mkdir()
        _run(
            ["hdiutil", "attach", "-nobrowse", "-readonly", "-mountpoint", str(mount_point),
             str(archive.resolve())]
        )
        try:
            for item in mount_point.rglob("*"):
                if item.is_file() and not item.is_symlink():
                    target = dest / "contents" / item.relative_to(mount_point)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target)
        finally:
            subprocess.run(["hdiutil", "detach", str(mount_point), "-quiet"], check=False)
    else:
        raise ValueError(f"unbekanntes Artefaktformat: {archive.suffix}")


def scan_artifact(path: Path, workdir: Path) -> tuple[list[str], set[str]]:
    """Scannt *path* selbst (Container-Ebene) und seinen entpackten Inhalt."""
    raw = path.read_bytes()
    findings = scan_bytes(raw)
    unknown_users = dev_path_users(raw)

    extract_dir = workdir / f"{path.name}.extracted"
    extract_payload(path, extract_dir)
    for member in extract_dir.rglob("*"):
        if member.is_file() and not member.is_symlink():
            data = member.read_bytes()
            findings.extend(scan_bytes(data))
            unknown_users |= dev_path_users(data)
    return findings, unknown_users


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default="dist", help="zu scannendes Verzeichnis")
    args = parser.parse_args(argv)

    directory = Path(args.directory)
    files = sorted(p for p in directory.iterdir() if p.is_file())
    if not files:
        print(f"::error::Keine Dateien in {directory} gefunden.")
        return 1

    failed = False
    with tempfile.TemporaryDirectory(prefix="scan-release-artifacts-") as tmp:
        workdir = Path(tmp)
        for path in files:
            size_mb = path.stat().st_size / 1_000_000
            print(f">> Scanne {path.name} ({size_mb:.1f} MB, inkl. entpacktem Inhalt)")
            try:
                findings, unknown_users = scan_artifact(path, workdir)
            except (subprocess.CalledProcessError, ValueError) as exc:
                print(f"::error::{path.name}: Entpacken zum Scannen fehlgeschlagen – {exc}")
                failed = True
                continue
            for finding in findings:
                print(f"::error::{path.name}: möglicher Fund – {finding}")
                failed = True
            if unknown_users:
                print(
                    f"::error::{path.name}: unbekannte Pfad-Benutzer außerhalb der Allowlist "
                    f"{sorted(_ALLOWED_PATH_USERS)}: {sorted(unknown_users)}"
                )
                failed = True
            else:
                print("   OK: keine Entwicklerpfade außerhalb der Allowlist gefunden")

    if failed:
        print("::error::Secret-Scan fehlgeschlagen – siehe obige Funde.")
        return 1
    print(">> Secret-/Pfad-Scan (#584): keine hochkonfidenten Funde in allen Artefakten (inkl. entpacktem Inhalt).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
