from __future__ import annotations

from copy import deepcopy

MODEL_CONFIG = {
    "hours_per_day": 24,
    "inclusive_due_date": True,
    "mandatory_is_hard": True,
    "cash_hard_constraint": False,
    "cash_shortfall_weight_jpy_per_jpy": 1.0,
    "customer_point_jpy": 150_000,
    "future_value_weight": 0.10,
    "risk_weight": 0.25,
    "payment_delay_weight": 0.002,
    "delay_weight_jpy_per_hour": 8_000,
    "labor_effort_weight_jpy_per_hour": 500,
    "default_solver_time_limit": 30,
    "default_solver_workers": 8,
    "default_seed": 42,
}


def get_config(overrides: dict | None = None) -> dict:
    cfg = deepcopy(MODEL_CONFIG)
    if overrides:
        cfg.update(overrides)
    return cfg
