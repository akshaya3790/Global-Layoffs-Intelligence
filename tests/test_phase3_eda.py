"""Phase 3 tests: aggregations reconcile with the canonical table under the documented filters
(src/phase3_eda.py rules R-SOURCE ... R-SAMPLE), missing values never become 0, duplicates are never
silently dropped, and every chart-input CSV written by notebook 03 matches a fresh recomputation."""
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import phase3_eda as eda  # noqa: E402

PROCESSED = ROOT / "data" / "processed"
EDA_DIR = ROOT / "reports" / "eda"


@pytest.fixture(scope="module")
def events():
    return eda.load_events(PROCESSED / "layoff_events.csv")


@pytest.fixture(scope="module")
def g(events):
    return eda.global_rows(events)


@pytest.fixture(scope="module")
def t(events):
    return eda.tech_rows(events)


# ---------------------------------------------------------------- synthetic: R-JOBS never turns missing into 0
def _toy():
    return pd.DataFrame({
        "event_key": ["a", "b", "c", "d", "e"],
        "grp": ["X", "X", "Y", "Y", "Z"],
        "employees_laid_off": pd.array([100, pd.NA, pd.NA, pd.NA, 0], dtype="Int64"),
    })


def test_group_with_no_headcount_gets_nan_not_zero():
    out = eda.summarise(_toy(), "grp")
    assert out.loc["X", "verified_jobs_cut"] == 100           # missing row in X is ignored, not added as 0
    assert pd.isna(out.loc["Y", "verified_jobs_cut"])         # all missing -> NaN, never 0
    assert out.loc["Y", "events"] == 2 and out.loc["Y", "events_with_headcount"] == 0
    assert out.loc["Y", "headcount_coverage_pct"] == 0


def test_a_real_zero_is_kept_as_zero():
    out = eda.summarise(_toy(), "grp")
    assert out.loc["Z", "verified_jobs_cut"] == 0 and out.loc["Z", "events_with_headcount"] == 1


def test_median_ignores_missing_rows():
    out = eda.summarise(_toy(), "grp")
    assert out.loc["X", "median_cut"] == 100                   # would be 50 if missing were treated as 0


def test_size_bands_exclude_missing_and_cover_every_known_value():
    toy = pd.DataFrame({"employees_laid_off": pd.array([1, 99, 100, 499, 500, 999, 1000, 4999, 5000, pd.NA],
                                                       dtype="Int64")})
    bands = eda.size_band_summary(toy).set_index("size_band")["events"]
    assert bands.tolist() == [2, 2, 2, 2, 1] and bands.sum() == 9


def test_pct_bands_exclude_missing_and_include_100():
    toy = pd.DataFrame({"workforce_pct": pd.array([0, 4.9, 5, 50, 100, pd.NA], dtype="Float64")})
    bands = eda.pct_summary(toy).set_index("workforce_pct_band")["events"]
    assert bands.sum() == 5 and bands["50-100%"] == 2 and bands["0-5%"] == 2


# ---------------------------------------------------------------- R-SOURCE: global and tech never mixed
def test_global_and_tech_split_is_complete_and_disjoint(events, g, t):
    assert len(g) == 5000 and len(t) == 35 and len(g) + len(t) == len(events)
    assert set(g["source_confidence"]) == {"high"} and set(t["source_confidence"]) == {"low"}


def test_global_aggregations_contain_no_tech_rows(g):
    assert eda.yearly_summary(g)["events"].sum() == 5000
    assert eda.monthly_events(g)["month"].min() == "2019-01"


# ---------------------------------------------------------------- totals reconcile (R-EVENTS, R-JOBS)
def test_yearly_monthly_industry_region_country_totals_equal_5000(g):
    assert eda.yearly_summary(g)["events"].sum() == 5000
    assert eda.monthly_events(g)["events"].sum() == 5000
    assert eda.industry_summary(g)["events"].sum() == 5000
    assert eda.region_summary(g)["events"].sum() == 5000
    assert eda.country_summary(g)["events"].sum() == 5000
    assert eda.industry_year_share(g).sum().round(0).between(99, 101).all()


def test_verified_jobs_equal_sum_of_present_headcounts(g):
    total = int(g["employees_laid_off"].dropna().sum())
    for table in [eda.yearly_summary(g), eda.industry_summary(g), eda.region_summary(g), eda.country_summary(g)]:
        assert int(table["verified_jobs_cut"].sum()) == total
        assert table["events_with_headcount"].sum() == 2489


def test_missing_headcounts_stay_missing(g):
    assert g["employees_laid_off"].isna().sum() == 2511
    assert g["workforce_pct"].isna().sum() == 3879
    assert eda.size_band_summary(g)["events"].sum() == 2489
    assert eda.pct_summary(g)["events"].sum() == 1121
    # median over known values only; treating missing as 0 would pull it to 0
    assert g["employees_laid_off"].median() == 200


def test_unresolved_country_groups_show_nan_not_zero(g):
    c = eda.country_summary(g).set_index("country")
    for name in ["Arizona", "New York", "Quebec", "Sa"]:          # these 4 rows have no headcount
        assert pd.isna(c.loc[name, "verified_jobs_cut"])


# ---------------------------------------------------------------- R-UNKNOWN: Unknown and Unresolved stay visible
def test_unknown_and_unresolved_are_visible(g):
    ind = eda.industry_summary(g).set_index("industry_group")
    assert ind.loc["Unknown", "events"] == 1564 == int(g["qc_missing_sector"].sum())
    reg = eda.region_summary(g).set_index("region")
    assert reg.loc["Unknown", "events"] == 470 and reg.loc["Unresolved", "events"] == 6
    c = eda.country_summary(g)
    assert set(c.loc[c["country_status"] == "not a country (flagged)", "country"]) == \
        {"Arizona", "Nevada", "New York", "Rhode Island", "Quebec", "Sa"}


def test_us_share_uses_known_country_base(g):
    us = eda.us_share_by_year(g)
    assert us["events_known_country"].sum() + us["events_missing_country"].sum() == 5000
    assert us["us_events"].sum() == (g["country"] == "United States").sum()


# ---------------------------------------------------------------- duplicates are never silently removed
def test_duplicate_candidates_remain_in_counts(g):
    sens = eda.sensitivity_by_year(g)
    assert sens["all_events"].sum() == 5000
    assert sens["all_events"].sum() - sens["excl_internal_duplicates"].sum() == 42
    assert sens["all_events"].sum() - sens["excl_cross_source_duplicate_candidates"].sum() == 18
    assert (sens["all_events"].values == eda.yearly_summary(g)["events"].values).all()


def test_furloughs_are_counted_and_excludable(g):
    sens = eda.sensitivity_by_year(g).set_index("event_year")
    assert sens.loc[2020, "all_events"] - sens.loc[2020, "excl_furloughs"] == 105
    assert sens["all_events"].sum() - sens["excl_furloughs"].sum() == int(g["is_furlough"].sum())


# ---------------------------------------------------------------- quality flags: not computed != False
def test_qc_summary_matches_columns_and_keeps_not_computed_separate(events):
    qc = eda.qc_flag_summary(events)
    for _, r in qc.iterrows():
        col = events.loc[events["source_dataset"] == r["source_dataset"], r["flag"]]
        assert r["true"] == col.sum() and r["not_computed"] == col.isna().sum()
    tech = qc[qc["source_dataset"] == eda.TECH].set_index("flag")
    assert tech.loc["qc_suspect_date", "true"] == 6
    assert tech.loc["qc_same_company_same_url", "not_computed"] == 35


# ---------------------------------------------------------------- tech-only tables
def test_tech_tables_reconcile(t):
    bridge = pd.read_csv(PROCESSED / "layoff_event_departments.csv")
    assert eda.tech_reason_summary(t)["events"].sum() == 35
    ai = eda.tech_ai_summary(t)
    assert ai["events"].sum() == 35 and ai["suspect_dates"].sum() == 6
    assert ai["reported_laid_off"].sum() == t["employees_laid_off"].sum()
    assert eda.tech_severance_summary(t)["events"].sum() == 35
    dept = eda.tech_department_summary(bridge)
    assert dept["events_involving"].sum() == len(bridge) == 70
    assert np.isclose(dept["weighted_events"].sum(), 35)
    assert bridge["event_key"].nunique() == 35 and "employees_laid_off" not in bridge.columns


# ---------------------------------------------------------------- chart-input CSVs written by notebook 03
CHART_INPUTS = {
    "03_01_monthly_events.csv": lambda g, t: eda.monthly_events(g),
    "03_02_yearly_events_and_jobs.csv": lambda g, t: eda.yearly_summary(g),
    "03_03_industry_ranking.csv": lambda g, t: eda.industry_summary(g),
    "03_05_region_events.csv": lambda g, t: eda.region_summary(g),
    "03_07_us_share_by_year.csv": lambda g, t: eda.us_share_by_year(g),
}


@pytest.mark.parametrize("name", sorted(CHART_INPUTS))
def test_chart_input_csv_matches_recomputation(name, g, t):
    path = EDA_DIR / name
    if not path.exists():
        pytest.skip("run notebooks/03_exploratory_analysis.ipynb first")
    saved = pd.read_csv(path)
    fresh = CHART_INPUTS[name](g, t).reset_index(drop=True)
    assert list(saved.columns) == list(fresh.columns)
    for col in saved.columns:
        a, b = saved[col], fresh[col]
        if pd.api.types.is_numeric_dtype(a) or pd.api.types.is_bool_dtype(a):
            assert np.allclose(a.astype(float), pd.to_numeric(b, errors="coerce").astype(float), equal_nan=True), col
        else:
            assert a.astype(str).tolist() == b.astype(str).tolist(), col


def test_chart_input_csv_totals_use_known_values_only():
    path = EDA_DIR / "03_08_size_and_pct_distribution.csv"
    if not path.exists():
        pytest.skip("run notebooks/03_exploratory_analysis.ipynb first")
    yearly = pd.read_csv(EDA_DIR / "03_02_yearly_events_and_jobs.csv")
    assert yearly["events"].sum() == 5000 and yearly["events_with_headcount"].sum() == 2489
    bands = pd.read_csv(EDA_DIR / "03_08_size_and_pct_distribution.csv")
    assert bands.loc[bands["chart"] == "size_band", "events"].sum() == 2489
    assert bands.loc[bands["chart"] == "pct_band", "events"].sum() == 1121
