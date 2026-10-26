# Leakage-Free Deep Time-Series Benchmark on Asset Returns

## Description

This repository contains the source code required to run the experiments for the manuscript **"Do Deep Time-Series Architectures Beat Naive Baselines? A Leakage-Free Out-of-Sample Benchmark on Asset Returns"**. It evaluates LSTM, a standard Transformer, Autoformer, PatchTST, and iTransformer for one-step-ahead daily log-return forecasting under a strict rolling-origin, leakage-free protocol.

This submission package contains source code only. Precomputed predictions, metrics, result CSV files, manuscript tables, manuscript figures, model checkpoints, logs, and other generated experimental outputs are intentionally not included.

## Dataset information

The analysis covers CSI 300, S&P 500, CSI 1000, and BTC/USD. These are third-party datasets and are not redistributed here. See `data/README.md` for the required local filenames and source URLs.

## Code information

- `code/common/`: shared data loading, rolling-window, scaling, and training utilities.
- `code/final_experiment/`: main experiment configuration, model adapters, training core, and experiment runner.
- `code/robustness_experiment/`: window-length, input-length, and re-tuning robustness runners.
- `code/check_data.py`: validates local input datasets.
- `code/verify_returns.py`: verifies return construction and basic input consistency.
- `code/test_environment.py`: reports the active software and hardware environment.
- `code/test_rolling_protocol.py`: checks the rolling-origin indexing protocol.
- `code/check_official_sources.py`: checks that the required third-party model source snapshots are present.
- `official_models/`: minimal upstream source snapshots needed by the study, with original license files and attribution. Unrelated upstream result documentation is not bundled.

## Computing environment

The reported experiments were run on AutoDL with Ubuntu 22.04, Python 3.10, PyTorch 2.1.2, CUDA 11.8, one NVIDIA GeForce RTX 4090D (24 GB), 15 vCPU on an Intel Xeon Platinum 8474C, and 80 GB RAM. The baseline uses random seed 42; the seed sensitivity also supports 7 and 2024. See `ENVIRONMENT.txt`.

## Requirements

Create a Python 3.10 environment and install:

```bash
pip install -r requirements.txt
```

For GPU execution, install the PyTorch build appropriate for the local CUDA environment if the default pip build does not match the host.

## Data preparation

1. Obtain the third-party data from the sources documented in `data/README.md`.
2. Prepare the four CSVs with the filenames listed there and place them in `data/`.
3. Check the input files:

```bash
python code/check_data.py
python code/verify_returns.py
```

## Usage instructions

The project root is resolved automatically. It may also be set explicitly:

```bash
export STOCK_EMH_PROJECT_ROOT=/path/to/stock_emh_project
```

Check the environment and supplied model snapshots:

```bash
python code/test_environment.py
python code/check_official_sources.py
```

For a fresh code-only clone, you can also run:

```bash
bash run_smoke_tests.sh
```

The smoke script skips data-dependent checks until the four third-party CSV files are placed in `data/`. Once the data are present, it also runs the data, return-construction, and rolling-origin leakage checks.

Run one main experiment, for example:

```bash
python code/final_experiment/run_experiment.py --asset CSI300 --model LSTM --mode full
```

Supported assets are `CSI300`, `SP500`, `CSI1000`, and `BTCUSD`. Supported models are `LSTM`, `Transformer`, `Autoformer`, `PatchTST`, and `iTransformer`.

The complete main experiment matrix is listed in `run_main_experiments.sh`. Robustness runners are in `code/robustness_experiment/`, and `run_robustness_examples.sh` documents representative settings used in the study.

Generated outputs are written locally by the experiment scripts. They are not included in this submission archive.

## Methodology summary

At every forecast origin, only information available before the forecast target is used. The baseline rolling history contains 504 observations, the input sequence contains 60 lagged returns, the internal validation block contains 126 targets, and the horizon is one day. Model weights are re-initialized and re-estimated at each origin. Hyperparameters are re-tuned periodically with Optuna using the rolling history only. Normalization parameters are computed from the fitting subsample and then applied to validation and test observations.

## Reproducibility notes

- Random seeds: baseline 42; additional seed replications 7 and 2024.
- No absolute local Windows or AutoDL path is required.
- The submitted source files contain English-only comments and user-facing text.
- Third-party model licenses are retained under `official_models/`.
- Raw third-party market data are intentionally not redistributed; source information is provided instead.
- No precomputed experimental results or generated result artifacts are included.

## Citations

If using the third-party architectures, please cite their original publications and repositories. The manuscript bibliography contains the full references for Autoformer, PatchTST, and iTransformer.

## License and third-party code

The first-party experiment scripts are supplied for scholarly reproduction of the submitted work. Third-party model files remain governed by the license files shipped in their respective subdirectories. See `THIRD_PARTY_MODELS.md`.

## Analysis code and separately supplied results

This repository contains source code and documentation only. Experimental outputs, market-data CSVs, saved predictions, metrics, manuscript tables and figures, model checkpoints, logs, and run manifests are not bundled. Experimental outputs are handled separately from this repository. The results archive requires a newly issued DOI; its identifier must be added to the manuscript data-availability statement once the new deposit is published. This repository does not reuse the earlier archive DOI.

The `analysis/` directory contains the current table and figure scripts. Their input files must be supplied separately. With an external results archive available, run:

```bash
python analysis/make_tables.py --results /path/to/results-archive/predictions --robustness /path/to/results-archive/predictions/robustness --out tables
python analysis/make_supplementary_tables.py --predictions /path/to/results-archive/predictions --out tables
ANALYSIS_DIR=/path/to/results-archive/predictions/analysis python analysis/make_figures.py
```

Tables 5 and 6 use aligned forecast aggregates. Tables 4, 8, and 9 use per-origin forecasts. Table 7 uses previously prepared robustness summaries. The figures use saved aggregate and rolling-series inputs. `analysis/README.md` describes the required external layout and the scope of the scripts.

Table 1 requires separately acquired and prepared source-return files:

```bash
python analysis/make_descriptive_stats.py --data /path/to/prepared/data --out tables
```

The forecasting runner does not create every aggregate, rolling-series input, or robustness summary needed by these analysis commands. The analysis archive layout also omits the `full/` mode directory used by the runner. Supply the required analysis layout explicitly rather than treating the source-only clone as a complete results archive.

## Seeds and tuning budgets

The runner accepts seed, search-budget, and output-tag options:

```bash
# Baseline
python code/final_experiment/run_experiment.py --asset CSI300 --model LSTM --mode full
# Additional seeds
python code/final_experiment/run_experiment.py --asset CSI300 --model LSTM --mode full --seed 7 --tag seed7
python code/final_experiment/run_experiment.py --asset CSI300 --model LSTM --mode full --seed 2024 --tag seed2024
# Larger tuning budget
python code/final_experiment/run_experiment.py --asset CSI300 --model Transformer --mode full --budget 60 --tag budget60
```

Baseline full runs write locally to `results/final/full/ASSET/`. Tagged runs write to `results/TAG/MODE/ASSET/`. The runner records forecasts, selected configurations, validation losses, selected epochs, and training times, and writes trial-level Optuna logs for newly executed searches. Use fresh output directories for independent executions because matching trial logs are appended.

`code/report_model_sizes.py` counts model parameters from externally supplied forecast files. `code/verify_provenance.py` re-executes sampled forecast origins and requires local input data plus a separate archived prediction tree:

```bash
python code/report_model_sizes.py --results results/final --out tables/model_sizes.csv
python code/verify_provenance.py --asset CSI300 --model LSTM --n 12 --device cpu --predictions-root /path/to/results-archive/predictions
```

Verification at sampled origins does not reconstruct historical rejected Optuna trials or establish full-run provenance by itself. No historical results are embedded in this repository's publication metadata.
