# Tabular Classification SKILL

A reusable, leakage-safe SKILL for end-to-end tabular classification
with automated report generation.

**IN6227 Data Mining — Assignment 1 — Variant 2**

## Overview

This skill guides an AI agent through a complete data-mining workflow:
data profiling, preprocessing decision-making, leakage-safe model
training, evaluation, and automated report generation. It generalizes
to **any tabular classification dataset** — no hardcoded column names,
no dataset-specific logic.

**Design principle:** Simple, transparent, explainable, human-supervisable.
Not a complex AutoML system.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Step 1: Profile the data
python scripts/data_profiler.py --data path/to/train.csv --target label \
    --out profile.json --config-out preprocess_config.json

# Step 2: Train and evaluate (CV on train, test once)
python scripts/train_eval.py --train path/to/train.csv --test path/to/test.csv \
    --target label --config preprocess_config.json --profile profile.json \
    --out results.json --manifest-out run_manifest.json --plots-dir plots

# Step 3: Populate official Word template and export PDF
python scripts/populate_template.py
#   → final_report.docx
#   → final_report.pdf (≤ 2 pages)
```

## Results (Variant 2 dataset)

| Model | CV F1 | CV ROC-AUC | Test F1 | Test AUC |
|---|---|---|---|---|
| Dummy | 0.235 | 0.498 | — | — |
| LogisticRegression | 0.660 | 0.890 | — | — |
| **RandomForest** | **0.664** | **0.889** | **0.663** | **0.889** |
| GradientBoosting | 0.626 | 0.891 | — | — |

Best model: **RandomForest** (selected by CV F1).

## Structure

```
SKILL.md              Main skill instructions (60% of grade)
scripts/              Deterministic Python scripts
  data_profiler.py     → profile.json, preprocess_config.json
  train_eval.py        → results.json, run_manifest.json, plots/
  populate_template.py → final_report.docx, final_report.pdf
references/           Decision tables and guidelines
assets/               Report templates and metadata
tests/                Generalization tests (Breast Cancer, Iris)
REFLECTION.md         Reflection on the process (20% of grade)
```

## Model Ladder

1. **DummyClassifier** — mandatory baseline (no-information lower bound)
2. **LogisticRegression** — linear, interpretable, `class_weight="balanced"`
3. **RandomForest** — nonlinear, robust, `class_weight="balanced"`
4. **GradientBoosting** — strong tabular baseline

Dummy is always trained. All three additional models are evaluated and
compared; the best is selected by mean CV F1.

## Leakage Safety

- All preprocessing (imputation, scaling, encoding) is inside sklearn
  `Pipeline` / `ColumnTransformer`.
- Cross-validation uses `StratifiedKFold` — preprocessing refit per fold.
- The test set is used **once**, only after model selection.
- Target never appears in the feature matrix.

## Generalization

Tested on:
- **sklearn Breast Cancer** (binary, 30 numeric features) — PASS
- **sklearn Iris** (multiclass, 4 numeric features) — PASS

Run: `python tests/test_generalization.py`

## License

MIT
