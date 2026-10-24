-- 18_missingness_summary.sql
-- Question  : How complete is each important field, per source?
-- Unit      : one row = one (source, field). missing = NULL rows; missing_pct = missing / rows in source.
-- Filters   : both sources, shown separately. 100% missing means the field does not exist in that source.
-- Reconciles: reports/eda/03_09_missingness_global.csv (source_dataset, column, missing, rows, missing_pct).
SELECT e.source_dataset,
       f.field                                                   AS column_name,
       count(*) FILTER (WHERE f.is_missing)                      AS missing,
       count(*)                                                  AS rows,
       round(100.0 * count(*) FILTER (WHERE f.is_missing) / count(*), 1) AS missing_pct
FROM core.layoff_events e
CROSS JOIN LATERAL (VALUES
    ('employees_laid_off', e.employees_laid_off IS NULL), ('workforce_pct', e.workforce_pct IS NULL),
    ('industry_raw', e.industry_raw IS NULL), ('country', e.country IS NULL), ('hq_country', e.hq_country IS NULL),
    ('city', e.city IS NULL), ('state', e.state IS NULL), ('company_domain', e.company_domain IS NULL),
    ('news_url', e.news_url IS NULL), ('news_excerpt', e.news_excerpt IS NULL),
    ('total_employees', e.total_employees IS NULL), ('reason', e.reason IS NULL),
    ('department', e.department IS NULL), ('severance_weeks', e.severance_weeks IS NULL),
    ('ai_related', e.ai_related IS NULL)
) AS f(field, is_missing)
GROUP BY e.source_dataset, f.field
ORDER BY e.source_dataset, missing_pct DESC, f.field;
