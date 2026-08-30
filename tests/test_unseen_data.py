from copy import deepcopy

from nexaworks.data.model import build_model
from nexaworks.data.validate import validate_semantics
from nexaworks.scenario.runner import run_scenario


def test_large_dataset_without_hardcoded_work_id(raw):
    large = deepcopy(raw)
    optional = next((w for w in large["work_items"] if not w.get("mandatory")), None)
    if optional is None:
        raise AssertionError("Fixture must contain at least one optional work item.")
    template = deepcopy(optional)
    for i in range(5):
        clone = deepcopy(template)
        clone["id"] = f"UNSEEN_{i:03d}"
        title = clone.get("title")
        if isinstance(title, dict):
            clone["title"] = {k: f"{v} #{i}" for k, v in title.items()}
        else:
            clone["title"] = f"{title} #{i}"
        large["work_items"].append(clone)
    dm = build_model(large)
    validation = validate_semantics(dm, large)
    assert not ((validation["status"] == "Invalid Input")).any(), validation
    result = run_scenario(large, "test_large", time_limit=5, workers=1)
    assert result["solver_status"] in ("OPTIMAL", "FEASIBLE")
