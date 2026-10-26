# Analysis scripts and external inputs

The Python scripts in this directory are included as source code. Their required data, saved predictions, and computed outputs are not bundled.

## Expected external archive layout

The separately supplied results archive must provide:

- `predictions/final/ASSET/MODEL_predictions.csv` for baseline forecasts.
- `predictions/seed7/ASSET/MODEL_predictions.csv` and `predictions/seed2024/ASSET/MODEL_predictions.csv` for seed comparisons.
- `predictions/budget60/ASSET/MODEL_predictions.csv` for budget comparisons on the assets used in that experiment.
- `predictions/analysis/ASSET_OOS_ALL.csv` with `Date`, `True`, `HM`, `PER`, and the five model prediction columns.
- `predictions/analysis/ASSET_ROLLING_ROS2_126.csv` and `ASSET_ROLLING_ROS2_252.csv` with the rolling series used by the figure script.
- `predictions/robustness/analysis/WINDOW_ROBUSTNESS_LONG.csv`, `SEQLEN_ROBUSTNESS_LONG.csv`, and `RETUNE_ROBUSTNESS_LONG.csv` for robustness summaries.

Use the asset and model identifiers listed in the root README. The scripts consume the provided inputs; the code-only package does not supply or verify their historical availability.

## Commands

From the code-package root, regenerate Tables 5--7 and the bandwidth sensitivity output:

```bash
python analysis/make_tables.py --results /path/to/results-archive/predictions --robustness /path/to/results-archive/predictions/robustness --out tables
```

Regenerate Tables 4, 8, and 9:

```bash
python analysis/make_supplementary_tables.py --predictions /path/to/results-archive/predictions --out tables
```

Regenerate Table 1 from separately acquired and prepared return files:

```bash
python analysis/make_descriptive_stats.py --data /path/to/prepared/data --out tables
```

The descriptive-statistics script includes the manuscript's reference values as validation constants; these are not a bundled dataset or a precomputed output file.

Regenerate Figures 1--6 using externally supplied aggregates and rolling series:

```bash
ANALYSIS_DIR=/path/to/results-archive/predictions/analysis python analysis/make_figures.py
```

The figure script writes JPG files and bitmap PDF files to `figs/`. These formats reflect the existing implementation; the PDF output is not vector artwork.

Tables 5 and 6 use aligned forecast aggregates. Tables 4, 8, and 9 use per-origin forecasts. Table 7 uses previously prepared robustness summaries and does not recompute those robustness experiments from raw data. The scripts do not provide a single command that rebuilds every input from the forecasting runner's output.
