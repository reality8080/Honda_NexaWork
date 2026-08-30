# Final submission checklist

## Files

- [ ] `README.md` finalized with candidate name, Space URL and repository URL.
- [ ] `SUBMISSION_README.md` finalized.
- [ ] `data/candidate_dataset.json` included.
- [ ] `candidate_dataset.schema.json` included if provided by the assignment.
- [ ] `candidate_dataset_reference.xlsx` included if desired for readability.
- [ ] 3–6 clean screenshots included.
- [ ] Optional demo video is ≤ 5 minutes.

## Runtime

- [ ] `python -m app.main` works in a fresh venv.
- [ ] `docker build` succeeds.
- [ ] Docker container serves port 7860.
- [ ] Hugging Face Docker Space starts successfully.
- [ ] Alternate dataset import works.
- [ ] Invalid dataset does not crash model construction.
- [ ] Infeasible scenario shows diagnostics beyond generic `NO_SOLUTION` when deterministic blockers are detectable.
- [ ] Restore returns to the initial dataset.
- [ ] Save scenario + plan works.
- [ ] Three-language core workflow has been checked.

## Evidence

- [ ] Decision screen
- [ ] Sales screen
- [ ] Explain/validation screen
- [ ] Scenario edit/restore
- [ ] Strict-cash behavior
