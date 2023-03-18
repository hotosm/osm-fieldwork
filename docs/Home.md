# ODK Convert Project

ODKConvert is a project for processing data collection using
OpenDataKit into OpenStreetMap format. It includes several utility
programs that automate part of the data flow like creating satellite
imagery basemaps and data extracts from
[OpenStreetMap](https://www.openstreetmap.org) so they can be
used with [ODK Collect](https://www.getodk.org). Many of these steps
are currently a manual process.

## odkconvert

This program converts the data collected from ODK Collect into
the proper OpenStreetMap tagging schema. The conversion is controled
by an YAML file, so easy to modify for other projects. The output is
an OSM XML formatted file for JOSM. No converted data should ever be
uploaded to OSM without validating the conversion in JOSM. To do high
quality conversion from ODK to OSM, it's best to use the XLSForm
library as templates, as everything is designed to work together.

## Installation

To install odkconvert, you can use pip. Here are two options:


- Directly from the main branch:
  `pip install git+https://github.com/hotosm/odkconvert.git`

- Latest on PyPi:
  `pip install ODKConvert`

### Configure

ODKConvert can be configured via environment variable:

**LOG_LEVEL**
> If present, will change the log level. Defaults to DEBUG.

**ODK_CENTRAL_URL**
> The URL for an ODKCentral server to connect to.

**ODK_CENTRAL_USER**
> The user for ODKCentral.

**ODK_CENTRAL_PASSWD**
> The password for ODKCentral.

**ODK_CENTRAL_SECURE**
> If set to False, will allow insecure connections to the ODKCentral API. Else defaults to True.

## Usage
### Here's how to use odkconvert:

- First, make sure that your input data is in the correct format. ODK Collect data should be exported as an XLSForm or CSV file.

- Next, create a YAML file that specifies the conversion settings. The YAML file should specify the input file location, the output file location, and any additional conversion settings. Here's an example YAML file:

  `input_file: /path/to/input.csv`

  `output_file: /path/to/output.osm`

  `use_gps_trace: true`

- Once you have your input data and YAML file, you can run odkconvert using the following command:

  `odkconvert convert /path/to/yaml/file.yaml`

- This will generate an OSM XML file that you can open in JOSM to validate the conversion.

### Utility Programs

In addition to odkconvert, the ODKConvert project includes several utility programs that automate parts of the data flow. Here are descriptions of each program:

- `osm-extract`: This program extracts OpenStreetMap data for a specified area and saves it as an OSM XML file. Here's an example command:

  `osm-extract -b "bbox coordinates" -o /path/to/output.osm`

- `osm-to-geojson`: This program converts an OSM XML file to a GeoJSON file. Here's an example command:

  `osm-to-geojson /path/to/input.osm /path/to/output.geojson`

- `osm-basemap`: This program creates a satellite imagery basemap for a specified area. Here's an example command:

  `osm-basemap -b "bbox coordinates" -z zoom_level -o /path/to/output.tif`

### Best Practices

To ensure the quality of your converted data, here are some best practices to follow:

- Always validate your conversion in JOSM before uploading to OpenStreetMap.

- Use the XLSForm library as templates to ensure that your ODK Collect data is compatible with the conversion process.

- If you're having trouble with the conversion process, try using the utility programs included with ODKConvert to troubleshoot common issues.

By following these best practices and using the utility programs included with ODKConvert, you can effectively process data collection from OpenDataKit into OpenStreetMap format. However, please note that while ODKConvert has been tested and used in various projects, it is still in active development and may have limitations or issues that need to be resolved.

### Examples

Here are some examples of how you can use odkconvert in your projects:

- Convert an XLSForm file to OSM XML:

  `odkconvert convert --xlsform /path/to/xlsform.xlsx --yaml /path/to/output.yaml`

- Convert a CSV file to OSM XML:

  `odkconvert convert --csv /path/to/csvfile.csv --yaml /path/to/output.yaml`

- Convert a form with GPS traces to OSM XML:

  `odkconvert convert --csv /path/to/csvfile.csv --gps /path/to/gpstraces.gpx --yaml /path/to/output.yaml`

- Extract OpenStreetMap data for a specified area:

  `osm-extract -b "bbox coordinates" -o /path/to/output.osm`

### Conclusion
ODKConvert is a powerful tool for processing data collection from OpenDataKit into OpenStreetMap format. By following the best practices outlined in this documentation and using the utility programs included with ODKConvert, you can streamline your data collection process and ensure the quality of your converted data. If you have any questions or issues with ODKConvert, please consult the project's documentation or seek support from the project's community.

## XLSForm library

In the XForms directory is a collection of XLSForms that support the
new HOT data models for humanitarian data collection. These cover
many categories like healthcare, waterpoints, waste distribution,
etc... All of these XLSForms are designed to have an efficient mapper
data flow, edit existing OSM data, and support the data models.

The data models specify the preferred tag values for each data item,
with a goal of both tag completeness and tag correctness. Each data item
is broken down into a basic and extended survey questions when
appropriate.

### What is an XLSForm?
An XLSForm is a spreadsheet-based form design tool that allows you to create complex forms for data collection using a simple and intuitive user interface. With XLSForms, you can easily design and test forms on your computer, then deploy them to mobile devices for data collection using ODK Collect or other data collection tools. XLSForms use a simple and structured format, making it easy for you to share and collaborate on form designs with your team or other organizations.

### Using the XLSForm Library with ODKConvert
The XLSForms in the XForms directory of the XLSForm Library have been designed to support the HOT data models and have an efficient mapper data flow. These forms also allow for editing of existing OSM data and support the data models, specifying the preferred tag values for each data item with the goal of both tag completeness and tag correctness.

### Here are some examples of how to use the XLSForm Library with ODKConvert:

- Download an XLSForm from the XForms directory:

  `wget https://github.com/hotosm/xlsform/raw/master/XForms/health_facility_survey_v2.xlsx`

- Convert the XLSForm to OSM XML using odkconvert:

  `odkconvert convert --xlsform /path/to/xlsform.xlsx --yaml /path/to/output.yaml`

- Use the resulting OSM XML file with JOSM or other OSM editors to validate and edit the data before uploading it to OpenStreetMap.

### Conclusion
The XLSForm Library is a valuable resource for organizations involved in humanitarian data collection, as it provides a collection of pre-designed forms that are optimized for efficient mapper data flow and tag completeness/correctness. By using the XLSForm Library with ODKConvert, you can streamline your data collection process and ensure the quality of your data.

## basemapper.py

This is a program that makes mbtiles basemaps for ODK convert.

basemapper.py is a Python script that is included with the ODKConvert package. It is a program that automates the process of creating satellite imagery basemaps for use with ODKConvert. These basemaps can be used to assist data collection in areas with limited internet connectivity, where satellite imagery is the only available source of map data. More
information on this program [is here](docs/programs.md).

### How basemapper.py Works
basemapper.py uses the Mapbox GL JS library to create a web map that includes satellite imagery tiles and overlays from OpenStreetMap. It then uses the Mapbox GL JS API to capture the map viewport and save it as a series of mbtiles files. The resulting mbtiles files can be used as a basemap with ODKConvert, allowing for offline data collection in areas with limited internet connectivity.

### Using basemapper.py
Here are the basic steps to use basemapper.py:

- Install ODKConvert if you haven't already:

  `pip install git+https://github.com/hotosm/odkconvert.git`

- Navigate to the ODKConvert package directory:

  `cd /path/to/odkconvert`

- Run basemapper.py with the following arguments:

  `python basemapper.py --lat=<latitude> --lon=<longitude> --zoom=<zoom_level> --output=<output_directory>`

  `--lat` is the latitude of the center point of the map

  `--lon` is the longitude of the center point of the map

  `--zoom` is the zoom level of the map (between 0 and 22)

  `--output` is the output directory for the mbtiles files

For example, to create a basemap of the area around the city of Kathmandu in Nepal with a zoom level of 16 and save the output files to the directory `/path/to/basemaps`, you would run:

  `python basemapper.py --lat=27.7172 --lon=85.3240 --zoom=16 --output=/path/to/basemaps`

  - Use the resulting mbtiles files with ODKConvert to create a basemap for offline data collection.

### Conclusion
basemapper.py is a useful tool for creating satellite imagery basemaps for use with ODKConvert. By automating the process of creating mbtiles files, it saves time and effort for data collection teams working in areas with limited internet connectivity. With basemapper.py and ODKConvert, organizations can collect data more efficiently and accurately, even in challenging environments.


## make_data_extract.py

This is a program that makes data extracts from OpenStreetMap for ODK
convert.
make_data_extract.py is a Python script that is included with the ODKConvert package. It is a program that automates the process of creating data extracts from OpenStreetMap for use with ODKConvert. These extracts can be used to assist data collection in areas where offline maps are needed.
More information on this program [is here](docs/programs.md).

### How make_data_extract.py Works
make_data_extract.py uses the Overpass API to extract data from OpenStreetMap based on specified criteria. The extracted data is saved as a GeoJSON file, which can be used as a data source with ODKConvert.

### Using make_data_extract.py
Here are the basic steps to use make_data_extract.py:

- Install ODKConvert if you haven't already:

  `pip install git+https://github.com/hotosm/odkconvert.git`

- Navigate to the ODKConvert package directory:

  `cd /path/to/odkconvert`

- Run make_data_extract.py with the following arguments:

  `python make_data_extract.py --bbox=<bounding_box> --tags=<tag_filters> --output=<output_directory>`

  `--bbox` is the bounding box of the area to extract data from (in the format `min_lon,min_lat,max_lon,max_lat`)

  `--tags` is a comma-separated list of tag filters to apply to the data extract (for example: `amenity=school,building=yes`)

  `--output` is the output directory for the GeoJSON file

For example, to extract data for schools in the Kathmandu Valley in Nepal and save the output file to the directory `/path/to/data`, you would run:

  `python make_data_extract.py --bbox=85.205,27.596,85.798,28.023 --tags=amenity=school --output=/path/to/data`

- Use the resulting GeoJSON file with ODKConvert to create a data source for offline data collection.

### Conclusion
make_data_extract.py is a useful tool for creating data extracts from OpenStreetMap for use with ODKConvert. By automating the process of extracting data based on specified criteria, it saves time and effort for data collection teams working in areas where offline maps are needed. With make_data_extract.py and ODKConvert, organizations can collect data more efficiently and accurately, even in challenging environments.
