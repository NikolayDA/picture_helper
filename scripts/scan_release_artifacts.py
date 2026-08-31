#!/usr/bin/env python3
"""Sicherheits-Scan für gebaute Release-Artefakte (#584, #731, #920).

Entpackt jedes Artefakt in einem Verzeichnis (z. B. ``dist/``) – AppImage
(``--appimage-extract``), ``.deb`` (``dpkg-deb -x``, rekursiv für die darin
gewrappte AppImage) bzw. ``.dmg`` (``hdiutil attach``/``detach``) – und prüft
sowohl die Rohdatei als auch jede entpackte Datei binär auf hochkonfidente
Geheimnis-Muster (AWS-Keys, GitHub-Tokens, private PEM-Schlüssel,
Slack-Tokens). Ein reiner
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

Mit ``--clamav-database`` wird dieselbe entpackte Nutzdatenbasis zusätzlich
mit ClamAV geprüft. Vor dem Artefaktscan muss die aktive Signaturdatenbank den
EICAR-Kontrollstring erkennen. Danach wird jedes Artefakt separat zusammen mit
seinem entpackten Inhalt gescannt. Der Lauf ist nur erfolgreich, wenn ClamAV
Exit 0, null Funde, keine Limitwarnung und mehr als 0 gescannte Bytes meldet.
Die expliziten 2-GB-Limits liegen über den bekannten Release-Artefakten; jede
sonstige Limitüberschreitung wird durch ``--alert-exceeds-max=yes`` zum harten
Fehler statt zu einem still als sauber gewerteten Skip.

**Maschinenlesbarer Bericht (#920).** ``--report`` schreibt zusätzlich
``security-scan-report.json``: je Artefakt die getrennt gescannten Bytes von
Rohdatei und entpackter Nutzlast, Befundzahlen je Kategorie, den
EICAR-Selbsttest, Limitwarnungen, das Alter der Signaturdatenbank und das
Gesamtverdikt ``PASS``/``FAIL``/``UNAVAILABLE``. ``--summary`` rendert daraus
die Job-Summary, gegliedert in harte Befunde, ``UNAVAILABLE``-Zustände, als
bekannt annotierte Anomalien und unbekannte Auffälligkeiten. Runbook-Schritt 4
stützt sich auf diesen Bericht; die ``MALWARE-01``-Entscheidung bleibt beim
Security-Owner.

**Register bekannter Build-Anomalien (#920).** ``--anomaly-register`` liest
``release/build-anomalies.json`` und annotiert damit **ausschließlich
Log-Muster** der Bau-Phasen (``--build-log-dir``), die als unbedenklich
eingestuft und begründet sind. Das Register ist strikt getrennt von der
Befundlogik: Es kann kein Secret-, Entwicklerpfad- oder Malware-Ergebnis
verändern, geht nicht in ``overall_verdict`` ein und ändert nie den
Exit-Code. Ein abgelaufener Eintrag annotiert nicht mehr und erzeugt eine
sichtbare Warnung, damit die Anomalie erneut in der Triage landet statt still
weiterzugelten.

``--logs-only`` wertet ausschließlich die Phasen-Logs aus und rührt ``dist/``
nicht an. Der Artefaktscan im Kandidatenbau läuft nur bei Erfolg – fällt vorher
ein Build- oder Smoke-Schritt, trägt ein eigener Schritt die Anomalie-Durchsicht
in diesem Modus nach. Ein leeres ``dist/`` bleibt dadurch das, was es ist: bei
einem grünen Build ein harter Fehler.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Final

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

_CLAMAV_LIMIT_OPTIONS = (
    "--max-filesize=2000M",
    "--max-scansize=2000M",
    "--max-files=2000000",
    # ClamAV begrenzt diesen Wert selbst auf 100. Die maximale gueltige
    # Rekursionstiefe verhindert stille Standard-Skips, ohne den gesamten
    # Aufruf wegen einer ungueltigen Option vor dem ersten Scan abzubrechen.
    "--max-recursion=100",
    "--max-embeddedpe=2000M",
    "--pcre-max-filesize=2000M",
    "--alert-exceeds-max=yes",
)
_CLAMAV_DATA_SCANNED = re.compile(
    r"(?m)^Data scanned:\s*([0-9]+(?:\.[0-9]+)?)\s*([KMGT]?i?B)\s*$",
    re.IGNORECASE,
)
_CLAMAV_INFECTED = re.compile(r"(?m)^Infected files:\s*(\d+)\s*$")
_CLAMAV_LIMIT_MARKER = "Heuristics.Limits.Exceeded"
# Die beiden Teilnachweise heissen im Bericht wie in der Summary gleich. Als
# doppelt getippte Literale waere ein Umbenennen genau die Sorte stiller Drift,
# gegen die dieses Repo sonst Waechter stellt: die Summary faende die Spalte
# nicht mehr und zeigte "keine Evidenz" statt der Zahl.
_LABEL_RAW: Final = "Rohdatei"
_LABEL_PAYLOAD: Final = "entpackte Nutzlast"
# ``clamscan --version`` liefert "ClamAV <engine>/<sigs>/<Signaturdatum>".
_CLAMAV_VERSION_DATE = re.compile(r"/(\w{3} \w{3}\s+\d{1,2} \d{2}:\d{2}:\d{2} \d{4})$")
_SIGNATURE_MAX_AGE_DAYS: Final = 14
# Genau die vier Schreibweisen, die ``clamscan`` erzeugt: ``loggBytes`` in
# clamav/clamscan/clamscan.c kennt nur ``GiB``/``MiB``/``KiB``/``B`` und rechnet
# durchgaengig mit 1024. Dezimale Labels (``MB``) gibt es dort nicht – sie hier
# zu akzeptieren hiesse, eine Bytezahl aus einer Einheit zu raten, deren
# Semantik wir nicht kennen. Unbekannte Einheit -> ``None`` (im Bericht als
# "keine Evidenz"), nie eine plausibel aussehende falsche Zahl. Beobachtet im
# Kandidatenlauf 33065289784: "Data scanned: 1.28 GiB".
_BYTE_UNITS: Final[dict[str, int]] = {
    "B": 1, "KIB": 1024, "MIB": 1024**2, "GIB": 1024**3,
}
# Hex statt Klartext: Manche lokale Virenscanner quarantänisieren bereits
# Quellcode, der den EICAR-Teststring wörtlich enthält. Erst im temporären
# Arbeitsverzeichnis wird daraus die standardisierte 68-Byte-Kontrolldatei.
_EICAR_HEX = (
    "58354f2150254041505b345c505a58353428505e2937434329377d24"
    "45494341522d5354414e444152442d414e544956495255532d544553"
    "542d46494c452124482b482a"
)

# ── Bericht und Register (#920) ────────────────────────────────────────

REPORT_SCHEMA: Final = 1
REPORT_KIND: Final = "release-security-scan"
REGISTER_SCHEMA: Final = 1
REGISTER_KIND: Final = "release-build-anomalies"
REGISTER_PATH: Final = "release/build-anomalies.json"

VERDICT_PASS: Final = "PASS"
VERDICT_FAIL: Final = "FAIL"
VERDICT_UNAVAILABLE: Final = "UNAVAILABLE"

# Die Plattformkennungen sind exakt die ``platform_tag``-Werte der
# Kandidatenbau-Matrix, die Phasen exakt die dort erfassten Build-Log-Dateien.
# ``tests/test_scan_release_artifacts.py`` haelt beide Listen gegen
# ``.github/workflows/release-linux.yml`` – ein Tippfehler im Register wuerde
# den Eintrag sonst still wirkungslos machen.
KNOWN_PLATFORMS: Final = ("linux-x86_64", "linux-raspberrypi-arm64", "macos-arm64")
# Welches Leg welche Phasen-Logs schreibt. Ein *unbekannter* Dateiname faellt
# ohnehin auf; der gefaehrlichere Fall ist der umgekehrte: ``build-logs/``
# existiert, das erwartete Log fehlt aber. Ohne diese Erwartung saehe der
# Bericht dann exakt aus wie ein sauberer Lauf (``anomalies_total: 0``,
# Abschnitt 4 "Keine.") – die Durchsicht haette abgehakt, ohne eine Zeile
# gelesen zu haben. Deshalb je Plattform erwartet und ein fehlendes Log
# sichtbar gewarnt.
PHASES_BY_PLATFORM: Final[dict[str, tuple[str, ...]]] = {
    "linux-x86_64": ("smoke-launch-appimage", "deb-install-smoke"),
    "linux-raspberrypi-arm64": ("smoke-launch-appimage", "deb-install-smoke"),
    "macos-arm64": ("smoke-launch-macos-app",),
}
KNOWN_PHASES: Final = tuple(
    sorted({phase for phases in PHASES_BY_PLATFORM.values() for phase in phases})
)
# Ein Fingerprint muss lang genug sein, um genau eine Meldung zu treffen.
# Kurze Fragmente waeren faktisch die breiten Regex-Suppressionen, die #920
# ausdruecklich ausschliesst.
MIN_FINGERPRINT_LENGTH: Final = 24

_TRACEBACK_HEADER = re.compile(r"^Traceback \(most recent call last\):")
_EXCEPTION_LINE = re.compile(r"^[A-Za-z_][\w.]*(?:Error|Exception|Interrupt|Exit)(?::|$)")
_FATAL_LINE = re.compile(
    r"(?i)\b(fatal python error|segmentation fault|abort trap|core dumped|bus error)\b"
)
_ANNOTATION_LINE = re.compile(r"^::(?:error|warning)")


class RegisterError(RuntimeError):
    """Das Anomalie-Register ist unlesbar, unvollstaendig oder zu unscharf."""


@dataclass(frozen=True)
class AnomalyEntry:
    """Ein kuratierter, begruendeter und befristeter Registereintrag."""

    entry_id: str
    fingerprint: str
    platforms: tuple[str, ...]
    phases: tuple[str, ...]
    reason: str
    owner: str
    reference: str
    expires: date
    notes: str

    def expired(self, today: date) -> bool:
        return today > self.expires

    def matches(self, *, platform: str, phase: str, text: str) -> bool:
        """Literaler Teilstring-Treffer – niemals ein regulaerer Ausdruck."""
        return platform in self.platforms and phase in self.phases and self.fingerprint in text


@dataclass(frozen=True)
class AnomalyRegister:
    """Validiertes Register samt Digest der versionierten Quelldatei."""

    schema: int
    version: int
    digest: str
    entries: tuple[AnomalyEntry, ...]


@dataclass(frozen=True)
class LogAnomaly:
    """Eine auffaellige Logzeile einer Bau-Phase (dedupliziert)."""

    phase: str
    line: int
    text: str
    kind: str
    occurrences: int


@dataclass(frozen=True)
class ClamavTargetResult:
    """Ergebnis eines ClamAV-Teilscans (Rohdatei bzw. entpackte Nutzlast)."""

    label: str
    ok: bool
    exit_code: int
    infected: int | None
    data_scanned_bytes: int | None
    limit_warning: bool


@dataclass(frozen=True)
class ArtifactMalwareResult:
    """Beide Teilnachweise eines Artefakts mit ihrem gemeinsamen Verdikt."""

    ok: bool
    detail: str
    targets: tuple[ClamavTargetResult, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": VERDICT_PASS if self.ok else VERDICT_FAIL,
            "detail": self.detail,
            "targets": [
                {
                    "label": target.label,
                    "ok": target.ok,
                    "exit_code": target.exit_code,
                    "infected": target.infected,
                    "data_scanned_bytes": target.data_scanned_bytes,
                    "limit_warning": target.limit_warning,
                }
                for target in self.targets
            ],
        }


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


def _run(cmd: list[str], *, cwd: Path | None = None) -> None:
    subprocess.run(cmd, check=True, capture_output=True, cwd=cwd)


def _run_clamav(database: Path, targets: list[Path]) -> subprocess.CompletedProcess[str]:
    """Startet ClamAV mit dem für Release-Artefakte fail-closed Vertrag."""
    command = [
        "clamscan",
        "--database", str(database),
        "--recursive",
        "--infected",
        "--stdout",
        *_CLAMAV_LIMIT_OPTIONS,
        *(str(target) for target in targets),
    ]
    return subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def _print_clamav_output(result: subprocess.CompletedProcess[str]) -> None:
    output = result.stdout or ""
    if output:
        print(output.rstrip())


def parse_scanned_bytes(output: str) -> int | None:
    """Liest ``Data scanned: 1.28 GiB`` als ganzzahlige Bytezahl.

    Der Runbook-Schritt 4 verlangt "mehr als 0 gescannte Bytes je Artefakt und
    Teilnachweis" – als Zahl im Bericht ist das pruefbar, als Freitextzeile im
    Joblog nur lesbar.
    """
    match = _CLAMAV_DATA_SCANNED.search(output)
    if match is None:
        return None
    factor = _BYTE_UNITS.get(match.group(2).upper())
    if factor is None:
        return None
    return int(float(match.group(1)) * factor)


def _positive_scanned_bytes(output: str) -> bool:
    match = _CLAMAV_DATA_SCANNED.search(output)
    return match is not None and float(match.group(1)) > 0


def clamav_scan_succeeded(result: subprocess.CompletedProcess[str]) -> bool:
    """Nur echte, limitfreie Scans ohne Fund als Erfolg akzeptieren.

    Insbesondere ist die historische #731-Ausgabe ``Data scanned: 0 B`` bei
    Exit 0 ein Fehler: ``Data read`` belegt nur Dateizugriff, nicht dass die
    Engine den Inhalt tatsächlich gegen Signaturen geprüft hat.
    """
    output = result.stdout or ""
    infected = _CLAMAV_INFECTED.search(output)
    return (
        result.returncode == 0
        and infected is not None
        and int(infected.group(1)) == 0
        and _positive_scanned_bytes(output)
        and _CLAMAV_LIMIT_MARKER not in output
    )


def verify_clamav_eicar(database: Path, workdir: Path) -> bool:
    """Beweist vor dem Artefaktscan, dass Engine und Signaturen aktiv sind."""
    control = workdir / "eicar-clamav-control.com"
    control.write_bytes(bytes.fromhex(_EICAR_HEX))
    try:
        result = _run_clamav(database, [control])
    finally:
        control.unlink(missing_ok=True)
    _print_clamav_output(result)
    output = result.stdout or ""
    infected = _CLAMAV_INFECTED.search(output)
    return (
        result.returncode == 1
        and infected is not None
        and int(infected.group(1)) >= 1
        and _positive_scanned_bytes(output)
        and re.search(r"(?i)eicar.*FOUND", output) is not None
    )


def clamav_signature_state(
    database: Path, *, now: datetime | None = None
) -> dict[str, Any]:
    """Liest Engine-/Signaturzeile und leitet das Alter der Datenbank ab.

    Frueher stand diese Auswertung als eingebettetes Python-Heredoc im
    Workflow (#731). Hier ist sie testbar, und ihr Ergebnis landet im Bericht
    statt nur im Joblog. Ist die Zeile nicht auswertbar, bleibt ``age_days``
    ``None`` – das ist ein Hinweis, kein harter Befund.
    """
    state: dict[str, Any] = {
        "path": str(database),
        "version_line": None,
        "signature_date": None,
        "age_days": None,
        "stale": False,
        "max_age_days": _SIGNATURE_MAX_AGE_DAYS,
    }
    try:
        completed = subprocess.run(
            ["clamscan", "--database", str(database), "--version"],
            check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
    except OSError as exc:  # clamscan fehlt – der Aufrufer meldet das separat
        state["version_line"] = f"nicht ermittelbar: {exc}"
        return state
    line = (completed.stdout or "").strip().splitlines()
    state["version_line"] = line[0] if line else ""
    match = _CLAMAV_VERSION_DATE.search(state["version_line"] or "")
    if match is None:
        return state
    text = re.sub(r"\s+", " ", match.group(1))
    try:
        signature_date = datetime.strptime(text, "%a %b %d %H:%M:%S %Y").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return state
    reference = now or datetime.now(timezone.utc)
    age_days = (reference - signature_date).days
    state["signature_date"] = signature_date.isoformat()
    state["age_days"] = age_days
    state["stale"] = age_days > _SIGNATURE_MAX_AGE_DAYS
    return state


def scan_artifact_with_clamav(
    artifact: Path, extracted: Path, database: Path
) -> ArtifactMalwareResult:
    """Scannt Rohartefakt und Nutzdaten mit je eigener Nichtnull-Evidenz."""
    payload_files = [
        member for member in extracted.rglob("*")
        if member.is_file() and not member.is_symlink()
    ]
    if not payload_files:
        detail = f"{artifact.name}: entpackte Nutzlast ist leer."
        print(f"::error::{detail}")
        return ArtifactMalwareResult(ok=False, detail=detail, targets=())

    print(f">> ClamAV: {artifact.name} (Rohdatei + entpackter Inhalt, getrennt)")
    targets: list[ClamavTargetResult] = []
    for label, target in ((_LABEL_RAW, artifact), (_LABEL_PAYLOAD, extracted)):
        print(f"   Teilnachweis: {label}")
        result = _run_clamav(database, [target])
        _print_clamav_output(result)
        output = result.stdout or ""
        infected = _CLAMAV_INFECTED.search(output)
        ok = clamav_scan_succeeded(result)
        targets.append(ClamavTargetResult(
            label=label,
            ok=ok,
            exit_code=result.returncode,
            infected=int(infected.group(1)) if infected is not None else None,
            data_scanned_bytes=parse_scanned_bytes(output),
            limit_warning=_CLAMAV_LIMIT_MARKER in output,
        ))
        if not ok:
            detail = (
                f"{artifact.name} ({label}): ClamAV-Nachweis ungültig – "
                "Fund, Fehler, Limitüberschreitung oder 0 gescannte Bytes."
            )
            print(f"::error::{detail}")
            return ArtifactMalwareResult(ok=False, detail=detail, targets=tuple(targets))
    print(f"   OK: ClamAV hat {artifact.name} und seine Nutzdaten getrennt gescannt")
    return ArtifactMalwareResult(
        ok=True,
        detail="Rohdatei und entpackte Nutzlast getrennt und ohne Fund gescannt.",
        targets=tuple(targets),
    )


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


@dataclass(frozen=True)
class ArtifactScan:
    """Ergebnis des deterministischen Secret-/Pfad-Scans eines Artefakts."""

    findings: tuple[str, ...]
    blocking_users: frozenset[str]
    informational_users: frozenset[str]
    raw_bytes: int
    payload_bytes: int
    payload_files: int


def scan_artifact(path: Path, workdir: Path) -> ArtifactScan:
    """Scannt *path* selbst (Container-Ebene) und seinen entpackten Inhalt.

    Liefert Funde, blockierende und informative Pfad-Benutzer sowie die
    getrennt gezaehlten Bytes von Rohdatei und entpackter Nutzlast (#920).
    Blockierend ist nur ein unbekannter Pfad-Benutzer innerhalb des eigenen
    ``bgremover``-Pakets; derselbe Fund in einer Drittanbieter-Abhängigkeit
    oder in den rohen Container-Bytes (keine Paketzuordnung möglich) ist
    lediglich informativ – s. Modul-Docstring."""
    raw = path.read_bytes()
    findings = scan_bytes(raw)
    informational_users = dev_path_users(raw)
    blocking_users: set[str] = set()
    payload_bytes = 0
    payload_files = 0

    extract_dir = workdir / f"{path.name}.extracted"
    extract_payload(path, extract_dir)
    for member in extract_dir.rglob("*"):
        if member.is_file() and not member.is_symlink():
            data = member.read_bytes()
            payload_bytes += len(data)
            payload_files += 1
            findings.extend(scan_bytes(data))
            users = dev_path_users(data)
            if not users:
                continue
            if _is_own_package_path(member.relative_to(extract_dir)):
                blocking_users |= users
            else:
                informational_users |= users
    return ArtifactScan(
        findings=tuple(findings),
        blocking_users=frozenset(blocking_users),
        informational_users=frozenset(informational_users),
        raw_bytes=len(raw),
        payload_bytes=payload_bytes,
        payload_files=payload_files,
    )


# ── Anomalie-Register (#920) ───────────────────────────────────────────


def _require_text(data: dict[str, Any], key: str, entry_id: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RegisterError(f"Eintrag {entry_id!r}: {key} fehlt oder ist leer")
    return value


def _require_choices(
    data: dict[str, Any], key: str, entry_id: str, allowed: tuple[str, ...]
) -> tuple[str, ...]:
    value = data.get(key)
    if not isinstance(value, list) or not value:
        raise RegisterError(f"Eintrag {entry_id!r}: {key} muss eine nichtleere Liste sein")
    unknown = [item for item in value if item not in allowed]
    if unknown:
        raise RegisterError(
            f"Eintrag {entry_id!r}: unbekannte {key} {unknown!r}; erlaubt sind {list(allowed)}"
        )
    return tuple(str(item) for item in value)


def parse_register(text: str) -> AnomalyRegister:
    """Liest und validiert das Register aus seinem versionierten JSON-Text.

    Fail-closed: unbekanntes Schema, fehlende Pflichtfelder, doppelte IDs,
    unbekannte Plattform/Phase, ein zu kurzer Fingerprint oder ein
    unlesbares Ablaufdatum sind Fehler. Ein Register, das nicht geladen werden
    kann, darf nicht stillschweigend als "keine bekannten Anomalien" gelten.
    """
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RegisterError(f"Register ist kein gueltiges JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise RegisterError("Register ist kein Objekt")
    if raw.get("schema") != REGISTER_SCHEMA:
        raise RegisterError(f"unbekanntes Register-Schema: {raw.get('schema')!r}")
    if raw.get("kind") != REGISTER_KIND:
        raise RegisterError(f"unerwartete Register-Art: {raw.get('kind')!r}")
    version = raw.get("register_version")
    if not isinstance(version, int) or version < 1:
        raise RegisterError("register_version muss eine positive Ganzzahl sein")
    raw_entries = raw.get("entries")
    if not isinstance(raw_entries, list):
        raise RegisterError("entries muss eine Liste sein")

    entries: list[AnomalyEntry] = []
    seen_ids: set[str] = set()
    for item in raw_entries:
        if not isinstance(item, dict):
            raise RegisterError("Registereintrag ist kein Objekt")
        entry_id = _require_text(item, "id", "<ohne id>")
        if entry_id in seen_ids:
            raise RegisterError(f"doppelte Eintrags-ID: {entry_id!r}")
        seen_ids.add(entry_id)
        fingerprint = _require_text(item, "fingerprint", entry_id)
        if len(fingerprint) < MIN_FINGERPRINT_LENGTH:
            raise RegisterError(
                f"Eintrag {entry_id!r}: Fingerprint ist mit {len(fingerprint)} Zeichen zu kurz "
                f"(mindestens {MIN_FINGERPRINT_LENGTH}) – breite Muster sind ausgeschlossen"
            )
        reference = _require_text(item, "reference", entry_id)
        if not reference.startswith("https://github.com/NikolayDA/picture_helper/issues/"):
            raise RegisterError(
                f"Eintrag {entry_id!r}: reference muss auf ein Issue dieses Repositories zeigen"
            )
        expires_text = _require_text(item, "expires", entry_id)
        try:
            expires = date.fromisoformat(expires_text)
        except ValueError as exc:
            raise RegisterError(
                f"Eintrag {entry_id!r}: expires ist kein ISO-Datum ({expires_text!r})"
            ) from exc
        notes = item.get("notes", "")
        if not isinstance(notes, str):
            raise RegisterError(f"Eintrag {entry_id!r}: notes muss Text sein")
        entries.append(AnomalyEntry(
            entry_id=entry_id,
            fingerprint=fingerprint,
            platforms=_require_choices(item, "platforms", entry_id, KNOWN_PLATFORMS),
            phases=_require_choices(item, "phases", entry_id, KNOWN_PHASES),
            reason=_require_text(item, "reason", entry_id),
            owner=_require_text(item, "owner", entry_id),
            reference=reference,
            expires=expires,
            notes=notes,
        ))
    return AnomalyRegister(
        schema=REGISTER_SCHEMA,
        version=version,
        digest=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        entries=tuple(entries),
    )


def load_register(path: Path) -> AnomalyRegister:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RegisterError(f"Register {path} ist nicht lesbar: {exc}") from exc
    return parse_register(text)


def detect_log_anomalies(text: str, *, phase: str) -> list[LogAnomaly]:
    """Findet auffaellige Zeilen einer Bau-Phase, dedupliziert nach Wortlaut.

    Ein Python-Traceback wird ueber seine **Ausnahmezeile** gemeldet, nicht
    ueber die Kopfzeile: nur die Ausnahmezeile traegt die Meldung, an der ein
    Registereintrag ueberhaupt ansetzen kann. Bleibt ein Traceback ohne
    Ausnahmezeile (abgeschnittenes Log), wird die Kopfzeile selbst gemeldet –
    ein abgebrochener Traceback ist die verdaechtigere Variante.
    """
    found: dict[str, LogAnomaly] = {}
    pending_traceback: int | None = None

    def record(line_no: int, content: str, kind: str) -> None:
        existing = found.get(content)
        if existing is None:
            found[content] = LogAnomaly(
                phase=phase, line=line_no, text=content, kind=kind, occurrences=1,
            )
        else:
            found[content] = LogAnomaly(
                phase=existing.phase, line=existing.line, text=existing.text,
                kind=existing.kind, occurrences=existing.occurrences + 1,
            )

    for number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        if _TRACEBACK_HEADER.match(line):
            if pending_traceback is not None:
                record(pending_traceback, "Traceback (most recent call last):", "traceback")
            pending_traceback = number
            continue
        if _EXCEPTION_LINE.match(line):
            record(number, line, "traceback" if pending_traceback is not None else "exception")
            pending_traceback = None
            continue
        if _ANNOTATION_LINE.match(line):
            record(number, line, "annotation")
            continue
        if _FATAL_LINE.search(line):
            record(number, line, "fatal")
    if pending_traceback is not None:
        record(pending_traceback, "Traceback (most recent call last):", "traceback")
    return sorted(found.values(), key=lambda anomaly: (anomaly.phase, anomaly.line))


def read_build_logs(directory: Path) -> list[tuple[str, str]]:
    """Liest ``<phase>.log`` aus *directory*, sortiert nach Phasenname."""
    if not directory.is_dir():
        return []
    logs: list[tuple[str, str]] = []
    for path in sorted(directory.glob("*.log")):
        logs.append((path.stem, path.read_text(encoding="utf-8", errors="replace")))
    return logs


def classify_anomalies(
    anomalies: list[LogAnomaly],
    register: AnomalyRegister | None,
    *,
    platform: str,
    today: date,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Teilt Anomalien in ``(bekannt annotiert, unbekannt)``.

    Beruehrt ausschliesslich Log-Auffaelligkeiten. Scanner-Befunde werden hier
    nie uebergeben und koennen daher auch nicht annotiert oder unterdrueckt
    werden – das ist die tragende Invariante aus #920.
    """
    known: list[dict[str, Any]] = []
    unknown: list[dict[str, Any]] = []
    active = [
        entry for entry in (register.entries if register is not None else ())
        if not entry.expired(today)
    ]
    for anomaly in anomalies:
        base: dict[str, Any] = {
            "phase": anomaly.phase,
            "line": anomaly.line,
            "kind": anomaly.kind,
            "occurrences": anomaly.occurrences,
            "text": anomaly.text,
        }
        entry = next(
            (
                candidate for candidate in active
                if candidate.matches(platform=platform, phase=anomaly.phase, text=anomaly.text)
            ),
            None,
        )
        if entry is None:
            unknown.append(base)
            continue
        known.append({
            **base,
            "entry_id": entry.entry_id,
            "reason": entry.reason,
            "owner": entry.owner,
            "reference": entry.reference,
            "expires": entry.expires.isoformat(),
        })
    return known, unknown


def expired_entries(register: AnomalyRegister, *, today: date) -> list[AnomalyEntry]:
    return [entry for entry in register.entries if entry.expired(today)]


def overall_verdict(hard_findings: list[str], unavailable: list[str]) -> str:
    """Leitet das Gesamtverdikt ausschliesslich aus Befunden und Luecken ab.

    Das Anomalie-Register geht hier bewusst **nicht** ein: es annotiert
    Log-Muster fuer die menschliche Durchsicht und darf nie ein Verdikt
    verschieben (#920, Nicht-Ziele).
    """
    if hard_findings:
        return VERDICT_FAIL
    if unavailable:
        return VERDICT_UNAVAILABLE
    return VERDICT_PASS


# ── Bericht und Job-Summary (#920) ─────────────────────────────────────


def render_summary(report: dict[str, Any]) -> str:
    """Rendert die viergliedrige Job-Summary aus dem Bericht."""
    lines: list[str] = []
    verdict = report["verdict"]
    icon = {"PASS": "✅", "FAIL": "❌", "UNAVAILABLE": "⚠️"}.get(verdict, "•")
    platform = report.get("platform") or "unbekannt"
    lines.append(f"## {icon} Artefakt-Sicherheitsscan — {platform}")
    lines.append("")
    counts = report["counts"]
    lines.append("| Feld | Wert |")
    lines.append("| --- | --- |")
    lines.append(f"| Gesamtverdikt | **{verdict}** |")
    lines.append(f"| Artefakte | {len(report['artifacts'])} |")
    lines.append(f"| Secret-Funde | {counts['secrets']} |")
    lines.append(f"| Entwicklerpfade (blockierend) | {counts['dev_paths_blocking']} |")
    lines.append(f"| Entwicklerpfade (informativ) | {counts['dev_paths_informational']} |")
    lines.append(f"| Malware-Funde | {counts['malware_infected']} |")
    lines.append(
        f"| Artefakte ohne gültigen Malware-Nachweis | {counts['malware_failed_artifacts']} |"
    )
    lines.append(f"| Limitwarnungen | {len(report['limit_warnings'])} |")
    lines.append(f"| EICAR-Selbsttest | {report['eicar_selftest']['status']} |")
    lines.append(f"| Malware-Scan | {report['malware_scan']['status']} |")
    signature = report["signature_database"]
    age = signature.get("age_days")
    age_text = "nicht auslesbar" if age is None else f"{age} Tage"
    if signature.get("stale"):
        age_text += f" ⚠️ älter als {signature['max_age_days']} Tage"
    lines.append(f"| Signaturdatenbank | {age_text} |")
    lines.append("")

    # Hinweise (veraltete Signaturen, unbekannte Log-Phasen, abgelaufene
    # Registereintraege) stehen sichtbar oben statt nur im JSON – sie sind
    # weder harte Befunde noch UNAVAILABLE-Zustaende, duerfen aber nicht
    # untergehen.
    if report["warnings"]:
        lines.append("**Hinweise:**")
        lines.append("")
        lines.extend(f"- ⚠️ {item}" for item in report["warnings"])
        lines.append("")

    # Runbook-Schritt 4 verlangt je Artefakt getrennte, nichtleere Bytezahlen
    # fuer Rohdatei und entpackte Nutzlast – hier als Tabelle statt als
    # verstreute "Data scanned"-Zeilen im Joblog.
    lines.append("| Artefakt | Rohdatei (Byte) | Nutzlast (Byte) | Dateien | ClamAV roh | "
                 "ClamAV Nutzlast |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
    for artifact in report["artifacts"]:
        scanned = {
            target["label"]: target["data_scanned_bytes"]
            for target in artifact.get("malware", {}).get("targets", [])
        }
        lines.append(
            f"| {artifact['name']} | {artifact.get('raw_bytes', 0)} "
            f"| {artifact.get('payload_bytes', 0)} | {artifact.get('payload_files', 0)} "
            f"| {_scanned(scanned.get(_LABEL_RAW))} "
            f"| {_scanned(scanned.get(_LABEL_PAYLOAD))} |"
        )
    lines.append("")

    lines.append("### 1. Harte Befunde")
    lines.append("")
    if report["hard_findings"]:
        lines.extend(f"- ❌ {item}" for item in report["hard_findings"])
    else:
        lines.append("Keine. Secret-, Entwicklerpfad- und Malware-Prüfung ohne Befund.")
    lines.append("")

    lines.append("### 2. `UNAVAILABLE`-Zustände")
    lines.append("")
    if report["unavailable"]:
        lines.extend(f"- ⚠️ {item}" for item in report["unavailable"])
    else:
        lines.append("Keine. Alle vorgesehenen Prüfungen konnten laufen.")
    lines.append("")

    anomalies = report["anomalies"]
    lines.append("### 3. Als bekannt annotierte Anomalien")
    lines.append("")
    if anomalies["known"]:
        lines.append("| Phase | Meldung | Registereintrag | Owner | Referenz | Läuft ab |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for item in anomalies["known"]:
            lines.append(
                f"| {item['phase']} | `{_cell(item['text'])}` | {item['entry_id']} "
                f"| {item['owner']} | {item['reference']} | {item['expires']} |"
            )
        lines.append("")
        lines.append(
            "Annotiert heißt **gesehen und begründet**, nicht unterdrückt: die Meldungen "
            "stehen unverändert im Joblog und beeinflussen das Verdikt nicht."
        )
    else:
        lines.append("Keine bekannten Anomalien in den erfassten Bau-Phasen.")
    lines.append("")

    lines.append("### 4. Unbekannte Auffälligkeiten")
    lines.append("")
    if anomalies["unknown"]:
        lines.append("| Phase | Zeile | Meldung | Vorkommen |")
        lines.append("| --- | --- | --- | --- |")
        for item in anomalies["unknown"]:
            lines.append(
                f"| {item['phase']} | {item['line']} | `{_cell(item['text'])}` "
                f"| {item['occurrences']} |"
            )
        lines.append("")
        lines.append(
            "Diese Meldungen sind **nicht** als bekannt eingestuft und gehören in die "
            "Durchsicht des Security-Owners."
        )
    else:
        lines.append("Keine.")
    lines.append("")

    register = report["register"]
    lines.append("### Register bekannter Build-Anomalien")
    lines.append("")
    if register.get("path") is None:
        lines.append("Kein Register übergeben – jede Auffälligkeit gilt als unbekannt.")
    else:
        lines.append(
            f"`{register['path']}` — Version {register['version']}, "
            f"Einträge: {register['entries']}, Digest `{register['digest'][:12]}`"
        )
        if register["expired"]:
            lines.append("")
            lines.append("Abgelaufene Einträge — sie annotieren nicht mehr:")
            lines.extend(
                f"- ⚠️ `{item['id']}` (abgelaufen am {item['expires']}, Owner {item['owner']}, "
                f"{item['reference']})"
                for item in register["expired"]
            )
    lines.append("")
    return "\n".join(lines)


def _scanned(value: int | None) -> str:
    """Zeigt fehlende ClamAV-Evidenz als solche, nie als Null."""
    return "–" if value is None else str(value)


def _cell(text: str) -> str:
    """Macht eine Logzeile für eine Markdown-Tabellenzelle unschädlich."""
    return text.replace("|", "\\|").replace("`", "'")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--clamav-database",
        type=Path,
        help="optionaler Signaturdatenbank-Pfad für den fail-closed Malware-Scan",
    )
    parser.add_argument(
        "--malware-unavailable",
        metavar="GRUND",
        help="Malware-Scan konnte nicht laufen; Grund wird sichtbar als UNAVAILABLE gefuehrt",
    )
    parser.add_argument("--report", type=Path, help="Zielpfad fuer security-scan-report.json")
    parser.add_argument("--summary", type=Path, help="Zielpfad fuer die Markdown-Job-Summary")
    parser.add_argument(
        "--anomaly-register", type=Path, help=f"Register bekannter Build-Anomalien ({REGISTER_PATH})"
    )
    parser.add_argument(
        "--build-log-dir", type=Path, help="Verzeichnis mit <phase>.log der Bau-Phasen"
    )
    parser.add_argument(
        "--platform", choices=KNOWN_PLATFORMS, help="platform_tag des Kandidatenbau-Legs"
    )
    parser.add_argument(
        "--logs-only",
        action="store_true",
        help=(
            "nur die Phasen-Logs auswerten, keine Artefakte scannen – fuer den "
            "Nachtrag, wenn ein frueherer Schritt des Laufs gefallen ist"
        ),
    )
    parser.add_argument("directory", nargs="?", default="dist", help="zu scannendes Verzeichnis")
    args = parser.parse_args(argv)
    if args.anomaly_register is not None and args.platform is None:
        parser.error("--anomaly-register verlangt --platform (sonst greift kein Eintrag)")
    if args.clamav_database is not None and args.malware_unavailable is not None:
        parser.error("--clamav-database und --malware-unavailable schliessen einander aus")
    if args.logs_only and args.clamav_database is not None:
        parser.error("--logs-only scannt keine Artefakte und damit auch nicht mit ClamAV")
    return args


def _collect_anomalies(
    args: argparse.Namespace,
    register: AnomalyRegister | None,
    warnings: list[str],
    today: date,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Liest die Build-Logs und teilt ihre Auffaelligkeiten in bekannt/unbekannt."""
    build_logs: list[dict[str, Any]] = []
    anomalies: list[LogAnomaly] = []
    seen_phases: set[str] = set()
    if args.build_log_dir is not None:
        if not args.build_log_dir.is_dir():
            warnings.append(
                f"Kein Build-Log-Verzeichnis unter {args.build_log_dir} – "
                "Anomalie-Durchsicht ohne Datengrundlage."
            )
        for phase, text in read_build_logs(args.build_log_dir):
            if phase not in KNOWN_PHASES:
                warnings.append(
                    f"Unbekannte Build-Log-Phase {phase!r}; kein Registereintrag kann greifen."
                )
            seen_phases.add(phase)
            found = detect_log_anomalies(text, phase=phase)
            anomalies.extend(found)
            build_logs.append({
                "phase": phase,
                "lines": len(text.splitlines()),
                "anomalies": len(found),
            })
        # Fail-open-Richtung schliessen: ein fehlendes erwartetes Log ist von
        # einem sauberen Lauf sonst nicht unterscheidbar (s. PHASES_BY_PLATFORM).
        for phase in PHASES_BY_PLATFORM.get(args.platform or "", ()):
            if phase not in seen_phases:
                warnings.append(
                    f"Erwartetes Phasen-Log {phase!r} fehlt fuer Plattform "
                    f"{args.platform!r} – dieser Bau-Schritt ist ungeprueft, "
                    "nicht unauffaellig."
                )
    known, unknown = classify_anomalies(
        anomalies, register, platform=args.platform or "", today=today,
    )
    expected = list(PHASES_BY_PLATFORM.get(args.platform or "", ()))
    return (
        {
            "files": build_logs,
            "anomalies_total": len(anomalies),
            "expected_phases": expected,
            "missing_phases": sorted(set(expected) - seen_phases),
        },
        {"known": known, "unknown": unknown},
    )


def _register_section(
    args: argparse.Namespace, register: AnomalyRegister | None, today: date
) -> tuple[dict[str, Any], list[str]]:
    """Baut den Registerabschnitt des Berichts und die Ablaufwarnungen."""
    if register is None:
        return (
            {"path": None, "version": None, "digest": None, "entries": 0, "expired": []},
            [],
        )
    stale = expired_entries(register, today=today)
    warnings = [
        f"Registereintrag {entry.entry_id!r} ist am {entry.expires.isoformat()} abgelaufen "
        f"und annotiert nicht mehr – Owner {entry.owner}, {entry.reference}."
        for entry in stale
    ]
    return (
        {
            "path": str(args.anomaly_register),
            "version": register.version,
            "digest": register.digest,
            "entries": len(register.entries),
            "expired": [
                {
                    "id": entry.entry_id,
                    "expires": entry.expires.isoformat(),
                    "owner": entry.owner,
                    "reference": entry.reference,
                }
                for entry in stale
            ],
        },
        warnings,
    )


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    today = datetime.now(timezone.utc).date()

    register: AnomalyRegister | None = None
    if args.anomaly_register is not None:
        try:
            register = load_register(args.anomaly_register)
        except RegisterError as exc:
            # Fail-closed: ein unlesbares Register darf nicht als "keine
            # bekannten Anomalien" durchgehen. Es wird von ``make check``
            # mitvalidiert, ein Fehler hier ist also ein umgangener Test.
            print(f"::error::Anomalie-Register ungueltig – {exc}")
            return 1

    directory = Path(args.directory)
    files: list[Path] = []
    if not args.logs_only:
        files = sorted(p for p in directory.iterdir() if p.is_file())
        if not files:
            # Ein gruener Build ohne Artefakt ist ein harter Fehler und bleibt
            # es. Genau deshalb laeuft der Artefaktscan-Schritt im Workflow nur
            # bei Erfolg – der Nachtrag im Fehlerfall nutzt --logs-only.
            print(f"::error::Keine Dateien in {directory} gefunden.")
            return 1

    database: Path | None = args.clamav_database
    if database is not None and (
        not database.is_dir() or not any(database.iterdir())
    ):
        print(f"::error::ClamAV-Signaturdatenbank fehlt oder ist leer: {database}")
        return 1

    hard_findings: list[str] = []
    unavailable: list[str] = []
    warnings: list[str] = []
    artifacts: list[dict[str, Any]] = []
    limit_warnings: list[str] = []
    counts = {
        "secrets": 0,
        "dev_paths_blocking": 0,
        "dev_paths_informational": 0,
        "malware_infected": 0,
        "malware_failed_artifacts": 0,
        "scan_errors": 0,
    }
    signature: dict[str, Any] = {
        "path": None, "version_line": None, "signature_date": None,
        "age_days": None, "stale": False, "max_age_days": _SIGNATURE_MAX_AGE_DAYS,
    }
    unavailable_reason = args.malware_unavailable or "kein --clamav-database uebergeben"
    if args.logs_only:
        unavailable_reason = "nur Phasen-Logs ausgewertet (--logs-only)"
    eicar: dict[str, Any] = {"status": VERDICT_UNAVAILABLE, "detail": unavailable_reason}
    malware_scan: dict[str, Any] = {
        "status": VERDICT_UNAVAILABLE,
        "reason": unavailable_reason,
    }
    if args.logs_only:
        detail = (
            "Artefaktscan nicht gelaufen: --logs-only wertet ausschliesslich die "
            "Phasen-Logs aus, weil ein frueherer Schritt des Laufs gefallen ist."
        )
        unavailable.append(detail)
        print(f"::warning::{detail}")
    if database is None:
        unavailable.append(f"Malware-Scan: {malware_scan['reason']}")
        print(f"::warning::Malware-Scan UNAVAILABLE – {malware_scan['reason']}")

    with tempfile.TemporaryDirectory(prefix="scan-release-artifacts-") as tmp:
        workdir = Path(tmp)
        clamav_ready = database is not None
        if database is not None:
            signature = clamav_signature_state(database)
            print(f"Engine/Signatur: {signature['version_line']}")
            if signature["age_days"] is None:
                print("Signaturdatum nicht auslesbar - Frische-Check übersprungen")
            else:
                print(f"Signaturalter: {signature['age_days']} Tage")
            if signature["stale"]:
                stale_text = (
                    f"ClamAV-Signaturdatenbank ist {signature['age_days']} Tage alt "
                    f"(> {_SIGNATURE_MAX_AGE_DAYS}) - clamav-db-refresh.yml pruefen."
                )
                warnings.append(stale_text)
                print(f"::warning::{stale_text}")

            print(">> ClamAV-EICAR-Selbsttest: Engine und Signaturdatenbank prüfen")
            clamav_ready = verify_clamav_eicar(database, workdir)
            if clamav_ready:
                eicar = {"status": VERDICT_PASS, "detail": "EICAR-Kontrollstring erkannt"}
                malware_scan = {"status": VERDICT_PASS, "reason": ""}
            else:
                eicar = {"status": VERDICT_FAIL, "detail": "EICAR-Kontrollstring nicht erkannt"}
                malware_scan = {"status": VERDICT_FAIL, "reason": "EICAR-Selbsttest fehlgeschlagen"}
                detail = (
                    "ClamAV-EICAR-Selbsttest fehlgeschlagen – "
                    "Artefakte dürfen nicht als malwaregeprüft gelten."
                )
                print(f"::error::{detail}")
                hard_findings.append(detail)

        for path in files:
            size_mb = path.stat().st_size / 1_000_000
            print(f">> Scanne {path.name} ({size_mb:.1f} MB, inkl. entpacktem Inhalt)")
            entry: dict[str, Any] = {"name": path.name, "raw_bytes": path.stat().st_size}
            try:
                scan = scan_artifact(path, workdir)
            except (subprocess.CalledProcessError, ValueError) as exc:
                detail = f"{path.name}: Entpacken zum Scannen fehlgeschlagen – {exc}"
                print(f"::error::{detail}")
                hard_findings.append(detail)
                counts["scan_errors"] += 1
                entry["error"] = str(exc)
                if clamav_ready:
                    # Ohne entpackte Nutzlast gibt es fuer dieses Artefakt
                    # keinen der beiden geforderten ClamAV-Teilnachweise. Ein
                    # danach unveraendertes ``malware_scan: PASS`` wuerde im
                    # Bericht das Gegenteil behaupten.
                    missing = f"{path.name}: kein ClamAV-Nachweis (Artefakt nicht entpackbar)."
                    entry["malware"] = {"status": VERDICT_FAIL, "detail": missing, "targets": []}
                    counts["malware_failed_artifacts"] += 1
                    malware_scan = {"status": VERDICT_FAIL, "reason": missing}
                artifacts.append(entry)
                continue
            entry.update({
                "raw_bytes": scan.raw_bytes,
                "payload_bytes": scan.payload_bytes,
                "payload_files": scan.payload_files,
                "secret_findings": list(scan.findings),
                "blocking_path_users": sorted(scan.blocking_users),
                "informational_path_users": sorted(scan.informational_users),
            })
            extract_dir = workdir / f"{path.name}.extracted"
            if clamav_ready and database is not None:
                malware = scan_artifact_with_clamav(path, extract_dir, database)
                entry["malware"] = malware.as_dict()
                for target in malware.targets:
                    counts["malware_infected"] += target.infected or 0
                    if target.limit_warning:
                        limit_warnings.append(
                            f"{path.name} ({target.label}): {_CLAMAV_LIMIT_MARKER}"
                        )
                if not malware.ok:
                    hard_findings.append(malware.detail)
                    counts["malware_failed_artifacts"] += 1
                    malware_scan = {"status": VERDICT_FAIL, "reason": malware.detail}
            for finding in scan.findings:
                print(f"::error::{path.name}: möglicher Fund – {finding}")
                hard_findings.append(f"{path.name}: möglicher Fund – {finding}")
                counts["secrets"] += 1
            if scan.blocking_users:
                detail = (
                    f"{path.name}: unbekannte Pfad-Benutzer im eigenen bgremover-Paket "
                    f"außerhalb der Allowlist {sorted(_ALLOWED_PATH_USERS)}: "
                    f"{sorted(scan.blocking_users)}"
                )
                print(f"::error::{detail}")
                hard_findings.append(detail)
                counts["dev_paths_blocking"] += len(scan.blocking_users)
            else:
                print("   OK: keine Entwicklerpfade außerhalb der Allowlist im eigenen Paket gefunden")
            if scan.informational_users:
                counts["dev_paths_informational"] += len(scan.informational_users)
                print(
                    f"   Hinweis (nicht blockierend): unbekannte Pfad-Benutzer in "
                    f"Drittanbieter-Inhalten außerhalb der Allowlist "
                    f"{sorted(_ALLOWED_PATH_USERS)}: {sorted(scan.informational_users)}"
                )
            artifacts.append(entry)

    build_logs, anomalies = _collect_anomalies(args, register, warnings, today)
    register_section, register_warnings = _register_section(args, register, today)
    for text in register_warnings:
        print(f"::warning::{text}")
    warnings.extend(register_warnings)

    report: dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "kind": REPORT_KIND,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "platform": args.platform,
        "directory": str(directory),
        "verdict": overall_verdict(hard_findings, unavailable),
        "counts": counts,
        "eicar_selftest": eicar,
        "signature_database": signature,
        "malware_scan": malware_scan,
        "limit_warnings": limit_warnings,
        "artifacts": artifacts,
        "build_logs": build_logs,
        "anomalies": anomalies,
        "register": register_section,
        "hard_findings": hard_findings,
        "unavailable": unavailable,
        "warnings": warnings,
    }
    if args.report is not None:
        write_json(args.report, report)
        print(f">> Sicherheitsbericht geschrieben: {args.report}")
    if args.summary is not None:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(render_summary(report), encoding="utf-8")
        print(f">> Job-Summary geschrieben: {args.summary}")

    if hard_findings:
        print("::error::Artefakt-Sicherheits-Scan fehlgeschlagen – siehe obige Funde.")
        return 1
    if args.logs_only:
        # Kein "keine Funde in allen Artefakten": in diesem Modus wurde kein
        # einziges Artefakt geprueft. Ein Erfolgssatz darueber waere schlicht
        # unwahr und genau die Art Aussage, die #920 abschaffen will.
        print(">> Nur Phasen-Logs ausgewertet – kein Artefaktscan in diesem Lauf.")
        return 0
    print(
        ">> Secret-/Pfad-Scan (#584): keine hochkonfidenten Funde in allen "
        "Artefakten (inkl. entpacktem Inhalt)."
    )
    if database is not None:
        print(
            ">> Malware-Scan (#731): EICAR-Kontrolle und ClamAV-Scan jedes "
            "Artefakts samt entpackter Nutzdaten bestanden."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
