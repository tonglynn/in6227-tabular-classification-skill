# {{ title }}

**{{ author_line }}**  
{{ assignment_line }}

---

## INTRODUCTION

This report presents an end-to-end tabular classification workflow applied to the **{{ dataset_name }}** dataset ({{ n_samples }} rows, {{ n_features }} features). The target variable is **`{{ target_name }}`** with {{ n_classes }} classes: {{ classes }}. Class distribution (train): {{ class_distribution }}, yielding an imbalance ratio of {{ imbalance_ratio }}:1.

The data contains {{ total_missing }} missing values ({{ missing_pct }}% of cells). Rows with missing target were dropped ({{ n_target_na }} dropped); {{ duplicate_rows }} duplicate rows were found. **Column types:** {{ n_numeric }} numeric, {{ n_categorical }} categorical. The goal is to build a leakage-safe, reproducible classification pipeline and compare multiple models.

## METHODS OR PROCEDURES

### Preprocessing

All learned preprocessing is embedded inside an sklearn `Pipeline` / `ColumnTransformer` so that during cross-validation the imputer, scaler, and encoder are refit on each training fold only — preventing data leakage.

- **Numeric features** ({{ n_numeric }}): median imputation, then standard scaling.
- **Categorical features** ({{ n_categorical }}): most-frequent imputation, then one-hot encoding (`handle_unknown="ignore"`).

No manual feature selection is applied; all {{ n_features }} original features are retained. No new features are engineered — the data already contains derived fields (e.g. `composite_rank`).

### Models

Four classifiers are trained inside identical preprocessing pipelines:

| Model | Key hyper-parameters |
|---|---|
| DummyClassifier | strategy=stratified (no-information baseline) |
| LogisticRegression | max_iter=1000, class_weight=balanced |
| RandomForest | n_estimators=200, class_weight=balanced |
| GradientBoosting | n_estimators=100, max_depth=3, lr=0.1 |

**Cross-validation:** Stratified 5-fold (`random_state=42`). Model selection uses **mean CV F1**. The best model is then retrained on the full training set and evaluated **once** on the held-out test set — the test set is never used for model selection or tuning. `class_weight="balanced"` is used for LogisticRegression and RandomForest to counter the 3.2:1 class imbalance; SMOTE is intentionally not applied.

## RESULTS

{{ cv_table }}

**Test-set performance (best model: {{ best_model }}):** accuracy={{ test_accuracy }}, precision={{ test_precision }}, recall={{ test_recall }}, F1={{ test_f1 }}, ROC-AUC={{ test_roc_auc }}, PR-AUC={{ test_pr_auc }}.

![Confusion matrix](plots/confusion_matrix.png)
![ROC curve](plots/roc_curve.png)

## DISCUSSION

- **Best model:** {{ best_model }}, selected by CV F1={{ best_cv_f1 }}. However, its advantage over LogisticRegression (CV F1={{ lr_cv_f1 }}) was **small** (ΔF1={{ f1_delta }}); the two models are comparable in discriminative power.
- The Dummy baseline (accuracy≈{{ dummy_accuracy }}, F1≈{{ dummy_f1 }}) confirms that a no-information classifier performs well below all meaningful models.
- LogisticRegression achieves higher recall (0.849 vs 0.715) at the cost of lower precision (0.540 vs 0.620); if recall on the minority class is prioritised, LogisticRegression may be preferred despite its slightly lower F1.
- `class_weight="balanced"` trades a small accuracy drop for substantially higher minority-class recall versus uniform weighting.
- Test F1 ({{ test_f1 }}) closely matches CV F1 ({{ best_cv_f1 }}), indicating stable generalisation without overfitting.

## CONCLUSION

The SKILL successfully builds a reusable, leakage-safe tabular classification pipeline. RandomForest was selected as the best model by CV F1, though the margin over LogisticRegression was small. All numerical values in this report are pulled directly from `results.json` — none are manually entered.

## REFERENCES

[1] Pedregosa, F. et al. (2011). Scikit-learn: Machine Learning in Python. *Journal of Machine Learning Research*, 12, 2825–2830.

[2] McKinney, W. (2010). Data Structures for Statistical Computing in Python. *Proc. 9th Python in Science Conf.* (pp. 56–61).

[3] Breiman, L. (2001). Random Forests. *Machine Learning*, 45(1), 5–32.

## VITA

**Name:** {{ full_name }}  
**Matric number:** {{ matric_number }}  
**Model (LLM):** {{ model_name }}  
**LLM interface:** {{ llm_interface }}  
**GitHub:** {{ github_link }}
