from __future__ import annotations

from nexaworks.pipeline import run_pipeline


def run_scenario(raw, scenario_id="scenario", patch=None, time_limit=None, workers=None, seed=None, config=None):
    return run_pipeline(
        raw=raw,
        scenario_id=scenario_id,
        patch=patch,
        time_limit=time_limit,
        workers=workers,
        seed=seed,
        config=config,
    )
