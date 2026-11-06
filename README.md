# Probabilistic Forecasting of Phnom Penh Consumer Price Inflation

*A Time-Series Study of Forecast Uncertainty*

**Status (2026-11-06):** research protocol v1.0 frozen; software tested on synthetic data; the core Phnom Penh CPI
series has been ingested locally and exploratory figures 1-5 produced. **No model has been fitted to real data and there
are no forecasting results.** Data, figures and other real-data outputs are not stored in this repository (see
[Data and rights](#data-and-rights-summary)); `python scripts/make_eda_figures.py` regenerates the figures from a
locally supplied data file.

## Research problem

The study asks whether probabilistic forecasting methods give better-calibrated and sharper predictive distributions of
consumer price inflation than conventional benchmarks, at horizons of 1, 3, 6 and 12 months, and whether forecast
uncertainty changes across inflation regimes. The target is year-on-year inflation of the **NIS Consumer Price Index for
Phnom Penh** (October-December 2006 = 100, SES 2004 weights). It is not a national index, and this project never
describes it as national inflation.

## Data and rights (summary)

- The Data EF dataset "Cambodia's Inflation Rate 2005-2025" is the NIS Phnom Penh CPI, although its title says
  "Cambodia" (verified against NIS releases; [audit](docs/DATA_SOURCE_AUDIT.md)).
- Two samples: **core** 2006-01 to 2025-12 (240 YoY months) and **extended** to 2026-09 (249), the extension subject to
  validation gate G2.
- A new CPI (SES 2019 weights, provincial coverage) was planned for December 2025 but is not in any NIS release up to
  September 2026. It will not be spliced onto the old series.
- Research use is permitted by the Data EF Terms of Use; redistribution of raw or transformed data is not addressed.
  **No data are stored in this repository** ([rights](docs/DATA_RIGHTS_AND_ATTRIBUTION.md)).

## Method (planned; see the protocol)

The 12-month log change is the sum of 12 monthly log changes, $x_t = 100\,\Delta\ln P_t$. At cutoff $C$, the target
$C+k$ splits into an observed part (the last $12-k$ monthly changes) and a future part (the remaining $\min(k,12)$).
Models forecast the future part; quantiles are mapped exactly to percentage YoY. Benchmarks include persistence, a
rolling mean and a known-component + seasonal-mean benchmark. Evaluation is expanding-window rolling-origin with
WIS (primary), CRPS, pinball loss, coverage, sharpness, MAE/RMSE/MASE, Diebold-Mariano (HLN) and block bootstrap. A
separate, timestamped prospective forecast record respects the actual publication lag.

## Repository layout

```
configs/protocol.toml            all protocol v1.0 settings
docs/                            audit, rights, measurement, protocol, next steps
src/cambodia_inflation/
  data/        parsing.py (M/1/YYYY, DD/MM swap detection), validation.py, provenance.py (gate G2), synthetic.py
  statistics/  transforms.py (x_t, YoY, log YoY, exact transforms)
  forecasting/ identity.py (K + U), windows.py (5 specs), quantiles.py, backtest.py
  evaluation/  scoring.py (pinball, WIS, CRPS, coverage, PIT bins), point.py (MAE, RMSE, MASE)
  models/      benchmarks.py (B0b persistence, B2 known component; reference implementations)
  prospective/ registry.py (append-only, hashed, publication-lag-aware forecast records)
  visualization/ style.py, eda.py (figures 1-5)
scripts/make_eda_figures.py      figures 1-5 + summary from the data file (outputs git-ignored)
configs/data_manifest.toml       expected file name and SHA-256 of the data file (the file itself is not in the repo)
tests/                           149 tests on synthetic data
reports/                         unedited test and lint output (real-data outputs are git-ignored)
paper/references.bib             verified references only
```

## Reproduce the checks

```
python -m venv --system-site-packages .venv      # reuses NumPy, pandas, SciPy, pytest (see requirements.txt)
.venv\Scripts\python -m pytest -q                 # 149 passed on 2026-11-06
ruff check src tests scripts && ruff format --check src tests scripts
```

Figures 1-5: download the CSV manually from the Data EF dataset page
(https://data.mef.gov.kh/datasets/pd_66a9f36b36d76b00019fe83b), save it under the file name in
`configs/data_manifest.toml` in `%USERPROFILE%\portfolio-data\p11-inflation\raw\` (or set `P11_DATA_DIR`), then run
`set PYTHONPATH=src` and `.venv\Scripts\python scripts\make_eda_figures.py`. The script refuses a file whose SHA-256
differs from the manifest.

## Documents

| Document | Content |
|---|---|
| [docs/RESEARCH_PROTOCOL.md](docs/RESEARCH_PROTOCOL.md) | Protocol v1.0 (frozen): questions, hypotheses, identity, models, windows, metrics, prospective system, gates |
| [docs/DATA_SOURCE_AUDIT.md](docs/DATA_SOURCE_AUDIT.md) | Four candidate sources, verification against NIS, consistency checks, decisions |
| [docs/DATA_RIGHTS_AND_ATTRIBUTION.md](docs/DATA_RIGHTS_AND_ATTRIBUTION.md) | What the terms permit, activity by activity; attribution wording |
| [docs/MEASUREMENT_AND_SERIES_BREAKS.md](docs/MEASUREMENT_AND_SERIES_BREAKS.md) | Index methodology, planned vs implemented changes, candidate breaks, samples |
| [docs/NEXT_STEPS.md](docs/NEXT_STEPS.md) | Gates, completed and remaining Stage 3 work |

## Licence

Not chosen yet (owner decision). Any data licence is separate from the code licence; see the rights document.
