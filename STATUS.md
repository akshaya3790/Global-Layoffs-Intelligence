# Project status

**As of:** 24 October 2026. This page is the current status. Older files in `reports/*.md` are kept as history and may be out of date (for example, `PROJECT_STATUS_SUMMARY.md` still says Phase 2 has not started).

## Verified on the Windows PC (local results)

Environment: Windows 11, Python 3.14.6, PostgreSQL 18 (service running), psycopg2 2.9.13, pandas 3.0.3.

| Check | Result |
|---|---|
| Raw SHA-256, `layoffs_2019_2026_sample.csv` | `a181c6ce…f686`, matches |
| Raw SHA-256, `tech_layoffs_2025_2026.csv` | `f011a4d0…cc5c`, matches |
| Tests without the database | **177 passed, 23 skipped** (the 23 are database tests), 0 failed |
| Notebook 05 executed end to end | 12 of 12 code cells, 0 errors |
| Notebook 03 finding F3 | Reworded: only "2020 > every other year" is claimed for disclosed jobs |

## Not yet run locally

| Step | Blocked by |
|---|---|
| Load twice, 5,035 events and 142/142 checks per load | PostgreSQL password not yet entered in `.env` |
| 19 SQL queries and reconciliation with Phase 3 | same |
| 23 database tests (18 Phase 4 + 5 BI views) | same |
| `sql/ddl/06_bi_views.sql` against a real database | same |
| Power BI dashboard (4 pages) | Power BI Desktop is not installed |

## Earlier cloud results (not this PC)

On a Linux copy with PostgreSQL 16 the project reported 142/142 checks per load, idempotent reruns, 16 of 19 queries reconciled with 0 mismatching cells, and 184 tests passing with the database.

## Local-only folders (not in git)

- `_recovery/`: files used to restore the project on 23 Oct 2026.
- `_backups/2026-10-24/`: originals of every file changed on 24 Oct (`03_exploratory_analysis.ipynb`, `phase4_load.py`, `requirements.txt`, `.gitignore`, `WORK_REPORT_2026-10-23_phase3.md`).

## Known differences from the verified cloud copy

8 Phase 1 files are the older v1 run (notebook 01, 2 interim staged CSVs, 2 audit CSVs, 2 figures, `NOTEBOOK_PLAN.md`); the 9th, `requirements.txt`, has been updated. They do not feed Phase 4, which reads `data/processed/` (byte-identical to the manifest). The v2 versions are in `reports/audit/history/run_2026-10-23_phase1_v2/`.
