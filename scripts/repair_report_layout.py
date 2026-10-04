from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Inches

BASE = Path(__file__).resolve().parents[1]
DOCX = BASE / "final_report.docx"
IMAGE = BASE / "plots" / "confusion_matrix.png"

doc = Document(str(DOCX))

# Remove the floating VML picture inserted by the old COM routine. Its anchor
# is in the first column and can cover the title block when Word repaginates.
for p in doc.paragraphs:
    for child in list(p._p.xpath(".//w:pict | .//w:drawing")):
        parent = child.getparent()
        if parent is not None:
            parent.remove(child)

# Put the figure in the reserved empty paragraph immediately after Results text.
paras = doc.paragraphs
idx = next(i for i, p in enumerate(paras) if p.text.startswith("Test-set performance"))
results_para = paras[idx]
target = doc.paragraphs[idx + 1]
target.alignment = 0
target.add_run().add_picture(str(IMAGE), width=Inches(1.15))

# Fill the actual GitHub URL in VITA.
for p in doc.paragraphs:
    if p.text.startswith("GitHub:"):
        p.text = "GitHub: https://github.com/tonglynn/in6227-tabular-classification-skill"

# Keep the template's blue 9 pt footer styling and use a compact title that
# fits the original footer tab stops.
footer_title = "IN6227 ASSIGNMENT 1, VARIANT 2"
footer_author = "LIN TONG, G2608825L"
for section in doc.sections:
    for footer in (section.footer, section.even_page_footer, section.first_page_footer):
        if not footer.paragraphs:
            continue
        for p in footer.paragraphs:
            if p.text and "Assignment 1" in p.text:
                p.runs[0].text = footer_title
                for r in p.runs[1:]:
                    r.text = ""
            elif p.text and "LIN TONG" in p.text:
                p.runs[0].text = footer_author
                for r in p.runs[1:]:
                    r.text = ""

doc.save(str(DOCX))
print(DOCX)
