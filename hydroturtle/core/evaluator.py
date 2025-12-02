import json
import csv
import re
from datetime import datetime, date, time
from pathlib import Path
from hydroturtle.mapping.loader import load_mapping as _load_mapping

# --- time helpers ------------------------------------------------------------
def _iso_datetime_from(parts, fmts):
    """
    parts: list of strings (e.g., ["1981","01","01","13","45"])
    fmts:  either ["%Y-%m-%d"] or ["%Y","%m","%d","%H","%M"] etc.
    Returns an xsd:dateTime literal at 00:00Z if no time, else uses given time.
    """
    s = " ".join([str(p).strip() for p in parts if p is not None])
    if not s:
        raise ValueError("Empty date/time parts")

    # If fmts are component-wise and match the number of parts, join with space
    if isinstance(fmts, list) and len(fmts) > 1:
        if len(fmts) == len(parts):
            try:
                fmt = " ".join(fmts)
                dt = datetime.strptime(s, fmt)
                # If user gave only date (no time tokens), normalize to 00:00:00Z
                if "%H" not in fmt and "%M" not in fmt and "%S" not in fmt:
                    dt = datetime(dt.year, dt.month, dt.day)
                return f"\"{dt.strftime('%Y-%m-%dT%H:%M:%SZ')}\"^^xsd:dateTime"
            except Exception:
                pass
        # else fall through to single-format attempt

    # Try each full-format string (e.g., ["%Y-%m-%d", "%Y/%m/%d %H:%M"])
    for f in (fmts or []):
        try:
            dt = datetime.strptime(s, f)
            # If format has no time directives, set time to 00:00:00Z
            if all(x not in f for x in ("%H", "%M", "%S")):
                dt = datetime(dt.year, dt.month, dt.day)
            return f"\"{dt.strftime('%Y-%m-%dT%H:%M:%SZ')}\"^^xsd:dateTime"
        except Exception:
            pass

    # ISO fallback
    try:
        # Allow "YYYY-MM-DD" or "YYYY-MM-DD HH:MM[:SS]"
        dt = datetime.fromisoformat(s.replace("Z","").replace("z",""))
        if isinstance(dt, date) and not isinstance(dt, datetime):
            dt = datetime.combine(dt, time())
        return f"\"{dt.strftime('%Y-%m-%dT%H:%M:%SZ')}\"^^xsd:dateTime"
    except Exception:
        raise ValueError(f"Could not parse date '{s}' with formats {fmts or '[]'}")

def _expand_token(token, row, row_index, ctx, slug: str | None = None):
    rid = _row_id(row, ctx, ctx.get("_file_id"))
    # allow slug placeholder in templates
    if token == "@catchment":
        return ctx["uri_templates"]["catchment"].format(id=rid, rowIndex=row_index, slug=(slug or ""))
    if token == "@sensor":
        return ctx["uri_templates"]["sensor"].format(id=rid, rowIndex=row_index, slug=(slug or ""))
    if token == "@collection":
        return ctx["uri_templates"]["collection"].format(id=rid, rowIndex=row_index, slug=(slug or ""))
    if token == "@observation":
        tpl = ctx["uri_templates"].get("observation", "hyobs:observation_{id}_{rowIndex}_{slug}")
        return tpl.format(id=rid, rowIndex=row_index, slug=(slug or ""))
    if token == "@resultTime":
        t = ctx["time_defaults"]["resultTime"]
        cols = []
        for c in t["from"]:
            cols.append(row[c.lstrip("$")] if c.startswith("$") else c)
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
    """
    Legacy wrapper around the new hydroturtle.mapping.loader.load_mapping.

    New code should prefer hydroturtle.mapping.loader.load_mapping directly,
    but existing imports from hydroturtle.core.evaluator keep working.
    """
    return _load_mapping(mapping_path, json_encoding=json_encoding)


def iter_rows(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        yield from csv.DictReader(f)

def convert(csv_path: str, mapping: dict,
            csv_encoding: str | None = None,
            csv_delimiter: str | None = None):

    ctx = mapping["context"]
    prefixes = mapping["prefixes"]
    rules = mapping["rules"]
    use_legacy = mapping.get("compat", {}).get("typed_literal_shorthand", True)

    # delimiter hint from mapping if not given
    if csv_delimiter is None:
        csv_delimiter = mapping.get("context", {}).get("csv", {}).get("delimiter")

    # derive file id (for batch cases like LamaH-CE)
    ctx["_file_id"] = _derive_id_from_filename(csv_path, mapping)

    # ✅ preflight: only require file id if NO id column is declared
    id_col = (ctx.get("columns") or {}).get("id")
    if not id_col and not ctx["_file_id"]:
        raise ValueError(
            f"No ID could be derived for file '{csv_path}'. "
            f"Set mapping.context.columns.id OR mapping.derive.id_from_filename.regex."
        )

    triples_by_subject = {}

    def add_triple(s, p, o):
        triples_by_subject.setdefault(s, []).append((p, o))

    for i, row in enumerate(iter_rows(csv_path, csv_encoding=csv_encoding, csv_delimiter=csv_delimiter)):
        # resolve the effective id for THIS row
        rid = _row_id(row, ctx, ctx.get("_file_id"))

        for col, spec in rules.items():
            val = row.get(col)
            if val is None:
                continue
            if isinstance(val, str) and val.strip().lower() in {"", "na", "nan"}:
                continue

            subj_tpl = ctx["uri_templates"].get("observation", "hyobs:observation_{id}_{rowIndex}")
            slug = col.lower()
            s = subj_tpl.format(id=rid, rowIndex=i, slug=slug)

            spec_iter = iter(spec)
            first = next(spec_iter)
            if isinstance(first, list) and first and first[0] == "@subject":
                subj_token = first[1]
                if isinstance(subj_token, str) and subj_token.startswith("@"):
                    s = _expand_token(subj_token, row, i, ctx, slug=slug)
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
    try:
        from charset_normalizer import from_path
        best = from_path(path).best()
        if best and best.encoding:
            return best.encoding
    except Exception:
        pass
    return None

# --- CSV reader with encoding + delimiter robustness ------------------------
def _sniff_delimiter(sample: str) -> str:
    # Try csv.Sniffer first
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=[",",";","\t","|"])
        return dialect.delimiter
    except Exception:
        pass
    # Simple heuristic: pick the delimiter with the most hits in the header
    header = sample.splitlines()[0] if sample else ""
    candidates = [",",";","\t","|"]
    counts = {d: header.count(d) for d in candidates}
    best = max(counts, key=counts.get)
    return best if counts[best] > 0 else ","

def iter_rows(csv_path: str,
              csv_encoding: str | None = None,
              csv_delimiter: str | None = None):
    """
    Robust CSV reader with:
      - encoding auto/override,
      - delimiter auto/override.
    """
    def _yield_with(enc: str, delim: str | None, strict: bool = True):
        with open(csv_path, "r", newline="", encoding=enc, errors=("strict" if strict else "replace")) as f:
            # Sniff if needed
            if delim is None:
                sample = f.read(65536)
                f.seek(0)
                d = _sniff_delimiter(sample)
            else:
                d = delim
            reader = csv.DictReader(f, delimiter=d)
            first = next(reader)  # early validate
            yield first
            for r in reader:
                yield r

    # Encoding selection (explicit → detected → fallbacks → replace)
    if csv_encoding:
        yield from _yield_with(csv_encoding, csv_delimiter, strict=True)
        return

    enc = detect_encoding(csv_path)
    if enc:
        try:
            yield from _yield_with(enc, csv_delimiter, strict=True)
            return
        except Exception:
            pass

    for enc_try in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            yield from _yield_with(enc_try, csv_delimiter, strict=True)
            return
        except Exception:
            continue

    yield from _yield_with("utf-8", csv_delimiter, strict=False)

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

def _derive_id_from_filename(csv_path: str, mapping: dict) -> str | None:
    d = (mapping or {}).get("derive", {}).get("id_from_filename")
    name = Path(csv_path).name
    stem = Path(csv_path).stem

    if not d or not d.get("regex"):
        m2 = re.match(r"^ID_(\d+)", stem, flags=re.IGNORECASE)
        return m2.group(1) if m2 else stem

    pat = d["regex"]
    grp = d.get("group", 1)

    m = re.search(pat, name, flags=re.IGNORECASE)
    if m:
        return m.group(grp)

    m2 = re.match(r"^ID_(\d+)", stem, flags=re.IGNORECASE)
    return m2.group(1) if m2 else stem


def _row_id(row: dict, ctx: dict, file_id: str | None) -> str:
    id_col = (ctx or {}).get("columns", {}).get("id")
    if id_col:
        v = row.get(id_col)
        if v not in (None, ""):
            return str(v)
    if file_id:
        return str(file_id)
    return ""




