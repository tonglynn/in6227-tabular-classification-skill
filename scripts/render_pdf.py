#!/usr/bin/env python3
"""Render report.md to a compact PDF (≤ 2 pages) using reportlab.

Parses a subset of Markdown (headings, bold, bullet lists, pipe tables,
images) and lays them out with small margins and 8-pt body text so the
entire report fits in two pages.
"""
import argparse
import os
import re
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, KeepTogether,
)
from reportlab.lib.enums import TA_LEFT


def md_inline(text: str) -> str:
    """Convert inline markdown to reportlab HTML subset."""
    # Bold
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # Inline code
    text = re.sub(r"`(.+?)`", r'<font name="Courier">\1</font>', text)
    return text


def parse_markdown(md_text: str, plots_dir: str):
    """Yield reportlab flowables from markdown text.

    Uses Times-Roman 10pt body text to align with the official report
    template (IN6227-Reports-Template.doc) which specifies Times New
    Roman 10-point font.
    """
    # Official template: Times New Roman 10pt. reportlab's "Times-Roman"
    # is the metric-compatible built-in equivalent.
    FONT = "Times-Roman"
    FONT_BOLD = "Times-Bold"
    FONT_ITALIC = "Times-Italic"

    h1 = ParagraphStyle("H1", fontName=FONT_BOLD, fontSize=10, leading=12,
                        spaceAfter=3, spaceBefore=2)
    h2 = ParagraphStyle("H2", fontName=FONT_BOLD, fontSize=10, leading=12,
                        spaceAfter=2, spaceBefore=4)
    h3 = ParagraphStyle("H3", fontName=FONT_BOLD, fontSize=10, leading=12,
                        spaceAfter=1, spaceBefore=3)
    body = ParagraphStyle("Body", fontName=FONT, fontSize=10, leading=12,
                          spaceAfter=2, alignment=TA_LEFT)
    bullet = ParagraphStyle("Bullet", parent=body, leftIndent=12,
                            bulletIndent=2, spaceAfter=1)

    flowables = []
    lines = md_text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        # Blank line
        if not line.strip():
            i += 1
            continue

        # Horizontal rule
        if line.strip() == "---":
            flowables.append(Spacer(1, 3))
            i += 1
            continue

        # H1
        if line.startswith("# ") and not line.startswith("## "):
            flowables.append(Paragraph(md_inline(line[2:]), h1))
            i += 1
            continue

        # H3 (check before H2 since ### starts with ##)
        if line.startswith("### "):
            flowables.append(Paragraph(md_inline(line[4:]), h3))
            i += 1
            continue

        # H2
        if line.startswith("## "):
            flowables.append(Paragraph(md_inline(line[3:]), h2))
            i += 1
            continue

        # Image: ![alt](path)
        img_match = re.match(r"!\[(.+?)\]\((.+?)\)", line)
        if img_match:
            img_path = img_match.group(2)
            # Resolve relative to plots_dir
            if not os.path.isabs(img_path):
                img_path = os.path.join(plots_dir, os.path.basename(img_path))
            if os.path.exists(img_path):
                try:
                    img = RLImage(img_path, width=2.0 * inch, height=1.6 * inch)
                    flowables.append(img)
                except Exception:
                    pass
            i += 1
            continue

        # Table
        if line.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].startswith("|"):
                table_lines.append(lines[i])
                i += 1
            flowables.append(build_table(table_lines, body))
            flowables.append(Spacer(1, 2))
            continue

        # Bullet list
        if line.startswith("- "):
            while i < len(lines) and lines[i].strip().startswith("- "):
                txt = lines[i].strip()[2:]
                flowables.append(Paragraph(f"• {md_inline(txt)}", bullet))
                i += 1
            continue

        # Regular paragraph (may span multiple non-empty lines)
        para_lines = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not lines[i].startswith(("#", "|", "- ", "!", "---")):
            para_lines.append(lines[i].rstrip())
            i += 1
        para_text = " ".join(para_lines)
        flowables.append(Paragraph(md_inline(para_text), body))

    return flowables


def build_table(table_lines, style):
    """Build a reportlab Table from markdown pipe-table lines."""
    rows = []
    for idx, line in enumerate(table_lines):
        # Skip separator row (|---|---|)
        if re.match(r"^\|[\s\-:|]+\|$", line.strip()):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append(cells)

    if not rows:
        return Spacer(1, 0)

    # Create paragraph-wrapped cells for text wrapping
    cell_style = ParagraphStyle("Cell", parent=style, fontName="Times-Roman",
                                 fontSize=8, leading=10)
    data = []
    for r_idx, row in enumerate(rows):
        data.append([Paragraph(md_inline(c), cell_style) for c in row])

    # Estimate column widths based on content
    n_cols = len(data[0]) if data else 1
    avail = A4[0] - 2 * 15 * mm  # margins
    if n_cols <= 2:
        col_widths = [avail * 0.3, avail * 0.7]
    else:
        # First column narrower (model name), rest equal
        first_w = avail * 0.2
        rest_w = (avail - first_w) / (n_cols - 1)
        col_widths = [first_w] + [rest_w] * (n_cols - 1)
    col_widths = col_widths[:n_cols]

    tbl = Table(data, colWidths=col_widths)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4C72B0")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Times-Roman"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#E8EEF5")]),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
    ]))
    return tbl


def main():
    ap = argparse.ArgumentParser(description="Render report.md to PDF (≤2 pages).")
    ap.add_argument("--input", default="report.md", help="Input markdown")
    ap.add_argument("--out", default="report.pdf", help="Output PDF")
    ap.add_argument("--plots-dir", default="plots", help="Directory for plot images")
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as f:
        md_text = f.read()

    # Resolve plots_dir relative to the markdown file's directory
    md_dir = os.path.dirname(os.path.abspath(args.input))
    plots_dir = args.plots_dir
    if not os.path.isabs(plots_dir):
        plots_dir = os.path.join(md_dir, plots_dir)

    flowables = parse_markdown(md_text, plots_dir)

    # Official template header: "IN6227 DATA MINING 2023, WKWSCI"
    header_style = ParagraphStyle(
        "Header", fontName="Times-Roman", fontSize=8, leading=10,
        alignment=TA_LEFT, textColor=colors.grey,
    )
    header_para = Paragraph("IN6227 DATA MINING 2023, WKWSCI", header_style)

    def on_page(canvas, doc):
        canvas.saveState()
        canvas.setFont("Times-Roman", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(15 * mm, A4[1] - 8 * mm, "IN6227 DATA MINING 2023, WKWSCI")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        args.out, pagesize=A4,
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=15 * mm, bottomMargin=12 * mm,
        title="IN6227 Assignment 1 Report",
    )
    doc.build(flowables, onFirstPage=on_page, onLaterPages=on_page)

    # Verify page count
    try:
        from pypdf import PdfReader
        reader = PdfReader(args.out)
        n_pages = len(reader.pages)
    except Exception:
        n_pages = "?"

    size_kb = os.path.getsize(args.out) / 1024
    print(f"[render_pdf] Wrote {args.out} ({size_kb:.0f} KB, {n_pages} page(s))")
    if isinstance(n_pages, int) and n_pages > 2:
        print(f"[render_pdf] WARNING: PDF has {n_pages} pages — exceeds 2-page limit!")
    elif isinstance(n_pages, int):
        print(f"[render_pdf] OK: {n_pages} page(s) — within 2-page limit.")


if __name__ == "__main__":
    main()
