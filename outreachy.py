from io import BytesIO
from osm_fieldwork.basemapper import create_basemap_file

with open("D:\\customers\\osm-fieldwork\\tests\\testdata\\Rollinsville.geojson", "rb") as f:
    boundary = f.read() # Read the file into memory
    boundary_bytesio = BytesIO(boundary)   # Convert the file into a BytesIO object


create_basemap_file(
    verbose=True,
    boundary=boundary_bytesio,
    outfile="outreachy.mbtiles",
    zooms="12-15",
    source="esri",
)
