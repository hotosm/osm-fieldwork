<!-- ![](images/hot_logo.png) -->

## OSM-Fieldwork Project

Osm_Fieldwork is a project that aims to simplify the process of processing data collected using ODK into OpenStreetMap format. It consists of several utility programs that automate different parts of the data flow. These include creating satellite imagery basemaps and data extracts from OpenStreetMap so they can be used with ODK Collect. It is maintained by the [Humanitarian OpenStreetMap Team (HOT)](https://www.hotosm.org/) and designed to work with [ODK Collect](https://docs.getodk.org/collect-intro/), an Android app for data collection, and [ODK Central](https://docs.getodk.org/central-intro/), a web-based platform for managing and visualizing data.

## osm_fieldwork

This program converts the data collected from ODK Collect into the proper OpenStreetMap tagging schema. The conversion is controlled by a YAML file, which makes it easy to modify for other projects. The output is an OSM XML formatted file for JOSM. However, it is important to note that no converted data should ever be uploaded to OSM without first validating the conversion in JOSM. To do high-quality conversion from ODK to OSM, it's best to use the XLSForm library as template, as everything is designed to work together.

Osm_Fieldwork includes the following utilities:

- `make_data_extract.py`: extracts OpenStreetMap data within a given boundary and category (e.g., buildings, amenities) using Overpass Turbo or a Postgres database.
- `CSVDump.py`: converts a CSV file downloaded from ODK Central to OSM XML format.
- `odk2csv.py`: converts an ODK XML instance file to the same CSV format used by ODK Central.
- `ODKDump.py`: extracts data from an ODK Collect instance XML file and converts it to OSM XML format.
- `ODKForm.py`: parses an ODK XML form file and extracts its fields and data types.
- `ODKInstance.py`: parses an ODK Collect instance XML file and extracts its fields and data values.

Osm_Fieldwork also includes support modules, such as convert.py for processing YAML config files and osmfile.py for writing OSM XML output files.

## Installation

To install osm-fieldwork, you can use pip. Here are two options:

1. Directly from the main branch:
   `pip install git+https://github.com/hotosm/osm-fieldwork.git`

   -OR-

2. Latest on PyPi:
   `pip install Osm-Fieldwork`

> Note: installation requires GDAL >3.4 installed on your system.

## Usage

Each utility has its own command-line interface, with various options and arguments. You can find detailed instructions on how to use each utility by running it with the -h or --help option.
For example, to extract OSM data within a boundary polygon from Overpass Turbo, run:

`./make_data_extract.py --overpass --boundary mycounty.geojson`

This will create a GeoJSON file with the extracted data.

To convert a CSV file from ODK Central to OSM XML format, run:

`./CSVDump.py -i data.csv`

This will generate two output files - one OSM XML of public data, and the other a GeoJson file with all the data.

## Contributing

Osm_Fieldwork is an open-source project, and contributions are always welcome! If you want to contribute, please read the [Contribution Guidelines](https://github.com/hotosm/osm-fieldwork/wiki/Contribution) and [Code of Conduct](https://github.com/hotosm/osm-fieldwork/wiki/Code-of-Conduct) first.

## License

Osm_Fieldwork is released under the [AGPLv3](https://www.gnu.org/licenses/agpl-3.0.en.html).
