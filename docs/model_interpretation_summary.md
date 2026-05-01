# Model Interpretation Summary

## Overview

The final forecast is a deterministic hybrid time-series pipeline rather than a single black-box model. The explanation therefore focuses on decomposition, analog shape behavior, and target-ratio stability.

## Key Forecast Drivers

| Driver | Role |
|---|---|
| Monthly anchor | Controls the overall scale of `Revenue` and `COGS`. |
| Daily analog profile | Redistributes monthly totals across individual dates. |
| 364/365-day analogs | Capture day-of-week aligned yearly recurrence. |
| Previous-year same-month profile | Captures month-specific demand timing. |
| COGS/Revenue guard | Keeps COGS consistent with Revenue and avoids unrealistic margin shifts. |

## Business Interpretation

`Revenue` and `COGS` move closely together, so they are treated as linked outputs. This is important for inventory and logistics planning because demand volume and cost exposure must remain coherent.

The model avoids a common failure mode in regime-shifted data: learning old high-scale years too strongly and over-forecasting future totals. Instead, it keeps the monthly scale stable and improves the timing pattern inside each month.

## Why Daily Shape Matters

The public forecast horizon is sensitive to how monthly totals are distributed across days. A month can have a reasonable total but still score poorly if peaks and troughs are placed on the wrong days. The analog daily shape addresses this by using historical calendar-aligned behavior.

## Ratio Stability

COGS is not forecast as an unrelated independent series. The final forecast preserves the observed relationship between COGS and Revenue, with block-level ratios kept in a realistic range.

## Final Recommendation

Use `outputs/final_submission.csv` as the final submission file. The workbook in this repository is provided for inspection and validation.

