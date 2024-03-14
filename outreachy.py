from osm_fieldwork.basemapper import create_basemap_file
from osm_fieldwork.shared_utils import read_bytes_geojson

FILEPATH = "tests/testdata/Rollinsville.geojson"
boundary = read_bytes_geojson(FILEPATH)

create_basemap_file(
    verbose=True,
    boundary=boundary,
    outfile="outreachy.mbtiles",
    zooms="12-15",
    source="esri",
)
