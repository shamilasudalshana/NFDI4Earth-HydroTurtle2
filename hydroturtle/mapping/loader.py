from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def _from_new_configuration(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adapt a 'new-style' mapping JSON (with top-level 'configuration')
    into the 'old-style' structure that hydroturtle.core.evaluator.convert
    expects:

        {
          "compat": {...},
          "prefixes": {...},
          "derive": {...},
          "context": {
            "columns": {...},
            "csv": {...},
            "uri_templates": {...},
            "time_defaults": {
              "resultTime": {
                "from": ["$date", ...],
                "format": ["%Y-%m-%d", ...]
              }
            }
          },
          "rules": {...}
        }

    This keeps the evaluator logic unchanged.
    """

    compat: Dict[str, Any] = raw.get("compat", {"typed_literal_shorthand": True})
    prefixes: Dict[str, str] = raw.get("prefixes", {})
    rules: Dict[str, Any] = raw.get("rules", {})

    cfg: Dict[str, Any] = raw.get("configuration", {})
    csv_cfg: Dict[str, Any] = cfg.get("csv", {}) or {}
    col_types: Dict[str, Any] = cfg.get("column_types", {}) or {}

    # ------------------------------------------------------------------
    # ID handling
    # ------------------------------------------------------------------
    id_cfg: Dict[str, Any] = col_types.get("id", {}) or {}
    id_column_name: Optional[str] = id_cfg.get("column_name")

    id_from_filename: Dict[str, Any] = id_cfg.get("id_from_filename", {}) or {}

    derive: Dict[str, Any] = {}
    if id_from_filename:
        regex = id_from_filename.get("regex")
        # Hydrologist JSON uses "regex-split" for the group index
        group = (
            id_from_filename.get("group")
            or id_from_filename.get("regex-split")
            or 1
        )
        derive["id_from_filename"] = {
            "regex": regex,
            "group": group,
        }

    # ------------------------------------------------------------------
    # Date / time handling
    # ------------------------------------------------------------------
    date_cfg: Dict[str, Any] = col_types.get("date", {}) or {}
    time_cfg: Dict[str, Any] = col_types.get("time", {}) or {}

    date_col_name: Optional[str] = date_cfg.get("column_name")
    date_fmt: Optional[str] = date_cfg.get("format")

    time_col_name: Optional[str] = time_cfg.get("column_name")
    time_fmt: Optional[str] = time_cfg.get("format")

    # Multi-component dates (e.g. LamaH-CE: YYYY, MM, DD)
    components: List[Dict[str, Any]] = date_cfg.get("components") or []

    result_from: List[str] = []
    result_fmt: List[str] = []

    if date_col_name and date_fmt:
        # Simple case: single date column
        result_from.append(f"${date_col_name}")
        result_fmt.append(date_fmt)

        # If we also have an explicit time column, combine it
        if time_col_name and time_fmt:
            result_from.append(f"${time_col_name}")
            result_fmt.append(time_fmt)

    elif components:
        # Multi-column date: ["YYYY","MM","DD", ...]
        for comp in components:
            cname = comp.get("column_name")
            cfmt = comp.get("format")
            if cname and cfmt:
                result_from.append(f"${cname}")
                result_fmt.append(cfmt)

    # Build the legacy time_defaults structure
    time_defaults: Dict[str, Any] = {}
    if result_from:
        time_defaults["resultTime"] = {
            "from": result_from,
            "format": result_fmt,
        }

    # ------------------------------------------------------------------
    # Columns + URI templates
    # ------------------------------------------------------------------
    columns: Dict[str, Any] = {
        "id": id_column_name,
        "date": date_col_name,
        "time": time_col_name,
    }

    uri_templates: Dict[str, str] = (
        col_types.get("templates_for_subject_id", {}) or {}
    )

    context: Dict[str, Any] = {
        "columns": columns,
        "csv": csv_cfg,
        "uri_templates": uri_templates,
    }
    if time_defaults:
        context["time_defaults"] = time_defaults

    # ------------------------------------------------------------------
    # Final legacy-like mapping dict
    # ------------------------------------------------------------------
    legacy: Dict[str, Any] = {
        "compat": compat,
        "prefixes": prefixes,
        "context": context,
        "rules": rules,
    }
    if derive:
        legacy["derive"] = derive

    return legacy


def load_mapping(mapping_path: str, json_encoding: str = "utf-8") -> Dict[str, Any]:
    """
    Unified mapping loader:
    - Old format: expects a top-level 'context' → returned as-is.
    - New format: expects a top-level 'configuration' → adapted to legacy form.
    """
    text = Path(mapping_path).read_text(encoding=json_encoding)
    raw = json.loads(text)

    # Old-style mapping (what you have today)
    if "context" in raw and "configuration" not in raw:
        return raw

    # New-style mapping with 'configuration'
    if "configuration" in raw:
        return _from_new_configuration(raw)

    raise ValueError(
        f"Unrecognized mapping JSON in {mapping_path!r}: "
        f"expected 'context' or 'configuration' at top level."
    )
