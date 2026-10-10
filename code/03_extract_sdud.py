#!/usr/bin/env python3
"""Step 03 - Extract buprenorphine candidate rows from the CMS SDUD annual files.

For each SDUD year file in data/raw/sdud/ this writes, to data/interim/sdud/:
  sdud_<year>_bup_candidates.csv   every row whose NDC is a buprenorphine candidate
  sdud_<year>_ndc_index.csv        every distinct NDC in the file with its product names,
                                   row count, and quarters seen (used to audit the crosswalk)
  sdud_<year>_state_quarter_rows.csv  rows per state x quarter x utilization type for ALL drugs,
                                   so a state-quarter CMS did not report is distinguishable
                                   from one with zero buprenorphine

A row is a candidate when EITHER
  (a) its product name matches the broad pattern in NAME_PATTERN, OR
  (b) its NDC appears in data/raw/ndc_reference/reference_bup_ndcs.txt (NDCs that the
      FDA NDC Directory or RxNorm lists with buprenorphine as an active ingredient).
Candidates are confirmed or rejected in step 04 (the NDC crosswalk); nothing here decides
what counts as buprenorphine.

Years already processed are skipped unless --force is given, so the step can be resumed.
Usage:  python code/03_extract_sdud.py [--years 2016 2017 ...] [--force]
"""
import argparse
import collections
import csv
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "sdud")
REF = os.path.join(ROOT, "data", "raw", "ndc_reference", "reference_bup_ndcs.txt")
OUT = os.path.join(ROOT, "data", "interim", "sdud")

# Broad on purpose: SDUD product names are truncated to 10 characters and inconsistently
# spelled (e.g. "BUPRENORPH", "Buprenofph", "BUPREN&NAL", "BUP/NAL 8M"). "BUP" must start a
# word so that IBUPROFEN and NEBUPENT do not match; BUPROPION and BUPIVACAINE are excluded.
NAME_PATTERN = re.compile(
    r"(?<![A-Z])BUP(?!ROP|IV)|SUBOX|SUBUT|ZUBSOL|BUNAV|SUBLOC|BRIXAD|PROBUPH|BELBUC|BUTRAN",
    re.I,
)

HEADER = ["utilization_type", "state", "ndc", "labeler_code", "product_code", "package_size",
          "year", "quarter", "suppression_used", "product_name", "units_reimbursed",
          "number_of_prescriptions", "total_amount_reimbursed", "medicaid_amount_reimbursed",
          "non_medicaid_amount_reimbursed"]


def load_reference():
    if not os.path.exists(REF):
        print(f"note: {os.path.relpath(REF, ROOT)} not found; using name pattern only", file=sys.stderr)
        return set()
    with open(REF) as f:
        return {line.strip() for line in f if line.strip() and not line.startswith("#")}


def year_of(path):
    m = re.search(r"(20\d\d)", os.path.basename(path))
    return int(m.group(1))


def process(path, ref_ndcs):
    year = year_of(path)
    cand_path = os.path.join(OUT, f"sdud_{year}_bup_candidates.csv")
    index_path = os.path.join(OUT, f"sdud_{year}_ndc_index.csv")
    index = {}
    sq = collections.Counter()
    n_rows = n_cand = 0
    with open(path, newline="", encoding="utf-8", errors="replace") as fin, \
            open(cand_path + ".tmp", "w", newline="") as fout:
        reader = csv.reader(fin)
        header = next(reader)
        if [h.strip().lower().replace(" ", "_") for h in header] != HEADER:
            sys.exit(f"{path}: unexpected header {header}")
        w = csv.writer(fout)
        w.writerow(HEADER + ["source_file"])
        src = os.path.basename(path)
        for row in reader:
            n_rows += 1
            ndc = row[2].strip().zfill(11)
            name = row[9].strip()
            e = index.get(ndc)
            if e is None:
                e = index[ndc] = [collections.Counter(), 0, set()]
            e[0][name] += 1
            e[1] += 1
            e[2].add(f"{row[6]}Q{row[7]}")
            sq[(row[1].strip(), row[6], row[7], row[0].strip())] += 1
            if ndc in ref_ndcs or NAME_PATTERN.search(name):
                row[2] = ndc
                w.writerow(row + [src])
                n_cand += 1
    os.replace(cand_path + ".tmp", cand_path)
    with open(index_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ndc", "year", "n_rows", "quarters", "product_names"])
        for ndc in sorted(index):
            names, n, qs = index[ndc]
            w.writerow([ndc, year, n, ";".join(sorted(qs)), " | ".join(f"{k}" for k, _ in names.most_common())])
    with open(os.path.join(OUT, f"sdud_{year}_state_quarter_rows.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["state", "year", "quarter", "utilization_type", "n_rows_all_drugs"])
        for k in sorted(sq):
            w.writerow(list(k) + [sq[k]])
    print(f"{year}: {n_rows:,} rows read, {n_cand:,} candidate rows, {len(index):,} distinct NDCs")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="*", type=int)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    ref = load_reference()
    files = sorted(glob.glob(os.path.join(RAW, "*.csv")), key=year_of)
    for p in files:
        y = year_of(p)
        if a.years and y not in a.years:
            continue
        done = os.path.join(OUT, f"sdud_{y}_ndc_index.csv")
        if os.path.exists(done) and not a.force:
            print(f"{y}: already extracted (use --force to redo)")
            continue
        process(p, ref)


if __name__ == "__main__":
    main()
