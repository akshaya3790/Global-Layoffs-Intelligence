"""Phase 4: load the verified processed CSVs into PostgreSQL.

Usage (from the project root, after setting up .env - see sql/README.md):
    python src/phase4_load.py

What one run does
  1. PRE-FLIGHT (no database writes): every file exists, its header is exactly as expected, every row has
     the right number of fields, required fields are filled, every value has the expected type, primary
     keys are unique, and the SHA-256 and row count match data/processed/phase2_output_manifest.csv.
     Any problem stops the run with a list of the offending CSV lines.
  2. SCHEMA: applies sql/ddl/*.sql (CREATE ... IF NOT EXISTS only; nothing is dropped) and checks that
     existing core tables have exactly the expected columns. A mismatch stops the run - it never ALTERs.
  3. SAFETY GUARD: refuses to touch core tables that contain rows if no successful load of this pipeline
     is recorded in audit.load_runs (the data would be of unknown origin).
  4. ONE TRANSACTION: empty and reload staging (COPY), check types/keys in staging, replace the contents of
     the core tables (TRUNCATE + INSERT ... SELECT with explicit casts), run the integrity checks.
     COMMIT only if every check passes; otherwise ROLLBACK, so the previously committed data is untouched.
  5. AUDIT: run status, file hashes, row counts and every check result are written to the audit schema on
     a separate connection, so failed runs are recorded too.

Re-running is safe: each successful run replaces the core tables with the same rows (counts never double).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import platform
import sys
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

import psycopg2
from psycopg2 import sql

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase4_spec as spec  # noqa: E402
from phase4_config import connect, find_project_root, DatabaseConfigError  # noqa: E402

LOADER_VERSION = "phase4-1.0"
DDL_FILES = ["01_schemas.sql", "02_audit.sql", "03_staging.sql", "04_core.sql", "05_views.sql", "06_bi_views.sql"]
MAX_EXAMPLES = 5
NULL_LIKE = {"NULL", "null", "NaN", "nan", "None", "NA", "N/A"}


class LoadError(RuntimeError):
    def __init__(self, stage: str, message: str):
        super().__init__(f"[{stage}] {message}")
        self.stage = stage


@dataclass
class FileReport:
    file_name: str
    core_table: str
    sha256: str
    csv_rows: int
    manifest_sha256: str | None = None
    manifest_rows: int | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def matches_manifest(self):
        if self.manifest_sha256 is None:
            return None
        return self.sha256 == self.manifest_sha256 and self.csv_rows == self.manifest_rows


# ---------------------------------------------------------------- 1. pre-flight (pure Python, no database)
def _type_ok(value: str, typ: str) -> bool:
    if typ == "text":
        return True
    if typ in ("int", "smallint"):
        try:
            d = Decimal(value)
        except InvalidOperation:
            return False
        if not d.is_finite() or d != d.to_integral_value():
            return False
        limit = 32767 if typ == "smallint" else 2147483647
        return -limit - 1 <= d <= limit
    if typ == "numeric":
        try:
            return Decimal(value).is_finite()
        except InvalidOperation:
            return False
    if typ == "bool":
        return value in ("True", "False")
    if typ == "date":
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return len(value) == 10
        except ValueError:
            return False
    raise ValueError(f"unknown type code {typ}")


def read_manifest(input_dir: Path) -> dict[str, tuple[int, str]]:
    path = input_dir / spec.MANIFEST_FILE
    if not path.is_file():
        raise LoadError("preflight", f"{spec.MANIFEST_FILE} not found in {input_dir.name}/")
    with path.open(newline="", encoding="utf-8") as f:
        return {r["file"]: (int(r["rows"]), r["sha256"]) for r in csv.DictReader(f)}


def preflight_file(path: Path, file_name: str) -> tuple[FileReport, list[str]]:
    """Validate one CSV. Returns its report and a list of problems (empty = OK)."""
    table, cols, pk = spec.FILES[file_name]
    problems: list[str] = []
    raw = path.read_bytes()
    report = FileReport(file_name, table, hashlib.sha256(raw).hexdigest(), 0)
    reader = csv.reader(io.StringIO(raw.decode("utf-8"), newline=""))
    header = next(reader, None)
    expected = [c for c, _, _ in cols]
    if header != expected:
        missing = [c for c in expected if c not in (header or [])]
        extra = [c for c in (header or []) if c not in expected]
        problems.append(f"{file_name}: header does not match the expected schema "
                        f"(missing {missing or 'none'}, unexpected {extra or 'none'}, order differs: "
                        f"{not missing and not extra})")
        return report, problems
    bad: dict[str, list[str]] = {}
    seen_pk: dict[tuple, int] = {}
    null_like: dict[str, int] = {}
    for line_no, row in enumerate(reader, start=2):
        report.csv_rows += 1
        if len(row) != len(cols):
            bad.setdefault("field count", []).append(f"line {line_no}: {len(row)} fields, expected {len(cols)}")
            continue
        for (name, typ, required), value in zip(cols, row):
            if value == "":
                if required:
                    bad.setdefault(f"{name} is required", []).append(f"line {line_no}")
                continue
            if not _type_ok(value, typ):
                bad.setdefault(f"{name} is not {typ}", []).append(f"line {line_no}: {value[:40]!r}")
            if typ == "text" and value in NULL_LIKE:
                null_like[name] = null_like.get(name, 0) + 1
        key = tuple(row[expected.index(k)] for k in pk)
        if key in seen_pk:
            bad.setdefault(f"duplicate primary key {pk}", []).append(
                f"line {line_no} repeats line {seen_pk[key]}: {key}")
        else:
            seen_pk[key] = line_no
    for what, examples in bad.items():
        problems.append(f"{file_name}: {what} in {len(examples)} row(s), e.g. " +
                        "; ".join(examples[:MAX_EXAMPLES]))
    for name, n in null_like.items():
        report.warnings.append(f"{file_name}: {n} value(s) in {name} look like a null marker "
                               "(e.g. 'NULL'); kept as text, not converted")
    return report, problems


def preflight(input_dir: Path, check_manifest: bool = True) -> list[FileReport]:
    problems: list[str] = []
    reports: list[FileReport] = []
    manifest = read_manifest(input_dir) if check_manifest else {}
    for file_name in spec.FILES:
        path = input_dir / file_name
        if not path.is_file():
            problems.append(f"{file_name}: file not found")
            continue
        report, file_problems = preflight_file(path, file_name)
        problems += file_problems
        if check_manifest:
            if file_name not in manifest:
                problems.append(f"{file_name}: not listed in {spec.MANIFEST_FILE}")
            else:
                report.manifest_rows, report.manifest_sha256 = manifest[file_name]
                if not report.matches_manifest:
                    problems.append(f"{file_name}: differs from the verified Phase 2 output "
                                    f"(sha256 {report.sha256[:12]} vs manifest {report.manifest_sha256[:12]}, "
                                    f"rows {report.csv_rows} vs {report.manifest_rows})")
        reports.append(report)
    if problems:
        raise LoadError("preflight", "input files failed validation; nothing was loaded:\n  - " +
                        "\n  - ".join(problems))
    return reports


# ---------------------------------------------------------------- 2. schema
def apply_ddl(conn, root: Path) -> None:
    with conn, conn.cursor() as cur:
        for name in DDL_FILES:
            cur.execute((root / "sql" / "ddl" / name).read_text(encoding="utf-8"))


def check_encoding(conn) -> None:
    """Company names contain non-ASCII characters (e.g. accents), so the database must store UTF-8."""
    with conn.cursor() as cur:
        cur.execute("SELECT current_setting('server_encoding')")
        enc = cur.fetchone()[0]
    conn.rollback()
    if enc.upper() not in ("UTF8", "UTF-8"):
        raise LoadError("schema", f"database encoding is {enc}, but UTF8 is required (names contain accents). "
                        "Create the database with ENCODING 'UTF8' TEMPLATE template0 (sql/README.md, step 2).")


def check_schema_drift(conn) -> None:
    """Existing core/staging tables must have exactly the expected columns, in order."""
    problems = []
    with conn.cursor() as cur:
        for file_name, (table, cols, _) in spec.FILES.items():
            want = [spec.core_column(file_name, c) for c, _, _ in cols]
            for schema in ("staging", "core"):
                cur.execute("SELECT column_name FROM information_schema.columns "
                            "WHERE table_schema = %s AND table_name = %s ORDER BY ordinal_position",
                            (schema, table))
                have = [r[0] for r in cur.fetchall()]
                if have != want:
                    problems.append(f"{schema}.{table}: columns differ from the expected schema")
    conn.rollback()
    if problems:
        raise LoadError("schema", "existing tables do not match this pipeline's schema; nothing was changed. "
                        "Inspect them (or use a new database) before loading:\n  - " + "\n  - ".join(problems))


def guard_existing_data(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT EXISTS (SELECT 1 FROM core.layoff_events LIMIT 1), "
                    "EXISTS (SELECT 1 FROM audit.load_runs WHERE status = 'succeeded')")
        has_rows, has_success = cur.fetchone()
    conn.rollback()
    if has_rows and not has_success:
        raise LoadError("schema", "core.layoff_events already contains rows that were not loaded by this "
                        "pipeline (no successful run in audit.load_runs). Refusing to replace them.")


# ---------------------------------------------------------------- 3. load
def _cast(column: str, typ: str) -> sql.Composable:
    col = sql.Identifier(column)
    if typ in ("int", "smallint"):
        pg = "integer" if typ == "int" else "smallint"
        return sql.SQL("{}::numeric::" + pg).format(col)          # "50.0" -> 50 (integral checked first)
    if typ == "text":
        return col
    return sql.SQL("{}::" + spec.PG_TYPES[typ].lower()).format(col)


def staging_type_checks(cur) -> list[str]:
    """Second line of defence in the database: count staging values that would not cast cleanly."""
    patterns = {"int": r"^-?[0-9]+(\.0+)?$", "smallint": r"^-?[0-9]+(\.0+)?$",
                "numeric": r"^-?[0-9]+(\.[0-9]+)?$", "bool": r"^(True|False)$", "date": r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$"}
    problems = []
    for file_name, (table, cols, _) in spec.FILES.items():
        for name, typ, required in cols:
            column = spec.core_column(file_name, name)
            parts = []
            if typ in patterns:
                parts.append(sql.SQL("({c} IS NOT NULL AND {c} !~ {p})").format(
                    c=sql.Identifier(column), p=sql.Literal(patterns[typ])))
            if required:
                parts.append(sql.SQL("{c} IS NULL").format(c=sql.Identifier(column)))
            if not parts:
                continue
            cur.execute(sql.SQL("SELECT count(*) FROM staging.{t} WHERE {cond}").format(
                t=sql.Identifier(table), cond=sql.SQL(" OR ").join(parts)))
            n = cur.fetchone()[0]
            if n:
                problems.append(f"staging.{table}.{column}: {n} value(s) missing or not {typ}")
    return problems


def load_staging(cur, input_dir: Path, reports: list[FileReport]) -> dict[str, int]:
    tables = [sql.Identifier("staging", t) for t, _, _ in spec.FILES.values()]
    cur.execute(sql.SQL("TRUNCATE {}").format(sql.SQL(", ").join(tables)))
    counts = {}
    for report in reports:
        table, cols, _ = spec.FILES[report.file_name]
        names = [spec.core_column(report.file_name, c) for c, _, _ in cols]
        copy = sql.SQL("COPY staging.{t} ({c}) FROM STDIN WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')").format(
            t=sql.Identifier(table), c=sql.SQL(", ").join(map(sql.Identifier, names)))
        with (input_dir / report.file_name).open("r", encoding="utf-8", newline="") as f:
            cur.copy_expert(copy.as_string(cur), f)
        cur.execute(sql.SQL("SELECT count(*) FROM staging.{}").format(sql.Identifier(table)))
        counts[report.file_name] = cur.fetchone()[0]
        if counts[report.file_name] != report.csv_rows:
            raise LoadError("staging", f"{report.file_name}: {report.csv_rows} CSV rows but "
                            f"{counts[report.file_name]} staging rows")
    return counts


def load_core(cur) -> dict[str, int]:
    core_tables = ["source_datasets"] + [t for t, _, _ in spec.FILES.values()]
    cur.execute(sql.SQL("TRUNCATE {}").format(
        sql.SQL(", ").join(sql.Identifier("core", t) for t in core_tables)))
    for row in spec.SOURCE_DATASETS:
        cur.execute("INSERT INTO core.source_datasets (source_dataset, source_file, source_confidence, "
                    "description, known_limitations) VALUES (%(source_dataset)s, %(source_file)s, "
                    "%(source_confidence)s, %(description)s, %(known_limitations)s)", row)
    counts = {"source_datasets": len(spec.SOURCE_DATASETS)}
    for file_name, (table, cols, pk) in spec.FILES.items():           # parents before children
        names = [spec.core_column(file_name, c) for c, _, _ in cols]
        select = sql.SQL(", ").join(_cast(n, t) for n, (_, t, _) in zip(names, cols))
        order = sql.SQL(", ").join(sql.Identifier(spec.core_column(file_name, k)) for k in pk)
        cur.execute(sql.SQL("INSERT INTO core.{t} ({c}) SELECT {s} FROM staging.{t} ORDER BY {o}").format(
            t=sql.Identifier(table), c=sql.SQL(", ").join(map(sql.Identifier, names)), s=select, o=order))
        counts[table] = cur.rowcount
    return counts


# ---------------------------------------------------------------- 4. audit (separate, autocommit connection)
def _audit_start(audit_conn, input_dir_rel: str, manifest_checked: bool) -> int:
    with audit_conn.cursor() as cur:
        cur.execute("SELECT current_setting('server_version'), current_user")
        server_version, db_user = cur.fetchone()
        cur.execute("INSERT INTO audit.load_runs (status, loader_version, input_dir, manifest_checked, "
                    "python_version, psycopg2_version, server_version, db_user) "
                    "VALUES ('running', %s, %s, %s, %s, %s, %s, %s) RETURNING run_id",
                    (LOADER_VERSION, input_dir_rel, manifest_checked, platform.python_version(),
                     psycopg2.__version__.split()[0], server_version, db_user))
        return cur.fetchone()[0]


def _audit_finish(audit_conn, run_id, reports, staging_counts, core_counts, checks, error: LoadError | None):
    with audit_conn.cursor() as cur:
        for r in reports:
            cur.execute("INSERT INTO audit.load_files (run_id, file_name, core_table, sha256, manifest_sha256, "
                        "matches_manifest, csv_rows, staging_rows, core_rows) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        (run_id, r.file_name, r.core_table, r.sha256, r.manifest_sha256, r.matches_manifest,
                         r.csv_rows, staging_counts.get(r.file_name),
                         None if error else core_counts.get(r.core_table)))
        for c in checks:
            cur.execute("INSERT INTO audit.validation_results (run_id, check_id, category, description, "
                        "expected, actual, passed) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (run_id, c["check_id"], c["category"], c["description"], c["expected"],
                         c["actual"], c["passed"]))
        cur.execute("UPDATE audit.load_runs SET finished_at = now(), status = %s, error_stage = %s, "
                    "error_message = %s WHERE run_id = %s",
                    ("failed" if error else "succeeded", error.stage if error else None,
                     str(error)[:4000] if error else None, run_id))


# ---------------------------------------------------------------- orchestration
def run_load(input_dir: Path | None = None, dbname: str | None = None, check_manifest: bool = True,
             verbose: bool = True) -> dict:
    """Run the full pipeline. Returns a summary dict; raises LoadError / DatabaseConfigError on failure."""
    import phase4_checks as checks_mod

    root = find_project_root()
    input_dir = (input_dir or root / "data" / "processed").resolve()
    try:
        input_rel = input_dir.relative_to(root).as_posix()
    except ValueError:
        input_rel = f"(outside project)/{input_dir.name}"
    say = print if verbose else (lambda *a, **k: None)

    say(f"1/5 pre-flight: validating {len(spec.FILES)} CSV files in {input_rel}/ ...")
    reports = preflight(input_dir, check_manifest)
    for r in reports:
        for w in r.warnings:
            say("    warning:", w)
    say(f"    OK: {sum(r.csv_rows for r in reports):,} rows, headers/types/keys valid"
        + (", hashes match the Phase 2 manifest" if check_manifest else " (manifest check SKIPPED)"))

    conn = connect(dbname, root)
    audit_conn = connect(dbname, root)
    audit_conn.autocommit = True
    try:
        say("2/5 schema: applying sql/ddl (create-if-not-exists only) ...")
        check_encoding(conn)
        apply_ddl(conn, root)
        check_schema_drift(conn)
        guard_existing_data(conn)
        run_id = _audit_start(audit_conn, input_rel, check_manifest)
        say(f"    OK: load run {run_id} recorded in audit.load_runs")

        staging_counts, core_counts, results, error = {}, {}, [], None
        try:
            with conn.cursor() as cur:
                say("3/5 staging: COPY into staging tables ...")
                staging_counts = load_staging(cur, input_dir, reports)
                problems = staging_type_checks(cur)
                if problems:
                    raise LoadError("staging", "type checks failed:\n  - " + "\n  - ".join(problems))
                say("4/5 core: replacing core tables inside one transaction ...")
                try:
                    core_counts = load_core(cur)
                except psycopg2.Error as exc:
                    raise LoadError("core", f"{exc.pgerror or exc}".strip()) from None
                say("5/5 validation: running integrity and reconciliation checks ...")
                baseline = checks_mod.compute_baseline(input_dir)
                results = checks_mod.run_checks(cur, baseline, staging_counts, reports)
                failed = [c for c in results if not c["passed"]]
                if failed:
                    raise LoadError("validation", f"{len(failed)} of {len(results)} checks failed: " +
                                    "; ".join(f"{c['check_id']} expected {c['expected']} got {c['actual']}"
                                              for c in failed[:MAX_EXAMPLES]))
            conn.commit()
        except LoadError as exc:
            conn.rollback()
            error = exc
        except psycopg2.Error as exc:
            conn.rollback()
            error = LoadError("database", f"{exc.pgerror or exc}".strip())
        _audit_finish(audit_conn, run_id, reports, staging_counts, core_counts, results, error)
        if error:
            say(f"    FAILED and rolled back; previously committed data is unchanged (run {run_id}).")
            raise error
        say(f"    OK: {len(results)} checks passed; committed (run {run_id}).")
        return {"run_id": run_id, "core_counts": core_counts, "staging_counts": staging_counts,
                "checks": results, "files": reports}
    finally:
        conn.close()
        audit_conn.close()


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Load the verified processed CSVs into PostgreSQL.")
    p.add_argument("--input-dir", type=Path, help="folder with the processed CSVs (default data/processed)")
    p.add_argument("--dbname", help="database name (default: PGDATABASE)")
    p.add_argument("--skip-manifest-check", action="store_true",
                   help="TESTS ONLY: load files whose hashes differ from the Phase 2 manifest (recorded in the audit)")
    args = p.parse_args(argv)
    try:
        summary = run_load(args.input_dir, args.dbname, not args.skip_manifest_check)
    except DatabaseConfigError as exc:
        print(f"\nENVIRONMENT PROBLEM (not a pipeline failure):\n{exc}", file=sys.stderr)
        return 2
    except LoadError as exc:
        print(f"\nLOAD FAILED: {exc}", file=sys.stderr)
        return 1
    print("\nRows loaded:")
    for table, n in summary["core_counts"].items():
        print(f"  core.{table:38s} {n:6,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
