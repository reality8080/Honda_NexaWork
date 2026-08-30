# README FIRST — evaluator order

1. Run locally or open the Hugging Face Space.
2. Load `candidate_dataset.json`.
3. Run optimization with baseline (soft cash).
4. Inspect Decision, Sales and Explain.
5. Turn on Strict cash and rerun.
6. Apply a Scenario Patch and rerun.
7. Restore the initial scenario.
8. Save scenario + plan.
9. For local verification, run `pytest -q`.

Required assignment files that must be supplied before final submission:

- `data/candidate_dataset.json`
- `candidate_dataset.schema.json` if you intend to include the provided schema reference
- optional `candidate_dataset_reference.xlsx` for readability

The repository deliberately does not fabricate missing canonical assignment files.
