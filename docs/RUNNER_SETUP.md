# Runner-Neuaufbau: MacBook und Raspberry Pi (Kochbuch)

Schritt-für-Schritt-Anleitung, um die beiden Self-hosted Runner der
Release-Abnahme auf einem **frisch installierten** Gerät wieder einzurichten –
inklusive Kommandos, mit denen sich vorab prüfen lässt, ob und in welchem
Zustand die Runner bereits registriert sind.

Dieses Dokument ist ein **Kochbuch**, keine neue Regelquelle: Verbindlich sind
[`RELEASE_AUTOMATION.md`](RELEASE_AUTOMATION.md) (§2 Registrierung, §2.1/§2.2
Sitzung/Härtung, §3 Sicherheits-Checkliste, §6 Wartung, §7 Heartbeat) und der
Prüfcode in [`scripts/abnahme_preflight.py`](../scripts/abnahme_preflight.py).
Bei Widerspruch gelten diese Quellen. Alle Soll-Zustände hier sind exakt die
Bedingungen, die der tägliche Heartbeat (`--hardening-strict`) durchsetzt.

Zielzustand (aus [`RELEASE_AUTOMATION.md`](RELEASE_AUTOMATION.md) §1):

| Gerät | Runner-Name | Labels | Dienstform |
|---|---|---|---|
| MacBook (Apple Silicon) | `Mac` | `self-hosted`, `macOS`, `ARM64` | LaunchAgent des angemeldeten Benutzers |
| Raspberry Pi 5 (Debian 12, Desktop) | `raspberrypi` | `self-hosted`, `Linux`, `ARM64` | systemd-System-Dienst |

---

## 0. Vorab prüfen: Sind die Runner schon da, und wie ist ihr Status?

### 0.1 Aus der Ferne (Repository-Sicht)

Braucht `gh` mit einem Konto, das Admin-Rechte am Repository hat (als Owner
reicht das normale `gh auth login`):

```sh
REPO=NikolayDA/picture_helper
gh api "repos/$REPO/actions/runners" --jq '
  if .total_count == 0 then "Keine Self-hosted Runner registriert."
  else .runners[]
    | "\(.name)\tstatus=\(.status)\tbusy=\(.busy)\tlabels=\([.labels[].name] | join(","))"
  end'
```

Erwartete Ausgabe bei intaktem Bestand (Reihenfolge egal):

```text
Mac	status=online	busy=false	labels=self-hosted,macOS,ARM64,…
raspberrypi	status=online	busy=false	labels=self-hosted,Linux,ARM64,…
```

Einordnung:

- `status=offline` → Gerät oder Dienst ist unten; erst §5 (Wiederbelebung)
  versuchen, bevor neu registriert wird.
- Runner fehlt in der Liste → neu registrieren (§2 bzw. §3). GitHub entfernt
  einen Runner, der länger nicht verbunden war, automatisch
  ([`RELEASE_AUTOMATION.md`](RELEASE_AUTOMATION.md) §6).
- `status=online` sagt nur „verbunden", **nicht** „einsatzbereit" – die
  eigentliche Bereitschaft belegt erst der Heartbeat (0.2) bzw. der
  Preflight auf dem Gerät (0.3).

### 0.2 Ohne Admin-API: Heartbeat von Hand starten

Der tägliche Heartbeat ist die verbindliche Bereitschaftsprüfung
([`RELEASE_AUTOMATION.md`](RELEASE_AUTOMATION.md) §7). Ein manueller Lauf
beantwortet „vorhanden **und** einsatzbereit?" in unter einer Minute:

```sh
REPO=NikolayDA/picture_helper
gh workflow run runner-heartbeat.yml --repo "$REPO"
sleep 10
gh run watch --repo "$REPO" \
  "$(gh run list --repo "$REPO" --workflow runner-heartbeat.yml --limit 1 \
     --json databaseId --jq '.[0].databaseId')" --exit-status
```

- **Grün** (≈ 40 s): beide Runner haben den Job angenommen und die strikte
  Bereitschaftsprüfung bestanden – nichts zu tun.
- **Rot nach ~15 min**: mindestens ein Runner nimmt keine Jobs an (offline
  oder belegt); der Befund steht als Kommentar im Betriebs-Issue
  [#939](https://github.com/NikolayDA/picture_helper/issues/939).
- **Rot, aber Runner-Job lief**: Das Joblog des jeweiligen
  `Heartbeat …`-Jobs nennt die gescheiterte Prüfung (`[preflight]`/
  `[haertung]`-Zeilen) – Abhilfe je Befund in §2–§3 dieses Dokuments.

### 0.3 Auf dem Gerät selbst

Im Runner-Verzeichnis (`~/actions-runner`):

```sh
# macOS:
cd ~/actions-runner && ./svc.sh status

# Raspberry Pi:
cd ~/actions-runner
systemctl is-active "$(cat .service)"
systemctl show "$(cat .service)" -p Restart --value   # Soll: always
```

Vollständige Bereitschafts- und Härtungsprüfung (identisch zum Heartbeat) im
Repo-Checkout auf dem Gerät:

```sh
# macOS:
python3 scripts/abnahme_preflight.py --platform macos-arm64 --hardening-strict
# Raspberry Pi:
python3 scripts/abnahme_preflight.py --platform linux-arm64 --hardening-strict
```

Beim allerersten Aufruf baut die `qt-gl`-Sonde einmalig ihre schlanke
Qt-Runtime (`~/.cache/bgremover/preflight-qt`, bis zu 7 Minuten); danach ist
der Aufruf schnell. Nur die Härtung – ohne Runtime-Bau, ohne Checkout-Pflicht
auf dem Zielsystempfad – prüft dieser Schnelltest:

```sh
# Im Repo-Checkout; auf dem Mac "macos-arm64", auf dem Pi "linux-arm64":
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
  (§3); der Runner wird unter diesem Benutzer eingerichtet und dieser
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
  (Raspberry Pi OS **mit Desktop** bringt sie mit).

Die Registrierung selbst läuft für beide Geräte gleich
([`RELEASE_AUTOMATION.md`](RELEASE_AUTOMATION.md) §2): GitHub → Repository →
**Settings → Actions → Runners → New self-hosted runner**, Plattform wählen,
und die dort angezeigten Befehle (Download, Prüfsumme, `./config.sh` mit dem
angezeigten Token) auf dem Gerät ausführen. Das Registrierungs-Token ist nur
**kurz gültig** – den Block also erst öffnen, wenn das Gerät bereitsteht. Bei
`./config.sh` gilt:

- **Labels: die Standard-Labels unverändert übernehmen.** Die Workflows
  adressieren exakt `[self-hosted, macOS, ARM64]` bzw.
  `[self-hosted, Linux, ARM64]`; beide Label-Sätze entstehen automatisch.
- **Runner-Name:** `Mac` bzw. `raspberrypi` (Wiedererkennbarkeit in Läufen
  und Betriebs-Issue; technisch erzwungen wird der Name nicht).
- Übrige Fragen (Arbeitsordner, Runner-Gruppe) mit Enter bestätigen.

---

## 2. MacBook (macOS arm64) neu aufsetzen

### 2.1 Systemvoraussetzungen

```sh
xcode-select --install   # git + python3 (Command Line Tools); überspringt sich, wenn vorhanden
python3 --version        # Soll: ≥ 3.10
```

### 2.2 Runner registrieren und als Dienst einrichten

Registrierungsblock aus der GitHub-UI ausführen (§1), dabei
`--name Mac` wählen. Danach – **als der angemeldete Runner-Benutzer, ohne
sudo** (der Dienst muss ein LaunchAgent der GUI-Sitzung werden, kein
LaunchDaemon):

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
Display-Schlaf zählt mit, die Abnahme erzeugt native Screenshots):

```sh
sudo pmset -c sleep 0 displaysleep 0
# Nur für einen zugeklappt betriebenen MacBook zusätzlich:
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

Im Repo-Checkout (einmalig `git clone
https://github.com/NikolayDA/picture_helper.git && cd picture_helper`):

```sh
python3 scripts/abnahme_preflight.py --platform macos-arm64 --hardening-strict
```

Soll-Ausgabe: alle Zeilen `ok` (`python`/`venv`/`speicher`/`session`/`gl`/
`qt-gl`/`netz` und `[haertung] ok: sleep-schutz`, `dienst-neustart`),
Abschlusszeile „Runner ist einsatzbereit." – erster Lauf wegen des
Qt-Runtime-Baus bis zu 7 Minuten.

---

## 3. Raspberry Pi (Linux arm64) neu aufsetzen

### 3.1 Betriebssystem und Pakete

Raspberry Pi OS **mit Desktop** (Debian 12, 64-bit) installieren – die
Qt-/GL-Systembibliotheken der Desktop-Session sind Voraussetzung. Dann:

```sh
sudo apt update
sudo apt install -y git python3-venv
python3 --version   # Soll: ≥ 3.10
```

**Desktop-Autologin** aktivieren, sonst existiert nach einem Reboot keine
grafische Sitzung und jede GL-Prüfung fällt:
`sudo raspi-config` → *System Options* → *Boot / Auto Login* →
*Desktop Autologin*.

### 3.2 Eng begrenztes sudo für den .deb-Smoke

Der Abnahme-Lauf installiert/entfernt das `bgremover`-Paket; der
Runner-Benutzer braucht dafür **nur** diese zwei Kommandos passwortlos
([`RELEASE_AUTOMATION.md`](RELEASE_AUTOMATION.md) §3 – kein allgemeines
NOPASSWD):

```sh
printf '%s ALL=(root) NOPASSWD: /usr/bin/apt-get install *, /usr/bin/dpkg -r bgremover\n' "$(id -un)" \
  | sudo tee /etc/sudoers.d/abnahme >/dev/null
sudo chmod 440 /etc/sudoers.d/abnahme
sudo visudo -c   # Muss "parsed OK" melden
# Gegenprobe (beide müssen ohne Passwortabfrage "erlaubt" zeigen):
sudo -n -l /usr/bin/apt-get install bgremover
sudo -n -l /usr/bin/dpkg -r bgremover
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
(`actions.runner.<repo>.<name>.service`).

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

Prüfen (Benutzer, Umgebung, Policy):

```sh
systemctl show "$unit" -p User -p Environment
systemctl show "$unit" -p Restart --value   # Soll: always
```

Der Preflight akzeptiert als Restart-Policy `always`, `on-failure` oder
`on-abnormal`; alles andere (insbesondere das Vorlagen-Default `no`) ist ein
Befund.

### 3.5 Reboot-Probe (einmalig, Pflicht)

Belegt Autologin, Session-Durchreichung, Dienststart und Restart-Policy in
einem Zug ([`RELEASE_AUTOMATION.md`](RELEASE_AUTOMATION.md) §2.2):

```sh
sudo reboot
# Nach dem Hochfahren, OHNE manuelle Anmeldung, per SSH:
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
exportieren, was das Drop-in dem Dienst gibt:

```sh
export WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/$(id -u)
python3 scripts/abnahme_preflight.py --platform linux-arm64 --hardening-strict
```

---

## 4. Abschluss: Repository-Konfiguration und Erst-Heartbeat

Der Heartbeat verlangt die Repository-Variable `RUNNER_HEARTBEAT_ISSUE`
(Betriebs-Issue als Alarmkanal, aktuell `939`) – ohne sie bricht die
Auswertung absichtlich vor der Messung ab. Bestand prüfen bzw. setzen:

```sh
REPO=NikolayDA/picture_helper
gh variable list --repo "$REPO"
# Falls sie fehlt:
gh variable set RUNNER_HEARTBEAT_ISSUE --repo "$REPO" --body "939"
```

`ABNAHME_X86_64_ENABLED` darf dabei **nicht** gesetzt sein, solange kein
x86_64-Gerät existiert – sonst meldet jeder Lauf einen Ausfall, den es nicht
gibt. Danach den Erst-Heartbeat starten und abwarten (Kommandos in §0.2).
Grün = beide Geräte angenommen **und** bestanden; fertig.

Für geplante Wartungsfenster (Neuaufsetzen des zweiten Geräts, OS-Updates)
den Heartbeat **befristet** pausieren und danach die Pause entfernen
([`RELEASE_AUTOMATION.md`](RELEASE_AUTOMATION.md) §6.1/§7):

```sh
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
| Heartbeat rot: `session`/`gl`/`qt-gl` | Pi: Autologin/Drop-in prüfen (§3.4); Mac: Konsolenbenutzer prüfen (§2.2) |
| Heartbeat rot: `sleep-schutz`/`dienst-neustart` | §2.3 bzw. §3.4 erneut anwenden – `KeepAlive` überlebt kein `svc.sh install` |
| Runner aus der GitHub-Liste verschwunden | Zu lange offline, von GitHub entfernt → §2/§3 komplett wiederholen |

Ein Befund für `Mac` oder `raspberrypi` im Betriebs-Issue
[#939](https://github.com/NikolayDA/picture_helper/issues/939) ist immer
echt und gehört zeitnah behandelt – der Heartbeat kommentiert nur im
Fehlerfall.
