from pyproj import Transformer

# Function to transform coordinates
def transform_coordinates(dataframe, x_col, y_col, input_epsg="EPSG:3035", output_epsg="EPSG:4326"):
    """
    Transforms coordinates from input_epsg to output_epsg.
    Overwrites the specified x_col and y_col in the DataFrame.
    """
    transformer = Transformer.from_crs(input_epsg, output_epsg, always_xy=True)
    dataframe[[x_col, y_col]] = dataframe.apply(
        lambda row: transformer.transform(row[x_col], row[y_col]),
        axis=1,
        result_type='expand'
    )
    return dataframe


# Function to check and transform CRS
def ensure_wgs84(gdf): #gdf means GeoDataFrame
    """
    Ensures that the GeoDataFrame's CRS is WGS 84 (EPSG:4326).
    If not, transforms it to WGS 84.
    """
    if gdf.crs is None:
        raise ValueError("The dataset does not have a CRS defined. Please provide the current CRS.")

    # Check if the CRS is already WGS 84
    if gdf.crs.to_string() != "EPSG:4326":
        print(f"Current CRS: {gdf.crs}")
        #new_crs = input("Please provide the EPSG code of the current CRS (e.g., 'EPSG:3035'): ")

        # Reproject the GeoDataFrame to WGS 84
        gdf = gdf.to_crs("EPSG:4326")
        print(f"Transformed to WGS 84: {gdf.crs}")

    return gdf