# Runner-Neuaufbau: MacBook und Raspberry Pi (Kochbuch)

Schritt-für-Schritt-Anleitung, um die beiden Self-hosted Runner der
Release-Abnahme auf einem **frisch installierten** Gerät wieder einzurichten –
inklusive Kommandos, mit denen sich vorab prüfen lässt, ob und in welchem
Zustand die Runner bereits registriert sind.

Dieses Dokument ist ein **Kochbuch**, keine neue Regelquelle: Verbindlich sind
[`RELEASE_AUTOMATION.md`](RELEASE_AUTOMATION.md) (§2 Registrierung, §2.1/§2.2
Sitzung/Härtung, §3 Sicherheits-Checkliste, §6 Wartung, §7 Heartbeat) und der
Prüfcode in [`scripts/abnahme_preflight.py`](../scripts/abnahme_preflight.py).
Bei Widerspruch gelten diese Quellen. Die maschinell prüfbaren Soll-Zustände
sind exakt die Bedingungen des täglichen Heartbeats (`--hardening-strict`);
Registrierung, Runner-Namen und Ablageorte prüft er nicht.

Zielzustand (Geräte/Labels aus [`RELEASE_AUTOMATION.md`](RELEASE_AUTOMATION.md)
§1, Dienstform aus §2; die Runner-Namen sind Konvention dieses Repos):

| Gerät | Runner-Name | Labels | Dienstform |
|---|---|---|---|
| MacBook (Apple Silicon) | `Mac` | `self-hosted`, `macOS`, `ARM64` | LaunchAgent des angemeldeten Benutzers |
| Raspberry Pi 5 (Debian 12, Desktop) | `raspberrypi` | `self-hosted`, `Linux`, `ARM64` | systemd-System-Dienst |

**Wo welche Kommandos laufen:** Alle `gh`-Kommandos dieser Anleitung laufen
auf dem **Arbeitsrechner** (installiertes, authentifiziertes `gh` mit
Admin-Rechten am Repository), niemals auf dem Runner-Gerät – dorthin gehört
kein Repository-Token ([`RELEASE_AUTOMATION.md`](RELEASE_AUTOMATION.md) §3).
Alle übrigen Blöcke laufen auf dem jeweiligen Gerät.

---

## 0. Vorab prüfen: Sind die Runner schon da, und wie ist ihr Status?

### 0.1 Aus der Ferne (Repository-Sicht)

Auf dem Arbeitsrechner; als Repository-Owner reicht das normale
`gh auth login`:

```sh
REPO=NikolayDA/picture_helper
gh api "repos/$REPO/actions/runners" --jq '
  if .total_count == 0 then "Keine Self-hosted Runner registriert."
  else .runners[]
    | "\(.name)\tstatus=\(.status)\tbusy=\(.busy)\tversion=\(.version // "?")\tlabels=\([.labels[].name] | join(","))"
  end'
```

Erwartete Ausgabe bei intaktem Bestand (Reihenfolge egal, Version variiert):

```text
Mac	status=online	busy=false	version=2.328.0	labels=self-hosted,macOS,ARM64
raspberrypi	status=online	busy=false	version=2.328.0	labels=self-hosted,Linux,ARM64
```

Einordnung:

- `status=offline` → Gerät oder Dienst ist unten; erst §5 (Wiederbelebung)
  versuchen, bevor neu registriert wird.
- Runner fehlt in der Liste → neu registrieren (§2 bzw. §3). GitHub entfernt
  einen Runner automatisch, der **mehr als 14 Tage** nicht verbunden war
  (offizielle GitHub-Doku,
  [remove-runners](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/remove-runners)).
- `status=online` sagt nur „verbunden", **nicht** „einsatzbereit" – die
  eigentliche Bereitschaft belegt erst der Heartbeat (0.2) bzw. der
  Preflight auf dem Gerät (0.3).

### 0.2 Ohne Admin-API: Heartbeat von Hand starten

Der tägliche Heartbeat ist die verbindliche Bereitschaftsprüfung
([`RELEASE_AUTOMATION.md`](RELEASE_AUTOMATION.md) §7). Ein manueller Lauf
beantwortet „vorhanden **und** einsatzbereit?":

```sh
REPO=NikolayDA/picture_helper
gh workflow run runner-heartbeat.yml --repo "$REPO"
sleep 10
gh run watch --repo "$REPO" \
  "$(gh run list --repo "$REPO" --workflow runner-heartbeat.yml --limit 1 \
     --json databaseId --jq '.[0].databaseId')" --exit-status
```

- **Grün** (typisch unter einer Minute; nach einem Neuaufsetzen wegen des
  einmaligen Qt-Runtime-Baus deutlich länger): beide Runner haben den Job
  angenommen und die strikte Bereitschaftsprüfung bestanden – nichts zu tun.
- **Offline-Fall:** Der FAIL-Kommentar im Betriebs-Issue
  [#939](https://github.com/NikolayDA/picture_helper/issues/939) kommt zur
  Annahmefrist (~15 min). Der **Lauf** selbst bleibt danach offen – der
  wartende Runner-Job hält ihn, erst der Folgetag beendet ihn als
  „cancelled" ([`RELEASE_AUTOMATION.md`](RELEASE_AUTOMATION.md) §7,
  *Grenzen*). `gh run watch` dann abbrechen und den Issue-Kommentar bzw. den
  roten Job „Heartbeat-Auswertung" lesen.
- **Rot, aber der Runner-Job lief:** Das Joblog des jeweiligen
  `Heartbeat …`-Jobs nennt die gescheiterte Prüfung als
  `::error`-Annotation (Titel `Preflight <plattform>` bzw.
  `Haertung <plattform>`) – Abhilfe je Befund in §2–§3 dieses Dokuments.

### 0.3 Auf dem Gerät selbst

Dienststatus, im Runner-Verzeichnis – macOS:

```sh
cd ~/actions-runner && ./svc.sh status
```

Raspberry Pi:

```sh
cd ~/actions-runner
systemctl is-active "$(cat .service)"
systemctl show "$(cat .service)" -p Restart --value   # Soll: always
```

Vollständige Bereitschafts- und Härtungsprüfung (identisch zum Heartbeat) im
Repo-Checkout auf dem Gerät – macOS:

```sh
cd ~/picture_helper
python3 scripts/abnahme_preflight.py --platform macos-arm64 --hardening-strict
```

Raspberry Pi (über SSH vorher die Sitzungsvariablen exportieren, §3.5):

```sh
cd ~/picture_helper
python3 scripts/abnahme_preflight.py --platform linux-arm64 --hardening-strict
```

Beim allerersten Aufruf baut die `qt-gl`-Sonde einmalig ihre schlanke
Qt-Runtime (`~/.cache/bgremover/preflight-qt`, bis zu 7 Minuten); danach ist
der Aufruf schnell. Nur die Härtung – ohne Runtime-Bau – prüft dieser
Schnelltest (funktioniert auf beiden Geräten unverändert):

```sh
cd ~/picture_helper
python3 - <<'EOF'
import sys
sys.path.insert(0, "scripts")
import abnahme_preflight as p
platform = "macos-arm64" if sys.platform == "darwin" else "linux-arm64"
for name, err in p.run_hardening(platform):
    print(f"{name}: {err or 'ok'}")
EOF
```

---

## 1. Gemeinsame Voraussetzungen (beide Geräte)

Aus [`RELEASE_AUTOMATION.md`](RELEASE_AUTOMATION.md) §1/§3 und
`scripts/abnahme_preflight.py`:

- **Dedizierter Benutzer** ohne Zugriff auf persönliche Daten/Schlüssel
  (§3). Anlegen: Mac über Systemeinstellungen → Benutzer:innen (mit
  Admin-Rechten für die einmalige Einrichtung, siehe §2.3); Pi über den
  Raspberry Pi Imager bzw. den Erststart-Assistenten – der dort angelegte
  Benutzer ist zugleich der Runner-Benutzer und Mitglied der
  `sudo`-Gruppe. Der Runner läuft unter diesem Benutzer, und dieser
  Benutzer ist an der grafischen Sitzung angemeldet.
- `python3` ≥ 3.10 **mit venv-Modul** im PATH (Debian/Pi: Paket
  `python3-venv`).
- ≥ 2 GB freier Speicher im Runner-Arbeitsverzeichnis; das Verzeichnis liegt
  **nicht** in einem synchronisierten Ordner (iCloud/Nextcloud o. Ä.).
- Netzzugang zu `api.github.com`/`github.com`.
- Laufende **grafische Sitzung** (macOS: angemeldeter Benutzer; Pi:
  Desktop-Session mit Autologin) – ein „Idle"-Runner ohne Sitzung fällt im
  Preflight, nicht erst in der Abnahme.
- PyQt6 muss **nicht** systemweit installiert werden – Workflow und
  Preflight legen ihre venvs selbst an. Auf dem Pi müssen die
  Qt-Systembibliotheken der laufenden Desktop-Session vorhanden sein
  (Raspberry Pi OS **mit Desktop** bringt sie mit, §3.1).

Die Registrierung selbst läuft für beide Geräte gleich
([`RELEASE_AUTOMATION.md`](RELEASE_AUTOMATION.md) §2): GitHub → Repository →
**Settings → Actions → Runners → New self-hosted runner**, Plattform wählen,
und die dort angezeigten Befehle (Download, Prüfsumme, `./config.sh` mit dem
angezeigten Token) auf dem Gerät ausführen. Das Registrierungs-Token ist
**eine Stunde gültig** (offizielle GitHub-Doku) – den Block also erst öffnen,
wenn das Gerät bereitsteht. Bei `./config.sh` gilt:

- **Labels: die Standard-Labels unverändert übernehmen.** Die Workflows
  adressieren exakt `[self-hosted, macOS, ARM64]` bzw.
  `[self-hosted, Linux, ARM64]`; beide Label-Sätze entstehen automatisch.
- **Runner-Name:** `Mac` bzw. `raspberrypi` (Wiedererkennbarkeit in Läufen
  und Betriebs-Issue; technisch erzwungen wird der Name nicht).
- Übrige Fragen (Arbeitsordner, Runner-Gruppe) mit Enter bestätigen.

---

## 2. MacBook (macOS arm64) neu aufsetzen

### 2.1 Systemvoraussetzungen

Auf einem fabrikneuen Mac zuerst Homebrew installieren (der Installer holt
dabei auch die Xcode Command Line Tools und damit `git`; Quelle:
[brew.sh](https://brew.sh)) – danach Python/git wie in
[`INSTALL_MAC.md`](../INSTALL_MAC.md) dokumentiert:

```sh
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
eval "$(/opt/homebrew/bin/brew shellenv)"
```

```sh
brew install python git
python3 --version   # Soll: ≥ 3.10
```

Das Runner-Verzeichnis (`~/actions-runner`) und der Repo-Checkout gehören
**nicht** nach `~/Documents`, `~/Desktop`, `~/Downloads` oder in iCloud
Drive – dort blockiert macOS-TCC Dateizugriffe gestarteter Programme
([`INSTALL_MAC.md`](../INSTALL_MAC.md), Abschnitt „Troubleshooting"); direkt
unter dem Home-Verzeichnis ist richtig.

### 2.2 Runner registrieren und als Dienst einrichten

Registrierungsblock aus der GitHub-UI ausführen (§1), dabei
`--name Mac` wählen. Danach – **als der angemeldete Runner-Benutzer, ohne
sudo** (der Dienst muss ein LaunchAgent der GUI-Sitzung werden, kein
LaunchDaemon; das offizielle `svc.sh` bricht unter `sudo` ohnehin mit
„Must not run with sudo" ab):

```sh
cd ~/actions-runner
./svc.sh install
./svc.sh start
./svc.sh status
```

Sichtprüfung: Settings → Actions → Runners zeigt `Mac` als „Idle";
`cat .service` nennt den erzeugten Dienst, die plist liegt unter
`~/Library/LaunchAgents/actions.runner.*.plist`. Runner- und
Konsolenbenutzer müssen identisch sein:

```sh
printf 'Runner: %s; Konsole: %s\n' "$(id -un)" "$(stat -f '%Su' /dev/console)"
```

### 2.3 Härtung: Sleep-Schutz und Neustart-Policy (Pflicht für den Heartbeat)

**Sleep-Schutz** – am Netzteil weder System- noch Display-Schlaf (der
Display-Schlaf zählt mit, die Abnahme erzeugt native Screenshots). Die
`pmset`-Kommandos brauchen Admin-Rechte; einmalig von einem Admin
ausgeführt, wirkt die Einstellung systemweit:

```sh
sudo pmset -c sleep 0 displaysleep 0
```

Nur für einen **zugeklappt** betriebenen MacBook zusätzlich:

```sh
sudo pmset -a disablesleep 1
```

Alternative für Geräte, die sonst schlafen sollen: den Runner in einen
`caffeinate -dimsu`-Wrapper hängen. Der Preflight akzeptiert beides; bei der
`caffeinate`-Variante zählt nur eine Assertion, die einem
`caffeinate`-Prozess **gehört** und beide Schlafarten hält
(`PreventUserIdleSystemSleep` + `PreventUserIdleDisplaySleep`) – systemweite
Zähler anderer Programme genügen nicht.

**Neustart-Policy** – der offizielle LaunchAgent setzt kein `KeepAlive`, ein
abgestürzter Dienst bliebe unten. Einmalig ergänzen – und **nach jedem
späteren `./svc.sh install` erneut**, weil die plist dabei neu erzeugt wird:

```sh
cd ~/actions-runner
plist=~/Library/LaunchAgents/$(basename "$(cat .service)")
/usr/libexec/PlistBuddy -c 'Add :KeepAlive bool true' "$plist" \
  || /usr/libexec/PlistBuddy -c 'Set :KeepAlive true' "$plist"
./svc.sh stop && ./svc.sh start
/usr/libexec/PlistBuddy -c 'Print :KeepAlive' "$plist"   # Soll: true
```

### 2.4 Abschlussprüfung am Gerät

Einmalig den Repo-Checkout anlegen (direkt unter dem Home-Verzeichnis,
§2.1), dann den strikten Preflight fahren:

```sh
cd ~ && git clone https://github.com/NikolayDA/picture_helper.git
cd ~/picture_helper
python3 scripts/abnahme_preflight.py --platform macos-arm64 --hardening-strict
```

Soll-Ausgabe: alle Zeilen `ok` (`python`/`venv`/`speicher`/`session`/`gl`/
`qt-gl`/`netz` und `[haertung] ok: sleep-schutz`, `dienst-neustart`),
Abschlusszeile „Runner ist einsatzbereit." – erster Lauf wegen des
Qt-Runtime-Baus bis zu 7 Minuten.

---

## 3. Raspberry Pi (Linux arm64) neu aufsetzen

### 3.1 Betriebssystem, Pakete und Checkout

Raspberry Pi OS **mit Desktop** (Debian 12, 64-bit) installieren – die
Qt-/GL-Systembibliotheken der Desktop-Session sind Voraussetzung. Der im
Imager bzw. Erststart-Assistenten angelegte Benutzer ist der
Runner-Benutzer (§1). Dann:

```sh
sudo apt update
sudo apt install -y git python3-venv python3-pyqt6 libfuse2
python3 --version   # Soll: ≥ 3.10
```

Warum diese Pakete: `python3-venv` braucht der Preflight für seine venvs;
`python3-pyqt6` zieht die Qt-/XCB-Systembibliotheken automatisch mit, die
auch die PyQt6-Wheels der Prüf-venvs zur Laufzeit brauchen
([`INSTALL_LINUX.md`](../INSTALL_LINUX.md)); `libfuse2` braucht der direkte
AppImage-Start im Abnahme-Smoke.

Zwei Einstellungen in `sudo raspi-config`:

- **Desktop-Autologin** (*System Options* → *Boot / Auto Login* →
  *Desktop Autologin*) – sonst existiert nach einem Reboot keine grafische
  Sitzung und jede GL-Prüfung fällt.
- **SSH aktivieren** (*Interface Options* → *SSH*; alternativ beim Flashen
  im Raspberry Pi Imager vorkonfigurieren) – für die Reboot-Probe (§3.5)
  und die Fernwartung.

Einmalig den Repo-Checkout für die manuellen Prüfschritte anlegen (der
Heartbeat selbst checkt in seinen Jobs eigenständig aus):

```sh
cd ~ && git clone https://github.com/NikolayDA/picture_helper.git
```

### 3.2 Eng begrenztes sudo für den .deb-Smoke

Der Abnahme-Lauf installiert/entfernt das `bgremover`-Paket; der
Runner-Benutzer braucht dafür **nur** diese zwei Kommandos passwortlos
([`RELEASE_AUTOMATION.md`](RELEASE_AUTOMATION.md) §3 – kein allgemeines
NOPASSWD). Den Block **als der Runner-Benutzer** ausführen – `$(id -un)`
landet wörtlich in der sudoers-Datei; als anderer Benutzer ausgeführt,
bekäme der falsche Account die Rechte und der Preflight-Check `deb-sudo`
fiele trotzdem:

```sh
printf '%s ALL=(root) NOPASSWD: /usr/bin/apt-get install *, /usr/bin/dpkg -r bgremover\n' "$(id -un)" \
  | sudo tee /etc/sudoers.d/abnahme >/dev/null
sudo chmod 440 /etc/sudoers.d/abnahme
sudo visudo -c   # Muss "parsed OK" melden
# Gegenprobe - exakt die zwei Prüfungen des Preflight-Checks "deb-sudo";
# beide müssen ohne Passwortabfrage mit Exit 0 enden:
sudo -n -l "$(which apt-get)" install bgremover
sudo -n -l "$(which dpkg)" -r bgremover
```

### 3.3 Runner registrieren und als Dienst einrichten

Registrierungsblock aus der GitHub-UI ausführen (§1), dabei
`--name raspberrypi` wählen. Danach als systemd-**System**-Dienst (mit sudo –
anders als auf dem Mac):

```sh
cd ~/actions-runner
sudo ./svc.sh install
sudo ./svc.sh start
sudo ./svc.sh status
```

`cat .service` nennt die erzeugte Unit
(`actions.runner.<owner>-<repo>.<name>.service`, hier also
`actions.runner.NikolayDA-picture_helper.raspberrypi.service`).

### 3.4 Drop-in: grafische Sitzung und Neustart-Policy (Pflicht)

Der Dienst braucht die Umgebungsvariablen der grafischen Sitzung und eine
Restart-Policy; beides kommt in ein systemd-Drop-in, das ein späteres
`svc.sh install` überlebt. **In einem Terminal der Desktop-Sitzung** (nicht
über eine nackte SSH-Shell – dort fehlen die Variablen) zuerst die Ist-Werte
erfassen:

```sh
printf 'DISPLAY=%s\nWAYLAND_DISPLAY=%s\nXDG_RUNTIME_DIR=%s\n' \
  "${DISPLAY:-}" "${WAYLAND_DISPLAY:-}" "${XDG_RUNTIME_DIR:-}"
id -u
```

Dann das Drop-in schreiben. Der Block übernimmt die Werte der aktuellen
Sitzung automatisch (Wayland-Standard von Raspberry Pi OS Bookworm; für eine
X11-Session stattdessen `Environment=DISPLAY=:0` und
`Environment=XAUTHORITY=/home/<benutzer>/.Xauthority` eintragen, vgl.
[`RELEASE_AUTOMATION.md`](RELEASE_AUTOMATION.md) §2.1). Als eigene Datei
`10-abnahme.conf` angelegt, damit kein vorhandenes `override.conf`
überschrieben wird:

```sh
cd ~/actions-runner
unit="$(cat .service)"
sudo mkdir -p "/etc/systemd/system/${unit}.d"
sudo tee "/etc/systemd/system/${unit}.d/10-abnahme.conf" >/dev/null <<EOF
[Service]
Environment=WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-wayland-0}
Environment=XDG_RUNTIME_DIR=/run/user/$(id -u)
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus
Restart=always
RestartSec=10
EOF
sudo systemctl daemon-reload
sudo ./svc.sh stop && sudo ./svc.sh start
```

Prüfen (funktioniert auch in einer späteren, frischen Shell):

```sh
cd ~/actions-runner
systemctl show "$(cat .service)" -p User -p Environment
systemctl show "$(cat .service)" -p Restart --value   # Soll: always
```

Der Preflight akzeptiert als Restart-Policy `always`, `on-failure` oder
`on-abnormal`; alles andere (insbesondere das Vorlagen-Default `no`) ist ein
Befund.

Optional, falls `needrestart` installiert ist (verhindert, dass ein
`apt upgrade` den Runner-Dienst mitten in einem Job neu startet – offizielles
Rezept der GitHub-Doku):

```sh
echo '$nrconf{override_rc}{qr(^actions\.runner\..+\.service$)} = 0;' \
  | sudo tee /etc/needrestart/conf.d/actions_runner_services.conf
```

### 3.5 Reboot-Probe (einmalig, Pflicht)

Belegt Autologin, Session-Durchreichung, Dienststart und Restart-Policy in
einem Zug ([`RELEASE_AUTOMATION.md`](RELEASE_AUTOMATION.md) §2.2):

```sh
sudo reboot
```

Nach dem Hochfahren, **ohne** manuelle Anmeldung, per SSH:

```sh
cd ~/actions-runner
systemctl is-active "$(cat .service)"                 # Soll: active
systemctl show "$(cat .service)" -p Restart --value   # Soll: always
```

Dann den Heartbeat von Hand starten (§4) – erst dessen grüner
`Heartbeat Linux aarch64`-Job ist der bindende Nachweis, dass der **Dienst**
(nicht die SSH-Shell) die Sitzung sieht. Ergebnis und Datum im Betriebs-Issue
[#939](https://github.com/NikolayDA/picture_helper/issues/939) notieren.

Hinweis für Handläufe über SSH: `scripts/abnahme_preflight.py` liest die
Umgebung des **eigenen** Prozesses. Vor einem manuellen Aufruf über SSH also
exakt die Werte exportieren, die im Drop-in `10-abnahme.conf` stehen
(Wayland-Beispiel; bei einer X11-Session stattdessen
`export DISPLAY=… XAUTHORITY=…`):

```sh
export WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/$(id -u)
cd ~/picture_helper
python3 scripts/abnahme_preflight.py --platform linux-arm64 --hardening-strict
```

---

## 4. Abschluss: Repository-Konfiguration und Erst-Heartbeat

Auf dem Arbeitsrechner. Der Heartbeat verlangt die Repository-Variable
`RUNNER_HEARTBEAT_ISSUE` (Betriebs-Issue als Alarmkanal, aktuell `939`) –
ohne sie bricht die Auswertung absichtlich vor der Messung ab. Bestand
prüfen bzw. setzen:

```sh
REPO=NikolayDA/picture_helper
gh variable list --repo "$REPO"
# Falls sie fehlt:
gh variable set RUNNER_HEARTBEAT_ISSUE --repo "$REPO" --body "939"
```

`ABNAHME_X86_64_ENABLED` darf dabei **nicht auf `true`** stehen, solange
kein x86_64-Gerät existiert (jeder andere Wert wirkt wie „nicht gesetzt") –
sonst meldet jeder Lauf einen Ausfall, den es nicht gibt. Danach den
Erst-Heartbeat starten und abwarten (Kommandos in §0.2). Grün = beide Geräte
angenommen **und** bestanden; fertig.

Für geplante Wartungsfenster (Neuaufsetzen des zweiten Geräts, OS-Updates)
den Heartbeat **befristet** pausieren und danach die Pause entfernen
([`RELEASE_AUTOMATION.md`](RELEASE_AUTOMATION.md) §6.1/§7):

```sh
REPO=NikolayDA/picture_helper
gh variable set RUNNER_HEARTBEAT_PAUSED --repo "$REPO" --body "true"
gh variable set RUNNER_HEARTBEAT_PAUSED_UNTIL --repo "$REPO" --body "2026-12-31"  # Enddatum anpassen
# … Eingriff …
gh variable delete RUNNER_HEARTBEAT_PAUSED --repo "$REPO"
gh variable delete RUNNER_HEARTBEAT_PAUSED_UNTIL --repo "$REPO"
```

---

## 5. Wiederbeleben statt neu aufsetzen

Bevor ein „offline"-Runner neu registriert wird
([`RELEASE_AUTOMATION.md`](RELEASE_AUTOMATION.md) §6):

| Symptom | Abhilfe |
|---|---|
| `status=offline`, Gerät läuft | Dienst neu starten: macOS `cd ~/actions-runner && ./svc.sh stop && ./svc.sh start`; Pi `sudo ./svc.sh stop && sudo ./svc.sh start` |
| Mac nach Neustart offline | Am Gerät **anmelden** – der LaunchAgent lebt in der GUI-Sitzung und startet erst mit ihr |
| Heartbeat rot: `session`/`gl`/`qt-gl` | Pi: Autologin/Drop-in prüfen (§3.4); Mac: Konsolenbenutzer prüfen (§2.2). Folgt `qt-gl` mit „Übersprungen" auf einen `session`-/`gl`-Befund, zuerst diesen beheben |
| Heartbeat rot: `qt-gl` Stufe `plugin`, Sitzung ist aber da | Ein im Profil des Runner-Benutzers gesetztes `QT_QPA_PLATFORM` (z. B. `offscreen`) entfernen – die Sonde akzeptiert nur die Sitzungs-Plugins `cocoa`/`xcb`/`wayland`/`wayland-egl` |
| Heartbeat rot: `qt-gl` Stufe `renderer` nach einem Treiber-/Mesa-Update | Das Gerät rendert nur noch in Software (llvmpipe & Co.) – GPU-Treiber der Desktop-Session reparieren; ein Software-Renderer gilt nirgends als Hardware-Nachweis |
| Heartbeat rot: `sleep-schutz`, obwohl `caffeinate` läuft | Der Wrapper muss **beide** Schlafarten halten (`caffeinate -dimsu`, nicht nur `-i`) und selbst der Assertion-Eigentümer sein |
| Heartbeat rot: `sleep-schutz`/`dienst-neustart` | §2.3 bzw. §3.4 erneut anwenden – `KeepAlive` überlebt kein `svc.sh install` |
| Runner aus der GitHub-Liste verschwunden | Mehr als 14 Tage offline, von GitHub entfernt → Registrierung und Dienst (§2/§3) komplett wiederholen |

Ein FAIL-Kommentar im Betriebs-Issue
[#939](https://github.com/NikolayDA/picture_helper/issues/939) ist nie
Rauschen, aber der Text unterscheidet: „mit einem anderen Lauf belegt"
während einer laufenden Abnahme ist kein Ausfall
([`RELEASE_AUTOMATION.md`](RELEASE_AUTOMATION.md) §7); jeden anderen Befund
für `Mac` oder `raspberrypi` zeitnah behandeln – der Heartbeat kommentiert
nur im Fehlerfall.
