#!/usr/bin/env python3
"""Step 01 - Fetch every raw input and verify it against data/raw/MANIFEST.csv.

For each manifest row: if the local file exists and its SHA-256 matches, nothing happens.
Otherwise the file is downloaded from source_url to a temporary name, hashed, and
  - moved into place if the hash matches the manifest, or
  - kept as <file>.new and reported if the hash differs (the agency has republished the file;
    decide deliberately whether to adopt the new vintage, then update the manifest).
Every fetch is appended to data/raw/PROVENANCE.txt.

The FDA NDC Directory zips and the RxNav cache are refreshed by hand (FDA republishes daily);
their hashes are recorded in the manifest when they are adopted.
Some agency hosts refuse non-browser clients; if a download fails, open source_url in a
browser, save the file into data/raw/<file>, and re-run this script to verify it.
Usage: python code/01_fetch.py [--only sdud/ arcos/ ...]
"""
import argparse
import csv
import hashlib
import os
import shutil
import sys
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def log(path, url, digest):
    with open(os.path.join(RAW, "PROVENANCE.txt"), "a") as f:
        f.write(f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}\t{os.path.relpath(path, RAW)}\t"
                f"{os.path.getsize(path)}\t{digest}\t{url}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=[])
    a = ap.parse_args()
    bad = 0
    for r in csv.DictReader(open(os.path.join(RAW, "MANIFEST.csv"))):
        if a.only and not any(r["file"].startswith(p) for p in a.only):
            continue
        path = os.path.join(RAW, r["file"])
        if os.path.exists(path) and sha256(path) == r["sha256"]:
            print(f"ok       {r['file']}")
            continue
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".part"
        try:
            req = urllib.request.Request(r["source_url"], headers={"User-Agent": "MBAT/1.0 (research data pipeline)"})
            with urllib.request.urlopen(req, timeout=300) as resp, open(tmp, "wb") as out:
                shutil.copyfileobj(resp, out, 1 << 20)
        except Exception as e:  # noqa: BLE001
            print(f"FAILED   {r['file']}: {e}  -> download {r['source_url']} in a browser into data/raw/{r['file']}")
            bad += 1
            continue
        d = sha256(tmp)
        log(tmp, r["source_url"], d)
        if d == r["sha256"]:
            os.replace(tmp, path)
            print(f"fetched  {r['file']}")
        else:
            os.replace(tmp, path + ".new")
            print(f"CHANGED  {r['file']}: source now differs from the pinned vintage; saved as {r['file']}.new")
            bad += 1
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
