# -*- coding: utf-8 -*-
"""
make_tables.py -- regenerate Table 5, Table 6 and Table 7 of the manuscript
from archived out-of-sample forecast files.

Usage
-----
    python make_tables.py --results results/final --out tables

Inputs (must exist)
-------------------
    results/final/analysis/{ASSET}_OOS_ALL.csv
        columns: Date, True, HM, PER, LSTM, Transformer, Autoformer, PatchTST, iTransformer
    results/robustness/analysis/WINDOW_ROBUSTNESS_LONG.csv
    results/robustness/analysis/SEQLEN_ROBUSTNESS_LONG.csv
    results/robustness/analysis/RETUNE_ROBUSTNESS_LONG.csv

Outputs
-------
    tables/table5.csv            point estimates (MSE, MAE, R2OS, DA, N)
    tables/table6.csv            predictive-accuracy tests vs HM and PER
    tables/table6_bandwidth.csv Clark-West with lag 1 vs automatic bandwidth
    tables/table7.csv            robustness of R2OS to W, L and the re-tuning interval

Statistical conventions (must match the manuscript)
---------------------------------------------------
* Forecast loss is squared error.
* R2OS = 1 - SSE(model) / SSE(HM); HM has R2OS = 0 by construction.
* Newey-West (Bartlett) HAC variance.
  - Primary specification: one lag (as stated in Section 3.6 of the manuscript).
  - Sensitivity: Newey-West (1994) automatic bandwidth
        floor(4 * (n/100)^(2/9)), bounded to [1, n-1].
* Clark-West: f_t = e_HM,t^2 - e_m,t^2 + (HM_t - m_t)^2,
  one-sided upper-tail standard-normal p-value.
 * Realised loss differential: d_t = e_m,t^2 - e_HM,t^2 (positive = model worse than HM),
   two-sided Student-t(N-1) p-value, Holm-adjusted over the 20 model-asset comparisons.
* DM-HLN against PER: d_t = e_PER,t^2 - e_m,t^2 (positive = model better than PER),
  HLN small-sample correction, one-sided Student-t(N-1) p-value. Holm adjustment
  is applied separately to the CW, realised-loss, and DM-HLN families.
"""

import argparse
import math
import os
from pathlib import Path

import numpy as np
import pandas as pd

ASSETS = ["CSI300", "SP500", "CSI1000", "BTCUSD"]
MODELS = ["LSTM", "Transformer", "Autoformer", "PatchTST", "iTransformer"]


# ----------------------------------------------------------------------
# HAC helpers
# ----------------------------------------------------------------------
def nw_variance(x, lag):
    """Newey-West long-run variance with Bartlett weights."""
    x = np.asarray(x, dtype=float)
    n = x.size
    xc = x - x.mean()
    s = float(np.dot(xc, xc) / n)
    for ell in range(1, lag + 1):
        w = 1.0 - ell / (lag + 1.0)
        s += 2.0 * w * float(np.dot(xc[ell:], xc[:-ell]) / n)
    return s


def auto_bandwidth(n):
    """Newey-West (1994) plug-in bandwidth, bounded to [1, n-1]."""
    return int(max(1, min(math.floor(4.0 * (n / 100.0) ** (2.0 / 9.0)), n - 1)))


def normal_sf(z):
    """Upper-tail standard-normal probability."""
    return 0.5 * math.erfc(z / math.sqrt(2.0))


def _beta_continued_fraction(a, b, x):
    """Continued fraction used by the regularized incomplete beta function."""
    max_iter, eps, tiny = 300, 3.0e-14, 1.0e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for m in range(1, max_iter + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            return h
    raise ArithmeticError("Incomplete-beta continued fraction did not converge")


def regularized_beta(x, a, b):
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    front = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                     + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _beta_continued_fraction(a, b, x) / a
    return 1.0 - front * _beta_continued_fraction(b, a, 1.0 - x) / b


def student_t_sf(value, df):
    """Student-t upper-tail probability without an external SciPy dependency."""
    if value == 0.0:
        return 0.5
    x = df / (df + value * value)
    tail = 0.5 * regularized_beta(x, df / 2.0, 0.5)
    return tail if value > 0 else 1.0 - tail


def student_t_ppf(probability, df):
    """Student-t quantile by bisection; used for two-sided 95% intervals."""
    if not 0.0 < probability < 1.0:
        raise ValueError("probability must lie strictly between zero and one")
    if probability == 0.5:
        return 0.0
    if probability < 0.5:
        return -student_t_ppf(1.0 - probability, df)
    low, high = 0.0, 1.0
    while student_t_sf(high, df) > 1.0 - probability:
        high *= 2.0
    for _ in range(100):
        mid = (low + high) / 2.0
        if student_t_sf(mid, df) > 1.0 - probability:
            low = mid
        else:
            high = mid
    return (low + high) / 2.0


def holm(pvalues):
    """Holm step-down adjustment."""
    p = np.asarray(pvalues, dtype=float)
    m = p.size
    order = np.argsort(p)
    adjusted = np.empty(m)
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, min((m - rank) * p[idx], 1.0))
        adjusted[idx] = running
    return adjusted


# ----------------------------------------------------------------------
# Table 5
# ----------------------------------------------------------------------
def build_table5(frames):
    rows = []
    for asset, df in frames.items():
        y = df["True"].to_numpy()
        sse_hm = np.sum((y - df["HM"].to_numpy()) ** 2)
        for model in ["HM", "PER"] + MODELS:
            pred = df[model].to_numpy()
            err = y - pred
            rows.append({
                "Asset": asset,
                "Model": model,
                "MSE": float(np.mean(err ** 2)),
                "MAE": float(np.mean(np.abs(err))),
                "R2OS": float(1.0 - np.sum(err ** 2) / sse_hm),
                "DA": float(np.mean(np.sign(y) == np.sign(pred))),
                "N": int(y.size),
            })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Table 6
# ----------------------------------------------------------------------
def build_table6(frames, lag=1):
    rows = []
    for asset, df in frames.items():
        y = df["True"].to_numpy()
        n = y.size
        hm = df["HM"].to_numpy()
        per = df["PER"].to_numpy()
        e_hm = y - hm
        e_per = y - per
        sse_hm = np.sum(e_hm ** 2)
        bw = auto_bandwidth(n)
        for model in MODELS:
            pred = df[model].to_numpy()
            e_m = y - pred

            # Clark-West adjusted differential
            f = e_hm ** 2 - e_m ** 2 + (hm - pred) ** 2
            cw_lag1 = f.mean() / math.sqrt(nw_variance(f, 1) / n)
            cw_auto = f.mean() / math.sqrt(nw_variance(f, bw) / n)

            # Realised squared-loss differential, positive = model worse than HM
            d = e_m ** 2 - e_hm ** 2
            se_lag1 = math.sqrt(nw_variance(d, lag) / n)
            se_auto = math.sqrt(nw_variance(d, bw) / n)
            z_lag1 = d.mean() / se_lag1
            z_auto = d.mean() / se_auto
            tcrit = student_t_ppf(0.975, n - 1)

            # DM-HLN against PER, positive = model better than PER
            dm_d = e_per ** 2 - e_m ** 2
            dm = dm_d.mean() / math.sqrt(nw_variance(dm_d, 1) / n)
            # For horizon H=1, the HLN factor is sqrt((N-1)/N).
            hln = math.sqrt((n - 1.0) / n)
            dm_hln = dm * hln

            rows.append({
                "Asset": asset,
                "Model": model,
                "N": int(n),
                "R2OS": float(1.0 - np.sum(e_m ** 2) / sse_hm),
                "CW_lag1": float(cw_lag1),
                "p_CW_lag1": float(normal_sf(cw_lag1)),
                "CW_auto": float(cw_auto),
                "p_CW_auto": float(normal_sf(cw_auto)),
                "dMSE_x1e4": float(d.mean() * 1e4),
                "dMSE_SE_x1e4": float(se_lag1 * 1e4),
                "dMSE_CI95_low": float((d.mean() - tcrit * se_lag1) * 1e4),
                "dMSE_CI95_high": float((d.mean() + tcrit * se_lag1) * 1e4),
                "p_dMSE_lag1": float(2.0 * student_t_sf(abs(z_lag1), n - 1)),
                "p_dMSE_auto": float(2.0 * student_t_sf(abs(z_auto), n - 1)),
                "DM_HLN": float(dm_hln),
                "p_DM": float(student_t_sf(dm_hln, n - 1)),
                "HAC_bandwidth_auto": int(bw),
            })
    table = pd.DataFrame(rows)
    table["p_CW_holm"] = holm(table["p_CW_lag1"])
    table["p_CW_auto_holm"] = holm(table["p_CW_auto"])
    table["p_dMSE_holm"] = holm(table["p_dMSE_lag1"])
    table["p_dMSE_auto_holm"] = holm(table["p_dMSE_auto"])
    table["p_DM_holm"] = holm(table["p_DM"])
    table["sig_CW_holm"] = table["p_CW_holm"] < 0.05
    table["sig_CW_auto_holm"] = table["p_CW_auto_holm"] < 0.05
    table["sig_dMSE_holm"] = table["p_dMSE_holm"] < 0.05
    table["sig_dMSE_auto_holm"] = table["p_dMSE_auto_holm"] < 0.05
    table["sig_DM_holm"] = table["p_DM_holm"] < 0.05
    return table


# ----------------------------------------------------------------------
# Table 7
# ----------------------------------------------------------------------
def build_table7(results_root):
    """results_root is the robustness results directory (…/results/robustness)."""
    anal = os.path.join(results_root, "analysis")
    out = []

    path = os.path.join(anal, "WINDOW_ROBUSTNESS_LONG.csv")
    if os.path.isfile(path):
        df = pd.read_csv(path)
        col_r2 = [c for c in df.columns if c.lower() in ("ros2", "r_os2", "r2os")][0]
        col_w = [c for c in df.columns if c.lower() in ("window", "w")][0]
        pivot = df.pivot_table(index=["Asset", "Model"], columns=col_w, values=col_r2)
        for (asset, model), row in pivot.iterrows():
            out.append({"Panel": "A: window length W", "Asset": asset, "Model": model,
                        **{f"value_{int(k)}": float(v) for k, v in row.dropna().items()}})

    path = os.path.join(anal, "SEQLEN_ROBUSTNESS_LONG.csv")
    if os.path.isfile(path):
        df = pd.read_csv(path)
        col_r2 = [c for c in df.columns if c.lower() in ("ros2", "r_os2", "r2os")][0]
        col_l = [c for c in df.columns if c.lower() in ("seqlen", "seq_len", "seqlength", "l")][0]
        pivot = df.pivot_table(index=["Asset", "Model"], columns=col_l, values=col_r2)
        for (asset, model), row in pivot.iterrows():
            out.append({"Panel": "B: input length L", "Asset": asset, "Model": model,
                        **{f"value_{int(k)}": float(v) for k, v in row.dropna().items()}})

    path = os.path.join(anal, "RETUNE_ROBUSTNESS_LONG.csv")
    if os.path.isfile(path):
        df = pd.read_csv(path)
        col_r2 = [c for c in df.columns if c.lower() in ("ros2", "r_os2", "r2os")][0]
        col_k = [c for c in df.columns
                 if c.lower() in ("tuneevery", "retune", "interval", "tune_every", "k")][0]
        pivot = df.pivot_table(index=["Asset", "Model"], columns=col_k, values=col_r2)
        for (asset, model), row in pivot.iterrows():
            out.append({"Panel": "C: re-tuning interval", "Asset": asset, "Model": model,
                        **{f"value_{int(k)}": float(v) for k, v in row.dropna().items()}})

    return pd.DataFrame(out)


def _fmt_p(value, digits=3):
    return r"$<0.001$" if value < 0.001 else f"{value:.{digits}f}"


def write_table6_tex(table, path):
    """Write the 20 body rows for the manuscript's Table 6."""
    asset_labels = {"CSI300": "CSI 300", "SP500": r"S\&P 500",
                    "CSI1000": "CSI 1000", "BTCUSD": "BTC/USD"}
    rows = []
    for asset in ASSETS:
        subset = table[table["Asset"] == asset].set_index("Model")
        for index, model in enumerate(MODELS):
            r = subset.loc[model]
            asset_cell = asset_labels[asset] if index == 0 else ""
            r2 = f"${r['R2OS']:.5f}$"
            cw = (f"\\phantom{{-}}{r['CW_lag1']:.4f}" if r["CW_lag1"] >= 0
                  else f"${r['CW_lag1']:.4f}$")
            d_ci = (f"{r['dMSE_x1e4']:.3f} [{r['dMSE_CI95_low']:.3f}, "
                    f"{r['dMSE_CI95_high']:.3f}]")
            dm = f"{r['DM_HLN']:.3f}"
            rows.append(
                f"{asset_cell} & {model} & {r2} & {cw} & {_fmt_p(r['p_CW_lag1'], 4)} & "
                f"{r['p_CW_holm']:.3f} & {d_ci} & {_fmt_p(r['p_dMSE_lag1'])} & "
                f"{_fmt_p(r['p_dMSE_holm'])} & {dm} & {_fmt_p(r['p_DM'])} & "
                f"{_fmt_p(r['p_DM_holm'])} \\\\")
        if asset != ASSETS[-1]:
            rows.append(r"\midrule")
    Path(path).write_text("\n".join(rows) + "\n", encoding="utf-8")


# ----------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results/final")
    ap.add_argument("--robustness", default="results/robustness")
    ap.add_argument("--out", default="tables")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)

    frames = {}
    for asset in ASSETS:
        path = os.path.join(args.results, "analysis", f"{asset}_OOS_ALL.csv")
        df = pd.read_csv(path)
        df["Date"] = pd.to_datetime(df["Date"])
        frames[asset] = df.sort_values("Date").reset_index(drop=True)

    table5 = build_table5(frames)
    table6 = build_table6(frames)
    table7 = build_table7(args.robustness)

    table5.to_csv(os.path.join(args.out, "table5.csv"), index=False, float_format="%.10f")
    table6.to_csv(os.path.join(args.out, "table6.csv"), index=False, float_format="%.12g")
    write_table6_tex(table6, os.path.join(args.out, "table6_body.tex"))
    table7.to_csv(os.path.join(args.out, "table7.csv"), index=False, float_format="%.10f")

    bw = table6[["Asset", "Model", "CW_lag1", "p_CW_lag1", "p_CW_holm",
                 "CW_auto", "p_CW_auto", "p_CW_auto_holm", "dMSE_x1e4", "p_dMSE_lag1",
                 "p_dMSE_holm", "p_dMSE_auto", "p_dMSE_auto_holm",
                 "HAC_bandwidth_auto"]]
    bw.to_csv(os.path.join(args.out, "table6_bandwidth.csv"), index=False, float_format="%.12g")

    print(f"Table 5: {len(table5)} rows -> {args.out}/table5.csv")
    print(f"Table 6: {len(table6)} rows -> {args.out}/table6.csv")
    print(f"Table 7: {len(table7)} rows -> {args.out}/table7.csv")
    print()
    print("Clark-West, Holm-adjusted, minimum p = "
          f"{table6['p_CW_holm'].min():.4f} "
          f"({int(table6['sig_CW_holm'].sum())} significant at 5%)")
    print("Realised loss differential, Holm-adjusted, "
          f"{int(table6['sig_dMSE_holm'].sum())} of {len(table6)} significant at 5%, "
          f"{int((table6['dMSE_x1e4'] > 0).sum())} positive (model worse than HM)")
    print("DM-HLN vs persistence, Holm-adjusted, "
          f"{int(table6['sig_DM_holm'].sum())} of {len(table6)} significant at 5%, "
          f"minimum statistic = {table6['DM_HLN'].min():.4f}")
    print("Realised loss, automatic bandwidth, Holm-adjusted, "
          f"{int(table6['sig_dMSE_auto_holm'].sum())} of 20 significant at 5%")
    print("Clark-West, automatic bandwidth, Holm-adjusted, "
          f"{int(table6['sig_CW_auto_holm'].sum())} of 20 significant at 5%")


if __name__ == "__main__":
    main()
