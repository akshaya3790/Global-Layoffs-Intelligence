# Resume bullets (verified work only)

Every number below was produced on the Windows PC on 24 October 2026 (see `STATUS.md`). Pick 3–4 per role.

## Data Engineer

- Built a reproducible Python and PostgreSQL pipeline that loads 5,035 layoff records from two sources through staging and core schemas in a single audited transaction, guarded by 142 automated integrity and reconciliation checks per load; verified rerun-safe (two consecutive loads, identical content).
- Pinned raw data with SHA-256 fingerprints and traced every processed row back to its source file and line; kept Git byte-exact so checksums survive a fresh clone.
- Wrote 200 pytest tests, including database tests that create and drop throwaway PostgreSQL databases, covering business rules such as no zero-filling of missing values and no low-confidence rows in global totals.

## Data Analyst

- Wrote 19 documented analytical SQL queries (CTEs, window functions, filtered aggregates) and reconciled 16 of them cell by cell with the pandas analysis: 979 cells, 0 mismatches.
- Designed 5 PostgreSQL reporting views for a Power BI dashboard and reconciled all 14 headline metrics between SQL and Python.
- Audited and standardised a 5,000-event global layoffs sample: kept 2,511 undisclosed headcounts as NULL instead of zero and mapped 77 raw industry labels into 16 groups.

## Data Scientist

- Validated a 26% company-level sample against published population totals: event counts matched within about ±1 percentage point (ratios 0.256–0.271), while disclosed-job totals did not (0.225–0.341), and corrected a published year-ranking claim accordingly.
- Quantified uncertainty with a 1,000-replicate company-cluster bootstrap, showing that only 2020's disclosed-job lead over other years is statistically supported.
- Modelled time to a company's next layoff with Kaplan-Meier survival analysis and log-rank tests (implemented and unit-tested in NumPy/SciPy): 12.6% of companies (95% CI 11.5–13.8%) laid off again within 12 months.
- Chose not to ship a severity classifier after a feasibility probe showed weak signal (ROC-AUC ≈ 0.63) and a selection-biased target.

## Not yet claimable

- "Built a 4-page Power BI dashboard": add this only after the `.pbix` is built and its cards match `powerbi/headline_reconciliation.csv`.
