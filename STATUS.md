# Project status

**As of:** 24 October 2026. This page is the current status. Older files in `reports/*.md` are kept as history and may be out of date (for example, `PROJECT_STATUS_SUMMARY.md` still says Phase 2 has not started).

## Verified on the Windows PC (local results, 24 Oct 2026)

Environment: Windows 11, Python 3.14.6, PostgreSQL 18.6 (UTF8), psycopg2 2.9.13, pandas 3.0.3. Database `layoffs_db` was created new for this run (it did not exist before).

| Check | Result |
|---|---|
| Raw SHA-256, `layoffs_2019_2026_sample.csv` | `a181c6ce…f686`, matches |
| Raw SHA-256, `tech_layoffs_2025_2026.csv` | `f011a4d0…cc5c`, matches |
| Load 1 (`python src/phase4_load.py`) | exit 0, **5,035 events**, **142/142 checks**, committed (run 1) |
| Load 2 (rerun) | exit 0, **142/142 checks**, row counts and content fingerprint (md5 of all events) identical to load 1 |
| Schemas and views | `staging`, `core`, `audit`; 10 views in `core` including the 5 new `v_bi_*` |
| 19 analytics queries (`python src/phase4_analytics.py`) | **19/19 ran**; 16 reconciled with Phase 3, **979 cells, 0 mismatches**; 3 are checked in tests instead |
| Full test suite with the database (`LAYOFFS_ENABLE_DB_TESTS=1`) | **200 passed, 0 failed, 0 skipped** |
| Dashboard headline numbers (`python src/phase5_export_bi.py`) | **14/14 match** between SQL views and pandas (the 12-month repeat probability comes from notebook 05, not SQL) |
| Notebook 05 executed end to end | 12 of 12 code cells, 0 errors |
| Notebook 03 finding F3 | Reworded: only "2020 > every other year" is claimed for disclosed jobs |
| Test databases | all `layoffs_test_*` databases were dropped by the tests; only `layoffs_db` remains |

## Not done

| Step | Blocked by |
|---|---|
| Power BI dashboard (4 pages, `.pbix`, screenshots) | Power BI Desktop is not installed. Build steps, DAX and the numbers to match are in `powerbi/`. |
| Push to GitHub | Needs an empty GitHub repository created by you |

## Earlier cloud results (not this PC)

On a Linux copy with PostgreSQL 16 the project reported 142/142 checks per load, idempotent reruns, 16 of 19 queries reconciled with 0 mismatching cells, and 184 tests passing with the database.

## Local-only folders (not in git)

- `_recovery/`: files used to restore the project on 23 Oct 2026.
- `_backups/2026-10-24/`: originals of every file changed on 24 Oct (`03_exploratory_analysis.ipynb`, `phase4_load.py`, `requirements.txt`, `.gitignore`, `WORK_REPORT_2026-10-23_phase3.md`).

## Known differences from the verified cloud copy

8 Phase 1 files are the older v1 run (notebook 01, 2 interim staged CSVs, 2 audit CSVs, 2 figures, `NOTEBOOK_PLAN.md`); the 9th, `requirements.txt`, has been updated. They do not feed Phase 4, which reads `data/processed/` (byte-identical to the manifest). The v2 versions are in `reports/audit/history/run_2026-10-23_phase1_v2/`.
