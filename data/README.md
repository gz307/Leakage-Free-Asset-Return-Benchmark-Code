# Input data specification

This directory contains documentation only. Obtain and prepare input data separately, subject to each provider's access and reuse terms.

| Local filename | Series | Source | Price field or observation convention |
| --- | --- | --- | --- |
| `CSI300_daily_data.csv` | CSI 300 | Wind Financial Terminal | Unadjusted daily close |
| `SP500_daily_data.csv` | `^GSPC` | Yahoo Finance | Adjusted daily close |
| `CSI1000_daily_data.csv` | CSI 1000 | Wind Financial Terminal | Unadjusted daily close |
| `BTC_USD_daily_data.csv` | `btc` | Coin Metrics | `ReferenceRateUSD` sampled at 00:00 UTC |

Each file must contain:

- `Date`: one unique, parseable observation date per row.
- `Log_Return`: a finite numeric daily log return in decimal units, computed as `log(P_t / P_previous)`.

`Close` may be retained for source-price checks but is not read by the forecasting runner or the descriptive-statistics script. The BTC/USD reference rate is not an exchange closing price.

Use each asset's own observed calendar. Do not impute missing observations. Compute the first retained return using the preceding available source observation. Retain original provider exports and retrieval metadata separately for author-side verification.

The default runner reads these files from this directory. It expects historical observations in the intended evaluation period; it sorts dates and rejects duplicate dates and non-finite returns. This package includes neither provider downloads nor prepared datasets.

Provider references:

- Wind Financial Terminal: https://www.wind.com.cn/portal/zh/WFT/index.html
- Yahoo Finance: https://finance.yahoo.com/quote/%5EGSPC/history/
- Coin Metrics: https://docs.coinmetrics.io/market-data/reference-rates-overview/reference_rate
