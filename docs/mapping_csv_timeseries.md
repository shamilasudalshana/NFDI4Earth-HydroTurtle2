# Mapping CSV Time Series Data

## 1. Purpose

This document explains how to use HydroTurtle mapping files to convert **time series CSV files** (e.g. daily, monthly observations) into RDF using SOSA/SSN and QUDT.

Typical datasets include:

- CAMELS-GB daily time series
- LamaH-CE daily time series
- QUADICA monthly data

---

## 2. Key Differences from Attribute Mappings

Time series mappings and attribute mappings both use the same JSON structure, but they differ in what kind of RDF nodes they create.

Time series mappings typically:

- Create one `sosa:Observation` per variable per row
- Use `@resultTime` for timestamps
- Use `@collection` to group observations for an ID

Attribute mappings typically:

- Do not create `sosa:Observation` nodes
- Attach properties directly to `@sensor` or `@catchment`
- Often describe geometry, area, or static statistics

---

## 3. Key Characteristics of Time Series Mappings

Time series mappings usually share the following features:

- One row = one observation per variable
- A date (or year/month/day components)
- Multiple measured variables in columns

HydroTurtle creates:

- One `sosa:Observation` per row *and* per variable
- A shared `sosa:ObservationCollection` per station/catchment

---

## 4. Configuration for Time Series

### 4.1 Identifier

Example:

```json
"id": {
  "column_name": "OBJECTID",
  "id_from_filename": null
}
```

The identifier is reused for:

- Sensor URI
- Catchment URI
- Observation collection URI

---

### 4.2 Date and Time

Single-column date example: (Camels-GB)

```json
"date": {
  "column_name": "Date",
  "format": "%Y-%m-%d"
}
```

Multi-column date example: (LamaH-CE)

```json
"date": {
  "column_name": null,
  "format": null,
  "components": [
    { "column_name": "YYYY", "format": "%Y" },
    { "column_name": "MM",   "format": "%m" },
    { "column_name": "DD",   "format": "%d" }
  ]
}
```

HydroTurtle automatically generates `sosa:resultTime`.

---

## 5. Writing Time Series Rules

Each rule corresponds to **one variable/column**.

Example for precipitation:

```json
"prec": [
  ["@subject", "@observation"],
  ["rdf:type", "sosa:Observation"],
  ["sosa:observedProperty", "envthes:30106"],
  ["sosa:hasFeatureOfInterest", "@catchment"],
  ["sosa:madeBySensor", "@sensor"],
  ["sosa:memberOf", "@collection"],
  ["sosa:resultTime", "@resultTime"],
  ["sosa:hasResult", [
    ["rdf:type", "qudt:QuantityValue"],
    ["qudt:numericValue", "^^xsd:decimal"],
    ["qudt:unit", "unit:MilliM"]
  ]]
]
```

---

## 6. Reusing One Mapping for Multiple Datasets

HydroTurtle ignores rules whose column names do not exist in the CSV.

This allows a single mapping file to be reused for within same dataset with differnt files (follows the same data schema) as example: 

- QUADICA meteo monthly CSVs
- WRTDS monthly CSVs

Only matching columns are converted.

---

## 6. Common Patterns

### 6.1 Quantities with units

Use `sosa:hasResult` + `qudt:QuantityValue`.

### 6.2 Simple numeric values

Use `sosa:hasSimpleResult`:

```json
["sosa:hasSimpleResult", "^^xsd:decimal"]
```

### 6.3 Analyte selection (in QUADIC)

For water quality datasets, use `select` blocks to map solutes dynamically.

```json
"qwmean_C": [
  ["@subject", "@observation"],
  ["rdf:type", "sosa:Observation"],
  ["sosa:observedProperty", "hyobs:SoluteConcentrationFlowWeightedMean"],
  ["hyobs:hasAnalyte",
    ["select", "$solute",
      ["Cl",   "chebi:17996"],
      ["NO3N", "chebi:17632"],
      ["NH4N", "chebi:28938"],
      ["PO4P", "chebi:18367"],
      ["SO4",  "chebi:16189"],
      ["Ca",   "chebi:29108"],
      ["Mg",   "chebi:18420"],
      ["DIN",  "hyobs:DissolvedInorganicNitrogen"],
      ["DOC",  "hyobs:DissolvedOrganicCarbon"],
      ["TOC",  "hyobs:TotalOrganicCarbon"],
      ["TN",   "hyobs:TotalNitrogen"],
      ["TP",   "hyobs:TotalPhosphorus"],
      ["default", "hyobs:UnknownAnalyte"]
    ]
```


---

## 7. Testing

Recommended workflow:

1. Test with a small CSV slice
2. Inspect Turtle output
3. Run `csv-batch` on the full dataset

---

Time series mappings are the most common use case for HydroTurtle and are designed to be easy to adapt and reuse.

