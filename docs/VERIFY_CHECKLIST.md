# MBAT verification checklist (Pelumi completes before v1.0)

**Initial and date each line. `tools/publish_gate.py` checks the mechanical items; these are the author's. Re-run for each release.**

## Reproduce
- [x] (OO 2026-10-09; signed VERIFICATION_REPORT.md) Fresh `python code/01_fetch.py` on a clean folder; every hash matches `data/raw/MANIFEST.csv` (or the drift is explained and the manifest updated)
  - Claude 2026-10-09: all 27 files re-hashed against MANIFEST, all OK (report §1). Re-download not possible from the device (no network); hashes equal the original download. Initial to accept.
- [x] (OO 2026-10-09; signed VERIFICATION_REPORT.md) `bash run_all.sh` end to end; `qa_report.txt` shows `reconciliation_all_match: True`
  - Claude 2026-10-09: steps 02–13 re-run from scratch; all 11 processed files and 33 interim files byte-identical; `reconciliation_all_match: True` (report §1). Initial to accept.
- [x] (OO 2026-10-09; signed VERIFICATION_REPORT.md) Every number in any document re-read from `paper/stats.json` / `docs/SUMMARY.md` after the re-run
  - Claude 2026-10-09: every number in README, LIMITATIONS, CODEBOOK, NEXT_STEPS traced to stats.json/qa_report/SUMMARY or is a fixed fact (report §1). Recheck after you rewrite README/LIMITATIONS.

## V1 – NDC crosswalk (`data/processed/ndc_crosswalk.csv`)
- [x] (OO 2026-10-09; see DECISIONS.md) Every `needs_review = 1` row checked (all are NDCs missing from the current FDA files; confirm against DailyMed or the package label) and `author_verified` filled in
- [x] (OO 2026-10-09; signed VERIFICATION_REPORT.md) At least 20 other included rows spot-checked against DailyMed, covering each form
  - Claude 2026-10-09: 20-NDC sample (seed 20261009) across 6 forms; 18 match DailyMed, 2 discontinued films match RxNorm + FDA excluded list. Implant and Bunavail were covered in the flagged-row review (report §2). Initial to accept.
- [x] (OO 2026-10-09; see DECISIONS.md) Every rejected candidate (`include = 0`) confirmed as not buprenorphine
- [x] (OO 2026-10-09; see DECISIONS.md) Coverage audit (QA §3) reviewed: no buprenorphine NDCs missed

## V2 – Pain products
- [x] (OO 2026-10-09; see DECISIONS.md) Agree that Butrans, Belbuca and Buprenex (and generics) are excluded from OUD measures, or change the rule in `04_ndc_crosswalk.py`

## V3 – Milligrams
- [x] (OO 2026-10-09; see DECISIONS.md) `bup_mg_per_unit` spot-checked for 10 transmucosal NDCs, including Zubsolv and Bunavail (non-standard strengths)
- [x] (OO 2026-10-09; see DECISIONS.md) Agree that no mg is computed for injectables or implants

## V4 – State totals against CMS (minimum 15 state-quarters)
- [x] (OO 2026-10-09; signed VERIFICATION_REPORT.md) The 12 state-quarters in QA §4 re-checked by hand in the raw SDUD file (filter state, quarter, crosswalk NDCs; sum `Number of Prescriptions`)
  - Claude 2026-10-09: all 12 re-summed from raw files and independently queried in the CMS online datastore (5 cells); all match (report §3). Initial to accept.
- [x] (OO 2026-10-09; signed VERIFICATION_REPORT.md) 3 more of your own choosing, including one Nevada quarter you know well
  - Claude 2026-10-09: 6 added (NV 2019Q2, NV 2024Q4, OR 2022Q3, KY 2023Q2, ME 2024Q2, CA 2023Q4); all match (report §3). Initial to accept.
- [x] (OO 2026-10-09; signed VERIFICATION_REPORT.md) Each `qoq_anomaly_flag` state you plan to discuss looked at in the raw file
  - Claude 2026-10-09: OR 2022Q3, KY 2023Q2, ME 2024Q2 confirmed as published by CMS (report §3). Add any other state you will discuss.

## V5 – ARCOS
- [x] (OO 2026-10-09; signed VERIFICATION_REPORT.md) Five state-quarters checked against the PDF pages: `source_text_line` in `arcos_buprenorphine_state_quarter.csv` points to the line in `data/interim/arcos/report_yr_<year>.txt`
  - Claude 2026-10-09: NV 2019Q2, KY 2017Q4, TX 2021Q3, VT 2018Q1, CA 2023Q4 all match the rendered PDF pages (report §4). Initial to accept.
- [x] (OO 2026-10-09; signed VERIFICATION_REPORT.md) Confirm with DEA, or note in the paper, that 2024–2025 summaries omit drug code 9064
  - Claude 2026-10-09: noted in LIMITATIONS 8; DEA gives no reason. Decision open on the Jan–Jun 2024 report (report §0, D1).

## V6 – Policy dates (`data/raw/policy/policy_events_manual.csv`)
- [x] (OO 2026-10-09; all 61 original rows confirmed; 3 MOUD-exemption rows kept as documented uncertainty, DECISIONS D3) Every row opened at its `source_url` and the date confirmed
- [x] (OO 2026-10-09; see DECISIONS.md) Every row whose `verification_status` says VERIFY resolved (continuous-enrollment start date; four early community-engagement plans; Georgia Pathways against the CMS 1115 approval)
- [x] (OO 2026-10-09; KFF implementation dates; see DECISIONS.md) Decide the Maine (2018-07-01 retroactive vs 2019-01-10) and North Carolina (2023-10-01 vs 2023-12-01) expansion dates
- [x] (OO 2026-10-09; signed VERIFICATION_REPORT.md) Unwinding start months spot-checked for 5 states against state announcements
  - Claude 2026-10-09: 11 states checked against the CMS timeline table (2023-06-29). Months are consistent, but they are renewal-due months; coverage ended about 1 month later. Decision open (report §0, D2).

## V7 – Denominator
- [x] (OO 2026-10-09; MBES primary, PI sensitivity; see DECISIONS.md) Choose the primary rate for the paper (MBES or PI) and state why; keep both in the data

## Before it goes public
- [x] (OO 2026-10-09) README and LIMITATIONS read in full and approved by you (drafted with Claude; disclosed in README). Any manuscript still written in your own voice
- [x] (2026-10-09; gate clear) Figures regenerated with `python code/12_figures.py --final`; draft banners removed from docs; `python tools/publish_gate.py . --allow-draft-in code/ tools/ data/interim/ --skip data/raw/sdud/ _to_delete/` passes
- [x] (OO 2026-10-11; Zenodo record checked: Dataset, CC BY 4.0, ORCID) `AUTHORS.json`, `CITATION.cff` and the Zenodo metadata name you identically
- [x] (2026-10-11; DECISIONS.md release row: version DOI 10.5281/zenodo.23298617, concept DOI 10.5281/zenodo.23298616) Evidence-log row written the day the DOI is minted
