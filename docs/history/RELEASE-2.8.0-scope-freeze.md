# Release 2.8.0 – stabiler Scope-Freeze

Nachfolger von [`RELEASE-2.7.3-scope-freeze.md`](RELEASE-2.7.3-scope-freeze.md).
Dieses Dokument enthält ausschließlich Angaben, die **vor** seinem Merge
bekannt sind. Kandidaten-SHA, Commitliste, Pfadklassifikationen und Zähler
werden nicht nachgetragen, sondern beim Gate aus Git abgeleitet und als
maschinenlesbare Provenienz außerhalb der Git-Historie gespeichert (siehe
[`RELEASE-2.7.3-scope-freeze.md`](RELEASE-2.7.3-scope-freeze.md) bzw. #742).

## Stabile, maschinenlesbare Angaben

- **Basis-Tag:** `v2.7.3` (= `2eaf5295196fd482024f2a04cabf7fe6f8ee2e5a`)
- **Kandidatenversion:** `2.8.0`
- **Release-Scope:** `minor-release-2.8.0`
- **Pfadpolicy:** `release/path-policy.json` (Version `5`)

Der volle Basis-SHA ist unveränderlich. Der Tagname allein genügt nicht: Das
Gate weist ein verschobenes Tag zurück. Die Policy-Version bindet die Semantik,
mit der alle Pfade im Fenster `Basis..Laufkopf` klassifiziert werden.

## Scope

Anders als die letzten vier Patch-Releases (2.7.0–2.7.3) enthält dieser
Kandidat ein echtes neues Feature und wird deshalb bewusst als Minor-Version
statt als weiterer Patch geführt:

- **Epic #805 (#806–#811), Standard-/Experten-Umschalter im Karten-Inspector:**
  ein persistenter, global geltender Umschalter im Inspector-Kopf
  (`bgremover/expert_mode_toggle.py`, `right_panel.py`) blendet je Schritt
  eine kuratierte Basis-Ansicht ein; der Experten-Modus zeigt weiterhin exakt
  den vollen, unveränderten Funktionsumfang. Persistiert additiv über
  `QSettings` (`EXPERT_MODE_KEY`), Default Standard-Modus – ältere Versionen
  ignorieren den Schlüssel beim Downgrade. Details:
  [`docs/REDESIGN_SPEC.md`](../REDESIGN_SPEC.md) §15.
- **#795–#797 (EufyMake-Warnungstexte, Nachträge zu #687):** `#687`s
  Bittiefen-/Druckflächen-Fix landete bereits im `[Unreleased]`-Fenster vor
  diesem Kandidaten; `#795` liefert den zugrundeliegenden Validator-Fix,
  `#796/#797` schärfen anschließend nur die Warnungstexte (ZBrush-/
  Photoshop-Exportworkflow statt pauschaler 16-Bit-Pflicht) und die
  Annahmeninventar-Dokumentation dazu, ohne weiteres Anwenderverhalten zu
  ändern.

Die übrigen Commits seit v2.7.3 sind ausschließlich Release-Tooling,
Test-Fixtures und Doku-Governance ohne Auswirkung auf das Programmverhalten:
die ClamAV-/Recommendations-/3D-Evidenz-Härtung des Release-Gates (#793),
die Korrektur für absichtliche Einzelplattform-Abnahmeläufe (#791), die
Automatisierung des `RECOMMENDATIONS.md`-Live-Checks (#789/#790), das
Scroll-Verhalten des automatisierten 3D-Screenshot-Nachweises (#781/#788),
eine CLAUDE.md-Synchronisation (#794) sowie mehrere EufyMake-Governance- und
Fixture-Dokumentationsnachträge (#798–#804). Sie sind Teil des
First-Parent-Fensters und werden vom Gate einzeln klassifiziert, ändern aber
nicht den fachlichen Scope dieses Release: **nur Epic #805 und die
geschärften EufyMake-Warnungstexte sind Anwender:innen sichtbar.**

Änderungen außerhalb dieses Scope benötigen vor dem Build eine bewusste
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

Die Policy-Version wurde für diesen Kandidaten von `4` auf `5` angehoben: Das
Repointen von `current-freeze` auf dieses Dokument ließ den Pfad des
vorherigen aktiven Freeze-Dokuments (`RELEASE-2.7.3-scope-freeze.md`) ohne
Klassifikationsregel zurück. Ein neuer, expliziter
`historical-freeze-2.7.3`-Eintrag schließt die Lücke, analog zum
`historical-freeze-2.7.2`-Eintrag beim vorherigen Rollover.

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

- Epic #741 bleibt bis zum praktischen Nachweis „keine zweite
  Hardware-Abnahme nach Tag/Publish" für diesen Kandidaten offen (siehe
  `RECOMMENDATIONS.md`) – genau dieser Nachweis ist das Ziel des
  2.8.0-Releasezyklus.
- #781s Vision-Verdikt-Persistenz ist mit v2.7.3 bereits umgesetzt und wird
  hier nicht erneut nachgewiesen.
