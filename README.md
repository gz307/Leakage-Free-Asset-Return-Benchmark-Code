# Asset return benchmark code

This repository contains the forecasting and analysis code for *Do deep time-series architectures beat naive baselines? A leakage-free out-of-sample benchmark on asset returns*.

The accompanying Zenodo deposit cited in the manuscript contains this code together with the four prepared source-data CSVs, 70 saved model-asset forecast files, robustness summaries, and analysis outputs. It is the self-contained collection corresponding to the reported results. This code package does not duplicate the large prediction outputs or the source-data CSVs. No Release or publication-identifier setup is required to use the code.

## Contents and setup

- `code/final_experiment/`: configuration, training functions, model factory, and experiment runner.
- `official_models/`: supplied Autoformer, PatchTST, and iTransformer implementations and their licences. LSTM and the standard Transformer are implemented in the model factory.
- `analysis/`: scripts for the reported tables and figures.
- `data/`: source attribution, file specifications, and construction notes.
- `RUN_MANIFEST.json`: environment, seeds, tuning budgets, and experimental settings.
- `PROVENANCE.md`: mapping from saved inputs to paper results and reconstruction limits.

Install the dependencies in `requirements.txt`, using the environment described in `ENVIRONMENT.txt`. For retraining, copy the four source-data CSVs from the Zenodo archive into `data/`. For regeneration from saved predictions, use the complete Zenodo archive, whose README gives all analysis commands.

Example baseline run from the project root:

```bash
python code/final_experiment/run_experiment.py --asset CSI300 --model LSTM --mode full
```

The existing model checkpoints and rejected-trial Optuna histories are not included. Table 8 is reconstructed from saved summary metrics; per-origin forecasts for those protocol-sensitivity experiments are not included. These limitations do not prevent reconstruction of the displayed table from the archived summaries.

## Rights

Author-created analysis scripts and documentation retain their stated CC BY 4.0 licence. This does not relicense third-party source data or model implementations. The third-party model directories include their original licences. Data source attribution and applicable provider rights are described in `data/README.md` and the Zenodo archive.
