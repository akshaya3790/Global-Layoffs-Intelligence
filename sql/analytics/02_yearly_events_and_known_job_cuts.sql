-- 02_yearly_events_and_known_job_cuts.sql
-- Question  : Per year, how many events, and how many jobs were cut where the headcount is known?
-- Unit      : one row = one calendar year (global sample).
-- Filters   : global sample only; all rows counted (furloughs and duplicate candidates included - see 19).
-- Missing   : verified_jobs_cut sums ONLY known headcounts (2,489 of 5,000 rows). Missing headcounts are
--             never treated as 0; a year with no known headcount would show NULL. Always read the jobs
--             figure together with headcount_coverage_pct - it is a LOWER BOUND, not a total.
-- Caveats   : 2026 is partial (Jan to 14 Jun); May-June 2026 possibly incomplete.
-- Reconciles: reports/eda/03_02_yearly_events_and_jobs.csv.
SELECT event_year,
       count(*)                                                            AS events,
       count(employees_laid_off)                                           AS events_with_headcount,
       sum(employees_laid_off)                                             AS verified_jobs_cut,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY employees_laid_off)     AS median_cut,
       round(100.0 * count(employees_laid_off) / count(*), 1)              AS headcount_coverage_pct,
       round(100.0 * count(*) / sum(count(*)) OVER (), 1)                  AS share_of_events_pct,
       count(*) FILTER (WHERE is_permanent_layoff)                         AS permanent_events,
       count(*) FILTER (WHERE is_furlough)                                 AS furlough_events,
       (event_year = 2026)                                                 AS partial_year,
       CASE WHEN event_year = 2026 THEN 'partial year: Jan to 14 Jun 2026; May-Jun possibly incomplete'
            ELSE 'complete year' END                                       AS period_note
FROM core.v_global_events
GROUP BY event_year
ORDER BY event_year;
