#!/usr/bin/python3

"""module for testing the perfomance of basemapper"""

from io import BytesIO
from osm_fieldwork.basemapper import create_basemap_file

with open("./tests/testdata/Rollinsville.geojson", "rb") as geojson_file:
    boundary =  geojson_file.read()
    boundary_bytesio = BytesIO(boundary)

create_basemap_file(
    verbose=True,
    boundary=boundary_bytesio,
    outfile="outreachy.mbtiles",
    zooms="12-15",
    source="esri",
)
