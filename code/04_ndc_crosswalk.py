#!/usr/bin/env python3
"""Step 04 - Classify every candidate NDC from step 03 into the MBAT NDC crosswalk.

Authority for each NDC is its NLM RxNorm concept (RxNav ndcstatus), which resolves
current and obsolete NDCs to a clinical drug name such as
"buprenorphine 8 MG / naloxone 2 MG Sublingual Film". The FDA NDC Directory attributes
from step 02 are attached for cross-checking.

Inputs:
  data/interim/sdud/sdud_<year>_bup_candidates.csv     (step 03)
  data/raw/ndc_reference/rxnav_ndcstatus_cache.json    (RxNav responses; fetched if missing)
  data/raw/ndc_reference/fda_bup_packages.csv          (step 02)
  data/raw/ndc_reference/author_verification.csv   the author's sign-off per NDC (method, note,
                                                   initials/date); merged in so it survives re-runs
Output:
  data/processed/ndc_crosswalk.csv   one row per candidate NDC, with include flag, product
                                     group, form, mg per unit, and a needs_review flag

Classification rules (the author rules on these; see docs/VERIFY_CHECKLIST.md, V1-V3):
  - Not buprenorphine in RxNorm  -> include = 0 (bupivacaine, bupropion, Bupap, Buphenyl, ...)
  - Sublingual tablet or film, or buccal film containing naloxone (Bunavail)
                                 -> oud_transmucosal
  - Extended-release prefilled syringe (Sublocade, Brixadi) or implant (Probuphine)
                                 -> oud_extended
  - Transdermal system (Butrans and generics), buccal film without naloxone (Belbuca and
    generics), 0.3 mg/mL injection (Buprenex and generics)
                                 -> pain (reported separately, excluded from OUD measures)
"""
import csv
import glob
import json
import os
import re
import statistics
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INTERIM = os.path.join(ROOT, "data", "interim", "sdud")
REF = os.path.join(ROOT, "data", "raw", "ndc_reference")
OUT = os.path.join(ROOT, "data", "processed")
CACHE = os.path.join(REF, "rxnav_ndcstatus_cache.json")
RXNAV = "https://rxnav.nlm.nih.gov/REST/ndcstatus.json?ndc={}"


def load_candidates():
    c = {}
    for f in sorted(glob.glob(os.path.join(INTERIM, "sdud_*_bup_candidates.csv"))):
        for r in csv.DictReader(open(f, newline="")):
            e = c.setdefault(r["ndc"], {"names": {}, "years": set(), "rows": 0, "upr": []})
            nm = r["product_name"].strip()
            e["names"][nm] = e["names"].get(nm, 0) + 1
            e["years"].add(int(r["year"]))
            e["rows"] += 1
            try:
                u, n = float(r["units_reimbursed"]), float(r["number_of_prescriptions"])
                if n > 0:
                    e["upr"].append(u / n)
            except ValueError:
                pass  # suppressed rows carry no counts
    return c


def load_rxnav(ndcs):
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {"results": {}}
    missing = [n for n in ndcs if n not in cache["results"]]
    if missing:
        print(f"fetching {len(missing)} NDCs from RxNav", file=sys.stderr)
        for n in missing:
            with urllib.request.urlopen(RXNAV.format(n), timeout=30) as resp:
                cache["results"][n] = json.load(resp)["ndcStatus"]
            time.sleep(0.06)  # RxNav asks for <= 20 requests per second
        cache["retrieved_utc_updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        json.dump(cache, open(CACHE, "w"), indent=1)
    return cache


FORM_PATTERNS = [
    ("Sublingual Tablet", "sublingual_tablet"), ("Sublingual Film", "sublingual_film"),
    ("Buccal Film", "buccal_film"), ("Prefilled Syringe", "er_injection"),
    ("Drug Implant", "implant"), ("Transdermal System", "transdermal"),
    ("Injection", "injection_0.3mg_ml"), ("Cartridge", "injection_0.3mg_ml"),
]
BRAND = re.compile(r"\[([^\]]+)\]")
BUP_MG = re.compile(r"buprenorphine ([\d.]+) MG(?!/)")


def classify(concept):
    """Return (include, ingredient, form, group, mg_per_unit, brand) from an RxNorm concept name."""
    if not concept or "buprenorphine" not in concept.lower():
        return 0, "", "", "not_buprenorphine", "", ""
    ingredient = "buprenorphine_naloxone" if "naloxone" in concept.lower() else "buprenorphine"
    form = next((f for pat, f in FORM_PATTERNS if pat in concept), "unrecognized")
    brand = (BRAND.search(concept).group(1) if BRAND.search(concept) else "")
    if form in ("sublingual_tablet", "sublingual_film"):
        group = "oud_transmucosal"
    elif form == "buccal_film":
        group = "oud_transmucosal" if ingredient == "buprenorphine_naloxone" else "pain"
    elif form in ("er_injection", "implant"):
        group = "oud_extended"
    elif form in ("transdermal", "injection_0.3mg_ml"):
        group = "pain"
    else:
        group = "unclassified"
    mg = ""
    if group == "oud_transmucosal":
        m = BUP_MG.search(concept)
        mg = m.group(1) if m else ""
    return 1, ingredient, form, group, mg, brand


def main():
    os.makedirs(OUT, exist_ok=True)
    cands = load_candidates()
    rx = load_rxnav(sorted(cands))
    fda = {r["ndc11"]: r for r in csv.DictReader(open(os.path.join(REF, "fda_bup_packages.csv")))}
    av_path = os.path.join(REF, "author_verification.csv")
    av = {r["ndc11"]: r for r in csv.DictReader(open(av_path))} if os.path.exists(av_path) else {}
    rows = []
    for ndc in sorted(cands):
        e = cands[ndc]
        s = rx["results"].get(ndc, {})
        concept = s.get("conceptName") or ""
        inc, ingr, form, group, mg, brand = classify(concept)
        f = fda.get(ndc, {})
        upr = statistics.median(e["upr"]) if e["upr"] else ""
        reasons = []
        if not concept:
            reasons.append("no RxNorm concept")
        if inc and group in ("unclassified",):
            reasons.append("form not recognized")
        if inc and group == "oud_transmucosal" and not mg:
            reasons.append("mg per unit not parsed")
        if inc and not f:
            reasons.append("not in FDA NDC Directory files")
        if inc and f and "BUPRENORPH" not in (f.get("substances", "") + f.get("proprietary_name", "")).upper():
            reasons.append("FDA substance disagrees")
        if not inc and f:
            reasons.append("FDA lists buprenorphine but RxNorm does not")
        if inc and group == "oud_transmucosal" and upr != "" and not (1 <= upr <= 120):
            reasons.append(f"median units/rx {upr:.1f} outside 1-120")
        if inc and group == "oud_extended" and upr != "" and upr > 5:
            reasons.append(f"median units/rx {upr:.1f} > 5 for injectable")
        rows.append({
            "ndc11": ndc, "include": inc, "product_group": group, "ingredient": ingr,
            "form": form, "brand": brand, "bup_mg_per_unit": mg,
            "rxnorm_concept": concept, "rxcui": s.get("rxcui", ""), "rxnorm_ndc_status": s.get("status", ""),
            "fda_listing": f.get("fda_listing", "not_found"), "fda_package_level": f.get("package_level", ""),
            "fda_proprietary_name": f.get("proprietary_name", ""),
            "fda_dosage_form": f.get("dosage_form", ""), "fda_labeler": f.get("labeler", ""),
            "sdud_product_names": " | ".join(sorted(e["names"], key=lambda k: -e["names"][k])),
            "sdud_first_year": min(e["years"]), "sdud_last_year": max(e["years"]), "sdud_rows": e["rows"],
            "median_units_per_rx": f"{upr:.2f}" if upr != "" else "",
            "needs_review": int(bool(reasons)), "review_reason": "; ".join(reasons),
            "verification_method": av.get(ndc, {}).get("check_method", ""),
            "verification_note": av.get(ndc, {}).get("note", ""),
            "author_verified": av.get(ndc, {}).get("author_verified", ""),
        })
    with open(os.path.join(OUT, "ndc_crosswalk.csv"), "w", newline="") as fo:
        w = csv.DictWriter(fo, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    from collections import Counter
    print(f"{len(rows)} candidate NDCs; RxNorm version {rx.get('version', {}).get('version', '?')}")
    print("by group:", dict(Counter(r["product_group"] for r in rows)))
    print("needs_review:", sum(r["needs_review"] for r in rows),
          "| reviewed and signed by author:", sum(1 for r in rows if r["needs_review"] and r["author_verified"]))
    for r in rows:
        if r["needs_review"] and not r["author_verified"]:
            print(f"  {r['ndc11']} {r['product_group']:17} {r['rxnorm_concept'][:60]:60} | {r['review_reason']}")


if __name__ == "__main__":
    main()
