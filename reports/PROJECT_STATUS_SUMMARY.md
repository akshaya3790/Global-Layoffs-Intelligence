# Global Layoffs Intelligence: status summary

**As of:** 2026-10-23
**Where things stand:** Phase 1 (data audit) is finished and verified. Phase 2 (cleaning) is planned but **not started**, and notebook 02 does not exist yet.

---

## 1. Notebook 02 checks (run today)

I checked the shared project folder (`global-layoffs-intelligence/notebooks/`) and the working copy. Your OneDrive folder is not visible from here.

| Check | Result | Evidence |
|---|---|---|
| `notebooks/02_data_cleaning.ipynb` exists | **FAIL** | The `notebooks/` folder contains only `01_data_intake_and_quality_audit.ipynb`. No file named `02_data_cleaning*` exists anywhere in the project folder. |
| Both original CSVs load in the notebook | **NOT CHECKED** (notebook missing) | Notebook 01 does load both: 5,000 and 35 rows. |
| Baseline row counts, column names, data types and missing-value counts are displayed | **NOT CHECKED** (notebook missing) | Notebook 01 shows all four (Sections 3, 4 and 5). |
| Runs from a fresh kernel without errors | **NOT CHECKED** (notebook missing) | Notebook 01: 41/41 cells, 0 errors. |

Notebook 02 was not created because Phase 2 is waiting for your approval of the plan. If a notebook 02 exists in your OneDrive folder, share it here and I'll run these 4 checks on it.

---

## 2. The project in one paragraph

A portfolio project that analyses layoffs from 2019 to 2026 with **Python** (cleaning and analysis), **PostgreSQL** (database and SQL queries), **Power BI** (dashboard) and **machine learning** (predicting whether a layoff will be a major one). It is built in six phases, and each phase is reviewed before the next one starts.

## 3. The data

| | Global file | Tech file |
|---|---|---|
| File | `data/raw/layoffs_2019_2026_sample.csv` | `data/raw/tech_layoffs_2025_2026.csv` |
| Rows × columns | 5,000 × 20 | 35 × 16 |
| Period | Jan 2019 to Jun 2026 | Jan 2025 to Feb 2026 |
| Source | Fliar Research (a 26% sample, CC BY-NC licence) | Unknown |
| Strength | Long history, 112 countries | Has reason, department, severance and an AI-related flag |
| Weakness | Many blanks (headcount 50%, % of workforce 78%) | Small, source unverified, some dates look wrong |

## 4. What Phase 1 did (notebook 01)

It **looked at and checked** the data without changing it.

1. **Raw files protected.** Each raw file has a SHA-256 fingerprint. The fingerprints still match your original uploads after every run.
2. **Counts and structure.** Row counts, column names and data types were recorded for both files, plus a side-by-side map of how their columns relate.
3. **Missing values measured, not filled.** Blanks stay blank, and nothing was turned into 0. In the global file a headcount exists only when the source marked it "verified" (2,489 rows). The other 2,511 are blank because the number was never confirmed.
4. **Dates checked.** All 5,035 dates are real calendar dates, in the expected period, and none are in the future.
5. **Numbers checked.** No negative layoffs, no percentages over 100, and no text in number columns.
6. **Duplicates inside each file.** There are no exact copies. 42 global rows share a news article with the same company, and these are flagged for review.
7. **Duplicates across the two files.**
   - 115 same-company pairs were found between the files.
   - **18 pairs (11 tech rows) were kept** as possible duplicates and saved in `data/interim/possible_duplicate_pairs.csv`, all marked `pending_review`.
   - **97 pairs were excluded** by the rule "more than 120 days apart and a different size". They are saved separately in `data/interim/excluded_candidate_pairs.csv`, so that decision can be checked too.
   - Key finding: **6 tech rows** (Twitch, Dell, Roku, Accenture, Unity, Adobe) have the exact same layoff size as a 2023-24 event, but the tech file dates them 2025-26. That suggests the tech file has wrong dates for these rows.
8. **Nothing deleted or merged.** Each problem became a True/False flag column (`qc_...`) in the staged copies in `data/interim/`.
9. **Audit trail.** Every check is logged with real counts in `reports/audit/audit_log.csv`. Earlier runs are kept in `audit_log_history.csv` and `reports/audit/history/`.

## 5. How Phase 1 was tested

- The **notebook was run from a fresh kernel** on a clean copy: 41 of 41 code cells ran with 0 errors.
- **25 automated tests pass** (`python -m pytest -v tests`):
  - **12 fake test rows** (an invalid date, a future date, a negative count, a percentage of 140, text in a number column, a missing headcount, and others) are each flagged exactly as expected. The fake rows live in `tests/fixtures/` and never touch the real data.
  - Output tests confirm the raw checksums, 18 + 97 = 115 pairs with no overlap, that every pair traces back to its raw CSV line, and 2,511 missing headcounts with 0 zeros.
- A rule was broken on purpose in a scratch copy, and the matching test failed, which shows the tests catch problems.
- While writing the tests, I found that the first version of the number check would crash on text, and fixed it.

## 6. Verification scorecard (13 checks)

**11 PASS, 2 NEEDS REVIEW, 0 FAIL** (details in `reports/PHASE1_VERIFICATION_REPORT_v2.md`)

The 2 NEEDS REVIEW items:
- All 18 kept pairs score "medium", so the score doesn't rank them. It was left unchanged so the review file stays identical.
- One audit-log row counts missing *columns*, not missing cells.

## 7. Open items before Phase 2

1. **Your review** of the 18 kept pairs (and optionally the 97 excluded ones). You can also choose to treat them all as "unsure" for now.
2. **Your decisions A-01 to A-16** in `reports/PHASE2_CANONICAL_MODEL_PLAN.md`. Examples: how to standardise country names, which industry groups to use, and how to label the 6 suspect tech dates. "Use the recommendations" is a valid answer.
3. Four rules have not been tested on fake data yet (news mentions < 1, laid off > total employees, negative severance, and the tech % × total cross-check).
4. The tech file's source is unknown, so it will be kept as a separate, lower-confidence table.

## 8. What Phase 2 will do, once approved

Notebook 02 will build one combined table: one row per source record, the original value kept next to each cleaned value, every change logged, and still nothing deleted. After that come the analysis charts (Phase 3), PostgreSQL (Phase 4), the risk model (Phase 5), and the Power BI guide and README (Phase 6).

## 9. Key files

| What | Path |
|---|---|
| Phase 1 notebook | `notebooks/01_data_intake_and_quality_audit.ipynb` |
| Validation rules | `src/phase1_validation.py` |
| Tests | `tests/` |
| Pairs to review | `data/interim/possible_duplicate_pairs.csv`, `data/interim/excluded_candidate_pairs.csv` |
| Audit records | `reports/audit/` |
| Verification reports | `reports/PHASE1_VERIFICATION_REPORT.md` (v1), `reports/PHASE1_VERIFICATION_REPORT_v2.md` |
| Phase 2 plan | `reports/PHASE2_CANONICAL_MODEL_PLAN.md`, `reports/phase2_column_mapping_proposal.csv` |
| Notebook roadmap | `NOTEBOOK_PLAN.md` |
