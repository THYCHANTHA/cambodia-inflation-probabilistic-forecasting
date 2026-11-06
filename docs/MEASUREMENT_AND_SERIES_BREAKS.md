# Measurement and series breaks

Status: 2026-11-06 (updated for protocol v1.0). Sources: NIS monthly releases (files listed in DATA_SOURCE_AUDIT.md), IMF Country Report No. 26/62
*Cambodia: Report on the Observance of Standards and Codes - Data Module* (March 2026; "based on the information available
at the time it was completed in September 2025"), and checks on the Data EF file. Statements attributed to the IMF are
quoted or closely paraphrased from that report; nothing here is inferred from the names of variables.

## 1. The index actually measured

| Property | Value | Evidence |
|---|---|---|
| Geography | **Phnom Penh only** | Every NIS release title; IMF CR 26/62 (authorities' response, para. 12) |
| Price reference period | October-December 2006 = 100 | NIS release titles; Q4-2006 mean of the Data EF index = 100.00 |
| Expenditure weights | SES 2004 | IMF CR 26/62 ("The current weights were taken from the Cambodia Socio-Economic Survey (SES) 2004") |
| Basket | 258 items | IMF CR 26/62, para. 13 ("279 items, up from 258 items") |
| Classification | 12 COICOP main groups (food 44.775%, housing/utilities 17.084%, transport 12.228%, restaurants 5.861%, health 5.141%, ...) | NIS Excel Table 2 (Jan 2026, Sep 2026 identical weights) |
| Index formula | Not documented in the files read. IMF recommends the short-term price relative approach "rather than the long-term price relative", which implies long-term relatives are used now | IMF CR 26/62 |
| Missing prices | Carry-forward imputation for temporarily missing non-seasonal items, which the IMF says "introduces a bias into the CPI" | IMF CR 26/62 |
| Known component anomalies | IMF cites "persistent downward movement of index for clothing and footwear, persistent flat index for communications". The communication group index is about 66.7 in 2025-2026 (NIS Excel) | IMF CR 26/62; NIS Excel |
| Scope gaps | Services such as telecommunications, insurance, air travel, accommodation and digital products missing or sparsely covered | IMF CR 26/62 |
| Overall IMF assessment | Accuracy and reliability "Largely Not Observed"; revisions analysis "Largely Not Observed" | IMF CR 26/62, Table 12 |

**Consequence for the research:** the target is *Phnom Penh consumer price inflation measured with 2004 expenditure
weights*. It must not be called national inflation. Carry-forward imputation smooths month-on-month changes and can
create artificial persistence; this is a property of the measurement, not of the price process, and the paper must say so.

## 2. Planned versus implemented changes

| Planned (IMF CR 26/62, information to September 2025) | Implemented? (evidence as of 2026-11-06) |
|---|---|
| Electronic (tablet) price collection | **Yes, July 2025** per the authorities ("This goal was achieved in July 2025") |
| New basket, 279 items | **Not visible in any published file.** Sep 2026 release still uses the 2006 base and the same 12 group weights |
| New weights from SES 2019 | Same: not implemented in published data |
| Provincial price collection and regional weights for a national CPI | Not implemented in published data. NIS "Sub-national CPI" page exists but contains no files |
| "The NIS plans to complete the update of the CPI by December 2025" | Not observed in publications through September 2026 |
| Replacement of the SQL compilation system | Unknown |

The authorities' own wording is "plans to complete", so the planned changes are not treated as completed.

## 3. Candidate breaks in the observed series

| Date | Type | What is observed | Treatment |
|---|---|---|---|
| 2007-06 to 2009-10 | Economic regime (food and fuel price shock and reversal) | MoM up to +8.27% (2008-03); YoY peaks at 35.57%; negative YoY 2009-03 to 2009-10 | Kept. Dominates variance estimates; motivates robustness runs that start the estimation sample in 2010 and a rolling window |
| 2024-01 | Unusual single-month fall | MoM -2.48% (NIS: -2.5%), with decreases in almost every group at once (meat, fish, vegetables, fruit, clothing, housing/fuels, transport, recreation, restaurants). NIS gives no methodological note | Kept as published. Cause unknown: neither a measurement event nor a genuine price move can be confirmed. Robustness: intervention dummy / exclusion of this origin from evaluation summaries |
| 2025-07 | **Collection-mode change** (paper to tablets) | Not yet tested | Pre-specified date for a break test in the mean and variance of MoM changes; only 6 months after the change are in the portal file (+9 from NIS), so power is very low |
| 2026-03, 2026-09 | Large transport-group moves | Transport +15.3% (Mar 2026) and +8.0% (Sep 2026) MoM; headline YoY 5.6% (Mar), 5.3% (Sep) | Outside the portal file; inside the 2026 extension. Treated as data, flagged in results |
| Future (date unknown) | **Methodological break**: new basket, weights, geography and probably a new base period | Not yet published | Do not splice. If NIS publishes an overlap period, a linked series may be considered with the linking coefficient and its effect documented; otherwise the new series is a separate target |

## 4. Back-casting and linking

- No back-cast series and no linked old/new series have been published.
- The Data EF series and the NIS 2026 Excel files are **the same index** (same base, weights, geography; overlap month
  2025-12 equals to rounding: 211.53 vs 211.527). Appending 2026 values is an extension, not a link. Precision differs
  (2 vs 3 decimals); the effect on YoY is below 0.005 pp and will be quantified in code.
- The portal's 2005 YoY values rely on 2004 index values that are not in the file and were not verified; the recomputed
  target therefore starts in 2006-01.
- No real-time vintages exist. Spot checks (DATA_SOURCE_AUDIT.md §2) found no revisions between NIS releases and the
  portal, but there is no revision policy, so absence of revisions cannot be established.

### 4.1 Research samples (owner decision, 2026-11-06; protocol v1.0 §4)

| Sample | YoY months | Composition | Status |
|---|---|---|---|
| Core | 2006-01 to 2025-12 (240) | Data EF series only (old CPI system throughout) | Defined; ingestion waits for gate G1 |
| Extended | 2006-01 to 2026-09 (249) | Core + NIS tables for 2026-01 to 2026-09, same index | Included only if all nine months pass gate G2 |

Gate G2 (per month): NIS table parsed without the Excel date serial; title says Phnom Penh; base "October - December
2006 = 100"; the 12 group weights equal the core-period weights; no provincial component; every overlap month agrees with
the core value within 0.006 index points; source file and SHA-256 recorded. Status 2026-11-06: **not run**. During the
audit 2026-01, -02, -03, -08 and -09 were opened and showed the old base and weights; 2026-04 to 2026-07 were not opened.
The checks are implemented in `src/cambodia_inflation/data/provenance.py` and tested on synthetic tables only.

If NIS publishes the new CPI, its months are never appended to either sample (section 3, last row).

## 5. Timing of information

IMF CR 26/62 Table 1 gives Cambodia's CPI dissemination timeliness as "2M+" (more than two months after the reference
month; SDDS requires 1M), and notes key users (MEF, NBC) receive data earlier than the public. A forecast "made at month
t using CPI up to t" is therefore not a real-time forecast for a public user. The protocol includes a release-lag variant
(information set ends at t-2).

## 6. Open measurement questions (for NIS/NBC)

1. Index formula and elementary aggregation; whether the weights are price-updated.
2. Whether the January 2024 fall reflects a methodological event (outlet sample, item replacement, imputation).
3. Whether the July 2025 tablet introduction changed the outlet sample or the collection dates.
4. Planned date and form of the new CPI, and whether a linked back series will be published.
