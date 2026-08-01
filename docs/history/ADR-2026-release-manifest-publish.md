# ADR-2026: Byteidentische Veröffentlichung aus dem Freigabemanifest

**Status:** Akzeptiert
**Datum:** 2026-08-01
**Entscheider:** Repository-Owner
**Bezug:** #741, #742, #744, #747

## Kontext

Der frühere Tag-Push startete `release-linux.yml` erneut. Damit wurden nach der
Hardware-Abnahme neue Dateien gebaut; die abgenommenen SHA-256-Werte waren
nicht die der veröffentlichten Bytes. Außerdem trug die Plattform-Evidenz den
`GITHUB_SHA` des Abnahme-Workflows statt des Quell-Builds. Run-ID, Workflow und
`head_sha` der Artefaktquelle wurden vor der Freigabe nicht als gemeinsamer
Vertrag geprüft.

## Entscheidung

Der Release-Pfad besteht aus drei getrennten, manuellen Workflows:

1. `release-linux.yml` baut einen Kandidaten auf genau einem Commit. Er hat
   keinen Tag-Trigger, keine Schreibrechte und keinen Publish-Job. Drei
   unveränderliche Artefaktcontainer enthalten genau fünf Dateien; die
   Freeze-Provenienz aus #742 liegt attempt-spezifisch daneben.
2. `release-abnahme.yml` erhält ausschließlich die Build-Run-ID. Ein
   GitHub-hosted Vorjob prüft Run-ID, Workflow-Pfad, erfolgreichen Abschluss,
   Quell-`head_sha`, Actions-Artefakt-IDs/-Digests, Freeze-Provenienz und die
   exakte Fünfermenge. Die Self-hosted Jobs müssen auf demselben Commit laufen
   und schreiben diesen Quell-SHA in ihre Evidenz. Nur eine vollständige
   technische Abschlussmatrix erzeugt ein Freigabemanifest.
3. `release-publish.yml` erhält Tag, Build-Run-ID, Abnahme-Run-ID und den
   exakten Manifest-Artefaktnamen. Er validiert beide Run-Metadaten, beide
   Workflow-Pfade, Run-Attempts, Tag/Version, Tag→Commit, Freeze-Provenienz,
   Plattformstatus, Dateinamen, Größen und SHA-256. Die fünf Dateien werden
   ausschließlich über die im Manifest gebundene Build-Run-ID geladen. Der
   Workflow enthält keinen Build-Schritt.

Es gibt **keine freeze-equivalent-Ausnahme**. Build, Abnahme und Tag müssen
denselben 40-stelligen Commit-SHA nennen. Eine spätere release-neutrale
Änderung rechtfertigt keinen anderen veröffentlichten Commit; bei Bedarf wird
ein neuer Kandidat gebaut und abgenommen.

## Freigabemanifest

`release-approval-manifest.json` hat Schema- und Policy-Version `1` und enthält:

- Kandidaten-Run-ID/-Attempt, Workflow-Pfad und Quell-`head_sha`;
- Version und erwarteten Tag;
- Referenzen (Name, ID, Archiv-Digest) auf die drei Build-Container;
- Referenz und Nutzlast-SHA-256 der Freeze-Provenienz;
- Abnahme-Run-ID/-Attempt, Workflow-Pfad und `head_sha`;
- Status je Plattform (`approved`; Linux x86_64 bis zur Reaktivierung explizit
  `paused`);
- exakt fünf Datensätze `{name, sha256, bytes, platform,
  acceptance_status}`;
- UTC-Erzeugungszeitpunkt.

Das Manifest liegt als attempt-spezifisches, unveränderliches Actions-Artefakt
`release-approval-manifest-<attempt>` im Abnahme-Run. Eine eigene Artefakt-ID
kann es nicht ohne Selbstreferenz in seinen Inhalt aufnehmen; `(Abnahme-Run-ID,
exakter Artefaktname)` ist deshalb seine eindeutige Referenz. GitHub bindet das
hochgeladene Artefakt anschließend zusätzlich an ID und Digest.

## Veröffentlichung und Wiederholung

Der Publish-Workflow arbeitet Draft-first:

- kein Release vorhanden → leeren Draft erzeugen, fünf Dateien hochladen,
  erneut herunterladen, gegen das Manifest hashen, erst dann veröffentlichen;
- leerer vorhandener Draft → Upload fortsetzen;
- vollständiger byteidentischer Draft → ohne Upload veröffentlichen;
- bereits veröffentlicht und byteidentisch → erfolgreicher No-op;
- teilweise, zusätzliche oder abweichende Assets → **harter Abbruch ohne
  automatische Änderung**.

Beim letzten Fall entscheidet der Owner ausdrücklich, ob der Draft/die Assets
bereinigt werden oder ein neuer Tag verwendet wird. Es gibt weder `--clobber`
noch automatisches Löschen. Ein fehlgeschlagener Teil-Upload bleibt unsichtbar
als Draft und kann nicht versehentlich als gemischtes Release erscheinen.

Build-, Evidenz-, Matrix- und Manifest-Artefakte werden für 90 Tage
aufbewahrt. Das deckt den vorgesehenen Build→Hardware-Abnahme→Publish-Abstand;
nach Ablauf wird kein Publish improvisiert, sondern ein neuer Kandidat erzeugt.

## Verworfene Alternativen

- **Tag-Push baut erneut:** verworfen, weil die veröffentlichten Bytes nicht
  die abgenommenen sind.
- **Freeze-equivalent statt identischer Commit:** verworfen; zusätzliche
  Klassifikations- und Rekonstruktionsregeln würden die zentrale Aussage
  unnötig abschwächen.
- **Issue-Kommentar als Freigabequelle:** verworfen; Kommentare sind
  veränderlich und kein Run-/Artefaktvertrag.
- **Automatisches Reparieren partieller Releases:** verworfen; Löschen oder
  Clobber könnte einen sichtbaren, zuvor funktionierenden Zustand zerstören.

## Konsequenzen

- Ein Release veröffentlicht nachweislich dieselben fünf Bytes, die die
  Hardware-Abnahme geprüft hat.
- Ein Tag allein kann keinen Build und keine Veröffentlichung mehr auslösen.
- Manipulierte/missing/extra Artefakte sowie falsche Runs, Workflows, Commits,
  Tags oder Plattformstatus blockieren vor der ersten Release-Mutation.
- Der Bedienablauf benötigt zwei Run-IDs und einen Manifestnamen; diese Werte
  sind im Actions-Lauf sichtbar und im Runbook dokumentiert.
- `tests/test_release_contract.py`, `tests/test_release_gate.py` und
  `tests/test_release_abnahme_workflow.py` fixieren den Vertrag einschließlich
  Negativ-, Retry- und Bytegleichheitstests (#747).
