# First-return construction notes

The first daily log return in each supplied prepared series uses the immediately preceding source-series observation:

\[
r_{t_0}=\log(P_{t_0}/P_{t_{-1}}),
\]

where \(t_{-1}\) is the prior available source observation, not an imputed or forward-filled value. The first observation dates and preceding values implied by the prepared CSVs are:

| Asset | First return date | Implied preceding source value |
|---|---:|---:|
| CSI 300 | 2010-01-04 | 3575.684 |
| S&P 500 | 2010-01-04 | 1115.10 |
| CSI 1000 | 2014-10-20 | 6058.668 |
| BTC/USD | 2014-09-18 | 457.334 |

These preceding values are inferred from the first stored return and the first in-sample source value. They are provided as a construction check, not as independently verified provider records. The preceding observation dates and values should be confirmed against the authors' original Wind, Yahoo Finance, and Coin Metrics exports before publication. The public source-data deposit is identified in data/README.md. Original provider export metadata are not included in this forecast-replication ZIP.

For BTC/USD, the series is Coin Metrics asset `btc`, metric `ReferenceRateUSD`, sampled at 00:00 UTC. It is a reference rate and should not be described as an exchange closing price. The equity series use the respective daily close fields recorded in `DATA_MANIFEST.csv`.
