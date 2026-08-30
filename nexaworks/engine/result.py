from __future__ import annotations

import pandas as pd


def empty_result():
    return {
        "decision": pd.DataFrame(), "assignment": pd.DataFrame(), "schedule": pd.DataFrame(),
        "commercial_option": pd.DataFrame(), "objective_value": None, "solver_status": None,
        "cash_end_actual_jpy": None, "cash_end_expected_jpy": None, "cash_shortfall_jpy": None,
    }


def extract_result(engine):
    return engine.result()
