"""Pilot: build the paper PDF (two-column conference layout in the style of the project draft: numbered left-aligned headings,
abstract block, captions "Table N:" / "Figure N:", colour accents) from one Markdown-like source, paper/paper.md.
The same source feeds the Google Doc (scripts/pilot/to_doc_md.py).

Source format
  TITLE: ...                       AUTHORS: name | affiliation | email   (one author per line, after the AUTHORS: line)
  ABSTRACT: ...                    KEYWORDS: a, b, c
  # Heading                        numbered 1, 2, ...        ## Heading   numbered 1.1, 1.2, ...
  #* Heading                       unnumbered heading (appendices, acknowledgment)
  Hero: figs/name.png | caption    full-width figure under the abstract on page 1 (Figure 1)
  Table: caption                   followed by pipe-separated rows; the first row is the header
  Figure: figs/name.png | caption
  (1) text                         bullet (contributions);  RQn (...). text   research-question bullet
  [n] reference text               inside the References section
  *italic*  **bold**               inline
Roman-numeral cross references in the text (Table XI, Section VI-E) are converted to Arabic (Table 11, Section 6.5) when rendering.
Run with the scratch venv that has reportlab:  python scripts/pilot/build_paper.py
"""
from __future__ import annotations

import os
import pathlib
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BalancedColumns, BaseDocTemplate, CondPageBreak, Frame, FrameBreak, HRFlowable, Image, KeepTogether, NextPageTemplate, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "paper" / os.environ.get("PAPER_SRC", "paper.md")
OUT = ROOT / "paper" / os.environ.get("PAPER_OUT", "paper.pdf")
FONTS = pathlib.Path("C:/Windows/Fonts")

BLUE = colors.HexColor("#1F4E8C")
TEAL = colors.HexColor("#00666F")
TINT = colors.HexColor("#EEF3FA")
ZEBRA = colors.HexColor("#F4F7FB")


def register_fonts() -> tuple[str, str, str, str]:
    files = {"TNR": "times.ttf", "TNR-B": "timesbd.ttf", "TNR-I": "timesi.ttf", "TNR-BI": "timesbi.ttf"}
    if all((FONTS / f).exists() for f in files.values()):
        for name, f in files.items():
            pdfmetrics.registerFont(TTFont(name, str(FONTS / f)))
        pdfmetrics.registerFontFamily("TNR", normal="TNR", bold="TNR-B", italic="TNR-I", boldItalic="TNR-BI")
        return "TNR", "TNR-B", "TNR-I", "TNR-BI"
    return "Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic"


R, B, I, BI = register_fonts()  # noqa: E741
BODY = ParagraphStyle("body", fontName=R, fontSize=9.4, leading=11.6, alignment=TA_JUSTIFY, firstLineIndent=10, spaceAfter=3.8)
BODY0 = ParagraphStyle("body0", parent=BODY, firstLineIndent=0)
BUL = ParagraphStyle("bul", parent=BODY, firstLineIndent=0, leftIndent=12, bulletIndent=2, spaceAfter=1.8)
ABST = ParagraphStyle("abst", fontName=R, fontSize=9, leading=10.8, alignment=TA_JUSTIFY)
ABSH = ParagraphStyle("absh", fontName=B, fontSize=10, leading=12, alignment=TA_CENTER, textColor=colors.black, spaceAfter=2)
KEYW = ParagraphStyle("keyw", fontName=R, fontSize=8.8, leading=10.6, alignment=TA_CENTER, spaceBefore=3)
TITLE = ParagraphStyle("title", fontName=B, fontSize=18, leading=21.5, alignment=TA_CENTER, spaceAfter=7, textColor=colors.black)
AUTH = ParagraphStyle("auth", fontName=R, fontSize=10, leading=12, alignment=TA_CENTER)
AFF = ParagraphStyle("aff", fontName=I, fontSize=8.6, leading=10.2, alignment=TA_CENTER)
NOTE = ParagraphStyle("note", fontName=R, fontSize=8, leading=9.6, alignment=TA_CENTER, spaceBefore=1, spaceAfter=5)
H1 = ParagraphStyle("h1", fontName=B, fontSize=11.6, leading=13.6, alignment=TA_LEFT, spaceBefore=15, spaceAfter=1.5, textColor=colors.black, keepWithNext=1)
H2 = ParagraphStyle("h2", fontName=B, fontSize=9.8, leading=11.6, alignment=TA_LEFT, spaceBefore=9, spaceAfter=2.5, textColor=colors.black, keepWithNext=1)
EQ = ParagraphStyle("eq", fontName=I, fontSize=9.6, leading=12.4, alignment=TA_CENTER, spaceBefore=3, spaceAfter=6, textColor=colors.black)
CONT = ParagraphStyle("cont", parent=BODY, firstLineIndent=0, fontName=B, spaceBefore=4, spaceAfter=2, textColor=colors.black)
CAP_T = ParagraphStyle("capt", fontName=R, fontSize=8, leading=9.6, alignment=TA_JUSTIFY, spaceBefore=8, spaceAfter=3)
CAP_F = ParagraphStyle("capf", fontName=R, fontSize=8, leading=9.6, alignment=TA_JUSTIFY, spaceBefore=3, spaceAfter=9)
REF = ParagraphStyle("ref", fontName=R, fontSize=8, leading=9.4, alignment=TA_JUSTIFY, leftIndent=14, firstLineIndent=-14, spaceAfter=1.6)
CELL = ParagraphStyle("cell", fontName=R, fontSize=7.4, leading=8.6)
CELLH = ParagraphStyle("cellh", parent=CELL, fontName=B, textColor=colors.white)

MARGIN, GUTTER = 0.62 * inch, 0.22 * inch
PW, PH = letter
COLW = (PW - 2 * MARGIN - GUTTER) / 2
FULLW = PW - 2 * MARGIN
ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50}


def r2i(s: str) -> int:
    total = 0
    for a, b in zip(s, s[1:] + " "):
        v = ROMAN[a]
        total += -v if b != " " and ROMAN[b] > v else v
    return total


def arabize(t: str) -> str:
    """Table XI -> Table 11, Tables I and II -> Tables 1 and 2, Section VI-E -> Section 6.5, Sections IV and V -> Sections 4 and 5."""
    t = re.sub(r"\b(Tables?) ([IVXL]+)(?: and ([IVXL]+))?\b",
               lambda m: f"{m.group(1)} {r2i(m.group(2))}" + (f" and {r2i(m.group(3))}" if m.group(3) else ""), t)

    def sec(m: re.Match) -> str:
        one = str(r2i(m.group(2))) + (f".{ord(m.group(3)) - 64}" if m.group(3) else "")
        two = f" and {r2i(m.group(4))}" if m.group(4) else ""
        return f"{m.group(1)} {one}{two}"
    return re.sub(r"\b(Sections?) ([IVX]+)(?:-([A-F]))?(?: and ([IVX]+))?\b", sec, t)


def inline(text: str) -> str:
    t = arabize(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"\b([exy])_(1|T|t)\b", r"\1<sub>\2</sub>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"<i>\1</i>", t)
    return re.sub(r"`(.+?)`", r"<font face='Courier' size='8'>\1</font>", t)


def parse(md: str) -> dict:
    doc = {"title": "", "authors": [], "abstract": "", "keywords": "", "hero": None, "body": []}
    lines = md.splitlines()
    i = 0
    sec, sub, tab, fig = 0, 0, 0, 0
    mode = None
    while i < len(lines):
        ln = lines[i].rstrip()
        i += 1
        if not ln.strip():
            continue
        if ln.startswith("TITLE:"):
            doc["title"] = ln[6:].strip()
        elif ln.startswith("AUTHORS:"):
            while i < len(lines) and "|" in lines[i]:
                doc["authors"].append([p.strip() for p in lines[i].split("|")])
                i += 1
        elif ln.startswith("ABSTRACT:"):
            doc["abstract"] = ln[9:].strip()
        elif ln.startswith("KEYWORDS:"):
            doc["keywords"] = ln[9:].strip()
        elif ln.startswith("Hero:"):
            fig += 1
            path, cap = [p.strip() for p in ln[5:].split("|", 1)]
            doc["hero"] = (fig, path, cap)
        elif ln.startswith("#* "):
            doc["body"].append(("h1", ln[3:]))
            mode = "plain"
        elif ln.startswith("## "):
            sub += 1
            doc["body"].append(("h2", f"{sec}.{sub} {ln[3:]}"))
        elif ln.startswith("# "):
            sec, sub = sec + 1, 0
            mode = "refs" if ln[2:].strip().lower() == "references" else None
            doc["body"].append(("h1", ln[2:] if mode == "refs" else f"{sec} {ln[2:]}"))
        elif ln.startswith("Table:"):
            tab += 1
            rows = []
            while i < len(lines) and "|" in lines[i]:
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            doc["body"].append(("table", tab, re.sub(r"^TABLE [IVXL]+\.\s*", "", ln[6:].strip()), rows))
        elif ln.startswith("Figure:"):
            fig += 1
            path, cap = [p.strip() for p in ln[7:].split("|", 1)]
            doc["body"].append(("figure", fig, path, cap))
        elif mode == "refs" and re.match(r"\[\d+\]", ln):
            doc["body"].append(("ref", ln))
        elif sec == 1 and re.match(r"^\(\d\) ", ln):
            doc["body"].append(("bullet", ln[4:]))
        elif sec == 1 and re.match(r"^RQ\d \(", ln):
            m = re.match(r"^(RQ\d \([^)]*\)\.)(.*)$", ln)
            doc["body"].append(("bullet", f"**{m.group(1)}**{m.group(2)}" if m else ln))
        elif ln.strip() == "Contributions:":
            doc["body"].append(("cont", "Contributions"))
        elif ln.startswith("Precision = "):
            doc["body"].append(("eq", ln))
        else:
            doc["body"].append(("p", ln))
    return doc


def table_flow(num: int, cap: str, rows_: list) -> KeepTogether:
    ncol = len(rows_[0])
    w = [COLW * 0.34] + [COLW * 0.66 / (ncol - 1)] * (ncol - 1) if ncol > 2 else ([COLW * 0.30, COLW * 0.70] if rows_[0][0] == "Term" else [COLW * 0.55, COLW * 0.45])
    small = ncol >= 6
    cs = ParagraphStyle("c2", parent=CELL, fontSize=6.4, leading=7.6) if small else CELL
    ch = ParagraphStyle("ch2", parent=cs, fontName=B, textColor=colors.white)

    def fmt(c: str) -> str:
        t = inline(c)
        if re.match(r"[+-]?\d", c) and " [" in c:
            head, tail = t.split(" [", 1)
            return head + "<br/><font size=5.9>[" + tail + "</font>"
        return t

    data = [[Paragraph(fmt(c) if r else inline(c), ch if r == 0 else cs) for c in row] for r, row in enumerate(rows_)]
    tb = Table(data, colWidths=w, repeatRows=1)
    style = [("BACKGROUND", (0, 0), (-1, 0), BLUE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#c9d3e0")), ("LINEBELOW", (0, -1), (-1, -1), 0.8, BLUE),
             ("TOPPADDING", (0, 0), (-1, -1), 1.4), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.4),
             ("LEFTPADDING", (0, 0), (-1, -1), 2.5), ("RIGHTPADDING", (0, 0), (-1, -1), 2.5)]
    for k in range(2, len(rows_), 2):
        style.append(("BACKGROUND", (0, k), (-1, k), ZEBRA))
    tb.setStyle(TableStyle(style))
    capp = Paragraph(f"<b>Table {num}:</b> {inline(cap)}", CAP_T)
    if tb.wrap(COLW, 10000)[1] > 2.3 * inch:
        return [CondPageBreak(1.25 * inch), capp, tb, Spacer(1, 6)]
    return KeepTogether([capp, tb, Spacer(1, 6)])


def figure_flow(num: int, path: str, cap: str, width: float) -> KeepTogether:
    p = ROOT / "paper" / path
    iw, ih = ImageReader(str(p)).getSize()
    img = Image(str(p), width=width, height=width * ih / iw)
    return KeepTogether([img, Paragraph(f"<b>Figure {num}:</b> {inline(cap)}", CAP_F)])


def build(doc: dict) -> None:
    head: list = [Paragraph(inline(doc["title"]), TITLE)]
    n = len(doc["authors"])
    cols = min(n, 3)
    cells = []
    for name, aff, mail in doc["authors"]:
        cells.append([Paragraph(f"<b>{inline(name)}</b>", AUTH), Paragraph(inline(aff), AFF), Paragraph(inline(mail), AFF)])
    rows = [cells[k:k + cols] for k in range(0, n, cols)]
    for r in rows:
        while len(r) < cols:
            r.append("")
    t = Table([[c for c in r] for r in rows], colWidths=[FULLW / cols] * cols)
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    head += [t, Paragraph("* All authors contributed equally to this work.", NOTE)]
    abox = Table([[[Paragraph("Abstract", ABSH), Paragraph(inline(doc["abstract"]), ABST)]]], colWidths=[FULLW * 0.9])
    abox.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), TINT), ("BOX", (0, 0), (-1, -1), 0.8, BLUE),
                              ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                              ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    head += [abox]
    if doc["keywords"]:
        head.append(Paragraph("<b>Keywords:</b> " + inline(doc["keywords"]), KEYW))
    if doc["hero"]:
        num, path, cap = doc["hero"]
        ip = ROOT / "paper" / path
        iw, ih = ImageReader(str(ip)).getSize()
        head += [Spacer(1, 5), Image(str(ip), width=FULLW, height=FULLW * ih / iw),
                 Paragraph(f"<b>Figure {num}:</b> {inline(cap)}", CAP_F)]
    head_h = sum(f.wrap(FULLW, 10000)[1] + getattr(f, "style", ParagraphStyle("x")).spaceBefore + getattr(f, "style", ParagraphStyle("x")).spaceAfter
                 if hasattr(f, "style") else f.wrap(FULLW, 10000)[1] for f in head) + 14

    story: list = list(head) + [FrameBreak()]
    first_para = True
    for item in doc["body"]:
        kind = item[0]
        if kind == "h1":
            story.append(Paragraph(inline(item[1]), H1))
            story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#9db7d8"), spaceBefore=0, spaceAfter=4))
            first_para = True
        elif kind == "h2":
            story.append(Paragraph(inline(item[1]), H2))
            first_para = True
        elif kind == "p":
            story.append(Paragraph(inline(item[1]), BODY0 if first_para else BODY))
            first_para = False
        elif kind == "eq":
            parts = [x.strip() for x in item[1].rstrip(",").split(", ")]
            story.append(Paragraph("<br/>".join(inline(x) for x in parts), EQ))
            first_para = False
        elif kind == "cont":
            story.append(Paragraph(inline(item[1]) + ".", CONT))
        elif kind == "bullet":
            story.append(Paragraph(inline(item[1]), BUL, bulletText="\u2022"))
        elif kind == "ref":
            story.append(Paragraph(inline(item[1]), REF))
        elif kind == "table":
            tf = table_flow(item[1], item[2], item[3])
            story.extend(tf) if isinstance(tf, list) else story.append(tf)
        elif kind == "figure":
            story.append(figure_flow(item[1], item[2], item[3], COLW))

    cut = next((k for k, f in enumerate(story) if isinstance(f, Paragraph) and f.getPlainText().startswith("Author Contributions")), None)
    if cut is not None:
        tail = story[cut:]
        story = story[:cut] + [NextPageTemplate("last"), PageBreak(),
                               BalancedColumns(tail, nCols=2, needed=60, leftPadding=0, innerPadding=GUTTER, rightPadding=0, topPadding=0, bottomPadding=0,
                                               endSlack=0.05, vLinesStrokeColor=colors.HexColor("#c9d3e0"), vLinesStrokeWidth=0.4)]

    def footer(canvas, d):
        canvas.saveState()
        canvas.setFont(R, 8)
        canvas.setFillColor(colors.HexColor("#555555"))
        canvas.drawCentredString(PW / 2, 0.38 * inch, str(d.page))
        canvas.restoreState()

    top = head_h
    first_frames = [Frame(MARGIN, PH - MARGIN - top, FULLW, top, id="head", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0),
                    Frame(MARGIN, MARGIN, COLW, PH - 2 * MARGIN - top, id="c1", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0),
                    Frame(MARGIN + COLW + GUTTER, MARGIN, COLW, PH - 2 * MARGIN - top, id="c2", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)]
    later_frames = [Frame(MARGIN, MARGIN, COLW, PH - 2 * MARGIN, id="l1", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0),
                    Frame(MARGIN + COLW + GUTTER, MARGIN, COLW, PH - 2 * MARGIN, id="l2", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)]
    d = BaseDocTemplate(str(OUT), pagesize=letter, title=doc["title"], author=", ".join(a[0] for a in doc["authors"]),
                        leftMargin=MARGIN, rightMargin=MARGIN, topMargin=MARGIN, bottomMargin=MARGIN)
    d.addPageTemplates([PageTemplate(id="first", frames=first_frames, onPage=footer, autoNextPageTemplate="later"),
                        PageTemplate(id="later", frames=later_frames, onPage=footer),
                        PageTemplate(id="last", frames=[Frame(MARGIN, MARGIN, FULLW, PH - 2 * MARGIN, id="full", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)], onPage=footer)])
    d.build(story)


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    build(parse(SRC.read_text(encoding="utf-8")))
    print("wrote", OUT)
