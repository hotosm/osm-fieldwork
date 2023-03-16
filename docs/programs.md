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
