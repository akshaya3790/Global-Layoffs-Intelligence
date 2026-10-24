# Phase 4 implementation plan (Step 1 audit result)

Written on 2026-10-23, **before** any Phase 4 code or schema was created.

## 1. Audit of the current project (actually run)

| Item | Finding |
|---|---|
| Repository layout | `data/{raw,interim,processed}`, `notebooks/01-03`, `src/` (5 modules), `tests/` (7 files + fixtures), `reports/` (audit, eda, figures, phase reports), `NOTEBOOK_PLAN.md`, `requirements.txt`. There is **no** `sql/` folder yet. |
| Git / `.gitignore` | The project folder is **not** a git repository, and it has **no `.gitignore`**. One will be added, so `.env` and passwords stay out of version control once the repo is created. |
| Configuration | No config or credential files exist. |
| Dependencies | `requirements.txt` already lists `psycopg2-binary>=2.9` and `sqlalchemy>=2.0`. Installed versions: psycopg2 2.9.13, pandas 3.0.5, pytest 9.1.1. |
| Existing tests | **116 passed, 0 failed** (`python -m pytest -q tests`), run before any Phase 4 change |
| Phase 2 manifest | The SHA-256 of all 10 processed files **matches** `phase2_output_manifest.csv` |
| Phase 1-3 baseline | 92 files under `data/`, `notebooks/`, `src/`, `tests/` and `reports/{eda,figures,audit}` were hashed into `reports/phase4/phase1_3_baseline_hashes.csv`. They are compared again at the end of Phase 4. |
| PostgreSQL | **PostgreSQL 16.15** server and client are installed in this cloud environment. The default cluster `main` (port 5432) is **down and was left untouched**. A **separate, new cluster `layoffs` on port 5433** was created for this project, with role `layoffs_app` (password kept outside the project) and an empty database `layoffs_db`. No existing database was overwritten. |

## 2. Processed files: actual shape and keys

| File | Rows | Cols | Natural key (verified unique) | Goes to PostgreSQL? |
|---|---|---|---|---|
| `layoff_events.csv` | 5,035 | 69 | `event_key`; also (`source_dataset`, `source_row_number`) | **Yes**, the main table |
| `layoff_event_departments.csv` | 70 | 8 | (`event_key`, `department_position`) | **Yes**, the bridge table |
| `quality_issues.csv` | 4,886 | 5 | (`event_key`, `quality_flag`) | **Yes** |
| `transformation_log.csv` | 16 | 6 | `rule_id` | **Yes** (reproducibility) |
| `field_lineage.csv` | 54 | 3 | (`canonical_field`, `source_dataset`, `source_field`) | **Yes** (lineage) |
| `company_name_mapping.csv` | 3,532 | 6 | (`source_dataset`, `company_name_raw`) | **Yes**. Every event's raw name is present, with 0 mismatches. |
| `industry_mapping.csv` | 77 | 4 | (`source_dataset`, `industry_raw`) | **Yes**. Every event's label is present, with 0 mismatches. |
| `cross_source_industry_disagreements.csv` | 9 | 8 | `event_key_tech` | **Yes** |
| `possible_duplicate_pairs.csv` | 18 | 19 | `pair_id` | **Yes**. These pairs are pending review, and none is resolved. |
| `excluded_candidate_pairs.csv` | 97 | 26 | `excluded_pair_id` | **Yes**. These were excluded by rule and never reviewed. |
| `phase2_output_manifest.csv` | 10 | 3 | `file` | **No.** It is used to verify the input files before every load, and its hashes are recorded in the load audit table. |

Other checks I ran on the actual values:
- **No literal text** `NULL`, `NaN`, `None`, `NA` or `N/A` appears in any field.
- **No quoted empty strings.** An empty field always means missing.
- `employees_laid_off`, `total_employees`, `severance_weeks` and `news_mentions` are written as `50.0` but are **always whole numbers**, so they become INTEGER.
- `workforce_pct` has up to 6 decimals (e.g. `33.333333`), so it becomes NUMERIC with no fixed scale and **no rounding**.
- `ai_related` has **3 values** (Yes / Partial / No), so it stays **TEXT, not BOOLEAN**.
- Quality-flag columns are True / False / empty, where empty means the check was **not computed** for that source. They become BOOLEAN, with NULL kept as "not computed".

## 3. Conflicts found, and how I resolved them

1. **`NOTEBOOK_PLAN.md` said "star schema (fact + company, sector, country, date dimensions)".** Your Phase 4 brief says: *do not introduce a company dimension or other normalization that loses the original company name, source-specific industry or source-row traceability.* **I follow the brief:**
   - one wide event table that keeps every original column;
   - the existing mapping tables as lookups, linked by foreign keys;
   - a small `source_datasets` reference table.

   There is no company, sector, country or date dimension. The plan will be updated to say this.
2. **The column `column` in `transformation_log.csv` is a reserved word in SQL.** It is renamed to `column_name` in PostgreSQL. This is the only rename, and it is documented.
3. **Value-range rules (headcount > 0, percentage 0-100) are not database constraints.** Phases 1-2 deliberately keep out-of-range values and flag them (`qc_*`), so a CHECK constraint would reject data the earlier phases decided to keep. These rules are checked by validation queries instead.
4. **The 5 decisions from Phase 3 are still open.** The 7 values that aren't countries stay as loaded (region `Unresolved`), and May-June 2026 is labelled *partial / possible collection lag* in the queries.

## 4. Blocking issues

**None.** PostgreSQL is available here. On your own machine you need PostgreSQL 13 or later; the setup steps are in `sql/README.md`.

## 5. Build order (each step is validated before the next)

1. Schema document and DDL (`reports/PHASE4_SCHEMA_AND_RELATIONSHIPS.md`, `sql/ddl/`).
2. Configuration: `.env.example`, `.gitignore`, connection helper with clear error messages.
3. Loader (`src/phase4_load.py`). It runs these steps in order:
   1. pre-flight: headers, types, hashes against the manifest;
   2. load into staging;
   3. type and key checks;
   4. replace the core tables in **one transaction**;
   5. integrity checks;
   6. commit, or roll back and record the failure.
4. Integrity and reconciliation checks (`src/phase4_checks.py`). These are stored in `audit.validation_results` on every load.
5. Analytical SQL (`sql/analytics/*.sql`), plus a runner that reconciles results with the Phase 3 chart data.
6. Tests:
   - unit tests that need no database;
   - integration tests in an isolated throwaway database (`layoffs_test_*`), including a repeat load, invalid input and rollback.
7. Notebook 04 (project convention), a fresh-copy rerun, a regression check against the baseline hashes, and the report.
