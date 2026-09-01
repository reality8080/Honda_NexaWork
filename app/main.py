from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path

import gradio as gr
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
DATA_PATH = BASE / "data" / "candidate_dataset.json"


from nexaworks import MODEL_CONFIG, explain_decisions, load_dataset, run_pipeline, save_plan, save_scenario, sales_option_analysis
from nexaworks.scenario.patch import apply_patch
from nexaworks.i18n import localize_dataframe, t, TRANSLATIONS


def load_action(file_path, language):
    try:
        path = file_path or (str(DATA_PATH) if DATA_PATH.exists() else None)
        raw = load_dataset(path)
        return raw, deepcopy(raw), f"{t(language, 'loaded')} Top-level keys: {', '.join(raw.keys())}"
    except Exception as exc:
        return None, None, f"Load error: {exc}"


def run_action(raw, strict_cash, time_limit, language):
    if raw is None:
        return None, "", *([pd.DataFrame()] * 5)
    cfg = deepcopy(MODEL_CONFIG)
    cfg["cash_hard_constraint"] = bool(strict_cash)
    try:
        outcome = run_pipeline(raw=raw, config=cfg, time_limit=int(time_limit))
        result = outcome["result"]
        status = (
            f"Solver: {outcome['solver_status']} | Objective: {outcome['objective_value']} | "
            f"Diagnostics: {len(outcome['post_check']) if outcome['post_check'] is not None else 0}"
        )
        explanation = (
            explain_decisions(result, outcome.get("data_model"), cfg, outcome.get("validation"), outcome.get("post_check"), language=language)
            if outcome.get("data_model") is not None else pd.DataFrame()
        )
        if outcome.get("data_model") is not None:
            start = pd.Timestamp(raw["metadata"]["planning_start"])
            end = pd.Timestamp(raw["metadata"]["planning_end"])
            planning_days = (end - start).days + 1
            sales = sales_option_analysis(outcome["data_model"], result, planning_days, cfg)
        else:
            sales = pd.DataFrame()
        warnings = outcome.get("post_check", pd.DataFrame())

        # Áp dụng dịch DataFrame trước khi hiển thị lên giao diện
        decision_df = localize_dataframe(result.get("decision", pd.DataFrame()), language)
        assignment_df = localize_dataframe(result.get("assignment", pd.DataFrame()), language)
        sales_df = localize_dataframe(sales, language)
        explanation_df = localize_dataframe(explanation, language)
        warnings_df = localize_dataframe(warnings, language)

        return outcome, status, decision_df, assignment_df, sales_df, explanation_df, warnings_df
    except Exception as exc:
        return {"error": str(exc)}, f"Run error: {exc}", *([pd.DataFrame()] * 5)

def patch_action(raw, patch_text, language):
    if raw is None:
        return None, t(language, "need_load")
    try:
        obj = json.loads(patch_text or "{}")
        updated = apply_patch(raw, obj)
        return updated, t(language, "patched")
    except Exception as exc:
        return raw, f"Patch error: {exc}"


def restore_action(initial_raw, language):
    if initial_raw is None:
        return None, "", t(language, "need_load")
    return deepcopy(initial_raw), "{}", t(language, "restored")


def save_action(raw, outcome, language):
    if raw is None or outcome is None or outcome.get("result") is None:
        return "Run optimization first."
    out = BASE / "outputs"
    out.mkdir(exist_ok=True)
    save_scenario(out / "scenario.json", raw, outcome.get("scenario_id", "ui_scenario"))
    save_plan(out / "plan.json", outcome["result"])
    return f"{t(language, 'saved')}: {out.resolve()}"


def language_updates(language, raw, outcome):
    # Khởi tạo các DataFrame rỗng mặc định
    decision_df = pd.DataFrame()
    assignment_df = pd.DataFrame()
    sales_df = pd.DataFrame()
    explanation_df = pd.DataFrame()
    warnings_df = pd.DataFrame()

    # Nếu đã có kết quả tối ưu hóa (outcome), tạo lại dữ liệu bảng và bản địa hóa (localize)
    if outcome and isinstance(outcome, dict) and outcome.get("result") is not None:
        result = outcome["result"]
        dm = outcome.get("data_model")
        cfg = deepcopy(MODEL_CONFIG)

        raw_decision = result.get("decision", pd.DataFrame())
        raw_assignment = result.get("assignment", pd.DataFrame())

        if dm is not None:
            explanation = explain_decisions(
                result, dm, cfg, outcome.get("validation"), outcome.get("post_check"), language=language
            )
            if raw is not None and "metadata" in raw:
                start = pd.Timestamp(raw["metadata"]["planning_start"])
                end = pd.Timestamp(raw["metadata"]["planning_end"])
                planning_days = (end - start).days + 1
                sales = sales_option_analysis(dm, result, planning_days, cfg)
            else:
                sales = pd.DataFrame()
        else:
            explanation = pd.DataFrame()
            sales = pd.DataFrame()

        warnings = outcome.get("post_check", pd.DataFrame())

        # Dịch tiêu đề cột và giá trị hiển thị trong các DataFrame
        decision_df = localize_dataframe(raw_decision, language)
        assignment_df = localize_dataframe(raw_assignment, language)
        sales_df = localize_dataframe(sales, language)
        explanation_df = localize_dataframe(explanation, language)
        warnings_df = localize_dataframe(warnings, language)

    # Cập nhật giao diện (Label/Button/Header) đồng thời cập nhật lại giá trị bảng (Dataframe)
    return (
        gr.update(label=t(language, "upload")),
        gr.update(value=t(language, "load")),
        gr.update(label=t(language, "strict")),
        gr.update(label=t(language, "time")),
        gr.update(value=t(language, "run")),
        gr.update(value=t(language, "restore")),
        gr.update(label=t(language, "status")),
        gr.update(label=t(language, "status")),
        gr.update(label=t(language, "decision"), value=decision_df),
        gr.update(label=t(language, "assignment"), value=assignment_df),
        gr.update(label=t(language, "sales"), value=sales_df),
        gr.update(label=t(language, "explain"), value=explanation_df),
        gr.update(label=t(language, "warnings"), value=warnings_df),
        gr.update(label=t(language, "patch")),
        gr.update(value=t(language, "apply")),
        gr.update(value=t(language, "save")),
        gr.update(value=f"# {t(language, 'title')}"),
    )

def edit_data_action(raw, entity, action, item_id, payload, language):
    if raw is None:
        return raw, t(language, "need_load")
    try:
        data = json.loads(payload or "{}")
        key_map = {"work_items": "work_items", "people": "people", "company": "company"}
        k = key_map[entity]
        if action == "add":
            if k not in raw:
                raw[k] = []
            raw[k].append(data)
        elif action == "edit":
            items = raw.get(k, [])
            for i, it in enumerate(items):
                if str(it.get("id") or it.get("work_id") or it.get("person_id")) == str(item_id):
                    items[i] = {**it, **data}
                    break
        elif action == "delete":
            raw[k] = [it for it in raw.get(k, []) if str(it.get("id") or it.get("work_id") or it.get("person_id")) != str(item_id)]
        return raw, t(language, "patched")
    except Exception as exc:
        return raw, f"Edit error: {exc}"

with gr.Blocks(title="NexaWorks Operations Decision Support Tool") as demo:
    raw_state = gr.State(None)
    initial_state = gr.State(None)
    outcome_state = gr.State(None)

    header = gr.Markdown(f"# {t('English', 'title')}")
    language = gr.Dropdown(list(TRANSLATIONS.keys()), value="English", label="Language", scale=1)
    with gr.Row():
        upload = gr.File(label=t("English", "upload"), file_types=[".json"], type="filepath", scale=3)
        load_btn = gr.Button(t("English", "load"), scale=1)
    load_status = gr.Textbox(label=t("English", "status"))

    with gr.Row():
        strict = gr.Checkbox(label=t("English", "strict"), value=False)
        limit = gr.Slider(1, 120, value=30, step=1, label=t("English", "time"))
        run_btn = gr.Button(t("English", "run"), variant="primary")
        restore_btn = gr.Button(t("English", "restore"))

    status = gr.Textbox(label=t("English", "status"))

    with gr.Tab(t("English", "edit_data") if "edit_data" in TRANSLATIONS["English"] else "Edit Data"):
        with gr.Row():
            entity = gr.Dropdown(choices=["work_items", "people", "company"], value="work_items", label="Entity")
            action = gr.Dropdown(choices=["add", "edit", "delete"], value="edit", label="Action")
        item_id = gr.Textbox(label="ID (for edit/delete)")
        payload = gr.Textbox(label="JSON payload (for add/edit)", lines=10, value="{}")
        edit_btn = gr.Button(t("English", "apply_edit"))
        edit_status = gr.Textbox()

    with gr.Tab(t("English", "decision")):
        decision = gr.Dataframe(label=t("English", "decision"), interactive=False)
        assignment = gr.Dataframe(label=t("English", "assignment"), interactive=False)
    with gr.Tab(t("English", "sales")):
        sales = gr.Dataframe(label=t("English", "sales"), interactive=False)
    with gr.Tab(t("English", "explain")):
        explanation = gr.Dataframe(label=t("English", "explain"), interactive=False)
        warnings = gr.Dataframe(label=t("English", "warnings"), interactive=False)
    with gr.Tab("Scenario Patch"):
        patch = gr.Textbox(label=t("English", "patch"), lines=14, value="{}")
        patch_btn = gr.Button(t("English", "apply"))
        patch_status = gr.Textbox()

    save_btn = gr.Button(t("English", "save"))
    save_status = gr.Textbox()

    load_btn.click(load_action, [upload, language], [raw_state, initial_state, load_status])
    restore_btn.click(restore_action, [initial_state, language], [raw_state, patch, patch_status])



    edit_btn.click(edit_data_action, [raw_state, entity, action, item_id, payload, language], [raw_state, edit_status])

    patch_btn.click(patch_action, [raw_state, patch, language], [raw_state, patch_status])
    run_btn.click(
        run_action,
        [raw_state, strict, limit, language],
        [outcome_state, status, decision, assignment, sales, explanation, warnings],
    )
    save_btn.click(save_action, [raw_state, outcome_state, language], [save_status])
    language.change(
        language_updates,
        inputs=[language, raw_state, outcome_state],
        outputs=[
            upload,
            load_btn,
            strict,
            limit,
            run_btn,
            restore_btn,
            load_status,
            status,
            decision,
            assignment,
            sales,
            explanation,
            warnings,
            patch,
            patch_btn,
            save_btn,
            header,
        ],
    )


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", "7860")))
