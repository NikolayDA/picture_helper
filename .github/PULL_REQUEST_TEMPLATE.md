<!--
Danke für deinen Beitrag! Bitte die Checkliste ausfüllen (siehe CONTRIBUTING.md
und CLAUDE.md). Keine Secrets/Tokens/internen Hosts eintragen.
-->

## Kurzbeschreibung

<!-- Was ändert dieser PR und warum? -->

Löst #

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
