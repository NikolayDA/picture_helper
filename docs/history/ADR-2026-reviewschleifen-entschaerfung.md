# ADR: Entschärfung der Review-Schleifen (Ein-Review-Trigger, Konvergenzregel, Meta-Freeze)

**Status:** angenommen · **Datum:** 2026-08-24 · **Bezug:** #828,
[`ISSUE-841-VERIFIKATION.md`](ISSUE-841-VERIFIKATION.md),
[`docs/PROZESSE_UML.md`](../PROZESSE_UML.md)

## Kontext

Seit der Scharfschaltung des automatischen Reviews am 18.08.2026 (Secret
gesetzt, PR #825) lief bei jedem `opened`/`synchronize` ein 30-Turn-Review,
dessen Inline-Konversationen über die Branch-Protection-Pflicht „Require
conversation resolution" den Merge sperrten. Messung über alle 104 gemergten
PRs vom 27.07.–24.08. (GitHub-API, vollständig):

| Fenster | PRs | Ø Reviews/PR | Ø Inline-Kommentare/PR | Ø Nacharbeits-Pushes/PR |
|---|---|---|---|---|
| 27.07.–09.08. | 43 | 2,0 | 2,9 | 0,7 |
| 10.08.–17.08. | 35 | 1,5 | 2,2 | 0,6 |
| 18.08.–24.08. | 26 | 28,3 | 28,4 | 5,1 |

In der letzten Woche waren 81 % aller Commits Nacharbeit nach dem ersten
Review; PR #850 brauchte 47 Commits und 154 Review-Threads für eine
Allowlist-Zeile, und 8 der 10 zuletzt gemergten PRs änderten das
Review-System selbst. Die Schleife: Fix-Push → `synchronize` → neues
Voll-Review über den gesamten Diff → neue/umformulierte Threads →
Konversationspflicht sperrt Merge → nächster Fix-Push. Konvergenz ist dabei
nicht garantiert; auch von `cancel-in-progress` verwaiste „outdated"-Threads
sperrten weiter (21 von 30 auf #850).

## Entscheidung

1. **Ein Review je PR (E1).** `claude-code-review.yml` hört auf
   `opened`/`ready_for_review` statt `synchronize`; Drafts überspringt das
   Job-`if`. Eine Wiederholung gibt es nur auf ausdrückliche Anforderung über
   das Label `re-review` (Label entfernen und neu setzen wiederholt erneut).
   Reine Doku-PRs (`**/*.md`, `docs/**`) sind per `paths-ignore` ausgenommen;
   dort bleibt die `@claude`-Erwähnung. Die Concurrency-Gruppe liegt auf
   Job-Ebene, damit ein beliebiges Label den einzigen Review-Lauf nicht
   abbrechen kann (Codex-P1 auf PR #857); ein erneuter Draft-Zyklus
   (zurück in den Draft und wieder ready) zählt bewusst als
   Wiederholungs-Anforderung der Autor:in statt Zustands-Tracking
   einzuführen (Codex-P2 ebd.). Die Branch-Protection-Pflicht
   „Require conversation resolution before merging" wird entfernt —
   Review-Befunde sperren den Merge nicht mehr technisch. Der frühere
   Sticky-Kommentar-Rest aus #828 ist damit gegenstandslos: Ein Review je PR
   kann keinen Kommentarstapel bilden; die destruktiven
   `gh pr comment`-Flags bleiben gesperrt.
2. **Konvergenzregel (E2).** Höchstens zwei Bot-Review-Runden je PR; danach
   entscheidet ein Mensch gesammelt, was umgesetzt wird, und schließt den
   Rest mit einem Satz Begründung. Bot-Befunde sind Input der
   Merge-Entscheidung, keine Merge-Bedingung. Normativ festgehalten in
   [`docs/PROZESSE_UML.md`](../PROZESSE_UML.md) (Abschnitt 3) und
   [`CONTRIBUTING.md`](../../CONTRIBUTING.md).
3. **Meta-Freeze (E3).** Keine weiteren Umbauten an der Review-Mechanik
   (Prompt-Feinschliff, Taxonomie-Erweiterungen, `actions: read`-Streichung,
   `Read`-Pfadregel), bis die passive Messreihe steht und der Prompt
   verschlankt ist. Das selbstblockierende Kriterium „drei
   aufeinanderfolgende grüne Läufe, Konfig-Fixes setzen die Zählung zurück"
   ist ersetzt durch die passive Messung über die nächsten zehn realen
   Review-Läufe ohne Rücksetzung
   ([`ISSUE-841-VERIFIKATION.md`](ISSUE-841-VERIFIKATION.md), Punkt 1).

## Konsequenzen

- Fix-Pushes und „Update branch" erzeugen keine neuen Review-Runden mehr;
  die `strict`-Rückkante kostet nur noch einen Check-Lauf, kein Opus-Review.
- Das Review-Volumen sinkt um grob 80 % (ein Lauf je PR statt Ø 5–6) — das
  entlastet auch das Abo-Nutzungslimit, an dem im August sowohl Codex
  (Release-2.8.0-PRs ungeprüft) als auch die Claude-Workflows anschlugen.
- Befunde können jetzt unbearbeitet gemergt werden; das fängt die
  Konvergenzregel auf (bewusste menschliche Entscheidung je Befund) — die
  Verantwortung wandert von der Mechanik zur Disziplin, und das ist gewollt.
- Ein Draft-PR erhält bis `ready_for_review` kein Review; ein Doku-PR keins
  automatisch. Beides ist Absicht (Budget, Rauschen).

## Aktivierung (am 24.08.2026 abgeschlossen)

1. [x] In den [Repository-Einstellungen](https://github.com/NikolayDA/picture_helper/settings)
   unter *Branches → main* **„Require conversation resolution before
   merging"** entfernt. Pflichtstatus `Lightweight PR checks` und
   `strict`-Modus blieben unverändert; der Live-Snapshot in
   `docs/PROZESSE_UML.md` ist nachgezogen.
2. [x] Das Label **`re-review`** im Repository angelegt (*Issues → Labels*),
   damit die Wiederholungs-Anforderung nutzbar ist.
