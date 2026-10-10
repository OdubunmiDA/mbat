# MBAT codebook

**Covers `data/processed/mbat_panel_state_quarter.csv` (primary), then the long file, crosswalk and policy files.**

## Conventions that apply everywhere

- **Unit:** state (50 states + DC, USPS code) × calendar quarter, 2016Q1–2027Q4.
- **Suppression:** CMS suppresses SDUD counts below 11. Suppressed rows contribute 0 to every sum, so `rx_*`, `units_*`, `amt_*` and `bup_mg_*` are lower bounds. `rx_*_upper` adds 10 per suppressed row.
- **Missing vs zero:** after the last released SDUD quarter, utilization is NA (`data_status = sdud_not_yet_released`). For a released quarter, 0 means CMS reported the state that quarter and no included buprenorphine row had an unsuppressed count.
- **OUD measures exclude pain-labeled buprenorphine.** `oud_total = oud_transmucosal + oud_extended`.
- **Amounts** are nominal US dollars as reimbursed (no inflation adjustment). They are pre-rebate, as SDUD reports them.

## Identifiers and quality flags

| Column | Definition |
|---|---|
| `state`, `year`, `quarter`, `yq` | Panel keys; `yq` like `2022Q2` |
| `data_status` | `sdud_released`; `sdud_released_preliminary` (quarters from the newest annual SDUD file, first release, revised as states resubmit); `sdud_not_yet_released` |
| `sdud_mco_reported` | 1 if CMS published any managed-care (MCOU) SDUD rows for the state-quarter (any drug) |
| `mco_reporting_gap` | 1 if the state reported MCOU rows in any of the prior 4 quarters but none this quarter (totals likely incomplete) |
| `qoq_anomaly_flag` | 1 if `rx_oud_total` changed by more than 50% from a prior quarter above 1,000. Values are left as CMS published them; usually a state submission artifact |

## SDUD utilization (source: CMS SDUD; product groups from `ndc_crosswalk.csv`)

Suffix `_<group>` is one of `oud_transmucosal`, `oud_extended`, `pain`, `oud_total`.

| Column | Definition |
|---|---|
| `rx_<group>` | Number of prescriptions (sum of SDUD `number_of_prescriptions`, FFS + MCO) |
| `rx_<group>_upper` | `rx_<group>` + 10 × `n_suppressed_rows_<group>` |
| `units_<group>` | Units reimbursed. Tablets and films are counted as each; injectables in mL, as CMS reports them; patches as each |
| `amt_total_<group>` | Total amount reimbursed (Medicaid + non-Medicaid), USD |
| `amt_medicaid_<group>` | Medicaid amount reimbursed, USD |
| `bup_mg_oud_transmucosal` | Buprenorphine mg dispensed = units × `bup_mg_per_unit` (crosswalk). Transmucosal only. Not computed for injectables or implants (see LIMITATIONS 5) |
| `n_rows_<group>`, `n_suppressed_rows_<group>` | SDUD NDC-rows and suppressed NDC-rows contributing |
| `share_rows_suppressed_oud` | `n_suppressed_rows_oud_total / n_rows_oud_total` |
| `rx_oud_total_ffs`, `rx_oud_total_mco` | OUD prescriptions by utilization type (fee-for-service, managed care) |

## Enrollment (source: CMS)

| Column | Definition |
|---|---|
| `mbes_medicaid` | Mean monthly total Medicaid enrollees in the quarter, from "Medicaid Enrollment – New Adult Group" (CMS-64/MBES). Available 2016Q1–2025Q2. Latest CMS update per state-month |
| `mbes_viii_group` | Mean monthly VIII (ACA expansion) group enrollees, same source |
| `pi_medicaid` | Mean monthly "Total Medicaid Enrollment", Performance Indicator dataset. Available from mid-2017 to 2026Q2. Updated reports preferred over preliminary |
| `pi_medicaid_chip` | Same, Medicaid + CHIP |
| `*_months` | Months contributing to the quarterly mean (drop quarters with < 3 if you need complete quarters) |
| `pi_expanded_any_month` | CMS PI flag: state reported as having expanded Medicaid in any month of the quarter |

The two series differ: PI/MBES has a median of about 0.91 where both exist (QA §7). Rates are computed against each separately and are not interchangeable.

## Rates

| Column | Definition |
|---|---|
| `rx_oud_per_1k_{mbes,pi}` | `rx_oud_total` per 1,000 enrollees per quarter |
| `rx_oud_transmucosal_per_1k_*`, `rx_oud_extended_per_1k_*` | Same by product group |
| `bup_mg_oud_transmucosal_per_enrollee_*` | Transmucosal buprenorphine mg per enrollee per quarter |

## ARCOS (source: DEA ARCOS Retail Drug Summary, drug code 9064)

| Column | Definition |
|---|---|
| `arcos_bup_grams` | Grams of buprenorphine (base) distributed to retail registrants in the state, Report 2. All payers, all indications. 2016Q1–2023Q4 only |
| `arcos_bup_grams_per_100k` | Grams per 100,000 population as DEA reports it, Report 3 |

## CDC overdose deaths (source: CDC NCHS VSRR, 12-month-ending)

The value at the quarter's last month (Mar/Jun/Sep/Dec), meaning deaths in the 12 months ending that quarter. NY = CDC "NY" (excluding NYC) + "YC" (NYC).

| Column | Definition |
|---|---|
| `od_all_12mo_{reported,predicted}` | All drug overdose deaths |
| `od_opioid_12mo_*` | Opioids (T40.0–T40.4, T40.6). Missing where CDC withholds the count for low drug specificity |
| `od_synthetic_12mo_*` | Synthetic opioids other than methadone (T40.4) |
| `cdc_percent_complete` | CDC's percent-complete indicator for all-drug deaths |

## Policy indicators (source: `policy_annotations.csv`; one citation per event)

"In effect" means the event's start is on or before the quarter's last day and its end (if any) is on or after the quarter's first day.

| Column | Definition |
|---|---|
| `expansion_date` | ACA expansion implementation date (KFF, October 2026). Blank = not adopted |
| `expansion_in_effect`, `expansion_mid_quarter` | Expansion in effect in the quarter; started after the quarter's first day |
| `continuous_enrollment_in_effect` | Federal continuous enrollment condition (2020-03-18 to 2023-03-31) |
| `unwinding_start_month` | First CMS Renewal Outcomes *reporting month* with Medicaid/CHIP terminations at renewal (Metric 5b+5c > 0). This is the month renewals were **due** for the first cohort that lost coverage; coverage typically ended at the end of that month, so the first month without coverage is usually one month later (three months later in Oregon). Checked against the CMS state timeline table of 2023-06-29 for 11 states (see `docs/VERIFICATION_REPORT.md`) |
| `unwinding_in_effect` | Quarter overlaps the state's unwinding start through 2024-05-31 (CMS completion deadline) |
| `unwinding_first_disenrollment_month` | First month in which people were without coverage after an unwinding renewal: `unwinding_start_month` + 1 month (Oregon + 3). **Use this for event timing** |
| `unwinding_disenrollment_basis` | `cms_state_timeline` where the lag was checked against the CMS state timeline table (2023-06-29; 11 states); `assumed_1_month` otherwise |
| `unwinding_disenrollment_in_effect` | Quarter overlaps `unwinding_first_disenrollment_month` through 2024-05-31 |
| `x_waiver_eliminated` | On or after 2022-12-29 |
| `mandatory_moud_benefit` | On or after 2020-10-01 (SUPPORT Act; made permanent by CAA 2024). 0 for Hawaii, South Dakota and Wyoming during their provider-shortage exemption (2020-10-01 to 2025-09-30, per CMS SMD #24-004); blank for those three after 2025-09-30 until re-certification status is confirmed |
| `community_engagement_federal_in_effect` | Expansion state and quarter on or after 2027-01-01 (good-faith exemptions to 2028-12-31 are not yet coded) |
| `community_engagement_state_planned_start` | Planned early start reported by KFF (April 2026); actual start not confirmed |
| `state_work_requirement_waiver_in_effect` | Georgia Pathways (from 2023-07-01) |
| `bup_prior_auth_required`, `bup_daily_dose_cap_mg` | **Empty in v1.0** (see NEXT_STEPS) |

## Long file: `mbat_panel_state_quarter_product.csv`

Keys `state, year, quarter, utilization_type (FFSU/MCOU), product_group`. Columns `rx, units, amt_total, amt_medicaid, bup_mg, n_rows, n_suppressed_rows, n_ndcs, all_rows_suppressed` are defined as above. A row exists for every state-quarter-utilization type CMS reported.

## Crosswalk: `ndc_crosswalk.csv`

| Column | Definition |
|---|---|
| `ndc11` | 11-digit NDC as in SDUD |
| `include` | 1 if RxNorm identifies buprenorphine |
| `product_group`, `ingredient`, `form`, `brand` | Classification from the RxNorm concept name (rules in `code/04_ndc_crosswalk.py`) |
| `bup_mg_per_unit` | Buprenorphine mg per tablet or film (transmucosal only) |
| `rxnorm_concept`, `rxcui`, `rxnorm_ndc_status` | RxNav `ndcstatus` response (RxNorm 05-Oct-2026) |
| `fda_*` | FDA NDC Directory attributes where the NDC is listed |
| `sdud_*`, `median_units_per_rx` | How the NDC appears in SDUD (names, years, rows, units per prescription) |
| `needs_review`, `review_reason` | Rows the author should check first |
| `verification_method`, `verification_note` | How the author checked the row: `DailyMed` (current label), `RxNorm+SDUD` (discontinued product; RxNorm concept and the CMS-recorded product name agree), or `RxNorm only` (CMS name lacks strength) |
| `author_verified` | The author's initials and date; stored in `data/raw/ndc_reference/author_verification.csv` so it survives re-runs |
