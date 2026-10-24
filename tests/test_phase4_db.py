"""Phase 4 integration tests against a REAL PostgreSQL server, each in its own throwaway database.

They run only when LAYOFFS_ENABLE_DB_TESTS=1 and the PG* connection settings (or .env) point to a server
where the user may CREATE DATABASE. Every test database is named layoffs_test_<random>, is created by
the fixture and dropped afterwards; no other database is touched. Without the setting these tests are
SKIPPED (reported as skipped, not passed).
"""
from pathlib import Path
import os
import secrets
import shutil
import sys

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import phase4_config as config  # noqa: E402
import phase4_load as loader  # noqa: E402
import phase4_analytics as analytics  # noqa: E402

PROCESSED = ROOT / "data" / "processed"
config.load_dotenv(ROOT / ".env")
pytestmark = pytest.mark.skipif(os.environ.get("LAYOFFS_ENABLE_DB_TESTS") != "1",
                                reason="set LAYOFFS_ENABLE_DB_TESTS=1 (and PG* settings) to run database tests")

CORE_COUNTS = {"source_datasets": 2, "company_name_mapping": 3532, "industry_mapping": 77, "layoff_events": 5035,
               "layoff_event_departments": 70, "quality_issues": 4886, "transformation_log": 16, "field_lineage": 54,
               "cross_source_industry_disagreements": 9, "possible_duplicate_pairs": 18,
               "excluded_candidate_pairs": 97}


@pytest.fixture
def test_db():
    name = f"layoffs_test_{secrets.token_hex(4)}"
    admin = config.connect(root=ROOT)
    admin.autocommit = True
    with admin.cursor() as cur:
        cur.execute(f'CREATE DATABASE "{name}" ENCODING \'UTF8\' TEMPLATE template0')
    try:
        yield name
    finally:
        assert name.startswith("layoffs_test_")              # never drop anything else
        with admin.cursor() as cur:
            cur.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s", (name,))
            cur.execute(f'DROP DATABASE IF EXISTS "{name}"')
        admin.close()


def q(db, sql, params=None):
    conn = config.connect(db, ROOT)
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()


def core_counts(db):
    return {t: q(db, f"SELECT count(*) FROM core.{t}")[0][0] for t in CORE_COUNTS}


def fingerprint(db):
    """Cheap content fingerprint of the core tables, to prove a failed load changed nothing."""
    return q(db, "SELECT md5(string_agg(e::text, '|' ORDER BY event_key)) FROM core.layoff_events e")[0][0], \
        core_counts(db)


@pytest.fixture
def loaded_db(test_db):
    loader.run_load(dbname=test_db, verbose=False)
    return test_db


@pytest.fixture
def work_dir(tmp_path):
    d = tmp_path / "processed"
    shutil.copytree(PROCESSED, d)
    return d


# ---------------------------------------------------------------- clean load, counts, audit
def test_clean_load_counts_and_checks(test_db):
    summary = loader.run_load(dbname=test_db, verbose=False)
    assert core_counts(test_db) == CORE_COUNTS
    assert summary["checks"] and all(c["passed"] for c in summary["checks"])
    runs = q(test_db, "SELECT status, manifest_checked, input_dir FROM audit.load_runs")
    assert runs == [("succeeded", True, "data/processed")]
    files = q(test_db, "SELECT file_name, csv_rows, staging_rows, core_rows, matches_manifest FROM audit.load_files")
    assert len(files) == 10 and all(r[1] == r[2] == r[3] and r[4] for r in files)
    n, passed = q(test_db, "SELECT count(*), count(*) FILTER (WHERE passed) FROM audit.validation_results")[0]
    assert n == passed == len(summary["checks"]) >= 140


def test_repeat_load_does_not_double_data(loaded_db):
    before = fingerprint(loaded_db)
    loader.run_load(dbname=loaded_db, verbose=False)
    assert fingerprint(loaded_db) == before
    assert core_counts(loaded_db) == CORE_COUNTS
    assert q(loaded_db, "SELECT count(*) FROM staging.layoff_events")[0][0] == 5035
    assert q(loaded_db, "SELECT status, count(*) FROM audit.load_runs GROUP BY 1") == [("succeeded", 2)]


# ---------------------------------------------------------------- nulls, flags, duplicates preserved
def test_missing_values_stay_null(loaded_db):
    ev = pd.read_csv(PROCESSED / "layoff_events.csv", dtype=str, keep_default_na=False, na_values=[""])
    row = q(loaded_db, """SELECT count(*) - count(employees_laid_off), count(*) - count(workforce_pct),
                                 count(*) - count(country), count(*) - count(industry_raw),
                                 count(*) FILTER (WHERE employees_laid_off = 0),
                                 count(*) FILTER (WHERE company_domain IN ('', 'NULL', 'nan', 'None')),
                                 count(*) FILTER (WHERE qc_headcount_not_verified IS NULL)
                          FROM core.layoff_events""")[0]
    assert row == (ev["employees_laid_off"].isna().sum(), ev["workforce_pct"].isna().sum(), ev["country"].isna().sum(),
                   ev["industry_raw"].isna().sum(), 0, 0, 35)
    assert row[:4] == (2511, 3879, 470, 1564)


def test_quality_limitations_are_preserved_not_fixed(loaded_db):
    assert q(loaded_db, "SELECT count(*) FROM core.layoff_events WHERE region = 'Unresolved'")[0][0] == 6
    assert q(loaded_db, "SELECT count(*) FROM core.layoff_events WHERE industry_group = 'Unknown'")[0][0] == 1564
    assert q(loaded_db, "SELECT count(*) FROM core.layoff_events WHERE qc_country_not_a_country")[0][0] == 7
    suspects = q(loaded_db, "SELECT event_key, event_date::text = event_date_raw FROM core.layoff_events "
                            "WHERE qc_suspect_date ORDER BY 1")
    assert [k for k, _ in suspects] == ["T-00002", "T-00007", "T-00013", "T-00014", "T-00018", "T-00031"]
    assert all(same for _, same in suspects)
    assert q(loaded_db, "SELECT count(*), count(DISTINCT possible_duplicate_group) FROM core.layoff_events "
                        "WHERE possible_duplicate_group IS NOT NULL")[0] == (29, 11)
    assert q(loaded_db, "SELECT count(*) FROM core.layoff_events WHERE possible_internal_duplicate")[0][0] == 42
    assert q(loaded_db, "SELECT DISTINCT review_status FROM core.possible_duplicate_pairs") == [("pending_review",)]


def test_exact_numeric_reconciliation(loaded_db):
    ev = pd.read_csv(PROCESSED / "layoff_events.csv", keep_default_na=False, na_values=[""], low_memory=False)
    g = ev[ev["source_dataset"] == "fliar_global_sample"]
    total, n = q(loaded_db, "SELECT sum(employees_laid_off), count(employees_laid_off) FROM core.v_global_events")[0]
    assert (total, n) == (int(g["employees_laid_off"].sum()), 2489) == (2788908, 2489)
    assert str(q(loaded_db, "SELECT workforce_pct FROM core.layoff_events WHERE workforce_pct::text LIKE '33.3333%' "
                            "LIMIT 1")[0][0]) == "33.333333"       # no rounding on the way in


def test_bridge_relationship(loaded_db):
    assert q(loaded_db, """SELECT count(*) FROM (SELECT event_key FROM core.layoff_event_departments
                           GROUP BY event_key HAVING sum(allocation_weight) <> 1) x""")[0][0] == 0
    assert q(loaded_db, "SELECT count(DISTINCT event_key) FROM core.layoff_event_departments")[0][0] == 35
    import psycopg2
    conn = config.connect(loaded_db, ROOT)
    try:
        with pytest.raises(psycopg2.errors.ForeignKeyViolation), conn.cursor() as cur:
            cur.execute("INSERT INTO core.layoff_event_departments VALUES "
                        "('T-99999', 'tech_layoffs_2025_2026', 99, 'X', 'X', 1, 1, 1)")
    finally:
        conn.rollback()
        conn.close()


# ---------------------------------------------------------------- failure behaviour and rollback
def test_invalid_input_is_rejected_before_touching_the_database(loaded_db, work_dir):
    before = fingerprint(loaded_db)
    path = work_dir / "layoff_events.csv"
    path.write_text(path.read_text(encoding="utf-8").replace(",2019-01-04,2019-01-04,", ",2019-01-04,2019-13-45,", 1),
                    encoding="utf-8")
    with pytest.raises(loader.LoadError, match="differs from the verified Phase 2 output"):
        loader.run_load(work_dir, dbname=loaded_db, verbose=False)
    with pytest.raises(loader.LoadError, match="event_date is not date"):
        loader.run_load(work_dir, dbname=loaded_db, check_manifest=False, verbose=False)
    assert fingerprint(loaded_db) == before
    assert q(loaded_db, "SELECT count(*) FROM audit.load_runs")[0][0] == 1        # pre-flight never writes


def test_broken_relationship_rolls_back_and_keeps_committed_data(loaded_db, work_dir):
    before = fingerprint(loaded_db)
    path = work_dir / "layoff_event_departments.csv"
    path.write_text(path.read_text(encoding="utf-8").replace("T-00001,", "T-99999,", 1), encoding="utf-8")
    with pytest.raises(loader.LoadError) as exc:
        loader.run_load(work_dir, dbname=loaded_db, check_manifest=False, verbose=False)
    assert exc.value.stage == "core" and "foreign key" in str(exc.value)
    assert fingerprint(loaded_db) == before                                         # rollback worked
    assert q(loaded_db, "SELECT count(*) FROM staging.layoff_event_departments WHERE event_key = 'T-99999'")[0][0] == 0
    status = q(loaded_db, "SELECT status, error_stage, manifest_checked FROM audit.load_runs ORDER BY run_id")
    assert status == [("succeeded", None, True), ("failed", "core", False)]


def test_failed_validation_check_rolls_back(loaded_db, work_dir):
    before = fingerprint(loaded_db)
    path = work_dir / "quality_issues.csv"
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    path.write_text("".join(lines[:1] + lines[2:]), encoding="utf-8")       # drop one issue row
    with pytest.raises(loader.LoadError) as exc:
        loader.run_load(work_dir, dbname=loaded_db, check_manifest=False, verbose=False)
    assert exc.value.stage == "validation" and "qc.quality_issues_match_flags" in str(exc.value)
    assert fingerprint(loaded_db) == before
    failed = q(loaded_db, "SELECT check_id FROM audit.validation_results v JOIN audit.load_runs r USING (run_id) "
                          "WHERE r.status = 'failed' AND NOT v.passed")
    assert ("qc.quality_issues_match_flags",) in failed


def test_refuses_to_replace_data_of_unknown_origin(loaded_db):
    conn = config.connect(loaded_db, ROOT)
    with conn, conn.cursor() as cur:
        cur.execute("UPDATE audit.load_runs SET status = 'failed'")
    conn.close()
    before = fingerprint(loaded_db)
    with pytest.raises(loader.LoadError, match="not loaded by this pipeline"):
        loader.run_load(dbname=loaded_db, verbose=False)
    assert fingerprint(loaded_db) == before


def test_schema_drift_stops_without_altering(test_db):
    conn = config.connect(test_db, ROOT)
    with conn, conn.cursor() as cur:
        cur.execute("CREATE SCHEMA core; CREATE TABLE core.transformation_log (rule_id text, note text)")
    conn.close()
    with pytest.raises(loader.LoadError, match="core.transformation_log: columns differ"):
        loader.run_load(dbname=test_db, verbose=False)
    assert q(test_db, "SELECT column_name FROM information_schema.columns WHERE table_schema = 'core' "
                      "AND table_name = 'transformation_log' ORDER BY ordinal_position") == [("rule_id",), ("note",)]


def test_wrong_database_encoding_is_rejected(test_db):
    admin = config.connect(root=ROOT)
    admin.autocommit = True
    name = test_db + "_ascii"
    with admin.cursor() as cur:
        cur.execute(f'CREATE DATABASE "{name}" ENCODING \'SQL_ASCII\' LC_COLLATE \'C\' LC_CTYPE \'C\' TEMPLATE template0')
    try:
        with pytest.raises(loader.LoadError, match="UTF8 is required"):
            loader.run_load(dbname=name, verbose=False)
    finally:
        with admin.cursor() as cur:
            cur.execute(f'DROP DATABASE "{name}"')
        admin.close()


# ---------------------------------------------------------------- analytical SQL
def run_sql(db, name):
    conn = config.connect(db, ROOT)
    try:
        return analytics.run_query(conn, ROOT / "sql" / "analytics" / f"{name}.sql")[0]
    finally:
        conn.close()


def test_every_query_runs_and_reconciles_with_phase3(loaded_db):
    for path in sorted((ROOT / "sql" / "analytics").glob("*.sql")):
        result = run_sql(loaded_db, path.stem)
        assert len(result) > 0, path.name
        if path.stem in analytics.RECONCILE:
            rec = analytics.reconcile(path.stem, result, ROOT / "reports" / "eda")
            assert rec["cells_compared"] > 0 and rec["mismatches"] == 0, (path.name, rec["mismatch_examples"])


def test_reconciliation_detects_a_difference(loaded_db):
    result = run_sql(loaded_db, "02_yearly_events_and_known_job_cuts")
    result.loc[0, "verified_jobs_cut"] += 1
    assert analytics.reconcile("02_yearly_events_and_known_job_cuts", result, ROOT / "reports" / "eda")["mismatches"] == 1


def test_global_queries_never_include_tech_rows(loaded_db):
    assert run_sql(loaded_db, "02_yearly_events_and_known_job_cuts")["events"].sum() == 5000
    assert run_sql(loaded_db, "01_monthly_events")["events"].sum() == 5000
    assert run_sql(loaded_db, "11_tech_reason_summary")["events"].sum() == 35


def test_period_labels_for_partial_2026(loaded_db):
    months = run_sql(loaded_db, "01_monthly_events").set_index("month")["period_note"]
    assert months["2026-05"].startswith("partial: possible collection lag") and months["2026-06"].startswith("partial")
    assert months["2026-04"].startswith("partial year") and months["2025-12"] == "complete"


def _global_csv():
    ev = pd.read_csv(PROCESSED / "layoff_events.csv", keep_default_na=False, na_values=[""], low_memory=False)
    return ev[ev["source_dataset"] == "fliar_global_sample"]


def test_repeat_layoff_queries_match_pandas(loaded_db):
    g = _global_csv()
    per = g.groupby("company_name").agg(events=("event_key", "size"),
                                        dup=("possible_internal_duplicate", lambda s: (s == True).sum()),  # noqa: E712
                                        jobs=("employees_laid_off", lambda s: s.sum(min_count=1)))
    repeat = per[per["events"] >= 2].sort_values(["events"], ascending=False)
    sql_rep = run_sql(loaded_db, "15_repeat_layoff_companies").set_index("company_name")
    assert set(sql_rep.index) == set(repeat.index) and len(sql_rep) == 688
    for name, r in repeat.iterrows():
        s = sql_rep.loc[name]
        assert s["events"] == r["events"] and s["events_flagged_internal_duplicate"] == r["dup"]
        assert (pd.isna(s["known_jobs_cut"]) and pd.isna(r["jobs"])) or s["known_jobs_cut"] == r["jobs"]
    dist = run_sql(loaded_db, "16_repeat_layoff_distribution").set_index("events_per_company")["companies_all"]
    expected = per["events"].clip(upper=4).value_counts()
    assert dist["1"] == expected[1] and dist["2"] == expected[2] and dist["3"] == expected[3] and dist["4+"] == expected[4]
    assert dist.sum() == g["company_name"].nunique()


def test_workforce_pct_by_year_uses_known_values_only(loaded_db):
    g = _global_csv()
    res = run_sql(loaded_db, "10_workforce_pct_by_year")
    total = res[res["event_year"].isna()].iloc[0]
    assert total["rows_with_pct"] == g["workforce_pct"].notna().sum() == 1121
    assert total["rows_without_pct"] == 3879 and float(total["median_workforce_pct"]) == g["workforce_pct"].median()
    by_year = res.dropna(subset=["event_year"]).set_index("event_year")
    for y, grp in g.groupby("event_year"):
        assert by_year.loc[y, "rows_with_pct"] == grp["workforce_pct"].notna().sum()
        assert float(by_year.loc[y, "median_workforce_pct"]) == grp["workforce_pct"].median()
