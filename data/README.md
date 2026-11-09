# Data sources and local input files

The four source-data CSV files are included in the data/ directory of the public Zenodo archive alongside the complete code and replication materials; they are not restricted to reviewers. The GitHub code package contains this documentation; obtain the CSV files from the Zenodo deposit cited in the manuscript. Third-party ownership and applicable provider terms remain in effect. The four prepared files used by the forecasting runner must be placed in this directory (or supplied through `STOCK_EMH_PROJECT_ROOT`) with the filenames listed below. Each file must contain `Date` and `Log_Return`; `Close` is also required only when checking returns against source prices.

| File | Series and source | Field used | Sample period |
|---|---|---|---|
| `CSI300_daily_data.csv` | CSI 300, Wind Financial Terminal | Unadjusted close | 2010-01-04 to 2026-07-17 |
| `SP500_daily_data.csv` | `^GSPC`, Yahoo Finance | Adjusted close | 2010-01-04 to 2026-07-17 |
| `CSI1000_daily_data.csv` | CSI 1000, Wind Financial Terminal | Unadjusted close | 2014-10-20 to 2026-07-17 |
| `BTC_USD_daily_data.csv` | `btc`, Coin Metrics ReferenceRateUSD | Reference rate sampled at 00:00 UTC | 2014-09-18 to 2026-07-16 |

The retrieval dates are listed in `DATA_MANIFEST.csv`; source links are listed below. The Zenodo archive already places the source-data CSVs in the data directory for Table 1 or retraining. When using the GitHub code package, copy those files into data/. There is no automated provider downloader. Users obtaining the original provider series independently should use the documented fields and sample periods under the applicable provider terms.

## Rebuild Table 1

With the four prepared CSV files available locally, run from the archive root:

```bash
python analysis/make_descriptive_stats.py --data data --out tables
```

The script writes `tables/table1.csv` and checks dates, counts, means, sample standard deviations, skewness, and Fisher excess kurtosis against the manuscript's printed values. The normal distribution has excess kurtosis zero. This script checks the stored `Log_Return` values against Table 1; it does not independently validate the provider's original export or retrieve the preceding source price.

The full-sample return counts and out-of-sample counts follow the manuscript's convention: the first return uses the preceding observation from the relevant source series, and the out-of-sample count equals the full-sample count minus the initial 504-return window. The inferred preceding values and their verification limitation are recorded in `DATA_CONSTRUCTION_NOTES.md`. BTC/USD uses the Coin Metrics reference-rate timestamp at 00:00 UTC; it is not an exchange closing price.

## Provider references

- CSI 300 and CSI 1000: [Wind Financial Terminal](https://www.wind.com.cn/portal/zh/WFT/index.html)
- S&P 500, ticker `^GSPC`: [Yahoo Finance historical data](https://finance.yahoo.com/quote/%5EGSPC/history/)
- BTC/USD: [Coin Metrics Reference Rates](https://docs.coinmetrics.io/market-data/reference-rates-overview/reference_rate)
