-- 07_us_share_by_year.sql
-- Question  : What share of events with a KNOWN country happened in the United States, per year?
-- Unit      : one row = one year.
-- Filters   : global sample only. Denominator = events with a known country (missing countries are
--             excluded from the base and reported separately, so they do not drag the share down).
-- Caveats   : 2026 is partial.
-- Reconciles: reports/eda/03_07_us_share_by_year.csv.
SELECT event_year,
       count(country)                                                              AS events_known_country,
       count(*) FILTER (WHERE country = 'United States')                           AS us_events,
       round(100.0 * count(*) FILTER (WHERE country = 'United States') / count(country), 1) AS us_share_pct,
       count(*) - count(country)                                                   AS events_missing_country
FROM core.v_global_events
GROUP BY event_year
ORDER BY event_year;
