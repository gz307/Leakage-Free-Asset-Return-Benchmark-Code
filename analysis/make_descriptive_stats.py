# -*- coding: utf-8 -*-
"""Compute descriptive statistics from separately supplied daily log returns."""

import argparse
import os

import pandas as pd


FILES = {
    "CSI 300": "CSI300_daily_data.csv",
    "S&P 500": "SP500_daily_data.csv",
    "CSI 1000": "CSI1000_daily_data.csv",
    "BTC/USD": "BTC_USD_daily_data.csv",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="directory containing prepared return CSV files")
    parser.add_argument("--out", default="tables")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    rows = []
    missing = 0

    for name, filename in FILES.items():
        path = os.path.join(args.data, filename)
        if not os.path.isfile(path):
            print(f"missing: {path}")
            missing += 1
            continue

        frame = pd.read_csv(path)
        frame["Date"] = pd.to_datetime(
            frame["Date"].astype(str).str.replace("/", "-", regex=False)
        )
        returns = frame["Log_Return"].astype(float)
        row = {
            "Asset": name,
            "Start": str(frame["Date"].min().date()),
            "End": str(frame["Date"].max().date()),
            "N": len(frame),
            "Mean_pct": round(returns.mean() * 100, 6),
            "SD_pct": round(returns.std(ddof=1) * 100, 6),
            "Skewness": round(returns.skew(), 6),
            "Excess_kurtosis": round(returns.kurt(), 6),
        }
        rows.append(row)
        print(
            f"{name:<10} N={row['N']}  mean={row['Mean_pct']:.3f}%"
            f"  sd={row['SD_pct']:.3f}%  skew={row['Skewness']:.3f}"
            f"  exkurt={row['Excess_kurtosis']:.3f}"
        )

    output_path = os.path.join(args.out, "table1.csv")
    pd.DataFrame(rows).to_csv(output_path, index=False)
    print(f"saved: {output_path}")
    print(f"assets processed: {len(rows)}; missing files: {missing}")
    print("kurtosis: Fisher excess kurtosis (normal distribution = 0)")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
