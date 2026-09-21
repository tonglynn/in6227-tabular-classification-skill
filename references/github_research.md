# GitHub Research — Upstream Design Influences

> This document records the provenance chain from upstream open-source
> AutoML / tabular-classification projects to the design of this SKILL.
>
> **Important honesty note:** The previous AI agent performed GitHub
> research during the initial build, but did not save a separate
> research log. The design influences are therefore reconstructed from
> the **embedded artifacts** in this repository — specifically
> [decision_guide.md](decision_guide.md), the code in
> [scripts/](../scripts/), and the architecture described in
> [SKILL.md](../SKILL.md). Where an upstream detail is not recoverable
> from these local artifacts, it is marked **"not recorded"** rather
> than guessed.

---

## 1. AutoGluon

| Field | Value |
|---|---|
| Repository URL | https://github.com/autogluon/autogluon |
| File/path reviewed | not recorded |
| Commit/tag | not recorded |
| License | Apache-2.0 (per project README; not directly verified in this session) |

### Design concepts borrowed

- **Layered profiling → decision → training structure.** AutoGluon's
  workflow separates data inspection, problem-type inference, and model
  training into distinct phases. This SKILL mirrors that layering:
  [data_profiler.py](../scripts/data_profiler.py) inspects,
  `preprocess_config.json` records decisions,
  [train_eval.py](../scripts/train_eval.py) trains.

- **Leaderboard-style reporting.** AutoGluon outputs a leaderboard table
  comparing models on multiple metrics. This SKILL's `results.json`
  stores per-model CV metrics (accuracy, precision, recall, F1, ROC-AUC,
  PR-AUC) and the final report renders a compact comparison table —
  the same leaderboard concept in a lightweight form.

### Concepts intentionally not borrowed

- **Multi-layer stacking** (AutoGluon's signature feature): too heavy
  for a transparent, explainable academic SKILL.
- **Automated hyperparameter search** at AutoGluon's scale: the SKILL
  uses sensible defaults, not HPO.
- **Custom metric optimisation layer**: not needed for a 4-model
  comparison.

### Code copied?

No. The implementation is entirely our own lightweight sklearn code.

### Where the concept appears

- Layered structure: [SKILL.md §4](../SKILL.md) Step 1 (profile) → Step 2
  (train) → Step 3 (report).
- Leaderboard: [results.json](../results.json) `models.*.cv_mean` and
  the Word table in `final_report.pdf`.

---

## 2. FLAML

| Field | Value |
|---|---|
| Repository URL | https://github.com/microsoft/FLAML |
| File/path reviewed | not recorded |
| Commit/tag | not recorded |
| License | MIT (per project README; not directly verified in this session) |

### Design concepts borrowed

- **Economical model/hyperparameter search.** FLAML's philosophy is to
  find a good model *cheaply* rather than exhaustively. This SKILL
  adopts the same spirit: four models with sensible defaults, no grid
  search, no Bayesian optimisation. The goal is a *good enough, fast,
  transparent* comparison — not a maximally-tuned AutoML run.

- **Cost-awareness.** FLAML tracks wall-clock cost per trial. This
  SKILL records `cv_time_sec` per model in `results.json` and
  `run_manifest.json`, so the user can see that LogisticRegression
  (2.45s) is cheaper than RandomForest — the same cost-transparency
  principle.

### Concepts intentionally not borrowed

- **FLAML's blended search strategy** (CFO/BSO): too complex for the
  assignment's scope.
- **Automated hyperparameter flipping**: the SKILL uses fixed defaults
  for reproducibility.

### Code copied?

No.

### Where the concept appears

- Economical 4-model ladder: [decision_guide.md §4](decision_guide.md)
  and [train_eval.py](../scripts/train_eval.py).
- `cv_time_sec` per model: [results.json](../results.json).

---

## 3. mljar-supervised

| Field | Value |
|---|---|
| Repository URL | https://github.com/mljar/supervised |
| File/path reviewed | not recorded |
| Commit/tag | not recorded |
| License | MIT (per project README; not directly verified in this session) |

### Design concepts borrowed

- **Structured machine-readable outputs feeding automated reports.**
  mljar-supervised writes JSON-structured results (learner descriptions,
  metrics, predictions) that downstream tools consume to generate
  human-readable reports. This SKILL adopts the same pattern:
  `profile.json`, `results.json`, and `run_manifest.json` are
  machine-readable, and `populate_template.py` reads them to fill the
  official Word template — no manual number entry.

- **Separation of "results" from "report".** mljar keeps the raw
  results directory separate from the rendered Markdown report. This
  SKILL does the same: `results.json` is the source of truth;
  `final_report.pdf` is a rendered view of it.

### Concepts intentionally not borrowed

- **mljar's extensive report suite** (decision-tree visualisations,
  SHAP plots, ensemble explanation): too heavy for a ≤2-page report.
- **Auto ensemble construction**: not used; the SKILL reports
  individual models only.

### Code copied?

No.

### Where the concept appears

- Structured JSON outputs → template population:
  [populate_template.py](../scripts/populate_template.py) reads
  `results.json` and `profile.json`.
- Source-of-truth separation: [SKILL.md §9](../SKILL.md) "Structured
  Outputs" table.

---

## 4. claude-for-ai-platforms (Anthropic reference)

| Field | Value |
|---|---|
| Repository URL | not recorded (the previous agent referenced design patterns associated with Anthropic's AI-platform guidance, but the exact repo URL was not saved) |
| File/path reviewed | not recorded |
| Commit/tag | not recorded |
| License | not recorded |

### Design concepts borrowed

- **Model ladder.** A progression from a trivial baseline to
  increasingly complex models, so that each step's marginal improvement
  is visible. This SKILL's ladder: Dummy → LogisticRegression →
  RandomForest → GradientBoosting (see [README.md §Model Ladder](../README.md)
  and [decision_guide.md §4](decision_guide.md)).

- **Dummy baseline.** A no-information classifier
  (`DummyClassifier(strategy="stratified")`) is always trained first,
  establishing a floor. Every other model's improvement is measured
  *relative to* this baseline.

- **Explicit decision tables.** Rather than hiding preprocessing and
  model choices in code comments, the SKILL surfaces them as readable
  tables in [decision_guide.md](decision_guide.md): column-type
  detection, imputation, scaling/encoding, model selection, class
  imbalance, cross-validation, metric selection, and selection
  criterion.

- **Named traps.** The SKILL explicitly names and avoids common
  pitfalls: "leakage" (preprocessing outside Pipeline), "test leakage"
  (using test for selection), "SMOTE leakage" (oversampling outside CV
  loop), "target leakage" (target in features). These appear in
  [SKILL.md §5](../SKILL.md) and [REFLECTION.md §2](../REFLECTION.md).

### Concepts intentionally not borrowed

- **Full agent-loop orchestration**: the SKILL is deterministic scripts,
  not an agent that iterates.
- **Self-critique / self-revision loop**: the SKILL runs once; the
  REFLECTION is written after, not in a loop.

### Code copied?

No.

### Where the concept appears

- Model ladder: [train_eval.py](../scripts/train_eval.py) model dict,
  [README.md](../README.md).
- Dummy baseline: [decision_guide.md §4](decision_guide.md).
- Decision tables: entire [decision_guide.md](decision_guide.md).
- Named traps: [SKILL.md §5](../SKILL.md), [REFLECTION.md](../REFLECTION.md).

---

## Summary: provenance chain

```
Previous agent's GitHub research (not saved as a file)
        │
        ▼
Embedded in local artifacts:
  decision_guide.md, SKILL.md, train_eval.py, results.json
        │
        ▼
This file (github_research.md) reconstructs the chain
        │
        ▼
SKILL implementation (lightweight sklearn, our own code)
```

### Honesty statement

- **No upstream code was copied.** All scripts in this repository are
  original, lightweight sklearn-based implementations.
- **Upstream details not recovered** from the local artifacts (exact
  file paths, commits, licenses verified at the time) are marked
  **"not recorded"** above. They are not guessed.
- This document was reconstructed by the current agent (GLM-5.2) from
  the repository's own files, not from a fresh GitHub browsing session.
