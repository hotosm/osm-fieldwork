from io import BytesIO

from osm_fieldwork.basemapper import create_basemap_file


def main():
    with open("/Users/pro-3ies/Desktop/osm-fieldwork/tests/testdata/Rollinsville.geojson", "rb") as geojson_file:
        boundary = geojson_file.read()
        boundary_bytesio = BytesIO(boundary)


create_basemap_file(
    verbose=True,
    boundary="-4.730494,41.650541,-4.725634,41.652874",
    outfile="outreachy.mbtiles",
    zooms="12-15",
    source="esri",
)

if __name__ == "__main__":
    main()
