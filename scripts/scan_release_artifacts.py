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
Benutzernamen außerhalb der expliziten Allowlist gelten als möglicher Leak
einer echten Entwicklermaschine – aber **nur innerhalb des eigenen
``bgremover``-Pakets** lässt das den Scan hart fehlschlagen. Drittanbieter-
Abhängigkeiten (numpy, networkx, PyQt6-sip, …) bringen nachweislich eigene,
harmlose ``/home``/``/Users``-Beispielpfade mit – Docstrings (numpys
``DataSource`` nutzt seit jeher ``/home/guido/…``), Kommentare (numbas
``pycc/cc.py`` nennt ``/home/antoine/…``), Zitat-URLs (networkx' HITS-Modul
verlinkt Jon Kleinbergs Cornell-Homepage ``.../home/kleinber/auth.pdf``) oder
vom jeweiligen Hersteller einkompilierte Build-Pfade (PyQt6-Qt6s ``sip``-
Erweiterung enthält ``/home/bob/bob/include/…``). Diese Strings gehören nicht
zu unserem Build und ändern sich unvorhersehbar mit jedem Versions-Bump einer
Abhängigkeit – ein Hart-Fehlschlag darauf wäre struktureller Lärm ohne
Sicherheitswert (empirisch an drei realen CI-Läufen bestätigt, #608). Nur
``bgremover`` kompilieren wir selbst zu Bytecode; ein echter Leak einer
Entwicklermaschine könnte sich daher ausschließlich dort zeigen. Funde
außerhalb bleiben sichtbar (nicht blockierend geloggt), damit nichts still
verschwindet.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

# Echte Secrets stehen als eigenstaendiger Wert (Umgebungsvariable, Header,
# JSON-Feld, Kommandozeile) und sind daher immer von einem Nicht-Identifier-
# Zeichen umgeben (Anfuehrungszeichen, Gleichheitszeichen, Leerraum,
# Zeilenende). In grossen kompilierten Binaerdateien (C++-Mangling,
# Symboltabellen) tauchen dieselben Zeichenklassen dagegen oft *mitten* in
# einem viel laengeren, ununterbrochenen Bezeichner auf – z. B. "highs_..."
# enthaelt "ghs_" ohne Wortgrenze davor. Die Lookaround-Anker unten verwerfen
# genau diesen Fall, ohne auf einen Fingerprint-Allowlist-Eintrag pro
# Bibliothek angewiesen zu sein (empirisch bestaetigt: scipy/HiGHS liefert so
# 43 Treffer aus derselben Namenskonvention – ein Fingerprint je Symbol waere
# nicht wartbar).
_SECRET_PATTERNS: dict[str, re.Pattern[bytes]] = {
    "AWS Access Key ID": re.compile(rb"(?<![A-Za-z0-9])AKIA[0-9A-Z]{16}(?![A-Za-z0-9])"),
    "GitHub-Token": re.compile(
        rb"(?<![A-Za-z0-9_])gh[oprsu]_[A-Za-z0-9]{36,}(?![A-Za-z0-9_])"
        rb"|(?<![A-Za-z0-9_])github_pat_[A-Za-z0-9_]{22,}(?![A-Za-z0-9_])"
    ),
    "privater PEM-Schlüssel": re.compile(
        rb"-----BEGIN (RSA |EC |OPENSSH |DSA |ENCRYPTED |)PRIVATE KEY-----"
    ),
    "Slack-Token": re.compile(rb"(?<![A-Za-z0-9-])xox[baprs]-[0-9A-Za-z-]{10,}(?![A-Za-z0-9-])"),
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
    zusaetzlicher, echter Fund nicht hinter einem frueheren Treffer verborgen
    bleibt; identische (Label, Fingerprint) werden dedupliziert, damit ein
    oft wiederholter Treffer nicht die Ausgabe flutet.
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


def _is_own_package_path(relative_path: Path) -> bool:
    """True, wenn *relative_path* zum eigenen ``bgremover``-Paket gehört.

    Alles andere im entpackten Baum ist eine Drittanbieter-Abhängigkeit, die
    wir nie selbst kompilieren – deren eigene ``/home``/``/Users``-Strings
    sind daher kein Signal für einen Leak unserer Build-Umgebung."""
    return "bgremover" in relative_path.parts


def scan_artifact(path: Path, workdir: Path) -> tuple[list[str], set[str], set[str]]:
    """Scannt *path* selbst (Container-Ebene) und seinen entpackten Inhalt.

    Liefert ``(Funde, blockierende Pfad-Benutzer, informative Pfad-Benutzer)``.
    Blockierend ist nur ein unbekannter Pfad-Benutzer innerhalb des eigenen
    ``bgremover``-Pakets; derselbe Fund in einer Drittanbieter-Abhängigkeit
    oder in den rohen Container-Bytes (keine Paketzuordnung möglich) ist
    lediglich informativ – s. Modul-Docstring."""
    raw = path.read_bytes()
    findings = scan_bytes(raw)
    informational_users = dev_path_users(raw)
    blocking_users: set[str] = set()

    extract_dir = workdir / f"{path.name}.extracted"
    extract_payload(path, extract_dir)
    for member in extract_dir.rglob("*"):
        if member.is_file() and not member.is_symlink():
            data = member.read_bytes()
            findings.extend(scan_bytes(data))
            users = dev_path_users(data)
            if not users:
                continue
            if _is_own_package_path(member.relative_to(extract_dir)):
                blocking_users |= users
            else:
                informational_users |= users
    return findings, blocking_users, informational_users


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
                findings, blocking_users, informational_users = scan_artifact(path, workdir)
            except (subprocess.CalledProcessError, ValueError) as exc:
                print(f"::error::{path.name}: Entpacken zum Scannen fehlgeschlagen – {exc}")
                failed = True
                continue
            for finding in findings:
                print(f"::error::{path.name}: möglicher Fund – {finding}")
                failed = True
            if blocking_users:
                print(
                    f"::error::{path.name}: unbekannte Pfad-Benutzer im eigenen bgremover-Paket "
                    f"außerhalb der Allowlist {sorted(_ALLOWED_PATH_USERS)}: {sorted(blocking_users)}"
                )
                failed = True
            else:
                print("   OK: keine Entwicklerpfade außerhalb der Allowlist im eigenen Paket gefunden")
            if informational_users:
                print(
                    f"   Hinweis (nicht blockierend): unbekannte Pfad-Benutzer in "
                    f"Drittanbieter-Inhalten außerhalb der Allowlist "
                    f"{sorted(_ALLOWED_PATH_USERS)}: {sorted(informational_users)}"
                )

    if failed:
        print("::error::Secret-Scan fehlgeschlagen – siehe obige Funde.")
        return 1
    print(">> Secret-/Pfad-Scan (#584): keine hochkonfidenten Funde in allen Artefakten (inkl. entpacktem Inhalt).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
