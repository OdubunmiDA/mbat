#!/usr/bin/env bash
# Run MBAT steps 02-13 in order (step 01, the download, is run separately: python code/01_fetch.py).
set -euo pipefail
cd "$(dirname "$0")"
python code/02_reference_ndcs.py
python code/03_extract_sdud.py --force
python code/04_ndc_crosswalk.py
python code/05_enrollment.py
python code/06_arcos.py
python code/07_cdc_overdose.py
python code/08_policy.py
python code/09_build_panel.py
rm -f data/interim/qa/recon_*.json   # re-derive from the raw files every full run
python code/10_reconcile.py
python code/11_qa_report.py "$@" > /dev/null
python code/12_figures.py "$@"
python code/13_summary.py "$@"
echo "Done. Read data/processed/qa_report.txt and docs/SUMMARY.md."
