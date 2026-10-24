# Notebook plan: Global Layoffs Intelligence

Each phase is one notebook in `notebooks/`. A phase starts only after you review the previous one.
Every notebook uses numbered sections with: an objective (plain language), a concept explanation, small code cells, and a validation or interpretation cell.

| Phase | Notebook | Purpose | Main outputs | Status |
|---|---|---|---|---|
| 1 | `01_data_intake_and_quality_audit.ipynb` | Inspect schemas, count records per source, measure missing values, validate dates and numbers, find duplicates inside and across files. **Changes nothing.** | `data/interim/*_staged.csv`, `data/interim/possible_duplicate_pairs.csv`, `reports/audit/*` | **Done, awaiting your review** |
| 2 | `02_data_cleaning.ipynb` | Apply the decisions you approve: standard country and sector names, clean company names, whitespace, apply your duplicate-pair decisions. Original columns kept next to cleaned ones. | `data/processed/layoffs_clean.csv`, `data/processed/tech_ai_layoffs_clean.csv`, cleaning log | Not started |
| 3 | `03_exploratory_analysis.ipynb` | Trends by year/month, sector, country, repeat layoffs, COVID era, AI-related layoffs. Matplotlib charts. | `reports/figures/03_*.png`, key findings | Not started |
| 4 | `04_postgresql_load_and_sql_analysis.ipynb` + `sql/` | Star schema in PostgreSQL (fact + company, sector, country, date dimensions), load, 15-20 business queries (CTEs, window functions), reporting views for Power BI. | `sql/*.sql`, database `layoffs_db` | Not started |
| 5 | `05_ml_layoff_risk_model.ipynb` | Layoff risk (severity) classifier: predict whether an event is a major layoff (>= 500 people or >= 20% of staff) from sector, region, timing and company history. Baseline vs tree model, leakage check, explainability. | `models/`, predictions table in PostgreSQL | Not started |
| 6 | `powerbi/DASHBOARD_GUIDE.md` + `README.md` | Power BI pages, visuals and DAX measures (you build the .pbix), project README and resume bullets. | guide, README | Not started |

## Python kernel
See the "How to run this notebook" cell at the top of notebook 01. In short: create `.venv`, `pip install -r requirements.txt`,
register it with `python -m ipykernel install --user --name layoffs-env --display-name "Python (layoffs-env)"`, and pick that kernel in Jupyter or VS Code.

## Folder layout
```
global-layoffs-intelligence/
├── data/
│   ├── raw/          # original files, never modified (checked by SHA-256 in notebook 01)
│   ├── interim/      # staged copies with quality flags, duplicate-pair review file
│   └── processed/    # cleaned data (Phase 2)
├── notebooks/
├── sql/              # Phase 4
├── models/           # Phase 5
├── powerbi/          # Phase 6
├── reports/
│   ├── audit/        # audit log, missing-value tables, raw-file fingerprints
│   └── figures/
├── NOTEBOOK_PLAN.md
└── requirements.txt
```
