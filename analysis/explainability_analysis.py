"""Explainability analysis for the final DATATHON forecasting pipeline.

The final forecasting model is deterministic and component-based. Therefore the
primary explainability artifact is a direct decomposition of the final forecast
formula into monthly-anchor and daily-analog components. A SHAP surrogate is also
provided as an optional diagnostic, but it is not the forecasting model.
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from run_final_forecast import hybrid_analog  # noqa: E402

TARGETS = ("Revenue", "COGS")
REPORT_DIR = ROOT / "reports"
Q2PLUS_START = pd.Timestamp("2024-04-01")


def build_explainability_frame() -> pd.DataFrame:
    sample = pd.read_csv(ROOT / "sample_submission.csv", parse_dates=["Date"]).sort_values("Date")
    anchor = pd.read_csv(ROOT / "artifacts" / "monthly_anchor.csv", parse_dates=["Date"]).sort_values("Date")
    sales = pd.read_csv(ROOT / "dataset" / "sales.csv", parse_dates=["Date"]).sort_values("Date")
    final = pd.read_csv(ROOT / "outputs" / "final_submission.csv", parse_dates=["Date"]).sort_values("Date")

    analog = hybrid_analog(sample.reset_index(drop=True), anchor.reset_index(drop=True), sales.reset_index(drop=True))

    df = final.merge(anchor, on="Date", suffixes=("", "_anchor"))
    df = df.merge(analog, on="Date", how="left")
    df["year"] = df["Date"].dt.year
    df["month"] = df["Date"].dt.month
    df["day"] = df["Date"].dt.day
    df["dow"] = df["Date"].dt.dayofweek
    df["dayofyear"] = df["Date"].dt.dayofyear
    df["is_weekend"] = (df["dow"] >= 5).astype(int)
    df["is_month_start"] = df["Date"].dt.is_month_start.astype(int)
    df["is_month_end"] = df["Date"].dt.is_month_end.astype(int)
    df["is_q2plus"] = df["Date"].ge(Q2PLUS_START).astype(int)
    df["cogs_anchor_ratio"] = df["COGS_anchor"] / df["Revenue_anchor"].clip(lower=1e-9)
    df["cogs_analog_ratio"] = df["COGS_analog"] / df["Revenue_analog"].clip(lower=1e-9)
    df["revenue_anchor_gap"] = df["Revenue_analog"] - df["Revenue_anchor"]
    df["cogs_anchor_gap"] = df["COGS_analog"] - df["COGS_anchor"]
    return df


def add_formula_components(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Revenue_anchor_weight"] = np.where(out["Date"].ge(Q2PLUS_START), 0.58, 0.65)
    out["Revenue_analog_weight"] = 1.0 - out["Revenue_anchor_weight"]
    out["COGS_anchor_weight"] = np.where(out["Date"].ge(Q2PLUS_START), 0.76, 0.80)
    out["COGS_analog_weight"] = 1.0 - out["COGS_anchor_weight"]

    out["Revenue_anchor_component"] = out["Revenue_anchor_weight"] * out["Revenue_anchor"]
    out["Revenue_analog_component"] = out["Revenue_analog_weight"] * out["Revenue_analog"]
    out["COGS_anchor_component"] = out["COGS_anchor_weight"] * out["COGS_anchor"]
    out["COGS_analog_component"] = out["COGS_analog_weight"] * out["COGS_analog"]
    return out


def component_importance(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    specs = {
        "Revenue": ["Revenue_anchor_component", "Revenue_analog_component"],
        "COGS": ["COGS_anchor_component", "COGS_analog_component"],
    }
    for target, components in specs.items():
        denominator = sum(float(df[col].abs().sum()) for col in components)
        for col in components:
            rows.append({
                "target": target,
                "component": col.replace(f"{target}_", "").replace("_component", ""),
                "mean_daily_contribution": float(df[col].mean()),
                "total_abs_contribution": float(df[col].abs().sum()),
                "importance_share": float(df[col].abs().sum() / max(denominator, 1e-9)),
            })
    return pd.DataFrame(rows).sort_values(["target", "importance_share"], ascending=[True, False])


def calendar_diagnostics(df: pd.DataFrame) -> pd.DataFrame:
    diagnostics = []
    for target in TARGETS:
        work = df.copy()
        work["target"] = work[target]
        month_ratio = work.groupby("month")["target"].mean() / work["target"].mean()
        dow_ratio = work.groupby("dow")["target"].mean() / work["target"].mean()
        diagnostics.append({
            "target": target,
            "driver": "highest_month_effect",
            "value": int(month_ratio.idxmax()),
            "relative_to_average": float(month_ratio.max()),
        })
        diagnostics.append({
            "target": target,
            "driver": "lowest_month_effect",
            "value": int(month_ratio.idxmin()),
            "relative_to_average": float(month_ratio.min()),
        })
        diagnostics.append({
            "target": target,
            "driver": "highest_day_of_week_effect",
            "value": int(dow_ratio.idxmax()),
            "relative_to_average": float(dow_ratio.max()),
        })
        diagnostics.append({
            "target": target,
            "driver": "lowest_day_of_week_effect",
            "value": int(dow_ratio.idxmin()),
            "relative_to_average": float(dow_ratio.min()),
        })
    return pd.DataFrame(diagnostics)


def write_component_outputs(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    REPORT_DIR.mkdir(exist_ok=True)
    importance = component_importance(df)
    diagnostics = calendar_diagnostics(df)
    importance.to_csv(REPORT_DIR / "component_importance.csv", index=False)
    diagnostics.to_csv(REPORT_DIR / "calendar_driver_diagnostics.csv", index=False)

    try:
        import matplotlib.pyplot as plt

        chart = importance.copy()
        chart["label"] = chart["target"] + " - " + chart["component"]
        plt.figure(figsize=(8, 4.5))
        plt.barh(chart["label"], chart["importance_share"])
        plt.xlabel("Importance share in final forecast formula")
        plt.title("Primary Explainability: Forecast Component Importance")
        plt.tight_layout()
        plt.savefig(REPORT_DIR / "component_importance.png", dpi=160, bbox_inches="tight")
        plt.close()
    except Exception as exc:  # plotting is helpful but not required for reproducibility
        print(f"Component plot skipped: {exc}")

    return importance, diagnostics


def run_surrogate_shap(df: pd.DataFrame) -> pd.DataFrame | None:
    try:
        import shap
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.metrics import r2_score
        import matplotlib.pyplot as plt
    except ImportError:
        print("Optional SHAP surrogate skipped because shap/scikit-learn is not installed.")
        return None

    features = [
        "Revenue_anchor",
        "COGS_anchor",
        "Revenue_analog",
        "COGS_analog",
        "cogs_anchor_ratio",
        "cogs_analog_ratio",
        "revenue_anchor_gap",
        "cogs_anchor_gap",
        "year",
        "month",
        "day",
        "dow",
        "dayofyear",
        "is_weekend",
        "is_month_start",
        "is_month_end",
        "is_q2plus",
    ]
    outputs = []
    for target in TARGETS:
        X = df[features].copy()
        y = df[target].copy()
        model = RandomForestRegressor(
            n_estimators=500,
            max_depth=8,
            min_samples_leaf=3,
            random_state=2026,
            n_jobs=1,
        )
        model.fit(X, y)
        surrogate_r2 = r2_score(y, model.predict(X))
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)
        mean_abs = np.abs(shap_values).mean(axis=0)
        importance = pd.DataFrame({"feature": features, "mean_abs_shap": mean_abs})
        importance["target"] = target
        importance["surrogate_r2"] = surrogate_r2
        outputs.append(importance.sort_values("mean_abs_shap", ascending=False))

        plt.figure(figsize=(9, 6))
        shap.summary_plot(shap_values, X, show=False, max_display=12)
        plt.title(f"Diagnostic SHAP Summary - {target} Surrogate")
        plt.tight_layout()
        plt.savefig(REPORT_DIR / f"diagnostic_shap_summary_{target.lower()}.png", dpi=160, bbox_inches="tight")
        plt.close()

    all_importance = pd.concat(outputs, ignore_index=True)
    all_importance.to_csv(REPORT_DIR / "diagnostic_surrogate_shap_importance.csv", index=False)
    return all_importance


def write_markdown_report(
    importance: pd.DataFrame,
    diagnostics: pd.DataFrame,
    shap_importance: pd.DataFrame | None,
) -> None:
    lines = [
        "# Explainability Analysis",
        "",
        "## Scope",
        "",
        "The final sales forecasting pipeline is deterministic and component-based. The primary explainability method is therefore a direct decomposition of the final forecast formula, not a post-hoc replacement model.",
        "",
        "## Primary Feature Importance From Forecast Formula",
        "",
        "| Target | Component | Importance Share | Mean Daily Contribution |",
        "|---|---:|---:|---:|",
    ]
    for _, row in importance.iterrows():
        lines.append(
            f"| {row['target']} | {row['component']} | {row['importance_share']:.2%} | {row['mean_daily_contribution']:.2f} |"
        )

    lines.extend([
        "",
        "## Business Interpretation",
        "",
        "- Monthly anchor is the dominant driver because it controls total monthly scale. This is the most important business signal in a dataset with a clear regime shift between high-scale and low-scale periods.",
        "- Daily analog profile is the second driver. It does not mainly change total scale; it moves revenue and cost within each month according to calendar-aligned historical behavior.",
        "- COGS is explained together with Revenue. The pipeline keeps COGS close to the cost structure implied by the monthly anchor and analog pattern, avoiding unrealistic margin movement.",
        "",
        "## Calendar Diagnostics",
        "",
        "| Target | Driver | Value | Relative To Average |",
        "|---|---:|---:|---:|",
    ])
    for _, row in diagnostics.iterrows():
        lines.append(
            f"| {row['target']} | {row['driver']} | {row['value']} | {row['relative_to_average']:.4f} |"
        )

    if shap_importance is not None:
        lines.extend([
            "",
            "## Optional SHAP Diagnostic",
            "",
            "A Random Forest surrogate is trained only for diagnostic explainability. It is not used to generate the submission. Its purpose is to verify whether a tree-based explanation recovers the same drivers as the deterministic component decomposition.",
            "",
            "| Target | Surrogate R2 | Top SHAP Feature | Mean Absolute SHAP |",
            "|---|---:|---:|---:|",
        ])
        top = shap_importance.sort_values(["target", "mean_abs_shap"], ascending=[True, False]).groupby("target").head(1)
        for _, row in top.iterrows():
            lines.append(
                f"| {row['target']} | {row['surrogate_r2']:.6f} | {row['feature']} | {row['mean_abs_shap']:.4f} |"
            )
    else:
        lines.extend([
            "",
            "## Optional SHAP Diagnostic",
            "",
            "SHAP surrogate output was skipped because the optional SHAP dependencies were not available. This does not affect the final forecast or the primary component-based explanation.",
        ])

    lines.extend([
        "",
        "## Generated Artifacts",
        "",
        "- `reports/component_importance.csv`",
        "- `reports/calendar_driver_diagnostics.csv`",
        "- `reports/component_importance.png`",
        "- `reports/diagnostic_surrogate_shap_importance.csv` if SHAP dependencies are installed",
    ])
    (REPORT_DIR / "explainability_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    df = add_formula_components(build_explainability_frame())
    importance, diagnostics = write_component_outputs(df)
    shap_importance = run_surrogate_shap(df)
    write_markdown_report(importance, diagnostics, shap_importance)
    print("Explainability analysis generated in reports/.")


if __name__ == "__main__":
    main()
