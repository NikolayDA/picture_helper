# Release 2.9.0 – stabiler Scope-Freeze

Nachfolger von [`RELEASE-2.8.0-scope-freeze.md`](RELEASE-2.8.0-scope-freeze.md).
Dieses Dokument enthält ausschließlich Angaben, die **vor** seinem Merge
bekannt sind. Kandidaten-SHA, Commitliste, Pfadklassifikationen und Zähler
werden nicht nachgetragen, sondern beim Gate aus Git abgeleitet und als
maschinenlesbare Provenienz außerhalb der Git-Historie gespeichert (siehe
[`RELEASE-2.8.0-scope-freeze.md`](RELEASE-2.8.0-scope-freeze.md) bzw. #742).

## Stabile, maschinenlesbare Angaben

- **Basis-Tag:** `v2.8.0` (= `1bf95b08453b92a6d66cfc13622211bdf47cc5e2`)
- **Kandidatenversion:** `2.9.0`
- **Release-Scope:** `minor-release-2.9.0`
- **Pfadpolicy:** `release/path-policy.json` (Version `11`)

Der volle Basis-SHA ist unveränderlich. Der Tagname allein genügt nicht: Das
Gate weist ein verschobenes Tag zurück. Die Policy-Version bindet die Semantik,
mit der alle Pfade im Fenster `Basis..Laufkopf` klassifiziert werden.

## Scope

Der Kandidat enthält ein neues Feature und wird deshalb – wie schon 2.8.0 –
bewusst als Minor-Version statt als Patch geführt:

- **#863, Zoom-Pille auch in der 3D-Reliefvorschau:** Die schwebende
  Glas-Zoom-Pille (`bgremover/zoom_control.py`) bedient über das generische
  `ZoomTarget`-Protokoll jetzt auch die `Relief3DView` (Kamera-Zoom, 100 % =
  eingepasste Ansicht, gleiche ±10-%-Schritte; das Fixier-Schloss friert auch
  Mausrad- und Tasten-Zoom ein). Reiner UI-Zustand ohne History-Eintrag und
  ohne Schreibpfad ins Modell – die 3D-Vorschau bleibt reine Darstellung.
- **#839 (PR #846), Höhen-Live-Vorschau beim Moduswechsel:** Der Wechsel in den
  Standard-Modus und das Verlassen des Relief-Schritts verwerfen eine nicht
  angewendete Optimieren-Vorschau jetzt zuverlässig. Zuvor blieb sie am Canvas
  sichtbar, obwohl die Apply-/Verwerfen-Regler nicht mehr erreichbar waren –
  „Bild speichern" und der EufyMake-Export hätten dann vom unveränderten
  Modell exportiert. Der einzige Befund dieses Fensters, der Exportdaten
  betreffen konnte.
- **#864, Anwendungs-Icon zur Laufzeit:** `bgremover/icons/app_icon.png` liegt
  als Paketdaten bei und wird beim Start über `QApplication.setWindowIcon`
  gesetzt. Wirkt in **allen** Artefakten (macOS-App-Umschalter und
  Stage-Manager-Seitenleiste, Linux-Taskleisten ohne `.desktop`-Zuordnung).
- **#867/#868, zwei Inspector-Umbauten:** Der Modus-Hinweis unter dem
  Inspector-Kopf wird zum Tooltip am Standard-/Experten-Umschalter (Platz für
  die eigentlichen Werkzeuge), und der Primärbutton „Höhenkarte aus Bild
  erzeugen" steht kartenlos an der Spitze von Schritt 5. Reine
  Anordnungs-/Beschriftungsänderungen ohne Funktionsverlust.

Zwei weitere Korrekturen sind **nicht** im ausgelieferten `.dmg` wirksam,
sondern nur im aus dem Quellbaum gebauten macOS-App-Bundle. Sie berühren
ausschließlich `create_BgRemover_app.sh` und `diagnose_mac.sh`; das
Release-DMG entsteht über PyInstaller:

- **#865:** Der venv-Stub re-exec't bei Framework-Python das echte
  Interpreter-Binary in `Python.framework/…/Python.app`; das Bundle bettet
  jetzt eine Kopie als `Contents/MacOS/BgRemoverPython` ein, damit der Prozess
  unter der Identität von `BgRemover.app` läuft.
- **#866 (PR #870/#871):** Setup und Launcher erkennen die
  Hardware-Architektur unabhängig von einer übersetzten Shell; eine
  x86_64-App-venv auf Apple Silicon wird gemeldet statt unbemerkt unter
  Rosetta betrieben.

Die übrigen Commits seit v2.8.0 sind ausschließlich Test-, CI- und
Doku-Governance ohne Auswirkung auf das Programmverhalten: die
Reviewschleifen-Entschärfung und die Verschlankung des Review-Workflows
(#848/#850/#851/#852/#853/#855/#857/#858/#862/#875/#876), das Nachziehen der
Pfadpolicy um unklassifizierte Doku-Pfade (#861), die fail-safe
Vision-Vorbewertung (#817/#819), der Live-Check-Generator für die
Recommendations-Triage (#821/#823/#824), die UML-Prozessdiagramme
(#835/#842/#854), das Test-Suite-Audit (#869/#873), Marker- und
Governance-Tests (#831/#834/#845) sowie die laufenden
Recommendations-Synchronisationen (#818/#820/#822/#830/#838/#843/#872/#874).
Sie sind Teil des First-Parent-Fensters und werden vom Gate einzeln
klassifiziert, ändern aber nicht den fachlichen Scope dieses Release:
**anwender:innensichtbar sind nur #863, #839, #864, #867 und #868 sowie – im
selbst gebauten macOS-Bundle – #865 und #866.**

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

Die Policy-Version wurde für diesen Kandidaten zunächst von `5` auf `6`
angehoben: Das Repointen von `current-freeze` auf dieses Dokument ließ den
Pfad des vorherigen aktiven Freeze-Dokuments
(`RELEASE-2.8.0-scope-freeze.md`) ohne Klassifikationsregel zurück. Ein neuer,
expliziter `historical-freeze-2.8.0`-Eintrag schloss diese Lücke, analog zum
`historical-freeze-2.7.3`-Eintrag beim vorherigen Rollover.

Version `7` klassifiziert zusätzlich die durch #878 neu erzeugten
Screenshot-Sets als kandidatenrelevante Testevidenz: Der Doku-Referenztest
ermittelt aus diesem Verzeichnis das neueste Set und prüft dessen Manifest.
Der zuvor unbekannte und damit fail-closed blockierende Pfad wird dadurch zu
einem erlaubten Gate-Eingang; diese Änderung erfordert gemäß ADR-Nachtrag vom
2026-08-25 einen Versionssprung. Die sechs dabei angelegten
Recommendations-Archive sind dagegen als release-neutrale Statushistorie
einzeln nachgewiesen. Die 15 mit #861 ergänzten, ebenfalls release-neutralen
Doku-Pfade bleiben davon unberührt.

Version `8` klassifiziert die mit #918 entstandene
[`ADR-2026-release-ref-entkopplung.md`](ADR-2026-release-ref-entkopplung.md)
als kandidatenrelevant — dieselbe Vertragsklasse wie die übrigen
Release-Prozess-ADRs (Freeze-Provenienz, Manifest-Publish, ClamAV-Cache): Sie
legt fest, auf welchem Ref ein Release läuft und wie dessen Unveränderlichkeit
erzwungen wird. Ohne Eintrag blieb der Pfad unbekannt und blockierte
fail-closed — genau die vorgesehene Wirkung, hier im PR statt im
Kandidatenbau.

Der **veröffentlichte** Kandidat v2.9.0 (`d31073c7495ae9fd55501f595e8bda6cbcf4007b`, Tag `v2.9.0`) wurde noch
unter Policy-Version `6` gebaut, abgenommen und veröffentlicht; die
unveränderliche Freeze-Provenienz jenes Kandidatenlaufs hält diesen Stand
fest. Die Versionen `7` und `8` greifen erst ab dem nächsten Kandidatenbau.

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

- Der Meta-Freeze für Umbauten an der Review-Mechanik ist mit der
  abgeschlossenen Zehn-Läufe-Messung (10/10, Auswertung in
  [`ISSUE-841-VERIFIKATION.md`](ISSUE-841-VERIFIKATION.md)) beendet; #828 ist
  geschlossen. Für diesen Kandidaten besteht daraus keine offene Schuld.
- Die EufyMake-Hardwarevalidierung (#681, #687–#691) bleibt extern blockiert
  und ist bewusst **nicht** Teil dieses Scope: Der Exportpfad ist gegenüber
  2.8.0 unverändert.
