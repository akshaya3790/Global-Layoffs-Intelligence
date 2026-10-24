# Power BI dashboard: build guide

**Status (24 Oct 2026):** not built yet. Power BI Desktop is not installed on this PC. Everything the dashboard needs is ready: the SQL views (`sql/ddl/06_bi_views.sql`), the survival results (`reports/stats/`) and a CSV fallback (`powerbi/data/`, written by `python src/phase5_export_bi.py`).

Save the finished file as `powerbi/layoffs_dashboard.pbix`, with one screenshot per page in `powerbi/screenshots/` and a PDF export.

## 0. Before you start

1. Install **Power BI Desktop** (free) from the Microsoft Store.
2. Load the database: `python src/phase4_load.py` (this also creates the `v_bi_*` views).
3. Run `python src/phase5_export_bi.py`. It writes `powerbi/headline_reconciliation.csv`, the numbers every card must show.

## 1. Connect (Import mode)

*Get data → PostgreSQL database*. Server `localhost:5432`, database `layoffs_db`, **Import** (not DirectQuery). Sign in with the database user and password from your `.env`.
Select only: `core.v_bi_events`, `core.v_bi_company_summary`, `core.v_bi_quality`, `core.v_bi_benchmark`, `core.v_bi_kpis`, `core.v_tech_events`, `core.v_period_notes`.
Then *Get data → Text/CSV* for `reports/stats/km_curve_overall.csv`, `repeat_probability_by_industry.csv`, `repeat_probability_by_first_cut_size.csv` and `bootstrap_yearly.csv`.

**If the PostgreSQL connector fails:** import the same views from `powerbi/data/*.csv` instead.

## 2. Model

- Date table (*Modeling → New table*):
  `Date = ADDCOLUMNS(CALENDAR(DATE(2019,1,1), DATE(2026,6,30)), "Year", YEAR([Date]), "Month", FORMAT([Date], "yyyy-mm"))`
- Relationships: `Date[Date]` 1→* `v_bi_events[event_date]`; `v_bi_company_summary[company_name]` 1→* `v_bi_events[company_name]`.
- Leave `v_tech_events` **unrelated** to everything, so it can never be added to a global number.

## 3. Measures (DAX)

```DAX
Events = COUNTROWS(v_bi_events)
Companies = DISTINCTCOUNT(v_bi_events[company_name])
Events with headcount = CALCULATE([Events], v_bi_events[has_disclosed_headcount] = TRUE())
Events headcount unknown = [Events] - [Events with headcount]
Disclosed jobs cut (lower bound) = SUM(v_bi_events[employees_laid_off])
Median disclosed cut = MEDIAN(v_bi_events[employees_laid_off])
Disclosure rate % = DIVIDE([Events with headcount], [Events]) * 100
Events 2019 baseline = CALCULATE([Events], REMOVEFILTERS('Date'), v_bi_events[event_year] = 2019)
Events vs 2019 % = DIVIDE([Events], [Events 2019 baseline]) * 100
Unknown sector % = DIVIDE(CALCULATE([Events], v_bi_events[industry_group] = "Unknown"), [Events]) * 100
US share of known-country % = DIVIDE(CALCULATE([Events], v_bi_events[country] = "United States"),
                                     CALCULATE([Events], v_bi_events[country] <> "Unknown")) * 100
Repeat companies = CALCULATE(COUNTROWS(v_bi_company_summary), v_bi_company_summary[is_repeat_company] = TRUE())
Median days to next round = MEDIAN(v_bi_company_summary[days_to_second_event])
```

`MEDIAN` and `SUM` skip blanks, so undisclosed headcounts are never counted as 0. Never create a "layoff rate" measure: the global file has no company size.

## 4. Banner on every page

A text box across the top of each page:

> **26% company sample of news-reported layoffs (5,000 of 19,208 events). Counts are sample counts. Job figures are disclosed cuts only (lower bound). 2026 covers January to 14 June only.** Source: Fliar Research (2026), CC BY-NC 4.0.

## 5. Pages

| Page | Question | Cards | Visuals | Slicers |
|---|---|---|---|---|
| **1 Executive overview** | Is layoff activity unusual right now? | Events; Events vs 2019 %; Companies; Median disclosed cut; Disclosure rate % | Monthly events line (`month_start`) with a shaded May–Jun 2026 band; yearly events bars with error bars from `bootstrap_yearly.csv` | Year, region, industry group, `is_furlough` |
| **2 Industry and geography** | Where do layoffs concentrate, and what shifted? | Unknown sector %; US share of known-country % | Ranked bar by `industry_group` (Unknown in grey); 100% stacked column of industry share by year; top countries outside the US; region → country drill-down | Year, region |
| **3 Companies and repeat layoffs** | Which employers cut repeatedly, and how soon? | Repeat companies; Median days to next round; 12-month repeat probability (12.6%, from `repeat_probability_overall.csv`) | Repeat-company table (`events ≥ 2`, sorted); Kaplan-Meier step line from `km_curve_overall.csv` (x = t/30.44 months, y = 1 − survival); 12-month repeat probability by first-cut size | Industry group |
| **4 Data quality and coverage** | How far can I trust a number? | Disclosure rate %; Unknown sector %; event ratio range (0.256–0.271) | Disclosure rate by region and industry (`v_bi_quality`); sample ÷ full by year (`v_bi_benchmark`, events vs jobs); sensitivity table (query 19 result); a separate orange panel for the 35-row tech case study (`v_tech_events`) | none |

Warnings to place as small notes next to the relevant visual: "31% of events have no sector"; "9% have no country"; "brand names may be split across several names"; "industry differences in repeat risk are not statistically significant (p ≈ 0.13)"; "tech file: unknown source, company size derived from its own percentage, 6 suspect dates".

## 6. Reconcile before publishing

Every card must equal the `sql_value` in `powerbi/headline_reconciliation.csv`. Clear all slicers, compare each card, and add a ✓ in a copy of that file. Do not publish a page with a mismatch.
