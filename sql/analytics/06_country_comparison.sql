-- 06_country_comparison.sql
-- Question  : Which countries have the most events, and which country values are missing or unresolved?
-- Unit      : one row = one event-country value (country is where the layoff happened, not the HQ).
-- Filters   : global sample only; all rows counted.
-- Missing   : NULL country is shown as 'Unknown' (status 'missing'). Values that are not countries are
--             shown unchanged with status 'not a country (flagged)'. Jobs: known headcounts only.
-- Reconciles: reports/eda/03_06_top_countries_outside_us.csv (the 'ok' rows other than the US).
SELECT coalesce(country, 'Unknown')                                        AS country,
       region,
       count(*)                                                            AS events,
       count(employees_laid_off)                                           AS events_with_headcount,
       sum(employees_laid_off)                                             AS verified_jobs_cut,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY employees_laid_off)     AS median_cut,
       round(100.0 * count(employees_laid_off) / count(*), 1)              AS headcount_coverage_pct,
       round(100.0 * count(*) / sum(count(*)) OVER (), 1)                  AS share_of_events_pct,
       CASE WHEN country IS NULL        THEN 'missing'
            WHEN region = 'Unresolved'  THEN 'not a country (flagged)'
            ELSE 'ok' END                                                  AS country_status
FROM core.v_global_events
GROUP BY country, region
ORDER BY events DESC, country;
