<!--
Danke für deinen Beitrag! Bitte die Checkliste ausfüllen (siehe CONTRIBUTING.md
und CLAUDE.md). Keine Secrets/Tokens/internen Hosts eintragen.
-->

## Kurzbeschreibung

<!-- Was ändert dieser PR und warum? -->

<!--
Nur die englischen Schlüsselwörter schließen ein Issue automatisch:
`Closes #123` / `Fixes #123` / `Resolves #123`. Ein deutsches „Löst #123"
wertet GitHub NICHT aus – bei PR #812 blieben dadurch sieben umgesetzte
Issues (#805–#811) nach dem Merge offen und mussten von Hand nachgezogen
werden (#817-Runde). Schließt der PR kein Issue, die Zeile durch einen
reinen Verweis ersetzen, z. B. „Bezug: #123".
-->

Closes #

## Standard-Gate

- [ ] `make check` (bzw. `make pr-check`) läuft lokal grün.
- [ ] CHANGELOG (`[Unreleased]`) bei nutzersichtbarer Änderung aktualisiert.
- [ ] Bei berührten Docs: i18n-Parität (`docs/i18n/`) gewahrt, keine toten
      Markdown-Links.
- [ ] Falls die Qt-apt-Paketliste geändert wurde: alle sechs Dateien synchron
      (`.github/workflows/ci.yml`, `pr-ci.yml`, `ui-nightly.yml`,
      `benchmark.yml`, `coverage.yml`, `.claude/hooks/session-start.sh` —
      Befund N6).
- [ ] Kommentare/Docstrings auf Deutsch, Code-Identifier englisch.

## Tests

<!-- Welche Tests wurden ergänzt/angepasst? Wie manuell getestet? -->
