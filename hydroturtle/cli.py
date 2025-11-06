import argparse
from hydroturtle.core.engine import run_convert, run_convert_batch
from hydroturtle.core.engine_shp import run_convert_shp

def main():
    ap = argparse.ArgumentParser(description="HydroTurtle converter")
    sub = ap.add_subparsers(dest="cmd", required=True)

    # CSV single
    sp_csv = sub.add_parser("csv", help="Convert CSV → RDF/Turtle")
    sp_csv.add_argument("csv")
    sp_csv.add_argument("mapping")
    sp_csv.add_argument("out")
    sp_csv.add_argument("--csv-encoding", default=None)
    sp_csv.add_argument("--json-encoding", default="utf-8")

    # CSV batch
    sp_csvb = sub.add_parser("csv-batch", help="Convert many CSVs → TTLs")
    sp_csvb.add_argument("input_glob", help=r'Glob, e.g. "D:\camels\*.csv"')
    sp_csvb.add_argument("mapping")
    sp_csvb.add_argument("out_dir")
    sp_csvb.add_argument("--csv-encoding", default=None)
    sp_csvb.add_argument("--json-encoding", default="utf-8")

    # SHP
    sp_shp = sub.add_parser("shp", help="Convert ESRI Shapefile → RDF/Turtle")
    sp_shp.add_argument("shapefile")
    sp_shp.add_argument("mapping")
    sp_shp.add_argument("out")
    sp_shp.add_argument("--id-field", default=None, 
                        help="attribute name holding the unique ID (defaults to mapping.context.columns.id, else OBJECTID)")
    sp_shp.add_argument("--src-crs", default=None)
    sp_shp.add_argument("--json-encoding", default="utf-8")

    args = ap.parse_args()

    if args.cmd == "csv":
        run_convert(args.csv, args.mapping, args.out,
                    csv_encoding=args.csv_encoding,
                    json_encoding=args.json_encoding)
        return

    if args.cmd == "csv-batch":
        run_convert_batch(args.input_glob, args.mapping, args.out_dir,
                          csv_encoding=args.csv_encoding,
                          json_encoding=args.json_encoding)
        return

    if args.cmd == "shp":
        run_convert_shp(args.shapefile, args.mapping, args.out,
                        id_field=args.id_field,
                        src_crs_override=args.src_crs,
                        json_encoding=args.json_encoding)
        return

if __name__ == "__main__":
    main()