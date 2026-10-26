"""Rebuild Tables 4, 8, and 9 from archived per-origin forecasts."""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ASSETS = ["CSI300", "SP500", "CSI1000", "BTCUSD"]
MODELS = ["LSTM", "Transformer", "Autoformer", "iTransformer", "PatchTST"]
ASSET_LABELS = {"CSI300": "CSI 300", "SP500": "S&P 500",
                "CSI1000": "CSI 1000", "BTCUSD": "BTC/USD"}


def load_prediction(root, run, asset, model):
    path = Path(root) / run / asset / f"{model}_predictions.csv"
    frame = pd.read_csv(path, parse_dates=["Date"])
    frame = frame.sort_values("Date").reset_index(drop=True)
    if frame.empty or frame["Date"].duplicated().any():
        raise ValueError(f"Invalid forecast file: {path}")
    last_known = pd.to_datetime(frame["LastKnownDate"])
    if not (last_known < frame["Date"]).all():
        raise ValueError(f"Temporal boundary violation in {path}")
    return frame


def r2os(frame, model):
    y = frame["True"].to_numpy(dtype=float)
    hm = frame["HM"].to_numpy(dtype=float)
    pred = frame[model].to_numpy(dtype=float) if model in frame else frame["Prediction"].to_numpy(dtype=float)
    denom = np.square(y - hm).sum()
    return float(1.0 - np.square(y - pred).sum() / denom)


def build_table8(root):
    rows = []
    for asset in ("CSI300", "BTCUSD"):
        base = {m: load_prediction(root, "final", asset, m) for m in MODELS}
        high = {m: load_prediction(root, "budget60", asset, m) for m in MODELS}
        # Each run uses the same asset dates and realized series.
        for model in MODELS:
            for f in (base[model], high[model]):
                if not f["Date"].equals(base[model]["Date"]):
                    raise ValueError(f"Date mismatch for {asset}/{model}")
                # BTCUSD has tiny source-rounding differences across archived runs.
                if not np.allclose(f["True"], base[model]["True"], atol=1e-6, rtol=0):
                    raise ValueError(f"Realized returns differ for {asset}/{model}")
        vals20 = {m: r2os(base[m], "Prediction") for m in MODELS}
        vals60 = {m: r2os(high[m], "Prediction") for m in MODELS}
        rank20 = {m: i + 1 for i, m in enumerate(sorted(MODELS, key=lambda x: vals20[x], reverse=True))}
        rank60 = {m: i + 1 for i, m in enumerate(sorted(MODELS, key=lambda x: vals60[x], reverse=True))}
        for model in MODELS:
            rows.append({"Asset": asset, "AssetLabel": ASSET_LABELS[asset], "Model": model,
                         "R2OS_20": vals20[model], "R2OS_60": vals60[model],
                         "Delta_R2OS": vals60[model] - vals20[model],
                         "Rank_20": rank20[model], "Rank_60": rank60[model]})
    return pd.DataFrame(rows)


def build_table9(root):
    rows = []
    for asset in ASSETS:
        by_seed = {}
        for run, seed in (("final", 42), ("seed7", 7), ("seed2024", 2024)):
            by_seed[seed] = {}
            seed_frames = {}
            for model in MODELS:
                frame = load_prediction(root, run, asset, model)
                seed_frames[model] = frame
                by_seed[seed][model] = r2os(frame, "Prediction")
            reference = seed_frames[MODELS[0]]
            for model in MODELS[1:]:
                frame = seed_frames[model]
                if not frame["Date"].equals(reference["Date"]):
                    raise ValueError(f"Date mismatch for {run}/{asset}/{model}")
                if not np.allclose(frame["True"], reference["True"], atol=1e-6, rtol=0):
                    raise ValueError(f"Realized returns differ for {run}/{asset}/{model}")
        ranks_by_model = {model: [] for model in MODELS}
        for seed in (42, 7, 2024):
            ordered = sorted(MODELS, key=lambda model: by_seed[seed][model], reverse=True)
            for rank, model in enumerate(ordered, 1):
                ranks_by_model[model].append(rank)
        for model in MODELS:
            vals = {seed: by_seed[seed][model] for seed in (42, 7, 2024)}
            ranks = ranks_by_model[model]
            rows.append({"Asset": asset, "AssetLabel": ASSET_LABELS[asset], "Model": model,
                         "R2OS_seed42": vals[42], "R2OS_seed7": vals[7],
                         "R2OS_seed2024": vals[2024], "Mean": np.mean(list(vals.values())),
                         "SD": np.std(list(vals.values()), ddof=1),
                         "Rank_min": min(ranks), "Rank_max": max(ranks)})
    return pd.DataFrame(rows)


def build_table4(root):
    records = []
    for asset in ASSETS:
        for model in MODELS:
            frame = load_prediction(root, "final", asset, model)
            for value in frame["HyperParameters"]:
                pars = json.loads(value) if isinstance(value, str) else value
                records.append({"Asset": asset, "Model": model, **pars})
    df = pd.DataFrame(records)
    categorical = {
        "LSTM": ["hidden_size", "num_layers"],
        "Transformer": ["num_layers", "d_model", "nhead", "d_ff"],
        "Autoformer": ["num_layers", "d_model", "nhead", "d_ff", "moving_avg"],
        "PatchTST": ["num_layers", "d_model", "nhead", "d_ff", "patch_len", "stride"],
        "iTransformer": ["num_layers", "d_model", "nhead", "d_ff"],
    }
    rows = []
    for model in MODELS:
        sub = df[df["Model"] == model]
        for field in categorical[model]:
            counts = sub[field].value_counts(dropna=True).sort_index()
            total = int(counts.sum())
            summary = ", ".join(f"{value:g} ({count / total:.1%})" for value, count in counts.items())
            rows.append({"Model": model, "Hyperparameter": field, "Summary": summary,
                         "ForecastOrigins": total})
        for field in ("lr", "dropout"):
            values = sub[field].dropna().astype(float)
            rows.append({"Model": model, "Hyperparameter": f"{field} (median; range)",
                         "Summary": f"{values.median():.6g}; {values.min():.6g}--{values.max():.6g}",
                         "ForecastOrigins": int(values.size)})
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", default="predictions")
    parser.add_argument("--out", default="tables")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    table8 = build_table8(args.predictions)
    table9 = build_table9(args.predictions)
    table4 = build_table4(args.predictions)
    for name, frame in (("table8.csv", table8), ("table9.csv", table9), ("table4.csv", table4)):
        frame.to_csv(out / name, index=False, float_format="%.12g")
        print(f"{name}: {len(frame)} rows -> {out / name}")
    print(f"Table 8: all negative at 60 trials={bool((table8.R2OS_60 < 0).all())}; "
          f"ordering unchanged in both assets={bool((table8.Rank_20 == table8.Rank_60).all())}; "
          f"mean absolute change={table8.Delta_R2OS.abs().mean():.6f}; "
          f"max absolute change={table8.Delta_R2OS.abs().max():.6f}")
    seed_columns = ["R2OS_seed42", "R2OS_seed7", "R2OS_seed2024"]
    stable_negative = int((table9[seed_columns] < 0).all(axis=1).sum())
    pooled_origins = sum(len(load_prediction(args.predictions, "final", a, m))
                         for a in ASSETS for m in MODELS)
    print(f"Table 9: all-negative seed triplets={stable_negative}/20; "
          f"mean SD={table9.SD.mean():.6f}")
    print(f"Table 4: selected configurations summarized over {pooled_origins} "
          "model-asset-origin records")


if __name__ == "__main__":
    main()
