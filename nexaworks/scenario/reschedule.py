from __future__ import annotations
from copy import deepcopy
import pandas as pd
from .runner import run_scenario
from .compare import summarize_schedule_change

def build_urgent_patch(dm, top_n=1, due_within_days=10):
    meta=dm["metadata"].iloc[0] if not dm["metadata"].empty else {}
    start=pd.Timestamp(meta.get("planning_start") or dm["work_items"]["earliest_start_dt"].min())
    wi=dm["work_items"].copy(); wi=wi[wi["mandatory"]==False].copy(); wi["days_left"]=(wi["due_date_dt"]-start).dt.days
    wi=wi[wi["days_left"]<=due_within_days].sort_values(["strategic_value","days_left"],ascending=[False,True]).head(top_n)
    patch={"work_items":{}}
    for _,row in wi.iterrows():
        patch["work_items"][row["work_id"]]={"mandatory":True,"committed":True,"due_date":(start+pd.Timedelta(days=max(3,due_within_days//2))).strftime("%Y-%m-%d"),"strategic_value":max(int(row.get("strategic_value") or 0),5)}
    return patch

def build_batch_patches(dm,max_items=3,due_within_days=14):
    meta=dm["metadata"].iloc[0] if not dm["metadata"].empty else {}; start=pd.Timestamp(meta.get("planning_start") or dm["work_items"]["earliest_start_dt"].min())
    wi=dm["work_items"].copy(); wi=wi[wi["mandatory"]==False].copy(); wi["days_left"]=(wi["due_date_dt"]-start).dt.days
    wi=wi[wi["days_left"]<=due_within_days].sort_values(["strategic_value","days_left"],ascending=[False,True]).head(max_items)
    return [{"work_items":{row["work_id"]:{"mandatory":True,"committed":True,"due_date":(start+pd.Timedelta(days=max(5,int(row["days_left"])//2))).strftime("%Y-%m-%d"),"strategic_value":max(int(row.get("strategic_value") or 0),5)}}} for _,row in wi.iterrows()]

def flexible_reschedule(raw,urgent_patch,time_limit=8,seed=42):
    before=run_scenario(raw,"flexible_before",time_limit=time_limit,seed=seed); after=run_scenario(raw,"flexible_after",patch=urgent_patch,time_limit=time_limit,seed=seed)
    return {"before":before,"after":after,"schedule_change":summarize_schedule_change(before["result"]["schedule"],after["result"]["schedule"])}

def batch_reschedule(raw,patches,time_limit=15,seed=42):
    merged={s:{} for s in ["company","people","customers","shared_resources","work_items","commercial_options","portfolio_effects"]}
    for patch in patches:
        for section,values in patch.items():
            if section=="company": merged[section].update(values)
            else:
                for rid,changes in values.items(): merged[section][rid]={**merged[section].get(rid,{}),**changes}
    return {"patch":merged,"result":run_scenario(raw,"batch",patch=merged,time_limit=time_limit,seed=seed)}
