"""Phase 5 tests for sql/ddl/06_bi_views.sql against a REAL PostgreSQL server, in a throwaway database.

Same switch as tests/test_phase4_db.py: they run only when LAYOFFS_ENABLE_DB_TESTS=1, and every database
they create is named layoffs_test_<random> and dropped afterwards. Each view is reconciled with a pandas
recomputation from data/processed, and no tech row may appear in any global view.
"""
from pathlib import Path
import os
import secrets
import sys

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import phase3_eda as eda  # noqa: E402
import phase4_config as config  # noqa: E402
import phase4_load as loader  # noqa: E402
import phase5_stats as st  # noqa: E402

config.load_dotenv(ROOT / ".env")
pytestmark = pytest.mark.skipif(os.environ.get("LAYOFFS_ENABLE_DB_TESTS") != "1",
                                reason="set LAYOFFS_ENABLE_DB_TESTS=1 (and PG* settings) to run database tests")


@pytest.fixture(scope="module")
def db():
    name = f"layoffs_test_{secrets.token_hex(4)}"
    admin = config.connect(root=ROOT)
    admin.autocommit = True
    with admin.cursor() as cur:
        cur.execute(f'CREATE DATABASE "{name}" ENCODING \'UTF8\' TEMPLATE template0')
    try:
        loader.run_load(dbname=name, verbose=False)
        yield name
    finally:
        assert name.startswith("layoffs_test_")              # never drop anything else
        with admin.cursor() as cur:
            cur.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s", (name,))
            cur.execute(f'DROP DATABASE IF EXISTS "{name}"')
        admin.close()


@pytest.fixture(scope="module")
def g():
    return eda.global_rows(eda.load_events(ROOT / "data" / "processed" / "layoff_events.csv"))


def frame(db, sql):
    conn = config.connect(db, ROOT)
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            return pd.DataFrame(cur.fetchall(), columns=[d[0] for d in cur.description])
    finally:
        conn.close()


def test_bi_events_global_only_and_nulls_kept(db, g):
    ev = frame(db, "SELECT * FROM core.v_bi_events")
    assert len(ev) == 5000
    assert not ev["event_key"].str.startswith("T-").any()            # no tech row in a global view
    assert ev["employees_laid_off"].isna().sum() == 2511               # undisclosed stays NULL, never 0
    assert (ev["has_disclosed_headcount"] == ev["employees_laid_off"].notna()).all()
    assert (ev.loc[ev["employees_laid_off"].isna(), "size_band"] == "Undisclosed").all()
    assert ev["is_partial_period"].sum() == (g["event_year"] == 2026).sum()
    assert ev["period_note"].notna().all()


def test_bi_kpis_match_pandas(db, g):
    k = frame(db, "SELECT * FROM core.v_bi_kpis").iloc[0]
    h = g["employees_laid_off"].dropna()
    assert k["events"] == 5000
    assert k["companies"] == g["company_name"].nunique()
    assert k["events_with_headcount"] == len(h) == 2489
    assert k["events_headcount_unknown"] == 2511
    assert k["disclosed_jobs_cut_lower_bound"] == h.sum()
    assert float(k["median_disclosed_cut"]) == float(h.median())
    assert k["events_2019_baseline"] == 476
    assert k["repeat_companies"] == (g["company_name"].value_counts() >= 2).sum()


def test_bi_company_summary_matches_survival_input(db, g):
    cs = frame(db, "SELECT * FROM core.v_bi_company_summary").set_index("company_name")
    gaps = st.first_gap_table(g).set_index("company_name")
    assert len(cs) == len(gaps)
    rep = gaps[gaps["event"] == 1]
    assert (cs.loc[rep.index, "days_to_second_event"].astype(int) == rep["duration_days"]).all()
    assert cs.loc[gaps[gaps["event"] == 0].index, "days_to_second_event"].isna().all()
    assert cs["events"].sum() == 5000


def test_bi_quality_reconciles(db, g):
    qv = frame(db, "SELECT * FROM core.v_bi_quality")
    for dim in ["year", "region", "industry_group"]:
        part = qv[qv["dimension"] == dim]
        assert part["events"].sum() == 5000
        assert part["events_with_headcount"].sum() == 2489
    yr = qv[qv["dimension"] == "year"].set_index("value")
    assert yr.loc["2023", "events"] == 885


def test_bi_benchmark_matches_notebook_05(db, g):
    b = frame(db, "SELECT * FROM core.v_bi_benchmark ORDER BY event_year").set_index("event_year")
    ref = st.benchmark_by_year(g).set_index("event_year")
    assert (b["sample_events"] == ref["sample_events"]).all()
    assert (b["events_ratio"].astype(float) == ref["events_ratio"]).all()
    assert (b["jobs_ratio"].astype(float) == ref["jobs_ratio"]).all()
