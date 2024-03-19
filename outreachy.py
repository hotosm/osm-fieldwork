from io import BytesIO
from osm_fieldwork.basemapper import create_basemap_file

with open("C:\Users\jahna\Downloads\map.geojson", "rb") as geojson_file:
    boundary = geojson_file.read()
    boundary_bytesio = BytesIO(boundary)

create_basemap_file(
    verbose=True,
    boundary=boundary_bytesio,
    outfile="outreachy.mbtiles",
    zooms="12-15",
    source="esri",
)