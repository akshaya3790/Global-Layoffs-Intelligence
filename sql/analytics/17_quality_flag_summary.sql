-- 17_quality_flag_summary.sql
-- Question  : How many records carry each data-quality flag, per source?
-- Unit      : one row = one (source, flag). flagged = TRUE rows, not_flagged = FALSE rows,
--             not_computed = NULL rows (the check does not apply to that source - NOT the same as FALSE).
-- Filters   : both sources, shown separately (never added together).
-- Reconciles: reports/eda/03_10_quality_flags_global.csv (columns true / not_computed).
SELECT e.source_dataset,
       f.flag,
       count(*) FILTER (WHERE f.val)            AS flagged,
       count(*) FILTER (WHERE NOT f.val)        AS not_flagged,
       count(*) FILTER (WHERE f.val IS NULL)    AS not_computed,
       count(*)                                 AS rows_in_source
FROM core.layoff_events e
CROSS JOIN LATERAL (VALUES
    ('qc_date_unparseable', e.qc_date_unparseable), ('qc_date_outside_expected_range', e.qc_date_outside_expected_range),
    ('qc_date_after_audit_date', e.qc_date_after_audit_date), ('qc_non_numeric_value', e.qc_non_numeric_value),
    ('qc_headcount_not_positive', e.qc_headcount_not_positive), ('qc_pct_out_of_range', e.qc_pct_out_of_range),
    ('qc_headcount_status_conflict', e.qc_headcount_status_conflict), ('qc_headcount_not_verified', e.qc_headcount_not_verified),
    ('qc_missing_sector', e.qc_missing_sector), ('qc_missing_country', e.qc_missing_country),
    ('qc_noisy_company_name', e.qc_noisy_company_name), ('qc_same_company_same_url', e.qc_same_company_same_url),
    ('qc_possible_cross_source_dup', e.qc_possible_cross_source_dup), ('qc_headcount_math_gap_gt10pct', e.qc_headcount_math_gap_gt10pct),
    ('qc_suspect_date', e.qc_suspect_date), ('qc_company_name_needs_review', e.qc_company_name_needs_review),
    ('qc_country_not_a_country', e.qc_country_not_a_country), ('qc_industry_cross_source_conflict', e.qc_industry_cross_source_conflict)
) AS f(flag, val)
GROUP BY e.source_dataset, f.flag
ORDER BY e.source_dataset, f.flag;
