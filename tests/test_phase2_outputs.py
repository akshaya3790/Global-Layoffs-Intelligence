"""Checks the files written by notebook 02 (run notebooks 01 and 02 first)."""
from pathlib import Path
import hashlib
import sys

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import phase2_cleaning as pc  # noqa: E402

RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
INTERIM = ROOT / "data" / "interim"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def events():
    return pd.read_csv(PROCESSED / "layoff_events.csv", keep_default_na=False, na_values=[""])


@pytest.fixture(scope="module")
def raw():
    return (pd.read_csv(RAW / "layoffs_2019_2026_sample.csv", keep_default_na=False, na_values=[""]),
            pd.read_csv(RAW / "tech_layoffs_2025_2026.csv", keep_default_na=False, na_values=[""]))


def test_schema(events):
    assert list(events.columns) == pc.CANONICAL_COLUMNS + pc.QC_COLUMNS
    assert len(pc.CANONICAL_COLUMNS) == 51 and len(pc.QC_COLUMNS) == 18


def test_row_counts_and_keys(events):
    assert events["source_dataset"].value_counts().to_dict() == {pc.GLOBAL_NAME: 5000, pc.TECH_NAME: 35}
    assert events["event_key"].is_unique and events["event_key"].notna().all()
    assert not events.duplicated(["source_dataset", "source_row_number"]).any()


def test_lineage_every_row_back_to_raw_line(events, raw):
    glob, tech = raw
    g = events[events["source_dataset"] == pc.GLOBAL_NAME]
    t = events[events["source_dataset"] == pc.TECH_NAME]
    assert g["company_name_raw"].tolist() == glob.iloc[g["source_row_number"] - 2]["company_name"].tolist()
    assert g["source_event_id"].tolist() == glob.iloc[g["source_row_number"] - 2]["layoff_id"].tolist()
    assert g["event_date_raw"].tolist() == glob.iloc[g["source_row_number"] - 2]["date"].tolist()
    assert t["company_name_raw"].tolist() == tech.iloc[t["source_row_number"] - 2]["Company"].tolist()
    assert t["event_date_raw"].tolist() == tech.iloc[t["source_row_number"] - 2]["Date"].tolist()


def test_missing_values_preserved(events, raw):
    glob, tech = raw
    g = events[events["source_dataset"] == pc.GLOBAL_NAME]
    assert g["employees_laid_off"].isna().sum() == glob["headcount_cut"].isna().sum() == 2511
    assert (events["employees_laid_off"] == 0).sum() == 0
    assert events["workforce_pct"].isna().sum() == glob["pct_workforce"].isna().sum() == 3879
    assert g["country"].isna().sum() == glob["country"].isna().sum() == 470


def test_tech_kept_separate_and_suspect_dates_unchanged(events):
    t = events[events["source_dataset"] == pc.TECH_NAME]
    assert (t["source_confidence"] == "low").all()
    s = t[t["date_reliability"] == "suspect_date"]
    assert set(s["company_name"]) == {"Twitch", "Dell", "Roku", "Accenture", "Unity", "Adobe"}
    assert (s["event_date"] == s["event_date_raw"]).all()


def test_uncertain_company_names_kept_raw(events):
    r = events[events["company_name_review_status"] == "needs_review"]
    assert len(r) == 13 and (r["company_name"] == r["company_name_raw"]).all()


def test_review_files_identical_to_phase1():
    for name in ["possible_duplicate_pairs.csv", "excluded_candidate_pairs.csv"]:
        assert sha256(PROCESSED / name) == sha256(INTERIM / name)


def test_departments_bridge(events):
    b = pd.read_csv(PROCESSED / "layoff_event_departments.csv")
    assert b["event_key"].isin(events["event_key"]).all() and b["event_key"].nunique() == 35
    assert not b.duplicated(["event_key", "department"]).any()
    assert (b.groupby("event_key")["allocation_weight"].sum().round(9) == 1).all()
    assert "employees_laid_off" not in b.columns


def test_quality_issues_match_flags(events):
    q = pd.read_csv(PROCESSED / "quality_issues.csv")
    assert len(q) == events["qc_issue_count"].sum()
    assert q["event_key"].isin(events["event_key"]).all()


def test_outputs_match_recorded_fingerprints():
    m = pd.read_csv(PROCESSED / "phase2_output_manifest.csv")
    for _, r in m.iterrows():
        assert sha256(PROCESSED / r["file"]) == r["sha256"], r["file"]
