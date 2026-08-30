from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path

import gradio as gr
import pandas as pd

from nexaworks import MODEL_CONFIG, explain_decisions, load_dataset, run_pipeline, save_plan, save_scenario, sales_option_analysis
from nexaworks.scenario.patch import apply_patch

BASE = Path(__file__).resolve().parents[1]
DATA_PATH = BASE / "data" / "candidate_dataset.json"

LANG = {
    "English": {
        "title": "NexaWorks Operations Decision Support Tool",
        "upload": "Dataset (candidate_dataset.json)",
        "load": "Load dataset",
        "strict": "Strict cash constraint",
        "time": "Solver time limit (s)",
        "run": "Run optimization",
        "restore": "Restore initial scenario",
        "status": "Status",
        "decision": "Decision",
        "assignment": "Assignment",
        "sales": "Commercial options",
        "explain": "Decision explanation",
        "warnings": "Warnings / validation / infeasibility diagnostics",
        "patch": "Scenario patch (JSON)",
        "apply": "Apply patch",
        "save": "Save scenario + plan",
        "language": "Language",
        "loaded": "Dataset loaded.",
        "restored": "Scenario restored to the initial dataset.",
        "patched": "Scenario updated. Run optimization again.",
        "need_load": "Load or upload a dataset first.",
        "saved": "Saved to",
    },
    "Tiếng Việt": {
        "title": "Công cụ hỗ trợ quyết định vận hành NexaWorks",
        "upload": "Dữ liệu (candidate_dataset.json)",
        "load": "Nạp dữ liệu",
        "strict": "Ràng buộc tiền mặt cứng",
        "time": "Giới hạn thời gian solver (giây)",
        "run": "Chạy tối ưu hóa",
        "restore": "Khôi phục scenario ban đầu",
        "status": "Trạng thái",
        "decision": "Quyết định",
        "assignment": "Phân công",
        "sales": "Phương án thương mại",
        "explain": "Giải thích quyết định",
        "warnings": "Cảnh báo / validation / chẩn đoán infeasibility",
        "patch": "Scenario patch (JSON)",
        "apply": "Áp dụng patch",
        "save": "Lưu scenario + plan",
        "language": "Ngôn ngữ",
        "loaded": "Đã nạp dữ liệu.",
        "restored": "Đã khôi phục scenario ban đầu.",
        "patched": "Scenario đã thay đổi. Hãy chạy tối ưu hóa lại.",
        "need_load": "Hãy nạp hoặc upload dataset trước.",
        "saved": "Đã lưu tại",
    },
    "日本語": {
        "title": "NexaWorks 運用意思決定支援ツール",
        "upload": "データセット (candidate_dataset.json)",
        "load": "データを読み込む",
        "strict": "厳格なキャッシュ制約",
        "time": "ソルバー制限時間 (秒)",
        "run": "最適化を実行",
        "restore": "初期シナリオに戻す",
        "status": "ステータス",
        "decision": "意思決定",
        "assignment": "担当割当",
        "sales": "商用オプション",
        "explain": "意思決定の説明",
        "warnings": "警告 / 検証 / infeasibility 診断",
        "patch": "Scenario patch (JSON)",
        "apply": "Patch を適用",
        "save": "Scenario + plan を保存",
        "language": "言語",
        "loaded": "データセットを読み込みました。",
        "restored": "初期シナリオに戻しました。",
        "patched": "シナリオを更新しました。もう一度最適化を実行してください。",
        "need_load": "先にデータセットを読み込むかアップロードしてください。",
        "saved": "保存先",
    },
}


def t(language, key):
    return LANG.get(language, LANG["English"]).get(key, LANG["English"].get(key, key))


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
            explain_decisions(result, outcome.get("data_model"), cfg, outcome.get("validation"), outcome.get("post_check"))
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
        return outcome, status, result.get("decision", pd.DataFrame()), result.get("assignment", pd.DataFrame()), sales, explanation, warnings
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


def language_updates(language):
    # Core labels are switched; dynamic solver diagnostics stay machine-generated.
    return (
        gr.update(label=t(language, "upload")),
        gr.update(value=t(language, "load")),
        gr.update(label=t(language, "strict")),
        gr.update(label=t(language, "time")),
        gr.update(value=t(language, "run")),
        gr.update(value=t(language, "restore")),
        gr.update(label=t(language, "status")),
        gr.update(label=t(language, "decision")),
        gr.update(label=t(language, "assignment")),
        gr.update(label=t(language, "sales")),
        gr.update(label=t(language, "explain")),
        gr.update(label=t(language, "warnings")),
        gr.update(label=t(language, "patch")),
        gr.update(value=t(language, "apply")),
        gr.update(value=t(language, "save")),
        gr.update(value=f"# {t(language, 'title')}"),
    )


with gr.Blocks(title="NexaWorks Operations Decision Support Tool") as demo:
    raw_state = gr.State(None)
    initial_state = gr.State(None)
    outcome_state = gr.State(None)

    header = gr.Markdown(f"# {t('English', 'title')}")
    language = gr.Dropdown(list(LANG.keys()), value="English", label="Language", scale=1)
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
    patch_btn.click(patch_action, [raw_state, patch, language], [raw_state, patch_status])
    run_btn.click(
        run_action,
        [raw_state, strict, limit, language],
        [outcome_state, status, decision, assignment, sales, explanation, warnings],
    )
    save_btn.click(save_action, [raw_state, outcome_state, language], [save_status])
    language.change(
        language_updates,
        [language],
        [upload, load_btn, strict, limit, run_btn, restore_btn, load_status, decision, assignment, sales, explanation, warnings, patch, patch_btn, save_btn, header],
    )


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", "7860")))
