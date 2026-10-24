"""Writes reviewable mapping PROPOSALS for decisions A-02 (company names) and A-04 (industry groups).

Run from the project root:  python src/make_mapping_proposals.py
Reads data/raw/ only. Writes reports/phase2_proposals/. Changes no data.
"""
from pathlib import Path

import pandas as pd

from phase2_mappings import clean_company, industry_group, TECH_INDUSTRY_MAP, INDUSTRY_GROUPS, GLOBAL_REVIEW_NOTES

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "reports" / "phase2_proposals"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    glob = pd.read_csv(RAW / "layoffs_2019_2026_sample.csv", keep_default_na=False, na_values=[""])
    tech = pd.read_csv(RAW / "tech_layoffs_2025_2026.csv", keep_default_na=False, na_values=[""])

    # ---- A-02 company names: one row per distinct raw name per source
    names = pd.concat([
        glob["company_name"].value_counts().rename_axis("company_name_raw").reset_index(name="rows").assign(source_dataset="global"),
        tech["Company"].value_counts().rename_axis("company_name_raw").reset_index(name="rows").assign(source_dataset="tech"),
    ], ignore_index=True)
    names[["company_name_proposed", "method", "review_status", "note"]] = names["company_name_raw"].apply(
        lambda n: pd.Series(clean_company(n)))
    # names that end up identical (ignoring case) are grouped; list the raw variants being combined
    names["group_key"] = names["company_name_proposed"].str.lower()
    variants = names.groupby("group_key")["company_name_raw"].agg(lambda s: " | ".join(sorted(set(s))))
    names["raw_variants_combined"] = names["group_key"].map(variants)
    names["combines_variants"] = names["raw_variants_combined"].str.contains(r" \| ", regex=True)
    names = names.sort_values(["review_status", "method", "company_name_raw"])
    names.drop(columns="group_key").to_csv(OUT / "company_name_mapping_proposal.csv", index=False)

    # ---- A-04 industry groups: one row per distinct raw label per source
    ind = pd.concat([
        glob["sector"].fillna("(missing)").value_counts().rename_axis("industry_raw").reset_index(name="rows").assign(source_dataset="global"),
        tech["Industry"].value_counts().rename_axis("industry_raw").reset_index(name="rows").assign(source_dataset="tech"),
    ], ignore_index=True)
    ind["industry_group_proposed"] = [industry_group(None if l == "(missing)" else l, s)
                                      for l, s in zip(ind["industry_raw"], ind["source_dataset"])]
    ind["note"] = [TECH_INDUSTRY_MAP.get(l, ("", ""))[1] if s == "tech" else GLOBAL_REVIEW_NOTES.get(l, "")
                   for l, s in zip(ind["industry_raw"], ind["source_dataset"])]
    ind["review_status"] = ind["note"].str.contains("needs review").map({True: "needs_review", False: "auto"})
    assert set(ind["industry_group_proposed"]) <= set(INDUSTRY_GROUPS), "an industry label is UNMAPPED"
    ind.sort_values(["source_dataset", "industry_group_proposed", "rows"], ascending=[True, True, False]) \
       .to_csv(OUT / "industry_mapping_proposal.csv", index=False)

    # ---- cross-source check: same company, do the two sources agree on industry group?
    rows = []
    for _, t in tech.iterrows():
        g = glob[glob["company_name"].str.lower() == t["Company"].lower()]
        for sector in sorted(g["sector"].dropna().unique()):
            rows.append({"company": t["Company"], "tech_industry": t["Industry"],
                         "tech_group": industry_group(t["Industry"], "tech"),
                         "global_sector": sector, "global_group": industry_group(sector, "global")})
    check = pd.DataFrame(rows)
    check["groups_agree"] = check["tech_group"] == check["global_group"]
    check.to_csv(OUT / "cross_source_industry_check.csv", index=False)

    print("company names:", len(names), "| changed:", (names["method"] != "unchanged").sum(),
          "| needs_review:", (names["review_status"] == "needs_review").sum(),
          "| names combined with others:", names["combines_variants"].sum())
    print("industry labels:", len(ind), "| groups used:", ind["industry_group_proposed"].nunique())
    print("cross-source pairs:", len(check), "| disagree:", (~check["groups_agree"]).sum())


if __name__ == "__main__":
    main()
