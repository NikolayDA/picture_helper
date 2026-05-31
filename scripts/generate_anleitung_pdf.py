#!/usr/bin/env python3
"""Erzeugt ``ANLEITUNG.pdf`` reproduzierbar aus ``ANLEITUNG.md``.

Markdown -> HTML (python-markdown) -> PDF (WeasyPrint) mit einem an
GitHub angelehnten Stylesheet, damit Ueberschriften, Tabellen, Listen,
Zitate und Code-Bloecke sauber gesetzt werden. Geeignete Systemschriften
werden eingebettet (Umlaute, Box-Zeichnung, Pfeile, ⌘); nicht enthaltene
Emoji werden vorab durch lesbare Platzhalter ersetzt.

Aufruf:
  python scripts/generate_anleitung_pdf.py            # ANLEITUNG.md -> ANLEITUNG.pdf
  python scripts/generate_anleitung_pdf.py --in DOC.md --out DOC.pdf

Abhaengigkeiten: pip install -e ".[docs]"
Zusaetzlich noetig: DejaVu-Schriften (Linux-System-Paket
fonts-dejavu-core) oder die macOS-Systemschriften Arial/Courier New und
die WeasyPrint-Systembibliotheken (Pango/Cairo/GDK-Pixbuf).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import markdown
from fontTools.ttLib import TTFont
from weasyprint import HTML

ROOT = Path(__file__).resolve().parent.parent

# DejaVu liegt auf Debian/Ubuntu unter diesem Pfad. Auf macOS verwenden
# wir die mitgelieferten Arial-/Courier-New-Schriften als Fallback.
DEJAVU_DIR = Path("/usr/share/fonts/truetype/dejavu")
MAC_FONT_DIR = Path("/System/Library/Fonts/Supplemental")
FONT_SETS = (
    (
        DEJAVU_DIR / "DejaVuSans.ttf",
        DEJAVU_DIR / "DejaVuSans-Bold.ttf",
        DEJAVU_DIR / "DejaVuSansMono.ttf",
        DEJAVU_DIR / "DejaVuSansMono-Bold.ttf",
    ),
    (
        MAC_FONT_DIR / "Arial.ttf",
        MAC_FONT_DIR / "Arial Bold.ttf",
        MAC_FONT_DIR / "Courier New.ttf",
        MAC_FONT_DIR / "Courier New Bold.ttf",
    ),
)


def _select_font_set() -> tuple[Path, Path, Path, Path]:
    for font_set in FONT_SETS:
        if all(path.is_file() for path in font_set):
            return font_set
    return FONT_SETS[0]


SANS, SANS_BOLD, MONO, MONO_BOLD = _select_font_set()

# Bewusste Ersetzungen; alle uebrigen, von der Schrift nicht abgedeckten
# Zeichen (v. a. Deko-Emoji) werden entfernt (Fallback "").
EMOJI_FALLBACK = {"⬤": "●"}


def _covered_codepoints() -> set[int]:
    """Vereinigt die cmaps der eingebetteten Sans- und Mono-Schriften."""
    cps: set[int] = set()
    for path in (SANS, MONO):
        tt = TTFont(str(path), fontNumber=0)
        for table in tt["cmap"].tables:
            cps.update(table.cmap.keys())
        tt.close()
    return cps


def _sanitize(text: str, covered: set[int]) -> str:
    out = []
    for ch in text:
        if ord(ch) < 0x80 or ord(ch) in covered:
            out.append(ch)
        else:
            out.append(EMOJI_FALLBACK.get(ch, ""))
    return "".join(out)


def _css() -> str:
    """An GitHub-Markdown angelehntes Stylesheet (Druck/A4)."""
    return f"""
@font-face {{ font-family:'BgRemover Sans'; src:url('file://{SANS}'); }}
@font-face {{ font-family:'BgRemover Sans'; font-weight:bold;
              src:url('file://{SANS_BOLD}'); }}
@font-face {{ font-family:'BgRemover Sans Mono'; src:url('file://{MONO}'); }}
@font-face {{ font-family:'BgRemover Sans Mono'; font-weight:bold;
              src:url('file://{MONO_BOLD}'); }}

@page {{
  size: A4;
  margin: 18mm 16mm;
  @bottom-center {{
    content: counter(page) " / " counter(pages);
    font-family:'BgRemover Sans'; font-size: 8pt; color:#8b949e;
  }}
}}

body {{
  font-family:'BgRemover Sans', sans-serif;
  font-size: 10pt; line-height: 1.55; color:#1f2328;
}}
a {{ color:#0969da; text-decoration:none; }}

h1, h2, h3, h4, h5, h6 {{
  font-weight: bold; line-height: 1.25;
  margin: 1.3em 0 0.55em; break-after: avoid;
}}
h1 {{ font-size: 1.9em; color:#0b3d6b;
      border-bottom:2px solid #0969da; padding-bottom:.25em; }}
h2 {{ font-size: 1.45em; border-bottom:1px solid #d0d7de;
      padding-bottom:.25em; }}
h3 {{ font-size: 1.2em; }}
h4 {{ font-size: 1.0em; }}

p {{ margin: 0 0 0.85em; }}
ul, ol {{ margin: 0 0 0.85em; padding-left: 2em; }}
li {{ margin: 0.2em 0; }}
li::marker {{ color:#57606a; }}

blockquote {{
  margin: 0 0 0.85em; padding: 0.4em 1em;
  color:#3a4a5c; background:#ddf4ff;
  border-left: 4px solid #0969da; border-radius: 0 4px 4px 0;
}}
blockquote p {{ margin: 0.3em 0; }}

code, kbd, samp {{
  font-family:'BgRemover Sans Mono', monospace; font-size: 0.88em;
}}
:not(pre) > code {{
  background:#eaeef2; padding:.15em .35em; border-radius:4px;
}}
pre {{
  font-family:'BgRemover Sans Mono', monospace; font-size: 8pt;
  line-height: 1.35; background:#f6f8fa; color:#1f2328;
  padding: 12px 14px; border:1px solid #d0d7de; border-radius:6px;
  white-space: pre; overflow: hidden; break-inside: avoid;
}}
pre code {{ background:none; padding:0; font-size: inherit; }}

table {{
  border-collapse: collapse; width: 100%;
  margin: 0 0 1em; font-size: 0.95em; break-inside: avoid;
}}
th, td {{
  border:1px solid #d0d7de; padding: 6px 11px;
  text-align: left; vertical-align: top;
}}
th {{ background:#f1f3f5; font-weight: bold; }}
tbody tr:nth-child(even) {{ background:#f6f8fa; }}

hr {{ border:0; border-top:1px solid #d0d7de; margin: 1.4em 0; }}
img {{ max-width: 100%; }}
"""


def build_pdf(md_path: Path, pdf_path: Path) -> None:
    for fp in (SANS, SANS_BOLD, MONO, MONO_BOLD):
        if not fp.exists():
            sys.exit(
                f"Schriftdatei fehlt: {fp}\n"
                "Bitte 'fonts-dejavu-core' installieren oder unter macOS "
                "die Systemschriften Arial/Courier New pruefen."
            )
    covered = _covered_codepoints()
    raw = _sanitize(md_path.read_text(encoding="utf-8"), covered)

    body = markdown.markdown(
        raw,
        extensions=["extra", "sane_lists", "toc"],
        output_format="html",
    )
    document = (
        "<!DOCTYPE html><html lang='de'><head><meta charset='utf-8'>"
        f"<style>{_css()}</style></head><body>{body}</body></html>"
    )
    HTML(string=document, base_url=str(ROOT)).write_pdf(str(pdf_path))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Erzeugt ANLEITUNG.pdf aus ANLEITUNG.md.")
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
