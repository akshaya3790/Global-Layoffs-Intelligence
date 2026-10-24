-- 01_monthly_events.sql
-- Question  : How many layoff events happened in each calendar month?
-- Unit      : one row = one month; events = number of global event rows dated in that month.
-- Filters   : global sample only (core.v_global_events, 5,000 rows). ALL rows are counted, including
--             furloughs, duplicate candidates and rows with quality flags. Tech rows are never included.
-- Missing   : a month with no rows would show 0 because this is a COUNT of rows (not a missing value).
--             No month in the data is empty.
-- Caveats   : 2026 is partial (data ends 14 Jun 2026). May and June 2026 look incomplete (possible
--             collection lag) - see period_note; do NOT read them as a real decline.
-- Reconciles: reports/eda/03_01_monthly_events.csv (month, events, events_3m_avg).
WITH bounds AS (
    SELECT date_trunc('month', min(event_date))::date AS first_month,
           date_trunc('month', max(event_date))::date AS last_month
    FROM core.v_global_events
), months AS (
    SELECT generate_series(first_month, last_month, INTERVAL '1 month')::date AS month_start FROM bounds
), counts AS (
    SELECT date_trunc('month', event_date)::date AS month_start, count(*) AS events
    FROM core.v_global_events GROUP BY 1
)
SELECT to_char(m.month_start, 'YYYY-MM')                                   AS month,
       coalesce(c.events, 0)                                               AS events,
       round(avg(coalesce(c.events, 0)) OVER (ORDER BY m.month_start
             ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1)                 AS events_3m_avg,
       p.period_note
FROM months m
LEFT JOIN counts c USING (month_start)
LEFT JOIN core.v_period_notes p USING (month_start)
ORDER BY m.month_start;
