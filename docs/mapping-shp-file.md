# Mapping Shapefile Data (SHP)

## 1. Purpose

This document explains how to convert **ESRI Shapefiles** (stations/points and catchments/polygons) into RDF using HydroTurtle.

Shapefiles are typically used for:

- Station locations (points)
- Catchment boundaries (polygons)
- GeoSPARQL-compatible geometries for spatial queries

HydroTurtle converts all geometries into **CRS84/WGS84 GeoSPARQL WKT literals**, so the output can be used with GeoSPARQL functions.

---

## 2. Key Differences from CSV Mappings

Shapefile mappings:

- Do not use CSV parsing or delimiters
- Use **feature attributes** (table fields) + a **geometry column**
- Often map **only geometry**, because the descriptive attributes may already exist in CSVs
- Support reprojection using `configuration.shapefile.src_crs`

---

## 3. Configuration

Shapefile mappings use the same `configuration` layout as CSV mappings, but they typically only need:

- The feature ID field (`column_types.id.column_name`)
- Templates for subject IDs (sensor/catchment/geom)
- Optional CRS override for reprojection

Example (polygons):

```json
"configuration": {
  "shapefile": {
    "src_crs": "EPSG:3035"
  },
  "column_types": {
    "id": { "column_name": "ID", "id_from_filename": null },
    "date": { "column_name": null, "format": null },
    "time": { "column_name": null, "format": null },
    "templates_for_subject_id": {
      "catchment": "hyobs:catchment_{id}",
      "geom": "hyobs:geomPolygon_{id}"
    }
  }
}
```
Notes:
- If `src_crs` is missing, HydroTurtle will attempt to read CRS from the `.prj` file.
- The output WKT is always emitted as CRS84 (longitude/latitude).
---
## 4. Declaring Subjects and Types

Shapefile mappings often define a fixed subject template via `@subject`.

Example: “each polygon feature represents a catchment”

```json
"rules": {
  "@subject": { "@template": "@catchment" },
  "rdf:type": "envthes:30212"
}
```
Example: “each point feature represents a sensor/station”
```json
"rules": {
  "@subject": { "@template": "@sensor" },
  "rdf:type": "sosa:Sensor"
}
```

## 5. Geometry Mapping

HydroTurtle represents geometry as a separate node resolved by `@geom`.

### 5.1 Polygon geometry (catchments)
```json
"rules": {
  "@subject": { "@template": "@catchment" },
  "rdf:type": "envthes:30212",
  "geo:hasGeometry": "@geom",

  "@geom": [
    ["rdf:type", "sf:Polygon"],
    ["geo:asWKT", { "@wkt": "geometry" }]
  ]
}
```
### 5.2 Point geometry (stations)
```json
"rules": {
  "@subject": { "@template": "@sensor" },
  "rdf:type": "sosa:Sensor",
  "geo:hasGeometry": "@geom",

  "@geom": [
    ["rdf:type", "sf:Point"],
    ["geo:asWKT", { "@wkt": "geometry" }]
  ]
}
```
The special object:

```json
{ "@wkt": "geometry" }
```
means: “take the feature geometry from the shapefile and emit it as CRS84 GeoSPARQL WKT”.

---

## 6. Mapping Shapefile Table Attributes (Optional)

You can map additional fields from the shapefile attribute table if needed.

Example: `Area_km2` on catchment polygons:
```json
"Area_km2": [
  ["@subject", "@catchment"],
  ["hyobs:hasCatchmentAreaKm2", [
    ["rdf:type", "qudt:QuantityValue"],
    ["qudt:numericValue", "^^xsd:decimal"],
    ["qudt:unit", "unit:KiloM2"]
  ]]
]
```
Important notes:
- Attribute rules only apply if the shapefile field exists.
- HydroTurtle will skip empty-like values.

## 7. Best Practices

- Prefer **ID columns that match your CSV IDs exactly** (e.g., `"10002"` not `"10002.0000"`).
- Put CRS in the mapping (`configuration.shapefile.src_crs`) if .prj is missing or wrong.
- Keep shapefile mappings minimal if attributes already exist in CSV conversions.
- Use consistent templates (`sensor_{id}`, `catchment_{id}`, `geomPoint_{id}`, `geomPolygon_{id}`) across datasets.

## 8. Examples

See `examples/` for complete shapefile mappings:

- LamaH-CE points + polygons
- CAMELS-GB catchment polygons
- QUADICA points + polygons

---
This mapping format is designed to be reusable, extensible, and understandable by domain scientists without programming experience.

