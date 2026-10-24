"""Phase 4: database integrity and reconciliation checks.

Every check compares what is in PostgreSQL with a value computed INDEPENDENTLY from the processed CSV
files (read as plain text with pandas), so a loading bug cannot hide itself. The checks describe the data
as it really is: they expect the actual numbers of missing headcounts, unknown sectors and unresolved
countries - they never require complete data.

run_checks() is called by phase4_load.py inside the load transaction (a failure rolls the load back) and
the results are stored in audit.validation_results. Checks are grouped by category:
  counts, keys, bridge, nulls, qc_flags, sources, duplicates, dates, reconciliation, distributions, mappings
"""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pandas as pd
from psycopg2 import sql

import phase4_spec as spec

GLOBAL, TECH = "fliar_global_sample", "tech_layoffs_2025_2026"


def canon(v) -> str:
    """One text form for comparing Python/CSV values with PostgreSQL values."""
    if v is None or (isinstance(v, float) and pd.isna(v)) or v is pd.NA:
        return "NULL"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float, Decimal)):
        d = Decimal(str(v))
        if d == d.to_integral_value():
            return str(d.quantize(Decimal(1)))
        return format(d.normalize(), "f")
    return str(v)


def dist(pairs) -> str:
    """Canonical text for a distribution [(key..., count)], sorted by key."""
    return "; ".join(f"{'|'.join(canon(k) for k in p[:-1])}={canon(p[-1])}"
                     for p in sorted(pairs, key=lambda p: tuple(canon(k) for k in p[:-1])))


def compute_baseline(input_dir: Path) -> dict[str, pd.DataFrame]:
    """Read every processed CSV as text. Empty field -> NA; nothing else is converted."""
    return {spec.FILES[f][0]: pd.read_csv(input_dir / f, dtype=str, keep_default_na=False, na_values=[""])
            for f in spec.FILES}


def _q(cur, query, params=None):
    cur.execute(query, params)
    return cur.fetchall()


def run_checks(cur, base: dict[str, pd.DataFrame], staging_counts: dict, reports) -> list[dict]:
    results: list[dict] = []

    def add(check_id, category, description, expected, actual):
        results.append({"check_id": check_id, "category": category, "description": description,
                        "expected": canon(expected) if not isinstance(expected, str) else expected,
                        "actual": canon(actual) if not isinstance(actual, str) else actual,
                        "passed": (canon(expected) if not isinstance(expected, str) else expected) ==
                                  (canon(actual) if not isinstance(actual, str) else actual)})

    ev = base["layoff_events"]
    by_src = {s: ev[ev["source_dataset"] == s] for s in (GLOBAL, TECH)}

    # ---- 1. counts: CSV = staging = core
    for r in reports:
        table = r.core_table
        add(f"count.staging.{table}", "counts", f"{r.file_name}: staging rows = CSV rows",
            r.csv_rows, staging_counts.get(r.file_name))
        n = _q(cur, sql.SQL("SELECT count(*) FROM core.{}").format(sql.Identifier(table)))[0][0]
        add(f"count.core.{table}", "counts", f"core.{table}: rows = CSV rows", r.csv_rows, n)
    add("count.core.source_datasets", "counts", "core.source_datasets has the 2 documented sources",
        dist([(s, 1) for s in ev["source_dataset"].unique()]),
        dist(_q(cur, "SELECT source_dataset, count(*) FROM core.source_datasets GROUP BY 1")))

    # ---- 2-3. keys
    n, n_distinct, n_null = _q(cur, "SELECT count(*), count(DISTINCT event_key), count(*) - count(event_key) "
                                    "FROM core.layoff_events")[0]
    add("keys.event_key", "keys", "event_key is unique and never NULL", f"{len(ev)}/{len(ev)}/0",
        f"{n}/{n_distinct}/{n_null}")
    add("keys.source_row", "keys", "(source_dataset, source_row_number) is unique", len(ev),
        _q(cur, "SELECT count(DISTINCT (source_dataset, source_row_number)) FROM core.layoff_events")[0][0])
    add("keys.source_event_id", "keys", "source_event_id: unique, present for every global row, NULL for tech",
        f"{by_src[GLOBAL]['source_event_id'].nunique()}/{by_src[TECH]['source_event_id'].isna().sum()}",
        "{}/{}".format(*_q(cur, "SELECT count(DISTINCT source_event_id) FILTER (WHERE source_dataset = %s), "
                                "count(*) FILTER (WHERE source_dataset = %s AND source_event_id IS NULL) "
                                "FROM core.layoff_events", (GLOBAL, TECH))[0]))
    for child, col in [("layoff_event_departments", "event_key"), ("quality_issues", "event_key"),
                       ("possible_duplicate_pairs", "tech_record_id"), ("possible_duplicate_pairs", "global_record_id"),
                       ("excluded_candidate_pairs", "tech_record_id"), ("excluded_candidate_pairs", "global_record_id"),
                       ("cross_source_industry_disagreements", "event_key_tech")]:
        orphans = _q(cur, sql.SQL("SELECT count(*) FROM core.{t} c LEFT JOIN core.layoff_events e "
                                  "ON e.event_key = c.{c} WHERE e.event_key IS NULL").format(
            t=sql.Identifier(child), c=sql.Identifier(col)))[0][0]
        add(f"keys.fk.{child}.{col}", "keys", f"every {child}.{col} exists in layoff_events", 0, orphans)
    wrong_side = _q(cur, """
        SELECT count(*) FROM (
          SELECT p.tech_record_id t, p.global_record_id g FROM core.possible_duplicate_pairs p
          UNION ALL SELECT x.tech_record_id, x.global_record_id FROM core.excluded_candidate_pairs x) q
        JOIN core.layoff_events et ON et.event_key = q.t JOIN core.layoff_events eg ON eg.event_key = q.g
        WHERE et.source_dataset <> %s OR eg.source_dataset <> %s""", (TECH, GLOBAL))[0][0]
    add("keys.pairs_point_to_right_sources", "keys", "pair files link a tech record to a global record", 0, wrong_side)

    # ---- 4-5. bridge
    dep = base["layoff_event_departments"]
    add("bridge.only_tech_events", "bridge", "department rows belong to tech events only", 0,
        _q(cur, "SELECT count(*) FROM core.layoff_event_departments d JOIN core.layoff_events e USING (event_key) "
                "WHERE e.source_dataset <> %s", (TECH,))[0][0])
    add("bridge.event_coverage", "bridge", "events with a department = tech events with a department text",
        int(by_src[TECH]["department"].notna().sum()),
        _q(cur, "SELECT count(DISTINCT event_key) FROM core.layoff_event_departments")[0][0])
    add("bridge.weights_sum_to_1", "bridge", "allocation weights add up to exactly 1 for every event", 0,
        _q(cur, "SELECT count(*) FROM (SELECT event_key FROM core.layoff_event_departments GROUP BY event_key "
                "HAVING sum(allocation_weight) <> 1) x")[0][0])
    add("bridge.weight_total", "bridge", "total allocation weight = number of events in the bridge",
        dep["event_key"].nunique(), _q(cur, "SELECT sum(allocation_weight) FROM core.layoff_event_departments")[0][0])
    add("bridge.departments_in_event", "bridge", "departments_in_event = rows per event", 0,
        _q(cur, "SELECT count(*) FROM (SELECT event_key FROM core.layoff_event_departments GROUP BY event_key "
                "HAVING count(*) <> max(departments_in_event)) x")[0][0])

    # ---- 6. nulls: every nullable event column, per source, equals the CSV
    for name, typ, required in spec.EVENTS:
        if required:
            continue
        expected = dist([(s, int(by_src[s][name].isna().sum())) for s in (GLOBAL, TECH)])
        actual = dist(_q(cur, sql.SQL("SELECT source_dataset, count(*) - count({c}) FROM core.layoff_events "
                                      "GROUP BY 1").format(c=sql.Identifier(name))))
        add(f"nulls.{name}", "nulls", f"NULL count of {name} per source = empty CSV fields", expected, actual)
    for col in ["employees_laid_off", "workforce_pct", "total_employees", "severance_weeks", "news_mentions"]:
        zeros_csv = int((pd.to_numeric(ev[col], errors="coerce") == 0).sum())
        add(f"nulls.no_new_zeros.{col}", "nulls", f"{col}: no zero created from a missing value", zeros_csv,
            _q(cur, sql.SQL("SELECT count(*) FROM core.layoff_events WHERE {c} = 0").format(c=sql.Identifier(col)))[0][0])
    for table in ["possible_duplicate_pairs", "excluded_candidate_pairs"]:
        for col in ["global_headcount", "headcount_diff_pct", "global_pct", "reviewer_notes"]:
            add(f"nulls.{table}.{col}", "nulls", f"{table}.{col}: NULL count = empty CSV fields",
                int(base[table][col].isna().sum()),
                _q(cur, sql.SQL("SELECT count(*) - count({c}) FROM core.{t}").format(
                    c=sql.Identifier(col), t=sql.Identifier(table)))[0][0])

    # ---- 7. quality flags (TRUE / FALSE / NULL = not computed) and the quality_issues table
    for flag in spec.QC_FLAGS:
        expected = dist([(s, v, int((by_src[s][flag].fillna("NULL") == v).sum()))
                         for s in (GLOBAL, TECH) for v in ("True", "False", "NULL")
                         if (by_src[s][flag].fillna("NULL") == v).any()])
        actual = dist([(s, {True: "True", False: "False", None: "NULL"}[v], n) for s, v, n in _q(cur, sql.SQL(
            "SELECT source_dataset, {c}, count(*) FROM core.layoff_events GROUP BY 1, 2").format(c=sql.Identifier(flag)))])
        add(f"qc.{flag}", "qc_flags", f"{flag}: TRUE/FALSE/NULL counts per source = CSV", expected, actual)
    add("qc.issue_count", "qc_flags", "qc_issue_count total = CSV", sum(int(x) for x in ev["qc_issue_count"]),
        _q(cur, "SELECT sum(qc_issue_count) FROM core.layoff_events")[0][0])
    true_flags = " UNION ALL ".join(
        f"SELECT event_key, '{f}' AS quality_flag FROM core.layoff_events WHERE {f}" for f in spec.QC_FLAGS)
    mismatch = _q(cur, f"""WITH t AS ({true_flags}), q AS (SELECT event_key, quality_flag FROM core.quality_issues)
        SELECT (SELECT count(*) FROM (SELECT * FROM q EXCEPT SELECT * FROM t) a)
             + (SELECT count(*) FROM (SELECT * FROM t EXCEPT SELECT * FROM q) b)""")[0][0]
    add("qc.quality_issues_match_flags", "qc_flags", "quality_issues has exactly one row per TRUE flag", 0, mismatch)
    qi = base["quality_issues"]
    add("qc.quality_issues_by_flag", "qc_flags", "quality_issues rows per flag = CSV",
        dist(qi.groupby("quality_flag").size().items()),
        dist(_q(cur, "SELECT quality_flag, count(*) FROM core.quality_issues GROUP BY 1")))

    # ---- source labels
    add("sources.labels", "sources", "source_dataset / confidence / file combinations = CSV",
        dist(ev.groupby(["source_dataset", "source_confidence", "source_file"]).size().reset_index().values.tolist()),
        dist(_q(cur, "SELECT source_dataset, source_confidence, source_file, count(*) FROM core.layoff_events "
                     "GROUP BY 1, 2, 3")))
    add("sources.global_total", "sources", "global rows (never mixed with tech) = 5,000 in CSV",
        len(by_src[GLOBAL]), _q(cur, "SELECT count(*) FROM core.v_global_events")[0][0])
    add("sources.tech_total", "sources", "tech rows = 35 in CSV", len(by_src[TECH]),
        _q(cur, "SELECT count(*) FROM core.v_tech_events")[0][0])

    # ---- 8. duplicates and suspect dates are preserved
    add("dup.group_members", "duplicates", "events per possible_duplicate_group = CSV (nothing merged)",
        dist(ev.dropna(subset=["possible_duplicate_group"]).groupby("possible_duplicate_group").size().items()),
        dist(_q(cur, "SELECT possible_duplicate_group, count(*) FROM core.layoff_events "
                     "WHERE possible_duplicate_group IS NOT NULL GROUP BY 1")))
    add("dup.internal", "duplicates", "possible_internal_duplicate TRUE rows = CSV",
        int((ev["possible_internal_duplicate"] == "True").sum()),
        _q(cur, "SELECT count(*) FROM core.layoff_events WHERE possible_internal_duplicate")[0][0])
    for table in ["possible_duplicate_pairs", "excluded_candidate_pairs"]:
        add(f"dup.{table}.status", "duplicates", f"{table}: review_status values = CSV (none resolved)",
            dist(base[table].groupby("review_status").size().items()),
            dist(_q(cur, sql.SQL("SELECT review_status, count(*) FROM core.{} GROUP BY 1").format(sql.Identifier(table)))))
    suspects = ev[ev["qc_suspect_date"] == "True"]
    add("dates.suspect_preserved", "dates", "the 6 suspect-date events keep their original date",
        dist([(k, d, 1) for k, d in zip(suspects["event_key"], suspects["event_date_raw"])]),
        dist([(k, d.isoformat(), 1) for k, d in _q(cur, "SELECT event_key, event_date FROM core.layoff_events "
                                                         "WHERE qc_suspect_date")]))
    add("dates.unchanged", "dates", "event_date equals event_date_raw for every row", 0,
        _q(cur, "SELECT count(*) FROM core.layoff_events WHERE event_date::text <> event_date_raw")[0][0])
    add("dates.range", "dates", "first and last event date per source = CSV",
        dist([(s, by_src[s]["event_date"].min(), by_src[s]["event_date"].max(), 1) for s in (GLOBAL, TECH)]),
        dist([(s, a.isoformat(), b.isoformat(), 1) for s, a, b in
              _q(cur, "SELECT source_dataset, min(event_date), max(event_date) FROM core.layoff_events GROUP BY 1")]))

    # ---- 9. numeric reconciliation (exact: CSV text summed as Decimal)
    for col in ["employees_laid_off", "workforce_pct", "total_employees", "severance_weeks", "news_mentions"]:
        expected = dist([(s, int(by_src[s][col].notna().sum()),
                          sum((Decimal(x) for x in by_src[s][col].dropna()), Decimal(0))) for s in (GLOBAL, TECH)])
        actual = dist(_q(cur, sql.SQL("SELECT source_dataset, count({c}), coalesce(sum({c}), 0) "
                                      "FROM core.layoff_events GROUP BY 1").format(c=sql.Identifier(col))))
        add(f"recon.{col}", "reconciliation", f"{col}: known-value count and exact sum per source = CSV",
            expected, actual)
    g = by_src[GLOBAL]
    yearly = [(y, int(grp["employees_laid_off"].notna().sum()),
               sum((Decimal(x) for x in grp["employees_laid_off"].dropna()), Decimal(0)))
              for y, grp in g.groupby("event_year")]
    add("recon.yearly_headcount", "reconciliation", "global known headcount per year (count, sum) = CSV",
        dist(yearly), dist(_q(cur, "SELECT event_year, count(employees_laid_off), coalesce(sum(employees_laid_off), 0) "
                                    "FROM core.v_global_events GROUP BY 1")))
    for table, col in [("possible_duplicate_pairs", "tech_headcount"), ("excluded_candidate_pairs", "global_headcount")]:
        add(f"recon.{table}.{col}", "reconciliation", f"{table}.{col} sum = CSV",
            sum((Decimal(x) for x in base[table][col].dropna()), Decimal(0)),
            _q(cur, sql.SQL("SELECT coalesce(sum({c}), 0) FROM core.{t}").format(
                c=sql.Identifier(col), t=sql.Identifier(table)))[0][0])

    # ---- 10. distributions (NULL / Unknown / Unresolved kept as their own groups)
    for col in ["industry_group", "country", "region", "reason_category_derived", "ai_related",
                "headcount_status", "date_reliability", "company_name_review_status", "industry_raw"]:
        expected = dist([(s, k if pd.notna(k) else None, n) for (s, k), n in
                         ev.groupby(["source_dataset", col], dropna=False).size().items()])
        actual = dist(_q(cur, sql.SQL("SELECT source_dataset, {c}, count(*) FROM core.layoff_events "
                                      "GROUP BY 1, 2").format(c=sql.Identifier(col))))
        add(f"dist.{col}", "distributions", f"{col} distribution per source = CSV (incl. NULL)", expected, actual)
    add("dist.departments", "distributions", "events per department = CSV",
        dist(dep.groupby("department")["event_key"].nunique().items()),
        dist(_q(cur, "SELECT department, count(DISTINCT event_key) FROM core.layoff_event_departments GROUP BY 1")))

    # ---- 11. mappings, lineage and logs
    add("map.company_rows", "mappings", "company_name_mapping.rows = events per raw name (all names)", 0,
        _q(cur, """SELECT count(*) FROM core.company_name_mapping m LEFT JOIN (
                     SELECT source_dataset, company_name_raw, count(*) n FROM core.layoff_events GROUP BY 1, 2) e
                   USING (source_dataset, company_name_raw) WHERE e.n IS DISTINCT FROM m.rows""")[0][0])
    add("map.company_name_consistent", "mappings", "each event's company_name = its mapping row", 0,
        _q(cur, "SELECT count(*) FROM core.layoff_events e JOIN core.company_name_mapping m "
                "USING (source_dataset, company_name_raw) WHERE e.company_name <> m.company_name "
                "OR e.company_name_method <> m.company_name_method "
                "OR e.company_name_review_status <> m.company_name_review_status")[0][0])
    add("map.industry_rows", "mappings", "industry_mapping.rows = events per raw label ('(missing)' = NULL)", 0,
        _q(cur, """SELECT count(*) FROM core.industry_mapping m LEFT JOIN (
                     SELECT source_dataset, coalesce(industry_raw, '(missing)') industry_raw, count(*) n
                     FROM core.layoff_events GROUP BY 1, 2) e
                   USING (source_dataset, industry_raw) WHERE e.n IS DISTINCT FROM m.rows""")[0][0])
    add("map.industry_group_consistent", "mappings", "each event's industry_group = its mapping row", 0,
        _q(cur, "SELECT count(*) FROM core.layoff_events e JOIN core.industry_mapping m "
                "ON m.source_dataset = e.source_dataset AND m.industry_raw = coalesce(e.industry_raw, '(missing)') "
                "WHERE e.industry_group <> m.industry_group")[0][0])
    add("map.disagreement_keys", "mappings", "every global key listed in a disagreement exists, is global, "
        "and the count matches global_rows", 0,
        _q(cur, """SELECT count(*) FROM core.cross_source_industry_disagreements d WHERE d.global_rows <> (
                     SELECT count(*) FROM core.v_industry_disagreement_global_events v
                     JOIN core.v_global_events g ON g.event_key = v.global_event_key
                     WHERE v.event_key_tech = d.event_key_tech)""")[0][0])
    lin = base["field_lineage"]
    add("map.lineage", "mappings", "field_lineage rows per source = CSV",
        dist(lin.groupby("source_dataset").size().items()),
        dist(_q(cur, "SELECT source_dataset, count(*) FROM core.field_lineage GROUP BY 1")))
    tl = base["transformation_log"]
    add("map.transformation_log", "mappings", "transformation_log rows_changed per rule = CSV",
        dist(zip(tl["rule_id"], tl["rows_changed"])),
        dist(_q(cur, "SELECT rule_id, rows_changed FROM core.transformation_log")))
    return results
