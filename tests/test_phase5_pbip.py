"""Phase 5 tests for the generated Power BI project (powerbi/LayoffsDashboard.*).

* Every report file is valid against Microsoft's published PBIR JSON schemas (cached offline in
  tests/fixtures/pbir_schemas, downloaded from developer.microsoft.com on 24 Oct 2026).
* The report has the four planned pages, each with the sample-coverage banner.
* Every field a visual uses exists in the semantic model (TMDL), so no visual can show a broken binding.
* No global visual reads the separate tech table.
"""
from pathlib import Path
import json
import re

import pytest

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "powerbi" / "LayoffsDashboard.Report"
DEFINITION = REPORT / "definition"
MODEL = ROOT / "powerbi" / "LayoffsDashboard.SemanticModel" / "definition"
CACHE = Path(__file__).resolve().parent / "fixtures" / "pbir_schemas"
PAGES = ["1 Executive overview", "2 Industry and geography", "3 Companies and repeat layoffs",
         "4 Data quality and coverage"]

pytestmark = pytest.mark.skipif(not DEFINITION.exists(), reason="run python src/phase5_build_pbip.py first")


def _schema(uri):
    return json.loads((CACHE / uri.split("/definition/", 1)[1].replace("/", "__")).read_text(encoding="utf-8"))


def _files():
    return sorted(DEFINITION.rglob("*.json"))


def _visuals():
    return [json.loads(f.read_text(encoding="utf-8")) for f in sorted(DEFINITION.glob("pages/*/visuals/*/visual.json"))]


def _fields(obj):
    """Yield (kind, table, name) for every Column/Measure reference inside a visual."""
    if isinstance(obj, dict):
        for kind in ("Column", "Measure"):
            if kind in obj and "SourceRef" in obj[kind].get("Expression", {}):
                yield kind, obj[kind]["Expression"]["SourceRef"]["Entity"], obj[kind]["Property"]
        for v in obj.values():
            yield from _fields(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _fields(v)


def _model():
    cols, measures = {}, {}
    for f in (MODEL / "tables").glob("*.tmdl"):
        text = f.read_text(encoding="utf-8")
        table = re.search(r"^table (\S+)", text, re.M).group(1)
        cols[table] = set(re.findall(r"^\tcolumn '([^']+)'", text, re.M))
        measures[table] = set(re.findall(r"^\tmeasure '([^']+)'", text, re.M))
    return cols, measures


def test_report_files_match_microsoft_schemas():
    jsonschema = pytest.importorskip("jsonschema")
    referencing = pytest.importorskip("referencing")
    from referencing.jsonschema import DRAFT7
    registry = referencing.Registry(retrieve=lambda uri: referencing.Resource.from_contents(
        _schema(uri), default_specification=DRAFT7))
    problems = []
    for f in _files():
        doc = json.loads(f.read_text(encoding="utf-8"))
        schema = _schema(doc["$schema"])
        validator = jsonschema.validators.validator_for(schema, default=jsonschema.Draft7Validator)(schema, registry=registry)
        problems += [f"{f.relative_to(DEFINITION)}: {e.message[:120]}" for e in validator.iter_errors(doc)]
    assert len(_files()) >= 40 and problems == []


def test_schema_check_rejects_a_broken_visual():
    jsonschema = pytest.importorskip("jsonschema")
    referencing = pytest.importorskip("referencing")
    from referencing.jsonschema import DRAFT7
    doc = _visuals()[0]
    doc = {**doc, "notAProperty": 1}
    schema = _schema(doc["$schema"])
    registry = referencing.Registry(retrieve=lambda uri: referencing.Resource.from_contents(
        _schema(uri), default_specification=DRAFT7))
    assert list(jsonschema.Draft7Validator(schema, registry=registry).iter_errors(doc))


def test_four_pages_each_with_coverage_banner():
    meta = json.loads((DEFINITION / "pages" / "pages.json").read_text(encoding="utf-8"))
    names = [json.loads((DEFINITION / "pages" / p / "page.json").read_text(encoding="utf-8"))["displayName"]
             for p in meta["pageOrder"]]
    assert names == PAGES
    for p in meta["pageOrder"]:
        texts = " ".join((v / "visual.json").read_text(encoding="utf-8")
                         for v in (DEFINITION / "pages" / p / "visuals").iterdir())
        assert "26% company sample" in texts and "lower bound" in texts and "2026 covers January to 14 June only" in texts


def test_every_bound_field_exists_in_the_model():
    cols, measures = _model()
    missing = [(k, t, n) for v in _visuals() for k, t, n in _fields(v)
               if n not in (measures if k == "Measure" else cols).get(t, set())]
    assert missing == []


def test_tech_table_only_in_its_own_panel():
    tech_visuals = [v for v in _visuals() if any(t == "v_tech_events" for _, t, _ in _fields(v))]
    assert all({t for _, t, _ in _fields(v)} == {"v_tech_events"} for v in tech_visuals)
    assert len(tech_visuals) == 2                    # the count card and the case-study table on page 4


def test_no_credentials_in_project():
    text = " ".join(f.read_text(encoding="utf-8", errors="ignore")
                    for f in (ROOT / "powerbi").rglob("*") if f.is_file() and f.suffix in {".json", ".tmdl", ".pbir", ".pbism", ".pbip"})
    assert not re.search(r"(?i)password\s*[=:]", text)
