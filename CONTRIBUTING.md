# Beitragen zu BgRemover

Danke für dein Interesse! Bugs, Verbesserungsvorschläge und Pull Requests sind willkommen.

## Inhaltsverzeichnis

1. [Verhaltenskodex](#verhaltenskodex)
2. [Fehler melden](#fehler-melden)
3. [Feature-Vorschläge](#feature-vorschläge)
4. [Issue-Triage: Priorität und Blocker](#issue-triage-priorität-und-blocker)
5. [Entwicklungsumgebung einrichten](#entwicklungsumgebung-einrichten)
6. [Code beitragen](#code-beitragen)
7. [Konventionen](#konventionen)
8. [Tests](#tests)
9. [Dokumentation](#dokumentation)
10. [Releases](#releases)

---

## Verhaltenskodex

Konstruktiver, respektvoller Umgang ist Voraussetzung für Beiträge. Beleidigungen, Diskriminierung oder Trolling führen zum Ausschluss.

## Fehler melden

1. Zunächst prüfen, ob das Issue bereits existiert.
2. Unter „New issue" die Vorlage **Fehlerbericht** wählen (deutsches Issue-Formular).
3. Pflichtangaben des Formulars:
   - **BgRemover-Version** — steht im Fenstertitel („BgRemover Pro <Version>").
   - **Plattform** — macOS arm64/x86_64, Linux x86_64, Linux arm64 (Raspberry Pi) oder Sonstige.
   - **Installationsart** — DMG, AppImage, `.deb`, Quellinstallation/venv oder Web-Session.
   - **Schritte zur Reproduktion** — nummeriert, vom Start der Anwendung bis zum Fehler.
   - **Bestätigung**, dass Logauszug, Screenshots und Anhänge keine
     personenbezogenen oder vertraulichen Inhalte enthalten. Sie ist immer
     erforderlich (GitHub Issue Forms kennen keine bedingten Pflichtfelder) und
     bedingt formuliert — ein Bericht ohne Anhang bleibt absendbar.
4. Freiwillig, aber hilfreich: Betriebssystem-Version, **Python-Version bei
   Quellinstallation/venv oder Web-Session**, ob die KI-Hintergrundentfernung
   installiert ist, erwartetes vs. beobachtetes Verhalten, Screenshot und ein
   Logauszug aus `bgremover.log` (Einstellungen → **Protokolldatei** →
   **Ordner öffnen**).

Sicherheitslücken bitte **nicht** als öffentliches Issue melden — siehe [SECURITY.md](SECURITY.md);
das Issue-Formular verlinkt denselben Weg als Kontaktlink.

## Feature-Vorschläge

Unter „New issue" die Vorlage **Funktionswunsch** wählen. Pflichtangaben:
- **Problem oder Anlass** — welche Aufgabe gelingt heute nicht oder nur umständlich?
- **Gewünschtes Verhalten** — wie soll die Funktion bedienbar sein?

Dazu optional der betroffene Workflow-Schritt (Öffnen · Freistellen · Anpassen ·
Form & Maße · Relief & Ebenen · Export · übergreifend), erwogene Alternativen und
zusätzlicher Kontext.

Größere Änderungen an der Architektur vorab im Issue diskutieren, bevor Code geschrieben wird.

Beide Vorlagen liegen als YAML-Issue-Forms unter `.github/ISSUE_TEMPLATE/`;
freie Issues ohne Vorlage bleiben möglich (`config.yml`). Änderungen an den
Formularen prüft `tests/test_issue_forms.py` vor dem Merge — im
Template-Chooser erscheinen sie erst danach.

## Issue-Triage: Priorität und Blocker

GitHub ist die einzige Quelle für den offenen Bestand (#1032/#1033). Jedes
offene Issue trägt seine Triage selbst:

- **Genau ein Prioritäts-Label:** `prio:now` (als Nächstes empfohlen),
  `prio:next` (eingeplant, aber nicht das nächste Paket) oder `prio:later`
  (zurückgestellt oder mehrstufig blockiert). Die Zuordnung ist eine
  Entscheidung des Repository-Owners; wer ein Issue eröffnet, setzt einen
  Vorschlag, der Owner passt ihn bei Bedarf an.
- **Interne Blocker** (ein anderes Issue) ausschließlich als native
  GitHub-Abhängigkeit „blocked by" – kein Label. GitHub aktualisiert die
  Abhängigkeit beim Schließen des Blockers selbst.
- **Externe Blocker** (Hardware, Account, Billing, ein künftiger
  Release-Lauf) als `blocked:extern` plus eine Kommentarzeile
  „Blockiert extern durch: …". Je Blocker genau eine Darstellung.
- Bewusst **kein** `status:ready` und kein Label für Zustände, die GitHub
  selbst kennt: „bereit" ergibt sich aus dem Fehlen offener Abhängigkeiten und
  externer Blocker. Alles, was neben einer GitHub-eigenen Darstellung von Hand
  synchron gehalten werden müsste, wiederholt die Drift-Schleife im Kleinen.
- Epics erhalten ihre Teil-Issues als Sub-Issues; dauerhaft offene
  Betriebs-Issues (etwa der Heartbeat-Alarmkanal) tragen kein Blocker-Label.

Der einmalige Cutover aus der früheren Tabelle in `RECOMMENDATIONS.md` lief
über `scripts/triage_issue_cutover.py` (Entscheidungsakte, idempotentes
`apply`, `verify`); das Skript ist kein Wächter und läuft in keinem Workflow.

## Entwicklungsumgebung einrichten

```bash
git clone https://github.com/NikolayDA/picture_helper.git
cd picture_helper
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[test]"
```

Unter Linux werden Qt-Systembibliotheken benötigt:

```bash
sudo apt-get install -y \
  libgl1 libglib2.0-0 libdbus-1-3 libxkbcommon0 \
  libxcb1 libxcb-cursor0 libxcb-icccm4 libxcb-image0 \
  libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 \
  libxcb-shape0 libxcb-xinerama0 libxcb-xkb1 libxkbcommon-x11-0 \
  libegl1 libxcb-util1
```

Prüfen, ob alles in Ordnung ist:

```bash
make doctor
```

## Code beitragen

1. Repository forken und einen Feature-Branch anlegen:
   ```bash
   git checkout -b feature/kurze-beschreibung
   ```
2. Änderungen vornehmen — die [Konventionen](#konventionen) beachten.
3. Tests schreiben oder anpassen (siehe [Tests](#tests)).
4. Gate lokal bestehen lassen:
   ```bash
   make check
   ```
5. Commit mit aussagekräftiger Nachricht (Englisch oder Deutsch, Imperativ):
   ```
   feat(canvas): Drehen via Tastenkürzel ergänzen
   fix(workers): Race-condition beim Abbruch beheben
   ```
6. Pull Request gegen `main` öffnen und das PR-Template ausfüllen.

Pull Requests, die `make check` nicht bestehen, werden nicht gemergt.

Das automatische Claude-Review läuft genau einmal je PR (beim Öffnen bzw.
beim Verlassen des Draft-Status); eine Wiederholung gibt es nur über das
Label `re-review`. Für Bot-Befunde gilt die **Konvergenzregel**: höchstens
zwei Bot-Review-Runden je PR, danach entscheidet ein Mensch gesammelt, was
umgesetzt wird, und schließt den Rest mit einem Satz Begründung — Bot-Befunde
sind Input der Merge-Entscheidung, keine Merge-Bedingung
([Prozessdiagramme, Abschnitt 3](docs/PROZESSE_UML.md)). Die zwei Runden
zählt, wer den PR mergt (aktuell der Repository-Owner).

Praktisches zum Label `re-review`: Es muss im Repository existieren
(einmaliger Owner-Schritt, siehe Abschnitt *Aktivierung* im
[ADR](docs/history/ADR-2026-reviewschleifen-entschaerfung.md)); erneut
anfordern heißt Label **entfernen und neu setzen** (nur das Setzen
triggert); auf Drafts und reinen Doku-PRs tut das Label bewusst nichts —
dort ist die `@claude`-Erwähnung der Weg zu einem Review.

Als Überblick sind Commit, PR-Erstellung, PR-Durchführung und Release als
UML-Aktivitätsdiagramme gezeichnet: [Prozessdiagramme](docs/PROZESSE_UML.md).
Sie bilden ab, sie bestimmen nicht — verbindlich bleiben diese Datei, das
PR-Template und das Release-Runbook.

## Konventionen

| Bereich | Regel |
|---------|-------|
| **Sprache (Kommentare/Docstrings)** | Deutsch |
| **Sprache (Code-Identifier)** | Englisch |
| **Sprache (Commits, PR-Titel)** | Englisch oder Deutsch |
| **Zeilenlänge** | 100 Zeichen (ruff, `E501` ignoriert) |
| **Linter** | `ruff check` mit Regeln `E,F,W,I,B,UP,SIM` |
| **Formatter** | `ruff format` |
| **Typprüfung** | `mypy` (Qt-arme Module streng, Qt-lastige laxer) |
| **Stil** | Kompakt — keine unnötigen Zwischenzeilen oder Kommentare |

Der bestehende Stil (Dateilänge, Kompaktheit, deutschen Kommentare) soll erhalten bleiben. Keine unnötigen Refactorings außerhalb des eigentlichen Änderungsbereichs.

## Tests

```bash
make test        # CI-Subset (ohne volle UI-Suite)
make coverage    # Coverage-Report (Schwelle: 86 %)
make ui          # Volle qtbot-UI-Suite (nur bei Bedarf / nightly)
```

Für headless-Umgebungen (Server, CI) muss `QT_QPA_PLATFORM=offscreen` gesetzt sein — `make` erledigt das automatisch.

Neue Features brauchen Tests. Bugfixes idealerweise einen Regressionstest. Marker:
- `@pytest.mark.ui` — volle UI-Tests (nightly)
- `@pytest.mark.ui_smoke` — leichtgewichtige UI-Tests (laufen in CI mit)

## Dokumentation

BgRemover ist mehrsprachig (Deutsch, Englisch, Spanisch, Französisch, Ukrainisch, Chinesisch). Änderungen an deutschen Basisdokumenten (`README.md`, `ANLEITUNG.md`, `CHANGELOG.md` usw.) müssen in den entsprechenden `docs/i18n/`-Dateien gespiegelt werden, damit die i18n-Paritätstests grün bleiben.

Markdown-Links werden durch Tests geprüft — keine toten Links einführen.

## Releases

Der verbindliche Ablauf steht ausschließlich im
[Release-Runbook](docs/RELEASE_PROCESS.md); Kriterien und Plattformumfang in
der [versionierten Abnahme-Checkliste](docs/RELEASE_ACCEPTANCE_CHECKLIST.md).
Release-Schritte nicht in weiteren Dokumenten duplizieren.

## Fragen?

Ein Issue öffnen oder auf einen bestehenden PR/Issue antworten. Danke für deinen Beitrag!
