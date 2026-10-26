# Leakage-Free Deep Time-Series Benchmark on Asset Returns

## Description

Source code for *Do deep time-series architectures beat naive baselines? A leakage-free out-of-sample benchmark on asset returns*. The models are LSTM, the standard Transformer, Autoformer, PatchTST, and iTransformer.

The repository contains source code and documentation. Market data, saved predictions, tables, figures, checkpoints, and logs are maintained separately.

## Dataset information

The study uses CSI 300, S&P 500, CSI 1000, and BTC/USD. Input filenames, required columns, and provider references are listed in `data/README.md`.

## Code information

- `code/final_experiment/`: configuration, rolling-window splits, scaling, training, model adapters, and forecasting runner.
- `code/report_model_sizes.py`: parameter counts from supplied forecast configurations.
- `code/verify_provenance.py`: sampled forecast verification using supplied data and predictions.
- `analysis/`: descriptive statistics, forecast evaluation, and plotting scripts.
- `official_models/`: required upstream model sources and original licenses.

## Computing environment

Python 3.10 and PyTorch 2.1.2 were used with CUDA 11.8. See `ENVIRONMENT.txt` for the reference environment.

## Requirements

```bash
python -m pip install -r requirements.txt
```

Install the PyTorch build appropriate for the local CUDA environment. The forecasting runner uses CUDA when available and otherwise uses the CPU.

## Data preparation

Obtain the provider data, prepare the CSV files described in `data/README.md`, and place them in `data/`. The project root is resolved automatically; `STOCK_EMH_PROJECT_ROOT` can override it. An alternative root must contain both `data/` and `official_models/`.

## Usage instructions

```bash
python code/final_experiment/run_experiment.py --asset CSI300 --model LSTM --mode smoke --tag smokecheck
python code/final_experiment/run_experiment.py --asset CSI300 --model LSTM --mode full
python code/final_experiment/run_experiment.py --asset CSI300 --model LSTM --mode full --seed 7 --tag seed7
python code/final_experiment/run_experiment.py --asset CSI300 --model LSTM --mode full --seed 2024 --tag seed2024
python code/final_experiment/run_experiment.py --asset CSI300 --model Transformer --mode full --budget 60 --tag budget60
```

Supported assets are `CSI300`, `SP500`, `CSI1000`, and `BTCUSD`. Supported models are `LSTM`, `Transformer`, `Autoformer`, `PatchTST`, and `iTransformer`.

Baseline full runs write to `results/final/full/ASSET/`. Tagged runs write to `results/TAG/MODE/ASSET/`. Use a fresh output directory for an independent execution because trial logs are appended when a matching file exists.

## Analysis

Analysis scripts read separately supplied return files, predictions, forecast aggregates, rolling series, and robustness summaries. Input layouts and commands are documented in `analysis/README.md`.

```bash
python analysis/make_descriptive_stats.py --data /path/to/prepared/data --out tables
python analysis/make_tables.py --results /path/to/predictions --robustness /path/to/predictions/robustness --out tables
python analysis/make_supplementary_tables.py --predictions /path/to/predictions --out tables
ANALYSIS_DIR=/path/to/predictions/analysis python analysis/make_figures.py
```

## Citations and licenses

Cite the original publications when using Autoformer, PatchTST, or iTransformer. Third-party source attribution is in `THIRD_PARTY_MODELS.md`; the original licenses are retained under `official_models/`.
