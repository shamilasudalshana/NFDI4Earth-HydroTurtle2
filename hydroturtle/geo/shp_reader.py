from typing import Iterator, Optional, Dict, Any
import fiona
from shapely.geometry import shape
from shapely.ops import transform as shp_transform
from pyproj import CRS, Transformer

def _derive_src_crs(dataset) -> Optional[CRS]:
    # Fiona exposes crs_wkt (new) or crs (legacy). Handle both.
    try:
        if dataset.crs_wkt:
            return CRS.from_wkt(dataset.crs_wkt)
    except Exception:
        pass
    try:
        if dataset.crs:
            return CRS.from_user_input(dataset.crs)
    except Exception:
        pass
    return None

def _make_transformer(src: CRS, dst: CRS) -> Transformer:
    # always_xy=True enforces lon,lat order which we want for CRS84
    return Transformer.from_crs(src, dst, always_xy=True)

def iter_features(shp_path: str,
                  id_field: str = "OBJECTID",
                  src_crs_override: Optional[str] = None
                  ) -> Iterator[Dict[str, Any]]:
    """
    Stream features from a shapefile. Each item:
      { "id": <id value>, "props": <attr dict>, "geom": <shapely geometry in CRS84> }
    """
    dst_crs = CRS.from_user_input("OGC:CRS84")  # lon/lat

    with fiona.open(shp_path) as ds:
        src_crs = CRS.from_user_input(src_crs_override) if src_crs_override else _derive_src_crs(ds)
        if not src_crs:
            raise RuntimeError(
                "No CRS detected for shapefile and none provided. "
                "Re-run with --src-crs EPSG:xxxx (e.g. --src-crs EPSG:25833)."
            )

        tfm = _make_transformer(src_crs, dst_crs)

        for feat in ds:
            props = dict(feat.get("properties", {}))
            if id_field not in props:
                raise KeyError(f"ID field '{id_field}' not found in attributes: available={list(props.keys())[:10]}...")
            fid = props[id_field]
            if feat.get("geometry") is None:
                # skip empty geometries cleanly
                continue
            g = shape(feat["geometry"])

            # Support 2D and 3D transforms
            def _xy(x, y, z=None):
                if z is None:
                    x2, y2 = tfm.transform(x, y)
                    return (x2, y2)
                else:
                    x2, y2, z2 = tfm.transform(x, y, z)
                    return (x2, y2, z2)

            g84 = shp_transform(_xy, g)
            yield {"id": fid, "props": props, "geom": g84}
