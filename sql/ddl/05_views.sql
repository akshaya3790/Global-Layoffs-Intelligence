-- 05_views.sql
-- Helper views. They only filter or reshape core tables; they never drop, merge or relabel records.
-- CREATE OR REPLACE only touches these project-owned views in schema core.

-- Global sample only (5,000 rows, high confidence). Use for every market-level figure.
CREATE OR REPLACE VIEW core.v_global_events AS
SELECT * FROM core.layoff_events WHERE source_dataset = 'fliar_global_sample';

-- Technology file only (35 rows, low confidence). Never add these to global totals.
CREATE OR REPLACE VIEW core.v_tech_events AS
SELECT * FROM core.layoff_events WHERE source_dataset = 'tech_layoffs_2025_2026';

-- Data-completeness label per month, used by the trend queries.
-- 2026 is partial (data ends 14 June 2026); May and June 2026 look incomplete (possible collection lag).
CREATE OR REPLACE VIEW core.v_period_notes AS
SELECT d::date                                   AS month_start,
       EXTRACT(YEAR FROM d)::int                 AS event_year,
       CASE WHEN d >= DATE '2026-05-01' THEN 'partial: possible collection lag (May-Jun 2026), not evidence of a decline'
            WHEN d >= DATE '2026-01-01' THEN 'partial year (2026 data ends 14 Jun)'
            ELSE 'complete' END                  AS period_note
FROM generate_series(DATE '2019-01-01', DATE '2026-06-01', INTERVAL '1 month') AS d;

-- Members of each possible-duplicate group (no primary record chosen, nothing merged).
CREATE OR REPLACE VIEW core.v_duplicate_group_members AS
SELECT possible_duplicate_group, event_key, source_dataset, source_confidence, company_name,
       event_date, qc_suspect_date, employees_laid_off
FROM core.layoff_events
WHERE possible_duplicate_group IS NOT NULL;

-- The ';'-separated global_event_keys of each industry disagreement, one row per global event.
CREATE OR REPLACE VIEW core.v_industry_disagreement_global_events AS
SELECT d.event_key_tech, d.company_name, k.global_event_key
FROM core.cross_source_industry_disagreements AS d
CROSS JOIN LATERAL unnest(string_to_array(d.global_event_keys, ';')) AS k(global_event_key)
WHERE k.global_event_key <> '';
