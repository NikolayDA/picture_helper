# ADR-2026: Release auf einem unveränderlichen Release-Ref statt auf `main`

**Status:** Akzeptiert
**Datum:** 2026-08-30
**Entscheider:** Repository-Owner
**Bezug:** #881, #914, #918; baut auf #744/#747 (Freigabevertrag) und #742/#743
(Freeze-Provenienz) auf

## Kontext

Das Runbook band Kandidatenbau und Abnahme an `main` und verlangte in Schritt 5
die Gleichheit von `main`-Kopf und Kandidaten-SHA. Die Konsequenz stand
ausdrücklich dort: „Jeder Merge nach `main` verbrennt diesen Kandidaten." Bei
v2.9.0 war `main` dadurch rund **47,5 Stunden** eingefroren
([Protokoll #881](https://github.com/NikolayDA/picture_helper/issues/881)) — vom
Kandidaten-Commit bis zum Tag. Ein Branch- oder Tag-Wiederanlauf war bewusst
nicht erlaubt; das Runbook forderte dafür „zuerst eine eigene, fail-closed
abgesicherte Prozessentscheidung". Dieser ADR trifft sie.

Drei Beobachtungen tragen die Entscheidung:

1. **Die Beweiskette hängt am SHA, nicht am Ref-Namen.**
   `release_contract.validate_workflow_run` prüft Run-ID, Workflow-Pfad,
   `workflow_dispatch`, erfolgreichen Abschluss und `head_sha` — an keiner
   Stelle einen Branchnamen. `candidate-source` vergleicht den Workflow-SHA
   gegen den Kandidaten-SHA. Der Publish-Job checkt den Kandidaten-Commit aus
   dem **Manifest** aus, nicht aus dem Dispatch-Ref. Der `main`-Bezug war eine
   *Prozess*konvention, keine technische Voraussetzung.
2. **Der Präzedenzfall existiert bereits.** Runbook-Schritt 9 dispatcht seit
   #741/#748 regulär auf den Release-Tag statt auf `main`, ohne dass die
   Beweiskette darunter gelitten hätte.
3. **Die Fenster werden eher länger, nicht kürzer.** Mit dem MAS-Kanal (#882)
   kommen weitere Ausgänge hinzu. Sie sind laut #905 `POST_RELEASE` und
   erzwingen selbst keinen Freeze — ein `main`, das an der Länge des
   Release-Fensters hängt, ist trotzdem der falsche Ausgangspunkt.

Der `main`-Freeze war also ein *Nebeneffekt* der Konvention, kein Schutz. Er
kostete Durchsatz, ohne eine Prüfung zu tragen.

## Entscheidung

Ein Release läuft vollständig auf einem unveränderlichen Branch
`release/vX.Y.Z`, der exakt auf den Kandidaten-Commit zeigt. `main` bleibt
während des gesamten Releases mergebar.

- **Anlage** in Runbook-Schritt 2, unmittelbar nach der Freeze-Vorprüfung, auf
  genau den Commit, den `verify_release_freeze.py` als Kandidaten ausgewiesen
  hat.
- **Schutz** über ein Repository-Ruleset auf `release/*`: keine Force-Pushes,
  keine weiteren Commits, kein Löschen durch Nicht-Owner. Der Ref ist ein
  Branch und kein Tag, weil Rulesets und Branch-Protection genau diesen Schutz
  für Branches tragen.
- **Dispatch** aller vier Workflow-Starts (Runbook-Schritte 3, 5, 8 und 9) auf
  `release/vX.Y.Z` statt auf `main`.
- **Verifikation vor jedem Dispatch** über
  `release_contract.py verify-release-ref`: Der Ref muss dem Namensschema
  folgen, auf ein **Commit**-Objekt zeigen und exakt den erwarteten
  Kandidaten-SHA tragen. Ein Kommando statt vier kopierter Shell-Blöcke — eine
  handgepflegte Kopie an vier Stellen wäre genau die Drift, die dieses
  Repository sonst überall festnagelt.
- **Kein Nachschieben.** Der Ref zeigt exakt auf den Kandidaten-SHA, oder der
  Lauf bricht ab. Ein Fix bedeutet weiterhin: neuer Kandidat ab Schritt 1.

Die `MAIN_SHA`-Gleichheitsprüfung aus Schritt 5 entfällt ersatzlos. Sie prüfte
die Konvention, nicht die Bindung; die Ref-SHA-Prüfung prüft die Bindung.

## Bedrohungsmodell

Vier Fehlerbilder, jeweils mit dem Gate, das greift:

| Bedrohung | Wirkung ohne Gate | Was greift |
|---|---|---|
| **Verwechselter Ref** (Dispatch auf `release/v2.9.0` statt `v2.9.1`) | Kandidat auf dem falschen Commit gebaut oder abgenommen | `verify-release-ref` vor dem Dispatch (Ref-Name **und** SHA); in der Abnahme zusätzlich `candidate-source`, das `GITHUB_SHA` gegen den Kandidaten-SHA des Vertrags prüft |
| **Nachträglich mutierter Branch** (Force-Push oder Nachschub auf den Release-Ref) | Ein späterer Dispatch liefe auf anderem Code als der abgenommene | Ruleset verhindert es; zusätzlich fällt es bei der nächsten `verify-release-ref`-Prüfung und im `candidate-source`-Gate auf, weil der SHA nicht mehr passt |
| **Divergenz zu `main`** (`main` läuft weiter) | — (ausdrücklich erlaubt und der Zweck dieser Entscheidung) | Keins nötig: Der Kandidat ist der Ref-Commit. Die Freeze-Provenienz wurde an genau diesem Commit erzeugt und bleibt gültig, weil sie den Kandidaten aus der First-Parent-Historie ableitet, nicht aus dem `main`-Kopf |
| **Versehentlicher Dispatch auf `main`** | Lauf auf einem Commit, der nicht der Kandidat ist | Kandidatenbau: die Freeze-Prüfung läuft auf dem falschen Kopf und der Operator sieht in Schritt 3 einen abweichenden `headSha`. Abnahme: `candidate-source` bricht hart ab. Publish: unkritisch für die Bytes (alle Bindungen kommen aus dem Manifest), aber die Workflow-**Definition** stammt dann von `main` statt vom Kandidaten — siehe Konsequenzen |

Was sich **nicht** ändert: Die SHA-Gleichheitsprüfung in `candidate-source`
bleibt das technische Gate. `verify-release-ref` ist eine vorgelagerte
Kontrolle, die den Fehler vor dem Dispatch sichtbar macht statt danach — sie
ersetzt das Gate nicht und darf es nie ersetzen.

## Lebenszyklus des Refs

1. **Anlage** (Schritt 2): `git push origin "$CANDIDATE_SHA:refs/heads/release/vX.Y.Z"`
   auf den Freeze-Kandidaten. Vor der Anlage darf der Ref nicht existieren; ein
   vorhandener Ref derselben Version bedeutet einen abgebrochenen früheren
   Versuch und wird bewusst entschieden (löschen oder neue Patch-Version), nie
   überschrieben.
2. **Schutz** (Schritt 2): Ruleset auf `release/*` aktiv, bevor der erste
   Dispatch läuft.
3. **Nutzung** (Schritte 3, 5, 8, 9): jeder Dispatch mit vorheriger
   `verify-release-ref`-Prüfung.
4. **Aufbewahrung:** Der Ref bleibt bis zum Abschluss von Schritt 9 bestehen —
   der Post-Release-Update-Nachweis dispatcht auf ihn. Danach ist er
   entbehrlich, weil der Tag denselben Commit unveränderlich festhält.
5. **Löschung:** frühestens nach abgeschlossenem Schritt 9 und nur durch den
   Release-Owner. Ein Löschen ist **optional**; ein stehengelassener Ref ist
   harmlos, weil er geschützt und deckungsgleich mit dem Tag ist. Bei einem
   Hotfix entsteht ein neuer Ref mit der neuen Patch-Version.

## Konsequenzen

**Gewonnen.** `main` bleibt während eines Releases mergebar. Ein Merge
verbrennt den Kandidaten nicht mehr — er verändert nur `main`, während der
Kandidat auf seinem eigenen, geschützten Ref liegt. Das Release-Fenster ist
damit nicht länger eine Sperre für alle anderen Arbeiten.

**Eingekauft.** Die Workflow-**Definition** eines Dispatches stammt jetzt vom
Kandidaten-Commit statt vom aktuellen `main`. Ein nach dem Freeze auf `main`
gemergter Fix an `release-abnahme.yml` oder `release-publish.yml` wirkt für
diese Kandidatenlinie **nicht** rückwirkend, sondern erst ab dem nächsten
Kandidaten. Das ist dieselbe bewusst in Kauf genommene Eigenschaft, die für den
Aggregations-Job bereits in [RELEASE_AUTOMATION.md](../RELEASE_AUTOMATION.md)
§4.1 beschrieben ist — und sie ist hier sogar die *gewünschte* Wirkung: Der
veröffentlichte Stand wird mit der Prozesslogik geprüft, die zu ihm gehört,
nicht mit einer später hinzugekommenen. Wer einen Prozessfehler mitten im
Release beheben muss, baut einen neuen Kandidaten — genau wie bei jeder anderen
Änderung.

**Unverändert.** Fünf Dateien, byteidentisch, Draft-first, kein Clobber. Ein
Kandidatenlauf, ein Freigabemanifest. `candidate-source` als hartes SHA-Gate.
Die Go-/No-Go-Entscheidung bleibt menschlich.

## Verworfene Alternativen

- **Beim `main`-Freeze bleiben.** Der Status quo. Verworfen, weil der Freeze
  keine Prüfung trägt: Er kostete bei v2.9.0 47,5 Stunden Durchsatz, ohne dass
  eine einzige Zusicherung an ihm hing.
- **Auf den Release-Tag dispatchen statt auf einen Branch.** Funktioniert
  technisch (Schritt 9 macht es), scheitert aber am Zeitpunkt: Der Tag entsteht
  erst in Schritt 7, die Schritte 3 und 5 brauchen den Ref vorher. Außerdem
  tragen Tags den Ruleset-Schutz gegen Force-Push nicht in derselben Form wie
  Branches.
- **Einen langlebigen `release`-Branch führen.** Verworfen, weil er über
  mehrere Releases hinweg mutiert und damit genau die Unveränderlichkeit
  verlöre, die den Ref auszeichnet. Ein Ref je Version ist unveränderlich und
  nach dem Release entbehrlich.
- **Den Ref nur dokumentieren, ohne Verifikationskommando.** Verworfen: Die
  Prüfung wird vor vier Dispatches gebraucht. Vier kopierte Shell-Blöcke sind
  die Drift-Quelle, die dieses Repository an anderer Stelle mit eigenen
  Wächtern bekämpft.

## Nachweise

- `scripts/release_contract.py verify-release-ref` — Ref-Schema, Commit-Objekt,
  SHA-Gleichheit; netzfrei über die `gh api`-Antwort.
- `tests/test_release_contract.py` — Positiv- und Negativfälle der Prüfung.
- `tests/test_release_governance.py` — das Runbook dispatcht auf den Release-Ref
  und nicht mehr auf `main`; die `MAIN_SHA`-Konvention ist verschwunden.
- `tests/test_release_abnahme_workflow.py` — das `candidate-source`-Gate bleibt
  als hartes SHA-Gate erhalten.
