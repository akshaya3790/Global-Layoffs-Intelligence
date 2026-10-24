-- 04_industry_share_by_year.sql
-- Question  : What share of each year's events falls in each industry group?
-- Unit      : one row = one (industry group, year); share_pct = % of THAT YEAR's global events.
-- Filters   : global sample only; 'Unknown' included, so each year's shares add up to 100%.
-- Caveats   : 2026 is partial (Jan to 14 Jun).
-- Reconciles: reports/eda/03_04_industry_share_by_year.csv (wide format there).
SELECT industry_group,
       event_year,
       count(*)                                                                         AS events,
       round(100.0 * count(*) / sum(count(*)) OVER (PARTITION BY event_year), 1)        AS share_pct
FROM core.v_global_events
GROUP BY industry_group, event_year
ORDER BY industry_group, event_year;
