#!/usr/bin/env python3
"""Step 08 - Dated policy annotations, as events and as state-quarter indicators.

Inputs:
  data/raw/policy/policy_events_manual.csv   hand-compiled events, one citation per row
  data/raw/policy/cms_updated-renewal-outcomes-october-2024-releasefinal.csv
      CMS Medicaid and CHIP Updated Renewal Outcomes; each state's unwinding start is derived
      as the first reporting month with any terminations (Metric 5b + 5c > 0).
  data/raw/enrollment/medicaid-enrollment-new-adult-group-02052026.csv
      CMS notes of the form "<State> expanded ... by adopting the VIII Group on <date>", used
      only to cross-check the KFF expansion dates.
Outputs:
  data/processed/policy_annotations.csv       every event (manual + derived), with citation
  data/processed/policy_state_quarter.csv     indicators for 51 states x 2016Q1-2027Q4
  data/interim/policy/expansion_date_crosscheck.csv

Indicator conventions (see docs/CODEBOOK.md):
  An event "in effect" in a quarter means its start date is on or before the quarter's last day
  and its end date (if any) is on or after the quarter's first day. *_mid_quarter = 1 when the
  start date falls after the first day of that quarter (partial exposure).
  mandatory_moud_benefit is 0 for states with a documented exemption (Hawaii, South Dakota,
  Wyoming; 2020-10-01 to 2025-09-30) and blank after the exemption window until their
  re-certification status under section 1905(ee)(2) is confirmed.
  Prior-authorization and dose-cap columns exist but are empty in v1.0: no dated 50-state source
  for Medicaid-specific buprenorphine PA or dose limits was found (see docs/NEXT_STEPS.md).
"""
import os
import re
import sys
from datetime import date

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
PROC = os.path.join(ROOT, "data", "processed")
INT = os.path.join(ROOT, "data", "interim", "policy")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from states import NAME_TO_ABBR, STATES, norm_name  # noqa: E402

RENEWAL = os.path.join(RAW, "policy", "cms_updated-renewal-outcomes-october-2024-releasefinal.csv")
RENEWAL_URL = "https://download.medicaid.gov/data/updated-renewal-outcomes-october-2024-releasefinal.csv"
MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july",
                                       "august", "september", "october", "november", "december"], 1)}


# Months from the first termination reporting month (renewal due) to the first month without
# coverage. Checked against CMS, "2023 State Timelines for Initiating Unwinding-Related Renewals"
# (2023-06-29) for the states in CHECKED; the 1-month lag is assumed for all other states.
DISENROLL_LAG = {"OR": 3}
CHECKED = {"ID", "NH", "OK", "SD", "AZ", "FL", "KY", "NV", "CA", "NY", "OR"}


def add_months(iso, k):
    y, m = int(iso[:4]), int(iso[5:7]) + k
    y, m = y + (m - 1) // 12, (m - 1) % 12 + 1
    return f"{y}-{m:02d}-01"


def unwinding_starts():
    d = pd.read_csv(RENEWAL)
    d.columns = [c.strip() for c in d.columns]
    t = d[d["Metric name"].str.contains(r"whose coverage was terminated \(Metric 5b \+ 5c\)", regex=True)].copy()
    t["v"] = pd.to_numeric(t["Value"].astype(str).str.replace(",", ""), errors="coerce")
    t = t[(t["v"] > 0) & t["State"].isin(STATES)]
    first = t.groupby("State")["Reporting period"].min()
    rows = []
    for st, p in first.items():
        rows.append({"state": st, "event_type": "unwinding_first_terminations",
                     "event_date": f"{p // 100}-{p % 100:02d}-01", "end_date": "",
                     "detail": "First reporting month with Medicaid/CHIP terminations at renewal (Metric 5b+5c > 0), derived by code/08_policy.py.",
                     "source_name": "CMS, Medicaid and CHIP Updated Renewal Outcomes (October 2024 final release)",
                     "source_url": RENEWAL_URL, "accessed": "2026-10-08", "verification_status": "derived_from_source"})
    missing = sorted(set(STATES) - set(first.index))
    return pd.DataFrame(rows), missing


def cms_expansion_notes():
    m = pd.read_csv(os.path.join(RAW, "enrollment", "medicaid-enrollment-new-adult-group-02052026.csv"))
    out = {}
    for note in m["Notes"].dropna().unique():
        g = re.search(r"^(.*?) (?:is expanding|expanded) its Medicaid program by adopting the VIII Group on (\w+) (\d+), (\d{4})", note)
        if g:
            name = norm_name(g.group(1).replace("Virgin Island", "Virgin Islands"))
            if name in NAME_TO_ABBR:
                out[NAME_TO_ABBR[name]] = date(int(g.group(4)), MONTHS[g.group(2).lower()], int(g.group(3))).isoformat()
    return out


def quarters():
    return [(y, q) for y in range(2016, 2028) for q in range(1, 5)]


def qbounds(y, q):
    start = date(y, 3 * q - 2, 1)
    end = date(y + (q == 4), 1 if q == 4 else 3 * q + 1, 1) - pd.Timedelta(days=1)
    return start, end.date() if hasattr(end, "date") else end


def in_effect(start, end, qs, qe):
    if not start:
        return 0
    s = date.fromisoformat(start)
    e = date.fromisoformat(end) if end else date(9999, 1, 1)
    return int(s <= qe and e >= qs)


def main():
    os.makedirs(INT, exist_ok=True)
    man = pd.read_csv(os.path.join(RAW, "policy", "policy_events_manual.csv"), dtype=str).fillna("")
    unw, missing = unwinding_starts()
    events = pd.concat([man, unw], ignore_index=True)
    events.to_csv(os.path.join(PROC, "policy_annotations.csv"), index=False)

    # cross-check KFF expansion dates against CMS notes
    cms = cms_expansion_notes()
    kff = man[man.event_type == "aca_expansion"].set_index("state")["event_date"]
    xc = pd.DataFrame([{"state": s, "kff_date": kff.get(s, ""), "cms_note_date": d,
                        "agree": kff.get(s, "") == d} for s, d in sorted(cms.items())])
    xc.to_csv(os.path.join(INT, "expansion_date_crosscheck.csv"), index=False)

    ev = {(r.state, r.event_type): (r.event_date, r.end_date) for r in events.itertuples()}
    us = lambda t: ev.get(("US", t), ("", ""))
    rows = []
    for st in STATES:
        exp = ev.get((st, "aca_expansion"), ("", ""))[0]
        uw = ev.get((st, "unwinding_first_terminations"), ("", ""))[0]
        ce_early = ev.get((st, "community_engagement_state_early"), ("", ""))[0]
        ga = ev.get((st, "state_work_requirement_waiver"), ("", ""))[0]
        for y, q in quarters():
            qs, qe = qbounds(y, q)
            r = {"state": st, "year": y, "quarter": q}
            r["expansion_in_effect"] = in_effect(exp, "", qs, qe)
            r["expansion_mid_quarter"] = int(bool(exp) and qs < date.fromisoformat(exp) <= qe)
            r["expansion_date"] = exp
            r["continuous_enrollment_in_effect"] = in_effect(*us("continuous_enrollment"), qs, qe)
            r["unwinding_start_month"] = uw
            r["unwinding_in_effect"] = in_effect(uw, us("unwinding_period")[1], qs, qe) if uw else ""
            dis = add_months(uw, DISENROLL_LAG.get(st, 1)) if uw else ""
            r["unwinding_first_disenrollment_month"] = dis
            r["unwinding_disenrollment_basis"] = ("cms_state_timeline" if st in CHECKED else "assumed_1_month") if uw else ""
            r["unwinding_disenrollment_in_effect"] = in_effect(dis, us("unwinding_period")[1], qs, qe) if dis else ""
            r["x_waiver_eliminated"] = in_effect(us("x_waiver_eliminated")[0], "", qs, qe)
            r["mandatory_moud_benefit"] = in_effect(us("mandatory_moud_benefit")[0], "", qs, qe)
            ex_s, ex_e = ev.get((st, "mandatory_moud_exemption"), ("", ""))
            if ex_s:
                # exempt states: 0 during the documented exemption; unknown (blank) after it ends
                # until re-certification status is confirmed
                if in_effect(ex_s, ex_e, qs, qe) and qs >= date.fromisoformat(ex_s):
                    r["mandatory_moud_benefit"] = 0
                elif ex_e and qs > date.fromisoformat(ex_e):
                    r["mandatory_moud_benefit"] = ""
            fed_ce = us("community_engagement_federal")[0]
            r["community_engagement_federal_in_effect"] = in_effect(fed_ce, "", qs, qe) if exp else 0
            r["community_engagement_state_planned_start"] = ce_early
            r["state_work_requirement_waiver_in_effect"] = in_effect(ga, "", qs, qe)
            r["bup_prior_auth_required"] = ""
            r["bup_daily_dose_cap_mg"] = ""
            rows.append(r)
    pq = pd.DataFrame(rows)
    pq.to_csv(os.path.join(PROC, "policy_state_quarter.csv"), index=False)
    print(f"{len(events)} events ({len(unw)} derived unwinding starts); {len(pq)} state-quarter rows")
    print("unwinding start months:", unw.event_date.str[:7].value_counts().sort_index().to_dict())
    if missing:
        print("no termination data for:", missing)
    print(f"expansion cross-check vs CMS notes: {int(xc.agree.sum())}/{len(xc)} agree")
    for r in xc[~xc.agree].itertuples():
        print(f"  {r.state}: KFF {r.kff_date} vs CMS note {r.cms_note_date}")


if __name__ == "__main__":
    main()
