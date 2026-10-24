-- 03_industry_ranking.sql
-- Question  : Which industry groups have the most layoff events?
-- Unit      : one row = one industry group (17 values including 'Unknown').
-- Filters   : global sample only; all rows counted.
-- Missing   : 'Unknown' (sector missing, 1,564 rows) is KEPT as its own group and ranked like the others,
--             so the shares of the known groups are not inflated. Jobs: known headcounts only + coverage.
-- Reconciles: reports/eda/03_03_industry_ranking.csv.
SELECT row_number() OVER (ORDER BY count(*) DESC, industry_group)          AS rank_by_events,
       industry_group,
       count(*)                                                            AS events,
       round(100.0 * count(*) / sum(count(*)) OVER (), 1)                  AS share_of_events_pct,
       count(employees_laid_off)                                           AS events_with_headcount,
       sum(employees_laid_off)                                             AS verified_jobs_cut,
       round(100.0 * count(employees_laid_off) / count(*), 1)              AS headcount_coverage_pct,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY employees_laid_off)     AS median_cut
FROM core.v_global_events
GROUP BY industry_group
ORDER BY rank_by_events;
