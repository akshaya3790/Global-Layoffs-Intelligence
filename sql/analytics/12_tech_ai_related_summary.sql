-- 12_tech_ai_related_summary.sql
-- LOWER-CONFIDENCE TECH FILE ONLY (35 rows, unknown source). Never combine with global figures.
-- Question  : How do events marked AI_Related = Yes / Partial / No compare?
-- Unit      : one row = one AI_Related value, as reported by the file (no stated definition).
-- Filters   : core.v_tech_events only. suspect_dates counts rows flagged qc_suspect_date (6 in total);
--             those rows are kept, with their original dates.
-- Reconciles: reports/eda/03_T2_tech_ai_and_severance.csv (chart = ai_related).
SELECT ai_related,
       count(*)                                                            AS events,
       sum(employees_laid_off)                                             AS reported_laid_off,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY workforce_pct)          AS median_pct_workforce,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY severance_weeks)        AS median_severance_weeks,
       count(*) FILTER (WHERE qc_suspect_date)                             AS suspect_dates
FROM core.v_tech_events
GROUP BY ai_related
ORDER BY array_position(ARRAY['Yes', 'Partial', 'No'], ai_related);
