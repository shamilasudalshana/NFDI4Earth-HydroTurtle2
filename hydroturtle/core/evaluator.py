import json
import csv
import re
from datetime import datetime, date, time
from pathlib import Path

# --- time helpers ------------------------------------------------------------
def _iso_datetime_from(parts, fmts):
    s = " ".join(parts).strip()
    # try patterns provided by mapping (can be multiple)
    for f in (fmts or []):
        try:
            dt = datetime.strptime(s, f)
            return f"\"{dt.strftime('%Y-%m-%dT00:00:00Z')}\"^^xsd:dateTime"
        except Exception:
            pass
    # ISO fallback
    try:
        dt = datetime.fromisoformat(s)
        if isinstance(dt, date) and not isinstance(dt, datetime):
            dt = datetime.combine(dt, time())
        return f"\"{dt.strftime('%Y-%m-%dT00:00:00Z')}\"^^xsd:dateTime"
    except Exception:
        raise ValueError(f"Could not parse date '{s}' with formats {fmts} or ISO YYYY-MM-DD")

def _expand_token(token, row, row_index, ctx):
    if token == "@catchment":
        return ctx["uri_templates"]["catchment"].format(id=row[ctx["columns"]["id"]], rowIndex=row_index)
    if token == "@sensor":
        return ctx["uri_templates"]["sensor"].format(id=row[ctx["columns"]["id"]], rowIndex=row_index)
    if token == "@collection":
        return ctx["uri_templates"]["collection"].format(id=row[ctx["columns"]["id"]], rowIndex=row_index)
    if token == "@geom":
        # use template if present; else default
        geom_tpl = ctx["uri_templates"].get("geom", "hyobs:geomPoint_{id}")
        return geom_tpl.format(id=row[ctx["columns"]["id"]], rowIndex=row_index)
    if token == "@resultTime":
        t = ctx["time_defaults"]["resultTime"]
        cols = [row[c.lstrip("$")] for c in t["from"]]
        return _iso_datetime_from(cols, t.get("format", []))
    return token


# --- value evaluators --------------------------------------------------------
def _eval_object(obj, row, row_index, ctx):
    # simple string with {id} templating
    if isinstance(obj, str):
        if obj.startswith("@"):
            return _expand_token(obj, row, row_index, ctx)
        return obj.format(id=row.get(ctx["columns"]["id"], ""), rowIndex=row_index)

    # ["select", "$col", ["Case","Val"], ["default","Val"]]
    if isinstance(obj, list) and obj and obj[0] == "select":
        _, keyexpr, *pairs = obj
        key = row[keyexpr.lstrip("$")]
        default_val = None
        for pair in pairs:
            k, v = pair
            if k == "default":
                default_val = v
            elif str(key) == str(k):
                return v
        return default_val if default_val is not None else str(key)

    # bnode: a list of [p, o] pairs -> return single-line bnode "[ p o ; p o ; ... ]"
    if isinstance(obj, list) and obj and isinstance(obj[0], list) and len(obj[0]) == 2:
        parts = []
        for p,o in obj:
            o_eval = _eval_object(o, row, row_index, ctx)
            parts.append(f"{p} {o_eval}")
        return "[ " + " ; ".join(parts) + " ]"

    # dict or other types not used in this MVP
    return str(obj)

# --- mapping/convert orchestrator -------------------------------------------
def load_mapping(mapping_path: str, json_encoding: str = "utf-8"):
    import json
    from pathlib import Path
    return json.loads(Path(mapping_path).read_text(encoding=json_encoding))


def iter_rows(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        yield from csv.DictReader(f)

def convert(csv_path: str, mapping: dict, csv_encoding: str | None = None):
    ctx = mapping["context"]
    prefixes = mapping["prefixes"]
    rules = mapping["rules"]

    # >>> compat switch (default True to preserve old behavior)
    use_legacy = mapping.get("compat", {}).get("typed_literal_shorthand", True)

    triples_by_subject = {}

    def add_triple(s, p, o):
        triples_by_subject.setdefault(s, []).append((p, o))

    # >>> pass csv_encoding here <<<
    for i, row in enumerate(iter_rows(csv_path, csv_encoding=csv_encoding)):
        for col, spec in rules.items():
            if col not in row or row[col] in (None, "", "NA"):
                continue

            subj_tpl = ctx["uri_templates"].get("observation", "hyobs:observation_{id}_{rowIndex}")
            slug = col.lower()
            s = subj_tpl.format(id=row[ctx["columns"]["id"]], rowIndex=i, slug=slug)

            # allow first entry to override subject: ["@subject", "@sensor"] or ["@subject", "@catchment"]
            spec_iter = iter(spec)
            first = next(spec_iter)
            if isinstance(first, list) and first and first[0] == "@subject":
                subj_token = first[1]  # "@sensor" | "@catchment" | "@collection" | custom template
                if subj_token.startswith("@"):
                    s = _expand_token(subj_token, row, i, ctx)
                else:
                    s = subj_token.format(id=row[ctx["columns"]["id"]], rowIndex=i, slug=slug)
            else:
                # didn't override; put the first back
                spec_iter = iter(spec)

            for entry in spec_iter:
                p, o = entry[0], entry[1]

                if use_legacy and isinstance(o, str) and o.startswith("^^"):
                    csv_val = row[col]
                    o_eval = f"\"{csv_val}\"^^{o[2:]}"
                else:
                    o_eval = _render_obj(
                        o, row,
                        row_index=i,
                        ctx=ctx,
                        current_col=col,
                        use_legacy=use_legacy
                    )

                add_triple(s, p, o_eval)


    return triples_by_subject, prefixes

def run_convert(csv_path, mapping_path, out_path):
    triples_by_subject, prefixes = convert(csv_path, load_mapping(mapping_path))
    from hydroturtle.io.ttl_writer import write_turtle
    write_turtle(triples_by_subject, prefixes, out_path)
    return out_path

# --- Encoding detection & robust CSV reading ---------------------------------
def detect_encoding(path: str) -> str | None:
    """
    Try to detect file encoding using charset-normalizer.
    Returns an encoding name (e.g., 'cp1252', 'utf-8') or None.
    """
    try:
        from charset_normalizer import from_path
        best = from_path(path).best()
        if best and best.encoding:
            return best.encoding
    except Exception:
        pass
    return None

def iter_rows(csv_path: str, csv_encoding: str | None = None):
    """
    Robust CSV reader:
      1) uses explicit csv_encoding if provided,
      2) else tries detect_encoding(),
      3) else tries a fallback list: utf-8, utf-8-sig, cp1252, latin-1,
      4) finally uses utf-8 with errors='replace' to never crash.
    """
    import csv

    def _yield_with(enc: str, strict: bool = True):
        with open(csv_path, newline="", encoding=enc, errors=("strict" if strict else "replace")) as f:
            reader = csv.DictReader(f)
            # Touch first row to validate decoding early
            first = next(reader)
            yield first
            for r in reader:
                yield r

    # 1) explicit
    if csv_encoding:
        yield from _yield_with(csv_encoding, strict=True)
        return

    # 2) auto-detect
    enc = detect_encoding(csv_path)
    if enc:
        try:
            # print(f"[hydroturtle] Detected CSV encoding: {enc}")
            yield from _yield_with(enc, strict=True)
            return
        except Exception:
            pass

    # 3) common fallbacks
    for enc_try in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            # print(f"[hydroturtle] Trying CSV encoding: {enc_try}")
            yield from _yield_with(enc_try, strict=True)
            return
        except Exception:
            continue

    # 4) last resort: never crash (may replace bad bytes)
    # print("[hydroturtle] Falling back to utf-8 with replacement.")
    yield from _yield_with("utf-8", strict=False)

# hydroturtle/core/evaluator.py

def _render_template(tpl: str, mapping: dict) -> str:
    return tpl.format(**mapping)

def eval_value(spec, row):
    # primitive string (already a QName/IRI or typed literal marker)
    if isinstance(spec, str):
        return spec

    # object specs
    if isinstance(spec, dict):
        # Column reference
        if "@col" in spec:
            v = row.get(spec["@col"], "")
            cast = spec.get("as")
            if cast and cast.startswith("^^"):  # typed literal
                return f"\"{v}\"{cast}"
            return str(v)

        # Template expansion (for WKT, etc.)
        if "@template" in spec:
            tpl = spec["@template"]
            src = spec.get("from", {})
            resolved = {}
            for k, v in src.items():
                if isinstance(v, dict) and "@col" in v:
                    resolved[k] = str(row.get(v["@col"], ""))
                else:
                    resolved[k] = str(v)
            lit = _render_template(tpl, resolved)
            cast = spec.get("as")
            return f"\"{lit}\"{cast}" if cast else f"\"{lit}\""

        # (Optional) point reprojection block could go here later:
        # if "@point" in spec:  ...  (convert easting/northing -> lon/lat)

    # fallback
    return str(spec)

# add row_index and ctx params
def _render_obj(spec, row, row_index=None, ctx=None, current_col=None, use_legacy=True):
    # Legacy typed-literal shorthand: "^^xsd:TYPE" => use row[current_col]
    if use_legacy and isinstance(spec, str) and spec.startswith("^^"):
        v = row.get(current_col, "")
        return f"\"{v}\"^^{spec[2:]}"

    # NEW: expand @tokens like @catchment, @sensor, @geom, @collection, @resultTime
    if isinstance(spec, str) and spec.startswith("@"):
        # reuse your existing expander
        return _expand_token(spec, row, row_index, ctx)

    # Inline bnode: [["p","o"], ...]
    if isinstance(spec, list) and spec and isinstance(spec[0], list) and len(spec[0]) == 2:
        parts = []
        for p, o in spec:
            parts.append(
                f"{p} {_render_obj(o, row, row_index=row_index, ctx=ctx, current_col=current_col, use_legacy=use_legacy)}"
            )
        return "[ " + " ; ".join(parts) + " ]"

    # Dict or plain string
    return eval_value(spec, row) if isinstance(spec, (dict, str)) else str(spec)


