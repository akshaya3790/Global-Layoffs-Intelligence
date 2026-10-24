# Data dictionary

Main tables and columns. Units: counts are numbers of events; headcounts are people; percentages are 0–100 unless stated; dates are ISO `YYYY-MM-DD`.

## `core.layoff_events` (= `data/processed/layoff_events.csv`, 5,035 rows × 69 columns)

One row per layoff event: 5,000 from the global sample (`source_dataset = 'fliar_global_sample'`, keys `G-…`) and 35 from the tech file (`'tech_layoffs_2025_2026'`, keys `T-…`). Full column-to-source mapping: `data/processed/field_lineage.csv`.

| Column | Type | Meaning |
|---|---|---|
| `event_key` | text, PK | `G-00001`… or `T-00001`… |
| `source_dataset`, `source_confidence` | text | which file; `high` (global) or `low` (tech) |
| `source_file`, `source_row_number` | text, int | raw file and CSV line the row came from |
| `company_name_raw`, `company_name` | text | as published; standardised (capitalisation only) |
| `company_name_review_status` | text | `auto` (4,996), `proposed` (26), `needs_review` (13) |
| `event_date`, `event_year`, `event_quarter`, `event_month` | date, int | event date and its parts |
| `date_reliability`, `date_flag_reason` | text | e.g. suspect tech-file dates |
| `industry_raw`, `industry_group` | text | source label; one of 16 groups or `Unknown` |
| `country_raw`, `country`, `region` | text | event location; NULL country = not given; region includes `Unknown`, `Unresolved` |
| `employees_laid_off` | int | global: **verified** headcount, NULL = not disclosed (never 0); tech: reported figure |
| `headcount_status` | text | `verified` (2,489), `failed_check` (1,314), `not_disclosed` (1,197), `reported_unverified` (35, tech) |
| `workforce_pct` | numeric | % of workforce cut, when reported (1,121 global events) |
| `is_furlough`, `is_permanent_layoff` | bool | temporary vs permanent |
| `possible_duplicate_group`, `possible_internal_duplicate` | text, bool | duplicate flags; nothing merged |
| `reason_category_derived`, `ai_mentioned_in_news_derived` | text, bool | keyword-derived; not used for findings |
| `ai_related`, `department`, `severance_weeks`, `total_employees`, `reason` | various | tech file only |
| `qc_*` (18 flags) and `qc_issue_count` | bool, int | Phase 1–2 quality flags and their count per row |

## Other `core` tables

| Table | Rows | Content |
|---|---|---|
| `company_name_mapping` | 3,532 | raw → standardised company name, method, review status |
| `industry_mapping` | 77 | raw industry label → group |
| `layoff_event_departments` | 70 | tech-file departments, one row per event × department |
| `quality_issues` | 4,886 | one row per event × raised flag |
| `transformation_log` | 16 | every cleaning rule, rows changed, examples |
| `field_lineage` | 54 | canonical column ← source column |
| `possible_duplicate_pairs` / `excluded_candidate_pairs` | 18 / 97 | cross-source pairs (pending review / excluded) |
| `cross_source_industry_disagreements` | 9 | tech vs global industry conflicts |

## Reporting views (`sql/ddl/05_views.sql`, `06_bi_views.sql`)

| View | Grain | Notes |
|---|---|---|
| `v_global_events` / `v_tech_events` | event | the only way global and tech rows are read |
| `v_bi_events` | global event (5,000) | ~25 dashboard columns, `has_disclosed_headcount`, `size_band`, `is_partial_period`, `period_note` |
| `v_bi_company_summary` | company (3,467) | events, first/last date, `days_to_second_event` (NULL = censored), disclosed jobs |
| `v_bi_quality` | dimension value | disclosure, Unknown-industry and missing-country rates by year, region, industry |
| `v_bi_benchmark` | year (8) | sample vs full events and disclosed jobs, ratios |
| `v_bi_kpis` | 1 row | every headline number |

## Audit tables

`audit.load_runs` (one row per load), `audit.load_files` (rows and hashes per file), `audit.validation_results` (142 checks per run).

## Statistics outputs (`reports/stats/`)

`benchmark_by_year.csv`, `benchmark_categories.csv`, `bootstrap_yearly.csv` (estimate and 90% bounds), `km_curve_overall.csv` (t in days, at_risk, events, survival, lo, hi), `repeat_probability_*.csv` (6/12/24-month repeat probability with 95% bounds), `logrank_tests.csv`.
