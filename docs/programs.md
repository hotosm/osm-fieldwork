# ODK Convert Utility Programs

ODK Convert contains few standalone utility programs for converting
data from ODK Collect and the ODK Central server, and a few support
modules.

## make_data_extract.py
The `make_data_extract.py` program is used to extract OpenStreetMap (OSM) data for use with the `select_one_from_file` function in ODK Collect. This function allows users to select from a list of options generated from an external file. The `make_data_extract.py` program creates a data extract that can be used as an external file with the `select_one_from_file` function. The data extract can be created using Overpass Turbo or a Postgres database.

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
### Overpass Turbo:
The `--overpass` option uses Overpass Turbo to extract OSM data. By default, the program extracts the `buildings` category of OSM data. The size of the extracted data can be limited using the `--boundary` option. The program outputs the data in GeoJSON format.

### Example:

    ./make_data_extract.py --overpass --boundary mycounty.geojson -g mycounty_buildings.geojson

This example uses Overpass Turbo to extract the `buildings` category of OSM data within the boundary specified in the `mycounty.geojson` file. The program outputs the data in GeoJSON format to a file named `mycounty_buildings.geojson`.

### Postgres Database:
The --postgres option uses a Postgres database to extract OSM data. By default, the program uses localhost as the database host. The name of the database can be specified using the --dbname option. The program extracts the buildings category of OSM data by default. The size of the extracted data can be limited using the --boundary option. The program outputs the data in GeoJSON format.

### Example:

    ./make_data_extract.py --postgres -dn colorado --boundary mycounty.geojson -g mycounty_buildings.geojson

This example extracts the `buildings` category of OSM data from a Postgres database named `colorado`. The program limits the size of the extracted data to the boundary specified in the `mycounty.geojson` file. The program outputs the data in GeoJSON format to a file named `mycounty_buildings.geojson`.

### Input File:

The `--infile` option can be used to specify an input file in OSM XML, OSM PBF, or GeoJSON format. The program extracts the `buildings` category of OSM data by default. The program outputs the data in GeoJSON format.

### Example:

    ./make_data_extract.py --infile mydata.osm.pbf -g mydata_buildings.geojson

This example extracts the `buildings` category of OSM data from an input file in OSM PBF format named `mydata.osm.pbf`. The program outputs the data in GeoJSON format to a file named `mydata_buildings.geojson`.

### Category:

The `--category` option can be used to specify which category of OSM data to extract. The program supports two categories: `buildings` and `amenities`.

### Example:

    ./make_data_extract.py --overpass --boundary mycounty.geojson --category amenities -g mycounty_amenities.geojson

This example uses Overpass Turbo to extract the `amenities` category of OSM data within the boundary specified in the `mycounty.geojson` file. The program outputs the data in GeoJSON format to a file named `mycounty_amenities.geojson`.

### Boundary:

The `--boundary` option can be used to specify a polygon boundary to limit the size of the extracted data. The boundary can be specified in GeoJSON format.

Example:

    ./make_data_extract.py --postgres -dn colorado --category buildings --boundary mycounty.geojson -g mycounty_buildings.geojson

This example extracts the `buildings` category of OSM data from a Postgres database named `colorado`. The program limits the size of the extracted data to the boundary specified in the `mycounty.geojson` file. The program outputs the data in GeoJSON format to a file named `mycounty_buildings.geojson`.

### Output File Format:

The program outputs the extracted OSM data in GeoJSON format. The name of the output file can be specified using the `--geojson option`. If the option is not specified, the program uses the input file name with `_buildings.geojson` appended to it.

    ./make_data_extract.py --overpass --boundary mycounty.geojson -g mycounty_buildings.geojson

This example uses Overpass Turbo to extract the `buildings` category of OSM data within the boundary specified in the `mycounty.geojson` file. The program outputs the data in GeoJSON format to a file named `mycounty_buildings.geojson`.

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

CSVDump.py is a Python script that converts a CSV file downloaded from ODK Central to OpenStreetMap (OSM) XML format. The tool can be useful for users who want to work with OpenStreetMap data and want to convert ODK Central data into a compatible format.



    options:
     -h, --help                   - show this help message and exit
     -v, --verbose                - verbose output
     -i CSVFILE, --infile CSVFILE - Specifies the path and filename of the input CSV file downloaded from ODK Central. This option is required for the program to run.

### Examples:

To convert a CSV file named "survey_data.csv" located in the current working directory, the following command can be used:

    python CSVDump.py -i survey_data.csv

To enable verbose output during the conversion process, the following command can be used:

    python CSVDump.py -i survey_data.csv -v

### Input Format:

CSVDump.py expects an input file in CSV format downloaded from ODK Central. The CSV file should have a header row with column names that correspond to the survey questions. Each row in the CSV file should contain a response to the survey questions, with each column representing a different question.

### Output Format:

The output of CSVDump.py is an OSM XML file that can be used with OpenStreetMap data tools and services. The converted OSM XML file will have tags for each survey question in the CSV file, as well as any metadata associated with the survey. The format of the OSM XML file generated by CSVDump.py is compatible with other OpenStreetMap data tools and services.

### Limitations:

- CSVDump.py only supports CSV files downloaded from ODK Central. Other CSV files may not be compatible with the tool.
- The tool only supports simple data types such as strings, numbers, and dates. Complex data types such as arrays and nested structures are not supported.

## odk2csv.py

odk2csv.py is a command-line tool that is part of the osm_fieldwork package. Its main purpose is to convert an Open Data Kit (ODK) XML instance file to CSV format, which can be easily imported into ODK Central for analysis.

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

Once you have the osm_fieldwork package installed, you can use odk2csv.py to convert an ODK XML instance file to CSV format. Here's an example command:

    odk2csv.py -i path/to/my_survey.xml

In this example, `my_survey.xml` is the ODK XML instance file that we want to convert to CSV format. After running the command, odk2csv.py will create a new CSV file in the same directory as the XML instance file. The CSV file will have the same name as the XML instance file but with a .csv file extension.

For instance, if the XML instance file is named "my_survey.xml", the output CSV file will be named "my_survey.csv".

If you want to see more detailed information during the conversion process, you can use the `-v` or `--verbose` option. Here's an example command that enables verbose output:

    odk2csv.py -i path/to/my_survey.xml -v

In this example, odk2csv.py will display more detailed information about the conversion process, such as the number of rows and columns in the CSV file.

## ODKDump.py

ODKDump.py is a Python script that is part of the OSM-Fieldwork toolset for converting Open Data Kit (ODK) data into various formats. It is used to dump the contents of an ODK Collect instance file into a readable format. This script takes several command line options that modify its behavior:

    options:
     -h, --help              - show this help message and exit
     -v, --verbose           - verbose output
     -i, --instance INSTANCE - The instance file from ODK Collect
     -x, --xform XFORM       - Load an alternal conversion file
     -o, --outdir            - The directory for the output file

-h or --help: This option displays the help message and exits. To use this option, run the following command:

    python ODKDump.py -h

-v or --verbose: This option enables verbose output, which displays more detailed information about the conversion process. To use this option, run the following command:

    python ODKDump.py -v -i path/to/instance.xml

-i or --instance: This option specifies the instance file created in ODK Collect that should be converted. The path to the instance file should be provided as the argument for this option. To use this option, run the following command:

    python ODKDump.py -i path/to/instance.xml

-x or --xform: This option allows users to load an alternate conversion file. By default, ODKDump.py uses a conversion file named odk_common.xsl. However, users can specify an alternate conversion file using this option. The path to the alternate conversion file should be provided as the argument for this option. To use this option, run the following command:

    python ODKDump.py -x path/to/alternate_conversion_file.xsl -i path/to/instance.xml

-o or --outdir: This option specifies the output directory for the converted file. By default, the converted file is saved in the same directory as the instance file. However, users can specify an output directory using this option. The path to the output directory should be provided as the argument for this option. To use this option, run the following command:

    python ODKDump.py -o path/to/output/directory -i path/to/instance.xml

Note that the -i or --instance option is required for all commands, as it specifies the instance file that should be converted. Additionally, the -x or --xform option is optional and should only be used if an alternate conversion file is desired.

## ODKForm.py

ODKForm.py parses the ODK XML XForm, and creates a data structure so
any code using this class can access the data types of each input
field. It can be run standalone from the command line, but this is
only for debugging purposes.

    options:
     -h, --help                           - show this help message and exit
     -v, --verbose,                       - verbose output
     -i, --infile XFORM, --instance XFORM - The definition file from ODK Collect

Usage:

    odkform.py [-h] [-v] [-i XFORM | -d DIR]

### Examples:

- Parsing a single XForm file:

        $ odkform.py -i myform.xml

This will parse the file myform.xml and create a Python data structure representing the form.

- Parsing all XForm files in a directory:

        $ odkform.py -d forms/

This will parse all XForm files in the `forms/` directory and create Python data structures for each form.

The data structure created by ODKForm.py is a Python dictionary with the following keys:

- `title`: The title of the form.
- `id`: The ID of the form.
- `version`: The version of the form.
- `body`: A list of dictionaries representing the form's fields.

Each dictionary in the body list represents a field in the form and has the following keys:

- `type`: The type of the field (e.g., text, integer, select_one).
- `name`: The name of the field.
- `label`: The label of the field.
- `hint`: The hint of the field.
- `required`: A boolean value indicating whether the field is required.
- `choices`: A list of dictionaries representing the choices for select_one and select_multiple fields. Each dictionary has the following keys:
    - `name`: The name of the choice.
    - `label`: The label of the choice.

## ODKInstance.py

ODKInstance.py parses the ODK Collect instanceXML file, and creates a
data structure so any code using this class can access the collected
data values. It can be run standalone from the command line, but this is only for debugging purposes.

### Usage:
ODKInstance.py can be run from the command line or imported as a module in a Python program. When run from the command line, the following options are available:

    options:
     -h, --help                       - show this help message and exit
     -v, --verbose                    - verbose output
     -i INSTANCE, --instance INSTANCE - The instance file from ODK Collect

When importing ODKInstance.py as a module in a Python program, you can create an instance of the ODKInstance class and use its methods to access the data values in the instanceXML file.

### Example:
Here's an example of how to use ODKInstance.py in a Python program:

    from ODKInstance import ODKInstance

    # Create an instance of the ODKInstance class
    odk_instance = ODKInstance('/path/to/instance.xml')

    # Access a data value in the instanceXML file
    value = odk_instance.get_value('question_name')

In this example, we create an instance of the ODKInstance class and specify the path to the instanceXML file generated by ODK Collect. We can then use the get_value() method to access the value of a particular question in the form by passing the question's name as an argument.

Note that ODKInstance.py is primarily intended for use by developers who are working with ODK Collect and need to process the data collected by the app. End users who are using ODK Collect to fill out forms will not typically need to interact directly with ODKInstance.py.

## convert.py

The convert.py module is part of the osm_fieldwork package and provides functionality for converting ODK forms between different formats using a YAML configuration file.

### Usage:
To use convert.py, you'll need to create a YAML configuration file that specifies the input and output formats for the conversion process. Here's an example configuration file:

    input:
      type: xlsform
      path: path/to/form.xls

    output:
      type: odk
      path: path/to/converted/form

In this example, we're specifying that the input form is an XLSForm located at 'path/to/form.xls', and that the output format should be ODK, with the converted form saved to 'path/to/converted/form'.

Once you have a configuration file, you can use convert.py from the command line by running the following command:

    python convert.py path/to/config.yaml

This will start the conversion process using the specified configuration file. The converted form will be saved to the path specified in the configuration file.

### Supported Formats:
convert.py supports the following input and output formats:

- XLSForm: A format for creating ODK forms using a spreadsheet.
- ODK: The native format used by ODK Collect for storing forms and collected data.
- JSON: A lightweight data-interchange format.
- CSV: A common format for storing tabular data

Note that convert.py does not support all possible variations of these formats. For example, some advanced features of XLSForm may not be supported.

### Configuration File Options:

The following options are available in the configuration file:

- input:
    - type: The input format (e.g. xlsform, odk, json, csv).
    - path: The path to the input file.
- output:
    - type: The output format (e.g. odk, json, csv).
    - path: The path to save the converted output file.

### Example:
Here's an example of how to use convert.py to convert an XLSForm to ODK format:

    input:
      type: xlsform
      path: path/to/form.xls

    output:
      type: odk
      path: path/to/converted/form

And then run the following command:

    python convert.py path/to/config.yaml

In this example, we're specifying that the input form is an XLSForm located at 'path/to/form.xls', and that the output format should be ODK, with the converted form saved to 'path/to/converted/form'. Running the command will start the conversion process using the specified configuration file.

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
    node_xml = writer.createNode(node)
    way_xml = writer.createWay(way)
    relation_xml = writer.createRelation(relation)
    writer.add_tag('1234', 'amenity', 'post_office')
    writer.write(node_xml)
    writer.write(way_xml)
    writer.write(relation_xml)
    writer.close()


This would create XML code for the node, way, and relation using createNode(), createWay(), and createRelation() respectively. These methods return a string of XML code which is then written to the output file using writer.write(). The add_tag() method can be used to add additional tags to any of the elements being written to the file.

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

`yamlfile.py` is a module that reads in a YAML config file containing information about how to convert data between different formats. The config file contains a list of conversion rules, where each rule specifies the source format, the target format, and any additional information needed to perform the conversion. The module parses the YAML file and creates a Python object representing the conversion rules, which can be used by other code in the conversion process.

To use `yamlfile.py`, you first need to create a YAML config file containing the conversion rules. Here's an example of a simple YAML config file that converts CSV files to ODK Collect forms:

    - source: csv
    target: odk
    settings:
        form_id: my_form
        form_title: My Form
        form_version: 1.0
        csv_delimiter: ","

This rule specifies that CSV files should be converted to ODK Collect forms, with the specified settings. The `settings` dictionary contains additional information needed to perform the conversion, such as the form ID, form title, form version, and the delimiter used in the CSV file.

Once you have created the YAML config file, you can use `yamlfile.py` to read it into a Python object. Here's an example of how to use the `read_yaml_file()` function to read the YAML config file:

    import yamlfile

    config_file = 'my_config.yaml'
    conversion_rules = yamlfile.read_yaml_file(config_file)

This will read the `my_config.yaml` file and return a Python list containing the conversion rules.

You can then use the conversion rules to perform the actual data conversion. Here's an example of how to use the `get_conversion_rule()` function to get the conversion rule for a specific source and target format:

    import yamlfile

    config_file = 'my_config.yaml'
    conversion_rules = yamlfile.read_yaml_file(config_file)

    source_format = 'csv'
    target_format = 'odk'
    conversion_rule = yamlfile.get_conversion_rule(conversion_rules, source_format, target_format)

    # Perform the conversion using the conversion rule

This will search through the list of conversion rules for a rule that matches the specified source and target format, and return the matching rule. You can then use the conversion rule to perform the actual data conversion.

Note that `yamlfile.py` relies on the PyYAML library to parse the YAML file. If you don't have PyYAML installed, you will need to install it using a package manager like `pip` before you can use `yamlfile.py`.

To handle errors when reading the YAML config file, `yamlfile.py` raises a `YamlFileError` exception. This exception is raised if the YAML file is not found, if the YAML file is malformed, or if a required field is missing from the conversion rule. You can catch this exception and handle it appropriately in your code.

Here's an example of how to catch the `YamlFileError` exception:

    import yamlfile

    config_file = 'my_config.yaml'

    try:
        conversion_rules = yamlfile.read_yaml_file(config_file)
    except yamlfile.YamlFileError as e:
        print(f"Error reading YAML file: {str(e)}")

This will catch any YamlFileError exceptions raised by `read_yaml_file()` and print an error message.

In summary, `yamlfile.py` is a module that reads in a YAML config file containing conversion rules and creates a Python object representing the rules. This object can be used by other code in the data conversion process. To use `yamlfile.py`, you need to create a YAML config file containing conversion rules, and then use the `read_yaml_file()` function to read the file into a Python object. You can then use the object to get the conversion rule for a specific source and target format, and perform the actual data conversion.
