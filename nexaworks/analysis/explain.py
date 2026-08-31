from __future__ import annotations
import pandas as pd
from nexaworks.engine.financials import work_financials
from i18n import t

def explain_decisions(result, dm, config, validation=None, post_check=None, language="English"):
    if result.get("decision", pd.DataFrame()).empty:
        return pd.DataFrame()
    validation = validation if validation is not None else pd.DataFrame()
    post_check = post_check if post_check is not None else pd.DataFrame()
    rows = []
    for _, r in result["decision"].iterrows():
        w = r["work_id"]
        raw = dm["work_items"].set_index("work_id").loc[w].to_dict()
        reasons = []
        
        reasons.append(t(language, "selected_by_objective") if r["selected"] else t(language, "not_selected"))
        if r["decision"] == "delay":
            reasons.append(t(language, "starts_later", hours=int(r['delay_hours'])))
        if r["mandatory"]:
            reasons.append(t(language, "mandatory"))
        elif r["committed"]:
            reasons.append(t(language, "committed"))
            
        deps = dm["work_dependencies"].loc[dm["work_dependencies"]["work_id"] == w, "depends_on_work_id"].tolist()
        if deps:
            reasons.append(f"{t(language, 'depends_on')}: " + ", ".join(deps))
            
        people = result["assignment"].loc[result["assignment"]["work_id"] == w, "person_id"].tolist()
        if people:
            reasons.append(f"{t(language, 'assigned')}: " + ", ".join(people))
            
        margin, risk = work_financials(raw, config)
        cid = raw.get("customer_id")
        csv = crv = 0
        if pd.notna(cid) and cid in set(dm["customers"]["customer_id"]):
            cust = dm["customers"].set_index("customer_id").loc[cid]
            csv = float(cust.get("strategic_value") or 0)
            crv = float(cust.get("reference_value") or 0)
            
        customer_value = (float(raw.get("strategic_value") or 0) + csv + crv) * config["customer_point_jpy"]
        labor = float(result["assignment"].loc[result["assignment"]["work_id"] == w, "labor_cost_jpy"].sum())
        
        warns = []
        if not validation.empty:
            warns += validation.loc[validation["record_id"] == w, "message"].tolist()
        if not post_check.empty:
            warns += post_check.loc[post_check["record_id"] == w, "message"].tolist()
            
        rows.append({
            "work_id": w,
            "decision": r["decision"],
            "reason": "; ".join(reasons),
            "expected_margin_jpy": round(margin),
            "risk_penalty_jpy": round(risk * config["risk_weight"]),
            "customer_value_jpy": round(customer_value),
            "labor_cost_jpy": round(labor),
            "delay_penalty_jpy": round(float(r["delay_hours"]) * config["delay_weight_jpy_per_hour"]),
            "effective_hours": int(r["effective_hours"]),
            "warnings": "; ".join(warns)
        })
    return pd.DataFrame(rows)