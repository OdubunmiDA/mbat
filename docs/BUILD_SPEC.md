# MBAT build spec

**This spec governed v1.0 (released 2026-10-09; originally targeted for March 2027). Update it before the code whenever scope changes.**

```
PROJECT:        Medicaid Buprenorphine Access Tracker (MBAT). Archetype: open dataset,
                with a data-descriptor paper planned as a second output.

QUESTION:       How much buprenorphine does Medicaid pay for in each state and quarter,
                relative to enrollment, alongside retail buprenorphine supply, overdose
                deaths, and the dated Medicaid policy changes that shape access?

SOURCES:        (vintages pinned in data/raw/MANIFEST.csv with SHA-256)
  1. CMS State Drug Utilization Data (SDUD), annual files 2016–2026
     https://download.medicaid.gov/data/  (2020–2025 are July 2026 re-releases; 2026 has Q1 only)
     Public domain (U.S. Government work). Retrieved 2026-10-08.
  2. CMS Medicaid & CHIP enrollment: Performance Indicator dataset, Sept 2026 release;
     Medicaid Enrollment – New Adult Group (Feb 2026 release). Public domain. Retrieved 2026-10-08.
  3. DEA ARCOS Retail Drug Summary, annual reports 2016–2025 (PDF).
     https://www.deadiversion.usdoj.gov/arcos/retail_drug_summary/  Public domain. Retrieved 2026-10-08.
  4. CDC NCHS VSRR Provisional Drug Overdose Death Counts (xkb8-kh2a), Sept 16 2026 update.
     https://data.cdc.gov/api/v3/views/xkb8-kh2a/export.csv  Public domain. Retrieved 2026-10-08.
  5. NLM RxNorm (RxNav API ndcstatus/ndcproperties) and the FDA NDC Directory, used only
     to classify NDCs in the crosswalk. Responses are cached in data/raw/ndc_reference/.
  6. Policy annotations: hand-compiled table with one primary citation per row
     (CMS, state Medicaid agencies, Federal Register, statute, KFF trackers).

UNIT:           State (50 states + DC) × calendar quarter, 2016Q1–2027Q4 (51 × 48 = 2,448 rows).
                Utilization measures are filled through the last SDUD quarter released
                (currently 2026Q1); later quarters carry policy annotations only and an
                explicit data_status flag, never zeros.

MEASURES:       (full definitions in docs/CODEBOOK.md)
  SDUD, by state-quarter, summed over FFS and managed-care rows, also kept separately:
    prescriptions, units reimbursed, total and Medicaid amount reimbursed
    split by product group:
      oud_transmucosal  sublingual/buccal buprenorphine and buprenorphine-naloxone
      oud_extended      extended-release injection (Sublocade, Brixadi) and implant (Probuphine)
      pain              buprenorphine products labeled for pain (Butrans, Belbuca, Buprenex)
    oud_total = oud_transmucosal + oud_extended; pain products are reported separately
    and excluded from every OUD measure.
    buprenorphine mg dispensed (transmucosal only) = units × mg per unit from the crosswalk.
    suppressed row count and share of NDC-rows suppressed (CMS suppresses counts < 11).
  Enrollment: mean monthly total Medicaid enrollment in the quarter; expansion-group enrollment.
  Rates: OUD prescriptions and transmucosal mg per 1,000 enrollees.
  ARCOS: buprenorphine grams distributed to retail registrants by state-quarter, and grams
    per 100,000 population as DEA reports them.
  CDC: 12-month-ending overdose deaths (all drugs; opioids T40.0–T40.4, T40.6; synthetic
    opioids T40.4) at the last month of each quarter, reported and predicted values.
    These are context variables, not buprenorphine-specific outcomes.
  Policy: Medicaid expansion effective date and expansion status by quarter; continuous-
    enrollment unwinding window; community-engagement (work requirement) start;
    buprenorphine prior-authorization and dose-cap rules where a dated source exists.

OUTPUTS:
  data/processed/mbat_panel_state_quarter.csv     the panel (primary release file)
  data/processed/mbat_panel_state_quarter_product.csv   long file by product group
  data/processed/ndc_crosswalk.csv                every buprenorphine NDC seen in SDUD, classified
  data/processed/policy_annotations.csv           dated policy events with citations
  data/processed/qa_report.txt                    row counts, reconciliations, spot checks
  paper/stats.json, paper/figures/*.png           numbers and figures for any document
  docs/ README, CODEBOOK, LIMITATIONS, VERIFY_CHECKLIST, PUBLISH_GUIDE, NEXT_STEPS

VENUES:         1. Zenodo v1.0 (October 2026), DOI;  2. Zenodo v1.1 (March 2027) and v1.2 (July 2027, adds 2026Q2–Q4
                SDUD and any corrected vintages);  3. GitHub repository linked to Zenodo;
                4. data-descriptor paper (target to be chosen by the author).

VERIFY POINTS:  (the author rules on each before release)
  V1. Every NDC classification in ndc_crosswalk.csv, especially rows flagged needs_review.
  V2. Treatment of pain-labeled products (excluded from OUD measures).
  V3. mg-per-unit for each transmucosal NDC and the decision to omit mg for injectables.
  V4. State totals for ≥5 state-quarters reconciled by hand against the raw SDUD file.
  V5. ARCOS values extracted from the PDFs, checked against the PDF page for ≥5 state-quarters.
  V6. Each policy date against its cited source.
  V7. Enrollment denominator choice (total Medicaid vs Medicaid+CHIP).

LICENSE:        Code MIT; data and documentation CC BY 4.0, with attribution to CMS, DEA,
                CDC/NCHS, and NLM as the underlying public sources.

AUTHOR:         Oluwapelumi Odubunmi (sole author), ORCID 0009-0004-8843-5339,
                odubunmipelumi@gmail.com, Department of Pharmaceutical Outcomes and Policy,
                College of Pharmacy, University of Florida.

ASSUMPTIONS:    State code "XX" (the national total row in SDUD) is excluded so national
                sums are built from states. Puerto Rico and territories are excluded from v1.0.
                SDUD rows are summed as published; CMS revisions after the pinned vintage
                are picked up only in a new release.
```
