import json
from pathlib import Path
from docx import Document

base = Path(__file__).resolve().parents[1]
meta_path = base / 'assets' / 'metadata.json'
meta = json.loads(meta_path.read_text(encoding='utf-8'))
meta['model_name'] = 'GPT-6'
meta['llm_interface'] = 'Codex desktop'
meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

doc_path = base / 'final_report.docx'
doc = Document(doc_path)
for p in doc.paragraphs:
    if p.text.startswith('Model (LLM):'):
        p.text = 'Model (LLM): GPT-6'
    elif p.text.startswith('LLM interface:'):
        p.text = 'LLM interface: Codex desktop'
doc.save(doc_path)
print('metadata corrected')
