# Phase 2 Approval Checklist (A-01 to A-16)

**Updated:** 2026-10-23, 09:55 UTC
**Status:** WAITING FOR YOUR APPROVAL. Notebook 02 has not been created, and no cleaning has been applied.

**How to reply:** "approve all recommended", or list changes by ID (for example "A-04: review first").

---

## 0. Current status, re-checked today (nothing was modified)

| Item | Result |
|---|---|
| Raw files | `data/raw/layoffs_2019_2026_sample.csv` (5,000 rows) and `data/raw/tech_layoffs_2025_2026.csv` (35 rows). SHA-256 values `a181c6ce…` and `f011a4d0…` still match `reports/audit/raw_file_manifest.csv`. |
| Tests | `python -m pytest tests` → **25 passed** (run today) |
| Duplicate review files | `possible_duplicate_pairs.csv`: 18 pairs, all `pending_review`. `excluded_candidate_pairs.csv`: 97 pairs, all `excluded_by_rule_not_reviewed`. |
| Source-line traceability | Every record has `record_id` and `source_row_number`. Both pair files carry the tech and global record IDs. The excluded file also has CSV line numbers and `layoff_id`. |
| Audit history | `audit_log_history.csv`: 2 runs (v1 with 31 checks, v2 with 41). v1 is archived in `reports/audit/history/run_2026-10-23_phase1_v1/` with `SHA256SUMS.txt`. |
| Notebooks | Only `01_data_intake_and_quality_audit.ipynb`. **02 does not exist** (as intended). |

---

## 1. Decisions you have already made

| ID | Decision | Effect on later analysis |
|---|---|---|
| **TECH** ✅ | The tech dataset stays a separate, lower-confidence source | Every row carries `source_dataset` and `source_confidence` (`high` = global, `low` = tech). SQL, EDA and Power BI default to global rows for totals and trends. Tech rows feed a separate "AI layoffs 2025-26" view. |
| **A-07** ✅ | The 6 suspicious tech dates (Twitch, Dell, Roku, Accenture, Unity, Adobe) keep their original values | `date_reliability = "suspect_date"`, plus a `date_flag_reason` naming the matching 2023-24 global record. **No date is inferred or replaced.** Time charts of tech data must show or exclude these 6 explicitly. |

---

## 2. Decisions needed

| ID | Decision | Recommended option | Reason | Effect on later analysis |
|---|---|---|---|---|
| **A-01** | Tech rows have no source ID | `source_event_id` = NULL for tech rows. Use Phase 1 `event_key` (`T-00001`) as the key. | Inventing an ID would look like source data when it isn't. | PostgreSQL primary key = `event_key`. Lineage still goes back to the CSV line. |
| **A-02** | Company name cleaning | Keep `company_name_raw` unchanged. `company_name` = trim + remove legal suffixes + a reviewable `company_name_mapping.csv` for the 84 sentence-like names and the X/Twitter alias. | Noisy names split one company's history into several companies. | Correct "repeat layoff" counts, which are an ML feature (prior rounds) and a Power BI page. A wrong mapping would merge two companies, so the mapping is reviewable. |
| **A-03** | Country labels | `USA`, `United States (usa)` → `United States`. `United Kingdom (uk)` → `United Kingdom`. `United States (cnmi)` → `Northern Mariana Islands`. | The same country under 2 labels splits counts. | Correct country totals and map visuals. `country_raw` is kept. |
| **A-04** | Industry taxonomy | About 15 `industry_group` values via a reviewable `industry_mapping.csv` (49 global + 27 tech labels). Labels with a slash map on their first part. Missing → `Unknown`. | The two sources use different label lists, and the global list has overlaps (Consumer / Consumer Goods). | The industry is a main chart dimension and an ML feature. `Unknown` (31% of global rows) stays visible. |
| **A-05** | Global `country` vs `company_country` | `country` = event location (global `country`). `hq_country` = `company_country`. Never fill one from the other. | They differ in 239 rows, so they mean different things. | Maps show where layoffs happened. 470 rows have no event country and stay `Unknown`. |
| **A-05b** | Meaning of the tech `Country` | Store it in `country` with `country_basis = "hq_assumed"`. Global rows get `"event_location"`. | Tech `Location` values are HQ cities (e.g. IBM → Armonk, NY). | Prevents comparing HQ countries with event countries without noticing. |
| **A-06** | Splitting tech `Location` | `city` = before the comma. `state` = after the comma only if it's a 2-letter US code. Keep `location_raw`. | Formats mix `City, ST` and `City, Country`. | City and state filters work for the tech view. |
| **A-08** | Headcount reliability | Keep the global `headcount_status`. Tech = `reported_unverified`. Missing stays NULL. | The two sources verify numbers differently. | Totals can be split by reliability. The 2,511 missing global headcounts are **never 0**, so every "jobs cut" total must state its coverage (about 50%). |
| **A-09** | Global `total_employees` | Do **not** derive it. Leave it NULL. | Dividing headcount by % would invent company sizes from partial data. | Company size isn't available as a global ML feature. The model uses sector, region, timing and history instead. |
| **A-10** | Global reason | `reason` = NULL. `reason_category_derived` from published keyword rules on `news_excerpt`, with a `reason_method` column. | There's no source reason field, only news text. | Reason charts are possible but labelled "derived". About 70% of rows will be `Not stated`. |
| **A-11** | Multi-value departments | Keep the original text, plus a bridge table `layoff_event_departments.csv` (tech only). | Values like "Engineering, Marketing" can't be counted otherwise. | Power BI department charts avoid double counting events. |
| **A-12** | AI-related for global rows | `ai_related` = NULL for global. A separate `ai_mentioned_in_news_derived` flag (about 40 rows). | A source flag and a keyword guess are not the same evidence. | The AI analysis relies mainly on the tech file, and any global AI chart is labelled "derived". |
| **A-13** | Duplicates | **Link, never merge.** Copy both pair files unchanged into `data/processed/`. Add `possible_duplicate_group` to linked events. No primary record is chosen until you review. | Your review is still pending. | All 5,035 rows are kept. There's no double counting because default totals use global rows only (TECH decision). |
| **A-14** | Whitespace | Strip it in cleaned columns only. | 6 `news_url` values start with line breaks. | Clean links in Power BI. Raw values are unchanged. |
| **A-15** | 42 same-company shared-URL rows | Keep them, with `possible_internal_duplicate = True`. | Same article but different dates: could be follow-ups or repeats. | They can be excluded in sensitivity checks. Nothing is deleted. |
| **A-16** | Furloughs | Keep all 133. `is_permanent_layoff` = NOT `is_furlough` for global rows, NULL for tech. | Furloughs are temporary, and 111 of them fall in the COVID period. | "Permanent layoffs" trends can filter them out. The COVID spike stays explainable. |

---

## 3. The four untested validation rules, with proposed synthetic tests

These rules ran on the real data in notebook 01 and found 0 hits, but they have never been shown to fire. They are currently **inline expressions in notebook 01**, not functions in `src/phase1_validation.py`, so testing them means moving them into that file (see issue 1 below).

| # | Rule (as written in notebook 01) | Proposed function | Synthetic cases (`tests/fixtures/synthetic_tech_rules.csv`) | Expected |
|---|---|---|---|---|
| R1 | `news_mentions < 1` (global) | `flag_news_mentions_below_one` | `0` → flag, `-3` → flag, `1` → no flag, empty → no flag (missing ≠ 0), `abc` → no flag here (caught by the non-numeric rule) | fires only on 0 and -3 |
| R2 | `Employees_Laid_Off > Total_Employees` (tech) | `flag_laid_off_exceeds_total` | 1,500 of 1,000 → flag. 1,000 of 1,000 → no flag (100% is allowed). 500 of 1,000 → no flag. Total missing → no flag. | fires only on 1,500/1,000 |
| R3 | `Severance_Weeks < 0` (tech) | `flag_negative_severance` | `-2` → flag, `0` → no flag (no severance is valid), `12` → no flag, empty → no flag | fires only on -2 |
| R4 | Laid off vs % × total differs by more than 10% (tech) | `flag_headcount_math_gap(threshold=10)` | 500 / 10% / 5,000 → no flag (0% gap). 600 / 10% / 5,000 → flag (20% gap). 540 / 10% / 5,000 → no flag (8%). Any of the three missing → no flag and no crash. 0% → no division-by-zero crash. | fires only on the 20% case |

Each test also checks that the input data isn't modified and that no other flag fires.

---

## 4. Issues that need your attention

1. **Testing R1-R4 requires a small change to Phase 1 code.** The four rules would move from notebook 01 cells into `src/phase1_validation.py` as functions, and notebook 01 would call them. This is the same refactor done for the other rules. Proof required afterwards: notebook 01 re-run gives identical audit counts, `possible_duplicate_pairs.csv` stays byte-identical, and the audit history gets a new run appended (nothing overwritten). **Approve "R1-R4: yes" or tell me to leave Phase 1 untouched.**
2. **The duplicate review is still pending** (18 + 97 pairs). Phase 2 can go ahead without it under A-13, but no record will be marked primary until you review.
3. **Mapping files (A-02, A-04)** will be generated and applied in notebook 02 and saved for review. If you want to check them *before* they are applied, say "A-02/A-04: review first", and I'll stop after generating them.
4. **Known open items from Phase 1** (not blocking):
   - All 18 kept pairs score "medium", so the score doesn't rank them.
   - One audit-log row counts columns, not cells.
   - The 45-day rule has no row-level flag (0 hits).
5. **Your OneDrive copy** isn't visible from here. Everything above refers to the shared project folder.

## 5. What happens after approval (not started)

Notebook 02 builds `data/processed/layoff_events.csv` (5,035 rows, one per source record, each raw value next to its cleaned value), plus a quality-issues report, a transformation log, field lineage, mapping files, the department bridge table and both pair files (unchanged). It reuses `src/phase1_validation.py`, checks raw SHA-256 values at the start and end, runs from a fresh kernel, and adds tests for schema, row counts, missingness, lineage and reproducibility. No PostgreSQL, ML or Power BI work.
