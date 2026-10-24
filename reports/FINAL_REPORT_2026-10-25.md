# Final report, 25 October 2026

All results below were produced on the Windows PC. "Inspected in Power BI" means Power BI Desktop was opened and its window captured; Power BI's own engine could not be queried from this PC.

## Checklist

| # | Item | Status |
|---|---|---|
| 1 | Back up the working report | Done: `_backups/2026-10-24/powerbi_final_freeze/` (80 files, local) |
| 2 | Four pages preserved, no redesign | Done |
| 3 | 14 headline metrics vs SQL | Done: 14/14 pass, 0 difference (table in `reports/POWERBI_VALIDATION.md`) |
| 4 | Global and tech data separate | Done: 0 tech rows in global views (SQL + tests); tech appears only on page 4's panel |
| 5 | Interval charts | Done: estimate = column, bounds = markers, one source row per category (test); values match notebook 05 |
| 6 | Page 2 year selector, page 4 Group by | Done: inspected in Power BI with 2020, 2023 and region; matches SQL; other visuals unchanged |
| 7 | Disclosures | Done: banner on all 4 pages; Unknown, missing-country, censoring and tech-source notes |
| 8 | Refresh, save, exports | Refresh: done 24 Oct, data unchanged since (load run 3 identical). Screenshots: done. **`.pbix`: not done. PDF: not done** (both need File menu actions in Power BI) |
| 9 | Exported files exist | Screenshots exist (205–224 KB each). No `.pbix`/PDF yet |
| 10 | Pipeline tests | Done: **214 passed** with the database; 191 passed + 23 skipped without |
| 11 | Loader idempotent | Done: 3 runs, 142/142 each, identical md5 `a99e3e0c…c319` |
| 12 | 19 SQL queries | Done: 19/19 ran; 16 reconciled, 979 cells, 0 mismatches |
| 13 | Documentation | Done: README, STATUS, docs/ (methodology, data_dictionary, business_findings, architecture, setup_windows, resume_and_interview), reports/POWERBI_VALIDATION; old reports moved to `reports/history/` |
| 14 | Public release prepared | Done: branch `public-release` (one commit, about 253 files, 11 MB), separate history from `main`; fresh copy: 135 passed, 79 skipped, 0 failed |
| 15 | Published | **Not done: waiting on your approval** |
| 16 | Findings report | Done: `docs/business_findings.md` (6 findings with evidence, denominator, uncertainty, decision) |
| 17 | Resume and interview materials | Done: `docs/resume_and_interview.md` (3 bullets, 2-minute walkthrough, 5-minute technical, Q&A, bullets by role) |

## Public-release scan (branch `public-release`)

- No `.env`, password, token, `_recovery`, `_backups`, Power BI cache, `.pbix` or PDF.
- No tech-file rows: `data/interim/`, `data/processed/`, tech summaries, mapping proposals, the page 4 screenshot and slicer captures are excluded; notebook 01–04 outputs are cleared. The only tech references left are file names, column/row counts, hashes, and a list of six tech event IDs inside a database test (identifiers only, no data).
- No local folder path (`<project folder>` and a placeholder Power BI parameter instead).
- Attribution: Fliar Research (2026), CC BY-NC 4.0 (non-commercial) in README and on every dashboard page.
- What a public clone can run: 135 tests; 79 skip (23 need PostgreSQL, 56 need the excluded data). Rebuilding `data/processed/` and loading PostgreSQL needs the tech file, which is not distributed. This is stated in `PUBLIC_RELEASE.md` and the README.

## Push commands (run only after you approve)

```
git remote add origin https://github.com/akshaya3790/Global-Layoffs-Intelligence.git
git push -u origin public-release:main
```

This publishes only the `public-release` commit as the repository's `main` branch. Your local `main` (full history, tech-derived data) is not pushed.

## Remaining

1. `.pbix` and PDF (Power BI File menu, your action).
2. Push approval.
