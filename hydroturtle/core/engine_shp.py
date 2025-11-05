from typing import Dict, Any, List, Tuple
import json
from pathlib import Path
from hydroturtle.geo.shp_reader import iter_features
from hydroturtle.geo.wkt import wkt_literal_crs84
from hydroturtle.io.ttl_writer import write_turtle

# Very small evaluator tailored for SHP rules:
# - @template tokens: @sensor, @catchment, @geom
# - special object {"@wkt": "geometry"} to emit GeoSPARQL WKT literal
# - inject id value when object is "^^xsd:string" and predicate is dct:identifier

def load_mapping(mapping_path: str, json_encoding: str = "utf-8") -> Dict[str, Any]:
    return json.loads(Path(mapping_path).read_text(encoding=json_encoding))

def _build_uri(name: str, ctx: Dict[str, Any], id_value: Any) -> str:
    tpl = ctx["uri_templates"].get(name)
    if not tpl:
        raise KeyError(f"uri_templates missing key '{name}'")
    return tpl.format(id=id_value)

def _resolve_ref(token: str, ctx: Dict[str, Any], id_value: Any) -> str:
    # e.g. token="@sensor" -> expand to URI using template
    if token.startswith("@"):
        key = token[1:]
        if key in ("sensor", "catchment", "geom"):
            return _build_uri(key, ctx, id_value)
    return token

def _emit(triples_by_subject: Dict[str, List[Tuple[str, str]]], s: str, p: str, o: str):
    triples_by_subject.setdefault(s, []).append((p, o))

def run_convert_shp(shp_path: str, mapping_path: str, out_path: str,
                    id_field: str = "OBJECTID",
                    src_crs_override: str | None = None,
                    json_encoding: str = "utf-8"):
    mapping = load_mapping(mapping_path, json_encoding=json_encoding)
    prefixes = mapping["prefixes"]
    ctx = mapping["context"]

    # Pre-validate required templates
    ctx.setdefault("uri_templates", {})
    for needed in ("sensor", "geom"):  # polygons mapping may also use "catchment"
        if needed not in ctx["uri_templates"]:
            pass  # allow polygon-only maps to omit 'sensor'

    triples_by_subject: Dict[str, List[Tuple[str, str]]] = {}

    for feat in iter_features(shp_path, id_field=id_field, src_crs_override=src_crs_override):
        fid = feat["id"]
        props = feat["props"]
        geom = feat["geom"]

        # Subject override
        subject = None
        subj_spec = mapping.get("rules", {}).get("@subject")
        if isinstance(subj_spec, dict) and "@template" in subj_spec:
            subject = _resolve_ref(subj_spec["@template"], ctx, fid)
        if not subject:
            # default to sensor nodes for points; polygon mapping usually overrides to @catchment
            if "sensor" in ctx.get("uri_templates", {}):
                subject = _resolve_ref("@sensor", ctx, fid)
            else:
                subject = _resolve_ref("@catchment", ctx, fid)

        # Iterate rule dict
        for pred, obj in mapping["rules"].items():
            if pred == "@subject":
                continue

            # Case 1: simple IRI object (string)
            if isinstance(obj, str):
                val = obj
                # Inject id for dct:identifier when given ^^xsd:string
                if val == "^^xsd:string" and pred.endswith("identifier"):
                    o = f"\"{props.get(id_field, fid)}\"^^xsd:string"
                else:
                    o = _resolve_ref(val, ctx, fid)
                _emit(triples_by_subject, subject, pred, o)
                continue

            # Case 2: array of triples describing a related node or geometry
            if isinstance(obj, list):
                # Support geometry blocks when predicate is a node like "@geom"
                # Convention: a block that contains ["geo:asWKT", {"@wkt": "geometry"}]
                # and ["rdf:type","sf:Point|sf:Polygon"]
                # We compute the related node (e.g., @geom) and attach via pred
                # Example mapping:
                # "geo:hasGeometry": [
                #   ["@subject","@catchment"],
                #   ["rdf:type","envthes:30212"],
                #   ["geo:hasGeometry","@geom"]
                # ],
                # "@geom": [
                #   ["rdf:type","sf:Polygon"],
                #   ["geo:asWKT", {"@wkt":"geometry"}]
                # ]

                # If pred starts with '@', treat it as a node builder for that URI
                if pred.startswith("@"):
                    node_uri = _resolve_ref(pred, ctx, fid)
                    for part in obj:
                        if not isinstance(part, list) or len(part) != 2:
                            continue
                        p2, o2 = part
                        if isinstance(o2, dict) and "@wkt" in o2:
                            wkt_lit = wkt_literal_crs84(geom)
                            _emit(triples_by_subject, node_uri, p2, wkt_lit)
                        else:
                            _emit(triples_by_subject, node_uri, p2, _resolve_ref(o2, ctx, fid))
                    # link from subject to this node if the mapping intended it
                    # (usually handled by a separate "geo:hasGeometry" block)
                    continue

                # Otherwise, interpret this list as immediate triples from 'subject'
                for part in obj:
                    if not isinstance(part, list) or len(part) != 2:
                        continue
                    p2, o2 = part
                    # 👇 Defensive guard: ignore directive-like predicates
                    if isinstance(p2, str) and p2.startswith("@"):
                        # e.g., someone mistakenly wrote ["@subject", "@sensor"] in a block
                        continue

                    if isinstance(o2, dict) and "@wkt" in o2:
                        wkt_lit = wkt_literal_crs84(geom)
                        _emit(triples_by_subject, subject, p2, wkt_lit)
                    else:
                        _emit(triples_by_subject, subject, p2, _resolve_ref(o2, ctx, fid))
                continue

            # Fallback: ignore unknown shapes quietly

    write_turtle(triples_by_subject, prefixes, out_path)
    return out_path