import argparse
from hydroturtle.core.engine import run_convert          # CSV engine (existing)
from hydroturtle.core.engine_shp import run_convert_shp  # SHP engine (new)

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
    sp_csv.add_argument("--json-encoding", default="utf-8",
                        help="mapping JSON encoding (default utf-8)")

    # SHP mode
    sp_shp = sub.add_parser("shp", help="Convert ESRI Shapefile → RDF/Turtle")
    sp_shp.add_argument("shapefile")
    sp_shp.add_argument("mapping")
    sp_shp.add_argument("out")
    sp_shp.add_argument("--id-field", default="OBJECTID",
                        help="attribute name that holds the unique id (default OBJECTID)")
    sp_shp.add_argument("--src-crs", default=None,
                        help="override source CRS (e.g. EPSG:25833) if .prj missing/incorrect")
    sp_shp.add_argument("--json-encoding", default="utf-8",
                        help="mapping JSON encoding (default utf-8)")

    args = ap.parse_args()

    if args.cmd == "csv":
        run_convert(args.csv, args.mapping, args.out,
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
