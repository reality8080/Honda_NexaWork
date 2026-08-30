from copy import deepcopy
from nexaworks.data.validate import validate_raw_structure, validate_semantics
from nexaworks.data.model import build_model

def test_missing_field(raw):
    bad=deepcopy(raw); del bad["work_items"][0]["required_hours"]; assert not validate_raw_structure(bad).empty

def test_no_skill_coverage(raw):
    bad=deepcopy(raw)
    for p in bad["people"]:
        if "backend" in p.get("skills",{}): p["skills"]["backend"]=0
    v=validate_semantics(build_model(bad),bad); assert ((v["code"]=="NO_SKILL_COVERAGE")&(v["status"]=="Infeasible")).any()
