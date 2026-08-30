from __future__ import annotations
import json
from pathlib import Path
from nexaworks.scenario.runner import run_scenario

def save_scenario(path,raw,scenario_id="scenario"):
    payload={"scenario_id":scenario_id,"dataset":raw}; Path(path).write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8"); return str(path)

def load_scenario(path): return json.loads(Path(path).read_text(encoding="utf-8"))["dataset"]

def save_plan(path,result):
    payload={k:result.get(k) for k in ["solver_status","objective_value","cash_end_actual_jpy","cash_end_expected_jpy","cash_shortfall_jpy"]}
    for key in ["decision","assignment","schedule","commercial_option"]: payload[key]=result.get(key).to_dict(orient="records") if hasattr(result.get(key),"to_dict") else []
    Path(path).write_text(json.dumps(payload,ensure_ascii=False,indent=2,default=str),encoding="utf-8"); return str(path)

def decision_signature(result):
    d=result.get("decision")
    if d is None or d.empty: return []
    cols=[c for c in ["work_id","decision","selected","start_hour","end_hour","effective_hours"] if c in d.columns]
    return d[cols].sort_values("work_id").to_dict(orient="records")

def reproducibility_check(raw,seed=42):
    r1=run_scenario(raw,"repro_1",seed=seed,workers=1); r2=run_scenario(raw,"repro_2",seed=seed,workers=1)
    return {"same_decision":decision_signature(r1["result"])==decision_signature(r2["result"]),"run_1_status":r1["solver_status"],"run_2_status":r2["solver_status"]}
