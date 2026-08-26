# ADR: Verschlankung des Review-Workflows (Prompt, Prosa, Turn-Budget)

**Status:** angenommen · **Datum:** 2026-08-24 · **Bezug:** #828,
[`ADR-2026-reviewschleifen-entschaerfung.md`](ADR-2026-reviewschleifen-entschaerfung.md),
[`ISSUE-841-VERIFIKATION.md`](ISSUE-841-VERIFIKATION.md)

## Kontext

Nach der Reviewschleifen-Entschärfung (E1–E3, PR #857) blieb der zweite
Treiber der Meta-Spirale: `claude-code-review.yml` war auf 828 Zeilen
angewachsen (davon ~540 Zeilen Kommentar-/Begründungsprosa, Prompt ~180 Zeilen
überwiegend Formregeln), und `tests/test_claude_workflow_diagnostics.py`
pinnte mit 54 Tests auf 1931 Zeilen auch reine Formulierungen dieser Prosa.
Jede Umformulierung wurde damit zum Test-Bruch, jede Antwort auf einen
Review-Befund erzeugte neuen Text, der neue Befunde zog (PR #850: eine
Allowlist-Zeile, +2301 Zeilen, ~15 Review-Wellen).
[`ISSUE-841-VERIFIKATION.md`](ISSUE-841-VERIFIKATION.md) hält dazu fest:
„Anweisungen wirken auch über Umfang und Nachdrücklichkeit, und Regeln
optimieren zuverlässig auf die Messgröße."

Die Nummerierung setzt die Empfehlungsserie der Reviewschleifen-Analyse
fort (E1–E3 = Entschärfung, PR #857): **E4** ist die hier beschriebene
Verschlankung von Prompt, Prosa und Tests, **E5** die Kostenbremse
(Turn-Budget, Timeout, Opus nur noch einmal je PR).

## Entscheidung

1. **Prompt auf den Auftrag reduziert.** Fachlicher Auftrag zuerst, dann
   Ausgabewege, Werkzeuggrenze und die Fremdinhalt-Regel – zusammen ~55
   Zeilen. Von den Formregeln bleibt nur, was empirisch belegt oder
   sicherheitstragend ist: einfache Anführungszeichen mit
   `'\''`-Apostroph, keine `#`-Zeilenanfänge im Kommentar-Body (belegt
   abgelehnter Fall, Lauf 32640784005), Längen-Vorsichtsmaß < 10 000
   Zeichen, Verengung von `gh pr comment` auf `--body '…'`.
2. **Begründungsprosa wandert hierher** (Abschnitte unten). Die
   Workflow-Datei trägt je Entscheidung höchstens einen Kurzkommentar mit
   Verweis. Ergebnis: Workflow ~240 statt 828 Zeilen (davon ~65 Zeilen das
   geteilte Diagnose-Skript); das Skript bleibt **code-identisch**, nur
   seine Inline-Kommentare sind auf Kurzform verdichtet.
3. **Testdatei auf Sicherheits-/Verhaltensinvarianten reduziert.**
   `test_claude_workflow_diagnostics.py` prüft nur noch, was Verhalten oder
   Sicherheit trägt (Liste unten); alle Wortlaut-Pins auf Begründungsprosa
   sind gestrichen. Der Trigger-Wächter lebt weiter in
   `tests/test_process_documentation.py`.
4. **Turn-Budget 30 → 25 (kalibriert) und Timeout 30 → 15 Minuten (E5).**
   Mit dem schlanken Prompt entfallen die Turns für Formregel-Navigation;
   echte Reviews liefen median ~5, maximal ~9 Minuten. Die Erstsetzung 20
   wurde an zwei realen Läufen auf PR #858 (~3.300-Zeilen-Diff)
   kalibriert: Job 97538305150 endete mit `error_max_turns` nach
   21 Turns **ohne gepostete Ausgabe** (der teuerste Fall — Antwort:
   Budget-Disziplin im Prompt, Überblick per `--name-only` zuerst,
   Zusammenfassung spätestens nach zwei Dritteln des Budgets); Job
   97540368095 lieferte danach mit Disziplin Zusammenfassung plus vier
   Inline-Befunde, brauchte dafür aber 23 Turns — die Action wertet
   `num_turns > max` auch bei erfolgreichem Ergebnis als roten Lauf.
   Ein disziplinierter Groß-Diff-Lauf braucht real >20, also Deckel 25.
   Rückdrehpfad: Erst wenn ein Lauf **trotz** Disziplin leer endet oder
   eine Serie realer Läufe mit geposteter Ausgabe am Deckel scheitert,
   wird hier weiter erhöht — nicht der Prompt wieder aufgebläht; ein
   Anheben fasst diesen Abschnitt, den geteilten #828-Kopfblock beider
   Workflows und den Test-Pin synchron an.

   **Nachtrag 2026-08-26 — Deckel 25 → 40, Timeout 15 → 20 Minuten.**
   Der oben beschriebene Anhebungsfall ist eingetreten. Die passive
   Zehn-Läufe-Messung aus #828
   ([ISSUE-841-VERIFIKATION.md](ISSUE-841-VERIFIKATION.md)) endete
   6 grün / 4 rot, und **alle vier** roten Läufe scheiterten allein am
   Deckel — drei davon (Läufe 2, 3 und 9 mit 29, 30 und 29 Turns) mit
   bereits vollständig veröffentlichter Zusammenfassung und
   Inline-Befunden. Das ist wörtlich die hier verlangte „Serie realer
   Läufe mit geposteter Ausgabe, die am Deckel scheitert". Der
   Ablehnungszähler stand dabei in allen zehn Läufen auf 0: Das Budget
   geht in Arbeit auf, nicht mehr in eine Ablehnungsschleife — die
   Bedingung „nicht der Prompt wieder aufgebläht" ist damit erfüllt,
   der Prompt bleibt unangetastet. Lauf 10 traf mit exakt 25 Turns die
   Obergrenze und lieferte trotzdem fünf Inline-Befunde; 25 war also
   nicht großzügig, sondern grenzwertig. 40 statt der knapp
   ausreichenden 30 lässt bewusst Luft über dem beobachteten Maximum,
   damit derselbe Fall nicht in drei Monaten wiederkehrt.
   Der **Timeout zieht mit**, weil er sonst an die Stelle des Deckels
   tritt: Bei der langsamsten gemessenen Rate (Lauf 32903367472,
   ~20 s/Turn) kosten 40 Turns rund 13 Minuten, die alten 15 hätten den
   roten Check nur gegen einen schlechteren Fehlermodus getauscht —
   Timeout-Kill **ohne jede Ausgabe** statt roter Check **mit**
   vollständiger Ausgabe. Kostenbremse bleibt der
   Ein-Review-je-PR-Trigger, nicht der Timeout.
5. **Bewusst unverändert:** die Allowlist (wortgleich übernommen), das
   Verhalten des Diagnose-Skripts, das Opus-Pinning (ein Review je PR ist
   die Kostenbremse; das stärkere Modell je Lauf ist gewollt) und die
   Ein-Review-Trigger-Mechanik aus E1.

Damit ist die Freeze-Bedingung „Prompt-Verschlankung" aus dem
Entschärfungs-ADR erfüllt; der Meta-Freeze für weitere Mechanik-Umbauten
(u. a. `actions: read`-Absenkung, `Read`-Pfadregel) bleibt bis zum
Abschluss der passiven Zehn-Läufe-Messung bestehen. Diese Messung ist am
2026-08-26 mit 10/10 abgeschlossen; der Freeze ist damit beendet, und die
Deckel-Anhebung im Nachtrag zu Entscheidung 4 ist die erste Änderung
danach. Die beiden genannten Umbauten stehen weiterhin aus.

## Werkzeuggrenze des Reviews (verbindliche Fassung)

**Freigegeben** (rein lesend plus die zwei Ausgabewege):
`gh pr diff|view|list`, `gh pr comment <nr> --body '…'` (sonst kein Flag),
`gh issue view <nummer>` (nur Rumpf, kein `--comments`, höchstens die
ersten zwei im PR-Kopf referenzierten Issues), Read/Grep/Glob, WebFetch auf
`docs.claude.com`, `code.claude.com`, `platform.claude.com`,
`docs.anthropic.com`, `docs.github.com`, `raw.githubusercontent.com` sowie
genau diese Git-Formen (exakt, ohne weitere Flags/Pipes/Umleitungen):
`git status --short`, `git show-ref --head`,
`git log --oneline --decorate --max-count=30 HEAD`,
`git diff --stat HEAD^ HEAD`, `git diff --name-only HEAD^ HEAD`,
`git show --stat --oneline HEAD`, `git show --format=fuller --no-patch HEAD`.

**Bewusst nicht freigegeben:** `git fetch`, lokale Testausführung,
pauschales `gh api`, `gh run` (Actions-Logs), Edit/Write und alle Git-/
Datei-Schreibbefehle. Diese Aufzählung ist regeltragend für die
P-Abgrenzung der Taxonomie unten; die kanonische Definition steht hier,
der Review-Prompt trägt eine operative Kurzfassung für den Agenten, die
agents-README verweist hierauf.

Tragende Sicherheitsargumente (aus #825/#841/#850/#853 kondensiert):

- **Fork-Schutz über den Trigger:** `on: pull_request` reicht Forks keine
  Secrets durch; `HAS_CLAUDE_TOKEN` bleibt dort leer, der Job überspringt
  sich. Ein Wechsel auf `pull_request_target` höbe genau das auf.
- **Git nur in exakten Formen:** Präfix-Wildcards könnten über `--output`
  Dateien schreiben. Die `gh`-Familie behält Präfix-Wildcards (Argumente
  sind PR-/Issue-Nummern) – akzeptiertes Restrisiko; Umleitung, Pipe und
  Verkettung prüft die Kommandoanalyse je Teilkommando.
- **`gh pr comment` auf `--body '…'` verengt:** `--body-file`/`-F` wäre
  ein Datei-Egress-Kanal in einen öffentlichen Kommentar;
  `--edit-last`/`--create-if-none`/`--delete-last` könnten bestehende
  Befunde verändern oder entfernen (welche davon die Runner-`gh`-Version
  führt, ist unbelegt – die Verengung ist davon unabhängig richtig). Ein
  Sticky-Nachzug ist seit dem Ein-Review-Trigger gegenstandslos.
- **Keine Deny-Regel als zweite Schicht:** `*` matcht auch Leerzeichen im
  selben Kommandostring – eine Regel gegen `--body-file` träfe jede
  Zusammenfassung, die das Flag bloß erwähnt, und sperrte den einzigen
  Ausgabeweg statt ihn zu verengen.
- **Fremdinhalt ist Daten:** Issues darf jeder Account anlegen, bei
  Fork-PRs stammt auch der Diff von Dritten, und der Text erreicht einen
  Agenten mit `pull-requests: write`. Die Prompt-Regel (melden statt
  folgen; keine URLs aus Fremdquellen abrufen – `raw.githubusercontent.com`
  deckt bewusst jedes öffentliche Repository) ist die eigentliche Härtung;
  `Read` über das Runner-Dateisystem plus öffentliche Ausgabewege bleibt
  der Egress-Kanal, den der Trigger-Schutz und diese Regel gemeinsam
  einhegen (eine `Read`-Pfadregel als zweite Schicht bleibt offener
  #828-Punkt).
- **Rechte:** `contents: read` (kein Schreibweg in den Code),
  `pull-requests: write` genügt für beide Ausgabewege – gemessen an Lauf
  32670229428, der unter `issues: read` Zusammenfassung und
  Inline-Befunde postete. Bleibt die Ausgabe künftig aus, ist
  `issues: write` die belegte Untergrenze. `actions: read` bleibt, bis ein
  beobachteter Lauf die Absenkung deckt.

## Ablehnungs-Taxonomie (Auswertungsregel für Diagnose und Messreihe)

Gilt ausschließlich für das Review (enge Allowlist + `contents: read`);
im interaktiven `claude.yml` ist umgekehrt jede Ablehnung ein Befund, weil
der Agent dort schreiben und ausführen soll.

- **L** – lesende Ablehnung, die eine Erweiterung genau dieser Allowlist
  schließen könnte. Darf nie vorkommen; tritt sie auf, ist sie die Lücke
  und gehört gefixt. Grenze über die Ursache: Liegt der Grund außerhalb
  von `--allowedTools`, ist es W.
- **A** – Ausführung (pytest, ruff, `python -c`, Shell-Filter): erwartbar.
- **N** – Netzzugriff auf eine nicht freigegebene Domain: erwartbar.
  N geht L vor (die Domain-Auswahl ist eine dokumentierte
  Ausschlussentscheidung).
- **S** – Schreibzugriff (Datei, Git, Remote): erwartbar.
- **P** – lesende Absicht in nicht freigegebener Form (abweichende Flags,
  Pipe, Umleitung, Verkettung): Prompt-Befund, keine Allowlist-Lücke.
  P geht L vor, wenn nur die **Parameter** eines freigegebenen Kommandos
  enger sind (Prüfsteine: `--max-count=20` wie `--max-count=200` sind P)
  oder das Kommando ausdrücklich unter „Bewusst nicht freigegeben" steht.
  Ein dort **nicht** gelistetes, fehlendes Lesekommando bleibt L – so lag
  `gh issue view` vor #841.
- **W** – Ursache außerhalb von `--allowedTools` (z. B. nicht parsebares
  Kommando: belegt an `gh pr comment --body '## …'`, Lauf 32640784005).
  Fix sitzt im Prompt oder Inhalt, nie in der Allowlist.

A, N, S, P und W dürfen abgelehnt werden und rechtfertigen keine
Allowlist-Erweiterung; P und W sind Prompt-Befunde. **Ausnahme:** Eine
Ablehnung auf den zwei Ausgabewegen (Inline-Kommentar-Werkzeug,
`gh pr comment`) blockiert die Abnahme unabhängig von der Klasse – sonst
stünde „Befund gefunden, Kommentar abgewiesen, Lauf grün" als Normalfall
im Log. Die Diagnose-Ausgabe wird nur zeilenverankert ausgewertet
(`grep -c '^Abgelehnte Aufrufe: 0$'`), nie per Teilkettensuche: Belegzeilen
tragen bis zu 300 Zeichen Fremdtext, der die Kopfzeile zitieren kann.

## Invarianten des Diagnose-Schritts (Code unverändert; Herleitung)

Beide Workflows tragen denselben Schritt; die Kurzfassungen der einst
ausführlich hergeleiteten Invarianten: ein jq-Fehler endet als Warnung,
nie als „0 Ablehnungen"; Container- **und** Element-Typprüfung (ein
Nicht-Array-`permission_denials` wird als Anomalie gebucht, `null`
ebenso); `tojson` + Zeichen-Deckel + `gsub("\n"; " ")` erzwingen genau
eine Ausgabezeile je Ablehnung; die Klassenmarke (`[ABLEHNUNG]`/
`[ANOMALIE]`) steht am Zeilenanfang; gezählt wird aus der Liste selbst,
Anomalien getrennt („nicht leere Liste ⇒ nie 0"); nicht Auswertbares
nennt keine Zahl, die als Urteil lesbar wäre; `continue-on-error` plus
Gating am Schritt-Ergebnis (bei frühem Abbruch fehlt `execution_file` –
genau dann wird die Diagnose gebraucht).

## Von den Tests gepinnte Invarianten

`tests/test_claude_workflow_diagnostics.py` prüft nach der Reduktion:
Action-Schritt trägt `id: claude`; Diagnose-Schritt wortgleich in beiden
Workflows, `continue-on-error`, korrektes `if`-Gating und die
Fail-sichtbar-Fragmente; geteilter Kommentarblock und Token-Kosten-Block
wortgleich; Allowlist ohne Schreib-/Ausführungswege (kein Edit/Write,
keine Git-Schreibform, Git nur in den exakten Formen oben, `gh` nur
`pr diff|view|list|comment` + `issue view`, WebFetch nur die sechs
Domains); `fetch-depth: 0` vor den Git-Leseformen; Prompt verengt den
Ausgabeweg (`--body '…'`, kein `--body-file`, kein Flag das Kommentare
verändert, keine `#`-Zeilenanfänge, `'\''`-Regel), nennt jede freigegebene
`gh`-/Git-Form und WebFetch-Domain, reicht die PR-Nummer explizit durch,
behandelt Fremdinhalt als Daten und begrenzt das Issue-Lesen auf den
Rumpf; kein `use_sticky_comment`; `--max-turns` und `--model` gesetzt.
Trigger-Mechanik (Typen, `paths-ignore`, Job-`if`) pinnt
`tests/test_process_documentation.py`.
