"""Unit tests for the PROPOSED Phase 2 mapping rules (A-02, A-04). They test the rules only; no data is changed."""
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from phase2_mappings import (rule_clean_company, clean_company, industry_group,  # noqa: E402
                             GLOBAL_SECTOR_MAP, TECH_INDUSTRY_MAP, INDUSTRY_GROUPS)


def test_suffix_removed_only_at_end():
    assert rule_clean_company("Apple Inc") == "Apple"
    assert rule_clean_company("Eaton Corp. PLC") == "Eaton"
    assert rule_clean_company("Coca-Cola Co") == "Coca-Cola"
    assert rule_clean_company("Incorp Systems") == "Incorp Systems"       # 'Inc' inside a word is kept


def test_brand_words_kept():
    assert rule_clean_company("The Walt Disney Company") == "The Walt Disney Company"
    assert rule_clean_company("Royal Bank of Scotland Group") == "Royal Bank of Scotland Group"


def test_missing_stays_missing_and_never_empty():
    assert rule_clean_company(np.nan) is np.nan
    assert rule_clean_company("Ltd") == "Ltd"                              # would be empty -> keep original


def test_description_names_kept_raw_and_flagged():
    name, method, status, _ = clean_company("Cargo services firm in Charlotte")
    assert name == "Cargo services firm in Charlotte" and method == "kept_raw_pending_review" and status == "needs_review"


def test_p2_uncertain_subsidiaries_keep_exact_raw_name():
    for raw in ["Spanish subsidiary of Deutsche Bank", "Walt Disney Company‑Owned Marvel Studios",
                "Think & Learn Private Limited", "Tata Steel in the Netherlands"]:
        name, method, status, _ = clean_company(raw)
        assert (name, method, status) == (raw, "kept_raw_pending_review", "needs_review")


def test_p1_industry_groups():
    assert len(INDUSTRY_GROUPS) == 17 and INDUSTRY_GROUPS[-1] == "Unknown"      # 16 real groups + Unknown
    assert industry_group("High Tech", "global") == "Technology (mixed)"
    assert industry_group("Semiconductors", "global") == "Hardware & Semiconductors"
    assert industry_group("Hardware", "tech") == "Hardware & Semiconductors"
    assert industry_group("Semiconductors/AI", "tech") == "Hardware & Semiconductors"


def test_alias_x_twitter():
    assert clean_company("X (Twitter)")[0] == clean_company("X - formerly called Twitter")[0] == "Twitter"


def test_every_raw_label_is_mapped_to_a_known_group():
    glob = pd.read_csv(ROOT / "data" / "raw" / "layoffs_2019_2026_sample.csv")
    tech = pd.read_csv(ROOT / "data" / "raw" / "tech_layoffs_2025_2026.csv")
    assert set(glob["sector"].dropna()) <= set(GLOBAL_SECTOR_MAP)
    assert set(tech["Industry"]) <= set(TECH_INDUSTRY_MAP)
    groups = {industry_group(x, "global") for x in glob["sector"]} | {industry_group(x, "tech") for x in tech["Industry"]}
    assert groups <= set(INDUSTRY_GROUPS)


def test_missing_sector_is_unknown_not_dropped():
    assert industry_group(np.nan, "global") == "Unknown"
