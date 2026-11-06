# Research protocol

**Version 1.0, FROZEN 2026-11-06.** Written before any model was fitted to real data. v0.1 (draft, same date) contained
four items marked [OWNER]; the owner decided all four on 2026-11-06 (section 13). Every later change goes into the
deviations log (section 14) with date and reason. The Git commit hash of this version is recorded when the repository is
created (none exists yet; the owner has not approved a commit).

**Gates that remain open (the protocol is frozen, the research is not unblocked):**

| Gate | Blocks | Status |
|---|---|---|
| G1 Data-use permission for real-data ingestion | Stage 4 onward | **Opened 2026-11-06** for the core Data EF file on the owner's report that permission to plot was granted (written evidence to be filed; DATA_RIGHTS §1a) |
| G2 Validation of the nine 2026 NIS observations (section 4.3) | Extended sample | Not done (only five of nine months were opened during the audit) |
| G3 Publication rights (raw, transformed and derived outputs) | Any public release, including prospective-forecast records | Unresolved; written confirmation requested from MEF/NIS |
| G4 Owner approval of real-data modelling | Stage 5 | Not given |

## 1. Disclosure of what has already been seen

Before this protocol was written the analyst had seen, during the data audit: the summary statistics in
DATA_SOURCE_AUDIT.md §3 (full-sample YoY mean, SD, extremes, negative-YoY months, largest monthly changes), the
2024-2025 monthly values, and selected 2026 headline values (Feb 2.6%, Mar 5.6%, Sep 5.3% YoY). No model was fitted and
no forecast was compared with an outcome. Historical values are public, so the historical evaluation is
**pseudo-out-of-sample, not blind**. The prospective system (section 10) provides genuinely ex-ante forecasts.

## 2. Title and geographic scope

**Title:** *Probabilistic Forecasting of Phnom Penh Consumer Price Inflation: A Time-Series Study of Forecast Uncertainty.*

The target is the NIS Consumer Price Index for **Phnom Penh** (October-December 2006 = 100, SES 2004 weights, 258 items).
The historical series is never described as national or Cambodian inflation, in any document, table, figure, axis label
or caption. Inspiration: the distributional-forecasting research direction of Baruník and Hanus (e.g. *Taming
data-driven probability distributions*, Journal of Forecasting, 2025); this project applies established statistical
methods and does not reproduce or claim their methods.

## 3. Research questions and testable hypotheses

- **RQ1.** Can statistical models produce reliable probabilistic forecasts of Phnom Penh CPI inflation at horizons of
  1, 3, 6 and 12 months? *Reliable* means empirical coverage of the 50/80/90% central intervals consistent with nominal
  levels (block-bootstrap/HAC confidence intervals, section 11.3) and no gross departure in the PIT/quantile-bin histogram.
- **RQ2.** Do probabilistic models improve on conventional benchmarks in calibration, sharpness and accuracy?
- **RQ3.** Does forecast uncertainty change across inflation regimes?

| Hypothesis | Operational form (test set, each horizon separately) |
|---|---|
| H1: autoregressive models give useful baseline forecasts | Relative MAE (AR / persistence) < 1 and relative WIS < 1, with DM-HLN test and block-bootstrap CI. Skill is also judged against the known-component benchmark B2, because short-horizon accuracy is largely mechanical (section 5.3) |
| H2: suitable probabilistic models improve calibration over simple benchmark distributions | Student-t, bootstrap, quantile-regression and recalibrated models have lower WIS than the Gaussian model and coverage closer to nominal |
| H3: uncertainty varies across periods | Mean interval width, WIS and coverage differ across the pre-specified subperiods (section 9.3); ARCH-LM test on monthly residuals |

Hypotheses may be rejected; results are reported for every model and horizon regardless.

## 4. Data samples

### 4.1 Two samples (owner decision 2)

| Sample | YoY months | Index months used | Sources | Role |
|---|---|---|---|---|
| **Core** | 2006-01 to 2025-12 (240) | 2005-01 to 2025-12 | Data EF `pd_66a9f36b36d76b00019fe83b` (NIS Phnom Penh CPI) | Historical comparison specification; all primary results are reported for it |
| **Extended** | 2006-01 to 2026-09 (249) | 2005-01 to 2026-09 | Core + NIS monthly tables Jan-Sep 2026 | Reported alongside the core sample, only after gate G2 passes |

Every observation carries its provenance (source id, file name, file SHA-256). Where the extension files repeat a core
month (e.g. Dec 2025 in the Jan 2026 table), the core value is kept and the repeat is used only as an overlap check.

### 4.2 Recomputation rule

YoY values are recomputed from the index; portal-supplied MoM, YoY and moving-average columns are used only to validate.
The 2005 portal YoY values depend on 2004 index values that are not in the dataset and are not used.

### 4.3 Gate G2: validation of the 2026 extension (all must pass, per month)

1. Nine distinct months, 2026-01 to 2026-09, each read from an NIS table and parsed without relying on the Excel date
   serial (the Sep 2026 file labels its September column with the serial for August 2026).
2. Definition: title states Phnom Penh; base "October - December 2006 = 100".
3. Weights: the 12 COICOP group weights equal those of the core period files (food 44.775, ..., miscellaneous 2.285).
4. Geography: Phnom Penh, no provincial component.
5. Consistency with the old system: every overlap month (a previous-month or previous-year column in a 2026 file) agrees
   with the core value to within rounding (|difference| <= 0.006 index points against the 2-decimal core value).
6. Recorded with source file and SHA-256. Failure of any check keeps the month out of the extended sample and is reported.

The software implements these checks (`data.provenance`); they have not yet been run on real files.

## 5. Target and the forecast identity

### 5.1 Definitions

With $P_t$ the all-items index for month $t$:

$$x_t = 100\,\Delta\ln P_t = 100\,(\ln P_t-\ln P_{t-1}),$$

$$y^{\log}_t = 100\,(\ln P_t-\ln P_{t-12}) = \sum_{j=0}^{11} x_{t-j},\qquad
y_t = 100\,(P_t/P_{t-12}-1) = g\!\left(y^{\log}_t\right),\quad g(v)=100\,(e^{v/100}-1).$$

**Primary target:** $y_t$ (simple YoY, the published definition). **Robustness target:** $y^{\log}_t$.

### 5.2 Decomposition at a forecast origin

Let $C$ be the information cutoff (last month whose index is in the information set) and $k\ge1$ the number of months
from $C$ to the target month $C+k$. Then

$$y^{\log}_{C+k} = \underbrace{\sum_{j=k}^{11} x_{C+k-j}}_{K_{C,k}\ \text{(observed at }C)} \;+\; \underbrace{\sum_{j=0}^{\min(k,12)-1} x_{C+k-j}}_{U_{C,k}\ \text{(future)}},\qquad K_{C,k}=0\ \text{for}\ k\ge 12.$$

$K_{C,k}$ is the sum of the last $12-k$ observed monthly changes; $U_{C,k}$ is the sum of the $\min(k,12)$ future
monthly changes that fall inside the target's 12-month window.

### 5.3 Forecasting rule (owner decision 5)

For every model in the monthly family the predictive distribution of $U_{C,k}$ is produced (by simulating paths of
$x_{C+1},\dots,x_{C+k}$ or directly), then

$$F_{y^{\log}_{C+k}}(v) = F_{U_{C,k}}\!\left(v-K_{C,k}\right),\qquad q^{y}_\tau = g\!\left(K_{C,k}+q^{U}_\tau\right).$$

Because $g$ is strictly increasing, quantiles transform exactly; means do not ($E[g(V)]\neq g(E[V])$), so point
forecasts are medians (section 11.1). Simulated paths give forecasts for all horizons from one set of draws, so the
distributions at different horizons are mutually consistent. The relevant horizon for the identity is $k=h+\ell$, where
$h$ is the nominal horizon from the origin and $\ell$ the publication lag in months (section 8.4).

Consequences stated in the paper: (i) at $k=1$, eleven of twelve components are observed, so short-horizon accuracy is
largely mechanical; (ii) forecast errors at horizon $k$ overlap across consecutive origins (MA($k-1$) structure), so
consecutive forecasts are **not** independent (section 11.3).

## 6. Models

All models are refitted at every origin using only data with dates $\le C$. Orders and hyperparameters are chosen inside
each training window by information criteria or are fixed below. Quantile levels
$\mathcal{T}=\{0.05,0.10,0.25,0.50,0.75,0.90,0.95\}$.

### 6.1 Benchmarks

| ID | Model | Predictive distribution |
|---|---|---|
| B0 | Persistence $\hat y_{C+k}=y_C$ (for YoY this equals the past-year average of monthly inflation) | (a) Gaussian with variance of past $k$-step changes; (b) empirical quantiles of past $k$-step changes $y_{s+k}-y_s$, $s+k\le C$ |
| B1 | Mean of $y$ over the last 12 months (36 as robustness) | Empirical quantiles of its past $k$-step errors |
| B2 | **Known component + seasonal mean:** $K_{C,k}$ plus the sum of training-window calendar-month means of $x$ for the future months in the window | Empirical quantiles of past errors of $U$ |

### 6.2 Statistical models

**Family D (direct, on YoY):** $y_{C+k}=\alpha_k+\sum_{i=0}^{p-1}\beta_{k,i}\,y_{C-i}+\varepsilon_{C+k}$, OLS, $p\in\{1,\dots,13\}$
by BIC within each window (the AR baseline of H1).

**Family M (monthly, iterated through the identity):** seasonal AR
$x_t=\mu+\sum_{m=1}^{11}\delta_m D_{m,t}+\sum_{i=1}^{p}\phi_i x_{t-i}+e_t$ with $p\le12$ by BIC, and SARIMA$(p,0,q)(P,0,Q)_{12}$ on
$x_t$ over $p,q\le2$, $P,Q\le1$ by BIC. ETS on $\ln P_t$ (damped additive trend, additive seasonality) as a robustness
benchmark only.

### 6.3 Predictive distributions

| ID | Construction |
|---|---|
| P-G | Gaussian errors (Family M: simulated paths; Family D: $k$-step residual variance) |
| P-T | Location-scale Student-t fitted by maximum likelihood to residuals, $\nu\in[3,100]$ |
| P-QR | Linear quantile regression of $U_{C,k}$ on $k\,\bar x^{(12)}_C$ and $k\,\bar x^{(3)}_C$ (mean monthly change over the last 12 and 3 months); $q_\tau=g(K_{C,k}+\hat U_\tau)$; crossing removed by sorting, number of crossings reported |
| P-BS | Family M with residual bootstrap: (i) i.i.d.; (ii) moving-block, block length 6 (12 as robustness); 2,000 paths per origin |
| P-RC | Empirical quantile recalibration of P-G using PIT values of earlier forecasts whose targets were observed by $C$; active once at least 36 such values exist |
| X-QGB | **Exploratory only**: gradient boosting with quantile loss, fixed settings (200 trees, depth 2, learning rate 0.05, at least 10 samples per leaf, subsample 0.8), P-QR regressors plus calendar month; not tuned; reported regardless |

Not included: quantile random forests, deep learning. GARCH is added **only if** the ARCH-LM test (section 7) rejects at
5%, as AR-GARCH(1,1)-t on $x_t$ with the `arch` package.

## 7. Exploratory analysis (descriptive; chooses nothing for the test set)

Summary statistics and distributions of $y_t$ and $x_t$; plots of $P_t$ and $y_t$; calendar-month means of $x_t$ with an
F-test on seasonal dummies; ACF/PACF of $x_t$ and $y_t$ (the latter persistent by construction); rolling 12- and 36-month
SD; ADF (constant, lag by AIC) and KPSS (level) on $\ln P_t$, $x_t$, $y_t$, interpreted jointly; OLS-CUSUM; Chow tests at
the pre-specified dates 2024-01 and 2025-07; ARCH-LM on monthly residuals; outliers flagged with a robust z-score
(median/MAD, $|z|>4$) and never removed from the main analysis.

## 8. Experimental design (historical, pseudo-out-of-sample)

### 8.1 Rolling-origin evaluation

At each origin: restrict data to $t\le C$; select and fit every model; forecast $h=1,3,6,12$; store quantiles (and CDF
parameters or draws where available) with origin, cutoff, horizon and target date; score after the outcome; advance one
month. The software guarantees that the model receives only the index up to $C$ (tests in `tests/test_backtest.py`).

The initial window is counted in YoY observations: the first cutoff is the month of the $n$-th target observation from
the estimation start.

### 8.2 Window specifications

| Spec | Estimation start (first YoY month) | Initial window | Scheme | First cutoff | Role |
|---|---|---|---|---|---|
| MAIN | 2006-01 | 120 | expanding | 2015-12 | Primary |
| ROLL | 2006-01 | 120 | rolling (120) | 2015-12 | Robustness |
| P2010-96 | 2010-01 | **96** | expanding | 2017-12 | Post-2010 robustness, primary (owner decision 3) |
| P2010-120 | 2010-01 | 120 | expanding | 2019-12 | Post-2010 robustness, secondary sensitivity |
| LAG2 | as MAIN, publication lag 2 | 120 | expanding | 2015-12 (first origin 2016-02) | Release-lag robustness |

Settings still open in section 6 (recalibration warm-up, block length, P-QR regressors) are chosen once on the MAIN
development set and then applied unchanged to every specification.

### 8.3 Development and test sets

- **Development set:** forecasts whose *target* is at or before 2019-12 (MAIN: origins from 2015-12).
- **Test set:** forecasts whose *origin* is 2020-01 or later. Forecasts with origin at or before 2019-12 and target after
  2019-12 belong to neither set.
- P2010-120 has no development set (its first cutoff is 2019-12); it uses the settings fixed on MAIN.

Test-set sizes (number of forecasts; computed by the software, `tests/test_windows.py`):

| Sample | $h=1$ | $h=3$ | $h=6$ | $h=12$ |
|---|---|---|---|---|
| Core (targets to 2025-12) | 71 | 69 | 66 | 60 |
| Extended (targets to 2026-09) | 80 | 78 | 75 | 69 |

Development-set sizes, MAIN: 48, 46, 43, 37; P2010-96: 24, 22, 19, 13. At $h=12$ the core test set contains five
non-overlapping 12-month periods; significance tests at long horizons have little power and are interpreted cautiously.

### 8.4 Subperiods for RQ3 (by target date)

2016-2019, 2020-2021 (COVID), 2022 (commodity price surge), 2023-2025, 2026-01 to 2026-09 (extended sample only).

### 8.5 Publication lag

No real-time vintages exist. MAIN assumes the index for month $C$ is known at origin $C$; this is not true for a public
user (IMF: dissemination "2M+"). LAG2 sets $C=$ origin $-2$, so $k=h+2$.

## 9. Pre-specified dates

Break-test dates 2024-01 and 2025-07 (MEASUREMENT_AND_SERIES_BREAKS.md §3); subperiod boundaries in 8.4.

## 10. Prospective forecasting system (owner decision 4)

Separate from the historical experiments and always labelled **prospective**.

- **When:** after each new NIS CPI publication.
- **Information cutoff:** the latest month whose index had actually been published at the issuance timestamp, according
  to a recorded publication calendar (month → publication date, with its evidence). The software refuses an issuance whose
  data contain a later month than that, or whose cutoff is later than the latest published month.
- **Horizons:** $k\in\{1,3,6,12\}$ months after the cutoff (target $C+k$); the lag between the target and the issuance
  date is recorded.
- **Recorded for every issuance (append-only, never overwritten):** issue timestamp (UTC), latest published month,
  information cutoff, model name and version, model parameters, data SHA-256 and data version, code version, horizons,
  target months, all quantiles, central intervals (50/80/90%), a content hash of the record.
- **Outcomes:** recorded later as separate append-only files (actual value, its publication date, scores). An outcome
  whose publication date is before the issuance is rejected.
- **Storage:** outside the repository (default `%USERPROFILE%\portfolio-data\p11-inflation\prospective\`), local and
  private until gate G3 is resolved. The software refuses a registry path inside the repository.
- Prospective issuance with real data requires gates G1 and G4. If NIS introduces the new CPI, prospective scoring stops
  at the break and is reported separately.

## 11. Evaluation

### 11.1 Point forecasts (median $q_{0.5}$ for all models)

MAE, RMSE, and MASE with fixed scale: $\mathrm{MASE}_h=\mathrm{MAE}_h/\bar d_h$, $\bar d_h$ the mean absolute $h$-step change
of $y$ in the MAIN initial window (2006-01 to 2015-12).

### 11.2 Probabilistic forecasts

- Pinball loss $L_\tau(q,y)=(\mathbb{1}\{y<q\}-\tau)(q-y)$.
- Weighted interval score with $K=3$ central intervals ($\alpha\in\{0.1,0.2,0.5\}$) and the median. With these levels,
  $\mathrm{WIS}=\frac{1}{K+1/2}\sum_{\tau\in\mathcal{T}}L_\tau(q_\tau,y)$ exactly. **Primary metric: WIS.**
- CRPS: closed form for Gaussian; sample (energy) form $\mathbb{E}|X-y|-\tfrac12\mathbb{E}|X-X'|$ for simulated
  distributions; not computed for quantile-only models. $\mathrm{CRPS}=2\int_0^1 L_\tau(F^{-1}(\tau),y)\,d\tau$ is used as a
  software consistency check.
- Coverage and mean width of the 50/80/90% central intervals; PIT histograms (CDF models) or eight-bin quantile
  histograms with expected shares 0.05, 0.05, 0.15, 0.25, 0.25, 0.15, 0.05, 0.05. For $k>1$ these are descriptive only.

### 11.3 Inference

Diebold-Mariano with Newey-West variance (Bartlett, lag $h-1$) and the Harvey-Leybourne-Newbold correction ($t_{n-1}$);
moving-block bootstrap (block $\max(h,6)$, 5,000 resamples, fixed seed) for relative WIS, relative MAE and coverage.
Pre-specified comparisons: each model against B0(b) and against Family D with P-G, per horizon, on WIS and MAE; Holm
adjustment within horizon and metric. Overlapping forecasts are never treated as independent; no claim rests on one
metric or one horizon.

## 12. Reproducibility

Python 3.12, project-local virtual environment (system site packages reused). Seed 20261106; per-forecast generators
seeded by (seed, origin, horizon). All settings in `configs/protocol.toml`. Data file checked against its SHA-256 before
every run. Figures in PNG and PDF from code only.

Methodological references to be verified against publisher records before they enter `paper/references.bib`:
Koenker and Bassett (1978); Diebold and Mariano (1995); Harvey, Leybourne and Newbold (1997); Newey and West (1987);
Künsch (1989); Gneiting and Raftery (2007); Gneiting, Balabdaoui and Raftery (2007); Hyndman and Koehler (2006);
Chernozhukov, Fernández-Val and Galichon (2010); Bracher et al. (2021); Atkeson and Ohanian (2001); Stock and Watson
(2007); Dickey and Fuller (1979); Kwiatkowski et al. (1992).

## 13. Owner decisions (2026-11-06)

1. Title as in section 2; repository `cambodia-inflation-probabilistic-forecasting`; Phnom Penh terminology everywhere.
2. Two samples, core (240) and extended (249), extension subject to gate G2 and NIS permissions; provenance per observation.
3. Post-2010 robustness: 96-month initial window primary, 120 secondary.
4. Separate timestamped prospective system that respects the publication lag; records local and private.
5. Monthly-change identity with the exact log-to-percentage transformation; known-component benchmark retained.

## 14. Deviations log

| Date | Version | Change | Reason |
|---|---|---|---|
| 2026-11-06 | 1.0 (gate status only) | G1 opened; no protocol content changed | Owner-reported permission |
| 2026-11-06 | 0.1 → 1.0 | Title; two samples and gate G2; window table with P2010-96 primary and P2010-120 secondary; prospective system; identity restated with $x_t$, cutoff $C$ and $k=h+\ell$; test-set sizes for both samples | Owner decisions 1-5 |
