# Leakage-Free Asset Return Benchmark

## Description

Source code for *Do deep time-series architectures beat naive baselines? A leakage-free out-of-sample benchmark on asset returns*.

The project evaluates one-step-ahead daily log-return forecasts from LSTM, the standard Transformer, Autoformer, PatchTST, and iTransformer. Each asset is processed independently using chronological rolling windows. The historical mean and persistence forecasts provide reference benchmarks.

This repository contains source code, dependency information, and model licenses. Market data and precomputed experimental outputs are supplied separately.

## Repository contents

| Path | Purpose |
| --- | --- |
| `code/final_experiment/config.py` | Data paths, asset identifiers, and default protocol settings |
| `code/final_experiment/core.py` | Data loading, rolling splits, scaling, training, and prediction |
| `code/final_experiment/model_factory.py` | Model implementations and adapters |
| `code/final_experiment/run_experiment.py` | Forecasting runner and hyperparameter search |
| `code/report_model_sizes.py` | Parameter counts for supplied forecast configurations |
| `code/verify_provenance.py` | Sampled forecast verification |
| `analysis/` | Descriptive statistics, evaluation tables, and plotting scripts |
| `official_models/` | Required upstream model sources and original licenses |
| `requirements.txt` | Python dependencies |
| `ENVIRONMENT.txt` | Reference software and hardware environment |
| `THIRD_PARTY_MODELS.md` | Upstream attribution and implementation notes |

## Requirements

Use Python 3.10. The reference environment uses PyTorch 2.1.2 and CUDA 11.8 on Ubuntu 22.04. The forecasting runner selects a CUDA device when available and otherwise uses the CPU. Hardware details are recorded in `ENVIRONMENT.txt`.

From the repository root, install the dependencies:

```bash
python -m pip install -r requirements.txt
```

Dependencies include PyTorch, NumPy, pandas, SciPy, scikit-learn, Matplotlib, Optuna, tqdm, einops, and Pillow. Install the PyTorch build appropriate for the target machine and CUDA environment.

## Dataset information

Create a `data/` directory at the repository root and place the prepared input files there.

| Asset identifier | Required filename | Source series and field |
| --- | --- | --- |
| `CSI300` | `CSI300_daily_data.csv` | CSI 300, Wind Financial Terminal, unadjusted daily close |
| `SP500` | `SP500_daily_data.csv` | S&P 500, Yahoo Finance ticker `^GSPC`, adjusted daily close |
| `CSI1000` | `CSI1000_daily_data.csv` | CSI 1000, Wind Financial Terminal, unadjusted daily close |
| `BTCUSD` | `BTC_USD_daily_data.csv` | Coin Metrics asset `btc`, field `ReferenceRateUSD`, sampled at 00:00 UTC |

Provider references:

- [Wind Financial Terminal](https://www.wind.com.cn/portal/zh/WFT/index.html)
- [Yahoo Finance historical data](https://finance.yahoo.com/quote/%5EGSPC/history/)
- [Coin Metrics Reference Rates](https://docs.coinmetrics.io/market-data/reference-rates-overview/reference_rate)

Obtain the source data under the relevant providers' access and reuse terms. No automated provider downloader is included.

### Input columns and preparation

Each input CSV must contain:

| Column | Definition |
| --- | --- |
| `Date` | A unique, parseable observation date |
| `Log_Return` | A finite daily log return in decimal units |

Compute `Log_Return` as `log(P_t / P_previous)`, using consecutive available observations from the same source series. The first retained return requires the preceding source observation. An optional `Close` column may be retained for source-price checks; the forecasting runner and descriptive-statistics script do not read it.

Use each asset's own observation calendar. Do not impute missing observations. The BTC/USD reference rate is not an exchange closing price. The loader sorts dates and rejects duplicate dates and non-finite returns.

Paths are resolved from the repository root automatically. The optional `STOCK_EMH_PROJECT_ROOT` environment variable can specify another root; that directory must contain both `data/` and `official_models/`.

## Methodology

At each forecast origin:

1. Collect the preceding rolling history and construct lagged inputs and one-step-ahead targets.
2. Reserve the final supervised observations for chronological validation and use the earlier supervised observations for fitting.
3. Fit the input scaler on fitting inputs and the target scaler on fitting targets. Apply the input scaler to validation and forecasting inputs, and the target scaler to validation targets.
4. Run Optuna at scheduled tuning origins, using validation loss to select hyperparameters.
5. Initialize the forecasting network from scratch, train on the fitting subset, and restore the checkpoint with the lowest validation loss. There is no subsequent combined fitting-and-validation refit.
6. Generate the next return forecast, invert target scaling, and advance the origin by one observation.

The baseline settings are defined in `code/final_experiment/config.py`:

| Setting | Default |
| --- | --- |
| Rolling history | 504 observations |
| Input sequence | 60 lagged returns |
| Validation block | 126 targets |
| Forecast horizon | 1 observation |
| Forecast step | 1 observation |
| Hyperparameter retuning interval | 63 observations |
| Optuna trials per search | 20 |
| Optuna training limit / patience | 30 epochs / 5 epochs |
| Forecast-model training limit / patience | 50 epochs / 10 epochs |
| Batch size | 64 |
| Random seed | 42 |

## Forecasting usage

Run commands from the repository root after preparing the input data.

### Short smoke run

```bash
python code/final_experiment/run_experiment.py --asset CSI300 --model LSTM --mode smoke --tag smokecheck
```

### Full run

```bash
python code/final_experiment/run_experiment.py --asset CSI300 --model LSTM --mode full
```

Supported assets are `CSI300`, `SP500`, `CSI1000`, and `BTCUSD`. Supported models are `LSTM`, `Transformer`, `Autoformer`, `PatchTST`, and `iTransformer`. Invoke the runner separately for each asset and model.

### Seeds and search budgets

```bash
python code/final_experiment/run_experiment.py --asset CSI300 --model LSTM --mode full --seed 7 --tag seed7
python code/final_experiment/run_experiment.py --asset CSI300 --model LSTM --mode full --seed 2024 --tag seed2024
python code/final_experiment/run_experiment.py --asset CSI300 --model Transformer --mode full --budget 60 --tag budget60
```

Use `--help` to inspect the available runner arguments.

### Local outputs

| Run | Output directory |
| --- | --- |
| Baseline full run | `results/final/full/ASSET/` |
| Tagged run | `results/TAG/MODE/ASSET/` |

The runner creates `MODEL_predictions.csv`, `MODEL_tuning.csv`, and `MODEL_optuna_trials.csv`. Prediction rows include dates, realized returns, benchmark and model forecasts, selected hyperparameters, validation loss, selected epoch, and training time.

Use a fresh tag or output directory for an independent execution because an existing trial log is appended to. These files are generated locally when the programs run; they are not bundled in this repository.

## Analysis usage

Analysis scripts require separately supplied inputs.

### Descriptive statistics

```bash
python analysis/make_descriptive_stats.py --data /path/to/prepared/data --out tables
```

This command reads the four return CSV files and computes observation counts, date ranges, means, sample standard deviations, skewness, and Fisher excess kurtosis.

### Forecast metrics and statistical tests

```bash
python analysis/make_tables.py --results /path/to/predictions --robustness /path/to/predictions/robustness --out tables
```

The predictions root must contain `analysis/ASSET_OOS_ALL.csv` for each asset. These files contain `Date`, `True`, `HM`, `PER`, and the five model prediction columns. The robustness directory must contain these prepared summary files under `analysis/`:

- `WINDOW_ROBUSTNESS_LONG.csv`
- `SEQLEN_ROBUSTNESS_LONG.csv`
- `RETUNE_ROBUSTNESS_LONG.csv`

The script computes point estimates, Clark-West and DM-HLN statistics, realized-loss comparisons, multiplicity adjustments, and bandwidth sensitivity. Robustness tables read the supplied summaries.

### Configurations, budgets, and seeds

```bash
python analysis/make_supplementary_tables.py --predictions /path/to/predictions --out tables
```

The predictions root must contain per-origin files named `ASSET/MODEL_predictions.csv` under `final/`, `seed7/`, `seed2024/`, and `budget60/`. The budget comparison reads `CSI300` and `BTCUSD`.

### Figures

```bash
ANALYSIS_DIR=/path/to/predictions/analysis python analysis/make_figures.py
```

The figure script reads `TABLE4_MAIN_RESULTS.csv` and the four `ASSET_ROLLING_ROS2_252.csv` files from the specified directory. It writes JPG and bitmap PDF files to `figs/`.

The forecasting runner includes a `full/` mode directory in its output paths. The prepared analysis layout described above does not include that directory. Supply the analysis tree explicitly, including the aggregates, rolling series, and robustness summaries; the runner alone does not construct all of those analysis inputs.

## Parameter counts and forecast verification

Parameter counts from locally generated baseline forecast files:

```bash
python code/report_model_sizes.py --results results/final --out tables/model_sizes.csv
```

A sampled forecast check requires both the local source-return CSV files and a separate prediction tree containing `final/ASSET/MODEL_predictions.csv`:

```bash
python code/verify_provenance.py --asset CSI300 --model LSTM --n 12 --device cpu --predictions-root /path/to/predictions
```

The check reconstructs sampled rolling origins, reuses their supplied hyperparameters and seed, and compares the resulting forecasts with the supplied forecast records. The `--seed` argument must match the input records. The command checks sampled origins rather than reconstructing a complete historical hyperparameter search.

## Citations and licenses

Cite the accompanying manuscript and the original architecture publications when using this code. Upstream repository links and attribution are provided in [THIRD_PARTY_MODELS.md](THIRD_PARTY_MODELS.md).

Autoformer, PatchTST, and iTransformer retain the license files in their respective `official_models/` directories. Provider data remain subject to their own access and reuse terms.

For reproducibility questions, open a repository issue with the command used, dependency versions, and the relevant error message.
