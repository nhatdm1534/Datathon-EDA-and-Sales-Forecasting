# Explainability Analysis

## Purpose

The competition requires an explanation of the main factors driving the revenue forecast. Because the final forecast is a deterministic hybrid pipeline, the primary explanation is based on direct decomposition of the actual forecast formula rather than treating a surrogate model as the real predictor.

## Primary Explanation Method

The final forecast combines two business components:

- Monthly anchor: controls the total monthly scale of `Revenue` and `COGS`.
- Daily analog profile: redistributes monthly totals across days using calendar-aligned historical patterns.

The explainability script calculates component importance directly from the final formula. This is the main explanation used for the report.

## Optional SHAP Diagnostic

The script may also train a Random Forest surrogate and compute SHAP values. This is only a diagnostic check to verify that a tree-based post-hoc explanation recovers the same drivers. The surrogate is not used to generate the submission.

## How to Run

```bash
python analysis/explainability_analysis.py
```

The compatibility command below runs the same analysis:

```bash
python analysis/shap_analysis.py
```

The script produces:

```text
reports/explainability_analysis.md
reports/component_importance.csv
reports/calendar_driver_diagnostics.csv
reports/component_importance.png
reports/diagnostic_surrogate_shap_importance.csv
reports/diagnostic_shap_summary_revenue.png
reports/diagnostic_shap_summary_cogs.png
```

## Business Interpretation

Monthly anchor should dominate because the main forecasting risk is selecting the correct scale for each month. Daily analog features matter because they place peaks and troughs on individual dates within each month. The COGS forecast is interpreted together with Revenue because cost should remain consistent with revenue scale and margin behavior.
