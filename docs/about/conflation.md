# Conflating With OpenStreetMap

Now that the data collected using [ODK
Collect](https://docs.getodk.org/collect-intro) has been converted to
OSM XML, it needs to be conflated against the existing
OpenStreetMap(OSM) data before  validation by a human being. Due to
the wonderful flexibility of the OpenStreetMap(OSM) data schema, this
can be difficult to fully automate. At best it can assist the human
mapper by identifying probable duplicates, and other conflation
issues. Rather than delete the possible duplicates, instead a tag is
added so the mapper can find them easily and decide.

Conflation algorythms are not very elegant, they are usually slow and
brute force. But they also save the mapper time doing this completely
manually.

This project's conflation software can use either a local postgres
database, or a GeoJson file produced by the
[make_data_extracts](make_data_extracts) program. This program is also
used by [FMTM](https://fmtm.hotosm.org), so you can use those as
well. Obviously using postgres locally is much faster, especially for
large areas.

## Setting Up Postgres

For raw OSM data, the existing country data is downloaded from [GeoFabrik](
https://download.geofabrik.de/index.html), and imported using a
modified schema for osm2pgsql.

	osm2pgsql --create -d nepal --extra-attributes --output=flex --style raw.lua nepal-latest-internal.osm.pbf

The *raw.lua* script is [available
here](https://github.com/hotosm/underpass/blob/master/raw/raw.lua). It's
part of the [Underpass
project](https://hotosm.github.io/underpass/index.html). It uses a
more compressed and efficient data schema designed for data analysis.
Once the data is imported, do this to improve query performance.

	cluster ways_poly using ways_poly_geom_idx;
	create index on ways_poly using gin(tags);

The existing OSM database schema stores some tags in columns, and
other tags in a hstore column. Much of this is historical. But this
also makes it very complicated to query the database, as you need to
know what is a column, and what is in the hstore column. The raw.lua
schema is much more compact, as everything is in a single column.

## Using Postgres

If you use the [odk_merge](odk_merge) program, you don't have to deal
with accessing the database directly, but here's how if you want to.

This would find all of the tags for a hotel:

	SELECT osm_id, tags FROM nodes WHERE tags->>'amenity'='hotel'

If you want to get more fancy, you can also use the geometry in the
query. From python we setup a few values for the query, and note the
*::geometry* suffix, which uses meters instead of units. Meters are
easier to work with than units of the planet's circumferance. 

self.tolerance = 2
wkt.wkt = "Point", "coordinates": [-107.911957, 40.037573]
value = 'Meeker Hotel'

query = f"SELECT osm_id,tags,version,ST_AsText(ST_Centroid(geom)) FROM ways_POLY WHERE ST_Distance(geom::geography, ST_GeogFromText(\'SRID=4326;{wkt.wkt}\')) < {self.tolerance} AND levenshtein(tags->>'name', {value}) <= 1"

This query finds any building polygon with 2 meters where the name
matches. The levenstein function does a fuzzy string match, since
minor differences in the name can still be a match. Minor typos in the
ODK collected data or OSM often have minor typos.

## Using a GeoJson File

Using a data file also works the same way, only you can't really query
the data file the same way. Instead the entire data file is loaded
into a data structure so it can be queried by looping through all the
data. While not very efficient, it works well.

## Conflating The Data

All data collected using Collect is a node, but we also want to check
both nodes and ways. Many amenities in OSM are only a node, since
adding data with a mobile app, POIs is all they support. Any data
added by [JOSM](https://josm.openstreetmap.de) or the
[iD](https://wiki.openstreetmap.org/wiki/ID) editors is often a
polygon. Many buildings have been added to OSM using the HOT [Tasking
Manager](https://tasks.hotosm.org), and were traced from satellite
imagery.

Buildings traced from imagery have only a single tag, which is
*building=yes*. When field mapping, we now know that building is a
resturant, a medical clinic, or a residence. Since OSM guidelines
prefer the tags fo on the building polygon, and not be a separate POI
within the building. If there are multiple businesses in the same
building polygon, then they stay as a POI in the building.

### Conflating With Postgres

Since the database has 2 tables, one for nodes and the other for
polygons, we have to query both. A possible duplicate is one that is
within the desired distance and has a match in one of the tags and
values. Names are fuzzy matched to handle minor spelling differences.

The **nodes** table is queried first. If no possible duplicates are
found, then the **ways** table is queried next. The query just looks
for any nearby POI that has a match between any of the tags. Currently
the distance is set to 2 meters. Often the GPS coordinates from
Collect are where you are standing, usualy in front of the building.
This distance threshold is configurable, but if it's too large, you
get many false positives. As all mobile mapping apps only add a POI
for an amenity, it's common it's in the nodes table.

If nothing is found in the nodes table, then we check the polygons the
same way, distance and a tag match. Often people working on a desktop
or laptop may add more tags to an existing feature, and properly have
all the tags be in the building way, and not a POI within the
building. If there are miltiple small businesses in the same building,
then each remains a POI within the building polygon.

If a possible duplicate is found, the tags from the collected data and
the tags from OSM are merged together. In the case of the name tag,
the existing name is converted to an **old_name** tags, and the
collected name value is used for the **name* tag.

### Conflating with a GeoJson File

Since GeoJson supports multiple geometry types, unlike postgres, there
is only one set of data to compare against. The same process as used
for postgres is used for the data file, the only difference being the
data file is loaded into a data structure, and then has to loop
through all the existing features. This is slower than using postgres,
but works the same. One advantage is this can use he data extract from
FMTM, and not require the mapper to have a postgres database.

## String Matching

There are more spelling mistakes, weird capitalization, embedded
quotes, etc... in the values for the name tag than I can count. This
makes matching on the name somewhat complicated even when using fuzzy
string matching. Typing in names on one's smartphone also can add
typos or do auto-correction. And of course those mistakes may also
already be in OSM, and the feature you collected may be the correct
one.

For a potential match, the old value is placed in a *old_name* tag, in
addition to the the *fixme* tag used to flag a possible
duplicate. This enables the validator to decide and fix any minor
differences in the value. This mostly only applies to the **name**
tag, as most other tags have a more formalized value.

When an amenity has changed names, for example when a restaurant gets
new owners, this won't likely be caught as a duplicate unless the
amenity tag values match.

## Validating The Results

Conflation does not generate perfect results. It's necessary to have a
validator go through the reults and decide. The output file from
conflation does not remove anything from the collected data. Instead it
adds custom tags on what it finds. This way the validator can search
for those tags when getting started, and delete the duplicate and
validate the tag merging.

The primary tag added is a **fixme** tag for possible duplicates. If
there is more than a difference in the string values used for the
*name* tag, the existing tag is renamed to be *old_name*. While
this is not an actual OSM tag, the *alt_name* tag is currrently used
to avoid conflicts. It's up to the validator to decide what the
apppropriate value is.

I often notice when collecting data in the field on my smartphone,
typos are common. Missing capitalization on names or sometimes the
wrong character is common.

Here's a simple chart of the conversion [Data Flow](conflation.svg).
