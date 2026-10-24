-- 08_layoff_size_distribution.sql
-- Question  : How big are layoffs, in people?
-- Unit      : one row = one size band; events = global events whose KNOWN headcount falls in the band.
-- Filters   : global sample; only rows with a known headcount (denominator shown). Rows without a
--             headcount are NOT put in any band (they are reported in rows_without_headcount).
-- Reconciles: reports/eda/03_08_size_and_pct_distribution.csv (chart = size_band).
WITH banded AS (
    SELECT CASE WHEN employees_laid_off < 100  THEN 1 WHEN employees_laid_off < 500  THEN 2
                WHEN employees_laid_off < 1000 THEN 3 WHEN employees_laid_off < 5000 THEN 4 ELSE 5 END AS band_order
    FROM core.v_global_events
    WHERE employees_laid_off IS NOT NULL
), bands(band_order, size_band) AS (
    VALUES (1, '1-99'), (2, '100-499'), (3, '500-999'), (4, '1,000-4,999'), (5, '5,000+')
)
SELECT b.size_band,
       count(x.band_order)                                                          AS events,
       round(100.0 * count(x.band_order) / sum(count(x.band_order)) OVER (), 1)     AS share_of_verified_pct,
       (SELECT count(employees_laid_off) FROM core.v_global_events)                 AS denominator_rows_with_headcount,
       (SELECT count(*) - count(employees_laid_off) FROM core.v_global_events)      AS rows_without_headcount
FROM bands b
LEFT JOIN banded x USING (band_order)
GROUP BY b.band_order, b.size_band
ORDER BY b.band_order;
