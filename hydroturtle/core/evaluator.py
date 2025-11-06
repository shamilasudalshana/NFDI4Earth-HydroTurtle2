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

def _expand_token(token, row, row_index, ctx, slug: str | None = None):
    def _rid():
        id_col = ctx["columns"].get("id")
        return row.get(id_col) if id_col else row.get("__RID__", "")

    if token == "@catchment":
        return ctx["uri_templates"]["catchment"].format(id=_rid(), rowIndex=row_index)
    if token == "@sensor":
        return ctx["uri_templates"]["sensor"].format(id=_rid(), rowIndex=row_index)
    if token == "@collection":
        return ctx["uri_templates"]["collection"].format(id=_rid(), rowIndex=row_index)
    if token == "@observation":
        # need slug to distinguish variables (precipitation, pet, …)
        slug_val = (slug or "").lower() or "obs"
        tpl = ctx["uri_templates"].get(
            "observation",
            "hyobs:observation_{id}_{rowIndex}_{slug}"
        )
        return tpl.format(id=_rid(), rowIndex=row_index, slug=slug_val)
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

    # compat switch (preserve old ^^xsd:* shorthand)
    use_legacy = mapping.get("compat", {}).get("typed_literal_shorthand", True)

    triples_by_subject = {}
    def add_triple(s, p, o):
        triples_by_subject.setdefault(s, []).append((p, o))

    # NEW: figure out a file-scoped ID if mapping wants it
    file_id = _derive_id_from_filename(csv_path, ctx)

    for i, row in enumerate(iter_rows(csv_path, csv_encoding=csv_encoding)):
        # compute the chosen row id (column id OR filename id)
        rid = _row_id(row, ctx, file_id)
        # row2 carries the resolved id for all helper expansions
        row2 = dict(row)
        row2["__RID__"] = rid

        for col, spec in rules.items():
            val = row.get(col)
            if val is None:
                continue
            if isinstance(val, str) and val.strip().lower() in {"", "na", "nan"}:
                continue

            subj_tpl = ctx["uri_templates"].get("observation", "hyobs:observation_{id}_{rowIndex}")
            slug = col.lower()
            s = subj_tpl.format(id=rid, rowIndex=i, slug=slug)

            # allow first entry to override subject
            spec_iter = iter(spec)
            first = next(spec_iter)
            if isinstance(first, list) and first and first[0] == "@subject":
                subj_token = first[1]  # "@sensor" | "@catchment" | "@collection" | template
                if isinstance(subj_token, str) and subj_token.startswith("@"):
                    s = _expand_token(subj_token, row2, i, ctx, slug=slug)
                else:
                    s = str(subj_token).format(id=rid, rowIndex=i, slug=slug)
            else:
                spec_iter = iter(spec)

            for entry in spec_iter:
                p, o = entry[0], entry[1]

                if use_legacy and isinstance(o, str) and o.startswith("^^"):
                    csv_val = row[col]
                    o_eval = f"\"{csv_val}\"^^{o[2:]}"
                else:
                    o_eval = _render_obj(
                        o, row2,
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
        
        # --- reprojection directive ---
        if "@point" in spec:
            pt = spec["@point"]
            E = float(row.get(pt["easting"]["@col"]))
            N = float(row.get(pt["northing"]["@col"]))
            src = pt.get("src_crs")
            dst = pt.get("dst_crs", "EPSG:4326")

            from pyproj import Transformer
            tf = Transformer.from_crs(src, dst, always_xy=True)
            lon, lat = tf.transform(E, N)

            # you can round if you like
            lon_s = f"{lon:.8f}"
            lat_s = f"{lat:.8f}"

            # merge into template vars
            tpl = spec["@template"]
            lit = tpl.format(lon=lon_s, lat=lat_s)
            cast = spec.get("as")
            return f"\"{lit}\"{cast}" if cast else f"\"{lit}\"" 

        # (Optional) point reprojection block could go here later:
        # if "@point" in spec:  ...  (convert easting/northing -> lon/lat)

    # fallback
    return str(spec)

def _render_obj(spec, row, row_index, ctx, current_col=None, use_legacy=True):
    # 1) typed-literal shorthand anywhere (nested or top-level)
    if use_legacy and isinstance(spec, str) and spec.startswith("^^"):
        # use the CSV value of the column whose rule we're currently executing
        v = "" if current_col is None else row.get(current_col, "")
        return f"\"{v}\"{spec}"  # e.g. -> "31"^^xsd:integer

    # 2) plain strings: tokens, QNames/IRIs, normal literals
    if isinstance(spec, str):
        if spec.startswith("@"):
            return _expand_token(spec, row, row_index, ctx, slug=(current_col or "").lower())
        return spec

    # 3) ["select", "$col", ["Case","IRI"], ..., ["default","IRI"]]
    if isinstance(spec, list) and spec and spec[0] == "select":
        _, keyexpr, *pairs = spec
        key = row.get(keyexpr.lstrip("$"), "")
        default_val, chosen = None, None
        for k, v in pairs:
            if k == "default":
                default_val = v
            elif str(key) == str(k):
                chosen = v
                break
        return chosen if chosen is not None else (default_val if default_val is not None else str(key))

    # 4) blank node: list of [p, o] pairs
    if isinstance(spec, list) and spec and isinstance(spec[0], list) and len(spec[0]) == 2:
        parts = []
        for p, o in spec:
            o_eval = _render_obj(o, row, row_index, ctx, current_col=current_col, use_legacy=use_legacy)
            parts.append(f"{p} {o_eval}")
        return "[ " + " ; ".join(parts) + " ]"

    # 5) dict objects (@col / @template)
    if isinstance(spec, dict):
        if "@col" in spec:
            v = row.get(spec["@col"], "")
            cast = spec.get("as")
            return f"\"{v}\"{cast}" if cast and cast.startswith("^^") else str(v)
        if "@template" in spec:
            tpl = spec["@template"]
            src = spec.get("from", {})
            resolved = {k: (str(row.get(v["@col"], "")) if isinstance(v, dict) and "@col" in v else str(v))
                        for k, v in src.items()}
            lit = _render_template(tpl, resolved)
            cast = spec.get("as")
            # WKT etc. should be a quoted literal if cast is present
            return f"\"{lit}\"{cast}" if cast else lit

    # 6) fallback
    return str(spec)



# --- helpers ---------------------------------------------------------------
import re
from pathlib import Path

def _derive_id_from_filename(csv_path: str, ctx: dict) -> str | None:
    d = (ctx or {}).get("derive", {}).get("id_from_filename")
    if not d:
        return None
    pat = d.get("regex")
    grp = d.get("group", 1)
    if not pat:
        return None
    m = re.search(pat, Path(csv_path).name)
    return m.group(grp) if m else None

def _row_id(row: dict, ctx: dict, file_id: str | None) -> str:
    id_col = (ctx or {}).get("columns", {}).get("id")
    if id_col:
        return str(row.get(id_col, ""))
    if file_id:
        return str(file_id)
    return ""  # last resort; you could raise if you want to be strict



