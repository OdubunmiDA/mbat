#!/usr/bin/env python3
"""Step 10 - Independent reconciliation of panel totals against the raw CMS SDUD files.

This deliberately does NOT read the step 03 candidate files. For each spot-check state-quarter
it re-reads the raw annual SDUD file, keeps rows whose NDC is an included crosswalk NDC, and sums
prescriptions by product group. The result must equal the panel exactly; any difference means
the pipeline lost or double-counted rows.

Spot checks (written to data/interim/qa/spot_checks.csv on first run, then reused):
  named: chosen to cover easy, hard, and extreme cases (see NAMED below)
  random: 5 released state-quarters drawn with a fixed seed
Resumable by year: python code/10_reconcile.py [--years 2018 2019 ...]
"""
import argparse
import csv
import glob
import json
import os
import re

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "sdud")
PROC = os.path.join(ROOT, "data", "processed")
QA = os.path.join(ROOT, "data", "interim", "qa")
SEED = 20261008
NAMED = [  # (state, year, quarter, why)
    ("NV", 2022, 2, "author's home Medicaid program (Nevada)"),
    ("FL", 2025, 4, "large state, managed-care dominated"),
    ("WY", 2018, 1, "small state, FFS only"),
    ("KY", 2019, 3, "high-volume state"),
    ("VT", 2019, 2, "highest rate per 1,000 enrollees in the panel"),
    ("DC", 2023, 1, "heavy suppression"),
    ("PA", 2026, 1, "preliminary quarter with a large drop from 2025Q4"),
]


def spot_checks():
    path = os.path.join(QA, "spot_checks.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    p = pd.read_csv(os.path.join(PROC, "mbat_panel_state_quarter.csv"))
    rel = p[p.data_status != "sdud_not_yet_released"]
    named_keys = {(s, y, q) for s, y, q, _ in NAMED}
    pool = rel[~rel.apply(lambda r: (r.state, r.year, r.quarter) in named_keys, axis=1)]
    rnd = pool.sample(5, random_state=SEED)
    rows = [{"state": s, "year": y, "quarter": q, "kind": "named", "why": w} for s, y, q, w in NAMED]
    rows += [{"state": r.state, "year": int(r.year), "quarter": int(r.quarter), "kind": "random",
              "why": f"random draw, seed {SEED}"} for r in rnd.itertuples()]
    sc = pd.DataFrame(rows)
    os.makedirs(QA, exist_ok=True)
    sc.to_csv(path, index=False)
    return sc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="*", type=int)
    a = ap.parse_args()
    sc = spot_checks()
    xw = pd.read_csv(os.path.join(PROC, "ndc_crosswalk.csv"), dtype={"ndc11": str})
    grp = dict(zip(xw[xw.include == 1].ndc11, xw[xw.include == 1].product_group))
    files = {int(re.search(r"(20\d\d)", os.path.basename(f)).group(1)): f for f in glob.glob(os.path.join(RAW, "*.csv"))}
    for year in sorted(sc.year.unique()):
        if a.years and year not in a.years:
            continue
        out = os.path.join(QA, f"recon_{year}.json")
        if os.path.exists(out):
            print(f"{year}: done")
            continue
        want = {(r.state, str(r.quarter)) for r in sc[sc.year == year].itertuples()}
        tot = {}
        with open(files[year], newline="", encoding="utf-8", errors="replace") as f:
            rd = csv.reader(f)
            next(rd)
            for row in rd:
                k = (row[1].strip(), row[7].strip())
                if k not in want:
                    continue
                g = grp.get(row[2].strip().zfill(11))
                if not g:
                    continue
                t = tot.setdefault(f"{k[0]}|{k[1]}", {"oud_transmucosal": 0.0, "oud_extended": 0.0, "pain": 0.0, "suppressed_rows": 0})
                if row[8].strip().lower() == "true":
                    t["suppressed_rows"] += 1
                elif row[11].strip():
                    t[g] += float(row[11])
        json.dump(tot, open(out, "w"), indent=1)
        print(f"{year}: {tot}")


if __name__ == "__main__":
    main()
