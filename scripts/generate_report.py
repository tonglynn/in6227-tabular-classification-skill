#!/usr/bin/env python3
"""Generate the markdown report from structured outputs.

Reads profile.json, results.json, and assets/metadata.json, renders the
Jinja2 template at assets/report_template.md, and writes report.md.

No metric is invented or hard-coded — every number comes from the JSON
files produced by the deterministic scripts.
"""
import argparse
import json
import os
from jinja2 import Environment, FileSystemLoader


def load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_cv_table(results: dict) -> str:
    """Build a markdown table of cross-validation metrics."""
    models = results["models"]
    header = "| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC |"
    sep = "|---|---|---|---|---|---|---|"
    lines = [header, sep]
    for name, data in models.items():
        m = data["cv_mean"]
        marker = " **(best)**" if name == results.get("best_model") else ""
        lines.append(
            f"| {name}{marker} | {m['accuracy']:.4f} | {m['precision']:.4f} | "
            f"{m['recall']:.4f} | {m['f1']:.4f} | {m['roc_auc']:.4f} | "
            f"{m.get('pr_auc', float('nan')):.4f} |"
        )
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Generate report.md from structured outputs.")
    ap.add_argument("--profile", required=True, help="profile.json")
    ap.add_argument("--results", required=True, help="results.json")
    ap.add_argument("--template", default="assets/report_template.md")
    ap.add_argument("--metadata", default="assets/metadata.json")
    ap.add_argument("--out", default="report.md")
    args = ap.parse_args()

    profile = load_json(args.profile)
    results = load_json(args.results)
    meta = load_json(args.metadata)

    # Merge all data for the template
    tgt = profile["target"]
    test_metrics = results.get("test_metrics", {})
    dummy = results["models"].get("dummy", {}).get("cv_mean", {})
    best_model_name = results.get("best_model", "")
    best = results["models"].get(best_model_name, {}).get("cv_mean", {})
    lr = results["models"].get("logistic_regression", {}).get("cv_mean", {})

    ctx = {
        # Metadata — official template fields
        "title": f"{meta['assignment']} {meta['variant']}",
        "author_line": f"{meta['full_name']}, {meta['matric_number']}",
        "assignment_line": f"{meta['assignment']}",
        "full_name": meta["full_name"],
        "matric_number": meta["matric_number"],
        "model_name": meta["model_name"],
        "llm_interface": meta["llm_interface"],
        "github_link": meta["github_link"],
        # Profile
        "dataset_name": profile["dataset_name"],
        "n_samples": profile["n_samples"],
        "n_features": profile["n_features"],
        "target_name": tgt["name"],
        "n_classes": tgt["n_classes"],
        "classes": ", ".join(tgt["classes"]),
        "class_distribution": ", ".join(f"{k}={v}" for k, v in tgt["counts"].items()),
        "imbalance_ratio": tgt.get("imbalance_ratio", "N/A"),
        "n_numeric": len(profile["numeric_columns"]),
        "n_categorical": len(profile["categorical_columns"]),
        "total_missing": profile["total_missing"],
        "missing_pct": round(profile["total_missing"] / (profile["n_samples"] * profile["n_columns"]) * 100, 3),
        "n_target_na": tgt.get("n_missing", 0),
        "duplicate_rows": profile.get("duplicate_rows", 0),
        # Results
        "cv_table": build_cv_table(results),
        "best_model": best_model_name,
        "best_cv_f1": f"{best.get('f1', 0):.4f}",
        "lr_cv_f1": f"{lr.get('f1', 0):.4f}",
        "f1_delta": f"{best.get('f1', 0) - lr.get('f1', 0):.4f}",
        "dummy_accuracy": f"{dummy.get('accuracy', 0):.4f}",
        "dummy_f1": f"{dummy.get('f1', 0):.4f}",
        # Test metrics
        "test_accuracy": f"{test_metrics.get('accuracy', 0):.4f}",
        "test_precision": f"{test_metrics.get('precision', 0):.4f}",
        "test_recall": f"{test_metrics.get('recall', 0):.4f}",
        "test_f1": f"{test_metrics.get('f1', 0):.4f}",
        "test_roc_auc": f"{test_metrics.get('roc_auc', 0):.4f}",
        "test_pr_auc": f"{test_metrics.get('pr_auc', 0):.4f}",
    }

    # Render with Jinja2
    tpl_dir = os.path.dirname(os.path.abspath(args.template))
    tpl_name = os.path.basename(args.template)
    env = Environment(loader=FileSystemLoader(tpl_dir), trim_blocks=True)
    template = env.get_template(tpl_name)
    output = template.render(**ctx)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"[generate_report] Wrote report -> {args.out} ({len(output)} chars)")


if __name__ == "__main__":
    main()
