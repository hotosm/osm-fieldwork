# OSM Fieldwork Programs

OSM Fieldwork contains a few standalone utility programs for converting
data from ODK Collect and the ODK Central server, and a few support
modules. You can install from the source tree using:
pip install .

or you can install the package from PyPi.org:

    pip install osm-fieldwork

## make_data_extract.py

The `make_data_extract.py` program is used to extract OpenStreetMap
(OSM) data for use with the `select_one_from_file` function in ODK
Collect. This function allows users to select from a list of options
generated from an external file. The `make_data_extract.py` program
creates a data extract that can be used as an external file with the
`select_one_from_file` function. There is more detailed information on
the program for making data extracts [here](make_data_extract.md).

## CSVDump.py

CSVDump.py is program converts a CSV file downloaded from
ODK Central to OpenStreetMap (OSM) XML format. The tool can be useful
for users who want to work with OpenStreetMap data and want to convert
ODK Central data into a compatible format. There is more detailed information on
the program for converting ODK to OSM [here](CSVDump.md)

## odk_merge.py

odk_merge.py is a program for conflating the OSM XML file produced
from CSVDump.py into with the data extract. This merges tags that have
been added or change by ODK Collect with exiting OSM data, The result
can be loaded into JOSM and after validation, uploaded to OSM.

# OSM Fieldwork Modules

## sqlite.py

This module creates mbtiles or sqlitedb files for basemaps. It's just
a wrapper around the existing sqlite3 module to create the output
files.

## osmfile.py

Osmfile.py is a module that writes OSM XML files for JOSM. It assumes
the data has already been converted using CSVDump. This module is only
used from within CSVDump.py. OSM XML format is needed as it's the only
format that supports conflation with upstream OSM data. More on
writing OSM XML [is here](osmfile.md).

## filter_data.py

filter_data.py is a program for filtering data extracts. Since an
extract can only include tags and values in the XLSform, thuis scans
the XLSForm, and is used to remove anything not included in the choices
sheet. While usually used as a module, if run standalone it can also
compare an XLSForm with the taginfo database to help modify the data
models.

## convert.py

The convert.py module is part of the osm_fieldwork package and
provides functionality for converting ODK forms between different
formats using a YAML configuration file. More detailed information on
this module [is here](convert.md)

## yamlfile.py

This reads in the yaml config file with all the conversion
information into a data structure that can be used when processing the
data conversion. More detail on this module [is here](yamlfile.md).

## odk2csv.py

Odk2csv.py is a command-line tool that is part of the osm-fieldwork
package. Its main purpose is to convert an ODK XML
instance file to CSV format, which can be easily imported into ODK
Central for analysis. This is primarily only used when working
offline, as it removes the need to access ODK Central.

    options:
     -h, --help                       - show this help message and exit
     -v, --verbose                    - verbose output
     -i INSTANCE, --instance INSTANCE - The instance file from ODK Collect

# Works In Progress

## ODKDump.py

ODKDump.py is a Python module that is part of the OSM-Fieldwork
toolset for converting ODK data into various
formats. It is used to parse the contents of an ODK Collect Instance
file into a readable format. This module currently is not finished,
instead use the **CSVDump.py** utility instead.

## ODKForm.py

ODKForm.py parses the XLSXForm, and creates a data structure so
any code using this class can access the data types of each input
field. This module currently is not finished. It turns out know the
input data types is not probably neccesary if we stick to processing
the CSV files.

## ODKInstance.py

ODKInstance.py parses the ODK Collect instanceXML file, and creates a
data structure so any code using this class can access the collected
data values. This module currently is not finished, instead use the
**odk2csv.py** utility instead.
