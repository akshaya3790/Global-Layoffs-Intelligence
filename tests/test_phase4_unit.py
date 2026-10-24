"""Phase 4 unit tests that need NO database: schema spec vs CSVs and DDL, pre-flight validation of bad
input, configuration and credential handling, and the documentation header of every analytical query."""
from pathlib import Path
import os
import re
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import phase4_spec as spec  # noqa: E402
import phase4_load as loader  # noqa: E402
import phase4_config as config  # noqa: E402
from phase4_checks import canon, dist  # noqa: E402

PROCESSED = ROOT / "data" / "processed"


# ---------------------------------------------------------------- spec and DDL agree with the real files
def test_preflight_accepts_the_verified_processed_files():
    reports = loader.preflight(PROCESSED, check_manifest=True)
    assert {r.file_name for r in reports} == set(spec.FILES)
    assert all(r.matches_manifest for r in reports)
    assert sum(r.csv_rows for r in reports) == 13794
    assert not any(r.warnings for r in reports)          # no 'NULL'/'NaN' text values in the data


def _ddl_columns(path: Path) -> dict[str, list[str]]:
    text = path.read_text()
    tables = {}
    for m in re.finditer(r"CREATE TABLE IF NOT EXISTS \w+\.(\w+) \((.*?)\n\);", text, re.S):
        cols = []
        for line in m.group(2).splitlines():
            line = line.strip()
            word = line.split()[0] if line else ""
            if word and word.upper() not in ("PRIMARY", "UNIQUE", "CHECK", "FOREIGN", "REFERENCES") \
                    and not word.startswith("--"):
                cols.append(word.rstrip(","))
        tables[m.group(1)] = cols
    return tables


@pytest.mark.parametrize("ddl", ["03_staging.sql", "04_core.sql"])
def test_ddl_columns_match_spec(ddl):
    tables = _ddl_columns(ROOT / "sql" / "ddl" / ddl)
    for file_name, (table, cols, _) in spec.FILES.items():
        assert tables[table] == [spec.core_column(file_name, c) for c, _, _ in cols], table


def test_core_ddl_not_null_matches_required_columns():
    text = (ROOT / "sql" / "ddl" / "04_core.sql").read_text()
    body = re.search(r"CREATE TABLE IF NOT EXISTS core\.layoff_events \((.*?)\n\);", text, re.S).group(1)
    for name, _, required in spec.EVENTS:
        line = next(l for l in body.splitlines() if l.strip().startswith(name + " "))
        assert ("NOT NULL" in line or "PRIMARY KEY" in line) == required, name


def test_ddl_never_drops_or_replaces_tables():
    for path in (ROOT / "sql" / "ddl").glob("*.sql"):
        code = "\n".join(l for l in path.read_text().splitlines() if not l.strip().startswith("--")).upper()
        assert "DROP " not in code and "TRUNCATE" not in code and "DELETE " not in code, path.name
        assert "CREATE TABLE " not in code.replace("CREATE TABLE IF NOT EXISTS", ""), path.name


# ---------------------------------------------------------------- pre-flight rejects bad input with clear messages
@pytest.fixture
def work_dir(tmp_path):
    d = tmp_path / "processed"
    shutil.copytree(PROCESSED, d)
    return d


def _edit(path: Path, old: str, new: str, count: int = 1):
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new, count), encoding="utf-8")


def test_changed_file_is_rejected_against_manifest(work_dir):
    _edit(work_dir / "transformation_log.csv", "T01,", "T01,", 1)
    (work_dir / "transformation_log.csv").write_text(
        (work_dir / "transformation_log.csv").read_text() + "\n", encoding="utf-8")
    with pytest.raises(loader.LoadError, match="differs from the verified Phase 2 output"):
        loader.preflight(work_dir, check_manifest=True)


@pytest.mark.parametrize("old,new,message", [
    (",2019-01-04,2019-01-04,", ",2019-01-04,2019-02-30,", "event_date is not date"),
    (",2019-01-04,2019-01-04,2019,", ",2019-01-04,2019-01-04,twenty,", "event_year is not smallint"),
])
def test_bad_types_are_rejected(work_dir, old, new, message):
    _edit(work_dir / "layoff_events.csv", old, new)
    with pytest.raises(loader.LoadError, match=message):
        loader.preflight(work_dir, check_manifest=False)


def test_fractional_integer_is_rejected(work_dir):
    path = work_dir / "transformation_log.csv"
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    header = lines[0].strip().split(",")
    assert header[4] == "rows_changed"
    first = lines[1]
    assert ",224," in first
    lines[1] = first.replace(",224,", ",224.5,", 1)
    path.write_text("".join(lines), encoding="utf-8")
    with pytest.raises(loader.LoadError, match="rows_changed is not int"):
        loader.preflight(work_dir, check_manifest=False)


def test_bad_boolean_and_missing_required_are_rejected(work_dir):
    path = work_dir / "layoff_events.csv"
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    lines[1] = lines[1].rstrip("\n").rsplit(",", 1)[0] + ",yes\n"                 # last column is a qc flag
    lines[2] = "," + lines[2].split(",", 1)[1]                                      # event_key empty
    path.write_text("".join(lines), encoding="utf-8")
    with pytest.raises(loader.LoadError) as exc:
        loader.preflight(work_dir, check_manifest=False)
    assert "qc_industry_cross_source_conflict is not bool" in str(exc.value)
    assert "event_key is required" in str(exc.value)


def test_duplicate_primary_key_is_rejected(work_dir):
    path = work_dir / "quality_issues.csv"
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    path.write_text("".join(lines + [lines[1]]), encoding="utf-8")
    with pytest.raises(loader.LoadError, match="duplicate primary key"):
        loader.preflight(work_dir, check_manifest=False)


def test_header_change_and_missing_file_are_rejected(work_dir):
    _edit(work_dir / "field_lineage.csv", "canonical_field,source_dataset,source_field",
          "canonical_field,source_field,source_dataset")
    (work_dir / "industry_mapping.csv").unlink()
    with pytest.raises(loader.LoadError) as exc:
        loader.preflight(work_dir, check_manifest=False)
    assert "field_lineage.csv: header does not match" in str(exc.value)
    assert "industry_mapping.csv: file not found" in str(exc.value)


def test_wrong_field_count_is_rejected(work_dir):
    path = work_dir / "field_lineage.csv"
    path.write_text(path.read_text(encoding="utf-8") + "a,b\n", encoding="utf-8")
    with pytest.raises(loader.LoadError, match="field count"):
        loader.preflight(work_dir, check_manifest=False)


def test_null_marker_text_is_kept_and_warned(work_dir):
    path = work_dir / "transformation_log.csv"
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    lines.append("T99,X,col,NULL,0,\n")
    path.write_text("".join(lines), encoding="utf-8")
    reports = loader.preflight(work_dir, check_manifest=False)
    warn = [w for r in reports for w in r.warnings]
    assert len(warn) == 1 and "look like a null marker" in warn[0]


@pytest.mark.parametrize("value,typ,ok", [
    ("50.0", "int", True), ("50.5", "int", False), ("-3", "int", True), ("abc", "int", False),
    ("40000", "smallint", False), ("33.333333", "numeric", True), ("inf", "numeric", False),
    ("True", "bool", True), ("true", "bool", False), ("2026-02-28", "date", True), ("2026-2-28", "date", False),
])
def test_type_rules(value, typ, ok):
    assert loader._type_ok(value, typ) is ok


# ---------------------------------------------------------------- comparison helpers used by the checks
def test_canon_and_dist():
    from decimal import Decimal
    assert canon(None) == "NULL" and canon(True) == "true" and canon(Decimal("2788908.0")) == "2788908"
    assert canon(2788908) == "2788908" and canon(Decimal("427.90")) == "427.9" and canon(0) == "0"
    assert dist([("b", 2), ("a", None)]) == "a=NULL; b=2"


# ---------------------------------------------------------------- configuration and credentials
def test_missing_settings_give_a_clear_environment_error(monkeypatch, tmp_path):
    for v in config.REQUIRED_VARS + ["PGPASSWORD"]:
        monkeypatch.delenv(v, raising=False)
    (tmp_path / "data" / "processed").mkdir(parents=True)
    (tmp_path / "sql").mkdir()
    with pytest.raises(config.DatabaseConfigError, match="Missing database settings: PGHOST"):
        config.connect(root=tmp_path)


def test_unreachable_server_gives_a_clear_environment_error(monkeypatch, tmp_path):
    (tmp_path / "data" / "processed").mkdir(parents=True)
    (tmp_path / "sql").mkdir()
    for k, v in {"PGHOST": "127.0.0.1", "PGPORT": "1", "PGDATABASE": "x", "PGUSER": "x", "PGPASSWORD": "x"}.items():
        monkeypatch.setenv(k, v)
    with pytest.raises(config.DatabaseConfigError, match="No PostgreSQL server answered") as exc:
        config.connect(root=tmp_path)
    assert "password" not in str(exc.value).lower().replace("pgpassword", "")


def test_dotenv_does_not_override_existing_variables(monkeypatch, tmp_path):
    monkeypatch.setenv("PGHOST", "from-shell")
    monkeypatch.delenv("PGPORT", raising=False)
    (tmp_path / ".env").write_text("PGHOST=from-file\nPGPORT=5999\n# comment\n")
    loaded = config.load_dotenv(tmp_path / ".env")
    assert os.environ["PGHOST"] == "from-shell" and os.environ["PGPORT"] == "5999" and loaded == ["PGPORT"]


def test_credentials_are_not_in_version_controlled_files():
    ignore = (ROOT / ".gitignore").read_text().splitlines()
    assert ".env" in ignore and "!.env.example" in ignore
    example = (ROOT / ".env.example").read_text()
    assert "PGPASSWORD=change_me" in example
    for path in list((ROOT / "src").glob("phase4_*.py")) + list((ROOT / "sql").rglob("*.sql")):
        assert not re.search(r"password\s*=\s*['\"][^'\"]+['\"]", path.read_text(), re.I), path.name


# ---------------------------------------------------------------- analytical queries are documented
@pytest.mark.parametrize("path", sorted((ROOT / "sql" / "analytics").glob("*.sql")), ids=lambda p: p.name)
def test_every_query_states_its_unit_and_filters(path):
    head = path.read_text()
    for label in ("-- Question", "-- Unit", "-- Reconciles"):
        assert label in head, f"{path.name} lacks {label}"
    assert "-- Filters" in head or "TECH FILE ONLY" in head
    code = "\n".join(l for l in head.splitlines() if not l.strip().startswith("--")).upper()
    for word in ("INSERT ", "UPDATE ", "DELETE ", "DROP ", "TRUNCATE ", "ALTER "):
        assert word not in code, f"{path.name} modifies data"


def test_queries_never_mix_tech_rows_into_global_figures():
    for path in sorted((ROOT / "sql" / "analytics").glob("*.sql")):
        text = path.read_text()
        if "core.layoff_events" in text.replace("core.layoff_event_departments", ""):
            # the only queries reading the combined table must report per source
            assert "GROUP BY e.source_dataset" in text, path.name
