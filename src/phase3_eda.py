"""Aggregations for notebooks/03_exploratory_analysis.ipynb.

Documented filtering rules (used by every function here and checked by tests/test_phase3_eda.py):

R-SOURCE   Main analysis uses ONLY the global dataset (source_confidence == "high").
           The 35 tech rows are analysed separately and never added to global numbers.
R-EVENTS   An "event" is one row. All global rows are counted: furloughs, possible duplicates and
           rows with quality flags are KEPT (sensitivity tables show the effect of excluding them).
R-JOBS     "Verified jobs cut" sums employees_laid_off where it is present (only verified headcounts
           exist in the global data). Missing is never treated as 0: a group with no verified
           headcount gets NaN, not 0, and every jobs figure is shown next to its coverage %.
R-PCT      Workforce % statistics use only rows where workforce_pct is present.
R-UNKNOWN  Missing industry / country stay visible as "Unknown"; non-country values as "Unresolved".
R-PARTIAL  2026 covers January to June only (global); it is labelled partial, never compared as a full year.
R-SAMPLE   The global file is a 26% sample of the source's events: counts describe the sample, not the market.
"""
import numpy as np
import pandas as pd

GLOBAL = "fliar_global_sample"
TECH = "tech_layoffs_2025_2026"
PARTIAL_YEAR = 2026
SIZE_BANDS = [(1, 99, "1-99"), (100, 499, "100-499"), (500, 999, "500-999"),
              (1000, 4999, "1,000-4,999"), (5000, None, "5,000+")]


def load_events(path) -> pd.DataFrame:
    df = pd.read_csv(path, keep_default_na=False, na_values=[""], parse_dates=["event_date"])
    for col in ["employees_laid_off", "total_employees", "severance_weeks", "news_mentions", "event_year",
                "event_month", "event_quarter", "qc_issue_count", "source_row_number"]:
        df[col] = df[col].astype("Int64")
    df["workforce_pct"] = df["workforce_pct"].astype("Float64")
    for col in [c for c in df.columns if c.startswith("qc_") and c != "qc_issue_count"] + \
               ["is_furlough", "is_permanent_layoff", "ai_mentioned_in_news_derived", "possible_internal_duplicate"]:
        df[col] = df[col].map({"True": True, "False": False, True: True, False: False}).astype("boolean")
    return df


def global_rows(df):
    return df[df["source_dataset"] == GLOBAL]


def tech_rows(df):
    return df[df["source_dataset"] == TECH]


def _jobs(series: pd.Series) -> float:
    """R-JOBS: sum of present values; NaN (not 0) when none are present."""
    return series.sum(min_count=1) if series.notna().any() else np.nan


def summarise(g: pd.DataFrame, by) -> pd.DataFrame:
    """Events, verified-headcount coverage and verified jobs per group (R-EVENTS, R-JOBS)."""
    out = g.groupby(by, dropna=False).agg(
        events=("event_key", "count"),
        events_with_headcount=("employees_laid_off", "count"),          # count() ignores missing
        verified_jobs_cut=("employees_laid_off", _jobs),
        median_cut=("employees_laid_off", "median"),
    )
    out["headcount_coverage_pct"] = (100 * out["events_with_headcount"] / out["events"]).round(1)
    out["share_of_events_pct"] = (100 * out["events"] / out["events"].sum()).round(1)
    return out


def monthly_events(g: pd.DataFrame) -> pd.DataFrame:
    """Events per calendar month over the full range; a month with no events is a real 0 COUNT of rows."""
    months = pd.period_range(g["event_date"].min(), g["event_date"].max(), freq="M")
    counts = g["event_date"].dt.to_period("M").value_counts().reindex(months, fill_value=0)
    out = counts.rename("events").rename_axis("month").reset_index()
    out["events_3m_avg"] = out["events"].rolling(3, min_periods=1).mean().round(1)
    out["month"] = out["month"].astype(str)
    return out


def yearly_summary(g: pd.DataFrame) -> pd.DataFrame:
    out = summarise(g, "event_year").reset_index()
    out["permanent_events"] = g.groupby("event_year")["is_permanent_layoff"].sum().values
    out["furlough_events"] = g.groupby("event_year")["is_furlough"].sum().values
    out["partial_year"] = out["event_year"] == PARTIAL_YEAR
    return out


def industry_summary(g: pd.DataFrame) -> pd.DataFrame:
    out = summarise(g, "industry_group").reset_index().sort_values("events", ascending=False)
    out["rank_by_events"] = range(1, len(out) + 1)
    return out


def industry_year_share(g: pd.DataFrame) -> pd.DataFrame:
    """Share (%) of each year's events by industry group; columns are years."""
    t = pd.crosstab(g["industry_group"], g["event_year"])
    return (100 * t / t.sum()).round(1)


def region_summary(g: pd.DataFrame) -> pd.DataFrame:
    return summarise(g, "region").reset_index().sort_values("events", ascending=False)


def country_summary(g: pd.DataFrame) -> pd.DataFrame:
    c = g.assign(country=g["country"].fillna("Unknown"))
    out = summarise(c, ["country", "region"]).reset_index().sort_values("events", ascending=False)
    out["country_status"] = np.select([out["country"] == "Unknown", out["region"] == "Unresolved"],
                                      ["missing", "not a country (flagged)"], "ok")
    return out


def us_share_by_year(g: pd.DataFrame) -> pd.DataFrame:
    """Share of events with a KNOWN country that happened in the United States (missing excluded from the base)."""
    known = g[g["country"].notna()]
    out = known.groupby("event_year").agg(events_known_country=("event_key", "count"),
                                          us_events=("country", lambda s: (s == "United States").sum()))
    out["us_share_pct"] = (100 * out["us_events"] / out["events_known_country"]).round(1)
    out["events_missing_country"] = g.groupby("event_year")["country"].apply(lambda s: s.isna().sum())
    return out.reset_index()


def size_band_summary(g: pd.DataFrame) -> pd.DataFrame:
    """Size bands over verified headcounts only (R-JOBS); missing rows are counted separately, not as a band."""
    h = g["employees_laid_off"].dropna().astype(int)
    rows = []
    for lo, hi, label in SIZE_BANDS:
        mask = (h >= lo) & ((h <= hi) if hi is not None else True)
        rows.append({"size_band": label, "events": int(mask.sum())})
    out = pd.DataFrame(rows)
    out["share_of_verified_pct"] = (100 * out["events"] / out["events"].sum()).round(1)
    return out


def pct_summary(g: pd.DataFrame) -> pd.DataFrame:
    p = g["workforce_pct"].dropna().astype(float)
    bins = [0, 5, 10, 20, 30, 50, 100.0001]
    labels = ["0-5%", "5-10%", "10-20%", "20-30%", "30-50%", "50-100%"]
    out = pd.cut(p, bins=bins, labels=labels, right=False).value_counts().reindex(labels).rename("events")
    return out.rename_axis("workforce_pct_band").reset_index()


def missingness(df: pd.DataFrame, columns) -> pd.DataFrame:
    rows = []
    for ds, part in df.groupby("source_dataset"):
        for col in columns:
            rows.append({"source_dataset": ds, "column": col, "missing": int(part[col].isna().sum()),
                         "rows": len(part), "missing_pct": round(100 * part[col].isna().mean(), 1)})
    return pd.DataFrame(rows)


def qc_flag_summary(df: pd.DataFrame) -> pd.DataFrame:
    flags = [c for c in df.columns if c.startswith("qc_") and c != "qc_issue_count"]
    rows = []
    for ds, part in df.groupby("source_dataset"):
        for f in flags:
            rows.append({"source_dataset": ds, "flag": f, "true": int(part[f].sum()),
                         "not_computed": int(part[f].isna().sum())})
    return pd.DataFrame(rows)


def sensitivity_by_year(g: pd.DataFrame) -> pd.DataFrame:
    """Events per year under alternative exclusions (rows are never deleted from the dataset itself)."""
    return pd.DataFrame({
        "all_events": g.groupby("event_year").size(),
        "excl_furloughs": g[~g["is_furlough"].fillna(False)].groupby("event_year").size(),
        "excl_internal_duplicates": g[~g["possible_internal_duplicate"].fillna(False)].groupby("event_year").size(),
        "excl_cross_source_duplicate_candidates": g[g["possible_duplicate_group"].isna()].groupby("event_year").size(),
    }).fillna(0).astype(int).reset_index()


# ---------------------------------------------------------------- tech-only (lower confidence)
def tech_reason_summary(t: pd.DataFrame) -> pd.DataFrame:
    return t.groupby("reason_category_derived").agg(events=("event_key", "count"),
                                                    reported_laid_off=("employees_laid_off", _jobs)) \
            .sort_values("events", ascending=False).reset_index()


def tech_department_summary(bridge: pd.DataFrame) -> pd.DataFrame:
    """Events touching each department (COUNT DISTINCT event_key) and the weighted event share (sums to 35)."""
    out = bridge.groupby("department").agg(events_involving=("event_key", "nunique"),
                                           weighted_events=("allocation_weight", "sum"))
    return out.sort_values("events_involving", ascending=False).reset_index()


def tech_ai_summary(t: pd.DataFrame) -> pd.DataFrame:
    out = t.groupby("ai_related").agg(events=("event_key", "count"),
                                      reported_laid_off=("employees_laid_off", _jobs),
                                      median_pct_workforce=("workforce_pct", "median"),
                                      median_severance_weeks=("severance_weeks", "median"),
                                      suspect_dates=("qc_suspect_date", "sum"))
    return out.reindex(["Yes", "Partial", "No"]).reset_index()


def tech_severance_summary(t: pd.DataFrame) -> pd.DataFrame:
    return t["severance_weeks"].value_counts().sort_index().rename("events").rename_axis("severance_weeks").reset_index()
