-- 14_tech_severance_summary.sql
-- LOWER-CONFIDENCE TECH FILE ONLY (35 rows, unknown source). Never combine with global figures.
-- Question  : How many weeks of severance were offered?
-- Unit      : one row = one severance_weeks value; events = tech rows with that value (reported, unverified).
-- Missing   : rows with no severance value would be shown as NULL (there are none in this file).
-- Reconciles: reports/eda/03_T2_tech_ai_and_severance.csv (chart = severance).
SELECT severance_weeks,
       count(*)                      AS events
FROM core.v_tech_events
GROUP BY severance_weeks
ORDER BY severance_weeks;
