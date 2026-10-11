# Medicaid Buprenorphine Access Tracker (MBAT)

**Status: v1.0.0 (2026-10-09), verified by the author ([`docs/VERIFICATION_REPORT.md`](docs/VERIFICATION_REPORT.md)). Planned updates: v1.1 (March 2027) and v1.2 (July 2027).**

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23298616.svg)](https://doi.org/10.5281/zenodo.23298616)

Cite all versions: [10.5281/zenodo.23298616](https://doi.org/10.5281/zenodo.23298616). This version (v1.0.0): [10.5281/zenodo.23298617](https://doi.org/10.5281/zenodo.23298617).

MBAT is a public, state-by-quarter panel of Medicaid-paid buprenorphine for opioid use disorder (OUD) in the 50 states and DC, 2016Q1–2027Q4. I built it because CMS State Drug Utilization Data (SDUD) are public but hard to use for buprenorphine: NDCs enter and leave the market, pain formulations share the same ingredient as OUD products, and small counts are suppressed. MBAT does that work once, documents every decision, and links the result to Medicaid enrollment, DEA ARCOS retail distribution, CDC provisional overdose deaths, and dated Medicaid policy events. Every input is a public download, so no data use agreement is needed.

Headline numbers, QA results and data coverage are in [`docs/SUMMARY.md`](docs/SUMMARY.md), which the pipeline generates from `paper/stats.json`. This README quotes no numbers by hand.

## What is in the release

| File | Grain | What it holds |
|---|---|---|
| `data/processed/mbat_panel_state_quarter.csv` | state × quarter (2,448 rows) | **Primary file.** OUD buprenorphine prescriptions, units, mg, spending, rates per 1,000 enrollees, enrollment, ARCOS, CDC, policy indicators, quality flags |
| `data/processed/mbat_panel_state_quarter_product.csv` | state × quarter × product group × FFS/MCO | The long form, including suppression counts |
| `data/processed/ndc_crosswalk.csv` | NDC | Every candidate buprenorphine NDC seen in SDUD, with RxNorm classification and review flags |
| `data/processed/policy_annotations.csv` | event | Dated policy events, one citation per row |
| `data/processed/mbat_sdud_buprenorphine_rows.csv` | SDUD row | Every included SDUD row, for auditing |
| `data/processed/qa_report.txt` | — | Row counts, reconciliation against raw CMS files, completeness, outliers. Read this first |
| `docs/CODEBOOK.md`, `docs/LIMITATIONS.md` | — | Definitions and known limits |

Product groups: `oud_transmucosal` (sublingual tablets and films, buccal buprenorphine-naloxone), `oud_extended` (Sublocade, Brixadi, Probuphine), and `pain` (Butrans and generics, Belbuca and generics, Buprenex and generics). Pain products are reported separately and excluded from every OUD measure.

## How to reproduce

Requirements: Python 3.10+, `pip install -r requirements.txt`, and poppler's `pdftotext` (macOS: `brew install poppler`). About 6 GB of disk is needed for the raw files.

```bash
python code/01_fetch.py          # downloads every raw input and checks its SHA-256 against data/raw/MANIFEST.csv
bash run_all.sh                  # steps 02-13; prints the QA report at the end
```

`01_fetch.py` will not overwrite a file whose hash already matches. If CMS, DEA or CDC has republished a file, the hash check fails, and the script tells you which file changed rather than silently using a new vintage. The pipeline is numbered in run order:

| Step | Script | Does |
|---|---|---|
| 01 | `01_fetch.py` | Downloads raw inputs; verifies hashes |
| 02 | `02_reference_ndcs.py` | Buprenorphine NDCs from the FDA NDC Directory (current + excluded, outer + inner packages) |
| 03 | `03_extract_sdud.py` | Streams each SDUD year; keeps candidate rows; indexes all NDCs and state-quarters |
| 04 | `04_ndc_crosswalk.py` | Classifies candidates using NLM RxNorm (RxNav), cached in `data/raw/ndc_reference/` |
| 05 | `05_enrollment.py` | Quarterly enrollment from two CMS series (MBES and Performance Indicator) |
| 06 | `06_arcos.py` | Buprenorphine (DEA code 9064) from ARCOS Retail Drug Summary Reports 2 and 3 |
| 07 | `07_cdc_overdose.py` | 12-month-ending overdose deaths at each quarter's last month |
| 08 | `08_policy.py` | Policy events and state-quarter indicators |
| 09 | `09_build_panel.py` | Assembles the panel |
| 10 | `10_reconcile.py` | Re-sums named state-quarters straight from the raw CMS files |
| 11 | `11_qa_report.py` | QA report and `paper/stats.json` |
| 12 | `12_figures.py` | Figures (`--final` for release figures) |
| 13 | `13_summary.py` | `docs/SUMMARY.md` from `paper/stats.json` |

Raw SDUD files (about 5 GB) are not redistributed in the repository or the Zenodo record, because `01_fetch.py` re-downloads them from CMS. Smaller raw inputs and the RxNav response cache are included.

## Sources

| Source | Vintage pinned | Link |
|---|---|---|
| CMS State Drug Utilization Data | 2016–2019 annual files; 2020–2025 re-released July 2026; 2026 (Q1 only) | https://data.medicaid.gov |
| CMS Medicaid & CHIP Performance Indicator enrollment | September 2026 release | https://data.medicaid.gov |
| CMS Medicaid Enrollment – New Adult Group (MBES) | February 2026 release | https://data.medicaid.gov |
| CMS Medicaid and CHIP Updated Renewal Outcomes | October 2024 final release | https://data.medicaid.gov |
| DEA ARCOS Retail Drug Summary | 2016–2025 annual reports | https://www.deadiversion.usdoj.gov/arcos/retail_drug_summary/arcos-drug-summary-reports.html |
| CDC NCHS VSRR Provisional Drug Overdose Death Counts | 2026-09-16 update | https://data.cdc.gov/d/xkb8-kh2a |
| FDA NDC Directory (current and excluded) | retrieved 2026-10-08 | https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory |
| NLM RxNorm via RxNav | 05-Oct-2026 | https://rxnav.nlm.nih.gov |
| Policy events | see `data/raw/policy/policy_events_manual.csv` | per row |

Exact files, sizes, row counts and SHA-256 hashes are in `data/raw/MANIFEST.csv`.

## Limitations

See [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md). The ones most likely to matter:
- SDUD sums are lower bounds because of cell suppression.
- 2026 quarters are preliminary.
- ARCOS buprenorphine ends at 2023Q4, because DEA's 2024 and 2025 summaries omit drug code 9064.
- `unwinding_start_month` is the renewal-due month; use `unwinding_first_disenrollment_month` for timing.
- Mandatory MOUD benefit coding for Hawaii, South Dakota and Wyoming is uncertain.
- CDC deaths are 12-month-ending counts.
- Prior-authorization and dose-cap columns are empty in v1.0.

## License and citation

Code: MIT (`LICENSE`). Data and documentation: CC BY 4.0 (`LICENSE-DATA.md`), with attribution to CMS, DEA, CDC/NCHS, FDA and NLM as the underlying public sources. Cite using `CITATION.cff` or the DOIs above.

## Maintainer

Oluwapelumi Odubunmi (ORCID [0009-0004-8843-5339](https://orcid.org/0009-0004-8843-5339)), Department of Pharmaceutical Outcomes and Policy, College of Pharmacy, University of Florida. odubunmipelumi@gmail.com

AI assistance: I used Claude (Anthropic) to write the code, process the data and draft this documentation, including this README. I made every analytic decision (`docs/DECISIONS.md`) and reviewed the checks of the crosswalk, totals and policy dates before release (`docs/VERIFY_CHECKLIST.md`, `docs/VERIFICATION_REPORT.md`).
