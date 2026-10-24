# Phase 1 Verification Report

**Project:** Global Layoffs Intelligence & Workforce Analytics
**Verified on:** 2026-10-23
**Copy that was verified:** the shared project folder `global-layoffs-intelligence/`. All paths below are relative to it.
Your local OneDrive copy was **not** inspected. If it was synced from this folder, the same results should apply, but that has not been checked.

**Result:** 9 PASS, 4 NEEDS REVIEW, 0 FAIL. No source data was modified while verifying.

---

## 1. Files located

| Item | Path | Facts checked |
|---|---|---|
| Original CSV (global) | `data/raw/layoffs_2019_2026_sample.csv` | 5,000 data rows, 20 columns. Byte-identical to the file inside the uploaded `archive 5.zip` (same SHA-256). |
| Original CSV (tech) | `data/raw/tech_layoffs_2025_2026.csv` | 35 data rows, 16 columns. Byte-identical to the uploaded CSV. |
| Source data card | `data/raw/SOURCE_DATA_CARD.md` | `REPORT.md` from the zip, renamed. Its contents are unchanged. |
| Phase 1 notebook | `notebooks/01_data_intake_and_quality_audit.ipynb` | 75 cells (37 of them code). |
| Duplicate review file | `data/interim/possible_duplicate_pairs.csv` | 18 pairs, 19 columns. |
| Checksum record | `reports/audit/raw_file_manifest.csv` | Columns `file, size_kb, sha256`. |
| Audit log | `reports/audit/audit_log.csv` | 31 checks. |
| Other outputs | `data/interim/global_layoffs_staged.csv` (5,000 rows), `data/interim/tech_layoffs_staged.csv` (35 rows), `reports/audit/{missing_values_summary, data_quality_summary, column_mapping}.csv`, `reports/figures/01_*.png` | |

**Column names (from the CSV headers, read with Python's `csv` module):**

- Global: `layoff_id, date, year, month, company_name, company_domain, country, company_country, company_state, company_city, sector, headcount_cut, headcount_status, pct_workforce, is_furlough, news_mentions, news_source, news_url, news_excerpt, fliar_profile_url`
- Tech: `Company, Employees_Laid_Off, Date, Industry, Location, Country, Reason, Department, Percentage_Workforce, Total_Employees, Severance_Weeks, AI_Related, Year, Month, Month_Name, Quarter`

---

## 2. Verification results

| # | Check | Status | Evidence |
|---|---|---|---|
| V1 | Notebook runs top to bottom in a fresh kernel | **PASS** | The notebook was copied to a clean folder with `data/interim/` and `reports/` deleted, then run with `jupyter nbconvert --execute` on a new `python3` kernel. All 37 code cells ran in order (execution counts 1-37), with 0 error outputs and 0 stderr warnings. The notebook saved in the project folder has the same result (37 cells, counts 1-37, 0 errors). |
| V2 | Both original CSVs exist and row counts match the audit | **PASS** | Counted with the `csv` module, independently of pandas: 5,000 and 35 rows. The audit log rows "source record count" record 5,000 and 35, and the notebook's own re-count assertion passed. |
| V3 | Checksums recomputed with the recorded algorithm | **PASS** | The manifest column is named `sha256`, and the notebook's `sha256_of()` uses `hashlib.sha256`, so the algorithm is SHA-256 (taken from the code, not assumed). The recomputed values match all 3 entries: `a181c6ce…f686` (global), `f011a4d0…fc5c` (tech), `8e93c93c…66bc` (data card). |
| V4 | Raw files unchanged since upload | **PASS** | The raw-file hashes equal the hashes of the original uploads (the zip member and the tech CSV). The notebook's final cell also re-hashes after all processing and asserts that nothing changed. |
| V5 | Audit log holds real results, not just "passed" messages | **PASS** | Every row has `records_checked`, `issues_found` and `action_taken`, computed at run time. Examples: 350 rows share a news URL, 42 same-company shared-URL rows, 127 legal-suffix names, 84 sentence-like names, 18 cross-source pairs, 6 padded `news_url` values. |
| V6 | Audit log units are consistent | **NEEDS REVIEW** (warning) | The "missing values (all columns)" row puts **12** in `issues_found`, which counts *columns* with gaps, not cells (the note says so). Every other row counts records. Suggestion: also log the number of missing cells. |
| V7 | 11 candidate tech records are traceable to source rows | **PASS** | All 18 pairs were traced back to the raw CSV line numbers, and company and date match in every case (table in section 3). |
| V8 | Every candidate has a review status, and none was deleted or merged | **PASS** | `review_status` = `pending_review` for 18/18 pairs. The staged files still have 5,000 + 35 rows, and every pair's record IDs exist in them. Flags: 11 tech rows and 18 global rows have `qc_possible_cross_source_dup = True`. |
| V9 | All candidate pairs that were considered are recorded | **NEEDS REVIEW** (gap) | The matcher found **115** same-company pairs and kept 18 using the rule "within 120 days, or headcount within 5%". The 97 rejected pairs are not saved anywhere, so the rejection can't be audited from the files. No *records* were lost, only candidate pairs. |
| V10 | Match confidence is useful | **NEEDS REVIEW** (warning) | All 18 pairs are `medium` and none is `high` or `low`, so the score does not rank them. Also, `pair_id` was assigned before sorting, so the IDs are out of order in the file (P-005 comes first). This is cosmetic. |
| V11 | Missing headcounts stay missing, not zero | **PASS** | Global `headcount_cut` has 2,511 missing in raw and 2,511 in staged. `pct_workforce` has 3,879 missing in both. Zero values: 0 in raw, 0 in staged. The notebook also checks with `assert_frame_equal` that every original column in the staged files matches the raw values exactly. |
| V12 | Date and numeric checks flag invalid values | **NEEDS REVIEW** (executed, but never triggered) | The checks ran and found 0 unparseable dates, 0 out-of-range dates, 0 negative headcounts, 0 percentages outside 0-100, and 0 headcount/status conflicts. Because the real data has no invalid values, the flag columns (`qc_date_unparseable`, `qc_headcount_status_conflict`, `qc_headcount_math_gap_gt10pct`) are all False, and **no test has shown they would catch a bad value**. Suggestion: add a test cell that feeds in a small fake bad row. |
| V13 | Within-file duplicate checks | **PASS** | Exact duplicates: 0 (global) and 0 (tech). Duplicate `layoff_id`: 0. Same company on the same date: 0. Same company within 45 days: 0, which confirms the data card's merge rule. 42 same-company shared-URL rows are flagged (`qc_same_company_same_url`). |

### Checks implemented but not fully carried into outputs (warnings, not errors)

- The "after audit date" count is computed in the date table (0 rows) but is **not written to the audit log**.
- The "whitespace-only cell" count is computed (0 cells) but not logged separately.
- "Same company within 45 days" and "noisy company name" are logged with counts. Noisy names have a flag column, but the 45-day check has **no row-level flag**. That is fine at 0 hits, but it would be needed if the data changes.

### Documentation errors found in the notebook text

- Section 9 "What we found" lists **5** same-size-but-far-apart matches (Twitch, Roku, Adobe, Accenture, Dell). The data shows **6**, because **Unity** (1,800 people in both files, 486 days apart) is also one. This is a text error only, and the CSV is correct.
- My earlier chat message also said 5. The correct number is 6.

### Confirmed errors

None. No check failed, and no output contradicts the raw data.

---

## 3. Traceability of the 11 candidate tech records (18 pairs)

"Line" is the line number in the raw CSV (the header is line 1).

| Pair | Tech record (line) | Tech company, date, laid off | Global record (line) | Global company, date, headcount (status) | Gap (days) | Status |
|---|---|---|---|---|---|---|
| P-001 | T-00002 (3) | Twitch, 2025-01-09, 500 | G-03089 (3090) | Twitch, 2023-12-06, 500 (verified) | -400 | pending_review |
| P-002 | T-00007 (8) | Dell, 2025-02-05, 6,650 | G-02557 (2558) | Dell, 2023-04-19, 6,550 (verified) | -658 | pending_review |
| P-003 | T-00009 (10) | Cisco, 2025-02-15, 7,000 | G-03909 (3910) | Cisco, 2024-12-31, missing (failed_check) | -46 | pending_review |
| P-004 | T-00013 (14) | Roku, 2025-03-30, 360 | G-02887 (2888) | Roku, 2023-09-05, 360 (verified) | -572 | pending_review |
| P-005 | T-00014 (15) | Accenture, 2025-03-30, 19,000 | G-02252 (2253) | Accenture, 2023-01-06, 19,000 (verified) | -814 | pending_review |
| P-006 | T-00014 (15) | Accenture, 2025-03-30, 19,000 | G-03937 (3938) | Accenture, 2025-01-12, missing (failed_check) | -77 | pending_review |
| P-007 | T-00018 (19) | Unity, 2025-05-08, 1,800 | G-03142 (3143) | Unity, 2024-01-08, 1,800 (verified) | -486 | pending_review |
| P-008 | T-00018 (19) | Unity, 2025-05-08, 1,800 | G-04039 (4040) | Unity, 2025-02-24, missing (failed_check) | -73 | pending_review |
| P-009 | T-00020 (21) | Intel, 2025-08-01, 34,000 | G-04165 (4166) | Intel, 2025-04-23, 21,000 (verified) | -100 | pending_review |
| P-010 | T-00020 (21) | Intel, 2025-08-01, 34,000 | G-04283 (4284) | Intel, 2025-06-23, 529 (verified) | -39 | pending_review |
| P-011 | T-00020 (21) | Intel, 2025-08-01, 34,000 | G-04381 (4382) | Intel, 2025-08-19, 2,400 (verified) | 18 | pending_review |
| P-012 | T-00020 (21) | Intel, 2025-08-01, 34,000 | G-04507 (4508) | Intel, 2025-10-08, 22,000 (verified) | 68 | pending_review |
| P-013 | T-00028 (29) | X (Twitter), 2026-01-18, 1,200 | G-04512 (4513) | Twitter, 2025-10-09, missing (failed_check) | -101 | pending_review |
| P-014 | T-00029 (30) | Microsoft, 2026-01-20, 3,000 | G-04476 (4477) | Microsoft, 2025-09-22, 9,000 (verified) | -120 | pending_review |
| P-015 | T-00029 (30) | Microsoft, 2026-01-20, 3,000 | G-04674 (4675) | Microsoft, 2026-01-01, 15,000 (verified) | -19 | pending_review |
| P-016 | T-00029 (30) | Microsoft, 2026-01-20, 3,000 | G-04943 (4944) | Microsoft, 2026-04-23, 8,500 (verified) | 93 | pending_review |
| P-017 | T-00031 (32) | Adobe, 2026-01-28, 680 | G-02463 (2464) | Adobe, 2023-03-08, 680 (verified) | -1,057 | pending_review |
| P-018 | T-00032 (33) | Meta, 2026-02-01, 5,000 | G-04665 (4666) | Meta, 2025-12-30, 600 (verified) | -33 | pending_review |

**Reading the evidence (for your review, not a decision):**

- **Same size, 1-3 years earlier (6 tech rows):** Twitch, Dell, Roku, Accenture (P-005), Unity (P-007), Adobe. The tech file's number matches a verified global event from 2023-24, which suggests the tech file has the wrong date for these rows.
- **Close in time, size disagrees or unknown (5 tech rows):** Cisco, Intel, X/Twitter, Microsoft, Meta. These could be the same round reported with different numbers, or separate rounds.

---

## 4. Suggested fixes to Phase 1 (not applied; each needs your OK)

1. Save all 115 considered pairs, with `kept` / `excluded` and the reason, to `data/interim/candidate_pairs_all.csv`.
2. Add a test cell that runs the date and number flags on a small fake row with bad values and asserts that they fire.
3. Log the "after audit date" and "whitespace-only" counts, and add a row-level flag for the 45-day rule.
4. Fix the Section 9 text (6 same-size matches, adding Unity), and assign `pair_id` after sorting.
5. Log missing *cells* as well as columns.
