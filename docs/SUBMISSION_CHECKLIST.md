# Final submission checklist

## Files

- [x] `README.md` finalized with candidate name, Space URL and repository URL.
- [x] `SUBMISSION_README.md` finalized.
- [x] `data/candidate_dataset.json` included.
- [x] `candidate_dataset.schema.json` included if provided by the assignment.
- [ ] `candidate_dataset_reference.xlsx` included if desired for readability.
- [x] 3–6 clean screenshots included (`submit_screen/`).
- [ ] Optional demo video is ≤ 5 minutes.

## Runtime

- [x] `python -m app.main` works in a fresh venv.
- [x] `docker build` succeeds.
- [x] Docker container serves port 7860.
- [x] Deploying on Render successfully.
- [x] Alternate dataset import works.
- [x] Invalid dataset does not crash model construction.
- [x] Infeasible scenario shows diagnostics beyond generic `NO_SOLUTION` when deterministic blockers are detectable.
- [x] Restore returns to the initial dataset.
- [x] Save scenario + plan works.
- [x] Three-language core workflow has been checked.

## Evidence

- [x] Decision screen → `submit_screen/01_decision_baseline.png`
- [x] Sales screen → `submit_screen/02_sales_baseline.png`
- [x] Explain/validation screen → `submit_screen/03_explanation_warnings.png`
- [x] Scenario edit/restore → `submit_screen/04a_*.png`, `04b_*.png`, `04c_*.png`
- [x] Strict-cash behavior → `submit_screen/05_strict_cash_infeasible.png`
