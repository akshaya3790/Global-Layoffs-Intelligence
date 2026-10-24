"""Phase 4: the expected shape of every processed CSV that is loaded into PostgreSQL.

This is the single source of truth used by
  * the pre-flight checks in phase4_load.py (exact header, required fields, value types),
  * the staging -> core INSERT statements (one cast per column),
  * tests/test_phase4_unit.py, which checks that sql/ddl/*.sql agrees with this file.

Type codes (CSV text -> PostgreSQL):
  text     -> TEXT
  int      -> INTEGER   (the CSV may write whole numbers as "50.0"; anything with a fraction is rejected)
  smallint -> SMALLINT  (same rule)
  numeric  -> NUMERIC   (no fixed scale, so values such as 33.333333 are stored exactly)
  bool     -> BOOLEAN   (CSV "True"/"False"; an empty field means "not computed" and becomes NULL)
  date     -> DATE      (CSV "YYYY-MM-DD")

An empty CSV field always becomes SQL NULL. Required columns must never be empty.
"""

PG_TYPES = {"text": "TEXT", "int": "INTEGER", "smallint": "SMALLINT", "numeric": "NUMERIC",
            "bool": "BOOLEAN", "date": "DATE"}

# The only deliberate rename: "column" is a reserved word in SQL.
RENAMES = {("transformation_log.csv", "column"): "column_name"}


def _cols(spec: str):
    """Parse 'name:type[!]' lines; '!' marks a required (NOT NULL) column."""
    out = []
    for line in spec.split():
        name, typ = line.split(":")
        required = typ.endswith("!")
        out.append((name, typ.rstrip("!"), required))
    return out


_QC_ALWAYS = ["qc_date_unparseable", "qc_date_outside_expected_range", "qc_date_after_audit_date",
              "qc_non_numeric_value", "qc_headcount_not_positive", "qc_pct_out_of_range"]
_QC_SOMETIMES = ["qc_headcount_status_conflict", "qc_headcount_not_verified", "qc_missing_sector",
                 "qc_missing_country", "qc_noisy_company_name", "qc_same_company_same_url"]
_QC_PHASE2 = ["qc_possible_cross_source_dup", "qc_headcount_math_gap_gt10pct", "qc_suspect_date",
              "qc_company_name_needs_review", "qc_country_not_a_country", "qc_industry_cross_source_conflict"]
QC_FLAGS = _QC_ALWAYS + _QC_SOMETIMES + _QC_PHASE2
# Flags that are NULL ("not computed") for one of the sources, so they cannot be NOT NULL.
QC_NULLABLE = set(_QC_SOMETIMES) | {"qc_headcount_math_gap_gt10pct"}

EVENTS = _cols("""
event_key:text! source_dataset:text! source_confidence:text! source_file:text! source_row_number:int!
source_event_id:text company_name_raw:text! company_name:text! company_name_method:text!
company_name_review_status:text! company_domain:text event_date_raw:text! event_date:date!
event_year:smallint! event_quarter:smallint! event_month:smallint! date_reliability:text! date_flag_reason:text
industry_raw:text industry_group:text! country_raw:text country:text country_basis:text! hq_country_raw:text
hq_country:text region:text! location_raw:text city:text state:text employees_laid_off:int
headcount_status:text! workforce_pct:numeric total_employees:int reason:text reason_category_derived:text!
reason_method:text! department:text severance_weeks:smallint ai_related:text ai_mentioned_in_news_derived:bool
is_furlough:bool is_permanent_layoff:bool news_source:text news_url_raw:text news_url:text news_excerpt:text
news_mentions:int source_profile_url:text possible_duplicate_group:text possible_internal_duplicate:bool
qc_issue_count:smallint!
""") + [(f, "bool", f not in QC_NULLABLE) for f in QC_FLAGS]

FILES = {
    # file name: (core table, columns, primary key)   -- listed in load order (parents first)
    "company_name_mapping.csv": ("company_name_mapping", _cols("""
        source_dataset:text! company_name_raw:text! company_name:text! company_name_method:text!
        company_name_review_status:text! rows:int!"""), ["source_dataset", "company_name_raw"]),
    "industry_mapping.csv": ("industry_mapping", _cols("""
        source_dataset:text! industry_raw:text! industry_group:text! rows:int!"""),
        ["source_dataset", "industry_raw"]),
    "layoff_events.csv": ("layoff_events", EVENTS, ["event_key"]),
    "layoff_event_departments.csv": ("layoff_event_departments", _cols("""
        event_key:text! source_dataset:text! source_row_number:int! department_raw:text! department:text!
        department_position:smallint! departments_in_event:smallint! allocation_weight:numeric!"""),
        ["event_key", "department_position"]),
    "quality_issues.csv": ("quality_issues", _cols("""
        event_key:text! source_dataset:text! source_row_number:int! company_name:text! quality_flag:text!"""),
        ["event_key", "quality_flag"]),
    "transformation_log.csv": ("transformation_log", _cols("""
        rule_id:text! decision:text! column:text! description:text! rows_changed:int! examples:text"""),
        ["rule_id"]),
    "field_lineage.csv": ("field_lineage", _cols("""
        canonical_field:text! source_dataset:text! source_field:text!"""),
        ["canonical_field", "source_dataset", "source_field"]),
    "cross_source_industry_disagreements.csv": ("cross_source_industry_disagreements", _cols("""
        company_name:text! event_key_tech:text! industry_raw_tech:text! industry_group_tech:text!
        industry_raw_global:text! industry_group_global:text! global_event_keys:text! global_rows:int!"""),
        ["event_key_tech"]),
    "possible_duplicate_pairs.csv": ("possible_duplicate_pairs", _cols("""
        pair_id:text! match_confidence:text! tech_record_id:text! global_record_id:text! tech_company:text!
        global_company:text! tech_date:date! global_date:date! date_gap_days:int! tech_headcount:int!
        global_headcount:int global_headcount_status:text! headcount_diff_pct:numeric tech_pct:numeric
        global_pct:numeric match_reason:text! global_news_url:text review_status:text! reviewer_notes:text"""),
        ["pair_id"]),
    "excluded_candidate_pairs.csv": ("excluded_candidate_pairs", _cols("""
        excluded_pair_id:text! source_dataset_tech:text! tech_record_id:text! tech_source_row_number:int!
        source_dataset_global:text! global_record_id:text! global_source_row_number:int! global_layoff_id:text!
        tech_company:text! global_company:text! name_match:text! matched_alias:text! tech_date:date!
        global_date:date! date_gap_days:int! tech_headcount:int! global_headcount:int
        global_headcount_status:text! headcount_diff_pct:numeric tech_pct:numeric global_pct:numeric
        match_score:text! exclusion_rule:text! exclusion_reason:text! review_status:text! reviewer_notes:text"""),
        ["excluded_pair_id"]),
}

MANIFEST_FILE = "phase2_output_manifest.csv"

# Reference rows for core.source_datasets (from data/raw/SOURCE_DATA_CARD.md and the Phase 1-3 reports).
SOURCE_DATASETS = [
    {"source_dataset": "fliar_global_sample", "source_file": "layoffs_2019_2026_sample.csv",
     "source_confidence": "high",
     "description": "Fliar Research global layoffs sample (CC BY-NC). 26% sample of the source's events, "
                    "Jan 2019 to 14 Jun 2026.",
     "known_limitations": "Sample, not the full market. About 50% of events have a verified headcount, "
                          "22% have a workforce %, 31% have no sector, 9% have no event country. 2026 is "
                          "partial; May-June 2026 look incomplete (possible collection lag)."},
    {"source_dataset": "tech_layoffs_2025_2026", "source_file": "tech_layoffs_2025_2026.csv",
     "source_confidence": "low",
     "description": "35 technology-company layoffs, 2025-2026, unknown provenance.",
     "known_limitations": "Unknown source; numbers reported, not verified; 6 dates flagged as suspect "
                          "(qc_suspect_date). Never add to global event totals."},
]


def core_column(file_name: str, csv_column: str) -> str:
    return RENAMES.get((file_name, csv_column), csv_column)
