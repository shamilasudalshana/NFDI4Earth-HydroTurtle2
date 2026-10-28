# HydroTurtle

HydroTurtle converts hydrometeorological datasets to RDF/Turtle using
[SOSA/SSN](https://www.w3.org/TR/vocab-ssn/), [QUDT](https://qudt.org/),
[GeoSPARQL](https://opengeospatial.github.io/ogc-geosparql/geosparql11/spec.html),
plus HYOBS and EnvThes terms. Conversion is driven by **JSON mappings** that describe how
columns/attributes become observations, attributes, and geometries.

- **CSV → RDF:** streaming, encoding-robust, supports cross-column selection
- **SHP → RDF:** CRS auto-detect + reprojection to CRS84, GeoSPARQL‐compliant WKT

## 🌟 Features

- Convert CSV files (with or without timestamps) into RDF
- Optionally support shapefiles and coordinate transformation (to WGS 84)
- Create complex or nested triples using JSON templates
- Generate `.ttl` files with correct prefixes and syntax
- Built using modular and reusable Python functions

### 🎬 Demo

Check out the app in action:


https://github.com/user-attachments/assets/126b819b-b3ca-4e59-a1ea-3d7d6c71e052


## 🧪 Example RDF Output

Given a row:
```csv
ID,YYYY,MM,DD,2m_temp_mean
32,1981,01,19,-7.1
```

HydroTurtle generates:
```turtle
hyobs:observation_1_c_32 rdf:type sosa:Observation ;
	sosa:observedProperty hyobs:AirTemperature2mMean ;
	sosa:hasFeatureOfInterest hyobs:catchment_32 ;
	sosa:madeBySensor hyobs:sensor_32 ;
	sosa:memberOf sosa:observationCollection_32 ;
	sosa:resultTime "1981-01-19T00:00:00Z"^^xsd:dateTime ;
	sosa:hasResult [ 
                    rdf:type  qudt:QuantityValue;
                    qudt:numericValue  "-7.1"^^xsd:decimal;
                    qudt:unit  unit:DEG_C] .
```





## Mapping files (JSON)
Each mapping provides:

- `prefixes` — CURIEs for your vocabularies
- `context.columns` — column names for ID/Date/Time (CSV) or ID field (SHP)
- `context.uri_templates` — patterns for node IRIs (e.g., hyobs:sensor_{id})
- `rules` — what to emit (observations, attributes, geometries)

### CSV example - Meteological Time series (From LamaH-CE)
```json
{
  "prefixes": {
    "rdf":"http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "sosa":"http://www.w3.org/ns/sosa/",
    "qudt":"http://qudt.org/schema/qudt/",
    "unit":"http://qudt.org/vocab/unit/",
    "xsd":"http://www.w3.org/2001/XMLSchema#",
    "envthes":"http://vocabs.lter-europe.net/EnvThes/",
    "hyobs":"https://w3id.org/hmontology/"
  },
  "configuration": {
    "column_types": {
      "id": { "column_name": null, "id_from_filename": { "regex": "ID_(\\d+)", "regex-split": 1 } },
      "date": { "column_name": "date", "format": "%Y-%m-%d" },
      "time": { "column_name": null, "format": null },
      "templates_for_subject_id": {
        "catchment":  "hyobs:catchment_{id}",
        "sensor":     "hyobs:sensor_{id}",
        "collection": "sosa:observationCollection_{id}",
        "observation":"hyobs:observation_{id}_{rowIndex}_{slug}"
      }
    }
  },
  "rules": {
    "precipitation": [
      ["@subject", "@observation"],
      ["rdf:type", "sosa:Observation"],
      ["sosa:observedProperty", "envthes:30106"],
      ["sosa:hasFeatureOfInterest", "@catchment"],
      ["sosa:madeBySensor", "@sensor"],
      ["sosa:memberOf", "@collection"],
      ["sosa:resultTime", "@resultTime"],
      ["sosa:hasResult", [
        ["rdf:type","qudt:QuantityValue"],
        ["qudt:numericValue","^^xsd:decimal"],
        ["qudt:unit","unit:MilliM"]
      ]]
    ]
  }
}

```
### SHP example (points) - gauging stations (From Lamah-CE)
```json
{
  "prefixes": {
    "rdf":"http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "sosa":"http://www.w3.org/ns/sosa/",
    "geo":"http://www.opengis.net/ont/geosparql#",
    "sf":"http://www.opengis.net/ont/sf#",
    "dct":"http://purl.org/dc/terms/",
    "xsd":"http://www.w3.org/2001/XMLSchema#",
    "hyobs":"https://w3id.org/hmontology/"
  },
  "configuration": {
    "shapefile": { "src_crs": "EPSG:3035" },
    "column_types": {
      "id": { "column_name": "ID", "id_from_filename": null },
      "date": { "column_name": null, "format": null },
      "time": { "column_name": null, "format": null },
      "templates_for_subject_id": {
        "sensor":"hyobs:sensor_{id}",
        "geom":"hyobs:geomPoint_{id}"
      }
    }
  },
  "rules": {
    "@subject": { "@template": "@sensor" },
    "rdf:type": "sosa:Sensor",
    "dct:identifier": "^^xsd:string",
    "geo:hasGeometry": "@geom",
    "@geom": [
      ["rdf:type", "sf:Point"],
      ["geo:asWKT", {"@wkt": "geometry"}]
    ]
  }
}
```

## 🔰 Getting started

To get started with defining your own mappings and performing conversion steps, see [here](/Getting%20Started.md).

## 📧 Contact
- [Auriol Degbelo](https://sites.google.com/site/aurioldegbelo)
- Shamila Sudalshana

## 🙌 Acknowledgments
Built using the: 
- [LamaH-CE Dataset](https://essd.copernicus.org/articles/13/4529/2021/)
- Camels-GB Dataset
- Quadica Dataset

The work was funded by the German Research Foundation through the project [NFDI4Earth](https://www.nfdi4earth.de/) (DFG project no. 460036893).
