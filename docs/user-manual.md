# Osm-Fieldwork User Manual

The osm-fieldwork project is a collection of utilities useful for
field data collection, focused on OpenStreetMap (OSM) and OpenDataKit
(ODK). Both of these are used heavily for humanitarian and emergency
response by many organizations. The problem is these two projects were
never designed to work together, so this project was born to fill the
gaps. Included are a few other useful utilities for field
mapping.

This project is also currently part of the backend for the
[FMTM project](https://github.com/hotosm/fmtm/wiki), but all of the
data processing can also be run standalone, and also works fully
offline. All the standalone programs run in a terminal, and are
written in Python.

## OpenDataKit (ODK)

[OpenDataKit](https://opendatakit.org/software/) is a format for
collecting data on mobile devices, including the spatial coordinates
of that data item. The primary source file is a spreadsheet called an
XLSForm, which gets converted to an XForm using the
[xls2xform](https://pypi.org/project/pyxform/) program. An XForm is is
in XML format. All collected data is stored as an instance file, also
in XML format on the mobile device, but of course is a different
schema than the XForm. Once the data is collected it gets uploaded to
an ODK Central server. From there you can download the collected data,
called submissions, in CSV or JSON format. The JSON format works
better. Here's where the conversion project starts, how to process the
downloaded data into something we can upload to OpenStreetMap
efficiently.

All of the XLSForms included in this project have all been carefully
edited to enable a good clean conversion to OSM XML. More information
on how to modify the conversion [is here](convert). If you base any
custom XLSForms from this library, you can also update the conversion
criteria. These XLSForms can also be downloaded from FMTM.

## Field Mapping Tasking Manager (FMTM)

The [FMTM](https://github.com/hotosm/fmtm/wiki) is a project to
coordinate field data collection in a similar way as the HOT Tasking
Manager. But other than the ability to break up a big area into tasks,
the rest works very differently. Often mangaing a group doing field
mapping is a bit like herding cats. Plus the mappers often aren't sure
where they should be mapping, or when they are finished. In addition,
it is now possible to load a data extract from OSM into [ODK
Collect](https://docs.getodk.org/collect-intro), and use that data to
set the default values when collecting the data so the mapper doesn't
have to do it. FMTM handles the creation of the data extract, as well
as processing the data into a format suitable to edit with JOSM or
QGIS. The FMTM backend is a FastAPI wrapped around this project.

## Processing Submissions

This section will focus on converting the JSON format, but the process
for converting the CSV submissions is the same. The JSON format seems to
be more complete for some XLSForms, so it's preferred. The first step
is converting it to OSM XML format, so it can be loaded into
[JOSM](https://josm.openstreetmap.de/) and edited. A YAML based config
file is used to convert the JSON format you just downloaded into the
OSM XML format.

The initial problem is neither the CSV or the JSON format stores the
coordinates in a way any editing program wants them. So that's the
most important part of the conversion process, generating a data file
with spatial coordinates in the right syntax. The conversion process
generates two output files, one in OSM XML format, the other in
GeoJson format. The OSM XML one has had the data filtered, not
everything collected is for OSM. But all the data goes in the GeoJson
file, so nothing is lost. Since the GeoJson format does not have to
follow OSM syntax, not all the tags and values may be similar to what
OSM expects, but that's not a problem for our use case.

The [config file](convert) for conversion has 3 sections, one for all the
conversion data, one for data to ignore completely, and a private
section for the GeoJson file. The stuff to ignore is extraneous fields
added by ODK Collect, like deviceID. Modifying the conversion is
straight forward as it's mostly just replacing one set of strings with
another.

For any of the XLSForms in this project's library, the configuration
is already done, but any custom XLSForms will need to modify it to get
a good conversion, or fix it in JOSM later. For a one-off project,
like an import, I usually get lazy and fix it in JOSM. But for
anything used several times, that gets old, so it's better to improve
the config file. 

To convert the JSON format file downloaded for ODK Central, run this
program:

 	json2osm.py -i Submissions.json
 	json2osm.py -i Submissions.json -y custom.yaml

or for the CSVfile:

	CSVDump.py -i Submissions.csv
	CSVDump.py -i Submissions.csv -u custom.yaml

which produces a Submissions.osm and Submissions.geojson files from
that data. The OSM XML file may have tags that got missed by the
conversion process, but the advantage is now all the data can be
viewed and edited by JOSM. If you want a clean conversion, edit the
config file and use that as an alternate for converting the data.

	json2osm -i Submissions.json -x custom.yaml

## Data Conflation

Now you have a file that can be viewed or edited, but it's all
collected, but some of the features may already exist in OSM. This can
be done manually in JOSM, which is ok for small datasets, but it's
easier to apply a little automated help. It's possible to find similar
features in OSM that are near the data we just collected for a
building, but has the same business name. How to conflate the
collected data with existing OSM data is [another
document](conflation).

To just use the [conflation software](odk_merge) requires setting
up a postgres database containing the OSM data for the county, region,
state, country, ect... You can also use the data extract from FMTM, as it
covers the same area the data was collected in. FMTM allow you to
download the data extract used for this task. Postgres works
much faster, but the GeoJson data extract works too as the files per
task are relativly small..
	
	odk_merge.py Submissions.osm PG:"nepal" -b kathmanu.geojson
	or
	odk_merge.py Submissions.osm kathmandu.geojson

In this example, the OSM XML file from the conversion process uses a local
postgres data with the country of Nepal loaded into it. You can also
specify an alternate boundary so the conflation will use a subset of
the entire database to limit the amount of data that has to be
queried. 

Each feature in the submission is queried to find any other features
with 2 meters where any tags match. Both POIs and buildings are
checked for a possible match. Often the building has "building=yes"
from remote mapping, so we'd also want to merge the tags from the
collected data into the building way. Multiple shops within the same
building remain as a POI in that building.

# Making imagery Basemaps

# Making data extracts

