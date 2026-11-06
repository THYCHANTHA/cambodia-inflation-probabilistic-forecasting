# Data source audit

**Project:** Forecasting Inflation Uncertainty in Cambodia (Project 11)
**Audit date:** 2026-11-06 (Stage 1). **Auditor:** research assistant working for the owner; every statement below was
checked against the cited page or file on this date unless it is marked *not verified*.
**Overall decision: CONDITIONAL.** Research use of the Phnom Penh CPI is permitted and the series is verified; publication
of the data (raw or as a full transformed series) is not established. See [DATA_RIGHTS_AND_ATTRIBUTION.md](DATA_RIGHTS_AND_ATTRIBUTION.md).

## 0. Summary of findings

1. **The "Cambodia's Inflation Rate 2005-2025" dataset on Data EF is the NIS Phnom Penh CPI, not a national CPI.** The
   portal title and description do not say so. Evidence: identical base (October-December 2006 = 100; the Q4-2006 mean
   of the portal index is exactly 100.00) and identical values to official NIS releases in all 7 months checked (table in
   section 2). NIS releases are titled "Consumer Price Index, Phnom Penh"; the IMF (Country Report 26/62) states that
   "for the existing CPI, the price information is taken from the capital city of Phnom Penh only".
2. **No new CPI has been published.** The IMF reported a planned update (279 items, SES 2019 weights, provincial weights)
   to be completed by December 2025. Every NIS file checked up to the latest (September 2026) is still "Phnom Penh
   (October - December 2006 = 100)" with the old group weights (food 44.775%). The NIS "Sub-national CPI" page has no
   files. There is therefore no new-versus-old series break in the data available today; one is expected in future.
3. **The portal series is internally consistent.** 252 consecutive months (Jan 2005 to Dec 2025), no gaps, no duplicates,
   no blank cells; the portal's MoM, YoY and 12-month moving average recompute from the index to within 0.06 pp / 0.06
   index points in every month.
4. **Date-format defect.** The CSV writes dates as `M/D/YYYY` with D always 1 (`2/1/2005` = February 2005), while the
   portal metadata declares `DD/MM/YYYY`. The JSON API parses them the wrong way (`2005-01-02` for February 2005). Any
   ingestion code must parse explicitly and validate month order; it must not trust the metadata format string.
5. **Usable target length.** YoY inflation can be recomputed from the index only from January 2006 (the 2005 YoY values on
   the portal use 2004 index values that are not in the dataset). Recomputed target: 240 months (2006-01 to 2025-12),
   extendable to 249 months (to 2026-09) from NIS Excel files of the same index.
6. **Licence.** Data EF Terms of Use allow use "for commercial or non-commercial purposes, as well as for research", with
   attribution. They do not mention redistribution, derived datasets or API use, and they prohibit undefined "data mining".
   NIS (the apparent producer) publishes no reuse terms on its website. NBC pages could not be read (HTTP 403 to automated
   access). IMF data terms allow redistribution with attribution but the IMF data API refused unauthenticated requests.

## 1. Audit table

| Field | A. MEF Data EF | B. NIS CPI releases | C. National Bank of Cambodia | D. IMF CPI dataset |
|---|---|---|---|---|
| Dataset name | "Cambodia's Inflation Rate 2005-2025" (`pd_66a9f36b36d76b00019fe83b`) | "Consumer Price Index, Phnom Penh (October - December 2006 = 100)", monthly report (PDF) and "Table 2" (Excel) | Monetary and financial statistics (page not readable) | IMF Consumer Price Index (CPI) dataflow `IMF.STA:CPI` |
| Original producer | **Not stated on the portal.** Inferred: NIS, Ministry of Planning (identical values and base; section 2) | NIS, Ministry of Planning | NBC (for its own series; CPI itself is compiled by NIS) | Data reported by national authorities; IMF curates |
| Portal | Data EF, owned and operated by the General Directorate of Digital Economy (GDDE), MEF (Terms of Use §1) | nis.gov.kh | nbc.gov.kh | data.imf.org / api.imf.org |
| Manager | National Bank of Cambodia (dataset `organization` field); reference link `www.nbc.gov.kh` | NIS | NBC | IMF Statistics Department |
| URL | https://data.mef.gov.kh/datasets/pd_66a9f36b36d76b00019fe83b ; CSV `.../api/v1/public-datasets/<id>/file` ; JSON `.../json?page=&page_size=` (max 200) | https://nis.gov.kh/en/national-cpi/ | https://www.nbc.gov.kh/english/economic_research/monetary_and_financial_statistics_data.php | https://data.imf.org/Datasets/CPI |
| Coverage | 2005-01 to 2025-12 (metadata `coverage_start/end`; confirmed in the file) | Listing on the page: 110 CPI files; monthly English PDF reports from Jan 2017; Excel "Table 2" files from Nov 2025 to Sep 2026; PDF reports for 2025-2026 incomplete (several months only as Excel) | Not verified | Not verified (data request returned HTTP 403) |
| Frequency | Monthly | Monthly | Not verified | Dataflow has a `FREQUENCY` dimension; Cambodia frequency not verified |
| Geography | **Phnom Penh** (inferred; the portal says "Cambodia") | Phnom Penh (stated in every release checked) | Not verified | Not verified. Third-party aggregators label the same values "national" (e.g. 212.33 for Jan 2026, which is the NIS Phnom Penh value), so labels in secondary sources are not reliable |
| CPI base | October-December 2006 = 100 (Q4-2006 mean of the file = 100.00) | October-December 2006 = 100 (stated) | Not verified | Not verified |
| Weight reference | Not stated on the portal | Group weights printed in each release (food 44.775, housing 17.084, transport 12.228, ...). Reference survey: **SES 2004** per IMF CR 26/62 ("The current weights were taken from the Cambodia Socio-Economic Survey (SES) 2004"); NIS releases checked do not name the survey | Not verified | Not verified |
| Revision policy | None published. `updated_at` 2026-09-24; column metadata updated 2026-03-18; 2 decimals | None published; IMF CR 26/62 recommends to "Develop and publish a predetermined and stable revisions policy" (revisions element rated "Largely Not Observed") | Not verified | IMF does not revise national CPI independently (not verified for this series) |
| Availability | CSV (12,893 bytes), JSON API, portal dashboard | PDF (1-decimal index), Excel `.xlsx`/`.xls` (3-decimal index, 12 COICOP groups) | HTML page; access from this machine refused (HTTP 403) | Web portal; SDMX structure endpoint public; data endpoint refused (HTTP 403) |
| Licence | Data EF Terms of Use (§2-§4, quoted in DATA_RIGHTS_AND_ATTRIBUTION.md); no named licence on the dataset page | **None found.** Footer "© 2025" NIS / Ministry of Planning; no terms, disclaimer or reuse page (`/terms-of-use/`, `/disclaimer/`, `/copyright/` return 404); Law on Statistics available only as a Khmer PDF, not reviewed | Not verified | IMF Copyright and Usage: download, copy, derivative works, publish and distribute Data with attribution; commercial reuse needs permission; third-party material needs the holder's permission |
| Attribution | Required (§2: "must include an attribution or reference to the data's source") | No stated wording; cite NIS as producer | Not verified | "Source: International Monetary Fund, Database Name, <link>"; material transformation must be stated |
| Redistribution | **Not addressed** (unknown) | **Unknown** | Unknown | Permitted for IMF Data with attribution; national-source data may fall under the third-party clause (not resolved) |
| Audit decision | **CONDITIONAL** (primary source for 2005-2025; research use permitted; no redistribution) | **CONDITIONAL** (verification source and 2026 extension; terms unknown; no redistribution) | **BLOCKED** (unreadable; optional explanatory variables deferred) | **DEFERRED / not verified** (not needed for the primary target; optional cross-check only) |

## 2. Verification of source A against NIS releases

The portal index (2 decimals) was compared with NIS official releases (PDF 1 decimal, Excel 3 decimals). All differences
are rounding only.

| Month | Data EF | NIS value | NIS file | Agreement |
|---|---|---|---|---|
| 2017-01 | 168.52 (MoM 0.29, YoY 4.42) | 168.5 (MoM 0.3, YoY 4.4) | `CPI_Report_Jan_2017_E.pdf` | rounding |
| 2024-01 | 197.82 (MoM -2.48, YoY -0.48) | 197.8 (MoM -2.5, YoY -0.5) | `CPI_Report_Jan_2024_Eng.pdf` | rounding |
| 2025-01 | 209.70 (YoY 6.00) | 209.7 (YoY 6.0); 209.695 | `1.-CPI_Report-Jan-2025_Eng.pdf`; `CPI-12-group-Jan-2026.xlsx` | rounding |
| 2025-02 | 208.54 | 208.5 | `CPI_Report_Feb-2026-1.pdf` (previous-year column) | rounding |
| 2025-03 | 207.42 | 207.4 | `CPI_report_March-2026.pdf` (previous-year column) | rounding |
| 2025-09 | 210.26 | 210.26 | `CPI-12-group-Sep-2026.xls` | exact |
| 2025-12 | 211.53 | 211.527 | `CPI-12-group-Jan-2026.xlsx` | rounding |

Conclusion: source A reproduces the NIS Phnom Penh CPI for every checked month, including the large January 2024 fall
(-2.5% MoM in NIS's own release, so it is not a portal error). The portal did not appear to revise history relative to
the 2017 release; this is a 7-month spot check, not a full revision study.

NIS values after the portal's end date (same base and weights): 2026-01 212.330, 2026-02 213.9, 2026-03 219.0,
2026-08 219.007, 2026-09 221.436 (YoY 5.3%). Only months actually opened are listed; 2026-04 to 2026-07 were not read.

## 3. Internal consistency checks on source A (executed 2026-11-06)

Script: a one-off check in the session scratchpad (to be re-implemented as tested code in `src/` in Stage 3).

| Check | Result |
|---|---|
| Rows | 252 |
| Date field | `M/1/YYYY` in all rows (second field always 1) |
| Monthly sequence complete and ordered, 2005-01 to 2025-12 | yes; 0 duplicates |
| Blank cells | 0 |
| Portal MoM vs 100*(CPI_t/CPI_{t-1} - 1), tolerance 0.06 pp | 0 mismatches |
| Portal YoY vs 100*(CPI_t/CPI_{t-12} - 1), from 2006-01 | 0 mismatches |
| Portal 12-month MA vs recomputed | 0 mismatches |
| Portal `YoY_3_Month_Avg` / `YoY_12_Month_Avg` (checked 2026-11-06 at ingestion) | **Metadata description is wrong.** The metadata calls them moving averages of the YoY rate; the values are the YoY change of the 3- / 12-month average index, 100 (MA_k(P)_t / MA_k(P)_{t-12} - 1): max abs diff 0.014 / 0.008 under that definition, versus 0.21 / 1.15 (2008-09) under the metadata's. Not used for research |
| Largest absolute MoM | +8.27% (2008-03), +4.43% (2008-04), -3.93% (2008-12), +3.39% (2007-06), -3.38% (2008-11), +2.90% (2008-05), +2.65% (2008-01), **-2.48% (2024-01)** |
| MoM exactly 0 / within ±0.05 pp | 2 / 19 months |
| Months with negative YoY | 2009-03 to 2009-10, 2024-01, 2024-02 |
| YoY (portal values, 2005-2025): min / max / mean / SD | -5.68 / 35.57 / 4.40 / 5.48 |
| YoY 2010-01 to 2025-12: mean / SD | 2.97 / 1.68 |

## 4. Files inspected (audit only; nothing stored in the project or committed)

Downloaded on 2026-11-06 to the session scratchpad (temporary, outside the repository) for inspection only:

| File | Size | SHA-256 |
|---|---|---|
| Data EF CSV (`/api/v1/public-datasets/pd_66a9f36b36d76b00019fe83b/file`, served as `pd_69d880bf0e0691000778ba2e.csv`) | 12,893 B | `6ae48968661f96d30486a3883481121034cec967f18f2deeb59deb06ea7f2cf6` |
| Data EF Terms of Use page (HTML) | 83,538 B | `cde7189defb4966ec6668b37ae8e73dced81a6b254ab3655348c3216b104fd07` (page includes dynamic content; hash is informative only) |
| NIS: 5 PDF reports (Jan 2017, Jan 2024, Jan 2025, Feb 2026, Mar 2026) and 3 Excel files (Dec 2025, Jan 2026, Sep 2026) | 0.02-0.44 MB each | not recorded (inspection only) |
| IMF Country Report No. 26/62 (PDF) | 946,242 B | not recorded |

A properly logged acquisition (with manifest and checksums, stored outside Git) is a Stage 4 task.

## 5. Observations on the NIS releases

- PDF text layers are partly unreadable: Khmer text and some table cells extract as empty characters, and column order is
  scrambled. Excel files are the reliable machine-readable source for 2025-2026. PDFs give 1-decimal indices only.
- The September 2026 Excel file labels its "September 2026" column with the Excel date serial for **August 2026** (46235);
  the Khmer text header says September. Parsers must not rely on that cell.
- Historical files are all under `wp-content/uploads/2026/06/` (re-uploaded in June 2026). The IMF noted that "as of
  September 2025, the most recent CPI release on the website (in English) was for the reference period April 2024". The
  publication record is therefore irregular; the release date of a given month cannot be reconstructed from the site.
- Release timeliness: IMF CR 26/62, Table 1 lists Cambodia's CPI dissemination timeliness as "2M+" (SDDS: 1M).

## 6. Source C (NBC) and D (IMF): what was attempted

- **NBC:** `monetary_and_financial_statistics_data.php` returned HTTP 403 to `curl` and to the fetch tool. A retry with a
  browser User-Agent was not performed (it would circumvent the site's bot check). Web search shows NBC publishes the
  monthly *Economic and Monetary Statistics* bulletin (PDF) and that secondary sources (CEIC, Trading Economics) carry an
  NBC core CPI "Oct-Dec 2006=100"; none of this was verified at the source. **Owner action:** open the page in a browser,
  list available tables and any terms, or write to the NBC statistics department.
- **IMF:** the SDMX structure for `IMF.STA:CPI` is public (dimensions COUNTRY, INDEX_TYPE, COICOP_1999,
  TYPE_OF_TRANSFORMATION, FREQUENCY). The data request for Cambodia returned HTTP 403 without credentials; no workaround
  was attempted. Even if obtained, the IMF series would be a re-publication of the same NIS Phnom Penh CPI unless shown
  otherwise, so it is not an independent measurement, only an independent transmission check.

## 7. Decision and conditions

| Source | Decision | Conditions |
|---|---|---|
| A. Data EF | CONDITIONAL | Use locally for research; attribute; label as **Phnom Penh CPI**; parse dates explicitly; recompute inflation from the index; do not commit or publish the raw file or a full derived monthly series until rights are confirmed in writing |
| B. NIS | CONDITIONAL | Use as verification source and for the 2026 extension (same index, same base, same weights, overlap agrees to rounding); same publication restrictions |
| C. NBC | BLOCKED | Not used. Optional covariates (exchange rate, core CPI, interest rates) deferred until page, coverage, release timing and terms are read |
| D. IMF | DEFERRED | Not used. Optional transmission cross-check only |
