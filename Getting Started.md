
## Installation

We strongly recommend a virtual environment.

```bash
# Windows PowerShell
python -m venv .venv
.venv\Scripts\Activate.ps1

# macOS/Linux
python -m venv .venv
source .venv/bin/activate

pip install -U pip setuptools
# install the package (editable is handy while developing)
pip install -e .

# optional: geospatial deps for shapefiles
pip install shapely>=2.0 fiona>=1.9 pyproj>=3.6

# If you hit GDAL/Fiona issues on Windows, a Conda env is the easy path:
conda create -n ht python=3.12 shapely fiona pyproj pip → conda activate ht → pip install -e .

```
## Command-line usage

HydroTurtle exposes two subcommands: `csv`, `csv-batch` and `shp`.

### CSV → RDF
```bash
# console script (after pip install -e .)
hydroturtle csv <input.csv> <mapping.json> <out.ttl>

# or module form (always works)
python -m hydroturtle.cli csv <input.csv> <mapping.json> <out.ttl>
```
**Encoding:** CSV encoding is auto-detected; override if needed:
```bash
hydroturtle csv data.csv mapping.json out.ttl --csv-encoding cp1252
```

**Notes** 
- Empty-like values (`""`, `NA`, `NaN`, case-insensitive) are skipped.
- CSV delimiter is auto-sniffed; override if needed:
```bash
hydroturtle csv data.csv mapping.json out.ttl --csv-delimiter ";"
```
### CSV (batch) → RDF (many files in a directory)
Process many per-gauge/per-catchment files in one go. IDs can be derived from filenames if needed.

```bash
hydroturtle csv-batch "<file_name_with_patten>" <mapping.json> <out_dir>
```
Example (CAMELS-GB time series):
```bash
hydroturtle csv-batch "C:\camels\TS\CAMELS_GB_hydromet_timeseries_*.csv" ^
  "examples\camels_gb\mapping_camels_gb_timeseries.json" ^
  "C:\out\camels_gb_ts"
```

### SHP → RDF (points/polygons)

```bash
hydroturtle shp <input.shp> <mapping_shp.json> <out.ttl>
# module form:
python -m hydroturtle.cli shp <input.shp> <mapping_shp.json> <out.ttl>
```
**Options**
- ID field can be provided via CLI (overrides mapping):
```bash
hydroturtle shp catchments.shp mapping_polygons.json out.ttl --id-field ID_STRING
```
- CRS can be provided via CLI (overrides mapping / .prj):
```bash
hydroturtle shp stations.shp mapping_points.json out.ttl --src-crs EPSG:3035
```

## Mapping files(JSON)
Each mapping provides:
- `prefixes` — CURIE prefixes for vocabularies
- `configuration.column_types` — declares ID/date/time columns and URI templates
- `configuration.shapefile.src_crs` — optional CRS override for shapefiles
- `rules` — what triples to emit (observations, attributes, geometries)   


- The mapping’s `context.columns` controls ID/Date recognition:
```json
"columns": { "id": "OBJECTID", "date": "Date", "time": null }
```
- Time parsing uses `context.time_defaults.resultTime` (formats are tried in order):
```json
"time_defaults": { "resultTime": { "from": ["$Date"], "format": ["%Y-%m-%d"] } }
```
- Legacy typed-literal shorthand is supported by default:
```json
"compat": { "typed_literal_shorthand": true }
```
which lets you write `"^^xsd:decimal"` and have the current cell value injected automatically—even inside blank nodes.

### CSV (batch) → RDF (many files)
Process many per-gauge/per-catchment files in one go. The gauge ID can be extracted from the filename.
```bash
hydroturtle csv-batch "<glob>" <mapping.json> <out_dir> \
  --id-from-filename "regex:(\d+)" \
  --filename-id-template "{id}"
```
**Parameters**
- `<glob>:` A filesystem glob for CSVs.
  - Windows PowerShell: wrap in double-quotes. 
- `--id-from-filename:` How to derive the ID from the filename.
  - `basename` — use the filename without extension.
  - `stem` — same as basename (no extension).
  - `regex:<pattern>` — first capturing group is used as the ID.
    - Example pattern for CAMELS-GB files like `CAMELS_GB_hydromet_timeseries_1001_19701001-20150930.csv`:
    ```python
    --id-from-filename "regex:.*_(\d+)_\d{8}-\d{8}\.csv$"
    ```
- `--filename-id-template`: How to write the extracted ID back when a mapping uses `{id}` in `uri_templates`.

**Example (CAMELS-GB time series)**
```bash
hydroturtle csv-batch "C:\camels\TS\CAMELS_GB_hydromet_timeseries_*.csv" ^
  "examples\camels_gb\mapping_camels_gb_timeseries.json" ^
  "C:\out\camels_gb_ts" ^
  --id-from-filename "regex:.*_(\d+)_\d{8}-\d{8}\.csv$" ^
  --filename-id-template "{id}"
```
**Works with the same mapping format** you use for single CSVs. The only difference is that `columns.id` may be missing in the CSV; the ID supplied by `--id-from-filename` fills it in.

### SHP → RDF (points/polygons)
```bash
hydroturtle shp <input.shp> <mapping_shp.json> <out.ttl>
# module form:
python -m hydroturtle.cli shp <input.shp> <mapping_shp.json> <out.ttl>
```
**Options**
- CRS is auto-detected from `.prj.` If missing/incorrect:
```bash
hydroturtle shp stations.shp mapping_points.json out.ttl --src-crs EPSG:25833 
```
- If your unique ID attribute isn’t `OBJECTID`:
```bash
hydroturtle shp catchments.shp mapping_polygons.json out.ttl --id-field GAUGE_ID
```
**WKT in mappings**
- Always quote WKT and include CRS when present:
```json
["geo:asWKT", {
  "@template": "<http://www.opengis.net/def/crs/OGC/1.3/CRS84> POINT ({lon} {lat})",
  "from": { "lon": {"@col":"gauge_lon"}, "lat":{"@col":"gauge_lat"} },
  "as": "^^geo:wktLiteral"
}]
```
HydroTurtle will emit `"…POINT (lon lat)"^^geo:wktLiteral` with proper quoting.

**Handy mapping shorthands**
These special tokens expand using `context.uri_templates` and row values:
- `@sensor`, `@catchment`, `@collection`, `@observation`, `@geom`
- `@resultTime` (built from `time_defaults`)
- `@subject` (first rule entry can override the subject per-block)

**Example:**
```json
["@subject", "@sensor"],
["hyobs:monitorsCatchment", "@catchment"],
["geo:hasGeometry", "@geom"]
```
**Windows tips**
- Use double-quotes around paths and globs.
- For PowerShell line continuations, use backtick (`) or caret (^) depending on your shell.
- If `hydroturtle` isn’t found, use module form:
```bash
python -m hydroturtle.cli csv <input.csv> <mapping.json> <out.ttl>
```

---

## Developer notes

#### Project layout
```perl
hydroturtle/
  hydroturtle/
    cli.py                # `csv`, `csv-batch`, `shp`
    core/                 # engines
    io/                   # turtle writer
    time/                 # date/time parsing
    mapping/              # loader + schema
    geo/                  # shapefile reader + WKT serializer
examples/                 # mapping file examples
docs/                     # mapping documentation
```
#### Shapefiles & CRS
- CRS is read from `.prj` where available.
- If missing/incorrect, set `configuration.shapefile.src_crs` in the mapping, or override with `--src-crs EPSG:xxxx`.
- Output WKT is CRS84 (lon,lat) as GeoSPARQL 1.1 WKT literal: 
`"<http://www.opengis.net/def/crs/OGC/1.3/CRS84> ..."^^geo:wktLiteral`

#### Encoding
- CSV encoding auto-detected; override with `--csv-encoding`.
- Mapping JSON defaults to UTF-8; override with `--json-encoding`.

#### Important 
- Mapping directives starting with `@` (e.g., `@subject`, `@geom`) are control directives and are not emitted as predicates.
