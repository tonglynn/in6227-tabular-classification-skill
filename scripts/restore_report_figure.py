"""Insert an inline Results figure without inheriting fixed heading spacing."""
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

base = Path(__file__).resolve().parents[1]
path = base / 'final_report.docx'
doc = Document(path)
discussion = next(p for p in doc.paragraphs if p.text.strip() == 'DISCUSSION')
if not doc.inline_shapes:
    figure = discussion.insert_paragraph_before()
    figure.style = doc.styles['Normal']
    fmt = figure.paragraph_format
    fmt.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fmt.line_spacing = 1.0
    fmt.space_before = Pt(4)
    fmt.space_after = Pt(3)
    fmt.left_indent = Pt(0)
    fmt.right_indent = Pt(0)
    fmt.first_line_indent = Pt(0)
    fmt.keep_with_next = True
    fmt.keep_together = True
    fmt.page_break_before = False
    figure.add_run().add_picture(str(base / 'plots' / 'confusion_matrix.png'), width=Inches(2.35))
    caption = discussion.insert_paragraph_before('Figure 1. Test-set confusion matrix.')
    caption.style = doc.styles['Normal']
    caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption.paragraph_format.line_spacing = 1.0
    caption.paragraph_format.space_after = Pt(6)
    caption.paragraph_format.keep_with_next = False
    for run in caption.runs:
        run.font.name = 'Times New Roman'
        run.font.size = Pt(9)
doc.save(path)
print('Inline figure inserted with proportional dimensions and automatic line height.')
