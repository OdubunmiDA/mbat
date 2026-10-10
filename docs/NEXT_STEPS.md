# MBAT next steps

v1.0.0 was released 2026-10-09 (moved forward from the March 2027 target; see DECISIONS).

## v1.1 (target March 2027)
1. Re-run `01_fetch.py`. CMS will likely have posted 2026Q2–Q3 SDUD and revised 2026Q1; update the manifest, re-run, and re-verify V4–V6 (`docs/VERIFY_CHECKLIST.md`).
2. **Prior authorization and dose caps.** No dated 50-state Medicaid source exists, so code them from primary documents:
   - For each state, use the Medicaid preferred drug list (PDL) and buprenorphine PA criteria, with archived copies via the Internet Archive for earlier years.
   - Record `state, effective_date, pa_required (transmucosal / extended), daily_dose_cap_mg, source_url, archive_url`.
   - Seed with published cross-sectional reviews (e.g., the JAMA Network Open thematic analysis of state Medicaid buprenorphine PA requirements, and Health Affairs comparisons of insurance restrictions 2017–2021), then confirm each state against its own documents.
   - The schema is in place (`bup_prior_auth_required`, `bup_daily_dose_cap_mg`).
3. Confirm the mandatory MOUD exemption scope and dates for Hawaii, South Dakota and Wyoming with CMS or the state Medicaid offices, including post-2025 re-certification (DECISIONS, D3).
4. Decide whether the federal community engagement indicator should also cover states whose only adult coverage is a section 1115 demonstration (e.g., Georgia Pathways) (DECISIONS, D4).
5. Confirm Iowa's planned 2026-12-01 community engagement start, and add actual 2027 federal implementation and good-faith exemptions.
6. Reconsider the DEA January–June 2024 ARCOS report (DECISIONS, D1).

## v1.2 (target July 2027)
- Take the CMS refresh of 2026 SDUD (expected to include 2026Q4) and any 2027 quarters released.
- Update enrollment (PI monthly; MBES if CMS posts past 2025Q2), CDC VSRR, and policy events.
- Check whether DEA restores buprenorphine to the ARCOS Retail Drug Summary.

## Data descriptor paper
- Draft a data-descriptor manuscript from `paper/stats.json` and the figures, in your own words. Choose the venue (a data journal or a field journal's data-paper track) before drafting, since it sets the format.
