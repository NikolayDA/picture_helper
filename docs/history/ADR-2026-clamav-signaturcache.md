# ADR-2026: ClamAV-Signaturbezug vom Kandidatenbau entkoppeln (versionierter Cache)

**Status:** Akzeptiert
**Datum:** 2026-08-13
**Entscheider:** Repository-Owner
**Bezug:** #731, Epic #741, Kriterium `MALWARE-01`

## Kontext

Der Virenscan der fünf Release-Artefakte (`release-linux.yml`) rief bislang
auf jedem der drei Matrix-Legs live `freshclam` auf, bevor `clamscan` gegen
`dist/` lief. In der Praxis lieferte das nie einen echten Scan mit geladener
Datenbank:

| Plattform | Fehlerbild | Ursache |
|---|---|---|
| Linux x86_64 / arm64 | `freshclam` bricht vor dem Bezug ab | Ein durch `apt install clamav` bereits laufender `clamav-freshclam`-Systemdienst hält denselben Log-/PID-Pfad wie der manuelle Aufruf – ein reiner Lock-Konflikt, kein Mirror-Problem. |
| macOS arm64 | Datenbankbezug schlägt fehl | `NULL X509 store` beim TLS-Handshake zum öffentlichen Mirror aus dem Homebrew-`freshclam`. |

Der bisherige Workflow-Kommentar behauptete, alle drei Legs scheiterten am
selben instabilen öffentlichen Mirror. Das ist falsch dokumentiert: Linux
scheitert nie am Mirror selbst, sondern an einer lokalen Ressourcenkollision;
nur macOS hat ein echtes Netzwerk-/TLS-Problem. Diese Falschdiagnose hätte
jeden Reparaturversuch am Mirror in die falsche Richtung gelenkt.

Weil der Update-Schritt `continue-on-error: true` trug und ein fehlender
Datenbankstand den Scan nur mit sichtbarer Warnung übersprang, lieferte der
Schritt in jedem realen Lauf bislang **keinen** tatsächlichen Scan – nur die
Illusion eines vorhandenen Sicherheitsnetzes.

## Entscheidung

Wir wählen **Option A: versionierter, rotierender Datenbank-Cache**, getrennt
vom Kandidatenbau erzeugt.

Ein neuer, unabhängiger Workflow (`clamav-db-refresh.yml`) holt die
Signaturdatenbank wöchentlich (plus manuell per `workflow_dispatch`) auf
einem einzelnen `ubuntu-latest`-Runner und legt sie unter einem **niemals
wiederverwendeten** Cache-Key (`clamav-db-v1-<github.run_id>`) ab –
GitHub-Actions-Caches sind unveränderlich, ein fester Schlüssel würde also nie
aktualisiert. `release-linux.yml` löst die „Rotation" über eine
`restore-keys`-Präfixsuche auf: Der jeweils neueste passende Cache-Eintrag
gewinnt, ganz ohne dass der Kandidatenbau selbst je `freshclam` aufruft.

Diese Entkopplung behebt beide dokumentierten Ursachen strukturell:

- **Linux-Lock:** Der Seed-Job stoppt den konkurrierenden
  `clamav-freshclam`-Systemdienst vor dem manuellen `freshclam`-Aufruf – der
  Lock-Konflikt entsteht so gar nicht erst.
- **macOS-X509:** Entfällt vollständig, weil kein macOS-Leg mehr selbst
  `freshclam` aufruft. Die Signaturdatenbank (`main.cvd`/`daily.cvd`/
  `bytecode.cvd`) ist plattformunabhängige, signierte Binärdaten – derselbe,
  auf Linux geholte Cache-Inhalt wird unverändert in den macOS-Homebrew-
  Datenbankpfad kopiert.

Ein Kandidatenbau, der auf keinen Cache-Eintrag trifft (Seed-Job noch nie
gelaufen oder Cache durch GitHubs 7-Tage-Leerlauf-Eviction entfernt), meldet
den Scan als **UNAVAILABLE** (sichtbare `::warning::`) und überspringt ihn –
bewusst nicht blockierend, analog zur bestehenden fail-safe-Vision-
Vorbewertung in `release-abnahme.yml` und zum bestehenden Kriterium
`MALWARE-01` („Scannerzustand PASS, FAIL oder sichtbar nicht verfügbar").
Ein tatsächlicher Fund bei vorhandener Datenbank blockiert weiterhin hart
(`clamscan`-Exitcode 1). Eine Datenbank älter als 14 Tage erzeugt zusätzlich
eine sichtbare Altersnwarnung, ohne den Build zu brechen.

## Erwogene Optionen

### A – Versionierter Datenbank-Cache (gewählt)

| Dimension | Bewertung |
|---|---|
| Komplexität | Niedrig-Mittel (ein zusätzlicher Workflow + Cache-Restore-Schritt) |
| Determinismus | Hoch – Kandidatenbau hängt nie mehr an einem Live-Mirror-Aufruf |
| Betrieb | Ein wöchentlicher Cron-Job; manueller Re-Seed über `workflow_dispatch` |
| Root-Cause-Fix | Löst Linux-Lock direkt; macht macOS-X509 gegenstandslos |

**Vorteile:** Keine neue Infrastruktur außerhalb von GitHub Actions, nutzt
denselben Cache-Mechanismus wie andere Build-Caches im Projekt, entkoppelt
Mirror-Flakiness vollständig vom teuren Kandidatenbau.
**Nachteile:** Der Scan ist nie „taufrisch" (bis zu ~1 Woche alt zwischen
Refreshs) – durch die 14-Tage-Alterswarnung und den wöchentlichen Cron aber
begrenzt und sichtbar.

### B – Kontrollierter Mirror

Verworfen: verlagert den Betriebsaufwand nur auf einen selbst betriebenen
Mirror (Verfügbarkeit, Aktualisierung, Vertrauensgrenze), ohne die
Linux-Lock-Ursache zu adressieren.

### C – Zentraler Scan-Dienst

Verworfen für jetzt: stärkste Isolation, aber neue, separat zu betreibende
Infrastruktur mit eigener Verfügbarkeits- und Datenabfluss-Bewertung – Aufwand
steht in keinem Verhältnis zum Nutzen gegenüber Option A, solange der
öffentliche ClamAV-Mirror für einen wöchentlichen Einzelabruf ausreicht.

### D – ClamAV entfernen

Verworfen: Die eigentliche Ursache (Lock-Konflikt) ist trivial behebbar; ein
funktionierender, wenn auch zusätzlicher Scan liefert realen Zusatzwert über
`scan_release_artifacts.py`/`pip-audit`/CodeQL hinaus (Signaturbasis statt
reiner Muster-/Metadatenprüfung).

## Sicherheitsvertrag

- Ein nicht verfügbarer oder veralteter Scanner weist den Release nie als
  „sauber gescannt" aus, sondern sichtbar als `UNAVAILABLE`/gealtert.
- Ein technischer Scan-Ausfall (Cache-Miss) ist **nicht blockierend** – wie
  bisher, konsistent mit `MALWARE-01` (`SHOULD`, `waiver_allowed: true`).
- Ein Malware-Fund bei vorhandener Datenbank ist **immer hart blockierend**.
- Evidenz (Quelle, Engine-Version, Signaturversion, Signaturdatum) landet im
  Job-Log jedes Build-Legs (`clamscan --version`), analog zu den bestehenden
  Provenienz-Logs desselben Workflows.
- `clamscan` liest die Datenbank im Kandidatenbau ausschließlich über
  `--database clamav-db-cache` (Codex-Review auf PR #779): kein Bezug auf
  einen plattform- oder formelabhängigen Systempfad (Homebrews Standard ist
  `var/lib/clamav`, nicht `share/clamav`) und keine Kopie in einen vom
  auto-gestarteten `clamav-freshclam`-Dienst mitgenutzten Ort mehr nötig –
  der Dienst wird auf dem Linux-Bein zusätzlich vorsorglich gestoppt.

## Konsequenzen

- `release-linux.yml` ruft nie mehr live `freshclam` auf; ein neuer,
  unabhängiger Workflow `clamav-db-refresh.yml` übernimmt den Bezug.
- Der irreführende Kommentar („alle drei Legs scheitern am selben Mirror")
  ist korrigiert.
- Der erste Kandidatenlauf nach diesem Wechsel trifft auf keinen Cache
  (Seed-Job muss zuerst laufen) – erwartet `UNAVAILABLE`, kein Fehlzustand.
- Wiederanlauf bei leerem/veraltetem Cache: `clamav-db-refresh.yml` manuell
  per `workflow_dispatch` anstoßen, danach den Kandidatenlauf neu starten
  (siehe Wiederanlaufmatrix in [`RELEASE_PROCESS.md`](../RELEASE_PROCESS.md)).

## Umsetzung

- [x] Workflow-Kommentar korrigiert (#731)
- [x] `clamav-db-refresh.yml` (Seed-Job, rotierender Cache, Linux-Lock-Fix)
- [x] `release-linux.yml` auf Cache-Restore statt Live-Fetch umgestellt
- [x] Evidenz (Quelle/Engine/Signaturversion/-datum) im Job-Log je Leg
- [x] Alterswarnung (> 14 Tage) und UNAVAILABLE-Zustand nicht blockierend
- [ ] Erster echter Kandidatenlauf mit Cache-Treffer auf allen drei Legs
      (Nachweis für `MALWARE-01`, aussteht bis zum nächsten Kandidatenbau)
