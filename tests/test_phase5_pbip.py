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
            ref = obj.get(kind, {}).get("Expression", {}).get("SourceRef", {}) if isinstance(obj.get(kind), dict) else {}
            if "Entity" in ref:                  # "Source" aliases (inside filter queries) are covered by `field`
                yield kind, ref["Entity"], obj[kind]["Property"]
        for v in obj.values():
            yield from _fields(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _fields(v)


# A TMDL object name is either quoted ('Share of all events in year %', with '' for a literal quote) or a bare
# identifier (Events). Power BI Desktop rewrites names without quotes when it saves, so accept both forms.
_TMDL_NAME = r"('(?:[^']|'')*'|[^\s=']+)"


def _tmdl_name(token):
    return token[1:-1].replace("''", "'") if token.startswith("'") else token


def _parse_tmdl(text):
    """(table, column names, measure names) from one TMDL table file."""
    table = _tmdl_name(re.search(rf"^table {_TMDL_NAME}", text, re.M).group(1))
    cols = {_tmdl_name(m) for m in re.findall(rf"^\tcolumn {_TMDL_NAME}", text, re.M)}
    measures = {_tmdl_name(m) for m in re.findall(rf"^\tmeasure {_TMDL_NAME}", text, re.M)}
    return table, cols, measures


def _model():
    cols, measures = {}, {}
    for f in (MODEL / "tables").glob("*.tmdl"):
        table, c, m = _parse_tmdl(f.read_text(encoding="utf-8"))
        cols[table], measures[table] = c, m
    return cols, measures


def _missing_fields(visuals, cols, measures):
    return [(k, t, n) for v in visuals for k, t, n in _fields(v)
            if n not in (measures if k == "Measure" else cols).get(t, set())]


def _schema_available(uri):
    return (CACHE / uri.split("/definition/", 1)[1].replace("/", "__")).exists()


def test_report_has_enough_files_to_validate():
    assert len(_files()) >= 40


@pytest.mark.parametrize("path", [str(f.relative_to(DEFINITION)) for f in _files()] if DEFINITION.exists() else [])
def test_report_file_matches_microsoft_schema(path):
    """Each report file is validated against the schema version it declares. A version that is not in the
    offline cache (for example visualContainer 2.14.0, which Power BI Desktop writes when it saves but Microsoft
    has not published) is reported as SKIPPED: unverified, not passed."""
    jsonschema = pytest.importorskip("jsonschema")
    referencing = pytest.importorskip("referencing")
    from referencing.jsonschema import DRAFT7
    doc = json.loads((DEFINITION / path).read_text(encoding="utf-8"))
    if not _schema_available(doc["$schema"]):
        pytest.skip(f"unverified: schema {doc['$schema'].split('/definition/', 1)[1]} is not available to the validator")
    registry = referencing.Registry(retrieve=lambda uri: referencing.Resource.from_contents(
        _schema(uri), default_specification=DRAFT7))
    schema = _schema(doc["$schema"])
    validator = jsonschema.validators.validator_for(schema, default=jsonschema.Draft7Validator)(schema, registry=registry)
    assert [e.message[:160] for e in validator.iter_errors(doc)] == []


def test_schema_check_rejects_a_broken_visual():
    jsonschema = pytest.importorskip("jsonschema")
    referencing = pytest.importorskip("referencing")
    from referencing.jsonschema import DRAFT7
    doc = next(v for v in _visuals() if _schema_available(v["$schema"]))
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
    assert sum(len(c) for c in cols.values()) > 50 and sum(len(m) for m in measures.values()) >= 15
    assert _missing_fields(_visuals(), cols, measures) == []


def test_tmdl_parser_reads_quoted_and_unquoted_names():
    text = ("table v_bi_events\n\n"
            "\tmeasure Events = COUNTROWS(v_bi_events)\n"
            "\tmeasure 'Share of all events in year %' = DIVIDE(1, 2)\n"
            "\tmeasure 'It''s quoted' = 1\n"
            "\tcolumn event_year\n"
            "\tcolumn 'industry_group'\n"
            "\tcolumn months = km_curve[t] / 30.44\n")
    table, cols, measures = _parse_tmdl(text)
    assert table == "v_bi_events"
    assert cols == {"event_year", "industry_group", "months"}
    assert measures == {"Events", "Share of all events in year %", "It's quoted"}
    assert _parse_tmdl("table 'My table'\n")[0] == "My table"


def test_missing_field_is_still_detected():
    """A visual that points at a column, measure or table the model does not have must fail the binding check."""
    cols, measures = _model()
    ref = lambda kind, table, name: {"field": {kind: {"Expression": {"SourceRef": {"Entity": table}}, "Property": name}}}
    broken = {"visual": {"query": {"queryState": {"Values": {"projections": [
        ref("Column", "v_bi_events", "no_such_column"), ref("Measure", "v_bi_events", "No such measure"),
        ref("Column", "no_such_table", "event_year"), ref("Column", "v_bi_events", "event_year")]}}}}}
    assert _missing_fields([broken], cols, measures) == [("Column", "v_bi_events", "no_such_column"),
                                                         ("Measure", "v_bi_events", "No such measure"),
                                                         ("Column", "no_such_table", "event_year")]


def test_tech_table_only_in_its_own_panel():
    tech_visuals = [v for v in _visuals() if any(t == "v_tech_events" for _, t, _ in _fields(v))]
    assert all({t for _, t, _ in _fields(v)} == {"v_tech_events"} for v in tech_visuals)
    assert len(tech_visuals) == 2                    # the count card and the case-study table on page 4


def test_no_credentials_in_project():
    text = " ".join(f.read_text(encoding="utf-8", errors="ignore")
                    for f in (ROOT / "powerbi").rglob("*") if f.is_file() and f.suffix in {".json", ".tmdl", ".pbir", ".pbism", ".pbip"})
    assert not re.search(r"(?i)password\s*[=:]", text)


def test_page2_has_no_pie_or_year_selector_left():
    """The pie chart, its year selector and its help text were removed on 25 Oct 2026. The selector only ever
    filtered the pie, so page 2 must have no visual interactions left and no slicer at all."""
    page = json.loads((DEFINITION / "pages" / "page2" / "page.json").read_text(encoding="utf-8"))
    types = [json.loads(f.read_text(encoding="utf-8"))["visual"]["visualType"]
             for f in (DEFINITION / "pages" / "page2" / "visuals").glob("*/visual.json")]
    assert "pieChart" not in types and "slicer" not in types
    assert "visualInteractions" not in page
    assert sorted(types) == sorted(["textbox", "textbox", "textbox", "card", "card", "card", "clusteredBarChart",
                                    "lineChart", "tableEx"])


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


def test_industry_share_chart_shows_top5_as_share_of_all_events_in_year():
    """Page 2 line chart: year on the axis, industry as legend, filtered to the five largest known
    industries, valued with a measure whose denominator removes every industry filter (no renormalising)."""
    vs = [json.loads(f.read_text(encoding="utf-8")) for f in (DEFINITION / "pages" / "page2" / "visuals").glob("*/visual.json")]
    c = [v for v in vs if v["visual"]["visualType"] == "lineChart"]
    assert len(c) == 1
    q = c[0]["visual"]["query"]["queryState"]
    assert q["Category"]["projections"][0]["field"]["Column"]["Property"] == "event_year"
    assert q["Series"]["projections"][0]["field"]["Column"]["Property"] == "industry_group"
    assert q["Y"]["projections"][0]["field"]["Measure"]["Property"] == "Share of all events in year %"
    values = [v[0]["Literal"]["Value"].strip("'") for v in
              c[0]["filterConfig"]["filters"][0]["filter"]["Where"][0]["Condition"]["In"]["Values"]]
    assert values == ["Retail & Consumer", "Finance & Fintech", "Healthcare & Life Sciences", "Software & IT",
                      "Food & Agriculture"]
    tmdl = (MODEL / "tables" / "v_bi_events.tmdl").read_text(encoding="utf-8")
    assert "measure 'Share of all events in year %' = DIVIDE([Events], CALCULATE([Events], "            "REMOVEFILTERS(v_bi_events[industry_group])))" in tmdl
    assert c[0]["visual"]["visualContainerObjects"]["title"][0]["properties"]["text"]["expr"]["Literal"]["Value"]         == "'Industry share of events by year'"
