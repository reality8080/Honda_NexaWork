from __future__ import annotations

from copy import deepcopy
from typing import Iterable

import pandas as pd


def canonical(value, language: str = "en"):
    if not isinstance(value, dict):
        return value
    return value.get(language, value.get("en", next(iter(value.values()), None)))


# Dataset dùng key "vi"; cột nội bộ/lưu file chuẩn hóa thành "_vn"
_LANG_COL = {"en": "en", "vi": "vn", "vn": "vn", "ja": "ja"}


def records_to_df(records: Iterable[dict], multilingual_fields=(), canonical_language: str = "en") -> pd.DataFrame:
    rows = []
    for rec in records:
        row = deepcopy(rec)
        for field in multilingual_fields:
            value = rec.get(field)
            if isinstance(value, dict):
                for lang, text in value.items():
                    suffix = _LANG_COL.get(lang, lang)
                    row[f"{field}_{suffix}"] = text
                row[f"{field}_canonical"] = canonical(value, canonical_language)
        rows.append(row)
    return pd.DataFrame(rows)


def _df(rows, columns):
    return pd.DataFrame(rows, columns=columns)


def build_model(raw: dict) -> dict[str, pd.DataFrame]:
    language = raw.get("metadata", {}).get("canonical_language", "en")
    dm = {}
    dm["metadata"] = records_to_df([raw["metadata"]], ["scenario_name", "note"], language)
    dm["company"] = records_to_df([raw["company"]], ["decision_context"], language)

    dm["people"] = records_to_df(raw["people"], ["name", "role"], language)
    dm["people"]["person_id"] = dm["people"]["id"]
    dm["person_skills"] = _df(
        [{"person_id": p["id"], "skill": s, "skill_level": level}
         for p in raw["people"] for s, level in p.get("skills", {}).items()],
        ["person_id", "skill", "skill_level"],
    )
    dm["person_languages"] = _df(
        [{"person_id": p["id"], "language": lang}
         for p in raw["people"] for lang in p.get("languages", [])],
        ["person_id", "language"],
    )
    dm["person_unavailability"] = _df(
        [{"person_id": p["id"], "start_date": r["start"], "end_date": r["end"]}
         for p in raw["people"] for r in p.get("unavailable_ranges", [])],
        ["person_id", "start_date", "end_date"],
    )

    dm["customers"] = records_to_df(raw["customers"], ["name"], language)
    dm["customers"]["customer_id"] = dm["customers"]["id"]
    dm["shared_resources"] = records_to_df(raw["shared_resources"], ["name"], language)
    dm["shared_resources"]["resource_id"] = dm["shared_resources"]["id"]

    dm["work_items"] = records_to_df(raw["work_items"], ["title", "notes"], language)
    dm["work_items"]["work_id"] = dm["work_items"]["id"]
    dm["work_items"]["earliest_start_dt"] = pd.to_datetime(dm["work_items"]["earliest_start"], errors="coerce")
    dm["work_items"]["due_date_dt"] = pd.to_datetime(dm["work_items"]["due_date"], errors="coerce")
    dm["work_skills"] = _df(
        [{"work_id": w["id"], "skill": x["skill"], "min_level": x["min_level"]}
         for w in raw["work_items"] for x in w.get("required_skills", [])],
        ["work_id", "skill", "min_level"],
    )
    dm["work_languages"] = _df(
        [{"work_id": w["id"], "language": lang}
         for w in raw["work_items"] for lang in w.get("required_languages", [])],
        ["work_id", "language"],
    )
    dm["work_resources"] = _df(
        [{"work_id": w["id"], "resource_id": x["resource_id"], "hours": x["hours"]}
         for w in raw["work_items"] for x in w.get("resource_requirements", [])],
        ["work_id", "resource_id", "hours"],
    )
    dm["work_dependencies"] = _df(
        [{"work_id": w["id"], "depends_on_work_id": dep}
         for w in raw["work_items"] for dep in w.get("dependencies", [])],
        ["work_id", "depends_on_work_id"],
    )
    dm["work_conflicts"] = _df(
        [{"work_id": w["id"], "conflicts_with_work_id": c}
         for w in raw["work_items"] for c in w.get("conflicts", [])],
        ["work_id", "conflicts_with_work_id"],
    )

    dm["commercial_options"] = records_to_df(raw["commercial_options"], ["label", "notes"], language)
    dm["commercial_options"]["work_id"] = dm["commercial_options"]["work_item_id"]
    dm["option_dependencies"] = _df(
        [{"option_id": o["option_id"], "depends_on_work_id": dep}
         for o in raw["commercial_options"] for dep in o.get("dependencies", [])],
        ["option_id", "depends_on_work_id"],
    )

    work_ids = {w["id"] for w in raw["work_items"]}
    option_ids = {o["option_id"] for o in raw["commercial_options"]}
    effect_rows, target_rows = [], []
    for e in raw["portfolio_effects"]:
        eff = e.get("effect", {})
        effect_rows.append({
            "effect_id": e["id"], "trigger": e["trigger"],
            "effect_type": eff.get("type"), "value": eff.get("value"),
            "value_jpy": eff.get("value_jpy"), "probability": eff.get("probability"),
            "description_canonical": canonical(eff.get("description", {}), language),
        })
        for target in e.get("targets", []):
            target_type = ("work" if target in work_ids else
                           "commercial_option" if target in option_ids else
                           "company_cash" if target == "company_cash" else "unresolved")
            target_rows.append({"effect_id": e["id"], "target_id": target, "target_type": target_type})
    dm["portfolio_effects"] = _df(effect_rows, ["effect_id", "trigger", "effect_type", "value", "value_jpy", "probability", "description_canonical"])
    dm["portfolio_effect_targets"] = _df(target_rows, ["effect_id", "target_id", "target_type"])
    return dm


RELATIONSHIP_MAP = pd.DataFrame([
    ["work_items", "customer_id", "customers.id", "Work → Customer"],
    ["work_items", "dependencies", "work_items.id", "Work → Prerequisite Work"],
    ["work_items", "resource_requirements", "shared_resources.id", "Work → Shared Resource"],
    ["work_items", "required_skills", "person_skills.skill", "Work → Qualified Person"],
    ["work_items", "required_languages", "person_languages.language", "Work → Language Coverage"],
    ["commercial_options", "work_item_id", "work_items.id", "Option → Sales Opportunity"],
    ["portfolio_effects", "trigger", "work_items.id", "Trigger → Portfolio Effect"],
], columns=["from_table", "from_field", "to_field", "meaning"])