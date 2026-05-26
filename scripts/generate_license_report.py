#!/usr/bin/env python3
"""Erzeugt eine Lizenz- und Rechtsuebersicht fuer dieses Projekt.

Der echte Dependency-Baum wird aus pyproject.toml ([project].dependencies und
[project].optional-dependencies) abgeleitet und ueber die installierten
Paket-Metadaten transitiv aufgeloest. Vorinstallierte System-/Container-Pakete,
die nicht zum Projekt gehoeren, bleiben dadurch aussen vor.

Ausgabe (rein technische Einschaetzung, keine Rechtsberatung):
  * vollstaendiger Report  -> --report
  * Kurzfassung fuer PR-Kommentare -> --summary

Die Ausgabesprache des vollstaendigen Reports/der Kurzfassung wird ueber
--lang gesteuert (Default: de). Mit --all-langs werden zusaetzlich
lokalisierte LICENSES.md-Dateien unter docs/i18n/<lang>/ erzeugt.

Aufruf:
  python scripts/generate_license_report.py \
      --report license-report.md --summary license-summary.md --all-langs
"""
from __future__ import annotations

import argparse
import datetime as _dt
import importlib.metadata as md
import re
import sys
from collections import defaultdict
from pathlib import Path

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # Python 3.10: optionaler Backport, sonst lazy
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]

from packaging.markers import default_environment
from packaging.requirements import Requirement


def _norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _load_pyproject(pyproject: Path) -> dict:
    if tomllib is None:
        raise RuntimeError(
            "tomllib nicht verfuegbar (Python < 3.11). Diesen Generator mit "
            "Python >=3.11 ausfuehren oder optional 'tomli' installieren."
        )
    return tomllib.loads(pyproject.read_text("utf-8"))


# --- Lizenz-Wissensbasis ---------------------------------------------------
# Reihenfolge = Copyleft-Staerke (groesser = staerker). Bestimmt die
# Ausgangslizenz des verteilten Gesamtwerks.
STRENGTH = {
    "permissive": 0,
    "mpl": 1,
    "lgpl": 2,
    "gpl": 3,
    "unknown": -1,
}

# Sprachneutrale Zuordnung Lizenz-Token -> Copyleft-Kategorie. Die
# sprachabhaengige Bewertungsprosa liegt in STRINGS[lang]["assessment"].
LICENSE_CATEGORY = {
    "mit": "permissive",
    "bsd": "permissive",
    "apache": "permissive",
    "psf": "permissive",
    "hpnd": "permissive",
    "isc": "permissive",
    "zlib": "permissive",
    "mpl": "mpl",
    "lgpl": "lgpl",
    "gpl": "gpl",
    "unknown": "unknown",
}

# --- Sprachen / Lokalisierung ---------------------------------------------
LANGS = ["de", "en", "es", "fr", "uk", "zh"]
LANG_LABEL = {
    "de": "Deutsch",
    "en": "English",
    "es": "Español",
    "fr": "Français",
    "uk": "Українська",
    "zh": "简体中文",
}

# Alle benutzerseitigen Texte. de = wortgetreu wie zuvor (damit das
# deutsche Root-Output byte-identisch bleibt); uebrige Sprachen mit
# vollem Unicode.
STRINGS: dict[str, dict] = {
    "de": {
        "assessment": {
            "mit": (
                "Permissive Lizenz. Nutzung, Aenderung und Weitergabe – auch "
                "kommerziell und in proprietaeren Produkten – sind erlaubt, solange "
                "Copyright- und Lizenzhinweis erhalten bleiben."
            ),
            "bsd": (
                "Permissive Lizenz (BSD-Familie). Kommerzielle und proprietaere "
                "Nutzung erlaubt; Copyright-/Lizenzhinweis muss mitgeliefert werden, "
                "keine Werbung mit den Autorennamen ohne Zustimmung."
            ),
            "apache": (
                "Permissive Lizenz mit ausdruecklicher Patentlizenz. Kommerzielle "
                "und proprietaere Nutzung erlaubt; Lizenz-/Copyright-Hinweis und "
                "Aenderungsvermerke (NOTICE) muessen erhalten bleiben."
            ),
            "psf": (
                "Permissive Python-Software-Foundation-Lizenz. Kommerzielle und "
                "proprietaere Nutzung erlaubt; Lizenz- und Copyright-Hinweis "
                "beibehalten."
            ),
            "hpnd": (
                "Permissive HPND/MIT-CMU-Lizenz (Pillow). Kommerzielle und "
                "proprietaere Nutzung erlaubt; Copyright- und Lizenzhinweis "
                "beibehalten."
            ),
            "isc": (
                "Permissive Lizenz (funktional wie MIT). Kommerzielle und "
                "proprietaere Nutzung erlaubt; Copyright-/Lizenzhinweis beibehalten."
            ),
            "zlib": (
                "Permissive zlib-Lizenz. Kommerzielle Nutzung erlaubt; veraenderte "
                "Quellen muessen als solche gekennzeichnet werden."
            ),
            "mpl": (
                "Schwaches, dateibezogenes Copyleft. Kommerzielle Nutzung erlaubt; "
                "nur Aenderungen an den MPL-lizenzierten Dateien selbst muessen "
                "wieder unter MPL offengelegt werden. Mit GPL-3.0 vereinbar."
            ),
            "lgpl": (
                "Schwaches Copyleft fuer Bibliotheken. Kommerzielle Nutzung erlaubt; "
                "Endnutzer muss die Bibliothek austauschen koennen (dynamisches "
                "Linking bzw. Re-Link-Moeglichkeit). Mit GPL-3.0 vereinbar."
            ),
            "gpl": (
                "Starkes Copyleft. Jede Weitergabe des Gesamtwerks muss als "
                "vollstaendiger Quelltext unter GPL erfolgen; eine proprietaere "
                "(closed-source) Weitergabe ist ausgeschlossen."
            ),
            "unknown": (
                "Lizenz aus den Paket-Metadaten nicht eindeutig bestimmbar – "
                "manuelle Pruefung der Originalquelle empfohlen."
            ),
        },
        "legend": {
            "gpl": "Starkes Copyleft",
            "lgpl": "Schwaches Copyleft (Bibliothek)",
            "mpl": "Schwaches Copyleft (Datei)",
            "permissive": "Permissiv",
            "unknown": "Unklar",
        },
        "verdict": {
            "gpl": [
                "**Kommerzielle Nutzung:** Erlaubt – die GPL untersagt keinen "
                "Verkauf. Es darf Geld fuer Vertrieb, Support oder Dienste "
                "verlangt werden.",
                "**Bedingungen:** Das verteilte Gesamtwerk steht unter "
                "`{project_license}`. Bei jeder Weitergabe (auch "
                "Verkauf) muss der vollstaendige, korrespondierende **Quelltext** "
                "unter GPL mitgeliefert oder schriftlich angeboten werden; der "
                "GPL-Lizenztext und alle Copyright-Hinweise muessen beiliegen; es "
                "duerfen keine zusaetzlichen Nutzungsbeschraenkungen ergaenzt "
                "werden.",
                "**Pflichten bei Veroeffentlichung/Verkauf:** Quelloffenlegung "
                "des Gesamtwerks unter GPL, Beilegen von GPL-Text und "
                "Copyright-/Lizenzhinweisen aller (auch permissiver) "
                "Dependencies, Hinweis auf Gewaehrleistungsausschluss. Eine "
                "**proprietaere/closed-source** Auslieferung ist **nicht** "
                "moeglich.",
                "**LGPL/Qt-Besonderheit:** Qt (PyQt6-Qt6) ist LGPL-v3; PyQt6 "
                "wird hier unter GPL-3.0 genutzt. Da das Gesamtwerk ohnehin GPL "
                "ist, sind die LGPL-Austauschpflichten durch die "
                "Quelloffenlegung abgedeckt.",
            ],
            "weak": [
                "**Kommerzielle Nutzung:** Erlaubt, auch in proprietaeren "
                "Produkten.",
                "**Bedingungen:** Aenderungen an MPL-/LGPL-Komponenten bzw. die "
                "Austauschbarkeit der LGPL-Bibliothek muessen offengelegt "
                "ermoeglicht werden; eigener Code kann proprietaer bleiben.",
                "**Pflichten bei Veroeffentlichung/Verkauf:** Lizenztexte und "
                "Copyright-Hinweise beilegen, geaenderte MPL-Dateien offenlegen, "
                "Re-Link-Moeglichkeit fuer LGPL-Bibliotheken sicherstellen.",
            ],
            "permissive": [
                "**Kommerzielle Nutzung:** Uneingeschraenkt erlaubt, auch in "
                "proprietaeren/closed-source Produkten.",
                "**Bedingungen:** Lediglich Beibehaltung der Copyright- und "
                "Lizenzhinweise (Attribution); keine Quelloffenlegungspflicht.",
                "**Pflichten bei Veroeffentlichung/Verkauf:** Lizenztexte und "
                "Copyright-Vermerke der verwendeten Pakete mitliefern.",
            ],
        },
        "conflicts": {
            "gpl_no_conflict": (
                "Kein Lizenzkonflikt erkannt: Alle Dependency-Lizenzen "
                "(permissive, MPL-2.0, LGPL-v3) sind mit GPL-3.0 vereinbar und "
                "koennen unter GPL-3.0 weitergegeben werden."
            ),
            "gpl_pyqt_project": (
                "PyQt6 ist `GPL-3.0-only`. Mit der Projektlizenz "
                "`{project_license}` vertraeglich – das Gesamtwerk ist "
                "effektiv unter GPL-3.0 zu verteilen."
            ),
            "gpl_dual_license": (
                "PyQt6/Qt sind dual lizenziert (GPL **oder** kommerzielle "
                "Riverbank/Qt-Lizenz). Solange das Projekt GPL bleibt, ist die "
                "GPL-Variante einschlaegig; fuer ein proprietaeres Produkt "
                "waeren kostenpflichtige PyQt6-/Qt-Lizenzen noetig."
            ),
            "no_strong_copyleft": (
                "Kein starkes Copyleft (GPL) in der Abhaengigkeitskette – keine "
                "projektweite Copyleft-Pflicht erkannt."
            ),
            "unknown_metadata": (
                "Mindestens ein Paket hat unklare Lizenz-Metadaten – siehe "
                "Tabelle, dort manuell pruefen."
            ),
        },
        "common": {"na": "n/a"},
        "full": {
            "title": "# Lizenz- & Rechtsuebersicht – {name} {version}",
            "disclaimer": (
                "> Automatisch generiert – **rein technische Einschaetzung der "
                "Lizenzbedingungen, keine Rechtsberatung.**"
            ),
            "status_line": (
                "> Stand: {generated} · Eigenlizenz des Projekts: "
                "`{lic}` · {count} Dependencies analysiert."
            ),
            "h_overall": "## Gesamtbewertung – kommerzielle Nutzbarkeit",
            "strongest_line": (
                "Staerkste relevante Lizenz im Gesamtwerk: **{legend}**."
            ),
            "h_conflicts": "## Hinweise auf potenzielle Lizenz-Konflikte",
            "h_distribution": "## Lizenzverteilung",
            "tbl_dist_header": "| Kategorie | Anzahl | Pakete |",
            "h_details": "## Dependencies im Detail",
            "tbl_detail_header": (
                "| Paket | Version | Lizenz | Kategorie | Einschaetzung |"
            ),
            "h_sources": "## Quellen / Projektseiten",
            "footer": (
                "_Erzeugt durch `scripts/generate_license_report.py`. Aenderungen am "
                "Dependency-Satz aktualisieren diesen Report automatisch im "
                "CI-Workflow._"
            ),
        },
        "summary": {
            "h": "## Lizenz-Check – Zusammenfassung",
            "intro": (
                "Projekt `{name}` · Eigenlizenz `{lic}` · "
                "{count} Dependencies · Stand {generated}."
            ),
            "strongest": "**Staerkste Lizenz im Gesamtwerk:** {legend}",
            "distribution_label": "**Lizenzverteilung:** ",
            "conflict_label": "**Konflikt-Check:** ",
            "full_listing_note": (
                "Vollstaendige Aufstellung: Workflow-Artefakt `license-report` bzw. "
                "`LICENSES.md` im Repo-Root. _Technische Einschaetzung, keine "
                "Rechtsberatung._"
            ),
        },
        "cli": {
            "report_written": "Report geschrieben: {path}",
            "summary_written": "Kurzfassung geschrieben: {path}",
            "localized_written": "Lokalisierte LICENSES geschrieben: {path}",
        },
    },
    "en": {
        "assessment": {
            "mit": (
                "Permissive license. Use, modification and redistribution – "
                "including commercial use and in proprietary products – are "
                "permitted as long as the copyright and license notice are "
                "retained."
            ),
            "bsd": (
                "Permissive license (BSD family). Commercial and proprietary use "
                "is allowed; the copyright/license notice must be shipped along, "
                "and the authors' names may not be used for promotion without "
                "consent."
            ),
            "apache": (
                "Permissive license with an explicit patent grant. Commercial "
                "and proprietary use is allowed; the license/copyright notice and "
                "change notes (NOTICE) must be retained."
            ),
            "psf": (
                "Permissive Python Software Foundation license. Commercial and "
                "proprietary use is allowed; keep the license and copyright "
                "notice."
            ),
            "hpnd": (
                "Permissive HPND/MIT-CMU license (Pillow). Commercial and "
                "proprietary use is allowed; keep the copyright and license "
                "notice."
            ),
            "isc": (
                "Permissive license (functionally like MIT). Commercial and "
                "proprietary use is allowed; keep the copyright/license notice."
            ),
            "zlib": (
                "Permissive zlib license. Commercial use is allowed; altered "
                "sources must be marked as such."
            ),
            "mpl": (
                "Weak, file-level copyleft. Commercial use is allowed; only "
                "changes to the MPL-licensed files themselves must be disclosed "
                "again under the MPL. Compatible with GPL-3.0."
            ),
            "lgpl": (
                "Weak copyleft for libraries. Commercial use is allowed; the end "
                "user must be able to replace the library (dynamic linking or a "
                "re-link option). Compatible with GPL-3.0."
            ),
            "gpl": (
                "Strong copyleft. Any redistribution of the combined work must "
                "be provided as complete source code under the GPL; proprietary "
                "(closed-source) redistribution is excluded."
            ),
            "unknown": (
                "License could not be determined unambiguously from the package "
                "metadata – manual review of the original source recommended."
            ),
        },
        "legend": {
            "gpl": "Strong copyleft",
            "lgpl": "Weak copyleft (library)",
            "mpl": "Weak copyleft (file)",
            "permissive": "Permissive",
            "unknown": "Unclear",
        },
        "verdict": {
            "gpl": [
                "**Commercial use:** Permitted – the GPL does not prohibit "
                "selling. Money may be charged for distribution, support or "
                "services.",
                "**Conditions:** The distributed combined work is governed by "
                "`{project_license}`. On every redistribution (including sale) "
                "the complete, corresponding **source code** must be shipped or "
                "offered in writing under the GPL; the GPL license text and all "
                "copyright notices must be included; no additional usage "
                "restrictions may be added.",
                "**Obligations on publication/sale:** Disclose the source of "
                "the combined work under the GPL, include the GPL text and the "
                "copyright/license notices of all (including permissive) "
                "dependencies, and the warranty disclaimer. A "
                "**proprietary/closed-source** delivery is **not** possible.",
                "**LGPL/Qt specifics:** Qt (PyQt6-Qt6) is LGPL-v3; PyQt6 is used "
                "here under GPL-3.0. Since the combined work is GPL anyway, the "
                "LGPL replacement obligations are covered by the source "
                "disclosure.",
            ],
            "weak": [
                "**Commercial use:** Permitted, including in proprietary "
                "products.",
                "**Conditions:** Changes to MPL/LGPL components, or the "
                "replaceability of the LGPL library, must be made disclosable; "
                "your own code can remain proprietary.",
                "**Obligations on publication/sale:** Include license texts and "
                "copyright notices, disclose modified MPL files, and ensure a "
                "re-link option for LGPL libraries.",
            ],
            "permissive": [
                "**Commercial use:** Permitted without restriction, including "
                "in proprietary/closed-source products.",
                "**Conditions:** Merely retaining the copyright and license "
                "notices (attribution); no source-disclosure obligation.",
                "**Obligations on publication/sale:** Ship the license texts "
                "and copyright notices of the packages used.",
            ],
        },
        "conflicts": {
            "gpl_no_conflict": (
                "No license conflict detected: all dependency licenses "
                "(permissive, MPL-2.0, LGPL-v3) are compatible with GPL-3.0 and "
                "can be redistributed under GPL-3.0."
            ),
            "gpl_pyqt_project": (
                "PyQt6 is `GPL-3.0-only`. Compatible with the project license "
                "`{project_license}` – the combined work is effectively to be "
                "distributed under GPL-3.0."
            ),
            "gpl_dual_license": (
                "PyQt6/Qt are dual licensed (GPL **or** a commercial "
                "Riverbank/Qt license). As long as the project stays GPL, the "
                "GPL variant applies; a proprietary product would require paid "
                "PyQt6/Qt licenses."
            ),
            "no_strong_copyleft": (
                "No strong copyleft (GPL) in the dependency chain – no "
                "project-wide copyleft obligation detected."
            ),
            "unknown_metadata": (
                "At least one package has unclear license metadata – see the "
                "table and review it manually there."
            ),
        },
        "common": {"na": "n/a"},
        "full": {
            "title": "# License & Legal Overview – {name} {version}",
            "disclaimer": (
                "> Automatically generated – **a purely technical assessment of "
                "the license terms, not legal advice.**"
            ),
            "status_line": (
                "> As of: {generated} · Project's own license: "
                "`{lic}` · {count} dependencies analyzed."
            ),
            "h_overall": "## Overall Assessment – Commercial Usability",
            "strongest_line": (
                "Strongest relevant license in the combined work: **{legend}**."
            ),
            "h_conflicts": "## Notes on Potential License Conflicts",
            "h_distribution": "## License Distribution",
            "tbl_dist_header": "| Category | Count | Packages |",
            "h_details": "## Dependencies in Detail",
            "tbl_detail_header": (
                "| Package | Version | License | Category | Assessment |"
            ),
            "h_sources": "## Sources / Project Pages",
            "footer": (
                "_Generated by `scripts/generate_license_report.py`. Changes to "
                "the dependency set update this report automatically in the "
                "CI workflow._"
            ),
        },
        "summary": {
            "h": "## License Check – Summary",
            "intro": (
                "Project `{name}` · Own license `{lic}` · "
                "{count} dependencies · As of {generated}."
            ),
            "strongest": "**Strongest license in the combined work:** {legend}",
            "distribution_label": "**License distribution:** ",
            "conflict_label": "**Conflict check:** ",
            "full_listing_note": (
                "Full listing: workflow artifact `license-report` or "
                "`LICENSES.md` in the repo root. _Technical assessment, not "
                "legal advice._"
            ),
        },
        "cli": {
            "report_written": "Report written: {path}",
            "summary_written": "Summary written: {path}",
            "localized_written": "Localized LICENSES written: {path}",
        },
    },
    "es": {
        "assessment": {
            "mit": (
                "Licencia permisiva. El uso, la modificación y la "
                "redistribución – incluido el uso comercial y en productos "
                "propietarios – están permitidos siempre que se conserven el "
                "aviso de copyright y de licencia."
            ),
            "bsd": (
                "Licencia permisiva (familia BSD). Se permite el uso comercial "
                "y propietario; debe incluirse el aviso de copyright/licencia y "
                "no se puede usar el nombre de los autores con fines "
                "publicitarios sin consentimiento."
            ),
            "apache": (
                "Licencia permisiva con concesión de patente explícita. Se "
                "permite el uso comercial y propietario; deben conservarse el "
                "aviso de licencia/copyright y las notas de cambios (NOTICE)."
            ),
            "psf": (
                "Licencia permisiva de la Python Software Foundation. Se "
                "permite el uso comercial y propietario; conservar el aviso de "
                "licencia y de copyright."
            ),
            "hpnd": (
                "Licencia permisiva HPND/MIT-CMU (Pillow). Se permite el uso "
                "comercial y propietario; conservar el aviso de copyright y de "
                "licencia."
            ),
            "isc": (
                "Licencia permisiva (funcionalmente como MIT). Se permite el "
                "uso comercial y propietario; conservar el aviso de "
                "copyright/licencia."
            ),
            "zlib": (
                "Licencia permisiva zlib. Se permite el uso comercial; las "
                "fuentes modificadas deben marcarse como tales."
            ),
            "mpl": (
                "Copyleft débil, a nivel de archivo. Se permite el uso "
                "comercial; solo los cambios en los propios archivos con "
                "licencia MPL deben divulgarse de nuevo bajo MPL. Compatible "
                "con GPL-3.0."
            ),
            "lgpl": (
                "Copyleft débil para bibliotecas. Se permite el uso comercial; "
                "el usuario final debe poder reemplazar la biblioteca "
                "(enlazado dinámico o posibilidad de reenlazado). Compatible "
                "con GPL-3.0."
            ),
            "gpl": (
                "Copyleft fuerte. Toda redistribución de la obra combinada debe "
                "realizarse como código fuente completo bajo la GPL; queda "
                "excluida una redistribución propietaria (código cerrado)."
            ),
            "unknown": (
                "La licencia no se puede determinar de forma inequívoca a "
                "partir de los metadatos del paquete – se recomienda una "
                "revisión manual de la fuente original."
            ),
        },
        "legend": {
            "gpl": "Copyleft fuerte",
            "lgpl": "Copyleft débil (biblioteca)",
            "mpl": "Copyleft débil (archivo)",
            "permissive": "Permisiva",
            "unknown": "Indeterminada",
        },
        "verdict": {
            "gpl": [
                "**Uso comercial:** Permitido – la GPL no prohíbe la venta. Se "
                "puede cobrar dinero por la distribución, el soporte o los "
                "servicios.",
                "**Condiciones:** La obra combinada distribuida se rige por "
                "`{project_license}`. En cada redistribución (incluida la "
                "venta) debe entregarse u ofrecerse por escrito el **código "
                "fuente** completo y correspondiente bajo la GPL; deben "
                "adjuntarse el texto de la licencia GPL y todos los avisos de "
                "copyright; no se pueden añadir restricciones de uso "
                "adicionales.",
                "**Obligaciones al publicar/vender:** Divulgación del código "
                "fuente de la obra combinada bajo la GPL, inclusión del texto "
                "GPL y de los avisos de copyright/licencia de todas las "
                "dependencias (incluso las permisivas), y aviso de exención de "
                "garantía. No es posible una entrega "
                "**propietaria/código cerrado**.",
                "**Particularidad LGPL/Qt:** Qt (PyQt6-Qt6) es LGPL-v3; aquí "
                "PyQt6 se usa bajo GPL-3.0. Como la obra combinada ya es GPL, "
                "las obligaciones de reemplazo de la LGPL quedan cubiertas por "
                "la divulgación del código fuente.",
            ],
            "weak": [
                "**Uso comercial:** Permitido, incluso en productos "
                "propietarios.",
                "**Condiciones:** Los cambios en componentes MPL/LGPL o la "
                "posibilidad de reemplazar la biblioteca LGPL deben poder "
                "divulgarse; tu propio código puede permanecer propietario.",
                "**Obligaciones al publicar/vender:** Adjuntar los textos de "
                "licencia y los avisos de copyright, divulgar los archivos MPL "
                "modificados y garantizar la posibilidad de reenlazado de las "
                "bibliotecas LGPL.",
            ],
            "permissive": [
                "**Uso comercial:** Permitido sin restricciones, incluso en "
                "productos propietarios/de código cerrado.",
                "**Condiciones:** Únicamente conservar los avisos de copyright "
                "y de licencia (atribución); sin obligación de divulgar el "
                "código fuente.",
                "**Obligaciones al publicar/vender:** Entregar los textos de "
                "licencia y los avisos de copyright de los paquetes utilizados.",
            ],
        },
        "conflicts": {
            "gpl_no_conflict": (
                "No se detecta ningún conflicto de licencias: todas las "
                "licencias de las dependencias (permisivas, MPL-2.0, LGPL-v3) "
                "son compatibles con GPL-3.0 y pueden redistribuirse bajo "
                "GPL-3.0."
            ),
            "gpl_pyqt_project": (
                "PyQt6 es `GPL-3.0-only`. Compatible con la licencia del "
                "proyecto `{project_license}` – la obra combinada debe "
                "distribuirse efectivamente bajo GPL-3.0."
            ),
            "gpl_dual_license": (
                "PyQt6/Qt tienen licencia dual (GPL **o** una licencia "
                "comercial de Riverbank/Qt). Mientras el proyecto siga siendo "
                "GPL, se aplica la variante GPL; un producto propietario "
                "requeriría licencias de pago de PyQt6/Qt."
            ),
            "no_strong_copyleft": (
                "No hay copyleft fuerte (GPL) en la cadena de dependencias – "
                "no se detecta ninguna obligación de copyleft a nivel de "
                "proyecto."
            ),
            "unknown_metadata": (
                "Al menos un paquete tiene metadatos de licencia poco claros – "
                "consulta la tabla y revísalo manualmente allí."
            ),
        },
        "common": {"na": "n/d"},
        "full": {
            "title": "# Resumen de Licencias y Aspectos Legales – {name} {version}",
            "disclaimer": (
                "> Generado automáticamente – **una evaluación puramente "
                "técnica de los términos de licencia, no asesoramiento "
                "jurídico.**"
            ),
            "status_line": (
                "> A fecha de: {generated} · Licencia propia del proyecto: "
                "`{lic}` · {count} dependencias analizadas."
            ),
            "h_overall": "## Evaluación general – usabilidad comercial",
            "strongest_line": (
                "Licencia relevante más fuerte en la obra combinada: "
                "**{legend}**."
            ),
            "h_conflicts": "## Notas sobre posibles conflictos de licencia",
            "h_distribution": "## Distribución de licencias",
            "tbl_dist_header": "| Categoría | Cantidad | Paquetes |",
            "h_details": "## Dependencias en detalle",
            "tbl_detail_header": (
                "| Paquete | Versión | Licencia | Categoría | Evaluación |"
            ),
            "h_sources": "## Fuentes / páginas del proyecto",
            "footer": (
                "_Generado por `scripts/generate_license_report.py`. Los "
                "cambios en el conjunto de dependencias actualizan este "
                "informe automáticamente en el flujo de trabajo de CI._"
            ),
        },
        "summary": {
            "h": "## Comprobación de licencias – resumen",
            "intro": (
                "Proyecto `{name}` · Licencia propia `{lic}` · "
                "{count} dependencias · A fecha de {generated}."
            ),
            "strongest": (
                "**Licencia más fuerte en la obra combinada:** {legend}"
            ),
            "distribution_label": "**Distribución de licencias:** ",
            "conflict_label": "**Comprobación de conflictos:** ",
            "full_listing_note": (
                "Listado completo: artefacto del flujo de trabajo "
                "`license-report` o `LICENSES.md` en la raíz del repositorio. "
                "_Evaluación técnica, no asesoramiento jurídico._"
            ),
        },
        "cli": {
            "report_written": "Informe escrito: {path}",
            "summary_written": "Resumen escrito: {path}",
            "localized_written": "LICENSES localizado escrito: {path}",
        },
    },
    "fr": {
        "assessment": {
            "mit": (
                "Licence permissive. L'utilisation, la modification et la "
                "redistribution – y compris à des fins commerciales et dans des "
                "produits propriétaires – sont autorisées tant que les mentions "
                "de copyright et de licence sont conservées."
            ),
            "bsd": (
                "Licence permissive (famille BSD). Utilisation commerciale et "
                "propriétaire autorisée ; la mention de copyright/licence doit "
                "être fournie et le nom des auteurs ne peut pas être utilisé à "
                "des fins publicitaires sans accord."
            ),
            "apache": (
                "Licence permissive avec octroi de brevet explicite. "
                "Utilisation commerciale et propriétaire autorisée ; la mention "
                "de licence/copyright et les notes de modification (NOTICE) "
                "doivent être conservées."
            ),
            "psf": (
                "Licence permissive de la Python Software Foundation. "
                "Utilisation commerciale et propriétaire autorisée ; conserver "
                "la mention de licence et de copyright."
            ),
            "hpnd": (
                "Licence permissive HPND/MIT-CMU (Pillow). Utilisation "
                "commerciale et propriétaire autorisée ; conserver la mention "
                "de copyright et de licence."
            ),
            "isc": (
                "Licence permissive (fonctionnellement comme MIT). Utilisation "
                "commerciale et propriétaire autorisée ; conserver la mention "
                "de copyright/licence."
            ),
            "zlib": (
                "Licence permissive zlib. Utilisation commerciale autorisée ; "
                "les sources modifiées doivent être signalées comme telles."
            ),
            "mpl": (
                "Copyleft faible, au niveau du fichier. Utilisation commerciale "
                "autorisée ; seules les modifications des fichiers sous licence "
                "MPL eux-mêmes doivent être à nouveau divulguées sous MPL. "
                "Compatible avec GPL-3.0."
            ),
            "lgpl": (
                "Copyleft faible pour les bibliothèques. Utilisation "
                "commerciale autorisée ; l'utilisateur final doit pouvoir "
                "remplacer la bibliothèque (liaison dynamique ou possibilité de "
                "réédition de liens). Compatible avec GPL-3.0."
            ),
            "gpl": (
                "Copyleft fort. Toute redistribution de l'œuvre combinée doit "
                "être effectuée sous forme de code source complet sous licence "
                "GPL ; une redistribution propriétaire (code fermé) est exclue."
            ),
            "unknown": (
                "Licence indéterminable sans ambiguïté à partir des métadonnées "
                "du paquet – une vérification manuelle de la source d'origine "
                "est recommandée."
            ),
        },
        "legend": {
            "gpl": "Copyleft fort",
            "lgpl": "Copyleft faible (bibliothèque)",
            "mpl": "Copyleft faible (fichier)",
            "permissive": "Permissive",
            "unknown": "Indéterminée",
        },
        "verdict": {
            "gpl": [
                "**Utilisation commerciale :** Autorisée – la GPL n'interdit "
                "pas la vente. De l'argent peut être demandé pour la "
                "distribution, le support ou les services.",
                "**Conditions :** L'œuvre combinée distribuée est régie par "
                "`{project_license}`. À chaque redistribution (vente comprise), "
                "le **code source** complet et correspondant doit être fourni "
                "ou proposé par écrit sous licence GPL ; le texte de la licence "
                "GPL et toutes les mentions de copyright doivent être joints ; "
                "aucune restriction d'utilisation supplémentaire ne peut être "
                "ajoutée.",
                "**Obligations en cas de publication/vente :** Divulgation du "
                "code source de l'œuvre combinée sous GPL, inclusion du texte "
                "GPL et des mentions de copyright/licence de toutes les "
                "dépendances (même permissives), et avis d'exclusion de "
                "garantie. Une livraison **propriétaire/code fermé** n'est "
                "**pas** possible.",
                "**Particularité LGPL/Qt :** Qt (PyQt6-Qt6) est en LGPL-v3 ; "
                "PyQt6 est utilisé ici sous GPL-3.0. Comme l'œuvre combinée est "
                "de toute façon en GPL, les obligations de remplacement de la "
                "LGPL sont couvertes par la divulgation du code source.",
            ],
            "weak": [
                "**Utilisation commerciale :** Autorisée, y compris dans des "
                "produits propriétaires.",
                "**Conditions :** Les modifications des composants MPL/LGPL ou "
                "la possibilité de remplacer la bibliothèque LGPL doivent "
                "pouvoir être divulguées ; votre propre code peut rester "
                "propriétaire.",
                "**Obligations en cas de publication/vente :** Joindre les "
                "textes de licence et les mentions de copyright, divulguer les "
                "fichiers MPL modifiés et garantir une possibilité de réédition "
                "de liens pour les bibliothèques LGPL.",
            ],
            "permissive": [
                "**Utilisation commerciale :** Autorisée sans restriction, y "
                "compris dans des produits propriétaires/à code fermé.",
                "**Conditions :** Conserver uniquement les mentions de "
                "copyright et de licence (attribution) ; aucune obligation de "
                "divulgation du code source.",
                "**Obligations en cas de publication/vente :** Fournir les "
                "textes de licence et les mentions de copyright des paquets "
                "utilisés.",
            ],
        },
        "conflicts": {
            "gpl_no_conflict": (
                "Aucun conflit de licence détecté : toutes les licences des "
                "dépendances (permissives, MPL-2.0, LGPL-v3) sont compatibles "
                "avec GPL-3.0 et peuvent être redistribuées sous GPL-3.0."
            ),
            "gpl_pyqt_project": (
                "PyQt6 est `GPL-3.0-only`. Compatible avec la licence du "
                "projet `{project_license}` – l'œuvre combinée doit "
                "effectivement être distribuée sous GPL-3.0."
            ),
            "gpl_dual_license": (
                "PyQt6/Qt sont sous double licence (GPL **ou** une licence "
                "commerciale Riverbank/Qt). Tant que le projet reste en GPL, "
                "la variante GPL s'applique ; un produit propriétaire "
                "nécessiterait des licences PyQt6/Qt payantes."
            ),
            "no_strong_copyleft": (
                "Aucun copyleft fort (GPL) dans la chaîne de dépendances – "
                "aucune obligation de copyleft à l'échelle du projet détectée."
            ),
            "unknown_metadata": (
                "Au moins un paquet a des métadonnées de licence peu claires – "
                "voir le tableau et le vérifier manuellement là-bas."
            ),
        },
        "common": {"na": "n/d"},
        "full": {
            "title": "# Aperçu des licences et aspects juridiques – {name} {version}",
            "disclaimer": (
                "> Généré automatiquement – **une évaluation purement "
                "technique des conditions de licence, pas un conseil "
                "juridique.**"
            ),
            "status_line": (
                "> Au : {generated} · Licence propre du projet : "
                "`{lic}` · {count} dépendances analysées."
            ),
            "h_overall": "## Évaluation globale – utilisabilité commerciale",
            "strongest_line": (
                "Licence pertinente la plus forte dans l'œuvre combinée : "
                "**{legend}**."
            ),
            "h_conflicts": "## Remarques sur d'éventuels conflits de licence",
            "h_distribution": "## Répartition des licences",
            "tbl_dist_header": "| Catégorie | Nombre | Paquets |",
            "h_details": "## Dépendances en détail",
            "tbl_detail_header": (
                "| Paquet | Version | Licence | Catégorie | Évaluation |"
            ),
            "h_sources": "## Sources / pages du projet",
            "footer": (
                "_Généré par `scripts/generate_license_report.py`. Les "
                "modifications de l'ensemble des dépendances mettent à jour ce "
                "rapport automatiquement dans le workflow CI._"
            ),
        },
        "summary": {
            "h": "## Vérification des licences – résumé",
            "intro": (
                "Projet `{name}` · Licence propre `{lic}` · "
                "{count} dépendances · Au {generated}."
            ),
            "strongest": (
                "**Licence la plus forte dans l'œuvre combinée :** {legend}"
            ),
            "distribution_label": "**Répartition des licences :** ",
            "conflict_label": "**Vérification des conflits :** ",
            "full_listing_note": (
                "Liste complète : artefact de workflow `license-report` ou "
                "`LICENSES.md` à la racine du dépôt. _Évaluation technique, pas "
                "un conseil juridique._"
            ),
        },
        "cli": {
            "report_written": "Rapport écrit : {path}",
            "summary_written": "Résumé écrit : {path}",
            "localized_written": "LICENSES localisé écrit : {path}",
        },
    },
    "uk": {
        "assessment": {
            "mit": (
                "Дозвільна ліцензія. Використання, зміна та поширення – зокрема "
                "комерційне та у пропрієтарних продуктах – дозволені, доки "
                "збережено повідомлення про авторські права та ліцензію."
            ),
            "bsd": (
                "Дозвільна ліцензія (родина BSD). Комерційне та пропрієтарне "
                "використання дозволене; повідомлення про авторські "
                "права/ліцензію має додаватися, реклама з іменами авторів без "
                "згоди заборонена."
            ),
            "apache": (
                "Дозвільна ліцензія з явним наданням патенту. Комерційне та "
                "пропрієтарне використання дозволене; повідомлення про "
                "ліцензію/авторські права та примітки про зміни (NOTICE) мають "
                "зберігатися."
            ),
            "psf": (
                "Дозвільна ліцензія Python Software Foundation. Комерційне та "
                "пропрієтарне використання дозволене; зберігайте повідомлення "
                "про ліцензію та авторські права."
            ),
            "hpnd": (
                "Дозвільна ліцензія HPND/MIT-CMU (Pillow). Комерційне та "
                "пропрієтарне використання дозволене; зберігайте повідомлення "
                "про авторські права та ліцензію."
            ),
            "isc": (
                "Дозвільна ліцензія (функціонально як MIT). Комерційне та "
                "пропрієтарне використання дозволене; зберігайте повідомлення "
                "про авторські права/ліцензію."
            ),
            "zlib": (
                "Дозвільна ліцензія zlib. Комерційне використання дозволене; "
                "змінені джерела мають бути позначені як такі."
            ),
            "mpl": (
                "Слабкий копілефт на рівні файлів. Комерційне використання "
                "дозволене; лише зміни у самих файлах під ліцензією MPL мають "
                "знову розкриватися під MPL. Сумісна з GPL-3.0."
            ),
            "lgpl": (
                "Слабкий копілефт для бібліотек. Комерційне використання "
                "дозволене; кінцевий користувач повинен мати змогу замінити "
                "бібліотеку (динамічне компонування або можливість "
                "повторного компонування). Сумісна з GPL-3.0."
            ),
            "gpl": (
                "Сильний копілефт. Будь-яке поширення комбінованого твору має "
                "здійснюватися як повний вихідний код під GPL; пропрієтарне "
                "(із закритим кодом) поширення виключене."
            ),
            "unknown": (
                "Ліцензію не вдалося однозначно визначити з метаданих пакета – "
                "рекомендовано ручну перевірку першоджерела."
            ),
        },
        "legend": {
            "gpl": "Сильний копілефт",
            "lgpl": "Слабкий копілефт (бібліотека)",
            "mpl": "Слабкий копілефт (файл)",
            "permissive": "Дозвільна",
            "unknown": "Невизначено",
        },
        "verdict": {
            "gpl": [
                "**Комерційне використання:** Дозволене – GPL не забороняє "
                "продаж. Можна стягувати плату за поширення, підтримку чи "
                "послуги.",
                "**Умови:** Поширюваний комбінований твір підпадає під "
                "`{project_license}`. За кожного поширення (зокрема продажу) "
                "повний відповідний **вихідний код** має надаватися або "
                "пропонуватися письмово під GPL; текст ліцензії GPL та всі "
                "повідомлення про авторські права мають додаватися; не можна "
                "додавати жодних додаткових обмежень використання.",
                "**Обов'язки при публікації/продажу:** Розкриття вихідного "
                "коду комбінованого твору під GPL, додавання тексту GPL та "
                "повідомлень про авторські права/ліцензії всіх (зокрема "
                "дозвільних) залежностей, відмова від гарантій. "
                "**Пропрієтарна/із закритим кодом** поставка **неможлива**.",
                "**Особливість LGPL/Qt:** Qt (PyQt6-Qt6) має LGPL-v3; PyQt6 "
                "тут використовується під GPL-3.0. Оскільки комбінований твір "
                "у будь-якому разі під GPL, обов'язки заміни за LGPL покриті "
                "розкриттям вихідного коду.",
            ],
            "weak": [
                "**Комерційне використання:** Дозволене, зокрема у "
                "пропрієтарних продуктах.",
                "**Умови:** Зміни у компонентах MPL/LGPL чи можливість заміни "
                "бібліотеки LGPL мають бути доступними для розкриття; ваш "
                "власний код може лишатися пропрієтарним.",
                "**Обов'язки при публікації/продажу:** Додати тексти ліцензій "
                "та повідомлення про авторські права, розкрити змінені файли "
                "MPL та забезпечити можливість повторного компонування для "
                "бібліотек LGPL.",
            ],
            "permissive": [
                "**Комерційне використання:** Дозволене без обмежень, зокрема "
                "у пропрієтарних продуктах/із закритим кодом.",
                "**Умови:** Лише збереження повідомлень про авторські права та "
                "ліцензію (атрибуція); без обов'язку розкриття вихідного коду.",
                "**Обов'язки при публікації/продажу:** Надати тексти ліцензій "
                "та повідомлення про авторські права використаних пакетів.",
            ],
        },
        "conflicts": {
            "gpl_no_conflict": (
                "Конфліктів ліцензій не виявлено: усі ліцензії залежностей "
                "(дозвільні, MPL-2.0, LGPL-v3) сумісні з GPL-3.0 і можуть "
                "поширюватися під GPL-3.0."
            ),
            "gpl_pyqt_project": (
                "PyQt6 має `GPL-3.0-only`. Сумісна з ліцензією проєкту "
                "`{project_license}` – комбінований твір фактично слід "
                "поширювати під GPL-3.0."
            ),
            "gpl_dual_license": (
                "PyQt6/Qt мають подвійне ліцензування (GPL **або** комерційна "
                "ліцензія Riverbank/Qt). Доки проєкт лишається під GPL, "
                "застосовується варіант GPL; для пропрієтарного продукту "
                "знадобилися б платні ліцензії PyQt6/Qt."
            ),
            "no_strong_copyleft": (
                "У ланцюгу залежностей немає сильного копілефту (GPL) – "
                "загальнопроєктного обов'язку копілефту не виявлено."
            ),
            "unknown_metadata": (
                "Принаймні один пакет має неясні метадані ліцензії – див. "
                "таблицю та перевірте вручну там."
            ),
        },
        "common": {"na": "н/д"},
        "full": {
            "title": "# Огляд ліцензій та правових аспектів – {name} {version}",
            "disclaimer": (
                "> Згенеровано автоматично – **суто технічна оцінка умов "
                "ліцензій, а не юридична консультація.**"
            ),
            "status_line": (
                "> Станом на: {generated} · Власна ліцензія проєкту: "
                "`{lic}` · проаналізовано залежностей: {count}."
            ),
            "h_overall": "## Загальна оцінка – комерційна придатність",
            "strongest_line": (
                "Найсильніша релевантна ліцензія в комбінованому творі: "
                "**{legend}**."
            ),
            "h_conflicts": "## Зауваження щодо можливих конфліктів ліцензій",
            "h_distribution": "## Розподіл ліцензій",
            "tbl_dist_header": "| Категорія | Кількість | Пакети |",
            "h_details": "## Залежності детально",
            "tbl_detail_header": (
                "| Пакет | Версія | Ліцензія | Категорія | Оцінка |"
            ),
            "h_sources": "## Джерела / сторінки проєктів",
            "footer": (
                "_Згенеровано `scripts/generate_license_report.py`. Зміни у "
                "наборі залежностей оновлюють цей звіт автоматично у "
                "робочому процесі CI._"
            ),
        },
        "summary": {
            "h": "## Перевірка ліцензій – підсумок",
            "intro": (
                "Проєкт `{name}` · Власна ліцензія `{lic}` · "
                "залежностей: {count} · станом на {generated}."
            ),
            "strongest": (
                "**Найсильніша ліцензія в комбінованому творі:** {legend}"
            ),
            "distribution_label": "**Розподіл ліцензій:** ",
            "conflict_label": "**Перевірка конфліктів:** ",
            "full_listing_note": (
                "Повний перелік: артефакт робочого процесу `license-report` "
                "або `LICENSES.md` у корені репозиторію. _Технічна оцінка, а "
                "не юридична консультація._"
            ),
        },
        "cli": {
            "report_written": "Звіт записано: {path}",
            "summary_written": "Підсумок записано: {path}",
            "localized_written": "Локалізований LICENSES записано: {path}",
        },
    },
    "zh": {
        "assessment": {
            "mit": (
                "宽松许可证。只要保留版权声明和许可证声明，即可使用、修改和"
                "再分发，包括商业用途和在专有产品中使用。"
            ),
            "bsd": (
                "宽松许可证（BSD 系列）。允许商业和专有用途；必须随附"
                "版权/许可证声明，未经同意不得使用作者姓名进行宣传。"
            ),
            "apache": (
                "带有明确专利授权的宽松许可证。允许商业和专有用途；必须保留"
                "许可证/版权声明和变更说明（NOTICE）。"
            ),
            "psf": (
                "宽松的 Python 软件基金会许可证。允许商业和专有用途；"
                "保留许可证和版权声明。"
            ),
            "hpnd": (
                "宽松的 HPND/MIT-CMU 许可证（Pillow）。允许商业和专有用途；"
                "保留版权和许可证声明。"
            ),
            "isc": (
                "宽松许可证（功能上等同于 MIT）。允许商业和专有用途；"
                "保留版权/许可证声明。"
            ),
            "zlib": (
                "宽松的 zlib 许可证。允许商业用途；修改后的源代码必须"
                "标明为已修改。"
            ),
            "mpl": (
                "弱的、文件级 copyleft。允许商业用途；仅对 MPL 许可文件"
                "本身的修改必须再次以 MPL 公开。与 GPL-3.0 兼容。"
            ),
            "lgpl": (
                "面向库的弱 copyleft。允许商业用途；最终用户必须能够替换"
                "该库（动态链接或可重新链接）。与 GPL-3.0 兼容。"
            ),
            "gpl": (
                "强 copyleft。整体作品的任何再分发都必须以 GPL 下的完整"
                "源代码形式进行；不允许专有（闭源）再分发。"
            ),
            "unknown": (
                "无法从软件包元数据中明确确定许可证 – 建议手动核查原始来源。"
            ),
        },
        "legend": {
            "gpl": "强 copyleft",
            "lgpl": "弱 copyleft（库）",
            "mpl": "弱 copyleft（文件）",
            "permissive": "宽松",
            "unknown": "不明确",
        },
        "verdict": {
            "gpl": [
                "**商业用途：** 允许 – GPL 并不禁止销售。可以就分发、支持或"
                "服务收取费用。",
                "**条件：** 所分发的整体作品受 `{project_license}` 约束。"
                "每次再分发（包括销售）都必须在 GPL 下随附或书面提供完整、"
                "对应的**源代码**；必须附上 GPL 许可证文本和所有版权声明；"
                "不得附加任何额外的使用限制。",
                "**发布/销售时的义务：** 在 GPL 下公开整体作品的源代码，"
                "随附 GPL 文本以及所有（包括宽松许可）依赖的版权/许可证声明，"
                "并附上免责声明。**专有/闭源**交付是**不**可能的。",
                "**LGPL/Qt 特殊说明：** Qt（PyQt6-Qt6）为 LGPL-v3；此处"
                "PyQt6 在 GPL-3.0 下使用。由于整体作品本就是 GPL，LGPL 的"
                "可替换义务已由源代码公开所涵盖。",
            ],
            "weak": [
                "**商业用途：** 允许，包括在专有产品中。",
                "**条件：** 对 MPL/LGPL 组件的修改，或 LGPL 库的可替换性，"
                "必须可被公开；你自己的代码可以保持专有。",
                "**发布/销售时的义务：** 随附许可证文本和版权声明，公开经"
                "修改的 MPL 文件，并确保 LGPL 库可重新链接。",
            ],
            "permissive": [
                "**商业用途：** 不受限制地允许，包括在专有/闭源产品中。",
                "**条件：** 仅需保留版权和许可证声明（署名）；无源代码公开"
                "义务。",
                "**发布/销售时的义务：** 随附所用软件包的许可证文本和版权"
                "声明。",
            ],
        },
        "conflicts": {
            "gpl_no_conflict": (
                "未检测到许可证冲突：所有依赖许可证（宽松、MPL-2.0、"
                "LGPL-v3）均与 GPL-3.0 兼容，可在 GPL-3.0 下再分发。"
            ),
            "gpl_pyqt_project": (
                "PyQt6 为 `GPL-3.0-only`。与项目许可证 `{project_license}` "
                "兼容 – 整体作品实际上应在 GPL-3.0 下分发。"
            ),
            "gpl_dual_license": (
                "PyQt6/Qt 采用双重许可（GPL **或** 商业 Riverbank/Qt "
                "许可证）。只要项目保持 GPL，即适用 GPL 变体；专有产品则"
                "需要付费的 PyQt6/Qt 许可证。"
            ),
            "no_strong_copyleft": (
                "依赖链中没有强 copyleft（GPL）– 未检测到项目级 copyleft "
                "义务。"
            ),
            "unknown_metadata": (
                "至少有一个软件包的许可证元数据不明确 – 请参阅表格并在"
                "那里手动核查。"
            ),
        },
        "common": {"na": "不适用"},
        "full": {
            "title": "# 许可证与法律概览 – {name} {version}",
            "disclaimer": (
                "> 自动生成 – **纯粹是对许可条款的技术性评估，并非法律"
                "意见。**"
            ),
            "status_line": (
                "> 截至：{generated} · 项目自身许可证："
                "`{lic}` · 已分析 {count} 个依赖。"
            ),
            "h_overall": "## 总体评估 – 商业可用性",
            "strongest_line": (
                "整体作品中最强的相关许可证：**{legend}**。"
            ),
            "h_conflicts": "## 关于潜在许可证冲突的说明",
            "h_distribution": "## 许可证分布",
            "tbl_dist_header": "| 类别 | 数量 | 软件包 |",
            "h_details": "## 依赖详情",
            "tbl_detail_header": (
                "| 软件包 | 版本 | 许可证 | 类别 | 评估 |"
            ),
            "h_sources": "## 来源 / 项目页面",
            "footer": (
                "_由 `scripts/generate_license_report.py` 生成。依赖集合的"
                "更改会在 CI 工作流中自动更新此报告。_"
            ),
        },
        "summary": {
            "h": "## 许可证检查 – 摘要",
            "intro": (
                "项目 `{name}` · 自身许可证 `{lic}` · "
                "{count} 个依赖 · 截至 {generated}。"
            ),
            "strongest": "**整体作品中最强的许可证：** {legend}",
            "distribution_label": "**许可证分布：** ",
            "conflict_label": "**冲突检查：** ",
            "full_listing_note": (
                "完整清单：工作流工件 `license-report` 或仓库根目录下的 "
                "`LICENSES.md`。_技术性评估，并非法律意见。_"
            ),
        },
        "cli": {
            "report_written": "已写入报告：{path}",
            "summary_written": "已写入摘要：{path}",
            "localized_written": "已写入本地化 LICENSES：{path}",
        },
    },
}


def _classify_token(tok: str) -> str:
    t = tok.lower()
    if "lgpl" in t or "lesser general public" in t:
        return "lgpl"
    if "gpl" in t or "general public license" in t:
        return "gpl"
    if "mpl" in t or "mozilla public" in t:
        return "mpl"
    if "apache" in t:
        return "apache"
    if "psf" in t or "python software foundation" in t:
        return "psf"
    if "mit-cmu" in t or "hpnd" in t:
        return "hpnd"
    if "isc" in t:
        return "isc"
    if "zlib" in t:
        return "zlib"
    if "bsd" in t:
        return "bsd"
    if "mit" in t:
        return "mit"
    if t in {"0bsd", "cc0-1.0", "cc0", "unlicense"}:
        return "mit"  # public-domain-aehnlich -> wie permissive behandeln
    return ""


def classify(raw: str) -> tuple[str, str, str]:
    """-> (Kategorie, Lizenz-Key, normalisierter Lizenz-String).

    Die Bewertungsprosa wird nicht hier, sondern beim Rendern in der
    Zielsprache ueber STRINGS[lang]["assessment"][key] aufgeloest.
    """
    if not raw or raw.strip().upper() in {"", "UNKNOWN", "NONE"}:
        return LICENSE_CATEGORY["unknown"], "unknown", "UNKNOWN"
    tokens = re.split(r"\s+(?:AND|OR|WITH)\s+|;|/|,", raw)
    keys = [k for k in (_classify_token(t) for t in tokens if t.strip()) if k]
    if not keys:
        return LICENSE_CATEGORY["unknown"], "unknown", raw.strip()
    # staerkstes Copyleft im Ausdruck bestimmt Kategorie & Bewertung
    best = max(keys, key=lambda k: STRENGTH[LICENSE_CATEGORY[k]])
    return LICENSE_CATEGORY[best], best, raw.strip()


# --- Dependency-Aufloesung -------------------------------------------------
def project_roots(pyproject: Path) -> tuple[list[str], dict[str, set[str]]]:
    data = _load_pyproject(pyproject)
    proj = data.get("project", {})
    roots: list[str] = []
    extras_for: dict[str, set[str]] = {}
    specs = list(proj.get("dependencies", []))
    for group in proj.get("optional-dependencies", {}).values():
        specs.extend(group)
    for spec in specs:
        try:
            req = Requirement(spec)
        except Exception:
            continue
        roots.append(req.name)
        if req.extras:
            extras_for.setdefault(_norm(req.name), set()).update(req.extras)
    return roots, extras_for


def license_string(dist: md.Distribution) -> str:
    meta = dist.metadata
    expr = meta.get("License-Expression")
    if expr:
        return expr
    classifiers = [
        c.split("::")[-1].strip()
        for c in (meta.get_all("Classifier") or [])
        if c.startswith("License")
    ]
    if classifiers:
        return "; ".join(dict.fromkeys(classifiers))
    lic = meta.get("License")
    if lic:
        return lic.strip().splitlines()[0][:80]
    return "UNKNOWN"


def resolve_closure(roots, extras_for):
    env = default_environment()
    closure: dict[str, dict] = {}
    visited: set[tuple[str, frozenset]] = set()

    def visit(name: str, active_extras: set[str]):
        try:
            dist = md.distribution(name)
        except md.PackageNotFoundError:
            return
        real = dist.metadata["Name"]
        key = _norm(real)
        if key not in closure:
            closure[key] = {
                "name": real,
                "version": dist.version,
                "license": license_string(dist),
                "url": dist.metadata.get("Home-page")
                or _project_url(dist)
                or "",
            }
        for raw_req in dist.requires or []:
            try:
                req = Requirement(raw_req)
            except Exception:
                continue
            if req.marker:
                ok = False
                for ex in (active_extras or {""}) | {""}:
                    e = dict(env)
                    e["extra"] = ex
                    try:
                        if req.marker.evaluate(e):
                            ok = True
                            break
                    except Exception:
                        pass
                if not ok:
                    continue
            child_extras = set(req.extras)
            sig = (_norm(req.name), frozenset(child_extras))
            if sig in visited:
                continue
            visited.add(sig)
            visit(req.name, child_extras)

    for r in roots:
        visit(r, extras_for.get(_norm(r), set()))
    return closure


def _project_url(dist: md.Distribution) -> str:
    for entry in dist.metadata.get_all("Project-URL") or []:
        label, _, url = entry.partition(",")
        if label.strip().lower() in {"homepage", "repository", "source"}:
            return url.strip()
    return ""


# --- Sprach-Switcher -------------------------------------------------------
def _switcher(active: str, basename: str, at_root: bool) -> str:
    """Navigationszeile zwischen den Sprachversionen einer Datei.

    at_root=True  -> Datei liegt im Repo-Root (aktive Sprache = de),
                     Links zeigen auf docs/i18n/<lang>/<basename>.
    at_root=False -> Datei liegt in docs/i18n/<active>/, Deutsch unter
                     ../../../<basename>, Geschwister unter ../<lang>/.
    """
    parts: list[str] = []
    for lang in LANGS:
        label = LANG_LABEL[lang]
        if lang == active:
            parts.append(f"**{label}**")
            continue
        if at_root:
            target = f"docs/i18n/{lang}/{basename}"
        elif lang == "de":
            target = f"../../../{basename}"
        else:
            target = f"../{lang}/{basename}"
        parts.append(f"[{label}]({target})")
    return " · ".join(parts)


# --- Reporting -------------------------------------------------------------
def build_reports(root_dir: Path, lang: str, nav_md: str, generated: str | None = None):
    pyproject = root_dir / "pyproject.toml"
    data = _load_pyproject(pyproject)
    proj = data.get("project", {})
    project_name = proj.get("name", "Projekt")
    project_version = proj.get("version", "")
    project_license = proj.get("license", "")
    if isinstance(project_license, dict):
        project_license = project_license.get("text", "") or project_license.get(
            "file", ""
        )

    roots, extras_for = project_roots(pyproject)
    closure = resolve_closure(roots, extras_for)
    closure.pop(_norm(project_name), None)  # eigenes Paket nicht als Dependency

    rows = []
    by_cat: dict[str, list[str]] = defaultdict(list)
    for key in sorted(closure):
        info = closure[key]
        cat, lic_key, lic = classify(info["license"])
        rows.append((info["name"], info["version"], lic, cat, lic_key, info["url"]))
        by_cat[cat].append(info["name"])

    proj_cat, _, _ = classify(str(project_license))
    strongest = proj_cat
    for _, _, _, cat, _, _ in rows:
        if STRENGTH.get(cat, -1) > STRENGTH.get(strongest, -1):
            strongest = cat

    if generated is None:
        generated = _dt.date.today().isoformat()
    full = _render_full(
        project_name,
        project_version,
        project_license,
        generated,
        rows,
        by_cat,
        strongest,
        lang,
        nav_md,
    )
    summary = _render_summary(
        project_name, project_license, generated, rows, by_cat, strongest, lang
    )
    return full, summary


def _verdict(strongest: str, project_license: str, lang: str) -> list[str]:
    v = STRINGS[lang]["verdict"]
    plic = project_license or "GPL-3.0"
    if strongest == "gpl":
        return [s.format(project_license=plic) for s in v["gpl"]]
    if strongest in {"mpl", "lgpl"}:
        return list(v["weak"])
    return list(v["permissive"])


def _conflicts(rows, strongest: str, project_license: str, lang: str) -> list[str]:
    c = STRINGS[lang]["conflicts"]
    notes: list[str] = []
    has_gpl_dep = any(cat == "gpl" for *_, cat, _, _ in rows)
    proj_is_gpl = "gpl" in str(project_license).lower()
    if strongest == "gpl":
        notes.append(c["gpl_no_conflict"])
        if has_gpl_dep and proj_is_gpl:
            notes.append(
                c["gpl_pyqt_project"].format(project_license=project_license)
            )
        notes.append(c["gpl_dual_license"])
    else:
        notes.append(c["no_strong_copyleft"])
    if any(cat == "unknown" for *_, cat, _, _ in rows):
        notes.append(c["unknown_metadata"])
    return notes


def _render_full(
    name, version, lic, generated, rows, by_cat, strongest, lang, nav_md
):
    s = STRINGS[lang]
    legend = s["legend"]
    na = s["common"]["na"]
    out: list[str] = [nav_md, ""]
    out.append(s["full"]["title"].format(name=name, version=version).rstrip())
    out.append("")
    out.append(s["full"]["disclaimer"])
    out.append(
        s["full"]["status_line"].format(
            generated=generated, lic=lic or na, count=len(rows)
        )
    )
    out.append("")
    out.append(s["full"]["h_overall"])
    out.append("")
    out.append(
        s["full"]["strongest_line"].format(
            legend=legend.get(strongest, strongest)
        )
    )
    out.append("")
    for line in _verdict(strongest, str(lic), lang):
        out.append(f"- {line}")
    out.append("")
    out.append(s["full"]["h_conflicts"])
    out.append("")
    for line in _conflicts(rows, strongest, str(lic), lang):
        out.append(f"- {line}")
    out.append("")
    out.append(s["full"]["h_distribution"])
    out.append("")
    out.append(s["full"]["tbl_dist_header"])
    out.append("|---|---|---|")
    for cat in sorted(by_cat, key=lambda c: -STRENGTH.get(c, -1)):
        pkgs = ", ".join(sorted(by_cat[cat]))
        out.append(f"| {legend.get(cat, cat)} | {len(by_cat[cat])} | {pkgs} |")
    out.append("")
    out.append(s["full"]["h_details"])
    out.append("")
    out.append(s["full"]["tbl_detail_header"])
    out.append("|---|---|---|---|---|")
    for pname, pver, plic, pcat, plic_key, _ in rows:
        out.append(
            f"| {pname} | {pver} | `{plic}` | {legend.get(pcat, pcat)} | "
            f"{s['assessment'][plic_key]} |"
        )
    out.append("")
    out.append(s["full"]["h_sources"])
    out.append("")
    for pname, _, _, _, _, purl in rows:
        if purl:
            out.append(f"- **{pname}** – {purl}")
    out.append("")
    out.append("---")
    out.append(s["full"]["footer"])
    out.append("")
    return "\n".join(out)


def _render_summary(name, lic, generated, rows, by_cat, strongest, lang):
    s = STRINGS[lang]
    legend = s["legend"]
    na = s["common"]["na"]
    out: list[str] = []
    out.append(s["summary"]["h"])
    out.append("")
    out.append(
        s["summary"]["intro"].format(
            name=name, lic=lic or na, count=len(rows), generated=generated
        )
    )
    out.append("")
    out.append(
        s["summary"]["strongest"].format(legend=legend.get(strongest, strongest))
    )
    out.append("")
    for line in _verdict(strongest, str(lic), lang)[:3]:
        out.append(f"- {line}")
    out.append("")
    out.append(s["summary"]["distribution_label"] + " · ".join(
        f"{legend.get(c, c)}: {len(by_cat[c])}"
        for c in sorted(by_cat, key=lambda c: -STRENGTH.get(c, -1))
    ))
    out.append("")
    confs = _conflicts(rows, strongest, str(lic), lang)
    out.append(s["summary"]["conflict_label"] + confs[0])
    out.append("")
    out.append(s["summary"]["full_listing_note"])
    out.append("")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--report", type=Path, default=Path("license-report.md"))
    ap.add_argument("--summary", type=Path, default=Path("license-summary.md"))
    ap.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parent.parent
    )
    ap.add_argument("--lang", choices=LANGS, default="de")
    ap.add_argument(
        "--all-langs",
        action="store_true",
        help="zusaetzlich docs/i18n/<lang>/LICENSES.md fuer en,es,fr,uk,zh erzeugen",
    )
    # Stabiles Datum fuer reproduzierbare Reports: ohne diese Option wandert
    # der "Stand:"-Zeitstempel mit dem Tag der Generierung, was bei
    # gehaerteter Drift-Pruefung jeden CI-Lauf nach Mitternacht UTC roten
    # macht. Default = heute (alter Pfad bleibt unveraendert).
    ap.add_argument(
        "--generated-date",
        default=None,
        help="Datumsstempel im Report (YYYY-MM-DD); Default: heute (UTC)",
    )
    args = ap.parse_args(argv)

    # Primaerausgabe in --lang (Default de) -> Root-Verhalten unveraendert.
    # Diese Datei landet via CI als Root-LICENSES.md, daher Switcher mit
    # Root-relativen Pfaden.
    nav = _switcher(args.lang, "LICENSES.md", at_root=(args.lang == "de"))
    full, summary = build_reports(args.root, args.lang, nav, args.generated_date)
    args.report.write_text(full, "utf-8")
    args.summary.write_text(summary, "utf-8")
    print(STRINGS[args.lang]["cli"]["report_written"].format(path=args.report))
    print(STRINGS[args.lang]["cli"]["summary_written"].format(path=args.summary))

    if args.all_langs:
        for lang in ("en", "es", "fr", "uk", "zh"):
            nav_l = _switcher(lang, "LICENSES.md", at_root=False)
            full_l, _ = build_reports(args.root, lang, nav_l, args.generated_date)
            out = args.root / "docs" / "i18n" / lang / "LICENSES.md"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(full_l, "utf-8")
            print(STRINGS[lang]["cli"]["localized_written"].format(path=out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
