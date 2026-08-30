from __future__ import annotations
import pandas as pd
from nexaworks.engine.financials import option_financials

def sales_option_analysis(dm,result,planning_days,config):
    chosen=set(result.get("commercial_option",pd.DataFrame()).get("option_id",[]))
    rows=[]
    for _,o in dm["commercial_options"].iterrows():
        p=float(o["estimated_win_probability"]); margin=(float(o["price_jpy"])-float(o["direct_cost_jpy"]))*p
        cash=float(o["price_jpy"])*p if float(o["payment_days"])<=planning_days else 0
        rows.append({"work_id":o["work_id"],"option_id":o["option_id"],"label":o.get("label_canonical",o.get("label")),"price_jpy":o["price_jpy"],"win_probability":p,"expected_margin_jpy":round(margin),"delivery_hours":o["delivery_hours"],"payment_days":o["payment_days"],"cash_in_horizon_jpy":round(cash),"warranty_months":o["warranty_months"],"follow_on_value_jpy":o["follow_on_value_jpy"],"integrated_utility":round(option_financials(o.to_dict(),config)),"selected_by_solver":o["option_id"] in chosen})
    return pd.DataFrame(rows).sort_values(["work_id","integrated_utility"],ascending=[True,False])
