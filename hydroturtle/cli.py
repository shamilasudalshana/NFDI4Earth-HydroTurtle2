# hydroturtle/cli.py
import argparse
from hydroturtle.core.engine import run_convert

def main():
    ap = argparse.ArgumentParser(description="HydroTurtle converter")
    ap.add_argument("csv")
    ap.add_argument("mapping")
    ap.add_argument("out")
    ap.add_argument("--csv-encoding", default=None, help="e.g., utf-8, utf-8-sig, cp1252, latin-1")
    ap.add_argument("--json-encoding", default="utf-8", help="mapping JSON encoding (default utf-8)")
    args = ap.parse_args()
    run_convert(args.csv, args.mapping, args.out,
                csv_encoding=args.csv_encoding,
                json_encoding=args.json_encoding)

if __name__ == "__main__":
    main()
