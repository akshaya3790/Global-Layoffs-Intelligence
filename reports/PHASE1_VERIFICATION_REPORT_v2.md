# Phase 1 Verification Report v2: targeted fixes

**Date:** 2026-10-23
**Scope:** the two fixes you asked for, then a full re-run. Phase 2 has **not** started.
**Previous report:** `reports/PHASE1_VERIFICATION_REPORT.md` (v1, kept unchanged).
**Copy checked:** the shared project folder `global-layoffs-intelligence/`. Your OneDrive copy was not touched.

---

## 1. What changed

| File | Change |
|---|---|
| `data/raw/*` | **None.** The SHA-256 hashes still match the manifest and your original uploads. |
| `reports/audit/history/run_2026-10-23_phase1_v1/` | **New.** A copy of every v1 audit record and interim file, plus the original notebook, saved before the re-run, with `SHA256SUMS.txt` |
| `reports/audit/audit_log_history.csv` | **New.** The v1 log (31 rows) plus each new run, appended and never overwritten |
| `data/interim/possible_duplicate_pairs.csv` | **Unchanged.** Byte-identical to v1 (SHA-256 `8a8379fe…`). |
| `data/interim/excluded_candidate_pairs.csv` | **New.** The 97 excluded candidate pairs |
| `src/phase1_validation.py` | **New.** The date and number rules, moved out of notebook cells into functions so the notebook and the tests run the same code |
| `tests/fixtures/synthetic_validation_cases.csv` | **New.** 12 synthetic rows, kept outside `data/` |
| `tests/test_phase1_validation.py`, `tests/test_phase1_outputs.py` | **New.** 25 automated tests |
| `notebooks/01_data_intake_and_quality_audit.ipynb` | Imports the rules from `src/`, adds Section 9b (excluded pairs), adds the future-date and non-numeric checks to the audit log, appends to the audit history, and fixes the Section 9 text (adds Unity, so 6 same-size matches) |
| `data/interim/*_staged.csv` | Same rows and the same values in every v1 column (checked with `assert_frame_equal`). There are 5 **new** flag columns: `qc_date_outside_expected_range`, `qc_date_after_audit_date`, `qc_non_numeric_value`, `qc_headcount_not_positive`, `qc_pct_out_of_range` (all False on real data). |
| `requirements.txt` | Added `pytest` |

---

## 2. Fix 1: all duplicate-match candidates preserved

**The rule that discarded them** (notebook Section 9, unchanged):

```python
close_in_time = pairs["date_gap_days"].abs() <= 120
same_size     = pairs["headcount_diff_pct"] <= 5
pairs = pairs[close_in_time | same_size]
```

A pair was dropped when the dates were **more than 120 days apart AND** the headcounts were **not within 5%**. "Not within 5%" includes pairs where the global headcount is missing, because a missing comparison counts as False.

**Reconstruction:** done exactly. The same code ran on the same raw files, and the result matches the earlier run.

| Count | Value | Evidence |
|---|---|---|
| Same-company candidate pairs generated | **115** | audit log, "cross-source candidates excluded by filter rule", records_checked = 115 |
| Kept for review (unchanged) | **18 pairs / 11 tech rows** | `possible_duplicate_pairs.csv`, byte-identical to v1 |
| Excluded by the rule | **97 pairs** | `excluded_candidate_pairs.csv` |
| Overlap between kept and excluded | 0 | notebook assertion and test |
| Excluded where the global headcount was missing | 27 | `exclusion_reason` column |
| Excluded date gaps | 125 to 2,564 days | all above 120, which a test checks |
| Name match type | 87 exact, 10 partial | `name_match` column |

**Excluded pairs by tech company:** Microsoft 19, Intel 15, X (Twitter) 13, Cisco 12, Accenture 9, Lyft 6, Snap 5, Unity 4, Amazon 3, Rivian 3, Twitch 2, and one each for Coinbase, Dell, Google, Peloton, Tesla and TikTok.

**Columns in the excluded file:** `excluded_pair_id`, `source_dataset_tech`, `tech_record_id`, `tech_source_row_number`, `source_dataset_global`, `global_record_id`, `global_source_row_number`, `global_layoff_id`, both company names, `name_match`, `matched_alias`, both dates, `date_gap_days`, both headcounts, `global_headcount_status`, `headcount_diff_pct`, both percentages, `match_score`, `exclusion_rule`, `exclusion_reason`, `review_status`, `reviewer_notes`.

- `match_score` = **`not calculated`** for every row. The confidence function was only ever applied to kept pairs, so no score was invented.
- `review_status` = `excluded_by_rule_not_reviewed` for every row.
- All 97 were traced to raw CSV line numbers: company, date and `layoff_id` match the raw files (test `test_excluded_pairs_traceable_to_raw_lines`).
- Nothing was merged or deleted.

---

## 3. Fix 2: validation rules tested on synthetic data

**Before this fix**, the date and number checks were inline expressions in notebook cells, not reusable functions. To test the *same* logic, those expressions were moved into `src/phase1_validation.py` unchanged, and the notebook now calls them. Proof that the move didn't change behaviour: the v1 audit checks give **the same `issues_found` in all 31 of them**, and the v1 staged columns and `qc_issue_count` are identical.

**Gaps found while writing the tests (now fixed):**
- **Non-numeric values:** the original rule (`df["headcount_cut"] <= 0`) **crashes with TypeError** when a column contains text. This is proved by `test_original_inline_rule_could_not_handle_text`. A new `flag_non_numeric` rule was added.
- **Future dates:** these were counted in a table but never logged or flagged per row. They are now logged and flagged.

**Synthetic cases** (`tests/fixtures/synthetic_validation_cases.csv`). Each test checks that the expected flags fire **and that no other flags fire**.

| Case | Input | Expected flags | Result |
|---|---|---|---|
| S01 | date `2025-02-30` | unparseable date | PASS |
| S02 | date `not-a-date` | unparseable date | PASS |
| S03 | date `2027-03-15` | after audit date, outside range | PASS |
| S04 | headcount `-50` | headcount not positive | PASS |
| S05 | pct `140` | pct out of range | PASS |
| S06 | headcount `twelve hundred` | non-numeric, verified-but-no-number conflict | PASS |
| S07 | pct `15%` | non-numeric | PASS |
| S08 | headcount empty, `not_disclosed` | none, and the value **stays missing** | PASS |
| S09 | 300 with `failed_check` | status conflict | PASS |
| S10 | valid control row | none | PASS |
| S11 | date `2015-06-01` | outside range | PASS |
| S12 | headcount `0` | headcount not positive | PASS |

**Missing values:** S08 stays NaN after number conversion and is never 0. Text (S06) becomes NaN, never 0. The rules don't modify their input (`test_rules_do_not_modify_input`).

**The tests can fail:** in a scratch copy, the pct rule was changed from `> 100` to `> 150`, and `test_each_case_flagged_exactly[S05]` **failed** as expected. The real file was not changed.

---

## 4. Re-run results (actually executed)

| Run | Command | Result |
|---|---|---|
| Notebook, fresh kernel, clean copy with all generated outputs deleted | `jupyter nbconvert --to notebook --execute` | 41 code cells, execution counts 1-41 in order, **0 errors, 0 stderr warnings** |
| Full test suite on that clean copy | `python -m pytest -v tests` | **25 passed, 0 failed** |
| Same suite on the project copy | `python -m pytest -q tests` | **25 passed** |

**Test list:** 8 output tests (raw checksums, pairs file unchanged since v1, v1 archive intact, 18 + 97 = 115 with no overlap, excluded pairs fail the rule, excluded pairs traceable, statuses and no invented score, no deletions and 2,511 missing headcounts with 0 zeros), 17 validation tests (12 synthetic cases, a fixture-coverage check, missing-stays-missing, text-not-zero, input-not-modified, and the original rule crashing on text).

**How to run them yourself** (from the project root, with the `layoffs-env` kernel's environment active):

```bash
jupyter nbconvert --to notebook --execute --inplace notebooks/01_data_intake_and_quality_audit.ipynb
python -m pytest -v tests
```

---

## 5. Status of every v1 check

| # | Check | v1 | v2 | Note |
|---|---|---|---|---|
| V1 | Notebook runs in a fresh kernel | PASS | **PASS** | 41/41 cells |
| V2 | Source files and row counts | PASS | **PASS** | 5,000 / 35 |
| V3 | Checksums (SHA-256) | PASS | **PASS** | |
| V4 | Raw files unchanged | PASS | **PASS** | |
| V5 | Audit log has real results | PASS | **PASS** | 41 checks this run; history kept |
| V6 | Audit log units consistent | NEEDS REVIEW | **NEEDS REVIEW** | not in scope; the "missing values" row still counts columns |
| V7 | 11 candidates traceable | PASS | **PASS** | |
| V8 | Review status, none deleted | PASS | **PASS** | |
| V9 | All considered pairs recorded | NEEDS REVIEW | **PASS** | 97 excluded pairs saved |
| V10 | Match confidence ranks pairs | NEEDS REVIEW | **NEEDS REVIEW** | kept unchanged as you asked; all 18 still "medium" |
| V11 | Missing headcounts stay missing | PASS | **PASS** | real data and synthetic S08 |
| V12 | Date and number flags proven to fire | NEEDS REVIEW | **PASS** | 12 synthetic cases |
| V13 | Within-file duplicates | PASS | **PASS** | |

---

## 6. Unresolved issues

1. **Human review outstanding.** 18 kept pairs (`pending_review`) and 97 excluded pairs (`excluded_by_rule_not_reviewed`).
2. **Confidence score doesn't discriminate** (V10). All 18 kept pairs are "medium". The scoring was left unchanged so the reviewed file stays identical.
3. **`pair_id` order is cosmetic** (P-005 is the first row). Left unchanged for the same reason.
4. **Audit unit mismatch** (V6). The "missing values" row counts columns, not cells.
5. **Some rules have no synthetic test:** `news_mentions < 1`, "laid off > total employees", `Severance_Weeks < 0`, and the tech-file % × total cross-check. They ran on real data (0 hits) but haven't been shown to fire.
6. **The 45-day rule** has a count (0) but no row-level flag.
7. **The tech file's provenance is unknown**, and 6 of its rows look like misdated 2023-24 events. This is for the Phase 2 decisions.
8. **The notebook now needs `src/phase1_validation.py`**, so copy the whole folder, not only the notebook.
9. **Your OneDrive copy** has not been updated by this thread.
