-- 10_workforce_pct_by_year.sql
-- Question  : How large are layoffs as a share of the workforce, per year?
-- Unit      : one row = one year (global sample).
-- Filters   : statistics use ONLY rows with a known workforce_pct; rows_with_pct is the denominator and
--             rows_without_pct shows how many were excluded. Missing is never treated as 0.
-- Caveats   : coverage is low (about 22% overall); 2026 is partial.
-- Reconciles: overall median 15 and n = 1,121 (Phase 3 notebook, section 6).
SELECT event_year,
       count(workforce_pct)                                                AS rows_with_pct,
       count(*) - count(workforce_pct)                                     AS rows_without_pct,
       round(100.0 * count(workforce_pct) / count(*), 1)                   AS pct_coverage_pct,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY workforce_pct)          AS median_workforce_pct,
       round(avg(workforce_pct), 1)                                        AS mean_workforce_pct,
       min(workforce_pct)                                                  AS min_workforce_pct,
       max(workforce_pct)                                                  AS max_workforce_pct
FROM core.v_global_events
GROUP BY ROLLUP (event_year)
ORDER BY event_year NULLS LAST;     -- the last row (event_year NULL) is the all-years total
