# Setup on Windows

Every command is labelled **[tested]** (run on the project PC on 24–25 Oct 2026: Windows 11, Python 3.14.6, PostgreSQL 18.6, Power BI Desktop 26.10) or **[not tested]**. Run commands in PowerShell from the project folder.

> **Public copy of this repository:** it does not include `data/processed/` or the tech raw file (see [PUBLIC_RELEASE.md](../PUBLIC_RELEASE.md)). There you can install, run the 135 tests that need neither, read the SQL and open the statistics outputs, but steps 4–7 need the full data.

## 1. Install the software

| Software | Notes |
|---|---|
| Python 3.11 or later | Tested with 3.14.6. Tick "Add python.exe to PATH" |
| PostgreSQL 13 or later | Tested with 18.6. The installer asks for a password for the `postgres` user: remember it |
| Power BI Desktop | Free, from the Microsoft Store or microsoft.com. Only needed for the dashboard |
| Git | Optional, to clone the repository |

## 2. Python packages

```powershell
python -m pip install -r requirements-lock.txt
```
**[tested]** (all packages already satisfied on the project PC). `requirements-lock.txt` pins the exact versions that passed all tests; `requirements.txt` gives minimum versions if you prefer newer ones **[not tested with newer versions]**.

Optional virtual environment **[not tested]**:
```powershell
python -m venv .venv; .venv\Scripts\Activate.ps1; python -m pip install -r requirements-lock.txt
```

## 3. Credentials (never committed)

```powershell
Copy-Item .env.example .env
notepad .env
```
**[tested]** Set `PGHOST=localhost`, `PGPORT=5432`, `PGDATABASE=layoffs_db`, `PGUSER=postgres` and type your own password after `PGPASSWORD=`. `.env` is listed in `.gitignore`. Variables already set in your shell take priority over `.env`.

## 4. Create the database (once)

The loader needs an empty UTF-8 database. In pgAdmin's Query Tool or *SQL Shell (psql)*, connected as `postgres`:
```sql
CREATE DATABASE layoffs_db ENCODING 'UTF8' TEMPLATE template0;
```
**[tested]** (run on the project PC through Python with the same statement; not through psql). If `layoffs_db` already exists, skip this: the loader never drops anything.

## 5. Tests that do not need PostgreSQL

```powershell
python -m pytest -q tests
```
**[tested]** Full local data: **191 passed, 23 skipped** (the 23 are the database tests). Public copy: **135 passed, 79 skipped**.

## 6. Load the database and run the SQL

```powershell
python src/phase4_load.py
python src/phase4_analytics.py
python src/phase5_export_bi.py
```
**[tested]**
- Loader: ends with `OK: 142 checks passed; committed (run N)` and 5,035 rows in `core.layoff_events`. Exit code 0 = loaded; 1 = a check failed and nothing was committed; 2 = settings or server problem. Running it again is safe (3 runs gave identical content).
- Analytics: `19 queries run, 19 succeeded, 16 reconciled with Phase 3, 0 problem(s).`
- Export: `14 of 14 headline numbers match` and writes `powerbi/headline_reconciliation.csv`.

## 7. All tests, including the database

```powershell
$env:LAYOFFS_ENABLE_DB_TESTS = "1"; python -m pytest -q tests
```
**[tested]** **214 passed.** These tests create and drop their own `layoffs_test_<random>` databases; they never touch `layoffs_db`. The PostgreSQL user needs the CREATEDB privilege.

## 8. Notebooks

Notebook 05 (statistics) was run on the project PC with nbclient **[tested]**:
```powershell
python -c "import nbformat; from nbclient import NotebookClient; p='notebooks/05_sample_validity_and_repeat_layoffs.ipynb'; nb=nbformat.read(p, as_version=4); NotebookClient(nb, timeout=600, kernel_name='python3', resources={'metadata': {'path': 'notebooks'}}).execute(); nbformat.write(nb, p)"
```
Interactive use: `python -m jupyter notebook` **[not tested]**.

## 9. Power BI dashboard

```powershell
python src/phase5_build_pbip.py
```
**[tested]** Writes `powerbi/LayoffsDashboard.pbip` with your folder in its `ProjectFolder` parameter. Then:
1. Double-click `powerbi\LayoffsDashboard.pbip` **[tested]**.
2. Click **Home → Refresh**. When asked, choose **Database**, enter `postgres` and your password, and click **Connect**. If asked about privacy levels, tick **Ignore privacy levels** and click **Save** **[tested]**.
3. Press **Ctrl+S** to keep the loaded data **[tested]**.
4. Compare the cards with `powerbi/headline_reconciliation.csv` (see [`reports/POWERBI_VALIDATION.md`](../reports/POWERBI_VALIDATION.md)).
5. Optional: **File → Save as → .pbix** and **File → Export → Export to PDF** **[not tested]**.

## 10. Public release (maintainer only)

```powershell
python src/make_public_release.py
```
**[tested]** Rebuilds the `public-release` branch from `main` without tech-derived data. It does not push.

## Troubleshooting

- **Loader exit code 2 / "password authentication failed":** check `.env` (no spaces or quotes around the password).
- **"database is not UTF-8":** create it again with `ENCODING 'UTF8' TEMPLATE template0` (step 4) under a new name and set `PGDATABASE`.
- **Power BI shows "(Blank)":** the data has not been refreshed yet (step 9.2).
