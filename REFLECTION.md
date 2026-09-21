# REFLECTION — IN6227 Assignment 1, Variant 2

## 1. Human Oversight

### Oversight gates designed into the SKILL

The SKILL incorporates several **designed-in** oversight mechanisms —
i.e., safeguards built into the workflow that would constrain a human
practitioner in the same way. These are gates in the *design*; they
are enforced automatically by the code, not manually approved by a
human at each step.

| Gate | Where enforced | What it prevents |
|---|---|---|
| **Preprocessing inside Pipeline** | `train_eval.py` — `ColumnTransformer` embedded in `Pipeline` | Fitting imputer/scaler/encoder on the full dataset before CV (leakage) |
| **Stratified K-Fold CV** | `train_eval.py` — `StratifiedKFold(shuffle=True, random_state=42)` | Class proportion drift across folds |
| **Test set used once** | `train_eval.py` — best model retrained on full train, evaluated on test only after selection | Using test data for model selection or tuning |
| **Target excluded from features** | `train_eval.py` — `X = df.drop(columns=[target])` | Target leakage into feature matrix |
| **Rows with NA target dropped** | `train_eval.py` — `df.dropna(subset=[target])` | Training on undefined labels |
| **No manual metric entry** | `generate_report.py` — all values come from `results.json` | Fabricated or altered performance numbers |
| **PDF page-count check** | `render_pdf.py` — verifies ≤ 2 pages via `pypdf` | Over-length report |
| **Generalization test** | `tests/test_generalization.py` — runs pipeline on Breast Cancer & Iris | Hard-coded dataset logic |
| **Official template alignment** | `render_pdf.py` — Times-Roman 10pt, sections: INTRODUCTION / METHODS / RESULTS / DISCUSSION / CONCLUSION / REFERENCES / VITA, running header | Ignoring official report template |

**Important distinction:** These gates are *designed into the SKILL* —
they run automatically when the scripts execute. The student did **not**
manually sit at each gate and approve/reject decisions during this
automated implementation. The gates are code-enforced safeguards, not
human-in-the-loop checkpoints that were triggered one by one.

### Oversight actually exercised during this implementation

The following checks were *actually performed* (by the AI agent, not by
the student) during the automated run:

- The AI agent inspected the existing project state (3 files only),
  classified each component as MISSING, and proceeded to build from
  scratch while preserving the valid `README.md`, `requirements.txt`,
  and `.gitignore`.
- The dataset was independently profiled and verified against the
  sanity-check expectations (31 112 × 16, target `label`, no : 23 645,
  yes : 7 464, imbalance 3.168 : 1). All matched.
- The profiler was run, its output (`profile.json`) was inspected, and
  the preprocessing config was confirmed to use median imputation for
  numerics and most-frequent imputation + one-hot encoding for
  categoricals — consistent with the leakage rules.
- The training script was executed end-to-end; CV and test metrics were
  printed to the console and cross-checked against `results.json`.
- The official `IN6227-Reports-Template.doc` was inspected (via Word COM
  automation) to extract its required sections (INTRODUCTION, METHODS OR
  PROCEDURES, RESULTS, DISCUSSION, CONCLUSION, REFERENCES, VITA) and
  formatting (Times New Roman 10pt). The report template was then
  restructured to match.
- The report was generated from `results.json` and verified to contain
  matching numbers (see §3 below).
- The PDF page count was verified to be 2.
- Generalization tests on Breast Cancer (binary) and Iris (multiclass)
  were executed to confirm no hard-coded target names or feature names.

## 2. Critical Evaluation

### What works well

- **Leakage safety**: all preprocessing lives inside sklearn
  `Pipeline` / `ColumnTransformer`, so during cross-validation the
  imputer, scaler, and encoder are refit on each training fold only.
  The test set is never touched during model selection.
- **Metric coverage**: six metrics (Accuracy, Precision, Recall, F1,
  ROC-AUC, PR-AUC) are computed for every model, both in CV and on the
  test set. F1 is used as the selection metric because it balances
  precision and recall — important under the 3.2 : 1 imbalance.
- **Reproducibility**: `random_state=42` is set everywhere; the
  `run_manifest.json` records the environment (Python, sklearn, numpy,
  pandas versions), scripts executed, timing, and leakage-safety flags.
- **Generalization**: no target name, feature name, or row count is
  hard-coded. The pipeline was tested on two sklearn datasets with
  different shapes, feature counts, and problem types (binary vs
  multiclass).
- **Automated reporting**: `report.md` and `report.pdf` are generated
  entirely from structured JSON outputs — no manual number entry.

### Limitations and honest caveats

- **No hyperparameter tuning**: model hyper-parameters are sensible
  defaults, not tuned. A grid search inside the CV loop could improve
  results, but was deliberately omitted to keep the SKILL simple and
  transparent (as the assignment requires).
- **No feature engineering**: all original features are used. The data
  already contains derived fields (e.g. `composite_rank`), so additional
  engineering may or may not help. This is a deliberate design choice
  for generality — engineered features tend to be dataset-specific.
- **No explicit feature selection**: feature importance is computed and
  reported (RandomForest), but no features are dropped. For a production
  deployment, recursive feature elimination could reduce noise, but for
  an academic assignment the full-feature approach is more transparent.
- **GradientBoosting**: included as a strong tabular baseline, but it
  was not the best model here (CV F1 = 0.626 vs RandomForest 0.664).
  This is because GradientBoosting lacks `class_weight="balanced"` and
  its recall on the minority class is lower.
- **`class_weight` vs SMOTE**: the SKILL uses `class_weight="balanced"`
  instead of SMOTE. This avoids the risk of synthetic-sample leakage
  if SMOTE were applied outside the CV loop, and is the recommended
  approach for moderate imbalance.
- **Placeholders for personal info**: matric number, full name, and
  GitHub link are clearly marked placeholders. These should be filled in
  by the student before submission.

### Model comparison insight

| Model | CV F1 | CV AUC | Test F1 | Test AUC |
|---|---|---|---|---|
| Dummy | 0.235 | 0.498 | — | — |
| LogisticRegression | 0.660 | 0.890 | — | — |
| RandomForest | 0.664 | 0.889 | 0.663 | 0.889 |
| GradientBoosting | 0.626 | 0.891 | — | — |

RandomForest achieved the highest mean CV F1, but its advantage over
LogisticRegression was **small** (ΔF1 = 0.004). LogisticRegression has
comparable AUC but higher recall (0.849 vs 0.715) at the cost of lower
precision (0.540 vs 0.620). If recall on the minority class is
prioritised (e.g., the "yes" class represents a costly event),
LogisticRegression with `class_weight="balanced"` might be preferred
despite the slightly lower F1. The two models are comparable in
discriminative power; the choice between them depends on the
precision-recall trade-off preferred by the application.

## 3. Trustworthiness

### Independent verification of concrete results

The following checks were performed to verify that the structured
outputs are self-consistent and trustworthy:

#### 3.1 Target counts

From `profile.json`:
```json
"counts": {"no": 23645, "yes": 7464}
```

Total: 23 645 + 7 464 = 31 109 (matches `n_samples` after dropping 3
NA-target rows from the original 31 112).

Independently verified via:
```python
import pandas as pd
df = pd.read_csv("train.csv").dropna(subset=["label"])
print(df["label"].value_counts())
# no    23645
# yes    7464
```

#### 3.2 One metric

From `results.json`, RandomForest CV mean F1: `0.6641119844308345`.
The report.md shows `0.6641` (4 dp). ✓ Consistent.

From `results.json`, test F1: `0.66305937408599`.
The report.md shows `0.6631` (4 dp). ✓ Consistent.

#### 3.3 Confusion matrix totals

From `results.json`:
```json
"confusion_matrix": [[8762, 1403], [901, 2267]]
```

Row totals: 8762 + 1403 = 10 165 (true "no"), 901 + 2267 = 3 168 (true "yes").
Grand total: 10 165 + 3 168 = 13 333 = `n_test`. ✓

Expected test class proportions: no ≈ 76.0%, yes ≈ 24.0%.
Actual: 10 165 / 13 333 = 76.2%, 3 168 / 13 333 = 23.8%. ✓ Close to
train distribution.

#### 3.4 Report / result consistency

Every number in `report.md` was cross-checked against `results.json`:

| Metric (report.md) | results.json value | Match? |
|---|---|---|
| CV accuracy (RF) 0.8266 | 0.8265775... | ✓ |
| CV F1 (RF) 0.6641 | 0.6641119... | ✓ |
| CV AUC (RF) 0.8892 | 0.8892434... | ✓ |
| Test accuracy 0.8272 | 0.8271956... | ✓ |
| Test F1 0.6631 | 0.6630593... | ✓ |
| Test AUC 0.8887 | 0.8886713... | ✓ |
| Dummy accuracy 0.6351 | 0.6351214... | ✓ |
| Dummy F1 0.2351 | 0.2350554... | ✓ |

All values match to 4 decimal places. No metric was manually entered or
altered.

### Trust assessment

| Aspect | Assessment |
|---|---|
| Data integrity | Original `train.csv` / `test.csv` unchanged — only read, never written |
| Leakage prevention | All preprocessing inside Pipeline; CV refits per fold; test used once |
| Metric correctness | Computed by sklearn `cross_validate` and `cross_val_predict`; independently verified |
| Report consistency | All report numbers trace to `results.json`; verified cell-by-cell |
| Official template alignment | Report uses INTRODUCTION / METHODS / RESULTS / DISCUSSION / CONCLUSION / REFERENCES / VITA sections; Times-Roman 10pt; running header matches `IN6227-Reports-Template.doc` |
| Reproducibility | `random_state=42` everywhere; `run_manifest.json` records actual Python/sklearn/numpy/pandas versions |
| Generalization | Tested on 2 additional datasets (binary + multiclass) without code changes |
| No fabrication | Personal info uses clear placeholders; no invented identity, GitHub link, or version |
| Model comparison honesty | Report does not overstate RF's advantage over LogReg (ΔF1=0.004, described as "small") |

---

*This reflection was written by the AI agent (GLM-5.2 via TraeCode)
that implemented the SKILL. Actions attributed to "the AI agent" were
actually performed; actions attributed to "the student" were not
fabricated.*
