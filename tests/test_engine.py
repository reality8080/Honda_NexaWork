import pytest
from nexaworks.data.model import build_model
from nexaworks.data.validate import validate_semantics
from nexaworks.scenario.runner import run_scenario
from nexaworks.config import MODEL_CONFIG
from nexaworks.engine.cpsat import NexaWorksEngine

def test_normal(raw):
    if not validate_semantics(build_model(raw),raw).empty: pytest.fail("Static validation failed")
    r=run_scenario(raw,time_limit=20)
    assert r["solver_status"] in ("OPTIMAL","FEASIBLE")

def test_strict_cash(raw):
    cfg=dict(MODEL_CONFIG); cfg["cash_hard_constraint"]=True
    dm=build_model(raw); e=NexaWorksEngine(dm,raw,cfg).build(); info=e.solve(time_limit=20,workers=1,seed=42)
    assert info["solver_status"] in ("INFEASIBLE","OPTIMAL","FEASIBLE")
