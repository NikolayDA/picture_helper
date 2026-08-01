# ADR-2026: Release-Freeze-Provenienz außerhalb der Git-Historie

**Status:** Akzeptiert
**Datum:** 2026-08-01
**Entscheider:** Repository-Owner
**Bezug:** #741, #742, #743, späterer Verbraucher #744

## Kontext

Das bisherige Freeze-Dokument enthielt einen Kandidaten-Pin, eine exakte
Commit-Anzahl und eine Tabelle mit vollständigen Commit-SHAs. Diese Werte sind
erst nach dem Merge des kandidatenrelevanten Commits bekannt. Dadurch war nach
jedem solchen Merge ein reiner Nachtrags-Commit nötig; dessen eigener SHA war
wiederum nicht im Dokument darstellbar. Das Problem ist strukturelle
Selbstreferenz, kein Bedienfehler.

Gleichzeitig muss das Gate folgende Eigenschaften behalten:

- unveränderlicher Basis-SHA,
- vollständige First-Parent-Historie bis zum geprüften Laufkopf,
- fail-closed Pfadklassifikation,
- maschinenlesbare Bindung an Workflow und Run,
- spätere Wiederverwendung durch den Publish-Vertrag aus #744.

## Entscheidung

Wir verwenden **Option A: Historie ableiten und Evidenz als unveränderliches
GitHub-Actions-Artefakt erzeugen**.

Das versionierte Freeze-Dokument enthält nur Version, Basis-Tag samt vollem
Basis-SHA, Scope und Policy-Version. Der Kandidat ist der geprüfte Workflow-Kopf
`GITHUB_SHA`. `scripts/verify_release_freeze.py` leitet Commitliste,
Pfadklassifikationen und Zähler aus `Basis..GITHUB_SHA` ab und schreibt
`release-freeze-provenance.json`.

Die Pfadsemantik kommt ausschließlich aus `release/path-policy.json`:

- enge positive Neutral-Allowlist,
- bekannte relevante Pfade mit Begründung,
- unbekannt = kandidatenrelevant und blockierend.

Der Workflow lädt die Provenienz unter einem attempt-spezifischen Namen hoch.
GitHub bindet das Artefakt an Run-ID, Artefakt-ID und Digest. Ein Validator
kann Basis, Kandidat, Inhaltskandidat, Policy-Digest, Commitliste und alle
Pfadklassifikationen aus Git rekonstruieren. #744 wird diesen Validator gegen
den freizugebenden Kandidaten aufrufen.

## Erwogene Optionen

### A – Abgeleitete Actions-Evidenz (gewählt)

| Dimension | Bewertung |
|---|---|
| Komplexität | Mittel |
| Selbstreferenz | Vollständig entfernt |
| Schutz | Run-/Artefaktidentität, Digest, Rekonstruktion aus Git |
| Betrieb | Nutzt vorhandene Actions-Infrastruktur |
| Aufbewahrung | Begrenzt; #744 überführt den Nachweis später in das Freigabemanifest |

**Vorteile:** Kein Repository-Nachtrag, unmittelbar maschinenlesbar, heute
umsetzbar, klarer Verbraucherpfad für #744.
**Nachteile:** Actions-Artefakte haben eine endliche Aufbewahrungsdauer; bis
#744 ist die Evidenz noch nicht dauerhaft an veröffentlichte Bytes gebunden.

### B – Git Notes

| Dimension | Bewertung |
|---|---|
| Komplexität | Mittel bis hoch |
| Selbstreferenz | Entfernt |
| Schutz | Separater, leicht übersehener und verschiebbarer Ref-Namespace |
| Betrieb | Zusätzliche Fetch-/Push-/Schutzregeln auf jedem Client und Runner |

**Vorteile:** Git-native Zuordnung zu einem Commit.
**Nachteile:** Notes werden standardmäßig weder geklont noch angezeigt; Schutz,
Backup und Berechtigungen wären ein neuer Betriebsvertrag.

### C – Manuelles Ledger oder verschobener Pin im Repository

| Dimension | Bewertung |
|---|---|
| Komplexität | Niedrig |
| Selbstreferenz | Nicht gelöst |
| Schutz | Bestehende Tests, aber weiterhin Folge-Commit nötig |

**Verworfen:** Verschiebt das Problem nur in eine andere Datei oder Tabelle und
verletzt das zentrale Akzeptanzkriterium von #742.

### D – Signierte Attestation als erster Schritt

| Dimension | Bewertung |
|---|---|
| Komplexität | Hoch |
| Selbstreferenz | Entfernt |
| Schutz | Sehr stark bei vollständiger OIDC-/Attestation-Kette |
| Betrieb | Zusätzliche Infrastruktur und Verifikationswerkzeuge |

**Zurückgestellt:** Für die spätere Supply-Chain-Härtung sinnvoll, aber für das
Entfernen des Freeze-Nachtrags unnötig breit. Das JSON-Schema kann später als
Attestation-Payload dienen.

## Konsequenzen

- Kandidatenrelevante Merges benötigen keinen Freeze-Nachtrag mehr.
- Die vollständige Commit-Tabelle verschwindet aus dem aktiven Freeze-Dokument.
- Eine neue oder unbekannte Datei stoppt den Release, bis ihre Klasse bewusst
  in der versionierten Policy dokumentiert ist.
- Eine reine release-neutrale Änderung bleibt in der Provenienz sichtbar,
  verschiebt aber den kandidatenrelevanten Inhaltskopf nicht.
- Policy-Version und Digest werden Teil jeder Evidenz.
- Bis #744 bleibt die dauerhafte Bindung an genau fünf veröffentlichte Bytes
  offen; die Actions-Evidenz ist der dafür vorgesehene Eingang.

## Umsetzung

- [x] Versionierte Pfadpolicy und gemeinsamer Klassifikator (#743)
- [x] Freeze-Dokument auf stabile Angaben reduzieren
- [x] Provenienzgenerator und Rekonstruktionsprüfung
- [x] Actions-Upload mit Run-/Attempt-Bindung
- [x] Regressionstests für Selbstreferenz und Manipulation
- [ ] Provenienz mit exakt fünf abgenommenen Artefakten verbinden (#744)
- [ ] Dauerhafte Freigabemanifest-Aufbewahrung definieren (#744/#745)
