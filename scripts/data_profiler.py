#!/usr/bin/env python3
"""Data profiler for tabular classification datasets.

Generates a JSON profile and a leakage-safe preprocessing configuration.
No transformation is applied to the data here — only inspection.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd


def detect_column_type(series: pd.Series, name: str) -> str:
    """Classify a column as 'numeric' or 'categorical'."""
    dtype = str(series.dtype)
    # Numeric dtypes
    if pd.api.types.is_numeric_dtype(series):
        # Low-cardinality integer could be categorical, but for classification
        # features we keep it numeric so scaling applies.
        return "numeric"
    # Anything else (object, str, category, bool) -> categorical
    return "categorical"


def profile_column(series: pd.Series, name: str) -> dict:
    """Compute profiling stats for one column."""
    n = len(series)
    n_missing = int(series.isna().sum())
    n_unique = int(series.nunique(dropna=True))
    col_type = detect_column_type(series, name)

    info = {
        "name": name,
        "dtype": str(series.dtype),
        "type": col_type,
        "n_unique": n_unique,
        "n_missing": n_missing,
        "missing_pct": round(n_missing / n * 100, 3) if n else 0.0,
    }

    if col_type == "numeric":
        desc = series.describe()
        info.update({
            "min": float(desc.get("min", 0)),
            "max": float(desc.get("max", 0)),
            "mean": float(desc.get("mean", 0)),
            "std": float(desc.get("std", 0)),
            "median": float(series.median()),
            "has_outliers": bool(
                series.between(
                    desc["mean"] - 3 * desc["std"],
                    desc["mean"] + 3 * desc["std"],
                ).mean() < 0.99
            ) if desc.get("std", 0) > 0 else False,
        })
    else:
        top = series.value_counts().head(10)
        info.update({
            "top_values": {str(k): int(v) for k, v in top.items()},
            "mode": str(series.mode().iloc[0]) if not series.mode().empty else None,
        })

    return info


def infer_target(df: pd.DataFrame) -> str:
    """Try to guess the target column name."""
    candidates = ["label", "target", "y", "class", "outcome", "churn"]
    cols_lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand in cols_lower:
            return cols_lower[cand]
    # Last column is a common convention
    return df.columns[-1]


def build_profile(df: pd.DataFrame, target: str, dataset_name: str) -> dict:
    """Build the full data profile dict."""
    n_samples, n_cols = df.shape
    feature_cols = [c for c in df.columns if c != target]

    columns = {}
    for c in df.columns:
        columns[c] = profile_column(df[c], c)

    # Target info
    target_info = {}
    if target in df.columns:
        tcol = df[target]
        target_info = {
            "name": target,
            "dtype": str(tcol.dtype),
            "n_classes": int(tcol.nunique(dropna=True)),
            "classes": [str(v) for v in sorted(tcol.dropna().unique().tolist())],
            "counts": {str(k): int(v) for k, v in tcol.value_counts().items()},
            "n_missing": int(tcol.isna().sum()),
        }
        counts = tcol.value_counts()
        if len(counts) == 2:
            minority = counts.min()
            majority = counts.max()
            target_info["imbalance_ratio"] = round(majority / minority, 3) if minority else None
            target_info["minority_class"] = str(counts.idxmin())
            target_info["majority_class"] = str(counts.idxmax())
            target_info["problem_type"] = "binary_classification"
        else:
            target_info["imbalance_ratio"] = None
            target_info["problem_type"] = "multiclass_classification"
    else:
        raise ValueError(f"Target column '{target}' not found in data.")

    numeric_cols = [c for c in feature_cols if columns[c]["type"] == "numeric"]
    categorical_cols = [c for c in feature_cols if columns[c]["type"] == "categorical"]

    profile = {
        "dataset_name": dataset_name,
        "n_samples": n_samples,
        "n_features": len(feature_cols),
        "n_columns": n_cols,
        "target": target_info,
        "feature_columns": feature_cols,
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "total_missing": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "columns": columns,
        "profiled_at": datetime.now(timezone.utc).isoformat(),
    }
    return profile


def build_preprocess_config(profile: dict) -> dict:
    """Derive a leakage-safe preprocessing config from the profile."""
    return {
        "target": profile["target"]["name"],
        "problem_type": profile["target"]["problem_type"],
        "numeric": {
            "columns": profile["numeric_columns"],
            "imputer": "median",
            "scaler": "standard",
        },
        "categorical": {
            "columns": profile["categorical_columns"],
            "imputer": "most_frequent",
            "encoder": "onehot",
            "handle_unknown": "ignore",
        },
        "drop_target_na": True,
        "random_state": 42,
    }


def main():
    ap = argparse.ArgumentParser(description="Profile a tabular dataset for classification.")
    ap.add_argument("--data", required=True, help="Path to CSV file")
    ap.add_argument("--target", default=None, help="Target column name (auto-detected if omitted)")
    ap.add_argument("--out", default="profile.json", help="Output profile JSON path")
    ap.add_argument("--config-out", default="preprocess_config.json", help="Output config JSON path")
    args = ap.parse_args()

    df = pd.read_csv(args.data)
    target = args.target or infer_target(df)
    dataset_name = os.path.splitext(os.path.basename(args.data))[0]

    print(f"[profiler] Data: {args.data}  shape={df.shape}")
    print(f"[profiler] Target: {target}")

    profile = build_profile(df, target, dataset_name)
    config = build_preprocess_config(profile)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, default=str)
    print(f"[profiler] Wrote profile -> {args.out}")

    with open(args.config_out, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, default=str)
    print(f"[profiler] Wrote config -> {args.config_out}")

    # Summary
    t = profile["target"]
    print(f"[profiler] Features: {profile['n_features']} "
          f"({len(profile['numeric_columns'])} numeric, "
          f"{len(profile['categorical_columns'])} categorical)")
    print(f"[profiler] Target: {t['name']}  classes={t['classes']}  "
          f"problem={t['problem_type']}")
    if t.get("imbalance_ratio"):
        print(f"[profiler] Imbalance ratio: {t['imbalance_ratio']}:1")


if __name__ == "__main__":
    main()
