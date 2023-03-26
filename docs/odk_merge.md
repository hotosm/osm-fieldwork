# odk_merge.py

This program conflates the data collected using ODK Collect with
existing OSM data. Many buildings in OSM were from imports of AI
derived building footprints, and the only tages are
_building=yes_. When doing ground data collection, in addition to
collecting new data, you want to add or correct tags in existing OSM
data.

The file of collected data is downloaded as a CSV file from ODK Central.
Then it's converted to OSM XML using **CSVDump.py**. Once converted,
to OSM XML format, all tags can be merged or added to existing OSM
data.

## Usage

    usage: odk_merge.py [-h] [-v] [-c ODKFILE] [-f OSMFILE] [-o OUTFILE] [-b BOUNDARY]

    This program conflates ODK data with existing features from OSM.

    options:
    -h, --help            show this help message and exit
    -v, --verbose         verbose output
    -c ODKFILE, --odkfile ODKFILE - ODK CSV file downloaded from ODK Central
    -f OSMFILE, --osmfile OSMFILE - OSM XML file created by odkconvert
    -o OUTFILE, --outfile OUTFILE - Output file from the merge
    -b BOUNDARY, --boundary BOUNDARY - Boundary polygon to limit the data size

The boundary file is a polygon to limit the dataset size, useful when
using downloaded OSM data for entire countries, or using a large
database. Most ODK data files are not usually very large. It can be in
any format, but GeoJson is the most common.

To specify a database as the OSM source, the input file gets prefixed
with _pg:_, followed by the database name. Otherwise use a disk
file.

The ODK source is an OSM XML file created by _CSVDump.py_, where all the
tags have been converted from the ODK Central submission download. The
output file is in OSM XML format, and contains modified entries where
existing data has the new tags added.

The `-c` and `-f` options are mandatory, while the `-o` and `-b` options are optional.

The `-b` option is useful when working with large OSM data files or when the user wants to limit the area of the merged data. The boundary file can be in any format, but GeoJSON is the most common.

However, currently, The --boundary (-b) option only takes a GeoJson file containing, not bounding box coordinates. It'd be a nice enhancement to add support for that, but currently it doesn't exist.

## Examples

    ./odk_merge.py -f pg:osm -c buildings.osm -b boundary.geojson

### Here are more examples of how to use odk_merge.py:

- Merge ODK data with an OSM XML file located on disk:

        odk_merge.py -c path/to/odk.csv -f path/to/osm.xml -o path/to/output.xml

    This command merges the ODK data in `odk.csv` with the OSM data in `osm.xml`, and outputs the resulting merged data in `output.xml`.

- Merge ODK data with an OSM database:

        odk_merge.py -c path/to/odk.csv -f pg:osm -o path/to/output.xml

    This command merges the ODK data in `odk.csv` with the OSM data in the database named `osm`, and outputs the resulting merged data in `output.xml`.

- Merge ODK data with an OSM XML file, limiting the merged data to a boundary polygon:

        odk_merge.py -c path/to/odk.csv -f path/to/osm.xml -o path/to/output.xml -b path/to/boundary.geojson

    This command merges the ODK data in `odk.csv` with the OSM data in `osm.xml`, limiting the merged data to the area defined by the boundary polygon in `boundary.geojson`, and outputs the resulting merged data in `output.xml`.

- Merge ODK data with an OSM XML file, enabling verbose output:

        odk_merge.py -c path/to/odk.csv -f path/to/osm.xml -o path/to/output.xml -v

    This command merges the ODK data in `odk.csv` with the OSM data in `osm.xml`, enabling verbose output during the merge process, and outputs the resulting merged data in `output.xml`.

- Merge ODK data with an OSM XML file, limiting the merged data to a boundary polygon and specifying a different output file name:

        odk_merge.py -c path/to/odk.csv -f path/to/osm.xml -o path/to/merged_data.xml -b path/to/boundary.geojson

    This command merges the ODK data in `odk.csv` with the OSM data in `osm.xml`, limiting the merged data to the area defined by the boundary polygon in `boundary.geojson`, and outputs the resulting merged data in `merged_data.xml`.

- Merge ODK data with an OSM database, limiting the merged data to a boundary polygon:

        odk_merge.py -c path/to/odk.csv -f pg:osm -o path/to/output.xml -b path/to/boundary.geojson

    This command merges the ODK data in `odk.csv` with the OSM data in the database named `osm`, limiting the merged data to the area defined by the boundary polygon in `boundary.geojson`, and outputs the resulting merged data in `output.xml`.

- Merge ODK data with an OSM database, enabling verbose output:

        odk_merge.py -c path/to/odk.csv -f pg:osm -o path/to/output.xml -v

    This command merges the ODK data in `odk.csv` with the OSM data in the database named `osm`, enabling verbose output during the merge process, and outputs the resulting merged data in `output.xml`.

- Merge ODK data with an OSM XML file, limiting the merged data to a boundary polygon specified as a WKT string:

        odk_merge.py -c path/to/odk.csv -f path/to/osm.xml -o path/to/output.xml -b "POLYGON((-122.4324 37.7782,-122.4120 37.7782,-122.4120 37.7880,-122.4324 37.7880,-122.4324 37.7782))"

    This command merges the ODK data in `odk.csv` with the OSM data in `osm.xml`, limiting the merged data to the area defined by the boundary polygon specified as a WKT string, and outputs the resulting merged data in `output.xml`.

- Merge ODK data with an OSM XML file, specifying a relative path for the output file:

        odk_merge.py -c path/to/odk.csv -f path/to/osm.xml -o ../output.xml

    This command merges the ODK data in `odk.csv` with the OSM data in `osm.xml`, and outputs the resulting merged data in a file named `output.xml` one level up from the current directory.

- Merge ODK data with an OSM database, specifying a different database name:

        odk_merge.py -c path/to/odk.csv -f pg:myosmdb -o path/to/output.xml

This command merges the ODK data in `odk.csv` with the OSM data in the database named `myosmdb`, and outputs the resulting merged data in `output.xml`.
