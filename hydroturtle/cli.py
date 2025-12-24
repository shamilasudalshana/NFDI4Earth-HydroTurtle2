import argparse
from hydroturtle.core.engine import run_convert, run_convert_batch  
from hydroturtle.core.engine_shp import run_convert_shp

def main():
    ap = argparse.ArgumentParser(description="HydroTurtle converter")
    sub = ap.add_subparsers(dest="cmd", required=True)

    # CSV mode
    sp_csv = sub.add_parser("csv", help="Convert CSV → RDF/Turtle")
    sp_csv.add_argument("csv")
    sp_csv.add_argument("mapping")
    sp_csv.add_argument("out")
    sp_csv.add_argument("--csv-encoding", default=None,
                        help="e.g., utf-8, utf-8-sig, cp1252, latin-1 (auto if omitted)")
    sp_csv.add_argument("--csv-delimiter", default=None,
                        help="Delimiter override, e.g., ';' (auto if omitted)")
    sp_csv.add_argument("--json-encoding", default="utf-8",
                        help="mapping JSON encoding (default utf-8)")

    # CSV batch mode 
    sp_csvb = sub.add_parser("csv-batch", help="Batch-convert CSVs → RDF/Turtle (glob path)")
    sp_csvb.add_argument("glob", help=r'Glob, e.g. "D:\camels\*.csv"')
    sp_csvb.add_argument("mapping")
    sp_csvb.add_argument("out_dir")
    sp_csvb.add_argument("--csv-encoding", default=None)
    sp_csvb.add_argument("--csv-delimiter", default=None)
    sp_csvb.add_argument("--json-encoding", default="utf-8")

    # SHP mode
    sp_shp = sub.add_parser("shp", help="Convert ESRI Shapefile → RDF/Turtle")
    sp_shp.add_argument("shapefile")
    sp_shp.add_argument("mapping")
    sp_shp.add_argument("out")
    sp_shp.add_argument("--id-field", default=None,
                        help="ID field in SHP table (if omitted, uses mapping configuration)")
    sp_shp.add_argument("--src-crs", default=None,
                        help="Override source CRS (if omitted, uses mapping configuration)")
    sp_shp.add_argument("--json-encoding", default="utf-8")

    args = ap.parse_args()

    if args.cmd == "csv":
        run_convert(args.csv, args.mapping, args.out,
                    csv_encoding=args.csv_encoding,
                    csv_delimiter=args.csv_delimiter,
                    json_encoding=args.json_encoding)
        return

    if args.cmd == "csv-batch":
        run_convert_batch(args.glob, args.mapping, args.out_dir,
                          csv_encoding=args.csv_encoding,
                          csv_delimiter=args.csv_delimiter,
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
