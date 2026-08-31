from __future__ import annotations
import json
from pathlib import Path
from nexaworks.scenario.runner import run_scenario
from nexaworks.i18n import localize_value

# Chuẩn lưu file: chỉ _en / _vn / _ja (không bao giờ _vi)
_LANG_SUFFIX = ("en", "vn", "ja")
_TEXT_COLS = {
    "title", "label", "decision", "reason", "message", "status", "code",
    "selected", "notes", "warnings",
}


def _to_vn_suffix(key: str) -> str:
    """Đổi hậu tố _vi → _vn."""
    if key.endswith("_vi"):
        return key[:-3] + "_vn"
    return key


def _is_nan(v) -> bool:
    return v is None or (isinstance(v, float) and v != v)


def _multilang_records(df):
    """Lưu records: mỗi trường text có đúng 3 cột _en / _vn / _ja, không trùng _vi."""
    if df is None or not hasattr(df, "to_dict") or getattr(df, "empty", True):
        return []
    records = df.to_dict(orient="records")
    out = []
    for row in records:
        new_row = {}
        for k, v in row.items():
            # Dict {en,vi,ja} → bung thành cột chuẩn
            if isinstance(v, dict) and set(v.keys()) <= {"en", "vi", "ja", "vn"}:
                for code, text in v.items():
                    if _is_nan(text):
                        continue
                    suffix = "vn" if code in ("vi", "vn") else code
                    new_row[f"{k}_{suffix}"] = text
                continue
            if _is_nan(v):
                continue
            nk = _to_vn_suffix(k)
            # Không ghi đè nếu đã có giá trị tốt hơn
            if nk not in new_row:
                new_row[nk] = v

        # Bổ sung bản dịch cho cột text scalar (decision, selected, …)
        for col in list(new_row.keys()):
            if col in _TEXT_COLS and not any(f"{col}_{s}" in new_row for s in _LANG_SUFFIX):
                val = new_row[col]
                new_row[f"{col}_en"] = localize_value(val, "English")
                new_row[f"{col}_vn"] = localize_value(val, "Tiếng Việt")
                new_row[f"{col}_ja"] = localize_value(val, "日本語")

        # Đảm bảo đủ 3 hậu tố + xóa mọi _vi
        bases = set()
        for k in list(new_row.keys()):
            if k.endswith("_vi"):
                base = k[:-3]
                new_row.setdefault(f"{base}_vn", new_row[k])
                del new_row[k]
                bases.add(base)
            else:
                for s in _LANG_SUFFIX:
                    if k.endswith(f"_{s}"):
                        bases.add(k[: -(len(s) + 1)])
                        break
        for base in bases:
            en = new_row.get(f"{base}_en")
            if en is not None:
                new_row.setdefault(f"{base}_vn", en)
                new_row.setdefault(f"{base}_ja", en)
            new_row.pop(f"{base}_vi", None)

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