# Hugging Face Spaces deployment

1. Create a new Space and select **Docker** as the SDK.
2. Upload the project contents from the repository root.
3. Include the canonical `data/candidate_dataset.json`.
4. Keep `app_port: 7860` in the root README front matter.
5. Wait for the Docker build to finish.
6. Open the Space URL and verify: Load → Run optimization → Explain → strict-cash rerun → Scenario Patch → Restore.

No secret is required for the current application.
