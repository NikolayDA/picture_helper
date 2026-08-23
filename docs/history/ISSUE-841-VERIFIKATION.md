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

1. **Zählbarkeit.** Läufe auf PR #850 selbst zählen nicht — jeder von ihnen hat
   die Konfiguration verändert, gegen die gemessen wird. Die Zählung beginnt mit
   dem ersten Reviewlauf nach dem Merge von #850.
2. **Abschlussgrund.** Der Diagnoseschritt muss `Lauf: success,` melden. Ein
   `error_max_turns` ist kein bestandener Lauf, auch nicht mit null Ablehnungen.
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
   tabelliert. Zweite Bedingung: Der Lauf muss auch tatsächlich etwas
   veröffentlicht haben — mindestens eine Zusammenfassung als PR-Kommentar.
5. **Klasse je Ablehnung von Hand notieren.** Der Diagnoseschritt gibt nur
   `tool_name` und die ersten 300 Zeichen aus; die Einteilung L/A/N/S/P ist
   daraus nicht maschinell rekonstruierbar. Maßgeblich ist die Definition in
   `.github/workflows/claude-code-review.yml`, nicht eine Zusammenfassung davon.

## Qualitative Hälfte (#828)

Die vier Punkte oben messen **Ablehnungen**, der Zweck des Jobs ist aber ein
gutes Review. Ein Lauf mit `Abgelehnte Aufrufe: 0` und einer inhaltsarmen
Zusammenfassung erfüllt sie formal — der Diagnoseschritt zählt, was abgewiesen
wurde, nie was geleistet wurde. Deshalb aus
[#828](https://github.com/NikolayDA/picture_helper/issues/828) als fünfte,
bewusst nicht maschinell prüfbare Bedingung:

> Ein Lauf zählt nur, wenn er auch etwas geliefert hat: mindestens eine
> Zusammenfassung als PR-Kommentar mit konkretem Bezug zum Diff, und
> Inline-Befunde, sofern der Diff welche hergibt. Ein ablehnungsfreier Lauf
> ohne Befunde und ohne nachvollziehbare Prüfung zählt nicht als grün, sondern
> gar nicht.

Der Anlass ist konkret: Der Prompt in `.github/workflows/claude-code-review.yml`
ist mit #850 von rund 40 auf über 100 Zeilen gewachsen, und der Zuwachs ist fast
vollständig Werkzeug- und Formatgovernance. Der fachliche Auftrag steht
unverändert in sechs Zeilen ganz oben. Anweisungen wirken auch über Umfang und
Nachdrücklichkeit, und Regeln optimieren zuverlässig auf die Messgröße.

Die Go-/No-Go-Entscheidung ist ohnehin ein menschlicher Schritt; diese Bedingung
verhindert nur, dass die Zahl allein den Ausschlag gibt.

**#828 bleibt offen.** Sein Akzeptanzkriterium verlangt einen Folgelauf mit
*weniger Ablehnungen* als der jeweilige Referenzlauf. Diese Messreihe hat nie
stattgefunden: #841 wurde vor ihrem Beginn geschlossen. Die Kriterien stehen
deshalb hier, das Issue bleibt bis zu einer echten Messung offen — ein Haken
ohne Messwert wäre genau die Lücke, gegen die dieses Dokument geschrieben ist.
