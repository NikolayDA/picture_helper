# Release-Runbook

**Owner:** Repository-Owner
**Ausführende Rollen:** Release-Owner, CI, Hardware-Abnahme, Security-Owner
**Anwendungsfall:** regulärer Release, Hotfix und Wiederanlauf eines fehlgeschlagenen Releases
**Letzte Aktualisierung:** 2026-08-01
**Letzte Übung:** [lokaler Dry-Run vom 2026-08-01](history/RELEASE-RUNBOOK-DRY-RUN-2026-08-01.md)

## Zweck und verbindliche Quellen

Dieses Dokument ist die einzige kanonische Ablaufbeschreibung für Releases.
Ein Release ist erst abgeschlossen, wenn Schritt 9 dokumentiert ist.

| Gegenstand | Verbindliche Quelle |
|---|---|
| Paketversion | `project.version` in [`pyproject.toml`](../pyproject.toml) |
| Bereits veröffentlichte Version | [GitHub Releases](https://github.com/NikolayDA/picture_helper/releases) und Tags |
| Kriterien, Statuswerte und Plattformumfang | [Versionierte Abnahme-Checkliste](RELEASE_ACCEPTANCE_CHECKLIST.md) |
| Hardware-Kommandos | [Packaging-Smokes](PACKAGING_SMOKE.md) |
| Runnerbetrieb und Labels | [Release-Automatisierung](RELEASE_AUTOMATION.md) |
| Release-Artefaktvertrag | [Manifest-ADR](history/ADR-2026-release-manifest-publish.md) |

Der Vertrag umfasst exakt fünf Dateien: Linux x86_64 AppImage und `.deb`, Linux
arm64 AppImage und `.deb` sowie macOS arm64 DMG. Windows ist nicht enthalten.
Linux x86_64 bleibt sichtbar pausiert, bis beide Hardwarekriterien tatsächlich
bestanden sind.

## Voraussetzungen und Evidenzablage

- `main` enthält sämtliche Release-Änderungen und ist lokal aktuell.
- `gh auth status` ist erfolgreich; Release-Owner darf Workflows starten und Releases verwalten.
- Die selbst gehosteten Runner `macos-arm64` und `linux-arm64` sind online und haben eine grafische Sitzung.
- Ein offenes Release-Issue dient als Entscheidungsprotokoll; seine Nummer wird als `RELEASE_ISSUE` verwendet.
- Kandidaten-, Abnahme- und Publish-Run-ID, vollständiger Commit-SHA, Tag und Manifestname werden im Issue notiert.
- Actions-Artefakte werden 90 Tage aufbewahrt. Ein abgelaufenes Artefakt darf nie durch einen anderen Lauf ersetzt werden.

Die Beispiele verwenden folgende Shell-Variablen. Werte immer aus der verlinkten
GitHub-Ansicht übernehmen, nicht erraten:

```bash
RELEASE_VERSION="X.Y.Z"
RELEASE_TAG="v${RELEASE_VERSION}"
RELEASE_ISSUE="ISSUE_NUMMER"
CANDIDATE_RUN_ID="RUN_ID"
ACCEPTANCE_RUN_ID="RUN_ID"
APPROVAL_ARTIFACT_NAME="release-approval-manifest-1"
```

## Ablauf

### 1. Release vorbereiten

**Trigger:** Der vereinbarte Funktionsumfang ist auf `main`, oder ein Hotfix ist
freigegeben.
**Owner:** Release-Owner.
**Input:** Release-Issue, gewünschte Version, aktueller `main`-Commit.

```bash
git fetch origin main --tags
git switch main
git pull --ff-only origin main
python -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])'
git log -1 --format='%H %s'
```

Prüfe, dass `CHANGELOG.md` und der geplante Release-Text Auswirkung,
unterstützte Plattformen, bekannte Einschränkungen sowie Upgrade- und
Rollback-Hinweis enthalten. Starte danach die Dokumentprüfung:

```bash
python scripts/release_contract.py validate-checklist \
  --checklist docs/RELEASE_ACCEPTANCE_CHECKLIST.md
python -m pytest tests/test_markdown_links.py -q
```

**Output/Evidenz:** Version, vollständiger Commit-SHA und Ergebnis der Dokumentprüfung im Release-Issue.
**Erwartetes Ergebnis:** Version ist eindeutig, Tag existiert noch nicht, Release Notes erfüllen `NOTES-01`.
**Fehler/Wiederanlauf:** Inkonsistenzen auf einem neuen PR beheben. Danach Schritt 1 vollständig wiederholen; nicht taggen.

### 2. Kandidatenstand einfrieren

**Trigger:** Schritt 1 ist grün.
**Owner:** Release-Owner; Prüfung durch CI.
**Input:** aktueller `main`-Commit und `release/path-policy.json`.

```bash
python scripts/verify_release_freeze.py \
  --output-provenance /tmp/release-freeze-provenance.json
git rev-parse HEAD
```

Der Laufkopf ist der Kandidat. Unbekannte oder kandidatenrelevante Änderungen
nach der abgeleiteten Basis blockieren fail-closed; ein manueller SHA-Ledger
wird nicht gepflegt.

**Output/Evidenz:** lokale Freeze-Provenienz als Vorprüfung; später die unveränderliche
`release-freeze-provenance-<attempt>` aus dem Kandidatenlauf.
**Erwartetes Ergebnis:** Policy, Basis, Pfade und Kandidaten-SHA sind widerspruchsfrei.
**Fehler/Wiederanlauf:** Pfadklassifikation oder Dokumentation per PR korrigieren und bei Schritt 1 neu beginnen.
Ein alter Kandidatenlauf bleibt historische Evidenz, wird aber nicht weiterverwendet.

### 3. Unveränderlichen Kandidaten bauen

**Trigger:** Freeze-Vorprüfung ist grün und der gewünschte SHA liegt auf `main`.
**Owner:** Release-Owner startet; CI baut.
**Input:** `main`, `with_ai=true`.

```bash
gh workflow run release-linux.yml --ref main -f with_ai=true
gh run list --workflow release-linux.yml --branch main --event workflow_dispatch --limit 5
gh run watch "$CANDIDATE_RUN_ID" --exit-status
gh run view "$CANDIDATE_RUN_ID" --json headSha,conclusion,url
```

Übernimm die Run-ID erst, nachdem `headSha` dem in Schritt 2 notierten Commit
entspricht. Der Workflow führt Full CI aus, baut exakt fünf Dateien und legt
Artefaktcontainer sowie Freeze-Provenienz mit IDs und Digests ab.

**Output/Evidenz:** `CANDIDATE_RUN_ID`, Run-URL, Commit-SHA und die Namen der Build-Artefakte im Issue.
**Erwartetes Ergebnis:** erfolgreicher `release-linux.yml`-Lauf auf exakt einem Commit.
**Fehler/Wiederanlauf:** Ein fehlgeschlagener oder abgelaufener Lauf wird nie umgedeutet.
Nach einer Code-/Dokumentänderung bei Schritt 1 beginnen; bei reinem Infrastrukturfehler darf
derselbe Workflow auf demselben unveränderten SHA neu gestartet werden, erhält aber eine neue Run-ID.

### 4. Kandidatenvertrag und Sicherheitsbefunde prüfen

**Trigger:** Schritt 3 ist erfolgreich.
**Owner:** Release-Owner; Malwarebefunde zusätzlich Security-Owner.
**Input:** Kandidatenlauf und dessen Actions-Artefakte.

```bash
gh api "repos/NikolayDA/picture_helper/actions/runs/${CANDIDATE_RUN_ID}/artifacts?per_page=100"
gh run view "$CANDIDATE_RUN_ID" --log
```

Prüfe `VERSION-01`, `FREEZE-01`, `BUILD-01`, `BUILD-02`, `PROVENANCE-01`
und `MALWARE-01`. Genau fünf Produktdateien müssen im Kandidatenvertrag stehen;
ihre Namen, Größen und SHA-256-Werte sind die spätere Veröffentlichungsquelle.
Ein Malware-Fund ist immer No-Go. Nicht verfügbare Scanner bleiben sichtbar
und erfordern die in der Checkliste erlaubte, begründete Entscheidung.

**Output/Evidenz:** Links auf Lauf, Kandidatenvertrag, Provenienz und Security-Entscheidung.
**Erwartetes Ergebnis:** keine zusätzliche oder fehlende Datei, keine ungebundene Provenienz, kein Malware-Fund.
**Fehler/Wiederanlauf:** Bei Vertrags- oder Hashfehler Kandidatenlauf verwerfen und Ursache per PR beheben.
Bei Scanner-Ausfall entscheidet der Security-Owner über Wiederholung oder ausdrücklich erlaubten Waiver.

### 5. Abnahme auf echter Hardware durchführen

**Trigger:** Schritt 4 ist freigegeben und die aktiven Runner sind online.
**Owner:** Hardware-Abnahme; Start durch Release-Owner.
**Input:** `CANDIDATE_RUN_ID`, Zielplattformen `alle`, Release-Issue.

```bash
gh workflow run release-abnahme.yml --ref main \
  -f run_id="$CANDIDATE_RUN_ID" \
  -f platforms=alle \
  -f dry_run=false \
  -f target_issue="$RELEASE_ISSUE"
gh run list --workflow release-abnahme.yml --branch main --event workflow_dispatch --limit 5
gh run watch "$ACCEPTANCE_RUN_ID" --exit-status
```

Die genaue Geräteprozedur steht in `PACKAGING_SMOKE.md`. Verbindlich sind die
stabilen IDs in `RELEASE_ACCEPTANCE_CHECKLIST.md`, darunter echter Start aus
dem Bundle, sichtbare Version, natives 3D, kontrolliertes Speichern/Neuladen
und menschlich geprüfte Screenshots. Vision-Auswertung ist nur Vorbewertung.

**Output/Evidenz:** Abschlussmatrix im Release-Issue, plattformspezifische `evidenz.json`, Screenshots und Run-URL.
**Erwartetes Ergebnis:** macOS arm64 und Linux arm64 sind `PASS`; Linux x86_64 bleibt `PENDING`, solange pausiert.
**Fehler/Wiederanlauf:** Fehlende Hardware, Hänger oder `FAIL` blockieren. Nach reinem Runnerfehler darf die Abnahme
mit derselben Kandidaten-Run-ID erneut laufen; fachliche Fehler erfordern Fix und neuen Kandidaten ab Schritt 1.

### 6. Freigabemanifest und Release-Instanz abnehmen

**Trigger:** Schritt 5 ist erfolgreich abgeschlossen.
**Owner:** Release-Owner.
**Input:** Abnahme-Run und `release-approval-manifest-<attempt>`.

```bash
mkdir -p /tmp/release-approval
gh run download "$ACCEPTANCE_RUN_ID" \
  -n "$APPROVAL_ARTIFACT_NAME" \
  -D /tmp/release-approval
python scripts/release_contract.py extract-instance \
  --manifest /tmp/release-approval/release-approval-manifest.json \
  --output /tmp/release-acceptance-instance.json
python scripts/release_contract.py validate-instance \
  --checklist docs/RELEASE_ACCEPTANCE_CHECKLIST.md \
  --instance /tmp/release-acceptance-instance.json \
  --through-phase pre-release
```

Prüfe im Manifest Checklisten-Version, vollständigen Commit, Checklisten-Hash,
alle stabilen IDs und Evidenzlinks. Ein Waiver braucht Owner, konkrete
releasebezogene Begründung und Evidenz; technisch nicht erlaubte Waiver und
`NOT_APPLICABLE` werden vom Vertrag abgewiesen.

**Output/Evidenz:** `ACCEPTANCE_RUN_ID`, exakter Manifestname, Manifest- und Instanzhash im Issue.
**Erwartetes Ergebnis:** sämtliche Pre-Release-`MUST` sind `PASS`; erlaubte offene Punkte sind sichtbar.
**Fehler/Wiederanlauf:** Manifest nie manuell editieren. Bei fehlender Evidenz Schritt 5 wiederholen;
bei Schema-/Bindungsfehler Ursache per PR beheben und mit neuem Kandidaten bei Schritt 1 starten.

### 7. Tag auf exakt den abgenommenen Commit setzen

**Trigger:** Go-Entscheidung in Schritt 6 ist protokolliert.
**Owner:** Release-Owner.
**Input:** Tag aus Manifest und dortiger `candidate.head_sha`.

```bash
CANDIDATE_SHA="VOLLSTAENDIGER_SHA_AUS_DEM_MANIFEST"
test "$(git rev-parse "$CANDIDATE_SHA")" = "$CANDIDATE_SHA"
git tag -a "$RELEASE_TAG" "$CANDIDATE_SHA" -m "Release $RELEASE_TAG"
test "$(git rev-parse "${RELEASE_TAG}^{commit}")" = "$CANDIDATE_SHA"
git push origin "$RELEASE_TAG"
```

**Output/Evidenz:** Tag-URL und aufgelöster vollständiger SHA im Issue.
**Erwartetes Ergebnis:** Tag zeigt bytegenau auf den vom Manifest gebundenen Kandidaten.
**Fehler/Wiederanlauf:** Falschen, noch nicht verwendeten Remote-Tag nur nach dokumentierter Owner-Freigabe löschen
und neu setzen. Sobald ein Release oder externer Download existiert, Tag nie verschieben; stattdessen Hotfix-Version.

### 8. Abgenommene Bytes veröffentlichen

**Trigger:** Schritt 7 ist verifiziert.
**Owner:** Release-Owner startet; CI veröffentlicht.
**Input:** Tag, Kandidaten-Run-ID, Abnahme-Run-ID und exakter Manifestname.

```bash
gh workflow run release-publish.yml --ref main \
  -f tag="$RELEASE_TAG" \
  -f candidate_run_id="$CANDIDATE_RUN_ID" \
  -f acceptance_run_id="$ACCEPTANCE_RUN_ID" \
  -f approval_artifact_name="$APPROVAL_ARTIFACT_NAME"
gh run list --workflow release-publish.yml --branch main --event workflow_dispatch --limit 5
```

Der Publish-Workflow baut nichts neu. Er prüft Tag, Runs, Commit,
Checklisten-Pin und SHA-256, lädt ausschließlich die fünf Kandidatendateien in
einen Draft und lädt sie danach öffentlich erneut. Erst Bytegleichheit erlaubt
die Veröffentlichung.

**Output/Evidenz:** Publish-Run-URL, Release-URL und Ergebnis der erneuten Hashprüfung.
**Erwartetes Ergebnis:** veröffentlichter, nicht als Draft markierter Release mit exakt fünf Manifestdateien.
**Fehler/Wiederanlauf:** Nicht mit `--clobber` reparieren. Bei leerem Draft darf derselbe Run erneut starten;
bei partiellem oder abweichendem Draft stoppt der Vertrag. Abschnitt „Rollback und Teilzustände“ anwenden.

### 9. Öffentliche und nachgelagerte Prüfung abschließen

**Trigger:** Schritt 8 ist erfolgreich und der Release ist öffentlich.
**Owner:** Release-Owner; Update-E2E durch Hardware-Abnahme.
**Input:** Release-URL, fünf `browser_download_url`-Links und Vorgängerartefakt.

```bash
gh release view "$RELEASE_TAG" --json url,isDraft,isPrerelease,assets
gh api "repos/NikolayDA/picture_helper/releases/tags/${RELEASE_TAG}" \
  --jq '.assets[] | [.name, .browser_download_url] | @tsv'
```

Lade alle fünf Assets ohne GitHub-Anmeldung über ihre `browser_download_url`
und vergleiche jeden Hash mit dem Manifest. Protokolliere für jedes Asset URL,
Ergebnis und SHA-256 in einem verlinkbaren Issue-Kommentar oder einem
unveränderlichen Laufprotokoll. Die URL des Publish-Laufs allein genügt dafür
nicht, weil dessen Downloads vor der Veröffentlichung authentifiziert
erfolgen. Prüfe auf den aktiven Plattformen zusätzlich die sichtbare
Produktversion. Führe danach `UPDATE-01` gemäß #748 mit einem echten
Vorgängerartefakt aus: Vorgänger meldet `UPDATE_AVAILABLE`, aktuelles Artefakt
`UP_TO_DATE`, Fehler werden `CHECK_FAILED`.

Pflege die separate Instanz mit `set-criterion`. Setze zuerst die drei
automatisierten Publish-Pflichten auf die verknüpfte Publish-Evidenz,
`PUBLIC-DOWNLOAD-01` auf das anonyme Download- und Hashprotokoll und danach
`UPDATE-01` auf den #748-Nachweis:

```bash
PUBLISH_EVIDENCE_URL="URL_DES_PUBLISH_LAUFS"
PUBLIC_DOWNLOAD_EVIDENCE_URL="URL_DES_ANONYMEN_DOWNLOAD_UND_HASH_PROTOKOLLS"
UPDATE_EVIDENCE_URL="URL_DES_748_NACHWEISES"
for RELEASE_CRITERION in PUBLISH-01 PUBLISH-02 PUBLISH-03; do
  python scripts/release_contract.py set-criterion \
    --checklist docs/RELEASE_ACCEPTANCE_CHECKLIST.md \
    --instance /tmp/release-acceptance-instance.json \
    --criterion "$RELEASE_CRITERION" \
    --status PASS \
    --evidence "$PUBLISH_EVIDENCE_URL" \
    --output /tmp/release-acceptance-instance.json
done
python scripts/release_contract.py set-criterion \
  --checklist docs/RELEASE_ACCEPTANCE_CHECKLIST.md \
  --instance /tmp/release-acceptance-instance.json \
  --criterion PUBLIC-DOWNLOAD-01 \
  --status PASS \
  --evidence "$PUBLIC_DOWNLOAD_EVIDENCE_URL" \
  --output /tmp/release-acceptance-instance.json
python scripts/release_contract.py set-criterion \
  --checklist docs/RELEASE_ACCEPTANCE_CHECKLIST.md \
  --instance /tmp/release-acceptance-instance.json \
  --criterion UPDATE-01 \
  --status PASS \
  --evidence "$UPDATE_EVIDENCE_URL" \
  --output /tmp/release-acceptance-instance.json
python scripts/release_contract.py validate-instance \
  --checklist docs/RELEASE_ACCEPTANCE_CHECKLIST.md \
  --instance /tmp/release-acceptance-instance.json \
  --through-phase post-release
gh issue comment "$RELEASE_ISSUE" --body-file /tmp/release-acceptance-instance.json
```

**Output/Evidenz:** finale Kriterienmatrix mit URLs/Hashes im Release-Issue; geschlossenes #748-Folgeissue.
**Erwartetes Ergebnis:** Publish- und Post-Release-Pflichten sind `PASS`; Release-Issue kann geschlossen werden.
**Fehler/Wiederanlauf:** Öffentlicher Download-, Versions- oder Updatefehler ist ein Incident.
Release nicht als abgeschlossen markieren; nach „Rollback und Teilzustände“ entscheiden.

## Hotfix-Pfad

Ein Hotfix überspringt keinen Schritt. Er erhält eine neue Patch-Version, einen
neuen Kandidaten-Run, neue Hardware-Abnahme, neues Manifest und neuen Tag.
Bekannte Evidenz darf verlinkt, aber nicht als Ergebnis des neuen Kandidaten
ausgegeben werden. Für einen dringenden `2.7.2`-Release gilt exakt dieser neue
Ablauf; ältere Tag-basierte oder manuelle Veröffentlichungswege sind ungültig.

## Rollback, Yank und Teilzustände

1. Veröffentlichung sofort stoppen und im Release-Issue `NO-GO` mit Run, Tag,
   betroffenen Dateien und beobachtetem Zustand notieren.
2. Bei einem fehlerhaften Draft keine Assets ersetzen und kein `--clobber`
   verwenden. Nach Owner-Freigabe den gesamten Draft entfernen oder mit einem
   neuen Hotfix-Tag neu beginnen; die ursprünglichen Logs und Manifestartefakte bleiben erhalten.
3. Einen bereits öffentlichen Release nicht still überschreiben und den Tag
   nicht verschieben. Als zurückgezogen markieren, Warnhinweis und Ersatzversion
   verlinken, dann den vollständigen Hotfix-Pfad durchlaufen.
4. Asset-Ersatz unter demselben Tag ist verboten: Er würde Manifesthashes,
   externe Caches und bereits heruntergeladene Dateien widersprechen.
5. Nach technischer Bereinigung den ursprünglichen Publish-Lauf nicht als
   Erfolg umdeuten. Neuer Lauf und neue Evidenz werden im Issue verknüpft.

## Wiederanlaufmatrix

| Störung | Zulässiger Wiederanlauf | Unzulässig |
|---|---|---|
| Build-Infrastruktur fällt aus, SHA unverändert | neuer Kandidatenlauf auf demselben SHA ab Schritt 3 | alte und neue Run-ID mischen |
| Code, Doku oder Policy ändert sich | neuer Kandidat ab Schritt 1 | alte Abnahme weiterverwenden |
| Abnahme-Runner fällt aus | neuer Abnahmelauf mit derselben Kandidaten-Run-ID | fehlende Plattform als `PASS` markieren |
| Fachlicher Hardware-Smoke schlägt fehl | Fix-PR und neuer Kandidat ab Schritt 1 | Waiver für nicht waiverfähiges `MUST` |
| Kandidaten-/Manifestartefakt nach 90 Tagen abgelaufen | neuer Kandidat ab Schritt 1 | gleichnamiges Artefakt aus anderem Lauf einsetzen |
| Publish-Draft leer | Publish-Workflow mit denselben gebundenen Inputs neu starten | Dateien lokal neu bauen |
| Publish-Draft partiell oder Hash abweichend | No-Go, dokumentierte Bereinigung, neuer Publish- oder Hotfix-Pfad | `--clobber` oder stiller Asset-Tausch |
| Öffentlicher Release fehlerhaft | Yank-Hinweis und neue Hotfix-Version | Tag verschieben oder Asset überschreiben |

## Eskalation und Waiver

- Nach zwei Infrastruktur-Wiederholungen ohne Fortschritt: Repository-Owner und zuständigen Runner-Owner im Issue erwähnen.
- Security-Fund oder unerklärter Hashunterschied: sofort No-Go; Security-Owner übernimmt die Entscheidung.
- Fehlende aktive Zielhardware ist blockierend. Linux x86_64 bleibt dagegen als vorab definierter `SHOULD`-Status `PENDING`.
- Nur Kriterien mit `waiver_allowed: true` dürfen `WAIVED` sein. Owner, Grund und mindestens ein Evidenzlink sind Pflicht.
- Kein Zeitdruck, ablaufendes Artefakt und kein geplanter Termin rechtfertigt das Umgehen eines `MUST`-Kriteriums.

## Dry-Run und Pflege

Vor einer strukturellen Änderung an Workflows, Manifest oder Checkliste wird
dieses Runbook ohne Release-Mutation geprobt: Befehle und Inputs werden gegen
Fixtures beziehungsweise Read-only-APIs geprüft, offene Unklarheiten werden
im verlinkten Dry-Run-Protokoll festgehalten. Ein realer Release bleibt die
verbindliche End-to-End-Probe auf Hardware.

Nach jedem echten Release aktualisiert der Release-Owner „Letzte Übung“ und
ergänzt neue Fehlerbilder in der Wiederanlaufmatrix. Prozessänderungen erfolgen
nur per PR zusammen mit Checklisten-/Workflow-Tests.

## Änderungsverlauf

| Datum | Änderung | Referenz |
|---|---|---|
| 2026-08-01 | Kanonisches Runbook, versionierter Checklisten-Pin, Wiederanlauf-, Hotfix- und Rollback-Pfade | #745, #746 |
