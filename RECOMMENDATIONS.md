**Deutsch** · [English](docs/i18n/en/RECOMMENDATIONS.md) · [Español](docs/i18n/es/RECOMMENDATIONS.md) · [Français](docs/i18n/fr/RECOMMENDATIONS.md) · [Українська](docs/i18n/uk/RECOMMENDATIONS.md) · [简体中文](docs/i18n/zh/RECOMMENDATIONS.md)

# Codeanalyse & bewertete Empfehlungen: BgRemover

## Bewertungsskala

| Symbol | Priorität | Bedeutung |
|--------|-----------|-----------|
| 🔴 | Kritisch | Fehler, Abstürze oder Datenverlust |
| 🟠 | Hoch | Spürbarer Einfluss auf Zuverlässigkeit oder Wartbarkeit |
| 🟡 | Mittel | Sinnvolle Verbesserung für Qualität, Lesbarkeit oder Testbarkeit |
| 🟢 | Niedrig | Optionales Polishing oder Prozessverbesserung |

## Aktueller Stand (2026-09-02, v2.9.0 veröffentlicht, offener Bestand vollständig geprüft)

**Tagesaudit 2026-09-02 (Stand `1ec9d96`):** 42 offene Issues gegen den
GitHub-Live-Stand geprüft. Die Triage-Tabelle war seit dem 2026-08-30 in allen
sechs Fassungen falsch – `recommendations-live-check` läuft seither rot:
**#914**, **#918**, **#939** und **#949** fehlten, **#692** stand noch als
offen (geschlossen am 2026-09-01 über PR #947). Der Tagesaudit vom 2026-08-31
führte #918 zudem als geschlossen; es war am selben Tag nach der
Abschlussprüfung wieder geöffnet worden und wartet nur noch auf den nächsten
echten Release-Lauf. Diese Runde korrigiert beides. Neu bewertet: #949
(Test-Suite-Audit, vier umsetzbare Teständerungen, kein Produktionsfehler),
#939 (dauerhafter Heartbeat-Alarmkanal, nicht schließen) und die Epic-Klammer
#914. Kein neuer 🔴-Befund.

**Release-Einschätzung: kein neues Release fällig.** Seit `v2.9.0` (2026-08-29)
liegen 25 Mainline-Commits vor – ausschließlich Release-Automatisierung, Doku
und Governance; `[Unreleased]` ist leer, und im Paket `bgremover/` änderte sich
nur der Nachweis-Hook `update_check_probe.py` (#917). Ein Kandidatenbau hätte
für Nutzer:innen keinen sichtbaren Inhalt. Vorgesehener Scope für ein späteres
**v2.10.0**: die COLOR-Tonwert-Engine (#693/#694 aus Epic #682) auf Basis des
jetzt verabschiedeten ADR #692, gegebenenfalls plus #949.

**EufyMake #681/#687–#691:** Fixtures, Protokollvorlagen und die freigegebene Testgovernance sind in den Issues abgebildet; der offene PR #948 hebt den Satz auf 33 Fixtures, ergänzt Alpha-/Coverage-Zelle, ein dimensionsgleiches COLOR/HEIGHT-Paar und einen Pre-Import-Inspector und belegt zwei Studio-Importe (4.2.2) ohne Druck. #687 steht bei 16/18 Kriterien; offen bleiben I-06 (Ordner/Manifest) und die Abschluss-Review nach den Realtests. Herstellerquelle und Testhypothese für den separaten Spot-UV-Pfad lauten Schwarz = Gloss, Weiß = kein Gloss; volle 16-Bit-Nutzung, `pHYs`-Priorität, Graustufe→mm und Gloss-Intensität bleiben echte Hardwarefragen aus #688–#690.

Unverändert abgeschlossen: **N1/N2/N4/N5/N6/N7/N8**, **O1–O8**, alles seit **2026-06-25** Erledigte, die Releases v2.7.0–v2.9.0 sowie Epic #741 mit seinen elf Teil-Issues, Epic #805 mit #806–#811, #817 und #821; seit dem letzten Sync neu geschlossen: #943 (PR #944) und #692 (PR #947) (Details: Vorige Runden).

Offener Bestand: eine Zeile je Issue in der Triage-Tabelle unten. Weder Zahl noch Zeilen werden seit #821 von Hand gepflegt – `scripts/recommendations_live_check.py --write` schreibt die Tabellen aller sechs Fassungen aus dem GitHub-Live-Stand fort, die Bewertungsspalten bleiben Handarbeit.

## Offene GitHub-Issues – Triage-Stand

| # | Titel | Relevanz | Komplexität | Empfohlenes Modell (Aufwand) | Nächster Schritt |
|---|-------|----------|--------------|-------------------------------|-------------------|
| [#681](https://github.com/NikolayDA/picture_helper/issues/681) | [Epic] EufyMake-Zielprofil – Height/Gloss/mm-DPI validieren | 🟠 Hoch (Korrektheit des wichtigsten Exportziels) | 🔴 Hoch (5 Teil-Issues, physische Hardware nötig) | – (Epic) | #687-Vorbereitung bei 16/18 AC; I-06 und Abschluss-Review bleiben offen, die Profilintegration #691 wartet auf die Realtests #688–#690 |
| [#687](https://github.com/NikolayDA/picture_helper/issues/687) | Annahmeninventar, Herstellerquellen, Testmatrix | 🟠 Hoch (verbindliche Grundlage für #688–#691) | 🔴 Hoch (eigene Deliverables fertig; Fixture-/Zellenlücken aus #688–#690 offen, Rest braucht reale Hardware) | – (kein Agent; reale EufyMake-Hardware nötig) | Blocked (extern) – 16/18 Akzeptanzkriterien erledigt; offen sind I-06 für Ordner/Manifest und die Abschluss-Review nach den Realtests aus #688–#690 |
| [#688](https://github.com/NikolayDA/picture_helper/issues/688) | HEIGHT-Bittiefe/-Semantik auf realer Hardware validieren | 🟠 Hoch (Reliefhöhe direkt betroffen) | 🔴 Hoch (physischer Drucker, Fixtures, Messprotokoll) | – (kein Agent; reale EufyMake-Hardware nötig) | In Review + Blocked (extern) – PR #948 schließt die Vorarbeit (33 Fixtures inkl. Alpha/Coverage, dimensionsgleiches COLOR/HEIGHT-Paar, Pre-Import-Inspector) und belegt zwei Studio-Importe; offen bleiben die physischen Druck-, Relief- und mm-Messungen |
| [#689](https://github.com/NikolayDA/picture_helper/issues/689) | mm/DPI, Zielgröße, Positionierungsvertrag validieren | 🟠 Hoch (Druckgröße/Registrierung) | 🔴 Hoch (physische Messungen, Kontrollmotive) | – (kein Agent; reale Hardware nötig) | Blocked (extern) + Vorarbeit offen – Startgröße im Studio-Importdialog aus `pHYs`/DPI unbelegt (N10, EM-F04); zusätzlich referenziert Zelle I-06 das Fixture- statt eines echten Export-Manifests, und nicht quadratische DPI sind weder getestet noch begründet ausgeschlossen |
| [#690](https://github.com/NikolayDA/picture_helper/issues/690) | Gloss-/Klarlack-Semantik validieren | 🟡 Mittel (Gloss ist laut Code bereits „experimental“) | 🔴 Hoch (physische Drucke, Materialverbrauch) | – (kein Agent; reale Hardware nötig) | Blocked (extern) + Vorarbeit offen – Vorarbeit aus #687 nur teilweise: genau eine Gloss-Zelle (I-10), keine Alpha-/Coverage-Fixtures, keine abweichende Gloss-Dimension, Gloss × HEIGHT ungekreuzt |
| [#691](https://github.com/NikolayDA/picture_helper/issues/691) | Versioniertes Zielprofil in Validator/Writer/Dialog/Doku | 🟠 Hoch (härtet den produktiven Exportpfad) | 🟠 Hoch (Cross-Cutting über eufymake_export/_validate/_writer + UI) | Opus, hoch | Blocked – wartet auf #688–#690 |
| [#682](https://github.com/NikolayDA/picture_helper/issues/682) | [Epic] COLOR-Tonwert-/Graustufen-Engine | 🟡 Mittel-Hoch (Roadmap-Fundament für Laser, kein akuter Bug) | 🔴 Hoch (4 verbleibende Teil-Issues: Kern→UI→Integration→Abnahme) | – (Epic) | In Bearbeitung – ADR #692 ist verabschiedet; als Nächstes den Kern #693 |
| [#693](https://github.com/NikolayDA/picture_helper/issues/693) | Qt-freier Kern: Histogramm/Graustufe/Levels/Gamma | 🟡 Mittel-Hoch | 🟡 Mittel (Erweiterung von `color_ops.py`, gut isoliert testbar) | Sonnet, hoch | Startbereit – ADR #692 (PR #947) liefert den Datenvertrag; Kern gegen dessen Formeln implementieren und testen |
| [#694](https://github.com/NikolayDA/picture_helper/issues/694) | Live-Vorschau + Bedienoberfläche Histogramm/Levels/Gamma | 🟡 Mittel | 🟡 Mittel-Hoch (Qt-UI, Debounce/Generation-Schutz analog Höhen-Vorschau) | Sonnet, hoch | Blocked – wartet auf Kern #693 |
| [#695](https://github.com/NikolayDA/picture_helper/issues/695) | Ebenen-/Auswahl-/History-/Projektintegration | 🟡 Mittel | 🟠 Hoch (viele Zustandsübergänge: Undo/Redo, Auswahl, Dirty-State) | Opus, hoch | Blocked – wartet auf #693/#694 |
| [#696](https://github.com/NikolayDA/picture_helper/issues/696) | Performance-/E2E-/Doku-/Laser-Schnittstellenabnahme | 🟡 Mittel (Abschluss-Gate, kein neues Feature) | 🟠 Hoch (Benchmark-Suite, E2E, Doku, Adapter-Contract) | Opus, hoch | Blocked – Abschluss-Issue nach #695 |
| [#882](https://github.com/NikolayDA/picture_helper/issues/882) | [Epic] BgRemover im Mac App Store | 🟡 Mittel-Hoch (neuer Distributionskanal, kein aktueller Produktfehler) | 🔴 Hoch (Lizenz, Sandbox, Paketierung, Store und Release-Governance) | – (Epic) | Blocked – zuerst die Lizenzstrategie als konkrete Phase-0-Teilaufgabe anlegen und entscheiden |
| [#883](https://github.com/NikolayDA/picture_helper/issues/883) | [MAS] Lizenzstrategie: PySide6 vs. Riverbank und Relizenzierung | 🟠 Hoch (harter Blocker für jede technische MAS-Arbeit) | 🔴 Hoch (Lizenz-/Owner-Entscheid, möglicher Qt-Port, Restrisiko) | Opus, hoch + Owner/Rechtsprüfung | Startbereit – ADR und Owner-Entscheid erstellen; bei PySide6 anschließend eigenes Port-Issue anlegen |
| [#884](https://github.com/NikolayDA/picture_helper/issues/884) | [MAS] Apple Developer Program Enrollment | 🟠 Hoch (blockiert Zertifikate und Store-Zugang) | 🟢 Niedrig (manueller Konto-/Zahlungsschritt) | – (kein Agent; Account Holder) | Blocked (extern) – Kontotyp entscheiden, Enrollment/2FA abschließen und Renewal-Verantwortung festhalten |
| [#885](https://github.com/NikolayDA/picture_helper/issues/885) | [MAS] Signing-Identitäten, App-ID und Provisioning-Profil | 🟠 Hoch (Voraussetzung für signierten Store-Build) | 🟡 Mittel (Owner-Secrets plus Bundle-ID-/Packaging-Vertrag) | – (kein Agent; Account Holder/Admin) | Blocked – wartet auf #884; danach Zertifikate, explizite App-ID und Profil erzeugen sowie Bundle-ID fixieren |
| [#886](https://github.com/NikolayDA/picture_helper/issues/886) | [MAS] App-Sandbox-Entitlements definieren und anwenden | 🟠 Hoch (zwingende Store- und Laufzeitvoraussetzung) | 🟠 Hoch (alle Mach-O-Dateien, Packaging- und Hardware-Nachweis) | Opus, hoch | Blocked – wartet auf Lizenzentscheid #883; danach minimale Entitlements plus Artefakt-/Hardwaretests umsetzen |
| [#887](https://github.com/NikolayDA/picture_helper/issues/887) | [MAS] Sandbox-tauglicher Inferenz-Kindprozess | 🟠 Hoch (KI-Kernfunktion muss im Store-Build laufen) | 🔴 Hoch (Spawn/Helper-Signierung, Zwei-Key-Regel, echte Sandbox) | Opus, hoch | Blocked – wartet auf #886; Re-Exec/Helper entscheiden und KI-Selfcheck auf Hardware belegen |
| [#888](https://github.com/NikolayDA/picture_helper/issues/888) | [MAS] Security-scoped Bookmarks für Dateien und Verzeichnisse | 🟠 Hoch (Recent Files und Quick-Save brechen sonst nach Neustart) | 🟠 Hoch (persistente Grants, Bilder/Projekte/Verzeichnisse, Kanal-Gating) | Opus, hoch | Blocked – wartet auf #886; Bookmark-Vertrag implementieren und Neustartfall sandboxed prüfen |
| [#889](https://github.com/NikolayDA/picture_helper/issues/889) | [MAS] Sandbox-sichere Schreibpfade und EufyMake-Export | 🟠 Hoch (Speicher- und Exportpfade, potenziell Datenintegrität) | 🔴 Hoch (Atomarität über mehrere Pfade und Powerbox-Grants) | Opus, hoch | Blocked – wartet auf #886; grant-konforme Atomarität/Endungen/Zielwahl entwerfen und auf Hardware prüfen |
| [#890](https://github.com/NikolayDA/picture_helper/issues/890) | [MAS] KI-Modell-Cache im Sandbox-Container | 🟡 Mittel (deterministischer Modellpfad im Store-Kanal) | 🟡 Mittel (isolierter Pfadvertrag plus Migrationsentscheid) | Sonnet, hoch | Blocked – wartet auf #886 und verzahnt mit #893; `U2NET_HOME` explizit setzen und Migration entscheiden |
| [#891](https://github.com/NikolayDA/picture_helper/issues/891) | [MAS] Distributionskanal-Flag und Update-Check-Gating | 🟠 Hoch (App-Store-Regel 2.4.5, keine Eigenupdates) | 🟠 Mittel-Hoch (zentrales Flag über Menü, Settings, Worker und Hooks) | Sonnet, hoch | Blocked – wartet auf #883; danach Kanalvertrag einführen und MAS-Netz-/UI-Pfade negativ testen |
| [#892](https://github.com/NikolayDA/picture_helper/issues/892) | [MAS] AiInstallDialog entfernen und KI-Backend bündeln | 🟠 Hoch (kein Nachinstallieren ausführbaren Codes im Store) | 🟡 Mittel (Kanal-Gating plus verbindlicher Packaging-Test) | Sonnet, hoch | Blocked – wartet auf #891; Dialog/Menü gaten und gebündeltes rembg/onnxruntime nachweisen |
| [#893](https://github.com/NikolayDA/picture_helper/issues/893) | [MAS] u2net-Modell bündeln oder beim Erststart laden | 🟠 Hoch (Review-Risiko und Funktionsfähigkeit der KI) | 🟠 Hoch (Produkt-/Review-Entscheid, Packaging oder neuer i18n-Flow) | Opus, hoch | Blocked – wartet auf #890/#891 und Lizenzentscheid #883; Variante dokumentieren, umsetzen und sandboxed verifizieren |
| [#894](https://github.com/NikolayDA/picture_helper/issues/894) | [MAS] Paketierungsweg Briefcase vs. py2app entscheiden | 🟠 Hoch (bestimmt die technische Machbarkeit des Kanals) | 🟠 Hoch (ergebnisoffener signierter Sandbox-/Upload-Spike) | Opus, hoch | Blocked – wartet auf #883; Briefcase-Spike durchführen, py2app als Fallback prüfen und ADR festhalten |
| [#895](https://github.com/NikolayDA/picture_helper/issues/895) | [MAS] onedir-App, Inside-out-Signierung und Qt-Store-Bereinigung | 🟠 Hoch (zentraler ausführbarer Store-Build) | 🔴 Hoch (alle Binaries, Qt, Provisioning, Upload-Validierung) | Opus, hoch | Blocked – wartet auf #885/#886/#894; gewählten Build-Zweig umsetzen und ohne ITMS-Fehler validieren |
| [#896](https://github.com/NikolayDA/picture_helper/issues/896) | [MAS] Info.plist und vollständiger Icon-Satz | 🟡 Mittel-Hoch (Store-Metadaten und Plattformvertrag) | 🟡 Mittel (Pflichtfelder, Architekturziel, deterministische Assets) | Sonnet, hoch | Blocked – wartet auf #895; Minimum-OS/Architektur und Dokumenttypen entscheiden, Plist/Icon-Tests ergänzen |
| [#897](https://github.com/NikolayDA/picture_helper/issues/897) | [MAS] signiertes productbuild-PKG und Transporter-Upload | 🟠 Hoch (einreichbares Store-Artefakt) | 🟠 Hoch (zweite Signatur, Build-Automation, manueller Erst-Upload) | Opus, hoch + Account Holder | Blocked – wartet auf #885/#895/#896; PKG reproduzierbar bauen und Delivery-Log belegen |
| [#898](https://github.com/NikolayDA/picture_helper/issues/898) | [MAS] Release-CI, Sechs-Artefakte-Vertrag und PKG-Scan | 🟠 Hoch (fail-closed Release-Integrität) | 🔴 Hoch (CI-Secrets, Vertrag, Entpacker, Malware-/Pfadscan) | Opus, hoch | Blocked – wartet auf #895/#897; MAS-Leg, Vertrag, Payload-Scan und Regressionstests gemeinsam erweitern |
| [#899](https://github.com/NikolayDA/picture_helper/issues/899) | [MAS] sandboxed Abnahme-Smokes auf echter Hardware | 🟠 Hoch (verbindliche Laufzeitevidenz für Kernpfade) | 🔴 Hoch (PKG, KI-Spawn, Powerbox, 3D und Evidenzschema) | Opus, hoch + macOS-Hardware | Blocked (extern) – wartet auf #898; Abnahmepfad implementieren und auf self-hosted ARM64 ausführen |
| [#900](https://github.com/NikolayDA/picture_helper/issues/900) | [MAS] TestFlight-Beta für macOS | 🟠 Hoch (frühe Review-/Fremdgeräte-Evidenz) | 🟡 Mittel (manuelle ASC-/Tester-Koordination) | – (kein Agent; Account Holder und Tester) | Blocked (extern) – wartet auf #897/#901; internen Build auf Fremdgerät mit KI, Dateien und 3D prüfen |
| [#901](https://github.com/NikolayDA/picture_helper/issues/901) | [MAS] App-Store-Connect-Record und Metadaten in sechs Sprachen | 🟠 Hoch (Name, Listing und Einreichungsvoraussetzung) | 🟠 Mittel-Hoch (Owner-Schritte plus sechs lokalisierte Metadatensätze) | Sonnet, hoch + Account Holder | Blocked – wartet auf #884/#885; Namen reservieren, Texte versionieren/einpflegen und Rating/Storefronts setzen |
| [#902](https://github.com/NikolayDA/picture_helper/issues/902) | [MAS] Store-Screenshot-Satz im 16:10-Format | 🟡 Mittel-Hoch (Pflichtmaterial für das Listing) | 🟡 Mittel (reproduzierbare Formate, Alpha-Check, Sprachentscheidung) | Sonnet, hoch | Blocked – wartet auf repräsentativen Build #895; Automation auf Store-Auflösungen erweitern und Satz prüfen |
| [#903](https://github.com/NikolayDA/picture_helper/issues/903) | [MAS] Privacy Policy und App-Privacy-Angaben | 🟠 Hoch (zwingende Store-/In-App-Pflicht) | 🟡 Mittel (Policy, Hosting, i18n-Link, Owner-Fragebogen) | Sonnet, hoch + Owner | Blocked – wartet auf Kanal-/Modellentscheid #891/#893; Policy hosten, in App/ASC verlinken und „Data Not Collected" belegen |
| [#904](https://github.com/NikolayDA/picture_helper/issues/904) | [MAS] EU-DSA-Status, Impressum und GPSR prüfen | 🟠 Hoch (EU-Storefronts und öffentliche Rechtspflichten) | 🟠 Mittel-Hoch (Owner-Selbsteinschätzung, Verifikation, Rechtsrisiko) | – (kein Agent; Owner/Rechtsprüfung) | Blocked (extern) – wartet auf #884; Trader-Status deklarieren und DDG/GPSR mit Owner/Wiedervorlage dokumentieren |
| [#905](https://github.com/NikolayDA/picture_helper/issues/905) | [MAS] Release-Governance um den Store-Kanal erweitern | 🟠 Hoch (verhindert einen Kanal neben dem fail-closed Vertrag) | 🟠 Hoch (Runbook, Checkliste, Vertrag, Path-Policy, sechs CHANGELOGs) | Opus, hoch | Blocked – begleitet #898/#899; vor Einreichung alle Governance-Verträge und Tests auf sechs Artefakte heben |
| [#906](https://github.com/NikolayDA/picture_helper/issues/906) | [MAS] Ersteinreichung und Review-Runde | 🟠 Hoch (manuelles Veröffentlichungs-Gate) | 🔴 Hoch (viele Abhängigkeiten, Restrisiken, Apple-Kommunikation) | – (kein Agent; Release-Owner) | Blocked (extern) – nach #896/#897/#899/#901–#905 Pre-Submission prüfen, einreichen und Ergebnis/Folge-Issues protokollieren |
| [#907](https://github.com/NikolayDA/picture_helper/issues/907) | [MAS] Betriebskonzept für Renewal, Updates und Kanäle | 🟡 Mittel-Hoch (langfristige Verfügbarkeit und Kanaltrennung) | 🟡 Mittel (Runbook, Verantwortungen, Erinnerungen, Kanalmatrix) | Opus, hoch + Owner | Blocked – Konzept vorab möglich, final nach #906; Renewal-/Update-/Webseiten-Routinen verbindlich verankern |
| [#914](https://github.com/NikolayDA/picture_helper/issues/914) | [Epic] Release-Prozess: Runner, automatisierte Nachweise, main-Freeze | 🟠 Hoch (Release-Betrieb; 8 von 9 Arbeitspaketen erledigt) | 🟡 Mittel (nur noch der #918-Rest) | – (Epic) | Fast fertig – offen ist allein das Erfolgskriterium „`main` bleibt mergebar", das der nächste echte Release-Lauf über #918 belegt |
| [#918](https://github.com/NikolayDA/picture_helper/issues/918) | Release-Ref statt main-Freeze (ADR + fail-closed Absicherung) | 🟠 Hoch (`main` bleibt während eines Releases mergebar) | 🟢 Niedrig (Code, Doku und Ruleset stehen) | – (kein Agent; nächster Release-Lauf) | Blocked (extern) – am 2026-08-31 nach der Abschlussprüfung wiedereröffnet; PR #936 und der aktive Ruleset 21941216 sind belegt, offen ist nur ein Lauf, dessen Post-Release-Abnahme nachweislich auf `release/vX.Y.Z` startete |
| [#939](https://github.com/NikolayDA/picture_helper/issues/939) | Betrieb: Self-hosted-Runner (Heartbeat-Alarmkanal) | 🟡 Mittel (Betriebskanal, kein Produktcode) | 🟢 Niedrig (reine Beobachtung) | – (kein Agent; Repo-Owner) | Dauerhaft offen – nicht schließen (`RUNNER_HEARTBEAT_ISSUE`); der FAIL vom 2026-08-31 war der geplante Meldeweg-Test, der Aufräumschritt ist erledigt (planmäßiger Lauf 33496675995 grün, x86_64 übersprungen, Mac und Pi bestanden) |
| [#949](https://github.com/NikolayDA/picture_helper/issues/949) | Test-Suite-Audit 2026-09-02 (RESOURCES-Drift, CropOverlay, Coverage-Lücken) | 🟡 Mittel (Testqualität und Drift-Schutz, kein Produktionsfehler) | 🟢 Niedrig-Mittel (vier klar umrissene Teständerungen, keine Produktionsänderung) | Sonnet, mittel | Startbereit – `RESOURCES.md`-Sollwerte aus den echten `uses:`-Zeilen ableiten, `test_crop_overlay.py` auf `set_position()`/`crop_rect()` umstellen, `crop_image()`-Rechteckzweig und den Nicht-RGBA-Zweig von `adjust_color()` abdecken |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | OpenAI-Quota für manuellen Codex-Scan wiederherstellen | 🟢 Niedrig (blockiert nur einen optionalen manuellen Scan) | 🟢 Niedrig (rein operativ, kein Code) | – (kein Agent; Repo-Owner: Billing) | Blocked (extern) – letzter Lauf (29233060507, 2026-07-13) belegt keinen erfolgreichen Scan; Billing/Quota weiterhin offen |

### Als Nächstes empfohlen

1. **#693** (Qt-freier Kern) – der ADR #692 ist verabschiedet, damit ist der COLOR-Epic #682
   startbereit; danach folgen #694, #695 und #696 in dieser Reihenfolge.
2. **#949** – vier kleine, klar umrissene Teständerungen ohne Produktionsrisiko; guter
   Parallel-PR neben dem Epic.
3. **#948** reviewen und mergen; danach vor der nächsten Studio-/Druckersession die restlichen
   Lücken aus #689/#690 schließen (Gloss-Zellen, echtes Export-Manifest für I-06) und
   #687 (Rest), #688, #689, #690 gebündelt ausführen.
4. **#883** (MAS-Lizenzstrategie) entscheidet über den Mac-App-Store-Pfad #882 –
   ohne diesen Owner-Entscheid bleibt die gesamte Kette #884–#907 blockiert.

## Vorige Runden

Ausführliche Protokolle seit v2.2: [docs/history/RECOMMENDATIONS-2026-v2.2-v2.9.md](docs/history/RECOMMENDATIONS-2026-v2.2-v2.9.md).

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
