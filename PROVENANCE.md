# Provenance of the reported results

## Archived materials

The Zenodo collection contains the complete supplied forecasting code, analysis scripts, four prepared source-data CSV files, and archived predictions and summaries supporting the manuscript. The code is also provided through GitHub. The manuscript and response letter provide the public repository link and DOI; no publication identifier needs to be inserted into these files after upload. FILE_SHA256.csv identifies the files in this archive, and RUN_MANIFEST.json records the experimental settings. Packaging changes do not represent a new training run.

## Output to input mapping

| Output | Saved inputs | Command or script |
|---|---|---|
| Table 1 | Four source-return CSVs in data/ | analysis/make_descriptive_stats.py |
| Table 4 | Baseline per-origin selected configurations | analysis/make_supplementary_tables.py |
| Tables 5 and 6 | predictions/analysis/{ASSET}_OOS_ALL.csv, checked against predictions/final/{ASSET}/{MODEL}_predictions.csv | analysis/make_tables.py |
| Table 8 | Three robustness summary CSVs listed below | analysis/make_tables.py |
| Table 9 | Baseline and budget60 per-origin forecasts | analysis/make_supplementary_tables.py |
| Table 10 | final, seed7 and seed2024 per-origin forecasts | analysis/make_supplementary_tables.py |
| Figures 1–6 | predictions/analysis forecast aggregates and rolling series | analysis/make_figures.py |
| Table 7 | tables/table6_bandwidth.csv | analysis/make_bandwidth_table.py |

## Table 8 provenance

All input files are in `predictions/robustness/analysis/`. These are saved experiment summaries, not per-origin forecasts. Each row retains Asset, Model, Source, MSE, MAE, R_OS2, DA and N, plus the varied setting. The archive does not include the original per-origin forecast files or training logs for these protocol-sensitivity runs. Accordingly, Table 8 can be reconstructed from the saved summaries, but its metrics cannot be independently recomputed from per-origin forecasts in this package. This limitation is stated in the revised manuscript.

| Panel | File | Setting column and values | Model coverage | Rows |
|---|---|---|---|---|---|
| A | WINDOW_ROBUSTNESS_LONG.csv | Window = 252, 504, 756 | LSTM and Transformer, four assets | 24 |
| B | SEQLEN_ROBUSTNESS_LONG.csv | SeqLen = 20, 60, 120 | LSTM and Transformer, four assets | 24 |
| C | RETUNE_ROBUSTNESS_LONG.csv | TuneEvery = 21, 63, 126 | LSTM, four assets | 12 |

`Source=Robustness` denotes an additional protocol-sensitivity result; `Source=Main` denotes the baseline setting; `Source=Main_restricted` denotes the baseline result restricted to the common window-length evaluation period in Panel A. In Panel A, sample sizes are 3259 (CSI300), 3406 (SP500), 2100 (CSI1000), and 3564 (BTCUSD), identical across the compared settings for each asset. The sample-size and source fields remain in the input files; `tables/table8.csv` pivots their R_OS2 values into the three manuscript panels. There is no inference of missing run timestamps, software identities or other unavailable historical metadata.

The generation command is:

```bash
python analysis/make_tables.py --results predictions --robustness predictions/robustness --out tables
```

## Minor revision verification

The script for Tables 5, 6, and 8 was executed from the archived inputs. The twenty baseline aggregates were checked against the dated per-model forecast files. Table 6 contains 13 Holm-significant realized-loss comparisons with one lag and 14 with eight lags. Only Transformer/BTCUSD changes classification (0.06739551798 to 0.02766128729). All realized-loss point estimates are positive. No CW comparison is Holm-significant under either bandwidth. The eight LSTM rolling positive-window percentages agree with the manuscript to one decimal place. No model was retrained.

Table 5 displays MSE × 10^4 to five decimal places; its computational values are unchanged. Positive-window proportions in the manuscript are intentionally restricted to LSTM. The archived all-model rolling paths are retained as figure inputs.


## Main-text table numbering in this revision

All ten tables are in the main manuscript; there is no appendix or supplementary table. Tables 1–6 retain their numbers. Table 7 is the bandwidth comparison (formerly S1), Table 8 is protocol robustness (formerly Table 7), Table 9 is tuning-budget sensitivity (formerly Table 8), and Table 10 is seed stability (formerly Table 9). The CSV output names have been updated to match. The concise data and code availability statement follows Section 6 Conclusion under the unnumbered Data and Code Availability heading; file mappings and experimental settings remain in this documentation and RUN_MANIFEST.json.


## Final consistency audit

The implemented sensitivity bandwidth is floor(4*(N/100)^(2/9)), bounded to [1, N-1], a deterministic sample-size rule. It equals eight for all four samples; it is not a fitted data-dependent plug-in bandwidth. This clarification changes no numerical result.

The 15 additional-seed and larger-budget BTC/USD files contain tiny differences in stored realized returns and benchmark values relative to the baseline files (maximum absolute difference 4.6889668e-08). Re-evaluating their saved model forecasts against the baseline realized-return and HM vectors changes R2OS by at most 1.3364130e-09; all five-decimal R2OS entries and rankings remain unchanged. This is a sensitivity check on the stored inputs, not evidence about the original cause of the precision differences. The archived forecasts and input values have been preserved.

Full-precision Table 7 results are in tables/table7.csv and tables/table6_bandwidth.csv.
