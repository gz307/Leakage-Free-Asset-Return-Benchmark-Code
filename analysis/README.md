# Analysis

All input data and generated outputs are supplied separately from this repository.

## Scripts

| Script | Input | Output |
| --- | --- | --- |
| `make_descriptive_stats.py` | Prepared return CSV files | Descriptive-statistics table |
| `make_tables.py` | Aligned forecast aggregates and robustness summaries | Forecast metrics, statistical tests, and robustness tables |
| `make_supplementary_tables.py` | Per-origin forecast files | Selected configurations, tuning-budget comparisons, and seed comparisons |
| `make_figures.py` | Forecast aggregates and rolling series | Figures 1--6 |

## Prediction input layout

- `final/ASSET/MODEL_predictions.csv`
- `seed7/ASSET/MODEL_predictions.csv`
- `seed2024/ASSET/MODEL_predictions.csv`
- `budget60/ASSET/MODEL_predictions.csv`
- `analysis/ASSET_OOS_ALL.csv`
- `analysis/ASSET_ROLLING_ROS2_126.csv`
- `analysis/ASSET_ROLLING_ROS2_252.csv`
- `robustness/analysis/WINDOW_ROBUSTNESS_LONG.csv`
- `robustness/analysis/SEQLEN_ROBUSTNESS_LONG.csv`
- `robustness/analysis/RETUNE_ROBUSTNESS_LONG.csv`

`ASSET_OOS_ALL.csv` contains `Date`, `True`, `HM`, `PER`, and the five model prediction columns. Use the asset and model identifiers listed in the main README.

## Commands

Run from the repository root:

```bash
python analysis/make_descriptive_stats.py --data /path/to/prepared/data --out tables
python analysis/make_tables.py --results /path/to/predictions --robustness /path/to/predictions/robustness --out tables
python analysis/make_supplementary_tables.py --predictions /path/to/predictions --out tables
ANALYSIS_DIR=/path/to/predictions/analysis python analysis/make_figures.py
```

The descriptive-statistics script computes values from the supplied returns. The table scripts read the specified forecasts and summaries; they do not retrain the models. The figure script writes JPG and bitmap PDF files to `figs/`.
