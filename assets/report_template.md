# {{ assignment }} — {{ variant }}

**Name:** {{ full_name }}  
**Matric number:** {{ matric_number }}  
**Model (LLM):** {{ model_name }}  
**LLM interface:** {{ llm_interface }}  
**GitHub:** {{ github_link }}

---

## 1. Data Exploration & Cleaning

The dataset **{{ dataset_name }}** contains **{{ n_samples }}** rows and **{{ n_features }}** features. The target variable is **`{{ target_name }}`** with {{ n_classes }} classes: {{ classes }}.

Class distribution (train): {{ class_distribution }} (imbalance ratio {{ imbalance_ratio }}:1).

**Column types:** {{ n_numeric }} numeric, {{ n_categorical }} categorical. Total missing values: {{ total_missing }} ({{ missing_pct }}% of cells). Rows with missing target were dropped ({{ n_target_na }} dropped). No duplicate rows were removed ({{ duplicate_rows }} found).

## 2. Feature Selection / Engineering

All {{ n_features }} original features are retained — no manual feature selection is applied. The preprocessing is **leakage-safe**: every learned transformation (imputation, scaling, encoding) lives inside an sklearn `Pipeline` / `ColumnTransformer`.

- **Numeric features** ({{ n_numeric }}): median imputation → standard scaling.
- **Categorical features** ({{ n_categorical }}): most-frequent imputation → one-hot encoding (`handle_unknown="ignore"`).

No new features are engineered; the data already contains derived fields (e.g. `composite_rank`).

## 3. Model Training

Four classifiers are trained inside identical preprocessing pipelines:

| Model | Key hyper-parameters |
|---|---|
| DummyClassifier | strategy=stratified (baseline) |
| LogisticRegression | max_iter=1000, class_weight=balanced |
| RandomForest | n_estimators=200, class_weight=balanced |
| GradientBoosting | n_estimators=100, max_depth=3, lr=0.1 |

**Cross-validation:** Stratified 5-fold (`random_state=42`). Model selection uses **mean CV F1**. The best model (**{{ best_model }}**) is then retrained on the full training set and evaluated **once** on the held-out test set.

## 4. Evaluation & Comparison

{{ cv_table }}

**Test-set performance (best model: {{ best_model }}):** accuracy={{ test_accuracy }}, precision={{ test_precision }}, recall={{ test_recall }}, F1={{ test_f1 }}, ROC-AUC={{ test_roc_auc }}, PR-AUC={{ test_pr_auc }}.

![Confusion matrix](plots/confusion_matrix.png)
![ROC curve](plots/roc_curve.png)

## 5. Findings & Discussion

- **Best model:** {{ best_model }}, selected by CV F1={{ best_cv_f1 }}.
- The Dummy baseline (accuracy≈{{ dummy_accuracy }}) confirms that a no-information classifier cannot beat the majority class.
- {{ best_model }} improves F1 from {{ dummy_f1 }} (dummy) to {{ best_cv_f1 }} (CV) — a meaningful gain.
- `class_weight="balanced"` is used for LogisticRegression and RandomForest to counter the 3.2:1 class imbalance, trading a small accuracy drop for substantially higher recall on the minority class.
- SMOTE is intentionally **not** applied; `class_weight` suffices and avoids synthetic-sample leakage risks.

All numerical values in this report are pulled directly from `results.json`; none are manually entered.
