# Explainability Analysis

## Scope

The final sales forecasting pipeline is deterministic and component-based. The primary explainability method is therefore a direct decomposition of the final forecast formula, not a post-hoc replacement model.

## Primary Feature Importance From Forecast Formula

| Target | Component | Importance Share | Mean Daily Contribution |
|---|---:|---:|---:|
| COGS | anchor | 79.04% | 3068376.75 |
| COGS | analog | 20.96% | 813855.73 |
| Revenue | anchor | 63.29% | 2771007.06 |
| Revenue | analog | 36.71% | 1607039.28 |

## Business Interpretation

- Monthly anchor is the dominant driver because it controls total monthly scale. This is the most important business signal in a dataset with a clear regime shift between high-scale and low-scale periods.
- Daily analog profile is the second driver. It does not mainly change total scale; it moves revenue and cost within each month according to calendar-aligned historical behavior.
- COGS is explained together with Revenue. The pipeline keeps COGS close to the cost structure implied by the monthly anchor and analog pattern, avoiding unrealistic margin movement.

## Calendar Diagnostics

| Target | Driver | Value | Relative To Average |
|---|---:|---:|---:|
| Revenue | highest_month_effect | 5 | 1.4254 |
| Revenue | lowest_month_effect | 12 | 0.5199 |
| Revenue | highest_day_of_week_effect | 0 | 1.0201 |
| Revenue | lowest_day_of_week_effect | 4 | 0.9780 |
| COGS | highest_month_effect | 4 | 1.3970 |
| COGS | lowest_month_effect | 1 | 0.5614 |
| COGS | highest_day_of_week_effect | 0 | 1.0287 |
| COGS | lowest_day_of_week_effect | 4 | 0.9669 |

## Optional SHAP Diagnostic

A Random Forest surrogate is trained only for diagnostic explainability. It is not used to generate the submission. Its purpose is to verify whether a tree-based explanation recovers the same drivers as the deterministic component decomposition.

| Target | Surrogate R2 | Top SHAP Feature | Mean Absolute SHAP |
|---|---:|---:|---:|
| COGS | 0.999222 | COGS_anchor | 1374494.0928 |
| Revenue | 0.998998 | Revenue_anchor | 1525426.2479 |

## Generated Artifacts

- `reports/component_importance.csv`
- `reports/calendar_driver_diagnostics.csv`
- `reports/component_importance.png`
- `reports/diagnostic_surrogate_shap_importance.csv` if SHAP dependencies are installed
