# Mapping CSV Attribute Data

## 1. Purpose

This document explains how to convert **static attribute CSV files** (catchment, station, or basin attributes) into RDF using HydroTurtle.

Attribute datasets typically describe:

- Catchment geometry and area
- Elevation statistics
- Climate indices
- Land use and soil properties

Unlike time series, attribute CSVs usually contain **one row per station or catchment**.

---

## 2. Key Differences from Time Series Mappings

Attribute mappings:

- Do not create `sosa:Observation` nodes
- Attach properties directly to `@sensor` or `@catchment`
- Often reuse the same subject across many columns

---

## 3. Configuration

Configuration for attribute mappings is usually simpler.

Example:

```json
"configuration": {
  "column_types": {
    "id": {
      "column_name": "gauge_id",
      "id_from_filename": null
    },
    "date": {
      "column_name": null,
      "format": null
    },
    "time": {
      "column_name": null,
      "format": null
    },
    "templates_for_subject_id": {
      "sensor": "hyobs:sensor_{id}",
      "catchment": "hyobs:catchment_{id}",
      "geom": "hyobs:geomPoint_{id}"
    }
  }
}
```

---

## 4. Declaring Resource Types

It is recommended to declare resource types explicitly.

Example:

```json
"CatchmentType": [
  ["@subject", "@catchment"],
  ["rdf:type", "envthes:30212"]
]
```

HydroTurtle automatically removes duplicate triples, so repeated type declarations are safe.

---

## 5. Mapping Simple Attributes

Example:

```json
"meanSlope": [
  ["@subject", "@catchment"],
  ["hyobs:meanSlope", "^^xsd:decimal"]
]
```

---

## 6. Mapping contextual attributes (Quantities with Units)

Example:

```json
"area": [
  ["@subject", "@catchment"],
  ["hyobs:hasCatchmentAreaKm2", [
    ["rdf:type", "qudt:QuantityValue"],
    ["qudt:numericValue", "^^xsd:decimal"],
    ["qudt:unit", "unit:KiloM2"]
  ]]
]
```

---

## 7. Geometry Mapping

HydroTurtle commonly represents station or catchment locations as a **WGS84 / CRS84 point geometry**.

In HydroTurtle, the geometry itself is a separate resource (resolved by `@geom`) and typically includes:

- `rdf:type sf:Point`
- `geo:asWKT` as a CRS84 WKT literal
- optional coordinates and elevation as `wgs84_pos:*` literals

### 7.1 Recommended pattern (lat/lon + WKT + elevation)

A typical mapping pattern (as used for CAMELS-GB) is:

```json
"gauge_lat": [
  ["@subject", "@geom"],
  ["rdf:type", "sf:Point"],
  ["geo:asWKT", {
    "@template": "<http://www.opengis.net/def/crs/OGC/1.3/CRS84> POINT ({lon} {lat})",
    "from": { "lon": { "@col": "gauge_lon" }, "lat": { "@col": "gauge_lat" } },
    "as": "^^geo:wktLiteral"
  }],
  ["wgs84_pos:alt", { "@col": "gauge_elev", "as": "^^xsd:decimal" }]
]
```

Notes:

- The WKT template uses **both** longitude and latitude, even though this rule key is anchored on a single column (e.g., `gauge_lat`).
- HydroTurtle fetches the referenced partner column (e.g., `gauge_lon`) via the `from` block.
- Elevation can be added as `wgs84_pos:alt` using either the same rule (as above) or a separate rule.

### 7.2 Separate elevation rule (optional)

Sometimes it is clearer to keep elevation in its own rule:

```json
"elev": [
  ["@subject", "@geom"],
  ["wgs84_pos:alt", "^^xsd:decimal"]
]
```

### 7.3 Practical recommendation

For most datasets with coordinates, we recommend:

1. Create the `sf:Point` and `geo:asWKT` once.
2. Add elevation (`wgs84_pos:alt`) when available.

This pattern is easy to reuse across datasets.

---

## 8. Best Practices

- Use one attribute mapping per dataset
- Group related attributes logically
- Declare resource types once where possible
- Prefer readability over compactness

---

## 9. Examples

See `examples/` for complete attribute mappings:

- CAMELS-GB attributes
- LamaH-CE attributes
- QUADICA attributes

---

Attribute mappings allow rich semantic description of hydrological entities and are a key strength of HydroTurtle.

