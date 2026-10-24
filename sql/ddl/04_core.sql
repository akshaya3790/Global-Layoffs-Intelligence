-- 04_core.sql
-- Typed analytical tables. Column names and order follow the processed CSVs (one documented rename:
-- transformation_log."column" -> column_name). Safe to rerun: CREATE ... IF NOT EXISTS only.
--
-- Design rules (see reports/PHASE4_SCHEMA_AND_RELATIONSHIPS.md):
--   * One row per source record. No company/sector/country/date dimension, so nothing original is lost.
--   * Missing stays NULL. Quality flags: TRUE / FALSE / NULL (= check not computed for that source).
--   * Range rules (headcount > 0, % between 0 and 100) are NOT constraints: Phases 1-2 keep such values
--     and flag them (qc_*), so a CHECK would reject data the project decided to keep. They are validated
--     by phase4_checks.py instead.
--   * Duplicate candidates are linked by possible_duplicate_group and the pair tables. No primary record
--     is chosen and no event is merged.

-- ---------------------------------------------------------------- reference: the two sources
CREATE TABLE IF NOT EXISTS core.source_datasets (
    source_dataset     TEXT PRIMARY KEY,
    source_file        TEXT NOT NULL UNIQUE,
    source_confidence  TEXT NOT NULL CHECK (source_confidence IN ('high', 'low')),
    description        TEXT NOT NULL,
    known_limitations  TEXT NOT NULL,
    UNIQUE (source_dataset, source_confidence, source_file)          -- target of the events FK below
);

-- ---------------------------------------------------------------- mapping tables (lookups, not dimensions)
CREATE TABLE IF NOT EXISTS core.company_name_mapping (
    source_dataset              TEXT    NOT NULL REFERENCES core.source_datasets (source_dataset),
    company_name_raw            TEXT    NOT NULL,
    company_name                TEXT    NOT NULL,
    company_name_method         TEXT    NOT NULL,
    company_name_review_status  TEXT    NOT NULL,
    rows                        INTEGER NOT NULL CHECK (rows > 0),   -- events using this raw name
    PRIMARY KEY (source_dataset, company_name_raw)
);

CREATE TABLE IF NOT EXISTS core.industry_mapping (
    source_dataset  TEXT    NOT NULL REFERENCES core.source_datasets (source_dataset),
    industry_raw    TEXT    NOT NULL,      -- '(missing)' is the Phase 2 label for an empty sector
    industry_group  TEXT    NOT NULL,
    rows            INTEGER NOT NULL CHECK (rows > 0),
    PRIMARY KEY (source_dataset, industry_raw)
);

-- ---------------------------------------------------------------- the event table (5,035 rows)
CREATE TABLE IF NOT EXISTS core.layoff_events (
    event_key                       TEXT     PRIMARY KEY CHECK (event_key ~ '^[GT]-[0-9]{5}$'),
    source_dataset                  TEXT     NOT NULL,
    source_confidence               TEXT     NOT NULL,
    source_file                     TEXT     NOT NULL,
    source_row_number               INTEGER  NOT NULL CHECK (source_row_number >= 2),  -- CSV line, header = 1
    source_event_id                 TEXT     UNIQUE,                                   -- global layoff_id
    company_name_raw                TEXT     NOT NULL,
    company_name                    TEXT     NOT NULL,
    company_name_method             TEXT     NOT NULL,
    company_name_review_status      TEXT     NOT NULL,
    company_domain                  TEXT,
    event_date_raw                  TEXT     NOT NULL,
    event_date                      DATE     NOT NULL,
    event_year                      SMALLINT NOT NULL,
    event_quarter                   SMALLINT NOT NULL CHECK (event_quarter BETWEEN 1 AND 4),
    event_month                     SMALLINT NOT NULL CHECK (event_month BETWEEN 1 AND 12),
    date_reliability                TEXT     NOT NULL,
    date_flag_reason                TEXT,
    industry_raw                    TEXT,
    industry_group                  TEXT     NOT NULL,     -- 'Unknown' when the sector is missing
    country_raw                     TEXT,
    country                         TEXT,                  -- event location; NULL = not given
    country_basis                   TEXT     NOT NULL,
    hq_country_raw                  TEXT,
    hq_country                      TEXT,
    region                          TEXT     NOT NULL,     -- includes 'Unknown' and 'Unresolved'
    location_raw                    TEXT,
    city                            TEXT,
    state                           TEXT,
    employees_laid_off              INTEGER,               -- NULL = not disclosed / not verified, never 0
    headcount_status                TEXT     NOT NULL,
    workforce_pct                   NUMERIC,               -- exact, no rounding
    total_employees                 INTEGER,
    reason                          TEXT,
    reason_category_derived         TEXT     NOT NULL,
    reason_method                   TEXT     NOT NULL,
    department                      TEXT,                  -- raw text; split rows are in layoff_event_departments
    severance_weeks                 SMALLINT,
    ai_related                      TEXT     CHECK (ai_related IN ('Yes', 'Partial', 'No')),  -- 3 values: not BOOLEAN
    ai_mentioned_in_news_derived    BOOLEAN,
    is_furlough                     BOOLEAN,
    is_permanent_layoff             BOOLEAN,
    news_source                     TEXT,
    news_url_raw                    TEXT,
    news_url                        TEXT,
    news_excerpt                    TEXT,
    news_mentions                   INTEGER,
    source_profile_url              TEXT,
    possible_duplicate_group        TEXT     CHECK (possible_duplicate_group ~ '^DG-[0-9]{3}$'),
    possible_internal_duplicate     BOOLEAN,
    qc_issue_count                  SMALLINT NOT NULL CHECK (qc_issue_count >= 0),
    qc_date_unparseable             BOOLEAN  NOT NULL,
    qc_date_outside_expected_range  BOOLEAN  NOT NULL,
    qc_date_after_audit_date        BOOLEAN  NOT NULL,
    qc_non_numeric_value            BOOLEAN  NOT NULL,
    qc_headcount_not_positive       BOOLEAN  NOT NULL,
    qc_pct_out_of_range             BOOLEAN  NOT NULL,
    qc_headcount_status_conflict    BOOLEAN,               -- NULL = not computed for this source
    qc_headcount_not_verified       BOOLEAN,
    qc_missing_sector               BOOLEAN,
    qc_missing_country              BOOLEAN,
    qc_noisy_company_name           BOOLEAN,
    qc_same_company_same_url        BOOLEAN,
    qc_possible_cross_source_dup    BOOLEAN  NOT NULL,
    qc_headcount_math_gap_gt10pct   BOOLEAN,
    qc_suspect_date                 BOOLEAN  NOT NULL,
    qc_company_name_needs_review    BOOLEAN  NOT NULL,
    qc_country_not_a_country        BOOLEAN  NOT NULL,
    qc_industry_cross_source_conflict BOOLEAN NOT NULL,

    UNIQUE (source_dataset, source_row_number),                       -- traceable to one CSV line
    UNIQUE (event_key, source_dataset, source_row_number),            -- target of child-table FKs
    CHECK (event_year    = EXTRACT(YEAR    FROM event_date)),
    CHECK (event_month   = EXTRACT(MONTH   FROM event_date)),
    CHECK (event_quarter = EXTRACT(QUARTER FROM event_date)),
    FOREIGN KEY (source_dataset, source_confidence, source_file)
        REFERENCES core.source_datasets (source_dataset, source_confidence, source_file),
    FOREIGN KEY (source_dataset, company_name_raw)
        REFERENCES core.company_name_mapping (source_dataset, company_name_raw),
    FOREIGN KEY (source_dataset, industry_raw)                         -- NULL industry_raw is not checked
        REFERENCES core.industry_mapping (source_dataset, industry_raw)
);

-- ---------------------------------------------------------------- tech departments bridge (70 rows)
CREATE TABLE IF NOT EXISTS core.layoff_event_departments (
    event_key             TEXT     NOT NULL,
    source_dataset        TEXT     NOT NULL,
    source_row_number     INTEGER  NOT NULL,
    department_raw        TEXT     NOT NULL,
    department            TEXT     NOT NULL,
    department_position   SMALLINT NOT NULL CHECK (department_position >= 1),
    departments_in_event  SMALLINT NOT NULL CHECK (departments_in_event >= 1),
    allocation_weight     NUMERIC  NOT NULL CHECK (allocation_weight > 0 AND allocation_weight <= 1),
    PRIMARY KEY (event_key, department_position),
    UNIQUE (event_key, department),
    CHECK (department_position <= departments_in_event),
    FOREIGN KEY (event_key, source_dataset, source_row_number)
        REFERENCES core.layoff_events (event_key, source_dataset, source_row_number)
);

-- ---------------------------------------------------------------- quality issues (one row per TRUE flag)
CREATE TABLE IF NOT EXISTS core.quality_issues (
    event_key          TEXT    NOT NULL,
    source_dataset     TEXT    NOT NULL,
    source_row_number  INTEGER NOT NULL,
    company_name       TEXT    NOT NULL,
    quality_flag       TEXT    NOT NULL CHECK (quality_flag LIKE 'qc\_%'),
    PRIMARY KEY (event_key, quality_flag),
    FOREIGN KEY (event_key, source_dataset, source_row_number)
        REFERENCES core.layoff_events (event_key, source_dataset, source_row_number)
);

-- ---------------------------------------------------------------- reproducibility tables
CREATE TABLE IF NOT EXISTS core.transformation_log (
    rule_id       TEXT    PRIMARY KEY,
    decision      TEXT    NOT NULL,
    column_name   TEXT    NOT NULL,          -- CSV header "column" (reserved word in SQL)
    description   TEXT    NOT NULL,
    rows_changed  INTEGER NOT NULL CHECK (rows_changed >= 0),
    examples      TEXT
);

CREATE TABLE IF NOT EXISTS core.field_lineage (
    canonical_field  TEXT NOT NULL,          -- '(dropped)' = source column not carried forward
    source_dataset   TEXT NOT NULL REFERENCES core.source_datasets (source_dataset),
    source_field     TEXT NOT NULL,          -- '(none: missing)' = the source has no such column
    PRIMARY KEY (canonical_field, source_dataset, source_field)
);

CREATE TABLE IF NOT EXISTS core.cross_source_industry_disagreements (
    company_name           TEXT    NOT NULL,
    event_key_tech         TEXT    PRIMARY KEY REFERENCES core.layoff_events (event_key),
    industry_raw_tech      TEXT    NOT NULL,
    industry_group_tech    TEXT    NOT NULL,
    industry_raw_global    TEXT    NOT NULL,
    industry_group_global  TEXT    NOT NULL,
    global_event_keys      TEXT    NOT NULL,  -- ';'-separated, kept as in the CSV; unnested by a view
    global_rows            INTEGER NOT NULL CHECK (global_rows > 0)
);

-- ---------------------------------------------------------------- duplicate-candidate review files
CREATE TABLE IF NOT EXISTS core.possible_duplicate_pairs (
    pair_id                  TEXT    PRIMARY KEY,
    match_confidence         TEXT    NOT NULL,
    tech_record_id           TEXT    NOT NULL REFERENCES core.layoff_events (event_key),
    global_record_id         TEXT    NOT NULL REFERENCES core.layoff_events (event_key),
    tech_company             TEXT    NOT NULL,
    global_company           TEXT    NOT NULL,
    tech_date                DATE    NOT NULL,
    global_date              DATE    NOT NULL,
    date_gap_days            INTEGER NOT NULL,
    tech_headcount           INTEGER NOT NULL,
    global_headcount         INTEGER,
    global_headcount_status  TEXT    NOT NULL,
    headcount_diff_pct       NUMERIC,
    tech_pct                 NUMERIC,
    global_pct               NUMERIC,
    match_reason             TEXT    NOT NULL,
    global_news_url          TEXT,
    review_status            TEXT    NOT NULL,
    reviewer_notes           TEXT,
    UNIQUE (tech_record_id, global_record_id)
);

CREATE TABLE IF NOT EXISTS core.excluded_candidate_pairs (
    excluded_pair_id          TEXT    PRIMARY KEY,
    source_dataset_tech       TEXT    NOT NULL,   -- file name, as written by Phase 1
    tech_record_id            TEXT    NOT NULL REFERENCES core.layoff_events (event_key),
    tech_source_row_number    INTEGER NOT NULL,
    source_dataset_global     TEXT    NOT NULL,
    global_record_id          TEXT    NOT NULL REFERENCES core.layoff_events (event_key),
    global_source_row_number  INTEGER NOT NULL,
    global_layoff_id          TEXT    NOT NULL,
    tech_company              TEXT    NOT NULL,
    global_company            TEXT    NOT NULL,
    name_match                TEXT    NOT NULL,
    matched_alias             TEXT    NOT NULL,
    tech_date                 DATE    NOT NULL,
    global_date               DATE    NOT NULL,
    date_gap_days             INTEGER NOT NULL,
    tech_headcount            INTEGER NOT NULL,
    global_headcount          INTEGER,
    global_headcount_status   TEXT    NOT NULL,
    headcount_diff_pct        NUMERIC,
    tech_pct                  NUMERIC,
    global_pct                NUMERIC,
    match_score               TEXT    NOT NULL,
    exclusion_rule            TEXT    NOT NULL,
    exclusion_reason          TEXT    NOT NULL,
    review_status             TEXT    NOT NULL,
    reviewer_notes            TEXT,
    UNIQUE (tech_record_id, global_record_id)
);

-- ---------------------------------------------------------------- indexes (what each one speeds up)
CREATE INDEX IF NOT EXISTS ix_events_source_date  ON core.layoff_events (source_dataset, event_date);     -- monthly/yearly trends per source
CREATE INDEX IF NOT EXISTS ix_events_industry     ON core.layoff_events (source_dataset, industry_group); -- industry rankings
CREATE INDEX IF NOT EXISTS ix_events_region       ON core.layoff_events (source_dataset, region, country);-- region / country comparisons
CREATE INDEX IF NOT EXISTS ix_events_company      ON core.layoff_events (source_dataset, company_name);   -- repeat layoffs by company
CREATE INDEX IF NOT EXISTS ix_events_dup_group    ON core.layoff_events (possible_duplicate_group)
    WHERE possible_duplicate_group IS NOT NULL;                                                          -- duplicate-group review
CREATE INDEX IF NOT EXISTS ix_events_industry_fk  ON core.layoff_events (source_dataset, industry_raw);   -- FK lookups
CREATE INDEX IF NOT EXISTS ix_departments_dept    ON core.layoff_event_departments (department);         -- department counts
CREATE INDEX IF NOT EXISTS ix_quality_flag        ON core.quality_issues (quality_flag);                 -- flag summaries
CREATE INDEX IF NOT EXISTS ix_pairs_global        ON core.possible_duplicate_pairs (global_record_id);
CREATE INDEX IF NOT EXISTS ix_excluded_global     ON core.excluded_candidate_pairs (global_record_id);
