from datetime import datetime

def from_columns(values, fmts):
    # values: ["2020-01-01","12:00:00"], fmts: ["%Y-%m-%d","%H:%M:%S"]
    dt = datetime.strptime(" ".join(values), " ".join(fmts))
    return f'"{dt.strftime("%Y-%m-%dT%H:%M:%SZ")}"^^xsd:dateTime'

def from_month(month_val, template="2000-{MM}-15T00:00:00Z"):
    m = int(month_val)
    iso = template.replace("{MM}", f"{m:02d}")
    return f'"{iso}"^^xsd:dateTime'
