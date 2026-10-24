# Work report: Phase 4, PostgreSQL integration, data integrity and SQL analytics

## 1. Summary of implementation

Phase 4 is **implemented and verified in this environment**. All of the following were actually executed:
- The 10 verified processed CSVs load into PostgreSQL 16 through a pre-flight-checked, transactional, audited pipeline.
- Each load runs **142 integrity and reconciliation checks**. They all pass, and the results are stored in the database.
- **19 analytical SQL queries** run. 16 of them were compared **cell by cell** with the Phase 3 chart data: 979 cells, 0 differences. The other 3 are checked against pandas in the tests.
- **68 new tests** were added (50 need no database, 18 need one). The full suite is **184 passed**.
- A complete clean-room rerun (notebooks 01-04, two loads, query reconciliation and all tests) gave identical results.
- Phases 1-3 are unchanged: **92 of 92** baseline files have identical hashes.

ML and Power BI were not started.

---

## 2. Actual database and environment used

| Item | Value |
|---|---|
| Server | **PostgreSQL 16.15** (Ubuntu 24.04), in this cloud workspace |
| Cluster | A **new, separate** cluster `layoffs` on port 5433, created for this project. The pre-existing default cluster `main` (port 5432, stopped) was **not touched**. |
| Database / role | `layoffs_db` (UTF-8) / `layoffs_app` (LOGIN, CREATEDB). The password is held outside the project and is not in any file I'm delivering. |
| Python | psycopg2 2.9.13, pandas 3.0.5, pytest 9.1.1 |
| Your machine | **Not tested.** On Windows you need PostgreSQL 13 or later plus the steps in `sql/README.md`. |

**Environment issue found and fixed:** the cluster's default encoding was `SQL_ASCII`, so the first copy failed on accented company names. I recreated my own empty `layoffs_db` as **UTF-8**. The loader now **refuses a non-UTF-8 database** with a clear message, and there is a test for this.

---

## 3. Schema and relationships

Full document: `reports/PHASE4_SCHEMA_AND_RELATIONSHIPS.md`, which has an ER diagram, every key, the nullability, types and indexes, and the deviations. The DDL is in `sql/ddl/01-05`.

**Three schemas:**
- `staging`: text copies of the CSVs.
- `core`: typed tables.
- `audit`: run, file and check history, never deleted.

**Core tables (11):**
- `layoff_events` (5,035 rows): one row per source record, with all 69 columns kept.
- `layoff_event_departments`: the bridge table.
- `quality_issues`.
- `company_name_mapping` and `industry_mapping`.
- `field_lineage` and `transformation_log`.
- `cross_source_industry_disagreements`.
- `possible_duplicate_pairs` and `excluded_candidate_pairs`.
- `source_datasets` (new, 2 rows): each source's confidence and known limitations.

**Keys and relationships:**
- Every event has a mapping row for its raw company name and its raw industry label, enforced by foreign keys.
- Child tables reference events through (`event_key`, `source_dataset`, `source_row_number`).
- Both pair tables link one tech event to one global event.
- **No company, sector, country or date dimension was created**, and no duplicate was merged or given a primary record.

**Deliberate deviations from the CSVs:**
1. `transformation_log.column` became `column_name`, because `column` is reserved in SQL.
2. `source_datasets` is a new table.
3. `50.0`-style whole numbers become INTEGER, and True / False / empty become BOOLEAN / NULL.
4. The manifest is used for verification and is not stored as a table.
5. **Range rules are not constraints.** Phases 1-2 keep out-of-range values and flag them, so these are checked by validation queries instead.

**Conflict with the plan:** `NOTEBOOK_PLAN.md` had planned a star schema with dimensions. I followed your brief (no normalisation that loses names or traceability) and updated the plan to say so.

---

## 4. Tables loaded: expected vs actual row counts

| Table | CSV rows (expected) | Staging | Core |
|---|---|---|---|
| layoff_events | 5,035 | 5,035 | 5,035 |
| layoff_event_departments | 70 | 70 | 70 |
| quality_issues | 4,886 | 4,886 | 4,886 |
| company_name_mapping | 3,532 | 3,532 | 3,532 |
| industry_mapping | 77 | 77 | 77 |
| field_lineage | 54 | 54 | 54 |
| transformation_log | 16 | 16 | 16 |
| cross_source_industry_disagreements | 9 | 9 | 9 |
| possible_duplicate_pairs | 18 | 18 | 18 |
| excluded_candidate_pairs | 97 | 97 | 97 |
| source_datasets | 2 (from the spec) | n/a | 2 |

All 10 file hashes match `phase2_output_manifest.csv`, and this is recorded in `audit.load_files`.

---

## 5. Reconciliation and integrity results (142 checks per load, all passed)

| Category | Checks | What is proven |
|---|---|---|
| counts | 21 | CSV = staging = core for every table |
| keys | 11 | `event_key` is unique and never null. (`source_dataset`, `source_row_number`) is unique. `source_event_id` is present for all 5,000 global rows and null for all 35 tech rows. No child row points to a missing event. Pair rows link tech to global. |
| bridge | 5 | Departments belong to tech events only, 35 events are covered, the weights add up to exactly 1 per event and to 35 in total, and `departments_in_event` is consistent |
| nulls | 49 | For each of the 36 nullable event columns, the null count per source equals the CSV. No zero was created in any numeric column. The nulls in the pair tables are preserved. |
| qc_flags | 21 | For all 18 flags, the TRUE / FALSE / NULL (not computed) counts per source equal the CSV. `quality_issues` has **exactly** one row per TRUE flag. |
| sources | 3 | Source, confidence and file labels are preserved: 5,000 global and 35 tech rows |
| duplicates | 4 | 11 groups and 29 members are kept, the 42 internal duplicates are kept, and both pair files keep their review status (`pending_review` / `excluded_by_rule_not_reviewed`) |
| dates | 3 | The 6 suspect dates keep their original values, `event_date` = `event_date_raw` for every row, and the date ranges per source are unchanged |
| reconciliation | 8 | **Exact** sums from the CSV text. Global known headcount: 2,489 rows totalling **2,788,908**. Workforce %: 1,121 rows totalling **24,761.242033** (no rounding). Also the tech totals, the per-year headcounts and the pair-table sums. |
| distributions | 10 | Industry group, country (NULL included), region (Unknown and Unresolved included), reason, `ai_related`, headcount status, date reliability, review status, raw industry and departments all match the CSV per source |
| mappings | 7 | Mapping rows equal the events per raw name and per label. Every event's cleaned name and group equals its mapping row. Every global key listed in a disagreement exists. The lineage and transformation-log contents match. |

---

## 6. Automated test results

| Suite | Result |
|---|---|
| Existing Phase 1-3 tests (before any change) | 116 passed |
| `tests/test_phase4_unit.py` (no database) | **50 passed** |
| `tests/test_phase4_db.py` (real PostgreSQL, throwaway `layoffs_test_*` databases) | **18 passed** |
| **Full suite with the database tests** (project copy and clean copy) | **184 passed, 0 failed** |
| Full suite without the database setting | 166 passed, 18 **skipped**, reported as skipped and not as passed |

**What the tests cover:**
- **Pre-flight rejections:** a changed file (hash), an impossible date, a non-numeric year, a fractional integer, a bad boolean, a missing required value, a duplicate key, a changed header, a missing file and a wrong field count. A literal text `NULL` value is kept and produces a warning.
- **Database behaviour:**
  - a clean load, with the audit trail recorded;
  - a **repeat load**, after which the content fingerprint and counts are identical;
  - nulls preserved, with no zeros created;
  - quality limitations kept as they are: 6 Unresolved, 1,564 Unknown and 6 suspect dates;
  - exact numeric reconciliation;
  - the foreign key enforced on the bridge table.
- **Failure behaviour:**
  - invalid input is rejected before the database is touched;
  - a **broken relationship rolls back**, so the committed data is unchanged and the failure is recorded in the audit;
  - a **failed validation check rolls back**;
  - the loader refuses to replace data of unknown origin;
  - schema drift stops the load without altering anything;
  - a non-UTF-8 database is rejected.
- **Queries:** every query runs and reconciles with Phase 3; a deliberately changed value **is detected**; global queries never include tech rows; 2026 and May-June 2026 are labelled; the repeat-layoff and workforce-% queries equal pandas.

Two problems were found while building, both in my own code, and fixed:
- **A check had a bug.** A missing pair of parentheses in a set operation made the first load (run 1) **fail and roll back**, as designed. That failed run is still visible in `audit.load_runs` in the main database.
- **A test expectation was wrong.** It said 3,914 missing workforce % values, but the CSV has 3,879, and the database matched the CSV.

---

## 7. SQL queries created and verified (`sql/analytics/`)

Every file states its question, counting unit, filters, how it treats missing values, and what it reconciles with. All run read-only.

| # | Query | Rows | Reconciliation |
|---|---|---|---|
| 01 | Monthly events + 3-month average + period note | 90 | Phase 3 03_01: match |
| 02 | Yearly events, **known** job cuts, coverage %, partial-year label | 8 | 03_02: match |
| 03 | Industry ranking, **Unknown ranked** | 17 | 03_03: match |
| 04 | Industry share by year | 135 | 03_04: match (an empty group-year counts as 0) |
| 05 | Region comparison, **Unknown + Unresolved** | 7 | 03_05: match |
| 06 | Country comparison with status ok / missing / not a country | 111 | 03_06: match |
| 07 | US share of known-country events | 8 | 03_07: match |
| 08 | Layoff-size bands, with denominator 2,489 | 5 | 03_08: match |
| 09 | Workforce-% bands, **known % only**, with denominator 1,121 shown | 6 | 03_08: match |
| 10 | Workforce % by year (median, mean, n, excluded) | 9 | pandas (tests) |
| 11-14 | **Tech file only:** reasons, AI_Related, departments, severance | 6 / 3 / 19 / 7 | T1 / T2: match |
| 15 | **Repeat layoffs by company** (new) | 688 | pandas (tests) |
| 16 | Companies by number of events, with and without internal duplicates | 5 | pandas (tests) |
| 17 | Quality flags per source (flagged / not / not computed) | 36 | 03_10: match |
| 18 | Missingness per field and source | 30 | 03_09: match |
| 19 | Sensitivity: furloughs and duplicate candidates excluded (events and known jobs) | 8 | 03_11: match |

**New result: repeat layoffs (global sample).**
- **688 companies** have 2 or more events, and 2,779 have exactly one.
- The top companies are Microsoft (22), Boeing (19), Intel (19), and Bosch, Nestle and Walmart (18 each).
- Setting aside the 42 possible internal duplicates changes the buckets only slightly: for 2 events, 401 becomes 397.

---

## 8. Files created or modified

- **New**
  - Plan and design:
    - `reports/PHASE4_IMPLEMENTATION_PLAN.md`
    - `reports/PHASE4_SCHEMA_AND_RELATIONSHIPS.md`
    - this report
  - SQL:
    - `sql/README.md`
    - `sql/ddl/01_schemas.sql` … `05_views.sql`
    - `sql/analytics/01-19*.sql`
  - Code:
    - `src/phase4_spec.py`
    - `src/phase4_config.py`
    - `src/phase4_load.py`
    - `src/phase4_checks.py`
    - `src/phase4_analytics.py`
  - Tests:
    - `tests/test_phase4_unit.py`
    - `tests/test_phase4_db.py`
  - Notebook: `notebooks/04_postgresql_load_and_sql_analysis.ipynb` (19 code cells, executed)
  - Configuration: `.env.example` (placeholders only) and `.gitignore`. It is new; the project had none.
  - Outputs in `reports/phase4/`:
    - `phase1_3_baseline_hashes.csv`
    - `sql_reconciliation.csv`
    - `query_results/*.csv` (19 files)
- **Modified:** `NOTEBOOK_PLAN.md` (Phase 4 row and folder layout only)
- **Not modified** (verified by hash, 92 files): `data/raw`, `data/interim`, `data/processed`, notebooks 01-03, the Phase 1-3 code and tests, and `reports/eda`, `reports/figures` and `reports/audit`

---

## 9. Known limitations and unresolved decisions

**Data limitations kept on purpose:**
- About 50% of headcounts and 78% of workforce % are missing in the global data.
- 31% of sectors are Unknown.
- 470 events have no country, and 6 country values are unresolved.
- The duplicate candidates are unreviewed.
- 2026 is partial, and May-June 2026 is probably incomplete. It is labelled in queries 01, 02 and 19.
- The tech file is low confidence.

**Pipeline limitations:**
- A reload replaces the core tables as a whole (atomically). It does not apply partial updates.
- The database tests need a server where the user can create databases.
- Only tested on Linux with PostgreSQL 16, not on your Windows machine.

**Decisions still open from Phase 3** (nothing was changed for them):
1. Relabel the 7 values that aren't countries, or keep them as Unresolved?
2. Confirm the 2 names added to the company-review list.
3. Keep the 7 capitalisation fixes?
4. For later phases, cut off the data at April 2026, or keep all months with a warning? I recommend keeping them with a warning, which is what the SQL does now.
5. Repeat-layoff analysis: now built in SQL (queries 15-16). Should it also be added to notebook 03?

**Also still open:** review of the 18 + 97 candidate pairs, and whether to create a GitHub repo. A `.gitignore` is now in place for that.

---

## 10. Exact commands to reproduce

```bash
# one time: create role + UTF-8 database (sql/README.md step 2), then
cp .env.example .env                       # fill in PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD
python src/phase4_load.py                  # load + 142 checks (exit 0 = committed)
python src/phase4_load.py                  # rerun: same counts, nothing doubles
python src/phase4_analytics.py             # 19 queries + reconciliation with Phase 3
LAYOFFS_ENABLE_DB_TESTS=1 python -m pytest -q tests   # 184 tests
jupyter nbconvert --to notebook --execute notebooks/04_postgresql_load_and_sql_analysis.ipynb
```

**Clean-room verification that was actually run:**
1. In a copy of the project, I deleted all generated data.
2. I ran notebooks 01, 02 and 03 (0 errors).
3. I created a new empty UTF-8 database.
4. I loaded twice: both runs succeeded with 142/142 checks, and there were 5,035 rows after the second load.
5. I ran the analytics: 19/19 queries succeeded and 0 cells differed.
6. I ran notebook 04 (0 errors) and the tests (184 passed).
7. All 13 Phase 3 CSVs, all 19 query results and the Phase 2 manifest were byte-identical to the project copy. The reconciliation summary differed only in its timing column.
8. I dropped the verification database afterwards.

---

## 11. Not executed or not verified

- **Not run on your Windows PC, or with your PostgreSQL installation.** The setup steps for Windows are written but untested.
- **Not tested on PostgreSQL versions other than 16.15.** The SQL uses features available since version 13.
- **No GitHub repository was created**, so "version-controlled" means the files are ready to commit and `.env` is excluded.
- **No Power BI views and no ML were built** (out of scope).
- **Performance was not measured beyond this small dataset.** A load takes about 2.5 seconds.
