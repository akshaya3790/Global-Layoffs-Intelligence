"""Validation rules used by notebooks/01_data_intake_and_quality_audit.ipynb.

The rules live here (instead of inside notebook cells) so the exact same code
can be run by the notebook on the real data and by tests/ on synthetic data.

Every function only *flags*: it returns True/False per row and never changes,
fills or drops the values it is given.
"""
import pandas as pd


def parse_dates(values: pd.Series) -> pd.Series:
    """Read yyyy-mm-dd text as dates. Anything unreadable (e.g. 2025-02-30) becomes NaT."""
    return pd.to_datetime(values, format="%Y-%m-%d", errors="coerce")


def to_number(values: pd.Series) -> pd.Series:
    """Read values as numbers. Text such as 'twelve' becomes NaN; missing stays missing (never 0)."""
    return pd.to_numeric(values, errors="coerce")


def flag_unparseable_date(values: pd.Series) -> pd.Series:
    """True when a date is missing or cannot be read as a real calendar date."""
    return parse_dates(values).isna()


def flag_date_outside_range(values: pd.Series, start: str, end: str) -> pd.Series:
    """True when a readable date falls before `start` or after `end`."""
    d = parse_dates(values)
    return (d < pd.Timestamp(start)) | (d > pd.Timestamp(end))


def flag_date_after(values: pd.Series, cutoff: str) -> pd.Series:
    """True when a readable date is later than `cutoff` (a date in the future)."""
    return parse_dates(values) > pd.Timestamp(cutoff)


def flag_non_numeric(values: pd.Series) -> pd.Series:
    """True when a cell is filled but is not a number (missing cells are NOT flagged)."""
    return values.notna() & to_number(values).isna()


def flag_not_positive(values: pd.Series) -> pd.Series:
    """True for numbers <= 0 (a layoff count must be at least 1). Missing/text -> False."""
    return to_number(values) <= 0


def flag_pct_out_of_range(values: pd.Series) -> pd.Series:
    """True for percentages <= 0 or > 100. Missing/text -> False."""
    n = to_number(values)
    return (n <= 0) | (n > 100)


def flag_headcount_status_conflict(headcount: pd.Series, status: pd.Series) -> pd.Series:
    """True when status says 'verified' but there is no number, or a number exists without 'verified'."""
    has_number = to_number(headcount).notna()
    verified = status == "verified"
    return (verified & ~has_number) | (~verified & has_number)


def validation_flags(df: pd.DataFrame, date_col: str, headcount_col: str, pct_col: str,
                     expected_start: str, expected_end: str, audit_date: str,
                     status_col=None, other_numeric_cols: tuple = ()) -> pd.DataFrame:
    """Run every date and number rule on one table and return one qc_ column per rule."""
    numeric_cols = [headcount_col, pct_col, *other_numeric_cols]
    flags = pd.DataFrame(index=df.index)
    flags["qc_date_unparseable"] = flag_unparseable_date(df[date_col])
    flags["qc_date_outside_expected_range"] = flag_date_outside_range(df[date_col], expected_start, expected_end)
    flags["qc_date_after_audit_date"] = flag_date_after(df[date_col], audit_date)
    flags["qc_non_numeric_value"] = pd.concat([flag_non_numeric(df[c]) for c in numeric_cols], axis=1).any(axis=1)
    flags["qc_headcount_not_positive"] = flag_not_positive(df[headcount_col])
    flags["qc_pct_out_of_range"] = flag_pct_out_of_range(df[pct_col])
    if status_col is not None:
        flags["qc_headcount_status_conflict"] = flag_headcount_status_conflict(df[headcount_col], df[status_col])
    return flags


# ---------------------------------------------------------------------------
# Rules R1-R4. Moved here from notebook 01 cells (2026-10-23) so they can be tested.
# Each keeps the notebook's original comparison. The only change: values pass through
# to_number() first, so a text value no longer crashes the rule (it is caught by
# flag_non_numeric instead). On numeric columns the result is identical.
# Missing values: a comparison with a missing value is False in pandas, so a missing
# input is NOT flagged by these rules. That is the behaviour the notebook always had;
# missing values are reported separately in the missing-value analysis.
# ---------------------------------------------------------------------------

def flag_news_mentions_below_one(values: pd.Series) -> pd.Series:
    """R1. True when news_mentions < 1. Original: global_df["news_mentions"] < 1"""
    return to_number(values) < 1


def flag_laid_off_exceeds_total(laid_off: pd.Series, total_employees: pd.Series) -> pd.Series:
    """R2. True when more people were laid off than the company employs.
    Original: tech_df["Employees_Laid_Off"] > tech_df["Total_Employees"]"""
    return to_number(laid_off) > to_number(total_employees)


def flag_negative_severance(values: pd.Series) -> pd.Series:
    """R3. True when severance weeks < 0 (0 weeks is allowed). Original: tech_df["Severance_Weeks"] < 0"""
    return to_number(values) < 0


def headcount_math_gap_pct(laid_off: pd.Series, pct: pd.Series, total_employees: pd.Series) -> pd.Series:
    """R4 helper. % difference between the reported count and pct x total / 100, rounded to 1 decimal.
    Original: implied = pct * total / 100; gap = (100 * (laid - implied) / implied).round(1)
    Missing input -> missing gap. pct or total of 0 -> implied 0 -> gap is +/-inf (or NaN for 0/0)."""
    implied = to_number(pct) * to_number(total_employees) / 100
    return (100 * (to_number(laid_off) - implied) / implied).round(1)


def flag_headcount_math_gap(laid_off: pd.Series, pct: pd.Series, total_employees: pd.Series,
                            threshold: float = 10) -> pd.Series:
    """R4. True when |gap| > threshold %. Original: tech_df[gap.abs() > 10]"""
    return headcount_math_gap_pct(laid_off, pct, total_employees).abs() > threshold
