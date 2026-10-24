# Phase 2: Final Canonical Schema and Mapping Proposals (for sign-off)

**Status:** PROPOSAL. Nothing has been applied to any data. Notebook 02 does not exist yet.
**Approved by you (09:58 UTC):** A-01 to A-16 as recommended, with safeguards. TECH stays separate and lower-confidence. A-07: the 6 dates are kept and flagged.
**Needs your sign-off:** the mapping examples (section 2) and the 5 open points (section 4).

---

## 1. Canonical table `data/processed/layoff_events.csv`

One row per source record: 5,000 global + 35 tech = **5,035 rows**. No row is dropped or merged.

| # | Column | Type | Global source → rule | Tech source → rule | Decision |
|---|---|---|---|---|---|
| 1 | `event_key` | text, PK | Phase 1 `record_id` (G-00001) | Phase 1 `record_id` (T-00001) | A-01 |
| 2 | `source_dataset` | text | `fliar_global_sample` | `tech_layoffs_2025_2026` | |
| 3 | `source_confidence` | text | `high` | `low` | TECH |
| 4 | `source_file` | text | file name | file name | |
| 5 | `source_row_number` | int | CSV line | CSV line | |
| 6 | `source_event_id` | text | `layoff_id` | NULL | A-01 |
| 7 | `company_name_raw` | text | `company_name` (unchanged) | `Company` (unchanged) | |
| 8 | `company_name` | text | `clean_company()` | `clean_company()` | A-02 |
| 9 | `company_name_method` | text | `unchanged` / `rule_suffix_or_spacing` / `manual_mapping` / `kept_raw_flagged` | same | A-02 |
| 10 | `company_domain` | text | `company_domain` | NULL | |
| 11 | `event_date_raw` | text | `date` | `Date` | |
| 12 | `event_date` | date | parsed `date` | parsed `Date` (**never replaced**) | A-07 |
| 13-15 | `event_year`, `event_quarter`, `event_month` | int | from `event_date` | from `event_date` | |
| 16 | `date_reliability` | text | `as_reported` | `as_reported` or `suspect_date` (6 rows) | A-07 |
| 17 | `date_flag_reason` | text | NULL | e.g. "headcount 500 equals global G-03089 dated 2023-12-06" | A-07 |
| 18 | `industry_raw` | text | `sector` | `Industry` | |
| 19 | `industry_group` | text | `industry_group(...,"global")`, missing → `Unknown` | `industry_group(...,"tech")` | A-04 |
| 20 | `country_raw` | text | `country` | `Country` | |
| 21 | `country` | text | standardised `country` | standardised `Country` | A-03, A-05 |
| 22 | `country_basis` | text | `event_location` | `hq_assumed` | A-05b |
| 23 | `hq_country_raw` / `hq_country` | text | `company_country` / standardised | NULL | A-05 |
| 24 | `region` | text | lookup from `country` | lookup from `country` | |
| 25 | `location_raw` | text | NULL | `Location` | A-06 |
| 26 | `city` | text | `company_city` | before the comma | A-06 |
| 27 | `state` | text | `company_state` | after the comma if it's a 2-letter US code, else NULL | A-06 |
| 28 | `employees_laid_off` | int (nullable) | `headcount_cut`, **NULL kept** | `Employees_Laid_Off` | A-08 |
| 29 | `headcount_status` | text | as in source | `reported_unverified` | A-08 |
| 30 | `workforce_pct` | numeric | `pct_workforce` | `Percentage_Workforce` | |
| 31 | `total_employees` | int | NULL (not derived) | `Total_Employees` | A-09 |
| 32 | `reason` | text | NULL | `Reason` | A-10 |
| 33 | `reason_category_derived` / `reason_method` | text | keyword rules on `news_excerpt` / `keyword_rule` | rules on `Reason` / `source_text` | A-10 |
| 34 | `department` | text | NULL | `Department` (original text) | A-11 |
| 35 | `severance_weeks` | int | NULL | `Severance_Weeks` | |
| 36 | `ai_related` | text | NULL | `AI_Related` | A-12 |
| 37 | `ai_mentioned_in_news_derived` | bool | keyword flag | NULL | A-12 |
| 38 | `is_furlough` | bool | `is_furlough` | NULL | |
| 39 | `is_permanent_layoff` | bool | NOT `is_furlough` | NULL | A-16 |
| 40 | `news_source`, `news_url_raw`, `news_url`, `news_excerpt`, `news_mentions`, `source_profile_url` | | from source; `news_url` stripped | NULL | A-14 |
| 41 | `possible_duplicate_group` | text | from the pair files, if linked | same | A-13 |
| 42 | `possible_internal_duplicate` | bool | 42 same-company shared-URL rows | False | A-15 |
| 43 | `qc_*` | bool | carried over from the Phase 1 staged files (unchanged) plus new Phase 2 flags | same | |

**Other outputs in `data/processed/`:** `quality_issues.csv` (one row per flag per record), `transformation_log.csv` (rule, rows affected, examples before and after), `field_lineage.csv`, `company_name_mapping.csv`, `industry_mapping.csv`, `layoff_event_departments.csv`, plus `possible_duplicate_pairs.csv` and `excluded_candidate_pairs.csv` (copied byte-for-byte).

---

## 2. Mapping proposals with examples

Full files are in `reports/phase2_proposals/`: `company_name_mapping_proposal.csv`, `industry_mapping_proposal.csv` and `cross_source_industry_check.csv`.

### 2a. Company names (A-02): 3,532 distinct raw names (3,497 global + 35 tech)

| Method | Names | Examples (raw → proposed) |
|---|---|---|
| Unchanged | 3,314 | `Microsoft` → `Microsoft` |
| Rule: legal suffix / spacing / curly apostrophe | 182 | `Apple Inc` → `Apple` · `Alcoa Corporation` → `Alcoa` · `Royal Philips NV` → `Royal Philips` · `Bloomingdale’s` → `Bloomingdale's` · `Eaton Corp. PLC` → `Eaton` |
| Manual, confident (`proposed`) | 25 | `Electric-car maker Tesla Inc. TSLA` → `Tesla` · `X (Twitter)` and `X - formerly called Twitter` → `Twitter` · 3 Goodyear spellings → `Goodyear Tire & Rubber` · `Byju` / `Byjus’s` → `BYJU'S` · `Scandinavias main airline SAS AB` → `SAS` |
| Manual, **your call** (`needs_review`) | 8 | `Spanish subsidiary of Deutsche Bank` → `Deutsche Bank` · `Mondalez International’s Cadbury chocolate factory` → `Cadbury` · `Walt Disney Company‑Owned Marvel Studios` → `Marvel Studios` · `Mahindra & Mahindra's Pininfarina Engineering` → `Pininfarina` · `Sodexo at The University of Pittsburgh` → `Sodexo` · `Sony Interactive Entertainment Japan Studio` → `Sony Interactive Entertainment` · `Think & Learn Private Limited` → `BYJU'S` · `Tata Vendor’s Amulite Auto Components Company` → `Amulite Auto Components` |
| Kept raw and flagged (not a company name) | 3 | `Cargo services firm in Charlotte` · `São José dos Campos metalmakers` · `First Of The Three Large Cognac Houses` |

**Effect:** 69 raw names collapse into 32 groups. Examples: `AT&T` + `AT&T Inc`, `Gap` + `Gap Inc`, `SNAP` + `Snap`, `Sony` + `Sony Corp`, `Twitter` + 2 X aliases. The raw name is always kept in `company_name_raw`.

### 2b. Industry groups (A-04): 77 raw labels (49 global + 1 missing + 27 tech) → 16 groups

| Group | Rows | Example raw labels |
|---|---|---|
| Retail & Consumer | 684 | Retail, Consumer Goods, Consumer, *tech:* E-commerce, Fitness Tech |
| Finance & Fintech | 378 | Financial Services, Fintech, Investment Industry, *tech:* Cryptocurrency |
| Healthcare & Life Sciences | 298 | Healthcare, Healthtech, Life Sciences |
| Software & IT | 295 | Enterprise Applications, Enterprise Infrastructure, AI-native, *tech:* SaaS/CRM, Social Media, Networking |
| Food & Agriculture | 268 | Food and Agriculture (+ Tech) |
| Media & Gaming | 227 | Media & Entertainment, Gaming, *tech:* Streaming, Gaming/Software |
| Industrial & Manufacturing | 208 | Industrial Goods, Aerospace & Defense, Chemicals, Conglomerates |
| Energy & Resources | 191 | Energy, Energy Tech, Mining |
| Automotive | 187 | Auto, Auto Tech, *tech:* Automotive/EV |
| Business Services | 185 | Business Services, *tech:* Consulting |
| Travel & Transport | 184 | Travel and Hospitality, Transportation, *tech:* Ridesharing, Travel Tech |
| Hardware & Semiconductors | 123 | Semiconductors, High Tech*, *tech:* Hardware |
| Real Estate & Construction | 94 | Real Estate and Construction (+ Tech) |
| Telecom | 83 | Telecom |
| Education & Public Sector | 66 | Education, Edtech, Nonprofits, Public Administration |
| **Unknown** | 1,564 | missing global sector (kept visible, not dropped) |

Every raw label is mapped, and there are no UNMAPPED values (enforced by a test).

---

## 3. R1-R4 behaviour with missing values (existing behaviour kept, not new)

The four rules keep the notebook's original comparisons. A missing input gives **no flag**, because a comparison with a missing value is False in pandas. That was always how notebook 01 behaved, and missing values are reported separately in the missing-value analysis. The tests document this behaviour; they don't introduce it.

---

## 4. Open points that need your sign-off

| # | Point | Evidence | Recommendation |
|---|---|---|---|
| **P1** | Global label **"High Tech"** (70 rows) is a mixed bag: OpenAI, Meta, Google, iRobot, DJI, Matterport | `industry_mapping_proposal.csv` (needs_review) | Add a 16th real group, **"Technology (mixed)"**, instead of forcing these into Hardware. The current draft maps them to Hardware & Semiconductors. |
| **P2** | The **8 `needs_review` company mappings** (subsidiary vs parent) | section 2a | Approve as listed, or tell me which ones should keep their raw name. |
| **P3** | The **two sources disagree on industry** for 9 of 16 company/label pairs (e.g. Dell: tech "Hardware" vs global "Investment Industry"; Unity: "Gaming" vs "Financial Services") | `cross_source_industry_check.csv` | Keep each row's own source label (the approved A-04 rule) and **don't override by company**. Note the disagreement as a known source-quality limitation of the global `sector` field. |
| **P4** | R4 edge case: when `% of workforce` = 0, the "implied" count is 0, so the gap is infinite and **R4 flags it** (existing behaviour). 0 laid off with 0% gives an undefined gap and no flag. | tests R4-10, R4-11 | Keep as is: a 0% value is also caught by the existing percentage rule, so the double flag is harmless. |
| **P5** | Tech `E-commerce` → Retail & Consumer puts **Shopify** (software) next to Wayfair | industry proposal | Keep it, since only 2 rows and one label can't be split by company without an override. |

Reply with "approve P1-P5 as recommended", or give your changes. Once approved, I'll build notebook 02.
