from __future__ import annotations

from typing import Dict, Any, List, Tuple, Optional
from hydroturtle.geo.shp_reader import iter_features
from hydroturtle.geo.wkt import wkt_literal_crs84
from hydroturtle.io.ttl_writer import write_turtle
from hydroturtle.mapping.loader import load_mapping


# SHP engine supports TWO rule styles:
#
# (A) Legacy SHP-style dict rules (already used for QUADICA geometry):
#     "rules": {
#        "@subject": {"@template":"@catchment"},
#        "rdf:type": "envthes:30212",
#        "geo:hasGeometry": "@geom",
#        "@geom": [
#            ["rdf:type","sf:Polygon"],
#            ["geo:asWKT", {"@wkt":"geometry"}]
#        ]
#     }
#
# (B) CSV-style "column rules" for SHP attributes:
#     "rules": {
#        "Area_km2": [
#            ["@subject","@catchment"],
#            ["hyobs:hasCatchmentAreaKm2", [
#                ["rdf:type","qudt:QuantityValue"],
#                ["qudt:numericValue","^^xsd:decimal"],
#                ["qudt:unit","unit:KiloM2"]
#            ]]
#        ]
#     }
#
# Column rules only run if that field exists in the SHP attribute table.


def _build_uri(name: str, ctx: Dict[str, Any], id_value: Any) -> str:
    tpl = ctx.get("uri_templates", {}).get(name)
    if not tpl:
        raise KeyError(f"uri_templates missing key '{name}'")
    return tpl.format(id=id_value)


def _resolve_ref(token: Any, ctx: Dict[str, Any], id_value: Any) -> Any:
    # Only strings can be template tokens like "@sensor"
    if isinstance(token, str) and token.startswith("@"):
        key = token[1:]
        if key in ("sensor", "catchment", "geom", "collection", "observation"):
            return _build_uri(key, ctx, id_value)
    return token


def _emit(triples_by_subject: Dict[str, List[Tuple[str, str]]], s: str, p: str, o: str):
    triples_by_subject.setdefault(s, []).append((p, o))


def _as_typed_literal(value: Any, datatype: str) -> str:
    # datatype like "^^xsd:decimal"
    # keep exact suffix the user provided (^^xsd:decimal)
    return f"\"{value}\"{datatype}"


def _render_obj_shp(
    spec: Any,
    props: Dict[str, Any],
    current_col: Optional[str],
    ctx: Dict[str, Any],
    fid: Any,
    geom: Any
) -> str:
    """
    Render an object for SHP mapping.

    Returns:
      - string object to emit
      - "" to mean: skip this triple
    """

    # 1) WKT literal
    if isinstance(spec, dict) and "@wkt" in spec:
        return wkt_literal_crs84(geom)

    # 2) explicit column reference: {"@col":"Area_km2","as":"^^xsd:decimal"}
    if isinstance(spec, dict) and "@col" in spec:
        col = spec["@col"]
        val = props.get(col)
        if val is None:
            return ""
        dt = spec.get("as")
        if isinstance(dt, str) and dt.startswith("^^"):
            return _as_typed_literal(val, dt)
        # default: plain literal string
        return f"\"{val}\""

    # 3) template token "@catchment", "@geom", ...
    if isinstance(spec, str) and spec.startswith("@"):
        return str(_resolve_ref(spec, ctx, fid))

    # 4) typed literal shorthand "^^xsd:decimal"
    # inject current field value
    if isinstance(spec, str) and spec.startswith("^^"):
        if current_col is None:
            # no current column context -> cannot inject, skip
            return ""
        val = props.get(current_col)
        if val is None:
            return ""
        return _as_typed_literal(val, spec)

    # 5) plain QName/IRI string
    if isinstance(spec, str):
        return spec

    # fallback
    return str(spec)


def _emit_blank_node_block(
    triples_by_subject: Dict[str, List[Tuple[str, str]]],
    subject: str,
    predicate: str,
    block: List[Any],
    props: Dict[str, Any],
    current_col: Optional[str],
    ctx: Dict[str, Any],
    fid: Any,
    geom: Any,
    bnode_counter: List[int]
):
    """
    Emit:
        subject predicate _:bN .
        _:bN p o .
        ...
    """
    bnode_counter[0] += 1
    bnode_id = f"_:b{fid}_{bnode_counter[0]}"
    _emit(triples_by_subject, subject, predicate, bnode_id)

    for part in block:
        if not (isinstance(part, list) and len(part) == 2):
            continue
        p3, o3 = part
        obj3 = _render_obj_shp(o3, props, current_col, ctx, fid, geom)
        if obj3 == "":
            continue
        _emit(triples_by_subject, bnode_id, p3, str(_resolve_ref(obj3, ctx, fid)))


def run_convert_shp(
    shp_path: str,
    mapping_path: str,
    out_path: str,
    id_field: str | None = None,
    src_crs_override: str | None = None,
    json_encoding: str = "utf-8"
):
    mapping = load_mapping(mapping_path, json_encoding=json_encoding)
    prefixes = mapping["prefixes"]
    ctx = mapping["context"]
    rules = mapping.get("rules", {})

    # Resolve ID field: CLI > mapping.context.columns.id > fallback
    mapping_id = ctx.get("columns", {}).get("id")
    id_field_final = id_field or mapping_id or "OBJECTID"

    triples_by_subject: Dict[str, List[Tuple[str, str]]] = {}

    for feat in iter_features(shp_path, id_field=id_field_final, src_crs_override=src_crs_override):
        fid = feat["id"]
        props = feat["props"]
        geom = feat["geom"]

        # per-feature blank node counter
        bnode_counter = [0]

        # Determine base subject
        subject: Optional[str] = None
        subj_spec = rules.get("@subject")
        if isinstance(subj_spec, dict) and "@template" in subj_spec:
            subject = str(_resolve_ref(subj_spec["@template"], ctx, fid))

        if not subject:
            # Default: prefer sensor if defined, else catchment
            if "sensor" in ctx.get("uri_templates", {}):
                subject = str(_resolve_ref("@sensor", ctx, fid))
            else:
                subject = str(_resolve_ref("@catchment", ctx, fid))

        # ------------------------------------------------------------
        # PASS A: legacy SHP dict rules (string values + node blocks)
        # ------------------------------------------------------------
        for pred, obj in rules.items():
            if pred == "@subject":
                continue

            # If this rule key is a real SHP attribute column name, it will be handled in PASS B.
            # Skipping it here prevents duplicate blank nodes like _:b1002_1 and _:b1002_2.
            if isinstance(pred, str) and (not pred.startswith("@")) and (pred in props):
                continue

            # Node-builder blocks like "@geom": [ ... ]
            if isinstance(obj, list) and isinstance(pred, str) and pred.startswith("@"):
                node_uri = str(_resolve_ref(pred, ctx, fid))
                for part in obj:
                    if not (isinstance(part, list) and len(part) == 2):
                        continue
                    p2, o2 = part

                    # blank-node blocks inside a node-builder block
                    if isinstance(o2, list):
                        _emit_blank_node_block(
                            triples_by_subject, node_uri, p2, o2,
                            props, current_col=None, ctx=ctx, fid=fid, geom=geom,
                            bnode_counter=bnode_counter
                        )
                        continue

                    obj2 = _render_obj_shp(o2, props, current_col=None, ctx=ctx, fid=fid, geom=geom)
                    if obj2 == "":
                        continue
                    _emit(triples_by_subject, node_uri, p2, str(_resolve_ref(obj2, ctx, fid)))
                continue

            # Simple predicate -> object
            if isinstance(obj, str):
                # Special-case: identifier shorthand on SHP
                # If mapping says dct:identifier: "^^xsd:string", inject the feature id
                if obj == "^^xsd:string" and isinstance(pred, str) and pred.endswith("identifier"):
                    val = props.get(id_field_final, fid)
                    o = f"\"{val}\"^^xsd:string"
                else:
                    o = str(_resolve_ref(obj, ctx, fid))
                _emit(triples_by_subject, subject, pred, o)
                continue

            # List of immediate triples from subject (legacy style)
            if isinstance(obj, list) and not (isinstance(pred, str) and pred.startswith("@")):
                for part in obj:
                    if not (isinstance(part, list) and len(part) == 2):
                        continue
                    p2, o2 = part

                    # skip accidental directives
                    if isinstance(p2, str) and p2.startswith("@"):
                        continue

                    # blank node block
                    if isinstance(o2, list):
                        _emit_blank_node_block(
                            triples_by_subject, subject, p2, o2,
                            props, current_col=None, ctx=ctx, fid=fid, geom=geom,
                            bnode_counter=bnode_counter
                        )
                        continue

                    obj2 = _render_obj_shp(o2, props, current_col=None, ctx=ctx, fid=fid, geom=geom)
                    if obj2 == "":
                        continue
                    _emit(triples_by_subject, subject, p2, str(_resolve_ref(obj2, ctx, fid)))
                continue

        # ------------------------------------------------------------
        # PASS B: CSV-style column rules for SHP attribute fields
        # ------------------------------------------------------------
        for col_name, rule_spec in rules.items():
            if not isinstance(col_name, str):
                continue
            if col_name.startswith("@"):
                continue
            if not isinstance(rule_spec, list):
                continue
            if col_name not in props:
                continue  # only apply if the SHP has that field

            current_col = col_name
            local_subject = subject

            for part in rule_spec:
                if not (isinstance(part, list) and len(part) == 2):
                    continue
                p, o = part

                # subject switch
                if p == "@subject":
                    local_subject = str(_resolve_ref(o, ctx, fid))
                    continue

                # blank node block
                if isinstance(o, list):
                    _emit_blank_node_block(
                        triples_by_subject, local_subject, p, o,
                        props, current_col=current_col, ctx=ctx, fid=fid, geom=geom,
                        bnode_counter=bnode_counter
                    )
                    continue

                obj = _render_obj_shp(o, props, current_col=current_col, ctx=ctx, fid=fid, geom=geom)
                if obj == "":
                    continue
                _emit(triples_by_subject, local_subject, p, str(_resolve_ref(obj, ctx, fid)))

    write_turtle(triples_by_subject, prefixes, out_path)
    return out_path
