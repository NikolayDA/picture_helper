# Release 2.6.0 – Artefaktnamen (#584) und Umfang dieser Prüfung

Teil von #580, Umsetzung des auf #584 nachgetragenen Umsetzungsauftrags
(folgt auf den Scope-Freeze aus #583,
[`RELEASE-2.6.0-scope-freeze.md`](RELEASE-2.6.0-scope-freeze.md)).

## Auslöser

#584 selbst ist der Kandidaten-Gate-Auftrag für v2.6.0 (fünf Artefakte,
volle Qualitäts-/Funktionsprüfung, Go-/No-Go-Entscheidung). Ein Kommentar
des Repo-Owners auf #584 (2026-07-15) hat den Umfang um zwei konkrete
Punkte ergänzt: Die Artefaktnamen sollen eindeutiger nach
Plattform/Gerät sein, und der Linux/Raspberry-Pi-Build soll dieselbe
eingebaute KI wie der macOS-Build sichtbar tragen.

## Befund

- Der Release-Workflow bündelt rembg/onnxruntime bereits standardmäßig für
  **alle** fünf Artefakte (`WITH_AI` gilt uniform über die gesamte
  Build-Matrix) – der Linux/Raspberry-Pi-Build hatte also schon dieselbe KI
  wie macOS, nur unsichtbar im Dateinamen.
- Zwei der fünf Artefakte trugen zuvor dasselbe rohe Architektur-Tag
  `arm64`: das Linux/Raspberry-Pi-`.deb` und die macOS-`.dmg`, nur an der
  Dateiendung unterscheidbar. AppImage (`aarch64`) und `.deb` (`arm64`)
  nutzten zudem unterschiedliche Vokabeln für denselben Prozessor.

## Umsetzung

Neues Namensschema `BgRemover-<Version>-<Plattform-Tag>[-ai].<Endung>`:

| Artefakt | Alt | Neu |
|---|---|---|
| Linux x86_64 AppImage | `BgRemover-2.6.0-x86_64.AppImage` | `BgRemover-2.6.0-linux-x86_64-ai.AppImage` |
| Linux/Raspberry-Pi aarch64 AppImage | `BgRemover-2.6.0-aarch64.AppImage` | `BgRemover-2.6.0-linux-raspberrypi-arm64-ai.AppImage` |
| Linux x86_64 `.deb` | `BgRemover-2.6.0-amd64.deb` | `BgRemover-2.6.0-linux-x86_64-ai.deb` |
| Linux/Raspberry-Pi aarch64 `.deb` | `BgRemover-2.6.0-arm64.deb` | `BgRemover-2.6.0-linux-raspberrypi-arm64-ai.deb` |
| macOS arm64 `.dmg` | `BgRemover-2.6.0-arm64.dmg` | `BgRemover-2.6.0-macos-arm64-ai.dmg` |

Der `-ai`-Suffix erscheint nur, wenn der jeweilige Build die
KI-Hintergrundentfernung tatsächlich bündelt (Standard für
Release-Downloads); beim `.deb` wird er aus dem Namen der gewrappten
AppImage abgeleitet statt über einen zweiten, unabhängig zu pflegenden
`--ai`-Schalter, kann also nicht von ihr abweichen.

Geändert: `packaging/linux/build_appimage.sh`, `packaging/linux/build_deb.sh`,
`packaging/mac/build_macos.sh`, `.github/workflows/release-linux.yml` (neues
Matrix-Feld `platform_tag`; Verify-Schritte und der Name des
Workflow-Zwischenartefakts folgen demselben Tag), `tests/test_linux_packaging.py`
+ `tests/test_macos_packaging.py` (neue/angepasste Assertions inkl. eines
End-to-End-Baus des `.deb` mit und ohne `-ai`), sowie README/INSTALL_*/
CHANGELOG auf Deutsch und in allen fünf Übersetzungen (en/es/fr/uk/zh).

Bewusst **nicht** verändert: die Zahl der Artefakte (weiterhin fünf), das
`.deb`-interne `Architecture`-Feld (`amd64`/`arm64`, von apt verlangt,
unabhängig vom für Menschen lesbaren Dateinamen), die Build-Matrix-Runner.

## Geprüft in dieser Sitzung (lokal, auf diesem Commit)

- `make check` (ruff + mypy + pytest): **1568 passed, 3 skipped, 13
  deselected, 0 fehlgeschlagen.**
- `shellcheck` manuell auf den drei geänderten Build-Skripten (nur
  vorbestehende Info-Hinweise außerhalb der geänderten Zeilen; die
  Paketierungs-Skripte sind nicht Teil von `make lint`s `lint-shell`-Auswahl).
- `tests/test_linux_packaging.py`/`tests/test_macos_packaging.py` bauen das
  `.deb` real (`dpkg-deb`) aus Stub-AppImages und verifizieren Namen inkl.
  `-ai`-Ableitung; die AppImage-/`.dmg`-Bauskripte selbst bleiben wie zuvor
  textbasiert geprüft (kein `python-appimage`/PyInstaller/Xcode in dieser
  Umgebung verfügbar).
- i18n-/Markdown-Governance-Tests (`test_changelog_metadata`,
  `test_i18n_docs`, `test_i18n_sync`, `test_markdown_links`) grün.

## Ausdrücklich NICHT Teil dieser Sitzung

Der volle Kandidaten-Gate aus #584 verlangt echte native Builds/Installs auf
allen fünf Zielplattformen (inklusive Hardware-Smokes auf echtem
Raspberry Pi und Mac) sowie eine Go-/No-Go-Entscheidung mit Commit-SHA. Das
lässt sich aus dieser sandboxed Sitzung heraus nicht seriös durchführen
(kein Zugriff auf echte Mac-/Pi-Hardware) und wurde auf Rückfrage bewusst
**nicht** über `workflow_dispatch` angestoßen (Kostenabwägung: mehrere native
Runner inkl. macOS/ARM für 30–60+ Minuten). Vor dem eigentlichen
`v2.6.0`-Tag bleibt offen:

- [ ] `release-linux.yml` per `workflow_dispatch` (oder Tag) real auf allen
      drei nativen Runnern durchlaufen lassen und die fünf resultierenden
      Dateinamen/Prüfsummen gegen die Tabelle oben abgleichen.
- [ ] Install-/Start-Smokes auf echter Raspberry-Pi- und macOS-Hardware.
- [ ] Die übrigen Akzeptanzkriterien aus #584 (Update-Check-/KI-Modell-
      Smokes, Secret-/Pfad-Scan der Artefakte, vollständige Gate-Matrix,
      finale Go-/No-Go-Entscheidung) abarbeiten.

Diese Sitzung liefert den konkreten, per Kommentar auf #584 nachgetragenen
Umsetzungsauftrag (Namensschema + sichtbare KI-Parität zwischen
Raspberry-Pi- und macOS-Build); die eigentliche Release-Freigabe bleibt der
nachfolgenden, tatsächlichen Kandidaten-Prüfung mit echten Artefakten
vorbehalten.
