# Basemapper.py

Basemapper is a program that creates basemaps for mobile apps in the
mbtiles and sqlitedb formats. These formats are commonly used by
mobile mapping applications like [Osmand](https://osmand.net/) and
[ODK Collect](https://docs.getodk.org/collect-intro/). There are two
primary formats:

- mbtiles, supported by many apps.
- sqlitedb, supported only by Osmand

Both of these use formats use underlying
[sqlite3](https://www.sqlite.org/index.html), with similar database
schemas. The schema are a simple XYZ that stores a png or jpeg
image. When the entire planet is chopped into squares, there is a
relation between which map tile contains the GPS coordinates you
want. Small zoom levels cover a large area, higher zoom levels a
smaller area.

Basemapper does not store anything in memory, all processing
is done as a stream so large areas can be downloaded. Time to go buy a
really large hard drive. You can also use this map tile cache for
any program that supports a TMS data source like
[JOSM](https://josm.openstreetmap.de/). Luckily once downloaded,
you don't have to update the map tile cache very often, but it's also
easy to do so when you need to. When I expect to be working offline, I
commonly download a larger area, and then in the field produce the
smaller files.

Basemapper. downloads map tiles to a cache and uses them to generate the
output files. It does not perform data conversion. The resulting
output can be used for visualizing geographic data and analyzing
survey responses in a spatial context. The script provides various
command-line options for customizing the output, such as setting the
zoom levels, boundary, tile cache, output file name, and more.

## Database Schemas

Mbtiles are used by multiple mobile apps, but our usage is primarly
for ODK Collect. Imagery basemaps are very useful for two
reasons. One, the map data may be lacking, so the imagery helps one to
naviagte. For ODK Collect the other advantage is you can select the
location based on where the building is, instead of were you are
standing. Mbtiles are pretty straight forward.

The sqlitedb schema used by Osmand looks the same at first, but has
one big difference. In this schema it tops out at zoom level 16, so
instead of incrementing, it decrements the zoom level. This obscure
detail took me a while to figure out, it isn't documented anywhere.

### mbtiles

    CREATE TABLE tiles (zoom_level integer, tile_column integer, tile_row integer, tile_data blob);
    CREATE INDEX tiles_idx on tiles (zoom_level, tile_column, tile_row);
    CREATE TABLE metadata (name text, value text);
    CREATE UNIQUE INDEX metadata_idx  ON metadata (name);

### sqlitedb

    CREATE TABLE tiles (x int, y int, z int, s int, image blob, PRIMARY KEY (x,y,z,s));
    CREATE INDEX IND on tiles (x,y,z,s);
    CREATE TABLE info (maxzoom Int, minzoom Int);
    CREATE TABLE android_metadata (en_US);

# Usage

The **basemapper.py** script is run from the command line when
running standalone, or the class can be imported into python
programs. The [Field Mapping Tasking
Manager](https://github.com/hotosm/fmtm/wiki) uses this as part of a
(FastAPI])<https://fastapi.tiangolo.com/>) backend for the website.

The first time you run basemapper.py, it'll start downloading map
tiles, which may take a long time. Often the upstream source is
slow. It is not unusual for downloading tiles, especially at higher
zoom levels may tak an entire day. Once tiles are download, producing
the outout tiles is quick as then it's just packaging. In areas where
I work frequentely, I usually download a large area even if it takes a
week or more so it's available when I need it. On my laptop I actually
have a map tile cache for the entire state of Colorado, as well as
many large areas of Nepal, Turkey, Kenya, Uganda, and Tanzania.

# Options

The basic syntax is as follows:

- -h, --help show this help message and exit
- -v, --verbose verbose output
- -b BOUNDARY, --boundary BOUNDARY - The boundary for the area you want, as BBOX string or geojson file.
- -z ZOOMS, --zooms ZOOMS - The Zoom levels
- -o OUTFILE, --outfile - OUTFILE Output file name
- -d OUTDIR, --outdir OUTDIR -Output directory name for tile cache
- -s {ersi,bing,topo,google,oam}, --source {ersi,bing,topo,google,oam} - Imagery source

The suffix of the output file is either **mbtiles** or **sqlitedb**, which is
used to select the output format. The boundary file, if specified, must be in
[GeoJson](https://geojson.org/) format.
If in BBOX string format, it must be comma separated:
"minX,minY,maxX,maxY".

## Imagery Sources

- ESRI - Environmental Systems Research Institute
- Bing - Microsoft Bing imagery
- Topo - USGS topographical maps (US only)
- OAM - OpenAerialMap

The default output directory is **/var/www/html**. The actual
subdirectory is the source name with **tiles** appended, so for
example **/var/www/html/oamtiles**. Putting the map tiles into webroot
lets JOSM or QGIS use them when working offline.

## Examples

### **Example 1:**

Generate a basemap for Osmand using
[ERSI](https://www.esri.com/en-us/home) imagery, for an area
specified by a geojson bounding box, and supporting zoom levels 12
through 19.

    [path]/basemapper.py -z 12-19 -b test.geojson -o test.sqlitedb -s esri

### **Example 2:**

As above, but mbtiles format, and Bing imagery source. The `-v` option
enables verbose output, which will show more details about the
download and processing progress. Also only download a single zoon
level.

    [path]/basemapper.py -v -z 16 -b test.geojson -o test.mbtiles -s bing
