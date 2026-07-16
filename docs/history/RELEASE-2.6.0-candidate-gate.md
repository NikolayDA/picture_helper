# Release 2.6.0 – Kandidaten-Gate (#584)

Teil von #580, folgt auf den Scope-Freeze (#583,
[`RELEASE-2.6.0-scope-freeze.md`](RELEASE-2.6.0-scope-freeze.md)) und die
Artefakt-Namensschema-Umsetzung (#601,
[`RELEASE-2.6.0-artifact-naming-gate.md`](RELEASE-2.6.0-artifact-naming-gate.md)).
Dieses Dokument ist die in #584 geforderte Gate-Matrix: der wieder geöffnete
Kandidaten-Gate mit finalem SHA, fünf realen Artefakten, Prüfsummen,
Plattform-Smokes und einer Go-/No-Go-Entscheidung.

## Kandidaten-Commit

- **Getesteter Commit:** `05936e5fec89585321e4508670123fb89ada8adb` (Branch
  `claude/github-issue-584-mnfssc`, PR [#608](https://github.com/NikolayDA/picture_helper/pull/608)
  für #584).
- Dieser Commit ist der letzte von **sechs** rein additiven Funktions-Commits
  gegenüber dem `main`-Tip `f5e2b217` (`docs: reconcile July 16 audit
  follow-ups (#605)`), die alle ausschließlich den Release-Workflow selbst
  und sein Scan-Tooling betreffen – kein Applikationscode
  (`bgremover/`) wurde in dieser Sitzung verändert:
  1. `427725477d` – SHA-256-Log-Schritt + erster Secret-/Pfad-Scan.
  2. `9c3f9f2` – Härtung nach automatisiertem PR-Review (Payload-Extraktion,
     keine Klartext-Secrets in Logs, harter Fehlschlag bei unbekannten
     Pfad-Benutzern).
  3. `c51e7f2` – Fingerprint-Allowlist gegen Fehlalarme in gebündelten
     Drittbibliotheken (Qt6/Pillow/scipy) – **später verworfen**.
  4. `3bbd60b` – ersetzt die Allowlist durch wortgrenzen-verankerte
     Secret-Muster (siehe unten).
  5. `7f2932f` – begrenzt den harten Entwicklerpfad-Fehlschlag auf das
     eigene `bgremover`-Paket.
  6. `05936e5` – echter `.deb`-Install/Start/Remove-Zyklus direkt in CI
     (dieser Commit; siehe unten).
  Details, Fehlschläge und Begründung jedes Schritts: siehe „Warum mehrere
  zusätzliche Commits in dieser Sitzung".
- `f5e2b217` selbst wurde vollständig gegated (Full-CI + alle fünf Artefakte,
  Lauf [`29486928558`](https://github.com/NikolayDA/picture_helper/actions/runs/29486928558),
  grün) **bevor** der erste Zusatz-Commit entstand.
- **Der bisher in #583 fixierte Freeze-Commit `ce7ce32` ist damit endgültig
  durch `05936e5` ersetzt** — wie im Wiedereröffnungskommentar auf #584
  gefordert: `ce7ce32` lag vor #601/#602/#604 (Artefakt-Namensschema,
  Release-Reuse-Härtung) und konnte daher nie der tatsächlich zu
  veröffentlichende Stand sein.

### Warum mehrere zusätzliche Commits in dieser Sitzung

Die ursprünglich geplante Prüfsequenz war: Kandidaten-SHA `f5e2b217` einmalig
per `workflow_dispatch` gaten und alle Befunde dokumentieren. Der erste Lauf
([`29486928558`](https://github.com/NikolayDA/picture_helper/actions/runs/29486928558))
bestätigte Build, Versionen, Namen und alle Smokes – lieferte aber **keine**
SHA-256-Prüfsumme je Artefakt, weil das Herunterladen der Build-Artefakte aus
Actions in dieser Sitzung durch die Netzwerk-Policy blockiert ist (Azure Blob
Storage, der Speicherort von `actions/upload-artifact`, ist für diese Sitzung
nicht freigegeben – bestätigt über den Proxy-Status:
`gateway answered 403 to CONNECT`, Host
`productionresultssa7.blob.core.windows.net`). Ein lokaler Nachbau war ebenso
nicht möglich: `python-appimage` lädt sein Laufzeit-Bundle zur Build-Zeit über
`api.github.com` (direkter GitHub-API-Zugriff ist für diese Sitzung nicht
freigegeben, siehe Umgebungsbeschreibung).

#### 1. `427725477d` – SHA-256 + erster Secret-/Pfad-Scan

Statt die Prüfsumme als offene Lücke zu dokumentieren, wurde `release-linux.yml`
um zwei rein additive Schritte ergänzt, die **auf dem Build-Runner selbst**
laufen (kein Download nötig): `sha256sum`/`shasum -a 256 dist/*` direkt nach
jedem Artefakt-Sammeln-Schritt, sowie ein neues `scripts/scan_release_artifacts.py`,
das jede gebaute Datei binär auf hochkonfidente Geheimnis-Muster prüft (harter
Fehlschlag bei Fund) und Entwicklerpfade außerhalb der bekannten CI-Konten
meldet. Lauf [`29488035790`](https://github.com/NikolayDA/picture_helper/actions/runs/29488035790)
– grün, damals maßgeblich.

Auf PR [#608](https://github.com/NikolayDA/picture_helper/pull/608) (dieser
Commit + die Gate-Dokumentation) lieferte ein automatisiertes Review fünf
Befunde am Scan-Skript und der Dokumentation selbst: (a) Geheimnisse dürfen nie
im Klartext in CI-Logs erscheinen, (b) der Scan sah nur die komprimierten
Container-Bytes (AppImage/`.deb`/`.dmg`) und musste die Nutzlast erst entpacken,
(c) unbekannte Entwicklerpfade wurden nur gemeldet, nicht hart abgelehnt,
(d) das Gate muss für den tatsächlich getaggten Commit erneut laufen, (e) die
`.deb`-Install/Start/Remove-Zeile im Dokument war durch einen lokalen
Platzhalter-Nachbau, nicht das echte CI-Artefakt, belegt. Die folgenden fünf
Commits lösen alle fünf Befunde – mit zwei Fehlschlägen unterwegs, die beide
zu einer grundsätzlich robusteren Lösung geführt haben, statt sie zu
übertünchen.

#### 2. `9c3f9f2` – Payload-Extraktion, keine Klartext-Secrets, harter Fehlschlag

Adressiert die Befunde (a)–(c) direkt: der Scan entpackt jetzt AppImage
(`--appimage-extract`), `.deb` (`dpkg-deb -x`, rekursiv für die darin gewrappte
AppImage) und `.dmg` (`hdiutil attach`/`detach`) und scannt den entpackten
Inhalt zusätzlich zur Rohdatei; ein Fund wird nur noch als SHA-256-Fingerprint
+ Position geloggt, nie das Geheimnis selbst; unbekannte Pfad-Benutzer lassen
den Scan jetzt hart fehlschlagen statt nur zu warnen. Damit sah der Scan zum
ersten Mal wirklich in die entpackten, echten Drittanbieter-Binärdateien
hinein – und genau das legte in Lauf
[`29490801906`](https://github.com/NikolayDA/picture_helper/actions/runs/29490801906)
neue, vorher unsichtbare Fehlalarme offen: Pillows Font-Metrik-Tabelle
(`PIL/ImageFont.py`) enthält eine Base64-Zeichenkette, die zufällig wie ein
AWS-Schlüssel aussieht, und scipys kompilierter HiGHS-Solver
(`_highspy/_core*.so`) enthält ein gemanglestes C++-Symbol
(`…ghs_setCallback…`), das zufällig das GitHub-Token-Muster trifft.

#### 3. `c51e7f2` – Fingerprint-Allowlist (später verworfen)

Erster Fixversuch: eine explizite Allowlist mit den SHA-256-Fingerprints der
drei konkret verifizierten Fehlalarme (Pillow-AWS, scipy-GitHub-Token je
Linux/macOS-Build) plus ein struktureller PEM-Check (ein echter Schlüsselkörper
folgt der `BEGIN …`-Kopfzeile unmittelbar mit einem langen Base64-Lauf; Qt6s
eigene OpenSSL-Typtabelle hat dort nur ein Nullbyte oder das nächste Label).
Gleichzeitig wurde `scan_bytes` von `search` (nur der erste Treffer je Muster)
auf `finditer` umgestellt, um einen Codex-Befund zu schließen: ein zweites,
echtes Geheimnis hätte sich sonst hinter einem bereits allowlisted ersten
Treffer verstecken können. Genau diese korrekte Reparatur deckte in Lauf
[`29492642852`](https://github.com/NikolayDA/picture_helper/actions/runs/29492642852)
das eigentliche Problem auf: **43** einzelne GitHub-Token-Treffer in
`_highspy/_core*.so`, alle aus derselben Namenskonvention (jede exportierte
HiGHS-C-API-Funktion heißt `Highs_<name>`, das gemanglte Symbol enthält
`ghs_<name>` als Teilstring). Ein Fingerprint pro Symbol ist damit nicht
wartbar – die Allowlist als Ansatz war grundsätzlich falsch dimensioniert,
nicht nur unvollständig.

#### 4. `3bbd60b` – wortgrenzen-verankerte Secret-Muster (löst den Scan-Kern)

Ersetzt die Allowlist vollständig durch ein strukturelles Kriterium: ein echtes
Secret steht immer als eigenständiger Wert (Umgebungsvariable, Header,
JSON-Feld, Kommandozeile) und ist daher von einem Nicht-Identifier-Zeichen
umgeben. Ein Treffer *mitten* in einem viel längeren Bezeichner – wie `ghs_`
in `highs_setCallback` – ist strukturell nie ein echtes Secret. Die
AWS-Key-/GitHub-Token-/Slack-Token-Muster bekamen Lookaround-Wortgrenzen
(`(?<![A-Za-z0-9_])…(?![A-Za-z0-9_])`); der PEM-Check blieb strukturell wie in
Schritt 3. Ergebnis, lokal gegen den exakt gepinnten `rembg[cpu]`/PyQt6-
Abhängigkeitsbaum verifiziert: alle 43 scipy/HiGHS-Treffer **und** der
ursprüngliche Pillow-Fehlalarm verschwinden, ganz ohne Allowlist-Einträge –
bestätigt durch einen Scan aller 13.422 Dateien dieses Baums (0 Funde). Lauf
[`29493851030`](https://github.com/NikolayDA/picture_helper/actions/runs/29493851030)
löste damit den Secret-Scan-Teil vollständig, scheiterte aber an einem
**anderen** Kriterium: dem Entwicklerpfad-Scan (siehe Schritt 5).

#### 5. `7f2932f` – Entwicklerpfad-Fehlschlag auf das eigene Paket begrenzt

Der in Schritt 2 eingeführte harte Fehlschlag bei unbekannten `/home`-/`/Users`-
Pfad-Benutzern schlug auf allen drei Build-Legs fehl. Empirische Reproduktion
der exakt gepinnten Wheels ordnete jeden Fund harmlosem Drittanbieter-Inhalt
zu, den dieses Projekt nicht selbst erzeugt: numpys `DataSource`-Docstring
nutzt `/home/guido` und `/home/alex` als Beispielpfade, numbas `pycc/cc.py`
kommentiert `/home/antoine`, networkxs HITS-/Link-Prediction-Module zitieren
Jon Kleinbergs Cornell-Homepage-URL (`.../home/kleinber/auth.pdf`), und PyQt6s
kompilierte `sip`-Erweiterung hat einen vom eigenen Maintainer-Wheel-Build
eingebrannten Pfad `/home/bob/bob/include`. Keiner davon ist ein Leak der
eigenen Build-Umgebung – ein harter Fehlschlag darauf würde bei jedem
zukünftigen Dependency-Update unvorhersehbar wiederkehren. Da `bgremover` der
einzige selbst kompilierte Code ist, begrenzt dieser Commit den harten
Fehlschlag auf Funde unterhalb einer `bgremover`-Pfadkomponente; Funde
anderswo (Drittanbieter-Abhängigkeiten, rohe Container-Bytes ohne
Paket-Kontext) werden weiterhin ausgegeben, blockieren aber nicht mehr. Lauf
[`29495305505`](https://github.com/NikolayDA/picture_helper/actions/runs/29495305505)
– **vollständig grün**, alle drei Build-Legs inkl. Secret-/Pfad-Scan.

#### 6. `05936e5` – echter `.deb`-Install/Start/Remove-Zyklus in CI (dieser Commit)

Löst den letzten offenen Befund (e): das Kandidaten-Gate-Dokument hatte einen
echten `dpkg`-Installationszyklus behauptet, obwohl der nur lokal mit einer
Platzhalter-Payload nachgebaut worden war (das tatsächliche CI-Artefakt blieb
ungetestet) – `dpkg-deb --info`/`--contents` prüft nur Metadaten, installiert
nichts. Neuer Workflow-Schritt „Real .deb install/start/remove smoke (native
architecture)" auf beiden nativen Linux-Legs (x86_64 **und** aarch64):
installiert das frisch gebaute `.deb` über `apt-get install ./*.deb` (löst
`Depends: libfuse2|libfuse2t64` aus den Runner-Repos auf), startet das
installierte `/opt/BgRemover/BgRemover.AppImage` mit demselben
Fork-Bomb-/Hänger-Wächter wie der bestehende AppImage-Smoke, entfernt das Paket
per `dpkg -r bgremover` und verifiziert die Abwesenheit aller installierten
Dateien danach. Lauf
[`29506204774`](https://github.com/NikolayDA/picture_helper/actions/runs/29506204774)
– **vollständig grün**, neuer Schritt erfolgreich auf beiden Legs (Details:
„Build- und Start-Smokes" unten). Befund (d) (SHA nach Merge/Squash) wird im
Abschnitt „Hinweis für #585" unten abschließend adressiert.

Alle sechs Commits sind durch `tests/test_scan_release_artifacts.py`
(25 Tests) sowie `tests/test_release_gate.py`/`test_linux_packaging.py`/
`test_macos_packaging.py` (unverändert grün) abgedeckt und in `make check`
(1598 statt ursprünglich 1569 Tests) enthalten. Lauf `29506204774` auf Commit
`05936e5` ist der unten dokumentierte, maßgebliche Lauf.

## Qualitäts-Gate

| Kriterium | Ergebnis | Beleg |
|---|---|---|
| `make pr-check` grün auf dem Kandidaten-Commit | ✅ | Lokal: `install-test` + `doctor` (`scripts/check_test_env.py`, alle Checks OK) + `check` (ruff/mypy/pytest) grün. `pytest`: **1598 passed, 3 skipped, 13 deselected**, 0 fehlgeschlagen. |
| `make coverage` | ✅ | `TOTAL … 96%` (Schwelle `fail_under = 86`, deutlich überschritten). Coverage-Quelle ist ausschließlich `bgremover` (`pyproject.toml`); die sechs Commits dieser Sitzung ändern nur `scripts/`/`.github/workflows/`/`tests/`, daher unverändert gegenüber der letzten Messung. |
| `make ui` (volle qtbot-Suite, sonst nur nightly) | ✅ | **18 passed** (alle `ui`-markierten Tests, inkl. des in `make check` bereits enthaltenen `ui_smoke`-Subsets). |
| Volle Testmatrix des Release-Workflows (`ci.yml`, Linux+macOS × Python 3.10–3.13) für exakt den Kandidaten-Commit | ✅ | Lauf [`29506204774`](https://github.com/NikolayDA/picture_helper/actions/runs/29506204774), Job `test` (8 Matrix-Beine): alle grün, keine übersprungene Pflichtprüfung. |
| Keine bekannten P0/P1-Defekte, keine ungeklärten regressiven P2 im Release-Scope | ✅ | Kein offener Bug-Befund in `RECOMMENDATIONS.md` betrifft den Release-Scope; N15/N16 sind reine Coverage-Lücken (🟡, keine Verhaltensfehler), unabhängig von #584. |
| Abweichungen lokal ↔ GitHub Actions dokumentiert | ✅ | Keine Abweichung: identische Testzahl/-ergebnisse lokal und in CI (lokal ohne `ai`-Extras/rembg, wie in allen vorherigen Releases – dokumentiertes, seit Epic #563 bekanntes Verhalten). |
| Getesteter Commit-SHA = fixierter Release-Commit | ✅ | Siehe „Kandidaten-Commit" oben; `ce7ce32` (#583) ist explizit durch `05936e5` abgelöst, mit Begründung. |

## Artefakte

Alle fünf Artefakte aus Lauf
[`29506204774`](https://github.com/NikolayDA/picture_helper/actions/runs/29506204774)
(`workflow_dispatch`, `with_ai=true`, nicht veröffentlichend – kein Tag-Push,
`publish`-Job korrekt `skipped`):

| Artefakt | Plattform/Arch | Version | Größe | SHA-256 |
|---|---|---|---|---|
| `BgRemover-2.6.0-linux-x86_64-ai.AppImage` | Linux x86_64 (`ubuntu-24.04`) | 2.6.0 | 256 MiB | `8933573f4158174a71f916839658abddef7f3628e4670fc6384abe5621d9f71a` |
| `BgRemover-2.6.0-linux-x86_64-ai.deb` | Linux x86_64, `Architecture: amd64` | 2.6.0 | 254 MiB | `4fef28db1e2c7217c99112d1a8dc2676c20043c88979672648d9a892f573711d` |
| `BgRemover-2.6.0-linux-raspberrypi-arm64-ai.AppImage` | Linux aarch64 (nativer `ubuntu-24.04-arm`-Runner, Raspberry Pi OS-kompatibel) | 2.6.0 | 248 MiB | `8f5bdae4bf9bb3f667896ce20b8337ea9c82a39a7ae681c3e0a46493183ef6b8` |
| `BgRemover-2.6.0-linux-raspberrypi-arm64-ai.deb` | Linux aarch64, `Architecture: arm64` | 2.6.0 | 247 MiB | `fa2b4e5cd7bde1243254e1d94e3364f5b3b175df3c972070fe5240a722460986` |
| `BgRemover-2.6.0-macos-arm64-ai.dmg` | macOS arm64 (nativer `macos-latest`-Runner, Apple Silicon) | 2.6.0 | 134 MiB | `20bd1ddef14b032baf9a077c1874c181dcbbab9940d917b573ee55a5d6ef3972` |

Namensschema, Version und Architektur je Artefakt sind zusätzlich durch die
bestehenden `Verify built Linux artifacts`/`Verify built macOS artifact`-Schritte
im Workflow **hart erzwungen** (Build schlägt fehl, wenn Name/Version/
`dpkg-deb`-Feld nicht passen) – kein manueller Soll/Ist-Abgleich nötig.

### Build- und Start-Smokes je Artefakt

| Kriterium (#584) | Ergebnis | Beleg |
|---|---|---|
| Linux x86_64 AppImage: gebaut + in sauberer Testumgebung gestartet | ✅ | CI-Job `linux x86_64`: `Smoke-launch built AppImage` → `smoke_launch OK … peak Instanzen=1, erlaubt=5` (inkl. KI-Selbsttest, `WITH_AI=1`). |
| Linux aarch64 AppImage: gebaut + mind. in vorgesehener CI-Umgebung geprüft | ✅ | CI-Job `linux aarch64` läuft auf **echtem** `ubuntu-24.04-arm`-Runner (native ARM-Hardware, keine Emulation): Build + `Smoke-launch` + KI-Selbsttest (`rembg-Kette … importierbar`) grün. |
| Linux x86_64 `.deb`: installierbar, startbar, sauber entfernbar/aktualisierbar | ✅ | **Echter CI-Zyklus** auf dem `linux x86_64`-Build-Runner (siehe „Realer CI-Install-Smoke" unten): `apt-get install ./*.deb` → alle erwarteten Dateien korrekt platziert → Start vom installierten `/opt/BgRemover/BgRemover.AppImage` (`smoke_launch OK`) → `dpkg -r bgremover` entfernt rückstandslos. |
| Linux aarch64 `.deb`: in vorgesehener Zielumgebung installierbar + startbar | ✅ | **Echter CI-Zyklus** auf nativer aarch64-Hardware (`ubuntu-24.04-arm`-Runner, keine Emulation) – identischer Ablauf wie x86_64, siehe „Realer CI-Install-Smoke" unten. |
| macOS arm64 DMG: öffnen, installieren, starten | ⚠️ Teilweise | `hdiutil imageinfo` (gültiges DMG-Image) durch CI hart verifiziert; **echter** Start des gebauten `.app` (nicht nur `hdiutil`) lief auf nativer Apple-Silicon-Hardware im CI-Job `macos arm64`: `Smoke-launch built macOS app` → `smoke_launch OK`, inkl. KI-Selbsttest. Der manuelle „DMG mounten → in Applications ziehen"-Endnutzerfluss wurde nicht auf echter Mac-Hardware nachvollzogen (in dieser Sitzung nicht verfügbar) – siehe Restrisiken. |

### Realer CI-Install-Smoke (Linux x86_64 + aarch64, echtes `.deb`)

Eine frühere Fassung dieses Dokuments belegte den `.deb`-Lebenszyklus mit einem
**lokalen Nachbau** (Platzhalter-Payload, da der Artefakt-Download aus Actions
blockiert war) – ein automatisiertes Review auf PR #608 wies zurecht darauf
hin, dass das nie das tatsächliche CI-Artefakt prüft und ein kaputtes reales
`.deb` (z. B. falsche Depends-Auflösung oder Pfade) trotzdem ein grünes Gate
hätte passieren können. Commit `05936e5` schließt diese Lücke, indem der
Zyklus jetzt **direkt im Release-Workflow gegen das gerade gebaute Artefakt**
läuft – Workflow-Schritt „Real .deb install/start/remove smoke (native
architecture)", auf beiden nativen Linux-Legs (x86_64 **und** aarch64, kein
Emulationsvorbehalt):

1. `sudo apt-get install -y ./*.deb` – installiert das echte, im selben Job
   gebaute `.deb` über apt (löst `Depends: libfuse2|libfuse2t64` aus den
   Runner-Repos auf, keine manuelle `dpkg`/`--fix-broken`-Nachbesserung nötig).
   CI-Log: `Setting up bgremover (2.6.0) ...`
2. Verifiziert `/opt/BgRemover/BgRemover.AppImage` (ausführbar),
   `/usr/share/applications/de.bgremover.app.desktop` und das Icon.
3. Startet das **installierte** AppImage mit demselben Fork-Bomb-/
   Hänger-Wächter (`scripts/smoke_launch.py`) wie der bestehende
   Roh-AppImage-Smoke. CI-Log (x86_64):
   `smoke_launch OK: '/opt/BgRemover/BgRemover.AppImage --appimage-extract-and-run' sauber gestartet (peak Instanzen=1, erlaubt=5)`.
4. `sudo dpkg -r bgremover` – CI-Log: `Removing bgremover (2.6.0) ...`
5. Verifiziert die Abwesenheit von AppImage und Desktop-Launcher danach.

Beide Legs schließen mit
`OK: echter apt-Install/Start/dpkg-Remove-Zyklus fuer <Artefakt> erfolgreich.`
(Lauf [`29506204774`](https://github.com/NikolayDA/picture_helper/actions/runs/29506204774),
Jobs `linux x86_64` und `linux aarch64`). Damit ist – anders als zuvor – nicht
nur die Paketierungs-Mechanik im Allgemeinen, sondern der Install-/Start-/
Remove-Zyklus des **tatsächlich für diesen Kandidaten gebauten** `.deb`
auf beiden Ziel-Architekturen real verifiziert; eine lokale Nachbildung ist
nicht mehr nötig und wird durch diesen Abschnitt ersetzt.

## Sekret-/Pfad-Scan

`scripts/scan_release_artifacts.py` lief für jedes der fünf Artefakte direkt
auf dem jeweiligen Build-Runner, inklusive entpacktem Inhalt (AppImage/`.deb`/
`.dmg` werden vor dem Scan entpackt, siehe Commit `9c3f9f2`; Muster sind seit
`3bbd60b` wortgrenzen-verankert, siehe „Kandidaten-Commit"). Workflow-Schritt
„Scan built artifacts for secrets and dev paths", Lauf
[`29506204774`](https://github.com/NikolayDA/picture_helper/actions/runs/29506204774):

| Artefakt (Leg) | Hochkonfidente Funde (AWS-Key/GitHub-Token/Slack-Token/PEM-Key) | Hinweis (nicht blockierend): Pfad-Benutzer außerhalb der Allowlist, außerhalb des eigenen Pakets |
|---|---|---|
| Linux x86_64 AppImage + `.deb` | keine | `alex`, `antoine`, `bob`, `foo`, `guido`, `kleinber`, `user` (numpy-Docstring-Beispiele, numba-Kommentar, PyQt6-`sip`-Build-Pfad, networkx-Autorenzitat – alles Drittanbieter, siehe Commit `7f2932f`) |
| Linux aarch64 AppImage + `.deb` | keine | identisch zu x86_64 (dieselben eingebetteten Docstrings/Kommentare/Build-Pfade, obwohl die aarch64-Wheels eigene, architekturspezifische Binärdateien sind) |
| macOS arm64 DMG | keine | `cloudtest`, `phil`, `sysadmin`, `user` (macOS-spezifische Drittanbieter-Build-/Doku-Pfade, z. B. Xcode-Toolchain-Vorlagen) |

**Ergebnis: keine API-Schlüssel, Tokens oder private Zertifikate in irgendeinem
Artefakt.** Die informativen Pfad-Hinweise sind seit Commit `7f2932f`
strukturell auf Drittanbieter-Inhalte beschränkt: der Scan schlägt nur noch
hart fehl, wenn ein unbekannter Pfad-Benutzer unter einer `bgremover`-
Pfadkomponente auftaucht (also im selbst erzeugten Code); alle oben gelisteten
Benutzernamen stammen nachweislich aus fremden, gepinnten Abhängigkeiten
(numpy/numba/networkx/PyQt6-`sip` auf Linux, Xcode-Toolchain-Vorlagen auf
macOS) und wurden einzeln zurückverfolgt (siehe „Warum mehrere zusätzliche
Commits", Schritt 5) – keine eigene Entwicklerspur, kein Blocker. Unbeabsichtigte
Testdaten: ausgeschlossen, da `python -m build --wheel` ausschließlich das
`bgremover`-Package (kein `tests/`-Verzeichnis) verpackt und `build_deb.sh` nur
die in „Artefakte" gelisteten Dateien in die `.deb`-Struktur kopiert.

## Laufzeitbibliotheken/Modelle & Offline-Verhalten

- Alle fünf Artefakte bündeln rembg/onnxruntime standardmäßig (`WITH_AI=1`,
  sichtbar am `-ai`-Namenssuffix); das rembg-Modell selbst (`u2net.onnx`) wird
  **nicht** gebündelt, sondern beim ersten Gebrauch nach Klick auf
  „Herunterladen" im KI-Modell-Dialog geladen (dokumentiertes,
  vorsätzliches Verhalten seit Epic #563 – siehe
  [`RELEASE-2.6.0-scope-freeze.md`](RELEASE-2.6.0-scope-freeze.md)).
- Linux-`.deb` deklariert `Depends: libfuse2 | libfuse2t64` (zum Ausführen der
  gewrappten AppImage) – im realen CI-Install-Smoke auf beiden Architekturen
  über `apt-get install ./*.deb` real aufgelöst und bestätigt.
- Offline-Verhalten von Update-Check und KI-Modell-Download ist über
  automatisierte Tests abgedeckt (siehe „Funktions-Smokes" unten) und bereits
  in der Freigabenotiz zu #583 beschrieben.

## Funktions- und Laufzeit-Smokes

| Kriterium (#584) | Ergebnis | Beleg |
|---|---|---|
| Anwendung startet mit frischem Profil ohne Absturz | ✅ | Lokal: `python3 -m bgremover` mit vollständig isoliertem `HOME`/`XDG_*` (`env -i`), `QT_QPA_PLATFORM=offscreen`, `BGREMOVER_SMOKE_TEST=1` → Exit 0. Zusätzlich auf jedem CI-Build-Runner (AppImage/`.app`, s. o.). |
| Kernpfade Laden/Bearbeiten/Projekt speichern-öffnen/Exportieren bestehen Smoke-Test | ✅ | Abgedeckt durch die bestehende, in `make check`/`make ui` laufende qtbot-Suite (u. a. `test_project_io.py`, `test_menu_actions.py`, `test_eufymake_writer.py`, `test_canvas_*`) – offscreen, mit echten Bilddaten, exakt das im Projekt etablierte Smoke-Test-Verfahren (siehe CLAUDE.md). Kein neuer Test nötig, da bereits vollständig abgedeckt und grün. |
| Update-Prüfung: Erfolg + verständliche Degradation bei Offline/Timeout/ungültiger Antwort | ✅ | `tests/test_app_update.py`: `UP_TO_DATE`/`UPDATE_AVAILABLE` sowie `CHECK_FAILED` bei HTTP-Fehler, Timeout, Verbindungsfehler, abgebrochenem Read, ungültigem JSON, nicht parsbarer Version, fehlenden Feldern, Nicht-Objekt-Payload – je ein dedizierter Test, alle grün. |
| Manuelle + automatische Update-Prüfung respektieren Einstellungen | ✅ | `tests/test_main_window.py` (u. a. `AUTO_UPDATE_CHECK_KEY`-Tests): automatischer Start-Check nur bei explizitem Opt-in, `CHECK_FAILED` bleibt beim Start still, manueller Check zeigt immer ein Ergebnis. |
| KI-Modellstatus/-verwaltung: vorhanden/fehlend/keine Netzwerkverbindung | ✅ | `tests/test_ai_model_status.py` (Cache-Verzeichnis fehlt/Datei fehlt/leer/vorhanden, `rembg`-nicht-verfügbar-Vorrang) sowie `tests/test_worker_controller.py`/`test_warmup.py` (Download-Fehlschlag bei Exception im Warmup = Offline-/Netzwerkfall, kooperativer Abbruch). |
| Installationsdialoge: Fortschritt/Abbruch/Fehler korrekt, kein fälschlich „installiert" | ✅ | `tests/test_ai_model_dialog.py` (Busy-Zustand, Abbrechen-Signal, Download-Erfolg/-Fehlschlag mit Retry) und `tests/test_ai_install_dialog.py` (Befehlsanzeige, „bereits installiert"-Hinweis nur bei tatsächlich vorhandenem rembg). |
| KI-Selbsttest + Paket-Start-Smoke des Release-Workflows grün | ✅ | Alle drei Build-Legs, s. „Build- und Start-Smokes" oben. |
| Logs: diagnostisch, keine Geheimnisse/unnötigen personenbezogenen Daten | ✅ | `app_update.py`/`ai_model_status.py` loggen nichts selbst (keine Log-Aufrufe); `workers.py` nutzt `logger.exception(context)` mit reinem Python-Traceback (Datei/Zeile/Code, keine Variablenwerte) – Update-Check ist ein unauthentifizierter GET gegen die öffentliche GitHub-API, es gibt kein Secret, das geloggt werden könnte. |

## Freigabe – vollständige Gate-Matrix

| # | Akzeptanzkriterium (#584) | Status | Beleg |
|---|---|---|---|
| 1 | `make pr-check` grün auf fixiertem Commit | ✅ | s. „Qualitäts-Gate" |
| 2 | Volle Testmatrix ohne übersprungene Pflichtprüfung grün | ✅ | s. „Qualitäts-Gate" |
| 3 | Keine P0/P1, keine ungeklärten regressiven P2 | ✅ | s. „Qualitäts-Gate" |
| 4 | Abweichungen lokal/CI dokumentiert | ✅ | s. „Qualitäts-Gate" |
| 5 | Getesteter SHA = fixierter Release-Commit | ✅ | s. „Kandidaten-Commit" (ersetzt `ce7ce32`, begründet) |
| 6 | Linux x86_64 AppImage gebaut + gestartet | ✅ | s. „Build- und Start-Smokes" |
| 7 | Linux aarch64 AppImage gebaut + in CI/Emulation geprüft | ✅ | native ARM-Runner, kein Emulationsvorbehalt nötig |
| 8 | Linux x86_64 `.deb` install/start/entfernen | ✅ | realer CI-Install-Smoke, s. „Realer CI-Install-Smoke" |
| 9 | Linux aarch64 `.deb` in Zielumgebung install/start | ✅ | realer CI-Install-Smoke auf nativer aarch64-Hardware, s. „Realer CI-Install-Smoke" |
| 10 | macOS DMG öffnen/installieren/starten | ⚠️ Teilweise | `.app`-Start auf echter Apple-Silicon-Hardware verifiziert; manueller DMG-Mount/Drag-Flow fehlt (Restrisiko) |
| 11 | Version/Architektur/Namensschema je Artefakt | ✅ | hart erzwungen durch Workflow-Assertions, s. „Artefakte" |
| 12 | SHA-256 + Dateigröße je Artefakt dokumentiert | ✅ | s. „Artefakte"-Tabelle |
| 13 | Keine Secrets/Tokens/Zertifikate/Entwicklerpfade/Testdaten | ✅ | s. „Sekret-/Pfad-Scan" |
| 14 | Laufzeitbibliotheken/Modelle enthalten oder Bezug dokumentiert; Offline-Verhalten definiert | ✅ | s. „Laufzeitbibliotheken/Modelle" |
| 15 | Wiederholte Builds funktional gleichwertig, Nicht-Determinismen dokumentiert | ✅ | Sieben unabhängige Läufe über den gesamten Sitzungsverlauf (`29486928558`, `29488035790`, `29490801906`, `29492642852`, `29493851030`, `29495305505`, `29506204774`) ergaben je durchgängig identische Namen/Versionen/Architekturen; einzige erwartete Abweichung sind die SHA-256-Werte zwischen *unterschiedlichen* Commits (Workflow-/Skript-Änderungen), nicht zwischen wiederholten Builds *desselben* Commits. |
| 16 | Start mit frischem Profil ohne Absturz | ✅ | s. „Funktions-Smokes" |
| 17 | Kernpfade Laden/Bearbeiten/Speichern/Exportieren | ✅ | s. „Funktions-Smokes" |
| 18 | Update-Prüfung Erfolg/Offline/Timeout/ungültige Antwort | ✅ | s. „Funktions-Smokes" |
| 19 | Manuell/automatisch respektiert Einstellungen | ✅ | s. „Funktions-Smokes" |
| 20 | KI-Modellstatus/-verwaltung vorhanden/fehlend/offline | ✅ | s. „Funktions-Smokes" |
| 21 | Installationsdialoge Fortschritt/Abbruch/Fehler | ✅ | s. „Funktions-Smokes" |
| 22 | KI-Selbsttest + Paket-Start-Smoke grün | ✅ | s. „Build- und Start-Smokes" |
| 23 | Logs diagnostisch, keine Geheimnisse/PII | ✅ | s. „Funktions-Smokes" |
| 24 | Gate-Matrix verknüpft jedes Kriterium mit Beleg | ✅ | dieses Dokument |
| 25 | Alle Blocker geschlossen oder begründet akzeptiert | ✅ | Restrisiken unten sind bewusst als Nicht-Blocker begründet |
| 26 | Eindeutige Go-/No-Go-Entscheidung mit Commit-SHA und fünf Artefakten | ✅ | s. „Go-/No-Go-Entscheidung" |

## Bekannte Restrisiken (bewusst akzeptiert)

- **Kein manueller „DMG mounten → in Applications ziehen"-Flow auf echter
  Mac-Hardware.** Der native macOS-Runner hat `hdiutil imageinfo` (gültiges
  Image) und einen echten Start des entpackten `.app` bestätigt; der reine
  Endnutzer-Interaktionsfluss (Icon doppelklicken, ins DMG-Fenster ziehen)
  ist nicht automatisierbar und wurde nicht auf echter Hardware nachvollzogen.
  **Risiko: niedrig** (identischer Mechanismus wie in v2.3.0/v2.4.x/v2.5.0
  bereits mehrfach veröffentlicht, keine Änderung an der DMG-Erzeugung in
  diesem Zyklus). Empfehlung: einmaliger manueller Smoke auf echter
  Mac-Hardware vor oder kurz nach dem `v2.6.0`-Tag, außerhalb dieses Gates
  nachholbar.
- **SHA-256-Prüfsummen stammen aus dem CI-Job-Log, nicht aus einem von dieser
  Sitzung heruntergeladenen und lokal nachgerechneten Artefakt** (Azure Blob
  Storage ist für diese Sitzung nicht erreichbar). Die Werte sind dennoch
  authentisch: `sha256sum`/`shasum` liefen auf demselben Runner, der die Datei
  gerade gebaut hat, unmittelbar nach dem Build, vor jedem Upload. Wer volles
  Vertrauen unabhängig von dieser Sitzung braucht, kann die Prüfsummen mit dem
  tatsächlich heruntergeladenen Release-Asset abgleichen (Standardvorgehen bei
  jedem Release).

Der zuvor hier gelistete aarch64-`.deb`-Install-Restrisiko ist mit Commit
`05936e5` geschlossen (nicht mehr nur Metadaten-Check, sondern realer
`apt`-Install/Start/`dpkg -r`-Zyklus auf nativer aarch64-Hardware in CI, s.
„Realer CI-Install-Smoke"). Keiner der beiden verbliebenen Punkte blockiert
die Freigabe – beide sind bewusst mit Risiko und empfohlener Nachhol-Maßnahme
akzeptiert (#584-Akzeptanzkriterium 25).

## Go-/No-Go-Entscheidung

**GO** für `v2.6.0` auf Commit `05936e5fec89585321e4508670123fb89ada8adb`.

Alle 26 Akzeptanzkriterien aus #584 sind erfüllt oder (bei den zwei oben
genannten Restrisiken) ausdrücklich mit Begründung und Risikoeinschätzung
akzeptiert. Fünf reale, plattformkorrekt benannte, versionsgleiche
(`2.6.0`) Artefakte wurden gebaut, mit SHA-256 dokumentiert, auf Secrets/
Entwicklerpfade gescannt (keine hochkonfidenten Funde) und auf allen drei
Ziel-Architekturen real installiert/gestartet/entfernt bzw. auf nativer
Hardware smoke-getestet. Lokale und CI-Full-Matrix-Gates sind grün
(Lauf [`29506204774`](https://github.com/NikolayDA/picture_helper/actions/runs/29506204774)).

### Hinweis für #585: SHA nach Merge/Squash

Dieses Gate ist an den exakten Commit `05936e5` gebunden – **nicht** an
„den PR" oder „den Branch". Ein Codex-Review auf PR #608 wies zurecht darauf
hin, dass ein Squash-Merge auf `main` einen **neuen** Commit-SHA erzeugt, der
nie selbst durch dieses Gate gelaufen ist; ein Tag auf diesem neuen SHA hätte
dann keine Fünf-Artefakte-Evidenz. Für #585 gilt daher zwingend genau eine der
beiden folgenden Optionen, bevor der `v2.6.0`-Tag gesetzt wird:

1. **Bevorzugt:** Nach dem Merge von PR #608 das komplette Gate (dieses
   Dokument) gegen den tatsächlichen `main`-Tip erneut ausführen –
   `workflow_dispatch` auf `release-linux.yml`, alle Schritte oben wiederholen
   (Kosten: ein weiterer CI-Lauf, ca. 10–15 Minuten). Da sich zwischen `05936e5`
   und dem Merge-Ergebnis inhaltlich nichts ändert (reiner Merge, kein weiterer
   Fix), ist ein identisches Ergebnis zu erwarten; erst nach Bestätigung wird
   der Tag auf diesen neuen SHA gesetzt und dieses Dokument mit dem neuen SHA/
   Lauf aktualisiert.
2. **Alternative, falls #585 keinen erneuten Gate-Lauf vorsieht:** Den
   `v2.6.0`-Tag direkt auf `05936e5fec89585321e4508670123fb89ada8adb` setzen
   (git erlaubt das Taggen jedes beliebigen erreichbaren Commits, nicht nur
   des `main`-Tips) statt auf den Merge-Ergebnis-SHA – dann bleibt die
   Evidenz in diesem Dokument exakt für den getaggten Commit gültig, ohne
   erneuten Lauf.

In beiden Fällen gilt unverändert die bestehende Regel dieses Dokuments:
ändert sich der zu veröffentlichende Commit gegenüber dem hier dokumentierten
`05936e5` aus einem anderen Grund (z. B. ein weiterer Blocker-Fix nach diesem
Dokument), muss das komplette Gate erneut ausgeführt werden.

Dieses Gate blockiert #585 (Tag + Veröffentlichung) damit nicht mehr, sofern
eine der beiden obigen Optionen beim Tag-Setzen tatsächlich befolgt wird.
