"""Checks the files written by notebook 01. Run the notebook first, then:  python -m pytest -v tests"""
from pathlib import Path
import hashlib

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
AUDIT = ROOT / "reports" / "audit"
V1 = AUDIT / "history" / "run_2026-10-23_phase1_v1"      # archived first Phase 1 run


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def archived_hashes() -> dict:
    lines = (V1 / "SHA256SUMS.txt").read_text().split("\n")
    return {name: digest for digest, name in (line.split() for line in lines if line.strip())}


def test_raw_files_match_recorded_checksums():
    manifest = pd.read_csv(AUDIT / "raw_file_manifest.csv")
    for _, row in manifest.iterrows():
        assert sha256(RAW / row["file"]) == row["sha256"], row["file"]


def test_reviewed_pairs_file_unchanged_since_v1():
    assert sha256(INTERIM / "possible_duplicate_pairs.csv") == archived_hashes()["possible_duplicate_pairs.csv"]


def test_archived_v1_records_intact():
    for name, digest in archived_hashes().items():
        assert sha256(V1 / name) == digest, name


@pytest.fixture(scope="module")
def kept():
    return pd.read_csv(INTERIM / "possible_duplicate_pairs.csv")


@pytest.fixture(scope="module")
def excluded():
    return pd.read_csv(INTERIM / "excluded_candidate_pairs.csv")


def test_candidate_counts(kept, excluded):
    assert len(kept) == 18 and kept["tech_record_id"].nunique() == 11
    assert len(excluded) == 97
    keys_k = set(zip(kept["tech_record_id"], kept["global_record_id"]))
    keys_x = set(zip(excluded["tech_record_id"], excluded["global_record_id"]))
    assert len(keys_k | keys_x) == 115 and not (keys_k & keys_x)


def test_excluded_pairs_really_fail_the_rule(excluded):
    assert (excluded["date_gap_days"].abs() > 120).all()
    assert not (excluded["headcount_diff_pct"] <= 5).any()


def test_excluded_pairs_traceable_to_raw_lines(excluded):
    tech = pd.read_csv(RAW / "tech_layoffs_2025_2026.csv")
    glob = pd.read_csv(RAW / "layoffs_2019_2026_sample.csv")
    for _, r in excluded.iterrows():
        t = tech.iloc[r["tech_source_row_number"] - 2]          # CSV line 2 = first data row
        g = glob.iloc[r["global_source_row_number"] - 2]
        assert t["Company"] == r["tech_company"] and t["Date"] == r["tech_date"]
        assert g["company_name"] == r["global_company"] and g["date"] == r["global_date"]
        assert g["layoff_id"] == r["global_layoff_id"]


def test_review_status_and_no_invented_score(kept, excluded):
    assert (kept["review_status"] == "pending_review").all()
    assert (excluded["review_status"] == "excluded_by_rule_not_reviewed").all()
    assert (excluded["match_score"] == "not calculated").all()


def test_no_records_deleted_and_missing_headcount_stays_missing():
    raw = pd.read_csv(RAW / "layoffs_2019_2026_sample.csv")
    staged = pd.read_csv(INTERIM / "global_layoffs_staged.csv")
    assert len(staged) == len(raw) == 5000
    assert len(pd.read_csv(INTERIM / "tech_layoffs_staged.csv")) == 35
    assert staged["headcount_cut"].isna().sum() == raw["headcount_cut"].isna().sum() == 2511
    assert (staged["headcount_cut"] == 0).sum() == 0
