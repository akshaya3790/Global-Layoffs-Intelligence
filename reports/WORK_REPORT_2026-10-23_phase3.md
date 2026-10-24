# Work report: Phase 3, exploratory analysis and charts

**Result:** `notebooks/03_exploratory_analysis.ipynb` is built and verified.
- A fresh copy ran notebooks 01, 02 and 03 back to back with **0 errors**.
- **116 of 116 tests** pass: the 93 existing ones plus 23 new Phase 3 tests.
- The fresh copy and the project copy produced **identical** chart data and chart images.

Raw files and Phase 2 outputs are unchanged. No PostgreSQL, ML or Power BI work was started.

---

## 1. What I did, step by step

1. **Re-verified Phase 2 first, in a fresh copy.**
   - Notebook 01 ran 41 of 41 cells and notebook 02 ran 36 of 36, with 0 errors.
   - Notebook 02's checks: 75 of 75 passed.
   - Tests: 93 of 93 passed.
   - The Phase 2 output manifest was identical to the project copy.
2. **Wrote `src/phase3_eda.py`.** Every aggregation behind a chart lives here, with the filtering rules written at the top (table below). The notebook calls these functions, and the tests check them.
3. **Built notebook 03.** It has 11 numbered sections. Each section has an objective, a plain-language explanation, small code cells and a validation cell. There are 24 code cells and 13 markdown cells.
   - Before analysing anything, it checks that `layoff_events.csv` and the department table still match the Phase 2 SHA-256 manifest.
4. **Exported 12 charts and 13 chart-data CSVs.** Every chart in `reports/figures/03_*.png` has its exact input table saved in `reports/eda/03_*.csv`, so any number on a chart can be checked.
5. **Looked at every chart and fixed what was wrong:**
   - Two labels overlapped on the monthly chart.
   - In the heatmap, the Unknown row was coloured blue and set the colour scale. It is now grey and kept off the scale.
   - Labels sat on top of the markers on the US-share chart.
   - A bar label touched the title on the workforce-% chart.
   - 2026 is now marked as partial on every year axis.
6. **Wrote 23 tests** (`tests/test_phase3_eda.py`), then **proved they catch the defects you were worried about**:
   - I temporarily made the code count missing headcount as 0, and 2 tests failed.
   - I temporarily made it drop the duplicate-candidate rows, and 13 tests failed.
   - I put the correct code back, and all 116 tests pass.
7. **Checked my own findings against the numbers and corrected one.** My draft said "2020 is the peak year even without furloughs". That is **wrong**: without its 105 furloughs, 2020 has 863 events, which is below 2023's 885. The finding now says the peak depends on counting furloughs.

### Filtering rules (applied to every chart and tested)

| Rule | Meaning |
|---|---|
| R-SOURCE | Global charts use only the 5,000 global rows. The 35 tech rows have their own section, coloured orange, and are never added to global numbers. |
| R-EVENTS | One row = one event. Furloughs, duplicate candidates and flagged rows are **all kept**. A sensitivity table shows what happens if they are excluded. |
| R-JOBS | "Verified jobs cut" sums only known headcounts. A group with no known headcount shows **blank (NaN), never 0**. Every jobs figure is shown with its coverage %. |
| R-PCT | Workforce-% statistics use only the 1,121 rows that have a percentage. |
| R-UNKNOWN | A missing industry or country is shown as **Unknown** (grey). Values that aren't countries are shown as **Unresolved** and are not reassigned. |
| R-PARTIAL | 2026 (Jan to 14 Jun) is labelled partial. |
| R-SAMPLE | The global file is a 26% sample, so counts describe the sample, not the market. |

---

## 2. Validation results (all actually run)

| Check | Result |
|---|---|
| Fresh copy: notebooks 01, 02 and 03 in sequence | 41/41, 36/36 and 24/24 code cells run in order, with 0 errors and 0 stderr |
| Notebook 02 checks | 75 of 75 passed |
| Notebook 03 inline validations | All passed. They are `assert` cells, so the notebook would stop on any failure. |
| Full test suite (fresh copy and project copy) | **116 passed**, 0 failed |
| Reproducibility | All **13 chart-data CSVs** and all **12 PNGs** are byte-identical between the fresh copy and the project copy. The Phase 2 manifest is identical. |
| Shared-folder copies | Every file is identical to the project copy. The only exception is that the shared folder adds a content-credentials metadata block (about 5.8 KB) to each PNG. The image pixels were compared and are identical. |
| Raw files | SHA-256 unchanged (`a181c6ce…`, `f011a4d0…`) |
| Input check in notebook 03 | `layoff_events.csv` and `layoff_event_departments.csv` match the Phase 2 manifest |

**What the reconciliation tests check:**
- Yearly, monthly, industry, region and country event totals each equal 5,000.
- Verified jobs per table equal the sum of the known headcounts (2,788,908 from 2,489 events).
- Missing values are still missing: 2,511 headcounts and 3,879 percentages.
- The size bands cover exactly 2,489 rows and the % bands exactly 1,121.
- The 4 Unresolved countries with no headcount show blank, not 0.
- The 42 internal duplicates and 18 cross-source candidates are still counted.
- The quality-flag counts equal the canonical columns, and "not computed" stays separate from False.
- The tech totals are 35, the department links are 70 with weights summing to 35, and there are 6 suspect dates.
- The saved chart CSVs equal a fresh recomputation.

---

## 3. Charts produced (`reports/figures/`)

| File | What it shows |
|---|---|
| `03_01_monthly_events.png` | Events per month with a 3-month average, and the COVID period shaded |
| `03_02_yearly_events_and_jobs.png` | Events per year and verified jobs per year as **two separate panels** (not a dual axis), with the coverage % printed |
| `03_03_industry_ranking.png` | 17 industry groups, Unknown in grey |
| `03_04_industry_share_by_year.png` | Heatmap of each group's share of each year |
| `03_05_region_events.png` | Regions, including Unknown (470) and Unresolved (6) |
| `03_06_top_countries_outside_us.png` | Top 15 countries outside the US. The table under it lists Unknown and the 6 unresolved values. |
| `03_07_us_share_by_year.png` | US share of events with a known country |
| `03_08_size_and_pct_distribution.png` | Size bands (n = 2,489) and workforce-% bands (n = 1,121) |
| `03_09_missingness_global.png` | Share of rows missing each field |
| `03_10_quality_flags_global.png` | Records per quality flag |
| `03_T1_…`, `03_T2_…` (orange) | **Tech file only:** reasons, departments, AI flag, severance |

---

## 4. Major findings (global, 5,000-event sample)

**Supported:**
- **F1** 2020 had the most events (968), peaking in April 2020 (165). **This depends on furloughs.** Without them, 2020 (863) is just below 2023 (885).
- **F2** Activity rose again from 2023 and stayed high through 2025: 885, 791 and 762 events, against about 40 a month before COVID and 55-95 a month in 2023-25. Excluding duplicate candidates changes no year by more than 14 events.
- **F3** Verified jobs cut: about 752k in 2020, and about 417-434k a year in 2023-25. **These are lower bounds**, because coverage is 42-53% per year.
- **F4** Most layoffs are small. The median verified cut is 200, 70% cut fewer than 500 people, and 6% cut 5,000 or more.
- **F5** The median workforce share cut is 15%. This is based on only 22% of events.
- **F6** Retail & Consumer is the largest known industry group in every year (680 events). Finance & Fintech (375) and Healthcare (298) follow.
- **F7** Travel & Transport's share was 8% in 2020-21, against 1-3% in other years. Software & IT peaked at 10% in 2023.
- **F8** The US has the most events (1,917). Its share of events with a known country went from about 28% in 2021 to 44-48% in 2023-26. Next are the UK (564), India (241) and Germany (226).

**Tech file (separate, lower confidence, 35 rows):**
- `AI_Related` is Yes for 9 events, Partial for 6 and No for 20.
- Engineering is involved in 15 events, Sales in 11 and Marketing in 9.
- Severance is 4-20 weeks, with a median of 12.
- No market-wide claims are drawn from this file.

---

## 5. Caveats

1. **Sample.** The global file is a 26% sample, so the counts can't be scaled up to market totals.
2. **Jobs totals are lower bounds.** Half of the events have no verified headcount, and those were kept missing, not counted as 0.
3. **Unknown is the largest industry (31%).** Rankings below the top 2-3 groups are fragile.
4. **New observation: the last two months look incomplete.** May 2026 has 12 events and June 2026 has 23 (the data ends 14 June), against 60-90 in earlier months. This is probably a collection lag in the source. **It is not a decline.** I flagged it in the notebook and changed nothing.
5. **Duplicates are unresolved but don't change the conclusions** (Section 8 of the notebook).
6. **Descriptive only.** Nothing here shows causes.

---

## 6. Decisions needed from you

**Carried over from Phase 2 (still unanswered, so nothing was changed):**
1. **The 7 values that aren't countries:** `Arizona`, `Nevada`, `New York`, `Rhode Island`, `Quebec`, `Sa` (event country) and `Au` (HQ country). Should I relabel them (e.g. Arizona → United States, Quebec → Canada) or keep them as Unresolved? They are currently shown as Unresolved in the charts.
2. **The 2 names I added to the company-review list:** Tata Steel in the Netherlands and Whole Foods Market Southern Region — Bake House. Please confirm they should stay under their raw names, pending review.
3. **Case harmonisation:** keep the 7 capitalisation changes (e.g. `SNAP` → `Snap`), or leave capitalisation as it was in the raw data?

**New in Phase 3:**

4. **May-June 2026:** should later phases (ML, Power BI) **cut off the data at April 2026** because of the probable collection lag, or keep all months with a warning? I recommend keeping all rows and adding a "data complete through April 2026" note to trend visuals.
5. **Repeat layoffs (companies with more than one event):** this was in the original plan for notebook 03 but not in your Phase 3 list, so I didn't build it. Should I add it?

**Still open from earlier:** review of the 18 + 97 candidate pairs, and whether to create or push a GitHub repo.

---

## 7. Files

- **New:**
  - `notebooks/03_exploratory_analysis.ipynb`
  - `src/phase3_eda.py`
  - `tests/test_phase3_eda.py`
  - `reports/figures/03_*.png` (12)
  - `reports/eda/03_*.csv` (13)
  - this report
- **Changed:** `NOTEBOOK_PLAN.md` (Phase 3 status only)
- **Not changed:** `data/raw/*`, `data/processed/*`, `data/interim/*`, notebooks 01-02, the Phase 1-2 source code and tests, and the audit history

**How to run:** open the project folder in Jupyter with the *Python (layoffs-env)* kernel, run notebooks 01 and 02, and then run notebook 03 with *Run All*. Run the tests with `python -m pytest -q tests`.
