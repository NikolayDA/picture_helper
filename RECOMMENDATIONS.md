**Deutsch** · [English](docs/i18n/en/RECOMMENDATIONS.md) · [Español](docs/i18n/es/RECOMMENDATIONS.md) · [Français](docs/i18n/fr/RECOMMENDATIONS.md) · [Українська](docs/i18n/uk/RECOMMENDATIONS.md) · [简体中文](docs/i18n/zh/RECOMMENDATIONS.md)

# Codeanalyse & bewertete Empfehlungen: BgRemover

## Bewertungsskala

| Symbol | Priorität | Bedeutung |
|--------|-----------|-----------|
| 🔴 | Kritisch | Fehler, Abstürze oder Datenverlust |
| 🟠 | Hoch | Spürbarer Einfluss auf Zuverlässigkeit oder Wartbarkeit |
| 🟡 | Mittel | Sinnvolle Verbesserung für Qualität, Lesbarkeit oder Testbarkeit |
| 🟢 | Niedrig | Optionales Polishing oder Prozessverbesserung |

## Aktueller Stand (2026-08-31, v2.9.0 veröffentlicht, offener Bestand vollständig geprüft)

**Tagesaudit 2026-08-31 (Stand `551d055`):** Geprüft wurden die zwölf heute
gemergten PRs #927–#932, #935–#938, #940 und #941 sowie die dadurch
geschlossenen Issues #918–#923, #933 und #934. Die Prüfung umfasste die
vollständigen Merge-Diffs, die im Merge enthaltenen Review-Nachbesserungen und
deren Regressionstests. Release-Ref und Wiederanlaufpfade, Security-Bericht,
Runner-Heartbeat/Dry-Run, Vorbereitungsgerüst sowie der echte Qt-/GL-Preflight
einschließlich Provenienzausgabe sind konsistent umgesetzt. Es blieb kein
konkreter, reproduzierbarer Restbefund; daher war kein Folge-Issue anzulegen.
Der offene Bestand und die drei Empfehlungen unten bleiben unverändert.

**Turnusprüfung 2026-08-30 (Delta nach Vollaudit):** Die 39 bereits am
2026-08-29 gegen `main` (Produktstand `411d47c`) vollständig und adversariell
geprüften offenen Issues sind unverändert; HEAD `1d31f2a` ergänzt danach nur
Dokumentation. Die nachgezogenen Beschreibungen #681/#882/#905/#906 und die
Fixture-/Zelllücken der EufyMake-Realtests #688–#690 bleiben korrekt sichtbar.
Neu hinzugekommenes #912 wurde separat gegen das Qt-Advisory und das gepinnte
Artefakt geprüft: CVSS 4.0 ist 6,3 statt 6,8, und das verwundbare
`QtCore5Compat` wird nicht ausgeliefert. #912 ist korrigiert und als „nicht
betroffen“ geschlossen; kein falscher Accepted-Risk-Eintrag, kein neuer 🔴-Befund.

**Nachtrag 2026-08-29:** v2.9.0 ist veröffentlicht. Die Hardware-Abnahme lief
auf macOS arm64 und Linux arm64 mit echten GPU-Renderern grün, Tag und
Veröffentlichung sind byteidentisch gegen das Freigabemanifest geprüft,
`PUBLIC-DOWNLOAD-01` und `UPDATE-01` sind erbracht. #881 ist damit geschlossen;
die bewusst pausierten Linux-x86_64-Kriterien bleiben sichtbar `PENDING`.
#878 ist mit PR #908 umgesetzt; diese Abschluss-Synchronisierung schließt das
Issue und entfernt es aus allen sechs aktuellen Triage-Tabellen.

**Turnusprüfung 2026-08-28:** Der GitHub-Live-Abgleich ergänzt die bislang
fehlenden offenen Issues **#878**, **#881**, **#882** sowie die inzwischen
angelegten MAS-Teil-Issues **#883–#907**. Beim damaligen Stand sollte #878 die
Lücke zwischen Standard-/Experten-Oberfläche und Nutzerhandbuch einschließlich
aktueller Screenshots und PDF schließen; die Umsetzung ist inzwischen über
PR #908 abgeschlossen. #881 ist das verbindliche Abnahme- und
Veröffentlichungsprotokoll für 2.9.0; Kandidatenbau und Vorprüfung sind grün,
die Hardware-Abnahme und menschlichen Freigaben stehen aus. #882 bündelt den
Mac-App-Store-Pfad als blockiertes Epic; #883–#907 konkretisieren dessen
Lizenz-, Konto-, Sandbox-, Paketierungs-, Store- und Betriebsphasen. Vor technischer Umsetzung muss
zuerst die Lizenzstrategie entschieden werden. Kein neuer 🔴-Befund.

**EufyMake #681/#687–#691:** Die vorhandenen 31 Fixtures, Protokollvorlagen und die freigegebene Testgovernance sind jetzt in den Issues abgebildet. #687 steht bei 16/18 Kriterien; offen bleiben I-06 (Ordner/Manifest) und die Abschluss-Review nach den Realtests. Herstellerquelle und Testhypothese für den separaten Spot-UV-Pfad lauten Schwarz = Gloss, Weiß = kein Gloss; volle 16-Bit-Nutzung, `pHYs`-Priorität, Graustufe→mm und Gloss-Intensität bleiben echte Hardwarefragen aus #688–#690.

Unverändert abgeschlossen: **N1/N2/N4/N5/N6/N7/N8**, **O1–O8**, alles seit **2026-06-25** Erledigte, die Releases v2.7.0–v2.8.0 sowie Epic #741 mit seinen elf Teil-Issues, Epic #805 mit #806–#811, #817 und #821; seit dem letzten Sync neu geschlossen: #836 (PR #844), #837 (PR #838), #839 (PR #846), #849 (PR #851), #841 (vom Owner geschlossen), #847 (PR #852), #866 (PR #870/#871), #869 (PR #873), #881 (vom Owner geschlossen) und #878 (PR #908/#910) (Details: Vorige Runden).

Offener Bestand: eine Zeile je Issue in der Triage-Tabelle unten. Weder Zahl noch Zeilen werden seit #821 von Hand gepflegt – `scripts/recommendations_live_check.py --write` schreibt die Tabellen aller sechs Fassungen aus dem GitHub-Live-Stand fort, die Bewertungsspalten bleiben Handarbeit.

## Offene GitHub-Issues – Triage-Stand

| # | Titel | Relevanz | Komplexität | Empfohlenes Modell (Aufwand) | Nächster Schritt |
|---|-------|----------|--------------|-------------------------------|-------------------|
| [#681](https://github.com/NikolayDA/picture_helper/issues/681) | [Epic] EufyMake-Zielprofil – Height/Gloss/mm-DPI validieren | 🟠 Hoch (Korrektheit des wichtigsten Exportziels) | 🔴 Hoch (5 Teil-Issues, physische Hardware nötig) | – (Epic) | #687-Vorbereitung bei 16/18 AC; I-06 und Abschluss-Review bleiben offen, die Profilintegration #691 wartet auf die Realtests #688–#690 |
| [#687](https://github.com/NikolayDA/picture_helper/issues/687) | Annahmeninventar, Herstellerquellen, Testmatrix | 🟠 Hoch (verbindliche Grundlage für #688–#691) | 🔴 Hoch (eigene Deliverables fertig; Fixture-/Zellenlücken aus #688–#690 offen, Rest braucht reale Hardware) | – (kein Agent; reale EufyMake-Hardware nötig) | Blocked (extern) – 16/18 Akzeptanzkriterien erledigt; offen sind I-06 für Ordner/Manifest und die Abschluss-Review nach den Realtests aus #688–#690 |
| [#688](https://github.com/NikolayDA/picture_helper/issues/688) | HEIGHT-Bittiefe/-Semantik auf realer Hardware validieren | 🟠 Hoch (Reliefhöhe direkt betroffen) | 🔴 Hoch (physischer Drucker, Fixtures, Messprotokoll) | – (kein Agent; reale EufyMake-Hardware nötig) | Blocked (extern) + Vorarbeit offen – Fixtures/Protokollvorlagen aus #687 liegen vor, aber Alpha/Coverage hat weder Fixture noch Testzelle (alle COLOR-Fixtures opak) und es fehlt ein COLOR/HEIGHT-Paar mit gleichem Pixelmaß (I-02/I-08 konfundiert); vor dem Testtag ergänzen |
| [#689](https://github.com/NikolayDA/picture_helper/issues/689) | mm/DPI, Zielgröße, Positionierungsvertrag validieren | 🟠 Hoch (Druckgröße/Registrierung) | 🔴 Hoch (physische Messungen, Kontrollmotive) | – (kein Agent; reale Hardware nötig) | Blocked (extern) + Vorarbeit offen – Startgröße im Studio-Importdialog aus `pHYs`/DPI unbelegt (N10, EM-F04); zusätzlich referenziert Zelle I-06 das Fixture- statt eines echten Export-Manifests, und nicht quadratische DPI sind weder getestet noch begründet ausgeschlossen |
| [#690](https://github.com/NikolayDA/picture_helper/issues/690) | Gloss-/Klarlack-Semantik validieren | 🟡 Mittel (Gloss ist laut Code bereits „experimental“) | 🔴 Hoch (physische Drucke, Materialverbrauch) | – (kein Agent; reale Hardware nötig) | Blocked (extern) + Vorarbeit offen – Vorarbeit aus #687 nur teilweise: genau eine Gloss-Zelle (I-10), keine Alpha-/Coverage-Fixtures, keine abweichende Gloss-Dimension, Gloss × HEIGHT ungekreuzt |
| [#691](https://github.com/NikolayDA/picture_helper/issues/691) | Versioniertes Zielprofil in Validator/Writer/Dialog/Doku | 🟠 Hoch (härtet den produktiven Exportpfad) | 🟠 Hoch (Cross-Cutting über eufymake_export/_validate/_writer + UI) | Opus, hoch | Blocked – wartet auf #688–#690 |
| [#682](https://github.com/NikolayDA/picture_helper/issues/682) | [Epic] COLOR-Tonwert-/Graustufen-Engine | 🟡 Mittel-Hoch (Roadmap-Fundament für Laser, kein akuter Bug) | 🔴 Hoch (5 Teil-Issues, ADR→Kern→UI→Integration→Abnahme) | – (Epic) | In Bearbeitung – #692 zuerst anstoßen |
| [#692](https://github.com/NikolayDA/picture_helper/issues/692) | ADR + Datenvertrag Tonwert/Histogramm/Graustufe | 🟠 Hoch (legt Vertrag für den gesamten Epic fest) | 🟡 Mittel (Architekturentscheid, keine Implementierung) | Opus, hoch | Startbereit |
| [#693](https://github.com/NikolayDA/picture_helper/issues/693) | Qt-freier Kern: Histogramm/Graustufe/Levels/Gamma | 🟡 Mittel-Hoch | 🟡 Mittel (Erweiterung von `color_ops.py`, gut isoliert testbar) | Sonnet, hoch | Blocked – wartet auf ADR #692 |
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
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | OpenAI-Quota für manuellen Codex-Scan wiederherstellen | 🟢 Niedrig (blockiert nur einen optionalen manuellen Scan) | 🟢 Niedrig (rein operativ, kein Code) | – (kein Agent; Repo-Owner: Billing) | Blocked (extern) – letzter Lauf (29233060507, 2026-07-13) belegt keinen erfolgreichen Scan; Billing/Quota weiterhin offen |

### Als Nächstes empfohlen

1. **#692** (ADR) öffnet den COLOR-Epic #682.
2. Vor der nächsten Studio-/Druckersession zuerst die in #688–#690 dokumentierten Lücken im
   Fixture-/Zellensatz schließen (Alpha/Coverage, COLOR/HEIGHT-Paar gleicher Größe, Gloss-Zellen,
   echtes Export-Manifest für I-06); danach #687 (Rest), #688, #689 und #690 gebündelt ausführen.
3. **#883** (MAS-Lizenzstrategie) entscheidet über den Mac-App-Store-Pfad #882 –
   ohne diesen Owner-Entscheid bleibt die gesamte Kette #884–#907 blockiert.

## Vorige Runden

Ausführliche Protokolle seit v2.2: [docs/history/RECOMMENDATIONS-2026-v2.2-v2.9.md](docs/history/RECOMMENDATIONS-2026-v2.2-v2.9.md).

Historische Befunde und Arbeitsprotokolle (Runden 1–5): [docs/history/RECOMMENDATIONS-2026-pre-v2.2.md](docs/history/RECOMMENDATIONS-2026-pre-v2.2.md).
