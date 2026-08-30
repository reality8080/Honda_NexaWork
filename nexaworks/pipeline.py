from __future__ import annotations

from .data.loader import load_dataset
from .data.model import build_model
from .data.validate import validate_raw_structure, validate_semantics, verify_solution, diagnose_infeasibility
from .engine.cpsat import NexaWorksEngine
from .engine.result import empty_result
from .config import get_config


def run_pipeline(raw=None, path=None, scenario_id="scenario", patch=None, time_limit=None, workers=None, seed=None, config=None):
    """End-to-end execution: raw validation -> model -> semantic validation -> CP-SAT -> checks."""
    if raw is None:
        raw = load_dataset(path)
    # Import lazily to avoid circular import: scenario.runner -> pipeline.
    from .scenario.patch import apply_patch
    scenario = apply_patch(raw, patch or {})
    cfg = get_config(config)

    raw_validation = validate_raw_structure(scenario)
    if not raw_validation.empty:
        return {
            "scenario_id": scenario_id,
            "solver_status": "INVALID_INPUT",
            "objective_value": None,
            "validation": raw_validation,
            "precheck": raw_validation.copy(),
            "result": empty_result(),
            "post_check": raw_validation.copy(),
            "data_model": None,
            "raw": scenario,
        }

    dm = build_model(scenario)
    validation = validate_semantics(dm, scenario)
    if not validation.empty and (validation["status"] == "Invalid Input").any():
        return {
            "scenario_id": scenario_id,
            "solver_status": "INVALID_INPUT",
            "objective_value": None,
            "validation": pd_concat(raw_validation, validation),
            "precheck": validation.copy(),
            "result": empty_result(),
            "post_check": validation.copy(),
            "data_model": dm,
            "raw": scenario,
        }

    if time_limit is None:
        time_limit = cfg["default_solver_time_limit"]
    if workers is None:
        workers = cfg["default_solver_workers"]
    if seed is None:
        seed = cfg["default_seed"]

    engine = NexaWorksEngine(dm, scenario, cfg).build()
    info = engine.solve(time_limit=time_limit, workers=workers, seed=seed)
    result = engine.result()

    if info["solver_status"] == "INFEASIBLE":
        diagnostics = diagnose_infeasibility(dm, scenario, cfg)
        if not diagnostics.empty:
            combined = pd_concat(validation, diagnostics)
        else:
            combined = validation.copy()
        post = combined if combined.empty else combined.copy()
    else:
        combined = validation.copy()
        post = verify_solution(result, dm, scenario, cfg, engine)

    return {
        "scenario_id": scenario_id,
        "solver_status": info["solver_status"],
        "objective_value": info["objective_value"],
        "best_bound": info.get("best_bound"),
        "validation": combined,
        "precheck": validation,
        "result": result,
        "post_check": post,
        "engine": engine,
        "data_model": dm,
        "raw": scenario,
        "seed": seed,
        "time_limit": time_limit,
        "workers": workers,
        "config": cfg,
    }


def pd_concat(left, right):
    import pandas as pd
    if left is None or left.empty:
        return right.copy()
    if right is None or right.empty:
        return left.copy()
    return pd.concat([left, right], ignore_index=True)
