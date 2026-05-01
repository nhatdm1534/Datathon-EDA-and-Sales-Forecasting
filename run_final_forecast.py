from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


TARGETS = ("Revenue", "COGS")
DEFAULT_WEIGHTS = (0.35, 0.25, 0.40)
Q2PLUS_WEIGHTS = (0.20, 0.10, 0.70)


def safe_normalize(values: np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    arr = np.where(np.isfinite(arr) & (arr > 0), arr, np.nan)
    if np.isfinite(arr).sum() == 0:
        return np.full(len(arr), 1.0 / max(len(arr), 1), dtype=float)
    arr = np.where(np.isfinite(arr), arr, float(np.nanmedian(arr)))
    total = float(arr.sum())
    if total <= 0:
        return np.full(len(arr), 1.0 / max(len(arr), 1), dtype=float)
    return arr / total


def lookup(series: dict[pd.Timestamp, float], date: pd.Timestamp) -> float:
    return float(series.get(pd.Timestamp(date), np.nan))


def same_month_day_or_dow(series: dict[pd.Timestamp, float], date: pd.Timestamp) -> float:
    prior_month_start = pd.Timestamp(year=int(date.year) - 1, month=int(date.month), day=1)
    try:
        same_day = pd.Timestamp(year=int(date.year) - 1, month=int(date.month), day=int(date.day))
    except ValueError:
        same_day = pd.NaT
    if pd.notna(same_day) and same_day in series:
        return lookup(series, same_day)

    prior_month_end = prior_month_start + pd.offsets.MonthEnd(0)
    candidates = [
        lookup(series, day)
        for day in pd.date_range(prior_month_start, prior_month_end, freq="D")
        if day.dayofweek == date.dayofweek and np.isfinite(lookup(series, day))
    ]
    if candidates:
        return float(np.median(candidates))
    return np.nan


def build_monthly_analog_shape(
    dates: pd.Series,
    monthly_total: float,
    series: dict[pd.Timestamp, float],
    weights: tuple[float, float, float],
) -> np.ndarray:
    lag364 = np.array([lookup(series, date - pd.Timedelta(days=364)) for date in dates], dtype=float)
    lag365 = np.array([lookup(series, date - pd.Timedelta(days=365)) for date in dates], dtype=float)
    same_prev_month = np.array([same_month_day_or_dow(series, date) for date in dates], dtype=float)
    shape = (
        weights[0] * safe_normalize(lag364)
        + weights[1] * safe_normalize(lag365)
        + weights[2] * safe_normalize(same_prev_month)
    )
    shape = shape / np.clip(shape.sum(), 1e-12, None)
    return monthly_total * shape


def analog_forecast_with_weights(
    sample: pd.DataFrame,
    anchor: pd.DataFrame,
    sales: pd.DataFrame,
    weights: tuple[float, float, float],
) -> pd.DataFrame:
    out = sample[["Date"]].copy()
    anchor_month = anchor.copy()
    anchor_month["year"] = anchor_month["Date"].dt.year
    anchor_month["month"] = anchor_month["Date"].dt.month
    anchor_month = anchor_month.groupby(["year", "month"], as_index=False)[list(TARGETS)].sum()

    generated: dict[str, dict[pd.Timestamp, float]] = {}
    for target in TARGETS:
        generated[target] = {
            pd.Timestamp(row.Date): float(getattr(row, target))
            for row in sales[["Date", target]].itertuples(index=False)
        }

    work = sample[["Date"]].copy()
    work["year"] = work["Date"].dt.year
    work["month"] = work["Date"].dt.month
    pred_frames = [out]

    for target in TARGETS:
        preds = pd.Series(index=sample.index, dtype=float)
        for (year, month), idx in work.groupby(["year", "month"], sort=True).groups.items():
            month_block = sample.loc[list(idx)].sort_values("Date")
            month_dates = month_block["Date"].reset_index(drop=True)
            total = float(
                anchor_month.loc[
                    (anchor_month["year"] == year) & (anchor_month["month"] == month),
                    target,
                ].iloc[0]
            )
            month_pred = build_monthly_analog_shape(month_dates, total, generated[target], weights=weights)
            preds.loc[month_block.index.to_numpy()] = month_pred
            for date, value in zip(month_dates, month_pred):
                generated[target][pd.Timestamp(date)] = float(value)
        pred_frames.append(preds.rename(f"{target}_analog"))

    return pd.concat(pred_frames, axis=1)


def hybrid_analog(sample: pd.DataFrame, anchor: pd.DataFrame, sales: pd.DataFrame) -> pd.DataFrame:
    default = analog_forecast_with_weights(sample, anchor, sales, weights=DEFAULT_WEIGHTS)
    q2plus = analog_forecast_with_weights(sample, anchor, sales, weights=Q2PLUS_WEIGHTS)
    out = default.copy()
    mask = out["Date"].ge(pd.Timestamp("2024-04-01"))
    for target in TARGETS:
        out.loc[mask, f"{target}_analog"] = q2plus.loc[mask, f"{target}_analog"].to_numpy(dtype=float)
    return out


def make_final_submission(anchor: pd.DataFrame, analog: pd.DataFrame) -> pd.DataFrame:
    merged = anchor.merge(analog, on="Date", how="inner")
    q2plus = merged["Date"].ge(pd.Timestamp("2024-04-01")).to_numpy()
    revenue_alpha = np.full(len(merged), 0.35, dtype=float)
    cogs_alpha = np.full(len(merged), 0.20, dtype=float)
    revenue_alpha[q2plus] = 0.42
    cogs_alpha[q2plus] = 0.24

    revenue = (1.0 - revenue_alpha) * merged["Revenue"] + revenue_alpha * merged["Revenue_analog"]
    cogs = (1.0 - cogs_alpha) * merged["COGS"] + cogs_alpha * merged["COGS_analog"]
    out = pd.DataFrame({"Date": merged["Date"], "Revenue": revenue, "COGS": cogs})
    out["Revenue"] = out["Revenue"].clip(lower=0).round(2)
    out["COGS"] = out["COGS"].clip(lower=0).round(2)
    return out


def main() -> None:
    sample = pd.read_csv("sample_submission.csv", parse_dates=["Date"]).sort_values("Date").reset_index(drop=True)
    anchor = pd.read_csv("artifacts/monthly_anchor.csv", parse_dates=["Date"]).sort_values("Date").reset_index(drop=True)
    sales = pd.read_csv("dataset/sales.csv", parse_dates=["Date"]).sort_values("Date").reset_index(drop=True)

    analog = hybrid_analog(sample, anchor, sales)
    submission = make_final_submission(anchor, analog)

    Path("outputs").mkdir(exist_ok=True)
    Path("check_data").mkdir(exist_ok=True)
    submission.to_csv("outputs/final_submission.csv", index=False)
    submission.to_csv("check_data/prediction_results.csv", index=False)

    summary = {
        "rows": int(len(submission)),
        "start_date": str(submission["Date"].min().date()),
        "end_date": str(submission["Date"].max().date()),
        "total_revenue": float(submission["Revenue"].sum()),
        "total_cogs": float(submission["COGS"].sum()),
        "cogs_revenue_ratio": float(submission["COGS"].sum() / submission["Revenue"].sum()),
    }
    print("Final forecast generated.")
    print(summary)


if __name__ == "__main__":
    main()
