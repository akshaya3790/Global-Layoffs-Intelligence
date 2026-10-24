"""Synthetic tests (R1-R4) and regression tests for the four rules moved from notebook 01 into
src/phase1_validation.py. Synthetic rows live only in tests/fixtures/synthetic_r1_r4_cases.csv."""
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from phase1_validation import (flag_news_mentions_below_one, flag_laid_off_exceeds_total,  # noqa: E402
                               flag_negative_severance, flag_headcount_math_gap, headcount_math_gap_pct)

FIXTURE = ROOT / "tests" / "fixtures" / "synthetic_r1_r4_cases.csv"
CASES = pd.read_csv(FIXTURE, keep_default_na=False, na_values=[""]).set_index("case_id")


def run_rule(df: pd.DataFrame, rule: str) -> pd.Series:
    if rule == "R1":
        return flag_news_mentions_below_one(df["news_mentions"])
    if rule == "R2":
        return flag_laid_off_exceeds_total(df["employees_laid_off"], df["total_employees"])
    if rule == "R3":
        return flag_negative_severance(df["severance_weeks"])
    if rule == "R4":
        return flag_headcount_math_gap(df["employees_laid_off"], df["percentage_workforce"], df["total_employees"])
    raise ValueError(rule)


@pytest.mark.parametrize("case_id", list(CASES.index))
def test_synthetic_case(case_id):
    row = CASES.loc[[case_id]]
    result = bool(run_rule(row, row["rule"].iloc[0]).iloc[0])
    assert result == bool(row["expected_flag"].iloc[0]), f"{case_id}: {row['description'].iloc[0]}"


def test_every_rule_has_flag_and_no_flag_and_missing_cases():
    for rule, group in CASES.groupby("rule"):
        assert group["expected_flag"].any() and (~group["expected_flag"]).any(), rule
        assert group["description"].str.contains("missing").any(), rule


@pytest.mark.parametrize("rule", ["R1", "R2", "R3", "R4"])
def test_rules_do_not_modify_input(rule):
    data = CASES[CASES["rule"] == rule].copy()
    before = data.copy()
    run_rule(data, rule)
    pd.testing.assert_frame_equal(data, before)


def test_missing_inputs_stay_missing_in_gap():
    gap = headcount_math_gap_pct(pd.Series([500.0]), pd.Series([np.nan]), pd.Series([5000.0]))
    assert gap.isna().all()            # missing in -> missing out, never 0


# ---------------- regression: new functions == original notebook expressions on the REAL data -------------

@pytest.fixture(scope="module")
def real():
    glob = pd.read_csv(ROOT / "data" / "raw" / "layoffs_2019_2026_sample.csv", keep_default_na=False, na_values=[""])
    tech = pd.read_csv(ROOT / "data" / "raw" / "tech_layoffs_2025_2026.csv", keep_default_na=False, na_values=[""])
    return glob, tech


def test_regression_r1(real):
    glob, _ = real
    pd.testing.assert_series_equal(flag_news_mentions_below_one(glob["news_mentions"]),
                                   glob["news_mentions"] < 1, check_names=False)


def test_regression_r2(real):
    _, tech = real
    pd.testing.assert_series_equal(flag_laid_off_exceeds_total(tech["Employees_Laid_Off"], tech["Total_Employees"]),
                                   tech["Employees_Laid_Off"] > tech["Total_Employees"], check_names=False)


def test_regression_r3(real):
    _, tech = real
    pd.testing.assert_series_equal(flag_negative_severance(tech["Severance_Weeks"]),
                                   tech["Severance_Weeks"] < 0, check_names=False)


def test_regression_r4(real):
    _, tech = real
    implied = tech["Percentage_Workforce"] * tech["Total_Employees"] / 100            # original notebook code
    original_gap = (100 * (tech["Employees_Laid_Off"] - implied) / implied).round(1)
    new_gap = headcount_math_gap_pct(tech["Employees_Laid_Off"], tech["Percentage_Workforce"], tech["Total_Employees"])
    pd.testing.assert_series_equal(new_gap, original_gap, check_names=False)
    pd.testing.assert_series_equal(
        flag_headcount_math_gap(tech["Employees_Laid_Off"], tech["Percentage_Workforce"], tech["Total_Employees"]),
        original_gap.abs() > 10, check_names=False)
