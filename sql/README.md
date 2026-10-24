# PostgreSQL setup and run guide (Phase 4)

These steps were tested on **PostgreSQL 16.15** (Ubuntu 24.04, Python 3 + psycopg2 2.9.13). Any PostgreSQL version from **13** up should work. Run every command from the **project root folder**.

## 0. Prerequisites

- PostgreSQL server 13 or later, installed and running. On Windows, use the installer from postgresql.org; it includes `psql` and pgAdmin.
- The project's Python environment (`pip install -r requirements.txt`), which includes `psycopg2-binary`.
- Phases 1-2 already run, so `data/processed/*.csv` exist and match `phase2_output_manifest.csv`.

## 1. Credentials (never committed)

```bash
cp .env.example .env              # Windows PowerShell: Copy-Item .env.example .env
```

Edit `.env` and set `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER` and `PGPASSWORD`. `.env` is listed in `.gitignore`. Variables already set in your shell take priority over `.env`.

## 2. Create a dedicated role and an empty UTF-8 database (one time)

Connect as an administrator (on Windows, open *SQL Shell (psql)* or pgAdmin's Query Tool as `postgres`) and run:

```sql
CREATE ROLE layoffs_app LOGIN CREATEDB PASSWORD 'choose-a-password';   -- CREATEDB only needed for the DB tests
CREATE DATABASE layoffs_db OWNER layoffs_app ENCODING 'UTF8' TEMPLATE template0;
```

Use a **new, empty** database. The loader only creates the schemas `staging`, `core` and `audit`, and it never drops anything. It refuses to run if:
- the database is not UTF-8;
- an existing table in those schemas has different columns;
- `core.layoff_events` already has rows that this pipeline didn't load.

## 3. Load the data

```bash
python src/phase4_load.py
```

It runs pre-flight, schema, staging, core and validation in order, and ends with the row count of every table. Running it again is safe: the core tables are replaced with identical rows in one transaction, so counts never double.

| Exit code | Meaning |
|---|---|
| 0 | Loaded, and every check passed |
| 1 | **Pipeline failure**: bad input, a constraint violation or a failed check. Nothing was committed, and the previous data is untouched. The reason is printed and stored in `audit.load_runs`. |
| 2 | **Environment problem**: settings missing, server not running, or login refused. Nothing was attempted. |

## 4. Run the analytical queries and reconcile them with Phase 3

```bash
python src/phase4_analytics.py
```

This runs all `sql/analytics/*.sql` in read-only transactions, writes each result to `reports/phase4/query_results/`, and writes a cell-by-cell comparison with `reports/eda/` to `reports/phase4/sql_reconciliation.csv`. Each query file can also be run on its own in psql or pgAdmin:

```bash
psql -f sql/analytics/02_yearly_events_and_known_job_cuts.sql
```

## 5. Tests

```bash
python -m pytest -q tests                               # database tests are SKIPPED
LAYOFFS_ENABLE_DB_TESTS=1 python -m pytest -q tests     # also runs the 18 database tests
# PowerShell:  $env:LAYOFFS_ENABLE_DB_TESTS = "1"; python -m pytest -q tests
```

The database tests create throwaway databases named `layoffs_test_<random>` and drop them afterwards. They never touch `layoffs_db`.

## 6. Checking a load

```sql
SELECT run_id, started_at, status, error_stage, error_message FROM audit.load_runs ORDER BY run_id DESC;
SELECT file_name, csv_rows, staging_rows, core_rows, matches_manifest FROM audit.load_files WHERE run_id = <n>;
SELECT check_id, expected, actual FROM audit.validation_results WHERE run_id = <n> AND NOT passed;
```

## 7. Rollback and clean-up

- **A failed load needs no clean-up.** The transaction (staging and core together) was rolled back, so `core` still holds the last good load. Only `audit` shows the attempt.
- **To undo a successful load**, rerun the loader on the verified files. It always reproduces the same content.
- **To remove everything Phase 4 created** (destructive, so only do it deliberately): drop the database you created in step 2.

  ```sql
  DROP DATABASE layoffs_db;
  ```

  Nothing in this project runs this for you.
