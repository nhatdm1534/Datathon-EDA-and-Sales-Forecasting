# Submission Overview

This folder is a minimal final pipeline package for DATATHON 2026.

## Included

- `run_final_forecast.py`: final reproducible forecasting script.
- `sample_submission.csv`: target date template.
- `dataset/`: official competition data used for history and EDA.
- `artifacts/monthly_anchor.csv`: monthly anchor used by the final forecast.
- `outputs/final_submission.csv`: selected submission file.
- `check_data/`: prediction copy and Excel check workbook.
- `notebooks/eda_analysis.ipynb`: exploratory analysis notebook.
- `docs/`: concise project, model explanation, and explainability note.
- `analysis/explainability_analysis.py`: main component-based explainability script.
- `analysis/shap_analysis.py`: compatibility entry point that runs the explainability script.
- `reports/`: generated explainability outputs after running the analysis script.

## Constraints Addressed

- No external data is used.
- The final forecast is deterministic and reproducible.
- Explainability is based on the actual forecast formula, with optional SHAP surrogate diagnostics only as a secondary check.

## Reproduction

```bash
python run_final_forecast.py
```

## Explainability

```bash
python analysis/explainability_analysis.py
```
