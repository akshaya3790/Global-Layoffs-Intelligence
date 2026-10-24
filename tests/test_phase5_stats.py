"""Phase 5 tests: the Kaplan-Meier and log-rank code match hand-worked answers, the bootstrap resamples
companies (not rows) and never turns a missing headcount into 0, the benchmark uses only global rows, and
the CSVs written by notebook 05 match a fresh recomputation."""
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import phase3_eda as eda  # noqa: E402
import phase5_stats as st  # noqa: E402

STATS_DIR = ROOT / "reports" / "stats"


@pytest.fixture(scope="module")
def g():
    return eda.global_rows(eda.load_events(ROOT / "data" / "processed" / "layoff_events.csv"))


# ---------------------------------------------------------------- synthetic: survival maths
def test_kaplan_meier_matches_hand_calculation():
    # times 1,2,2,3(censored),4: S(1)=4/5, S(2)=S(1)*2/4, S(4)=0
    km = st.kaplan_meier([1, 2, 2, 3, 4], [1, 1, 1, 0, 1]).set_index("t")
    assert km.loc[1.0, "survival"] == pytest.approx(0.8)
    assert km.loc[2.0, "survival"] == pytest.approx(0.8 * 2 / 4)
    assert km.loc[4.0, "survival"] == pytest.approx(0.0)
    assert 3.0 not in km.index                      # a censored time is not an event time
    assert km.loc[2.0, "at_risk"] == 4


def test_censoring_raises_survival_compared_with_ignoring_it():
    d, e = [1, 2, 3, 4, 5, 6], [1, 0, 1, 0, 1, 0]
    km = st.kaplan_meier(d, e)
    naive_share_repeated = sum(e) / len(e)
    assert 1 - km["survival"].iloc[-1] > naive_share_repeated


def test_logrank_identical_groups_has_no_signal():
    d = [1, 2, 3, 4, 1, 2, 3, 4]
    e = [1, 1, 0, 1, 1, 1, 0, 1]
    res = st.logrank_test(d, e, ["a"] * 4 + ["b"] * 4)
    assert res["chi2"] == pytest.approx(0, abs=1e-9)
    assert res["p_value"] == pytest.approx(1.0)


def test_logrank_two_group_known_value():
    # Group a fails at 1,2; group b at 3,4. The textbook two-group statistic is computed independently below.
    d = np.array([1, 2, 3, 4], float)
    e = np.array([1, 1, 1, 1])
    grp = np.array(["a", "a", "b", "b"])
    O = E = V = 0.0
    for t in [1, 2, 3, 4]:
        n = (d >= t).sum(); n1 = ((d >= t) & (grp == "a")).sum(); d1 = ((d == t) & (grp == "a")).sum()
        O += d1; E += n1 / n
        V += (n1 / n) * (1 - n1 / n) if n > 1 else 0
    assert st.logrank_test(d, e, grp)["chi2"] == pytest.approx(round((O - E) ** 2 / V, 2))


# ---------------------------------------------------------------- real data
def test_benchmark_uses_global_rows_only(g):
    b = st.benchmark_by_year(g)
    assert b["sample_events"].sum() == 5000
    assert b.loc[b["event_year"] == 2023, "sample_events"].item() == 885
    assert b["events_ratio"].between(0.25, 0.28).all()


def test_first_gap_table_one_row_per_company(g):
    gaps = st.first_gap_table(g)
    assert len(gaps) == g[st.CLUSTER_KEY].nunique()
    repeaters = (g[st.CLUSTER_KEY].value_counts() >= 2).sum()
    assert gaps["event"].sum() == repeaters
    assert (gaps["duration_days"] >= 0).all()
    assert (gaps.loc[gaps["event"] == 0, "first_date"] + pd.to_timedelta(gaps.loc[gaps["event"] == 0, "duration_days"], "D")
            == st.STUDY_END).all()


def test_bootstrap_point_estimates_and_missing_jobs(g):
    boot = st.cluster_bootstrap_yearly(g, n_boot=50, seed=1)
    yearly = g.groupby("event_year").size()
    assert boot.set_index("event_year")["events"].astype(int).to_dict() == yearly.to_dict()
    assert (boot["events_lo"] <= boot["events"]).all() and (boot["events"] <= boot["events_hi"]).all()
    # disclosed jobs are a sum of present values only: equal to the plain sum, never filled with 0
    assert boot.loc[boot["event_year"] == 2020, "disclosed_jobs"].item() == g.loc[g["event_year"] == 2020, "employees_laid_off"].sum()
    assert boot.attrs["clusters"] == g[st.CLUSTER_KEY].nunique()


def test_bootstrap_resamples_companies_not_rows():
    # Company X has 3 events, Y has 1. Drawing 2 companies gives XX=6, XY=4 or YY=2 events, never 3 or 5.
    toy = pd.DataFrame({"event_key": list("abcd"), "event_year": [2020] * 4,
                        "employees_laid_off": pd.array([10, pd.NA, 5, 7], dtype="Int64"),
                        st.CLUSTER_KEY: ["X", "X", "X", "Y"]})
    boot = st.cluster_bootstrap_yearly(toy, n_boot=200, seed=3, level=1.0)
    assert set([boot["events_lo"].item(), boot["events_hi"].item()]) <= {2, 4, 6}


# ---------------------------------------------------------------- notebook 05 outputs
@pytest.mark.parametrize("name", ["benchmark_by_year.csv", "benchmark_categories.csv"])
def test_saved_benchmarks_match_recomputation(g, name):
    path = STATS_DIR / name
    if not path.exists():
        pytest.skip("run notebooks/05_sample_validity_and_repeat_layoffs.ipynb first")
    fresh = st.benchmark_by_year(g) if name == "benchmark_by_year.csv" else st.benchmark_categories(g)
    saved = pd.read_csv(path)
    pd.testing.assert_frame_equal(saved, fresh, check_dtype=False)


def test_saved_repeat_probability_matches_recomputation(g):
    path = STATS_DIR / "repeat_probability_overall.csv"
    if not path.exists():
        pytest.skip("run notebooks/05_sample_validity_and_repeat_layoffs.ipynb first")
    fresh = st.repeat_probabilities(st.first_gap_table(g))
    pd.testing.assert_frame_equal(pd.read_csv(path), fresh, check_dtype=False)
