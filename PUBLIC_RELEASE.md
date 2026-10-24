# Public release: what is and is not published

The local project (branch `main`) contains data derived from the 35-row technology layoffs file, whose source and licence are unknown. Until redistribution rights are established, the public GitHub repository is published from a separate branch, `public-release`, that leaves that data out. `main` keeps the full local history unchanged and is not pushed.

## Excluded from `public-release`

Built by `python src/make_public_release.py` (one parentless commit; `main` is not touched).

| Path | Why |
|---|---|
| `data/raw/tech_layoffs_2025_2026.csv` | Unknown source and licence (never committed anywhere) |
| `data/interim/` | `tech_layoffs_staged.csv` is a staged copy of the tech file; the pair files list tech rows |
| `data/processed/` | `layoff_events.csv` and its companion tables contain the 35 tech-derived rows |
| `reports/audit/history/*/tech_layoffs_staged.csv`, `*/possible_duplicate_pairs.csv`, `*/excluded_candidate_pairs.csv` | Copies of tech rows |
| `reports/eda/03_T*`, `reports/figures/03_T*`, `reports/phase4/query_results/11-14_*` | Summaries of the tech file's contents |
| Historical reports that quote individual tech rows | `reports/history/PHASE1_VERIFICATION_REPORT*.md`, `PHASE2_APPROVAL_CHECKLIST.md`, `PHASE2_CANONICAL_MODEL_PLAN.md`, `PROJECT_STATUS_SUMMARY.md`, `WORK_REPORT_2026-10-23_phase2_build.md` |
| `deliverables/screenshots/page4.png`, `deliverables/validation/`, any `.pbix` / PDF | They show or embed the tech case-study rows |
| Outputs of notebooks 01-04 | They print tech rows; the code cells are kept, the outputs are cleared |
| This machine's folder path | Replaced by `<project folder>`, and by a placeholder in the Power BI `ProjectFolder` parameter |

Never committed at all (git-ignored): `.env`, `_recovery/`, `_backups/`, `powerbi/data/`, Power BI cache files.

## Published

All code (`src/`, `sql/`, `tests/`), notebooks 01-05 (05 with outputs, which use only global data), the global sample file and its data card (CC BY-NC 4.0, attributed), global EDA, statistics and query outputs, the Power BI project, and the documentation.

## What this means for reproducing the project

A public clone can read all code, SQL, tests, statistics outputs and the dashboard design. Tested on a fresh export of `public-release` (24 Oct 2026): **121 passed, 79 skipped, 0 failed**. The skips are 23 database tests and 56 tests that read the excluded data (`tests/conftest.py` reports them as skipped, with that reason). The local folder path is replaced by `<project folder>` or a placeholder in the Power BI `ProjectFolder` parameter. Rebuilding `data/processed/` (and therefore loading PostgreSQL) needs the tech file too, which is not distributed. If its licence is later confirmed, the full `main` history can be published instead.
