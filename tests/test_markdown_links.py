"""Repository-wide Markdown link hygiene checks."""
from __future__ import annotations

from pathlib import Path

from tests._markdown_utils import (
    IMAGE_LINK_RE,
    MARKDOWN_LINK_RE,
    ROOT,
    anchor_slug,
    broken_anchor_links,
    heading_anchors,
    local_target,
    markdown_files,
    without_fenced_code,
)


def test_all_markdown_local_links_and_images_resolve() -> None:
    """Every local Markdown link/image target in the repository must exist."""

    missing: list[str] = []
    for path in markdown_files():
        text = without_fenced_code(path.read_text(encoding="utf-8"))
        for kind, pattern in (("link", MARKDOWN_LINK_RE), ("image", IMAGE_LINK_RE)):
            for match in pattern.finditer(text):
                target = local_target(match.group(1))
                if target is None:
                    continue
                resolved = (path.parent / target).resolve()
                if not resolved.exists():
                    missing.append(
                        f"{path.relative_to(ROOT)} {kind} target does not exist: {target}"
                    )

    assert not missing, "Broken local Markdown targets:\n" + "\n".join(missing)


def test_all_markdown_anchor_links_resolve() -> None:
    """Jeder dokumentinterne Anker muss auf eine echte Überschrift zeigen.

    Geprüft werden beide Zielformen: ``#abschnitt`` gegen die Überschriften
    derselben Datei und ``pfad.md#abschnitt`` gegen die der Zieldatei. Ohne
    diesen Wächter bleibt ein toter Sprungverweis unsichtbar (#964/#965) –
    die Pfadprüfung oben verwirft Fragmente.
    """

    broken = broken_anchor_links(markdown_files())

    assert not broken, "Broken Markdown anchors:\n" + "\n".join(broken)


def test_anchor_slug_covers_the_characters_that_surprise() -> None:
    """Die Slug-Regel an den Zeichen prüfen, an denen sie überrascht.

    Die Fälle stammen bis auf die Dublette aus echten Überschriften des
    Bestands; erwartet wird jeweils der Anker, den GitHub daraus bildet.
    """

    cases = {
        # Umlaute bleiben stehen (ANLEITUNG.md:76).
        "2. Die Programmoberfläche im Überblick": "2-die-programmoberfläche-im-überblick",
        # Halbgeviertstrich entfällt und hinterlässt den doppelten Bindestrich
        # (docs/i18n/en/ANLEITUNG.md:342 – der Anker aus #964).
        "7. Step 2 – Cut out": "7-step-2--cut-out",
        # "&" und typografische Anführungszeichen entfallen (ANLEITUNG.md:139).
        "Menüs „Bearbeiten\", „Ansicht\", „Projekt\" & „Extras\"":
            "menüs-bearbeiten-ansicht-projekt--extras",
        # Klammern entfallen ohne Ersatz (ANLEITUNG.md:267).
        "5. Die Werkzeugleiste (links)": "5-die-werkzeugleiste-links",
        # CJK bleibt erhalten, Vollbreite-Satzzeichen entfallen
        # (docs/i18n/zh/ANLEITUNG.md:44 bzw. :226).
        "1. BgRemover 能做什么？": "1-bgremover-能做什么",
        "5. 工具栏（左侧）": "5-工具栏左侧",
        # Kyrillisch bleibt erhalten (docs/i18n/uk/ANLEITUNG.md:220).
        "4. Крок 1 – Відкрити зображення": "4-крок-1--відкрити-зображення",
    }

    for heading, expected in cases.items():
        assert anchor_slug(heading) == expected, heading


def test_heading_anchors_ignore_code_blocks_and_number_duplicates() -> None:
    """Überschriften in Codeblöcken erzeugen keinen Anker; Dubletten zählen hoch.

    Für die Dublette gibt es im Bestand keinen Fall – sie wird deshalb als
    einzige an einem konstruierten Dokument geprüft.
    """

    document = "\n".join(
        [
            "# Titel",
            "",
            "```",
            "## Keine Überschrift",
            "```",
            "",
            "## Abschnitt",
            "text",
            "## Abschnitt",
            "## Abschnitt",
        ]
    )

    anchors = heading_anchors(document)

    assert "keine-überschrift" not in anchors
    assert anchors["titel"] == 1
    assert anchors["abschnitt"] == 7
    assert anchors["abschnitt-1"] == 9
    assert anchors["abschnitt-2"] == 10


def test_anchor_guard_checks_fragments_behind_a_file_path(tmp_path: Path) -> None:
    """Auch ``pfad.md#abschnitt`` wird gegen die Zieldatei geprüft.

    Diese Zielform kommt im Bestand derzeit nicht vor; ohne diesen Fall bliebe
    der Zweig ungeprüft, der das Ziel auflöst, Nicht-Markdown und fehlende
    Dateien überspringt und die Zieldatei in der Meldung nennt. Der Test ruft
    deshalb dieselbe Funktion auf wie der repo-weite Wächter.
    """

    (tmp_path / "ziel.md").write_text("# Erster Abschnitt\n", encoding="utf-8")
    (tmp_path / "kein-markdown.txt").write_text("# Erster Abschnitt\n", encoding="utf-8")
    source = tmp_path / "quelle.md"
    source.write_text(
        "[gut](ziel.md#erster-abschnitt), [kaputt](ziel.md#zweiter-abschnitt),\n"
        "[kein Markdown](kein-markdown.txt#egal), [fehlende Datei](fehlt.md#egal)\n"
        "und [extern](https://example.org/#egal)\n",
        encoding="utf-8",
    )

    assert broken_anchor_links([source], root=tmp_path) == [
        "quelle.md:1 anchor does not resolve in ziel.md: #zweiter-abschnitt"
    ]


def test_heading_anchors_resolve_collisions_against_assigned_anchors() -> None:
    """Eine Überschrift, deren Titel selbst auf ``-1`` endet, behält ihren Anker.

    github-slugger zählt je Basis-Slug hoch, prüft die Kollision aber gegen die
    bereits **vergebenen** Anker. Wer nur den Basiszähler führt, vergibt hier
    zweimal ``abschnitt-1``, verliert ``abschnitt-1-1`` und meldet einen auf
    GitHub gültigen Verweis als kaputt (Review-Befund zu PR #972).
    """

    anchors = heading_anchors("## Abschnitt\n## Abschnitt\n## Abschnitt-1\n")
    assert anchors == {"abschnitt": 1, "abschnitt-1": 2, "abschnitt-1-1": 3}

    # Auch andersherum: Die "-1"-Überschrift steht zuerst und belegt den Anker,
    # den die spätere Dublette sonst bekommen hätte.
    anchors = heading_anchors("## A-1\n## A\n## A\n## A\n")
    assert anchors == {"a-1": 1, "a": 2, "a-2": 3, "a-3": 4}
