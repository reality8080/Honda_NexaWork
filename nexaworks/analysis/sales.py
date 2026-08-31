from __future__ import annotations
import pandas as pd
from nexaworks.engine.financials import option_financials


def _ml_text(row, field: str) -> dict:
    """Lấy text đa ngôn ngữ. Chuẩn cột: _en / _vn / _ja (đọc cả _vi cũ)."""
    out = {}
    # Cột đã bung: ưu tiên _vn, chấp nhận _vi legacy
    mapping = {"en": ("en",), "vn": ("vn", "vi"), "ja": ("ja",)}
    for std, aliases in mapping.items():
        for a in aliases:
            col = f"{field}_{a}"
            if col in row.index and pd.notna(row.get(col)):
                out[std] = row[col]
                break
    # Fallback: field là dict {en,vi,ja}
    raw = row.get(field)
    if isinstance(raw, dict):
        if "en" not in out and raw.get("en"):
            out["en"] = raw["en"]
        if "vn" not in out and (raw.get("vi") or raw.get("vn")):
            out["vn"] = raw.get("vi") or raw.get("vn")
        if "ja" not in out and raw.get("ja"):
            out["ja"] = raw["ja"]
    canon = row.get(f"{field}_canonical")
    if isinstance(canon, float) and canon != canon:
        canon = None
    if not canon:
        canon = out.get("en") or (next(iter(out.values())) if out else None)
    if canon and "en" not in out:
        out["en"] = canon
    return out


def sales_option_analysis(dm, result, planning_days, config):
    chosen = set(result.get("commercial_option", pd.DataFrame()).get("option_id", []))
    rows = []
    for _, o in dm["commercial_options"].iterrows():
        p = float(o["estimated_win_probability"])
        margin = (float(o["price_jpy"]) - float(o["direct_cost_jpy"])) * p
        cash = float(o["price_jpy"]) * p if float(o["payment_days"]) <= planning_days else 0
        labels = _ml_text(o, "label")
        rows.append({
            "work_id": o["work_id"],
            "option_id": o["option_id"],
            "label": labels.get("en"),
            "label_en": labels.get("en"),
            "label_vn": labels.get("vn") or labels.get("en"),
            "label_ja": labels.get("ja") or labels.get("en"),
            "price_jpy": o["price_jpy"],
            "win_probability": p,
            "expected_margin_jpy": round(margin),
            "delivery_hours": o["delivery_hours"],
            "payment_days": o["payment_days"],
            "cash_in_horizon_jpy": round(cash),
            "warranty_months": o["warranty_months"],
            "follow_on_value_jpy": o["follow_on_value_jpy"],
            "integrated_utility": round(option_financials(o.to_dict(), config)),
            "selected_by_solver": o["option_id"] in chosen,
        })
    return pd.DataFrame(rows).sort_values(
        ["work_id", "integrated_utility"], ascending=[True, False]
    )