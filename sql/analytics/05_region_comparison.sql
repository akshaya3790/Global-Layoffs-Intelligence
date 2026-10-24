-- 05_region_comparison.sql
-- Question  : How do regions compare (event location)?
-- Unit      : one row = one region.
-- Filters   : global sample only; all rows counted.
-- Missing   : 'Unknown' = no event country (470 rows). 'Unresolved' = the country value is a US state or a
--             fragment (Arizona, Nevada, New York, Rhode Island, Quebec, Sa; 6 rows) - kept as loaded,
--             because the relabelling decision is still open. Jobs: known headcounts only + coverage.
-- Reconciles: reports/eda/03_05_region_events.csv.
SELECT region,
       count(*)                                                            AS events,
       count(employees_laid_off)                                           AS events_with_headcount,
       sum(employees_laid_off)                                             AS verified_jobs_cut,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY employees_laid_off)     AS median_cut,
       round(100.0 * count(employees_laid_off) / count(*), 1)              AS headcount_coverage_pct,
       round(100.0 * count(*) / sum(count(*)) OVER (), 1)                  AS share_of_events_pct
FROM core.v_global_events
GROUP BY region
ORDER BY events DESC, region;
