from __future__ import annotations

def work_financials(row, config):
    p=float(row.get("success_probability") or 0)
    margin=(float(row.get("revenue_jpy") or 0)-float(row.get("direct_cost_jpy") or 0))*p
    risk=(1-p)*max(float(row.get("revenue_jpy") or 0),float(row.get("direct_cost_jpy") or 0))
    return margin,risk

def option_financials(row, config):
    p=float(row.get("estimated_win_probability") or 0)
    margin=(float(row.get("price_jpy") or 0)-float(row.get("direct_cost_jpy") or 0))*p
    future=float(row.get("follow_on_value_jpy") or 0)*p*float(config["future_value_weight"])
    risk=(1-p)*max(float(row.get("price_jpy") or 0),float(row.get("direct_cost_jpy") or 0))*float(config["risk_weight"])
    delay=float(row.get("price_jpy") or 0)*p*float(row.get("payment_days") or 0)*float(config["payment_delay_weight"])
    return margin+future-risk-delay
