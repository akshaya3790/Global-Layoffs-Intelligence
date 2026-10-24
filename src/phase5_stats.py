"""Statistics for notebooks/05_sample_validity_and_repeat_layoffs.ipynb.

Three questions, each answered only as far as the 26% company sample allows:

S-BENCH   Does the sample reproduce the full population? Sample aggregates are divided by the
          full-population tables published in data/raw/SOURCE_DATA_CARD.md (typed in below, cited).
S-BOOT    How uncertain are yearly figures? The sample keeps EVERY event of a fixed subset of companies
          (a cluster sample), so the bootstrap resamples whole companies, never single rows.
S-SURV    How soon does a company lay off again? Kaplan-Meier on the gap from a company's FIRST event in
          the sample to its second, right-censored at the last date in the data (2026-06-14).

Rules shared with phase3_eda.py: global rows only (R-SOURCE), missing headcounts stay missing and job
sums are "disclosed, lower bound" (R-JOBS), 2026 is partial (R-PARTIAL).
"""
import numpy as np
import pandas as pd
from scipy import stats

CITATION = ("Fliar Research (2026). Layoffs Dataset 2019-2026: Global, India, US, UK (sample release). "
            "Data: Radar API, https://github.com/fliarbi/radar-api-mcp. Licence CC BY-NC 4.0. "
            "Full-population figures from data/raw/SOURCE_DATA_CARD.md.")
NOMINAL_FRACTION = 5000 / 19208          # 26.0%: "5,000 of 19,208 layoff events" (data card)
STUDY_END = pd.Timestamp("2026-06-14")   # last event date in the global sample
CLUSTER_KEY = "company_name"             # the sample unit is the company

# Data card, table "Layoffs by year" (full data). 2026 is January to June only.
FULL_BY_YEAR = pd.DataFrame({
    "event_year": [2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026],
    "full_events": [1759, 3780, 1032, 2008, 3391, 3011, 2977, 1250],
    "full_disclosed_jobs": [764478, 3122163, 448334, 846889, 1822899, 1440648, 1734556, 749078],
})
# Data card, table "Layoffs by country worldwide" (top 5). Compared with the RAW country column.
FULL_BY_COUNTRY = {"United States": 7501, "United Kingdom": 2198, "India": 971, "Germany": 834, "Canada": 768}
# Data card, table "Layoffs by sector" (top 3). Compared with the RAW industry column.
FULL_BY_SECTOR = {"Retail": 1008, "Food and Agriculture": 795, "Consumer Goods": 773}
# Data card, key finding 5: companies with more than one layoff round.
FULL_REPEAT_COMPANIES = 2768


# ---------------------------------------------------------------- S-BENCH
def benchmark_by_year(g: pd.DataFrame) -> pd.DataFrame:
    s = g.groupby("event_year").agg(sample_events=("event_key", "count"),
                                    sample_disclosed_jobs=("employees_laid_off", lambda x: x.sum(min_count=1)))
    out = FULL_BY_YEAR.merge(s.reset_index(), on="event_year", how="left")
    out["events_ratio"] = (out["sample_events"] / out["full_events"]).round(3)
    out["jobs_ratio"] = (out["sample_disclosed_jobs"].astype(float) / out["full_disclosed_jobs"]).round(3)
    out["events_dev_pp"] = (100 * (out["events_ratio"] - NOMINAL_FRACTION)).round(1)
    out["jobs_dev_pp"] = (100 * (out["jobs_ratio"] - NOMINAL_FRACTION)).round(1)
    out["partial_year"] = out["event_year"] == 2026
    return out


def benchmark_categories(g: pd.DataFrame) -> pd.DataFrame:
    """Raw country / sector values and repeat companies against the full-data card."""
    rows = []
    for name, full in FULL_BY_COUNTRY.items():
        rows.append(("country", name, int((g["country_raw"] == name).sum()), full))
    for name, full in FULL_BY_SECTOR.items():
        rows.append(("sector", name, int((g["industry_raw"] == name).sum()), full))
    repeaters = int((g["company_name_raw"].value_counts() >= 2).sum())
    rows.append(("companies", "Companies with 2+ rounds (raw name)", repeaters, FULL_REPEAT_COMPANIES))
    out = pd.DataFrame(rows, columns=["dimension", "value", "sample", "full"])
    out["ratio"] = (out["sample"] / out["full"]).round(3)
    out["dev_pp"] = (100 * (out["ratio"] - NOMINAL_FRACTION)).round(1)
    return out


# ---------------------------------------------------------------- S-BOOT
def _yearly_stats(g: pd.DataFrame) -> pd.DataFrame:
    return g.groupby("event_year").agg(events=("event_key", "count"),
                                       disclosed_jobs=("employees_laid_off", lambda x: x.sum(min_count=1)),
                                       median_cut=("employees_laid_off", "median"))


def cluster_bootstrap_yearly(g: pd.DataFrame, n_boot: int = 1000, seed: int = 20261023,
                             level: float = 0.90) -> pd.DataFrame:
    """Percentile intervals for yearly events, disclosed jobs and median cut, resampling companies.

    Each replicate draws as many companies as the sample has, with replacement, and keeps all of each
    drawn company's events. Returns one row per year with the point estimate and the interval.
    """
    rng = np.random.default_rng(seed)
    g = g[["event_key", "event_year", "employees_laid_off", CLUSTER_KEY]].copy()
    g["employees_laid_off"] = g["employees_laid_off"].astype(float)
    codes, companies = pd.factorize(g[CLUSTER_KEY])
    order = np.argsort(codes, kind="stable")
    starts = np.searchsorted(codes[order], np.arange(len(companies)))
    ends = np.append(starts[1:], len(order))
    years = sorted(g["event_year"].unique())
    reps = {k: np.full((n_boot, len(years)), np.nan) for k in ("events", "disclosed_jobs", "median_cut")}
    yr = g["event_year"].to_numpy()
    jobs = g["employees_laid_off"].to_numpy()
    for b in range(n_boot):
        pick = rng.integers(0, len(companies), len(companies))
        idx = np.concatenate([order[starts[c]:ends[c]] for c in pick])
        for j, y in enumerate(years):
            m = idx[yr[idx] == y]
            reps["events"][b, j] = len(m)
            h = jobs[m][~np.isnan(jobs[m])]
            reps["disclosed_jobs"][b, j] = h.sum() if len(h) else np.nan
            reps["median_cut"][b, j] = np.median(h) if len(h) else np.nan
    lo_q, hi_q = (1 - level) / 2, 1 - (1 - level) / 2
    point = _yearly_stats(g).reindex(years)
    out = pd.DataFrame({"event_year": years})
    for k in reps:
        out[k] = point[k].to_numpy()
        out[f"{k}_lo"] = np.nanquantile(reps[k], lo_q, axis=0)
        out[f"{k}_hi"] = np.nanquantile(reps[k], hi_q, axis=0)
    out["partial_year"] = out["event_year"] == 2026
    out.attrs.update(n_boot=n_boot, seed=seed, level=level, clusters=len(companies))
    return out


def overlapping_years(boot: pd.DataFrame, metric: str = "disclosed_jobs") -> pd.DataFrame:
    """Pairs of full years whose intervals overlap: their order cannot be read from the sample."""
    full = boot[~boot["partial_year"]]
    rows = []
    for _, a in full.iterrows():
        for _, b in full.iterrows():
            if a["event_year"] < b["event_year"]:
                overlap = not (a[f"{metric}_hi"] < b[f"{metric}_lo"] or b[f"{metric}_hi"] < a[f"{metric}_lo"])
                rows.append({"year_a": int(a["event_year"]), "year_b": int(b["event_year"]), "intervals_overlap": overlap})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- S-SURV
def first_gap_table(g: pd.DataFrame, end: pd.Timestamp = STUDY_END) -> pd.DataFrame:
    """One row per company: days from its first sampled event to the next one (event=1), or to `end` (event=0).

    Covariates come from the first event: industry_group, region, era and size band of the first cut.
    """
    g = g.sort_values(["event_date", "event_key"])
    first = g.groupby(CLUSTER_KEY).nth(0).set_index(CLUSTER_KEY)
    second = g.groupby(CLUSTER_KEY).nth(1).set_index(CLUSTER_KEY)["event_date"]
    out = first[["event_date", "industry_group", "region", "employees_laid_off"]].rename(columns={"event_date": "first_date"})
    out["next_date"] = second.reindex(out.index)
    out["event"] = out["next_date"].notna().astype(int)
    out["duration_days"] = ((out["next_date"].fillna(end)) - out["first_date"]).dt.days
    out["era"] = np.where(out["first_date"] < pd.Timestamp("2022-01-01"), "2019-2021 (incl. COVID)", "2022 onwards")
    h = out["employees_laid_off"].astype(float)
    out["first_cut_size"] = np.select([h.isna().to_numpy(), (h < 500).to_numpy()],
                                      ["Undisclosed", "Under 500"], "500 or more")
    return out.reset_index()


def kaplan_meier(duration, event) -> pd.DataFrame:
    """Kaplan-Meier survival S(t) with Greenwood standard errors and log-log 95% intervals."""
    d = np.asarray(duration, float)
    e = np.asarray(event, int)
    times = np.unique(d[e == 1])
    surv, var_sum, rows = 1.0, 0.0, [{"t": 0.0, "at_risk": len(d), "events": 0, "survival": 1.0, "lo": 1.0, "hi": 1.0}]
    for t in times:
        n = int((d >= t).sum())
        k = int(((d == t) & (e == 1)).sum())
        surv *= 1 - k / n
        var_sum += k / (n * (n - k)) if n > k else np.inf
        if 0 < surv < 1 and np.isfinite(var_sum):
            se = np.sqrt(var_sum) / abs(np.log(surv))
            lo, hi = surv ** np.exp(1.96 * se), surv ** np.exp(-1.96 * se)
        else:
            lo = hi = surv
        rows.append({"t": t, "at_risk": n, "events": k, "survival": surv, "lo": lo, "hi": hi})
    return pd.DataFrame(rows)


def km_at(km: pd.DataFrame, t: float) -> pd.Series:
    """Survival curve value (step function) at time t."""
    return km[km["t"] <= t].iloc[-1]


def repeat_probabilities(gaps: pd.DataFrame, by=None, horizons=(182, 365, 730), min_n: int = 30) -> pd.DataFrame:
    """P(next layoff within h days) = 1 - S(h), with 95% intervals, overall or per group."""
    groups = [("All companies", gaps)] if by is None else list(gaps.groupby(by))
    rows = []
    for name, part in groups:
        if len(part) < min_n:
            continue
        km = kaplan_meier(part["duration_days"], part["event"])
        row = {"group": name, "companies": len(part), "repeats_observed": int(part["event"].sum())}
        for h in horizons:
            s = km_at(km, h)
            row[f"p_repeat_{h}d"] = round(1 - s["survival"], 3)
            row[f"p_repeat_{h}d_lo"] = round(1 - s["hi"], 3)
            row[f"p_repeat_{h}d_hi"] = round(1 - s["lo"], 3)
        rows.append(row)
    return pd.DataFrame(rows)


def logrank_test(duration, event, group) -> dict:
    """Multi-group log-rank test (chi-square with k-1 degrees of freedom)."""
    d = np.asarray(duration, float)
    e = np.asarray(event, int)
    grp = np.asarray(group)
    labels = np.unique(grp)
    k = len(labels)
    O, E = np.zeros(k), np.zeros(k)
    V = np.zeros((k, k))
    for t in np.unique(d[e == 1]):
        at_risk = d >= t
        n = at_risk.sum()
        dt = ((d == t) & (e == 1)).sum()
        n_g = np.array([(at_risk & (grp == lab)).sum() for lab in labels])
        d_g = np.array([((d == t) & (e == 1) & (grp == lab)).sum() for lab in labels])
        O += d_g
        E += dt * n_g / n
        if n > 1:
            f = dt * (n - dt) / (n * n * (n - 1))
            V += f * (np.diag(n_g * n) - np.outer(n_g, n_g))
    diff = (O - E)[:-1]
    chi2 = float(diff @ np.linalg.pinv(V[:-1, :-1]) @ diff)
    return {"groups": k, "chi2": round(chi2, 2), "df": k - 1, "p_value": float(stats.chi2.sf(chi2, k - 1)),
            "observed": dict(zip(labels, O.astype(int))), "expected": dict(zip(labels, E.round(1)))}
