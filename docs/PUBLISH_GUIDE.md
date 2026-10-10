# MBAT publish guide (v1.0, then v1.1 and v1.2)

**Run each step in order. Nothing is pushed or deposited until the publish gate passes (step 0.3).**

## 0. Finalize (about 10 minutes)
1. `bash run_all.sh --final` to regenerate the QA report, figures and SUMMARY for release.
2. Set the version in `README.md` and `CITATION.cff` (`version:`, `date-released:`).
3. `python tools/publish_gate.py . --allow-draft-in code/ tools/ data/interim/ --skip data/raw/sdud/ _to_delete/` must report no blockers. (Code legitimately contains draft-stamp logic and bracket indexing; interim files are not published, and the 5 GB raw SDUD files and `_to_delete/` are gitignored and skipped.) Resolve anything else it lists, including every policy row still marked VERIFY.

## 1. GitHub (about 10 minutes)
1. Create an empty repository at github.com/new, e.g. `mbat` (no README; the project has one).
2. In a terminal inside `Documents/MBAT`:
   ```bash
   git init -b main
   git add -A
   git commit -m "MBAT v1.0.0"
   git remote add origin https://github.com/<your-username>/mbat.git
   git push -u origin main
   ```
   `.gitignore` already keeps the 5 GB raw SDUD files out of the repository.
3. To automate this instead, give Claude a GitHub token (scope `repo`) as the environment variable `GITHUB_TOKEN` in a later session; `tools/publish_github.py` creates the repo, pushes and tags the release. Revoke the token afterwards.

## 2. Zenodo DOI (about 10 minutes; recommended route)
1. Log in at zenodo.org with your ORCID (0009-0004-8843-5339) so it attaches automatically.
2. Account > GitHub > switch on the `mbat` repository.
3. On GitHub: Releases > Draft a new release > tag `v1.0.0`, title "MBAT v1.0.0", paste the release notes below > Publish. Zenodo archives the release and mints a DOI within minutes.
4. On the new Zenodo record, edit the metadata:
   - **Upload type:** Dataset.
   - **Creators:** Odubunmi, Oluwapelumi; ORCID; affiliation as in `AUTHORS.json`.
   - **License:** CC BY 4.0 (note in the description that the code is MIT).
   - **Keywords:** from `CITATION.cff`.
   - **Related identifiers:** the GitHub URL (is supplemented by).
5. Copy the DOI into `CITATION.cff` (`doi:`), the README status line and the evidence log. Commit and push.
6. **v1.1 (March 2027) and v1.2 (July 2027):** re-run the pipeline on the refreshed CMS files, re-verify V4–V6, and publish GitHub releases `v1.1.0` and `v1.2.0`. Zenodo mints a new version DOI under the same concept DOI automatically.

Alternative: upload manually on Zenodo (New upload > the release zip plus `data/processed/*.csv` > same metadata), or supply `ZENODO_TOKEN` (scopes `deposit:write`, `deposit:actions`) for `tools/zenodo_deposit.py`, testing first against sandbox.zenodo.org.

## Release notes (paste into the GitHub release)
> MBAT v1.0.0. A state-by-quarter panel (50 states + DC, 2016Q1–2027Q4) of Medicaid-paid buprenorphine for OUD from CMS State Drug Utilization Data, linked to CMS enrollment, DEA ARCOS retail buprenorphine (through 2023Q4), CDC provisional overdose deaths, and dated policy events. Includes a classified NDC crosswalk, QA report with independent reconciliation against raw CMS files, codebook and limitations. Pinned source vintages are in data/raw/MANIFEST.csv. Raw SDUD files are re-downloaded by code/01_fetch.py.

## After publishing
Record on the same day: Zenodo DOI, GitHub release URL, date, version, and a saved PDF of the Zenodo record page.
