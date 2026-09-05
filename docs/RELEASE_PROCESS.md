# Release-Runbook

**Owner:** Repository-Owner
**Ausführende Rollen:** Release-Owner, CI, Hardware-Abnahme, Security-Owner
**Anwendungsfall:** regulärer Release, Hotfix und Wiederanlauf eines fehlgeschlagenen Releases
**Letzte Aktualisierung:** 2026-08-30
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
- Ein Repository-Ruleset schützt `release/*` gegen Force-Push (`non_fast_forward`), weitere Commits (`update`) und Löschen (`deletion`) (#918). Schritt 2 prüft das fail-closed und nennt das Anlage-Rezept, falls es fehlt — der Release beginnt nicht auf einem ungeschützten Ref.
- Die drei Release-Workflows bleiben während eines laufenden Releases unter ihren Pfaden auf `main` vorhanden: `workflow_dispatch` löst laut GitHub-Referenz nur aus, wenn die Workflow-Datei auf dem Default-Branch existiert („This event will only trigger a workflow run if the workflow file exists on the default branch"). Ausgeführt wird danach die Definition aus `$RELEASE_REF`. Ein Merge, der eine dieser Dateien auf `main` umbenennt oder entfernt, blockiert also die restlichen Dispatches — siehe Wiederanlaufmatrix.
- Ein offenes Release-Issue dient als Entscheidungsprotokoll; seine Nummer wird als `RELEASE_ISSUE` verwendet.
- Kandidaten-, Abnahme- und Publish-Run-ID, vollständiger Commit-SHA, Tag und Manifestname werden im Issue notiert.
- Actions-Artefakte werden 90 Tage aufbewahrt. Ein abgelaufenes Artefakt darf nie durch einen anderen Lauf ersetzt werden.

Die Beispiele verwenden folgende Shell-Variablen. Werte immer aus der verlinkten
GitHub-Ansicht übernehmen, nicht erraten:

```bash
RELEASE_VERSION="X.Y.Z"
RELEASE_TAG="v${RELEASE_VERSION}"
# Unveraenderlicher Release-Ref (#918): traegt alle vier Dispatches, damit
# main waehrend des Releases mergebar bleibt.
#
# Die beiden Namen haben getrennte Rollen und sind nicht austauschbar:
#   RELEASE_TAG  = die veroeffentlichte Version. Er entsteht erst in Schritt 7,
#                  benennt das Release und seine Assets.
#   RELEASE_REF  = Dispatch- und Wiederanlaufquelle. Er existiert ab Schritt 2,
#                  traegt den Ruleset-Schutz und ist die einzige Quelle, aus der
#                  ein Release-Workflow gestartet wird - auch der automatisierte
#                  Schritt-9-Dispatch im Publish-Lauf.
# Beide zeigen auf denselben Commit; genau deshalb ist die Verwechslung
# folgenlos-aussehend und muss benannt werden.
RELEASE_REF="release/${RELEASE_TAG}"
RELEASE_ISSUE="ISSUE_NUMMER"
CANDIDATE_RUN_ID="RUN_ID"
ACCEPTANCE_RUN_ID="RUN_ID"
APPROVAL_ARTIFACT_NAME="release-approval-manifest-1"
# Erst nach Schritt 8 bekannt – Quelle des PUBLIC-DOWNLOAD-01-Berichts.
PUBLISH_RUN_ID="RUN_ID"
# Zuletzt veroeffentlichter Release – Vorgaenger fuer die Update-Kriterien.
# Seit #919 bereits in Schritt 8 gebraucht: Der Publish-Lauf stoesst den
# Post-Release-Nachweis selbst an.
PREDECESSOR_TAG="vX.Y.Z"
# Erst nach Schritt 8 bekannt – der vom Publish-Lauf ausgeloeste Abnahme-Lauf.
UPDATE_ACCEPTANCE_RUN_ID="RUN_ID"
```

## Ablauf

### 1. Release vorbereiten

**Trigger:** Der vereinbarte Funktionsumfang ist auf `main`, oder ein Hotfix ist
freigegeben.
**Owner:** Release-Owner.
**Input:** gewünschte Version, aktueller `main`-Commit.

```bash
git fetch origin main --tags
git switch main
git pull --ff-only origin main
python -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])'
git log -1 --format='%H %s'
```

**Standardweg: `scripts/prepare_release.py`** (#923). Das Skript erzeugt den
gesamten schematischen Rohstand dieses Schritts deterministisch — Paketversion,
sechs datierte CHANGELOG-Abschnitte, AppStream-Eintrag, den Rollover der
Pfadpolicy samt Versionssprung, das Scope-Freeze-Gerüst und das vorbefüllte
Release-Issue:

```bash
python scripts/prepare_release.py <version> --issue-output /tmp/release-issue.md
```

Es trifft **keine** Entscheidung: Scope, Auswirkung, betroffene Anwender:innen,
Upgrade-Relevanz und bekannte Einschränkungen bleiben als `TODO(release)`
stehen und sind redaktionelle Handarbeit (`NOTES-01`). Solange eine dieser
Lücken offen ist, meldet das Freeze-Gate `editorial-placeholder` und der
Vorbereitungs-PR bleibt rot — das Gerüst kann sich nicht selbst freigeben.
Danach die Lizenz-Snapshots neu erzeugen
(`python scripts/generate_license_report.py`), die Lücken füllen und den PR
öffnen. Das Issue legt ein Mensch an; `--create-issue` ruft `gh` nur auf
ausdrücklichen Wunsch.

Zwei Schranken seit #944: Die Zielversion muss numerisch **über** der
pyproject-Version liegen (auch `2.09.0` bei Stand `2.9.0` wird abgewiesen) –
ein Tippfehler erzeugte sonst ein in sich konsistentes Downgrade-Gerüst. Und
die Issue-Ablage (`--issue-output` oder die temporäre Datei) entsteht **vor**
der ersten Repo-Änderung: Ist sie nicht beschreibbar, endet das Skript mit
Exit 2, ohne eine Release-Datei angefasst zu haben – Pfad korrigieren und
unverändert erneut aufrufen. Einträge, die schon unter `[Unreleased]` stehen,
wandern beim ersten Lauf unter das Gerüst der neuen Version. Ein regulärer
zweiter Aufruf bricht danach am Downgrade-Schutz ab, weil `pyproject.toml`
bereits die Zielversion trägt; wer nach einem Abbruch zwischen den Dateien
`pyproject.toml` zurückdreht (`git checkout pyproject.toml`) und erneut
aufruft, bekommt ein unverändertes Gerüst erneuert, die gewanderten Einträge
bleiben stehen. Nach dem Wandern stehen die Gerüst-Überschriften und die
mitgebrachten Überschriften doppelt im neuen Abschnitt (zweimal
`### Hinzugefügt`); das Freeze-Gate blockiert nur die `TODO(release)`-Lücken,
nicht diese Doppelung – sie ist beim Ausformulieren von Hand zusammenzuführen,
sonst landet sie über `extract_release_notes.py` im Release-Body.

Scheitert dieser Aufruf an einem GitHub-/Netzfehler, bleibt der Rohstand
vollständig geschrieben, und der gerenderte Issue-Text liegt als Datei bereit:
unter dem mit `--issue-output` gewählten Pfad, sonst in einer temporären Datei,
deren Pfad die Ausgabe nennt. Die Fehlermeldung gibt dazu den fertigen
Wiederanlaufbefehl aus — `cd <repo> && gh issue create --title … --body-file …`.
Er legt genau dieses Issue an und schreibt keine Release-Datei erneut. Ein
zweiter Skriptlauf ist **kein** Ersatz: Er bricht ab, weil `pyproject.toml`
dann bereits auf der Zielversion steht (#933).

Prüfe, dass `CHANGELOG.md` und der geplante Release-Text Auswirkung,
unterstützte Plattformen, bekannte Einschränkungen sowie Upgrade- und
Rollback-Hinweis enthalten. Starte danach die Dokumentprüfung:

```bash
python scripts/release_contract.py validate-checklist \
  --checklist docs/RELEASE_ACCEPTANCE_CHECKLIST.md
python -m pytest tests/test_markdown_links.py -q
```

Sieh außerdem nach, ob der letzte **monatliche Pipeline-Dry-Run** grün war
(#922, [`RELEASE_AUTOMATION.md`](RELEASE_AUTOMATION.md) §8). Er fährt denselben
Kandidatenpfad und macht Pipeline-Rot sichtbar, bevor es in Schritt 3 unter
Zeitdruck auffällt — genau der Fall aus #880:

```bash
gh run list --workflow release-linux.yml --event schedule --limit 3
```

Ein roter letzter Lauf ist kein Stopp-Kriterium für den Release, aber die
Ursache ist vor Schritt 3 zu klären: Sie trifft den Kandidatenbau sonst erneut.

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

Lege den Kandidaten jetzt auf dem unveränderlichen Release-Ref fest. Ab hier
laufen **alle** Dispatches auf diesem Ref, und `main` bleibt mergebar (#918,
[ADR](history/ADR-2026-release-ref-entkopplung.md)):

```bash
CANDIDATE_SHA="$(git rev-parse HEAD)"
# Ein bereits existierender Ref bedeutet einen abgebrochenen frueheren Versuch.
# Er wird bewusst entschieden (loeschen oder neue Patch-Version), nie ueberschrieben.
# Fail-closed in alle drei Richtungen: nur Exit 2 ("Ref fehlt") legt an, Exit 0
# ("existiert") und jeder andere Ausgang (Netz/Auth, 128) brechen ab. Ein bloss
# vorangestellter Guard wuerde den Push ohne `set -e` nicht binden – dieselbe
# Falle wie bei den Dispatches unten.
git ls-remote --exit-code origin "refs/heads/${RELEASE_REF}" >/dev/null 2>&1
case $? in
  # Leerer Erwartungswert hinter dem Doppelpunkt heisst "der Ref darf nicht
  # existieren": Der Push selbst ist damit anlege-only und kann einen
  # vorhandenen Ref auch bei Fast-Forward nicht still bewegen.
  2) git push origin --force-with-lease="refs/heads/${RELEASE_REF}:" \
       "${CANDIDATE_SHA}:refs/heads/${RELEASE_REF}" ;;
  0) echo "Release-Ref ${RELEASE_REF} existiert bereits – bewusst entscheiden, nicht ueberschreiben." >&2
     false ;;
  *) echo "Ref-Existenz nicht feststellbar (Netz/Auth) – Ref nicht anlegen." >&2
     false ;;
esac
```

Prüfe danach, dass das Ruleset für `release/*` tatsächlich greift — nicht in der
Weboberfläche, sondern an den aktiven Regeln des konkreten Refs. Die Prüfung
**bewertet** und bricht ab; eine bloß ausgegebene Regelliste ließe eine leere
Antwort wie eine bestandene Prüfung aussehen:

```bash
gh api "repos/NikolayDA/picture_helper/rules/branches/${RELEASE_REF}" > /tmp/release-ref-rules.json
python scripts/release_contract.py verify-ref-protection \
  --rules-json /tmp/release-ref-rules.json --ref "$RELEASE_REF"
```

Verlangt werden `non_fast_forward` (kein Force-Push), `update` (keine weiteren
Commits) und `deletion`. Fehlt eine davon — oder liefert der Endpunkt eine leere
Liste, weil gar kein Ruleset existiert —, endet das Kommando mit einem Fehler:
dann nicht weitermachen, sondern das Ruleset in Ordnung bringen. Der Endpunkt
liefert ausschließlich Regeln aus Rulesets im Zustand `active`; ein Ruleset in
`evaluate` oder `disabled` zählt also nicht als Schutz. Der Ref ist ein Branch
und kein Tag, weil nur Branches diesen Schutz tragen.

Die Prüfung deckt genau das Fenster ab, in dem sie zählt: Sie läuft **einmal**
vor dem ersten Dispatch. Würde das Ruleset danach entfernt, bliebe eine
tatsächliche Bewegung des Refs trotzdem nicht unbemerkt — `verify-release-ref`
läuft vor jedem weiteren Dispatch, und `candidate-source` vergleicht im Lauf
selbst `GITHUB_SHA` gegen den Kandidaten-SHA. Geprüft wird hier der *Schutz*,
gefangen wird die *Folge* seines Verlusts an anderer Stelle.

Fehlt das Ruleset noch, legt der Repository-Owner es einmalig an (danach gilt es
für jedes weitere Release):

```bash
gh api --method POST "repos/NikolayDA/picture_helper/rulesets" \
  --input - <<'JSON'
{
  "name": "release-refs",
  "target": "branch",
  "enforcement": "active",
  "conditions": {"ref_name": {"include": ["refs/heads/release/*"], "exclude": []}},
  "rules": [{"type": "deletion"}, {"type": "non_fast_forward"}, {"type": "update"}],
  "bypass_actors": [{"actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "always"}]
}
JSON
```

Der `bypass_actors`-Eintrag ist **nötig**, nicht bequem: Rulesets binden anders
als klassische Branch-Protection standardmäßig auch Repository-Admins. Ohne ihn
scheiterten zwei Handgriffe, die dieses Runbook selbst als Owner-Weg vorsieht —
das Löschen des Refs auf einem verworfenen Kandidaten (Schritt 2, Zweig `0)`)
und das optionale Aufräumen nach Schritt 9 —, der erste davon ausgerechnet im
Rollback-Moment. Er entwertet `verify-ref-protection` nicht: Gegen Versehen aus
Automatisierung und gegen Dritte greift der Schutz unverändert, und das harte
Gate bleibt ohnehin der SHA-Vergleich. Dass ein Ruleset den Owner selbst nicht
bindet, ist die im
[ADR](history/ADR-2026-release-ref-entkopplung.md) ausdrücklich getroffene
Entscheidung: eine bewusste Restlücke, die sich mit der ohnehin menschlichen
Go-/No-Go-Entscheidung deckt. Ein falscher `actor_id` fällt beim POST auf —
GitHub lehnt unbekannte Rollen ab, statt den Eintrag still zu verwerfen.

**Output/Evidenz:** lokale Freeze-Provenienz als Vorprüfung; Release-Ref mit aufgelöstem SHA im Issue;
später die unveränderliche `release-freeze-provenance-<attempt>` aus dem Kandidatenlauf.
**Erwartetes Ergebnis:** Policy, Basis, Kandidaten-SHA und Release-Ref sind widerspruchsfrei.
**Fehler/Wiederanlauf:** Pfadklassifikation oder Dokumentation per PR korrigieren und bei Schritt 1 neu beginnen.
Ein alter Kandidatenlauf bleibt historische Evidenz, wird aber nicht weiterverwendet.
Ein Release-Ref auf dem verworfenen Kandidaten wird gelöscht, bevor der neue entsteht.

### 3. Unveränderlichen Kandidaten bauen

**Trigger:** Freeze-Vorprüfung ist grün und der Release-Ref zeigt auf den Kandidaten.
**Owner:** Release-Owner startet; CI baut.
**Input:** `$RELEASE_REF`, `with_ai=true`.

```bash
gh api "repos/NikolayDA/picture_helper/rules/branches/${RELEASE_REF}" > /tmp/release-ref-rules.json
gh api "repos/NikolayDA/picture_helper/git/ref/heads/${RELEASE_REF}" > /tmp/release-ref.json
# Der Schutz bedingt den ersten Dispatch, statt ihm nur voranzugehen: Ohne die
# &&-Kopplung liefe er in einer Shell ohne `set -e` trotz Fehlers weiter —
# dieselbe Falle wie bei der SHA-Prüfung.
python scripts/release_contract.py verify-ref-protection \
  --rules-json /tmp/release-ref-rules.json --ref "$RELEASE_REF" \
  && python scripts/release_contract.py verify-release-ref \
  --ref-json /tmp/release-ref.json --ref "$RELEASE_REF" --expected-sha "$CANDIDATE_SHA" \
  && gh workflow run release-linux.yml --ref "$RELEASE_REF" -f with_ai=true
gh run list --workflow release-linux.yml --branch "$RELEASE_REF" --event workflow_dispatch --limit 5
gh run watch "$CANDIDATE_RUN_ID" --exit-status
gh run view "$CANDIDATE_RUN_ID" --json headSha,conclusion,url
```

Die Ref-Prüfung **bedingt** jeden Dispatch (`&&`, nicht nur davorstehend): Sie
fängt einen verwechselten oder nachträglich bewegten Ref ab, bevor ein Lauf
startet, statt erst im `candidate-source`-Gate der Abnahme. `&&` statt
`set -e`, damit ein Fehlschlag in einer interaktiven Shell diese nicht beendet.
Ein leerer oder unvollständiger `CANDIDATE_SHA` scheitert dabei ebenfalls — die
Prüfung verlangt einen vollständigen 40-stelligen Commit-SHA. Das harte Gate
bleibt `candidate-source`; diese Prüfung ersetzt es nicht.

Übernimm die Run-ID erst, nachdem `headSha` dem in Schritt 2 notierten Commit
entspricht. Der Workflow führt Full CI aus, baut exakt fünf Dateien und legt
Artefaktcontainer sowie Freeze-Provenienz mit IDs und Digests ab.

**Output/Evidenz:** `CANDIDATE_RUN_ID`, Run-URL, Commit-SHA und die Namen der Build-Artefakte im Issue.
**Erwartetes Ergebnis:** erfolgreicher `release-linux.yml`-Lauf auf exakt einem Commit.
**Fehler/Wiederanlauf:** Ein fehlgeschlagener oder abgelaufener Lauf wird nie umgedeutet.
Nach einer Code-/Dokumentänderung bei Schritt 1 beginnen; bei reinem Infrastrukturfehler darf
derselbe Workflow auf demselben unveränderten SHA neu gestartet werden, erhält aber eine neue Run-ID.

### 4. Kandidatenartefakte und Sicherheitsbefunde vorprüfen

**Trigger:** Schritt 3 ist erfolgreich.
**Owner:** Release-Owner; Malwarebefunde zusätzlich Security-Owner.
**Input:** Kandidatenlauf und dessen Actions-Artefakte.

```bash
gh api "repos/NikolayDA/picture_helper/actions/runs/${CANDIDATE_RUN_ID}/artifacts?per_page=100"
gh run download "$CANDIDATE_RUN_ID" --pattern 'security-scan-*' --dir security-scan-evidence
jq -r '.platform + " " + .verdict' security-scan-evidence/*/security-scan/security-scan-report.json
gh run view "$CANDIDATE_RUN_ID" --log   # nur noch bei Rueckfragen zum Bericht
```

`release-linux.yml` erzeugt an dieser Stelle **noch keinen Kandidatenvertrag**.
Prüfe den erfolgreichen Lauf, seine drei Produkt-Artefaktcontainer mit
insgesamt fünf Produktdateien, die Freeze-Provenienz und die Security-Logs als
Vorprüfung für `VERSION-01`, `FREEZE-01`, `BUILD-01`, `BUILD-02`,
`PROVENANCE-01` und `MALWARE-01`. Für die fünf mit `candidate-contract`
verifizierten Kriterien ist das noch keine formale Evidenz: Sie entsteht
geschlossen zu Beginn von Schritt 5, wenn `candidate-source` den
maschinenlesbaren Kandidatenvertrag aus den heruntergeladenen Dateien und
GitHub-Metadaten erzeugt. Nur `MALWARE-01` wird bereits hier abschließend durch
den Security-Owner entschieden.

Ein Malware-Fund ist immer No-Go. Bei vorhandenem Signaturcache muss jedes
Build-Leg zuerst den EICAR-Selbsttest bestehen. Danach muss für jedes
Artefakt der separate Scan von Rohdatei und entpackter Nutzlast mehr als
0 gescannte Bytes und keine `Heuristics.Limits.Exceeded`-Meldung zeigen.
`Data read` ohne `Data scanned` ist ausdrücklich keine Evidenz. Nicht
verfügbare Scanner bleiben sichtbar und erfordern die in der Checkliste
erlaubte, begründete Entscheidung.

Diese Angaben stehen seit #920 nicht mehr nur als Logzeilen da: Jedes
Build-Leg lädt `security-scan-<platform_tag>` mit
`security-scan/security-scan-report.json` (Schema 1, `release-security-scan`)
und den erfassten Phasen-Logs hoch und rendert dieselbe Auswertung als
Job-Summary. Der Bericht führt je Artefakt die getrennt gescannten Bytes von
Rohdatei und Nutzlast, die Befundzahlen je Kategorie, den EICAR-Selbsttest,
Limitwarnungen, das Alter der Signaturdatenbank und das Gesamtverdikt
`PASS`/`FAIL`/`UNAVAILABLE`. Die Summary gliedert in **harte Befunde**,
**`UNAVAILABLE`-Zustände**, **als bekannt annotierte Anomalien** und
**unbekannte Auffälligkeiten**. Prüfe alle vier Abschnitte je Leg; Abschnitt 4
ist der eigentliche Arbeitsvorrat.

Das kuratierte Register [`release/build-anomalies.json`](../release/build-anomalies.json)
liefert Abschnitt 3. Es annotiert ausschließlich bekannte, begründete
**Log-Muster** der Bau-Phasen und kann kein Secret-, Entwicklerpfad- oder
Malware-Ergebnis verändern — der fail-closed Scanner-Vertrag (Exit 0 ∧ null
Funde ∧ keine Limitwarnung ∧ > 0 gescannte Bytes) bleibt unberührt. Jeder
Eintrag nennt exakten Fingerprint, Plattform, Phase, Begründung, Owner,
Referenz-Issue und Ablaufdatum; erster Eintrag ist die kosmetische
rembg-Warmup-`InferenceError` des macOS-Smokes (Transparenznotiz zu #881).
Ein abgelaufener Eintrag annotiert **nicht mehr** und erzeugt eine sichtbare
Warnung — seine Anomalie erscheint dann wieder unter „unbekannt" und ist neu
zu bewerten (verlängern, ersetzen oder Ursache beheben). Ein neuer Eintrag ist
eine bewusste Kuratierung durch den Security-Owner per PR, nie eine
Verlegenheitslösung für eine unverstandene Meldung.

**Output/Evidenz:** Links auf Lauf, Build-Artefaktcontainer, Provenienz, `security-scan-<platform_tag>` je Leg und Security-Entscheidung.
**Erwartetes Ergebnis:** erwartete Build-Container, gebundene Provenienz und kein Malware-Fund; die formale Dateiprüfung folgt in Schritt 5.
**Fehler/Wiederanlauf:** Bei Artefakt- oder Provenienzfehler Kandidatenlauf verwerfen und Ursache per PR beheben
(neuer Kandidat ab Schritt 1). Nur wenn die Ursache nachweislich außerhalb des Repositorys liegt, sieht die
Wiederanlaufmatrix den Kandidatenlauf ab Schritt 3 auf demselben SHA vor.
Bei Scanner-Ausfall entscheidet der Security-Owner über Wiederholung oder ausdrücklich erlaubten Waiver.
Ist ein Build-Leg schon vor dem Artefaktscan gefallen, trägt ein eigener Schritt die Anomalie-Durchsicht der
Phasen-Logs nach (`--logs-only`, Verdikt `UNAVAILABLE`) – die Abschnitte 3 und 4 der Summary stehen also auch
dort zur Verfügung, um die bekannte kosmetische Meldung vom eigentlichen Fehler zu trennen.
Lässt sich ein Artefakt nicht entpacken (fehlendes `dpkg-deb`/`hdiutil`, nicht ausführbare AppImage,
unlesbare Datei), ist das seit #944 ein harter Befund je Artefakt: Der Bericht entsteht mit Verdikt `FAIL`
und nennt Artefakt und Ursache – Ursache per PR beheben, Kandidatenlauf ab Schritt 3 neu starten.

### 5. Abnahme auf echter Hardware durchführen

**Trigger:** Schritt 4 ist freigegeben und die aktiven Runner sind online.
**Owner:** Hardware-Abnahme; Start durch Release-Owner.
**Input:** `CANDIDATE_RUN_ID`, Zielplattformen `alle`, Release-Issue.

```bash
CANDIDATE_SHA="$(gh run view "$CANDIDATE_RUN_ID" --json headSha --jq .headSha)"
gh api "repos/NikolayDA/picture_helper/git/ref/heads/${RELEASE_REF}" > /tmp/release-ref.json
python scripts/release_contract.py verify-release-ref \
  --ref-json /tmp/release-ref.json --ref "$RELEASE_REF" --expected-sha "$CANDIDATE_SHA" \
  && gh workflow run release-abnahme.yml --ref "$RELEASE_REF" \
  -f run_id="$CANDIDATE_RUN_ID" \
  -f platforms=alle \
  -f dry_run=false \
  -f target_issue="$RELEASE_ISSUE"
gh run list --workflow release-abnahme.yml --branch "$RELEASE_REF" --event workflow_dispatch --limit 5
gh run watch "$ACCEPTANCE_RUN_ID" --exit-status
```

`CANDIDATE_SHA` ist der vollständige `headSha` aus Schritt 3. Die
Ref-Prüfung liest den Ref klonunabhängig direkt aus dem kanonischen
GitHub-Repository und bricht mit Exit 2 ab, wenn er nicht exakt auf diesen SHA
zeigt oder auf ein Nicht-Commit-Objekt verweist. Ein Merge nach `main`
verbrennt den Kandidaten seit #918 **nicht** mehr: Der Kandidat liegt auf dem
geschützten Release-Ref, `main` darf weiterlaufen. Was weiterhin gilt: Auf den
Release-Ref wird **nichts nachgeschoben** — er zeigt exakt auf den
Kandidaten-SHA, oder der Lauf bricht ab; ein Fix bedeutet neuen Kandidaten ab
Schritt 1. Der Workflow erzwingt die SHA-Bindung zusätzlich, indem
`candidate-source` den Workflow-SHA mit dem Kandidaten-SHA vergleicht — das
bleibt das harte technische Gate, die Ref-Prüfung ist ihm nur vorgelagert.
Entscheidung und Bedrohungsmodell:
[ADR](history/ADR-2026-release-ref-entkopplung.md).

Vor den Hardware-Jobs lädt `candidate-source` exakt die Produktdateien und die
Freeze-Provenienz aus dem Kandidatenlauf, validiert Anzahl, Namen, Größen,
SHA-256 und GitHub-Artefaktmetadaten und lädt den erzeugten Vertrag als
`release-candidate-contract-<attempt>` mit 90 Tagen Aufbewahrung hoch. Erst
dieser Schritt liefert die formale Evidenz für `VERSION-01`, `FREEZE-01`,
`BUILD-01`, `BUILD-02` und `PROVENANCE-01` und schließt damit die
Kandidatenvertragsprüfung ab.

Je Zielplattform prüft außerdem ein schneller Preflight-Job die
Einsatzbereitschaft des Self-hosted Runners (grafische Sitzung, ladbare
GL-Bibliothek, freier Speicher, `python3` mit venv, Netzzugang, unter Linux
das eng begrenzte `sudo`), bevor der schwere Abnahme-Job startet. Ein
GitHub-hosted Watchdog beendet den Lauf per force-cancel, wenn ein Preflight
nach zehn Minuten keinen Runner erhalten hat, statt der GitHub-Vorgabe von
bis zu 24 Stunden Queue-Wartezeit (#915). Ein separater Probelauf nur zur
Runner-Prüfung ist nicht nötig; ein Watchdog-Abbruch ist ein reiner
Runnerfehler im Sinne der Wiederanlaufregel unten. Details:
[RELEASE_AUTOMATION.md](RELEASE_AUTOMATION.md) §4.

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

Zwei gleichwertige Wege. Beide setzen denselben annotierten Tag auf denselben
Commit; der Unterschied ist nur, wer ihn setzt.

**a) Vom Publish-Workflow (Regelfall seit #919).** Diesen Schritt überspringen
und in Schritt 8 `create_tag=true` mitgeben. Der Workflow legt den Tag **erst
nach** der vollständigen Manifestprüfung an, ausschließlich auf
`candidate.head_sha` — nie auf einem Eingabewert und nie auf dem aktuellen
Checkout. Ein bereits korrekt zeigender Tag wird nur verifiziert
(Wiederanlauf ist idempotent), ein abweichender bricht ab und wird **nie**
verschoben.

**b) Von Hand (weiterhin gültig).** Genau der bisherige Ablauf:

```bash
CANDIDATE_SHA="VOLLSTAENDIGER_SHA_AUS_DEM_MANIFEST"
test "$(git rev-parse "$CANDIDATE_SHA")" = "$CANDIDATE_SHA"
git tag -a "$RELEASE_TAG" "$CANDIDATE_SHA" -m "Release $RELEASE_TAG"
test "$(git rev-parse "${RELEASE_TAG}^{commit}")" = "$CANDIDATE_SHA"
git push origin "$RELEASE_TAG"
```

In beiden Fällen prüft der Publish-Workflow den Tag anschließend erneut gegen
`candidate.head_sha` (`verify-approval --tag-sha`). Die Anlage ersetzt diese
Prüfung nicht, sie kommt dazu.

**Output/Evidenz:** Tag-URL und aufgelöster vollständiger SHA im Issue.
**Erwartetes Ergebnis:** Tag zeigt bytegenau auf den vom Manifest gebundenen Kandidaten.
**Fehler/Wiederanlauf:** Falschen, noch nicht verwendeten Remote-Tag nur nach dokumentierter Owner-Freigabe löschen
und neu setzen. Sobald ein Release oder externer Download existiert, Tag nie verschieben; stattdessen Hotfix-Version.

### 8. Abgenommene Bytes veröffentlichen

**Trigger:** Schritt 7 ist verifiziert.
**Owner:** Release-Owner startet; CI veröffentlicht.
**Input:** Tag, Kandidaten-Run-ID, Abnahme-Run-ID, exakter Manifestname und optional das Release-Issue.

```bash
# Wie in Schritt 5 aus dem Kandidatenlauf abgeleitet: Schritt 8 liegt oft Tage
# und eine neue Shell spaeter, in der CANDIDATE_SHA nicht mehr gesetzt ist.
CANDIDATE_SHA="$(gh run view "$CANDIDATE_RUN_ID" --json headSha --jq .headSha)"
gh api "repos/NikolayDA/picture_helper/git/ref/heads/${RELEASE_REF}" > /tmp/release-ref.json
python scripts/release_contract.py verify-release-ref \
  --ref-json /tmp/release-ref.json --ref "$RELEASE_REF" --expected-sha "$CANDIDATE_SHA" \
  && gh workflow run release-publish.yml --ref "$RELEASE_REF" \
  -f tag="$RELEASE_TAG" \
  -f candidate_run_id="$CANDIDATE_RUN_ID" \
  -f acceptance_run_id="$ACCEPTANCE_RUN_ID" \
  -f approval_artifact_name="$APPROVAL_ARTIFACT_NAME" \
  -f create_tag=true \
  -f predecessor_tag="$PREDECESSOR_TAG" \
  -f target_issue="$RELEASE_ISSUE"
gh run list --workflow release-publish.yml --branch "$RELEASE_REF" --event workflow_dispatch --limit 5
```

Der Publish-Workflow baut nichts neu. Er prüft Tag, Runs, Commit,
Checklisten-Pin und SHA-256, lädt ausschließlich die fünf Kandidatendateien in
einen Draft und lädt sie danach öffentlich erneut. Erst Bytegleichheit erlaubt
die Veröffentlichung.

Direkt danach läuft im selben Workflow der Nachweis-Job **Öffentlicher
Download-Nachweis (PUBLIC-DOWNLOAD-01)** (#916): Er lädt alle fünf Assets
**ohne** Authorization-Header über ihre `browser_download_url`, verifiziert sie
mit demselben `verify-artifacts` gegen das Freigabemanifest und sichert
`public-download-report.json` (je Datei Name, Größe, SHA-256, URL, Zeitstempel
und Ergebnis plus Gesamtverdikt) 90 Tage als Actions-Artefakt, gerendert als
Job-Summary und – bei gesetztem `target_issue` – als Issue-Kommentar. Er ist
ein eigener Job, weil ein Draft-Asset anonym gar nicht erreichbar ist: Der
Nachweis kann erst nach `--draft=false` entstehen.

`create_tag=true` setzt den Tag (Schritt 7a); wurde er von Hand gesetzt
(Schritt 7b), ist `create_tag=false` richtig — beide Wege enden in derselben
Verifikation. `predecessor_tag` steuert den Post-Release-Update-Nachweis: Der
Lauf stößt `release-abnahme.yml` am Ende selbst an (#919). Leer bleibt er
zulässig; dann wird der Nachweis sichtbar übersprungen und über den
Rückfallweg in Schritt 9 nachgezogen. Der Vorgänger wird **nie geraten** —
`/releases/latest` wäre durch Backfills und Pre-Releases verfälschbar.

Der Lauf hat damit vier Jobs in fester Reihenfolge:

| Job | Ergebnis |
|---|---|
| `publish` | Tag (optional), Draft, byteidentischer Upload, Veröffentlichung |
| `public-download` | `PUBLIC-DOWNLOAD-01` anonym über `browser_download_url` |
| `release-instance` | Release-Instanz mit `PUBLISH-01..03` + `PUBLIC-DOWNLOAD-01` auf `PASS`, validiert bis `publish` |
| `update-dispatch` | löst den Abnahme-Lauf für beide Update-Kriterien aus und verlinkt ihn |

**Output/Evidenz:** Publish-Run-URL, Release-URL, Ergebnis der erneuten Hashprüfung,
`public-download-report.json` des Nachweis-Jobs, Artefakt
`release-acceptance-instance-<attempt>` und die verlinkte Abnahme-Run-ID des Dispatch-Jobs.
**Erwartetes Ergebnis:** veröffentlichter, nicht als Draft markierter Release mit exakt fünf Manifestdateien;
Nachweis-Job grün mit Gesamtverdikt `PASS`; Instanz bis `publish` validiert; Update-Nachweis ausgelöst
oder sichtbar als übersprungen protokolliert.
**Fehler/Wiederanlauf:** Nicht mit `--clobber` reparieren. Bei leerem Draft darf derselbe Run erneut starten;
bei partiellem oder abweichendem Draft stoppt der Vertrag. Abschnitt „Rollback und Teilzustände“ anwenden.
Ein roter Nachweis-Job (Hash-Abweichung, fehlendes Asset, HTTP-Fehler) ist ein Incident: Zuerst den Bericht
lesen, dann nach „Rollback und Teilzustände“ entscheiden — nie stillschweigend wiederholen.

### 9. Öffentliche und nachgelagerte Prüfung abschließen

**Trigger:** Schritt 8 ist erfolgreich und der Release ist öffentlich.
**Owner:** Release-Owner; Update-E2E durch Hardware-Abnahme.
**Input:** `public-download-report.json` und Release-Instanz aus Schritt 8, Release-URL,
Run-ID des vom Publish-Lauf ausgelösten Abnahme-Laufs.

Dieser Schritt ist seit #919 im Regelfall **Prüfen und Protokollieren**: Tag,
Update-Dispatch und Instanzpflege laufen im Publish- bzw. im davon ausgelösten
Abnahme-Lauf. Die Handprozeduren bleiben als Rückfallwege darunter stehen und
gelten unverändert, wenn die Automatisierung nicht greifen konnte.

`PUBLIC-DOWNLOAD-01` wird seit #916 nicht mehr von Hand erbracht: Der
Nachweis-Job aus Schritt 8 hat alle fünf Assets bereits anonym über ihre
`browser_download_url` geladen und gegen das Freigabemanifest verifiziert.
Lies den Bericht und verwende ihn als Evidenz:

```bash
gh run view "$PUBLISH_RUN_ID"
gh run download "$PUBLISH_RUN_ID" --pattern 'public-download-report-*' --dir /tmp/public-download
PUBLIC_DOWNLOAD_REPORT="$(find /tmp/public-download -name public-download-report.json | head -1)"
jq '.verdict, (.assets[] | {name, result, sha256})' "$PUBLIC_DOWNLOAD_REPORT"
```

Der Artefaktname trägt die Versuchsnummer des Laufs
(`public-download-report-<run_attempt>`), deshalb `--pattern` statt `--name`:
Ein Wiederanlauf desselben Laufs legt den Bericht unter `-2` ab. `find` statt
eines festen Pfads, weil `gh run download` je nach Trefferzahl flach oder in
einem Unterverzeichnis je Artefaktnamen ablegt (dieselbe Doppeldeutigkeit, die
`release_contract.py` beim Manifest-Download abfängt).

Erwartet ist `"verdict": "PASS"` und je Asset `"result": "PASS"`. Die URL des
Publish-Laufs allein genügt weiterhin **nicht** als Nachweis: Die Downloads des
`publish`-Jobs erfolgen vor der Veröffentlichung authentifiziert aus dem Draft.
Maßgeblich ist ausschließlich der Bericht des Nachweis-Jobs. Prüfe auf den
aktiven Plattformen zusätzlich die sichtbare Produktversion.

**Rückfallweg (nur wenn der Nachweis-Job nicht gelaufen ist, z. B. nach einem
Wiederanlauf ohne ihn):** Lade alle fünf Assets ohne GitHub-Anmeldung über ihre
`browser_download_url` und vergleiche jeden Hash mit dem Manifest.
Protokolliere für jedes Asset URL, Ergebnis und SHA-256 in einem verlinkbaren
Issue-Kommentar oder einem unveränderlichen Laufprotokoll.

```bash
gh release view "$RELEASE_TAG" --json url,isDraft,isPrerelease,assets
gh api "repos/NikolayDA/picture_helper/releases/tags/${RELEASE_TAG}" \
  --jq '.assets[] | [.name, .browser_download_url] | @tsv'
```

`UPDATE-LINUX-ARM-01` und `UPDATE-MACOS-ARM-01` (#748/#917) stößt der
Publish-Lauf seit #919 selbst an, sofern `predecessor_tag` gesetzt war. Der
Dispatch läuft wie die Schritte 3, 5 und 8 auf `$RELEASE_REF` — er leitet ihn
deterministisch aus dem Tag ab und prüft seinen SHA vorher mit
`verify-release-ref` gegen `candidate.head_sha`; fehlt der Ref, bricht der Job
ab, statt auf eine andere Quelle auszuweichen. Der Job verlinkt den erzeugten
Abnahme-Lauf in der Job-Summary und — bei gesetztem `target_issue` — im
Release-Issue. Prüfe dort das Ergebnis:

```bash
gh run view "$PUBLISH_RUN_ID" --json jobs \
  --jq '.jobs[] | select(.name | startswith("Post-Release")) | .conclusion'
gh run watch "$UPDATE_ACCEPTANCE_RUN_ID" --exit-status
```

Der Marker `update-check:<tag>:<candidate_run_id>` macht den Lauf idempotent
auffindbar: Ein Wiederanlauf des Publish-Laufs löst **keinen** zweiten Nachweis
aus. Ein fehlgeschlagener Nachweis wird bewusst nicht automatisch wiederholt —
er ist laut Abschnitt „Rollback und Teilzustände" ein Incident.

**Rückfallweg (nur wenn kein `predecessor_tag` gesetzt war oder der Dispatch
sichtbar übersprungen wurde):** Starte `release-abnahme.yml` von Hand — mit
**derselben** `run_id` wie in Schritt 5 und dem Tag des Vorgängers.
`platforms` bestimmt, welche der beiden Kriterien der Lauf erbringt:

```bash
# Beide Kanäle in einem Lauf (Regelfall seit #917):
CANDIDATE_SHA="$(gh run view "$CANDIDATE_RUN_ID" --json headSha --jq .headSha)"
gh api "repos/NikolayDA/picture_helper/git/ref/heads/${RELEASE_REF}" > /tmp/release-ref.json
python scripts/release_contract.py verify-release-ref \
  --ref-json /tmp/release-ref.json --ref "$RELEASE_REF" --expected-sha "$CANDIDATE_SHA" \
  && gh workflow run release-abnahme.yml --ref "$RELEASE_REF" \
  -f run_id="$CANDIDATE_RUN_ID" \
  -f platforms=alle \
  -f dry_run=false \
  -f predecessor_tag="$PREDECESSOR_TAG" \
  -f target_issue="$RELEASE_ISSUE"
```

`platforms=alle` deckt beide Post-Release-Kriterien in einem Lauf ab (der
pausierte x86_64-Job bleibt übersprungen). Ist nur ein Runner verfügbar, geht
auch `platforms=linux-arm64` beziehungsweise `platforms=macos-arm64` — dann
bleibt aber das jeweils andere Kriterium `PENDING` und muss in einem zweiten
Lauf nachgezogen werden. Ein Einzelplattform-Lauf erzeugt bewusst **kein**
Freigabemanifest; die Abschlussmatrix kennzeichnet sich selbst als Diagnose.

**macOS-Grenze:** Der macOS-Nachweis läuft über den In-Prozess-Hook
`BGREMOVER_UPDATE_CHECK_PROBE`, den `bgremover/app.py` noch vor `QApplication`
auswertet. Er existiert erst ab **v2.7.3**; ein älterer Vorgänger lässt
`UPDATE-MACOS-ARM-01` mit dem benannten Befund `HOOK_FEHLT` fehlschlagen (keine
kaputte Sonde, sondern die dokumentierte historische Grenze). In diesem Fall
bleibt das Kriterium `PENDING` mit Verweis auf diese Grenze — es wird **nicht**
auf `WAIVED` gesetzt.

Für `workflow_dispatch` definiert GitHub `GITHUB_SHA` als den letzten Commit
des ausgewählten Branches oder Tags
([Ereignisreferenz](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_dispatch)).
Der Release-Ref zeigt direkt auf den Kandidaten-Commit, `GITHUB_SHA` ist damit
genau dieser SHA. Der zusätzliche Vergleich in `candidate-source` bleibt als
fail-closed Sicherung bestehen. Der Release-Ref wird deshalb **erst nach
diesem Schritt** entbehrlich; bis dahin bleibt er stehen.

Der Lauf zieht das Vorgängerartefakt je Plattform anonym über
`browser_download_url` und führt den Update-Check **aus dem gepackten Artefakt**
aus — Linux unter dem darin gebündelten Interpreter der AppImage, macOS über den
In-Prozess-Hook des DMG-Bundles. Bewertet wird beidseitig identisch: Vorgänger
meldet `UPDATE_AVAILABLE` mit exakt der neuen Version, das aktuelle Artefakt
`UP_TO_DATE`, und beide müssen sich selbst als die erwartete Version
ausweisen. `CHECK_FAILED` ist ein eigener harter Fehlerzustand und gilt nie als
„kein Update". Die Evidenz (Artefaktquelle, SHA-256, Plattform, Ausgangs- und
Zielversion, Antwortstatus je Rolle) liegt als `update_check/update_check.json`
im Plattform-Artefakt und als `[update-check]`-Zeilen im Joblog. Ablauf,
Grenzen und die manuelle Ersatzprozedur ohne Runner:
[RELEASE_AUTOMATION.md](RELEASE_AUTOMATION.md) §4.2 bzw.
[PACKAGING_SMOKE.md](PACKAGING_SMOKE.md) §4.1.

Die Release-Instanz entsteht seit #919 ebenfalls automatisch, in zwei
Hälften: Der Publish-Lauf setzt `PUBLISH-01..03` und `PUBLIC-DOWNLOAD-01` mit
den Evidenz-URLs seines eigenen Laufs (Artefakt
`release-acceptance-instance-<attempt>`); der von ihm ausgelöste Abnahme-Lauf
trägt `UPDATE-LINUX-ARM-01`/`UPDATE-MACOS-ARM-01` aus seiner eigenen
`update_check.json` nach und validiert erstmals `--through-phase post-release`
(Artefakt `release-acceptance-instance-final-<attempt>`, zusätzlich als
Issue-Kommentar). Lade die finale Instanz und prüfe sie:

```bash
gh run download "$UPDATE_ACCEPTANCE_RUN_ID" \
  --pattern 'release-acceptance-instance-final-*' --dir /tmp/release-instance
find /tmp/release-instance -name release-acceptance-instance.json \
  -exec jq -r '.criteria[] | select(.phase != "pre-release")
    | "\(.id) \(.requirement) \(.status)"' {} +
```

Erwartet ist `PASS` für alle `MUST`- und `POST_RELEASE`-Kriterien;
`ROLLBACK-01` (`SHOULD`, manuelle Go-/No-Go-Protokollierung) bleibt in der
Hand des Release-Owners.

**Rückfallweg (nur ohne automatische Instanz, etwa nach einem
Einzelplattform-Nachlauf):** Pflege die Instanz von Hand mit `set-criterion` —
zuerst die drei Publish-Pflichten auf die verknüpfte Publish-Evidenz,
`PUBLIC-DOWNLOAD-01` auf das anonyme Download- und Hashprotokoll und danach
`UPDATE-LINUX-ARM-01`/`UPDATE-MACOS-ARM-01` auf den jeweiligen
Plattform-Nachweis:

```bash
PUBLISH_EVIDENCE_URL="URL_DES_PUBLISH_LAUFS"
PUBLIC_DOWNLOAD_EVIDENCE_URL="URL_DES_ANONYMEN_DOWNLOAD_UND_HASH_PROTOKOLLS"  # Artefakt public-download-report-N des Publish-Laufs
UPDATE_LINUX_EVIDENCE_URL="URL_DER_LINUX_UPDATE_CHECK_EVIDENZ"
UPDATE_MACOS_EVIDENCE_URL="URL_DER_MACOS_UPDATE_CHECK_EVIDENZ"
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
  --criterion UPDATE-LINUX-ARM-01 \
  --status PASS \
  --evidence "$UPDATE_LINUX_EVIDENCE_URL" \
  --output /tmp/release-acceptance-instance.json
python scripts/release_contract.py set-criterion \
  --checklist docs/RELEASE_ACCEPTANCE_CHECKLIST.md \
  --instance /tmp/release-acceptance-instance.json \
  --criterion UPDATE-MACOS-ARM-01 \
  --status PASS \
  --evidence "$UPDATE_MACOS_EVIDENCE_URL" \
  --output /tmp/release-acceptance-instance.json
python scripts/release_contract.py validate-instance \
  --checklist docs/RELEASE_ACCEPTANCE_CHECKLIST.md \
  --instance /tmp/release-acceptance-instance.json \
  --through-phase post-release
gh issue comment "$RELEASE_ISSUE" --body-file /tmp/release-acceptance-instance.json
```

Nach Abschluss ist der Release-Ref entbehrlich — der Tag hält denselben Commit
unveränderlich fest. Ein Löschen ist **optional** und bleibt dem Release-Owner
vorbehalten; ein stehengelassener, geschützter Ref ist harmlos:

```bash
git push origin --delete "$RELEASE_REF"   # optional, erst nach Schritt 9
```

**Output/Evidenz:** finale Kriterienmatrix mit URLs/Hashes im Release-Issue; geschlossenes #748-Folgeissue.
**Erwartetes Ergebnis:** Publish- und Post-Release-Pflichten sind `PASS`; Release-Issue kann geschlossen werden.
**Fehler/Wiederanlauf:** Öffentlicher Download-, Versions- oder Updatefehler ist ein Incident.
Release nicht als abgeschlossen markieren; nach „Rollback und Teilzustände“ entscheiden.
Das gilt ausdrücklich auch für die beiden Update-Kriterien: Ein `CHECK_FAILED` oder ein
Vorgänger, der die neue Version nicht sieht, wird **nicht** auf `WAIVED`
gesetzt — der Fund betrifft alle bereits ausgelieferten Installationen. Kläre
zuerst, ob der Fehler am Release liegt (falscher/fehlender Tag, privates
Release, kaputter Asset-Satz) oder am Prüfpfad (Netz, Runner). Am Release ⇒
„Rollback und Teilzustände“ oder der Hotfix-Pfad mit neuer Patch-Version. Am
Prüfpfad ⇒ Nachweis wiederholen und den Fehlversuch mitprotokollieren.
`UPDATE-LINUX-ARM-01`/`UPDATE-MACOS-ARM-01` bleiben bis zum bestandenen Lauf
`PENDING`; da sie post-release sind, blockieren sie den Tag nicht, aber den
Abschluss des Release-Issues.

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

Ein Wiederanlauf „auf demselben SHA" trägt nur, solange die Behebung außerhalb des
Repositorys liegt (Runner-Umgebung, Build-Infrastruktur, Signaturcache): Jeder Dispatch
führt die Workflow-Definition aus `$RELEASE_REF` aus (#918), ein per PR gemergter Fix
ist auf dem unveränderten Kandidaten-Commit also nicht enthalten, und der Wiederanlauf
wiederholte den ursprünglichen Fehler. Braucht die Ursache einen Repo-Commit — Workflow,
Packaging-Skript, Scanner, Policy —, gilt immer „neuer Kandidat ab Schritt 1".

| Störung | Zulässiger Wiederanlauf | Unzulässig |
|---|---|---|
| Build-Infrastruktur fällt aus, SHA unverändert | neuer Kandidatenlauf auf demselben SHA ab Schritt 3 | alte und neue Run-ID mischen |
| Code, Doku oder Policy ändert sich | neuer Kandidat ab Schritt 1 | alte Abnahme weiterverwenden |
| **Merge nach `main` während eines laufenden Releases** | **kein Wiederanlauf nötig — der Kandidat liegt auf dem geschützten Release-Ref und bleibt gültig (#918)** | auf den Release-Ref nachschieben, um `main` einzuholen |
| Release-Ref zeigt nicht auf den Kandidaten-SHA (verwechselt, bewegt) | Ursache klären; bei falschem Ref den richtigen dispatchen, bei bewegtem Ref Kandidat verwerfen und ab Schritt 1 neu | Ref zurücksetzen und so tun, als sei nichts geschehen |
| Merge nach `main` entfernt oder benennt eine der drei Release-Workflow-Dateien um | Pfad auf `main` per PR wiederherstellen (Datei muss dort existieren, damit `workflow_dispatch` überhaupt auslöst), danach denselben Dispatch auf `$RELEASE_REF` wiederholen — der Kandidat bleibt gültig | Workflow ersatzweise auf `main` starten oder den Ref anpassen |
| Tag existiert schon und zeigt woanders hin (`create_tag=true`) | Publish bricht ab, bevor etwas veröffentlicht wird; Ursache klären. Sobald ein Release oder ein externer Download existiert, gilt der Hotfix-Pfad mit neuer Patch-Version | Tag verschieben, löschen und neu setzen oder `create_tag=false` als Umgehung nutzen |
| Update-Dispatch übersprungen (kein `predecessor_tag`) oder Abnahme-Lauf nicht auffindbar | Actions-Übersicht auf einen Lauf mit dem Marker `update-check:<tag>:<run_id>` prüfen; fehlt er, den Rückfallweg aus Schritt 9 von Hand starten | blind ein zweites Mal dispatchen oder die Update-Kriterien ohne Nachweis auf `PASS` setzen |
| Abnahme-Runner fällt aus oder der Watchdog bricht wegen Offline-Runner ab (#915) | Runner wieder online bringen, neuer Abnahmelauf mit derselben Kandidaten-Run-ID | fehlende Plattform als `PASS` markieren |
| Fachlicher Hardware-Smoke schlägt fehl | Fix-PR und neuer Kandidat ab Schritt 1 | Waiver für nicht waiverfähiges `MUST` |
| Kandidaten-/Manifestartefakt nach 90 Tagen abgelaufen | neuer Kandidat ab Schritt 1 | gleichnamiges Artefakt aus anderem Lauf einsetzen |
| ClamAV-Signaturcache leer/veraltet (`MALWARE-01` `UNAVAILABLE` oder Alterswarnung) | `clamav-db-refresh.yml` manuell per `workflow_dispatch` anstoßen, danach Kandidatenlauf ab Schritt 3 neu starten | `MALWARE-01` stillschweigend als bestanden werten |
| ClamAV-EICAR-Test, Payload-Scan, Limitprüfung oder Nichtnull-Evidenz schlägt bei vorhandenem Cache fehl | Ursache per PR beheben und neuen Kandidaten ab Schritt 1 bauen | Exit 0 oder `Data read` als ausreichenden PASS-Nachweis werten |
| Artefakt lässt sich im Security-Scan nicht entpacken (`dpkg-deb`/`hdiutil` fehlt, AppImage nicht ausführbar, Datei unlesbar; Verdikt `FAIL`, #944) | Ursache zuerst zuordnen: liegt sie außerhalb des Repositorys (Runner-Image, fehlendes Werkzeug auf dem Runner, transienter Werkzeugfehler), dort beheben und den Kandidatenlauf ab Schritt 3 auf demselben SHA neu starten; braucht die Behebung einen Repo-Commit (Workflow-Schritt, Packaging-Skript, Scanner), Fix-PR und neuer Kandidat ab Schritt 1 | den `--logs-only`-Ersatzbericht als Scan-Ergebnis werten, das Artefakt ungescannt freigeben oder nach einem gemergten Fix denselben SHA erneut fahren — der Lauf führt die Workflow-Definition des Release-Refs aus, der Fix wirkt dort nicht |
| Publish-Draft leer | Publish-Workflow mit denselben gebundenen Inputs neu starten | Dateien lokal neu bauen |
| Publish-Draft partiell oder Hash abweichend | No-Go, dokumentierte Bereinigung, neuer Publish- oder Hotfix-Pfad | `--clobber` oder stiller Asset-Tausch |
| Öffentlicher Download-Nachweis rot (Hash-Abweichung, fehlendes Asset, HTTP-Fehler) | Bericht lesen; Netz-/API-Fehler des Prüfpfads: Publish-Workflow mit denselben gebundenen Inputs erneut starten (er ist idempotent, `already-complete`) | Abweichung als Prüfpfad-Störung abtun oder `PUBLIC-DOWNLOAD-01` ohne grünen Bericht auf `PASS` setzen |
| Öffentlicher Release fehlerhaft | Yank-Hinweis und neue Hotfix-Version | Tag verschieben oder Asset überschreiben |

## Eskalation und Waiver

- Nach zwei Infrastruktur-Wiederholungen ohne Fortschritt: Repository-Owner und zuständigen Runner-Owner im Issue erwähnen.
- Security-Fund oder unerklärter Hashunterschied: sofort No-Go; Security-Owner übernimmt die Entscheidung.
- Fehlende aktive Zielhardware ist blockierend. Linux x86_64 bleibt dagegen als vorab definierter `SHOULD`-Status `PENDING`.
- Nur Kriterien mit `waiver_allowed: true` dürfen `WAIVED` sein. Owner, Grund und mindestens ein Evidenzlink sind Pflicht.
- Kein Zeitdruck, ablaufendes Artefakt und kein geplanter Termin rechtfertigt das Umgehen eines `MUST`-Kriteriums.

## Dry-Run und Pflege

**Begriffe.** „Dry-Run" bezeichnet in diesem Repository drei verschiedene
Dinge; sie werden hier bewusst auseinandergehalten:

| Gemeint ist | Wo | Zweck |
| --- | --- | --- |
| Runbook-Probe | dieser Abschnitt | dieses Runbook ohne Release-Mutation durchspielen |
| Pipeline-Dry-Run | `release-linux.yml` per `schedule` (#922) | den Kandidatenpfad zwischen den Releases fahren |
| Abnahme ohne Auswertung | Eingabe `dry_run` von `release-abnahme.yml` | nur die Smokes, ohne Vision-/Aggregationsschritt |

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
| 2026-09-05 | Wiederanlaufmatrix: „auf demselben SHA" nur für Behebungen außerhalb des Repositorys; nach einem per PR gemergten Fix immer neuer Kandidat ab Schritt 1 (der Lauf führt die Definition des Release-Refs aus); Zeile zu nicht entpackbaren Artefakten (#944) entsprechend geteilt, Schritt 4 verweist darauf | #987 (Codex-Review zu #985) |
| 2026-08-31 | Tag-Anlage (`create_tag`), Post-Release-Update-Dispatch und Release-Instanz laufen im Publish- bzw. im davon ausgelösten Abnahme-Lauf; Schritt 9 ist Prüfen und Protokollieren, die Handprozeduren bleiben Rückfallwege | #919 |
| 2026-08-30 | Release läuft auf dem unveränderlichen `release/vX.Y.Z`-Ref statt auf `main`; `MAIN_SHA`-Gleichheitsprüfung durch `verify-release-ref` ersetzt, `main` bleibt mergebar; Ref-Anlage anlege-only, Ruleset-Prüfung maschinell, Default-Branch-Voraussetzung von `workflow_dispatch` dokumentiert | #918 |
| 2026-08-30 | `UPDATE-01` in `UPDATE-LINUX-ARM-01`/`UPDATE-MACOS-ARM-01` geteilt; macOS-Nachweis über den In-Prozess-Hook, `platforms`-Wahl in Schritt 9 beschrieben (Checkliste 2.0.0) | #917 |
| 2026-08-30 | `PUBLIC-DOWNLOAD-01` als anonymer Nachweis-Job im Publish-Workflow; Schritt 8/9 auf den Bericht umgestellt, Handprozedur bleibt Rückfallweg (Checkliste 1.1.0) | #916 |
| 2026-08-30 | Runner-Readiness-Preflight und Queue-Watchdog in Schritt 5; Abschlussmatrix unvollständiger Läufe als Diagnose gekennzeichnet | #915 |
| 2026-08-01 | Kanonisches Runbook, versionierter Checklisten-Pin, Wiederanlauf-, Hotfix- und Rollback-Pfade | #745, #746 |
