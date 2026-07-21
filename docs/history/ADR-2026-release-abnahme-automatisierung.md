# ADR (2026-07-20): Automatisierte Release-Abnahme über Self-hosted Hardware-Runner

ADR zu #640 („[Abnahme-Automation] ADR + Betriebs-/Sicherheitsdoku") im Epic
#639 („Automatisierte Release-Abnahme"). Automatisiert die Evidenzsammlung der
manuellen Release-Prozeduren aus [../PACKAGING_SMOKE.md](../PACKAGING_SMOKE.md)
(Issue #595, Epic #582). Betriebsanleitung:
[../RELEASE_AUTOMATION.md](../RELEASE_AUTOMATION.md).
Status: **beschlossen, Implementierung läuft** (#641–#646).

## Kontext

Die Release-Abnahme verlangt Nachweise, die die Offscreen-CI prinzipiell nicht
liefern kann: Start der fünf Release-Artefaktklassen auf **echter
Zielhardware**, Screenshots mit **echtem GPU-Renderer**, Retina-/High-DPI-
Verhalten und GL-gebundene Performance-Metriken. Software-Renderer (llvmpipe)
werden von der Provenance-Prüfung des Screenshot-Generators (#635) bewusst
abgewiesen – ein GitHub-gehosteter Runner mit Xvfb kann diese Kriterien daher
nie ehrlich erfüllen. Bisher sind das manuelle Prozeduren mit Protokollpflicht
(Commit-SHA, Umgebung, Ergebnis).

## Entscheidung

Die Evidenz wird über **Self-hosted GitHub-Actions-Runner** auf der real
vorhandenen Zielhardware gesammelt, orchestriert von einem eigenen Workflow
[`release-abnahme.yml`](../../.github/workflows/release-abnahme.yml) (#641):

- **macOS arm64 (Apple M3):** DMG-Smoke inkl. Retina-/High-DPI-Nachweis (#643).
- **Linux aarch64 (Raspberry Pi 5):** AppImage- und `.deb`-Smoke auf echter
  Hardware inkl. GL-Provenance (#642).
- **Linux x86_64 (GPU): pausiert** – Entscheidung vom 2026-07-20, es besteht
  kein Zugang zu einem x86_64-Rechner mit echter GPU und X11-/Wayland-Session.
  Der Pfad wird mitentworfen, bleibt aber über die Repository-Variable
  `ABNAHME_X86_64_ENABLED` deaktiviert (Details und Wiederaufnahme-Kriterien in
  [../RELEASE_AUTOMATION.md](../RELEASE_AUTOMATION.md)). Für
  Release-Entscheidungen gilt dieser Hardware-Smoke solange als **offen
  deklariert**, nicht als erfüllt.

Die Automatisierung liefert **Evidenz, kein Urteil**: Die Go-/No-Go-
Entscheidung auf Basis der Abschlussmatrix (#646) bleibt ein menschlicher
Schritt. Die inhaltlichen Abnahmekriterien aus
[../PACKAGING_SMOKE.md](../PACKAGING_SMOKE.md) ändern sich nicht – nur ihr
Nachweis wird reproduzierbar per `workflow_dispatch`.

## Sicherheitsmodell (verbindlich, technisch erzwungen)

Self-hosted Runner führen Code auf Privatgeräten aus; GitHub selbst rät von
Self-hosted Runnern für öffentliche Repositories mit Fremd-PRs ab. Daraus
folgen harte Regeln, die #641 per Workflow-Definition und Governance-Test
(`tests/test_release_abnahme_workflow.py`) erzwingt:

1. **Nur `workflow_dispatch`.** Der Abnahme-Workflow hat keinerlei `push`-,
   `pull_request`- oder Fork-Trigger; fremder PR-Code erreicht die Runner nie.
2. **Least-Privilege-Permissions.** Der Workflow deklariert ausschließlich
   `contents: read` (Release-Assets) und `actions: read`
   (Workflow-Artefakte als alternative Quelle). Schreib-Scopes sind erst im
   Aggregations-Job aus #646 zulässig – und nur dort.
3. **Runner sind repo-exklusiv** registriert (kein Sharing mit anderen
   Repositories/Organisationen) und laufen unter einem dedizierten Benutzer
   ohne Zugriff auf private Daten; Checkliste in
   [../RELEASE_AUTOMATION.md](../RELEASE_AUTOMATION.md).
4. **Keine Secrets in Smoke-Steps.** Smoke-Skripte erhalten nur das
   Standard-`GITHUB_TOKEN` (read-only) für den Artefaktbezug; der
   Vision-API-Key aus #646 geht ausschließlich an den Auswertungsjob.
5. **`concurrency`-Gruppe** verhindert parallele Abnahme-Läufe auf denselben
   Geräten; jeder Job trägt ein hartes `timeout-minutes`.

## Evidenzvertrag

Jeder Nachweis besteht aus einem maschinenlesbaren `evidenz.json` plus einem
menschenlesbaren `manifest.md` und wird je Plattform als Workflow-Artefakt
`abnahme-<plattform>` hochgeladen. Pflichtfelder in `evidenz.json`:

| Feld | Bedeutung |
|---|---|
| `schema` | Versionsnummer des Evidenzformats (aktuell `1`) |
| `kind` | konstant `abnahme-evidenz` |
| `platform` | `linux-arm64` / `linux-x86_64` / `macos-arm64` |
| `status` | `platzhalter` (Gerüst #641) → später `bestanden` / `fehlgeschlagen` / `unbewertet` |
| `commit_sha` | Commit, aus dem der Abnahme-Lauf gestartet wurde |
| `quelle` | Artefaktquelle: `{"art": "release-tag" \| "run-id", "wert": …}` |
| `artefakte` | Liste `{name, sha256, bytes}` der geprüften Release-Artefakte |
| `umgebung` | OS/Release, Architektur, Python-Version, Runner-Name |
| `gl_provenance` | OpenGL Vendor/Renderer/Version (`null` nur im Platzhalter; ab #642/#643 Pflicht, Software-Renderer ⇒ `fehlgeschlagen`) |
| `erzeugt_am` | ISO-8601-Zeitstempel (UTC) |
| `hinweise` | Freitext-Liste (z. B. Platzhalter-Vermerk, pausierte Pfade) |

Damit ist die Protokollpflicht aus
[../PACKAGING_SMOKE.md](../PACKAGING_SMOKE.md) („Commit-SHA, Umgebung,
Ergebnis") maschinell erfüllt. Das Manifest-Muster mit
Hardware-Renderer-Provenance folgt dem Screenshot-Generator aus #635:
Software-Renderer sind als Hardware-Nachweis **ungültig** – jede spätere
GL-Evidenz (#642, #643, #645) muss die Provenance-Prüfung bestehen, sonst gilt
der Smoke als nicht erbracht.

## Rollen der Zusatzdienste

- **Vision-Vorbewertung (Claude API, #646):** bewertet Screenshots gegen einen
  Kriterienkatalog, strukturiert je Kriterium. **Fail-safe:** ohne API-Key oder
  bei API-Fehlern degradiert das Ergebnis zu `unbewertet`; der Abnahme-Lauf
  scheitert daran nie.
- **Aggregation/Abschlussmatrix (#646):** validiert alle Evidenz-Artefakte
  gegen diesen Vertrag und erzeugt die Matrix je Abnahmekriterium; pausierte
  Pfade erscheinen explizit als „pausiert, nicht erfüllt".
- **Mensch:** trifft die Go-/No-Go-Entscheidung auf Basis der Matrix.

## Verworfene Alternativen

- **GitHub-gehostete Runner + Xvfb/llvmpipe:** liefern nur Software-GL; genau
  die Nachweise, um die es geht (echter GPU-Renderer, Retina), sind dort
  prinzipiell nicht ehrlich erbringbar. Bleibt der richtige Ort für alles
  Headless-Taugliche (bestehende CI).
- **Kommerzielle GUI-Test-Suiten (z. B. Squish):** lösen das Hardware-Problem
  nicht (brauchen ebenfalls reale Geräte), kosten Lizenz und ergänzen wenig
  gegenüber der vorhandenen qtbot-/pytest-Infrastruktur.
- **GPU-Cloud-Runner:** decken weder Raspberry Pi 5 noch Apple-Retina-Panels
  ab, verursachen laufende Kosten und verschieben das Vertrauensproblem nur
  (fremde Hardware statt eigener).

## Konsequenzen

- Ein `workflow_dispatch`-Lauf ersetzt die manuelle Evidenzsammlung auf den
  registrierten Plattformen; die Geräte müssen dazu eingeschaltet und als
  Runner online sein (Betrieb: [../RELEASE_AUTOMATION.md](../RELEASE_AUTOMATION.md)).
- Der pausierte x86_64-Pfad bleibt sichtbar (Skip-Hinweis im Lauf, „pausiert"
  in der Matrix) statt still zu fehlen; Reaktivierung braucht nur Runner +
  Variable, keine Code-Änderung.
- Die Teil-Issues #641–#646 implementieren gegen diesen Vertrag; Änderungen am
  Vertrag laufen über einen ADR-Nachtrag, nicht über stille Formatdrift.
