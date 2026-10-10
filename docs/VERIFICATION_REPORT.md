# MBAT verification report

**Checks run by Claude on 2026-10-09; reviewed and signed by Oluwapelumi Odubunmi on 2026-10-09 (§6).**

How to review (about 20 minutes): read §0 and make the four decisions. Skim §1–§5, and open at least one piece of evidence in each section. Then sign §6.

---

## 0. Needs your attention

Nothing failed. Every number checked matches its source. Four items need a decision from you.

| # | Issue | What I found | My recommendation |
|---|---|---|---|
| **D1** | ARCOS 2024 | The 2024 and 2025 full-year DEA reports leave out buprenorphine (code 9064), and DEA gives no reason. An unlisted DEA file, `report_yr_Jan_Jun2024.pdf` (run 2024-10-03, now in your Downloads), *does* include 9064. It could extend ARCOS to 2024Q2. | **Leave it out of v1.0.** It is unlisted and covers only half a year. LIMITATIONS 8 now mentions it. Revisit for v1.1. |
| **D2** | Unwinding start is one month early | `unwinding_start_month` is the month renewals were *due* for the first cohort that lost coverage. People actually lost coverage about one month later; in Oregon it was three months later. For the **17 states** whose start month is the last month of a quarter (AL, CA, ID, IL, LA, MI, MN, MO, MS, NC, NH, NJ, NY, OK, SD, TN, WI) and for Oregon, this switches `unwinding_in_effect` on **one quarter early**. | **Add a second column**, `unwinding_first_disenrollment_month` (start + 1 month; Oregon + 3), with its own indicator. Keep the existing column. Use the new one in any event-study timing. The CODEBOOK and LIMITATIONS already explain the meaning. |
| **D3** | MOUD exemption: HI, SD, WY | CMS SMD #24-004 names all three states as exempt from the mandatory MOUD benefit. However, a CMS section 1135 letter dated 2021-03-19 shows South Dakota submitting a MAT state plan amendment effective 2020-10-01. The exemption may have been partial (for example, methadone/OTP only). | **Keep the 3 VERIFY rows** and the current coding (0 during the exemption, blank after). Email CMS or the SD Medicaid office before v1.1. The publish gate will block v1.0 until you either resolve these rows or re-tag them as "documented uncertainty". |
| **D4** | Community engagement in demonstration states | The federal community-engagement indicator is coded only for ACA expansion states. Whether 1115-demonstration-only states (for example, Georgia) fall under the federal requirement is not settled in the CMS material reviewed. | **Leave it as is for v1.0.** It is already stated in LIMITATIONS 10. |

---

## 1. Reproducibility

| Check | Result |
|---|---|
| Re-hash all 27 raw files against `data/raw/MANIFEST.csv` (SHA-256) | **27/27 OK** (16 reference files + 11 SDUD files, 4.9 GB). Logs: `data/interim/qa/repro/manifest_check_a.txt`, `manifest_check_b.txt` |
| Re-run steps 02–13 from scratch (`03 --force`, recon caches cleared) | **Byte-identical.** All 11 processed outputs and 35 interim and reference files have the same MD5 as before (`data/interim/qa/repro/before*.md5`, `after.md5`) |
| `reconciliation_all_match` in `qa_report.txt` | **True** |
| Numbers in README, LIMITATIONS, CODEBOOK and NEXT_STEPS | Every figure traces to `stats.json`, `qa_report.txt` or `SUMMARY.md`, or is a fixed fact (for example, the Sublocade mL sizes). Recheck after you rewrite the README and LIMITATIONS. |

Limitation: the device has no direct network access, so `01_fetch.py` could not re-download the files. The hash match proves the files are unchanged since they were downloaded. It does not prove CMS still serves the same files. The v1.1 refresh will show any drift.

## 2. NDC crosswalk (V1)

The 20-NDC random sample (seed 20261009, `data/interim/qa/ndc_spotcheck_sample.json`) covers 6 forms. All 20 are correct.

| NDC | Form | Confirmed |
|---|---|---|
| 65162-0415-03 | SL tablet | bup/nal 8/2 mg, DailyMed |
| 60687-0492-21 | SL tablet | bup 8 mg, DailyMed |
| 42858-0601-03 | SL tablet | bup/nal 2/0.5 mg, DailyMed |
| 72888-0183-30 | SL tablet | bup 8 mg, DailyMed |
| 00904-7010-06 | SL tablet | bup/nal 8/2 mg, DailyMed |
| 12496-1212-03 | SL film | Suboxone 12/3 mg, DailyMed |
| 00378-8766-93 | SL film | bup/nal 4/1 mg, DailyMed |
| 12496-1204-01 | SL film | Suboxone 4/1 mg, DailyMed |
| 00781-7238-06 | SL film | 8/2 mg (Sandoz, NDA022410, 2019–2021): discontinued; RxNorm + FDA excluded list |
| 52427-0694-11 | SL film | 4/1 mg (Almatica, ANDA205954, 2019–2021): discontinued; RxNorm + FDA excluded list |
| 59385-0023-01 / 0024-01 / 0021-60 | Buccal (Belbuca) | 300 / 450 / 75 mcg, DailyMed |
| 12496-0100-02 / 0300-02 | ER injection (Sublocade) | 100 mg/0.5 mL; 300 mg/1.5 mL, DailyMed (label lists the carton codes -0100-1 / -0300-1; the -2 syringe-in-pouch codes sit inside those cartons per the FDA NDC Directory). Author checked 12496-0100 on DailyMed 2026-10-09 |
| 58284-0208-01 | ER injection (Brixadi) | 8 mg/0.16 mL, DailyMed |
| 42858-0750-40 / 47781-0406-04 | Transdermal | 5 mcg/hr, DailyMed |
| 70069-0027-05 / 00143-9246-05 | Injection | 0.3 mg/mL, DailyMed |

The 7th form, implant (Probuphine), and buccal bup-naloxone (Bunavail) were already checked in your 41-row flagged review. Look up any NDC at `https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query=<NDC>`.

## 3. State totals against CMS (V4)

- **18 state-quarters, 54 cells** (OUD transmucosal, OUD extended, pain) were re-summed directly from the raw CMS files by `code/10_reconcile.py`. **All 54 match the panel.** The list and the reason each was chosen are in `data/interim/qa/spot_checks.csv`. They are the original 12 plus NV 2019Q2, NV 2024Q4, OR 2022Q3, KY 2023Q2, ME 2024Q2 and CA 2023Q4.
- **Independent second source:** the same cells were queried in CMS's own online SDUD datastore (data.medicaid.gov). That is a different system from the downloaded CSV files.

| State-quarter | OUD transmucosal Rx | OUD extended Rx | Match |
|---|---|---|---|
| NV 2022Q2 | 7,788 | 48 | ✓ |
| NV 2024Q4 | 7,757 | 217 | ✓ |
| OR 2022Q3 | 297 | 78 | ✓ (the Oregon collapse is real in CMS data) |
| KY 2023Q2 | 181,771 | 3,778 | ✓ (the Kentucky spike is real in CMS data) |
| CA 2023Q4 | 61,450 | 3,627 | ✓ |

The anomaly flags therefore mark state submission artifacts that CMS itself published. They are not pipeline errors.

## 4. ARCOS (V5)

Five state-quarters were checked against the DEA PDF page images. All five match.

| State-quarter | MBAT grams | Page image |
|---|---|---|
| NV 2019Q2 | 4,347.38 | `data/interim/qa/arcos_pages/NV_2019-394.png` |
| KY 2017Q4 | 34,938.66 | `…/KY_2017-0812.png` |
| TX 2021Q3 | 36,743.66 | `…/TX_2021-303.png` |
| VT 2018Q1 | 6,608.52 | `…/VT_2018-396.png` |
| CA 2023Q4 | 97,695.87 | `…/CA_2023-126.png` |

The absence of 9064 from 2024–2025 is noted in LIMITATIONS 8. See D1.

## 5. Policy dates (V6)

The unwinding start months were compared with the CMS table "2023 State Timelines for Initiating Unwinding-Related Renewals" (2023-06-29) for 11 states:

| MBAT month | States | First month without coverage (CMS) |
|---|---|---|
| 2023-03 | ID, NH, OK, SD | April 2023 |
| 2023-04 | AZ, FL | May 2023 |
| 2023-05 | KY, NV | June 2023 |
| 2023-06 | CA, NY | July 2023 |
| 2023-07 | OR | October 2023 |

All 11 states are consistent once the month is read as the renewal-due month. See D2 for the quarter shift.

MOUD exemptions: see D3. All other policy rows were already confirmed in your earlier review (DECISIONS.md).

## 6. Author sign-off

I reviewed §0–§5, opened the evidence I chose to check, and accept the results.

Decisions:
- D1: Agree, Jan–Jun 2024 report not used in v1.0 (OO 2026-10-09)
- D2: Agree, `unwinding_first_disenrollment_month` added and used for timing (OO 2026-10-09)
- D3: Option A, keep coding, labelled documented uncertainty; confirm with CMS/states before v1.1 (OO 2026-10-09)
- D4: Option A, keep expansion-states-only coding; revisit for v1.1 (OO 2026-10-09)

Author spot-checks 2026-10-09: ARCOS NV 2019Q2 page (matches); DailyMed Sublocade 100 mg/0.5 mL (matches).

Signed: Oluwapelumi Odubunmi (OO)  Date: 2026-10-09 
