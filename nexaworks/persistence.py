from __future__ import annotations
import json
from pathlib import Path
from nexaworks.scenario.runner import run_scenario
from nexaworks.i18n import localize_value

# Cột text cần lưu đa ngôn ngữ khi save
_TEXT_COLS = {
    "title", "label", "decision", "reason", "message", "status", "code",
    "selected", "notes", "warnings",
}


def _multilang_records(df):
    """Lưu records kèm cột _en / _vn / _ja cho các trường text."""
    if df is None or not hasattr(df, "to_dict") or getattr(df, "empty", True):
        return []
    records = df.to_dict(orient="records")
    out = []
    for row in records:
        new_row = dict(row)
        for col in list(row.keys()):
            # Đã có sẵn title_en/title_vi/title_ja → đổi vi→vn cho chuẩn yêu cầu
            if col.endswith("_vi"):
                base = col[:-3]
                new_row[f"{base}_vn"] = row[col]
            elif col.endswith("_en") or col.endswith("_ja"):
                pass  # giữ nguyên
            elif col in _TEXT_COLS and not any(
                f"{col}_{s}" in row for s in ("en", "vi", "ja")
            ):
                # Chỉ có 1 giá trị → nhân bản 3 ngôn ngữ (dịch decision/bool)
                val = row[col]
                new_row[f"{col}_en"] = localize_value(val, "English")
                new_row[f"{col}_vn"] = localize_value(val, "Tiếng Việt")
                new_row[f"{col}_ja"] = localize_value(val, "日本語")
        out.append(new_row)
    return out


def save_scenario(path, raw, scenario_id="scenario"):
    payload = {"scenario_id": scenario_id, "dataset": raw}
    Path(path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return str(path)


def load_scenario(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))["dataset"]


def save_plan(path, result):
    payload = {
        k: result.get(k)
        for k in [
            "solver_status",
            "objective_value",
            "cash_end_actual_jpy",
            "cash_end_expected_jpy",
            "cash_shortfall_jpy",
        ]
    }
    for key in ["decision", "assignment", "schedule", "commercial_option"]:
        df = result.get(key)
        payload[key] = _multilang_records(df) if hasattr(df, "to_dict") else []
    Path(path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return str(path)


def decision_signature(result):
    d = result.get("decision")
    if d is None or d.empty:
        return []
    cols = [
        c
        for c in ["work_id", "decision", "selected", "start_hour", "end_hour", "effective_hours"]
        if c in d.columns
    ]
    return d[cols].sort_values("work_id").to_dict(orient="records")


def reproducibility_check(raw, seed=42):
    r1 = run_scenario(raw, "repro_1", seed=seed, workers=1)
    r2 = run_scenario(raw, "repro_2", seed=seed, workers=1)
    return {
        "same_decision": decision_signature(r1["result"]) == decision_signature(r2["result"]),
        "run_1_status": r1["solver_status"],
        "run_2_status": r2["solver_status"],
    }