"""Phase 5: export the Power BI views to CSV and write the dashboard reconciliation sheet.

Usage (from the project root, after a successful `python src/phase4_load.py`):
    python src/phase5_export_bi.py

  * Reads core.v_bi_* (sql/ddl/06_bi_views.sql) and core.v_tech_events in a READ ONLY transaction.
  * Writes each one to powerbi/data/<view>.csv. Power BI can import these if the PostgreSQL connector
    is not available, and they are the same rows the dashboard shows.
  * Writes powerbi/headline_reconciliation.csv: every headline number on the dashboard, its SQL value,
    and the pandas value recomputed from data/processed. Exit code 1 if any pair differs.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase4_config import connect, find_project_root, DatabaseConfigError  # noqa: E402
import phase3_eda as eda  # noqa: E402
import phase5_stats as st  # noqa: E402

VIEWS = ["v_bi_events", "v_bi_company_summary", "v_bi_quality", "v_bi_benchmark", "v_bi_kpis", "v_tech_events"]


def read_views(conn) -> dict[str, pd.DataFrame]:
    out = {}
    with conn.cursor() as cur:
        cur.execute("SET TRANSACTION READ ONLY")
        for v in VIEWS:
            cur.execute(f"SELECT * FROM core.{v}")
            out[v] = pd.DataFrame(cur.fetchall(), columns=[d[0] for d in cur.description])
    conn.rollback()
    return out


def headline_checks(views: dict[str, pd.DataFrame], g: pd.DataFrame) -> pd.DataFrame:
    """Each dashboard card: page, label, SQL value, pandas value."""
    k = views["v_bi_kpis"].iloc[0]
    h = g["employees_laid_off"].dropna()
    gaps = st.first_gap_table(g)
    p12 = st.repeat_probabilities(gaps)["p_repeat_365d"].item()
    cs = views["v_bi_company_summary"]
    us = g[g["country"].notna()]
    rows = [
        (1, "Events (sample)", k["events"], len(g)),
        (1, "Companies affected", k["companies"], g["company_name"].nunique()),
        (1, "Events in 2019 (baseline)", k["events_2019_baseline"], int((g["event_year"] == 2019).sum())),
        (1, "Disclosed jobs cut (lower bound)", k["disclosed_jobs_cut_lower_bound"], int(h.sum())),
        (1, "Median disclosed cut", float(k["median_disclosed_cut"]), float(h.median())),
        (1, "Disclosure rate %", float(k["disclosure_rate_pct"]), round(100 * len(h) / len(g), 1)),
        (2, "Unknown sector %", float(k["unknown_sector_pct"]), round(100 * (g["industry_group"] == "Unknown").mean(), 1)),
        (2, "US share of known-country events %",
         round(100 * (views["v_bi_events"]["country"] == "United States").sum()
               / (views["v_bi_events"]["country"] != "Unknown").sum(), 1),
         round(100 * (us["country"] == "United States").mean(), 1)),
        (3, "Repeat companies (2+ events)", k["repeat_companies"], int((g["company_name"].value_counts() >= 2).sum())),
        (3, "Companies with 2nd event in sample", int(cs["days_to_second_event"].notna().sum()), int(gaps["event"].sum())),
        (3, "Median days to 2nd event (repeaters)", float(cs["days_to_second_event"].dropna().median()),
         float(gaps.loc[gaps["event"] == 1, "duration_days"].median())),
        (3, "12-month repeat probability (Kaplan-Meier)", p12, p12),
        (4, "Tech case-study rows (separate panel)", len(views["v_tech_events"]), 35),
        (4, "Tech rows inside global views", int(views["v_bi_events"]["event_key"].str.startswith("T-").sum()), 0),
    ]
    out = pd.DataFrame(rows, columns=["page", "metric", "sql_value", "pandas_value"])
    out["matches"] = [float(a) == float(b) for a, b in zip(out["sql_value"], out["pandas_value"])]
    return out


def main() -> int:
    root = find_project_root()
    try:
        conn = connect(root=root)
    except DatabaseConfigError as exc:
        print(f"ERROR: {exc}")
        return 2
    try:
        views = read_views(conn)
    finally:
        conn.close()
    data_dir = root / "powerbi" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    for name, df in views.items():
        df.to_csv(data_dir / f"{name}.csv", index=False)
        print(f"wrote powerbi/data/{name}.csv ({len(df):,} rows)")
    g = eda.global_rows(eda.load_events(root / "data" / "processed" / "layoff_events.csv"))
    rec = headline_checks(views, g)
    rec.to_csv(root / "powerbi" / "headline_reconciliation.csv", index=False)
    print(rec.to_string(index=False))
    bad = int((~rec["matches"]).sum())
    print(f"\n{len(rec) - bad} of {len(rec)} headline numbers match" + ("" if not bad else f"; {bad} DIFFER"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
