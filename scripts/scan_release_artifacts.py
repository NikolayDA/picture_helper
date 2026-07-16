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

# Bekannte Fehlalarme in Drittanbieter-Binaerdateien, die diese Anwendung
# bewusst mitbuendelt (#584/#608). Jeder Eintrag wurde durch einen lokalen
# Nachbau der exakten, in requirements/constraints.txt gepinnten
# rembg[cpu]-/PyQt6-Abhaengigkeiten *empirisch verifiziert* (nicht nur
# vermutet) – der Fund liegt nachweislich in oeffentlichem Drittanbieter-Code,
# nicht in diesem Projekt. Schluessel: SHA-256-Fingerprint der ersten 12
# Hex-Zeichen (wie in den Funden geloggt). Achtung Wartungslast: ein
# Versions-Bump von Pillow/scipy aendert den exakten Byte-Inhalt und damit
# den Fingerprint – der Scan schlaegt dann erneut fehl, bis der neue
# Fingerprint auf dieselbe Weise nachverifiziert und ergaenzt wird. Das ist
# beabsichtigt (kein blindes Vertrauen in "diese Bibliothek ist immer
# sicher"), nicht ein Defekt dieses Mechanismus. PEM-Treffer sind hier
# bewusst NICHT gelistet: die Kopfzeile allein (der einzige Teil, den das
# PEM-Muster erfasst) ist immer einer von nur sechs festen Strings, egal ob
# echtes Schluesselmaterial folgt oder nicht – ein Fingerprint nur der
# Kopfzeile waere nicht aussagekraeftig (jede echte PEM-Datei desselben Typs
# haette denselben Fingerprint wie ein Fehlalarm). Fuer PEM entscheidet
# stattdessen `_looks_like_real_pem_body` anhand des tatsaechlich folgenden
# Inhalts (s. u.) – robuster gegenueber Versions-/Architektur-Aenderungen,
# da mehrfach empirisch bestaetigt (x86_64/aarch64/macOS-arm64: 16
# unterschiedliche Fingerprints allein fuer dieselbe OpenSSL-Typtabelle in
# PyQt6-Qt6, s. PR-#608-Diskussion).
_ALLOWED_SECRET_FINGERPRINTS = {
    # Pillow, PIL/ImageFont.py: "AKIA" + 16 alphanumerische Zeichen tritt
    # zufaellig innerhalb einer als Literal eingebetteten, Base64-kodierten
    # Schriftmetrik-Tabelle auf (oeffentlicher, MIT-lizenzierter Quelltext).
    # Nur auf den Linux-Beinen beobachtet (python-appimage buendelt die
    # .py-Quelle direkt); die macOS-.app-Buendelung (PyInstaller) hat hier
    # keinen Treffer.
    "57a26f03da12": "Pillow ImageFont-Tabelle (Zufallstreffer in Base64-Daten)",
    # scipy, scipy/optimize/_highspy/_core*.so: "ghs_" ist eine Teilzeichen-
    # kette von "highs_setCallback" (HiGHS-Solver-C-API), gefolgt von genug
    # alphanumerischen Zeichen aus dem C++-Mangling, um zufaellig zu passen.
    # Der exakte Fingerprint ist Compiler-/Plattform-abhaengig (Linux
    # GCC-Build vs. macOS-Clang-Build erzeugen unterschiedliches Mangling).
    "d5ac2d294246": "scipy/HiGHS gemanglete C++-Symbole, Linux x86_64/aarch64 (Zufallstreffer)",
    "6d2cd5d3aea5": "scipy/HiGHS gemanglete C++-Symbole, macOS arm64 (Zufallstreffer)",
}

# Ein echter PEM-Schluessel hat unmittelbar nach der Kopfzeile (hoechstens
# durch einen Zeilenumbruch getrennt) einen langen Base64-Koerper
# (typischerweise hunderte Zeichen). OpenSSLs eigene PEM-Typtabelle (in
# libQt6Network/libqopensslbackend etc., s. o.) hat direkt danach nur ein
# Nullbyte oder das naechste Label. Eine reine "irgendwo in den naechsten
# Bytes"-Suche reicht nicht: einkompilierte Klartext-Fehlermeldungen wie
# "QSslDiffieHellmanParameters" (28 Zeichen, nur Buchstaben) koennen zufaellig
# lang genug sein – deshalb muss der Base64-Lauf **direkt** an die Kopfzeile
# anschliessen (± ein Zeilenumbruch), nicht irgendwo in einem Lookahead-Fenster.
_PEM_BODY_START = re.compile(rb"[\r\n]{0,2}[A-Za-z0-9+/=]{40,}")


def _looks_like_real_pem_body(data: bytes, match_end: int) -> bool:
    """Unterscheidet echtes PEM-Schluesselmaterial von einer Bibliotheks-
    internen Typ-/Dispatch-Tabelle (kein direkt anschliessender Schluessel-
    koerper)."""
    return _PEM_BODY_START.match(data, match_end) is not None


def scan_bytes(data: bytes) -> list[str]:
    """Sucht Geheimnis-Muster in *data*; liefert redigierte Fund-Beschreibungen.

    Loggt nie das Geheimnis selbst – nur Label, Byte-Position und einen
    SHA-256-Fingerprint der ersten 12 Hex-Zeichen, ausreichend zur
    Korrelation ("ist das derselbe Fund wie vorhin"), aber nicht umkehrbar.
    Findet alle Vorkommen je Muster (nicht nur das erste), damit ein
    zusaetzlicher, echter Fund nicht hinter einem frueheren – ggf.
    zugelassenen – Treffer verborgen bleibt; identische (Label, Fingerprint)
    werden dedupliziert, damit ein oft wiederholter Treffer nicht die
    Ausgabe flutet.
    """
    findings = []
    seen: set[tuple[str, str]] = set()
    for label, pattern in _SECRET_PATTERNS.items():
        for match in pattern.finditer(data):
            if label == "privater PEM-Schlüssel" and not _looks_like_real_pem_body(
                data, match.end()
            ):
                continue
            fingerprint = hashlib.sha256(match.group(0)).hexdigest()[:12]
            if fingerprint in _ALLOWED_SECRET_FINGERPRINTS:
                continue
            key = (label, fingerprint)
            if key in seen:
                continue
            seen.add(key)
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
