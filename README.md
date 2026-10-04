# Tabular Classification SKILL

A reusable SKILL for end-to-end tabular classification with automated report generation.

## Overview

This skill guides an AI agent through a complete data-mining workflow: data profiling, preprocessing decision-making, model training, evaluation, and report generation. It generalizes to **any tabular classification dataset** — no hardcoded column names, no dataset-specific logic.

**Design principle:** Simple, transparent, explainable, human-supervisable. Not a complex AutoML system.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Step 1: Profile the data
python scripts/data_profiler.py --data path/to/train.csv --target label --out profile.json

# Step 2: Train and evaluate (CV on train, test once)
python scripts/train_eval.py --train path/to/train.csv --test path/to/test.csv \
    --target label --config preprocess_config.json --out results.json

# Step 3: Generate report
python scripts/generate_report.py --profile profile.json --results results.json \
    --template assets/report_template.md --metadata metadata.json --out report.md

# Step 4: Render PDF
python scripts/render_pdf.py --input report.md --out report.pdf
```

## Structure

```
SKILL.md              Main skill instructions (60% of grade)
scripts/              Deterministic Python scripts
references/           Decision tables and guidelines
assets/               Report templates and styles
tests/                Generalization tests
REFLECTION.md         Reflection on the process (20% of grade)
```

## Model Ladder

1. **DummyClassifier** — mandatory baseline (no-information lower bound)
2. **LogisticRegression** — linear, interpretable
3. **RandomForest** — nonlinear, robust
4. **GradientBoosting** — strong tabular baseline

Dummy is always trained. At least 2 additional models are selected based on data characteristics.

## License

MIT
