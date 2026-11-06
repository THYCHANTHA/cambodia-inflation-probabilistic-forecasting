# Next steps

Status 2026-11-06: protocol v1.0 frozen; Stage 3 skeleton tested on synthetic data; the core Phnom Penh series was
ingested and exploratory figures 1-5 were produced (gate G1 opened). No model has been fitted to real data; modelling
needs gate G4.

## Gates (from RESEARCH_PROTOCOL.md)

| Gate | What resolves it | Owner |
|---|---|---|
| G1 Real-data ingestion | **Opened 2026-11-06** (owner reports permission to plot; file the written permission) | Owner |
| G2 2026 extension | Run the implemented checks on all nine NIS tables (2026-01 to 2026-09) and record the result | Assistant, after G1 |
| G3 Publication | Written replies from Data EF/GDDE, NBC and NIS on the questions in DATA_RIGHTS_AND_ATTRIBUTION.md §5 | Owner sends the request |
| G4 Real-data modelling | Owner approval | Owner |

## Stage 3: done

- Data: `M/1/YYYY` parser and detector for the DD/MM swap; monthly validation (frequency, order, duplicates, missing
  months, positivity, finiteness); observation-level provenance and the gate-G2 extension checks.
- Statistics: monthly log changes, simple and log YoY, exact log/percentage transforms.
- Forecasting: identity K + U with the exact quantile transform; window specs MAIN, ROLL, P2010-96, P2010-120, LAG2;
  origin/cutoff/target alignment with publication lag; dev/test split; backtest loop with leakage guards and
  per-(origin, horizon) seeding.
- Evaluation: pinball, interval score, WIS (two independent implementations), Gaussian and sample CRPS, coverage, width,
  quantile-bin histogram, PIT check, MAE, RMSE, MASE.
- Reference benchmarks B0(b) and B2 (needed to exercise the pipeline; not yet run on real data).
- Prospective registry: publication calendar, cutoff rule, append-only hashed issuance and outcome records, storage
  outside the repository enforced.
- 139 tests passed, Ruff clean (`reports/stage3_pytest.txt`, `reports/stage3_ruff.txt`). Two deliberate faults (one
  extra month leaked to the model; known window shifted by one month) were each caught by the tests (7 and 8 failures)
  and then reverted byte-for-byte.

## Stage 4 (partial): exploratory figures done 2026-11-06

- Core Data EF file fetched once to `%USERPROFILE%\portfolio-data\p11-inflation\raw\` (12,893 B; SHA-256 identical to the audit);
  `configs/data_manifest.toml` records it. Loader `data/loader.py` checks the hash and recomputes every portal column.
- Finding: the portal's `YoY_3/12_Month_Avg` are YoY changes of the 3/12-month average index, not averages of YoY rates
  as the metadata states (DATA_SOURCE_AUDIT.md §3).
- Figures 1-5 (PNG + PDF): `python scripts/make_eda_figures.py` -> `reports/figures/eda/`; summary `reports/eda_summary.txt`.
  Both git-ignored until publication scope is documented. Figures 6-12 need modelling (gate G4).
- 149 tests passed, Ruff clean.

## Stage 3: remaining

1. (done) Data EF loader.
2. Reader for NIS Excel tables (Table 2) that ignores the Excel date serial and reads base, geography and weights
   from the sheet; needs `openpyxl` (system, present) and `xlrd` for `.xls` (not installed in the venv; a decision is
   needed: install `xlrd` 2.0.1 (~0.8 MB) or convert files manually).
3. Manifest format and storage location outside Git (`%USERPROFILE%\portfolio-data\p11-inflation\`).
4. Remaining benchmark B0(a) (Gaussian persistence) and B1 (rolling mean).
5. Inference module: Diebold-Mariano with Newey-West (lag h-1) and HLN correction; moving-block bootstrap; Holm.
6. Student-t CRPS (closed form) for P-T.
7. (done for EDA) Plot style module; forecast figures 6-12 still to build.
8. `statsmodels` will be needed for the SARIMA/ETS models (Stage 5; not installed; tens of MB).
9. Command-line entry points (`scripts/`) for validation, backtest and prospective issuance.
10. Git: `git init` and the first commit only after the owner approves; the protocol v1.0 commit hash then goes into
    RESEARCH_PROTOCOL.md.

## Deferred

NBC covariates (page unreadable); IMF transmission cross-check; ETS; GARCH (conditional on the ARCH-LM rule).
