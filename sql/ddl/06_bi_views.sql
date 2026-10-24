-- 06_bi_views.sql
-- Reporting views for the Power BI dashboard (import mode). They only filter, reshape and aggregate core
-- tables; they never drop, merge or relabel records. CREATE OR REPLACE only touches these views.
--
-- Rules every view follows:
--   * GLOBAL ONLY: built on core.v_global_events, so the 35 tech rows can never enter a global figure.
--     The tech file stays in core.v_tech_events for its own labelled panel.
--   * Disclosed jobs are a LOWER BOUND: NULL headcounts stay NULL and are counted separately, never as 0.
--   * 2026 is partial (data ends 14 Jun 2026): flagged with is_partial_period / period_note.
--   * Counts are SAMPLE counts (26% company sample, 5,000 of 19,208 events), not market totals.

-- One row per global event, with the ~25 columns the dashboard needs.
CREATE OR REPLACE VIEW core.v_bi_events AS
SELECT e.event_key,
       e.company_name,
       e.company_domain,
       e.event_date,
       date_trunc('month', e.event_date)::date                          AS month_start,
       e.event_year,
       e.event_quarter,
       e.event_month,
       e.industry_group,
       e.industry_raw,
       COALESCE(e.country, 'Unknown')                                    AS country,
       e.region,
       e.employees_laid_off,                                             -- NULL = not disclosed
       (e.employees_laid_off IS NOT NULL)                                AS has_disclosed_headcount,
       CASE WHEN e.employees_laid_off IS NULL THEN 'Undisclosed'
            WHEN e.employees_laid_off < 100   THEN '1-99'
            WHEN e.employees_laid_off < 500   THEN '100-499'
            WHEN e.employees_laid_off < 1000  THEN '500-999'
            WHEN e.employees_laid_off < 5000  THEN '1,000-4,999'
            ELSE '5,000+' END                                            AS size_band,
       e.workforce_pct,                                                  -- NULL = not reported
       e.is_furlough,
       e.is_permanent_layoff,
       e.possible_internal_duplicate,
       (e.possible_duplicate_group IS NOT NULL)                          AS has_cross_source_candidate,
       e.company_name_review_status,
       e.reason_category_derived,
       e.news_source,
       e.news_url,
       e.qc_issue_count,
       (e.event_year = 2026)                                             AS is_partial_period,
       p.period_note
FROM core.v_global_events AS e
JOIN core.v_period_notes  AS p ON p.month_start = date_trunc('month', e.event_date)::date;

-- One row per company (cleaned name), from query 15 plus the gap to its second event.
-- days_to_second_event is NULL for single-event companies (censored at 14 Jun 2026, NOT "never").
CREATE OR REPLACE VIEW core.v_bi_company_summary AS
WITH ranked AS (
    SELECT company_name, event_date, industry_group, employees_laid_off, company_name_review_status,
           row_number() OVER (PARTITION BY company_name ORDER BY event_date, event_key) AS rn
    FROM core.v_global_events
)
SELECT company_name,
       count(*)                                                          AS events,
       (count(*) >= 2)                                                   AS is_repeat_company,
       min(event_date)                                                   AS first_event_date,
       max(event_date)                                                   AS last_event_date,
       max(event_date) FILTER (WHERE rn = 2) - min(event_date)           AS days_to_second_event,
       DATE '2026-06-14' - min(event_date)                               AS days_observed,
       count(DISTINCT extract(YEAR FROM event_date))                     AS distinct_years,
       count(employees_laid_off)                                         AS events_with_headcount,
       sum(employees_laid_off)                                           AS disclosed_jobs_cut,
       max(industry_group) FILTER (WHERE rn = 1)                         AS first_industry_group,
       string_agg(DISTINCT industry_group, '; ' ORDER BY industry_group) AS industry_groups,
       bool_or(company_name_review_status = 'needs_review')              AS name_needs_review
FROM ranked
GROUP BY company_name;

-- Disclosure and missingness rates by year, region and industry group (long format, one slicer field).
CREATE OR REPLACE VIEW core.v_bi_quality AS
WITH dims AS (
    SELECT 'year'::text AS dimension, event_year::text AS value, * FROM core.v_global_events
    UNION ALL
    SELECT 'region', region, * FROM core.v_global_events
    UNION ALL
    SELECT 'industry_group', industry_group, * FROM core.v_global_events
)
SELECT dimension,
       value,
       count(*)                                                                    AS events,
       count(employees_laid_off)                                                   AS events_with_headcount,
       round(100.0 * count(employees_laid_off) / count(*), 1)                      AS disclosure_rate_pct,
       count(workforce_pct)                                                        AS events_with_workforce_pct,
       count(*) FILTER (WHERE industry_group = 'Unknown')                          AS events_unknown_sector,
       round(100.0 * count(*) FILTER (WHERE industry_group = 'Unknown') / count(*), 1) AS unknown_sector_pct,
       count(*) FILTER (WHERE country IS NULL)                                     AS events_no_country,
       count(*) FILTER (WHERE region = 'Unresolved')                               AS events_unresolved_country,
       count(*) FILTER (WHERE is_furlough)                                         AS furlough_events,
       count(*) FILTER (WHERE possible_internal_duplicate)                         AS possible_internal_duplicates
FROM dims
GROUP BY dimension, value;

-- Sample vs full population by year. Full figures typed in from data/raw/SOURCE_DATA_CARD.md,
-- table "Layoffs by year" (Fliar Research 2026, CC BY-NC 4.0). Also in src/phase5_stats.py.
CREATE OR REPLACE VIEW core.v_bi_benchmark AS
WITH full_data (event_year, full_events, full_disclosed_jobs) AS (
    VALUES (2019, 1759, 764478), (2020, 3780, 3122163), (2021, 1032, 448334), (2022, 2008, 846889),
           (2023, 3391, 1822899), (2024, 3011, 1440648), (2025, 2977, 1734556), (2026, 1250, 749078)
), sample AS (
    SELECT event_year, count(*) AS sample_events, sum(employees_laid_off) AS sample_disclosed_jobs
    FROM core.v_global_events GROUP BY event_year
)
SELECT f.event_year,
       s.sample_events,
       f.full_events,
       round(s.sample_events::numeric / f.full_events, 3)                AS events_ratio,
       s.sample_disclosed_jobs,
       f.full_disclosed_jobs,
       round(s.sample_disclosed_jobs::numeric / f.full_disclosed_jobs, 3) AS jobs_ratio,
       round(5000::numeric / 19208, 3)                                   AS nominal_ratio,
       (f.event_year = 2026)                                             AS is_partial_period
FROM full_data AS f
JOIN sample    AS s USING (event_year);

-- Headline numbers in one row, so every dashboard card can be reconciled with SQL.
CREATE OR REPLACE VIEW core.v_bi_kpis AS
SELECT count(*)                                                          AS events,
       count(DISTINCT company_name)                                      AS companies,
       count(employees_laid_off)                                         AS events_with_headcount,
       count(*) - count(employees_laid_off)                              AS events_headcount_unknown,
       round(100.0 * count(employees_laid_off) / count(*), 1)            AS disclosure_rate_pct,
       sum(employees_laid_off)                                           AS disclosed_jobs_cut_lower_bound,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY employees_laid_off)   AS median_disclosed_cut,
       count(*) FILTER (WHERE event_year = 2019)                         AS events_2019_baseline,
       round(100.0 * count(*) FILTER (WHERE industry_group = 'Unknown') / count(*), 1) AS unknown_sector_pct,
       (SELECT count(*) FROM core.v_bi_company_summary WHERE is_repeat_company) AS repeat_companies,
       max(event_date)                                                   AS data_ends
FROM core.v_global_events;
