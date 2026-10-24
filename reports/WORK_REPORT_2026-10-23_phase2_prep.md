# Work report: Phase 2 preparation (your request of 09:58 UTC)

This report lists everything done in this step, in order, so you can see what may need correcting.

**Scope respected:** no notebook 02, no cleaning applied, no PostgreSQL, ML or Power BI work.

---

## Step 1: Saved the baseline before touching shared code

- Copied the current Phase 1 outputs (audit CSVs, interim CSVs, notebook 01, `src/phase1_validation.py`) to `reports/audit/history/run_2026-10-23_phase1_v2/`, together with `SHA256SUMS.txt`.
- The v1 archive (`run_2026-10-23_phase1_v1/`) was left untouched.

## Step 2: R1-R4 moved into shared validation code (your item 2 and 3)

**What changed in `src/phase1_validation.py`:** I **added** 5 functions at the end. No existing function was edited.

| Rule | New function | Original notebook expression it replaces |
|---|---|---|
| R1 | `flag_news_mentions_below_one` | `global_df["news_mentions"] < 1` |
| R2 | `flag_laid_off_exceeds_total` | `tech_df["Employees_Laid_Off"] > tech_df["Total_Employees"]` |
| R3 | `flag_negative_severance` | `tech_df["Severance_Weeks"] < 0` |
| R4 | `headcount_math_gap_pct` + `flag_headcount_math_gap` | `implied = pct*total/100; gap = (100*(laid-implied)/implied).round(1); gap.abs() > 10` |

**The only behaviour difference:** values pass through `to_number()` first, so a text value no longer crashes the rule (the separate non-numeric rule catches it instead). On the real, numeric data the result is identical, which the regression tests prove.

**Notebook 01:** cells in Sections 1 and 7 now call these functions instead of the inline expressions. Nothing else in the notebook changed.

## Step 3: Synthetic and regression tests

- **New fixture:** `tests/fixtures/synthetic_r1_r4_cases.csv` with **30 synthetic rows** that never touch `data/`.
  - R1: 0, -3, 0.5 (just below the boundary), 1 (boundary), 7, missing, text
  - R2: greater than total, equal to total (100%), below, zero laid off, zero total, either value missing
  - R3: -2, 0 (valid), 12, missing, -0.5
  - R4: 0% gap, 20%, 8%, exactly 10% (boundary, not flagged because the rule is strictly greater), 10.2%, -20%, each input missing, pct = 0, and 0 with 0
- **New tests:** `tests/test_phase1_rules_r1_r4.py`
  - 30 synthetic case tests
  - 1 coverage test: every rule has a flagged case, a non-flagged case and a missing-value case
  - 4 "input not modified" tests
  - 1 missing-stays-missing test
  - **4 regression tests**, which run each new function and the *original* notebook expression on the real raw data and require identical results
- **Missing values:** no new assumption was introduced. A missing input gives no flag, which is exactly how the original expressions behaved. The tests document this. See open point P4 in the schema file for the one edge case (pct = 0).

## Step 4: Re-ran everything and proved the baseline is unchanged

| Check | Result |
|---|---|
| Notebook 01 re-run (`nbconvert --execute`) | OK |
| `possible_duplicate_pairs.csv` | **byte-identical** to the baseline (SHA-256 `8a8379fe…`) |
| `excluded_candidate_pairs.csv`, both staged files, `data_quality_summary.csv`, `missing_values_summary.csv`, `column_mapping.csv`, `raw_file_manifest.csv` | **byte-identical** to the baseline |
| Audit log | all 41 checks have identical `records_checked` and `issues_found` |
| Audit history | new run appended; earlier runs kept (v1 with 31 rows + 2 runs with 41 rows) |
| Raw files | SHA-256 values unchanged (`a181c6ce…`, `f011a4d0…`) |
| Fresh kernel on a clean copy (generated outputs deleted first) | 41/41 code cells, execution order 1-41, **0 errors, 0 warnings** |
| Full test suite on the clean copy | **65 passed** (before the mapping tests were added) |
| Mutation check in a scratch copy (pct rule set to > 150, severance rule set to < -1) | the right tests **failed** (S05 and R3-05), so the tests do catch broken rules. The real code was not changed. |

## Step 5: Mapping proposals for A-02 and A-04 (generated, NOT applied)

- **New file `src/phase2_mappings.py`:** the cleaning rules and the hand-written mapping tables. It defines rules only.
- **New file `src/make_mapping_proposals.py`:** reads the raw files and writes proposals to `reports/phase2_proposals/`.
  - `company_name_mapping_proposal.csv`: 3,532 raw names. 3,314 unchanged, 182 rule-based, 25 manual (confident), 8 manual (needs your review), 3 kept raw and flagged.
  - `industry_mapping_proposal.csv`: 77 labels → 16 groups. 4 labels are marked needs_review.
  - `cross_source_industry_check.csv`: 16 company/label pairs, 9 of which disagree between the sources.
- **New tests `tests/test_phase2_mappings.py` (7 tests):** suffixes are removed only at the end, brand words are kept, missing stays missing, a name is never emptied, the X/Twitter alias works, every raw label is mapped to a known group, and a missing sector becomes `Unknown`.
- **Final full suite: 72 passed** (25 Phase 1 + 40 R1-R4 + 7 mapping).

## Step 6: Final canonical schema

`reports/PHASE2_FINAL_SCHEMA_AND_MAPPINGS.md` lists the 43 canonical columns with their source, rule and decision ID, the other output files, and mapping examples.

---

## Files added or changed in this step

| File | Status |
|---|---|
| `src/phase1_validation.py` | changed: 5 functions **added**, existing ones untouched |
| `notebooks/01_data_intake_and_quality_audit.ipynb` | changed: calls the R1-R4 functions; outputs identical |
| `reports/audit/audit_log.csv`, `audit_log_history.csv` | changed: new run appended |
| `reports/audit/history/run_2026-10-23_phase1_v2/` | new (baseline archive) |
| `tests/fixtures/synthetic_r1_r4_cases.csv`, `tests/test_phase1_rules_r1_r4.py`, `tests/test_phase2_mappings.py` | new |
| `src/phase2_mappings.py`, `src/make_mapping_proposals.py` | new |
| `reports/phase2_proposals/*.csv` | new (3 proposal files) |
| `reports/PHASE2_FINAL_SCHEMA_AND_MAPPINGS.md`, this report | new |
| `data/raw/*` and both duplicate-review files | **not changed** |

## Things you may want to correct

1. **P1-P5** in the schema file. P1 ("High Tech" group) and P3 (the sources disagree on industry) affect the industry charts the most.
2. The 8 `needs_review` company mappings: subsidiary or parent?
3. Notebook 01 now depends on 5 more functions in `src/`, so copy the whole `src/` folder to your OneDrive copy.
