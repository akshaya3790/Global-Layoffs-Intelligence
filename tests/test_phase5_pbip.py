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


def test_pie_counts_events_and_year_slicer_filters_only_the_pie():
    page = json.loads((DEFINITION / "pages" / "page2" / "page.json").read_text(encoding="utf-8"))
    visuals = {v["name"]: v for v in (json.loads(f.read_text(encoding="utf-8"))
                                      for f in (DEFINITION / "pages" / "page2" / "visuals").glob("*/visual.json"))}
    pie = [v for v in visuals.values() if v["visual"]["visualType"] == "pieChart"]
    matrix = [v for v in visuals.values() if v["visual"]["visualType"] == "pivotTable"]
    assert len(pie) == 1 and len(matrix) == 1                        # pie sits beside the year-by-industry matrix
    assert set(_fields(pie[0]["visual"]["query"])) == {("Column", "v_bi_events", "industry_group"),
                                                      ("Measure", "v_bi_events", "Events"),
                                                      ("Measure", "v_bi_events", "Share of selected events %")}
    year = [n for n, v in visuals.items() if v["visual"]["visualType"] == "slicer"
            and ("Column", "v_bi_events", "event_year") in set(_fields(v["visual"]))]
    assert len(year) == 1
    ignored = {i["target"] for i in page["visualInteractions"] if i["source"] == year[0] and i["type"] == "NoFilter"}
    assert ignored == set(visuals) - {year[0], pie[0]["name"]}       # every other visual ignores the year slicer


@pytest.mark.parametrize("page", ["page1", "page2", "page3", "page4"])
def test_visuals_stay_on_the_page_and_do_not_overlap(page):
    boxes = [(f.parent.name, json.loads(f.read_text(encoding="utf-8"))["position"])
             for f in (DEFINITION / "pages" / page / "visuals").glob("*/visual.json")]
    for name, p in boxes:
        assert p["x"] >= 0 and p["y"] >= 0 and p["x"] + p["width"] <= 1280 and p["y"] + p["height"] <= 720, name
    for i, (a, p) in enumerate(boxes):
        for b, q in boxes[i + 1:]:
            assert not (p["x"] < q["x"] + q["width"] and q["x"] < p["x"] + p["width"]
                        and p["y"] < q["y"] + q["height"] and q["y"] < p["y"] + p["height"]), (a, b)


def test_tech_table_is_wide_with_wrapped_headers():
    tables = [json.loads(f.read_text(encoding="utf-8")) for f in (DEFINITION / "pages" / "page4" / "visuals").glob("*/visual.json")]
    tech = [v for v in tables if v["visual"]["visualType"] == "tableEx"
            and {t for _, t, _ in _fields(v["visual"]["query"])} == {"v_tech_events"}]
    assert len(tech) == 1 and tech[0]["position"]["width"] >= 700
    assert tech[0]["visual"]["objects"]["columnHeaders"][0]["properties"]["wordWrap"]["expr"]["Literal"]["Value"] == "true"


@pytest.mark.parametrize("page,csv,key,est,lo,hi", [
    ("page1", "reports/stats/bootstrap_yearly.csv", "event_year", "events", "events_lo", "events_hi"),
    ("page3", "reports/stats/repeat_probability_by_first_cut_size.csv", "group",
     "p_repeat_365d", "p_repeat_365d_lo", "p_repeat_365d_hi"),
])
def test_interval_charts_show_estimate_and_bounds_without_adding_them(page, csv, key, est, lo, hi):
    """The estimate is the column (Y) and the bounds are markers (Y2). Each category has exactly one row in
    the source, so the visual's Sum() returns the stored value itself, and lower <= estimate <= upper."""
    import pandas as pd
    combo = [json.loads(f.read_text(encoding="utf-8")) for f in (DEFINITION / "pages" / page / "visuals").glob("*/visual.json")]
    combo = [v for v in combo if v["visual"]["visualType"] == "lineClusteredColumnComboChart"]
    assert len(combo) == 1
    q = combo[0]["visual"]["query"]["queryState"]
    name = lambda p: p["field"]["Aggregation"]["Expression"]["Column"]["Property"]
    assert [name(p) for p in q["Y"]["projections"]] == [est]
    assert [name(p) for p in q["Y2"]["projections"]] == [lo, hi]
    assert combo[0]["visual"]["objects"]["lineStyles"][0]["properties"]["strokeWidth"]["expr"]["Literal"]["Value"] == "0D"
    src = pd.read_csv(ROOT / csv)
    assert src[key].is_unique
    assert (src[lo] <= src[est]).all() and (src[est] <= src[hi]).all()


def test_industry_heatmap_is_share_of_each_years_events():
    """Page 2 matrix: industry rows x year columns; the value is Events / Events in the same year (the visual's
    "% of column total"), so every year column adds up to 100%, Unknown included."""
    vs = [json.loads(f.read_text(encoding="utf-8")) for f in (DEFINITION / "pages" / "page2" / "visuals").glob("*/visual.json")]
    m = [v for v in vs if v["visual"]["visualType"] == "pivotTable"]
    assert len(m) == 1
    q = m[0]["visual"]["query"]["queryState"]
    assert q["Rows"]["projections"][0]["field"]["Column"]["Property"] == "industry_group"
    assert q["Columns"]["projections"][0]["field"]["Column"]["Property"] == "event_year"
    a = q["Values"]["projections"][0]["field"]["Arithmetic"]
    assert a["Operator"] == 3 and a["Left"]["Measure"]["Property"] == "Events"
    assert a["Right"]["ScopedEval"]["Expression"]["Measure"]["Property"] == "Events"
    assert [s["Column"]["Property"] for s in a["Right"]["ScopedEval"]["Scope"]] == ["event_year"]
    assert m[0]["visual"]["visualContainerObjects"]["title"][0]["properties"]["text"]["expr"]["Literal"]["Value"]         == "'Industry share of events by year'"
