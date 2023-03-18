# ODK Convert Utility Programs

ODK Convert contains a few standalone utility programs for converting
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

odk2csv.py is a command-line tool that is part of the odkconvert package. Its main purpose is to convert an Open Data Kit (ODK) XML instance file to CSV format, which can be easily imported into ODK Central for analysis.

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

Once you have the odkconvert package installed, you can use odk2csv.py to convert an ODK XML instance file to CSV format. Here's an example command:

    odk2csv.py -i path/to/my_survey.xml

In this example, `my_survey.xml` is the ODK XML instance file that we want to convert to CSV format. After running the command, odk2csv.py will create a new CSV file in the same directory as the XML instance file. The CSV file will have the same name as the XML instance file but with a .csv file extension.

For instance, if the XML instance file is named "my_survey.xml", the output CSV file will be named "my_survey.csv".

If you want to see more detailed information during the conversion process, you can use the `-v` or `--verbose` option. Here's an example command that enables verbose output:

    odk2csv.py -i path/to/my_survey.xml -v

In this example, odk2csv.py will display more detailed information about the conversion process, such as the number of rows and columns in the CSV file.

## ODKDump.py

ODKDump.py is a Python script that is part of the ODKConvert toolset for converting Open Data Kit (ODK) data into various formats. It is used to dump the contents of an ODK Collect instance file into a readable format. This script takes several command line options that modify its behavior:

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

The convert.py module is part of the odkconvert package and provides functionality for converting ODK forms between different formats using a YAML configuration file.

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

## yamlfile.py

This reads in the yaml config file with all the conversion
information into a data structure that can be used when processing the
data conversion.
