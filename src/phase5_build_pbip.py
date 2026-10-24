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

import copy
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
        "\tsourceQueryCulture: en-US\n\tdataAccessOptions\n\t\tlegacyRedirects\n\t\treturnErrorValuesAsNull\n\tannotation __PBI_TimeIntelligenceEnabled = 0\n\n"
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
    for stale in (d / "tables").glob("*.tmdl"):           # e.g. LocalDateTable_* that Desktop adds on save
        if stale.stem not in tables:
            stale.unlink()
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


# Design system (24 Oct 2026 redesign): white canvas, navy text, blue data colours, orange only for warnings.
NAVY, MUTED, BLUE, LIGHT_BLUE, GREY = "#1B2A41", "#5A6577", "#1F5E7A", "#9CC3D5", "#9AA5B5"
WARN_BG, WARN_TEXT, TECH_BG = "#FFF1DC", "#7A3E00", "#C0612B"
THEME_NAME = "LayoffsTheme"
THEME = {
    "name": THEME_NAME,
    "dataColors": ["#1F3A5F", "#2A9D8F", "#E9A23B", "#7B5EA7", "#E07A5F", "#6A994E", "#3D6B99", "#5FB3A8",
                   "#F2C57C", "#A88BC9", "#F0A08B", "#8AB17D", "#B5838D", "#7A9CC6", "#C9B26B", "#4F7F6F"],
    "background": "#FFFFFF", "foreground": NAVY, "tableAccent": BLUE,
    "good": "#21734A", "neutral": "#C0612B", "bad": "#A3322A",
    "textClasses": {"title": {"fontFace": "Segoe UI Semibold", "fontSize": 11, "color": NAVY},
                    "label": {"fontFace": "Segoe UI", "fontSize": 9, "color": MUTED},
                    "callout": {"fontFace": "Segoe UI Semibold", "fontSize": 24, "color": NAVY},
                    "header": {"fontFace": "Segoe UI Semibold", "fontSize": 12, "color": NAVY}},
}
M = 16                      # page margin; every page uses the same grid
CARD_Y, CARD_H = 96, 84
MAIN_Y = 192


def literal(value: str) -> dict:
    return {"expr": {"Literal": {"Value": value}}}


def quoted(text: str) -> dict:
    return literal("'" + text.replace("'", "''") + "'")


class Page:
    def __init__(self, title, question):
        self.title, self.visuals, self.z, self.interactions = title, [], 0, []
        self.text(0, 0, 1280, 44, BANNER, size="9pt", bold=True, color=WARN_TEXT, background=WARN_BG)
        self.text(M, 48, 1248, 40, f"{title}: {question}", size="14pt", bold=True, color=NAVY)

    def _add(self, x, y, w, h, visual):
        self.z += 1
        name = f"v{len(self.visuals) + 1:02d}" + uuid.uuid5(uuid.NAMESPACE_URL, self.title + str(self.z)).hex[:14]
        self.visuals.append({"$schema": f"{SCHEMA}/visualContainer/{V_VISUAL}/schema.json", "name": name,
                             "position": {"x": x, "y": y, "z": self.z * 1000, "height": h, "width": w,
                                          "tabOrder": self.z * 1000},
                             "visual": visual})
        return name

    def text(self, x, y, w, h, value, size="10pt", bold=False, color=NAVY, background=None):
        style = {"fontSize": size, "color": color}
        if bold:
            style["fontWeight"] = "bold"
        visual = {"visualType": "textbox", "drillFilterOtherVisuals": True,
                  "objects": {"general": [{"properties": {"paragraphs": [{"textRuns": [{"value": value, "textStyle": style}]}]}}]}}
        if background:
            visual["visualContainerObjects"] = {"background": [{"properties": {
                "show": literal("true"), "color": {"solid": {"color": literal(f"'{background}'")}},
                "transparency": literal("0D")}}]}
        return self._add(x, y, w, h, visual)

    def visual(self, vtype, x, y, w, h, roles: dict, title: str | None = None, objects: dict | None = None,
               subtitle: str | None = None, sort_by: tuple | None = None):
        """roles: {projection role: [(kind, table, field[, display name[, format]]), ...]}, kind "m"|"c"|"sum".
        Display names and formats change only how a field is labelled in this visual, never its calculation."""
        state = {}
        for role, fields in roles.items():
            projections = []
            for kind, table, field, *extra in fields:
                src = {"Expression": {"SourceRef": {"Entity": table}}, "Property": field if isinstance(field, str) else field[0]}
                if kind == "m":
                    ref, expr, native = f"{table}.{field}", {"Measure": src}, field
                elif kind == "c":
                    ref, expr, native = f"{table}.{field}", {"Column": src}, field
                elif kind == "pct_of_col":          # field = (measure, column that defines the column total)
                    measure, col = field
                    m = {"Measure": {"Expression": {"SourceRef": {"Entity": table}}, "Property": measure}}
                    scope = [{"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": col}}]
                    expr = {"Arithmetic": {"Left": m, "Right": {"ScopedEval": {"Expression": m, "Scope": scope}},
                                           "Operator": 3}}
                    ref, native = f"Divide({table}.{measure}, ScopedEval({table}.{measure}, [{table}.{col}]))", f"%CT {measure}"
                else:
                    ref, expr = f"Sum({table}.{field})", {"Aggregation": {"Expression": {"Column": src}, "Function": 0}}
                    native = f"Sum of {field}"
                proj = {"field": expr, "queryRef": ref, "nativeQueryRef": native}
                if len(extra) > 0 and extra[0]:
                    proj["displayName"] = extra[0]
                if len(extra) > 1 and extra[1]:
                    proj["format"] = extra[1]
                projections.append(proj)
            state[role] = {"projections": projections}
        visual = {"visualType": vtype, "query": {"queryState": state}, "drillFilterOtherVisuals": True}
        if sort_by:                                    # (role, index) of the projection to sort descending
            role, i = sort_by
            visual["query"]["sortDefinition"] = {"sort": [{"field": state[role]["projections"][i]["field"],
                                                           "direction": "Descending"}]}
        if objects:
            visual["objects"] = objects
        vco = {"title": [{"properties": {"show": literal("true" if title else "false"),
                                         **({"text": quoted(title), "fontColor": {"solid": {"color": literal(f"'{NAVY}'")}},
                                             "fontSize": literal("11D"), "bold": literal("true")} if title else {})}}]}
        if subtitle:
            vco["subTitle"] = [{"properties": {"show": literal("true"), "text": quoted(subtitle),
                                               "fontColor": {"solid": {"color": literal(f"'{MUTED}'")}},
                                               "fontSize": literal("9D")}}]
        visual["visualContainerObjects"] = vco
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


def cards(page, items):
    """One aligned row of KPI cards: (table, measure, label)."""
    w = (1248 - 12 * (len(items) - 1)) // len(items)
    for i, (table, measure, label) in enumerate(items):
        page.visual("card", M + i * (w + 12), CARD_Y, w, CARD_H, {"Values": [("m", table, measure, label)]},
                    objects={"labels": [{"properties": {"fontSize": literal("22D"),
                                                        "color": {"solid": {"color": literal(f"'{NAVY}'")}}}}],
                             "categoryLabels": [{"properties": {"fontSize": literal("9D")}}]})


def dropdown(page, x, y, w, h, table, field, label, single=False):
    objects = {"data": [{"properties": {"mode": literal("'Dropdown'")}}],
               "header": [{"properties": {"text": quoted(label), "fontSize": literal("9D")}}]}
    if single:
        objects["selection"] = [{"properties": {"singleSelect": literal("true")}}]
    return page.visual("slicer", x, y, w, h, {"Values": [("c", table, field, label)]}, objects=objects)


def table_objects(widths: dict | None = None):
    obj = {"columnHeaders": [{"properties": {"wordWrap": literal("true"), "fontSize": literal("9D")}}],
           "values": [{"properties": {"fontSize": literal("9D")}}]}
    if widths:
        obj["columnWidth"] = [{"properties": {"value": literal(f"{w}D")}, "selector": {"metadata": ref}}
                              for ref, w in widths.items()]
    return obj


# Interval charts: the estimate is a column; the lower and upper bounds are markers with no connecting line,
# so they read as the ends of an interval, not as extra series to add up.
INTERVAL_LINES = {"lineStyles": [{"properties": {"strokeWidth": literal("0D"), "showMarker": literal("true"),
                                                 "markerSize": literal("6D")}}],
                  "dataPoint": [{"properties": {"fill": {"solid": {"color": literal(f"'{BLUE}'")}}}}]}


def heatmap_objects(table):
    """Matrix formatting: small text, a white-to-teal background scale on the share values, row totals
    (each year = 100%) kept, per-industry total column hidden."""
    m = {"Measure": {"Expression": {"SourceRef": {"Entity": table}}, "Property": "Events"}}
    scope = [{"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": "event_year"}}]
    share = {"Arithmetic": {"Left": m, "Right": {"ScopedEval": {"Expression": m, "Scope": scope}}, "Operator": 3}}
    ref = f"Divide({table}.Events, ScopedEval({table}.Events, [{table}.event_year]))"
    gradient = {"FillRule": {"Input": share, "FillRule": {"linearGradient2": {
        "min": {"color": {"Literal": {"Value": "'#FFFFFF'"}}},
        "max": {"color": {"Literal": {"Value": "'#4A9BB8'"}}},
        "nullColoringStrategy": {"strategy": {"Literal": {"Value": "'asZero'"}}}}}}}
    return {"values": [{"properties": {"fontSize": literal("8D")}},
                       {"properties": {"backColor": {"solid": {"color": {"expr": gradient}}}},
                        "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": ref}}],
            "rowHeaders": [{"properties": {"fontSize": literal("8D")}}],
            "columnHeaders": [{"properties": {"fontSize": literal("8D")}}],
            "subTotals": [{"properties": {"columnSubtotals": literal("false")}}]}


def build_pages():
    E, C, Q, B = "v_bi_events", "v_bi_company_summary", "v_bi_quality", "v_bi_benchmark"
    BY, KM, R1 = "bootstrap_yearly", "km_curve", "repeat_by_first_cut"

    # ---- page 1
    p1 = Page("1 Executive overview", "what is happening in the layoff-event sample, and how has it changed?")
    cards(p1, [(E, "Events", "Layoff events (sample)"), (E, "Events vs 2019 %", "Events vs 2019 (%, pick a year)"),
               (E, "Companies", "Companies affected"), (E, "Median disclosed cut", "Median disclosed cut (people)"),
               (E, "Disclosure rate %", "Events with disclosed headcount (%)")])
    p1.visual("lineChart", M, MAIN_Y, 760, 392,
              {"Category": [("c", E, "month_start", "Month")], "Y": [("m", E, "Events", "Layoff events", "#,0")]},
              "Layoff events per month", subtitle="Sample counts. May–Jun 2026 look incomplete (collection lag), "
                                                   "not a real decline.")
    p1.visual("lineClusteredColumnComboChart", 788, MAIN_Y, 476, 392,
              {"Category": [("c", BY, "event_year", "Year")],
               "Y": [("sum", BY, "events", "Events (sample)", "#,0")],
               "Y2": [("sum", BY, "events_lo", "90% interval: lower", "#,0"),
                      ("sum", BY, "events_hi", "90% interval: upper", "#,0")]},
              "Events per year with 90% interval",
              subtitle="Column = sample count; markers = company-cluster bootstrap interval. 2026 = Jan–Jun. "
                       "Not affected by the slicers.", objects=INTERVAL_LINES)
    for i, (field, label) in enumerate([("event_year", "Year"), ("region", "Region"),
                                        ("industry_group", "Industry group"), ("is_furlough", "Furlough (temporary)?")]):
        dropdown(p1, M + i * 315, 600, 303, 56, E, field, label)
    p1.text(M, 664, 1248, 40, "Counts describe a 26% company sample of news-reported layoffs, not every layoff "
                              "worldwide. Job figures are disclosed cuts only.", size="9pt", color=MUTED)

    # ---- page 2
    p2 = Page("2 Industry and geography", "where do layoff events concentrate, and how did the mix change?")
    cards(p2, [(E, "Events", "Layoff events (sample)"), (E, "Unknown sector %", "Events with unknown industry (%)"),
               (E, "US share of known-country %", "US share of events with a known country (%)")])
    p2.visual("clusteredBarChart", M, MAIN_Y, 400, 460,
              {"Category": [("c", E, "industry_group", "Industry group")], "Y": [("m", E, "Events", "Layoff events", "#,0")]},
              "Layoff events by industry group", subtitle="Event counts, not job cuts.",
              objects={"categoryAxis": [{"properties": {"fontSize": literal("9D"), "maxMarginFactor": literal("40L")}}],
                       "labels": [{"properties": {"show": literal("true"), "labelDisplayUnits": literal("1D")}}]})
    p2.text(M, 656, 400, 48, "Unknown = the source does not identify the industry. It is not zero layoffs; "
                             "it is shown so shares are not overstated.", size="9pt", color=MUTED)
    # Heatmap matrix (replaced the 100% stacked column on 25 Oct 2026): industry rows x year columns, each cell
    # = that industry's share of the year's events ("% of column total", computed in the visual, no new DAX).
    share = ("pct_of_col", E, ("Events", "event_year"), "Share of the year's events", "0.0%")
    p2.visual("pivotTable", 428, MAIN_Y, 480, 248,
              {"Rows": [("c", E, "industry_group", "Industry group")], "Columns": [("c", E, "event_year", "Year")],
               "Values": [share]},
              "Industry share of events by year", subtitle="Each column = 100% of that year's events.",
              objects=heatmap_objects(E))
    # Pie for one year at a time, beside (not instead of) the stacked chart: 17 groups, 6-9 under 3% per year,
    # so comparing years needs the stacked chart. All 17 groups are kept; nothing is merged into "Other".
    year = dropdown(p2, 428, 448, 150, 56, E, "event_year", "Year for the pie", single=True)
    p2.text(428, 508, 150, 196, "Pick one year to see its industry mix (all years if none is picked). "
                                "Hover a slice for its industry, event count and share.", size="9pt", color=MUTED)
    pie = p2.visual("pieChart", 586, 448, 322, 256,
                    {"Category": [("c", E, "industry_group", "Industry group")],
                     "Y": [("m", E, "Events", "Layoff events", "#,0")],
                     "Tooltips": [("m", E, "Share of selected events %", "Share of selected year (%)", "0.0")]},
                    "Industry share, selected year",
                    objects={"labels": [{"properties": {"show": literal("true"),
                                                        "labelStyle": literal("'Percent of total'"),
                                                        "fontSize": literal("8D")}}],
                             "legend": [{"properties": {"show": literal("false")}}]})
    p2.visual("tableEx", 920, MAIN_Y, 344, 512,
              {"Values": [("c", E, "region", "Region"), ("c", E, "country", "Country"),
                          ("m", E, "Events", "Events", "#,0")]},
              "Events by region and country", subtitle="Unknown = no country given (9% of events).",
              objects=table_objects({"v_bi_events.region": 105, "v_bi_events.country": 130, "v_bi_events.Events": 70}))
    p2.only_filters(year, pie)

    # ---- page 3
    p3 = Page("3 Companies and repeat layoffs", "which employers cut repeatedly, and how soon?")
    cards(p3, [(C, "Repeat companies", "Companies with 2+ events"),
               (C, "Median days to next round", "Median days to 2nd event (repeaters)"),
               ("repeat_overall", "12-month repeat probability %", "Another layoff within 12 months (%)")])
    p3.visual("tableEx", M, MAIN_Y, 560, 512,
              {"Values": [("c", C, "company_name", "Company"), ("sum", C, "events", "Events", "#,0"),
                          ("c", C, "first_event_date", "First event", "dd MMM yyyy"),
                          ("c", C, "last_event_date", "Last event", "dd MMM yyyy"),
                          ("sum", C, "disclosed_jobs_cut", "Disclosed jobs cut (lower bound)", "#,0")]},
              "Companies and their events (most events first)", subtitle="Brand names may be split across spellings.",
              sort_by=("Values", 1),
              objects=table_objects({"v_bi_company_summary.company_name": 170, "Sum(v_bi_company_summary.events)": 60,
                                     "v_bi_company_summary.first_event_date": 92,
                                     "v_bi_company_summary.last_event_date": 92,
                                     "Sum(v_bi_company_summary.disclosed_jobs_cut)": 110}))
    p3.visual("lineChart", 588, MAIN_Y, 676, 300,
              {"Category": [("c", KM, "months", "Months since first layoff in the sample")],
               "Y": [("sum", KM, "p_repeat", "Had another layoff", "0%")]},
              "Chance of another layoff after the first (Kaplan-Meier)",
              subtitle="Share of sampled companies with a 2nd layoff within N months. Companies with no 2nd event by "
                       "14 Jun 2026 count as censored, not 'never'. Association only, not a prediction.")
    p3.visual("lineClusteredColumnComboChart", 588, 504, 676, 200,
              {"Category": [("c", R1, "group", "Size of first cut")],
               "Y": [("sum", R1, "p_repeat_365d", "Repeat within 12 months", "0.0%")],
               "Y2": [("sum", R1, "p_repeat_365d_lo", "95% interval: lower", "0.0%"),
                      ("sum", R1, "p_repeat_365d_hi", "95% interval: upper", "0.0%")]},
              "12-month repeat probability by size of first cut",
              subtitle="Column = Kaplan-Meier estimate; markers = 95% interval.", objects=INTERVAL_LINES)

    # ---- page 4
    p4 = Page("4 Data quality and coverage", "how far can each number be trusted?")
    cards(p4, [(E, "Disclosure rate %", "Events with disclosed headcount (%)"),
               (E, "Unknown sector %", "Events with unknown industry (%)"),
               (E, "Events headcount unknown", "Events with undisclosed headcount"),
               ("v_tech_events", "Tech case-study rows", "Tech case-study rows (separate)")])
    p4.visual("lineChart", M, MAIN_Y, 620, 252,
              {"Category": [("c", B, "event_year", "Year")],
               "Y": [("sum", B, "events_ratio", "Events: sample ÷ full", "0.000"),
                     ("sum", B, "jobs_ratio", "Disclosed jobs: sample ÷ full", "0.000"),
                     ("sum", B, "nominal_ratio", "Expected 0.260 (5,000 ÷ 19,208)", "0.000")]},
              "Sample coverage vs the full data, by year",
              subtitle="Events track 0.26; disclosed job totals swing, so they are lower bounds for the sample only. "
                       "Source: Fliar data card.")
    p4.visual("clusteredBarChart", 648, MAIN_Y, 616, 204,
              {"Category": [("c", Q, "value", "Group")],
               "Y": [("sum", Q, "disclosure_rate_pct", "Headcount disclosure rate (%)", "0.0")]},
              "Headcount disclosure rate by group", subtitle="Share of events that state a headcount. "
                                                             "Choose year, region or industry below.",
              objects={"labels": [{"properties": {"show": literal("true")}}]})
    dropdown(p4, 648, 400, 616, 44, Q, "dimension", "Group by")
    p4.visual("tableEx", M, 456, 470, 248,
              {"Values": [("c", "sensitivity_by_year", "event_year", "Year"),
                          ("sum", "sensitivity_by_year", "all_events", "All events", "#,0"),
                          ("sum", "sensitivity_by_year", "excl_furloughs", "Without furloughs", "#,0"),
                          ("sum", "sensitivity_by_year", "excl_internal_duplicates", "Without possible duplicates", "#,0")]},
              "Sensitivity: events per year under exclusions (query 19)",
              objects=table_objects({"sensitivity_by_year.event_year": 60, "Sum(sensitivity_by_year.all_events)": 110,
                                     "Sum(sensitivity_by_year.excl_furloughs)": 130,
                                     "Sum(sensitivity_by_year.excl_internal_duplicates)": 150}))
    # The tech case-study table gets the full width right of the sensitivity table, under its warning card.
    p4.text(498, 456, 766, 52, "SEPARATE TECH CASE STUDY (35 rows). Source and licence unknown; company size is "
                               "derived from its own percentage; 6 dates look wrong. Never included in global totals.",
            size="9pt", bold=True, color="#FFFFFF", background=TECH_BG)
    p4.visual("tableEx", 498, 512, 766, 192,
              {"Values": [("c", "v_tech_events", "company_name", "Company"),
                          ("c", "v_tech_events", "event_date", "Date", "dd MMM yyyy"),
                          ("sum", "v_tech_events", "employees_laid_off", "Reported laid off", "#,0"),
                          ("c", "v_tech_events", "ai_related", "AI-related (source label)")]},
              objects=table_objects({"v_tech_events.company_name": 260, "v_tech_events.event_date": 130,
                                     "Sum(v_tech_events.employees_laid_off)": 160, "v_tech_events.ai_related": 170}))
    return [p1, p2, p3, p4]


# ---------------------------------------------------------------- colour pass (25 Oct 2026, colours only)
# Applied after the pages are built: it only adds or replaces colour properties (fills, font colours,
# backgrounds). Palette: navy, teal, amber, purple, coral, muted green, with lighter variants; orange stays
# reserved for warnings and the tech case study.
PALETTE = {"navy": "#1F3A5F", "teal": "#2A9D8F", "amber": "#E9A23B", "purple": "#7B5EA7", "coral": "#E07A5F",
           "green": "#6A994E", "grey": "#9AA5B5"}
# KPI cards: (background tint, number colour) per metric family, the same on every page.
CARD_COLOURS = {
    "Events": ("#E8EEF6", "#1F3A5F"), "Events vs 2019 %": ("#F1ECF8", "#5A3E8A"),
    "Companies": ("#E5F4F2", "#1D6F66"), "Median disclosed cut": ("#FCF2E1", "#8A5A00"),
    "Disclosure rate %": ("#ECF4E7", "#45692F"), "Unknown sector %": ("#FBEDE8", "#9A4A33"),
    "US share of known-country %": ("#F1ECF8", "#5A3E8A"), "Repeat companies": ("#E8EEF6", "#1F3A5F"),
    "Median days to next round": ("#E5F4F2", "#1D6F66"), "12-month repeat probability %": ("#F1ECF8", "#5A3E8A"),
    "Events headcount unknown": ("#FBEDE8", "#9A4A33"), "Tech case-study rows": ("#F8E6DA", "#8A3F1A"),
}
# One colour per industry group, used by every industry chart; Unknown is grey.
INDUSTRY_COLOURS = {
    "Retail & Consumer": "#1F3A5F", "Finance & Fintech": "#2A9D8F", "Healthcare & Life Sciences": "#7B5EA7",
    "Software & IT": "#E9A23B", "Food & Agriculture": "#6A994E", "Media & Gaming": "#E07A5F",
    "Industrial & Manufacturing": "#3D6B99", "Energy & Resources": "#8AB17D", "Automotive": "#B5838D",
    "Business Services": "#5FB3A8", "Travel & Transport": "#F2C57C", "Real Estate & Construction": "#A88BC9",
    "Telecom": "#F0A08B", "Technology (mixed)": "#7A9CC6", "Education & Public Sector": "#C9B26B",
    "Hardware & Semiconductors": "#4F7F6F", "Unknown": "#B8BEC7",
}
# Series colours by query reference (lines, interval estimates and bounds).
SERIES_COLOURS = {
    "v_bi_events.Events": PALETTE["navy"],                                  # p1 monthly line
    "Sum(bootstrap_yearly.events)": PALETTE["teal"],                       # p1 estimate column
    "Sum(bootstrap_yearly.events_lo)": PALETTE["amber"], "Sum(bootstrap_yearly.events_hi)": PALETTE["coral"],
    "Sum(km_curve.p_repeat)": PALETTE["purple"],                           # p3 Kaplan-Meier curve
    "Sum(repeat_by_first_cut.p_repeat_365d)": PALETTE["teal"],
    "Sum(repeat_by_first_cut.p_repeat_365d_lo)": PALETTE["amber"], "Sum(repeat_by_first_cut.p_repeat_365d_hi)": PALETTE["coral"],
    "Sum(v_bi_benchmark.events_ratio)": PALETTE["teal"], "Sum(v_bi_benchmark.jobs_ratio)": PALETTE["coral"],
    "Sum(v_bi_benchmark.nominal_ratio)": PALETTE["grey"],
    "Sum(v_bi_quality.disclosure_rate_pct)": PALETTE["green"],
}


def solid(hex_colour: str) -> dict:
    return {"solid": {"color": literal(f"'{hex_colour}'")}}


def _industry_points(entity="v_bi_events", column="industry_group"):
    col = {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": column}}
    return [{"properties": {"fill": solid(c)},
             "selector": {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": col,
                                                               "Right": {"Literal": {"Value": f"'{name}'"}}}}}]}}
            for name, c in INDUSTRY_COLOURS.items()]


def apply_colours(pages):
    for page in pages:
        for v in page.visuals:
            vis = v["visual"]
            if "query" not in vis:
                continue
            state = vis["query"]["queryState"]
            refs = [p["queryRef"] for role in state.values() for p in role["projections"]]
            fields = {p["field"].get("Column", {}).get("Property") for role in state.values() for p in role["projections"]}
            obj = vis["objects"] = copy.deepcopy(vis.get("objects", {}))   # INTERVAL_LINES is shared
            if vis["visualType"] == "card":
                measure = state["Values"]["projections"][0]["field"]["Measure"]["Property"]
                bg, fg = CARD_COLOURS[measure]
                obj["labels"][0]["properties"]["color"] = solid(fg)
                obj["categoryLabels"][0]["properties"]["color"] = solid(fg)
                vis.setdefault("visualContainerObjects", {})["background"] = [{"properties": {
                    "show": literal("true"), "color": solid(bg), "transparency": literal("0D")}}]
            elif "industry_group" in fields and vis["visualType"] in ("clusteredBarChart", "pieChart",
                                                                      "hundredPercentStackedColumnChart"):
                obj["dataPoint"] = _industry_points()
            elif vis["visualType"] in ("lineChart", "lineClusteredColumnComboChart", "clusteredBarChart"):
                obj["dataPoint"] = [{"properties": {"fill": solid(SERIES_COLOURS[r])}, "selector": {"metadata": r}}
                                    for r in refs if r in SERIES_COLOURS]


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
                                          "reportVersionAtImport": {"visual": V_VISUAL, "report": V_REPORT, "page": V_PAGE}},
                            "customTheme": {"name": f"{THEME_NAME}.json", "type": "RegisteredResources",
                                            "reportVersionAtImport": {"visual": V_VISUAL, "report": V_REPORT, "page": V_PAGE}}},
        "resourcePackages": [{"name": "SharedResources", "type": "SharedResources",
                              "items": [{"name": BASE_THEME, "path": f"BaseThemes/{BASE_THEME}.json", "type": "BaseTheme"}]},
                             {"name": "RegisteredResources", "type": "RegisteredResources",
                              "items": [{"name": f"{THEME_NAME}.json", "path": f"{THEME_NAME}.json", "type": "CustomTheme"}]}],
        "settings": {"useStylableVisualContainerHeader": True, "defaultDrillFilterOtherVisuals": True}})
    theme_dst = rp / "StaticResources" / "SharedResources" / "BaseThemes" / f"{BASE_THEME}.json"
    theme_dst.parent.mkdir(parents=True, exist_ok=True)
    if (THEME_DIR / f"{BASE_THEME}.json").exists():
        shutil.copyfile(THEME_DIR / f"{BASE_THEME}.json", theme_dst)
    custom = rp / "StaticResources" / "RegisteredResources" / f"{THEME_NAME}.json"
    custom.parent.mkdir(parents=True, exist_ok=True)
    dump(custom, THEME)
    pages = build_pages()
    apply_colours(pages)
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
