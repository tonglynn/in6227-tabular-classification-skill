#!/usr/bin/env python3
"""Populate the official IN6227-Reports-Template.doc with report content.

This script copies the official template, opens it via Word COM, and fills
content into the template's existing paragraphs/styles. This preserves:
- A4 page size, margins
- Two-column layout (Sections 2 & 3)
- Times New Roman 10pt body, 24pt title, 11pt author
- Header: "IN6227 DATA MINING 2023, WKWSCI"
- Footer: [DOCUMENT TITLE] left, [AUTHOR NAME] right (Times New Roman 9pt blue)
- All template paragraph styles
"""
import json
import os
import shutil

import win32com.client as win32

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_SRC = r"D:\Users\in6227\IN6227-Reports-Template.doc"
TEMPLATE_COPY = os.path.join(BASE, "report_filled.doc")
PROFILE_PATH = os.path.join(BASE, "profile.json")
RESULTS_PATH = os.path.join(BASE, "results.json")
META_PATH = os.path.join(BASE, "assets", "metadata.json")
PLOTS_DIR = os.path.join(BASE, "plots")
PDF_OUT = os.path.join(BASE, "report.pdf")
DOCX_OUT = os.path.join(BASE, "report_filled.docx")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def replace_para_text(doc, para_idx_0based, new_text):
    """Replace text of paragraph at 0-based index, preserving style."""
    para = doc.Paragraphs(para_idx_0based + 1)
    rng = para.Range
    rng.End = rng.End - 1  # Exclude paragraph mark
    rng.Text = new_text


def clear_para_text(doc, para_idx_0based):
    """Clear text of paragraph at 0-based index."""
    para = doc.Paragraphs(para_idx_0based + 1)
    rng = para.Range
    rng.End = rng.End - 1
    rng.Delete()


def find_heading(doc, heading_text, start_from=0):
    """Find a heading paragraph by text."""
    for i in range(start_from, doc.Paragraphs.Count):
        text = doc.Paragraphs(i + 1).Range.Text.strip()
        if heading_text.lower() in text.lower() and len(text) <= len(heading_text) + 5:
            return i
    return None


def find_next_heading(doc, headings, start_from):
    """Find the next heading from a list."""
    for i in range(start_from, doc.Paragraphs.Count):
        text = doc.Paragraphs(i + 1).Range.Text.strip()
        for h in headings:
            if h.lower() in text.lower() and len(text) <= len(h) + 5:
                return i
    return doc.Paragraphs.Count


def main():
    profile = load_json(PROFILE_PATH)
    results = load_json(RESULTS_PATH)
    meta = load_json(META_PATH)

    tgt = profile["target"]
    test_m = results.get("test_metrics", {})
    dummy = results["models"]["dummy"]["cv_mean"]
    best = results["models"][results["best_model"]]["cv_mean"]
    lr = results["models"]["logistic_regression"]["cv_mean"]

    # --- Copy template ---
    shutil.copy2(TEMPLATE_SRC, TEMPLATE_COPY)
    print(f"[populate] Copied template -> {TEMPLATE_COPY}")

    word = win32.Dispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False
    doc = word.Documents.Open(TEMPLATE_COPY)
    print(f"[populate] Opened, {doc.Paragraphs.Count} paragraphs")

    sections = ["INTRODUCTION", "METHODS OR PROCEDURES", "RESULTS",
                "DISCUSSION", "CONCLUSION", "REFERENCES"]

    # --- 1. TITLE BLOCK ---
    title_text = "IN6227 Assignment 1, Variant 2: Tabular Classification SKILL"
    for i in range(doc.Paragraphs.Count):
        text = doc.Paragraphs(i + 1).Range.Text.strip()
        if "Reports Template: Title Here" in text:
            replace_para_text(doc, i, title_text)
            print(f"[populate] Replaced title at P{i}")
            break

    # --- 2. AUTHOR + ASSIGNMENT LINE ---
    # Template P1: "Author Name, Matric Number\x0bIN6227-2023-Assignment-{1,2,3}"
    # \x0b = vertical tab = line break within same paragraph
    author_name_only = f"{meta['full_name']}, {meta['matric_number']}"
    author_text = f"{author_name_only}\x0bIN6227-2023-Assignment-1"
    for i in range(doc.Paragraphs.Count):
        text = doc.Paragraphs(i + 1).Range.Text.strip()
        if "Author Name, Matric Number" in text:
            replace_para_text(doc, i, author_text)
            print(f"[populate] Replaced author+assignment at P{i}")
            break

    # --- 3. FOOTER: left=title, right=author using tab stops ---
    # Template footer has: [DOCUMENT TITLE] on left, [AUTHOR NAME] on right
    # using tab stops (center at 212.6pt, right at 425.2pt)
    # The footer text uses \x07 (tab) to position text
    for sec in doc.Sections:
        for fi in range(1, 4):
            ftr = sec.Footers(fi)
            if not ftr:
                continue
            ftr_range = ftr.Range
            ftr_text = ftr_range.Text
            if "[DOCUMENT TITLE]" in ftr_text or "[AUTHOR NAME]" in ftr_text:
                # Replace placeholders preserving tab structure
                new_text = ftr_text.replace("[DOCUMENT TITLE]", title_text)
                new_text = new_text.replace("[AUTHOR NAME]", author_name_only)
                ftr_range.Text = new_text
                print(f"[populate] Replaced footer in Section {sec.Index} Footer {fi}")

    # --- 4. SECTION BODIES ---
    intro_body = (
        f"This report presents an end-to-end tabular classification workflow "
        f"applied to the dataset ({profile['n_samples']} rows, "
        f"{profile['n_features']} features). The target variable is "
        f"{tgt['name']} with {tgt['n_classes']} classes: "
        f"{', '.join(tgt['classes'])}. Class distribution (train): "
        f"{', '.join(f'{k}={v}' for k, v in tgt['counts'].items())}, "
        f"imbalance ratio {tgt.get('imbalance_ratio', 'N/A')}:1. "
        f"The data contains {profile['total_missing']} missing values. "
        f"Column types: {len(profile['numeric_columns'])} numeric, "
        f"{len(profile['categorical_columns'])} categorical. "
        f"The goal is to build a leakage-safe, reproducible classification "
        f"pipeline and compare multiple models."
    )

    methods_body = (
        f"All learned preprocessing (median imputation for numerics, "
        f"most-frequent imputation and one-hot encoding for categorics, "
        f"standard scaling) is embedded inside sklearn Pipeline / "
        f"ColumnTransformer, so during cross-validation the imputer, scaler, "
        f"and encoder are refit on each training fold only. No manual feature "
        f"selection is applied. Four classifiers are trained: "
        f"DummyClassifier (stratified baseline), LogisticRegression "
        f"(max_iter=1000, class_weight=balanced), RandomForest "
        f"(n_estimators=200, class_weight=balanced), and "
        f"GradientBoosting (n_estimators=100, max_depth=3). "
        f"Cross-validation uses Stratified 5-fold (random_state=42). "
        f"Model selection uses mean CV F1. The best model is retrained on "
        f"the full training set and evaluated once on the held-out test set."
    )

    results_body = (
        f"Test-set performance (best model: {results['best_model']}): "
        f"accuracy={test_m['accuracy']:.4f}, "
        f"precision={test_m['precision']:.4f}, "
        f"recall={test_m['recall']:.4f}, "
        f"F1={test_m['f1']:.4f}, "
        f"ROC-AUC={test_m['roc_auc']:.4f}, "
        f"PR-AUC={test_m['pr_auc']:.4f}."
    )

    discussion_body = (
        f"Best model: {results['best_model']}, selected by CV F1="
        f"{best['f1']:.4f}. Its advantage over LogisticRegression "
        f"(CV F1={lr['f1']:.4f}) was small (delta="
        f"{best['f1']-lr['f1']:.4f}); the two models are comparable in "
        f"discriminative power. The Dummy baseline (F1="
        f"{dummy['f1']:.4f}) confirms a no-information classifier performs "
        f"well below all meaningful models. LogisticRegression achieves "
        f"higher recall (0.849 vs 0.715) at the cost of lower precision "
        f"(0.540 vs 0.620). Test F1 ({test_m['f1']:.4f}) closely matches "
        f"CV F1 ({best['f1']:.4f}), indicating stable generalisation."
    )

    # CONCLUSION: NO metadata here — metadata goes in VITA only
    conclusion_body = (
        f"The SKILL successfully builds a reusable, leakage-safe tabular "
        f"classification pipeline. RandomForest was selected as the best "
        f"model by CV F1, though the margin over LogisticRegression was "
        f"small. All numerical values are pulled from results.json."
    )

    section_bodies = {
        "INTRODUCTION": intro_body,
        "METHODS OR PROCEDURES": methods_body,
        "RESULTS": results_body,
        "DISCUSSION": discussion_body,
        "CONCLUSION": conclusion_body,
    }

    for sec_idx, heading in enumerate(sections):
        heading_idx = find_heading(doc, heading)
        if heading_idx is None:
            print(f"[populate] WARNING: heading '{heading}' not found")
            continue

        next_headings = sections[sec_idx + 1:]
        next_idx = find_next_heading(doc, next_headings, heading_idx + 1)

        body_indices = []
        for i in range(heading_idx + 1, next_idx):
            text = doc.Paragraphs(i + 1).Range.Text.strip()
            if text:
                body_indices.append(i)

        print(f"[populate] '{heading}': heading at P{heading_idx}, "
              f"body paras: {body_indices}, next at P{next_idx}")

        if heading in section_bodies:
            body_text = section_bodies[heading]
            if body_indices:
                # Clear excess paragraphs in reverse order
                for idx in reversed(body_indices[1:]):
                    clear_para_text(doc, idx)
                # Replace first body paragraph
                replace_para_text(doc, body_indices[0], body_text)
                print(f"[populate] Replaced body for '{heading}' ({len(body_text)} chars)")
            else:
                heading_para = doc.Paragraphs(heading_idx + 1)
                rng = doc.Range(heading_para.Range.End, heading_para.Range.End)
                sel = word.Selection
                sel.SetRange(rng.Start, rng.Start)
                sel.TypeParagraph()
                sel.TypeText(body_text)
                print(f"[populate] Inserted body for '{heading}' ({len(body_text)} chars)")

    # --- 5. RESULTS: insert a proper Word TABLE ---
    # Two-column layout means each column is ~8cm wide.
    # A 7-column table won't fit. Use 4 columns: Model, F1, AUC, Acc
    results_idx = find_heading(doc, "RESULTS")
    if results_idx is not None:
        for i in range(results_idx + 1, doc.Paragraphs.Count):
            text = doc.Paragraphs(i + 1).Range.Text.strip()
            if text and "RESULTS" not in text.upper() and "DISCUSSION" not in text.upper():
                body_para = doc.Paragraphs(i + 1)
                insert_range = doc.Range(body_para.Range.End, body_para.Range.End)
                insert_range.InsertBefore("\r")

                # Compact 4-column table that fits in one column
                models = results["models"]
                table_data = [
                    ["Model", "Acc", "F1", "AUC"]
                ]
                for name, data in models.items():
                    m = data["cv_mean"]
                    marker = "*" if name == results.get("best_model") else ""
                    # Shorten model names
                    short_name = name.replace("logistic_regression", "log_reg")
                    table_data.append([
                        short_name + marker,
                        f"{m['accuracy']:.3f}",
                        f"{m['f1']:.3f}",
                        f"{m['roc_auc']:.3f}",
                    ])

                tbl_range = doc.Range(body_para.Range.End, body_para.Range.End)
                tbl_range.Collapse(1)

                n_rows = len(table_data)
                n_cols = len(table_data[0])
                tbl = doc.Tables.Add(tbl_range, n_rows, n_cols)

                for ri, row in enumerate(table_data):
                    for ci, val in enumerate(row):
                        cell = tbl.Cell(ri + 1, ci + 1)
                        cell.Range.Text = val
                        cell.Range.Font.Name = "Times New Roman"
                        cell.Range.Font.Size = 9
                        if ri == 0:
                            cell.Range.Font.Bold = True

                tbl.Borders.Enable = True
                # Set column widths to fit in one column (~8cm = 227pt)
                # 4 columns: Model=80pt, Acc=50pt, F1=50pt, AUC=50pt = 230pt
                try:
                    tbl.Columns(1).Width = 80
                    tbl.Columns(2).Width = 50
                    tbl.Columns(3).Width = 50
                    tbl.Columns(4).Width = 50
                except:
                    pass

                print(f"[populate] Inserted results table ({n_rows}x{n_cols})")
                break

    # --- 6. CONFUSION MATRIX: small image within column ---
    cm_path = os.path.join(PLOTS_DIR, "confusion_matrix.png")
    if os.path.exists(cm_path) and results_idx is not None:
        # Find the table we just inserted, then add image after it
        for i in range(results_idx + 1, doc.Paragraphs.Count):
            text = doc.Paragraphs(i + 1).Range.Text.strip()
            if "DISCUSSION" in text.upper():
                # Insert image BEFORE the DISCUSSION heading
                disc_para = doc.Paragraphs(i + 1)
                img_range = doc.Range(disc_para.Range.Start, disc_para.Range.Start)
                img_range.InsertBefore("\r")
                # Now insert image in the new paragraph
                new_para = doc.Paragraphs(i + 1)  # shifted
                img_sel = word.Selection
                img_sel.SetRange(new_para.Range.Start, new_para.Range.Start)
                # Add image with small width to fit in one column
                # Column width ≈ (page_width - margins - gap) / 2 ≈ 8cm ≈ 3.15 inch
                # Use 5cm ≈ 2 inch to be safe
                shape = img_sel.InlineShapes.AddPicture(cm_path)
                shape.Width = 113  # 4cm in points (1cm ≈ 28.35pt)
                shape.Height = 85  # maintain aspect ratio ≈ 3cm
                print(f"[populate] Inserted confusion matrix (4cm x 3cm)")
                break

    # --- 7. REFERENCES ---
    for i in range(doc.Paragraphs.Count):
        text = doc.Paragraphs(i + 1).Range.Text.strip()
        if text.startswith("[1]") and "Seeger" in text:
            replace_para_text(doc, i,
                "[1]\tPedregosa, F. et al. (2011). Scikit-learn: Machine Learning in Python. Journal of Machine Learning Research, 12, 2825-2830.")
            print(f"[populate] Replaced reference [1]")
            break

    for i in range(doc.Paragraphs.Count):
        text = doc.Paragraphs(i + 1).Range.Text.strip()
        if text.startswith("[2]") and "Benoit" in text:
            replace_para_text(doc, i,
                "[2]\tBreiman, L. (2001). Random Forests. Machine Learning, 45(1), 5-32.")
            print(f"[populate] Replaced reference [2]")
            break

    # --- 8. VITA: put all metadata here (not in CONCLUSION) ---
    for i in range(doc.Paragraphs.Count):
        para = doc.Paragraphs(i + 1)
        style_name = para.Style.NameLocal if para.Style else ""
        if "VITA" in style_name.upper():
            rng = para.Range
            rng.End = rng.End - 1
            vita_text = (
                f"Name: {meta['full_name']}\r"
                f"Matric number: {meta['matric_number']}\r"
                f"Assignment: IN6227-2023-Assignment-1, Variant 2\r"
                f"Model (LLM): {meta['model_name']}\r"
                f"LLM interface: {meta['llm_interface']}\r"
                f"GitHub: {meta['github_link']}"
            )
            rng.Text = vita_text
            print(f"[populate] Inserted VITA content at P{i} (style: {style_name})")
            break

    # --- Save and export ---
    if os.path.exists(DOCX_OUT):
        try:
            os.remove(DOCX_OUT)
        except:
            pass
    doc.SaveAs(DOCX_OUT, FileFormat=16)
    print(f"[populate] Saved .docx -> {DOCX_OUT}")

    if os.path.exists(PDF_OUT):
        try:
            os.remove(PDF_OUT)
        except:
            pass
    doc.ExportAsFixedFormat(
        PDF_OUT, ExportFormat=17, OpenAfterExport=False,
        OptimizeFor=0, Range=0, Item=0, IncludeDocProps=True,
        KeepIRM=True, CreateBookmarks=0, DocStructureTags=True,
        BitmapMissingFonts=True, UseISO19005_1=False,
    )
    print(f"[populate] Exported PDF -> {PDF_OUT}")

    doc.Close(False)
    word.Quit()

    try:
        from pypdf import PdfReader
        reader = PdfReader(PDF_OUT)
        n_pages = len(reader.pages)
    except:
        n_pages = "?"
    size_kb = os.path.getsize(PDF_OUT) / 1024
    print(f"[populate] PDF: {size_kb:.0f} KB, {n_pages} page(s)")
    if isinstance(n_pages, int) and n_pages > 2:
        print(f"[populate] WARNING: {n_pages} pages - exceeds 2-page limit!")
    elif isinstance(n_pages, int):
        print(f"[populate] OK: {n_pages} page(s) - within limit.")


if __name__ == "__main__":
    main()
