#!/usr/bin/env python3
"""Step 02 - Build the reference list of buprenorphine NDCs from the FDA NDC Directory.

Inputs  (data/raw/ndc_reference/):
  fda_ndctext.zip        FDA NDC Directory, current listings (product.txt, package.txt)
  fda_ndc_excluded.zip   FDA NDC Directory, excluded/expired listings
Outputs (data/raw/ndc_reference/):
  fda_bup_packages.csv     one row per buprenorphine package NDC (outer and inner packages)
  reference_bup_ndcs.txt   the 11-digit NDCs, one per line (read by step 03)

Package descriptions name inner-package NDCs as well, e.g.
"4 POUCH in 1 CARTON (0093-3600-40) / 1 PATCH in 1 POUCH (0093-3600-21)". Pharmacies
sometimes bill the inner NDC, so both levels are listed.

The FDA directory does not cover every NDC that appears in older SDUD quarters, because
discontinued listings eventually drop out of both files. Step 03 therefore also matches on
product name, and step 04 checks every candidate against RxNorm.
"""
import csv
import io
import os
import re
import zipfile
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(ROOT, "data", "raw", "ndc_reference")
INNER = re.compile(r"\((\d{4,5}-\d{3,4}-\d{1,2})\)")


def ndc11(code):
    """Convert a hyphenated FDA package NDC (4-4-2, 5-3-2, or 5-4-1) to 11 digits (5-4-2)."""
    a, b, c = code.split("-")
    return a.zfill(5) + b.zfill(4) + c.zfill(2)


def read_tsv(z, name):
    with z.open(name) as f:
        return list(csv.DictReader(io.TextIOWrapper(f, encoding="latin-1"), delimiter="\t"))


def is_bup(p):
    # Excluded listings often leave SUBSTANCENAME blank, so names are checked too.
    text = " ".join(p.get(k) or "" for k in ("SUBSTANCENAME", "PROPRIETARYNAME", "NONPROPRIETARYNAME"))
    return "BUPRENORPH" in text.upper()


def main():
    sources = [("fda_ndctext.zip", "product.txt", "package.txt", "current"),
               ("fda_ndc_excluded.zip", "Products_excluded.txt", "Packages_excluded.txt", "excluded")]
    rows = {}
    for zname, prod, pack, status in sources:
        z = zipfile.ZipFile(os.path.join(REF, zname))
        products = {p["PRODUCTID"]: p for p in read_tsv(z, prod) if is_bup(p)}
        for k in read_tsv(z, pack):
            p = products.get(k["PRODUCTID"])
            if not p or not k["NDCPACKAGECODE"]:
                continue
            codes = [k["NDCPACKAGECODE"]] + INNER.findall(k["PACKAGEDESCRIPTION"])
            for code in dict.fromkeys(codes):
                n = ndc11(code)
                if n in rows:  # first listing wins; current files are read before excluded
                    continue
                rows[n] = {
                    "ndc11": n, "fda_listing": status,
                    "package_level": "outer" if code == k["NDCPACKAGECODE"] else "inner",
                    "proprietary_name": p["PROPRIETARYNAME"], "nonproprietary_name": p["NONPROPRIETARYNAME"],
                    "dosage_form": p["DOSAGEFORMNAME"], "route": p["ROUTENAME"],
                    "substances": p["SUBSTANCENAME"], "strengths": p["ACTIVE_NUMERATOR_STRENGTH"],
                    "strength_units": p["ACTIVE_INGRED_UNIT"], "labeler": p["LABELERNAME"],
                    "application": p["APPLICATIONNUMBER"], "package_description": k["PACKAGEDESCRIPTION"].strip(),
                    "start_marketing": k.get("STARTMARKETINGDATE") or p["STARTMARKETINGDATE"],
                    "end_marketing": k.get("ENDMARKETINGDATE") or p["ENDMARKETINGDATE"],
                }
    out = sorted(rows.values(), key=lambda r: r["ndc11"])
    with open(os.path.join(REF, "fda_bup_packages.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    with open(os.path.join(REF, "reference_bup_ndcs.txt"), "w") as f:
        f.write("# Buprenorphine package NDCs (11-digit) from the FDA NDC Directory; built by code/02_reference_ndcs.py\n")
        f.writelines(r["ndc11"] + "\n" for r in out)
    print(f"{len(out)} buprenorphine NDCs:", dict(Counter((r["fda_listing"], r["package_level"]) for r in out)))


if __name__ == "__main__":
    main()
