#!/usr/bin/env python3
"""Step 11 - QA report and stats file.

Writes data/processed/qa_report.txt (read this before trusting anything) and paper/stats.json
(every number any MBAT document quotes; documents interpolate from it, never hand-typed).
Requires steps 02-10 to have run, including 10_reconcile.py for every spot-check year.
"""
import csv
import glob
import json
import os
import re
import sys
from datetime import date

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
INT = os.path.join(ROOT, "data", "interim")
OUT = os.path.join(PROC, "qa_report.txt")
STATS = os.path.join(ROOT, "paper", "stats.json")
NAME_PATTERN = re.compile(r"(?<![A-Z])BUP(?!ROP|IV)|SUBOX|SUBUT|ZUBSOL|BUNAV|SUBLOC|BRIXAD|PROBUPH|BELBUC|BUTRAN", re.I)

L = []
S = {}


def h(t):
    L.append("\n" + t + "\n" + "-" * len(t))


def line(t=""):
    L.append(t)


def main():
    man = pd.read_csv(os.path.join(ROOT, "data", "raw", "MANIFEST.csv"))
    xw = pd.read_csv(os.path.join(PROC, "ndc_crosswalk.csv"), dtype={"ndc11": str})
    rows = pd.read_csv(os.path.join(PROC, "mbat_sdud_buprenorphine_rows.csv"), dtype={"ndc": str}, low_memory=False)
    p = pd.read_csv(os.path.join(PROC, "mbat_panel_state_quarter.csv"))
    lt = pd.read_csv(os.path.join(PROC, "mbat_panel_state_quarter_product.csv"))
    rel = p[p.data_status != "sdud_not_yet_released"]
    final = p[p.data_status == "sdud_released"]

    is_final = "--final" in sys.argv
    line(f"MBAT QA report - generated {date.today().isoformat()}" + ("" if is_final else " - DRAFT (not yet verified by the author)"))

    # 1. stage counts
    h("1. Row counts by stage (SDUD)")
    cand = {}
    for f in glob.glob(os.path.join(INT, "sdud", "sdud_*_bup_candidates.csv")):
        y = int(re.search(r"(20\d\d)", f).group(1))
        cand[y] = sum(1 for _ in open(f)) - 1
    raw = man[man.file.str.startswith("sdud/")].assign(year=lambda d: d.file.str.extract(r"(20\d\d)")[0].astype(int))
    line(f"{'year':>5} {'raw rows':>12} {'candidates':>11} {'included*':>10} {'suppressed':>11}")
    inc_by_year = rows.groupby("year").size()
    sup_by_year = rows.groupby("year")["suppressed"].sum()
    for r in raw.sort_values("year").itertuples():
        line(f"{r.year:>5} {int(r.data_rows):>12,} {cand.get(r.year, 0):>11,} {int(inc_by_year.get(r.year, 0)):>10,} {int(sup_by_year.get(r.year, 0)):>11,}")
    line("* included = buprenorphine per crosswalk, in the 50 states + DC (national 'XX' and territories excluded)")
    S["sdud_raw_rows_total"] = int(raw.data_rows.sum())
    S["sdud_candidate_rows"] = int(sum(cand.values()))
    S["sdud_included_rows"] = int(len(rows))
    S["sdud_included_rows_suppressed"] = int(rows.suppressed.sum())

    # 2. crosswalk
    h("2. NDC crosswalk")
    inc = xw[xw.include == 1]
    S["ndc_candidates"] = int(len(xw))
    S["ndc_included"] = int(len(inc))
    S["ndc_excluded_not_buprenorphine"] = int((xw.include == 0).sum())
    S["ndc_needs_review"] = int(xw.needs_review.sum())
    for g, n in inc.product_group.value_counts().items():
        S[f"ndc_{g}"] = int(n)
    line(f"{len(xw)} candidate NDCs: {len(inc)} included, {S['ndc_excluded_not_buprenorphine']} rejected as not buprenorphine (RxNorm).")
    line("Included by group: " + ", ".join(f"{g} {n}" for g, n in inc.product_group.value_counts().items()))
    line("Included by form: " + ", ".join(f"{g} {n}" for g, n in inc.form.value_counts().items()))
    line(f"needs_review = 1 for {S['ndc_needs_review']} NDCs (reasons: " +
         "; ".join(f"{k} x{v}" for k, v in xw[xw.needs_review == 1].review_reason.value_counts().items()) + ")")
    line("Rejected candidates (name matched, RxNorm says not buprenorphine): " +
         ", ".join(sorted(set(xw[xw.include == 0].rxnorm_concept.str.extract(r"^(?:[\d.]+ \w+ )?(?:Smoking Cessation )?(?:\d+ HR )?([a-z]+)")[0].dropna()))))

    # 3. coverage audit
    h("3. Coverage audit: other NDCs from buprenorphine labelers whose names did not match")
    labelers = set(inc.ndc11.str[:5])
    idx = pd.concat([pd.read_csv(f, dtype={"ndc": str}) for f in glob.glob(os.path.join(INT, "sdud", "sdud_*_ndc_index.csv"))])
    idx = idx[idx.ndc.str[:5].isin(labelers) & ~idx.ndc.isin(xw.ndc11)]
    agg = idx.groupby("ndc").agg(rows=("n_rows", "sum"), names=("product_names", lambda s: " | ".join(sorted(set(" | ".join(s.fillna("").astype(str)).split(" | ")))[:3])))
    # Names that look like a buprenorphine product but escaped the step 03 pattern
    # (ibuprofen, bupropion, nalbuphine, and naloxone alone are expected and ignored)
    susp = agg[agg.names.str.contains(r"(?<![A-Z])(?:BUPR(?!OP)|BUP[/&-]|B/N|SUBO|SUBU|ZUBS|BRIX|BELB|SUBLO|BUTRA)",
                                      case=False, regex=True)]
    line(f"{len(agg)} non-candidate NDCs share a labeler with an included NDC; {len(susp)} have names that look like buprenorphine products:")
    for n, r in susp.sort_values("rows", ascending=False).head(25).iterrows():
        line(f"  {n}  rows={int(r.rows):>6}  {r.names[:80]}")
    S["coverage_audit_suspicious_ndcs"] = int(len(susp))
    S["qoq_anomaly_cells"] = int(p.qoq_anomaly_flag.sum())

    # 4. reconciliation
    h("4. Independent reconciliation against raw SDUD files (code/10_reconcile.py)")
    sc = pd.read_csv(os.path.join(INT, "qa", "spot_checks.csv"))
    recon_ok = True
    line(f"{'state':5} {'yq':7} {'kind':7} {'group':17} {'raw file':>10} {'panel':>10}  match  why")
    for r in sc.itertuples():
        fjs = os.path.join(INT, "qa", f"recon_{r.year}.json")
        if not os.path.exists(fjs):
            line(f"{r.state:5} {r.year}Q{r.quarter} NOT RUN - run code/10_reconcile.py --years {r.year}")
            recon_ok = False
            continue
        got = json.load(open(fjs)).get(f"{r.state}|{r.quarter}", {})
        for g in ["oud_transmucosal", "oud_extended", "pain"]:
            pv = lt[(lt.state == r.state) & (lt.year == r.year) & (lt.quarter == r.quarter) & (lt.product_group == g)]["rx"].sum()
            rv = got.get(g, 0.0)
            ok = abs(pv - rv) < 0.5
            recon_ok &= ok
            line(f"{r.state:5} {r.year}Q{r.quarter} {r.kind:7} {g:17} {rv:>10,.0f} {pv:>10,.0f}  {'OK' if ok else 'FAIL'}   {r.why if g == 'oud_transmucosal' else ''}")
    S["reconciliation_cells"] = int(len(sc) * 3)
    S["reconciliation_all_match"] = bool(recon_ok)

    # 5. completeness
    h("5. Panel completeness")
    S["panel_rows"] = int(len(p))
    S["panel_states"] = int(p.state.nunique())
    S["panel_first_quarter"] = "2016Q1"
    S["panel_last_quarter"] = "2027Q4"
    S["sdud_last_released_quarter"] = rel.yq.max()
    S["sdud_released_state_quarters"] = int(len(rel))
    S["sdud_preliminary_quarters"] = sorted(p[p.data_status == "sdud_released_preliminary"].yq.unique().tolist())
    line(f"{len(p)} state-quarters; {len(rel)} with released SDUD (through {S['sdud_last_released_quarter']}); "
         f"preliminary: {', '.join(S['sdud_preliminary_quarters'])}")
    line(f"released state-quarters with missing OUD total: {int(rel.rx_oud_total.isna().sum())}")
    gaps = p[p.mco_reporting_gap == 1]
    line("managed-care reporting gaps (likely incomplete totals): " + ", ".join(gaps.state + " " + gaps.yq))
    S["mco_reporting_gap_cells"] = int(len(gaps))
    nat = rel.groupby("yq")["rx_oud_total"].sum()
    last, prev = nat.index.max(), sorted(nat.index)[-2]
    S["national_rx_oud_last_vs_prev_pct"] = round(100 * (nat[last] / nat[prev] - 1), 1)
    line(f"national OUD prescriptions {prev} -> {last}: {S['national_rx_oud_last_vs_prev_pct']}% (preliminary data)")
    supp = rel.n_suppressed_rows_oud_total.sum() / rel.n_rows_oud_total.sum()
    S["share_oud_rows_suppressed_pct"] = round(100 * supp, 1)
    lb, ub = rel.rx_oud_total.sum(), rel.rx_oud_total_upper.sum()
    S["suppression_max_share_of_rx_pct"] = round(100 * (ub - lb) / ub, 1)
    line(f"{S['share_oud_rows_suppressed_pct']}% of OUD NDC-rows are suppressed; at most {S['suppression_max_share_of_rx_pct']}% "
         "of OUD prescriptions could sit in suppressed rows (10 per row upper bound).")

    # 6. ranges and outliers
    h("6. Range checks and outliers")
    for c in ["rx_oud_per_1k_mbes", "rx_oud_per_1k_pi", "bup_mg_oud_transmucosal_per_enrollee_mbes"]:
        v = final[c].dropna()
        line(f"{c}: n={len(v)} min={v.min():.2f} median={v.median():.2f} max={v.max():.2f}")
    neg = (rel[[c for c in rel.columns if c.startswith(("rx_", "units_", "amt_"))]] < 0).sum().sum()
    line(f"negative values in SDUD measures: {int(neg)}")
    q = rel.sort_values(["state", "year", "quarter"]).copy()
    q["prev"] = q.groupby("state").rx_oud_total.shift()
    q["chg"] = q.rx_oud_total / q.prev - 1
    big = q[(q.prev > 1000) & (q.chg.abs() > 0.5)]
    line(f"quarter-over-quarter changes > 50% (prior quarter > 1,000 rx): {len(big)} (flagged qoq_anomaly_flag = 1; values left as published)")
    for r in big.itertuples():
        line(f"  {r.state} {r.yq}: {r.prev:,.0f} -> {r.rx_oud_total:,.0f} ({100 * r.chg:+.0f}%)  mco_gap={r.mco_reporting_gap}")
    top = final.nlargest(3, "rx_oud_per_1k_mbes")[["state", "yq", "rx_oud_per_1k_mbes"]]
    line("highest rates: " + "; ".join(f"{r.state} {r.yq} {r.rx_oud_per_1k_mbes:.0f}" for r in top.itertuples()))

    # 7. other sources
    h("7. Enrollment, ARCOS, CDC, policy")
    e = rel[["mbes_medicaid", "pi_medicaid"]].dropna()
    ratio = e.pi_medicaid / e.mbes_medicaid
    S["enroll_pi_to_mbes_ratio_median"] = round(float(ratio.median()), 3)
    S["enroll_pi_to_mbes_ratio_p5"] = round(float(ratio.quantile(0.05)), 3)
    S["enroll_pi_to_mbes_ratio_p95"] = round(float(ratio.quantile(0.95)), 3)
    line(f"MBES coverage: {rel.mbes_medicaid.notna().sum()} released state-quarters; PI: {rel.pi_medicaid.notna().sum()}.")
    line(f"PI / MBES total Medicaid enrollment where both exist: median {S['enroll_pi_to_mbes_ratio_median']}, "
         f"5th-95th pct {S['enroll_pi_to_mbes_ratio_p5']}-{S['enroll_pi_to_mbes_ratio_p95']}")
    arc = p.dropna(subset=["arcos_bup_grams"])
    S["arcos_state_quarters"] = int(len(arc))
    S["arcos_last_quarter"] = arc.yq.max()
    probs = open(os.path.join(INT, "arcos", "arcos_parse_problems.txt")).read().strip()
    line(f"ARCOS buprenorphine: {len(arc)} state-quarters, {arc.yq.min()}-{arc.yq.max()}; parse problems: {probs}")
    both = rel.dropna(subset=["arcos_bup_grams", "bup_mg_oud_transmucosal"])
    share = both.bup_mg_oud_transmucosal.sum() / 1000 / both.arcos_bup_grams.sum()
    S["medicaid_transmucosal_mg_as_pct_of_arcos_retail"] = round(100 * share, 1)
    line(f"Sanity: Medicaid transmucosal buprenorphine (g) / ARCOS retail buprenorphine (g), pooled 2016-2023: "
         f"{S['medicaid_transmucosal_mg_as_pct_of_arcos_retail']}% (must be well below 100%)")
    rs = both.assign(s=both.bup_mg_oud_transmucosal / 1000 / both.arcos_bup_grams)
    over = rs[rs.s > 1]
    line(f"state-quarters where Medicaid grams exceed ARCOS retail grams: {len(over)}" +
         ("" if over.empty else " -> " + ", ".join(over.state + " " + over.yq)))
    cdc = rel.dropna(subset=["od_all_12mo_reported"])
    S["cdc_last_quarter"] = p.dropna(subset=["od_all_12mo_reported"]).yq.max()
    line(f"CDC: all-drug deaths present for {len(cdc)} released state-quarters; opioid deaths missing (CDC suppression "
         f"for low drug specificity) in {int(rel.od_opioid_12mo_reported.isna().sum())}. Last quarter: {S['cdc_last_quarter']}")
    ev = pd.read_csv(os.path.join(PROC, "policy_annotations.csv"))
    xc = pd.read_csv(os.path.join(INT, "policy", "expansion_date_crosscheck.csv"))
    S["policy_events"] = int(len(ev))
    line(f"policy events: {len(ev)}; KFF vs CMS expansion-date cross-check: {int(xc.agree.sum())}/{len(xc)} agree; "
         "disagreements: " + ", ".join(f"{r.state} (KFF {r.kff_date}, CMS {r.cms_note_date})" for r in xc[~xc.agree].itertuples()))
    line("policy rows still marked VERIFY in policy_events_manual.csv: " + str(int(ev.verification_status.fillna("").str.contains("VERIFY").sum())))

    # 8. headline numbers for documents
    h("8. Headline numbers (also in paper/stats.json)")
    yr = final.groupby("year")["rx_oud_total"].sum()
    S["rx_oud_by_year"] = {int(k): int(v) for k, v in yr.items()}
    S["rx_oud_peak_year"] = int(yr.idxmax())
    S["rx_oud_2016"] = int(yr[2016])
    S["rx_oud_2022"] = int(yr[2022])
    S["rx_oud_2025"] = int(yr[2025])
    S["rx_oud_pct_change_2016_2022"] = round(100 * (yr[2022] / yr[2016] - 1), 1)
    S["rx_oud_pct_change_2022_2025"] = round(100 * (yr[2025] / yr[2022] - 1), 1)
    ext = final.groupby("year")[["rx_oud_extended", "rx_oud_total"]].sum()
    S["extended_share_of_oud_rx_2025_pct"] = round(100 * ext.loc[2025, "rx_oud_extended"] / ext.loc[2025, "rx_oud_total"], 1)
    S["pain_rx_2025"] = int(final[final.year == 2025].rx_pain.sum())
    for k, v in S.items():
        line(f"{k}: {v}")

    os.makedirs(os.path.dirname(STATS), exist_ok=True)
    json.dump(S, open(STATS, "w"), indent=1)
    open(OUT, "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
