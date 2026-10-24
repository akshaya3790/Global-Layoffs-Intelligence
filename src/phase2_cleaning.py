"""Phase 2 cleaning rules for notebooks/02_data_cleaning.ipynb.

Every rule here was approved in reports/PHASE2_APPROVAL_CHECKLIST.md (A-01 to A-16) and
reports/PHASE2_FINAL_SCHEMA_AND_MAPPINGS.md (P1-P5). Each function returns NEW values and
never changes its input. Missing values stay missing unless a rule says otherwise.
"""
import re

import numpy as np
import pandas as pd

from phase1_validation import parse_dates

GLOBAL_NAME = "fliar_global_sample"
TECH_NAME = "tech_layoffs_2025_2026"

# ---------------------------------------------------------------- final schema
CANONICAL_COLUMNS = [
    "event_key", "source_dataset", "source_confidence", "source_file", "source_row_number", "source_event_id",
    "company_name_raw", "company_name", "company_name_method", "company_name_review_status", "company_domain",
    "event_date_raw", "event_date", "event_year", "event_quarter", "event_month", "date_reliability", "date_flag_reason",
    "industry_raw", "industry_group",
    "country_raw", "country", "country_basis", "hq_country_raw", "hq_country", "region",
    "location_raw", "city", "state",
    "employees_laid_off", "headcount_status", "workforce_pct", "total_employees",
    "reason", "reason_category_derived", "reason_method", "department", "severance_weeks",
    "ai_related", "ai_mentioned_in_news_derived", "is_furlough", "is_permanent_layoff",
    "news_source", "news_url_raw", "news_url", "news_excerpt", "news_mentions", "source_profile_url",
    "possible_duplicate_group", "possible_internal_duplicate", "qc_issue_count",
]

# Phase 1 flags carried over unchanged (NA where a flag was not computed for that source)
PHASE1_QC_COLUMNS = [
    "qc_date_unparseable", "qc_date_outside_expected_range", "qc_date_after_audit_date", "qc_non_numeric_value",
    "qc_headcount_not_positive", "qc_pct_out_of_range", "qc_headcount_status_conflict", "qc_headcount_not_verified",
    "qc_missing_sector", "qc_missing_country", "qc_noisy_company_name", "qc_same_company_same_url",
    "qc_possible_cross_source_dup", "qc_headcount_math_gap_gt10pct",
]
PHASE2_QC_COLUMNS = [
    "qc_suspect_date", "qc_company_name_needs_review", "qc_country_not_a_country",
    "qc_industry_cross_source_conflict",
]
QC_COLUMNS = PHASE1_QC_COLUMNS + PHASE2_QC_COLUMNS

# ---------------------------------------------------------------- A-03 / A-05 countries
COUNTRY_STANDARD = {           # A-03: only these four relabels were approved
    "USA": "United States",
    "United States (usa)": "United States",
    "United Kingdom (uk)": "United Kingdom",
    "United States (cnmi)": "Northern Mariana Islands",
}
# Values found in country columns that are states, provinces or fragments, not countries.
# Not relabelled (no approved rule): kept as-is and flagged qc_country_not_a_country.
NOT_A_COUNTRY = {"Arizona", "Nevada", "New York", "Rhode Island", "Quebec", "Au", "Sa"}

REGIONS = {
    "North America": ["United States", "Canada", "Mexico", "Puerto Rico", "Bermuda", "Northern Mariana Islands"],
    "Latin America & Caribbean": ["Argentina", "Brazil", "Chile", "Colombia", "Costa Rica", "El Salvador", "Honduras",
                                  "Panama", "Peru", "Uruguay", "Barbados", "Haiti", "Jamaica", "British Virgin Islands"],
    "Europe": ["Austria", "Belgium", "Bulgaria", "Croatia", "Czech Republic", "Denmark", "Estonia", "Finland", "France",
               "Germany", "Gibraltar", "Greece", "Guernsey", "Hungary", "Iceland", "Ireland", "Isle of Man", "Italy",
               "Jersey", "Latvia", "Lithuania", "Luxembourg", "Malta", "Monaco", "Netherlands", "Norway", "Poland",
               "Portugal", "Romania", "Russia", "Slovakia", "Slovenia", "Spain", "Sweden", "Switzerland", "Turkey",
               "Ukraine", "United Kingdom"],
    "Middle East & Africa": ["Algeria", "Cameroon", "Congo", "Egypt", "Ghana", "Israel", "Jordan", "Kenya", "Kuwait",
                             "Lesotho", "Liberia", "Malawi", "Mozambique", "Namibia", "Nigeria", "Oman", "Qatar",
                             "Rwanda", "Saudi Arabia", "Senegal", "Seychelles", "South Africa", "Togo", "Tunisia",
                             "Uganda", "United Arab Emirates"],
    "Asia Pacific": ["Australia", "Bangladesh", "Cambodia", "China", "Fiji", "Hong Kong", "India", "Indonesia", "Japan",
                     "Macau", "Malaysia", "Myanmar", "New Caledonia", "New Zealand", "Pakistan", "Papua New Guinea",
                     "Philippines", "Singapore", "South Korea", "Taiwan", "Tajikistan", "Thailand", "Vietnam"],
}
COUNTRY_TO_REGION = {c: r for r, cs in REGIONS.items() for c in cs}


def standardise_country(values: pd.Series) -> pd.Series:
    """A-03: apply the four approved relabels and trim spaces. Missing stays missing."""
    out = values.astype("string").str.strip()
    return out.replace(COUNTRY_STANDARD)


def region_of(country: pd.Series) -> pd.Series:
    """Region lookup. Missing -> 'Unknown'; non-country values -> 'Unresolved'; anything else unmapped -> 'Other'."""
    region = country.map(COUNTRY_TO_REGION).astype("string")
    region = region.mask(country.isin(NOT_A_COUNTRY), "Unresolved")
    region = region.mask(country.isna(), "Unknown")
    return region.fillna("Other")


# ---------------------------------------------------------------- A-06 location
US_STATE_CODES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME",
    "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA",
    "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
}


def split_location(values: pd.Series) -> pd.DataFrame:
    """A-06: city = text before the first comma; state = the part after it only if it is a US state code."""
    parts = values.astype("string").str.split(",", n=1, expand=True)
    city = parts[0].str.strip()
    after = parts[1].str.strip() if parts.shape[1] > 1 else pd.Series(pd.NA, index=values.index, dtype="string")
    state = after.where(after.isin(US_STATE_CODES))
    return pd.DataFrame({"city": city, "state": state.astype("string")})


# ---------------------------------------------------------------- A-10 reason, A-12 AI flag
AI_PATTERN_CASE_SENSITIVE = r"\bAI\b"                      # upper-case 'AI' only, so 'said' never matches
AI_PATTERN_ANY_CASE = r"artificial intelligence|automat"
REASON_RULES = [   # checked in this order after the AI rule; first match wins
    ("Pandemic", r"covid|coronavirus|pandemic|lockdown"),
    ("Closure / Bankruptcy", r"bankrupt|insolven|shut(?:ting)? down|closure|clos(?:e|ing) (?:its|the|a) |liquidat"),
    ("Merger / Acquisition", r"merger|acquisition|acquired|takeover|integration"),
    ("Offshoring / Relocation", r"offshor|relocat|outsourc|moving (?:jobs|production)"),
    ("Restructuring", r"restructur|reorgani|realign|streamlin|reset"),
    ("Cost Cutting", r"cost|sav(?:e|ing)s?\b|efficien|budget|profitab"),
    ("Demand / Market", r"demand|sales|market|tariff|downturn|slowdown|recession|inflation|revenue|headwind|decline"),
]


def derive_reason(text) -> str:
    """A-10: keyword category for one text. Missing or no keyword -> 'Not stated'."""
    if not isinstance(text, str):
        return "Not stated"
    if re.search(AI_PATTERN_CASE_SENSITIVE, text) or re.search(AI_PATTERN_ANY_CASE, text, re.IGNORECASE):
        return "AI / Automation"
    for label, pattern in REASON_RULES:
        if re.search(pattern, text, re.IGNORECASE):
            return label
    return "Not stated"


def ai_mentioned(values: pd.Series) -> pd.Series:
    """A-12: True when the text mentions 'AI' (upper-case word) or 'artificial intelligence'. Missing text -> NA."""
    text = values.astype("string")
    hit = text.str.contains(r"\bAI\b", regex=True) | text.str.contains("artificial intelligence", case=False)
    return hit.astype("boolean")


# ---------------------------------------------------------------- A-07 suspect dates, A-13 duplicate groups
def suspect_tech_dates(pairs: pd.DataFrame, max_size_diff_pct: float = 5, min_gap_days: int = 120) -> pd.DataFrame:
    """A-07: tech rows whose headcount is within 5% of a global event more than 120 days away.
    Returns one row per tech record with a written reason. Dates are NOT changed."""
    hit = pairs[(pairs["headcount_diff_pct"] <= max_size_diff_pct) & (pairs["date_gap_days"].abs() > min_gap_days)]
    reasons = hit.apply(lambda r: (f"headcount {int(r['tech_headcount'])} within {r['headcount_diff_pct']}% of global "
                                   f"{r['global_record_id']} ({int(r['global_headcount'])}) dated {r['global_date']}, "
                                   f"{abs(int(r['date_gap_days']))} days earlier/later ({r['pair_id']})"), axis=1)
    out = pd.DataFrame({"event_key": hit["tech_record_id"], "date_flag_reason": reasons})
    return out.groupby("event_key", as_index=False)["date_flag_reason"].agg("; ".join)


def duplicate_groups(pairs: pd.DataFrame) -> pd.Series:
    """A-13: link records that appear together in a kept candidate pair (connected components).
    Returns event_key -> group id (DG-001...). Nothing is merged."""
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in zip(pairs["tech_record_id"], pairs["global_record_id"]):
        parent[find(a)] = find(b)
    members = pd.Series({k: find(k) for k in list(parent)})
    roots = sorted(members.unique(), key=lambda r: sorted(members[members == r].index)[0])
    ids = {root: f"DG-{i:03d}" for i, root in enumerate(roots, start=1)}
    return members.map(ids).sort_index()


# ---------------------------------------------------------------- A-11 departments bridge
def departments_bridge(events: pd.DataFrame) -> pd.DataFrame:
    """A-11: one row per (event, department). No headcount column, so it cannot be summed by mistake;
    allocation_weight = 1 / departments_in_event lets an event count once in total."""
    has = events[events["department"].notna()]
    rows = []
    for _, e in has.iterrows():
        parts = [p.strip() for p in str(e["department"]).split(",") if p.strip()]
        for pos, dept in enumerate(parts, start=1):
            rows.append({"event_key": e["event_key"], "source_dataset": e["source_dataset"],
                         "source_row_number": e["source_row_number"], "department_raw": e["department"],
                         "department": dept, "department_position": pos, "departments_in_event": len(parts),
                         "allocation_weight": 1 / len(parts)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- change log helper
def changed_mask(before: pd.Series, after: pd.Series) -> pd.Series:
    """True where a value changed (two missing values count as unchanged)."""
    b, a = before.astype("string"), after.astype("string")
    both_missing = b.isna() & a.isna()
    return ~both_missing & (b.isna() | a.isna() | (b != a)).fillna(True)


def log_change(log: list, rule_id: str, decision: str, column: str, before: pd.Series, after: pd.Series,
               description: str, keys: pd.Series) -> int:
    """Append one transformation-log row (rows changed + up to 3 examples) and return the count."""
    mask = changed_mask(before, after)
    examples = [f"{k}: {b!r} -> {a!r}" for k, b, a in
                zip(keys[mask].head(3), before[mask].head(3), after[mask].head(3))]
    log.append({"rule_id": rule_id, "decision": decision, "column": column, "description": description,
                "rows_changed": int(mask.sum()), "examples": " | ".join(examples)})
    return int(mask.sum())
