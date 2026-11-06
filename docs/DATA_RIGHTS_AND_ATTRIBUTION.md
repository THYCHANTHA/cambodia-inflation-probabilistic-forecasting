# Data rights and attribution

Status: 2026-11-06. This is not legal advice; it records what the published terms say and what remains unknown.
Public accessibility and the existence of an API are **not** treated as an open-data licence.

## 1. Texts that were read

**Data EF Terms of Use** (https://data.mef.gov.kh/terms-of-use, read in full 2026-11-06; no revision date on the page;
footer "Copyright © 2026 Data EF. All rights reserved."). Relevant passages, verbatim:

- §1: "The Data EF website is owned and operated by the General Directorate of Digital Economy (GDDE) of the Ministry of
  Economy and Finance (MEF). In case of necessity, the GDDE reserves the right to update and amend these Terms of Use."
- §2: "All data published on or through the Data EF website ... is protected by the intellectual property laws of the
  Kingdom of Cambodia. Any use of data available on the Data EF website must include an attribution or reference to the
  data's source."
- §3: "The content available on the Data EF website has official sources from various data owner or data custodians under
  ministries and institutions of the Royal Government of Cambodia ... Users can use the content or data for commercial or
  non-commercial purposes, as well as for research and other legal purposes."
- §4: "Unauthorized access, hacking, data mining, or any abnormal activity on the website, or on systems, networks, or
  servers connected to the GDDE's website, is prohibited and punishable by law."
- §6: content "is for informational purposes only and does not constitute any express or implied guarantee".
- §9: governed by the laws of the Kingdom of Cambodia.

Not addressed anywhere in the terms: redistribution or republication of datasets, derived or transformed datasets, API
use, bulk download, and whether the terms of the original data owner (here NIS) take precedence. "Data mining" is not
defined.

**NIS website:** no terms of use, licence, disclaimer or citation policy found. Footer copyright notice "© 2025"
National Institute of Statistics, Ministry of Planning. The Law on Statistics is posted as a Khmer PDF and was not
reviewed (its text layer does not extract reliably; it should be read by a Khmer reader before any public release).

**IMF Copyright and Usage** (read 2026-11-06): users "may download, extract, copy, create derivative works, publish,
distribute, and use Data" with attribution; commercial reuse requires permission (copyright@imf.org); third-party material
requires the third party's permission. Not relevant unless source D is used.

**NBC:** not readable (HTTP 403). Unknown.

## 1a. Owner-reported permission (2026-11-06)

The owner reported that permission was granted to plot with this data ("They are accepted me to plot with this data").
The written permission itself has not been seen by the assistant; the owner should file a copy (sender, date, exact
wording and scope) with the project records. Action taken on that basis: **gate G1 opened** for the core Data EF file
(local ingestion and exploratory figures 1-5). Not assumed from this statement: modelling (gate G4), the 2026 NIS
extension (gate G2), or public release of figures, derived series or forecast records (gate G3). Real-data outputs are
kept in git-ignored `reports/figures/` and `reports/eda_summary.txt` until the scope of the permission is documented.

## 2. Activity-by-activity position

| Activity | Position | Basis |
|---|---|---|
| Accessing the data (portal, CSV, JSON API) | **Permitted** | Public pages; Terms §3. One request per file, no crawling |
| Using the data for academic research | **Permitted, with attribution** | Terms §3 names "research" explicitly; §2 attribution |
| Storing the data locally | **Permitted in practice (implied by use; not stated)** | Necessary for research use; store outside Git, on C: (`%USERPROFILE%\portfolio-data\p11-inflation\`), with checksums |
| Publishing results: model metrics, forecast-evaluation tables, a small number of quoted values, figures | **Probably permitted as "use" with attribution; not confirmed** | §3 allows use for research; no condition forbids publishing analysis. Figures of the full series reveal the series visually, which is what NIS publishes in its own reports. Owner decision before public release |
| Publishing transformed data (full monthly YoY or log-inflation series, forecast quantile files covering the sample) | **Unknown: treat as redistribution, do not publish** | A full YoY series together with one index value recovers the original index; terms silent on derived datasets |
| Redistributing the original dataset (CSV in the repo, release asset, Kaggle, etc.) | **Unknown: not done** | Terms silent; producer (NIS) terms unknown |
| Providing automatic download functionality in a public repo | **Unknown: not provided by default** | §4 prohibits undefined "data mining". A single, user-initiated request to the documented download endpoint is unlikely to be that, but this is not confirmed. Portfolio precedent (Project 08 public methods release): no MEF downloader. Default here: manual-download instructions plus a local loader that reads a user-supplied file |
| Commercial use | Permitted by Data EF §3; not planned | - |

## 3. Practical rules for this repository

1. No raw or full derived CPI series is committed (to be enforced by a hygiene test that fails on CSV/XLS/XLSX/Parquet
   files and on long numeric monthly tables under version control).
2. The repository may contain: code, synthetic test data, documentation, and (only after the owner's decision) result
   tables and figures.
3. The data file is supplied by the user (downloaded manually from the Data EF dataset page) and its SHA-256 is checked
   against the manifest. The project never downloads data on import or in tests.
4. Every figure and table that uses the data carries the attribution line below.
5. Until written confirmation is received, the repository stays **local or private**.

## 4. Attribution wording

> Data: National Institute of Statistics (NIS), Ministry of Planning, Cambodia, *Consumer Price Index, Phnom Penh
> (October-December 2006 = 100)*, accessed via Data EF (data.mef.gov.kh), dataset "Cambodia's Inflation Rate 2005-2025"
> (pd_66a9f36b36d76b00019fe83b), managed by the National Bank of Cambodia, retrieved 2026-11-06. 2026 values: NIS monthly
> CPI tables (nis.gov.kh). Inflation rates recomputed by the author from the index.

The attribution names NIS as producer because the values and base match NIS releases exactly (DATA_SOURCE_AUDIT.md §2).
The portal itself does not name NIS. If MEF or NBC state otherwise, this wording changes.

## 5. Written confirmation to request (owner to send; not sent)

The Project 08 request (`cambodia-rice-market-intelligence/docs/MEF_PERMISSION_REQUEST.md`) can be reused. For this
project ask Data EF/GDDE (with NBC as dataset manager) and NIS, separately for each activity in the table above:

1. Is NIS the original producer of `pd_66a9f36b36d76b00019fe83b`, and does the series cover Phnom Penh only?
2. May a derived monthly series (YoY inflation recomputed from the index) be published in a public GitHub repository?
3. May the original CSV be redistributed with attribution?
4. Is a script that downloads the CSV once, on the user's request, from the documented endpoint acceptable under §4?
5. Is there a revision policy or vintage archive for the series?
6. When will the updated CPI (SES 2019 weights, provincial coverage) be published, and will a linked back series be provided?

Until replies arrive, the rules in section 3 apply.
