## make_data_extract.py

The `make_data_extract.py` program is used to extract OpenStreetMap
(OSM) data for use with the `select_one_from_file` function in ODK
Collect. This function allows users to select from a list of options
generated from an external file. The `make_data_extract.py` program
creates a data extract that can be used as an external file with the
XLSForm. The data extract can be created using local Postgres
database, or the remote Underpass database.

To use the new `select_one_from_file` for editing existing OSM data you
need to produce a data extract from OSM. This can be done several
ways, but needed to be automated to be used for FMTM.

    options:
     --help (-h)               show this help message and exit
     --verbose (-v)            verbose output
     --geojson (-g) GEOJSON    Name of the GeoJson output file
     --boundary (-b) BOUNDARY  Boundary polygon to limit the data size
     --category (-c) CATEGORY  Which category to extract
     --uri (-u) URI            Database URI
     --xlsfile (-x) XLSFILE    An XLSForm in the library
     --list (-l) List          List all XLSForms in the library

## Examples

Make\*data\*extract uses a Postgres database to extract OSM data. By
default, the program uses **localhost** as the database host. If you
use \**underpass*as the data base name, this will remotely access the
[Humanitarian OpenStreetMap Team(HOT)](https://www.hotosm.org)
maintained OSM database that covers the entire planet, and is updated
every minute. The name of the database can be specified using the
\*--uri\*\* option. The program extracts the buildings category of OSM
data by default. The size of the extracted data can be limited using
the \_--boundary\* option. The program outputs the data in GeoJSON
format.

For raw OSM data, the existing country data is downloaded from [GeoFabrik](https://download.geofabrik.de/index.html), and imported using a
modified schema for osm2pgsql. First create the database and install
two postgres extensions:

    # createdb nigeria
    psql -d nigeria -c "CREATE EXTENSION postgis"
    psql -d nigeria -c "CREATE EXTENSION hstore"

And then import the OSM data.

> osm2pgsql --create -d nigeria --extra-attributes --output=flex --style raw.lua nigeria-latest-internal.osm.pbf

The *raw.lua* script is [available
here](https://github.com/hotosm/underpass/blob/master/utils/raw.lua). It's
part of the [Underpass
project](https://hotosm.github.io/underpass/index.html). It uses a
more compressed and efficient data schema.

### Example

    ./make_data_extract.py -u colorado --boundary mycounty.geojson -g mycounty_buildings.geojson

This example extracts the `buildings` category of OSM data from a
Postgres database named `colorado`. The program limits the size of the
extracted data to the boundary specified in the `mycounty.geojson`
file. The program outputs the data in GeoJSON format to a file named
`mycounty_buildings.geojson`.

### Boundary

The `--boundary` option can be used to specify a polygon boundary to
limit the size of the extracted data. The boundary has to be in
GeoJSON format, both multipolygons and polygons are supported.

Example:

    ./make_data_extract.py -u foo@colorado --category healthcare --boundary mycounty.geojson -g mycounty_healthcare.geojson

This example extracts the `healthcare` category of OSM data from a
Postgres database named `colorado` with e user *foo*. The program
limits the size of the extracted data to the boundary specified in the
`mycounty.geojson` file. The program outputs the data in GeoJSON
format to a file named `mycounty_healtcare.geojson`.

### Category

The `--category` option can be used to specify which category of OSM
data to extract. The program supports any category in the [xlsform
library](https://github.com/hotosm/osm-fieldwork/tree/main/osm_fieldwork/xlsforms)

### Example

    ./make_data_extract.py -u underpass --boundary mycounty.geojson --category amenities -g mycounty_amenities.geojson

This example uses Overpass Turbo to extract the `amenities` category
of OSM data within the boundary specified in the `mycounty.geojson`
file. The program outputs the data in GeoJSON format to a file named
`mycounty_amenities.geojson`.

### Output File Format

The program outputs the extracted OSM data in GeoJSON format. The name
of the output file can be specified using the `--geojson option`. If
the option is not specified, the program uses the input file name with
`_buildings.geojson` appended to it.

    ./make_data_extract.py -u colorado --boundary mycounty.geojson -g mycounty_buildings.geojson

## File Formats

ODK has 3 file formats. The primary one is the source file,
which is in XLSX format, and follows the XLSXForm specification. This
file is edited using a spreadsheet program, and convert using the
xls2xform program. That conversion products an ODK XML file. That file
is used by ODK Collect to create the input forms for the mobile
app. When using ODK Collect, the output file is another XML format,
unique to ODK Collect. These are the data collection instances.

The ODK server, ODK Central supports the downloading of XForms to the
mobile app, and also supports downloading the collected data. The only
output format is CSV.
