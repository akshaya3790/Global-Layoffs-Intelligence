# Methods

How the numbers in this project are produced, and what each one can and cannot support.

## 1. Data and sampling

- **Global file** (`data/raw/layoffs_2019_2026_sample.csv`, 5,000 rows, Jan 2019 – 14 Jun 2026). Fliar Research's news-derived layoff events. It is a **26% sample** of 19,208 events that keeps **every event of a fixed, hash-chosen subset of companies** (data card). That makes it a **cluster sample by company**, not a random sample of events.
- **Tech file** (`data/raw/tech_layoffs_2025_2026.csv`, 35 rows). Unknown source and licence; company size is derived from its own percentage; 6 dates look wrong. It is kept as a separate, low-confidence case study and never enters a global figure (enforced by `core.v_global_events`, the `v_bi_*` views and tests).
- **Benchmark.** The publisher's data card (`data/raw/SOURCE_DATA_CARD.md`) gives full-population tables (by year, top countries, top sectors, repeat companies). They are typed into `src/phase5_stats.py` and `core.v_bi_benchmark` with a citation.

## 2. Audit and cleaning (Phases 1–2)

- Raw files are never modified and are fingerprinted with SHA-256 (`a181c6ce…f686`, `f011a4d0…cc5c`).
- Phase 1 only **flags** problems (18 `qc_*` columns); nothing is fixed silently.
- Phase 2 builds one event table (`data/processed/layoff_events.csv`, 5,035 × 69) through 16 logged rules (`transformation_log.csv`); every row keeps its source file and line (`source_file`, `source_row_number`), and `field_lineage.csv` maps every column to its source field.
- **Missing values stay missing.** Only verified headcounts are kept; the 2,511 undisclosed headcounts are NULL, never 0. Missing industry and country stay visible as `Unknown`; non-country values as `Unresolved`.
- **Nothing is merged.** 42 possible internal duplicates and the cross-source candidate pairs are flagged, not removed. Company names are standardised conservatively (capitalisation only; 13 names need review).

## 3. Database (Phase 4)

PostgreSQL schemas `staging`, `core`, `audit`. `src/phase4_load.py` runs pre-flight checks (headers, types, keys, SHA-256 against the manifest), loads staging with COPY, replaces the core tables inside **one transaction**, and runs **142 integrity and reconciliation checks** before committing. A failed check rolls everything back. Each run is recorded in `audit.load_runs`, `audit.load_files` and `audit.validation_results`. Re-running is safe: the content is replaced with identical rows (verified: three runs, identical md5 fingerprint).

## 4. SQL analytics

19 documented queries in `sql/analytics/` (catalogue: `reports/phase4/QUERY_CATALOG.md`), run read-only by `src/phase4_analytics.py`. 16 are compared cell by cell with the pandas EDA (979 cells, 0 mismatches); 3 are recomputed in the database tests.

Definitions used everywhere:
- **Event** = one row. All global rows are counted, including furloughs and duplicate candidates (query 19 shows the effect of excluding them).
- **Disclosed jobs cut** = sum of verified headcounts only, labelled a lower bound and shown with its coverage.
- **US share** uses events with a known country as the denominator.
- **2026** is labelled partial and never compared as a full year.

## 5. Statistics (notebook 05, `src/phase5_stats.py`)

1. **Sample validity.** Sample ÷ full-population figures. A perfect 26% sample gives 0.260 (5,000 ÷ 19,208). Events by year: 0.256–0.271; top 5 countries: 0.248–0.271; top 3 sectors: 0.247–0.269; repeat companies: 0.245. Disclosed jobs by year: 0.225–0.341.
2. **Company-cluster bootstrap.** 1,000 replicates; each draws 3,467 companies with replacement and keeps all of their events, because that is how the sample was drawn. 90% percentile intervals for yearly events, disclosed jobs and the median cut. Seed 20261023.
3. **Kaplan–Meier time to next layoff.** One row per company; the clock starts at its first sampled event and stops at its second. Companies with no second event by 14 Jun 2026 are **right-censored**. Survival with Greenwood standard errors and log-log 95% intervals; differences tested with a multi-group log-rank test. Implemented in NumPy/SciPy and unit-tested against hand-worked examples (`tests/test_phase5_stats.py`).
4. **Sensitivity.** Query 19: events per year excluding furloughs, possible internal duplicates and cross-source candidates (at most 14 events change in any year apart from 2020's furloughs).

**Not built, on purpose:** a severity classifier (feasibility probe ROC-AUC ≈ 0.63; the target exists only for the non-random half of events with a disclosed headcount), a monthly forecast (about 90 points, a COVID shock and incomplete 2026), and an AI-layoffs analysis (41 relevant global rows).

## 6. Power BI

Built only on the reporting views (`sql/ddl/06_bi_views.sql`) and notebook 05's output tables; no new metric definitions. Validation: `reports/POWERBI_VALIDATION.md`.

## 7. Limitations

Sample, not a census; news-based (misses unreported layoffs; favours large, English-covered companies); disclosed jobs are lower bounds and disclosure is not random (North America 55.3% vs Latin America 41.3%); 2026 partial; 31% Unknown industry and 9% no country; brand names can be split across spellings; survival results are associations, left-truncated at 2019, and affected by the source merging reports within 45 days; no company size, so no layoff rates.
