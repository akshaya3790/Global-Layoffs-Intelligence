# Project status

**As of 25 October 2026 (updated after the documentation pass).** This is the single current status page. Older phase reports are kept unchanged in `reports/history/`.

## Done and verified on the Windows PC

Environment: Windows 11, Python 3.14.6, PostgreSQL 18.6 (UTF8), psycopg2 2.9.13, pandas 3.0.3, Power BI Desktop 26.10.

| Area | Result | Evidence |
|---|---|---|
| Raw data | SHA-256 unchanged: `a181c6ce…f686` (global), `f011a4d0…cc5c` (tech) | `Get-FileHash`; notebooks check on every run |
| Credentials | `.env` keys match `src/phase4_config.py`; password never printed; `.env` git-ignored and in no commit | git history scan |
| Database | `layoffs_db` created new on 24 Oct (UTF8); schemas `staging`, `core`, `audit` | |
| Loads | **3 runs** (24 Oct ×2, 25 Oct ×1): each 5,035 events, **142/142 checks**, identical md5 fingerprint `a99e3e0c…c319` | `audit.load_runs`, `audit.validation_results` |
| Data rules | 5,000 global + 35 tech; 2,511 global headcounts NULL, 0 zeros; 0 duplicate keys; 0 tech rows in global views | SQL checks, tests |
| SQL analytics | **19/19** queries ran; 16 reconciled with pandas, **979 cells, 0 mismatches** | `reports/phase4/sql_reconciliation.csv`, `QUERY_CATALOG.md` |
| Tests | **214 passed, 0 failed, 0 skipped** with the database (25 Oct); 191 passed + 23 database tests skipped without it | `LAYOFFS_ENABLE_DB_TESTS=1 python -m pytest -q tests` |
| Statistics | Notebook 05 executed, 12/12 cells, 0 errors | `notebooks/05_*.ipynb`, `reports/stats/` |
| Dashboard numbers | 14/14 headline numbers: SQL = pandas, and Power BI's displayed values = SQL | `powerbi/headline_reconciliation.csv`, `reports/POWERBI_VALIDATION.md` |
| Dashboard behaviour | Pie year selector (2020, 2023) and page 4 "Group by" (region) match SQL and filter only their own chart; interval charts plot estimate + bounds correctly | `deliverables/validation/`, `tests/test_phase5_pbip.py` |
| Screenshots | 4 page captures | `deliverables/screenshots/page1.png` … `page4.png` |
| Docs | README (portfolio landing page); `docs/architecture.md`, `data_dictionary.md`, `methodology.md`, `business_findings.md`, `setup_windows.md` (commands marked tested / not tested), `resume_and_interview.md`; `reports/POWERBI_VALIDATION.md` | repository |
| Dependencies | `requirements.txt` (minimums) and `requirements-lock.txt` (exact versions that passed all tests; pip dry-run: all already satisfied) | |
| Notebook command | The notebook 05 command in `docs/setup_windows.md` was rerun on 25 Oct: 12/12 cells, 0 errors | |

## Waiting on you

| Step | What to do |
|---|---|
| `.pbix` file | In Power BI: File → Save as → Power BI file (.pbix) → `deliverables\LayoffsDashboard.pbix` |
| PDF | In Power BI: File → Export → Export to PDF → `deliverables\` |
| GitHub | Approve and run the push of the `public-release` branch (see `PUBLIC_RELEASE.md`). Nothing has been pushed. The repository `https://github.com/akshaya3790/Global-Layoffs-Intelligence` is public and empty |

## Public-release decision

The tech file's source and licence are unknown. Its rows appear in `data/interim/`, `data/processed/`, the outputs of notebooks 01–04, some historical reports, the page 4 screenshot and any `.pbix`/PDF export. They are on `main` only, which stays local. The public repository is built from the separate branch `public-release`, which excludes them (`PUBLIC_RELEASE.md`).

## Earlier cloud results (not this PC)

Before the local run, a Linux copy with PostgreSQL 16 reported 142/142 checks per load, idempotent reruns, 16 of 19 queries reconciled with 0 mismatches, and 184 tests passing with the database. Those results are superseded by the local ones above.

## Local-only folders (not in git)

- `_recovery/`: files used to restore the project on 23 Oct 2026.
- `_backups/2026-10-24/`: copies made before every change (notebook 03, loader, requirements, `.gitignore`, and each Power BI version: before the PBIR fix, before the pie, before page 4, before the redesign, your 10:31 PM save, and the final freeze).

## Known differences from the verified cloud copy

8 Phase 1 files are the older v1 run (notebook 01, 2 interim staged CSVs, 2 audit CSVs, 2 figures, `reports/history/NOTEBOOK_PLAN.md`). They do not feed Phase 4, which reads `data/processed/` (byte-identical to the manifest). The v2 versions are in `reports/audit/history/run_2026-10-23_phase1_v2/`.
