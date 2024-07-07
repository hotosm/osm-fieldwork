# odk2osm

This programs reads the various data formats used with
[OpenDataKit](https://en.wikipedia.org/wiki/ODK_%28software%29),
and converts them to an OSM XML file, and a GeoJson file. The two
formats loaded from [ODK
Central](https://docs.getodk.org/central-intro/) are a CSV file
downloaded from the submissions page, or a JSON file downloaded using
[ODATA](https://www.odata.org/)

In addition for working offline, this can also parse the ODK XML
format used for the instances files in [ODK
Collect](https://getodk.org/). When working in the field, I use
[adb](https://developer.android.com/tools/adb) to pull files off my
smartphone using a USB cable.

The options for this program are:

 Convert ODK XML instance file to OSM XML format

 options:
   -h, --help            show this help message and exit
   -v [VERBOSE], --verbose [VERBOSE]
       verbose output
   -y YAML, --yaml YAML  Alternate YAML file
   -x XLSFILE, --xlsfile XLSFILE
       Source XLSFile
   -i INFILE, --infile INFILE
       The input file
By default, the
[xforms.yaml](https://github.com/hotosm/osm-fieldwork/blob/main/osm_fieldwork/xforms.yaml)
file is used when converting to OSM XML format. Using the *--yaml*
option allows you to have a custom conversion of the data collected by
your [XLSForm](https://xlsform.org/en/). This only applies to the OSM
XML output, when processing the GeoJson file, no conversion is done.

The input file is the CSV or JSON file downloaded from ODK
Central. ODK Collect stores the instance files in a collection of
sub-directories that are timestamped and have a unique instance number
as part of the file name. The primary part of the filename is the same
as the title of the XLSForm.

For example:

 instances/Buildings_3_2024-05-28_18-34-38/Buildings_3_2024-05-28_18-34-38.xml
 instances/Buildings_2_2024-01-24_13-36-20/Buildings_2_2024-01-24_13-36-20.xml
 instances/Buildings_3_2024-05-31_11-08-22/Buildings_3_2024-05-31_11-08-22.xml
 instances/Buildings_2_2024-01-26_15-16-53/Buildings_2_2024-01-26_15-16-53.xml
 instances/Buildings_2_2024-01-26_15-07-17/Buildings_2_2024-01-26_15-07-17.xml
 instances/Buildings_3_2024-05-29_11-46-53/Buildings_3_2024-05-29_11-46-53.xml
 instances/Buildings_3_2024-06-03_11-14-02/Buildings_3_2024-06-03_11-14-02.xml
 instances/Buildings_3_2024-06-03_10-33-27/Buildings_3_2024-06-03_10-33-27.xml
 instances/Buildings_2_2024-01-26_11-42-38/Buildings_2_2024-01-26_11-42-38.xml
 instances/Buildings_3_2024-05-29_12-13-37/Buildings_3_2024-05-29_12-13-37.xml
 ...

In this case the parameter passed to *odk2osm* can contain a regular
expression to process multiple files, as each time you open Collect,
it creates a new directory and file. The output is a single file.
So in this case, run odk2osm like this:

 odk2osm -v -i Buildings_3\* -x Buildings.xls

The --xlsfile is used to specigy the XLSForm that was used for this
mapping session. This is used to supply the correct data type of each
entry collected.
