# Decision Guide — Tabular Classification

Reference tables for preprocessing and model decisions used by the SKILL.

## 1. Column Type Detection

| Condition | Classification |
|---|---|
| `pd.api.types.is_numeric_dtype` is True | numeric |
| dtype is `object`, `str`, `category`, `bool` | categorical |
| Numeric with ≤ 2 unique non-null values | numeric (kept numeric for scaling) |

## 2. Imputation Strategy

| Column type | Strategy | Rationale |
|---|---|---|
| Numeric | `SimpleImputer(strategy="median")` | Robust to outliers |
| Categorical | `SimpleImputer(strategy="most_frequent")` | Preserves most common category |

Rows with missing target are dropped (`dropna(subset=[target])`).

## 3. Scaling / Encoding

| Column type | Transformer | Parameters |
|---|---|---|
| Numeric | `StandardScaler` | mean=0, std=1 (helps LR convergence) |
| Categorical | `OneHotEncoder` | `handle_unknown="ignore"`, `sparse_output=False` |

For very high-cardinality categoricals (> 50 unique), consider
`OneHotEncoder(min_frequency=...)` or target encoding.  Not needed for
the current dataset (max 21 unique).

## 4. Model Selection

| Model | Role | Hyper-parameters | When to use |
|---|---|---|---|
| `DummyClassifier` | Baseline | `strategy="stratified"` | Always — no-information lower bound |
| `LogisticRegression` | Linear | `max_iter=1000`, `class_weight="balanced"` | Interpretable, fast, good for sparse one-hot features |
| `RandomForestClassifier` | Nonlinear | `n_estimators=200`, `class_weight="balanced"` | Robust, handles mixed feature types, feature importance |
| `GradientBoostingClassifier` | Strong | `n_estimators=100`, `max_depth=3`, `learning_rate=0.1` | High accuracy on tabular data |

## 5. Class Imbalance Decision

| Imbalance ratio | Strategy |
|---|---|
| < 3:1 | No special treatment |
| 3:1 – 10:1 | `class_weight="balanced"` (if supported); justify with recall/F1 |
| > 10:1 | `class_weight="balanced"` + threshold tuning; never auto-SMOTE |

Do not automatically apply SMOTE.  Synthetic oversampling can introduce
leakage if not done inside the CV loop.

## 6. Cross-Validation

| Setting | Value | Rationale |
|---|---|---|
| Splitter | `StratifiedKFold` | Preserves class proportions |
| n_splits | 5 | Standard, good bias-variance trade-off |
| shuffle | True | Randomize fold composition |
| random_state | 42 | Reproducibility |

## 7. Metric Selection

| Metric | Scikit-learn scorer | Average method |
|---|---|---|
| Accuracy | `accuracy` | — |
| Precision | `precision` / `precision_weighted` | binary / multiclass |
| Recall | `recall` / `recall_weighted` | binary / multiclass |
| F1 | `f1` / `f1_weighted` | binary / multiclass (primary selection) |
| ROC-AUC | `roc_auc` / `roc_auc_ovr_weighted` | binary / multiclass |
| PR-AUC | `average_precision_score` | via `cross_val_predict` |

## 8. Model Selection Criterion

Primary: **mean CV F1** (balances precision and recall, important under
imbalance).

Tie-breaker: ROC-AUC, then PR-AUC.
