from __future__ import annotations
import pandas as pd

def compare_scenarios(before,after):
    def row(x):
        r=x.get("result",{}); d=r.get("decision",pd.DataFrame())
        return {"scenario":x.get("scenario_id"),"solver_status":x.get("solver_status"),"selected_works":int(d["selected"].sum()) if not d.empty else 0,"delayed_works":int((d["decision"]=="delay").sum()) if not d.empty else 0,"objective_value":r.get("objective_value"),"cash_end_actual_jpy":r.get("cash_end_actual_jpy"),"cash_shortfall_jpy":r.get("cash_shortfall_jpy")}
    return pd.DataFrame([row(before),row(after)])

def summarize_schedule_change(before,after):
    if before is None or after is None or before.empty or after.empty: return pd.DataFrame(columns=["work_id","before_start","after_start","change"])
    b=before.groupby("work_id")["start_hour"].min(); a=after.groupby("work_id")["start_hour"].min(); ids=sorted(set(b.index)|set(a.index)); rows=[]
    for w in ids:
        b0=b.get(w,float("nan")); a0=a.get(w,float("nan"))
        change="newly_scheduled" if w not in b.index else "removed_from_plan" if w not in a.index else "rescheduled" if b0!=a0 else "unchanged"
        rows.append({"work_id":w,"before_start":b0,"after_start":a0,"change":change})
    return pd.DataFrame(rows)
