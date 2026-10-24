# Phase 2 Plan: Canonical Data Model and Column Mapping

**Status:** PLAN ONLY. Nothing has been implemented, and no data has been changed.
**Based on:** the real headers and values of `data/raw/layoffs_2019_2026_sample.csv` (global, 5,000 × 20) and `data/raw/tech_layoffs_2025_2026.csv` (tech, 35 × 16).
**Machine-readable mapping:** `reports/phase2_column_mapping_proposal.csv`

---

## 1. Design principles

1. **One row per source record.** The two files are *stacked*, not merged. A suspected duplicate is linked through a review table and is never collapsed automatically.
2. **Raw value kept next to the clean value.** Wherever a value is standardised, the original is kept in a `*_raw` column.
3. **Lineage is recorded.** Every canonical field records which source field it came from and which transformation was applied (`field_lineage` table).
4. **Missing means unknown.** A field that does not exist in a source is NULL for that source, never 0, `False` or `"No"`.
5. **Derived values are labelled.** Anything inferred instead of read from the source (for example a reason guessed from news text) goes in a separate column whose name says it was derived.

---

## 2. Proposed canonical tables

### 2a. `layoff_events` (main table, 5,035 rows = 5,000 + 35)

| Canonical field | Type | Global source | Tech source | Notes |
|---|---|---|---|---|
| `event_key` | text PK | `record_id` from Phase 1 (`G-00001`) | `record_id` (`T-00001`) | New. Stable and unique across sources. |
| `source_dataset` | text | constant `fliar_global_sample` | constant `tech_layoffs_2025_2026` | |
| `source_file` | text | file name | file name | Carried from Phase 1. |
| `source_row_number` | int | CSV line | CSV line | Carried from Phase 1. |
| `source_event_id` | text | `layoff_id` | **NULL** (the tech file has no ID) | **A-01** |
| `company_name_raw` | text | `company_name` | `Company` | Unchanged. |
| `company_name` | text | cleaned `company_name` | cleaned `Company` | **A-02** |
| `company_domain` | text | `company_domain` | NULL | |
| `event_date` | date | `date` parsed | `Date` parsed | Format already checked (0 failures). |
| `event_year`, `event_quarter`, `event_month` | int | recomputed from `event_date` | recomputed from `event_date` | Source `year`/`month`/`Year`/`Month`/`Quarter`/`Month_Name` agreed 100%, so they are dropped from this table and kept in lineage. |
| `date_reliability` | text | `as_reported` | `as_reported` or `suspect_date` | **A-07** (6 tech rows) |
| `industry_raw` | text | `sector` | `Industry` | |
| `industry_group` | text | mapped from `sector` | mapped from `Industry` | **A-04** (shared taxonomy) |
| `country_raw` | text | `country` | `Country` | |
| `country` | text | standardised `country` | standardised `Country` | **A-03**, **A-05** |
| `hq_country` | text | standardised `company_country` | NULL | **A-05** |
| `region` | text | from `country` | from `country` | |
| `city`, `state` | text | `company_city`, `company_state` (HQ) | split from `Location` (`"San Jose, CA"`) | **A-06** |
| `employees_laid_off` | int | `headcount_cut` (only present when verified) | `Employees_Laid_Off` | Keep NULLs. **A-08** |
| `headcount_status` | text | `headcount_status` | constant `reported_unverified` | **A-08** |
| `workforce_pct` | numeric | `pct_workforce` | `Percentage_Workforce` | 78% NULL in global. |
| `total_employees` | int | NULL | `Total_Employees` | **A-09** (do not derive for global) |
| `reason` | text | NULL | `Reason` | Source text only. |
| `reason_category_derived` | text | keyword tag from `news_excerpt` | mapped from `Reason` | **A-10** |
| `department` | text | NULL | `Department` (for example `"Engineering, Marketing"`) | **A-11** |
| `severance_weeks` | int | NULL | `Severance_Weeks` | |
| `ai_related` | text | NULL | `AI_Related` (`Yes`/`Partial`/`No`) | **A-12** |
| `ai_mentioned_in_news_derived` | bool | keyword flag on `news_excerpt` (40 rows mention AI) | NULL | **A-12** |
| `is_furlough` | bool | `is_furlough` | **NULL** (unknown, not False) | |
| `news_source` | text | `news_source` | NULL | |
| `news_url` | text | `news_url`, whitespace stripped | NULL | 6 values have padding |
| `news_excerpt` | text | `news_excerpt` | NULL | |
| `news_mentions` | int | `news_mentions` | NULL | Not to be used as an ML feature (leakage) |
| `source_profile_url` | text | `fliar_profile_url` | NULL | |
| `qc_*` flags | bool | from the Phase 1 staged file | from the Phase 1 staged file | Carried over unchanged |
| `duplicate_group_id` | text | set after your review | set after your review | **A-13** |
| `is_primary_record` | bool | set after your review | set after your review | **A-13** |

### 2b. `duplicate_review`
One row per candidate pair. It holds the Phase 1 columns plus `review_decision` (`same_event` / `different_event` / `unsure`), `decided_by`, `decided_at`, `primary_event_key` and `notes`. The pairs come from Phase 1; nothing is merged here.

### 2c. `field_lineage`
`canonical_field, source_dataset, source_field, transformation, approved_by, approved_at`. This is filled from the mapping CSV, so it lists every original field name, including the ones that were dropped (for example `Month_Name`).

### 2d. `cleaning_log`
One row per transformation run: `step, rule_id, rows_affected, example_before, example_after, run_at`.

---

## 3. Ambiguous mappings (need your decision)

| ID | Question | Facts from the data | My recommendation |
|---|---|---|---|
| **A-01** | Tech rows have no source ID. | 35 rows, and none has an ID column. | Use `event_key` (`T-000xx`) and leave `source_event_id` NULL. Don't invent one. |
| **A-03** | How should country labels be standardised? | Tech uses `USA`. Global has `United States (usa)`, `United States (cnmi)` and `United Kingdom (uk)`. | Map to plain names (`United States`, `United Kingdom`). Should `(cnmi)`, the Northern Mariana Islands, become United States or stay separate? I recommend keeping it separate. |
| **A-05** | Global has two country columns. Which one is `country`? | `country` (where the layoff happened) and `company_country` (HQ). Both are filled for 3,355 rows and **disagree for 239**. 1,175 have only `country`, and 470 have neither. | `country` = event location and `hq_country` = HQ. Don't fill one from the other. |
| **A-05b** | Is the tech `Country` the event location or the HQ? | `Location` looks like HQ cities (`Armonk, NY` is IBM's HQ). | Treat it as HQ-like, and say this in the docs. |
| **A-06** | How should tech `Location` be split? | Formats are `"City, ST"` and `"City, Country"` (`Dublin, Ireland`). | City = text before the comma. State only when the part after the comma is a 2-letter US code. |
| **A-04** | Which industry taxonomy? | Global has 49 sector labels (overlaps like `Consumer` / `Consumer Goods`, `Fintech` / `Financial Services`). Tech has 27 labels (`Search/AI`, `SaaS/CRM`, `Automotive/EV`). | About 15 shared `industry_group` values, with a mapping table you approve. For tech labels with a slash, map on the first part. |
| **A-08** | How do the two sources' headcount reliability compare? | Global numbers exist only when `verified`. The tech file's source and method are unknown, and its numbers are internally very consistent (within 2%). | Label tech rows `reported_unverified` so totals can be filtered by reliability. |
| **A-10** | Derive a reason for global rows? | Global has no reason field, only news text (4,990 excerpts). | Yes, but only in `reason_category_derived`, with the keyword rules published. `reason` stays NULL. |
| **A-11** | How should multi-value departments be stored? | Values like `"Engineering, Marketing"`. | Keep the original text, and add a `layoff_event_departments` bridge table (one row per department) for Power BI. |
| **A-12** | Should AI-related be inferred for global rows? | Only the tech file has `AI_Related`. 40 global excerpts mention AI. | Keep `ai_related` NULL for global. Use the separate derived flag and never mix the two in one chart without a label. |

---

## 4. Transformations that need your approval

| ID | Transformation | Rows affected (from Phase 1) | Reversible? |
|---|---|---|---|
| **A-02** | Clean company names: trim, remove legal suffixes for the *clean* column only, and apply a hand-reviewed mapping for sentence-like names (for example `Electric-car maker Tesla Inc. TSLA` → `Tesla`) and aliases (`X (Twitter)` ↔ `Twitter`) | 198 flagged global names, plus 1 tech alias | Yes (raw kept) |
| **A-03** | Standardise country labels | 35 tech rows (`USA`) plus global rows with bracketed suffixes | Yes (raw kept) |
| **A-04** | Industry taxonomy mapping | all 5,035 rows (1,564 global rows have no sector and become `Unknown`) | Yes (raw kept) |
| **A-07** | Mark 6 tech rows as `suspect_date` (same headcount as a 2023-24 global event): Twitch, Dell, Roku, Accenture, Unity, Adobe | 6 | Yes (flag only, date unchanged) |
| **A-13** | Apply your duplicate decisions: link pairs into `duplicate_group_id` and choose a primary record. **Proposed rule:** when a pair is `same_event`, the verified global record is primary, and tech-only fields (reason, department, severance, AI flag) stay on the tech row and are joined by group, not copied. | 18 pairs / 11 tech rows | Yes (no rows deleted) |
| **A-14** | Strip leading and trailing whitespace from text fields | 6 `news_url` values (none elsewhere) | Yes |
| **A-15** | Handle the 42 global rows that share a news URL with the same company | 42 | Keep all and add the flag `possible_internal_duplicate`. No deletion. |
| **A-16** | Exclude furloughs from "permanent layoff" totals | 133 global rows | Filter only, not deleted |
| **A-09** | Do **not** derive `total_employees` for global rows from headcount ÷ pct | 0 (recommend not doing it) | n/a |

**No approval needed** (mechanical, lossless): parse `event_date` to a date type, recompute year/quarter/month, add `source_dataset` and lineage columns, carry the `qc_*` flags over.

---

## 5. Phase 2 outputs, once approved

- `notebooks/02_data_cleaning.ipynb`, in the same section style as notebook 01
- `data/processed/layoff_events.csv`, `duplicate_review.csv`, `field_lineage.csv`, `layoff_event_departments.csv`, `industry_mapping.csv`, `company_name_mapping.csv`
- `reports/audit/cleaning_log.csv`
- Validation cells: row counts in = row counts out (5,035), no new zeros, raw checksums unchanged, every approved rule logged with the rows it affected

## 6. Before Phase 2 can start

1. Your decisions on A-01 to A-16, or "use the recommendations".
2. Your review of `data/interim/possible_duplicate_pairs.csv` (18 pairs), or approval to treat all of them as `unsure` for now. In that case both rows stay in, linked, with the global record as primary for totals.
3. Whether to apply the 5 Phase 1 fixes listed in `PHASE1_VERIFICATION_REPORT.md` section 4 first.
