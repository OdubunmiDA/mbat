#!/usr/bin/env python3
"""Step 06 - Extract buprenorphine (DEA drug code 9064) from the ARCOS Retail Drug Summary PDFs.

For each annual report in data/raw/arcos/ this converts the PDF to layout text with
poppler's `pdftotext -layout` (cached in data/interim/arcos/) and reads two tables:
  Report 2  Retail drug distribution by state within drug code   -> grams, by quarter
  Report 3  Quarterly distribution by state per 100K population  -> grams per 100,000 population

Output: data/processed/arcos_buprenorphine_state_quarter.csv
  state_name, state, year, quarter, arcos_bup_grams, arcos_bup_grams_per_100k,
  source_file, source_page_line (line in the cached text, for checking against the PDF)

Every row is checked: the four quarters must sum to the TOTAL GRAMS column within 0.05 g
(rounding in the PDF); failures are printed and written to the QA log.

Coverage note: the 2024 and 2025 Retail Drug Summary reports published by DEA do not include
drug code 9064, so ARCOS buprenorphine ends at 2023Q4 in MBAT.
"""
import csv
import glob
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "arcos")
TXT = os.path.join(ROOT, "data", "interim", "arcos")
OUT = os.path.join(ROOT, "data", "processed", "arcos_buprenorphine_state_quarter.csv")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from states import NAME_TO_ABBR  # noqa: E402

REPORT = re.compile(r"REPORT 0?([1-7])\b")
DRUG = re.compile(r"DRUG(?: CODE)?:\s*(\d{4})")
NUM = r"([\d,]+(?:\.\d+)?)"
ROW = re.compile(r"^\s*([A-Z][A-Z .]+?)\s{2,}" + r"\s+".join([NUM] * 5) + r"\s*$")


def to_text(pdf):
    os.makedirs(TXT, exist_ok=True)
    txt = os.path.join(TXT, os.path.basename(pdf).replace(".pdf", ".txt"))
    if not os.path.exists(txt) or os.path.getmtime(txt) < os.path.getmtime(pdf):
        subprocess.run(["pdftotext", "-layout", pdf, txt], check=True)
    return txt


def parse(txt, year):
    report = drug = None
    found, problems = {}, []
    for i, line in enumerate(open(txt, encoding="utf-8", errors="replace"), start=1):
        m = REPORT.search(line)
        if m:
            report = int(m.group(1))
        m = DRUG.search(line)
        if m:
            drug = m.group(1)
            continue
        if report not in (2, 3) or drug != "9064":
            continue
        m = ROW.match(line)
        if not m:
            continue
        name = m.group(1).strip()
        if name not in NAME_TO_ABBR:
            continue  # territories, US TOTAL, and other non-state rows
        q = [float(x.replace(",", "")) for x in m.group(2, 3, 4, 5)]
        total = float(m.group(6).replace(",", ""))
        key = (report, name)
        if key in found:
            if found[key][0] != q:
                problems.append(f"{year} report {report} {name}: repeated with different values (line {i})")
            continue
        if abs(sum(q) - total) > 0.05 + 1e-6 * total:
            problems.append(f"{year} report {report} {name}: quarters sum {sum(q):.2f} != total {total:.2f} (line {i})")
        found[key] = (q, i)
    return found, problems


def main():
    rows, problems = [], []
    for pdf in sorted(glob.glob(os.path.join(RAW, "report_yr_*.pdf"))):
        year = int(re.search(r"(\d{4})", os.path.basename(pdf)).group(1))
        found, probs = parse(to_text(pdf), year)
        problems += probs
        n2 = sum(1 for k in found if k[0] == 2)
        n3 = sum(1 for k in found if k[0] == 3)
        print(f"{year}: report 2 states={n2}, report 3 states={n3}")
        if n2 == 0:
            continue  # drug code 9064 not published in this year's summary
        for name, abbr in NAME_TO_ABBR.items():
            g, line2 = found.get((2, name), ([None] * 4, ""))
            p, _ = found.get((3, name), ([None] * 4, ""))
            if line2 == "":
                problems.append(f"{year} {name}: missing from report 2")
            for qi in range(4):
                rows.append({"state_name": name, "state": abbr, "year": year, "quarter": qi + 1,
                             "arcos_bup_grams": g[qi], "arcos_bup_grams_per_100k": p[qi],
                             "source_file": os.path.basename(pdf), "source_text_line": line2})
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(ROOT, "data", "interim", "arcos", "arcos_parse_problems.txt"), "w") as f:
        f.write("\n".join(problems) + ("\n" if problems else "none\n"))
    print(f"{len(rows)} state-quarter rows written; {len(problems)} parse problems")
    for p in problems[:20]:
        print("  ", p)


if __name__ == "__main__":
    main()
