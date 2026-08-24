# #841 – Abnahmekriterien und Auswertungsprozedur

Ablage der Regeln, an denen sich der Review-Workflow aus
[#841](https://github.com/NikolayDA/picture_helper/issues/841) messen lässt.
Nicht normativ für den Code; eine Gedächtnisstütze für den Fall, dass das
Fehlerbild wiederkehrt.

**Stand:** #841 wurde am 2026-08-23 vom Repository-Owner geschlossen, ohne die
unten beschriebene Messreihe abzuwarten. Der Fix liegt in PR #850 (`2468aa8`).
Diese Datei hält fest, wogegen ein künftiger Verdachtsfall geprüft würde.

## Warum hier und nicht in der Triage-Tabelle

Die Regeln standen zwischenzeitlich in der #841-Zeile von `RECOMMENDATIONS.md`.
Das ist der falsche Ort: `update_triage_table` in
`scripts/recommendations_live_check.py` entfernt eine Zeile ersatzlos, sobald
ihr Issue geschlossen ist — beim nächsten `--write`-Lauf wären sie in allen
sechs Sprachfassungen gleichzeitig verschwunden, ohne dass ein Test anschlägt.

Ein Issue-Kommentar ist ebenfalls kein Ersatz: Er liegt außerhalb des
Repositorys, außerhalb der Historie und außerhalb des Markdown-Link-Tests, und
er ist ohne Spur im Repo editier- und löschbar. `docs/history/` ist laut
CLAUDE.md die Ablage für Befund-Historie und Abnahme-Matrizen; dort überlebt
die Regel sowohl `--write` als auch das Schließen des Issues.

## Woran ein Lauf gemessen wird

1. **Zählbarkeit (ersetzt am 2026-08-24, Reviewschleifen-Entschärfung).**
   Gemessen wird **passiv** über die nächsten **zehn realen Review-Läufe** auf
   gewöhnlichen PRs — es werden keine PRs oder Pushes als Messvehikel erzeugt.
   Zwischenzeitliche Konfigurationsänderungen setzen die Zählung **nicht**
   zurück: Jeder Lauf wird gegen die zu seinem Zeitpunkt aktive Konfiguration
   gelesen und mit deren Commit-SHA notiert. Die frühere Regel („drei
   aufeinanderfolgende grüne Läufe; Läufe auf dem Fix-PR zählen nicht") hatte
   sich als selbstblockierend erwiesen: Jeder Konfig-Fix disqualifizierte die
   eigene Messreihe und erzeugte Folge-PRs als Messvehikel — Belege und
   Entscheidung in
   [ADR-2026-reviewschleifen-entschaerfung.md](ADR-2026-reviewschleifen-entschaerfung.md).
2. **Abschlussgrund und Jobstatus.** Der Diagnoseschritt muss
   `Lauf: success,` melden **und** der GitHub-Actions-Job muss mit `success`
   enden. Ein `error_max_turns` oder ein roter Job ist kein bestandener Lauf,
   auch nicht mit null Ablehnungen. Beleg für die zweite Hälfte ist Lauf
   32777452835: Das Action-Ergebnis trug `subtype: success` und 29 Turns, der
   Job wurde wegen des auf 25 gepinnten Turn-Deckels trotzdem korrekt rot.
3. **Ablehnungszähler.** Der Diagnosezähler muss **0** sein. Geprüft wird
   vollzeilenverankert auf der **rohen Schrittausgabe**:

   ```
   grep -c '^Lauf: success,'          # muss 1 liefern
   grep -c '^Abgelehnte Aufrufe: 0$'  # muss 1 liefern
   ```

   `grep -c` liefert eine Zahl, kein Urteil: Beide Zählungen müssen **1** sein.
   Der Zeilenanker ist nicht verhandelbar — der Diagnoseschritt kürzt jede
   Belegzeile auf 300 Zeichen, und eine so gekürzte `[ABLEHNUNG]`-Zeile kann auf
   genau der Zeichenkette `Abgelehnte Aufrufe: 0` enden. Eine Teilkettensuche
   meldet dann „sauber" für einen Lauf mit protokollierter Ablehnung
   (nachgestellt: Teilkette `1`, verankert `0`). Aus einem Archiv-Log geholte
   Zeilen tragen einen Zeitstempel-Präfix — dort vorher abschneiden.
4. **Ein Nullwert genügt nicht.** Kommandofehler erzeugen keinen
   `permission_denials`-Eintrag. Fünf solcher stillen Ausgänge sind in #841
   tabelliert. Deshalb gilt zusätzlich die qualitative Bedingung unten: Der
   Lauf muss tatsächlich etwas veröffentlicht haben (Wortlaut dort, nicht
   hier doppelt).
5. **Klasse je Ablehnung von Hand notieren.** Der Diagnoseschritt gibt je
   Ablehnung `tool_name`, die Feldliste (`[Felder: …]`), einen vorhandenen
   Ablehnungsgrund im Klartext (`[Grund: …]`, seit #853) und die ersten
   300 Zeichen des `tool_input` aus. Der Grund ist ein Hinweis, nicht die
   Einteilung: L/A/N/S/P/W bleibt Handarbeit. Maßgeblich ist seit der
   Verschlankung die Definition in
   [ADR-2026-review-workflow-verschlankung.md](ADR-2026-review-workflow-verschlankung.md),
   nicht eine Zusammenfassung davon.

## Qualitative Hälfte (#828)

Die fünf Punkte oben messen **Ablehnungen**, der Zweck des Jobs ist aber ein
gutes Review. Ein Lauf mit `Abgelehnte Aufrufe: 0` und einer inhaltsarmen
Zusammenfassung erfüllt sie formal — der Diagnoseschritt zählt, was abgewiesen
wurde, nie was geleistet wurde. Deshalb aus
[#828](https://github.com/NikolayDA/picture_helper/issues/828) als sechste,
bewusst nicht maschinell prüfbare Bedingung (Punkt 4 verweist hierher):

> Ein Lauf zählt nur, wenn er auch etwas geliefert hat: mindestens eine
> Zusammenfassung als PR-Kommentar mit konkretem Bezug zum Diff, und
> Inline-Befunde, sofern der Diff welche hergibt. Ein ablehnungsfreier Lauf
> ohne Befunde und ohne nachvollziehbare Prüfung zählt nicht als grün, sondern
> gar nicht.

Der Anlass war konkret: Der Prompt in `.github/workflows/claude-code-review.yml`
war mit #850 von rund 40 auf über 100 Zeilen gewachsen, der Zuwachs fast
vollständig Werkzeug- und Formatgovernance, während der fachliche Auftrag
unverändert in sechs Zeilen ganz oben stand. Anweisungen wirken auch über
Umfang und Nachdrücklichkeit, und Regeln optimieren zuverlässig auf die
Messgröße. Mit der Verschlankung vom 2026-08-24
([ADR-2026-review-workflow-verschlankung.md](ADR-2026-review-workflow-verschlankung.md))
ist der Prompt wieder auf den Auftrag reduziert.

Die Go-/No-Go-Entscheidung ist ohnehin ein menschlicher Schritt; diese Bedingung
verhindert nur, dass die Zahl allein den Ausschlag gibt.

## Messprotokoll für #828

**Startpunkt:** finaler Konfigurationsstand aus PR #858, Merge-Commit `62a3826`.
Die Läufe auf #857 und #858 selbst zählen nicht, weil beide PRs die
Review-Mechanik geändert haben und damit keine gewöhnlichen PRs im Sinne von
Punkt 1 sind.

**Live-Abgleich vom 2026-08-24:** **1/10** qualifizierende Läufe. PR #859 ist
gemergt; seine drei Review-Läufe können deshalb ohne Rückkopplung auf den
gemessenen PR ausgewertet werden. Der erste Lauf erfüllt alle Kriterien und
zählt. Beide ausdrücklich angeforderten Re-Reviews veröffentlichten ebenfalls
konkrete Befunde, ihre Jobs endeten wegen 29 beziehungsweise 30 Turns über dem
Deckel von 25 aber rot und zählen deshalb nicht.

Für jeden künftigen Lauf wird genau eine Zeile ergänzt. `Konfiguration` ist die
Commit-SHA des zu diesem Lauf aktiven Workflow-Stands; `Ergebnis` ist nur dann
`grün`, wenn Abschlussgrund, Ablehnungszähler und qualitative Hälfte gemeinsam
erfüllt sind.

| Nr. | PR | Review-Lauf | Konfiguration | Abschlussgrund | Ablehnungen | Qualitative Hälfte | Ergebnis |
|---:|---:|---:|---|---|---:|---|---|
| 1 | [#859](https://github.com/NikolayDA/picture_helper/pull/859) | [32776206368](https://github.com/NikolayDA/picture_helper/actions/runs/32776206368) | `62a3826` | Job `success`; `success` (22 Turns) | 0 | Erfüllt – konkrete Zusammenfassung und zwei Inline-Befunde veröffentlicht | Grün |
| – | [#859](https://github.com/NikolayDA/picture_helper/pull/859) | [32777452835](https://github.com/NikolayDA/picture_helper/actions/runs/32777452835) | `62a3826` | Job `failure`; Action-Result `success` (29 Turns) über Deckel 25 | 0 | Erfüllt – konkrete Zusammenfassung und Inline-Befunde veröffentlicht | Nicht gezählt – Job rot |
| – | [#859](https://github.com/NikolayDA/picture_helper/pull/859) | [32779114518](https://github.com/NikolayDA/picture_helper/actions/runs/32779114518) | `62a3826` | Job `failure`; Action-Result `success` (30 Turns) über Deckel 25 | 0 | Erfüllt – konkrete Zusammenfassung und vier Inline-Befunde veröffentlicht | Nicht gezählt – Job rot |

**#828 bleibt offen, ist aber eingefroren.** Sein Akzeptanzkriterium ist die
passive Zehn-Läufe-Messung aus Punkt 1; ein Haken ohne Messwert wäre genau die
Lücke, gegen die dieses Dokument geschrieben ist. Die Prompt-Verschlankung ist
am 2026-08-24 erfolgt
([ADR-2026-review-workflow-verschlankung.md](ADR-2026-review-workflow-verschlankung.md));
bis die Messreihe steht, werden **keine weiteren Umbauten an der
Review-Mechanik** vorgenommen (Meta-Freeze, Begründung im
[ADR-2026-reviewschleifen-entschaerfung.md](ADR-2026-reviewschleifen-entschaerfung.md)):
Vom 22.–24.08.2026 waren acht von zehn gemergten PRs Änderungen am
Review-System selbst — unter Aufsicht ebendieses Review-Systems.
