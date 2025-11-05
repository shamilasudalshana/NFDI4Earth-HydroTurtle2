# HydroTurtle

HydroTurtle converts tabular hydrometeorological datasets (CSV) to RDF/Turtle using
[SOSA/SSN](https://www.w3.org/TR/vocab-ssn/), [QUDT](https://qudt.org/), plus HYOBS and EnvThes terms.
Mappings are JSON files that declare how columns become observations or attributes.

## Install

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
pip install -U pip
pip install .
```

## Usage
```bash
hydroturtle input.csv mapping.json out.ttl
# or:
python -m hydroturtle.cli input.csv mapping.json out.ttl
```
HydroTurtle auto-detects CSV encoding (utf-8, cp1252, etc.).
If needed, override:
```bash
hydroturtle input.csv mapping.json out.ttl --csv-encoding cp1252
```

## Mappings

See examples/quadica/:

mapping_quadica_meteo_daily.json – OBJECTID, Date, tavg/pre/pet

mapping_wrtds_monthly.json – WRTDS monthly concentration/flux/FN outputs

mapping_quadica_attributes.json – catchment attributes

Key features:

context.columns to set ID/Date columns once

@catchment, @sensor, @collection, @resultTime shorthands

@subject override per-rule (write to sensor/catchment)

["select", "$col", ["Case","IRI"], ["default","IRI"]] for branching

Typed placeholders: ^^xsd:decimal, ^^xsd:integer


## Legacy
Old scripts preserved in legacy/. The new engine is streaming, encoding-robust, and mapping-driven.
