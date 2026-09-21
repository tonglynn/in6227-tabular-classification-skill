#!/usr/bin/env python3
"""Generalization test for the tabular classification SKILL.

Runs the full pipeline (profiler → train_eval) on two sklearn built-in
datasets to verify that no component hard-codes target names, feature
names, or dataset-specific logic.

Datasets:
  1. Breast Cancer (binary, 30 numeric features)
  2. Iris (multiclass, 4 numeric features)

Usage:
  python tests/test_generalization.py
"""
import json
import os
import sys
import tempfile

# Add scripts dir to path
SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts")
sys.path.insert(0, SCRIPTS_DIR)

from data_profiler import build_profile, build_preprocess_config
from train_eval import (
    build_preprocessor, make_model_pipeline, get_models, scoring_dict,
    compute_pr_auc_cv, compute_test_metrics, plot_feature_importance,
)
from sklearn.datasets import load_breast_cancer, load_iris
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.preprocessing import LabelEncoder
import numpy as np
import pandas as pd
import time


def run_dataset(name: str, X: pd.DataFrame, y, target_name: str):
    """Run the full pipeline on a dataset and verify it works."""
    print(f"\n{'='*60}")
    print(f"  Generalization test: {name}")
    print(f"{'='*60}")

    df = X.copy()
    df[target_name] = y

    # Profile
    profile = build_profile(df, target_name, name)
    config = build_preprocess_config(profile)
    problem_type = config["problem_type"]
    print(f"  Shape: {df.shape}  Target: {target_name}  Type: {problem_type}")
    print(f"  Numeric: {len(profile['numeric_columns'])}  Categorical: {len(profile['categorical_columns'])}")
    print(f"  Classes: {profile['target']['classes']}")

    # Train / test split (80/20)
    from sklearn.model_selection import train_test_split
    train_df, test_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df[target_name])

    y_train = LabelEncoder().fit_transform(train_df[target_name])
    X_train = train_df.drop(columns=[target_name])
    y_test = LabelEncoder().fit_transform(test_df[target_name])
    X_test = test_df.drop(columns=[target_name])

    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)  # 3 folds for speed
    models = get_models(problem_type)
    scoring = scoring_dict(problem_type)

    cv_metric_keys = ["accuracy", "precision", "recall", "f1", "roc_auc"]
    all_ok = True

    for model_name, model in models.items():
        prep = build_preprocessor(config)
        pipe = make_model_pipeline(prep, model)
        cv_res = cross_validate(pipe, X_train, y_train, cv=cv, scoring=scoring, n_jobs=-1)
        cv_mean = {k: float(np.mean(cv_res[f"test_{k}"])) for k in cv_metric_keys}

        # PR-AUC
        prep2 = build_preprocessor(config)
        model2 = get_models(problem_type)[model_name]
        pipe2 = make_model_pipeline(prep2, model2)
        pr_auc = compute_pr_auc_cv(pipe2, X_train, y_train, cv)
        cv_mean["pr_auc"] = pr_auc

        # Test
        best_prep = build_preprocessor(config)
        best_pipe = make_model_pipeline(best_prep, model)
        best_pipe.fit(X_train, y_train)
        test_m = compute_test_metrics(best_pipe, X_test, y_test, problem_type)

        status = "OK" if not np.isnan(cv_mean["f1"]) and not np.isnan(test_m["f1"]) else "FAIL"
        if status == "FAIL":
            all_ok = False
        print(f"  [{status}] {model_name}: CV F1={cv_mean['f1']:.4f}  Test F1={test_m['f1']:.4f}  "
              f"Test AUC={test_m.get('roc_auc', float('nan')):.4f}")

    # Feature importance for RF
    rf_prep = build_preprocessor(config)
    rf_pipe = make_model_pipeline(rf_prep, get_models(problem_type)["random_forest"])
    rf_pipe.fit(X_train, y_train)
    fi = plot_feature_importance(rf_pipe, rf_prep, 10, os.path.join(tempfile.gettempdir(), f"{name}_fi.png"))
    if fi:
        print(f"  Feature importance (top 3): {fi[:3]}")

    return all_ok


def main():
    print("=" * 60)
    print("  SKILL Generalization Tests")
    print("=" * 60)

    results = []

    # 1. Breast Cancer (binary)
    bc = load_breast_cancer(as_frame=True)
    X_bc = bc.data
    y_bc = bc.target.astype(str).replace({"0": "malignant", "1": "benign"})
    ok = run_dataset("breast_cancer", X_bc, y_bc, "diagnosis")
    results.append(("breast_cancer", ok))

    # 2. Iris (multiclass)
    iris = load_iris(as_frame=True)
    X_iris = iris.data
    y_iris = pd.Series(iris.target).map({0: "setosa", 1: "versicolor", 2: "virginica"})
    ok = run_dataset("iris", X_iris, y_iris, "species")
    results.append(("iris", ok))

    # Summary
    print(f"\n{'='*60}")
    print("  SUMMARY")
    print(f"{'='*60}")
    for name, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}: {name}")

    if all(ok for _, ok in results):
        print("\n  All generalization tests PASSED.")
        return 0
    else:
        print("\n  Some generalization tests FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
