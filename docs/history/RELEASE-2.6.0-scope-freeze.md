# Release 2.6.0 – Scope-Freeze & Freigabenotiz

Teil von #580, Umsetzung von #583. Dokumentiert den fixierten Umfang des
Release-Kandidaten v2.6.0, damit Build, Release-Notizen und Anwendung
denselben Stand ausweisen.

## Release-Commit

- **Fixierter Freeze-Commit:** `ce7ce32` (`docs: Update RECOMMENDATIONS status
  to 2026-07-15 with three new epics (#596)`), letzter Commit auf `main` vor
  diesem Scope-Freeze.
- Ab diesem Commit werden nur noch begründete Release-Blocker in den
  Kandidaten aufgenommen (z. B. eine Regression in einer der release-
  relevanten Prüfungen). Neue Funktionen laufen über den nächsten Zyklus.
- Vergleichsbasis: `v2.5.0...ce7ce32` (23 Commits).

## Kategorisierung aller Änderungen seit v2.5.0

Jede Änderung im Vergleich `v2.5.0...ce7ce32` ist einer Kategorie
zugeordnet. Es gibt keine unbewerteten Änderungen.

### Nutzerfunktion (in CHANGELOG `[2.6.0]` unter „Hinzugefügt“)

Zusammengehörige Funktionswelle für Epic #563 (App-Update & KI-Modell-
Status), verteilt über die Commits `abc0068`, `d15c44b`, `4fe22ed`,
`b4e919b`, `dba97c9`:

- Update-Check-Kernlogik (#564)
- KI-Modell-Statuserkennung (#568)
- Menüpunkt „Nach Updates suchen…“ (#565)
- Menüpunkt „KI-Modell verwalten…“ (#569)
- Automatischer Update-Check beim Start (#566)
- KI-Modell-Download: echte Verdrahtung mit dem Warmup-Mechanismus (#570)
- Menüpunkt „KI-Hintergrundentfernung installieren…“ (Installationsdialog
  für manuelles rembg-Setup, #578)

### Fehlerbehebung (in CHANGELOG `[2.6.0]` unter „Behoben“)

- Sichtbarer Warmup-Fehler im KI-Modell-Dialog (#575, Commit `b4e919b`)
- „KI-Modell verwalten…“ ist ohne rembg nicht mehr stumm (#575, Commit
  `4fe22ed`)

### Geändert (in CHANGELOG `[2.6.0]` unter „Geändert“)

- setuptools-Pin gegen `PYSEC-2026-3447` angehoben (`78.1.1` → `>=83.0.0`,
  Teil von Commit `d15c44b`/`abc0068`-Reihe); zusätzlich `pillow` auf
  `12.3.0` in `requirements/constraints.txt` aktualisiert.

### Dokumentation/Build (nicht release-relevant für Nutzer:innen)

- `5fc95e2`, `b72c322`, `af1847e`, `7a4369d`, `ba19f7f`, `651464b`,
  `ce7ce32` – Snapshots von `RECOMMENDATIONS.md`.
- `bddfe9c` – `CLAUDE.md`-Pflege (i18n-Sprachen, CI-Automatisierung).
- `1af62fc` – nachträgliche v2.3.0-Tag/Release-Formalisierung (historisch).
- `6c373c2` – PR-Template um Standard-Gate-Checkliste ergänzt (#557).
- `5a74473`, `ed87a98`, `2c99e64` – Claude-Code-Review-/Agent-Workflows
  (#547, #548, #555), reine CI-/Repo-Tooling-Änderungen ohne Laufzeiteffekt.
- `b43dbd7` – Benchmark-Baseline über Workflow-Artefakt statt Push nach
  `main` (#545/#546).
- `f237ab1` – SessionStart-Hook robust gegen kaputtes System-`pip` (#559).
- `5576500`, `6eacd14`, `aea3522` – Testhygiene/Reusable-Workflow-Guard
  (#299, #318, #541), keine Verhaltensänderung der Anwendung.

### Ausdrücklich nicht release-relevant

Keine der 23 Commits wurde als „unbewertet“ zurückgelassen; alle oben
gelisteten Dokumentations-/Build-Commits sind bewusst als nicht
release-relevant für die Nutzer:innen-Changelog eingestuft (interne
Repo-Pflege, CI-Tooling, Snapshot-Doku).

## Versionssynchronisierung

Alle gefundenen Versionsquellen melden konsistent `2.6.0`:

- `pyproject.toml` (`[project].version`)
- `CHANGELOG.md` + alle fünf Übersetzungen (`docs/i18n/*/CHANGELOG.md`):
  `[2.6.0] – 2026-07-15`, neuer leerer `[Unreleased]`-Abschnitt darüber
- `LICENSES.md` + alle fünf Übersetzungen: Titelzeile und Datumsangabe
  aktualisiert (Dependency-Datenbasis unverändert, da seit dem letzten
  Report vom 2026-07-13 keine weiteren Abhängigkeitsänderungen hinzukamen)
- `packaging/linux/de.bgremover.app.metainfo.xml`: neuer
  `<release version="2.6.0" date="2026-07-15"/>`-Eintrag

`bgremover.__version__` liest `pyproject.toml` zur Laufzeit (bzw. die
Paket-Metadaten nach Installation) – kein weiterer Ort im Code hält die
Version separat vor (siehe `tests/test_version.py`).

## Netzwerk-, Datenschutz- und Fehlerverhalten der neuen Update-/KI-Funktionen

- **Update-Check** (`app_update.py`): Nur ein `GET` gegen die öffentliche
  GitHub-Releases-API (`api.github.com/repos/.../releases/latest`) über
  `urllib.request`, kein Tracking, keine Telemetrie, kein Asset-Download.
  Läuft manuell auf Klick oder – nur bei explizitem Opt-in in den
  Einstellungen (Default **aus**) – einmalig beim Start. Jeder Netzwerk-
  oder Parsing-Fehler wird als `CHECK_FAILED` mit lesbarer Meldung
  zurückgegeben, nie als Absturz; beim automatischen Start-Check bleibt ein
  `CHECK_FAILED` komplett still (kein Fehlerdialog beim Programmstart).
- **KI-Modell-Status/-Download** (`ai_model_status.py`,
  `RembgWarmupWorker`): Statuserkennung liest nur lokal, ob das
  rembg-Standardmodell bereits im Cache liegt (kein Netzwerkzugriff ohne
  expliziten Download-Klick). Der Download selbst läuft über das bestehende
  rembg/Hugging-Face-Modell-Hosting, ausschließlich nach Klick auf
  „Herunterladen“ im KI-Modell-Dialog, mit sichtbarem Abbrechen-Button.
- **Installationsdialog** (`ai_install_dialog.py`): Zeigt nur einen
  Kopieren-Button für einen Installationsbefehl; kein automatischer
  `pip install` aus der App heraus (PEP 668 blockiert das ohnehin ins
  System-Python).

Keine der Funktionen sendet Nutzungsdaten, Bilddaten oder Telemetrie.

## Release-Artefakte (geplant, fünf Stück)

| Artefakt | Plattform | Architektur |
|---|---|---|
| AppImage | Linux | x86_64 |
| AppImage | Linux | aarch64 |
| Debian-Paket (`.deb`) | Linux | x86_64 |
| Debian-Paket (`.deb`) | Linux | aarch64 |
| DMG | macOS | arm64 |

## Bekannte Einschränkungen

- Der Update-Check erkennt nur GitHub-Releases dieses Repositories; ein
  Fork oder eine Distro-verpackte Installation zeigt ggf. keine passende
  Update-Benachrichtigung.
- Der KI-Modell-Download hängt vom externen rembg-Modell-Hosting ab; bei
  dessen Nichtverfügbarkeit bricht der Download mit einer sichtbaren
  Fehlermeldung ab (kein stiller Fallback).
- Kein natives `.empf`-Exportformat für EufyMake Studio (weiterhin über
  `eufymake_export`/PNG-Assets, siehe ADR
  [`docs/history/ADR-2026-eufymake-exportpaket.md`](ADR-2026-eufymake-exportpaket.md)).

## Ausdrücklich nicht in diesem Release enthalten

- 16-Bit-Pipeline aus #581 (offene Arbeit, eigener Epic).
- 3D-Vorschau aus #582 (offene Arbeit, eigener Epic).
- Keine kosmetische Umstrukturierung außerhalb release-relevanter
  Dokumentation.

## Übersetzte Dokumente

`README.md`, `INSTALL_LINUX.md`, `INSTALL_MAC.md`, `RESOURCES.md`,
`ANLEITUNG.md` und `RECOMMENDATIONS.md` enthalten keine versionsspezifischen
Verweise auf `2.5.0`/`2.6.0` und benötigten daher keine inhaltliche
Anpassung für diesen Release. `CHANGELOG.md` und `LICENSES.md` wurden in
allen fünf Sprachen (`en`, `es`, `fr`, `uk`, `zh`) synchron mit dem
deutschen Original aktualisiert (`tests/test_changelog_metadata.py`,
`tests/test_licenses_version.py`).

## Verbleibende bekannte Risiken

- Der `LICENSES.md`-Report wurde nicht mit vollständig installierten
  `ai`-Extras neu generiert (diese Umgebung hat kein `rembg`/`onnxruntime`
  installiert); es wurden nur Versionsnummer und Datum in der Kopfzeile
  aktualisiert. Die zugrunde liegenden Abhängigkeitsversionen haben sich
  seit dem letzten Vollreport (2026-07-13, bereits nach v2.5.0 inkl.
  `pillow`/`setuptools`-Bump) nicht weiter geändert – ein `make`-Gate mit
  vollständigen Extras sollte das vor dem Tag trotzdem einmal verifizieren.
- Tag und Veröffentlichung sind **nicht** Teil dieses Issues (#583); der
  Kandidaten-Gate der nachfolgenden Release-Aufgabe (Teil von #580) prüft
  Tag/Version-Abgleich (`tests/test_release_gate.py`) und veröffentlicht
  bei grüner Full-CI-Matrix.

## Verantwortlichkeit für den Kandidaten-Gate

Freigabe und Tag-Erstellung liegen bei der nachfolgenden Release-Aufgabe
unter Epic #580; dieses Issue (#583) liefert ausschließlich den geprüften,
versionssynchronen Scope-Freeze-Stand als Grundlage dafür.
