"""Company-name and industry mapping rules for Phase 2 (decisions A-02 and A-04).

This file only DEFINES the rules. It does not change any data.
`make_mapping_proposals.py` uses it to write reviewable proposal files, and notebook 02
will use the same functions once the proposals are approved.
"""
import re

import pandas as pd

# ---------------------------------------------------------------- A-02 company names

# Legal-form words removed only when they are the LAST word(s) of a name.
# "Company", "Group" and "Holdings" are deliberately NOT removed: they are often part of the brand
# (e.g. "The Walt Disney Company", "Royal Bank of Scotland Group").
LEGAL_SUFFIXES = [
    "Inc", "Inc.", "Incorporated", "Corp", "Corp.", "Corporation", "Co", "Co.", "Ltd", "Ltd.", "Limited",
    "Private Limited", "Pvt Ltd", "Pvt. Ltd.", "Pty Ltd", "LLC", "L.L.C.", "plc", "PLC", "GmbH", "AG", "KG",
    "SA", "S.A.", "S.A.S", "SpA", "S.p.A.", "NV", "N.V.", "BV", "B.V.", "AB", "ASA", "Oyj", "SE",
]
_SUFFIX_RE = re.compile(r"(?:,?\s+(?:" + "|".join(re.escape(s) for s in sorted(LEGAL_SUFFIXES, key=len, reverse=True))
                        + r"))+\s*$")

# Hand-written mappings for names that rules cannot fix (sentence-like names, tickers, aliases).
# review_status: "proposed" = confident; "needs_review" = a judgement call for the reviewer.
MANUAL_COMPANY_MAP = {
    "Electric-car maker Tesla Inc. TSLA": ("Tesla", "proposed", "description + ticker removed"),
    "U.S. Silica Holdings Inc. SLCA": ("U.S. Silica", "proposed", "ticker removed"),
    "World Wrestling Entertainment Inc. WWE": ("World Wrestling Entertainment", "proposed", "ticker removed"),
    "X - formerly called Twitter": ("Twitter", "proposed", "alias of Twitter / X"),
    "X (Twitter)": ("Twitter", "proposed", "tech-file alias of Twitter; global file uses 'Twitter'"),
    "GOODYEAR Tire & Rubber Co": ("Goodyear Tire & Rubber", "proposed", "spelling variant"),
    "Goodyear Tire & Rubber Co": ("Goodyear Tire & Rubber", "proposed", "spelling variant"),
    "The Goodyear Tire & Rubber Company": ("Goodyear Tire & Rubber", "proposed", "spelling variant"),
    "The Monte dei Paschi di Siena": ("Monte dei Paschi di Siena", "proposed", "leading 'The' variant"),
    "Dah Chong Hong (DCH) Food Mart": ("Dah Chong Hong Food Mart", "proposed", "abbreviation in brackets removed"),
    "Artificial Intelligence (AI) Startup xAI": ("xAI", "proposed", "description removed"),
    "Scandinavias main airline SAS AB": ("SAS", "proposed", "description removed"),
    "The Smart Air Lines Gol": ("Gol", "proposed", "description removed"),
    "Swedish Game Developer Toadman Interactive": ("Toadman Interactive", "proposed", "description removed"),
    "The Quebec software developer helps LeddarTech drive again": ("LeddarTech", "proposed", "headline text removed"),
    "Revolution owners The Revel Collective": ("The Revel Collective", "proposed", "description removed"),
    "DAA (formerly the Dublin Airport Authority)": ("DAA", "proposed", "former-name note removed"),
    "Rapid (formerly known as Rapid AP)": ("Rapid", "proposed", "former-name note removed"),
    "China’s Longi Green Technology Energy Co": ("Longi Green Energy Technology", "proposed", "description removed"),
    "Tata Steel in the Netherlands": (None, "needs_review", "Dutch subsidiary vs parent Tata Steel; P2: raw name kept"),
    "Smart & Final distribution centers": ("Smart & Final", "proposed", "description removed"),
    "São Paulo Banco do Brasil": ("Banco do Brasil", "proposed", "location text removed"),
    "Whole Foods Market Southern Region — Bake House": (None, "needs_review", "business unit vs company; P2: raw name kept"),
    "Byju": ("BYJU'S", "proposed", "spelling variant"),
    "Byjus’s": ("BYJU'S", "proposed", "spelling variant"),
    "Sodexo at The University of Pittsburgh": (None, "needs_review", "site-level unit; parent used; P2: raw name kept until reviewed"),
    "Spanish subsidiary of Deutsche Bank": (None, "needs_review", "subsidiary mapped to parent; P2: raw name kept until reviewed"),
    "Mondalez International’s Cadbury chocolate factory": (None, "needs_review", "brand vs parent Mondelez; P2: raw name kept until reviewed"),
    "Walt Disney Company‑Owned Marvel Studios": (None, "needs_review", "subsidiary vs parent Disney; P2: raw name kept until reviewed"),
    "Mahindra & Mahindra's Pininfarina Engineering": (None, "needs_review", "subsidiary vs parent Mahindra; P2: raw name kept until reviewed"),
    "Tata Vendor’s Amulite Auto Components Company": (None, "needs_review", "description removed; P2: raw name kept until reviewed"),
    "Think & Learn Private Limited": (None, "needs_review", "legal entity behind BYJU'S; P2: raw name kept until reviewed"),
    "Sony Interactive Entertainment Japan Studio": (None, "needs_review", "studio vs parent; P2: raw name kept until reviewed"),
    # Not a company name at all: kept unchanged and flagged so they never group with real companies
    "Cargo services firm in Charlotte": (None, "needs_review", "description, not a name: keep raw, flag"),
    "São José dos Campos metalmakers": (None, "needs_review", "description, not a name: keep raw, flag"),
    "First Of The Three Large Cognac Houses": (None, "needs_review", "description, not a name: keep raw, flag"),
}


def rule_clean_company(name: str) -> str:
    """Trim, collapse spaces, straighten curly apostrophes and drop trailing legal-form words."""
    if not isinstance(name, str):
        return name                                   # missing stays missing
    out = " ".join(name.replace("’", "'").split())
    stripped = _SUFFIX_RE.sub("", out).rstrip(" ,")
    return stripped if stripped else out             # never return an empty name


def clean_company(name: str) -> tuple:
    """Return (company_name, method, review_status, note) for one raw name."""
    if name in MANUAL_COMPANY_MAP:
        target, status, note = MANUAL_COMPANY_MAP[name]
        if target is None:
            return name, "kept_raw_pending_review", status, note
        return target, "manual_mapping", status, note
    cleaned = rule_clean_company(name)
    if cleaned == name:
        return name, "unchanged", "auto", ""
    return cleaned, "rule_suffix_or_spacing", "auto", ""


# ---------------------------------------------------------------- A-04 industry groups

INDUSTRY_GROUPS = [
    "Software & IT", "Hardware & Semiconductors", "Telecom", "Finance & Fintech", "Retail & Consumer",
    "Food & Agriculture", "Media & Gaming", "Healthcare & Life Sciences", "Automotive",
    "Industrial & Manufacturing", "Energy & Resources", "Travel & Transport", "Real Estate & Construction",
    "Business Services", "Education & Public Sector", "Technology (mixed)", "Unknown",
]

GLOBAL_SECTOR_MAP = {
    "Enterprise Applications": "Software & IT", "Enterprise Infrastructure": "Software & IT",
    "AI-native": "Software & IT", "Mobile": "Software & IT",
    "Trending Themes In Enterprise Collaboration": "Software & IT",
    "High Tech": "Technology (mixed)", "Semiconductors": "Hardware & Semiconductors",
    "Telecom": "Telecom",
    "Financial Services": "Finance & Fintech", "Fintech": "Finance & Fintech", "Investment Industry": "Finance & Fintech",
    "Unbundling of Bank": "Finance & Fintech", "Blockchain Technology": "Finance & Fintech",
    "Retail": "Retail & Consumer", "Consumer Goods": "Retail & Consumer", "Consumer": "Retail & Consumer",
    "Food and Agriculture": "Food & Agriculture", "Food and Agriculture Tech": "Food & Agriculture",
    "Trending Themes In Food Tech": "Food & Agriculture",
    "Media & Entertainment": "Media & Gaming", "Gaming": "Media & Gaming",
    "Trending Themes In Media and Entertainment Tech": "Media & Gaming",
    "Healthcare": "Healthcare & Life Sciences", "Healthtech": "Healthcare & Life Sciences",
    "Life Sciences": "Healthcare & Life Sciences",
    "Auto": "Automotive", "Auto Tech": "Automotive",
    "Industrial Goods and Manufacturing": "Industrial & Manufacturing", "Conglomerates": "Industrial & Manufacturing",
    "Chemicals and Materials": "Industrial & Manufacturing", "Chemicals and Materials Tech": "Industrial & Manufacturing",
    "Aerospace, Maritime and Defense": "Industrial & Manufacturing",
    "Aerospace, Maritime and Defense Tech": "Industrial & Manufacturing",
    "Energy": "Energy & Resources", "Energy Tech": "Energy & Resources", "Mining": "Energy & Resources",
    "Environment": "Energy & Resources", "Environment Tech": "Energy & Resources",
    "Travel and Hospitality": "Travel & Transport", "Travel and Hospitality Tech": "Travel & Transport",
    "Transportation and Logistics": "Travel & Transport",
    "Real Estate and Construction": "Real Estate & Construction",
    "Real Estate and Construction Tech": "Real Estate & Construction",
    "Business Services": "Business Services", "Generic Company Lists": "Business Services",
    "Education": "Education & Public Sector", "Edtech": "Education & Public Sector",
    "Nonprofits": "Education & Public Sector", "Public Administration": "Education & Public Sector",
}

# Global labels whose group is a judgement call; shown to the reviewer in the proposal file.
GLOBAL_REVIEW_NOTES = {
    "High Tech": "P1 approved: own group 'Technology (mixed)' (OpenAI, Meta, Google, iRobot, DJI...)",
    "Investment Industry": "needs review: also used for Accenture, Autodesk, Dell; mapping follows the label, not the company",
    "Conglomerates": "needs review: e.g. Bosch; placed in Industrial & Manufacturing",
}

# Tech labels: (group, note). Labels with "/" are mapped on their first part, as approved in A-04.
TECH_INDUSTRY_MAP = {
    "Software": ("Software & IT", ""), "Enterprise Software": ("Software & IT", ""),
    "SaaS/CRM": ("Software & IT", "first part 'SaaS'"), "Software/Cloud": ("Software & IT", "first part 'Software'"),
    "Cloud Storage": ("Software & IT", ""), "Video Conferencing": ("Software & IT", ""),
    "Communication": ("Software & IT", "Discord: chat software"), "Social Media": ("Software & IT", ""),
    "Search/AI": ("Software & IT", "first part 'Search'"), "Networking": ("Software & IT", "matches global 'Enterprise Infrastructure' for Cisco"),
    "Hardware": ("Hardware & Semiconductors", ""), "Semiconductors": ("Hardware & Semiconductors", ""),
    "Semiconductors/AI": ("Hardware & Semiconductors", "first part 'Semiconductors'"),
    "Fintech": ("Finance & Fintech", ""), "Cryptocurrency": ("Finance & Fintech", ""),
    "E-commerce": ("Retail & Consumer", "P5 limitation: label-level mapping also puts Shopify (software) here; no company override"),
    "E-commerce/Cloud": ("Retail & Consumer", "first part 'E-commerce' (Amazon)"),
    "Fitness Tech": ("Retail & Consumer", "Peloton: consumer hardware/subscriptions"),
    "Live Streaming": ("Media & Gaming", ""), "Music Streaming": ("Media & Gaming", ""), "Streaming": ("Media & Gaming", ""),
    "Gaming/Software": ("Media & Gaming", "first part 'Gaming'"),
    "Automotive/EV": ("Automotive", "first part 'Automotive'"),
    "Ridesharing": ("Travel & Transport", ""), "Travel Tech": ("Travel & Transport", ""),
    "Consulting": ("Business Services", ""),
    "EdTech": ("Education & Public Sector", ""),
}


def industry_group(label, source: str) -> str:
    """Map one raw sector/industry label to an industry_group. Missing -> 'Unknown'. Unmapped -> 'UNMAPPED'."""
    if not isinstance(label, str) or not label.strip():
        return "Unknown"
    if source == "global":
        return GLOBAL_SECTOR_MAP.get(label, "UNMAPPED")
    return TECH_INDUSTRY_MAP.get(label, ("UNMAPPED", ""))[0]
