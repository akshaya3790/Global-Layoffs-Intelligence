-- 16_repeat_layoff_distribution.sql
-- Question  : How many companies had 1, 2, 3 or 4+ layoff events - and does that change if possible
--             internal duplicates are set aside?
-- Unit      : one row = one bucket of "events per company"; companies = number of distinct company_name.
-- Filters   : global sample only. Column companies_all counts every row. companies_excl_internal_dups is a
--             what-if that ignores rows flagged possible_internal_duplicate (nothing is deleted).
-- Note      : bucket 0 appears only in the what-if column: companies whose every row is flagged.
-- Reconciles: tests/test_phase4_db.py recomputes this from the CSV with pandas.
WITH per_company AS (
    SELECT company_name,
           count(*)                                                        AS n_all,
           count(*) FILTER (WHERE possible_internal_duplicate IS NOT TRUE) AS n_excl
    FROM core.v_global_events
    GROUP BY company_name
), buckets(bucket_order, events_per_company) AS (
    VALUES (0, '0 (every row flagged)'), (1, '1'), (2, '2'), (3, '3'), (4, '4+')
)
SELECT b.events_per_company,
       (SELECT count(*) FROM per_company WHERE least(n_all, 4) = b.bucket_order)  AS companies_all,
       (SELECT count(*) FROM per_company WHERE least(n_excl, 4) = b.bucket_order) AS companies_excl_internal_dups
FROM buckets b
ORDER BY b.bucket_order;
