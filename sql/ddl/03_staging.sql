-- 03_staging.sql
-- Staging tables: one per processed CSV, same column names and order, every column TEXT and nullable,
-- no keys. COPY fills them exactly as the CSV is written; typing and checks happen on the way to core.
-- GENERATED from src/phase4_spec.py (tests/test_phase4_unit.py checks the two agree). Safe to rerun.

-- source: data/processed/company_name_mapping.csv
CREATE TABLE IF NOT EXISTS staging.company_name_mapping (
    source_dataset TEXT,
    company_name_raw TEXT,
    company_name TEXT,
    company_name_method TEXT,
    company_name_review_status TEXT,
    rows TEXT
);

-- source: data/processed/industry_mapping.csv
CREATE TABLE IF NOT EXISTS staging.industry_mapping (
    source_dataset TEXT,
    industry_raw TEXT,
    industry_group TEXT,
    rows TEXT
);

-- source: data/processed/layoff_events.csv
CREATE TABLE IF NOT EXISTS staging.layoff_events (
    event_key TEXT,
    source_dataset TEXT,
    source_confidence TEXT,
    source_file TEXT,
    source_row_number TEXT,
    source_event_id TEXT,
    company_name_raw TEXT,
    company_name TEXT,
    company_name_method TEXT,
    company_name_review_status TEXT,
    company_domain TEXT,
    event_date_raw TEXT,
    event_date TEXT,
    event_year TEXT,
    event_quarter TEXT,
    event_month TEXT,
    date_reliability TEXT,
    date_flag_reason TEXT,
    industry_raw TEXT,
    industry_group TEXT,
    country_raw TEXT,
    country TEXT,
    country_basis TEXT,
    hq_country_raw TEXT,
    hq_country TEXT,
    region TEXT,
    location_raw TEXT,
    city TEXT,
    state TEXT,
    employees_laid_off TEXT,
    headcount_status TEXT,
    workforce_pct TEXT,
    total_employees TEXT,
    reason TEXT,
    reason_category_derived TEXT,
    reason_method TEXT,
    department TEXT,
    severance_weeks TEXT,
    ai_related TEXT,
    ai_mentioned_in_news_derived TEXT,
    is_furlough TEXT,
    is_permanent_layoff TEXT,
    news_source TEXT,
    news_url_raw TEXT,
    news_url TEXT,
    news_excerpt TEXT,
    news_mentions TEXT,
    source_profile_url TEXT,
    possible_duplicate_group TEXT,
    possible_internal_duplicate TEXT,
    qc_issue_count TEXT,
    qc_date_unparseable TEXT,
    qc_date_outside_expected_range TEXT,
    qc_date_after_audit_date TEXT,
    qc_non_numeric_value TEXT,
    qc_headcount_not_positive TEXT,
    qc_pct_out_of_range TEXT,
    qc_headcount_status_conflict TEXT,
    qc_headcount_not_verified TEXT,
    qc_missing_sector TEXT,
    qc_missing_country TEXT,
    qc_noisy_company_name TEXT,
    qc_same_company_same_url TEXT,
    qc_possible_cross_source_dup TEXT,
    qc_headcount_math_gap_gt10pct TEXT,
    qc_suspect_date TEXT,
    qc_company_name_needs_review TEXT,
    qc_country_not_a_country TEXT,
    qc_industry_cross_source_conflict TEXT
);

-- source: data/processed/layoff_event_departments.csv
CREATE TABLE IF NOT EXISTS staging.layoff_event_departments (
    event_key TEXT,
    source_dataset TEXT,
    source_row_number TEXT,
    department_raw TEXT,
    department TEXT,
    department_position TEXT,
    departments_in_event TEXT,
    allocation_weight TEXT
);

-- source: data/processed/quality_issues.csv
CREATE TABLE IF NOT EXISTS staging.quality_issues (
    event_key TEXT,
    source_dataset TEXT,
    source_row_number TEXT,
    company_name TEXT,
    quality_flag TEXT
);

-- source: data/processed/transformation_log.csv
CREATE TABLE IF NOT EXISTS staging.transformation_log (
    rule_id TEXT,
    decision TEXT,
    column_name TEXT,  -- CSV header "column" (reserved word in SQL)
    description TEXT,
    rows_changed TEXT,
    examples TEXT
);

-- source: data/processed/field_lineage.csv
CREATE TABLE IF NOT EXISTS staging.field_lineage (
    canonical_field TEXT,
    source_dataset TEXT,
    source_field TEXT
);

-- source: data/processed/cross_source_industry_disagreements.csv
CREATE TABLE IF NOT EXISTS staging.cross_source_industry_disagreements (
    company_name TEXT,
    event_key_tech TEXT,
    industry_raw_tech TEXT,
    industry_group_tech TEXT,
    industry_raw_global TEXT,
    industry_group_global TEXT,
    global_event_keys TEXT,
    global_rows TEXT
);

-- source: data/processed/possible_duplicate_pairs.csv
CREATE TABLE IF NOT EXISTS staging.possible_duplicate_pairs (
    pair_id TEXT,
    match_confidence TEXT,
    tech_record_id TEXT,
    global_record_id TEXT,
    tech_company TEXT,
    global_company TEXT,
    tech_date TEXT,
    global_date TEXT,
    date_gap_days TEXT,
    tech_headcount TEXT,
    global_headcount TEXT,
    global_headcount_status TEXT,
    headcount_diff_pct TEXT,
    tech_pct TEXT,
    global_pct TEXT,
    match_reason TEXT,
    global_news_url TEXT,
    review_status TEXT,
    reviewer_notes TEXT
);

-- source: data/processed/excluded_candidate_pairs.csv
CREATE TABLE IF NOT EXISTS staging.excluded_candidate_pairs (
    excluded_pair_id TEXT,
    source_dataset_tech TEXT,
    tech_record_id TEXT,
    tech_source_row_number TEXT,
    source_dataset_global TEXT,
    global_record_id TEXT,
    global_source_row_number TEXT,
    global_layoff_id TEXT,
    tech_company TEXT,
    global_company TEXT,
    name_match TEXT,
    matched_alias TEXT,
    tech_date TEXT,
    global_date TEXT,
    date_gap_days TEXT,
    tech_headcount TEXT,
    global_headcount TEXT,
    global_headcount_status TEXT,
    headcount_diff_pct TEXT,
    tech_pct TEXT,
    global_pct TEXT,
    match_score TEXT,
    exclusion_rule TEXT,
    exclusion_reason TEXT,
    review_status TEXT,
    reviewer_notes TEXT
);
