"""Tests the Phase 1 validation rules on SYNTHETIC data only.

The synthetic rows live in tests/fixtures/synthetic_validation_cases.csv and are never
added to data/raw or data/interim. Run from the project root:  python -m pytest -v tests
"""
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from phase1_validation import validation_flags, to_number  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "synthetic_validation_cases.csv"
EXPECTED_START, EXPECTED_END, AUDIT_DATE = "2019-01-01", "2026-06-30", "2026-10-23"   # same values as the notebook

# For each case: the flags that MUST be True. Every other flag must be False.
EXPECTED = {
    "S01": {"qc_date_unparseable"},
    "S02": {"qc_date_unparseable"},
    "S03": {"qc_date_after_audit_date", "qc_date_outside_expected_range"},
    "S04": {"qc_headcount_not_positive"},
    "S05": {"qc_pct_out_of_range"},
    "S06": {"qc_non_numeric_value", "qc_headcount_status_conflict"},  # 'verified' but no usable number
    "S07": {"qc_non_numeric_value"},
    "S08": set(),
    "S09": {"qc_headcount_status_conflict"},
    "S10": set(),
    "S11": {"qc_date_outside_expected_range"},
    "S12": {"qc_headcount_not_positive"},
}


@pytest.fixture(scope="module")
def cases():
    # read exactly like the notebook reads the raw files
    return pd.read_csv(FIXTURE, keep_default_na=False, na_values=[""]).set_index("case_id")


@pytest.fixture(scope="module")
def flags(cases):
    return validation_flags(cases, date_col="date", headcount_col="headcount_cut", pct_col="pct_workforce",
                            expected_start=EXPECTED_START, expected_end=EXPECTED_END, audit_date=AUDIT_DATE,
                            status_col="headcount_status", other_numeric_cols=("news_mentions",))


def test_fixture_covers_every_case(cases):
    assert set(cases.index) == set(EXPECTED)


@pytest.mark.parametrize("case_id", sorted(EXPECTED))
def test_each_case_flagged_exactly(flags, case_id):
    raised = {col for col, value in flags.loc[case_id].items() if bool(value)}
    assert raised == EXPECTED[case_id], f"{case_id}: expected {EXPECTED[case_id]}, got {raised}"


def test_missing_headcount_stays_missing(cases):
    numbers = to_number(cases["headcount_cut"])
    assert np.isnan(numbers["S08"])                 # missing stays NaN
    assert not (numbers.fillna(-1) == 0).loc[["S08"]].any()   # and is never turned into 0
    assert cases.loc["S08", "headcount_cut"] != 0 and pd.isna(cases.loc["S08", "headcount_cut"])


def test_text_in_numeric_field_is_not_turned_into_zero(cases):
    numbers = to_number(cases["headcount_cut"])
    assert np.isnan(numbers["S06"])


def test_rules_do_not_modify_input(cases):
    before = cases.copy()
    validation_flags(cases, "date", "headcount_cut", "pct_workforce", EXPECTED_START, EXPECTED_END, AUDIT_DATE,
                     status_col="headcount_status")
    pd.testing.assert_frame_equal(cases, before)


def test_original_inline_rule_could_not_handle_text(cases):
    """Documents WHY the non-numeric rule was added: the first version of the notebook compared the raw
    column directly (`df["headcount_cut"] <= 0`). With text in the column that comparison crashes."""
    with pytest.raises(TypeError):
        _ = cases["headcount_cut"] <= 0
