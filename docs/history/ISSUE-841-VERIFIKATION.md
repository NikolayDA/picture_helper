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
   gelesen und mit deren Commit-SHA notiert. Jeder reale Lauf belegt genau
   einen der zehn Stichprobenplätze, unabhängig davon, ob er grün oder rot
   endet; das Ergebnis ist die Messgröße, nicht die Eintrittskarte in die
   Stichprobe. Die frühere Regel („drei
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

> Ein Lauf besteht die qualitative Hälfte nur, wenn er auch etwas geliefert
> hat: mindestens eine Zusammenfassung als PR-Kommentar mit konkretem Bezug
> zum Diff, und Inline-Befunde, sofern der Diff welche hergibt. Jeder reale
> Lauf belegt unverändert genau einen Stichprobenplatz; ein Lauf ohne Befunde
> und ohne nachvollziehbare Prüfung wird **rot – qualitative Hälfte nicht
> erfüllt**, statt aus der festen Stichprobe herauszufallen.

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

**Live-Abgleich vom 2026-08-26: die Stichprobe ist voll — 10/10** reale Läufe
ausgewertet; Bilanz: **6 grün, 4 rot**. Alle zehn liefen unter derselben
Konfiguration `62a3826`: Seit diesem Commit ist keine der beiden
Claude-Workflow-Dateien mehr angefasst worden – der Meta-Freeze hat gehalten –,
und keiner der zehn PRs ändert die Review-Mechanik; es sind gewöhnliche PRs im
Sinne von Punkt 1.

Die Entkopplungsregel aus der Initialisierung dieser Tabelle (#859) ist dabei
eingehalten: Die Läufe eines PRs werden erst nach dessen Merge oder Schließung
in einem getrennten Nachtrag bewertet – das verschiebt ihre Auswertung,
verwirft sie aber nicht und verhindert, dass jeder weitere Review-Lauf einen
neuen Commit im gerade gemessenen PR erzwingt. Alle zehn Läufe unten gehören
zu inzwischen gemergten PRs. Reine Doku-PRs (#860, #862, #872, #874) tauchen
nicht auf: Der Workflow schließt sie über `paths-ignore` aus, es entsteht gar
kein Lauf.

Für jeden der zehn realen Läufe wird genau eine nummerierte Zeile ergänzt.
`Konfiguration` ist die Commit-SHA des zu diesem Lauf aktiven Workflow-Stands;
`Ergebnis` ist nur dann `grün`, wenn Abschlussgrund, Ablehnungszähler und
qualitative Hälfte gemeinsam erfüllt sind.

| Nr. | PR | Review-Lauf | Konfiguration | Abschlussgrund | Ablehnungen | Qualitative Hälfte | Ergebnis |
|---:|---:|---:|---|---|---:|---|---|
| 1 | [#859](https://github.com/NikolayDA/picture_helper/pull/859) | [32776206368](https://github.com/NikolayDA/picture_helper/actions/runs/32776206368) | `62a3826` | Job `success`; `success` (22 Turns) | 0 | Erfüllt – konkrete Zusammenfassung und zwei Inline-Befunde veröffentlicht | Grün |
| 2 | [#859](https://github.com/NikolayDA/picture_helper/pull/859) | [32777452835](https://github.com/NikolayDA/picture_helper/actions/runs/32777452835) | `62a3826` | Job `failure`; Action-Result `success` (29 Turns) über Deckel 25 | 0 | Erfüllt – konkrete Zusammenfassung und Inline-Befunde veröffentlicht | Rot – Turn-Deckel überschritten |
| 3 | [#859](https://github.com/NikolayDA/picture_helper/pull/859) | [32779114518](https://github.com/NikolayDA/picture_helper/actions/runs/32779114518) | `62a3826` | Job `failure`; Action-Result `success` (30 Turns) über Deckel 25 | 0 | Erfüllt – konkrete Zusammenfassung und vier Inline-Befunde veröffentlicht | Rot – Turn-Deckel überschritten |
| 4 | [#861](https://github.com/NikolayDA/picture_helper/pull/861) | [32840305319](https://github.com/NikolayDA/picture_helper/actions/runs/32840305319) | `62a3826` | Job `success`; `success` (24 Turns) | 0 | Erfüllt – konkrete Zusammenfassung und zwei Inline-Befunde veröffentlicht | Grün |
| 5 | [#863](https://github.com/NikolayDA/picture_helper/pull/863) | [32896919198](https://github.com/NikolayDA/picture_helper/actions/runs/32896919198) | `62a3826` | Job `failure`; Action-Result `error_max_turns` (26 Turns) | 0 | Erfüllt – konkrete Zusammenfassung und vier Inline-Befunde veröffentlicht | Rot – Turn-Budget aufgebraucht |
| 6 | [#864](https://github.com/NikolayDA/picture_helper/pull/864) | [32900479506](https://github.com/NikolayDA/picture_helper/actions/runs/32900479506) | `62a3826` | Job `success`; `success` (18 Turns) | 0 | Erfüllt – konkrete Zusammenfassung und zwei Inline-Befunde veröffentlicht | Grün |
| 7 | [#865](https://github.com/NikolayDA/picture_helper/pull/865) | [32903367472](https://github.com/NikolayDA/picture_helper/actions/runs/32903367472) | `62a3826` | Job `success`; `success` (17 Turns) | 0 | Erfüllt – konkrete Zusammenfassung und vier Inline-Befunde veröffentlicht | Grün |
| 8 | [#867](https://github.com/NikolayDA/picture_helper/pull/867) | [32905381889](https://github.com/NikolayDA/picture_helper/actions/runs/32905381889) | `62a3826` | Job `success`; `success` (18 Turns) | 0 | Erfüllt – konkrete Zusammenfassung und zwei Inline-Befunde veröffentlicht | Grün |
| 9 | [#868](https://github.com/NikolayDA/picture_helper/pull/868) | [32908766249](https://github.com/NikolayDA/picture_helper/actions/runs/32908766249) | `62a3826` | Job `failure`; Action-Result `success` (29 Turns) über Deckel 25 | 0 | Erfüllt – konkrete Zusammenfassung und vier Inline-Befunde veröffentlicht | Rot – Turn-Deckel überschritten |
| 10 | [#870](https://github.com/NikolayDA/picture_helper/pull/870) | [32941942819](https://github.com/NikolayDA/picture_helper/actions/runs/32941942819) | `62a3826` | Job `success`; `success` (25 Turns, Deckel genau erreicht) | 0 | Erfüllt – konkrete Zusammenfassung und fünf Inline-Befunde veröffentlicht | Grün |

Die beiden Review-Läufe nach dem zehnten – [32947024210](https://github.com/NikolayDA/picture_helper/actions/runs/32947024210)
(PR #871) und [32975538952](https://github.com/NikolayDA/picture_helper/actions/runs/32975538952)
(PR #873), beide Job `success` – liegen außerhalb der festen Stichprobe und
sind hier bewusst nicht bewertet: Die Stichprobe ist bei zehn geschlossen, ein
nachträgliches Aufstocken bis zum gewünschten Ergebnis wäre genau die
Beliebigkeit, gegen die Punkt 1 geschrieben ist.

## Auswertung der Zehn-Läufe-Messung (2026-08-26)

**Der Ablehnungszähler ist in allen zehn Läufen 0.** Das ist das eigentliche
Ergebnis. Der Befund, mit dem #828 eröffnet wurde – das Review verbrennt sein
Budget in einer Ablehnungsschleife – tritt nicht mehr auf. Zur Erinnerung an
die Eröffnungslage: drei der sechs ersten Läufe endeten im Turn-Limit, zwei
davon ohne irgendeine Ausgabe, und die abbrechenden Läufe wiesen 6 bis 10
Ablehnungen aus. Allowlist-Fix (#850) und die im Prompt ausformulierte
Werkzeuggrenze (#853/#858) haben gewirkt; die Akzeptanzbedingung aus #828
„ein Folgelauf weist weniger Ablehnungen aus als der jeweilige Referenzlauf"
ist mit 0 gegenüber 1 bis 10 in den Referenzläufen erfüllt.

**Die qualitative Hälfte ist in allen zehn Läufen erfüllt.** Jeder Lauf hat
eine Zusammenfassung mit konkretem Diff-Bezug veröffentlicht und zusätzlich
Inline-Befunde gesetzt (wo die Zeile sie beziffert: zwei bis fünf je Lauf).
Kein Lauf endete, ohne etwas geliefert zu haben – der teuerste Fehlermodus aus
der Eröffnung von #828 ist damit ebenfalls verschwunden.

**Was rot bleibt, ist ausschließlich das Turn-Budget**, in zwei
unterscheidbaren Formen:

- Die Action bricht selbst ab und meldet `error_max_turns` (Lauf 5, 26 Turns).
- Die Action liefert ein Ergebnis, und ihr nachgelagerter Deckel-Vergleich
  wirft: `Claude reported a successful result after 29 turns, exceeding the
  configured maximum of 25` (Läufe 2, 3 und 9 mit 29, 30 und 29 Turns). In
  dieser Form ist die Arbeit vollständig geleistet **und veröffentlicht**; rot
  wird allein der Check.

Der Verbrauch trennt sich sauber: sechs grüne Läufe bei 17 bis 25 Turns, vier
rote bei 26 bis 30. Lauf 10 traf mit exakt 25 Turns die Obergrenze und lieferte
trotzdem fünf Inline-Befunde – der Deckel aus E5 ist also nicht großzügig,
sondern grenzwertig bemessen.

**Offen ist damit eine Entscheidung, keine Messung.** Die Zahlen sagen nicht,
was zu tun ist: Ein Deckel von 30 hätte die Läufe 2, 3 und 9 grün werden
lassen (Lauf 5 ist nicht belegbar, weil er abgeschnitten wurde und mehr Turns
gebraucht haben könnte); ebenso vertretbar ist, einen roten Check bei
vollständig veröffentlichter Ausgabe hinzunehmen oder das Budget im Prompt
härter durchzusetzen. Die Go-/No-Go-Entscheidung ist laut Punkt 1 und laut
#828 ein menschlicher Schritt und lag beim Repository-Owner.

**Entscheidung vom 2026-08-26: Deckel 25 → 40.** Der Owner hat angehoben.
Der Timeout zieht von 15 auf 20 Minuten mit, sonst hätte er bei 40 Turns
die Rolle des Deckels übernommen — mit dem schlechteren Fehlerbild
(Timeout-Kill ohne Ausgabe statt rotem Check mit vollständiger Ausgabe).
Prompt, Allowlist, Modell-Pin und Trigger-Mechanik bleiben unverändert.
Herleitung und die drei synchron angefassten Stellen stehen im Nachtrag zu
Entscheidung 4 des
[ADR-2026-review-workflow-verschlankung.md](ADR-2026-review-workflow-verschlankung.md).
Die zehn Läufe oben bleiben die Messung **vor** dieser Änderung; eine neue
Stichprobe wird daraus nicht abgeleitet, solange kein neuer Verdachtsfall
auftritt.

**Der Meta-Freeze endet mit dieser Messreihe.** Er galt „bis die Messreihe
steht"
([ADR-2026-reviewschleifen-entschaerfung.md](ADR-2026-reviewschleifen-entschaerfung.md));
sein Anlass – vom 22.–24.08.2026 waren acht von zehn gemergten PRs Änderungen
am Review-System selbst, unter Aufsicht ebendieses Review-Systems – ist mit
zehn Läufen aus ausschließlich gewöhnlichen PRs abgetragen. Die in #828
zurückgestellten Restpunkte (Streichung von `actions: read`, `Read`-Pfadregel)
sind damit wieder verhandelbar; die Prompt-Verschlankung selbst ist am
2026-08-24 erfolgt
([ADR-2026-review-workflow-verschlankung.md](ADR-2026-review-workflow-verschlankung.md)).
