## make_data_extract.py

The `make_data_extract.py` program is used to extract OpenStreetMap
(OSM) data for use with the `select_one_from_file` function in ODK
Collect. This function allows users to select from a list of options
generated from an external file. The `make_data_extract.py` program
creates a data extract that can be used as an external file with the
`select_one_from_file` function. The data extract can be created using
Overpass Turbo or a Postgres database.

To use the new `select_one_from_file` for editing existing OSM data you
need to produce a data extract from OSM. This can be done several
ways, but needed to be automated to be used for FMTM.

    options:
     -h, --help            show this help message and exit
     -v, --verbose         verbose output
     -o, --overpass        Use Overpass Turbo
     -p, --postgres        Use a postgres database
     -g GEOJSON, --geojson GEOJSON Name of the GeoJson output file
     -i INFILE, --infile INFILE  Use a data file
     -dn DBNAME, --dbname DBNAME Database name
     -dh DBHOST, --dbhost DBHOST Database host
     -b BOUNDARY, --boundary BOUNDARY  Boundary polygon to limit the data size
     -c {buildings,amenities}, --category {buildings,amenities}
                        Which category to extract


## Examples

### Postgres Database:

The --postgres option uses a Postgres database to extract OSM data. By
default, the program uses **localhost** as the database host. If you
use **underpass* as the data base name, this will remotely access the
[Humanitarian OpenStreetMap Team(HOT)](https://www.hotosm.org)
maintained OSM database that covers the entire planet, and is updated
every minute. The name of the database can be specified using the
_--dbname_ option. The program extracts the buildings category of OSM
data by default. The size of the extracted data can be limited using
the _--boundary_ option. The program outputs the data in GeoJSON
format.

### Example:

    ./make_data_extract.py --postgres -dn colorado --boundary mycounty.geojson -g mycounty_buildings.geojson

This example extracts the `buildings` category of OSM data from a
Postgres database named `colorado`. The program limits the size of the
extracted data to the boundary specified in the `mycounty.geojson`
file. The program outputs the data in GeoJSON format to a file named
`mycounty_buildings.geojson`.

### Input File:

The `--infile` option can be used to specify an input file in OSM XML,
OSM PBF, or GeoJSON format. The program extracts the `buildings`
category of OSM data by default. The program outputs the data in
GeoJSON format. This can be used instead of a database.

### Example:

    ./make_data_extract.py --infile mydata.osm.pbf -g mydata_buildings.geojson

This example extracts the `buildings` category of OSM data from an
input file in OSM PBF format named `mydata.osm.pbf`. The program
outputs the data in GeoJSON format to a file named
`mydata_buildings.geojson`.

### Boundary:

The `--boundary` option can be used to specify a polygon boundary to
limit the size of the extracted data. The boundary can be specified in
GeoJSON format.

Example:

    ./make_data_extract.py --postgres -dn colorado --category buildings --boundary mycounty.geojson -g mycounty_buildings.geojson

This example extracts the `buildings` category of OSM data from a
Postgres database named `colorado`. The program limits the size of the
extracted data to the boundary specified in the `mycounty.geojson`
file. The program outputs the data in GeoJSON format to a file named
`mycounty_buildings.geojson`.

### Category:

The `--category` option can be used to specify which category of OSM
data to extract. The program supports any category in the [xlsform
library](https://github.com/hotosm/osm-fieldwork/tree/main/osm_fieldwork/xlsforms)

### Example:

    ./make_data_extract.py --overpass --boundary mycounty.geojson --category amenities -g mycounty_amenities.geojson

This example uses Overpass Turbo to extract the `amenities` category
of OSM data within the boundary specified in the `mycounty.geojson`
file. The program outputs the data in GeoJSON format to a file named
`mycounty_amenities.geojson`.

### Output File Format:

The program outputs the extracted OSM data in GeoJSON format. The name
of the output file can be specified using the `--geojson option`. If
the option is not specified, the program uses the input file name with
`_buildings.geojson` appended to it.

    ./make_data_extract.py --overpass --boundary mycounty.geojson -g mycounty_buildings.geojson

This example uses Overpass Turbo to extract the `buildings` category
of OSM data within the boundary specified in the `mycounty.geojson`
file. The program outputs the data in GeoJSON format to a file named
`mycounty_buildings.geojson`.

### Overpass Turbo:
The `--overpass` option uses Overpass Turbo to extract OSM data. By
default, the program extracts the `buildings` category of OSM
data. The size of the extracted data can be limited using the
`--boundary` option. The program outputs the data in GeoJSON format.

### Example:

    ./make_data_extract.py --overpass --boundary mycounty.geojson -g mycounty_buildings.geojson

This example uses Overpass Turbo to extract the `buildings` category
of OSM data within the boundary specified in the `mycounty.geojson`
file. The program outputs the data in GeoJSON format to a file named
`mycounty_buildings.geojson`.

## File Formats

OpenDataKit has 3 file formats. The primary one is the source file,
which is in XLSX format, and follows the XLSXForm specification. This
file is edited using a spreadsheet program, and convert using the
xls2xform program. That conversion products an ODK XML file. That file
is used by ODK Collect to create the input forms for the mobile
app. When using ODK Collect, the output file is another XML format,
unique to ODK Collect. These are the data collection instances.

The ODK server, ODK Central supports the downloading of XForms to the
mobile app, and also supports downloading the collected data. The only
output format is CSV.
