# IN6227-Assignment-1 — Variant-2

**Name:** [PLACEHOLDER: Enter your full name]  
**Matric number:** [PLACEHOLDER: Enter your matric number]  
**Model (LLM):** GLM-5.2  
**LLM interface:** TraeCode (Codex)  
**GitHub:** [PLACEHOLDER: Enter your GitHub repository link]

---

## 1. Data Exploration & Cleaning

The dataset **train** contains **31112** rows and **15** features. The target variable is **`label`** with 2 classes: no, yes.

Class distribution (train): no=23645, yes=7464 (imbalance ratio 3.168:1).

**Column types:** 7 numeric, 8 categorical. Total missing values: 50 (0.01% of cells). Rows with missing target were dropped (3 dropped). No duplicate rows were removed (0 found).

## 2. Feature Selection / Engineering

All 15 original features are retained — no manual feature selection is applied. The preprocessing is **leakage-safe**: every learned transformation (imputation, scaling, encoding) lives inside an sklearn `Pipeline` / `ColumnTransformer`.

- **Numeric features** (7): median imputation → standard scaling.
- **Categorical features** (8): most-frequent imputation → one-hot encoding (`handle_unknown="ignore"`).

No new features are engineered; the data already contains derived fields (e.g. `composite_rank`).

## 3. Model Training

Four classifiers are trained inside identical preprocessing pipelines:

| Model | Key hyper-parameters |
|---|---|
| DummyClassifier | strategy=stratified (baseline) |
| LogisticRegression | max_iter=1000, class_weight=balanced |
| RandomForest | n_estimators=200, class_weight=balanced |
| GradientBoosting | n_estimators=100, max_depth=3, lr=0.1 |

**Cross-validation:** Stratified 5-fold (`random_state=42`). Model selection uses **mean CV F1**. The best model (**random_forest**) is then retrained on the full training set and evaluated **once** on the held-out test set.

## 4. Evaluation & Comparison

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|
| dummy | 0.6351 | 0.2365 | 0.2337 | 0.2351 | 0.4978 | 0.2391 |
| logistic_regression | 0.7903 | 0.5401 | 0.8493 | 0.6602 | 0.8905 | 0.7049 |
| random_forest **(best)** | 0.8266 | 0.6204 | 0.7146 | 0.6641 | 0.8892 | 0.7058 |
| gradient_boosting | 0.8392 | 0.7083 | 0.5610 | 0.6260 | 0.8913 | 0.7131 |

**Test-set performance (best model: random_forest):** accuracy=0.8272, precision=0.6177, recall=0.7156, F1=0.6631, ROC-AUC=0.8887, PR-AUC=0.7010.

![Confusion matrix](plots/confusion_matrix.png)
![ROC curve](plots/roc_curve.png)

## 5. Findings & Discussion

- **Best model:** random_forest, selected by CV F1=0.6641.
- The Dummy baseline (accuracy≈0.6351) confirms that a no-information classifier cannot beat the majority class.
- random_forest improves F1 from 0.2351 (dummy) to 0.6641 (CV) — a meaningful gain.
- `class_weight="balanced"` is used for LogisticRegression and RandomForest to counter the 3.2:1 class imbalance, trading a small accuracy drop for substantially higher recall on the minority class.
- SMOTE is intentionally **not** applied; `class_weight` suffices and avoids synthetic-sample leakage risks.

All numerical values in this report are pulled directly from `results.json`; none are manually entered.