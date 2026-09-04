**Deutsch** · [English](docs/i18n/en/RECOMMENDATIONS.md) · [Español](docs/i18n/es/RECOMMENDATIONS.md) · [Français](docs/i18n/fr/RECOMMENDATIONS.md) · [Українська](docs/i18n/uk/RECOMMENDATIONS.md) · [简体中文](docs/i18n/zh/RECOMMENDATIONS.md)

# Codeanalyse & bewertete Empfehlungen: BgRemover

## Bewertungsskala

| Symbol | Priorität | Bedeutung |
|--------|-----------|-----------|
| 🔴 | Kritisch | Fehler, Abstürze oder Datenverlust |
| 🟠 | Hoch | Spürbarer Einfluss auf Zuverlässigkeit oder Wartbarkeit |
| 🟡 | Mittel | Sinnvolle Verbesserung für Qualität, Lesbarkeit oder Testbarkeit |
| 🟢 | Niedrig | Optionales Polishing oder Prozessverbesserung |

## Aktueller Stand (2026-09-03, v2.9.0 veröffentlicht, offener Bestand vollständig geprüft)

**Tagesaudit 2026-09-02 (Stand `91b32b4`):** Alle 42 offenen Issues wurden mit
Code, Merges, Kommentaren und – beim Mac-App-Store-Epic – aktuellen
Primärquellen abgeglichen. Statuskorrekturen stehen nun direkt in #681, #688,
#691, #682/#693, #914/#918 und #949. Inhaltlich neu: Die Lizenz/Provenienz des
separaten `u2net.onnx`-Artefakts ist nicht als Apache-2.0 belegt (#883/#893),
Apple kann auch bei einer Gratis-App Zahlungskontoangaben für Trader verlangen
(#884/#904), und die App-Downloadvalidierung muss in #895/#899/#906 ausdrücklich
entschieden und getestet werden. Kein neuer Produktfehler und kein 🔴-Befund.

**Nachprüfung 2026-09-03 (Stand `e7c379d`):** Die neuen PRs #955–#957 wurden
gegen die offenen Punkte geprüft. PR #956 hat die falsche Evidenzreferenz des
EufyMake-Profils bewusst innerhalb der noch unveröffentlichten v1 korrigiert
und zusätzliche Snapshot-/Bundle-Guards ergänzt; der frühere releasekritische
#691-Punkt ist damit erledigt. #955 betrifft die Test-Suite-Dokumentation, #957
die Release-Skripte; beide verändern die EufyMake-Empirie nicht.

**Release-Einschätzung: noch kein Kandidat angestoßen.** Seit `v2.9.0`
(2026-08-29) liegen am geprüften Mainline-Stand `e7c379d` 34 Commits vor. Mit PR #953 (versioniertes
EufyMake-Zielprofil, 16-Bit-HEIGHT-Default, Profil- und X/Y-DPI-Anzeige im
Dialog, Manifest-Provenienz) steht erstmals ein nutzersichtbarer Eintrag in
`[Unreleased]`; alles andere ist Release-Automatisierung, Doku und Governance.
Ob **v2.10.0** mit #953 allein oder erst zusammen mit der COLOR-Tonwert-Engine
(#693/#694 aus Epic #682, ADR #692) gebaut wird, ist ein Owner-Entscheid. PR
#956 hat die falsche Evidenzreferenz mit bewusster v1-Entscheidung und
Golden-/Bundle-Guards korrigiert. Damit besteht aus #691 kein zusätzlicher
Releaseblocker; das normale Release-Gate bleibt maßgeblich.

**EufyMake #681/#687–#691:** PRs #948, #951–#953, #956, #959–#961 sind gemergt; der reproduzierbare Satz umfasst 42 Einzel-Fixtures und sieben unveränderte echte Exportpakete (Schema 5). Alle 29 verpflichtenden druckfreien Importzellen sind in Studio 4.2.2 abgeschlossen. Neben nativem 8-/16-Bit-HEIGHT, COLOR/HEIGHT-Crop und `Gloss Varnish` ist nun belegt: gleiche Seitenrelation wird trotz abweichender Pixelmaße akzeptiert, eine abweichende HEIGHT-Seitenrelation dagegen mit `Depth image ratio does not match the original image` abgelehnt. I-14 ergänzt ein direkt erzeugtes, nicht vorgefiltertes 256-/128-px-Kanten-/Impuls-Paar; beide Varianten sind importseitig vorgeprüft. I-09 (`.empf`) bleibt nicht blockierend. Offen sind nur noch die physischen E1-Messungen zu #688–#690 und die Abschluss-Review von #687.

Unverändert abgeschlossen: **N1/N2/N4/N5/N6/N7/N8**, **O1–O8**, alles seit **2026-06-25** Erledigte, die Releases v2.7.0–v2.9.0 sowie Epic #741 mit seinen elf Teil-Issues, Epic #805 mit #806–#811, #817 und #821; seit dem letzten Sync neu geschlossen: #943 (PR #944), #692 (PR #947) sowie der ANLEITUNG-Review #963 samt #964–#966, #968 und #969 (PR #972) und #967 (PR #973) sowie das Test-Suite-Audit #949 (PR #977) und der PDF-Wächter #974 (PR #979) (Details: Vorige Runden).

Offener Bestand: eine Zeile je Issue in der Triage-Tabelle unten. Weder Zahl noch Zeilen werden seit #821 von Hand gepflegt – `scripts/recommendations_live_check.py --write` schreibt die Tabellen aller sechs Fassungen aus dem GitHub-Live-Stand fort, die Bewertungsspalten bleiben Handarbeit.

## Offene GitHub-Issues – Triage-Stand

| # | Titel | Relevanz | Komplexität | Empfohlenes Modell (Aufwand) | Nächster Schritt |
|---|-------|----------|--------------|-------------------------------|-------------------|
| [#681](https://github.com/NikolayDA/picture_helper/issues/681) | [Epic] EufyMake-Zielprofil – Height/Gloss/mm-DPI validieren | 🟠 Hoch (Korrektheit des wichtigsten Exportziels) | 🔴 Hoch (5 Teil-Issues, physische Hardware nötig) | – (Epic) | Profilintegration und alle 29 druckfreien Pflichtzellen sind erledigt; I-09 ist nicht blockierend. Offen: Hardwaretests #688–#690 und Abschluss-Review |
| [#687](https://github.com/NikolayDA/picture_helper/issues/687) | Annahmeninventar, Herstellerquellen, Testmatrix | 🟠 Hoch (verbindliche Grundlage für #688–#691) | 🔴 Hoch (Repository-Material vollständig; Rest braucht reale Hardware) | – (kein Agent; reale EufyMake-Hardware nötig) | Blocked (extern) – 17/18 Akzeptanzkriterien und alle 29 verpflichtenden Importzellen erledigt. Offen ist nur die Abschluss-Review nach #688–#690 |
| [#688](https://github.com/NikolayDA/picture_helper/issues/688) | HEIGHT-Bittiefe/-Semantik auf realer Hardware validieren | 🟠 Hoch (Reliefhöhe direkt betroffen) | 🔴 Hoch (physischer Drucker, Fixtures, Messprotokoll) | – (kein Agent; reale EufyMake-Hardware nötig) | Blocked (extern) – einschließlich des direkt erzeugten I-14-Filterpaars sind alle Preflights abgeschlossen; offen bleiben physische Präzisions-, Filter-, Relief- und mm-Messungen |
| [#689](https://github.com/NikolayDA/picture_helper/issues/689) | mm/DPI, Zielgröße, Positionierungsvertrag validieren | 🟠 Hoch (Druckgröße/Registrierung) | 🔴 Hoch (physische Messungen, Kontrollmotive) | – (kein Agent; reale Hardware nötig) | Blocked (extern) – Studio-Teilvertrag einschließlich Crop und HEIGHT-Seitenverhältnis ist belegt. Offen sind nur physische Registrierung, Messungen und Drucktoleranzen |
| [#690](https://github.com/NikolayDA/picture_helper/issues/690) | Gloss-/Klarlack-Semantik validieren | 🟡 Mittel (Gloss ist laut Code bereits „experimental“) | 🔴 Hoch (physische Drucke, Materialverbrauch) | – (kein Agent; reale Hardware nötig) | Blocked (extern) – der native Ink Mode `Gloss Varnish` ist vorgeprüft; offen bleiben zellspezifische Registrierung sowie physische Polarität, Intensität und Materialwirkung |
| [#691](https://github.com/NikolayDA/picture_helper/issues/691) | Versioniertes Zielprofil in Validator/Writer/Dialog/Doku | 🟠 Hoch (härtet den produktiven Exportpfad) | 🟢 Niedrig für den releasekritischen Rest; 🔴 Hardware für Abschluss | Sonnet, mittel + später Hardware | Implementierung releasebereit – PR #953 integriert Profil v1, PR #956 korrigiert die Evidenzreferenz mit bewusster v1-Entscheidung und Guards; nur die spätere Hochstufung nach #688–#690 bleibt offen |
| [#682](https://github.com/NikolayDA/picture_helper/issues/682) | [Epic] COLOR-Tonwert-/Graustufen-Engine | 🟡 Mittel-Hoch (Roadmap-Fundament für Laser, kein akuter Bug) | 🔴 Hoch (4 verbleibende Teil-Issues: Kern→UI→Integration→Abnahme) | – (Epic) | In Bearbeitung – ADR #692 ist verabschiedet; als Nächstes den Kern #693 |
| [#693](https://github.com/NikolayDA/picture_helper/issues/693) | Qt-freier Kern: Histogramm/Graustufe/Levels/Gamma | 🟡 Mittel-Hoch | 🟡 Mittel (Erweiterung von `color_ops.py`, gut isoliert testbar) | Sonnet, hoch | Startbereit – ADR #692 (PR #947) liefert den Datenvertrag; Kern gegen dessen Formeln implementieren und testen |
| [#694](https://github.com/NikolayDA/picture_helper/issues/694) | Live-Vorschau + Bedienoberfläche Histogramm/Levels/Gamma | 🟡 Mittel | 🟡 Mittel-Hoch (Qt-UI, Debounce/Generation-Schutz analog Höhen-Vorschau) | Sonnet, hoch | Blocked – wartet auf Kern #693 |
| [#695](https://github.com/NikolayDA/picture_helper/issues/695) | Ebenen-/Auswahl-/History-/Projektintegration | 🟡 Mittel | 🟠 Hoch (viele Zustandsübergänge: Undo/Redo, Auswahl, Dirty-State) | Opus, hoch | Blocked – wartet auf #693/#694 |
| [#696](https://github.com/NikolayDA/picture_helper/issues/696) | Performance-/E2E-/Doku-/Laser-Schnittstellenabnahme | 🟡 Mittel (Abschluss-Gate, kein neues Feature) | 🟠 Hoch (Benchmark-Suite, E2E, Doku, Adapter-Contract) | Opus, hoch | Blocked – Abschluss-Issue nach #695 |
| [#882](https://github.com/NikolayDA/picture_helper/issues/882) | [Epic] BgRemover im Mac App Store | 🟡 Mittel-Hoch (neuer Distributionskanal, kein aktueller Produktfehler) | 🔴 Hoch (Lizenz, Sandbox, Paketierung, Store und Release-Governance) | – (Epic) | Blocked – zuerst #883 entscheiden; dabei Qt-/Code-Lizenz und die ungeklärte Provenienz/Rechte des Modellartefakts getrennt behandeln |
| [#883](https://github.com/NikolayDA/picture_helper/issues/883) | [MAS] Lizenzstrategie: PySide6 vs. Riverbank und Relizenzierung | 🟠 Hoch (harter Blocker für jede technische MAS-Arbeit) | 🔴 Hoch (Lizenz-/Owner-Entscheid, möglicher Qt-Port, Restrisiko) | Opus, hoch + Owner/Rechtsprüfung | Startbereit – ADR/Owner-Entscheid erstellen und für das konkrete `u2net.onnx` Herkunft, Lizenz und Weiterverteilungsrecht belegen oder Ersatzmodell wählen |
| [#884](https://github.com/NikolayDA/picture_helper/issues/884) | [MAS] Apple Developer Program Enrollment | 🟠 Hoch (blockiert Zertifikate und Store-Zugang) | 🟢 Niedrig (manueller Konto-/Zahlungsschritt) | – (kein Agent; Account Holder) | Blocked (extern) – Kontotyp, Enrollment/2FA und Renewal klären; Gratis-App braucht keinen Paid-Apps-Vertrag, Trader können laut Apple dennoch Zahlungskontoangaben brauchen (#904) |
| [#885](https://github.com/NikolayDA/picture_helper/issues/885) | [MAS] Signing-Identitäten, App-ID und Provisioning-Profil | 🟠 Hoch (Voraussetzung für signierten Store-Build) | 🟡 Mittel (Owner-Secrets plus Bundle-ID-/Packaging-Vertrag) | – (kein Agent; Account Holder/Admin) | Blocked – wartet auf #884; danach Zertifikate, explizite App-ID und Profil erzeugen sowie Bundle-ID fixieren |
| [#886](https://github.com/NikolayDA/picture_helper/issues/886) | [MAS] App-Sandbox-Entitlements definieren und anwenden | 🟠 Hoch (zwingende Store- und Laufzeitvoraussetzung) | 🟠 Hoch (alle Mach-O-Dateien, Packaging- und Hardware-Nachweis) | Opus, hoch | Blocked – wartet auf Lizenzentscheid #883; danach minimale Entitlements plus Artefakt-/Hardwaretests umsetzen |
| [#887](https://github.com/NikolayDA/picture_helper/issues/887) | [MAS] Sandbox-tauglicher Inferenz-Kindprozess | 🟠 Hoch (KI-Kernfunktion muss im Store-Build laufen) | 🔴 Hoch (Spawn/Helper-Signierung, Zwei-Key-Regel, echte Sandbox) | Opus, hoch | Blocked – wartet auf #886; Re-Exec/Helper entscheiden und KI-Selfcheck auf Hardware belegen |
| [#888](https://github.com/NikolayDA/picture_helper/issues/888) | [MAS] Security-scoped Bookmarks für Dateien und Verzeichnisse | 🟠 Hoch (Recent Files und Quick-Save brechen sonst nach Neustart) | 🟠 Hoch (persistente Grants, Bilder/Projekte/Verzeichnisse, Kanal-Gating) | Opus, hoch | Blocked – wartet auf #886; Bookmark-Vertrag implementieren und Neustartfall sandboxed prüfen |
| [#889](https://github.com/NikolayDA/picture_helper/issues/889) | [MAS] Sandbox-sichere Schreibpfade und EufyMake-Export | 🟠 Hoch (Speicher- und Exportpfade, potenziell Datenintegrität) | 🔴 Hoch (Atomarität über mehrere Pfade und Powerbox-Grants) | Opus, hoch | Blocked – wartet auf #886; grant-konforme Atomarität/Endungen/Zielwahl entwerfen und auf Hardware prüfen |
| [#890](https://github.com/NikolayDA/picture_helper/issues/890) | [MAS] KI-Modell-Cache im Sandbox-Container | 🟡 Mittel (deterministischer Modellpfad im Store-Kanal) | 🟡 Mittel (isolierter Pfadvertrag plus Migrationsentscheid) | Sonnet, hoch | Blocked – wartet auf #886 und verzahnt mit #893; `U2NET_HOME` explizit setzen und Migration entscheiden |
| [#891](https://github.com/NikolayDA/picture_helper/issues/891) | [MAS] Distributionskanal-Flag und Update-Check-Gating | 🟠 Hoch (App-Store-Regel 2.4.5, keine Eigenupdates) | 🟠 Mittel-Hoch (zentrales Flag über Menü, Settings, Worker und Hooks) | Sonnet, hoch | Blocked – wartet auf #883; danach Kanalvertrag einführen und MAS-Netz-/UI-Pfade negativ testen |
| [#892](https://github.com/NikolayDA/picture_helper/issues/892) | [MAS] AiInstallDialog entfernen und KI-Backend bündeln | 🟠 Hoch (kein Nachinstallieren ausführbaren Codes im Store) | 🟡 Mittel (Kanal-Gating plus verbindlicher Packaging-Test) | Sonnet, hoch | Blocked – wartet auf #891; Dialog/Menü gaten und gebündeltes rembg/onnxruntime nachweisen |
| [#893](https://github.com/NikolayDA/picture_helper/issues/893) | [MAS] u2net-Modell bündeln oder beim Erststart laden | 🟠 Hoch (Review-Risiko und Funktionsfähigkeit der KI) | 🟠 Hoch (Produkt-/Review-Entscheid, Packaging oder neuer i18n-Flow) | Opus, hoch | Blocked – vor Variantenwahl konkrete Modellherkunft/-lizenz/-weiterverteilung über #883 belegen oder Ersatzmodell wählen; danach #890/#891 und Sandbox-Verifikation |
| [#894](https://github.com/NikolayDA/picture_helper/issues/894) | [MAS] Paketierungsweg Briefcase vs. py2app entscheiden | 🟠 Hoch (bestimmt die technische Machbarkeit des Kanals) | 🟠 Hoch (ergebnisoffener signierter Sandbox-/Upload-Spike) | Opus, hoch | Blocked – wartet auf #883; Briefcase-Spike durchführen, py2app als Fallback prüfen und ADR festhalten |
| [#895](https://github.com/NikolayDA/picture_helper/issues/895) | [MAS] onedir-App, Inside-out-Signierung und Qt-Store-Bereinigung | 🟠 Hoch (zentraler ausführbarer Store-Build) | 🔴 Hoch (alle Binaries, Qt, Provisioning, Upload-Validierung) | Opus, hoch | Blocked – nach #885/#886/#894 Build umsetzen, `AppTransaction` oder Receipt-Validierung fail-closed festlegen und ohne ITMS-Fehler prüfen |
| [#896](https://github.com/NikolayDA/picture_helper/issues/896) | [MAS] Info.plist und vollständiger Icon-Satz | 🟡 Mittel-Hoch (Store-Metadaten und Plattformvertrag) | 🟡 Mittel (Pflichtfelder, Architekturziel, deterministische Assets) | Sonnet, hoch | Blocked – wartet auf #895; Minimum-OS/Architektur und Dokumenttypen entscheiden, Plist/Icon-Tests ergänzen |
| [#897](https://github.com/NikolayDA/picture_helper/issues/897) | [MAS] signiertes productbuild-PKG und Transporter-Upload | 🟠 Hoch (einreichbares Store-Artefakt) | 🟠 Hoch (zweite Signatur, Build-Automation, manueller Erst-Upload) | Opus, hoch + Account Holder | Blocked – wartet auf #885/#895/#896; PKG reproduzierbar bauen und Delivery-Log belegen |
| [#898](https://github.com/NikolayDA/picture_helper/issues/898) | [MAS] Release-CI, Sechs-Artefakte-Vertrag und PKG-Scan | 🟠 Hoch (fail-closed Release-Integrität) | 🔴 Hoch (CI-Secrets, Vertrag, Entpacker, Malware-/Pfadscan) | Opus, hoch | Blocked – wartet auf #895/#897; MAS-Leg, Vertrag, Payload-Scan und Regressionstests gemeinsam erweitern |
| [#899](https://github.com/NikolayDA/picture_helper/issues/899) | [MAS] sandboxed Abnahme-Smokes auf echter Hardware | 🟠 Hoch (verbindliche Laufzeitevidenz für Kernpfade) | 🔴 Hoch (PKG, KI-Spawn, Powerbox, 3D und Evidenzschema) | Opus, hoch + macOS-Hardware | Blocked (extern) – nach #898 auf self-hosted ARM64 ausführen; gültigen und soweit reproduzierbar ungültigen App-Downloadnachweis in das Evidenzschema aufnehmen |
| [#900](https://github.com/NikolayDA/picture_helper/issues/900) | [MAS] TestFlight-Beta für macOS | 🟠 Hoch (frühe Review-/Fremdgeräte-Evidenz) | 🟡 Mittel (manuelle ASC-/Tester-Koordination) | – (kein Agent; Account Holder und Tester) | Blocked (extern) – wartet auf #897/#901; internen Build auf Fremdgerät mit KI, Dateien und 3D prüfen |
| [#901](https://github.com/NikolayDA/picture_helper/issues/901) | [MAS] App-Store-Connect-Record und Metadaten in sechs Sprachen | 🟠 Hoch (Name, Listing und Einreichungsvoraussetzung) | 🟠 Mittel-Hoch (Owner-Schritte plus sechs lokalisierte Metadatensätze) | Sonnet, hoch + Account Holder | Blocked – wartet auf #884/#885; Namen reservieren, Texte versionieren/einpflegen und Rating/Storefronts setzen |
| [#902](https://github.com/NikolayDA/picture_helper/issues/902) | [MAS] Store-Screenshot-Satz im 16:10-Format | 🟡 Mittel-Hoch (Pflichtmaterial für das Listing) | 🟡 Mittel (reproduzierbare Formate, Alpha-Check, Sprachentscheidung) | Sonnet, hoch | Blocked – wartet auf repräsentativen Build #895; Automation auf Store-Auflösungen erweitern und Satz prüfen |
| [#903](https://github.com/NikolayDA/picture_helper/issues/903) | [MAS] Privacy Policy und App-Privacy-Angaben | 🟠 Hoch (zwingende Store-/In-App-Pflicht) | 🟡 Mittel (Policy, Hosting, i18n-Link, Owner-Fragebogen) | Sonnet, hoch + Owner | Blocked – wartet auf Kanal-/Modellentscheid #891/#893; Policy hosten, in App/ASC verlinken und „Data Not Collected" belegen |
| [#904](https://github.com/NikolayDA/picture_helper/issues/904) | [MAS] EU-DSA-Status, Impressum und GPSR prüfen | 🟠 Hoch (EU-Storefronts und öffentliche Rechtspflichten) | 🟠 Mittel-Hoch (Owner-Selbsteinschätzung, Verifikation, Rechtsrisiko) | – (kein Agent; Owner/Rechtsprüfung) | Blocked (extern) – nach #884 Trader-Status, öffentliche Kontaktdaten, ggf. Zahlungskontoangaben sowie DDG/GPSR mit Owner/Wiedervorlage dokumentieren |
| [#905](https://github.com/NikolayDA/picture_helper/issues/905) | [MAS] Release-Governance um den Store-Kanal erweitern | 🟠 Hoch (verhindert einen Kanal neben dem fail-closed Vertrag) | 🟠 Hoch (Runbook, Checkliste, Vertrag, Path-Policy, sechs CHANGELOGs) | Opus, hoch | Blocked – begleitet #898/#899; vor Einreichung alle Governance-Verträge und Tests auf sechs Artefakte heben |
| [#906](https://github.com/NikolayDA/picture_helper/issues/906) | [MAS] Ersteinreichung und Review-Runde | 🟠 Hoch (manuelles Veröffentlichungs-Gate) | 🔴 Hoch (viele Abhängigkeiten, Restrisiken, Apple-Kommunikation) | – (kein Agent; Release-Owner) | Blocked (extern) – nach #896/#897/#899/#901–#905 inklusive App-Downloadvalidierung vorprüfen, einreichen und Ergebnis/Folge-Issues protokollieren |
| [#907](https://github.com/NikolayDA/picture_helper/issues/907) | [MAS] Betriebskonzept für Renewal, Updates und Kanäle | 🟡 Mittel-Hoch (langfristige Verfügbarkeit und Kanaltrennung) | 🟡 Mittel (Runbook, Verantwortungen, Erinnerungen, Kanalmatrix) | Opus, hoch + Owner | Blocked – Konzept vorab möglich, final nach #906; Renewal-/Update-/Webseiten-Routinen verbindlich verankern |
| [#914](https://github.com/NikolayDA/picture_helper/issues/914) | [Epic] Release-Prozess: Runner, automatisierte Nachweise, main-Freeze | 🟠 Hoch (Release-Betrieb; Implementierung weitgehend erledigt) | 🟢 Niedrig (zwei zeit-/ereignisgebundene Nachweise) | – (Epic) | Fast fertig – erster regulärer Dry-Run am 2026-09-03 04:40 UTC und beim nächsten echten Release End-to-End-Beleg inklusive #918 fehlen |
| [#918](https://github.com/NikolayDA/picture_helper/issues/918) | Release-Ref statt main-Freeze (ADR + fail-closed Absicherung) | 🟠 Hoch (`main` bleibt während eines Releases mergebar) | 🟢 Niedrig (Code, Doku und Ruleset stehen) | – (kein Agent; nächster Release-Lauf) | Blocked (extern) – am 2026-08-31 nach der Abschlussprüfung wiedereröffnet; PR #936 und der aktive Ruleset 21941216 sind belegt, offen ist nur ein Lauf, dessen Post-Release-Abnahme nachweislich auf `release/vX.Y.Z` startete |
| [#939](https://github.com/NikolayDA/picture_helper/issues/939) | Betrieb: Self-hosted-Runner (Heartbeat-Alarmkanal) | 🟡 Mittel (Betriebskanal, kein Produktcode) | 🟢 Niedrig (reine Beobachtung) | – (kein Agent; Repo-Owner) | Dauerhaft offen – nicht schließen (`RUNNER_HEARTBEAT_ISSUE`); der FAIL vom 2026-08-31 war der geplante Meldeweg-Test, der Aufräumschritt ist erledigt (planmäßiger Lauf 33496675995 grün, x86_64 übersprungen, Mac und Pi bestanden) |
| [#975](https://github.com/NikolayDA/picture_helper/issues/975) | eufymake: Beschriftungsträger 04 und 10 neu erzeugen und binden | 🟡 Mittel (zwei Testfelder auf dem Karton unbeschriftet; kein Blocker für die übrigen elf) | 🟢 Niedrig (Generator ist korrigiert; offen ist nur der Datennachzug) | – (kein Agent; macOS mit Arial nötig) | Blocked (extern) – unter Linux erzeugt Liberation Sans andere Bytes; Träger neu bauen, in Studio neu binden, `projects.json` nachziehen |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | OpenAI-Quota für manuellen Codex-Scan wiederherstellen | 🟢 Niedrig (blockiert nur einen optionalen manuellen Scan) | 🟢 Niedrig (rein operativ, kein Code) | – (kein Agent; Repo-Owner: Billing) | Blocked (extern) – letzter Lauf (29233060507, 2026-07-13) belegt keinen erfolgreichen Scan; Billing/Quota weiterhin offen |
| [#958](https://github.com/NikolayDA/picture_helper/issues/958) | Heartbeat: gestufte Offline-Eskalation 7/14/21 Tage (Mail-Hinweise, Austragung) und Wächter für die Fristen | 🟡 Mittel (Runner-Betrieb und Benachrichtigungen, kein Produktfehler) | 🟠 Hoch (Historienauswertung, idempotente Stufen, Workflow-Rechte, Tests und Doku) | Opus, hoch + Owner-Entscheid | Entscheidung nötig – E1 tägliche Kommentare, E2 automatische/manuelle Austragung und E3 Stufentage festlegen; danach fail-safe umsetzen und per Test-Issue abnehmen |

### Als Nächstes empfohlen

1. **#693** (Qt-freier Kern) – der ADR #692 ist verabschiedet; danach folgen
   #694, #695 und #696 in dieser Reihenfolge.
2. **#949** – vier kleine, klar umrissene Teständerungen; danach Baseline auf
   aktuellem `main` samt Plattform und optionalen Abhängigkeiten neu erfassen.
3. **#883** – Qt-/Code-Lizenz entscheiden und die Rechte/Provenienz des konkreten
   `u2net.onnx` belegen oder ein eindeutig lizenzierbares Ersatzmodell wählen.
4. Nach Geräte-/Materialfreigabe die offenen physischen Messungen aus **#689**
   zusammen mit #687 (Rest), #688 und #690 durchführen; native HEIGHT-/Gloss-
   Pfade und I-08 sind vorgeprüft. Danach #691
   abschließen: Profil v1 hochstufen oder bei Widerspruch v2 anlegen.

## Vorige Runden

Ausführliche Protokolle seit v2.2: [docs/history/RECOMMENDATIONS-2026-v2.2-v2.9.md](docs/history/RECOMMENDATIONS-2026-v2.2-v2.9.md).

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
