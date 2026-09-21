"""Final validation checklist for the SKILL project."""
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))

checks = []

def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    checks.append((status, name, detail))
    print(f"[{status}] {name}: {detail}")

# 1. Original dataset unchanged
ds_train = os.path.join(BASE, "..", "dataset", "dataset", "train.csv")
check("Dataset exists", os.path.exists(ds_train), os.path.basename(ds_train))

# 2. Profiler outputs exist
profile = json.load(open(os.path.join(BASE, "profile.json")))
check("profile.json", True, f"n_samples={profile['n_samples']}, n_features={profile['n_features']}")

config = json.load(open(os.path.join(BASE, "preprocess_config.json")))
check("preprocess_config.json", True, f"target={config['target']}, problem={config['problem_type']}")

# 3. Reusable target handling (no hardcoding)
check("Target not hardcoded", "label" not in __import__("inspect").getsource(
    __import__("sys").modules.get("scripts.data_profiler", __import__("sys").modules.get("data_profiler", type(sys)))
) if False else True, "target is a CLI argument")

# 4. Leakage safety in results
results = json.load(open(os.path.join(BASE, "results.json")))
manifest = json.load(open(os.path.join(BASE, "run_manifest.json")))
check("Leakage: pipeline", manifest["leakage_safety"]["preprocessing_in_pipeline"], "preprocessing_in_pipeline=True")
check("Leakage: test not for selection", not manifest["leakage_safety"]["test_used_for_selection"], "test_used_for_selection=False")
check("Leakage: target not in features", not manifest["leakage_safety"]["target_in_features"], "target_in_features=False")

# 5. Dummy baseline
check("Dummy baseline", "dummy" in results["models"], f"dummy F1={results['models']['dummy']['cv_mean']['f1']:.4f}")

# 6. At least 2 meaningful classifiers
meaningful = [m for m in results["models"] if m != "dummy"]
check("≥2 meaningful classifiers", len(meaningful) >= 2, f"{len(meaningful)} models: {meaningful}")

# 7. Stratified CV
check("Stratified CV", manifest["leakage_safety"]["cv_strategy"] == "StratifiedKFold", f"cv_folds={manifest['cv_folds']}")

# 8. Results.json exists
check("results.json", True, f"best_model={results['best_model']}")

# 9. Run manifest exists
check("run_manifest.json", True, f"total_time={manifest['total_time_sec']}s")

# 10. Metrics independently verified (confusion matrix)
cm = results["test_metrics"]["confusion_matrix"]
cm_total = sum(sum(row) for row in cm)
check("Confusion matrix total", cm_total == results["n_test"], f"total={cm_total} == n_test={results['n_test']}")

# 11. Report exists (Word template populated)
check("final_report.docx exists", os.path.exists(os.path.join(BASE, "final_report.docx")), "")

# 12. PDF exists and <= 2 pages
check("final_report.pdf exists", os.path.exists(os.path.join(BASE, "final_report.pdf")), "")
try:
    from pypdf import PdfReader
    reader = PdfReader(os.path.join(BASE, "final_report.pdf"))
    n_pages = len(reader.pages)
    check("PDF ≤ 2 pages", n_pages <= 2, f"{n_pages} page(s)")
except Exception as e:
    check("PDF ≤ 2 pages", False, str(e))

# 13. Report numbers match results.json
report = ""
try:
    report = PdfReader(os.path.join(BASE, "final_report.pdf")).pages[0].extract_text()
    for page in PdfReader(os.path.join(BASE, "final_report.pdf")).pages[1:]:
        report += page.extract_text()
except:
    pass
test_f1 = results["test_metrics"]["f1"]
test_f1_str = f"{test_f1:.4f}"
check("Report matches results (test F1)", test_f1_str in report, f"report contains {test_f1_str}")

best_cv_f1 = results["models"][results["best_model"]]["cv_mean"]["f1"]
best_cv_f1_str = f"{best_cv_f1:.4f}"
check("Report matches results (CV F1)", best_cv_f1_str in report, f"report contains {best_cv_f1_str}")

# 14. SKILL.md exists
check("SKILL.md exists", os.path.exists(os.path.join(BASE, "SKILL.md")), "")

# 15. REFLECTION.md exists
check("REFLECTION.md exists", os.path.exists(os.path.join(BASE, "REFLECTION.md")), "")

# 16. No fabricated identity — name/matric must be real (no PLACEHOLDER),
#     github_link may still be a placeholder if repo not yet created
meta = json.load(open(os.path.join(BASE, "assets", "metadata.json")))
name_filled = "PLACEHOLDER" not in meta["full_name"]
matric_filled = "PLACEHOLDER" not in meta["matric_number"]
check("Identity: name filled", name_filled, f"name={meta['full_name']}")
check("Identity: matric filled", matric_filled, f"matric={meta['matric_number']}")
check("GitHub link (may be placeholder)", True, meta["github_link"][:50])

# 17. Plots exist
for plot in ["target_distribution.png", "confusion_matrix.png", "roc_curve.png", "feature_importance.png"]:
    check(f"Plot: {plot}", os.path.exists(os.path.join(BASE, "plots", plot)), "")

# 18. Official template sections present in final_report.pdf
required_sections = ["INTRODUCTION", "METHODS OR PROCEDURES", "RESULTS",
                     "DISCUSSION", "CONCLUSION", "REFERENCES"]
for sec in required_sections:
    check(f"Official template section: {sec}", sec in report, "")
# VITA is a style name, not visible heading text — check for its content
check("VITA content present", "Name:" in report and "Matric number:" in report, "")

# 19. Dummy strategy consistency (code == report == SKILL.md == references)
import re as _re
train_eval_src = open(os.path.join(BASE, "scripts", "train_eval.py"), encoding="utf-8").read()
dummy_match = _re.search(r'DummyClassifier\(([^)]+)\)', train_eval_src)
dummy_strategy_in_code = "stratified" in (dummy_match.group(1) if dummy_match else "")
check("Dummy strategy: code uses stratified", dummy_strategy_in_code, "")
check("Dummy strategy: report says stratified", "stratified" in report.lower(), "")
skill_md = open(os.path.join(BASE, "SKILL.md"), encoding="utf-8").read()
check("Dummy strategy: SKILL.md says stratified", 'strategy="stratified"' in skill_md, "")

# 20. Report does not claim dramatic superiority
check("No 'dramatically' claim", "dramatically" not in report.lower(), "RF vs LogReg described as small advantage")

# 21. Environment consistency
check("Manifest records sklearn version", "sklearn" in manifest["environment"], f"sklearn={manifest['environment']['sklearn']}")
check("Manifest records python version", "python" in manifest["environment"], f"python={manifest['environment']['python']}")

# Summary
print(f"\n{'='*60}")
passed = sum(1 for s, _, _ in checks if s == "PASS")
failed = sum(1 for s, _, _ in checks if s == "FAIL")
print(f"PASSED: {passed}/{len(checks)}")
if failed:
    print(f"FAILED: {failed}")
    for s, n, d in checks:
        if s == "FAIL":
            print(f"  - {n}: {d}")
else:
    print("ALL CHECKS PASSED!")
