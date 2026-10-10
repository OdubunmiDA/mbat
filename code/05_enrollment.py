#!/usr/bin/env python3
"""Step 05 - Quarterly Medicaid enrollment denominators by state.

Two CMS series are kept side by side because neither covers the whole panel:

  PI   Medicaid & CHIP Performance Indicator dataset (Sept 2026 release).
       Monthly "Total Medicaid Enrollment" and "Total Medicaid and CHIP Enrollment",
       2017-06 onward (a single 2013-09 baseline month is ignored). Where a state-month has both
       a preliminary (P) and an updated (U) report, the updated report is used.
       Also supplies CMS's monthly "State Expanded Medicaid" (Y/N) flag.
  MBES Medicaid Enrollment - New Adult Group (Feb 2026 release), from CMS-64 / MBES.
       Monthly "Total Medicaid Enrollees" and "Total VIII Group Enrollees", 2014-01 to 2025-06.
       Where CMS republished a state-month, the latest update (Updated Year/Month) is used.

Quarterly value = mean of the available months in the quarter; the number of months is kept
so a reader can drop partial quarters. Output: data/processed/enrollment_state_quarter.csv
"""
import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "enrollment")
OUT = os.path.join(ROOT, "data", "processed", "enrollment_state_quarter.csv")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from states import NAME_TO_ABBR, STATES, norm_name  # noqa: E402


def num(s):
    return pd.to_numeric(s.astype(str).str.replace(",", "").str.strip(), errors="coerce")


def pi_series():
    p = pd.read_csv(os.path.join(RAW, "pi-dataset-september-2026-release.csv"), low_memory=False)
    p = p[p["Reporting Period"] >= 201701].copy()
    p["state"] = p["State Abbreviation"].str.strip()
    p["year"] = p["Reporting Period"] // 100
    p["month"] = p["Reporting Period"] % 100
    p["rank"] = (p["Preliminary or Updated"] == "U").astype(int)
    p = p.sort_values("rank").groupby(["state", "year", "month"], as_index=False).last()
    p["pi_medicaid"] = num(p["Total Medicaid Enrollment"])
    p["pi_medicaid_chip"] = num(p["Total Medicaid and CHIP Enrollment"])
    p["pi_expanded"] = (p["State Expanded Medicaid"].str.strip() == "Y").astype(int)
    p["pi_report_type"] = p["Preliminary or Updated"]
    return p[["state", "year", "month", "pi_medicaid", "pi_medicaid_chip", "pi_expanded", "pi_report_type"]]


def mbes_series():
    m = pd.read_csv(os.path.join(RAW, "medicaid-enrollment-new-adult-group-02052026.csv"))
    m["name"] = m["State"].map(norm_name)
    m = m[m["name"].isin(NAME_TO_ABBR)].copy()
    m["state"] = m["name"].map(NAME_TO_ABBR)
    m["year"], m["month"] = m["Enrollment Year"], m["Enrollment Month"]
    m["upd"] = m["Updated Year"] * 100 + m["Updated Month"]
    m = m.sort_values("upd").groupby(["state", "year", "month"], as_index=False).last()
    m["mbes_medicaid"] = num(m["Total Medicaid Enrollees"])
    m["mbes_viii_group"] = num(m["Total VIII Group Enrollees"])
    return m[["state", "year", "month", "mbes_medicaid", "mbes_viii_group"]]


def quarterly(df, cols):
    df = df.copy()
    df["quarter"] = (df["month"] - 1) // 3 + 1
    g = df.groupby(["state", "year", "quarter"])
    out = g[cols].mean()
    for c in cols:
        out[c + "_months"] = g[c].count()
    return out.reset_index()


def main():
    pi = pi_series()
    mb = mbes_series()
    piq = quarterly(pi, ["pi_medicaid", "pi_medicaid_chip"])
    piq["pi_expanded_any_month"] = quarterly(pi, ["pi_expanded"])["pi_expanded"].gt(0).astype(int).values
    mbq = quarterly(mb, ["mbes_medicaid", "mbes_viii_group"])
    grid = pd.MultiIndex.from_product([STATES, range(2016, 2028), range(1, 5)],
                                      names=["state", "year", "quarter"]).to_frame(index=False)
    out = grid.merge(mbq, how="left").merge(piq, how="left")
    for c in out.columns:
        if c.endswith("_months"):
            out[c] = out[c].fillna(0).astype(int)
    out.to_csv(OUT, index=False, float_format="%.1f")
    have = lambda c: out.loc[out[c].notna(), ["year", "quarter"]].astype(str).agg("Q".join, axis=1)
    for c in ["mbes_medicaid", "pi_medicaid"]:
        h = have(c)
        print(f"{c}: {out[c].notna().sum()} state-quarters, {h.min()} to {h.max()}")
    print(f"PI months used: {len(pi)} ({(pi.pi_report_type == 'P').sum()} preliminary)")


if __name__ == "__main__":
    main()
