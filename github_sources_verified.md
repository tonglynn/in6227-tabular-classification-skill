# GitHub Sources — Independently Verified

Verification date: 2026-09-22

Purpose: provide a traceable, independently checked record of the public GitHub sources that influenced the IN6227 Variant 2 SKILL design. This file verifies source existence and the specific design ideas that are actually supported by those sources. It does **not** claim that upstream code was copied.

---

## 1. AutoGluon

Repository: https://github.com/autogluon/autogluon  
Default branch observed: `master`  
License: Apache-2.0  
Repository page: https://github.com/autogluon/autogluon

### Exact upstream files / features verified

- `tabular/src/autogluon/tabular/predictor/predictor.py`
  - https://github.com/autogluon/autogluon/blob/master/tabular/src/autogluon/tabular/predictor/predictor.py
  - The `TabularPredictor` code imports and coordinates learner/trainer abstractions.
  - It exposes `leaderboard(...)` for tabular model comparison.
  - When `problem_type=None`, the problem type is inferred from labels.
  - It supports out-of-fold predictions in bagged mode and explicitly warns against using evaluation test data as tuning data.

- `core/src/autogluon/core/models/abstract/abstract_model.py`
  - https://github.com/autogluon/autogluon/blob/master/core/src/autogluon/core/models/abstract/abstract_model.py
  - Contains `_infer_problem_type(...)`, which delegates to `infer_problem_type(...)`.

### Design ideas legitimately borrowed

- Separate responsibilities across profiling / orchestration / model training rather than putting everything in one function.
- Infer task characteristics from the target when appropriate.
- Compare models using a compact leaderboard-style result table.
- Keep validation/model-selection data separate from a final unseen test set.
- Use out-of-fold / cross-validation logic as a model-selection concept rather than repeatedly inspecting the final test set.

### Intentionally not borrowed

- AutoGluon's large AutoML model zoo.
- Multi-layer stacking / weighted ensembles.
- Heavy automatic hyperparameter search.
- AutoGluon as a runtime dependency.

### Where adapted in this project

- `scripts/data_profiler.py`
- `scripts/train_eval.py`
- structured model comparison in `results.json`
- final report comparison table
- train/CV/final-test separation rules in `SKILL.md`

No claim is made that AutoGluon source code was copied.

---

## 2. FLAML

Repository: https://github.com/microsoft/FLAML  
Default branch observed: `main`  
License: MIT (declared in `pyproject.toml`)  
Repository page: https://github.com/microsoft/FLAML

### Exact upstream files / features verified

- `flaml/automl/automl.py`
  - https://github.com/microsoft/FLAML/blob/main/flaml/automl/automl.py
  - The AutoML search-space metadata includes `low_cost_init_value`.
  - The project is explicitly designed around economical model selection and hyperparameter optimization.

- `pyproject.toml`
  - https://github.com/microsoft/FLAML/blob/main/pyproject.toml
  - Declares the project license as MIT.

### Design ideas legitimately borrowed

- Prefer economical model search over exhaustive tuning.
- Use a small, defensible candidate set rather than hundreds of configurations.
- Treat compute/time cost as part of model-selection design.

### Intentionally not borrowed

- FLAML's optimizer implementation.
- FLAML as a runtime dependency.
- Large automatic HPO searches.

### Where adapted in this project

- Small model candidate pool in `SKILL.md`.
- Minimal / no HPO by default in `scripts/train_eval.py`.
- Explicit reasoning that simple models are sufficient unless extra complexity is justified.

No claim is made that FLAML source code was copied.

---

## 3. MLJAR Supervised

Repository: https://github.com/mljar/mljar-supervised  
Default branch observed: `master`  
License: MIT  
Repository page: https://github.com/mljar/mljar-supervised

### Exact upstream features verified

- Repository README documents automatic Markdown model reports.
- `AutoML.report_structured(...)` can return Markdown, Python dict, or JSON.
- Structured report generation writes machine-readable report data that can be consumed by external tools / LLMs.
- Recent release notes document `report_structured()` and `report_structured.json`.

Relevant pages:

- https://github.com/mljar/mljar-supervised
- https://github.com/mljar/mljar-supervised/releases

### Design ideas legitimately borrowed

- Machine-readable intermediate artifacts before report generation.
- Separate model computation from narrative report rendering.
- Generate reports from structured results rather than manually copying metric values.
- Compact leaderboard/model-summary output.

### Intentionally not borrowed

- MLJAR's full AutoML engine.
- SHAP/fairness/reporting stack.
- MLJAR as a runtime dependency.

### Where adapted in this project

- `profile.json`
- `preprocess_config.json`
- `results.json`
- `run_manifest.json`
- report generation driven from structured outputs

No claim is made that MLJAR source code was copied.

---

## 4. BrendenKennedy / claude-for-ai-platforms

Repository: https://github.com/BrendenKennedy/claude-for-ai-platforms  
Default branch observed: `main`  
Repository license: MIT  
Repository page: https://github.com/BrendenKennedy/claude-for-ai-platforms

### Exact SKILL verified

`/.claude/skills/tabular/SKILL.md`

https://github.com/BrendenKennedy/claude-for-ai-platforms/blob/main/.claude/skills/tabular/SKILL.md

This is the strongest direct structural reference for the IN6227 SKILL.

### Specific design ideas verified in that SKILL

- All learned preprocessing belongs inside sklearn `Pipeline` / `ColumnTransformer`.
- Dummy baseline first.
- Model ladder:
  - `DummyClassifier(strategy="most_frequent")`
  - logistic / linear model
  - gradient boosting
- `StratifiedKFold` for ordinary classification.
- `GroupKFold` when rows share an entity.
- Final test set remains held out from model selection.
- For imbalance, accuracy can mislead; PR-AUC / F1 and `class_weight` are suggested before SMOTE.
- Named pitfalls include leakage from target encoding, imbalance, misleading impurity feature importance, and unsafe persistence/versioning practices.

### Design ideas legitimately borrowed

- Baseline-first model ladder.
- Leakage-safe `Pipeline` / `ColumnTransformer`.
- Split discipline and untouched final test set.
- Decision rules for class imbalance.
- Named traps / failure modes.
- Persisting the full preprocessing+model pipeline together.

### Adaptation made for IN6227

The submitted project is intentionally simpler than the upstream skill:

- Uses scikit-learn only.
- Uses Dummy + Logistic Regression + Random Forest + Gradient Boosting as the small candidate set.
- Uses explicit JSON artifacts and an assignment-specific report pipeline.
- Adds human-oversight gates for the Variant 2 reflection requirement.
- Does not adopt XGBoost / LightGBM by default.
- Does not adopt the whole Claude scaffold.

### Important consistency note

The upstream tabular SKILL explicitly uses `DummyClassifier(strategy="most_frequent")`.

If this project intentionally uses `strategy="stratified"` instead, `SKILL.md`, code, report, and reflection should all say so consistently and explain the adaptation. Do not claim the exact Dummy strategy was copied from upstream if it differs.

No claim is made that upstream source code was copied.

---

## 5. citriac / claude-skills

Repository: https://github.com/citriac/claude-skills  
Default branch observed: `main`  
Relevant skill: `data-analysis/SKILL.md`  
Exact file:
https://github.com/citriac/claude-skills/blob/main/data-analysis/SKILL.md

The skill frontmatter declares `license: MIT`.

### Specific structure verified

The data-analysis skill uses a six-step workflow:

1. Load and profile data.
2. Compute descriptive statistics.
3. Identify trends and patterns.
4. Perform correlation / hypothesis testing.
5. Detect anomalies / outliers.
6. Synthesize findings into a report.

It also includes explicit "Best Practices" and "Edge Cases", with concrete threshold-style examples such as:

- warn when a target has >30% missing values,
- flag extreme skewness beyond |2.0|,
- flag predictor correlation above 0.9,
- special handling for small samples (`n < 30`).

### Design ideas legitimately borrowed

- Numbered operational workflow.
- Explicit Best Practices / Edge Cases.
- Threshold-triggered warnings rather than vague prose.
- Report limitations and caveats instead of silently making assumptions.

### Important scope limitation

This is a **general data-analysis skill**, not a tabular-classification model-selection skill.

Therefore it should be cited as a structural / workflow reference only. It should **not** be used as evidence for the Dummy→LogReg→GBM ladder, scikit-learn leakage-safe modeling, or class-imbalance model rules. Those are better supported by the BrendenKennedy tabular SKILL and scikit-learn practice.

---

# Verified provenance summary

| Source | What is actually supported | How this project adapts it |
|---|---|---|
| AutoGluon | task inference, learner/trainer separation, leaderboard, CV/OOF concepts, unseen-test discipline | profile → train/evaluate → structured report |
| FLAML | economical AutoML / low-cost search | small model pool, restrained tuning |
| MLJAR Supervised | structured machine-readable reports + Markdown reporting | `profile.json`, `results.json`, `run_manifest.json` → report |
| BrendenKennedy tabular SKILL | leakage-safe pipeline, baseline ladder, CV rules, imbalance rules, named traps | core SKILL decision rules |
| citriac data-analysis SKILL | six-step workflow, best practices, thresholded edge cases | workflow structure and explicit warnings |

---

# Recommended wording for README / SKILL provenance

> The SKILL design was informed by public open-source references rather than copied from a single implementation. AutoGluon influenced the separation of profiling, model orchestration and leaderboard-style comparison; FLAML influenced the deliberately economical model search; MLJAR Supervised influenced the use of machine-readable structured artifacts feeding automated reporting; BrendenKennedy's tabular SKILL provided the strongest direct reference for leakage-safe sklearn pipelines, baseline-first model selection, cross-validation discipline and named failure modes; and citriac's data-analysis SKILL influenced the numbered workflow and explicit edge-case rules. The submitted implementation is a lightweight scikit-learn design developed specifically for IN6227 and does not depend on those frameworks at runtime.

---

# What should NOT be claimed

Do not claim any of the following unless separate evidence is preserved:

- that the current Trae session personally read the original repositories before implementation;
- that a specific upstream commit was the exact commit used by WorkBuddy, unless that commit was recorded at the time;
- that upstream source code was copied;
- that citriac's skill contains the classification model ladder;
- that AutoGluon's entire AutoML architecture was reproduced;
- that current GitHub star counts are part of the technical justification.

This document is an independent verification of the public sources and of the specific concepts that they actually support.
