#!/usr/bin/env python3
"""Step 13 - Write docs/SUMMARY.md from paper/stats.json (the only place prose quotes numbers)."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = json.load(open(os.path.join(ROOT, "paper", "stats.json")))
final = "--final" in sys.argv
f = lambda n: f"{n:,}"

by_year = "\n".join(f"| {y} | {f(v)} |" for y, v in S["rx_oud_by_year"].items())
md = f"""# MBAT summary
{'' if final else chr(10) + '**DRAFT. Generated from paper/stats.json by code/13_summary.py. Not yet verified by the author.**' + chr(10)}
## Coverage
- Panel: {S['panel_states']} jurisdictions x {S['panel_first_quarter']}-{S['panel_last_quarter']} ({f(S['panel_rows'])} state-quarters).
- SDUD released through {S['sdud_last_released_quarter']} ({f(S['sdud_released_state_quarters'])} state-quarters); preliminary: {', '.join(S['sdud_preliminary_quarters'])}.
- ARCOS buprenorphine: {f(S['arcos_state_quarters'])} state-quarters through {S['arcos_last_quarter']}. CDC deaths through {S['cdc_last_quarter']}. Policy events: {S['policy_events']}.

## Pipeline and QA
- SDUD rows read: {f(S['sdud_raw_rows_total'])}; candidate rows: {f(S['sdud_candidate_rows'])}; included buprenorphine rows: {f(S['sdud_included_rows'])} ({f(S['sdud_included_rows_suppressed'])} suppressed).
- NDCs: {S['ndc_candidates']} candidates, {S['ndc_included']} included ({S['ndc_oud_transmucosal']} transmucosal OUD, {S['ndc_oud_extended']} extended-release OUD, {S['ndc_pain']} pain), {S['ndc_excluded_not_buprenorphine']} rejected; {S['ndc_needs_review']} flagged for review.
- Independent reconciliation against raw CMS files: {S['reconciliation_cells']} cells, all match = {S['reconciliation_all_match']}.
- Suppression: {S['share_oud_rows_suppressed_pct']}% of OUD NDC-rows suppressed; at most {S['suppression_max_share_of_rx_pct']}% of OUD prescriptions could lie in them.
- Flags: {S['mco_reporting_gap_cells']} managed-care reporting gaps; {S.get('qoq_anomaly_cells', 'n/a')} quarter-over-quarter anomalies (kept as published).
- Enrollment series: PI / MBES median ratio {S['enroll_pi_to_mbes_ratio_median']} (5th-95th pct {S['enroll_pi_to_mbes_ratio_p5']}-{S['enroll_pi_to_mbes_ratio_p95']}).
- Sanity: Medicaid transmucosal buprenorphine grams equal {S['medicaid_transmucosal_mg_as_pct_of_arcos_retail']}% of ARCOS retail grams, 2016-2023 pooled.

## Headline series: Medicaid OUD buprenorphine prescriptions, 50 states + DC (lower bound)
| Year | Prescriptions |
|---|---|
{by_year}

- Change {2016}-{S['rx_oud_peak_year']}: {S['rx_oud_pct_change_2016_2022']:+}%; change 2022-2025: {S['rx_oud_pct_change_2022_2025']:+}%.
- Extended-release share of OUD prescriptions, 2025: {S['extended_share_of_oud_rx_2025_pct']}%.
- 2026 is excluded above (preliminary; {S['national_rx_oud_last_vs_prev_pct']}% vs the prior quarter at this vintage).
"""
open(os.path.join(ROOT, "docs", "SUMMARY.md"), "w").write(md)
print("docs/SUMMARY.md written")
