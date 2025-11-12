from pathlib import Path
from glob import glob
from hydroturtle.core.evaluator import load_mapping, convert
from hydroturtle.io.ttl_writer import write_turtle

def run_convert(csv_path, mapping_path, out_path,
                csv_encoding=None, csv_delimiter=None, json_encoding="utf-8"):
    mapping = load_mapping(mapping_path, json_encoding=json_encoding)
    triples_by_subject, prefixes = convert(csv_path, mapping, csv_encoding=csv_encoding, csv_delimiter=csv_delimiter)
    write_turtle(triples_by_subject, prefixes, out_path)
    return out_path

def run_convert_batch(input_glob: str, mapping_path: str, out_dir: str,
                      csv_encoding=None, csv_delimiter=None, json_encoding="utf-8"):
    mapping = load_mapping(mapping_path, json_encoding=json_encoding)
    outd = Path(out_dir)
    outd.mkdir(parents=True, exist_ok=True)
    for fp in sorted(glob(input_glob)):
        out = outd / (Path(fp).stem + ".ttl")
        triples_by_subject, prefixes = convert(fp, mapping, csv_encoding=csv_encoding, csv_delimiter=csv_delimiter)
        write_turtle(triples_by_subject, prefixes, str(out))
