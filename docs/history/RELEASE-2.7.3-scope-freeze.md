# Release 2.7.3 – stabiler Scope-Freeze

Nachfolger von [`RELEASE-2.7.2-scope-freeze.md`](RELEASE-2.7.2-scope-freeze.md).
Dieses Dokument enthält ausschließlich Angaben, die **vor** seinem Merge
bekannt sind. Kandidaten-SHA, Commitliste, Pfadklassifikationen und Zähler
werden nicht nachgetragen, sondern beim Gate aus Git abgeleitet und als
maschinenlesbare Provenienz außerhalb der Git-Historie gespeichert (siehe
[`RELEASE-2.7.2-scope-freeze.md`](RELEASE-2.7.2-scope-freeze.md) bzw. #742).

## Stabile, maschinenlesbare Angaben

- **Basis-Tag:** `v2.7.2` (= `230c61e6578fd6f73ff650dd737c903ed42b397e`)
- **Kandidatenversion:** `2.7.3`
- **Release-Scope:** `patch-release-2.7.3`
- **Pfadpolicy:** `release/path-policy.json` (Version `3`)

Der volle Basis-SHA ist unveränderlich. Der Tagname allein genügt nicht: Das
Gate weist ein verschobenes Tag zurück. Die Policy-Version bindet die Semantik,
mit der alle Pfade im Fenster `Basis..Laufkopf` klassifiziert werden.

## Scope

Der Patch-Release veröffentlicht ausschließlich einen bereits gemergten
Sicherheitsfix, der seit v2.7.2 im `[Unreleased]`-Abschnitt aller sechs
CHANGELOG-Dateien lag, ohne dass ein Kandidat dafür gebaut wurde:

- **#769 (CVE-2025-5683, ICNS-DoS in `QImage`):** `_recent_thumbnail_icon`
  (`bgremover/right_panel.py`) lädt „Zuletzt geöffnet“-Thumbnails jetzt über
  die validierte Pillow-Pipeline (`open_validated_image`) statt über ein
  direktes `QPixmap(path)`, das den Dateiinhalt anhand der Bytes statt der
  Endung erkennt und damit an der Pillow-Format-Whitelist der App vorbeiging
  (PR #782).

Die übrigen Commits seit v2.7.2 sind ausschließlich Release-Tooling,
Doku-Governance und CI-Diagnose ohne Auswirkung auf das Programmverhalten –
u. a. der GitHub-Live-Check gegen `RECOMMENDATIONS.md`-Drift (#752/#783),
die Entkopplung des ClamAV-Signaturbezugs vom Release-Build (#779/#780), das
Scoping des Vision-API-Zugriffs (#656/#778), die selbstdokumentierende
`UPDATE-01`-Vorgängerartefakt-Prüfung (#748/#763/#776) sowie mehrere
CLAUDE.md-/TESTING.md-Doku-Nachträge (#764–#768/#771, #775). Sie sind Teil
des First-Parent-Fensters und werden vom Gate einzeln klassifiziert, ändern
aber nicht den fachlichen Scope dieses Patch-Release: **nur #769 wird
Anwender:innen sichtbar.**

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
die Run-ID bilden die externe Identität.

## Pfadklassen

Die einzige Quelle ist [`release/path-policy.json`](../../release/path-policy.json):

- `release-neutral` ist eine enge positive Allowlist mit Begründung und
  Build-Input-Nachweis je Eintrag.
- `candidate-relevant` umfasst bekannte Produkt-, Metadaten-, Build-, Test-,
  Workflow-, Release- und Evidenzpfade.
- unbekannte Pfade sind kandidatenrelevant **und blockierend**, bis die Policy
  bewusst ergänzt und versioniert wurde.

Die Policy-Version ist gegenüber dem 2.7.2-Freeze unverändert auf `3`
(zuletzt durch #780 angehoben, vor dem Basis-Tag v2.7.2 gemergt). Kein
Policy-Nachtrag ist für diesen Kandidaten nötig.

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

- #781 verfolgt die Persistenz der Vision-Einzelverdikte aus der
  Abnahme-Automation als eigenständige Verbesserung; sie blockiert diesen
  Patch-Release nicht.
- Epic #741 bleibt bis zum praktischen Nachweis „keine zweite
  Hardware-Abnahme nach Tag/Publish“ in einem künftigen Releasezyklus offen
  (siehe `RECOMMENDATIONS.md`).
