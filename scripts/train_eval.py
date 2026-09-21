#!/usr/bin/env python3
"""Leakage-safe model training and evaluation for tabular classification.

All preprocessing (imputation, scaling, encoding) is embedded inside
sklearn Pipeline / ColumnTransformer so that during cross-validation the
preprocessing is refit on each training fold only.  The held-out test set
is used exactly once, after model selection.

Outputs:
  results.json       — all metrics, feature importance, confusion matrix
  run_manifest.json  — run metadata (scripts, params, timing, env)
  plots/             — target distribution, confusion matrix, ROC curve,
                        feature importance
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix,
)
from sklearn.model_selection import StratifiedKFold, cross_validate, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelEncoder
from sklearn.impute import SimpleImputer

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# ── Helpers ──────────────────────────────────────────────────────────────

def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_preprocessor(config: dict) -> ColumnTransformer:
    """Build the ColumnTransformer from the preprocessing config."""
    num_cfg = config["numeric"]
    cat_cfg = config["categorical"]

    numeric_steps = [
        ("imputer", SimpleImputer(strategy=num_cfg["imputer"])),
    ]
    if num_cfg.get("scaler") == "standard":
        numeric_steps.append(("scaler", StandardScaler()))
    numeric_pipeline = Pipeline(numeric_steps)

    categorical_steps = [
        ("imputer", SimpleImputer(strategy=cat_cfg["imputer"])),
        ("encoder", OneHotEncoder(
            handle_unknown=cat_cfg.get("handle_unknown", "ignore"),
            sparse_output=False,
        )),
    ]
    categorical_pipeline = Pipeline(categorical_steps)

    transformers = []
    if num_cfg["columns"]:
        transformers.append(("num", numeric_pipeline, num_cfg["columns"]))
    if cat_cfg["columns"]:
        transformers.append(("cat", categorical_pipeline, cat_cfg["columns"]))

    return ColumnTransformer(transformers=transformers, remainder="drop")


def make_model_pipeline(preprocessor: ColumnTransformer, model) -> Pipeline:
    return Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", model),
    ])


def get_models(problem_type: str) -> dict:
    """Return model dict: name -> estimator (no preprocessor)."""
    is_binary = problem_type == "binary_classification"
    cw = "balanced" if is_binary else None

    models = {
        "dummy": DummyClassifier(strategy="stratified", random_state=42),
        "logistic_regression": LogisticRegression(
            max_iter=1000, class_weight=cw, random_state=42, solver="lbfgs",
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=200, max_depth=None, min_samples_leaf=2,
            class_weight=cw, random_state=42, n_jobs=-1,
        ),
        "gradient_boosting": GradientBoostingClassifier(
            n_estimators=100, max_depth=3, learning_rate=0.1,
            random_state=42,
        ),
    }
    return models


def scoring_dict(problem_type: str) -> dict:
    """Build a scoring dict for cross_validate."""
    if problem_type == "binary_classification":
        return {
            "accuracy": "accuracy",
            "precision": "precision",
            "recall": "recall",
            "f1": "f1",
            "roc_auc": "roc_auc",
        }
    return {
        "accuracy": "accuracy",
        "precision": "precision_weighted",
        "recall": "recall_weighted",
        "f1": "f1_weighted",
        "roc_auc": "roc_auc_ovr_weighted",
    }


def compute_pr_auc_cv(pipeline, X, y, cv) -> float:
    """Compute cross-validated PR-AUC (average precision)."""
    try:
        proba = cross_val_predict(pipeline, X, y, cv=cv, method="predict_proba")
        return float(average_precision_score(y, proba[:, 1]))
    except Exception:
        return float("nan")


def compute_test_metrics(pipeline, X_test, y_test, problem_type: str) -> dict:
    """Evaluate a fitted pipeline on the test set."""
    y_pred = pipeline.predict(X_test)
    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, average="binary" if problem_type == "binary_classification" else "weighted", zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, average="binary" if problem_type == "binary_classification" else "weighted", zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, average="binary" if problem_type == "binary_classification" else "weighted", zero_division=0)),
    }
    # ROC-AUC / PR-AUC (needs probabilities)
    try:
        proba = pipeline.predict_proba(X_test)
        n_classes = proba.shape[1]
        if problem_type == "binary_classification" and n_classes == 2:
            metrics["roc_auc"] = float(roc_auc_score(y_test, proba[:, 1]))
            metrics["pr_auc"] = float(average_precision_score(y_test, proba[:, 1]))
        else:
            metrics["roc_auc"] = float(roc_auc_score(y_test, proba, multi_class="ovr", average="weighted"))
            # PR-AUC for multiclass: macro average of per-class AP
            from sklearn.preprocessing import label_binarize
            y_bin = label_binarize(y_test, classes=sorted(np.unique(y_test)))
            aps = []
            for i in range(n_classes):
                if y_bin.shape[1] > 1:
                    aps.append(average_precision_score(y_bin[:, i], proba[:, i]))
            metrics["pr_auc"] = float(np.mean(aps)) if aps else float("nan")
    except Exception:
        metrics["roc_auc"] = float("nan")
        metrics["pr_auc"] = float("nan")

    metrics["confusion_matrix"] = confusion_matrix(y_test, y_pred).tolist()
    return metrics


# ── Plotting ────────────────────────────────────────────────────────────

def plot_target_distribution(y, target_name, out_path):
    counts = pd.Series(y).value_counts()
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.bar([str(c) for c in counts.index], counts.values, color=["#4C72B0", "#DD8452"][:len(counts)])
    for i, v in enumerate(counts.values):
        ax.text(i, v + max(counts.values) * 0.01, str(v), ha="center", fontsize=8)
    ax.set_title(f"Target distribution: {target_name}")
    ax.set_ylabel("Count")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_confusion_matrix(cm, classes, out_path):
    fig, ax = plt.subplots(figsize=(4, 3.5))
    im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    ax.set_title("Confusion matrix (test)")
    fig.colorbar(im, fraction=0.046, pad=0.04)
    ax.set_xticks(range(len(classes)))
    ax.set_yticks(range(len(classes)))
    ax.set_xticklabels(classes, fontsize=8)
    ax.set_yticklabels(classes, fontsize=8)
    thresh = cm.max() / 2
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], "d"),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black", fontsize=8)
    ax.set_ylabel("True")
    ax.set_xlabel("Predicted")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_roc_curve(pipeline, X_test, y_test, out_path):
    try:
        proba = pipeline.predict_proba(X_test)
        from sklearn.metrics import roc_curve
        fpr, tpr, _ = roc_curve(y_test, proba[:, 1])
        auc = roc_auc_score(y_test, proba[:, 1])
        fig, ax = plt.subplots(figsize=(4, 3.5))
        ax.plot(fpr, tpr, label=f"AUC = {auc:.3f}", color="#4C72B0")
        ax.plot([0, 1], [0, 1], "--", color="grey", lw=1)
        ax.set_xlabel("False positive rate")
        ax.set_ylabel("True positive rate")
        ax.set_title("ROC curve (test)")
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
    except Exception:
        pass


def plot_feature_importance(pipeline, preprocessor, top_k, out_path):
    """Plot top-K feature importances for tree-based models."""
    clf = pipeline.named_steps.get("classifier")
    if not hasattr(clf, "feature_importances_"):
        return None
    importances = clf.feature_importances_
    # Get feature names from the fitted preprocessor
    try:
        feat_names = preprocessor.get_feature_names_out()
    except Exception:
        feat_names = [f"f{i}" for i in range(len(importances))]
    pairs = sorted(zip(feat_names, importances), key=lambda x: -x[1])[:top_k]
    names = [p[0] for p in pairs][::-1]
    vals = [p[1] for p in pairs][::-1]
    fig, ax = plt.subplots(figsize=(5, max(3, len(names) * 0.3)))
    ax.barh(names, vals, color="#55A868")
    ax.set_title(f"Top {top_k} feature importances")
    ax.set_xlabel("Importance")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return [{"feature": str(n), "importance": float(v)} for n, v in pairs]


# ── Main ────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Train and evaluate classifiers (leakage-safe).")
    ap.add_argument("--train", required=True)
    ap.add_argument("--test", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--config", required=True, help="preprocess_config.json")
    ap.add_argument("--profile", default=None, help="profile.json (optional)")
    ap.add_argument("--out", default="results.json")
    ap.add_argument("--manifest-out", default="run_manifest.json")
    ap.add_argument("--plots-dir", default="plots")
    ap.add_argument("--cv-folds", type=int, default=5)
    args = ap.parse_args()

    os.makedirs(args.plots_dir, exist_ok=True)
    t_start = time.time()

    config = load_config(args.config)
    problem_type = config["problem_type"]

    # ── Load data ──
    train_df = pd.read_csv(args.train)
    test_df = pd.read_csv(args.test)

    # Drop rows with missing target (leakage-safe: dropping NA target rows is fine)
    if config.get("drop_target_na", True):
        n_before = len(train_df)
        train_df = train_df.dropna(subset=[args.target])
        test_df = test_df.dropna(subset=[args.target]) if args.target in test_df.columns else test_df
        print(f"[train_eval] Dropped {n_before - len(train_df)} rows with NA target in train")

    X_train = train_df.drop(columns=[args.target])
    y_train = train_df[args.target]
    has_test_target = args.target in test_df.columns
    if has_test_target:
        X_test = test_df.drop(columns=[args.target])
        y_test = test_df[args.target]
    else:
        X_test = test_df
        y_test = None

    # Encode target
    le = LabelEncoder()
    y_train_enc = le.fit_transform(y_train)
    if y_test is not None:
        y_test_enc = le.transform(y_test)
    classes = list(le.classes_)
    print(f"[train_eval] Train: {X_train.shape}  Test: {X_test.shape}")
    print(f"[train_eval] Target classes: {classes}  encoded: {sorted(np.unique(y_train_enc))}")

    # ── Build preprocessor ──
    # Re-derive column lists from the actual data to guarantee generality
    numeric_cols = config["numeric"]["columns"]
    cat_cols = config["categorical"]["columns"]
    # Keep only columns that actually exist
    numeric_cols = [c for c in numeric_cols if c in X_train.columns]
    cat_cols = [c for c in cat_cols if c in X_train.columns]
    config["numeric"]["columns"] = numeric_cols
    config["categorical"]["columns"] = cat_cols

    preprocessor = build_preprocessor(config)
    models = get_models(problem_type)
    scoring = scoring_dict(problem_type)

    cv = StratifiedKFold(n_splits=args.cv_folds, shuffle=True, random_state=42)

    # ── Target distribution plot ──
    plot_target_distribution(y_train_enc, args.target, os.path.join(args.plots_dir, "target_distribution.png"))

    # ── Cross-validation ──
    results = {
        "target": args.target,
        "classes": classes,
        "problem_type": problem_type,
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "n_features": int(len(numeric_cols) + len(cat_cols)),
        "cv_folds": args.cv_folds,
        "models": {},
    }

    cv_metric_keys = ["accuracy", "precision", "recall", "f1", "roc_auc"]

    for name, model in models.items():
        print(f"\n[train_eval] CV: {name}")
        # Fresh preprocessor for each model (avoid fitting same preprocessor twice)
        prep = build_preprocessor(config)
        pipe = make_model_pipeline(prep, model)

        t0 = time.time()
        cv_res = cross_validate(pipe, X_train, y_train_enc, cv=cv, scoring=scoring, n_jobs=-1)
        cv_time = time.time() - t0

        cv_mean = {k: float(np.mean(cv_res[f"test_{k}"])) for k in cv_metric_keys}
        cv_std = {k: float(np.std(cv_res[f"test_{k}"])) for k in cv_metric_keys}

        # PR-AUC via cross_val_predict
        prep2 = build_preprocessor(config)
        model2 = get_models(problem_type)[name]
        pipe2 = make_model_pipeline(prep2, model2)
        pr_auc = compute_pr_auc_cv(pipe2, X_train, y_train_enc, cv)

        cv_mean["pr_auc"] = pr_auc
        cv_std["pr_auc"] = float("nan")

        results["models"][name] = {
            "cv_mean": cv_mean,
            "cv_std": cv_std,
            "cv_time_sec": round(cv_time, 2),
        }
        print(f"  CV mean: accuracy={cv_mean['accuracy']:.4f}  "
              f"f1={cv_mean['f1']:.4f}  roc_auc={cv_mean['roc_auc']:.4f}  "
              f"pr_auc={pr_auc:.4f}  ({cv_time:.1f}s)")

    # ── Select best model by mean CV F1 ──
    best_name = max(results["models"], key=lambda n: results["models"][n]["cv_mean"]["f1"])
    best_model = models[best_name]
    print(f"\n[train_eval] Best model by CV F1: {best_name}")

    # ── Train best on full train, evaluate on test ──
    best_prep = build_preprocessor(config)
    best_pipe = make_model_pipeline(best_prep, best_model)
    best_pipe.fit(X_train, y_train_enc)

    results["best_model"] = best_name
    results["selection_metric"] = "f1"

    if y_test is not None:
        test_metrics = compute_test_metrics(best_pipe, X_test, y_test_enc, problem_type)
        results["test_metrics"] = test_metrics
        print(f"[train_eval] Test: accuracy={test_metrics['accuracy']:.4f}  "
              f"f1={test_metrics['f1']:.4f}  roc_auc={test_metrics.get('roc_auc', float('nan')):.4f}")

        # Plots
        cm = np.array(test_metrics["confusion_matrix"])
        plot_confusion_matrix(cm, classes, os.path.join(args.plots_dir, "confusion_matrix.png"))
        if problem_type == "binary_classification":
            plot_roc_curve(best_pipe, X_test, y_test_enc, os.path.join(args.plots_dir, "roc_curve.png"))

    # Feature importance
    fi = plot_feature_importance(best_pipe, best_prep, 20, os.path.join(args.plots_dir, "feature_importance.png"))
    if fi:
        results["feature_importance"] = fi

    results["run_at"] = datetime.now(timezone.utc).isoformat()

    # ── Write results ──
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n[train_eval] Wrote results -> {args.out}")

    # ── Run manifest ──
    manifest = {
        "run_at": results["run_at"],
        "train_file": os.path.basename(args.train),
        "test_file": os.path.basename(args.test),
        "target": args.target,
        "n_train": results["n_train"],
        "n_test": results["n_test"],
        "cv_folds": args.cv_folds,
        "models_evaluated": list(models.keys()),
        "best_model": best_name,
        "selection_metric": "f1",
        "best_cv_f1": results["models"][best_name]["cv_mean"]["f1"],
        "test_metrics": results.get("test_metrics", {}),
        "total_time_sec": round(time.time() - t_start, 2),
        "scripts": ["data_profiler.py", "train_eval.py", "generate_report.py", "render_pdf.py"],
        "environment": {
            "python": sys.version.split()[0],
            "sklearn": __import__("sklearn").__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
        "leakage_safety": {
            "preprocessing_in_pipeline": True,
            "cv_strategy": "StratifiedKFold",
            "test_used_for_selection": False,
            "target_in_features": False,
        },
    }
    with open(args.manifest_out, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, default=str)
    print(f"[train_eval] Wrote manifest -> {args.manifest_out}")


if __name__ == "__main__":
    main()
