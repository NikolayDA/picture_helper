# Release-Abnahme-Automatisierung: Betrieb der Self-hosted Runner

Betriebsanleitung zu Epic #639: Der Workflow
[`release-abnahme.yml`](../.github/workflows/release-abnahme.yml) sammelt die
Release-Abnahme-Evidenz für die
[versionierte Checkliste](RELEASE_ACCEPTANCE_CHECKLIST.md) (#595)
automatisiert auf Self-hosted GitHub-Actions-Runnern. Architektur- und
Sicherheitsentscheidungen:
[ADR-2026-release-abnahme-automatisierung.md](history/ADR-2026-release-abnahme-automatisierung.md).
Der byteidentische Build→Abnahme→Publish-Vertrag ist in
[ADR-2026-release-manifest-publish.md](history/ADR-2026-release-manifest-publish.md)
festgelegt.

Der kanonische Build→Abnahme→Publish-Ablauf steht ausschließlich im
[Release-Runbook](RELEASE_PROCESS.md). `PACKAGING_SMOKE.md` liefert die
Hardware-Kommandos; dieses Dokument beschreibt nur Betrieb und technisches
Verhalten der selbst gehosteten Runner.

## 1. Runner-Übersicht

| Plattform | Gerät | Labels | Status |
|---|---|---|---|
| macOS arm64 | MacBook (Apple M3) | `self-hosted`, `macOS`, `ARM64` | aktiv geplant |
| Linux aarch64 | Raspberry Pi 5 (Debian 12) | `self-hosted`, `Linux`, `ARM64` | aktiv geplant |
| Linux x86_64 | – | `self-hosted`, `Linux`, `X64` | **pausiert** (siehe §5) |

Voraussetzungen je Gerät: `python3` (≥ 3.10) **mit venv-Modul** im PATH
(Debian/Pi: `python3-venv`), laufende grafische Sitzung (macOS: angemeldeter
Benutzer; Pi: X11-/Wayland-Session), genug freier Speicher für die
Release-Artefakte (≥ 2 GB) und Netzzugang zu `api.github.com`/`github.com`.
Der Workflow legt seine PyQt6-Umgebung selbst als venv an (die GL-/Retina-
Probes brauchen PyQt6) – es muss **kein** PyQt6 systemweit installiert sein;
auf dem Pi müssen aber die Qt-Systembibliotheken (`libGL`, xcb-Plugins der
laufenden Desktop-Session) vorhanden sein. Für den **`.deb`-Smoke** braucht der
Linux-Runner-Benutzer ein eng begrenztes `sudo` – nur für
`apt-get install`/`dpkg -r` von `bgremover` (siehe §3), analog zum
`release-linux.yml`-Installationszyklus.

## 2. Runner registrieren (je Gerät ca. 5 Minuten)

1. GitHub → Repository → **Settings → Actions → Runners → New self-hosted
   runner**, Plattform wählen (macOS arm64 bzw. Linux ARM64).
2. Die dort angezeigten Befehle auf dem Gerät ausführen (Download, `config.sh`
   mit dem angezeigten Token). Bei der Label-Abfrage die Standard-Labels
   unverändert übernehmen – der Workflow adressiert genau
   `[self-hosted, macOS, ARM64]` bzw. `[self-hosted, Linux, ARM64]`.
3. **Als Dienst einrichten**, damit der Runner Neustarts überlebt:
   - Linux (Pi): `sudo ./svc.sh install && sudo ./svc.sh start` (systemd).
   - macOS: als der angemeldete dedizierte Runner-Benutzer
     `./svc.sh install && ./svc.sh start` (LaunchAgent; Gerät darf für
     Abnahme-Läufe nicht im Ruhezustand sein).
4. Sichtprüfung: Der Runner erscheint unter Settings → Actions → Runners als
   „Idle".

### 2.1 Grafische Sitzung an den Dienst durchreichen (Pflicht)

Ein „Idle"-Runner allein reicht nicht: Qt/Cocoa/X11/Wayland und der GPU-Treiber
müssen aus dem Runner-Prozess erreichbar sein. Der Workflow prüft dies vor der
Installation des Test-venv und bricht mit einer konkreten Fehlermeldung ab,
statt versehentlich einen Offscreen-Lauf als Hardware-Nachweis zu werten.

**macOS:** `svc.sh` muss vom aktuell angemeldeten Runner-Benutzer ausgeführt
werden. Der erzeugte Dienst muss unter
`~/Library/LaunchAgents/actions.runner.*.service.plist` liegen, nicht als
systemweiter LaunchDaemon. Prüfen:

```sh
cat .service
./svc.sh status
printf 'Runner: %s; Konsole: %s\n' "$(id -un)" "$(stat -f '%Su' /dev/console)"
```

Runner- und Konsolenbenutzer müssen identisch sein. Diese Form entspricht dem
von GitHub [dokumentierten macOS-LaunchAgent](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/configure-the-application?platform=mac);
der Workflow prüft dieselbe Bedingung nochmals unmittelbar vor dem nativen
Qt-Lauf.

**Linux:** Der systemd-Dienst läuft als derselbe dedizierte Benutzer, der an
der Desktop-Sitzung angemeldet ist. Zuerst in einem Terminal **dieser
grafischen Sitzung** die tatsächlichen Werte erfassen:

```sh
printf 'DISPLAY=%s\nWAYLAND_DISPLAY=%s\nXDG_RUNTIME_DIR=%s\nXAUTHORITY=%s\n' \
  "${DISPLAY:-}" "${WAYLAND_DISPLAY:-}" "${XDG_RUNTIME_DIR:-}" "${XAUTHORITY:-}"
id -u
```

Dann den von `svc.sh` erzeugten Unit-Namen mit `cat .service` ermitteln und
per `sudo systemctl edit <actions.runner.…service>` ergänzen. Für X11 zum
Beispiel (Werte an die Ausgabe oben anpassen):

```ini
[Service]
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/runner/.Xauthority
```

Für Wayland zum Beispiel (`1001` und `wayland-0` anpassen):

```ini
[Service]
Environment=XDG_RUNTIME_DIR=/run/user/1001
Environment=WAYLAND_DISPLAY=wayland-0
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1001/bus
```

Danach `sudo systemctl daemon-reload`, `sudo ./svc.sh stop` und
`sudo ./svc.sh start`. Mit `sudo systemctl show <unit> -p User -p Environment`
prüfen, dass Benutzer und Werte stimmen. Mindestens `DISPLAY` oder
`WAYLAND_DISPLAY` muss gesetzt sein; bei Wayland ist `XDG_RUNTIME_DIR`
zusätzlich Pflicht. Die nativen Workflow-Schritte entfernen außerdem bewusst
ein eventuell geerbtes `QT_QPA_PLATFORM`, damit Qt das Backend dieser Sitzung
wählt.

## 3. Sicherheits-Checkliste (vor Inbetriebnahme, je Runner)

- [ ] Runner ist **nur für dieses Repository** registriert (kein Org-Sharing).
- [ ] Der Abnahme-Workflow ist der einzige, der Self-hosted-Labels anspricht;
      er läuft ausschließlich über `workflow_dispatch` – nie auf Push-, PR-
      oder Fork-Events (erzwungen durch
      `tests/test_release_abnahme_workflow.py`).
- [ ] Runner läuft unter einem **dedizierten Benutzer** ohne Zugriff auf
      persönliche Daten/Schlüssel.
- [ ] Linux-Runner (für den `.deb`-Smoke): **eng begrenztes** `sudo` nur für
      die Paketkommandos, z. B. per `/etc/sudoers.d/abnahme`:
      `runner ALL=(root) NOPASSWD: /usr/bin/apt-get install *, /usr/bin/dpkg -r bgremover`.
      Kein allgemeines passwortloses `sudo`. macOS braucht kein `sudo` (DMG
      wird read-only gemountet).
- [ ] Repository-Einstellung geprüft: Actions-Ausführung für Fork-PRs
      erfordert Freigabe (Settings → Actions → General).
- [ ] Ausreichend freier Speicher; das Arbeitsverzeichnis des Runners liegt
      nicht in einem synchronisierten Ordner (iCloud/Nextcloud o. Ä.).

## 4. Technisches Verhalten des Abnahme-Jobs

Startreihenfolge, Inputs, erwartete Ergebnisse und Wiederanlauf stehen in
Schritt 3 bis 6 des [Release-Runbooks](RELEASE_PROCESS.md). Für Diagnose und
Runnerpflege sind die Eingaben des Abnahme-Jobs:

- **`run_id`**: die notierte Run-ID des erfolgreichen
  `release-linux.yml`-Kandidatenlaufs. Andere Workflows, fehlgeschlagene Runs
  oder ein abweichender Commit werden vor den Hardware-Jobs abgewiesen.
- **`platforms`**: `alle` (Standard) oder gezielt `macos-arm64` /
  `linux-arm64` / `linux-x86_64` (letzteres nur bei aktivierter Variable aus
  §5).
- **`dry_run`**: überspringt den Auswertungs-Job (Vision-Vorbewertung +
  Abschlussmatrix, #646). Die Plattform-Jobs laufen weiterhin und laden ihre
  Evidenz hoch; nur die zusammenfassende Matrix und der Issue-Kommentar
  entfallen (nützlich für reine Runner-/Smoke-Prüfläufe).
- **`target_issue`**: positive Issue-Nummer für den Kommentar mit der
  Abschlussmatrix; Standard ist `595`. Ungültige Werte brechen nur den
  nachgelagerten Kommentar-Schritt kontrolliert ab.

**Preflight und Runner-Watchdog (#915).** Vor den schweren Plattform-Jobs
läuft je angeforderter Plattform ein Preflight-Job
(`scripts/abnahme_preflight.py`) auf dem Self-hosted Runner: grafische
Sitzung, ladbare GL-Bibliothek, freier Speicher (≥ 2 GB), `python3` ≥ 3.10
mit venv, Netzzugang zu `api.github.com` und unter Linux das eng begrenzte
`sudo` für den `.deb`-Zyklus (§3) — bewusst ohne venv-Installation, in
Sekunden; die vollständige Qt-/GL-Probe bleibt Teil der Plattform-Jobs.
Parallel überwacht ein GitHub-hosted Watchdog (`scripts/abnahme_watchdog.py`)
die Queue: Steht ein Preflight nach zehn Minuten ohne Runner-Zuweisung,
beendet er den gesamten Lauf per **force-cancel** mit einer Fehlermeldung,
die die wartende Plattform und den Abhilfeweg benennt — GitHub selbst bräche
erst nach 24 Stunden ab, und `timeout-minutes` zählt erst ab Jobstart.
Force-cancel statt Cancel, weil ein regulärer Abbruch die
`!cancelled()`-Aggregation weiterlaufen ließe (die missverständliche Matrix
des abgebrochenen Laufs 33071408111). Das Schreibrecht zum Run-Abbruch trägt
im gesamten Workflow nur der Watchdog; ohne erfolgreiche Beobachtung
(API-Fehler) fällt er bewusst kein Verdikt. Ein manueller Probelauf nur zur
Runner-Prüfung vor der bindenden Abnahme ist damit nicht mehr nötig; ein
Watchdog-Abbruch ist ein reiner Runnerfehler im Sinne der
Wiederanlaufmatrix des Runbooks.

Ein GitHub-hosted Vorjob prüft zuerst Run-ID, Workflow-Pfad, Abschlussstatus,
Quell-Commit, Freeze-Provenienz, die drei Actions-Artefaktreferenzen und die
exakte Menge aus zwei AppImages, zwei DEBs und einem DMG. Jeder Plattform-Job
lädt danach nur die passenden Dateien aus dieser Build-Run-ID, berechnet ihren
SHA256 und lädt sein Ergebnis als Workflow-Artefakt
`abnahme-<plattform>-<run_attempt>` hoch
(`evidenz.json` + `manifest.md`, Pflichtfelder im
[ADR](history/ADR-2026-release-abnahme-automatisierung.md)). Der SHA-256 des
entpackten Release-Files wird zum verbindlichen Manifestwert und muss später
mit den veröffentlichten Bytes übereinstimmen. Der Smoke selbst belegt Start ohne
Crash/Fork-Bomb/Hänger, GL-Provenance der Runner-Hardware, `.deb`-Hygiene und
(macOS) Retina. Innerhalb desselben Smoke-Schritts starten AppImage,
installiertes `.deb`-AppImage und das aus dem DMG kopierte `.app`-Bundle
jeweils ein zweites Mal – über
`smoke_launch.py --native` (kein erzwungenes `offscreen`) mit dem
Automationshook `BGREMOVER_SCREENSHOT_3D` – und liefert Screenshot samt
GL-Provenance-Sidecar direkt aus dem **laufenden gepackten Prozess** (#648):
Beispielbild synthetisieren → Höhenkarte erzeugen → 3D-Vorschau aktivieren →
Azimut-, Elevations- und Standardqualitäts-Regler gemeinsam in den Scroll-
Viewport bringen und ihre vollständige Geometrie prüfen → Fenster-Grab,
sobald der Viewer `ready` ist. Schema 2 der Sidecar verlangt dafür
`preview3d_controls_visible=true` und die drei Namen in
`preview3d_visible_controls`; fehlt der Nachweis, scheitert der native Smoke
für AppImage, installiertes `.deb` und DMG fail-closed. Ein Software-Renderer
lässt den Nachweis ebenfalls fehlschlagen (dasselbe Gate wie die Runner-
Hardware-Provenance oben); Screenshot und Sidecar landen mit
artefaktklassenspezifischen Namen unter `screenshots/` in der Plattform-
Evidenz. Danach führt derselbe
Hardware-Job die native
MainWindow-E2E-Regression aus (Bild öffnen → HEIGHT → 3D-`ready` samt
hochgeladenem Mesh/gerendertem Frame → Undo/Redo → Save/Open → erneut
3D-`ready`/Fallback aus der neu geladenen HEIGHT-Ebene) und schreibt
`e2e-evidenz.json` – dieser Nachweis läuft weiterhin aus dem **Source-
Checkout** heraus (`pytest` gegen das installierte `bgremover`-Paket), nicht
aus dem gepackten Artefakt; genau diese Lücke schließt der neue native
3D-Screenshot oben. Seit #685-Review gilt dieselbe Einschränkung nicht mehr für
den EufyMake-Export- und den 2.7.0-Projekt-Öffnen-Nachweis: derselbe
Smoke-Schritt startet jede Artefaktklasse ein drittes Mal mit dem
Automationshook `BGREMOVER_ACCEPTANCE_EXTRA` (`bgremover.acceptance_smoke`,
kein GL nötig) und schreibt `acceptance_extra_<klasse>.json` direkt aus dem
gepackten Prozess. Seit #686 prüft derselbe Hook zusätzlich die im
Fenstertitel **sichtbare Produktversion** gegen den Sollwert aus dem
Artefaktdateinamen (`BGREMOVER_ACCEPTANCE_EXTRA_VERSION`, gesetzt aus
`release_abnahme.version_from_artifact_name`) und speichert eine
**kontrollierte Projekt-Kopie** über den echten `save_project`-Pfad, lädt sie
neu und vergleicht sie wertgleich – der `.bgrproj`-Schreibpfad, den der
EufyMake-Export nicht abdeckt. Die Live-GL-Suite rendert mit dem echten Viewer-Shaderpfad
die 1-/16-/40-MP-Szenarien jeweils dreimal. Sie speichert die Rohmessungen,
verdichtet Zeitmetriken per Median und meldet für `gl_peak_mb` die größte
Prozess-RSS-High-Water-Mark inklusive Qt-/Treiber-Allokationen. Alle fünf
GL-Metriken plus Renderer-Provenance landen unter `preview3d-live/` (ebenfalls
aus dem Source-Checkout).

Nach den Plattform-Jobs läuft (außer bei `dry_run`) der **Aggregations-Job**
(#646): Er lädt alle `abnahme-*`-Artefakte, bewertet aufgefundene Screenshots
über die Claude-Vision-API vor (`abnahme_vision_check.py`, fail-safe – ohne
`ANTHROPIC_VISION_API_KEY` bleibt jedes Kriterium `unbewertet` und blockiert nie;
seit #817 gilt das auch für die Ausgabe: fehlt das Evidenzverzeichnis, weil eine
Plattform-Phase abgebrochen ist, wird das Zielverzeichnis angelegt und eine leere
Verdiktliste geschrieben, statt den Aggregations-Job mitzureißen),
installiert dafür das gepinnte SDK in einem eigenen kurzlebigen venv (auch ein
Installationsfehler bleibt fail-safe und verhindert die Matrix nicht),
erzeugt daraus die **Abschlussmatrix** (`abnahme_aggregate.py`: je Kriterium
erfüllt/fehlgeschlagen/fehlt/pausiert/unbewertet mit Nachweis,
GL-Provenance, Gerät/OS (aus den Umgebungs-Pflichtfeldern der Evidenz),
Datum, Testperson (`automatisiert (kein manueller Tester)`, #685-Review –
der Lauf ist vollautomatisiert) und einem Link auf den erzeugenden
Workflow-Lauf) und postet sie als Kommentar an das Dispatch-Eingabefeld
`target_issue` (Standard: #595). Pro aktiver
Plattform erscheinen Hardware-Smoke, nativer Source-E2E und Live-GL-
Performance als getrennte Pflichtzeilen; fehlende/inkonsistente Evidenz kann
dadurch nicht von einem anderen Kriterium verdeckt werden. Der pausierte
x86_64-Pfad erscheint explizit als „pausiert", fehlende Evidenz als „fehlt" –
keine stillen Lücken. Eine Matrix mit blockierenden Lücken (fehlgeschlagener,
unvollständiger oder bewusster Einzelplattform-Lauf, z. B. der
Update-Nachweis aus Runbook-Schritt 9)
kennzeichnet sich seit #915 selbst in Titel und Einleitung als „Diagnose –
kein Abnahmeergebnis"; bei einem **abgebrochenen** Lauf entfällt der
Kommentar ganz (`!cancelled()` statt `always()` am Aggregations-Job).
Die Vision-Vorbewertung ist **beratend**:
`nicht_erfuellt` markiert eine Zeile als fehlgeschlagen, aber die Go-/No-Go-
Entscheidung bleibt der menschliche Schritt. Sind alle technischen
Pflichtzeilen erfüllt (Linux x86_64 darf entsprechend §5 explizit pausiert
sein), erzeugt derselbe Job zusätzlich
`release-approval-manifest-<run_attempt>`. Dieses unveränderliche
Actions-Artefakt enthält Build-/Abnahme-Run, Quell-SHA, Version/Tag,
Freeze-Provenienzreferenz, Plattformstatus und exakt fünf Datei-SHA-256. Den
Manifestnamen und die Abnahme-Run-ID für §4.1 notieren. Bei `dry_run`, einer
Teilplattform-Auswahl oder einer blockierenden Lücke entsteht kein Manifest.

### 4.1 Freigabemanifest und Veröffentlichung

Der Aggregations-Job erzeugt zusätzlich zur Abschlussmatrix das unveränderliche
Freigabemanifest und eine daraus extrahierbare Release-Instanz. Beide pinnen die
Checklisten-Version, ihren Dateihash und den Kandidaten-Commit. Veröffentlichung,
Wiederholung, Teilzustände und Rollback sind ausschließlich in Schritt 6 bis 9
des [Release-Runbooks](RELEASE_PROCESS.md) beschrieben.

**Ref-Bindung des Aggregations-Jobs (#829, Befund 2):** Keiner der
`actions/checkout`-Schritte in `release-abnahme.yml` setzt `ref:` – auch der
Aggregations-Job läuft damit auf dem Ref, gegen den der Workflow dispatcht
wurde, genau wie die evidenzerzeugenden Plattform-Jobs. Das ist für Letztere
beabsichtigt und Kern des Beweisketten-Modells (#641): Evidenz muss vom
exakt geprüften Kandidaten-Commit stammen. Für den Aggregations-Job – der
Evidenz nur **auswertet**, keine erzeugt – hat das eine Nebenwirkung: Ein
späterer Nachlauf desselben Kandidaten (z. B. Runbook-Schritt 9) führt
`abnahme_vision_check.py`/`abnahme_aggregate.py` weiterhin in der Fassung
aus, die zum Kandidatenzeitpunkt in `main` lag – ein danach auf `main`
gemergter Fix an diesen Auswertungsskripten wirkt für diese Kandidatenlinie
nicht rückwirkend, sondern erst ab dem nächsten Kandidaten, der ihn selbst
mitbaut. Das ist eine bewusst in Kauf genommene Eigenschaft, keine Lücke:
Sie hält die Auswertung reproduzierbar zum Kandidatenstand, auf Kosten davon,
dass ein Auswertungsfehler für die Lebensdauer der Kandidatenlinie
eingefroren bleibt.

Repository-Variablen (Settings → Secrets and variables → Actions →
Variables):

| Variable | Wirkung |
|---|---|
| `ABNAHME_X86_64_ENABLED` | `true` aktiviert den Linux-x86_64-Job; jeder andere Wert (oder nicht gesetzt) lässt ihn pausiert |

Optionales Repository-Secret (Settings → Secrets and variables → Actions →
Secrets):

| Secret | Wirkung |
|---|---|
| `ANTHROPIC_VISION_API_KEY` | aktiviert die Vision-Vorbewertung der Screenshots; fehlt es, bleibt die Screenshot-Zeile `unbewertet` (fail-safe, kein Fehler). Bewusst getrennt vom Secret der interaktiven Claude-Workflows (`CLAUDE_CODE_OAUTH_TOKEN`, #656) – nur der Aggregations-Job liest dieses Secret |

#### 4.1.1 Öffentlicher Download-Nachweis `PUBLIC-DOWNLOAD-01` (#916)

`release-publish.yml` trägt nach dem `publish`-Job einen zweiten Job
**Öffentlicher Download-Nachweis (PUBLIC-DOWNLOAD-01)**. Er läuft
GitHub-hosted und erbringt maschinell, was bei v2.9.0 rund sieben Stunden nach
dem Publish von Hand nachgeholt wurde (#881).

- **Warum erst nach dem Publish:** Der Verifikationsschritt im `publish`-Job
  lädt die Assets **vor** der Veröffentlichung authentifiziert aus dem Draft.
  Draft-Assets sind anonym gar nicht erreichbar; dieser Pfad belegt den
  Anwenderweg also nie. Der Nachweis läuft deshalb nach
  `gh release edit --draft=false`.
- **Anonym, nachweislich:** `scripts/public_download_check.py` kennt keinen
  Token-Parameter — weder die Release-Metadaten noch die Nutzlast tragen einen
  `Authorization`-Header. Der Job setzt kein `GH_TOKEN` im Environment des
  Download-Schritts und prüft das mit einer Guard-Zeile im Joblog. Ein
  versehentlich privat gebliebenes Release fällt damit auf.
- **Referenz bleibt das Freigabemanifest,** nicht der von GitHub gemeldete
  Asset-Digest; sonst würde dieselbe Quelle zweimal befragt. Das bindende
  Verdikt liefert derselbe Aufruf `release_contract.py verify-artifacts`, mit
  dem der `publish`-Job die hochgeladenen Bytes geprüft hat.
- **Evidenz:** `public-download-report.json` (Schema 1,
  `release-public-download`) hält je Datei Name, URL, Größe, SHA-256,
  Zeitstempel und Ergebnis sowie das Gesamtverdikt; er wird 90 Tage als
  Artefakt `public-download-report-<run_attempt>` gesichert, als Job-Summary
  gerendert und bei gesetztem `target_issue` als Issue-Kommentar gepostet.
  Auch ein Fehlschlag wird geschrieben — die Evidenz eines Incidents darf nicht
  nur im Joblog stehen.
- **Fail-closed:** Hash-Abweichung, fehlendes oder zusätzliches Asset und jeder
  HTTP-Fehler lassen den Lauf sichtbar rot enden. Nur transiente Antworten
  (429/5xx, Netzabbruch) werden höchstens dreimal wiederholt; eine 404 oder ein
  Hashunterschied nie; eine abgeschnittene Antwort (`IncompleteRead`) zählt als
  transient. Das Skript führt zusätzlich ein eigenes Zeitbudget und bricht von
  innen ab, bevor das Job-Zeitlimit greift — ein vom Runner gekillter Schritt
  schriebe keinen Bericht, und genau dann fehlte die Evidenz. Der Incident-Pfad
  steht in Schritt 9 des [Release-Runbooks](RELEASE_PROCESS.md).
- **Bekannte Grenze:** Auch die Release-Metadaten werden anonym geholt — erst
  das belegt die öffentliche Sichtbarkeit. Dafür zählt dieser eine Aufruf gegen
  das unauthentifizierte API-Kontingent (60/h je Quell-IP); auf einem geteilten
  GitHub-Runner ist ein Treffer unwahrscheinlich, aber möglich. Der Fehlertext
  nennt deshalb beide Ursachen (nicht öffentlich vs. Kontingent), und der
  Wiederanlauf ist ein erneuter Publish-Lauf mit denselben gebundenen Inputs —
  er ist idempotent und meldet `already-complete`.
- **Berechtigung:** `issues: write` trägt ausschließlich dieser Job; der
  `publish`-Job bleibt bei `contents: write` und `actions: read`.

### 4.2 Post-Release-Update-Nachweis (#748/#917)

`UPDATE-LINUX-ARM-01` und `UPDATE-MACOS-ARM-01` sind die einzigen **Post-Release**-Kriterien. Vor dem Tag kann kein
Vorgängerartefakt die neue Version am produktiven Endpunkt `/releases/latest`
sehen; als Pre-Release-Gate wäre der Nachweis logisch unmöglich. Er läuft
deshalb **nach** Schritt 8 des [Release-Runbooks](RELEASE_PROCESS.md), blockiert
den Tag nicht und schließt die Veröffentlichung fachlich ab.

**Aufruf.** Denselben `release-abnahme.yml`-Dispatch erneut starten, diesmal mit
gesetztem `predecessor_tag`:

| Eingabe | Wert |
|---|---|
| `run_id` | Run-ID **desselben** `release-linux.yml`-Kandidatenlaufs wie in der Hardware-Abnahme |
| `platforms` | `alle` für beide Kriterien in einem Lauf; `linux-arm64` bzw. `macos-arm64` für einen einzelnen Kanal (das jeweils andere Kriterium bleibt dann `PENDING`) |
| `predecessor_tag` | Tag des zuletzt veröffentlichten Vorgängers, z. B. `v2.9.0` |

Leerer `predecessor_tag` lässt den Nachweis aus; er bleibt dann `PENDING` und
wird nie als `PASS` fabriziert.

**Was der Lauf tut.** `release_abnahme.py --release-tag` lädt die Artefakte des
Vorgängers anonym über `browser_download_url` — derselbe öffentliche
Anwenderpfad wie in `PUBLIC-DOWNLOAD-01` — und schreibt Hash und Herkunft in ein
eigenes Evidenzverzeichnis. Wie `abnahme_smoke.py` daraus einen Nachweis macht,
unterscheidet sich je Plattform — bewertet wird danach identisch:

| Plattform | Weg ins gepackte Artefakt |
|---|---|
| Linux arm64 | beide AppImages entpacken und `scripts/update_probe_cli.py` **unter dem darin gebündelten CPython** aufrufen; funktioniert rückwirkend gegen jedes veröffentlichte Artefakt, weil nur `bgremover.app_update`/`bgremover._version` importiert werden |
| macOS arm64 | DMG mounten, App-Bundle in eine Wegwerfkopie je Rolle, Binary mit `BGREMOVER_UPDATE_CHECK_PROBE=<Ziel-JSON>` starten; der Hook läuft in `bgremover/app.py` **vor** `QApplication` und existiert erst ab v2.7.3 |

In beiden Fällen kommt der geprüfte Code aus dem ausgelieferten Bundle statt aus
dem Checkout — genau der Punkt, an dem #740 zuvor danebenlag. Der macOS-Start
läuft bewusst **ohne** `--native` durch `smoke_launch.py`: Fehlt der Hook wider
Erwarten, beendet `BGREMOVER_SMOKE_TEST` die dann startende GUI nach dem ersten
Event-Loop-Tick, statt den Job bis zum Zeitlimit hängen zu lassen.

**Bewertet wird in dieser Reihenfolge**, der erste Verstoß gewinnt:

1. `CHECK_FAILED` — eigener harter Fehlerzustand, nie „kein Update".
2. Die vom laufenden Artefakt **selbst** gemeldete Version muss zu seiner
   Herkunft passen (Vorgänger → Release-Tag, Kandidat → Kandidatenversion).
   Erst damit steht fest, dass wirklich das vorgesehene Bundle lief.
3. Der Status: Vorgänger `UPDATE_AVAILABLE`, Kandidat `UP_TO_DATE`.
4. Die vom Vorgänger gemeldete `latest_version` muss exakt die neue
   Kandidatenversion sein.

Tragen beide Rollen dieselbe Version, bricht der Nachweis ab — er prüfte sonst
ein Release gegen sich selbst. `--candidate-version` ist mit
`--predecessor-evidence-dir` Pflicht.

**Evidenz** unter `update_check/` im Plattform-Artefakt:

| Datei | Inhalt |
|---|---|
| `predecessor.json` / `current.json` | rohe Sonden-Nutzlast je Rolle |
| `update_check.json` | zusammenfassender Nachweis je Rolle: Artefaktname, Quelle (`release-tag`/`run-id`), SHA-256, Digest-Bestätigung, Plattform, erwartete und gemeldete Ausgangsversion, Antwortstatus, Zielversion, Befund |

Dieselben Angaben stehen als `[update-check] …`-Zeilen im Joblog, weil der
Runner die Ausgabe der Teilschritte abfängt. Die Evidenz enthält ausschließlich
öffentlich Bekanntes — kein Token, keine Header.

**Reichweite und Grenzen.**

- `UPDATE-LINUX-ARM-01` wird von der **Linux-arm64-AppImage** getragen. Das
  `.deb` installiert per `packaging/linux/build_deb.sh` genau dieselbe AppImage
  nach `/opt/BgRemover/BgRemover.AppImage`; ein zweiter Durchlauf prüfte
  dieselben Bytes und ist deshalb bewusst nicht verdrahtet. Seit #917 steht
  diese Begründung im Kriteriumstext der Checkliste statt nur hier — die
  Deklaration behauptet damit nicht mehr, als der Lauf erbringt.
- `UPDATE-MACOS-ARM-01` braucht einen **Vorgänger ≥ v2.7.3**: Erst ab da bringt
  ein Release den In-Prozess-Hook mit. Ein älterer Vorgänger führt zum benannten
  Befund `HOOK_FEHLT` — kein leeres Ergebnis und keine kaputte Sonde, sondern
  die dokumentierte historische Grenze. Das Kriterium bleibt dann `PENDING`.
  Rückwirkend ist die Lücke nicht schließbar: PyInstaller bettet den Bytecode in
  den Bootloader ein und liefert keinen generisch aufrufbaren Interpreter.
- Der Vorgänger muss ein **öffentliches** Release sein; ein versehentlich
  privates fällt beim anonymen Download auf.
- Steht kein Runner bereit, ersetzt die manuelle Prozedur in
  [`PACKAGING_SMOKE.md`](PACKAGING_SMOKE.md) §4.1 den Workflow-Lauf.

**Fehlschlag.** Kein stiller Wiederanlauf: Ein fehlgeschlagenes Update-Kriterium
ist ein Incident nach Schritt 9 des Runbooks und löst den dort beschriebenen
Rollback-/Hotfix-Entscheid aus.

## 5. Pausiert: Linux x86_64 (GPU)

**Entscheidung vom 2026-07-20:** Es besteht bis auf weiteres kein Zugang zu
einem Linux-x86_64-Rechner mit echter GPU und X11-/Wayland-Session. Der
x86_64-Job ist im Workflow vollständig definiert, wird aber über
`ABNAHME_X86_64_ENABLED` deaktiviert; ein Ersatz-Job meldet die Pause in jedem
Lauf sichtbar, statt still zu fehlen. Für Release-Entscheidungen gilt der
x86_64-Hardware-Smoke solange als **offen deklariert**, nicht als erfüllt –
die Abschlussmatrix (#646) führt ihn als „pausiert, nicht erfüllt".

Wiederaufnahme-Kriterien (in dieser Reihenfolge):

1. Linux-x86_64-Gerät mit echter GPU und grafischer Session als Runner
   registrieren (§2, Labels `self-hosted`, `Linux`, `X64`) und §3 abhaken.
2. Repository-Variable `ABNAHME_X86_64_ENABLED` auf `true` setzen.
3. Einen vollen Abnahme-Lauf starten; der x86_64-Job muss inklusive
   GL-Provenance, nativem Source-E2E und Live-GL-Suite (echter
   Hardware-Renderer, kein llvmpipe) grün durchlaufen.

Es ist keine Code-Änderung nötig.

## 6. Wartung

- Self-hosted Runner aktualisieren sich selbst; bei Problemen Dienst neu
  starten (`./svc.sh stop && ./svc.sh start`).
- Nach Betriebssystem-Updates (Pi: `apt upgrade`, macOS: Systemupdate) einen
  Dry-Run des Abnahme-Workflows ausführen, bevor ein echtes Release ansteht.
- Runner, die länger offline sind, entfernt GitHub nach 30 Tagen automatisch –
  dann §2 wiederholen.
