# Sicherheitsrichtlinie

## Unterstützte Versionen

Sicherheitsupdates werden ausschließlich für die jeweils aktuelle Release-Version bereitgestellt.

| Version | Unterstützt |
|---------|-------------|
| 2.3.x   | ✓           |
| < 2.3   | ✗           |

## Sicherheitslücken melden

**Bitte keine Sicherheitslücken als öffentliches GitHub-Issue melden.**

Schwachstellen werden vertraulich über eine der folgenden Wege gemeldet:

- **GitHub Private Vulnerability Reporting:** Über die Schaltfläche „Report a vulnerability" im Tab *Security* dieses Repositories.
- **E-Mail:** nikolay79@icloud.com

### Was in der Meldung angeben?

- Betroffene Version(en) und Betriebssystem
- Reproduzierbarer Ablauf (Schritte, Eingabedaten, Fehlerbild)
- Mögliche Auswirkung und Angriffsvektor
- Optional: vorgeschlagener Fix oder Patch

### Ablauf nach dem Eingang

1. Eingangsbestätigung innerhalb von **48 Stunden**.
2. Erstbewertung (Severity, Reproduzierbarkeit) innerhalb von **7 Tagen**.
3. Koordinierte Offenlegung nach Verfügbarkeit eines Fixes — üblicherweise innerhalb von **30 Tagen**, bei komplexen Fällen länger.
4. Der Meldende wird im CHANGELOG und ggf. in den Release Notes erwähnt (sofern gewünscht).

## Sicherheitsprofil der Anwendung

BgRemover ist ein lokales Desktop-Tool ohne Netzwerkdienst, Nutzerdatenbank oder Browser-Oberfläche. Relevante Angriffsflächen:

- **Bilddateien:** Verarbeitung durch Pillow/rembg — malformte oder bösartige Bilddateien könnten Schwachstellen in diesen Bibliotheken ausnutzen.
- **Dateipfade:** Laden, Speichern und CLI-Argumente — Path-Traversal-Szenarien.
- **Qt-Plugins:** Staging in ein temporäres Verzeichnis beim Start (`qt_plugins.py`).
- **rembg / ONNX-Laufzeit:** Das optionale KI-Extra lädt Modelle aus dem Netz und führt ONNX-Inferenz lokal aus.
- **CI/CD und Abhängigkeiten:** Supply-Chain-Risiken in Workflows und transitiven Paketen.

Regelmäßige automatische Sicherheitsscans laufen über den GitHub Codex Security Scanner (`.github/codex/`).

## Abhängigkeiten

Bekannte CVEs in Abhängigkeiten werden in `pyproject.toml` durch Mindestversions-Pins ausgeschlossen und im CHANGELOG dokumentiert. Bitte melde schwerwiegende, noch nicht gepinnte CVEs ebenfalls über den oben beschriebenen vertraulichen Weg.
