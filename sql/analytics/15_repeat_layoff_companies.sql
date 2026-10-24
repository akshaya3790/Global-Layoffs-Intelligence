-- 15_repeat_layoff_companies.sql
-- Question  : Which companies had more than one layoff event?
-- Unit      : one row = one company_name (cleaned name, Phase 2) with 2 or more global events.
-- Filters   : global sample only. ALL rows are counted; how many of them are flagged as possible internal
--             duplicates (same company + same news URL) is shown, so you can judge whether a "repeat" may
--             be one event reported twice. No rows are removed or merged.
-- Caveats   : names marked needs_review (13) are kept as their raw text, so a company could be split
--             across two spellings. Jobs: known headcounts only, with coverage.
-- Reconciles: tests/test_phase4_db.py recomputes this from the CSV with pandas.
SELECT company_name,
       count(*)                                                            AS events,
       count(*) FILTER (WHERE possible_internal_duplicate)                 AS events_flagged_internal_duplicate,
       count(*) FILTER (WHERE possible_duplicate_group IS NOT NULL)        AS events_with_cross_source_candidate,
       count(DISTINCT event_year)                                          AS distinct_years,
       min(event_date)                                                     AS first_event_date,
       max(event_date)                                                     AS last_event_date,
       count(employees_laid_off)                                           AS events_with_headcount,
       sum(employees_laid_off)                                             AS known_jobs_cut,
       string_agg(DISTINCT industry_group, '; ' ORDER BY industry_group)   AS industry_groups,
       bool_or(company_name_review_status = 'needs_review')                AS name_needs_review
FROM core.v_global_events
GROUP BY company_name
HAVING count(*) >= 2
ORDER BY events DESC, company_name;
