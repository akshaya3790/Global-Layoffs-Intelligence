# Work report: Phase 2 build (your request of 10:09 UTC)

**Result:** `notebooks/02_data_cleaning.ipynb` is built and verified. Two independent fresh-kernel runs produced **identical outputs** (same SHA-256), the notebook ran **75 validation checks, all passed**, and the **full test suite passes (93/93)**.
No PostgreSQL, ML or Power BI work was started.

---

## 1. Confirmations you asked for before the build

| Item | Final answer |
|---|---|
| Industry groups | **16 real groups + `Unknown` = 17 values.** The 70 "High Tech" rows → **Technology (mixed)**. Hardware & Semiconductors keeps global *Semiconductors* and tech *Hardware* / *Semiconductors/AI* (53 rows). |
| `layoff_event_departments.csv` | 70 rows (35 tech events × 2 departments). Columns: `event_key`, `source_dataset`, `source_row_number`, `department_raw`, `department`, `department_position`, `departments_in_event`, `allocation_weight`. There's **no headcount column**. Checks: every key exists in the main table, (event, department) is unique, weights add up to 1 per event, it covers exactly the 35 tech events, and the source line matches the main table. |
| Schema (correction) | My earlier "43 columns" was the row count of my schema table. The real schema is **51 named columns + 18 quality-flag columns = 69 columns**. The tests enforce the exact column list. `event_key` is unique and never missing, (source_dataset, source_row_number) is unique, and every row is traced back to its raw CSV line. |

---

## 2. What I did, step by step

1. **Applied P1-P5 to the mapping rules** (`src/phase2_mappings.py`).
   - P1: new group *Technology (mixed)*.
   - P2: the 8 uncertain names keep their **exact raw name**, marked `needs_review`. I also moved 2 more names to the same treatment because they are subsidiaries or business units: `Tata Steel in the Netherlands` and `Whole Foods Market Southern Region — Bake House`. With the 3 description-only names, that makes **13 names kept raw, pending review**.
   - P5: the E-commerce limitation is noted in the mapping.
   - Mapping tests were updated (`tests/test_phase2_mappings.py`), and the proposal files in `reports/phase2_proposals/` were regenerated.
2. **Wrote `src/phase2_cleaning.py`**, which holds the rules notebook 02 calls: country relabels (A-03), region lookup, location split (A-06), reason keywords (A-10), AI keyword flag (A-12), suspect-date rule (A-07), duplicate linking (A-13), the department bridge (A-11), and a change-log helper. It reuses `parse_dates` from Phase 1 instead of duplicating it.
3. **Built notebook 02** with 17 sections. Each has an objective, an explanation and small code cells, and every step ends with checks.
4. **Ran it, found and fixed 3 problems in my own first draft:**
   - Tech rows had `possible_internal_duplicate = False`, but that check was never computed for tech rows. They are now **missing (NA)**, as the "not computed ≠ False" rule requires.
   - Case harmonisation turned the tech row `Snap` into `SNAP`, because the all-caps spelling had more rows. The rule now **prefers a spelling that isn't all capitals**, then the most rows. Result: 5 global `SNAP` rows → `Snap`, plus `Cargologic Germany` → `CargoLogic Germany` and `DON'T NOD` → `Don't Nod` (7 rows in total, all logged).
   - The printout for non-country values was misleading ("Australia" appeared because its HQ field was `Au`). It now shows both country columns.
5. **Added tests:** `tests/test_phase2_cleaning.py` (10 unit tests on synthetic inputs) and `tests/test_phase2_outputs.py` (10 tests on the real outputs).
6. **Verified reproducibility:** I deleted all generated outputs in 3 separate clean copies and ran notebook 01, then notebook 02, then all tests in each copy.

---

## 3. Outputs (`data/processed/`)

| File | Rows | What it is |
|---|---|---|
| `layoff_events.csv` | 5,035 | the canonical table (69 columns) |
| `layoff_event_departments.csv` | 70 | department bridge (A-11) |
| `quality_issues.csv` | 4,886 | one row per (record, flag that is True) |
| `transformation_log.csv` | 16 | every rule, decision ID, rows changed, examples |
| `field_lineage.csv` | 54 | canonical column ← source column, per source, plus dropped columns |
| `company_name_mapping.csv` | 3,532 | raw → clean name, method, review status, rows |
| `industry_mapping.csv` | 77 | raw label → group, rows |
| `cross_source_industry_disagreements.csv` | 9 | P3 disagreements (recorded, not overridden) |
| `possible_duplicate_pairs.csv` / `excluded_candidate_pairs.csv` | 18 / 97 | **byte-identical** copies of the Phase 1 files |
| `phase2_output_manifest.csv` | 10 | SHA-256 of each output, used for the reproducibility test |

**Audit trail:** `reports/audit/phase2_check_log.csv` (75 checks), and the same checks were appended to `audit_log_history.csv`. All earlier runs are kept.

---

## 4. Verification results (actually run)

| Check | Result |
|---|---|
| **Fresh kernel, notebook 01** (3 clean copies) | 41/41 code cells, in order, 0 errors, 0 stderr |
| **Fresh kernel, notebook 02** (3 clean copies) | 36/36 code cells, in order, 0 errors, 0 stderr |
| **Notebook 02 checks** | **75 of 75 passed** (`phase2_check_log.csv`) |
| **Full test suite** | **93 passed, 0 failed** in each clean copy and in the project copy |
| **Reproducibility** | the output manifests from independent fresh runs A, B and C are **identical** to each other and to the project copy |
| **Row counts** | 5,000 global + 35 tech = 5,035 in, 5,035 out |
| **Primary key** | `event_key` is unique and never missing, and equals the Phase 1 `record_id` for every row |
| **Lineage** | for every row, the raw-preserving columns equal the raw CSV at `source_row_number`. Headcounts equal raw values after the type change. Global `source_event_id` = `layoff_id`. |
| **Missingness** | identical to raw for headcount (2,511), workforce % (3,879), sector, event country (470), HQ country, domain, news URL and excerpt. **0 zeros created.** |
| **Raw files** | SHA-256 checked at the start and the end of notebook 02. Unchanged. |
| **Phase 1 flags** | all 14 carried over. The global values equal the staged file, column by column. |

---

## 5. What the transformations did (from `transformation_log.csv`)

| Rule | Decision | Rows changed |
|---|---|---|
| T01 company name: rule + confident mappings | A-02/P2 | 224 |
| T01b company name: case harmonisation | A-02 | 7 |
| T02 date text → date | mechanical | 0 (same values, new type) |
| T03 suspect dates flagged, **not changed** | A-07 | 6 (Twitch, Dell, Roku, Accenture, Unity, Adobe) |
| T04 industry group | A-04/P1 | 4,772 (new column; 1,564 → Unknown) |
| T05 / T05b country / HQ country relabels | A-03/A-05 | 36 / 6 |
| T06 / T06b tech city / state | A-06 | 35 / 31 (Dublin, Ottawa, Stockholm and Walldorf have no US state) |
| T07 tech headcount_status | A-08 | 35 |
| T08 derived reason category | A-10 | 1,524 rows got a category; 3,511 "Not stated" |
| T09 derived AI mention (global) | A-12 | 41 |
| T10 is_permanent_layoff | A-16 | 5,000 global; missing for tech |
| T11 news URL whitespace | A-14 | 6 |
| T12 duplicate groups (linked, not merged) | A-13 | 29 records in 11 groups |
| T13 internal duplicate flag | A-15 | 42 |

---

## 6. Items that need your attention

1. **New finding (flagged, not changed):** 7 rows have state or fragment values in a country column: `Arizona`, `Nevada`, `New York`, `Rhode Island`, `Quebec`, `Sa` (event country) and `Au` (HQ country). They are flagged `qc_country_not_a_country`, and their region is `Unresolved`. Relabelling them needs a decision from you.
2. **13 company names pending review**, kept exactly as raw (the 8 from P2, plus Tata Steel Netherlands and the Whole Foods unit, plus the 3 descriptions). Please confirm the 2 I added to this list.
3. **P3 disagreements:** 9 companies, 46 rows flagged. Examples: Accenture (tech Business Services vs global Finance & Fintech) and Snap (Software & IT vs Retail & Consumer).
4. **Case-harmonisation rule:** I chose "prefer not all-caps, then most rows". It changed 7 rows. Tell me if you'd rather leave capitalisation alone.
5. **Other noisy names are left as they are:** Phase 1 flagged 198 noisy names. Only legal suffixes and the reviewed long names were changed. Short descriptive names such as `Popular's integration into Santander` keep their raw text and their Phase 1 flag.
6. **Still open from Phase 1:** review of the 18 + 97 candidate pairs. No record is marked primary yet.

## 7. Files added or changed

- **New:** `notebooks/02_data_cleaning.ipynb`, `src/phase2_cleaning.py`, `tests/test_phase2_cleaning.py`, `tests/test_phase2_outputs.py`, everything in `data/processed/`, `reports/audit/phase2_check_log.csv`, this report
- **Changed:** `src/phase2_mappings.py` (P1, P2, P5), `tests/test_phase2_mappings.py`, `reports/phase2_proposals/*` (regenerated), `NOTEBOOK_PLAN.md` (status), `reports/audit/audit_log_history.csv` (appended only)
- **Not changed:** `data/raw/*`, Phase 1 notebook and code, `data/interim/*` (including both review files), audit history archives
