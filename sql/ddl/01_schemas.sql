-- 01_schemas.sql
-- Three schemas keep the layers apart:
--   staging : exact text copies of the processed CSV files (reloaded on every run, no constraints)
--   core    : typed, constrained analytical tables (what queries and Power BI read)
--   audit   : one row per load run, per file and per validation check (never truncated)
-- Safe to run repeatedly: nothing is dropped or replaced.
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS audit;
