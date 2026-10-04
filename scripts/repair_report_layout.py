from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_TAB_ALIGNMENT, WD_TAB_LEADER

BASE = Path(__file__).resolve().parents[1]
DOCX = BASE / "final_report.docx"

doc = Document(str(DOCX))

# Remove the floating VML picture inserted by the old COM routine. Its anchor
# is in the first column and can cover the title block when Word repaginates.
for p in doc.paragraphs:
    for child in list(p._p.xpath(".//w:pict | .//w:drawing")):
        parent = child.getparent()
        if parent is not None:
            parent.remove(child)

# Keep the compact results table and prose. The official template has no
# figure slot; omitting the optional figure preserves the original two-page
# flow and prevents the second column from spilling onto a third page.

# Fill the actual GitHub URL in VITA.
for p in doc.paragraphs:
    if p.text.startswith("GitHub:"):
        p.text = "GitHub: https://github.com/tonglynn/in6227-tabular-classification-skill"

# Keep the template's blue 9 pt footer styling and restore the original
# one-line left/right layout using a right-aligned tab stop.
footer_title = "IN6227 ASSIGNMENT 1, VARIANT 2"
footer_author = "LIN TONG, G2608825L"
for section in doc.sections:
    for footer in (section.footer, section.even_page_footer, section.first_page_footer):
        if not footer.paragraphs:
            continue
        p = footer.paragraphs[0]
        p.text = ""
        p.paragraph_format.tab_stops.clear_all()
        p.paragraph_format.tab_stops.add_tab_stop(
            Inches(6.25), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.SPACES
        )
        run = p.add_run(footer_title + "\t" + footer_author)
        run.font.name = "Times New Roman"
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(0x44, 0x72, 0xC4)
        for extra in footer.paragraphs[1:]:
            extra._element.getparent().remove(extra._element)

doc.save(str(DOCX))
print(DOCX)
