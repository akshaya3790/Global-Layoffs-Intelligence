-- 09_workforce_pct_distribution.sql
-- Question  : What share of the workforce do layoffs cut?
-- Unit      : one row = one band of workforce_pct (lower bound included, upper excluded; last band 50-100%).
-- Filters   : global sample; ONLY rows with a known workforce_pct (1,121 of 5,000). Unknown percentages are
--             excluded from the calculation, never treated as 0; the denominator is shown on every row.
-- Reconciles: reports/eda/03_08_size_and_pct_distribution.csv (chart = pct_band).
WITH bands(band_order, workforce_pct_band, lo, hi) AS (
    VALUES (1, '0-5%', 0, 5), (2, '5-10%', 5, 10), (3, '10-20%', 10, 20),
           (4, '20-30%', 20, 30), (5, '30-50%', 30, 50), (6, '50-100%', 50, 100.0001)
)
SELECT b.workforce_pct_band,
       count(e.workforce_pct)                                                          AS events,
       round(100.0 * count(e.workforce_pct) / sum(count(e.workforce_pct)) OVER (), 1)  AS share_of_known_pct,
       (SELECT count(workforce_pct) FROM core.v_global_events)                         AS denominator_rows_with_pct,
       (SELECT count(*) - count(workforce_pct) FROM core.v_global_events)              AS rows_without_pct_excluded
FROM bands b
LEFT JOIN core.v_global_events e ON e.workforce_pct >= b.lo AND e.workforce_pct < b.hi
GROUP BY b.band_order, b.workforce_pct_band
ORDER BY b.band_order;
