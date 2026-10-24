-- 13_tech_department_summary.sql
-- LOWER-CONFIDENCE TECH FILE ONLY (35 rows, unknown source). Never combine with global figures.
-- Question  : Which departments are involved in the tech-file layoffs?
-- Unit      : one row = one department. events_involving = COUNT(DISTINCT event) - an event with two
--             departments counts once for each. weighted_events splits each event equally across its
--             departments (sums to 35). Headcounts are NOT split by department (the source does not say).
-- Reconciles: reports/eda/03_T1_tech_reasons_and_departments.csv (chart = department).
SELECT department,
       count(DISTINCT event_key)     AS events_involving,
       sum(allocation_weight)        AS weighted_events
FROM core.layoff_event_departments
GROUP BY department
ORDER BY events_involving DESC, department;
