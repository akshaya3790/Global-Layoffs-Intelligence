# Resume and interview materials

All numbers below were produced and checked on the project PC (see [STATUS.md](../STATUS.md)). Nothing here claims a predictive model, a forecast or a causal finding; the project has none.

## Three resume bullets

1. Built a reproducible Python and PostgreSQL pipeline that loads 5,035 layoff records through staging and core schemas in one audited transaction, guarded by 142 integrity checks per load and 267 automated tests; verified idempotent across three consecutive loads.
2. Wrote 19 analytical SQL queries and a 4-page Power BI dashboard on curated views; reconciled 979 cells with pandas (0 mismatches) and all 14 headline dashboard metrics with SQL.
3. Validated a 26% company-cluster sample against published population totals and quantified uncertainty with a company-cluster bootstrap and Kaplan–Meier survival analysis: 12.6% (95% CI 11.5–13.8%) of companies laid off again within 12 months.

More bullets by role are at the end of this page.

## Two-minute walkthrough

"This project looks at news-reported layoffs from 2019 to mid-2026. The data is a 26% sample from Fliar Research: 5,000 events at about 3,500 companies, plus a separate 35-row tech file with unknown provenance that I kept out of every global number.

I first audited the raw files without changing them, fingerprinted them, and flagged problems instead of fixing them silently. The big one: half the events don't disclose a headcount, so I kept those as missing rather than zero, and labelled every job figure a lower bound.

Then I loaded everything into PostgreSQL through a staging layer in one transaction with 142 checks, wrote 19 SQL queries, and reconciled them with my pandas analysis cell by cell.

The interesting part was the statistics. Because the sample keeps whole companies, I checked it against the publisher's full-population tables: event counts track the full data within about one percentage point, but job totals swing a lot. A company-cluster bootstrap showed I could not rank 2023, 2024 and 2025 by jobs cut, so I corrected an earlier claim. I also ran a Kaplan–Meier analysis: about 1 in 8 companies had another layoff within a year.

Finally I built a 4-page Power BI dashboard on SQL views, with the sample warning on every page, and checked every headline number against SQL."

## Five-minute technical explanation

1. **Ingestion and audit (Python).** Raw CSVs are read-only and SHA-256 pinned. Notebook 01 adds 18 `qc_*` flags (dates, numbers, duplicates, missing sector/country). Nothing is dropped.
2. **Cleaning (Python).** Notebook 02 applies 16 logged rules (`transformation_log`), builds one canonical table of 5,035 × 69 with lineage to the raw file and line, and writes a SHA-256 manifest of every output.
3. **Database (PostgreSQL).** `phase4_load.py`: pre-flight (headers, types, keys, manifest hashes) → COPY into `staging` → typed `INSERT … SELECT` into `core` inside one transaction → 142 checks (row counts, NULL preservation, key integrity, reconciliation with the CSVs) → commit or roll back. Every run is written to `audit`. Re-running replaces rows with identical content; I proved it with an md5 fingerprint across three runs.
4. **Analytics (SQL).** 19 queries with CTEs, window functions and `FILTER` aggregates, run read-only. 16 reconcile with the Phase 3 pandas outputs (979 cells); the rest are recomputed in tests.
5. **Statistics (Python).** Benchmark ratios against the data card; a company-cluster bootstrap (resampling companies, not rows, because the sample is clustered); Kaplan–Meier with right-censoring at the data end date, Greenwood intervals and log-rank tests, written in NumPy/SciPy and unit-tested.
6. **BI (Power BI).** Five reporting views (`v_bi_*`) with fixed grain; the report is generated as a Power BI Project (PBIP) from Python, validated against Microsoft's schemas, and every headline number is reconciled with SQL.
7. **Testing.** 267 pytest tests: business rules (missing never becomes zero, no tech rows in global figures), database integration in throwaway databases, statistics maths, and dashboard file checks.

## Likely questions, with short answers

**SQL**
- *How do you avoid counting missing headcounts as zero?* `SUM` and `COUNT(column)` ignore NULLs; I show `COUNT(*) - COUNT(employees_laid_off)` next to every job sum.
- *Why `FILTER` instead of `CASE`?* Clearer conditional aggregates, e.g. `count(*) FILTER (WHERE is_furlough)`.
- *What's a window function you used?* Ranking each company's events by date to find the second event (`row_number() OVER (PARTITION BY company_name ORDER BY event_date)`).

**Data quality**
- *Why not drop duplicates?* They're candidates, not proven duplicates. I flagged 42 and showed (query 19) that excluding them changes at most 14 events in a year.
- *How do you know the cleaning didn't change raw data?* Raw files are hash-pinned; every processed row carries its source file and line.

**PostgreSQL**
- *How is the load safe to rerun?* Core tables are replaced inside one transaction after checks pass; failures roll back; three runs gave the same md5 fingerprint.
- *Why a staging schema?* To validate types and keys on text first, so a bad file never touches `core`.

**Power BI**
- *How do you know the dashboard is right?* Every headline card comes from a view with a fixed definition; a script compares them with a pandas recomputation (14/14), and I compared what Power BI displays with SQL.
- *Why Import mode?* 5,035 rows; DirectQuery would add latency for no benefit.

**Sampling**
- *Is 26% enough?* For event counts, yes: they match the full data within about ±1 pp. For job totals, no: whole companies are in or out, so a few huge cuts swing the totals.

**Bootstrap**
- *Why resample companies?* The sample was drawn by company, and a company's events are correlated; resampling rows would make intervals too narrow.

**Survival analysis**
- *What is censoring here?* A company with no second layoff by 14 Jun 2026 has only been observed for part of its future; Kaplan–Meier uses that partial time instead of counting it as "never".
- *Can you say a large first layoff causes another?* No. It's an association; companies with larger cuts may differ in many ways.

**Limitations**
- News-based (misses unreported layoffs); 26% sample; job sums are lower bounds; 2026 partial; 31% unknown industry; no company size, so no layoff rates; tech file excluded for provenance reasons.
- *Why no machine-learning model?* A feasibility probe for "large layoff" reached ROC-AUC ≈ 0.63 with a selection-biased target; I chose to report a defensible statistical analysis instead.

## Bullets by role

Every number below was produced on the Windows PC on 24–25 October 2026 (see `STATUS.md`). Pick 3–4 per role.

### Data Engineer

- Built a reproducible Python and PostgreSQL pipeline that loads 5,035 layoff records from two sources through staging and core schemas in a single audited transaction, guarded by 142 automated integrity and reconciliation checks per load; verified rerun-safe (three consecutive loads, identical content).
- Pinned raw data with SHA-256 fingerprints and traced every processed row back to its source file and line; kept Git byte-exact so checksums survive a fresh clone.
- Wrote 267 pytest tests, including database tests that create and drop throwaway PostgreSQL databases, covering business rules such as no zero-filling of missing values and no low-confidence rows in global totals.

### Data Analyst

- Wrote 19 documented analytical SQL queries (CTEs, window functions, filtered aggregates) and reconciled 16 of them cell by cell with the pandas analysis: 979 cells, 0 mismatches.
- Built a 4-page Power BI dashboard on 5 PostgreSQL reporting views, with the sample-coverage warning on every page; reconciled all 14 headline metrics with SQL and tested its slicers against SQL results.
- Audited and standardised a 5,000-event global layoffs sample: kept 2,511 undisclosed headcounts as NULL instead of zero and mapped 77 raw industry labels into 16 groups.

### Data Scientist

- Validated a 26% company-level sample against published population totals: event counts matched within about ±1 percentage point (ratios 0.256–0.271), while disclosed-job totals did not (0.225–0.341), and corrected a published year-ranking claim accordingly.
- Quantified uncertainty with a 1,000-replicate company-cluster bootstrap, showing that only 2020's disclosed-job lead over other years is statistically supported.
- Modelled time to a company's next layoff with Kaplan-Meier survival analysis and log-rank tests (implemented and unit-tested in NumPy/SciPy): 12.6% of companies (95% CI 11.5–13.8%) laid off again within 12 months.
- Chose not to ship a severity classifier after a feasibility probe showed weak signal (ROC-AUC ≈ 0.63) and a selection-biased target.

### Evidence

[STATUS.md](../STATUS.md), [Power BI validation](../reports/POWERBI_VALIDATION.md), [query catalogue](../reports/phase4/QUERY_CATALOG.md), [business findings](business_findings.md).
