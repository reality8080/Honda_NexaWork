from __future__ import annotations

from copy import deepcopy

EDITABLE_ENTITY_KEYS={"people":"id","customers":"id","shared_resources":"id","work_items":"id","commercial_options":"option_id","portfolio_effects":"id"}

def apply_patch(raw, patch):
    data=deepcopy(raw)
    for section,changes in (patch or {}).items():
        if section not in data: continue
        if section=="company":
            if not isinstance(changes,dict): raise TypeError("company patch must be a dict")
            data[section].update(deepcopy(changes)); continue
        if section not in EDITABLE_ENTITY_KEYS: raise KeyError(f"Unsupported patch section: {section}")
        if not isinstance(changes,dict): raise TypeError(f"Patch {section} must map id to field changes")
        key=EDITABLE_ENTITY_KEYS[section]; records={r.get(key):r for r in data[section]}
        for rid,fields in changes.items():
            if rid not in records: raise KeyError(f"Unknown {section}.{key}={rid}")
            if not isinstance(fields,dict): raise TypeError("Record patch must be a dict")
            records[rid].update(deepcopy(fields))
    return data

def edit_record(raw, section, record_id, changes):
    if section=="company":
        data=deepcopy(raw); data["company"].update(deepcopy(changes)); return data
    key=EDITABLE_ENTITY_KEYS[section]; data=deepcopy(raw)
    for rec in data[section]:
        if rec.get(key)==record_id: rec.update(deepcopy(changes)); return data
    raise KeyError(f"Unknown {section}.{key}={record_id}")

def add_record(raw, section, record):
    key=EDITABLE_ENTITY_KEYS[section]; data=deepcopy(raw)
    if key not in record: raise ValueError(f"New record requires {key}")
    if any(r.get(key)==record[key] for r in data[section]): raise ValueError(f"Duplicate ID: {record[key]}")
    data[section].append(deepcopy(record)); return data

def delete_record(raw, section, record_id):
    key=EDITABLE_ENTITY_KEYS[section]; data=deepcopy(raw)
    filtered=[r for r in data[section] if r.get(key)!=record_id]
    if len(filtered)==len(data[section]): raise KeyError(f"Unknown {section}.{key}={record_id}")
    data[section]=filtered; return data

def restore_initial_dataset(initial_raw): return deepcopy(initial_raw)
