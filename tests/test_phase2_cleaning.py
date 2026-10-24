"""Unit tests for the Phase 2 cleaning rules (src/phase2_cleaning.py) on small synthetic inputs."""
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import phase2_cleaning as pc  # noqa: E402


def test_country_only_approved_relabels():
    s = pd.Series(["USA", "United States (usa)", "United Kingdom (uk)", "United States (cnmi)", " France ", None, "Arizona"])
    out = pc.standardise_country(s)
    assert out.tolist()[:5] == ["United States", "United States", "United Kingdom", "Northern Mariana Islands", "France"]
    assert pd.isna(out[5])                       # missing stays missing
    assert out[6] == "Arizona"                   # non-country kept as-is (no approved rule)


def test_region_lookup():
    s = pd.Series(["Germany", None, "Arizona", "Atlantis"], dtype="string")
    assert pc.region_of(s).tolist() == ["Europe", "Unknown", "Unresolved", "Other"]


def test_split_location():
    out = pc.split_location(pd.Series(["Armonk, NY", "Dublin, Ireland", "Paris", None]))
    assert out["city"].tolist()[:3] == ["Armonk", "Dublin", "Paris"] and pd.isna(out["city"][3])
    assert out["state"][0] == "NY" and out["state"][1:].isna().all()


def test_derive_reason():
    assert pc.derive_reason("AI replacing content creators") == "AI / Automation"
    assert pc.derive_reason("he said it was about costs") == "Cost Cutting"       # 'said' is not 'AI'
    assert pc.derive_reason("COVID-19 lockdown") == "Pandemic"
    assert pc.derive_reason(None) == "Not stated"
    assert pc.derive_reason("no keyword here") == "Not stated"


def test_ai_mentioned_missing_stays_missing():
    out = pc.ai_mentioned(pd.Series(["uses AI tools", "said nothing", None, "Artificial Intelligence push"]))
    assert out[0] and not out[1] and pd.isna(out[2]) and out[3]


def pairs_fixture():
    return pd.DataFrame({
        "pair_id": ["P-1", "P-2", "P-3", "P-4"],
        "tech_record_id": ["T-1", "T-1", "T-2", "T-3"], "global_record_id": ["G-1", "G-2", "G-3", "G-4"],
        "tech_headcount": [500, 500, 100, 300], "global_headcount": [500, 900, np.nan, 310],
        "headcount_diff_pct": [0.0, 80.0, np.nan, 3.3], "date_gap_days": [-400, 30, -10, 60],
        "global_date": ["2023-01-01", "2025-02-01", "2025-01-01", "2025-03-01"],
    })


def test_suspect_dates_rule():
    out = pc.suspect_tech_dates(pairs_fixture())
    assert out["event_key"].tolist() == ["T-1"]       # same size AND >120 days; T-3 is same size but only 60 days


def test_duplicate_groups_link_without_merging():
    groups = pc.duplicate_groups(pairs_fixture())
    assert groups["T-1"] == groups["G-1"] == groups["G-2"]
    assert groups["T-2"] == groups["G-3"] != groups["T-1"]
    assert groups.nunique() == 3 and len(groups) == 7


def test_departments_bridge_no_double_count():
    events = pd.DataFrame({"event_key": ["T-1", "T-2", "G-1"], "source_dataset": ["t", "t", "g"],
                           "source_row_number": [2, 3, 2], "department": ["Sales, Marketing", "Engineering", None]})
    b = pc.departments_bridge(events)
    assert len(b) == 3 and set(b["event_key"]) == {"T-1", "T-2"}
    assert np.allclose(b.groupby("event_key")["allocation_weight"].sum(), 1.0)
    assert "employees_laid_off" not in b.columns


def test_changed_mask_treats_two_missing_as_same():
    m = pc.changed_mask(pd.Series([None, "a", "a", None]), pd.Series([None, "a", "b", "x"]))
    assert m.tolist() == [False, False, True, True]
