# Project Description

## Objective

The objective is to forecast daily `Revenue` and `COGS` for the DATATHON 2026 preliminary round. The final solution is designed for forecasting accuracy, business consistency, and reproducibility using the official competition data only.

## Data Sources

The pipeline uses official tables in `dataset/`, including daily sales targets and transaction-level operational data:

- `sales.csv`: historical daily `Revenue` and `COGS`.
- `orders.csv`, `order_items.csv`, `products.csv`: transaction and product cost components.
- `payments.csv`, `returns.csv`, `shipments.csv`, `inventory.csv`, `web_traffic.csv`: supporting operational context for EDA and model understanding.
- `sample_submission.csv`: required output schema and forecast horizon.

## Modeling Strategy

The final forecast is built around four principles:

1. `Revenue` and `COGS` should be forecast as coupled business quantities.
2. Monthly forecast scale should remain stable because the historical data contains a major regime shift.
3. Daily seasonality matters, especially within the later forecast horizon.
4. The `COGS / Revenue` relationship must be guarded to avoid unrealistic margin movement.

The final pipeline first uses a monthly anchor for stable scale, then redistributes this monthly mass into daily values using analog shapes from historical daily patterns. This allows the forecast to capture intra-month timing without overreacting on total monthly scale.

## Final Output

The final forecast is stored in:

```text
outputs/final_submission.csv
```

The same file is copied to:

```text
check_data/prediction_results.csv
```

## Usage

Generate the final forecast:

```bash
python run_final_forecast.py
```


