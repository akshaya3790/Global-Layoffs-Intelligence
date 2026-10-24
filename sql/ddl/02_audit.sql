-- 02_audit.sql
-- Load audit trail. Rows are only ever INSERTed or UPDATEd (status/finish time); the loader never deletes them.
-- A failed load still leaves its run, file and check rows here, because they are written on a separate
-- connection from the load transaction that is rolled back.

CREATE TABLE IF NOT EXISTS audit.load_runs (
    run_id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    started_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at       TIMESTAMPTZ,
    status            TEXT        NOT NULL CHECK (status IN ('running', 'succeeded', 'failed')),
    loader_version    TEXT        NOT NULL,
    input_dir         TEXT        NOT NULL,   -- relative to the project root, never an absolute path
    manifest_checked  BOOLEAN     NOT NULL,   -- FALSE only when a test deliberately skips the hash check
    python_version    TEXT,
    psycopg2_version  TEXT,
    server_version    TEXT,
    db_user           TEXT,
    error_stage       TEXT,                   -- preflight / staging / core / validation
    error_message     TEXT
);

CREATE TABLE IF NOT EXISTS audit.load_files (
    run_id            BIGINT  NOT NULL REFERENCES audit.load_runs (run_id),
    file_name         TEXT    NOT NULL,
    core_table        TEXT    NOT NULL,
    sha256            TEXT    NOT NULL,
    manifest_sha256   TEXT,
    matches_manifest  BOOLEAN,
    csv_rows          INTEGER NOT NULL,
    staging_rows      INTEGER,
    core_rows         INTEGER,
    PRIMARY KEY (run_id, file_name)
);

CREATE TABLE IF NOT EXISTS audit.validation_results (
    run_id      BIGINT  NOT NULL REFERENCES audit.load_runs (run_id),
    check_id    TEXT    NOT NULL,
    category    TEXT    NOT NULL,
    description TEXT    NOT NULL,
    expected    TEXT,
    actual      TEXT,
    passed      BOOLEAN NOT NULL,
    PRIMARY KEY (run_id, check_id)
);
