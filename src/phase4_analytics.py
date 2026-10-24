"""Phase 4: run every analytical query in sql/analytics/ and reconcile it with the Phase 3 chart data.

Usage (from the project root, after a successful load):
    python src/phase4_analytics.py

For each .sql file (in name order) this:
  * runs it inside a READ ONLY transaction (queries cannot change data),
  * saves the result to reports/phase4/query_results/<name>.csv,
  * where a matching Phase 3 chart-data file exists (reports/eda/), compares every overlapping cell.
A summary is written to reports/phase4/sql_reconciliation.csv. Exit code 1 if any query fails or
any reconciled cell differs.
"""
from __future__ import annotations

import math
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase4_config import connect, find_project_root, DatabaseConfigError  # noqa: E402

# query -> (Phase 3 file, filter on that file, {sql column: phase3 column} keys, {sql column: phase3 column} values)
RECONCILE = {
    "01_monthly_events": ("03_01_monthly_events.csv", None, {"month": "month"},
                          {"events": "events", "events_3m_avg": "events_3m_avg"}),
    "02_yearly_events_and_known_job_cuts": ("03_02_yearly_events_and_jobs.csv", None, {"event_year": "event_year"},
        {c: c for c in ["events", "events_with_headcount", "verified_jobs_cut", "median_cut", "headcount_coverage_pct",
                        "share_of_events_pct", "permanent_events", "furlough_events", "partial_year"]}),
    "03_industry_ranking": ("03_03_industry_ranking.csv", None, {"industry_group": "industry_group"},
        {c: c for c in ["rank_by_events", "events", "share_of_events_pct", "events_with_headcount",
                        "verified_jobs_cut", "headcount_coverage_pct", "median_cut"]}),
    "04_industry_share_by_year": ("03_04_industry_share_by_year.csv", "melt",
                                  {"industry_group": "industry_group", "event_year": "event_year"},
                                  {"share_pct": "share_pct"}),
    "05_region_comparison": ("03_05_region_events.csv", None, {"region": "region"},
        {c: c for c in ["events", "events_with_headcount", "verified_jobs_cut", "median_cut",
                        "headcount_coverage_pct", "share_of_events_pct"]}),
    "06_country_comparison": ("03_06_top_countries_outside_us.csv", None, {"country": "country"},
        {c: c for c in ["region", "events", "events_with_headcount", "verified_jobs_cut", "median_cut",
                        "headcount_coverage_pct", "share_of_events_pct", "country_status"]}),
    "07_us_share_by_year": ("03_07_us_share_by_year.csv", None, {"event_year": "event_year"},
        {c: c for c in ["events_known_country", "us_events", "us_share_pct", "events_missing_country"]}),
    "08_layoff_size_distribution": ("03_08_size_and_pct_distribution.csv", ("chart", "size_band"),
        {"size_band": "size_band"}, {"events": "events", "share_of_verified_pct": "share_of_verified_pct"}),
    "09_workforce_pct_distribution": ("03_08_size_and_pct_distribution.csv", ("chart", "pct_band"),
        {"workforce_pct_band": "workforce_pct_band"}, {"events": "events"}),
    "11_tech_reason_summary": ("03_T1_tech_reasons_and_departments.csv", ("chart", "reason"),
        {"reason_category_derived": "reason_category_derived"},
        {"events": "events", "reported_laid_off": "reported_laid_off"}),
    "12_tech_ai_related_summary": ("03_T2_tech_ai_and_severance.csv", ("chart", "ai_related"),
        {"ai_related": "ai_related"},
        {c: c for c in ["events", "reported_laid_off", "median_pct_workforce", "median_severance_weeks",
                        "suspect_dates"]}),
    "13_tech_department_summary": ("03_T1_tech_reasons_and_departments.csv", ("chart", "department"),
        {"department": "department"}, {"events_involving": "events_involving", "weighted_events": "weighted_events"}),
    "14_tech_severance_summary": ("03_T2_tech_ai_and_severance.csv", ("chart", "severance"),
        {"severance_weeks": "severance_weeks"}, {"events": "events"}),
    "17_quality_flag_summary": ("03_10_quality_flags_global.csv", None,
        {"source_dataset": "source_dataset", "flag": "flag"}, {"flagged": "true", "not_computed": "not_computed"}),
    "18_missingness_summary": ("03_09_missingness_global.csv", None,
        {"source_dataset": "source_dataset", "column_name": "column"},
        {"missing": "missing", "rows": "rows", "missing_pct": "missing_pct"}),
    "19_sensitivity_by_year": ("03_11_sensitivity_by_year.csv", None, {"event_year": "event_year"},
        {c: c for c in ["all_events", "excl_furloughs", "excl_internal_duplicates",
                        "excl_cross_source_duplicate_candidates", "furlough_share_pct"]}),
}
# Rounded percentages: pandas rounds half-to-even, PostgreSQL half-away-from-zero, so allow one rounding step.
PCT_TOLERANCE = 0.051


def run_query(conn, path: Path) -> tuple[pd.DataFrame, float]:
    start = time.perf_counter()
    with conn.cursor() as cur:
        cur.execute("SET TRANSACTION READ ONLY")
        cur.execute(path.read_text(encoding="utf-8"))
        cols = [d.name for d in cur.description]
        rows = cur.fetchall()
    conn.rollback()
    return pd.DataFrame(rows, columns=cols), time.perf_counter() - start


def _key(v) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "NULL"
    try:
        f = float(v)
        return str(int(f)) if f.is_integer() else str(f)
    except (TypeError, ValueError):
        return str(v)


def _same(a, b, column: str) -> bool:
    a_na = a is None or (isinstance(a, float) and math.isnan(a)) or (a is pd.NA)
    b_na = b is None or (isinstance(b, float) and math.isnan(b)) or (b is pd.NA) or b == ""
    if a_na or b_na:
        return a_na and b_na
    if isinstance(a, bool) or str(b) in ("True", "False"):
        return str(bool(a)) == str(b)
    try:
        tol = PCT_TOLERANCE if column.endswith("_pct") else 1e-9
        return abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        return str(a) == str(b)


def reconcile(name: str, result: pd.DataFrame, eda_dir: Path) -> dict:
    file_name, filt, keys, values = RECONCILE[name]
    ref = pd.read_csv(eda_dir / file_name, keep_default_na=False, na_values=[""])
    if filt == "melt":
        ref = ref.melt(id_vars="industry_group", var_name="event_year", value_name="share_pct")
    elif filt:
        ref = ref[ref[filt[0]].astype(str) == filt[1]]
    ref_index = {tuple(_key(r[c]) for c in keys.values()): r for _, r in ref.iterrows()}
    got_index = {tuple(_key(r[c]) for c in keys): r for _, r in result.iterrows()}
    mismatches, cells = [], 0
    for k, r in ref_index.items():
        g = got_index.get(k)
        for sql_col, ref_col in values.items():
            cells += 1
            if g is None:
                # a (group, year) combination with no rows: SQL returns no row, Phase 3 shows 0 share
                if filt == "melt" and float(r[ref_col]) == 0:
                    continue
                mismatches.append(f"{k}: row missing in SQL result")
                break
            if not _same(g[sql_col], r[ref_col], sql_col):
                mismatches.append(f"{k}.{sql_col}: sql={g[sql_col]} phase3={r[ref_col]}")
    return {"phase3_file": f"reports/eda/{file_name}", "rows_compared": len(ref_index), "cells_compared": cells,
            "mismatches": len(mismatches), "mismatch_examples": " | ".join(mismatches[:3])}


def run_all(dbname: str | None = None, verbose: bool = True) -> pd.DataFrame:
    root = find_project_root()
    out_dir = root / "reports" / "phase4" / "query_results"
    out_dir.mkdir(parents=True, exist_ok=True)
    conn = connect(dbname, root)
    rows = []
    try:
        for path in sorted((root / "sql" / "analytics").glob("*.sql")):
            name = path.stem
            entry = {"query": f"sql/analytics/{path.name}", "status": "ok", "result_rows": None, "seconds": None,
                     "phase3_file": "", "rows_compared": 0, "cells_compared": 0, "mismatches": 0,
                     "mismatch_examples": "", "reconciliation": "not applicable (checked in tests)"}
            try:
                result, secs = run_query(conn, path)
            except Exception as exc:                                  # report every query, then fail
                conn.rollback()
                entry.update(status="ERROR", mismatch_examples=str(exc).strip()[:300], reconciliation="not run")
                rows.append(entry)
                continue
            result.to_csv(out_dir / f"{name}.csv", index=False)
            entry.update(result_rows=len(result), seconds=round(secs, 3))
            if name in RECONCILE:
                entry.update(reconcile(name, result, root / "reports" / "eda"))
                entry["reconciliation"] = "MATCH" if entry["mismatches"] == 0 else "MISMATCH"
            rows.append(entry)
            if verbose:
                print(f"{entry['status']:5s} {path.name:45s} {entry['result_rows']:>4} rows  {entry['reconciliation']}")
    finally:
        conn.close()
    summary = pd.DataFrame(rows)
    summary.to_csv(root / "reports" / "phase4" / "sql_reconciliation.csv", index=False)
    return summary


def main() -> int:
    try:
        summary = run_all()
    except DatabaseConfigError as exc:
        print(f"ENVIRONMENT PROBLEM (not a pipeline failure):\n{exc}", file=sys.stderr)
        return 2
    bad = summary[(summary["status"] != "ok") | (summary["reconciliation"] == "MISMATCH")]
    print(f"\n{len(summary)} queries run, {int((summary['status'] == 'ok').sum())} succeeded, "
          f"{int((summary['reconciliation'] == 'MATCH').sum())} reconciled with Phase 3, {len(bad)} problem(s).")
    return 1 if len(bad) else 0


if __name__ == "__main__":
    sys.exit(main())
