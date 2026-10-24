-- 19_sensitivity_by_year.sql
-- Question  : Do furloughs or unresolved duplicate candidates drive the yearly results?
-- Unit      : one row = one year.
-- Filters   : global sample only (tech rows never included); all_events counts every row.
--             Every column after all_events is a WHAT-IF that leaves some rows out of the count;
--             nothing is deleted from the database.
--   excl_furloughs                          : rows with is_furlough = TRUE left out (temporary layoffs)
--   excl_internal_duplicates                : rows flagged possible_internal_duplicate left out (42 rows)
--   excl_cross_source_duplicate_candidates  : rows in a possible_duplicate_group left out (18 global rows)
--   known_jobs_*                            : the same what-ifs for known headcounts (coverage applies)
-- Caveats   : 2026 is partial; May-June 2026 possibly incomplete.
-- Reconciles: reports/eda/03_11_sensitivity_by_year.csv (event columns).
SELECT event_year,
       count(*)                                                                     AS all_events,
       count(*) FILTER (WHERE is_furlough IS NOT TRUE)                              AS excl_furloughs,
       count(*) FILTER (WHERE possible_internal_duplicate IS NOT TRUE)              AS excl_internal_duplicates,
       count(*) FILTER (WHERE possible_duplicate_group IS NULL)                     AS excl_cross_source_duplicate_candidates,
       round(100.0 * count(*) FILTER (WHERE is_furlough) / count(*), 1)             AS furlough_share_pct,
       sum(employees_laid_off)                                                      AS known_jobs_all,
       sum(employees_laid_off) FILTER (WHERE is_furlough IS NOT TRUE)               AS known_jobs_excl_furloughs,
       sum(employees_laid_off) FILTER (WHERE possible_internal_duplicate IS NOT TRUE
                                         AND possible_duplicate_group IS NULL)      AS known_jobs_excl_all_duplicate_flags,
       CASE WHEN event_year = 2026 THEN 'partial year' ELSE 'complete year' END     AS period_note
FROM core.v_global_events
GROUP BY event_year
ORDER BY event_year;
