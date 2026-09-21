# SKILL: End-to-End Tabular Classification

> A reusable, leakage-safe workflow for tabular classification with
> automated reporting.  Designed for an AI agent (LLM) to execute on any
> tabular dataset, using Python / scikit-learn for all computation.

---

## 1. Purpose

This SKILL guides an AI agent through a complete data-mining workflow:

1. **Data discovery** — locate the dataset CSV files.
2. **EDA / profiling** — inspect shape, dtypes, missing values, target
   distribution, class imbalance.
3. **Preprocessing decisions** — choose imputation, scaling, encoding
   strategies (stored in `preprocess_config.json`).
4. **Model selection** — pick 2+ classifiers based on data characteristics.
5. **Leakage-safe training** — embed all preprocessing in sklearn
   `Pipeline` / `ColumnTransformer`; use stratified cross-validation.
6. **Evaluation** — compute Accuracy, Precision, Recall, F1, ROC-AUC,
   PR-AUC on CV folds; evaluate the best model **once** on the test set.
7. **Automated report generation** — render `report.md` from structured
   JSON outputs, then `report.pdf` (≤ 2 pages).

## 2. Architecture

```
LLM (reasoning, decisions, reporting)
        │
        ▼
Python / scikit-learn (all computation)
        │
        ├── scripts/data_profiler.py     → profile.json, preprocess_config.json
        ├── scripts/train_eval.py        → results.json, run_manifest.json, plots/
        ├── scripts/generate_report.py   → report.md
        └── scripts/render_pdf.py        → report.pdf
```

**Design principles:** simple, transparent, explainable, reproducible,
leakage-safe, generalizable.  Not an AutoML framework.

## 3. Prerequisites

```bash
pip install -r requirements.txt
```

Dependencies: pandas, numpy, scikit-learn, matplotlib, jinja2, markdown,
reportlab, pypdf.

## 4. Workflow

### Step 1 — Profile the data

```bash
python scripts/data_profiler.py \
    --data path/to/train.csv \
    --target label \
    --out profile.json \
    --config-out preprocess_config.json
```

The profiler:
- Classifies each column as **numeric** or **categorical**.
- Computes missing-value counts, unique-value counts, basic statistics.
- Detects the target type (binary / multiclass) and class imbalance.
- Writes `profile.json` (full profile) and `preprocess_config.json`
  (leakage-safe preprocessing decisions).

If `--target` is omitted, the profiler auto-detects the target by checking
common names (`label`, `target`, `y`, `class`, `outcome`, `churn`) and
falling back to the last column.

### Step 2 — Train and evaluate

```bash
python scripts/train_eval.py \
    --train path/to/train.csv \
    --test  path/to/test.csv \
    --target label \
    --config preprocess_config.json \
    --profile profile.json \
    --out results.json \
    --manifest-out run_manifest.json \
    --plots-dir plots \
    --cv-folds 5
```

The training script:
- Builds a `ColumnTransformer` with separate pipelines for numeric and
  categorical columns (all inside one sklearn `Pipeline`).
- Trains four models: `DummyClassifier` (baseline), `LogisticRegression`,
  `RandomForestClassifier`, `GradientBoostingClassifier`.
- Evaluates each via **Stratified 5-fold CV** (`random_state=42`).
- Computes: Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC.
- Selects the best model by **mean CV F1**.
- Retrains the best model on the full training set.
- Evaluates **once** on the held-out test set.
- Generates plots: target distribution, confusion matrix, ROC curve,
  feature importance.
- Writes `results.json` and `run_manifest.json`.

### Step 3 — Populate the official Word template and export PDF

```bash
python scripts/populate_template.py
```

**Architecture:** This script does NOT recreate the template. It:

1. Copies the official `IN6227-Reports-Template.doc` (never modifies the
   original)
2. Opens the copy via Microsoft Word COM automation (`win32com`)
3. Replaces text in the template's existing placeholder paragraphs
   (preserving all styles, fonts, margins, headers, footers, two-column
   layout)
4. Inserts a native Word table for model comparison results
5. Inserts a small confusion-matrix figure via `InlineShapes`
6. Saves as `final_report.docx`
7. Exports to `final_report.pdf` via Word's `ExportAsFixedFormat`

**Pipeline:**

```
profile.json + results.json + metadata.json
  → structured report content
  → COPY of lecturer's Word template
  → populate content into existing template paragraphs/styles
  → Microsoft Word
  → final_report.docx
  → Word ExportAsFixedFormat
  → final_report.pdf
```

**Why this approach:** The official `.doc` template is the authoritative
layout. Page size, margins, two-column layout, typography, heading
styles, paragraph spacing, headers, footers, and pagination all come
directly from the lecturer's Word template — none are recreated.

The report structure follows the official template sections:
INTRODUCTION → METHODS OR PROCEDURES → RESULTS → DISCUSSION →
CONCLUSION → REFERENCES → VITA.  Verified to be **≤ 2 pages**.

## 5. Leakage Rules (mandatory)

| Rule | Enforcement |
|---|---|
| All learned preprocessing inside `Pipeline` / `ColumnTransformer` | Built into `train_eval.py` |
| Never fit imputation / scaling / encoding on the full dataset before CV | CV uses the full pipeline; preprocessing is refit per fold |
| Never use the test set for model selection, tuning, or threshold tuning | Test is evaluated only once after the best model is chosen |
| Target must never appear in `X` | `X = df.drop(columns=[target])` |
| Drop rows with missing target before training | `df.dropna(subset=[target])` |

## 6. Model Selection Guidelines

| Criterion | Decision |
|---|---|
| Always | `DummyClassifier(strategy="stratified")` as the no-information baseline |
| Linear baseline | `LogisticRegression(max_iter=1000)` |
| Nonlinear, robust | `RandomForestClassifier(n_estimators=200)` |
| Strong tabular | `GradientBoostingClassifier(n_estimators=100)` |
| Moderate imbalance (3–10:1) | Use `class_weight="balanced"` where supported; justify with recall/F1 |
| Severe imbalance (>10:1) | Consider `class_weight="balanced"` or threshold tuning; never auto-SMOTE |

`random_state=42` everywhere.  Do not use XGBoost / LightGBM unless
genuinely necessary.

## 7. Evaluation Metrics

| Metric | When |
|---|---|
| Accuracy | Always (context with imbalance) |
| Precision | Binary (pos_label = minority) or weighted (multiclass) |
| Recall | Binary (pos_label = minority) or weighted (multiclass) |
| F1 | Primary selection metric |
| ROC-AUC | Always (binary: standard; multiclass: OvR weighted) |
| PR-AUC | Always (binary: `average_precision_score`; multiclass: macro AP) |

## 8. Generalization

The SKILL must **not** hard-code:
- Target column name (passed via `--target`)
- Specific feature names (read from `preprocess_config.json`)
- Specific row counts or class counts

Generalization is tested on:
- **sklearn Breast Cancer** dataset (binary, numeric-only)
- **sklearn Iris** dataset (multiclass, numeric-only)

Run: `python tests/test_generalization.py`

## 9. Structured Outputs

| File | Producer | Content |
|---|---|---|
| `profile.json` | `data_profiler.py` | Dataset shape, column types, stats, target distribution |
| `preprocess_config.json` | `data_profiler.py` | Numeric / categorical column lists, imputation / encoding strategies |
| `results.json` | `train_eval.py` | CV metrics per model, test metrics, feature importance, confusion matrix |
| `run_manifest.json` | `train_eval.py` | Run metadata, scripts, timing, environment, leakage-safety flags |
| `report.md` | `generate_report.py` | Human-readable report rendered from the above |
| `report.pdf` | `render_pdf.py` | PDF version (≤ 2 pages) |

## 10. Report Requirements

The report follows the official `IN6227-Reports-Template.doc` structure.
The template's sections are mapped to the assignment's content
requirements as follows:

| Official template section | Assignment content covered |
|---|---|
| **INTRODUCTION** | Data Exploration & Cleaning |
| **METHODS OR PROCEDURES** | Feature Selection / Engineering + Model Training |
| **RESULTS** | Evaluation & Comparison |
| **DISCUSSION** | Findings & Discussion |
| **CONCLUSION** | Summary |
| **REFERENCES** | Numbered citations |
| **VITA** | Matric number, full name, model name & version, LLM interface, GitHub link |

Formatting: Times New Roman 10-pt font, running header "IN6227 DATA
MINING 2023, WKWSCI", ≤ 2 pages.

All numbers in the report come from `results.json` — never manually
entered.  Use placeholders for missing personal information.

## 11. Directory Structure

```
in6227-tabular-classification-skill/
├── SKILL.md                      ← this file
├── README.md
├── REFLECTION.md
├── requirements.txt
├── .gitignore
├── assets/
│   ├── report_template.md        ← Jinja2 markdown template
│   └── metadata.json             ← student / model metadata
├── scripts/
│   ├── data_profiler.py
│   ├── train_eval.py
│   ├── generate_report.py
│   └── render_pdf.py
├── references/
│   └── decision_guide.md         ← preprocessing / model decision tables
├── tests/
│   └── test_generalization.py
├── profile.json                  ← generated
├── preprocess_config.json        ← generated
├── results.json                  ← generated
├── run_manifest.json             ← generated
├── report.md                     ← generated
├── report.pdf                    ← generated
└── plots/                        ← generated
    ├── target_distribution.png
    ├── confusion_matrix.png
    ├── roc_curve.png
    └── feature_importance.png
```
