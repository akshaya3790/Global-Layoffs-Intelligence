"""Phase 5: generate the Power BI project (powerbi/LayoffsDashboard.pbip) from code.

Usage (from the project root):
    python src/phase5_build_pbip.py

Writes a Power BI Project (PBIP) that Power BI Desktop opens like a .pbix:
  * a semantic model (TMDL) importing the verified core.v_bi_* views from PostgreSQL plus the notebook 05
    survival/bootstrap CSVs and the query 19 sensitivity table, with relationships and DAX measures;
  * a 4-page report (Executive overview, Industry and geography, Companies and repeat layoffs,
    Data quality and coverage), each page carrying the sample-coverage banner.
No credentials are written: Power BI asks for the PostgreSQL user and password on the first refresh.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "powerbi"
NAME = "LayoffsDashboard"
BANNER = ("26% company sample of news-reported layoffs (5,000 of 19,208 events). Counts are sample counts. "
          "Job figures are disclosed cuts only (lower bound). 2026 covers January to 14 June only. "
          "Source: Fliar Research (2026), CC BY-NC 4.0.")

# ---------------------------------------------------------------- semantic model
PG = {"text": "string", "date": "dateTime", "smallint": "int64", "integer": "int64", "bigint": "int64",
      "numeric": "double", "double precision": "double", "boolean": "boolean"}

VIEWS = {
    "v_bi_events": [("event_key", "text"), ("company_name", "text"), ("company_domain", "text"), ("event_date", "date"),
                    ("month_start", "date"), ("event_year", "smallint"), ("event_quarter", "smallint"),
                    ("event_month", "smallint"), ("industry_group", "text"), ("industry_raw", "text"),
                    ("country", "text"), ("region", "text"), ("employees_laid_off", "integer"),
                    ("has_disclosed_headcount", "boolean"), ("size_band", "text"), ("workforce_pct", "numeric"),
                    ("is_furlough", "boolean"), ("is_permanent_layoff", "boolean"),
                    ("possible_internal_duplicate", "boolean"), ("has_cross_source_candidate", "boolean"),
                    ("company_name_review_status", "text"), ("reason_category_derived", "text"),
                    ("news_source", "text"), ("news_url", "text"), ("qc_issue_count", "smallint"),
                    ("is_partial_period", "boolean"), ("period_note", "text")],
    "v_bi_company_summary": [("company_name", "text"), ("events", "bigint"), ("is_repeat_company", "boolean"),
                             ("first_event_date", "date"), ("last_event_date", "date"),
                             ("days_to_second_event", "integer"), ("days_observed", "integer"),
                             ("distinct_years", "bigint"), ("events_with_headcount", "bigint"),
                             ("disclosed_jobs_cut", "bigint"), ("first_industry_group", "text"),
                             ("industry_groups", "text"), ("name_needs_review", "boolean")],
    "v_bi_quality": [("dimension", "text"), ("value", "text"), ("events", "bigint"), ("events_with_headcount", "bigint"),
                     ("disclosure_rate_pct", "numeric"), ("events_with_workforce_pct", "bigint"),
                     ("events_unknown_sector", "bigint"), ("unknown_sector_pct", "numeric"),
                     ("events_no_country", "bigint"), ("events_unresolved_country", "bigint"),
                     ("furlough_events", "bigint"), ("possible_internal_duplicates", "bigint")],
    "v_bi_benchmark": [("event_year", "integer"), ("sample_events", "bigint"), ("full_events", "integer"),
                       ("events_ratio", "numeric"), ("sample_disclosed_jobs", "bigint"), ("full_disclosed_jobs", "integer"),
                       ("jobs_ratio", "numeric"), ("nominal_ratio", "numeric"), ("is_partial_period", "boolean")],
    "v_tech_events": [("event_key", "text"), ("company_name", "text"), ("event_date", "date"),
                      ("employees_laid_off", "integer"), ("workforce_pct", "numeric"), ("reason_category_derived", "text"),
                      ("ai_related", "text"), ("qc_suspect_date", "boolean")],
}

# CSV tables: (name, relative path, [(column, tmdl type)])
CSVS = {
    "km_curve": ("reports/stats/km_curve_overall.csv",
                 [("t", "double"), ("at_risk", "int64"), ("events", "int64"), ("survival", "double"),
                  ("lo", "double"), ("hi", "double")]),
    "repeat_by_first_cut": ("reports/stats/repeat_probability_by_first_cut_size.csv",
                            [("group", "string"), ("companies", "int64"), ("repeats_observed", "int64"),
                             ("p_repeat_365d", "double"), ("p_repeat_365d_lo", "double"), ("p_repeat_365d_hi", "double")]),
    "repeat_overall": ("reports/stats/repeat_probability_overall.csv",
                       [("group", "string"), ("companies", "int64"), ("p_repeat_365d", "double"),
                        ("p_repeat_365d_lo", "double"), ("p_repeat_365d_hi", "double"), ("p_repeat_730d", "double")]),
    "bootstrap_yearly": ("reports/stats/bootstrap_yearly.csv",
                         [("event_year", "int64"), ("events", "int64"), ("events_lo", "double"), ("events_hi", "double"),
                          ("disclosed_jobs", "double"), ("disclosed_jobs_lo", "double"), ("disclosed_jobs_hi", "double")]),
    "sensitivity_by_year": ("reports/phase4/query_results/19_sensitivity_by_year.csv",
                            [("event_year", "int64"), ("all_events", "int64"), ("excl_furloughs", "int64"),
                             ("excl_internal_duplicates", "int64"), ("excl_cross_source_duplicate_candidates", "int64"),
                             ("period_note", "string")]),
}

MEASURES = {
    "v_bi_events": [
        ("Events", "COUNTROWS(v_bi_events)", "#,0"),
        ("Companies", "DISTINCTCOUNT(v_bi_events[company_name])", "#,0"),
        ("Events with headcount", "CALCULATE([Events], v_bi_events[has_disclosed_headcount] = TRUE())", "#,0"),
        ("Events headcount unknown", "[Events] - [Events with headcount]", "#,0"),
        ("Disclosed jobs cut (lower bound)", "SUM(v_bi_events[employees_laid_off])", "#,0"),
        ("Median disclosed cut", "MEDIAN(v_bi_events[employees_laid_off])", "#,0"),
        ("Disclosure rate %", "ROUND(DIVIDE([Events with headcount], [Events]) * 100, 1)", "0.0"),
        ("Events 2019 baseline", "CALCULATE([Events], REMOVEFILTERS(v_bi_events[event_year]), v_bi_events[event_year] = 2019)", "#,0"),
        ("Events vs 2019 %", "ROUND(DIVIDE([Events], [Events 2019 baseline]) * 100, 1)", "0.0"),
        ("Unknown sector %",
         "ROUND(DIVIDE(CALCULATE([Events], v_bi_events[industry_group] = \"Unknown\"), [Events]) * 100, 1)", "0.0"),
        ("US share of known-country %",
         "ROUND(DIVIDE(CALCULATE([Events], v_bi_events[country] = \"United States\"), "
         "CALCULATE([Events], v_bi_events[country] <> \"Unknown\")) * 100, 1)", "0.0"),
        ("Share of selected events %",
         "ROUND(DIVIDE([Events], CALCULATE([Events], ALLSELECTED(v_bi_events[industry_group]))) * 100, 1)", "0.0"),
    ],
    "v_bi_company_summary": [
        ("Repeat companies", "CALCULATE(COUNTROWS(v_bi_company_summary), v_bi_company_summary[is_repeat_company] = TRUE())", "#,0"),
        ("Median days to next round", "MEDIAN(v_bi_company_summary[days_to_second_event])", "#,0"),
    ],
    "repeat_overall": [
        ("12-month repeat probability %", "ROUND(MAX(repeat_overall[p_repeat_365d]) * 100, 1)", "0.0"),
    ],
    "km_curve": [
        ("Repeat probability %", "ROUND((1 - MAX(km_curve[survival])) * 100, 1)", "0.0"),
    ],
    "v_tech_events": [
        ("Tech case-study rows", "COUNTROWS(v_tech_events)", "#,0"),
    ],
}


def tmdl_column(name, dtype, source=None, expression=None):
    fmt = {"dateTime": "\n\t\tformatString: Short Date", "int64": "\n\t\tformatString: 0",
           "double": ""}.get(dtype, "")
    head = f"\tcolumn '{name}'" + (f" = {expression}" if expression else "")
    src = "" if expression else f"\n\t\tsourceColumn: {source or name}"
    return f"{head}\n\t\tdataType: {dtype}{fmt}\n\t\tsummarizeBy: none{src}\n"


def tmdl_measures(table):
    out = ""
    for name, expr, fmt in MEASURES.get(table, []):
        out += f"\tmeasure '{name}' = {expr}\n\t\tformatString: {fmt}\n\n"
    return out


def m_block(lines):
    return "\n".join("\t\t\t\t" + ln for ln in lines)


def view_table(view, cols):
    body = f"table {view}\n\n" + tmdl_measures(view)
    for c, t in cols:
        body += tmdl_column(c, PG[t]) + "\n"
    keep = ", ".join(f'"{c}"' for c, _ in cols)
    m = ["let",
         "    Source = PostgreSQL.Database(PgServer, PgDatabase),",
         f'    View = Source{{[Schema = "core", Item = "{view}"]}}[Data],',
         f"    Kept = Table.SelectColumns(View, {{{keep}}})",
         "in",
         "    Kept"]
    body += f"\tpartition {view} = m\n\t\tmode: import\n\t\tsource =\n{m_block(m)}\n"
    return body


def csv_table(name, rel, cols):
    body = f"table {name}\n\n" + tmdl_measures(name)
    for c, t in cols:
        body += tmdl_column(c, t) + "\n"
    if name == "km_curve":
        body += tmdl_column("months", "double", expression="km_curve[t] / 30.44") + "\n"
        body += tmdl_column("p_repeat", "double", expression="1 - km_curve[survival]") + "\n"
    mtype = {"string": "type text", "int64": "Int64.Type", "double": "type number"}
    types = ", ".join(f'{{"{c}", {mtype[t]}}}' for c, t in cols)
    keep = ", ".join(f'"{c}"' for c, _ in cols)
    path = rel.replace("/", "\\")
    m = ["let",
         f'    Source = Csv.Document(File.Contents(ProjectFolder & "\\{path}"), '
         '[Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),',
         "    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),",
         f"    Kept = Table.SelectColumns(Headers, {{{keep}}}),",
         f'    Typed = Table.TransformColumnTypes(Kept, {{{types}}}, "en-US")',
         "in",
         "    Typed"]
    body += f"\tpartition {name} = m\n\t\tmode: import\n\t\tsource =\n{m_block(m)}\n"
    return body


def write_model():
    sm = OUT / f"{NAME}.SemanticModel"
    d = sm / "definition"
    (d / "tables").mkdir(parents=True, exist_ok=True)
    (sm / "definition.pbism").write_text(json.dumps({"version": "4.0", "settings": {}}, indent=2), encoding="utf-8")
    (sm / ".platform").write_text(json.dumps(platform("SemanticModel"), indent=2), encoding="utf-8")
    (d / "database.tmdl").write_text("database\n\tcompatibilityLevel: 1567\n", encoding="utf-8")
    tables = list(VIEWS) + list(CSVS)
    refs = "".join(f"ref table {t}\n" for t in tables)
    (d / "model.tmdl").write_text(
        "model Model\n\tculture: en-US\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n"
        "\tsourceQueryCulture: en-US\n\tdataAccessOptions\n\t\tlegacyRedirects\n\t\treturnErrorValuesAsNull\n\n"
        + refs, encoding="utf-8")
    folder = str(ROOT).replace('"', '""')
    (d / "expressions.tmdl").write_text(
        'expression PgServer = "localhost:5432" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]\n\n'
        'expression PgDatabase = "layoffs_db" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]\n\n'
        f'expression ProjectFolder = "{folder}" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]\n',
        encoding="utf-8")
    (d / "relationships.tmdl").write_text(
        f"relationship {uuid.uuid5(uuid.NAMESPACE_URL, 'events-company')}\n"
        "\tfromColumn: v_bi_events.company_name\n\ttoColumn: v_bi_company_summary.company_name\n", encoding="utf-8")
    for v, cols in VIEWS.items():
        (d / "tables" / f"{v}.tmdl").write_text(view_table(v, cols), encoding="utf-8")
    for n, (rel, cols) in CSVS.items():
        (d / "tables" / f"{n}.tmdl").write_text(csv_table(n, rel, cols), encoding="utf-8")


def platform(kind):
    return {"$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
            "metadata": {"type": kind, "displayName": NAME},
            "config": {"version": "2.0", "logicalId": str(uuid.uuid5(uuid.NAMESPACE_URL, NAME + kind))}}


# ---------------------------------------------------------------- report (PBIR: definition/ folder)
# Schema versions Power BI Desktop reads; every file is validated against these by tests/test_phase5_pbip.py.
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"
V_REPORT, V_PAGE, V_VISUAL, V_PAGES, V_META = "3.0.0", "2.0.0", "2.0.0", "1.0.0", "1.0.0"
BASE_THEME = "CY26SU10"
THEME_DIR = Path(r"C:\Program Files\Microsoft Power BI Desktop\bin\WebView2Resources\minerva\sharedresources\BaseThemes")


def literal(value: str) -> dict:
    return {"expr": {"Literal": {"Value": value}}}


class Page:
    def __init__(self, title, question):
        self.title, self.visuals, self.z, self.interactions = title, [], 0, []
        self.text(0, 0, 1280, 64, BANNER, size="9pt", bold=True, color="#FFFFFF", background="#8a5a00")
        self.text(16, 66, 1248, 40, f"{title}: {question}", size="13pt", bold=True, color="#1b2330")

    def _add(self, x, y, w, h, visual):
        self.z += 1
        name = f"v{len(self.visuals) + 1:02d}" + uuid.uuid5(uuid.NAMESPACE_URL, self.title + str(self.z)).hex[:14]
        self.visuals.append({"$schema": f"{SCHEMA}/visualContainer/{V_VISUAL}/schema.json", "name": name,
                             "position": {"x": x, "y": y, "z": self.z * 1000, "height": h, "width": w,
                                          "tabOrder": self.z * 1000},
                             "visual": visual})
        return name

    def text(self, x, y, w, h, value, size="10pt", bold=False, color="#1b2330", background=None):
        style = {"fontSize": size, "color": color}
        if bold:
            style["fontWeight"] = "bold"
        visual = {"visualType": "textbox", "drillFilterOtherVisuals": True,
                  "objects": {"general": [{"properties": {"paragraphs": [{"textRuns": [{"value": value, "textStyle": style}]}]}}]}}
        if background:
            visual["visualContainerObjects"] = {"background": [{"properties": {
                "show": literal("true"),
                "color": {"solid": {"color": literal(f"'{background}'")}},
                "transparency": literal("0D")}}]}
        return self._add(x, y, w, h, visual)

    def visual(self, vtype, x, y, w, h, roles: dict, title: str | None = None, objects: dict | None = None):
        """roles: {projection role: [("m"|"c"|"sum", table, field), ...]}"""
        state = {}
        for role, fields in roles.items():
            projections = []
            for kind, table, field in fields:
                src = {"Expression": {"SourceRef": {"Entity": table}}, "Property": field}
                if kind == "m":
                    ref, expr, native = f"{table}.{field}", {"Measure": src}, field
                elif kind == "c":
                    ref, expr, native = f"{table}.{field}", {"Column": src}, field
                else:
                    ref, expr = f"Sum({table}.{field})", {"Aggregation": {"Expression": {"Column": src}, "Function": 0}}
                    native = f"Sum of {field}"
                projections.append({"field": expr, "queryRef": ref, "nativeQueryRef": native})
            state[role] = {"projections": projections}
        visual = {"visualType": vtype, "query": {"queryState": state}, "drillFilterOtherVisuals": True}
        if objects:
            visual["objects"] = objects
        if title:
            visual["visualContainerObjects"] = {"title": [{"properties": {
                "show": literal("true"), "text": literal("'" + title.replace("'", "''") + "'")}}]}
        return self._add(x, y, w, h, visual)

    def only_filters(self, source, target):
        """Make `source` (a slicer) filter `target` only: every other visual on the page ignores it."""
        self.interactions += [{"source": source, "target": v["name"], "type": "NoFilter"}
                              for v in self.visuals if v["name"] not in (source, target)]

    def page_json(self, name):
        page = {"$schema": f"{SCHEMA}/page/{V_PAGE}/schema.json", "name": name, "displayName": self.title,
                "displayOption": "FitToPage", "height": 720, "width": 1280}
        if self.interactions:
            page["visualInteractions"] = self.interactions
        return page


def cards(page, items, y=110):
    w = (1248 - 12 * (len(items) - 1)) // len(items)
    for i, (table, measure) in enumerate(items):
        page.visual("card", 16 + i * (w + 12), y, w, 96, {"Values": [("m", table, measure)]})


def build_pages():
    E, C, Q, B = "v_bi_events", "v_bi_company_summary", "v_bi_quality", "v_bi_benchmark"
    p1 = Page("1 Executive overview", "is layoff activity unusual right now?")
    cards(p1, [(E, "Events"), (E, "Events vs 2019 %"), (E, "Companies"), (E, "Median disclosed cut"), (E, "Disclosure rate %")])
    p1.visual("lineChart", 16, 218, 760, 300, {"Category": [("c", E, "month_start")], "Y": [("m", E, "Events")]},
              "Layoff events per month (May-Jun 2026 incomplete)")
    p1.visual("clusteredColumnChart", 788, 218, 476, 300,
              {"Category": [("c", "bootstrap_yearly", "event_year")],
               "Y": [("sum", "bootstrap_yearly", "events_lo"), ("sum", "bootstrap_yearly", "events"),
                     ("sum", "bootstrap_yearly", "events_hi")]},
              "Events per year with 90% bootstrap interval (2026 = Jan-Jun)")
    for i, field in enumerate(["event_year", "region", "industry_group", "is_furlough"]):
        p1.visual("slicer", 16 + i * 315, 530, 303, 170, {"Values": [("c", E, field)]})

    p2 = Page("2 Industry and geography", "where do layoffs concentrate, and what shifted?")
    cards(p2, [(E, "Events"), (E, "Unknown sector %"), (E, "US share of known-country %")])
    p2.visual("clusteredBarChart", 16, 218, 400, 482, {"Category": [("c", E, "industry_group")], "Y": [("m", E, "Events")]},
              "Events by industry group (Unknown = no sector, 31%)")
    p2.visual("hundredPercentStackedColumnChart", 428, 218, 480, 236,
              {"Category": [("c", E, "event_year")], "Series": [("c", E, "industry_group")], "Y": [("m", E, "Events")]},
              "Industry share of events by year")
    # Pie for one year at a time, beside (not instead of) the stacked chart: 17 groups, 6-9 under 3% per year,
    # so comparing years needs the stacked chart. All 17 groups are kept; nothing is merged into "Other".
    year = p2.visual("slicer", 428, 462, 130, 238, {"Values": [("c", E, "event_year")]}, "Year for the pie",
                     objects={"data": [{"properties": {"mode": literal("'Dropdown'")}}],
                              "selection": [{"properties": {"singleSelect": literal("true")}}]})
    pie = p2.visual("pieChart", 566, 462, 342, 238,
                    {"Category": [("c", E, "industry_group")], "Y": [("m", E, "Events")],
                     "Tooltips": [("m", E, "Share of selected events %")]},
                    "Industry share of layoff events, selected year (all years if none picked)",
                    objects={"labels": [{"properties": {"show": literal("true"),
                                                        "labelStyle": literal("'Category, percent of total'")}}],
                             "legend": [{"properties": {"show": literal("false")}}]})
    p2.visual("tableEx", 920, 218, 344, 482, {"Values": [("c", E, "region"), ("c", E, "country"), ("m", E, "Events")]},
              "Events by region and country (9% have no country)")
    p2.only_filters(year, pie)

    p3 = Page("3 Companies and repeat layoffs", "which employers cut repeatedly, and how soon?")
    cards(p3, [(C, "Repeat companies"), (C, "Median days to next round"), ("repeat_overall", "12-month repeat probability %")])
    p3.visual("tableEx", 16, 218, 520, 482,
              {"Values": [("c", C, "company_name"), ("sum", C, "events"), ("c", C, "first_event_date"),
                          ("c", C, "last_event_date"), ("sum", C, "disclosed_jobs_cut")]},
              "Companies and their events (brand names may be split)")
    p3.visual("lineChart", 548, 218, 716, 280, {"Category": [("c", "km_curve", "months")], "Y": [("m", "km_curve", "Repeat probability %")]},
              "Chance of another layoff, months after the first (Kaplan-Meier)")
    p3.visual("clusteredColumnChart", 548, 510, 716, 190,
              {"Category": [("c", "repeat_by_first_cut", "group")],
               "Y": [("sum", "repeat_by_first_cut", "p_repeat_365d_lo"), ("sum", "repeat_by_first_cut", "p_repeat_365d"),
                     ("sum", "repeat_by_first_cut", "p_repeat_365d_hi")]},
              "12-month repeat probability by size of first cut (95% interval)")

    p4 = Page("4 Data quality and coverage", "how far can I trust a number?")
    cards(p4, [(E, "Disclosure rate %"), (E, "Unknown sector %"), (E, "Events headcount unknown"), ("v_tech_events", "Tech case-study rows")])
    p4.visual("lineChart", 16, 218, 620, 240,
              {"Category": [("c", B, "event_year")],
               "Y": [("sum", B, "events_ratio"), ("sum", B, "jobs_ratio"), ("sum", B, "nominal_ratio")]},
              "Sample / full data by year: events track 0.26, disclosed jobs do not")
    p4.visual("clusteredBarChart", 648, 218, 616, 240,
              {"Category": [("c", Q, "value")], "Y": [("sum", Q, "disclosure_rate_pct")]},
              "Headcount disclosure rate % (pick a dimension with the slicer)")
    p4.visual("slicer", 648, 462, 300, 60, {"Values": [("c", Q, "dimension")]})
    p4.visual("tableEx", 16, 470, 620, 230,
              {"Values": [("c", "sensitivity_by_year", "event_year"), ("sum", "sensitivity_by_year", "all_events"),
                          ("sum", "sensitivity_by_year", "excl_furloughs"),
                          ("sum", "sensitivity_by_year", "excl_internal_duplicates")]},
              "Sensitivity: events per year under exclusions (query 19)")
    p4.text(960, 462, 304, 60, "Tech case study (35 rows): unknown source, derived company size, 6 suspect dates. "
                               "Never part of global totals.", size="9pt", bold=True, color="#FFFFFF", background="#c0612b")
    p4.visual("tableEx", 960, 526, 304, 174,
              {"Values": [("c", "v_tech_events", "company_name"), ("c", "v_tech_events", "event_date"),
                          ("sum", "v_tech_events", "employees_laid_off"), ("c", "v_tech_events", "ai_related")]})
    return [p1, p2, p3, p4]


def write_report():
    """PBIR report: definition/{version,report}.json, pages/pages.json, pages/<page>/page.json and
    pages/<page>/visuals/<visual>/visual.json, plus the base theme Power BI expects next to it."""
    import shutil
    rp = OUT / f"{NAME}.Report"
    if (rp / "report.json").exists():          # superseded legacy layout; the caller backs it up first
        (rp / "report.json").unlink()
    if (rp / "definition").exists():
        shutil.rmtree(rp / "definition")
    d = rp / "definition"
    (d / "pages").mkdir(parents=True)
    (rp / "definition.pbir").write_text(json.dumps(
        {"version": "4.0", "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}}}, indent=2), encoding="utf-8")
    (rp / ".platform").write_text(json.dumps(platform("Report"), indent=2), encoding="utf-8")
    dump = lambda path, obj: path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
    dump(d / "version.json", {"$schema": f"{SCHEMA}/versionMetadata/{V_META}/schema.json", "version": "2.0.0"})
    dump(d / "report.json", {
        "$schema": f"{SCHEMA}/report/{V_REPORT}/schema.json",
        "themeCollection": {"baseTheme": {"name": BASE_THEME, "type": "SharedResources",
                                          "reportVersionAtImport": {"visual": V_VISUAL, "report": V_REPORT, "page": V_PAGE}}},
        "resourcePackages": [{"name": "SharedResources", "type": "SharedResources",
                              "items": [{"name": BASE_THEME, "path": f"BaseThemes/{BASE_THEME}.json", "type": "BaseTheme"}]}],
        "settings": {"useStylableVisualContainerHeader": True, "defaultDrillFilterOtherVisuals": True}})
    theme_dst = rp / "StaticResources" / "SharedResources" / "BaseThemes" / f"{BASE_THEME}.json"
    theme_dst.parent.mkdir(parents=True, exist_ok=True)
    if (THEME_DIR / f"{BASE_THEME}.json").exists():
        shutil.copyfile(THEME_DIR / f"{BASE_THEME}.json", theme_dst)
    pages = build_pages()
    names = [f"page{i + 1}" for i in range(len(pages))]
    dump(d / "pages" / "pages.json", {"$schema": f"{SCHEMA}/pagesMetadata/{V_PAGES}/schema.json",
                                      "pageOrder": names, "activePageName": names[0]})
    for name, page in zip(names, pages):
        pd_ = d / "pages" / name
        (pd_ / "visuals").mkdir(parents=True)
        dump(pd_ / "page.json", page.page_json(name))
        for v in page.visuals:
            (pd_ / "visuals" / v["name"]).mkdir()
            dump(pd_ / "visuals" / v["name"] / "visual.json", v)


def main():
    write_model()
    write_report()
    (OUT / f"{NAME}.pbip").write_text(json.dumps(
        {"version": "1.0", "artifacts": [{"report": {"path": f"{NAME}.Report"}}], "settings": {"enableAutoRecovery": True}},
        indent=2), encoding="utf-8")
    print("wrote", (OUT / f"{NAME}.pbip").relative_to(ROOT))


if __name__ == "__main__":
    main()
