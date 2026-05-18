#!/usr/bin/env python3
"""Erzeugt ``ANLEITUNG.pdf`` reproduzierbar aus ``ANLEITUNG.md``.

Reine Python-Loesung (Markdown -> HTML -> PDF via ``fpdf2``), damit die
PDF ohne LaTeX/Pandoc/Systemkonverter aus der Markdown-Quelle gebaut
werden kann. Die DejaVu-Schriften werden eingebettet, damit Umlaute,
Box-Zeichnung, Pfeile und das ⌘-Zeichen korrekt erscheinen. Emoji, die
DejaVu nicht enthaelt, werden vor dem Satz durch lesbare Platzhalter
ersetzt (sonst Tofu-Kaesten).

Aufruf:
  python scripts/generate_anleitung_pdf.py            # ANLEITUNG.md -> ANLEITUNG.pdf
  python scripts/generate_anleitung_pdf.py --in DOC.md --out DOC.pdf

Abhaengigkeiten: pip install -e ".[docs]"
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import markdown
from fontTools.ttLib import TTFont
from fpdf import FPDF
from fpdf.fonts import FontFace

ROOT = Path(__file__).resolve().parent.parent

# DejaVu liegt auf Debian/Ubuntu unter diesem Pfad (Paket: fonts-dejavu-core).
# Die Oblique-Varianten stecken im optionalen fonts-dejavu-extra; fehlen
# sie, wird auf die aufrechte Variante zurueckgegriffen (kein Schraegsatz,
# aber kein Abbruch).
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
_SANS = FONT_DIR / "DejaVuSans.ttf"
_SANS_B = FONT_DIR / "DejaVuSans-Bold.ttf"
_SANS_I = FONT_DIR / "DejaVuSans-Oblique.ttf"
_SANS_BI = FONT_DIR / "DejaVuSans-BoldOblique.ttf"
_MONO = FONT_DIR / "DejaVuSansMono.ttf"
_MONO_B = FONT_DIR / "DejaVuSansMono-Bold.ttf"


def _font_files() -> dict[tuple[str, str], Path]:
    """Mappt (Familie, Stil) auf vorhandene TTF; Oblique faellt auf
    die aufrechte/fette Variante zurueck, falls nicht installiert."""
    return {
        ("dejavu", ""): _SANS,
        ("dejavu", "B"): _SANS_B,
        ("dejavu", "I"): _SANS_I if _SANS_I.exists() else _SANS,
        ("dejavu", "BI"): _SANS_BI if _SANS_BI.exists() else _SANS_B,
        ("dejavumono", ""): _MONO,
        ("dejavumono", "B"): _MONO_B,
    }


FONT_FILES = _font_files()

# Bewusste Ersetzungen fuer haeufige Deko-Emoji; alle uebrigen, von der
# Schrift nicht abgedeckten Zeichen werden entfernt (Fallback "").
EMOJI_FALLBACK = {
    "⬤": "●",   # grosser Kreis -> normaler schwarzer Kreis
    "■": "■",
    "✓": "✓",
    "✗": "✗",
}


def _covered_codepoints() -> set[int]:
    """Vereinigt die cmaps von DejaVu Sans + Mono."""
    cps: set[int] = set()
    for key in (("dejavu", ""), ("dejavumono", "")):
        tt = TTFont(str(FONT_FILES[key]), fontNumber=0)
        for table in tt["cmap"].tables:
            cps.update(table.cmap.keys())
        tt.close()
    return cps


def _sanitize(text: str, covered: set[int]) -> str:
    """Ersetzt von der Schrift nicht darstellbare Zeichen."""
    out = []
    for ch in text:
        if ord(ch) < 0x80 or ord(ch) in covered:
            out.append(ch)
        else:
            out.append(EMOJI_FALLBACK.get(ch, ""))
    return "".join(out)


# Wird ueber DEFAULT_TAG_STYLES gemergt. FontFace fuer Block-Tags
# (h1.., pre) behaelt die Default-Abstaende von fpdf2 bei.
TAG_STYLES = {
    "h1": FontFace(family="dejavu", size_pt=20),
    "h2": FontFace(family="dejavu", size_pt=15),
    "h3": FontFace(family="dejavu", size_pt=12),
    "h4": FontFace(family="dejavu", size_pt=11),
    "code": FontFace(family="dejavumono"),
    "pre": FontFace(family="dejavumono"),
}


def _flatten_table_cells(html: str) -> str:
    """fpdf2 erlaubt in ``<td>/<th>`` keine verschachtelten Tags. Inhalt
    der Zellen daher auf reinen Text reduzieren (Fett/Code/Links in
    Tabellen verlieren ihre Auszeichnung, der Text bleibt erhalten)."""
    def repl(m: re.Match[str]) -> str:
        tag, inner = m.group(1), m.group(2)
        return f"<{tag}>{re.sub(r'<[^>]+>', '', inner)}</{tag}>"

    return re.sub(r"<(td|th)\b[^>]*>(.*?)</\1>", repl, html, flags=re.S)


def build_pdf(md_path: Path, pdf_path: Path) -> None:
    covered = _covered_codepoints()
    raw = md_path.read_text(encoding="utf-8")
    raw = _sanitize(raw, covered)

    html = markdown.markdown(
        raw,
        extensions=["extra", "sane_lists", "toc"],
        output_format="html",
    )
    # Doku-interne Sprungmarken (#anchor) entfernen: fpdf2 legt fuer
    # Heading-IDs keine Named Destinations an -> sonst Abbruch. Der
    # Inhaltsverzeichnis-Text bleibt als reiner Text erhalten.
    html = re.sub(
        r'<a\b[^>]*\bhref="#[^"]*"[^>]*>(.*?)</a>', r"\1", html, flags=re.S)
    html = _flatten_table_cells(html)
    # fpdf2 zeichnet Zellraender nur bei gesetztem border-Attribut.
    html = html.replace("<table>", '<table border="1">')

    pdf = FPDF(format="A4")
    pdf.set_margins(18, 16, 18)
    pdf.set_auto_page_break(auto=True, margin=16)
    for (family, style), fpath in FONT_FILES.items():
        if not fpath.exists():
            sys.exit(
                f"Schriftdatei fehlt: {fpath}\n"
                "Bitte das Paket 'fonts-dejavu-core' installieren."
            )
        pdf.add_font(family, style=style, fname=str(fpath))
    pdf.set_font("dejavu", size=10)
    pdf.add_page()
    pdf.write_html(
        html,
        font_family="dejavu",
        tag_styles=TAG_STYLES,
        table_line_separators=True,
    )
    pdf.output(str(pdf_path))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--in", dest="src", default=str(ROOT / "ANLEITUNG.md"),
        help="Markdown-Quelle (Default: ANLEITUNG.md)")
    parser.add_argument(
        "--out", dest="dst", default=str(ROOT / "ANLEITUNG.pdf"),
        help="Ziel-PDF (Default: ANLEITUNG.pdf)")
    args = parser.parse_args(argv)

    src = Path(args.src)
    if not src.is_file():
        sys.exit(f"Quelle nicht gefunden: {src}")
    dst = Path(args.dst)
    build_pdf(src, dst)
    print(f"PDF geschrieben: {dst} ({dst.stat().st_size} Bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
