from osm_fieldwork.basemapper import create_basemap_file

create_basemap_file(
    verbose=True,
    boundary="-4.730494,41.650541,-4.725634,41.652874",
    outfile="outreachy.mbtiles",
    zooms="12-15",
    source="esri",
)