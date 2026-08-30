from nexaworks import load_dataset, run_pipeline

if __name__=="__main__":
    raw=load_dataset(); r=run_pipeline(raw=raw); print({k:r[k] for k in ["scenario_id","solver_status","objective_value"]}); print(r["result"]["decision"].to_string(index=False))
