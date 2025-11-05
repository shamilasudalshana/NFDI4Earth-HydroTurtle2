from typing import Optional
from shapely.geometry.base import BaseGeometry
from shapely import to_wkt

# GeoSPARQL 1.1 recommends CRS IRI in the literal:
CRS84_IRI = "http://www.opengis.net/def/crs/OGC/1.3/CRS84"

def wkt_literal_crs84(geom: BaseGeometry) -> str:
    """
    Return a GeoSPARQL typed literal string including the CRS IRI prefix.
    Example: "<CRS84> POINT(lon lat)"^^geo:wktLiteral
    """
    # Preserve Z if present; Shapely 2's to_wkt auto-detects dimension
    wkt = to_wkt(geom, rounding_precision=15)
    return f"\"<{CRS84_IRI}> {wkt}\"^^geo:wktLiteral"
