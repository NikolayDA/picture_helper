# Release 2.7.2 – stabiler Scope-Freeze

Nachfolger von [`RELEASE-2.7.1-scope-freeze.md`](RELEASE-2.7.1-scope-freeze.md).
Dieses Dokument enthält seit #742 ausschließlich Angaben, die **vor** seinem
Merge bekannt sind. Kandidaten-SHA, Commitliste, Pfadklassifikationen und
Zähler werden nicht mehr nachgetragen, sondern beim Gate aus Git abgeleitet und
als maschinenlesbare Provenienz außerhalb der Git-Historie gespeichert.

## Stabile, maschinenlesbare Angaben

- **Basis-Tag:** `v2.7.1` (= `a3de137a0c0873f93f84186f9bba32d684a48808`)
- **Kandidatenversion:** `2.7.2`
- **Release-Scope:** `patch-release-2.7.2`
- **Pfadpolicy:** `release/path-policy.json` (Version `3`)

Der volle Basis-SHA ist unveränderlich. Der Tagname allein genügt nicht: Das
Gate weist ein verschobenes Tag zurück. Die Policy-Version bindet die Semantik,
mit der alle Pfade im Fenster `Basis..Laufkopf` klassifiziert werden.

## Scope

Der Patch-Release umfasst die seit v2.7.1 aufgenommenen Korrekturen an
Release-Abnahme, Evidenz und Release-Governance:

- vollständigere Artefakt- und Produktnachweise aus #734/#686,
- Versionsschnitt und Diagnosehärtung aus #735,
- Laufzeit-Herkunft für Haupt- und Kindprozess aus #738,
- checkout-freier Linux-Artefaktstart aus #750/#740,
- enge, positive Pfadklasse `release-neutral` aus #743,
- extern abgeleitete Freeze-Provenienz ohne Pin-/Ledger-Nachtrag aus #742.

Änderungen außerhalb dieses Patch-Scope benötigen vor dem Build eine bewusste
Scope-Entscheidung. Unbekannte Pfade blockieren das Gate fail-closed, auch wenn
sie vorsichtshalber als kandidatenrelevant gelten.

## Kandidat und Commit-Ledger

Der Kandidaten-SHA ist der von GitHub Actions geprüfte Laufkopf
(`GITHUB_SHA`). `scripts/verify_release_freeze.py` rekonstruiert aus der
First-Parent-Historie seit dem Basis-SHA:

1. alle Commits in ältester Reihenfolge,
2. alle gegenüber dem ersten Parent geänderten Pfade ohne
   Umbenennungserkennung,
3. die Regel und Klasse jedes Pfades,
4. die primäre Klasse jedes Commits,
5. den jüngsten kandidatenrelevanten Inhaltscommit.

Ein exakter Post-Merge-SHA, eine Commit-Anzahl oder eine manuelle SHA-Tabelle
stehen bewusst **nicht** in diesem Dokument. Ein kandidatenrelevanter Merge
kann daher unmittelbar geprüft und gebaut werden, ohne anschließend einen
reinen Freeze-Nachtrags-Commit zu benötigen.

Lokale Prüfung:

```bash
make release-freeze-check
python scripts/verify_release_freeze.py \
  --output-provenance /tmp/release-freeze-provenance.json
python scripts/verify_release_freeze.py \
  --verify-provenance /tmp/release-freeze-provenance.json
```

Im Workflow lädt `verify-candidate` die Datei als unveränderliches Actions-Artefakt
`release-freeze-provenance-<run_attempt>` hoch. Sie enthält zusätzlich
Repository, Workflow, Run-ID, Run-Attempt, Job und Ref. Der Artefakt-Digest und
die Run-ID bilden die externe Identität; #744 kann die Datei herunterladen und
gegen den erwarteten Kandidaten erneut rekonstruieren.

## Pfadklassen

Die einzige Quelle ist [`release/path-policy.json`](../../release/path-policy.json):

- `release-neutral` ist eine enge positive Allowlist mit Begründung und
  Build-Input-Nachweis je Eintrag.
- `candidate-relevant` umfasst bekannte Produkt-, Metadaten-, Build-, Test-,
  Workflow-, Release- und Evidenzpfade.
- unbekannte Pfade sind kandidatenrelevant **und blockierend**, bis die Policy
  bewusst ergänzt und versioniert wurde.

`README.md` bleibt wegen `pyproject.toml:[project].readme` relevant.
`docs/i18n/**` ist keine neutrale Verzeichnisklasse: übersetzte CHANGELOG- und
Lizenz-Snapshots sind relevante Gate-Eingänge; nur einzeln belegte Dateien wie
die Recommendations stehen in der Neutral-Allowlist. Die geplanten Dokumente
`docs/RELEASE_PROCESS.md` (#745) und
`docs/RELEASE_ACCEPTANCE_CHECKLIST.md` (#746) sind bereits ausdrücklich als
kandidatenrelevant klassifiziert.

## Verbindliche Konsistenzprüfungen

Das Gate prüft am Laufkopf:

- Paketversion gegen dieses Dokument,
- datierte CHANGELOG-Abschnitte und Release-Body-Pflichtangaben in sechs
  Sprachen,
- AppStream-Version und -Datum,
- sechs Lizenz-Snapshots,
- unveränderten Basis-Tag/SHA,
- Policy-Version und Policy-Digest,
- vollständige, explizite Pfadklassifikation aller First-Parent-Commits,
- Bindung des Kandidaten an `GITHUB_SHA` und die Actions-Run-IDs.

Die Entscheidung und verworfene Alternativen stehen in
[`ADR-2026-release-freeze-provenienz.md`](ADR-2026-release-freeze-provenienz.md).

## Noch offene Release-Schuld

- #744 muss exakt die abgenommenen fünf Artefakte samt dieser Provenienz
  veröffentlichen, statt sie beim Tag-Push neu zu bauen.
- #745 bündelt den gesamten Ablauf später in einem kanonischen Runbook.
- #746 führt die versionierte Abnahme-Checkliste mit stabilen IDs ein.
- #748 prüft nach Publish den produktiven Update-Pfad aus einem echten
  Vorgängerartefakt.
