from pathlib import Path
from nexaworks import load_dataset, run_pipeline, save_plan

if __name__=="__main__":
    raw=load_dataset(); r=run_pipeline(raw=raw); out=Path("outputs"); out.mkdir(exist_ok=True); print(save_plan(out/"baseline_plan.json",r["result"]))
