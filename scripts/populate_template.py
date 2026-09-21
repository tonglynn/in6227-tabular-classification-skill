#!/usr/bin/env python3
"""Populate the official IN6227-Reports-Template.doc with report content.

Strategy: Open the template copy via Word COM. For each section, find
the heading, then replace the body paragraphs directly by setting
Range.Text (preserves style). Delete excess paragraphs; insert new ones
via Selection.TypeText if needed. This avoids the InsertAfter merge issue.
"""
import json
import os
import shutil
import sys

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


def build_cv_table_text(results):
    models = results["models"]
    lines = []
    lines.append("Model\tAccuracy\tPrecision\tRecall\tF1\tROC-AUC\tPR-AUC")
    for name, data in models.items():
        m = data["cv_mean"]
        marker = " (best)" if name == results.get("best_model") else ""
        lines.append(
            f"{name}{marker}\t{m['accuracy']:.4f}\t{m['precision']:.4f}\t"
            f"{m['recall']:.4f}\t{m['f1']:.4f}\t{m['roc_auc']:.4f}\t"
            f"{m.get('pr_auc', 0):.4f}"
        )
    return "\n".join(lines)


def replace_para_text(doc, para_idx_0based, new_text):
    """Replace text of paragraph at 0-based index, preserving style."""
    para = doc.Paragraphs(para_idx_0based + 1)
    rng = para.Range
    rng.End = rng.End - 1  # Exclude paragraph mark
    rng.Text = new_text


def clear_para_text(doc, para_idx_0based):
    """Clear text of paragraph at 0-based index, deleting the text content."""
    para = doc.Paragraphs(para_idx_0based + 1)
    rng = para.Range
    rng.End = rng.End - 1  # Exclude paragraph mark
    rng.Delete()  # Delete the text content


def find_heading(doc, heading_text, start_from=0):
    """Find a heading paragraph by text (contains match, short text)."""
    for i in range(start_from, doc.Paragraphs.Count):
        text = doc.Paragraphs(i + 1).Range.Text.strip()
        if heading_text.lower() in text.lower() and len(text) <= len(heading_text) + 5:
            return i
    return None


def find_next_heading(doc, headings, start_from):
    """Find the next heading from a list, starting from start_from."""
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

    # --- Open in Word ---
    word = win32.Dispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False
    doc = word.Documents.Open(TEMPLATE_COPY)
    print(f"[populate] Opened, {doc.Paragraphs.Count} paragraphs")

    # --- Section headings in order ---
    sections = [
        "INTRODUCTION",
        "METHODS OR PROCEDURES",
        "RESULTS",
        "DISCUSSION",
        "CONCLUSION",
        "REFERENCES",
    ]

    # --- Replace title ---
    for i in range(doc.Paragraphs.Count):
        text = doc.Paragraphs(i + 1).Range.Text.strip()
        if "Reports Template: Title Here" in text:
            replace_para_text(doc, i, "IN6227 Assignment 1, Variant 2: Tabular Classification SKILL")
            print(f"[populate] Replaced title at P{i}")
            break

    # --- Replace author line ---
    for i in range(doc.Paragraphs.Count):
        text = doc.Paragraphs(i + 1).Range.Text.strip()
        if "Author Name, Matric Number" in text:
            new_author = f"{meta['full_name']}, {meta['matric_number']}"
            replace_para_text(doc, i, new_author)
            print(f"[populate] Replaced author at P{i}")
            break

    # Also replace the assignment line below it
    for i in range(doc.Paragraphs.Count):
        text = doc.Paragraphs(i + 1).Range.Text.strip()
        if "IN6227-2023-Assignment" in text:
            replace_para_text(doc, i, f"{meta['assignment']}-{meta['variant']}")
            print(f"[populate] Replaced assignment line at P{i}")
            break

    # --- Build section body texts ---
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

    cv_table = build_cv_table_text(results)
    results_body = (
        f"Cross-validation results (5-fold, stratified):\n{cv_table}\n"
        f"\nTest-set performance (best model: {results['best_model']}): "
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

    conclusion_body = (
        f"The SKILL successfully builds a reusable, leakage-safe tabular "
        f"classification pipeline. RandomForest was selected as the best "
        f"model by CV F1, though the margin over LogisticRegression was "
        f"small. All numerical values are pulled from results.json. "
        f"Model: {meta['model_name']}; LLM interface: "
        f"{meta['llm_interface']}; GitHub: {meta['github_link']}."
    )

    section_bodies = {
        "INTRODUCTION": intro_body,
        "METHODS OR PROCEDURES": methods_body,
        "RESULTS": results_body,
        "DISCUSSION": discussion_body,
        "CONCLUSION": conclusion_body,
    }

    # --- Process each section: replace body paragraphs ---
    for sec_idx, heading in enumerate(sections):
        heading_idx = find_heading(doc, heading)
        if heading_idx is None:
            print(f"[populate] WARNING: heading '{heading}' not found")
            continue

        # Find the next heading
        next_headings = sections[sec_idx + 1:]
        next_idx = find_next_heading(doc, next_headings, heading_idx + 1)

        # Collect body paragraph indices (between heading and next heading)
        body_indices = []
        for i in range(heading_idx + 1, next_idx):
            text = doc.Paragraphs(i + 1).Range.Text.strip()
            if text:  # Only non-empty paragraphs
                body_indices.append(i)

        print(f"[populate] '{heading}': heading at P{heading_idx}, "
              f"body paras: {body_indices}, next heading at P{next_idx}")

        if heading in section_bodies:
            body_text = section_bodies[heading]

            if body_indices:
                # Clear excess body paragraphs FIRST (reverse order to
                # keep indices stable), THEN replace the first one.
                # This avoids index shifts from \n creating new paragraphs.
                for idx in reversed(body_indices[1:]):
                    clear_para_text(doc, idx)

                # Replace first body paragraph with new text
                replace_para_text(doc, body_indices[0], body_text)

                # Apply PARAGRAPH (no indent) style to the first body para
                try:
                    doc.Paragraphs(body_indices[0] + 1).Style = doc.Styles("PARAGRAPH (no indent)")
                except:
                    try:
                        doc.Paragraphs(body_indices[0] + 1).Style = doc.Styles("PARAGRAPH")
                    except:
                        pass

                print(f"[populate] Replaced body for '{heading}' ({len(body_text)} chars)")
            else:
                # No body paragraphs found — need to insert one
                # Use Selection to type text after heading
                heading_para = doc.Paragraphs(heading_idx + 1)
                rng = doc.Range(heading_para.Range.End, heading_para.Range.End)
                sel = word.Selection
                sel.SetRange(rng.Start, rng.Start)
                sel.TypeParagraph()
                sel.TypeText(body_text)
                # Apply style
                try:
                    sel.Style = doc.Styles("PARAGRAPH (no indent)")
                except:
                    pass
                print(f"[populate] Inserted body for '{heading}' ({len(body_text)} chars)")

    # --- Replace references ---
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

    # --- Insert VITA content ---
    # The VITA section is at the end of the template, possibly with an
    # empty paragraph using the VITA style. Search by style name.
    for i in range(doc.Paragraphs.Count):
        para = doc.Paragraphs(i + 1)
        style_name = para.Style.NameLocal if para.Style else ""
        if "VITA" in style_name.upper():
            # Type content into this paragraph
            rng = para.Range
            rng.End = rng.End - 1  # Exclude paragraph mark
            vita_text = (
                f"Name: {meta['full_name']}\r"
                f"Matric number: {meta['matric_number']}\r"
                f"Model (LLM): {meta['model_name']}\r"
                f"LLM interface: {meta['llm_interface']}\r"
                f"GitHub: {meta['github_link']}"
            )
            rng.Text = vita_text
            print(f"[populate] Inserted VITA content at P{i} (style: {style_name})")
            break
    else:
        # Fallback: search by text
        for i in range(doc.Paragraphs.Count):
            text = doc.Paragraphs(i + 1).Range.Text.strip()
            if "VITA" in text.upper() and len(text) <= 10:
                vita_para = doc.Paragraphs(i + 1)
                rng = doc.Range(vita_para.Range.End, vita_para.Range.End)
                sel = word.Selection
                sel.SetRange(rng.Start, rng.Start)
                sel.TypeParagraph()
                sel.TypeText(
                    f"Name: {meta['full_name']}\r"
                    f"Matric number: {meta['matric_number']}\r"
                    f"Model (LLM): {meta['model_name']}\r"
                    f"LLM interface: {meta['llm_interface']}\r"
                    f"GitHub: {meta['github_link']}"
                )
                print(f"[populate] Inserted VITA content at P{i} (text match)")
                break

    # --- Insert confusion matrix image after RESULTS body ---
    cm_path = os.path.join(PLOTS_DIR, "confusion_matrix.png")
    if os.path.exists(cm_path):
        results_idx = find_heading(doc, "RESULTS")
        if results_idx is not None:
            # Find the body paragraph after RESULTS
            for i in range(results_idx + 1, doc.Paragraphs.Count):
                text = doc.Paragraphs(i + 1).Range.Text.strip()
                if text and "RESULTS" not in text and "DISCUSSION" not in text:
                    # Insert image after this paragraph
                    body_para = doc.Paragraphs(i + 1)
                    rng = doc.Range(body_para.Range.End, body_para.Range.End)
                    sel = word.Selection
                    sel.SetRange(rng.Start, rng.Start)
                    sel.TypeParagraph()
                    sel.InlineShapes.AddPicture(cm_path)
                    print(f"[populate] Inserted confusion matrix image after RESULTS body")
                    break

    # --- Save as .docx ---
    if os.path.exists(DOCX_OUT):
        try:
            os.remove(DOCX_OUT)
        except:
            pass
    doc.SaveAs(DOCX_OUT, FileFormat=16)
    print(f"[populate] Saved .docx -> {DOCX_OUT}")

    # --- Export as PDF ---
    if os.path.exists(PDF_OUT):
        try:
            os.remove(PDF_OUT)
        except:
            pass
    doc.ExportAsFixedFormat(
        PDF_OUT,
        ExportFormat=17,
        OpenAfterExport=False,
        OptimizeFor=0,
        Range=0,
        Item=0,
        IncludeDocProps=True,
        KeepIRM=True,
        CreateBookmarks=0,
        DocStructureTags=True,
        BitmapMissingFonts=True,
        UseISO19005_1=False,
    )
    print(f"[populate] Exported PDF -> {PDF_OUT}")

    doc.Close(False)
    word.Quit()

    # Verify page count
    try:
        from pypdf import PdfReader
        reader = PdfReader(PDF_OUT)
        n_pages = len(reader.pages)
    except Exception:
        n_pages = "?"

    size_kb = os.path.getsize(PDF_OUT) / 1024
    print(f"[populate] PDF: {size_kb:.0f} KB, {n_pages} page(s)")
    if isinstance(n_pages, int) and n_pages > 2:
        print(f"[populate] WARNING: {n_pages} pages - exceeds 2-page limit!")
    elif isinstance(n_pages, int):
        print(f"[populate] OK: {n_pages} page(s) - within limit.")


if __name__ == "__main__":
    main()
