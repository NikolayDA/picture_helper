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

Für den Neuaufbau eines **frisch installierten** Geräts von Null (Homebrew/apt,
Checkout, venv, Registrierung, Dienst, Härtung, Heartbeat-Nachweis) gibt es das
Copy-Paste-Kochbuch [`RUNNER_SETUP.md`](RUNNER_SETUP.md) (#946). Es konsolidiert
die Rezepte aus §2, §3, §6 und §7; verbindlich bleiben diese Abschnitte und
`scripts/abnahme_preflight.py`.

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

**Sleep-Schutz und Dienst-Neustart (macOS, #921).** Ein schlafender Mac nimmt
keine Jobs an – der Runner steht dann als „Idle" in der Oberfläche, während
die Warteschlange wächst. Zwei Einstellungen sichern die Bereitschaft; beide
prüft der Preflight (`scripts/abnahme_preflight.py`) und der tägliche
Heartbeat (§7) setzt sie durch:

```sh
# Am Netzteil weder System- noch Display-Schlaf. Der Display-Schlaf zählt mit:
# die Abnahme erzeugt native Screenshots (SCREEN-*), ein dunkles Display
# entwertet genau diesen Nachweis.
sudo pmset -c sleep 0 displaysleep 0
# Nur für einen zugeklappt betriebenen MacBook zusätzlich:
sudo pmset -a disablesleep 1
```

Alternative für Geräte, die sonst schlafen sollen: den Runner-Dienst in einen
`caffeinate`-Wrapper hängen (`caffeinate -dimsu`). Der Preflight akzeptiert
beides – ein dauerhaftes `pmset`-Profil **oder** aktive Assertions.

**Prüfkommando** (beide Zeilen müssen `0` zeigen bzw. die Assertions `1`):

```sh
pmset -g custom | awk '/^AC Power:/{ac=1} ac && /(^| )(sleep|displaysleep|disablesleep) /'
pmset -g assertions | grep -E 'PreventUserIdle(System|Display)Sleep'
```

Der LaunchAgent aus `svc.sh install` startet den Runner **nicht** von selbst
neu: Die offizielle Vorlage (`actions.runner.plist.template` in
`actions/runner`) setzt nur `RunAtLoad`, kein `KeepAlive`. Ein abgestürzter
Dienst bleibt damit unten, bis sich jemand am Gerät anmeldet. Einmalig
ergänzen (und nach jedem `svc.sh install` erneut, weil die Datei dabei neu
erzeugt wird):

```sh
plist=~/Library/LaunchAgents/$(basename "$(cat .service)")
/usr/libexec/PlistBuddy -c 'Add :KeepAlive bool true' "$plist" \
  || /usr/libexec/PlistBuddy -c 'Set :KeepAlive true' "$plist"
./svc.sh stop && ./svc.sh start
/usr/libexec/PlistBuddy -c 'Print :KeepAlive' "$plist"   # muss "true" sein
```

### 2.2 Neustartfestigkeit des Pi (Pflicht)

Dieselbe Lücke auf der Linux-Seite, aus derselben Quelle: Die Unit-Vorlage
`actions.runner.service.template` enthält **kein** `Restart=` – systemd
startet den Dienst nach einem Absturz also nicht neu. Der Drop-in gehört in
dieselbe Datei wie die Session-Variablen aus §2.1, damit ein späteres
`svc.sh install` ihn nicht überschreibt:

```sh
sudo systemctl edit "$(cat .service)"
```

```ini
[Service]
Restart=always
RestartSec=10
```

```sh
sudo systemctl daemon-reload
systemctl show "$(cat .service)" -p Restart --value   # muss "always" sein
```

**Grafische Sitzung nach Reboot.** Der Dienst startet mit dem System, die
Desktop-Sitzung aber nur, wenn der Runner-Benutzer automatisch angemeldet
wird – sonst fehlen `DISPLAY`/`WAYLAND_DISPLAY` und jede GL-Prüfung schlägt
fehl. Auf Raspberry Pi OS über `sudo raspi-config` → *System Options* →
*Boot / Auto Login* → *Desktop Autologin*, alternativ direkt in der
LightDM-Konfiguration (`/etc/lightdm/lightdm.conf`, `autologin-user=`).

**Reboot-Probe (einmalig, am Gerät):** `sudo reboot`; nach dem Hochfahren
ohne manuelle Anmeldung den Heartbeat von Hand starten (§7) und prüfen, dass
`Heartbeat Linux aarch64` grün durchläuft. Das belegt Autologin, Session,
Dienststart und Neustart-Policy in einem Zug. Ergebnis und Datum im
Betriebs-Issue notieren.

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
- [ ] Genau **zwei** Workflows sprechen Self-hosted-Labels an: der
      Abnahme-Workflow (`workflow_dispatch`) und der tägliche Heartbeat
      (`schedule` + `workflow_dispatch`, §7). Nie Push-, PR- oder
      Fork-Events. Beide checken ohne Credentials aus und führen auf dem
      Runner ausschließlich repo-eigenen Code aus. Die Liste ist seit #921
      maschinell erzwungen – `tests/test_runner_heartbeat_workflow.py`
      scannt **alle** Workflow-Dateien und schlägt bei einem dritten fehl;
      `tests/test_release_abnahme_workflow.py` deckt die Abnahme-Seite ab.
      Ein weiterer Workflow ist eine bewusste Entscheidung: erst die Liste
      im Test ändern, dann dieselben Schutzbedingungen erfüllen.
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
mit venv, Netzzugang zu `api.github.com`, unter Linux das eng begrenzte
`sudo` für den `.deb`-Zyklus (§3) — und seit #934 ein **echter Qt-/GL-Smoke**
(siehe unten).
**Echter Qt-/GL-Probeaufruf im Preflight (#934).** Der ursprüngliche
Ladetest prüfte nur, ob `libGL.so.1` beziehungsweise das
macOS-OpenGL-Framework **ladbar** ist. Das fand den real beobachteten Fehler
„GL-Bibliothek fehlt", belegte aber nicht, dass PyQt6 lädt, dass das native
Platform-Plugin in der angemeldeten Sitzung startet, dass ein
`QOpenGLContext` wirklich aktuell wird und dass er auf echter Hardware läuft.
Ein so defekter Runner bestand den Preflight und fiel erst Minuten später im
schweren Plattform-Job aus.

`scripts/qt_gl_probe.py` schließt genau diese Lücke: ein eigener Prozess mit
`QGuiApplication`, `QOffscreenSurface` und `QOpenGLContext`, der den Kontext
aktuell macht und Vendor/Renderer/Version ausliest. Vier benannte
Fehlerzustände statt eines pauschalen „Qt kaputt":

| Stufe | Bedeutung |
|---|---|
| `import` | PyQt-/Qt-Runtime fehlt oder ist unbrauchbar |
| `plugin` | natives Platform-Plugin startet nicht (oder Headless erzwungen) |
| `kontext` | kein gültiger, aktueller GL-Kontext |
| `renderer` | Software-Rasterizer statt Hardware (`renderer_provenance`) |

Ein Abbruch **ohne** Ergebniszeile ist ebenfalls ein Befund: Qt beendet den
Prozess bei fehlendem Platform-Plugin hart (`qFatal`, real als SIGABRT
beobachtet), statt eine Ausnahme zu werfen. Der Preflight wertet das als
`plugin` und hängt die tragenden stderr-Zeilen an. Damit dieser Zweig der
**reine** `qFatal`-Fall bleibt, ist die gesamte Qt-Sequenz nach dem
Anwendungsstart abgesichert: Ein Treiber- oder Bindings-Fehler wird als
`kontext` gemeldet, nicht als Plugin-Problem.

Akzeptiert werden nur die Platform-Plugins einer echten Desktop-Sitzung
(`cocoa`, `xcb`, `wayland`, `wayland-egl`) — bewusst eine **Whitelist**. Qt
liefert unter Linux weitere Plugins ohne Sitzung, die trotzdem
hardwarebeschleunigt sind (`eglfs`, `minimalegl`, `vnc`, `linuxfb`,
`vkkhrdisplay`); eine Blacklist aus `offscreen`/`minimal` ließe eine kaputte
Desktop-Sitzung den Preflight bestehen und erst in den nativen
Abnahme-Schritten scheitern.

Zwei weitere Regeln übernimmt die Sonde vom Produktivpfad, damit Preflight
und Artefakt denselben Vertrag prüfen: Ein reiner **OpenGL-ES-Kontext** wird
abgewiesen (PyQt6 bindet keine ES-Funktionssätze, ADR #591), und Erfolg setzt
**alle drei** Provenienzfelder voraus — fiele ausgerechnet der Renderer aus,
hätte die Software-Regel nichts zu bewerten und die Sonde meldete Hardware
ohne Beleg.

Einen stillen Skip gibt es nicht — ein nicht erbrachter Nachweis ist ein
Fehler, keine Auslassung. Sind `session` oder `gl` bereits beanstandet, wird
die Sonde allerdings **übersprungen und das sichtbar als Folgebefund
ausgewiesen**: Sie könnte dort nur `plugin` melden, und der erste Lauf zahlte
dafür den vollen Runtime-Bau.

**Die Provenienz steht auch im grünen Lauf.** Bei Erfolg meldet der Preflight
`[preflight] ok: qt-gl (Apple / Apple M3 Max / 2.1 Metal - 90.5)` statt nur
`ok: qt-gl`. Der Messwert entscheidet nichts — das Verdikt fällt allein über
die vier Stufen oben —, aber er macht den Treiberwechsel sichtbar, *bevor* er
die Software-Regel reißt: Nach einem Mesa- oder Systemupdate steht im Joblog
jedes Tages, welche GPU den Nachweis getragen hat. Dieselbe Abwägung wie bei
`laufzeit_herkunft` im Abnahme-Zusatznachweis (#738) — nicht bewertet, aber
immer gedruckt. Ohne sie musste die Angabe von Hand nachgeholt werden,
obwohl die Sonde sie im selben Moment schon gemessen hatte (#934).

**Woher die Runtime kommt.** Die Sonde läuft **nicht** im Release-venv,
sondern in einer schlanken Runtime mit nur den Qt-Pins — sonst kostete jeder
Heartbeat eine vollständige `.[test]`-Installation. Sie liegt unter
`~/.cache/bgremover/preflight-qt` (überschreibbar über
`BGREMOVER_PREFLIGHT_VENV`) und trägt einen Marker mit dem Schlüssel aus
Qt-Pins und Python-Minor:

- Die Pins kommen aus **derselben** `requirements/constraints.txt`, aus der
  das Release-venv installiert wird. Ein geänderter Pin ändert den Schlüssel
  und erzwingt den Neubau — das ist die Aktualisierung bei
  Dependency-Änderungen, ohne dass jemand daran denken muss.
- Der Marker wird **erst nach** erfolgreicher Installation geschrieben; ein
  abgebrochener Bau sieht damit nie frisch aus.
- Installiert wird ausschließlich aus Wheels (`--only-binary=:all:`): Ein
  Qt-Quellbau auf dem Pi spränge jedes Budget, ein benannter Fehler ist
  besser als ein stundenlanger Compilerlauf.
- Fehlende Pins, gescheiterter Bau, Timeout und Dateisystemfehler (read-only
  `$HOME`, volle Platte) sind benannte Preflight-Fehler (fail-closed), keine
  Warnungen und kein Traceback — sonst blieben die noch nicht ausgewerteten
  Checks ungemeldet.
- Ersetzt wird beim Rollover nur, was erkennbar die eigene Ablage ist
  (`pyvenv.cfg` oder Marker vorhanden). `BGREMOVER_PREFLIGHT_VENV` ist frei
  setzbar; ohne diese Schranke machte ein Tippfehler oder ein geerbtes Env
  aus dem Rollover ein rekursives Löschen fremder Daten.

Zeitbudgets: Der Aufruf selbst hat 90 Sekunden, der einmalige Bau 7 Minuten —
bewusst kleiner als die `timeout-minutes: 10` der Readiness-Jobs, damit der
benannte Fehler entsteht, bevor GitHub den Job abschneidet. Nur der erste
Lauf je Pin-Stand zahlt den Bau.

**Was der schnelle Probeaufruf ausdrücklich *nicht* ersetzt.** Er beweist,
dass der GUI-/Renderer-Pfad grundsätzlich trägt — nicht, dass das
**Artefakt** funktioniert. Im Plattform-Job bleiben unverändert: der Start
der gepackten Artefakte samt Fork-Bomb-/Hänger-Wächter
(`abnahme_smoke.py`), die GL-Provenance des Artefakts
(`abnahme_probe.py`), die devicePixelRatio-/Retina-Probe
(`abnahme_scale_probe.py`), der native 3D-Screenshot mit Sidecar-Nachweis,
der `.deb`-Zyklus, der EufyMake-/2.7.0-Zusatznachweis und der
Update-Check-Nachweis. Der Preflight sagt „dieser Runner kann rendern"; die
Abnahme sagt „dieser Kandidat läuft".

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

**Release-Ref statt `main` (#918):** Alle vier Release-Dispatches
(Kandidatenbau, Abnahme, Publish, Post-Release-Nachweis) laufen auf dem
unveränderlichen Branch `release/vX.Y.Z`, der exakt auf den Kandidaten-Commit
zeigt; `main` bleibt während des gesamten Releases mergebar. Vor jedem Dispatch
prüft `release_contract.py verify-release-ref`, dass der Ref dem Namensschema
folgt, auf ein Commit-Objekt zeigt und den erwarteten SHA trägt — vorgelagert
zum harten SHA-Gate in `candidate-source`, nicht als dessen Ersatz.
Entscheidung, Bedrohungsmodell und Lebenszyklus des Refs:
[ADR](history/ADR-2026-release-ref-entkopplung.md); Prozedur im
[Release-Runbook](RELEASE_PROCESS.md).

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
- **Berechtigung:** `issues: write` tragen nur die Jobs, die tatsächlich
  kommentieren — dieser und seit #919 `update-dispatch`. Der `publish`-Job,
  der als einziger den Release mutiert, bleibt bei `contents: write` und
  `actions: read`; `release-instance` kommt mit Leserechten aus, weil er
  Artefakt und Job-Summary schreibt statt zu kommentieren.

### 4.2 Post-Release-Update-Nachweis (#748/#917)

`UPDATE-LINUX-ARM-01` und `UPDATE-MACOS-ARM-01` sind die einzigen **Post-Release**-Kriterien. Vor dem Tag kann kein
Vorgängerartefakt die neue Version am produktiven Endpunkt `/releases/latest`
sehen; als Pre-Release-Gate wäre der Nachweis logisch unmöglich. Er läuft
deshalb **nach** Schritt 8 des [Release-Runbooks](RELEASE_PROCESS.md), blockiert
den Tag nicht und schließt die Veröffentlichung fachlich ab.

**Aufruf.** Seit #919 stößt der Publish-Lauf diesen Dispatch selbst an, sobald
ihm `predecessor_tag` mitgegeben wurde (Job `update-dispatch`); der manuelle
Start bleibt der Rückfallweg. In beiden Fällen laufen dieselben Eingaben:

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

### 4.3 Automatisierter Abschluss aus dem Publish-Lauf (#919)

Drei Handgriffe aus Runbook-Schritt 7 bis 9 laufen seitdem im Workflow. Was
sich **nicht** ändert: Jede Prüfung, die vorher galt, gilt weiter — die
Automatisierung ersetzt keine Verifikation, sie ersetzt Tipparbeit.

**Tag (`create_tag`, Stufe 1).** Der `publish`-Job legt den annotierten Tag
**nach** der vollständigen Manifestprüfung auf `candidate.head_sha` an. Die
Entscheidung trifft `release_contract.py plan-tag` netzfrei aus dem Manifest
und der Antwort von `git/matching-refs/tags/<tag>`:

| Lage | Ergebnis |
|---|---|
| Tag fehlt | `create` — annotiertes Tag-Objekt, dann Ref darauf |
| Tag zeigt auf `candidate.head_sha` | `already-correct` — Wiederanlauf ist idempotent |
| Tag zeigt woanders hin | Abbruch; ein Tag wird **nie** verschoben |

`matching-refs` statt `git/ref` ist Absicht: Der Endpunkt antwortet immer mit
HTTP 200 und einer (ggf. leeren) Liste, "Tag fehlt" ist damit ohne
404-Sonderfall im Shell vom Fehlerfall unterscheidbar. Weil er per **Präfix**
sucht, filtert `select_tag_ref` exakt auf `refs/tags/<tag>` — sonst hätte ein
`v2.9.0-rc1` den Anschein erweckt, `v2.9.0` existiere bereits. Annotierte Tags
werden vor dem SHA-Vergleich dereferenziert; ihr Ref zeigt auf das Tag-Objekt,
nicht auf den Commit.

**Update-Dispatch (Stufe 2).** Der Job `update-dispatch` startet
`release-abnahme.yml` mit `platforms=alle` und dem übergebenen
`predecessor_tag`. Zwei Eigenschaften tragen ihn:

- **Korrelation.** `workflow_dispatch` antwortet mit HTTP 204 ohne Body, die
  Run-ID entsteht erst serverseitig. Der Lauf kennzeichnet sich deshalb selbst:
  `dispatch_marker` landet im `run-name` (dieser darf laut Workflow-Syntax die
  Kontexte `github` und `inputs` referenzieren), ein kurzes Polling findet ihn
  über `displayTitle`. Dass ein mit `GITHUB_TOKEN` ausgelöster
  `workflow_dispatch` überhaupt einen Lauf erzeugt, ist die ausdrückliche
  Ausnahme der Rekursionssperre: "With the exception of `workflow_dispatch`
  and `repository_dispatch`, other `GITHUB_TOKEN`-triggered events do not
  create workflow runs at all".
- **Idempotenz.** Der Marker `update-check:<tag>:<candidate_run_id>` ist
  deterministisch und enthält den Publish-Lauf bewusst **nicht**. Ein
  Wiederanlauf findet den vorhandenen Lauf und dispatcht nicht erneut — auch
  dann nicht, wenn dieser fehlgeschlagen ist: Ein fehlgeschlagener
  Update-Nachweis ist ein Incident, kein Wiederholungsfall.

Dispatch-Ref ist der unveränderliche **Release-Ref** `release/vX.Y.Z` — dieselbe
Quelle wie in den Runbook-Schritten 3, 5 und 8 (#918). Er muss dem Publish-Lauf
nicht übergeben werden: Er ist deterministisch aus dem Tag ableitbar. Geprüft
wird er über `release_contract.validate_release_ref` gegen
`needs.publish.outputs.candidate_sha` — und zwar **im Skript, unmittelbar vor
einem tatsächlichen Dispatch**, nicht in einem vorgelagerten Workflow-Schritt:
Nach Runbook-Schritt 9 darf der Ref gelöscht sein, und ein Wiederanlauf, der den
vorhandenen Nachweislauf findet, dispatcht gar nicht mehr; eine unbedingte
Prüfung machte genau diesen idempotenten Wiederanlauf rot. Muss dispatcht
werden und fehlt der Ref oder zeigt er woandershin, bricht der Job ab, statt auf
eine andere Quelle auszuweichen. Der Tag bleibt die *veröffentlichte Version*, nicht
die Dispatch-Quelle — beide zeigen auf denselben Commit, und genau deshalb wäre
die Verwechslung folgenlos-aussehend: fail-closed bliebe sie, nur eben aus einer
zweiten Prozessquelle. `actions: write` trägt ausschließlich dieser Job.

**Release-Instanz (Stufe 3).** Sie entsteht in zwei Hälften, jede dort, wo die
Evidenz anfällt:

| Lauf | Kriterien | Validierung |
|---|---|---|
| `release-instance` (Publish) | `PUBLISH-01..03`, `PUBLIC-DOWNLOAD-01` → `PASS` | `--through-phase publish` |
| `aggregation` (ausgelöste Abnahme) | `UPDATE-LINUX-ARM-01`, `UPDATE-MACOS-ARM-01` aus der eigenen `update_check.json` | `--through-phase post-release` |

Der Publish-Lauf kann `post-release` nicht validieren — die beiden
Update-Kriterien sind dort noch `PENDING`, und
`validate_release_instance_completion` verlangt für `POST_RELEASE` ein `PASS`.
Beide Hälften benutzen die Checkliste **des Kandidaten-Commits**, weil die
Instanz deren Dateihash pinnt.

Die Statusabbildung ist fail-closed: keine Evidenz → `PENDING` (ohne
Evidenzeintrag, sonst sähe ein nicht erbrachter Nachweis belegt aus),
`ok: true` → `PASS`, `ok: false` → `FAIL`, unbekanntes Schema → Abbruch. Ein
`FAIL` blockiert den Abschluss und wird nie auf `WAIVED` gesetzt; die Instanz
wird trotzdem geschrieben und hochgeladen, weil sie genau dann die Evidenz des
Fehlschlags ist. Ein Lauf ohne `publish_run_id` lässt die Instanzpflege
unverändert aus.

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
- Runner, die länger offline sind, entfernt GitHub nach 14 Tagen automatisch –
  dann §2 wiederholen (Schritt für Schritt: [`RUNNER_SETUP.md`](RUNNER_SETUP.md)).

### 6.1 Neustart und Update je Gerät

Vor geplanten Eingriffen den Heartbeat befristet pausieren (§7), sonst meldet
er den Ausfall als echten Befund. Nach dem Eingriff die Pause **aufheben**;
ein abgelaufenes Wartungsfenster macht den nächsten Heartbeat rot – bewusst,
damit eine vergessene Pause nicht die Überwachung stilllegt.

**Raspberry Pi (Linux aarch64):**

```sh
sudo apt update && sudo apt full-upgrade
sudo reboot
# Nach dem Hochfahren, ohne manuelle Anmeldung:
systemctl is-active "$(cat .service)"                 # active
systemctl show "$(cat .service)" -p Restart --value   # always
python3 scripts/abnahme_preflight.py --platform linux-arm64 --hardening-strict
```

**MacBook (macOS arm64):** Systemupdate einspielen, neu starten und am Gerät
**anmelden** – der LaunchAgent lebt in der GUI-Sitzung des Runner-Benutzers
und startet erst mit ihr.

```sh
./svc.sh status                                        # läuft
pmset -g custom | awk '/^AC Power:/{ac=1} ac && /(^| )(sleep|displaysleep) /'
python3 scripts/abnahme_preflight.py --platform macos-arm64 --hardening-strict
```

Danach in beiden Fällen den Heartbeat einmal von Hand starten (§7). Steht ein
echtes Release an, zusätzlich den Dry-Run des Abnahme-Workflows fahren – der
Heartbeat belegt Bereitschaft, nicht die vollständige Abnahmekette.

## 7. Runner-Heartbeat: Ausfälle zwischen den Läufen (#921)

Der Lauf-Watchdog (#915) meldet einen Ausfall **im** Abnahme-Lauf – also
frühestens beim Release. Beim v2.9.0-Verzug war der Pi-Runner tagelang
offline, und genau das fiel erst beim Dispatch auf (#881). Der Workflow
[`runner-heartbeat.yml`](../.github/workflows/runner-heartbeat.yml) schließt
die Lücke davor: Er läuft **täglich um 05:30 UTC** (und auf Zuruf) und gibt
jedem aktiven Runner einen minimalen Job.

**Zwei Fristen, weil zwei verschiedene Fragen** (#921-Nachprüfung). Eine
einzige Frist beantwortete beide falsch: Die Doku versprach 15 Minuten, die
Auswertung wartete das volle Fenster ab und meldete „wartet nach 1500 s".

| Frist | Wert | Frage | Ausgang beim Ablauf |
|---|---|---|---|
| Annahme | **15 min** (900 s) | Hat der Runner den Job *angenommen*? | noch `queued` → `FAIL` (offline **oder belegt**, s. u.), sofort |
| Bereitschaft | **25 min** (1500 s) | Ist die *Prüfung abgeschlossen*? | noch `running` → `UNOBSERVED`, kein Verdikt |

Die Gesamtfrist ist die Summe aus Annahmefrist und dem Jobbudget des
Readiness-Jobs (`timeout-minutes: 10`), nicht frei gewählt. Das
Offline-Verdikt fällt zur **Annahmefrist** — auf das Gesamtfenster zu warten
verzögerte nur die Meldung, und die Zusage „binnen 15 Minuten" hielte nicht.
Beide Werte stehen als Voreinstellung im Skript und werden im Workflow
ausdrücklich übergeben; `tests/test_runner_heartbeat_workflow.py` hält
Doku, Workflow und Konstanten gegeneinander.

Zwei Feinheiten, die sich aus der Verkürzung ergeben:

- **Ein belegtes Gerät ist kein offline Gerät.** Self-hosted Runner nehmen
  standardmäßig einen Job gleichzeitig an. Läuft zur Heartbeat-Zeit ein
  Abnahme-Plattformjob auf demselben Runner, wartet der Heartbeat-Job zu
  Recht — und wird nach 15 statt nach 25 Minuten gemeldet. Die Meldung nennt
  diesen Grund deshalb ausdrücklich mit („offline, nimmt keine Jobs an oder
  ist mit einem anderen Lauf belegt"); wer den Issue-Kommentar liest, soll
  nicht nach einem Ausfall suchen, den es nicht gibt. Belastbarer wäre eine
  Auswertung des Runner-Zustands — die braucht aber genau das PAT mit
  `Administration: read`, das §7 unten bewusst ablehnt.
- **Ein API-Schluckauf verschenkt die Beobachtung nicht.** Die Annahmefrist
  terminiert nur auf **frischer** Grundlage. Ist die Beobachtung zum
  Fristablauf veraltet, läuft die Schleife bis zum Gesamtfenster weiter,
  damit sich die Jobs-API erholen kann — sonst gäbe der Monitor zehn Minuten
  für eine Störung auf, die er überlebt hätte, und meldete `UNOBSERVED`
  statt eines echten Verdikts.

Der Job auf dem Runner ist bewusst kein `echo`, sondern der Preflight aus
§2/§2.1/§2.2 mit `--hardening-strict`. Damit fällt nicht nur ein *offline*
Gerät auf, sondern auch ein eingeschaltetes, das nicht einsatzbereit wäre:
fehlende grafische Sitzung, fehlendes GL, voller Datenträger, abgeschalteter
Sleep-Schutz, Dienst ohne Neustart-Policy. Im Abnahme-Preflight bleiben die
Härtungspunkte bewusst Hinweise – ein Release soll nicht an einer
Display-Sleep-Einstellung scheitern; der tägliche Lauf ist die
Durchsetzungsstelle.

**Meldeweg.** Die Auswertung liest Status **und** Ergebnis der Runner-Jobs.
Damit trägt sie beide Hälften des Signals: den Runner, der den Job gar nicht
annimmt (offline), und den, der ihn annimmt und an der Bereitschaftsprüfung
scheitert (nicht einsatzbereit). Der Umweg über die Jobs-API ist nötig, weil
`if: failure()` in einem Schritt nur auf vorherige Schritte **desselben**
Jobs und auf Vorgänger per `needs` reagiert – die Runner-Jobs sind bewusst
keine Vorgänger der Auswertung.

**Konklusionen (#944).** Bestanden ist ein Job ausschließlich mit `success`.
`failure`, `timed_out` und `startup_failure` sind Gerätebefunde (`FAIL`,
Issue-Kommentar) – `startup_failure` heißt „angenommen, konnte nicht starten"
(kaputter Workspace, volles `_work`, Dienst am Ende). Jede andere
abgeschlossene Konklusion (`cancelled`, `skipped`, `stale`, fehlend) belegt
weder Bereitschaft noch Scheitern: Sie steht als `inconclusive_jobs` im Bericht
und ergibt `UNOBSERVED` ohne Issue-Kommentar, statt still als bestanden zu
gelten.

Der **verbindliche** Kanal ist der Kommentar im Betriebs-Issue: Die
Repository-Variable `RUNNER_HEARTBEAT_ISSUE` ist Pflicht, die Auswertung
prüft sie vor jeder Messung und schlägt sonst mit klarer Meldung fehl. Grund
steht unter *Grenzen*: Im Offline-Fall ist der **Lauf** nicht abgeschlossen,
und Actions benachrichtigt erst beim Laufabschluss — die Fehlermail bleibt
also genau dann aus, wenn sie gebraucht würde. Kommentiert wird **nur im
Fehlerfall**: ein täglicher Erfolgskommentar würde das Betriebs-Issue in
Rauschen verwandeln, in dem der eine Ausfalltag untergeht. Bericht
(`heartbeat.json`, Schema 1) und Summary hängen 30 Tage als Artefakt
`runner-heartbeat` am Lauf.

**Wartungsfenster.** Für geplante Eingriffe pausieren:

| Variable | Wert |
|---|---|
| `RUNNER_HEARTBEAT_PAUSED` | `true` |
| `RUNNER_HEARTBEAT_PAUSED_UNTIL` | Enddatum, `YYYY-MM-DD` |

Im Regelbetrieb erforderlich:

| Variable | Wert |
|---|---|
| `RUNNER_HEARTBEAT_ISSUE` | Nummer des Betriebs-Issues (Pflicht, s. *Meldeweg*) |

Die Pause ist sichtbar (Warnung und Job-Summary „pausiert") und **befristet**:
Fehlt das Enddatum, ist es unlesbar oder liegt es in der Vergangenheit, wird
der Lauf rot – die Pause selbst ist dann der Befund. Eine unbefristete Pause
wäre keine Pause, sondern eine abgeschaltete Überwachung, und niemand sähe
es. Nach dem Eingriff `RUNNER_HEARTBEAT_PAUSED` entfernen.

**Warum ohne PAT.** Der Runner-Status ließe sich direkt abfragen
(`GET /repos/{owner}/{repo}/actions/runners`), das braucht aber ein
Fine-grained PAT mit `Administration: read` – ein Recht, das dem
`GITHUB_TOKEN` nicht zuweisbar ist. Abwägung:

| | Heartbeat-Jobs (gewählt) | PAT mit `Administration: read` |
|---|---|---|
| Zusätzliches Dauergeheimnis | keines | ein Token mit Administrationsrecht am Repository |
| Aussage | Runner **nimmt Jobs an** und ist einsatzbereit | Runner ist bei GitHub als online registriert |
| Blinder Fleck | – | ein „online", aber unbrauchbarer Runner bleibt grün |
| Kosten | zwei Minutenjobs pro Tag | keine |

Ein online gemeldeter Runner ohne grafische Sitzung hätte dieselbe Abnahme
scheitern lassen; die Job-Annahme belegt mehr als der Statusflag und braucht
kein Geheimnis. Entscheidung deshalb: PAT-frei. Wird der Statusweg später
doch gebraucht (z. B. um zwischen „offline" und „busy" zu unterscheiden),
ist er additiv nachrüstbar.

**Grenzen.** Bleibt ein Runner offline, wartet sein Job bis zu 24 Stunden in
der Warteschlange. Der Heartbeat bricht ihn bewusst **nicht** ab: Ein
force-cancel ließe den Lauf als „cancelled" enden – ohne Fehlermeldung. Statt
dessen räumt `concurrency: cancel-in-progress` auf, sodass höchstens ein
wartender Lauf stehen bleibt. Die Kehrseite, und der Grund für die
Pflichtvariable oben: Dieser Lauf endet dann am Folgetag ebenfalls als
„cancelled". Auf die Actions-Fehlermail ist im Offline-Fall daher **kein**
Verlass — sie kommt nur, wenn der Lauf regulär abschließt (alle Runner haben
den Job angenommen, mindestens einer die Prüfung nicht bestanden). Der
Issue-Kommentar der Auswertung fällt dagegen zur Annahmefrist, also lange
bevor der wartende Job überhaupt endet. Kann die
Job-Liste nicht abgefragt werden (API-Fehler), meldet der Heartbeat
`UNOBSERVED` und schlägt keinen Alarm – ein Monitor ohne Beobachtung darf
kein Verdikt fällen.

## 8. Monatlicher Dry-Run des Kandidatenpfads (#922)

Beim v2.9.0-Release scheiterte der **erste** Kandidatenlauf an
`base-tag-missing` (#880): `ci.yml` lief als wiederverwendbarer Workflow ohne
vollen Checkout, das darin enthaltene Freeze-Gate fand deshalb weder Basis-Tag
noch First-Parent-Historie. Der Fehler war auf jedem PR unsichtbar — er
entsteht ausschließlich im Kandidatenkontext — und fiel am Release-Tag auf,
mit einem verbrannten Lauf und einem Fix unter Zeitdruck.

`release-linux.yml` läuft deshalb zusätzlich **monatlich am 3. um 04:40 UTC**
per `schedule`. Das ist die einzige Ausnahme von „dispatch-only": Ein
Tag-Trigger, Schreibrechte oder ein Publish-Job kommen dadurch **nicht**
zurück (`tests/test_release_gate.py` hält beides fest).

### 8.1 Was der Dry-Run prüft — und was nicht

Geprüft wird genau das, was nur dieser Workflow fährt:

| Stufe | Deckt ab |
| --- | --- |
| `verify-candidate` | Freeze-Gate, Pfadklassifikation, Kandidatenprovenienz, Artefakt-Upload der Provenienz |
| `test` | Full-CI-Matrix als **wiederverwendbarer** Workflow — genau der Aufrufpfad aus #880 |
| `build` | drei Build-Legs (2 × Linux, 1 × macOS), Smoke-Launches, `.deb`-Zyklus, Artefakt-Scan inkl. ClamAV-Cache-Restore, Artefakt-Upload |

Gebaut wird mit dem **produktiven** KI-Bündel (`WITH_AI=1`), weil ein Release
rembg bündelt (#881); ein Dry-Run mit `with_ai=false` prüfte einen anderen als
den ausgelieferten Pfad. Im `schedule`-Kontext gibt es kein `inputs.with_ai` —
die Bedingung steht deshalb als Workflow-`env` an genau einer Stelle und
speist auch den `--ai`-Schalter der Build-Schritte.

Der geplante Lauf hängt dabei **nicht** an der Verfügbarkeit des
`inputs`-Kontexts: In `env.WITH_AI` steht `github.event_name == 'schedule'`
links vom `||`, das Ergebnis ist für einen Dry-Run also `1` *by construction* —
unabhängig davon, was `inputs.with_ai` dort liefert. Das ist beabsichtigt: Die
Kontextreferenz führt `inputs` nur für `workflow_dispatch` und
wiederverwendbare Workflows; diese Formulierung muss die Frage gar nicht
beantworten.

Zusätzlich bricht der erste Job ab, wenn ein Dry-Run mit `WITH_AI=0` starten
würde (*Dry-Run ohne KI-Bündel*). Diese Zusicherung kann mit dem heutigen
Ausdruck **nicht** auslösen; sie sichert die *Folge* statt der Herleitung: Der
Test pinnt den Ausdruckstext, der Abbruch sein Ergebnis. Wer `env.WITH_AI`
später umformuliert und den Test mitzieht, fällt im ersten Job auf statt nach
~22 Minuten Build mit dem falschen Bündel.

**Nicht** geprüft wird alles, was am Kandidaten hängt: Abnahme auf echter
Hardware, Freigabemanifest, Veröffentlichung. Der Dry-Run ist ein
Pipeline-Test, kein Release-Test.

### 8.2 Warum ein Dry-Run nie ein Kandidat werden kann

Drei unabhängige Schranken, die erste ist die bindende:

1. **Freigabevertrag (fail-closed).** `release_contract.validate_workflow_run`
   verlangt `event == workflow_dispatch`. `release-abnahme.yml` ruft
   `prepare-candidate` im Job `candidate-source` auf — also **vor** jeder
   Hardware-Arbeit. Eine Dry-Run-Run-ID scheitert dort mit klarer Meldung,
   nicht erst irgendwo im Manifest.
2. **Sichtbare Kennzeichnung.** Der `run-name` lautet „Dry-Run — kein
   Kandidat" (Laufliste), ein `::notice::` und eine Job-Zusammenfassung stehen
   am Lauf, und jedes Build-Leg schreibt den Modus in seine Provenienzzeilen.
   Die Kennzeichnung steht bewusst **vor** dem Checkout: Gerade ein
   abgebrochener Lauf verleitet sonst dazu, seine Run-ID für einen Kandidaten
   zu halten.
3. **Kurze Aufbewahrung.** Die Produktartefakte eines Dry-Runs verfallen nach
   **3 Tagen** statt nach 90.

### 8.3 Kosten

Je Lauf: die Full-CI-Matrix (8 Legs) plus drei Build-Legs (~22 Minuten) und
~1,1 GB Artefakte. Bei monatlicher Frequenz und 3 Tagen Aufbewahrung ist der
Speicheranteil vernachlässigbar; der Rechenanteil entspricht etwa einem
zusätzlichen Kandidatenlauf pro Monat. Die kleinen Evidenzartefakte
(`release-freeze-provenance-<versuch>`, `security-scan-<plattform>`) behalten
bewusst 90 Tage — sie tragen die Diagnose eines roten Laufs und kosten kaum
Speicher.

Der Workflow bekommt **bewusst keine** `concurrency`-Gruppe: Sie würde einen
manuell gestarteten Kandidatenlauf entweder hinter einem laufenden Dry-Run
einreihen oder — mit `cancel-in-progress` — abbrechen. Beides wäre im Release
teurer als die seltene Gleichzeitigkeit. Gemeinsamen Zustand gibt es nicht;
der ClamAV-Signaturcache wird nur gelesen, Artefakte gehören je Lauf.

### 8.4 Reaktion auf einen roten Dry-Run

Der Job **Dry-Run-Ergebnis** fasst die drei Stufen an einer Stelle zusammen
und macht den Lauf rot, sobald eine gefallen ist — mit Ursache,
Diagnosematerial und Reaktionsweg in der Job-Zusammenfassung (dasselbe Muster
wie `recommendations-live-check.yml`).

**Owner: Repository-Owner.** Ein roter Dry-Run bleibt ein aktiver
Pipeline-Befund, bis die Ursache behoben oder bewusst als bekannt eingeordnet
ist. Reaktion vor dem nächsten Kandidatenbau, spätestens beim nächsten
Release — genau dort wäre sie sonst wieder Zeitdruckarbeit. Nach der Korrektur
lässt sich derselbe Pfad ohne Wartezeit erneut prüfen: `release-linux.yml`
manuell starten (dann als Kandidatenlauf gekennzeichnet) oder den nächsten
geplanten Lauf abwarten.

Abgebrochene oder übersprungene Stufen sind ausdrücklich **kein**
Grün-Nachweis: Der Bericht meldet sie als „unvollständig — kein Ergebnis"
statt als bestanden. Ein abgebrochener Lauf wäre sonst ein Beleg dafür, dass
der Release-Pfad trägt.

**Einordnung eines roten `verify-candidate`.** Das Freeze-Gate liest
`docs/history/RELEASE-<version>-scope-freeze.md` zur jeweils aktuellen
`pyproject`-Version — ein Versionsbump ohne zugehöriges Freeze-Dokument macht
jeden geplanten Lauf rot. Das ist aber kein Zustand, den `main` erreichen
kann: `pr-ci.yml` fährt `make pr-check`, und dieses Ziel enthält
`release-freeze-check` — denselben fail-closed Aufruf. Bump und Freeze-Dokument
müssen also ohnehin im selben PR landen. Ein rotes `verify-candidate` im
Dry-Run ist damit **kein** erwarteter Nebeneffekt der Release-Vorbereitung,
sondern ein Befund.

**Meldeweg — und seine Grenze.** Für den *gefallenen* Ausgang ist auf die
Actions-Fehlermail Verlass: Der Lauf schließt regulär mit `failure` ab, anders
als der Heartbeat, den ein offline Runner gar nicht erst abschließen lässt
(§7).

Für „hat nicht stattgefunden" gilt das **nicht**. Der Ausgang *unvollständig*
endet mit `exit 0`, der Lauf also als `cancelled` — dafür verschickt Actions
keine Mail. Ebenso wenig, wenn der geplante Lauf gar nicht erst startet (etwa
weil GitHub Schedules unter Last auslässt oder sie nach 60 Tagen ohne
Repository-Aktivität abschaltet). Das ist dieselbe Lücke wie beim Heartbeat für
den offline Runner, hier bewusst **ohne** dessen Gegenmittel: Ein
verpflichtender Issue-Kommentar wäre für einen monatlichen Pipeline-Test
unverhältnismäßig.

Getragen wird der Fall stattdessen von der Sichtprüfung in
[Runbook-Schritt 1](RELEASE_PROCESS.md): `gh run list --workflow
release-linux.yml --event schedule` zeigt sowohl einen ausgebliebenen als auch
einen unvollständig gebliebenen Lauf. Der Termin dafür ist genau der richtige —
unmittelbar bevor der Kandidatenbau denselben Pfad fährt.
