from __future__ import annotations

from collections import defaultdict
from typing import Any

import pandas as pd

ISSUE_COLUMNS = ["code", "status", "entity", "record_id", "field", "message"]


def issue(code, entity, record_id, field, message, status="Invalid Input"):
    return {
        "code": code,
        "status": status,
        "entity": entity,
        "record_id": record_id,
        "field": field,
        "message": message,
    }


def _frame(issues: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(issues, columns=ISSUE_COLUMNS)


def validate_raw_structure(raw: dict[str, Any]) -> pd.DataFrame:
    """Validate the JSON shape before any normalization/model construction."""
    issues: list[dict] = []
    if not isinstance(raw, dict):
        return _frame([issue("INVALID_ROOT", "root", None, None, "Dataset root must be a JSON object.")])

    required_top = [
        "metadata", "company", "people", "customers", "shared_resources",
        "work_items", "commercial_options", "portfolio_effects", "enumerations",
    ]
    for key in required_top:
        if key not in raw:
            issues.append(issue("MISSING_ENTITY", key, None, key, "Required entity is missing."))

    # Stop early when an entire required entity is missing; later checks would only create noise.
    if issues:
        return _frame(issues)

    object_specs = {"metadata": dict, "company": dict, "enumerations": dict}
    for key, typ in object_specs.items():
        if not isinstance(raw.get(key), typ):
            issues.append(issue("INVALID_ENTITY_TYPE", key, None, key, f"Entity must be a {typ.__name__}."))

    list_specs = {
        "people": "id", "customers": "id", "shared_resources": "id",
        "work_items": "id", "commercial_options": "option_id", "portfolio_effects": "id",
    }
    required_fields = {
        "people": ["id", "name", "capacity_hours", "hourly_cost_jpy", "skills", "languages", "unavailable_ranges"],
        "customers": ["id", "name", "strategic_value", "payment_reliability", "reference_value", "relationship_risk", "default_payment_days"],
        "shared_resources": ["id", "name", "capacity_hours", "exclusive"],
        "work_items": ["id", "title", "type", "mandatory", "committed", "customer_id", "revenue_jpy", "direct_cost_jpy", "cash_in_days", "success_probability", "required_hours", "earliest_start", "due_date", "strategic_value", "required_skills", "required_languages", "resource_requirements", "dependencies", "conflicts"],
        "commercial_options": ["work_item_id", "option_id", "label", "price_jpy", "direct_cost_jpy", "delivery_hours", "payment_days", "estimated_win_probability", "warranty_months", "follow_on_value_jpy"],
        "portfolio_effects": ["id", "trigger", "targets", "effect"],
    }
    numeric_fields = {
        "people": ["capacity_hours", "hourly_cost_jpy"],
        "customers": ["strategic_value", "payment_reliability", "reference_value", "relationship_risk", "default_payment_days"],
        "shared_resources": ["capacity_hours"],
        "work_items": ["revenue_jpy", "direct_cost_jpy", "success_probability", "required_hours", "late_penalty_jpy_per_day", "strategic_value"],
        "commercial_options": ["price_jpy", "direct_cost_jpy", "delivery_hours", "payment_days", "estimated_win_probability", "warranty_months", "follow_on_value_jpy"],
    }

    for entity, id_field in list_specs.items():
        records = raw.get(entity)
        if not isinstance(records, list):
            issues.append(issue("INVALID_ENTITY_TYPE", entity, None, entity, "Entity must be a list."))
            continue
        for idx, rec in enumerate(records):
            if not isinstance(rec, dict):
                issues.append(issue("INVALID_RECORD", entity, idx, entity, "Record must be an object."))
                continue
            rid = rec.get(id_field, idx)
            for field in required_fields[entity]:
                if field not in rec:
                    issues.append(issue("MISSING_FIELD", entity, rid, field, "Required field is missing."))
            for field in numeric_fields.get(entity, []):
                value = rec.get(field)
                if value is None:
                    continue
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    issues.append(issue("INVALID_TYPE", entity, rid, field, "Field must be numeric."))

    for rec in raw.get("work_items", []):
        if not isinstance(rec, dict):
            continue
        p = rec.get("success_probability")
        if isinstance(p, (int, float)) and not isinstance(p, bool) and not 0 <= p <= 1:
            issues.append(issue("INVALID_RANGE", "work_items", rec.get("id"), "success_probability", "Must be in [0,1]."))
        for field in ("required_hours", "revenue_jpy", "direct_cost_jpy", "strategic_value"):
            value = rec.get(field)
            if isinstance(value, (int, float)) and not isinstance(value, bool) and value < 0:
                issues.append(issue("INVALID_RANGE", "work_items", rec.get("id"), field, "Must be >= 0."))

    for rec in raw.get("commercial_options", []):
        if not isinstance(rec, dict):
            continue
        p = rec.get("estimated_win_probability")
        if isinstance(p, (int, float)) and not isinstance(p, bool) and not 0 <= p <= 1:
            issues.append(issue("INVALID_RANGE", "commercial_options", rec.get("option_id"), "estimated_win_probability", "Must be in [0,1]."))

    return _frame(issues)


def validate_semantics(dm, raw):
    """Validate PK/FK, date ranges, dependencies and basic skill/language coverage."""
    issues: list[dict] = []

    def add(code, status, entity, record_id, message, field=None):
        issues.append(issue(code, entity, record_id, field, message, status))

    key_specs = [
        ("people", "id"), ("customers", "id"), ("shared_resources", "id"),
        ("work_items", "id"), ("commercial_options", "option_id"), ("portfolio_effects", "effect_id"),
    ]
    for table, key in key_specs:
        if key in dm[table].columns:
            dup = dm[table].loc[dm[table][key].duplicated(keep=False), key].dropna().unique()
            for x in dup:
                add("DUPLICATE_PK", "Invalid Input", table, x, "Duplicate primary key.", key)

    ids = {
        "people": set(dm["people"].get("id", pd.Series(dtype=object))),
        "customers": set(dm["customers"].get("id", pd.Series(dtype=object))),
        "resources": set(dm["shared_resources"].get("id", pd.Series(dtype=object))),
        "works": set(dm["work_items"].get("id", pd.Series(dtype=object))),
        "options": set(dm["commercial_options"].get("option_id", pd.Series(dtype=object))),
    }
    for _, r in dm["work_items"].iterrows():
        if pd.notna(r.get("customer_id")) and r.get("customer_id") not in ids["customers"]:
            add("INVALID_FK", "Invalid Input", "work_items", r.get("id"), f"Unknown customer: {r.get('customer_id')}", "customer_id")
        if pd.notna(r.get("earliest_start_dt")) and pd.notna(r.get("due_date_dt")) and r["earliest_start_dt"] > r["due_date_dt"]:
            add("INVALID_DATE_RANGE", "Invalid Input", "work_items", r.get("id"), "earliest_start > due_date")
        if float(r.get("required_hours") or 0) < 0:
            add("INVALID_RANGE", "Invalid Input", "work_items", r.get("id"), "required_hours < 0", "required_hours")

    for _, r in dm["commercial_options"].iterrows():
        if r.get("work_id") not in ids["works"]:
            add("INVALID_FK", "Invalid Input", "commercial_options", r.get("option_id"), f"Unknown work item: {r.get('work_id')}", "work_item_id")

    for _, r in dm["work_resources"].iterrows():
        if r.get("work_id") not in ids["works"]:
            add("INVALID_FK", "Invalid Input", "work_resources", r.get("work_id"), "Unknown work item.", "work_id")
        if r.get("resource_id") not in ids["resources"]:
            add("INVALID_FK", "Invalid Input", "work_resources", r.get("work_id"), f"Unknown resource: {r.get('resource_id')}", "resource_id")

    for _, r in dm["work_dependencies"].iterrows():
        if r.get("work_id") not in ids["works"] or r.get("depends_on_work_id") not in ids["works"]:
            add("INVALID_FK", "Invalid Input", "work_dependencies", r.get("work_id"), f"Unknown prerequisite: {r.get('depends_on_work_id')}", "depends_on_work_id")
    for _, r in dm["work_conflicts"].iterrows():
        if r.get("work_id") not in ids["works"] or r.get("conflicts_with_work_id") not in ids["works"]:
            add("INVALID_FK", "Invalid Input", "work_conflicts", r.get("work_id"), f"Unknown conflict target: {r.get('conflicts_with_work_id')}", "conflicts_with_work_id")
    for _, r in dm["option_dependencies"].iterrows():
        if r.get("option_id") not in ids["options"] or r.get("depends_on_work_id") not in ids["works"]:
            add("INVALID_FK", "Invalid Input", "option_dependencies", r.get("option_id"), f"Unknown prerequisite: {r.get('depends_on_work_id')}", "depends_on_work_id")

    graph = defaultdict(list)
    for _, r in dm["work_dependencies"].iterrows():
        if r.get("work_id") in ids["works"] and r.get("depends_on_work_id") in ids["works"]:
            graph[r["depends_on_work_id"]].append(r["work_id"])
    color, cycle = {w: 0 for w in ids["works"]}, set()

    def dfs(u):
        color[u] = 1
        for v in graph[u]:
            if color[v] == 0:
                dfs(v)
            elif color[v] == 1:
                cycle.update([u, v])
        color[u] = 2

    for w in color:
        if color[w] == 0:
            dfs(w)
    if cycle:
        add("DEPENDENCY_CYCLE", "Invalid Input", "work_dependencies", ",".join(sorted(cycle)), "Dependency cycle detected.")

    skill_map = dm["person_skills"].set_index(["person_id", "skill"])["skill_level"].to_dict() if not dm["person_skills"].empty else {}
    lang_map = dm["person_languages"].groupby("person_id")["language"].apply(set).to_dict() if not dm["person_languages"].empty else {}
    for w in ids["works"]:
        reqs = dm["work_skills"].loc[dm["work_skills"]["work_id"] == w]
        for _, req in reqs.iterrows():
            if not any(skill_map.get((p, req["skill"]), 0) >= int(req["min_level"]) for p in ids["people"]):
                add("NO_SKILL_COVERAGE", "Infeasible", "work_items", w, f"No person satisfies {req['skill']} >= {req['min_level']}")
        for lang in dm["work_languages"].loc[dm["work_languages"]["work_id"] == w, "language"].tolist():
            if not any(lang in lang_map.get(p, set()) for p in ids["people"]):
                add("NO_LANGUAGE_COVERAGE", "Infeasible", "work_items", w, f"No person has language {lang}")
    return _frame(issues)


def diagnose_infeasibility(dm, raw, config) -> pd.DataFrame:
    """Deterministic diagnostics for common blockers when CP-SAT returns INFEASIBLE."""
    issues: list[dict] = []

    def add(code, entity, record_id, message, field=None):
        issues.append(issue(code, entity, record_id, field, message, "Infeasible"))

    people = dm["people"].set_index("person_id") if not dm["people"].empty else pd.DataFrame()
    total_capacity = int(people["capacity_hours"].sum()) if not people.empty else 0
    mandatory = dm["work_items"].loc[dm["work_items"]["mandatory"].fillna(False).astype(bool)]
    mandatory_hours = 0
    for _, w in mandatory.iterrows():
        options = dm["commercial_options"].loc[dm["commercial_options"]["work_id"] == w["work_id"]]
        if not options.empty:
            mandatory_hours += int(options["delivery_hours"].min())
        else:
            mandatory_hours += int(w["required_hours"])
    if mandatory_hours > total_capacity:
        add("MANDATORY_CAPACITY", "people", "TOTAL", f"Mandatory workload {mandatory_hours}h exceeds total people capacity {total_capacity}h.")

    # A mandatory work with no eligible assignee is a stronger explanation than generic INFEASIBLE.
    skill_map = dm["person_skills"].set_index(["person_id", "skill"])["skill_level"].to_dict() if not dm["person_skills"].empty else {}
    lang_map = dm["person_languages"].groupby("person_id")["language"].apply(set).to_dict() if not dm["person_languages"].empty else {}
    for _, w in mandatory.iterrows():
        wid = w["work_id"]
        for _, req in dm["work_skills"].loc[dm["work_skills"]["work_id"] == wid].iterrows():
            if not any(skill_map.get((p, req["skill"]), 0) >= int(req["min_level"]) for p in people.index):
                add("MANDATORY_NO_SKILL", "work_items", wid, f"Mandatory work requires {req['skill']} >= {req['min_level']}, but no eligible person exists.")
        for lang in dm["work_languages"].loc[dm["work_languages"]["work_id"] == wid, "language"].tolist():
            if not any(lang in lang_map.get(p, set()) for p in people.index):
                add("MANDATORY_NO_LANGUAGE", "work_items", wid, f"Mandatory work requires language {lang}, but no eligible person exists.")

    if config.get("cash_hard_constraint"):
        company = dm["company"].iloc[0]
        labor_floor = 0
        for _, w in mandatory.iterrows():
            opts = dm["commercial_options"].loc[dm["commercial_options"]["work_id"] == w["work_id"]]
            hours = int(opts["delivery_hours"].min()) if not opts.empty else int(w["required_hours"])
            labor_floor += hours * int(people["hourly_cost_jpy"].min()) if not people.empty else 0
        conservative_cash = int(company["starting_cash_jpy"] - company["fixed_cash_outflow_jpy"] - labor_floor)
        if conservative_cash < int(company["minimum_cash_buffer_jpy"]):
            add("STRICT_CASH_BLOCKER", "company", "COMPANY", f"Strict cash mode leaves only {conservative_cash:,} JPY before expected receipts, below the {int(company['minimum_cash_buffer_jpy']):,} JPY minimum buffer.")

    return _frame(issues)


def verify_solution(result, dm, raw, config, eng):
    """Check capacity, timing, dependencies, conflicts, resource use and cash after a feasible solve."""
    issues: list[dict] = []

    def add(code, status, entity, record_id, message, field=None):
        issues.append(issue(code, entity, record_id, field, message, status))

    decision = result.get("decision", pd.DataFrame())
    if decision.empty:
        add("NO_SOLUTION", "Infeasible", "solver", None, "No feasible solution returned.")
        return _frame(issues)

    selected = set(decision.loc[decision["selected"], "work_id"])
    assignment = result.get("assignment", pd.DataFrame())
    schedule = result.get("schedule", pd.DataFrame())
    people_idx = dm["people"].set_index("person_id") if not dm["people"].empty else pd.DataFrame()

    for p, g in assignment.groupby("person_id") if not assignment.empty else []:
        if p in people_idx.index and int(g["assigned_hours"].sum()) > int(people_idx.loc[p, "capacity_hours"]):
            add("CAPACITY_OVERLOAD", "Infeasible", "people", p, f"{int(g['assigned_hours'].sum())}h > {int(people_idx.loc[p, 'capacity_hours'])}h")

    works_idx = dm["work_items"].set_index("work_id")
    for _, r in decision.loc[decision["selected"]].iterrows():
        work = works_idx.loc[r["work_id"]]
        if r["end_hour"] > eng.hend(work["due_date_dt"]):
            add("DEADLINE_VIOLATION", "Infeasible", "work_items", r["work_id"], "End time exceeds due date.")
        if r["start_hour"] < eng.hstart(work["earliest_start_dt"]):
            add("EARLIEST_START_VIOLATION", "Infeasible", "work_items", r["work_id"], "Start time before earliest_start.")

    bounds = decision.set_index("work_id")
    if not schedule.empty:
        for _, a in schedule.iterrows():
            b = bounds.loc[a["work_id"]]
            if a["start_hour"] < b["start_hour"] or a["end_hour"] > b["end_hour"]:
                add("ASSIGNMENT_WINDOW_VIOLATION", "Infeasible", "work_items", a["work_id"], "Person interval outside work window.")

    for _, r in dm["work_dependencies"].iterrows():
        if r["work_id"] in selected and r["depends_on_work_id"] not in selected:
            add("DEPENDENCY_VIOLATION", "Infeasible", "work_items", r["work_id"], f"Missing prerequisite {r['depends_on_work_id']}")
    for _, r in dm["work_conflicts"].iterrows():
        if r["work_id"] in selected and r["conflicts_with_work_id"] in selected:
            add("CONFLICT_VIOLATION", "Infeasible", "work_items", r["work_id"], f"Conflicts with {r['conflicts_with_work_id']}")

    usage = dm["work_resources"].loc[dm["work_resources"]["work_id"].isin(selected)].groupby("resource_id")["hours"].sum() if not dm["work_resources"].empty else pd.Series(dtype=float)
    res_idx = dm["shared_resources"].set_index("resource_id")
    for rid, used in usage.items():
        if rid in res_idx.index and used > int(res_idx.loc[rid, "capacity_hours"]):
            add("RESOURCE_OVERLOAD", "Infeasible", "shared_resources", rid, f"{used}h > {int(res_idx.loc[rid, 'capacity_hours'])}h")

    company = dm["company"].iloc[0]
    labor = int(assignment["labor_cost_jpy"].sum()) if not assignment.empty else 0
    horizon_days = (pd.Timestamp(raw["metadata"]["planning_end"]) - pd.Timestamp(raw["metadata"]["planning_start"])).days + 1
    expected_cash = int(company["starting_cash_jpy"] - company["fixed_cash_outflow_jpy"] - labor)
    for _, wrow in dm["work_items"].iterrows():
        if wrow["work_id"] not in selected:
            continue
        if not eng.opts_by_work[wrow["work_id"]]:
            p = float(wrow.get("success_probability") or 0)
            if pd.notna(wrow.get("cash_in_days")) and float(wrow["cash_in_days"]) <= horizon_days:
                expected_cash += int(round(float(wrow.get("revenue_jpy") or 0) * p))
            expected_cash -= int(round(float(wrow.get("direct_cost_jpy") or 0) * p))
    for _, o in result.get("commercial_option", pd.DataFrame()).iterrows():
        p = float(o["estimated_win_probability"])
        expected_cash -= int(round(float(o["direct_cost_jpy"]) * p))
        if float(o["payment_days"]) <= horizon_days:
            expected_cash += int(round(float(o["price_jpy"]) * p))
    for effect in raw.get("portfolio_effects", []):
        if effect.get("trigger") in selected and effect.get("effect", {}).get("type") == "cash_inflow":
            expected_cash += int(round(float(effect["effect"].get("probability") or 0) * float(effect["effect"].get("value_jpy") or 0)))
    if expected_cash < int(company["minimum_cash_buffer_jpy"]):
        add("CASH_SHORTFALL", "Infeasible" if config["cash_hard_constraint"] else "Warning", "company", "COMPANY", f"Expected cash {expected_cash:,} < buffer {int(company['minimum_cash_buffer_jpy']):,}")
    return _frame(issues)
