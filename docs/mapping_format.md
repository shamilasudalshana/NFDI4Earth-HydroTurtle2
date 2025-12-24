# HydroTurtle Mapping Format

## 1. Introduction

HydroTurtle uses **mapping-driven transformation** to convert tabular hydrological datasets (CSV, Shapefile) into RDF/Turtle. Instead of writing code, users describe *how columns should be interpreted* and *how RDF resources should be created* using a JSON mapping file.

This design is intended for **hydrologists and environmental scientists**, not software developers. The goal is to make data conversion:

- Transparent
- Reusable
- Easy to adapt to new datasets

A mapping file describes *what the data means*, not *how the code works*.

---

## 2. Overall Structure of a Mapping File

A HydroTurtle mapping file has three main sections:

```json
{
  "prefixes": { ... },
  "configuration": { ... },
  "rules": { ... }
}
```

- **prefixes** – RDF namespace prefixes used in the mapping
- **configuration** – how IDs, dates, and URIs are constructed
- **rules** – how individual columns are converted into RDF triples

Each section is explained in detail below.

---

## 3. Prefixes

The `prefixes` section defines namespace shortcuts used throughout the mapping file.

Example:

```json
"prefixes": {
  "rdf":  "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
  "sosa": "http://www.w3.org/ns/sosa/",
  "qudt": "http://qudt.org/schema/qudt/",
  "unit": "http://qudt.org/vocab/unit/",
  "xsd":  "http://www.w3.org/2001/XMLSchema#",
  "hyobs": "https://w3id.org/hmontology/"
}
```

Users can freely add additional vocabularies as needed.

---

## 4. Configuration

The `configuration` section defines **how HydroTurtle understands the structure of the CSV file**.

### 4.1 column_types.id

Defines how the unique identifier of a station or catchment is obtained.

```json
"id": {
  "column_name": "gauge_id",
  "id_from_filename": {
    "regex": "CAMELS_GB_hydromet_timeseries_(\\d{4})_",
    "regex-split": 1
  }
}
```

- `column_name`: name of the ID column in the CSV (or `null` if not present)
- `id_from_filename`: optional way to extract ID from the filename using a regular expression

Either approach can be used, depending on the dataset.

---

### 4.2 column_types.date and time

Defines how timestamps are constructed.

Example with a single date column:

```json
"date": {
  "column_name": "date",
  "format": "%Y-%m-%d"
}
```

Example with multi-column dates (YYYY, MM, DD):

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

HydroTurtle combines these into an `xsd:dateTime` value used as `sosa:resultTime`.

---

### 4.3 templates_for_subject_id

This block defines how RDF resource identifiers (URIs) are constructed.

```json
"templates_for_subject_id": {
  "sensor": "hyobs:sensor_{id}",
  "catchment": "hyobs:catchment_{id}",
  "geom": "hyobs:geomPoint_{id}",
  "observation": "hyobs:observation_{id}_{rowIndex}_{slug}"
}
```

Available placeholders:

- `{id}` – station or catchment identifier
- `{rowIndex}` – row number in the CSV
- `{slug}` – lowercase column name

These templates ensure globally unique and reproducible URIs.

---

## 5. Rules

The `rules` section defines how **each CSV column** is converted into RDF.

Rules are keyed by **column name**.

If a column listed in `rules` does not exist in the CSV file, it is silently ignored. This allows one mapping to be reused across similar datasets.

---

### 5.1 Basic rule structure

```json
"precipitation": [
  ["@subject", "@observation"],
  ["rdf:type", "sosa:Observation"],
  ["sosa:observedProperty", "envthes:30106"],
  ["sosa:hasFeatureOfInterest", "@catchment"],
  ["sosa:madeBySensor", "@sensor"],
  ["sosa:resultTime", "@resultTime"],
  ["sosa:hasResult", [
    ["rdf:type", "qudt:QuantityValue"],
    ["qudt:numericValue", "^^xsd:decimal"],
    ["qudt:unit", "unit:MilliM"]
  ]]
]
```

---

### 5.2 Special tokens

- `@subject` – switch the current RDF subject
- `@sensor`, `@catchment`, `@collection`, `@observation` – resolve to URI templates
- `@resultTime` – automatically generated timestamp

---

### 5.3 Typed literal shorthand

HydroTurtle supports a shorthand notation:

```json
"^^xsd:decimal"
```

This automatically inserts the current CSV value as a typed literal.

---

## 6. Best Practices

- One mapping file per dataset schema
- Use examples as templates
- Do not worry about repeated rdf:type statements (duplicates are removed automatically)
- Test mappings on small CSV slices first

---

## 7. Examples

See the `examples/` directory in the HydroTurtle repository for complete, working mappings:

- LamaH-CE dataset (daily data)
- CAMELS-GB dataset (daily data)
- QUADICA dataset (monthly data)

---

This mapping format is designed to be reusable, extensible, and understandable by domain scientists without programming experience.

