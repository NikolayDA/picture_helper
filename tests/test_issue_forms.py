"""Netzfreies Gate für die GitHub-Issue-Forms (#1034).

Die Forms erscheinen im Template-Chooser erst **nach** dem Merge in den
Default-Branch – ein YAML- oder Schemafehler fällt dort also frühestens auf,
wenn jemand ein Issue anlegen will, und GitHub verwirft die Vorlage dann
kommentarlos. Dieser Test ist deshalb der einzige Wächter vor dem Merge: Er
parst beide Forms und die ``config.yml`` und prüft genau die Eigenschaften,
die die Diagnose trägt (Pflichtangaben, eindeutige IDs, gefüllte Dropdowns,
absoluter Kontaktlink).

Bewusst **nicht** geprüft wird das vollständige GitHub-Schema: Es ist nicht
versioniert abrufbar, und eine nachgebaute Vollkopie wäre eine weitere
Drift-Quelle. Geprüft wird, was hier zu Fehlern geführt hat.

PyYAML ist seit #1016 deklarierte ``[test]``-Abhängigkeit.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

_ROOT = Path(__file__).resolve().parent.parent
_TEMPLATE_DIR = _ROOT / ".github" / "ISSUE_TEMPLATE"

_BUG_FORM = _TEMPLATE_DIR / "bug_report.yml"
_FEATURE_FORM = _TEMPLATE_DIR / "feature_request.yml"
_CONFIG = _TEMPLATE_DIR / "config.yml"

_FORMS = (_BUG_FORM, _FEATURE_FORM)

# Die von GitHub für Issue Forms dokumentierten Elementtypen.
_ALLOWED_TYPES = {"markdown", "input", "textarea", "dropdown", "checkboxes"}

# Pflichtangaben je Form: ohne sie ist ein Bericht nicht triagierbar.
_REQUIRED_IDS = {
    _BUG_FORM.name: {"version", "platform", "installation", "reproduction", "confirmation"},
    _FEATURE_FORM.name: {"problem", "proposal"},
}

_EXPECTED_LABELS = {_BUG_FORM.name: "bug", _FEATURE_FORM.name: "enhancement"}

# Vorauswahl je optionalem Dropdown – als **Label**, nicht als Index. Der Index
# ist eine Position: Bekommt ``WorkflowStep`` je einen siebten Schritt, rutscht
# „übergreifend" auf 7 und ``default: 6`` zeigte auf den neuen Schritt. Das wäre
# der Schaden dieses PRs in umgekehrter Richtung – statt einer Lücke, die wie
# eine Antwort aussieht, eine falsche Antwort, die plausibel aussieht
# (Review PR #1063).
_EXPECTED_DROPDOWN_DEFAULTS = {
    _BUG_FORM.name: {"ai_backend": "unbekannt"},
    _FEATURE_FORM.name: {"workflow_step": "übergreifend"},
}


def _load(path: Path) -> dict[str, Any]:
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:  # pragma: no cover - der Fehlertext ist die Aussage
        pytest.fail(f"{path.name} ist kein valides YAML: {exc}")
    assert isinstance(doc, dict), f"{path.name}: Top-Level ist kein Mapping"
    return doc


# Ein spitzklammer-Platzhalter wie ``<Version>`` ausserhalb eines Code-Spans:
# GitHub rendert Labels, Beschreibungen und ``markdown``-Bloecke der Forms als
# Markdown und entfernt ihn als unbekanntes HTML-Tag – der Hinweis verliert
# lautlos genau das Beispiel, das er erklaeren soll (Review PR #1060).
_CODE_SPAN_RE = re.compile(r"`[^`]*`")
_ANGLE_PLACEHOLDER_RE = re.compile(r"<[A-Za-zÄÖÜäöü][^<>\s]*>")

# GitHub erlaubt in ``id`` nur Ziffern, Buchstaben, ``-`` und ``_``.
_ID_RE = re.compile(r"[0-9A-Za-z_-]+")

# Felder, die GitHub als Markdown rendert.
_RENDERED_KEYS = ("label", "description", "value")


def _is_required(element: dict[str, Any]) -> bool:
    """Wahr, wenn das Element eine Eingabe erzwingt.

    ``checkboxes`` kennt kein ``validations.required`` – dort hängt die Pflicht
    an der einzelnen Option. Beide Formen zählen hier gleich.
    """

    validations = element.get("validations") or {}
    if isinstance(validations, dict) and validations.get("required") is True:
        return True
    options = (element.get("attributes") or {}).get("options") or []
    return any(
        isinstance(option, dict) and option.get("required") is True for option in options
    )


@pytest.mark.parametrize("path", _FORMS, ids=lambda p: p.name)
def test_form_has_the_chooser_fields(path: Path) -> None:
    """``name``/``description``/``body`` sind Pflicht – ohne sie zeigt GitHub die Vorlage nicht."""

    doc = _load(path)
    for key in ("name", "description"):
        value = doc.get(key)
        assert isinstance(value, str) and value.strip(), f"{path.name}: {key} fehlt oder ist leer"
    body = doc.get("body")
    assert isinstance(body, list) and body, f"{path.name}: body fehlt oder ist leer"


@pytest.mark.parametrize("path", _FORMS, ids=lambda p: p.name)
def test_form_elements_are_well_formed(path: Path) -> None:
    """Erlaubter ``type``, eindeutige ``id`` je Eingabeelement, gefüllte ``attributes``."""

    body = _load(path)["body"]
    seen: set[str] = set()
    for index, element in enumerate(body):
        where = f"{path.name}[{index}]"
        assert isinstance(element, dict), f"{where}: Element ist kein Mapping"
        kind = element.get("type")
        assert kind in _ALLOWED_TYPES, f"{where}: unbekannter type {kind!r}"
        attributes = element.get("attributes")
        assert isinstance(attributes, dict) and attributes, f"{where}: attributes fehlen"
        if kind == "markdown":
            # Reine Hinweistexte tragen bewusst keine id (GitHub weist sie ab).
            assert "id" not in element, f"{where}: markdown-Element darf keine id tragen"
            assert str(attributes.get("value", "")).strip(), f"{where}: markdown ohne Text"
            continue
        element_id = element.get("id")
        assert isinstance(element_id, str) and element_id.strip(), f"{where}: id fehlt"
        assert element_id not in seen, f"{path.name}: id {element_id!r} doppelt vergeben"
        seen.add(element_id)
        assert str(attributes.get("label", "")).strip(), f"{where}: label fehlt"


@pytest.mark.parametrize("path", _FORMS, ids=lambda p: p.name)
def test_required_fields_are_enforced(path: Path) -> None:
    """Genau die Angaben, ohne die eine Triage nicht möglich ist, sind Pflicht."""

    body = _load(path)["body"]
    required = {
        element["id"]
        for element in body
        if element.get("type") != "markdown" and _is_required(element)
    }
    expected = _REQUIRED_IDS[path.name]
    missing = sorted(expected - required)
    assert not missing, f"{path.name}: nicht als required markiert: {', '.join(missing)}"
    # Die Gegenrichtung ist die, die Melder aussperrt: Issue Forms kennen keine
    # bedingten Pflichtfelder, ``python_version`` etwa gilt nur bei einer
    # Quellinstallation. Auf ``required`` gesetzt blockierte es jeden DMG- und
    # AppImage-Melder – ohne dass ein Test anschlüge (Review PR #1060).
    surplus = sorted(required - expected)
    assert not surplus, (
        f"{path.name}: zusätzlich als required markiert, obwohl die Angabe nicht"
        f" für jeden Melder zutrifft: {', '.join(surplus)}"
    )


@pytest.mark.parametrize("path", _FORMS, ids=lambda p: p.name)
def test_dropdowns_offer_a_choice(path: Path) -> None:
    """Ein Dropdown mit einer Option ist ein verstecktes Pflichtfeld ohne Aussage."""

    body = _load(path)["body"]
    dropdowns = [element for element in body if element.get("type") == "dropdown"]
    assert dropdowns, f"{path.name}: kein Dropdown – die Plattform-/Schritt-Auswahl fehlt"
    for element in dropdowns:
        options = element["attributes"].get("options")
        assert isinstance(options, list) and len(options) >= 2, (
            f"{path.name}: Dropdown {element['id']!r} hat weniger als zwei Optionen"
        )
        assert all(
            isinstance(option, str) and option.strip() for option in options
        ), f"{path.name}: Dropdown {element['id']!r} hat leere Optionen"


@pytest.mark.parametrize("path", _FORMS, ids=lambda p: p.name)
def test_dropdown_defaults_follow_the_requiredness(path: Path) -> None:
    """Ein optionales Dropdown braucht eine Vorauswahl, ein Pflicht-Dropdown darf keine haben.

    GitHub rendert ein nicht ausgefülltes Dropdown im erzeugten Issue als
    ``None`` – bei Textfeldern steht dort ``_No response_``. Für „KI-Hinter-
    grundentfernung installiert?" las sich das wie die Antwort „nein" statt
    wie „nicht ausgefüllt" (beobachtet an #1061), also ausgerechnet in einem
    Feld, das die Triage lenken soll.

    Umgekehrt wäre eine Vorauswahl an einem Pflicht-Dropdown schädlich: Sie
    nähme dem `required` seine Wirkung, weil das Formular schon mit der
    voreingestellten Antwort absendbar ist – „Plattform: macOS arm64" wäre
    dann keine Angabe, sondern eine Vermutung.
    """

    for element in _load(path)["body"]:
        if element.get("type") != "dropdown":
            continue
        attributes = element["attributes"]
        default = attributes.get("default")
        if _is_required(element):
            assert default is None, (
                f"{path.name}: Pflicht-Dropdown {element['id']!r} hat eine Vorauswahl –"
                " damit ist das Formular ohne bewusste Antwort absendbar"
            )
            continue
        assert isinstance(default, int) and not isinstance(default, bool), (
            f"{path.name}: optionales Dropdown {element['id']!r} ohne default –"
            " unausgefüllt erscheint es im Issue als 'None'"
        )
        options = attributes["options"]
        assert 0 <= default < len(options), (
            f"{path.name}: default {default} von {element['id']!r} liegt ausserhalb"
            f" der {len(options)} Optionen"
        )
        expected = _EXPECTED_DROPDOWN_DEFAULTS[path.name][element["id"]]
        assert options[default] == expected, (
            f"{path.name}: Vorauswahl von {element['id']!r} zeigt auf"
            f" {options[default]!r} statt auf {expected!r} – der Index folgt der"
            " Position, nicht der Aussage"
        )


@pytest.mark.parametrize("path", _FORMS, ids=lambda p: p.name)
def test_form_presets_its_label(path: Path) -> None:
    """Die Vorbelegung spart den ersten Triage-Handgriff."""

    labels = _load(path).get("labels")
    assert isinstance(labels, list), f"{path.name}: labels fehlen"
    assert _EXPECTED_LABELS[path.name] in labels, (
        f"{path.name}: Label {_EXPECTED_LABELS[path.name]!r} nicht vorbelegt"
    )


def test_bug_form_asks_for_the_log_as_plain_text() -> None:
    """``render: text`` verhindert, dass ein Logauszug als Markdown zerfällt.

    GitHub erlaubt bei gerenderten Textareas kein ``required`` – der Logauszug
    bleibt deshalb optional und steht bewusst nicht in ``_REQUIRED_IDS``.
    """

    body = _load(_BUG_FORM)["body"]
    log = next(element for element in body if element.get("id") == "log")
    assert log["attributes"].get("render") == "text"
    assert not _is_required(log), "gerenderte Textarea darf nicht required sein"


def test_bug_form_confirmation_holds_without_an_attachment() -> None:
    """Issue Forms kennen keine bedingten Pflichtfelder (#1034).

    Die Bestätigung ist deshalb immer erforderlich und bedingt formuliert –
    ein Bericht ohne Anhang bleibt absendbar.
    """

    body = _load(_BUG_FORM)["body"]
    confirmation = next(element for element in body if element.get("id") == "confirmation")
    options = confirmation["attributes"]["options"]
    assert len(options) == 1, "genau eine Bestätigung, sonst wird sie überlesen"
    text = " ".join(options[0]["label"].split())
    assert options[0].get("required") is True
    assert "auch, wenn nichts angehängt ist" in text, (
        "die bedingte Formulierung ist der Grund, warum die Pflicht keinen Bericht blockiert"
    )


@pytest.mark.parametrize("path", _FORMS, ids=lambda p: p.name)
def test_form_avoids_the_documented_rejection_reasons(path: Path) -> None:
    """Die Regeln, an denen GitHub eine Form nach dem Merge kommentarlos abweist.

    Quelle ist die Fehlerliste „Common validation errors when creating issue
    forms". Geprüft werden die Gründe, die hier überhaupt eintreten können und
    die die übrigen Tests nicht schon abdecken: mindestens ein Eingabefeld,
    eindeutige Beschriftungen, ``id`` nur aus erlaubten Zeichen und Optionen
    ohne Dubletten, ohne die reservierten ``none``/``n/a`` und ohne
    Wahrheitswerte. Die beiden reservierten Wörter sind erst mit der
    Vorauswahl scharf geworden: GitHub verbietet sie ausdrücklich, „when a
    default option is specified" – und der Defaultwächter verlangt für jedes
    optionale Dropdown genau so eine Vorauswahl.
    Ein ``ja``/``nein``-Paar ist dabei die reale Falle: YAML 1.1 liest
    ``no``/``yes``/``on``/``off`` als Boolean, die deutschen Wörter nicht.
    """

    body = _load(path)["body"]
    inputs = [element for element in body if element.get("type") != "markdown"]
    assert inputs, f"{path.name}: Body ohne Eingabefeld"

    labels = [element["attributes"]["label"].strip().casefold() for element in inputs]
    assert len(labels) == len(set(labels)), f"{path.name}: doppelte Beschriftung"

    for element in inputs:
        assert _ID_RE.fullmatch(element["id"]), (
            f"{path.name}: id {element['id']!r} enthält unerlaubte Zeichen"
        )
        options = element["attributes"].get("options") or []
        texts = [
            option["label"] if isinstance(option, dict) else option for option in options
        ]
        assert all(isinstance(text, str) for text in texts), (
            f"{path.name}: {element['id']!r} hat eine Option, die YAML nicht als Text liest"
        )
        normalised = [text.strip().casefold() for text in texts]
        assert len(normalised) == len(set(normalised)), (
            f"{path.name}: {element['id']!r} hat doppelte Optionen"
        )
        reserved = {"none", "n/a"} & set(normalised)
        assert not reserved, (
            f"{path.name}: {element['id']!r} nutzt ein reserviertes Wort"
            f" ({', '.join(sorted(reserved))})"
        )


def test_config_enables_blank_issues_and_links_the_security_policy() -> None:
    """``contact_links.url`` braucht eine absolute URL; ein relativer Pfad wird abgewiesen."""

    doc = _load(_CONFIG)
    assert doc.get("blank_issues_enabled") is True, (
        "Owner und Agenten legen weiterhin freie Prozess-Issues an"
    )
    links = doc.get("contact_links")
    assert isinstance(links, list) and links, "config.yml ohne Kontaktlink"
    for link in links:
        assert isinstance(link, dict), "Kontaktlink ist kein Mapping"
        for key in ("name", "url", "about"):
            assert str(link.get(key, "")).strip(), f"Kontaktlink ohne {key}"
        assert str(link["url"]).startswith("https://"), (
            f"Kontaktlink {link['name']!r}: keine absolute https-URL"
        )
    assert any("/security/policy" in link["url"] for link in links), (
        "der Weg für Sicherheitsmeldungen fehlt"
    )


def test_no_legacy_markdown_templates_remain() -> None:
    """Negativkontrolle: eine zurückkehrende ``.md``-Vorlage erschiene neben den Forms."""

    leftovers = sorted(path.name for path in _TEMPLATE_DIR.glob("*.md"))
    assert not leftovers, f"veraltete Markdown-Vorlagen: {', '.join(leftovers)}"


@pytest.mark.parametrize("path", _FORMS, ids=lambda p: p.name)
def test_angle_bracket_placeholders_stay_inside_code_spans(path: Path) -> None:
    """Ein Platzhalter ausserhalb eines Code-Spans verschwindet beim Rendern.

    Sichtbar wird das erst im fertigen Formular, und dort als *fehlender* Text –
    kein Parse-Fehler, keine Warnung. Geprueft werden die drei Felder, die
    GitHub als Markdown rendert.
    """

    offenders: list[str] = []
    for index, element in enumerate(_load(path)["body"]):
        attributes = element.get("attributes") or {}
        texts = [(key, attributes[key]) for key in _RENDERED_KEYS if key in attributes]
        # Auch die Beschriftung einer Checkbox-Option wird als Markdown gerendert.
        texts += [
            ("option", option["label"])
            for option in attributes.get("options") or []
            if isinstance(option, dict) and isinstance(option.get("label"), str)
        ]
        for key, value in texts:
            if not isinstance(value, str):
                continue
            bare = _CODE_SPAN_RE.sub("", value)
            offenders += [
                f"{path.name}[{index}].{key}: {match}"
                for match in _ANGLE_PLACEHOLDER_RE.findall(bare)
            ]

    assert not offenders, (
        "Platzhalter ausserhalb eines Code-Spans (GitHub entfernt sie beim Rendern):\n"
        + "\n".join(offenders)
    )


def test_feature_form_workflow_steps_match_the_stepper() -> None:
    """Drift-Wächter: die Auswahl führt genau die sechs Schritte der Schrittleiste.

    Ein umbenannter Schritt bliebe hier sonst still stehen und die Meldung
    zeigte auf einen Schritt, den die Anwendung nicht mehr kennt. Die Auswahl
    trägt zusätzlich „übergreifend" für alles, was keinem Schritt gehört.
    """

    from bgremover.i18n import configure_locale, current_locale
    from bgremover.stepper import WorkflowStep, step_label

    previous = current_locale()
    configure_locale("de")
    try:
        expected = [step_label(step) for step in WorkflowStep]
    finally:
        configure_locale(previous)

    body = _load(_FEATURE_FORM)["body"]
    element = next(item for item in body if item.get("id") == "workflow_step")
    options = element["attributes"]["options"]

    assert options[: len(expected)] == expected, (
        "Schrittnamen weichen von bgremover.stepper ab: "
        f"{options[: len(expected)]} statt {expected}"
    )
    assert options[len(expected) :] == ["übergreifend"], (
        "nach den sechs Schritten steht genau die übergreifende Auswahl"
    )
