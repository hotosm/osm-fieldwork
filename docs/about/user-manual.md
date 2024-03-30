# Osm-Fieldwork User Manual

The osm-fieldwork project is a collection of utilities useful for
field data collection, focused on OpenStreetMap (OSM) and ODK.
Both of these are used heavily for humanitarian and emergency
response by many organizations. The problem is these two projects were
never designed to work together, so this project was born to fill the
gaps. Included are a few other useful utilities for field
mapping.

This project is also currently part of the backend for the
[FMTM project](https://github.com/hotosm/fmtm/wiki), but all of the
data processing can also be run standalone, and also works fully
offline. All the standalone programs run in a terminal, and are
written in Python.

## ODK

[ODK](https://getodk.org) is a format for
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
on how to modify the conversion
[is here](https://hotosm.github.io/osm-fieldwork/api/convert).
If you base any
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

## Getting Started

This project is available from PyPi.org, and can be installed like
this:

    pip install osm-fieldwork

It contains multiple programs, each one that handles a specific part
of the conversion process. Each program is a single class so it can be
used as part of a FastAPI backend, but also runs standalone for
debugging, and working offline. These are all terminal based, as the
website frontend is the actual GUI.

- json2osm
  - Convert JSON from Central to OSM XML
- csv2osm
  - Convert CSV from Central to OSM XML
- odk2csv
  - Convert the ODK Instance to CSV
- odk2geojson
  - Convert the ODK Instance to GeoJson
- odk_merge
  - Conflate POIs from Collect with existing OSM data
- odk_client
  - Remotely control an ODK Central server

You can also to run the terminal based programs from the source
tree, which can be gotten from here:

    git clone git@github.com:hotosm/osm-fieldwork.git

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

The [config file](https://hotosm.github.io/osm-fieldwork/about/configuring/)
for conversion has 3 sections, one for all the
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
collected data with existing OSM data is
[another document](https://hotosm.github.io/osm-fieldwork/about/conflation/).

To just use the [conflation software](https://hotosm.github.io/osm-fieldwork/about/odk_merge/)
requires setting up a postgres database
containing the OSM data for the county, region,
state, country, ect... You can also use the data extract from FMTM, as it
covers the same area the data was collected in. FMTM allow you to
download the data extract used for this task. Postgres works
much faster, but the GeoJson data extract works too as the files per
task are relativly small.

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

There is much more detail on this program [here](https://hotosm.github.io/osm-fieldwork/about/odk_merge/).

# Utility Programs

## Making basemaps

Basemaps are very useful when using ODK Collect in areas where the map
data is poor. Imagery is particular is very useful, as you can use
that to select a location other than where you are standing. This
project has a utility that makes basemaps from several sources. It
builds a local tile store, so larger areas can be downloaded and in
the field when offline, smaller basemaps can be made from the tile
store. Since downloading map tiles is very time consuming, I usually
download larger areas and let it download for a few days.

    basemapper -s esri -b Pokara.geojson -z 8-15 -o pokara.mbtiles

This command will download all the map tiles from
[ESRI](https://www.esri.com) into an XYZ tile store for zoom levels 8
to 15. Since downloading imagery is slow, I often download larger
areas, and then use a subset of the tiles to make smaller
basemaps. The mbtiles file can be manually loaded into [ODK
Collect](https://docs.getodk.org/collect-intro) as a layer, and used
to adjust the location of the POI when mapping.

Since it often useful for navigation, basemapper can also produce a
basemap from the same map tiles for
[Osmand](https://osmand.net/). This is very useful when in areas with
little map data, for example during a remote backcountry trip. This
example downloads Bing imagery for Pokara, Nepal.

basemapper -s bing -b Pokara.geojson -z 8-19 -o pokara.sqlitedb

There is much more detail on this program [here](https://hotosm.github.io/osm-fieldwork/api/basemapper/).

## Converting for an Instance File

### odk2osm.py, odk2geojson.py, odk2csv.py

These programs read the XML format used by ODK Collect for Instance
files. Since each submission has a separate Instance file, this takes
a regular expression, and produces a single output file. This is only
used when working offline, so it's possible to edit the recently
collected data and update the map data. Very useful when working
offline during big disasters.

    odk2osm -i Highways Paths_2023-07-17\*

On your phone, you can find the instance files here:

/sdcard/Android/data/org.odk.collect.android/files/projects/[UUID]/instances

You can also manually update your data extracts by copying them to /sdcard/Android/data/org.odk.collect.android/files/projects/[UUID]/forms/[Form name]-media/

And manually update the XForm by copying them to
/sdcard/Android/data/org.odk.collect.android/files/projects/[UUID]/forms/

### Managing ODK Central

[ODK Central](<https://docs.getodk.org/central-intro/> is the server
side of ODK Collect. It's where XForms are downloaded from, and where
submissions go after being sent by Collect. As there are a lot of
options, this program is not very user friendly as it's primarily used
as part of the backend for the FMTM project, and most people would
just use the Central website.

However, this can be useful for scripting the server. For example to
list all the projects on a remote Central server:

    odk_client -s projects

And this lets you download all the submissions to project number 19
and using the XLSForm for buildings.

odk_client -v -i 19 -f buildings -x json

There is much more detail on this program [here](https://hotosm.github.io/osm-fieldwork/about/odk_client/).
