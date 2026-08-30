---
title: NexaWorks Operations Decision Support Tool
emoji: 📊
colorFrom: orange
colorTo: gray
sdk: docker
app_port: 7860
---

# NexaWorks Operations Decision Support Tool

A decision-support application for the four-week NexaWorks planning problem. The tool combines work selection, people assignment, scheduling, shared-resource constraints, commercial-option selection, cash constraints, scenario changes, validation, explanation and reproducibility.

This package is designed for three evaluation paths:

1. **Hugging Face Spaces** — Docker Space, port `7860`.
2. **Docker** — one-command local container.
3. **VS Code / local Python** — Python 3.11 virtual environment.

> The assignment's canonical `candidate_dataset.json` is intentionally not invented or replaced. Place the provided canonical dataset at `data/candidate_dataset.json`, or upload it through the UI.

## Quick start

### VS Code / local Python

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m app.main
```

Open `http://127.0.0.1:7860`.

### Docker

```powershell
docker build -t nexaworks .
docker run --rm -p 7860:7860 nexaworks
```

Open `http://127.0.0.1:7860`.

### Hugging Face Spaces

Create a new **Docker Space**, upload the repository contents, and make sure the canonical dataset is present at:

```text
data/candidate_dataset.json
```

The Space listens on port `7860`. The included Dockerfile starts `python -m app.main`.

## 1. Candidate and submission

- Candidate name: **[fill before submission]**
- Application URL: **[paste Hugging Face Space URL]**
- Source repository or archive: **[paste GitHub repository or final ZIP]**
- Evaluation login, if required: **Not required**
- Tested browser / operating system: **[fill after final clean-environment test]**
- Commit or release identifier: **[fill after final Git commit/tag]**

## 2. Problem interpretation / 課題の理解

The primary user is a management or operations decision-maker who needs to decide what work should be executed within a four-week planning horizon, who should perform it, when it should happen, which sales/commercial option should be offered, and how the plan should change when assumptions change.

The product treats the problem as an integrated decision problem rather than a static priority list. A plan is useful only when it is both economically attractive and operationally feasible. The main user action is therefore:

`Import/edit scenario → validate → optimize → inspect decisions/assignments/sales → understand reasons and warnings → change assumptions → re-optimize → compare/save plan`

## 3. Objective and decision model / 目的関数・判断モデル

### Decision variables

For each work item:

- `select[w]`: execute or not execute.
- `start/end`: schedule within the planning horizon and work window.
- `hours[w,p]`: hours assigned to person `p`.
- `option[o]`: commercial option selected for a sales opportunity.
- `effective_hours[w]`: effort after applicable portfolio effects.

### Objective

The model maximizes a weighted utility. Conceptually:

```text
work utility
= expected margin
+ customer value
- risk penalty

option utility
= expected margin
+ weighted future value
- risk penalty
- payment-delay penalty

portfolio objective
= work utility
+ selected option utility
- labor cost
- delay penalty
- cash-shortfall penalty (baseline soft-cash mode)
```

The current model assumptions are explicit in `nexaworks/config.py` and are intentionally separated from dataset facts.

### Hard constraints

The current model treats these as operational constraints:

- mandatory work must be selected;
- people cannot exceed available capacity;
- unavailable periods are blocked;
- required skill and language coverage must exist;
- selected work must respect earliest start and due date;
- dependencies must be respected;
- conflicts cannot be selected together;
- shared resources cannot exceed their modeled capacity;
- a selected sales work item with commercial options must select exactly one option;
- option dependencies must be respected;
- strict-cash mode makes the cash buffer a hard condition.

Baseline cash is deliberately modeled as a **soft constraint** so the optimizer can still return a plan and expose cash shortfall as a warning. The UI provides a strict-cash mode for sensitivity testing.

### Assignments and timing

CP-SAT decides both the work selection and the allocation of hours to qualified people. The schedule is represented on an hourly index because the source dataset provides dates rather than working-hour calendars. The model uses `24` hours per calendar day as an explicit assumption.

### Commercial options and no-bid

Commercial options are not ranked in isolation. Each option contributes price, estimated win probability, direct cost, delivery effort, payment timing, warranty and future value to the integrated decision. A sales opportunity can therefore be declined or delayed when the integrated capacity/cash/deadline problem makes an apparently attractive option undesirable.

### Uncertainty

Success and win probabilities are treated as estimates used to calculate expected values; they are not guarantees. The current deterministic model exposes the seed, solver status and best bound where available, but it does not claim probabilistic certainty from the expected-value objective.

## 4. Main workflow / 主要な利用フロー

```text
candidate_dataset.json / upload
        ↓
raw structure validation
        ↓
canonical data model
        ↓
semantic validation
        ↓
CP-SAT optimization
        ↓
result extraction
        ↓
post-check / infeasibility diagnostics
        ↓
Decision + Assignment + Sales + Explanation
        ↓
Scenario patch / Restore initial scenario
        ↓
Re-optimize and compare
        ↓
Save scenario + plan
```

The workflow intentionally separates initial data from the mutable scenario so that the user can experiment and return to the original dataset.

## 5. Architecture and technology / 技術構成

- Frontend: **Gradio**.
- Backend: **Python 3.11** application package.
- Database / persistence: **JSON files** for scenario and plan persistence; no external database is required.
- Optimization / decision engine: **OR-Tools CP-SAT**.
- Hosting / deployment: **Hugging Face Spaces (Docker)**, plus local Docker and VS Code execution.
- Major libraries and licenses: Python (PSF License); OR-Tools (Apache-2.0); NumPy (BSD-3-Clause); pandas (BSD-3-Clause); Gradio (Apache-2.0). Verify dependency license metadata again before redistributing the final archive.
- External APIs: **None required**.

### Package layout

```text
app/                    Gradio entrypoint
nexaworks/config.py     explicit model assumptions
nexaworks/data/         loading, normalization, validation
nexaworks/engine/       financials, CP-SAT, result extraction
nexaworks/scenario/     patch, run, compare, reschedule
nexaworks/analysis/     sales analysis and explanations
nexaworks/persistence.py scenario/plan persistence and reproducibility
nexaworks/pipeline.py   end-to-end orchestration
tests/                  automated tests
scripts/                local baseline/export helpers
```

## 6. Setup and operation / 起動・操作方法

### Fresh local environment

1. Install Python 3.11.
2. Create and activate the virtual environment.
3. Run `pip install -r requirements.txt`.
4. Place `candidate_dataset.json` under `data/` or upload it in the application.
5. Run `python -m app.main`.
6. Use **Load dataset**, then **Run optimization**.

No account, proprietary IDE or external service is required for local evaluation.

### Docker

```bash
docker build -t nexaworks .
docker run --rm -p 7860:7860 nexaworks
```

### Hugging Face

Use a Docker Space. The included `README.md` contains the Docker Space metadata (`sdk: docker`, `app_port: 7860`). Push the project files and the canonical dataset to the Space. No secret is required for the current application.

### Scenario operation

- **Restore initial scenario** resets the mutable scenario state to the originally loaded dataset.
- **Scenario Patch** accepts JSON changes and runs against a copied scenario rather than mutating the initial dataset.
- **Save scenario + plan** writes JSON artifacts to `outputs/` in the local/container filesystem.

## 7. Testing / テスト

Automated tests cover:

- required-field validation;
- semantic skill-coverage validation;
- normal solver execution when the canonical dataset is available;
- strict-cash infeasibility behavior;
- reproducibility with a fixed seed and single worker;
- increased record counts without relying on specific work-item IDs.

The package also uses pre-solve validation so malformed JSON is rejected before model construction. When CP-SAT returns `INFEASIBLE`, deterministic diagnostics are added for common blockers such as mandatory workload capacity, mandatory skill/language coverage and strict-cash pressure instead of showing only a generic `NO_SOLUTION` message.

Final submission testing should include a fresh-environment smoke test, an imported alternate dataset with the same schema, a deliberate invalid input, a strict-cash scenario, long text, empty states and a three-language check.

## 8. Japanese, English and Vietnamese support / 三言語対応

The UI includes a language selector for English, Vietnamese and Japanese. Core application controls and major status labels are localized in `app/main.py`.

The source dataset may also contain multilingual text fields; the data model preserves localized fields instead of destroying them during normalization.

Remaining localization work before final submission: review every generated reason/warning against actual evaluator terminology and verify long Vietnamese strings on the deployed Space. This should be treated as a release-validation step rather than assumed to be complete from machine-generated translation alone.

## 9. UI/UX and design rationale / デザインの意図

The first screen prioritizes the evaluation actions that change the decision: dataset loading, cash constraint mode, solver time limit and optimization. Results are split into Decision, Sales and Explain views so that a manager can first inspect the plan, then commercial choices, then reasons and warnings.

The UI distinguishes:

- **result**: what the optimizer selected;
- **warning/validation**: why input or execution may be problematic;
- **scenario controls**: what assumptions the user changes;
- **restore**: return to the original loaded dataset.

The project was refactored from the notebook into reusable modules. Notebook-only globals, `display()` calls and environment-specific paths were removed from the application layer.

## 10. AI and external-tool disclosure / AI・外部ツール利用

### ChatGPT

- Tool or service: **OpenAI ChatGPT**
- Used for: code refactoring guidance, package architecture, debugging, README drafting, Docker/Hugging Face packaging and review of validation behavior.
- Output accepted/rejected/substantially changed: generated implementation suggestions were adapted into the package; notebook logic remained the source for the core decision model, and project-specific fixes were added around validation, diagnostics, packaging and deployment.
- How verified: Python compilation checks, inspection of module imports, review against the assignment brief/template, and local application testing where dependencies/dataset were available.

### External runtime services

No external API is required by the application itself.

## 11. Important assumptions / 重要な仮定

1. One calendar day is modeled as 24 planning hours because the supplied planning dates do not define business-hour calendars.
2. `mandatory=True` is treated as a hard selection requirement; `committed` remains a prioritization/explanation signal.
3. Baseline cash buffer is soft; strict-cash mode turns it into a hard constraint.
4. Success/win probabilities are used for expected values.
5. Objective weights in `nexaworks/config.py` are model assumptions and can be overridden.
6. Exact cash receipt/outflow timestamps are not reconstructed beyond the horizon-level information available in the dataset.
7. Portfolio effects are applied only when represented by the supported dataset structure.

## 12. Known limitations and failure cases / 既知の制約・誤判断の可能性

1. **Expected-value limitation:** a high expected-value plan can still be poor under an adverse probability outcome because the current core model is not a full Monte Carlo/risk-distribution optimizer.
2. **Time-model limitation:** the 24-hours-per-day planning index does not represent weekends, business hours, overtime rules or time-zone-specific working calendars unless those constraints are explicitly encoded in the dataset/model.
3. **Infeasibility diagnosis limitation:** deterministic diagnostics can identify common blockers, but an infeasible CP-SAT model may have a combination of interacting constraints for which the current diagnostic list does not identify a unique minimal unsatisfied constraint set.
4. **Persistence limitation on hosted containers:** local `outputs/` JSON files are not intended as a durable multi-user database. A restart/redeployment of the hosted container may remove locally written artifacts.
5. **Multilingual QA limitation:** the translation layer is application-level text localization; it still requires human terminology review before final release.

## 13. Security, privacy and data handling / セキュリティ・データ取扱い

The application has no authentication requirement and does not require secrets for its current functionality. Dataset files are processed by the application runtime and saved locally when the user chooses to save a scenario or plan.

No external API is called by the decision engine. On Hugging Face Spaces, data handling is subject to the Space/container lifecycle and platform policies; users should avoid uploading confidential customer information to a public evaluation Space.

No private credentials should be committed to the repository.

## 14. One more day / あと1日あれば

The highest-value next improvement would be a stronger **infeasibility explanation and sensitivity workflow**: surface the active blocking constraints, compare soft-cash vs strict-cash plans side by side, and show which assumption changes cause the largest decision changes. This directly improves the assignment's requirement that the manager understand not just the recommendation but the execution problem behind it.

## 15. Screenshots and optional demo

Recommended final evidence set:

1. **Main decision screen** — selected/declined/delayed work and assignments.
2. **Sales screen** — commercial options with price, probability, margin, effort and payment timing.
3. **Explainability screen** — decision reasons and validation/infeasibility diagnostics.
4. **Scenario screen** — patch/edit → re-optimize workflow.
5. **Strict-cash case** — demonstrates how the plan or diagnostics changes.

Optional: a demo video of no more than five minutes covering one baseline scenario and one changed-assumption scenario.

## Evaluation checklist before publishing

- [ ] Canonical `candidate_dataset.json` is present.
- [ ] Space URL is public and loads from a clean browser.
- [ ] Docker build succeeds from the repository root.
- [ ] Local VS Code setup succeeds from the README only.
- [ ] Alternate dataset with the same structure can be imported.
- [ ] One changed input causes recomputation.
- [ ] Infeasible inputs are explicitly labeled as infeasible.
- [ ] Strict cash changes are reproducible.
- [ ] English / Vietnamese / Japanese core messages are reviewed.
- [ ] Three to six clean screenshots are captured.
- [ ] Final ZIP is below the assignment's 100 MB limit.
- [ ] No secrets or private credentials remain in the repository.
