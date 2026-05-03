# DATATHON 2026 - Sales Forecasting

This repository contains the final reproducible pipeline for the DATATHON 2026 preliminary round sales forecasting task. The objective is to predict daily `Revenue` and `COGS` for the required forecast horizon using only the official data files provided by the organizer.

## 1. Project Objective

The task is a daily business forecasting problem with two target variables:

- `Revenue`: expected daily sales revenue.
- `COGS`: expected daily cost of goods sold.

The final submission file is:

```text
outputs/final_submission.csv
```

The forecast horizon covered by the submission is:

```text
2023-01-01 to 2024-07-01
```

Lower public score is better. The final selected public score reference is:

```text
642079
```

## 2. Repository Structure

```text
.
├── analysis/
│   ├── explainability_analysis.py   # Main explainability script
│   └── shap_analysis.py             # Compatibility entry point for explainability
├── artifacts/
│   └── monthly_anchor.csv           # Monthly anchor used by the final forecast
├── check_data/
│   ├── check_data.xlsx              # Excel workbook for forecast inspection
│   └── prediction_results.csv       # Copy of the final prediction output
├── dataset/                         # Official competition input data
│   ├── sales.csv
│   ├── orders.csv
│   ├── order_items.csv
│   ├── products.csv
│   ├── customers.csv
│   ├── payments.csv
│   ├── promotions.csv
│   ├── returns.csv
│   ├── shipments.csv
│   ├── inventory.csv
│   ├── web_traffic.csv
│   └── geography.csv
├── docs/
│   ├── project_description.md
│   ├── model_interpretation_summary.md
│   └── shap_analysis.md
├── notebooks/
│   └── eda_analysis.ipynb           # Exploratory data analysis notebook
├── outputs/
│   └── final_submission.csv         # Final submission file
├── reports/                         # Generated explainability outputs
├── environment.yml
├── requirements.txt
├── run_final_forecast.py            # Main reproducible forecasting pipeline
├── sample_submission.csv            # Submission schema
└── SUBMISSION_OVERVIEW.md
```

## 3. Data Usage and Compliance

This solution uses only the official competition files stored in `dataset/` and the provided `sample_submission.csv` schema.

No external data is used. All time-based behavior is derived from the provided date columns and historical competition data.

The file `fe_data.csv` is not used by the final pipeline.

## 4. Forecasting Method

The final model is a deterministic hybrid forecasting pipeline. It is designed around the observed business structure of the data:

1. `Revenue` and `COGS` move closely together and should not be treated as unrelated targets.
2. Monthly scale is the most important driver because historical data contains a clear regime shift.
3. Daily timing still matters because the leaderboard metric is sensitive to how monthly totals are distributed across individual dates.

The pipeline has three main components:

### 4.1 Monthly Anchor

The monthly anchor controls the total forecast scale for each month. This prevents the model from overreacting to older high-scale periods or underreacting to more recent low-scale periods.

### 4.2 Daily Analog Allocation

After monthly totals are established, the pipeline distributes them into daily forecasts using calendar-aligned analog patterns:

- 364-day lag pattern.
- 365-day lag pattern.
- Previous-year same-month daily profile.

A stronger analog adjustment is applied in the later forecast horizon, where day-level timing was more sensitive.

### 4.3 COGS and Revenue Coupling

`COGS` is forecast together with `Revenue` using a guarded cost-to-revenue relationship. This keeps cost behavior realistic and avoids large artificial margin distortions.

## 5. Reproducibility

The final forecast is deterministic. No random sampling is used in the submission generation script.

To reproduce the final submission, install dependencies and run:

```bash
python run_final_forecast.py
```

This generates:

```text
outputs/final_submission.csv
check_data/prediction_results.csv
```

Expected summary after running the script:

```text
rows: 548
start_date: 2023-01-01
end_date: 2024-07-01
total_revenue: 2399169394.29
total_cogs: 2127463398.75
cogs_revenue_ratio: 0.8867499743
```

## 6. Environment Setup

Install dependencies with pip:

```bash
pip install -r requirements.txt
```

Or create the conda environment:

```bash
conda env create -f environment.yml
conda activate datathon-final-pipeline
```

## 7. Explainability

The competition requires an explanation of the main factors driving the forecast. Since the final pipeline is deterministic and component-based, the primary explainability method is direct decomposition of the actual forecast formula.

Run:

```bash
python analysis/explainability_analysis.py
```

For compatibility, this command also works:

```bash
python analysis/shap_analysis.py
```

The main generated report is:

```text
reports/explainability_analysis.md
```

The primary component importance from the final formula is:

```text
Revenue:
- Monthly anchor: 63.29%
- Daily analog:   36.71%

COGS:
- Monthly anchor: 79.04%
- Daily analog:   20.96%
```

Business interpretation:

- Monthly anchor is the dominant driver because it determines the correct scale of each forecast month.
- Daily analog allocation adjusts the timing of peaks and troughs within each month.
- COGS follows Revenue through a guarded cost structure, keeping margin behavior stable.

An optional SHAP surrogate diagnostic is also generated when `shap` and `scikit-learn` are installed. This surrogate is used only for post-hoc diagnostic explanation and is not used to generate the submission.

## 8. Final Output Files

Use this file for submission:

```text
outputs/final_submission.csv
```

A duplicate copy is stored for checking:

```text
check_data/prediction_results.csv
```

The Excel inspection workbook is:

```text
check_data/check_data.xlsx
```

## 9. Notes for Reviewers

- The final pipeline is fully reproducible from the files included in this repository.
- No external data is required.
- The model logic is implemented in `run_final_forecast.py`.
- Explainability artifacts are generated by `analysis/explainability_analysis.py`.
- SHAP outputs, if present, are diagnostic only; the primary explanation is component-based and tied directly to the actual forecast formula.

## 10. Contributors
1. Cam Tu Tran Thi.
2. Thanh Hung Pham.
3. Minh Nhat Dang.
4. Ngoc Han Le.
