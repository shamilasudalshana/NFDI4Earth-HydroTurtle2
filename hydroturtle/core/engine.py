from hydroturtle.core.evaluator import load_mapping, convert
from hydroturtle.io.ttl_writer import write_turtle

def run_convert(csv_path, mapping_path, out_path,
                csv_encoding=None, json_encoding="utf-8"):
    mapping = load_mapping(mapping_path, json_encoding=json_encoding)
    triples_by_subject, prefixes = convert(csv_path, mapping, csv_encoding=csv_encoding)
    write_turtle(triples_by_subject, prefixes, out_path)
    return out_path
