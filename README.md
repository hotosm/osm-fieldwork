# odkconvert

ODKConvert is a python3 script to convert data collecting using XForms
to generate proper OpenStreetMap tagging. This program parses the
XForm to get the correct data types of all the selections, and uses a
YAML data file to guide the conversion of tags. Note that each XForm
would potentially needs it's own YAML file.

The output is an OSM XML formatted file for JOSM. No converted data
should ever be uploaded to OSM without validating the conversion in
JOSM.
