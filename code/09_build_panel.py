#!/usr/bin/env python3
"""Step 09 - Assemble the MBAT state x quarter panel (2016Q1-2027Q4).

Inputs: step 03 candidate rows and state-quarter row counts, step 04 crosswalk, and the
processed enrollment (05), ARCOS (06), CDC (07), and policy (08) tables.
Outputs (data/processed/):
  mbat_sdud_buprenorphine_rows.csv          every included SDUD row, with crosswalk attributes
  mbat_panel_state_quarter_product.csv      long: state x quarter x product group x utilization type
  mbat_panel_state_quarter.csv              wide: one row per state-quarter (primary release file)

Conventions
  * SDUD state "XX" (CMS national total) and territories are excluded.
  * Suppressed SDUD rows (CMS suppresses counts below 11) carry no counts; they are counted in
    n_suppressed_rows and contribute zero to sums, so every SDUD sum is a lower bound. Each
    suppressed row holds at most 10 prescriptions, so rx_*_upper = rx_* + 10 x n_suppressed_rows_*
    is an upper bound on prescriptions.
  * qoq_anomaly_flag = 1 when OUD prescriptions change by more than 50% from a prior quarter
    above 1,000; values are left exactly as CMS published them.
  * mco_reporting_gap = 1 when a state reported managed-care (MCOU) rows in any of the previous
    four quarters but none in this quarter; totals for such quarters are likely incomplete.
  * A state-quarter where CMS published no SDUD rows of any drug for a utilization type is
    missing (NA) for that type, not zero. A state-quarter after the last released SDUD quarter
    has data_status = "sdud_not_yet_released" and NA utilization; quarters from the newest annual
    SDUD file are "sdud_released_preliminary".
  * Rates are per 1,000 enrollees per quarter, computed separately for each enrollment series.
"""
import glob
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INT = os.path.join(ROOT, "data", "interim", "sdud")
PROC = os.path.join(ROOT, "data", "processed")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from states import STATES  # noqa: E402

MEAS = ["number_of_prescriptions", "units_reimbursed", "total_amount_reimbursed", "medicaid_amount_reimbursed"]
SHORT = {"number_of_prescriptions": "rx", "units_reimbursed": "units",
         "total_amount_reimbursed": "amt_total", "medicaid_amount_reimbursed": "amt_medicaid"}
GROUPS = ["oud_transmucosal", "oud_extended", "pain"]


def load_rows():
    xw = pd.read_csv(os.path.join(PROC, "ndc_crosswalk.csv"), dtype={"ndc11": str})
    xw = xw[xw["include"] == 1]
    parts = [pd.read_csv(f, dtype={"ndc": str, "state": str}, low_memory=False)
             for f in sorted(glob.glob(os.path.join(INT, "sdud_*_bup_candidates.csv")))]
    d = pd.concat(parts, ignore_index=True)
    d["state"] = d["state"].str.strip()
    d["utilization_type"] = d["utilization_type"].str.strip()
    d = d.merge(xw[["ndc11", "product_group", "ingredient", "form", "brand", "bup_mg_per_unit", "rxnorm_concept"]],
                left_on="ndc", right_on="ndc11", how="inner").drop(columns="ndc11")
    d = d[d["state"].isin(STATES)].copy()
    for c in MEAS:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["suppressed"] = d["suppression_used"].astype(str).str.lower().eq("true")
    d["bup_mg"] = d["units_reimbursed"] * pd.to_numeric(d["bup_mg_per_unit"], errors="coerce")
    return d


def reported_cells():
    parts = [pd.read_csv(f, dtype={"state": str}) for f in glob.glob(os.path.join(INT, "sdud_*_state_quarter_rows.csv"))]
    r = pd.concat(parts)
    r = r[r["state"].isin(STATES)]
    return r


def long_table(d, rep):
    keys = ["state", "year", "quarter", "product_group", "utilization_type"]
    agg = d.groupby(keys).agg(
        **{SHORT[c]: (c, lambda s: s.sum(min_count=1)) for c in MEAS},
        bup_mg=("bup_mg", lambda s: s.sum(min_count=1)),
        n_rows=("ndc", "size"), n_suppressed_rows=("suppressed", "sum"),
        n_ndcs=("ndc", "nunique")).reset_index()
    # complete grid over reported cells: reported cell with no bup rows -> zeros, not NA
    cells = rep[["state", "year", "quarter", "utilization_type"]].drop_duplicates()
    grid = cells.merge(pd.DataFrame({"product_group": GROUPS}), how="cross")
    out = grid.merge(agg, on=keys, how="left")
    zero_cols = ["n_rows", "n_suppressed_rows", "n_ndcs"]
    out[zero_cols] = out[zero_cols].fillna(0).astype(int)
    for c in ["rx", "units", "amt_total", "amt_medicaid", "bup_mg"]:
        out[c] = out[c].fillna(0.0)  # no rows, or only suppressed rows: lower bound is zero
    out["all_rows_suppressed"] = ((out["n_rows"] > 0) & (out["n_rows"] == out["n_suppressed_rows"])).astype(int)
    out.loc[out["product_group"] != "oud_transmucosal", "bup_mg"] = np.nan
    return out.sort_values(keys)


def wide_panel(lt):
    allu = lt.groupby(["state", "year", "quarter", "product_group"]).agg(
        rx=("rx", lambda s: s.sum(min_count=1)), units=("units", lambda s: s.sum(min_count=1)),
        amt_total=("amt_total", lambda s: s.sum(min_count=1)), amt_medicaid=("amt_medicaid", lambda s: s.sum(min_count=1)),
        bup_mg=("bup_mg", lambda s: s.sum(min_count=1)), n_rows=("n_rows", "sum"),
        n_suppressed_rows=("n_suppressed_rows", "sum")).reset_index()
    w = allu.pivot_table(index=["state", "year", "quarter"], columns="product_group",
                         values=["rx", "units", "amt_total", "amt_medicaid", "bup_mg", "n_rows", "n_suppressed_rows"],
                         aggfunc="first")
    w.columns = [f"{m}_{g}" for m, g in w.columns]
    w = w.drop(columns=[c for c in w.columns if c.startswith("bup_mg_") and not c.endswith("oud_transmucosal")])
    w = w.reset_index()
    for m in ["rx", "units", "amt_total", "amt_medicaid", "n_rows", "n_suppressed_rows"]:
        w[f"{m}_oud_total"] = w[[f"{m}_oud_transmucosal", f"{m}_oud_extended"]].sum(axis=1, min_count=1)
    for g in GROUPS + ["oud_total"]:
        w[f"rx_{g}_upper"] = w[f"rx_{g}"] + 10 * w[f"n_suppressed_rows_{g}"]
    w = w.rename(columns={"bup_mg_oud_transmucosal": "bup_mg_oud_transmucosal"})
    # FFS / MCO split of OUD prescriptions
    oud = lt[lt.product_group.isin(["oud_transmucosal", "oud_extended"])]
    sp = oud.groupby(["state", "year", "quarter", "utilization_type"])["rx"].sum(min_count=1).unstack()
    sp = sp.rename(columns={"FFSU": "rx_oud_total_ffs", "MCOU": "rx_oud_total_mco"}).reset_index()
    w = w.merge(sp, how="left")
    w["share_rows_suppressed_oud"] = w["n_suppressed_rows_oud_total"] / w["n_rows_oud_total"]
    return w


def main():
    d = load_rows()
    d.to_csv(os.path.join(PROC, "mbat_sdud_buprenorphine_rows.csv"), index=False)
    rep = reported_cells()
    lt = long_table(d, rep)
    lt.to_csv(os.path.join(PROC, "mbat_panel_state_quarter_product.csv"), index=False, float_format="%.4f")
    w = wide_panel(lt)

    grid = pd.MultiIndex.from_product([STATES, range(2016, 2028), range(1, 5)],
                                      names=["state", "year", "quarter"]).to_frame(index=False)
    last = rep.assign(k=rep.year * 10 + rep.quarter).k.max()
    p = grid.merge(w, how="left")
    p["yq"] = p["year"].astype(str) + "Q" + p["quarter"].astype(str)
    # Quarters in the newest annual SDUD file are first-release data that CMS revises as states
    # resubmit (2026Q1 national OUD prescriptions were 14% below 2025Q4 at the pinned vintage).
    p["data_status"] = np.select(
        [p.year * 10 + p.quarter > last, p.year == last // 10],
        ["sdud_not_yet_released", "sdud_released_preliminary"], "sdud_released")
    p["sdud_mco_reported"] = p.merge(rep[rep.utilization_type == "MCOU"][["state", "year", "quarter"]].drop_duplicates()
                                     .assign(x=1), how="left")["x"].fillna(0).astype(int).values
    p = p.sort_values(["state", "year", "quarter"])
    prior = p.groupby("state")["sdud_mco_reported"].transform(lambda s: s.shift(1).rolling(4, min_periods=1).max())
    p["mco_reporting_gap"] = ((p.data_status != "sdud_not_yet_released") & (p.sdud_mco_reported == 0) & (prior == 1)).astype(int)

    enr = pd.read_csv(os.path.join(PROC, "enrollment_state_quarter.csv"))
    arc = pd.read_csv(os.path.join(PROC, "arcos_buprenorphine_state_quarter.csv"))[
        ["state", "year", "quarter", "arcos_bup_grams", "arcos_bup_grams_per_100k"]]
    cdc = pd.read_csv(os.path.join(PROC, "cdc_overdose_state_quarter.csv"))
    pol = pd.read_csv(os.path.join(PROC, "policy_state_quarter.csv"), dtype={"expansion_date": str, "unwinding_start_month": str, "unwinding_first_disenrollment_month": str,
                                                                                 "community_engagement_state_planned_start": str})
    p = p.merge(enr, how="left").merge(arc, how="left").merge(cdc, how="left").merge(pol, how="left")

    for den in ["mbes_medicaid", "pi_medicaid"]:
        tag = den.split("_")[0]
        p[f"rx_oud_per_1k_{tag}"] = p["rx_oud_total"] / p[den] * 1000
        p[f"rx_oud_transmucosal_per_1k_{tag}"] = p["rx_oud_transmucosal"] / p[den] * 1000
        p[f"rx_oud_extended_per_1k_{tag}"] = p["rx_oud_extended"] / p[den] * 1000
        p[f"bup_mg_oud_transmucosal_per_enrollee_{tag}"] = p["bup_mg_oud_transmucosal"] / p[den]

    # Flag (do not alter) abrupt quarter-over-quarter swings in OUD prescriptions; these are usually
    # state submission artifacts in SDUD (e.g. OR 2022Q3) and the values are kept as CMS published them.
    prev_rx = p.groupby("state")["rx_oud_total"].shift(1)
    chg = p["rx_oud_total"] / prev_rx - 1
    p["qoq_anomaly_flag"] = ((prev_rx > 1000) & (chg.abs() > 0.5)).astype(int)
    first = ["state", "year", "quarter", "yq", "data_status", "sdud_mco_reported", "mco_reporting_gap", "qoq_anomaly_flag"]
    p = p[first + [c for c in p.columns if c not in first]]
    p.to_csv(os.path.join(PROC, "mbat_panel_state_quarter.csv"), index=False, float_format="%.4f")
    rel = p[p.data_status != "sdud_not_yet_released"]
    print(f"panel: {len(p)} rows x {p.shape[1]} cols; released state-quarters {len(rel)} (through {last // 10}Q{last % 10})")
    print(f"included SDUD rows: {len(d):,} ({int(d.suppressed.sum()):,} suppressed)")
    print("mco_reporting_gap:", p.loc[p.mco_reporting_gap == 1, ["state", "yq"]].astype(str).agg(" ".join, axis=1).tolist())
    print("released but rx_oud_total NA:", int(rel.rx_oud_total.isna().sum()))
    print("national OUD rx by year:", rel.groupby("year")["rx_oud_total"].sum().round(0).astype(int).to_dict())


if __name__ == "__main__":
    main()
