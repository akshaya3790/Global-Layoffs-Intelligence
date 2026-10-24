-- 11_tech_reason_summary.sql
-- LOWER-CONFIDENCE TECH FILE ONLY (35 rows, unknown source). Never combine with global figures.
-- Question  : What reasons are given for the tech-file layoffs?
-- Unit      : one row = one derived reason category (keyword rule A-10 applied to the Reason text).
-- Filters   : core.v_tech_events only.
-- Missing   : reported_laid_off sums reported (unverified) headcounts; NULL if none reported.
-- Reconciles: reports/eda/03_T1_tech_reasons_and_departments.csv (chart = reason).
SELECT reason_category_derived,
       count(*)                      AS events,
       sum(employees_laid_off)       AS reported_laid_off
FROM core.v_tech_events
GROUP BY reason_category_derived
ORDER BY events DESC, reason_category_derived;
