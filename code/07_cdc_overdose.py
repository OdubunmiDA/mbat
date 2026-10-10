#!/usr/bin/env python3
"""Step 07 - CDC NCHS provisional overdose deaths, aligned to state-quarters.

Source: VSRR Provisional Drug Overdose Death Counts (data.cdc.gov xkb8-kh2a). Every value in
this source is a 12-month-ending count. MBAT takes the value for the last month of each
quarter (March, June, September, December), so the quarter's value is deaths in the 12 months
ending that quarter. Quarterly death counts cannot be derived exactly from this source.

New York: CDC reports "NY" (New York State excluding New York City) and "YC" (New York City)
separately. MBAT's NY = NY + YC; if either piece is missing the sum is left missing.

Indicators kept: all drug overdose deaths; opioids (T40.0-T40.4, T40.6); synthetic opioids
other than methadone (T40.4). Both reported ("data value") and predicted values are kept.
Output: data/processed/cdc_overdose_state_quarter.csv
"""
import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "raw", "cdc", "VSRR_xkb8-kh2a_export_2026-10-08.csv")
OUT = os.path.join(ROOT, "data", "processed", "cdc_overdose_state_quarter.csv")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from states import STATES  # noqa: E402

INDICATORS = {
    "Number of Drug Overdose Deaths": "od_all",
    "Opioids (T40.0-T40.4,T40.6)": "od_opioid",
    "Synthetic opioids, excl. methadone (T40.4)": "od_synthetic",
}
QEND = {"March": 1, "June": 2, "September": 3, "December": 4}


def main():
    d = pd.read_csv(SRC, low_memory=False)
    d = d[d["Indicator"].isin(INDICATORS) & d["Month"].isin(QEND)].copy()
    d["quarter"] = d["Month"].map(QEND)
    d["var"] = d["Indicator"].map(INDICATORS)
    for c in ["Data Value", "Predicted Value"]:
        d[c] = pd.to_numeric(d[c].astype(str).str.replace(",", ""), errors="coerce")
    d["State"] = d["State"].replace({"YC": "NYC"})
    long = d.melt(id_vars=["State", "Year", "quarter", "var"], value_vars=["Data Value", "Predicted Value"],
                  var_name="kind", value_name="v")
    long["col"] = long["var"] + "_12mo_" + long["kind"].map({"Data Value": "reported", "Predicted Value": "predicted"})
    w = long.pivot_table(index=["State", "Year", "quarter"], columns="col", values="v", aggfunc="first")
    # New York = NY (excl. NYC) + NYC; min_count=2 leaves the sum missing if either part is missing
    ny = w.loc[["NY", "NYC"]].groupby(level=["Year", "quarter"]).sum(min_count=2)
    ny["State"] = "NY"
    ny = ny.reset_index().set_index(["State", "Year", "quarter"])
    w = pd.concat([w.drop(index=["NY", "NYC"], level=0), ny])
    w = w.reset_index().rename(columns={"State": "state", "Year": "year"})
    w = w[w["state"].isin(STATES)]
    pc = d[d["var"] == "od_all"].groupby(["State", "Year", "quarter"])["Percent Complete"].min()
    pc = pc.rename("cdc_percent_complete").reset_index().rename(columns={"State": "state", "Year": "year"})
    w = w.merge(pc, how="left")
    w.to_csv(OUT, index=False)
    last = w.dropna(subset=["od_all_12mo_reported"]).sort_values(["year", "quarter"]).iloc[-1]
    print(f"{len(w)} state-quarters, {w.year.min()}Q1 to {int(last.year)}Q{int(last.quarter)}; "
          f"missing od_opioid reported: {w['od_opioid_12mo_reported'].isna().sum()}")


if __name__ == "__main__":
    main()
