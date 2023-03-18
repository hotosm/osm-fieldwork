# ODK Convert Utility Programs

ODK Convert contains a few standalone utility programs for converting
data from ODK Collect and the ODK Central server, and a few support
modules.

## make_data_extract.py

To use the new select_one_from_file for editing existing OSM data you
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

For example,

    ./make_data_extract.py --overpass --boundary mycounty.geojson

will use Overpass Turbo to extract data within the boundary. By
default, buildings are extracted.

Or this example:

    ./make_data_extract.py --postgres -dn colorado --category amenities --boundary mycounty.geojson

Which will extract the data from postgres. By default _localhost_ is
used, but that can be changed with --dbhost. This will use the
database _colorado_, and extract all the amenities.

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

## CSVDump.py

CSVDump.py converts a CSV downloaded from ODK Central to OSM XML.

    options:
     -h, --help                   - show this help message and exit
     -v, --verbose                - verbose output
     -i CSVFILE, --infile CSVFILE - The input file downloaded from ODK Central

## odk2csv.py

odk2csv.py converts an ODK XML instance file to the same CSV format
used by ODK Central.

    options:
     -h, --help                       - show this help message and exit
     -v, --verbose                    - verbose output
     -i INSTANCE, --instance INSTANCE - The instance file from ODK Collect

These are the modules containing support functions. These need to be
loaded into the python package managber, pip, before they can be
used. For debugging purposes these can be run from the command line as
well.

To install these from the source tree, you can either install
manually,

     pip install -e .

or run the python setup program

     python setup.py install

## ODKDump.py

    options:
     -h, --help              - show this help message and exit
     -v, --verbose           - verbose output
     -i, --instance INSTANCE - The instance file from ODK Collect
     -x, --xform XFORM       - Load an alternal conversion file
     -o, --outdir            - The directory for the output file

## ODKForm.py

ODKForm.py parses the ODK XML XForm, and creates a data structure so
any code using this class can access the data types of each input
field. It can be run standalone from the command line, but this is
only for debugging purposes.

    options:
     -h, --help                           - show this help message and exit
     -v, --verbose,                       - verbose output
     -i, --infile XFORM, --instance XFORM - The definition file from ODK Collect

## ODKInstance.py

ODKInstance.py parses the ODK Collect instanceXML file, and creates a
data structure so any code using this class can access the collected
data values. It can be run standalone from the command line, but this is
only for debugging purposes.

    options:
     -h, --help                       - show this help message and exit
     -v, --verbose                    - verbose output
     -i INSTANCE, --instance INSTANCE - The instance file from ODK Collect

## convert.py

This module uses the yaml config file to handle the conversion
process.

## osmfile.py
This module write OSM XML format output file.

osmfile.py is a Python module that provides functionality for writing OpenStreetMap (OSM) XML format output files. It is used as part of the odkconvert toolset, and can be used as part of a larger Python application.

When used, osmfile.py takes a Python data structure containing OSM data as input and generates an OSM XML format output file. The data structure consists of nested Python dictionaries and lists, with each dictionary representing an OSM node, way or relation, and each list representing a set of nodes, ways or relations.

For example, consider the following Python data structure representing a single OSM node:

    node = {
        'id': 1234,
        'lat': 51.5074,
        'lon': -0.1278,
        'tags': {
            'name': 'Big Ben',
            'amenity': 'clock'
        }
    }

To write this node to an OSM XML format output file using osmfile.py, you would first create a new osmfile.OsmWriter object, and then call the `write_node()` method, passing in the node dictionary as an argument:

    from osmfile import OsmFile

    writer = OsmFile('output.osm')
    writer.write_node(node)
    writer.write_way(way)
    writer.write_relation(relation)
    writer.add_tag('1234', 'amenity', 'post_office')
    writer.close()


This would write the following XML code to the output file:

    <node id="1234" lat="51.5074" lon="-0.1278">
    <tag k="name" v="Big Ben"/>
    <tag k="amenity" v="clock"/>
    </node>

osmfile.py also provides methods for writing OSM ways and relations to output files, and for adding tags to existing OSM nodes, ways and relations.

To write an OSM way to an output file, you would create a dictionary representing the way, with a `nodes` key containing a list of the node IDs that make up the way. For example:

    way = {
        'id': 5678,
        'nodes': [1234, 5678, 9012],
        'tags': {
            'name': 'Oxford Street',
            'highway': 'primary'
        }
    }

    writer.write_way(way)


This would write the following XML code to the output file:

    <way id="5678">
        <nd ref="1234"/>
        <nd ref="5678"/>
        <nd ref="9012"/>
        <tag k="name" v="Oxford Street"/>
        <tag k="highway" v="primary"/>
    </way>

To write an OSM relation to an output file, you would create a dictionary representing the relation, with a `members` key containing a list of dictionaries representing the members of the relation. Each member dictionary should have `type`, `ref` and `role` keys, specifying the type of OSM object (node, way or relation), the ID of the object, and the role of the object in the relation. For example:

    relation = {
        'id': 7890,
        'members': [
            {'type': 'way', 'ref': 5678, 'role': 'outer'},
            {'type': 'node', 'ref': 1234, 'role': 'admin_centre'}
        ],
        'tags': {
            'name': 'London Borough of Westminster',
            'type': 'boundary'
        }
    }

    writer.write_relation(relation)


This would write the following XML code to the output file:

    <relation id="7890">
        <member type="way" ref="5678" role="outer"/>
        <member type="node" ref="1234" role="admin_centre"/>
        <tag k="name" v="London Borough of Westminster"/>
        <tag k="type" v="boundary"/>
    </relation>

In addition to writing new OSM objects to an output file, osmfile.py also provides methods for adding tags to existing objects. To add a tag to an OSM object, you would call the `add_tag()` method, passing in the object's ID, the tag key and the tag value:

    writer.add_tag('1234', 'amenity', 'post_office')

This would add the following XML code to the output file, as a child of the existing `node` element with ID `1234`:

    <tag k="amenity" v="post_office"/>

Note that the `OsmWriter` class also provides methods for closing the output file and flushing any buffered data to disk. You should call the `close()` method once you have finished writing all of your OSM data to the output file.

## yamlfile.py

This reads in the yaml config file with all the conversion
information into a data structure that can be used when processing the
data conversion.
