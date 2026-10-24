# SQL analytics catalogue

Run on the Windows PC on 24 Oct 2026 against `layoffs_db` (PostgreSQL 18.6) with `python src/phase4_analytics.py`. Every query runs in a READ ONLY transaction. Results: `reports/phase4/query_results/`. Reconciliation: `reports/phase4/sql_reconciliation.csv`.

| # | Question | Filters | Rows | Reconciliation |
|---|---|---|---|---|
| 01 | How many layoff events happened in each calendar month? | global sample only (core.v_global_events, 5,000 rows). ALL rows are counted, including furloughs, duplicate candidates and rows with quality flags. Tech rows are never included. | 90 | MATCH: 180 cells, 0 mismatches |
| 02 | Per year, how many events, and how many jobs were cut where the headcount is known? | global sample only; all rows counted (furloughs and duplicate candidates included - see 19). | 8 | MATCH: 72 cells, 0 mismatches |
| 03 | Which industry groups have the most layoff events? | global sample only; all rows counted. | 17 | MATCH: 119 cells, 0 mismatches |
| 04 | What share of each year's events falls in each industry group? | global sample only; 'Unknown' included, so each year's shares add up to 100%. | 135 | MATCH: 136 cells, 0 mismatches |
| 05 | How do regions compare (event location)? | global sample only; all rows counted. | 7 | MATCH: 42 cells, 0 mismatches |
| 06 | Which countries have the most events, and which country values are missing or unresolved? | global sample only; all rows counted. | 111 | MATCH: 120 cells, 0 mismatches |
| 07 | What share of events with a KNOWN country happened in the United States, per year? | global sample only. Denominator = events with a known country (missing countries are excluded from the base and reported separately, so they do not drag the share down). | 8 | MATCH: 32 cells, 0 mismatches |
| 08 | How big are layoffs, in people? | global sample; only rows with a known headcount (denominator shown). Rows without a headcount are NOT put in any band (they are reported in rows_without_headcount). | 5 | MATCH: 10 cells, 0 mismatches |
| 09 | What share of the workforce do layoffs cut? | global sample; ONLY rows with a known workforce_pct (1,121 of 5,000). Unknown percentages are excluded from the calculation, never treated as 0; the denominator is shown on every row. | 6 | MATCH: 6 cells, 0 mismatches |
| 10 | How large are layoffs as a share of the workforce, per year? | statistics use ONLY rows with a known workforce_pct; rows_with_pct is the denominator and rows_without_pct shows how many were excluded. Missing is never treated as 0. | 9 | not applicable (checked in tests) |
| 11 | What reasons are given for the tech-file layoffs? | core.v_tech_events only. | 6 | MATCH: 12 cells, 0 mismatches |
| 12 | How do events marked AI_Related = Yes / Partial / No compare? | core.v_tech_events only. suspect_dates counts rows flagged qc_suspect_date (6 in total); those rows are kept, with their original dates. | 3 | MATCH: 15 cells, 0 mismatches |
| 13 | Which departments are involved in the tech-file layoffs? |  | 19 | MATCH: 38 cells, 0 mismatches |
| 14 | How many weeks of severance were offered? |  | 7 | MATCH: 7 cells, 0 mismatches |
| 15 | Which companies had more than one layoff event? | global sample only. ALL rows are counted; how many of them are flagged as possible internal duplicates (same company + same news URL) is shown, so you can judge whether a "repeat" may be one event reported twice. No rows are removed or merged. | 688 | not applicable (checked in tests) |
| 16 | How many companies had 1, 2, 3 or 4+ layoff events - and does that change if possible internal duplicates are set aside? | global sample only. Column companies_all counts every row. companies_excl_internal_dups is a what-if that ignores rows flagged possible_internal_duplicate (nothing is deleted). | 5 | not applicable (checked in tests) |
| 17 | How many records carry each data-quality flag, per source? | both sources, shown separately (never added together). | 36 | MATCH: 72 cells, 0 mismatches |
| 18 | How complete is each important field, per source? | both sources, shown separately. 100% missing means the field does not exist in that source. | 30 | MATCH: 78 cells, 0 mismatches |
| 19 | Do furloughs or unresolved duplicate candidates drive the yearly results? | global sample only (tech rows never included); all_events counts every row. Every column after all_events is a WHAT-IF that leaves some rows out of the count; nothing is deleted from the database. | 8 | MATCH: 40 cells, 0 mismatches |

**Totals:** 19 of 19 ran successfully; 16 reconciled with the Phase 3 pandas outputs (979 cells, 0 mismatches); queries 10, 15 and 16 have no Phase 3 chart file and are recomputed with pandas in `tests/test_phase4_db.py`.

Queries 11-14 use only the separate 35-row tech file (`core.v_tech_events`). All other queries use `core.v_global_events`, so tech rows never enter a global figure. Job figures are sums of disclosed headcounts (lower bounds); missing headcounts stay NULL.
