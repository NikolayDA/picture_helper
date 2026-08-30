# Versionierte Release-Abnahme-Checkliste

**Owner:** Repository-Owner
**Schema:** `1`
**Checklisten-Version:** `2.0.0`
**Gültigkeit:** für alle Releases, deren Freigabemanifest diese Version und den
vollständigen Commit-SHA sowie den SHA-256 dieser Datei pinnt.

## Zweck und Bindung

Diese Datei ist der verbindliche, release-unabhängige Abnahmevertrag. Eine
konkrete Release-Instanz entsteht im Freigabemanifest und speichert für jede
stabile Kriteriums-ID Status und Evidenz. Der Pin besteht aus:

- `path`: `docs/RELEASE_ACCEPTANCE_CHECKLIST.md`
- `checklist_version`: semantische Version dieser Definition
- `commit_sha`: vollständiger Kandidaten-Commit
- `sha256`: SHA-256 der Checklisten-Datei an genau diesem Commit

Änderungen an Bedeutung, Pflichtgrad, Plattformumfang oder Evidenzquelle
erhöhen mindestens die Minor-Version; inkompatible Änderungen erhöhen die
Major-Version. Alte Manifeste bleiben durch Commit und Dateihash
interpretierbar. Rechtschreibkorrekturen ohne Bedeutungsänderung dürfen die
Patch-Version erhöhen.

## Zustände

| Zustand | Bedeutung |
|---|---|
| `PASS` | Kriterium ist durch die verlinkte Evidenz erfüllt. |
| `FAIL` | Evidenz belegt einen Fehler; Veröffentlichung beziehungsweise Abschluss stoppt gemäß Pflichtgrad. |
| `WAIVED` | Owner hat eine ausdrücklich erlaubte Abweichung mit Begründung und Evidenz genehmigt. |
| `NOT_APPLICABLE` | Das Kriterium gilt nach seiner Definition nachweislich nicht; niemals Ersatz für fehlende Hardware. |
| `PENDING` | Noch nicht geprüft oder bewusst pausiert; gilt nicht als erfüllt. |

`MUST` muss vor Ende seiner Phase `PASS` sein oder – nur wenn das Kriterium es
erlaubt – einen vollständigen `WAIVED`-Datensatz tragen. `SHOULD` darf sichtbar
`PENDING` bleiben und wird in der Go-/No-Go-Entscheidung begründet.
`POST_RELEASE` blockiert den Tag nicht, muss aber für den fachlichen
Release-Abschluss abgearbeitet werden.

Ein Waiver enthält immer Owner, Begründung und mindestens einen
Evidenzverweis. Ein technischer Ausfall ist kein Waiver. Linux x86_64 ist
derzeit `PENDING`/pausiert und ausdrücklich **nicht** erfüllt.

## Plattform- und Artefaktumfang

| Artefakt-ID | Plattform | Format | Hardware-Status |
|---|---|---|---|
| `linux-x86_64-appimage` | Linux x86_64 | AppImage | pausiert, offen |
| `linux-x86_64-deb` | Linux x86_64 | `.deb` | pausiert, offen |
| `linux-arm64-appimage` | Linux arm64/Raspberry Pi | AppImage | Pflicht |
| `linux-arm64-deb` | Linux arm64/Raspberry Pi | `.deb` | Pflicht |
| `macos-arm64-dmg` | macOS arm64 | DMG | Pflicht |

Windows gehört nicht zum Releasevertrag. Eine neue Plattform erfordert eine
neue Checklisten-Version und eigene, stabile IDs.

## Kriterien

| ID | Phase | Pflicht | Owner | Erwartete Evidenz |
|---|---|---|---|---|
| `VERSION-01` | Pre-Release | MUST | Release-Owner | Freeze-Provenienz und Kandidatenvertrag: Paketversion, Tag-Erwartung, CHANGELOG und Release-Body konsistent |
| `FREEZE-01` | Pre-Release | MUST | Release-Owner | fail-closed Pfadklassifikation, Policy-Digest und vollständiger Kandidaten-Commit |
| `BUILD-01` | Pre-Release | MUST | CI | erfolgreicher `release-linux.yml`-Run auf exakt dem Kandidaten-Commit nach Full CI |
| `BUILD-02` | Pre-Release | MUST | CI | genau fünf Dateien, eindeutige Namen, Größen und SHA-256 im Kandidatenvertrag |
| `PROVENANCE-01` | Pre-Release | MUST | CI | unveränderliche Build-/Freeze-Artefakt-IDs und Digests |
| `LINUX-ARM-APPIMAGE-01` | Pre-Release | MUST | Hardware-Abnahme | AppImage auf realem Linux arm64: Start, gepackte Herkunft und natives 3D |
| `LINUX-ARM-DEB-01` | Pre-Release | MUST | Hardware-Abnahme | `.deb` auf realem Linux arm64: Installation, Start, gepackte Herkunft, natives 3D, Entfernen |
| `MACOS-ARM-DMG-01` | Pre-Release | MUST | Hardware-Abnahme | DMG-App auf realem macOS arm64: Start, gepackte Herkunft, Retina und natives 3D |
| `LINUX-X64-APPIMAGE-01` | Pre-Release | SHOULD | Hardware-Abnahme | AppImage auf realem Linux x86_64; derzeit sichtbar pausiert |
| `LINUX-X64-DEB-01` | Pre-Release | SHOULD | Hardware-Abnahme | `.deb` auf realem Linux x86_64; derzeit sichtbar pausiert |
| `SPAWN-LINUX-ARM-01` | Pre-Release | MUST | Hardware-Abnahme | Haupt- und Spawn-Kindprozess laden ausschließlich Bundle-Code |
| `SPAWN-MACOS-ARM-01` | Pre-Release | MUST | Hardware-Abnahme | Haupt- und Spawn-Kindprozess starten ohne Fork-Bomb/Hänger |
| `E2E-LINUX-ARM-01` | Pre-Release | MUST | Hardware-Abnahme | Projekt öffnen, HEIGHT/3D ready, Undo/Redo, kontrollierte Kopie speichern und neu laden |
| `E2E-MACOS-ARM-01` | Pre-Release | MUST | Hardware-Abnahme | Projekt öffnen, HEIGHT/3D ready, Undo/Redo, kontrollierte Kopie speichern und neu laden |
| `VISIBLE-VERSION-01` | Pre-Release | MUST | Hardware-Abnahme | sichtbare Produktversion stammt aus dem Bundle und stimmt mit dem Artefaktnamen überein |
| `SCREENSHOT-01` | Pre-Release | SHOULD | Release-Owner | native Screenshots; Vision ist nur Vorbewertung, finale Freigabe menschlich |
| `MALWARE-01` | Pre-Release | SHOULD | Security-Owner | Scannerzustand `PASS`, `FAIL` oder sichtbar nicht verfügbar; bei vorhandenem Cache EICAR-Erfolg und je Artefakt Rohdatei + entpackte Nutzlast mit mehr als 0 gescannten Bytes, keine Limitüberschreitung; Malware-Fund blockiert immer |
| `NOTES-01` | Pre-Release | MUST | Release-Owner | Release Notes nennen Auswirkung, Plattformen, Einschränkungen und Upgrade-/Rollback-Hinweis |
| `PUBLISH-01` | Publish | MUST | Release-Owner | Tag zeigt auf Manifest-`head_sha`; Publish verwendet Kandidaten- und Abnahme-Run |
| `PUBLISH-02` | Publish | MUST | CI | erneut geladene öffentliche Assets sind exakt die fünf Manifestdateien und byteidentisch |
| `PUBLISH-03` | Publish | MUST | CI | Draft-first; partielle oder abweichende Zustände blockieren ohne Clobber |
| `PUBLIC-DOWNLOAD-01` | Publish | MUST | CI | `public-download-report.json` des Publish-Laufs: alle fünf Assets anonym über `browser_download_url` geladen und gegen Manifesthash geprüft |
| `ROLLBACK-01` | Publish | SHOULD | Release-Owner | Go/No-Go, Yank/Rollback oder Hotfix-Entscheidung ist protokolliert |
| `UPDATE-LINUX-ARM-01` | Post-Release | POST_RELEASE | Hardware-Abnahme | Linux arm64: echtes Vorgänger-AppImage meldet `UPDATE_AVAILABLE`, Kandidat `UP_TO_DATE`, Fehler = `CHECK_FAILED`; das `.deb` ist mit abgedeckt, weil es byteidentisch dieselbe AppImage installiert |
| `UPDATE-MACOS-ARM-01` | Post-Release | POST_RELEASE | Hardware-Abnahme | macOS arm64: derselbe Nachweis aus dem gepackten DMG-Bundle über den In-Prozess-Hook `BGREMOVER_UPDATE_CHECK_PROBE`; setzt einen Vorgänger ≥ 2.7.3 voraus |

`UPDATE-01` ist seit Checklisten-Version 2.0.0 (#917) in zwei
Plattformkriterien geteilt. Der reale v2.9.0-Nachweis prüfte nur den
Linux-arm64-Kanal, während die eine gemeinsame ID drei Artefakte deklarierte —
die maschinenlesbare Deklaration behauptete also mehr, als nachgewiesen wurde.
Getrennte IDs machen jetzt sichtbar, welcher Kanal geprüft ist: Linux arm64
über den in der AppImage gebündelten Interpreter (rückwirkend gegen jedes
Artefakt), macOS arm64 über den In-Prozess-Hook des DMG-Bundles, der erst ab
v2.7.3 existiert. Beide tragen dieselbe Bewertungsreihenfolge; ein
`CHECK_FAILED` gilt nirgends als „kein Update".

`PUBLIC-DOWNLOAD-01` entsteht seit Checklisten-Version 1.1.0 (#916) als
`public-download-report.json` im Nachweis-Job von `release-publish.yml`: Der
Job lädt alle fünf Assets **nach** dem Veröffentlichen anonym über ihre
`browser_download_url` und vergleicht sie mit demselben `verify-artifacts`
gegen das Freigabemanifest wie der Publish-Job zuvor. Der Release-Owner liest
den Bericht und setzt das Kriterium; die frühere Handprozedur bleibt in
[RELEASE_PROCESS.md](RELEASE_PROCESS.md) als Rückfallweg dokumentiert.

Die detaillierten Hardware-Prozeduren stehen in
[PACKAGING_SMOKE.md](PACKAGING_SMOKE.md). Der vollständige Ablauf, Wiederanlauf,
Rollback und die Pflege der Release-Instanz stehen im
[Release-Runbook](RELEASE_PROCESS.md). Runnerbetrieb und Labels stehen in
[RELEASE_AUTOMATION.md](RELEASE_AUTOMATION.md).

## Maschinenlesbarer Vertrag

Der folgende JSON-Block ist Teil dieser Datei und wird von
`scripts/release_contract.py validate-checklist` gelesen. Tabelle und JSON
müssen dieselben IDs beschreiben; Tests verhindern Drift.

<!-- release-checklist-json:start -->
```json
{
  "schema": 1,
  "kind": "release-acceptance-checklist",
  "checklist_version": "2.0.0",
  "allowed_states": ["PASS", "FAIL", "WAIVED", "NOT_APPLICABLE", "PENDING"],
  "phases": ["pre-release", "publish", "post-release"],
  "requirements": ["MUST", "SHOULD", "POST_RELEASE"],
  "artifacts": [
    {"id": "linux-x86_64-appimage", "platform": "linux-x86_64", "format": "AppImage"},
    {"id": "linux-x86_64-deb", "platform": "linux-x86_64", "format": "deb"},
    {"id": "linux-arm64-appimage", "platform": "linux-arm64", "format": "AppImage"},
    {"id": "linux-arm64-deb", "platform": "linux-arm64", "format": "deb"},
    {"id": "macos-arm64-dmg", "platform": "macos-arm64", "format": "dmg"}
  ],
  "criteria": [
    {"id": "VERSION-01", "phase": "pre-release", "requirement": "MUST", "owner": "release-owner", "evidence_source": "freeze provenance + candidate contract", "description": "Version, expected tag, changelog and release body are consistent.", "artifacts": [], "verification": "candidate-contract", "waiver_allowed": false, "not_applicable_allowed": false},
    {"id": "FREEZE-01", "phase": "pre-release", "requirement": "MUST", "owner": "release-owner", "evidence_source": "release-freeze-provenance.json", "description": "Fail-closed path classification and candidate head are proven.", "artifacts": [], "verification": "candidate-contract", "waiver_allowed": false, "not_applicable_allowed": false},
    {"id": "BUILD-01", "phase": "pre-release", "requirement": "MUST", "owner": "ci", "evidence_source": "release-linux.yml run", "description": "Candidate build and full CI succeeded on the exact head.", "artifacts": [], "verification": "candidate-contract", "waiver_allowed": false, "not_applicable_allowed": false},
    {"id": "BUILD-02", "phase": "pre-release", "requirement": "MUST", "owner": "ci", "evidence_source": "release-candidate-contract.json", "description": "Exactly five named files, sizes and SHA-256 values are bound.", "artifacts": ["linux-x86_64-appimage", "linux-x86_64-deb", "linux-arm64-appimage", "linux-arm64-deb", "macos-arm64-dmg"], "verification": "candidate-contract", "waiver_allowed": false, "not_applicable_allowed": false},
    {"id": "PROVENANCE-01", "phase": "pre-release", "requirement": "MUST", "owner": "ci", "evidence_source": "Actions artifact IDs and digests", "description": "Build containers and freeze evidence are immutable and referenced.", "artifacts": [], "verification": "candidate-contract", "waiver_allowed": false, "not_applicable_allowed": false},
    {"id": "LINUX-ARM-APPIMAGE-01", "phase": "pre-release", "requirement": "MUST", "owner": "hardware-acceptance", "evidence_source": "linux-arm64 evidenz.json", "description": "AppImage starts from bundled code and renders native 3D.", "artifacts": ["linux-arm64-appimage"], "verification": "platform:linux-arm64", "waiver_allowed": false, "not_applicable_allowed": false},
    {"id": "LINUX-ARM-DEB-01", "phase": "pre-release", "requirement": "MUST", "owner": "hardware-acceptance", "evidence_source": "linux-arm64 evidenz.json", "description": "Deb installs, starts from bundled code, renders and removes cleanly.", "artifacts": ["linux-arm64-deb"], "verification": "platform:linux-arm64", "waiver_allowed": false, "not_applicable_allowed": false},
    {"id": "MACOS-ARM-DMG-01", "phase": "pre-release", "requirement": "MUST", "owner": "hardware-acceptance", "evidence_source": "macos-arm64 evidenz.json", "description": "DMG app starts from bundled code with Retina and native 3D evidence.", "artifacts": ["macos-arm64-dmg"], "verification": "platform:macos-arm64", "waiver_allowed": false, "not_applicable_allowed": false},
    {"id": "LINUX-X64-APPIMAGE-01", "phase": "pre-release", "requirement": "SHOULD", "owner": "hardware-acceptance", "evidence_source": "linux-x86_64 evidenz.json", "description": "AppImage hardware smoke on Linux x86_64; currently paused and open.", "artifacts": ["linux-x86_64-appimage"], "verification": "platform:linux-x86_64", "waiver_allowed": true, "not_applicable_allowed": false},
    {"id": "LINUX-X64-DEB-01", "phase": "pre-release", "requirement": "SHOULD", "owner": "hardware-acceptance", "evidence_source": "linux-x86_64 evidenz.json", "description": "Deb hardware smoke on Linux x86_64; currently paused and open.", "artifacts": ["linux-x86_64-deb"], "verification": "platform:linux-x86_64", "waiver_allowed": true, "not_applicable_allowed": false},
    {"id": "SPAWN-LINUX-ARM-01", "phase": "pre-release", "requirement": "MUST", "owner": "hardware-acceptance", "evidence_source": "linux-arm64 waechter_ergebnisse + acceptance-extra", "description": "Main and spawned child load bundled code without a fork bomb.", "artifacts": ["linux-arm64-appimage", "linux-arm64-deb"], "verification": "platform:linux-arm64", "waiver_allowed": false, "not_applicable_allowed": false},
    {"id": "SPAWN-MACOS-ARM-01", "phase": "pre-release", "requirement": "MUST", "owner": "hardware-acceptance", "evidence_source": "macos-arm64 waechter_ergebnisse + acceptance-extra", "description": "Main and spawned child start without fork bomb or hang.", "artifacts": ["macos-arm64-dmg"], "verification": "platform:macos-arm64", "waiver_allowed": false, "not_applicable_allowed": false},
    {"id": "E2E-LINUX-ARM-01", "phase": "pre-release", "requirement": "MUST", "owner": "hardware-acceptance", "evidence_source": "linux-arm64 e2e-evidenz.json + acceptance-extra", "description": "Project, HEIGHT, native 3D, undo/redo and save/reload roundtrip pass.", "artifacts": ["linux-arm64-appimage", "linux-arm64-deb"], "verification": "platform:linux-arm64", "waiver_allowed": false, "not_applicable_allowed": false},
    {"id": "E2E-MACOS-ARM-01", "phase": "pre-release", "requirement": "MUST", "owner": "hardware-acceptance", "evidence_source": "macos-arm64 e2e-evidenz.json + acceptance-extra", "description": "Project, HEIGHT, native 3D, undo/redo and save/reload roundtrip pass.", "artifacts": ["macos-arm64-dmg"], "verification": "platform:macos-arm64", "waiver_allowed": false, "not_applicable_allowed": false},
    {"id": "VISIBLE-VERSION-01", "phase": "pre-release", "requirement": "MUST", "owner": "hardware-acceptance", "evidence_source": "acceptance_extra_*.json", "description": "Visible bundled version matches the external artifact-name expectation.", "artifacts": ["linux-arm64-appimage", "linux-arm64-deb", "macos-arm64-dmg"], "verification": "active-platforms", "waiver_allowed": false, "not_applicable_allowed": false},
    {"id": "SCREENSHOT-01", "phase": "pre-release", "requirement": "SHOULD", "owner": "release-owner", "evidence_source": "native screenshots + vision-verdikte.json", "description": "Native screenshots are human-approved; model output is advisory only.", "artifacts": ["linux-arm64-appimage", "linux-arm64-deb", "macos-arm64-dmg"], "verification": "manual", "waiver_allowed": true, "not_applicable_allowed": false},
    {"id": "MALWARE-01", "phase": "pre-release", "requirement": "SHOULD", "owner": "security-owner", "evidence_source": "candidate scan evidence and #731 decision", "description": "Scanner availability is explicit; with a restored database, EICAR passes and every raw artifact plus extracted payload reports nonzero scanned bytes without limit alerts; every malware finding blocks.", "artifacts": ["linux-x86_64-appimage", "linux-x86_64-deb", "linux-arm64-appimage", "linux-arm64-deb", "macos-arm64-dmg"], "verification": "manual", "waiver_allowed": true, "not_applicable_allowed": false},
    {"id": "NOTES-01", "phase": "pre-release", "requirement": "MUST", "owner": "release-owner", "evidence_source": "CHANGELOG release section", "description": "Notes name impact, supported platforms, limitations and upgrade/rollback guidance.", "artifacts": [], "verification": "candidate-contract", "waiver_allowed": false, "not_applicable_allowed": false},
    {"id": "PUBLISH-01", "phase": "publish", "requirement": "MUST", "owner": "release-owner", "evidence_source": "release-publish.yml run metadata", "description": "Tag and both recorded runs refer to the accepted candidate head.", "artifacts": [], "verification": "publish", "waiver_allowed": false, "not_applicable_allowed": false},
    {"id": "PUBLISH-02", "phase": "publish", "requirement": "MUST", "owner": "ci", "evidence_source": "post-upload download + manifest verification", "description": "Public release contains exactly the five byte-identical manifest files.", "artifacts": ["linux-x86_64-appimage", "linux-x86_64-deb", "linux-arm64-appimage", "linux-arm64-deb", "macos-arm64-dmg"], "verification": "publish", "waiver_allowed": false, "not_applicable_allowed": false},
    {"id": "PUBLISH-03", "phase": "publish", "requirement": "MUST", "owner": "ci", "evidence_source": "publish state plan", "description": "Draft-first promotion blocks partial or divergent state without clobber.", "artifacts": [], "verification": "publish", "waiver_allowed": false, "not_applicable_allowed": false},
    {"id": "PUBLIC-DOWNLOAD-01", "phase": "publish", "requirement": "MUST", "owner": "ci", "evidence_source": "public-download-report.json (release-publish.yml)", "description": "All five public assets are downloaded anonymously and match their manifest hashes.", "artifacts": ["linux-x86_64-appimage", "linux-x86_64-deb", "linux-arm64-appimage", "linux-arm64-deb", "macos-arm64-dmg"], "verification": "publish", "waiver_allowed": false, "not_applicable_allowed": false},
    {"id": "ROLLBACK-01", "phase": "publish", "requirement": "SHOULD", "owner": "release-owner", "evidence_source": "release decision log", "description": "Go/no-go and any yank, rollback or hotfix decision are recorded.", "artifacts": [], "verification": "manual", "waiver_allowed": true, "not_applicable_allowed": true},
    {"id": "UPDATE-LINUX-ARM-01", "phase": "post-release", "requirement": "POST_RELEASE", "owner": "hardware-acceptance", "evidence_source": "linux-arm64 update_check/update_check.json (#748)", "description": "Linux arm64: predecessor AppImage reports UPDATE_AVAILABLE, candidate UP_TO_DATE, failures CHECK_FAILED. The deb is covered by the same run because it installs the byte-identical AppImage.", "artifacts": ["linux-arm64-appimage", "linux-arm64-deb"], "verification": "post-release", "waiver_allowed": false, "not_applicable_allowed": false},
    {"id": "UPDATE-MACOS-ARM-01", "phase": "post-release", "requirement": "POST_RELEASE", "owner": "hardware-acceptance", "evidence_source": "macos-arm64 update_check/update_check.json (#917)", "description": "macOS arm64: the same proof from the packaged DMG bundle via the in-process BGREMOVER_UPDATE_CHECK_PROBE hook; requires a predecessor of 2.7.3 or newer.", "artifacts": ["macos-arm64-dmg"], "verification": "post-release", "waiver_allowed": false, "not_applicable_allowed": false}
  ]
}
```
<!-- release-checklist-json:end -->

## Instanz- und Waiver-Regeln

Das Freigabemanifest enthält unter `release_instance` die Checklistenreferenz
und exakt einen Datensatz je ID. Nach Publish wird diese Instanz als separates
Abschlussprotokoll weitergeführt; das unveränderliche Freigabemanifest wird
nicht editiert. Die Kommandos und Ablageorte stehen im
[Release-Runbook](RELEASE_PROCESS.md).

Ein vollständiger Waiver-Datensatz hat dieses Format:

```json
{
  "owner": "github-login-or-role",
  "reason": "konkrete, releasebezogene Begründung",
  "evidence": ["https://github.com/NikolayDA/picture_helper/issues/…"]
}
```

`NOT_APPLICABLE` ist nur zulässig, wenn das Kriterium
`not_applicable_allowed: true` trägt. Die pausierten x86_64-Kriterien bleiben
`PENDING`; sie dürfen nicht als `NOT_APPLICABLE` oder `PASS` umgedeutet werden.

## Änderungsverlauf

| Version | Datum | Änderung | Referenz |
|---|---|---|---|
| `2.0.0` | 2026-08-30 | `UPDATE-01` in `UPDATE-LINUX-ARM-01` und `UPDATE-MACOS-ARM-01` geteilt (stabile ID entfällt ⇒ Major); Deklaration und Nachweis je Plattform deckungsgleich, `.deb`-Identitätsbegründung im Kriteriumstext | #917 |
| `1.1.0` | 2026-08-30 | `PUBLIC-DOWNLOAD-01` auf automatisierte Evidenz umgestellt (`verification: publish`, Owner CI, `public-download-report.json`) | #916 |
| `1.0.0` | 2026-08-01 | Erste versionierte Fassung mit stabilen IDs, Phasen, Pflichtgraden und Artefaktumfang | #746 |
