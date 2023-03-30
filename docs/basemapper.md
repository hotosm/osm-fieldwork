# Basemapper.py

Basemapper is a program that creates basemaps for mobile apps in the mbtiles and sqlitedb formats. These formats are commonly used by mobile mapping applications like Osmand and ODK Collect in two primary formats:

- mbtiles, supported by many apps.
- sqlite, supported by OSMAnd

Both of these use formats use underlying sqlite3, with similar database
schemas.

Basemapper does not store anything in memory, all processing
is done as a stream, so large areas can be downloaded. Time to go buy a
really large hard drive. You can also use this map tile cache for
any program that supports a TMS data source. Luckily once downloaded,
you don't have to update the map tile cache very often, but it's also
easy to do so when you need to.

Basemapper uses sqlite3 to create the database schema for these formats, and all processing is done as a stream, allowing for large areas to be downloaded without storing anything in memory. The resulting map tile cache can be used by any program that supports a TMS data source.

## Features

- Creates basemaps in mbtiles and sqlitedb formats
- Uses sqlite3 to create the database schema
- Processes data as a stream, allowing for large areas to be downloaded without storing anything in memory
- Can be used by any program that supports a TMS data source
- Can create mbtiles basemaps for ODK Collect

## Options

- -h, --help show this help message and exit.
- -v, --verbose verbose output.
- -b BOUNDARY, --boundary BOUNDARY - The boundary for the area you want.
- -z ZOOMS, --zooms ZOOMS - The Zoom levels to support.
- -t TILES, --tiles TILES - Top level directory for tile cache.
- -o OUTFILE, --outfile - OUTFILE Output file name. The file type is determined by the outfile extension.
- -d OUTDIR, --outdir OUTDIR -Output directory name for tile cache.
- -s {ersi,bing,topo,google,oam}, --source {ersi,bing,topo,google,oam} - Imagery source.

## Examples

**Example 1:**
Generate a basemap for OSMAnd using ERSI imagery, for an area specified by a geojson bounding box, and supporting zoom levels 12 through 19.

    ./basemapper.py -z 12-19 -b test.geojson -o test.sqlitedb -s ersi

**Example 2:**
As above, but mbtiles format, and Bing imagery source. The `-v` option enables verbose output,
which will show more details about the download and processing progress.


    ./basemapper.py -z 12-19 -b test.geojson -o test.mbtiles -s bing -v

**Example 3:**
Generate a basemap for the Topo imagery source using sqlitedb format.
 Additionally, the `-d` option specifies directory name for the title cache; /tiles/test. This is useful
 if you want to use the tile cache for other programs or update it later.

    ./basemapper.py -z 12-19 -b test.geojson -o test.sqlitedb -s topo -d /tiles/tests

**Example 4:**
Generate a basemap in mbtiles format using Google imagery source for an area specified by a geojson bounding box, and supporting zoom levels 10 through 16.

    ./basemapper.py -z 10-16 -b area.geojson -o map.mbtiles -s google

**Example 5:**
Generate a basemap in sqlitedb format using OpenAerialMap (OAM) imagery source for an area specified by a geojson bounding box, and supporting zoom levels 8 through 14.

    ./basemapper.py -z 8-14 -b area.geojson -o map.sqlitedb -s oam

**Example 6:**
Generate a basemap in mbtiles format using Topo imagery source for an area specified by a geojson bounding box, and supporting zoom levels 9 through 15. Additionally, the -t option specifies the top-level directory for the tile cache, which will be stored in /cache/tiles.

    ./basemapper.py -z 9-15 -b area.geojson -o map.mbtiles -s topo -t /cache/tiles

**Example 7:**
Generate a basemap in sqlitedb format using Bing imagery source for an area specified by a geojson bounding box, and supporting zoom levels 6 through 12. The -v option enables verbose output, which will show more details about the download and processing progress.

    ./basemapper.py -z 6-12 -b area.geojson -o map.sqlitedb -s bing -v

**Example 8:**
Generate a basemap in mbtiles format using OSMAnd imagery source for an area specified by a geojson bounding box, and supporting zoom levels 10 through 18. Additionally, the -d option specifies the output directory for the tile cache, which will be stored in /cache/tiles/osmand.

    ./basemapper.py -z 10-18 -b area.geojson -o map.mbtiles -s osmand -d /cache/tiles/osmand

**Example 9:**
Generate a basemap in sqlitedb format using Topo imagery source for an area specified by a geojson bounding box, and supporting zoom levels 11 through 17. The -v option enables verbose output, which will show more details about the download and processing progress.

    ./basemapper.py -z 11-17 -b area.geojson -o map.sqlitedb -s topo -v

**Example 10:**
Generate a basemap in mbtiles format using ERSI imagery source for an area specified by a geojson bounding box, and supporting zoom levels 7 through 13. The -b option specifies the boundary for the area you want.

    ./basemapper.py -z 7-13 -b area.geojson -o map.mbtiles -s ersi

## Benefits

- Streamlines the process of creating basemaps for mobile apps
- Creates easily usable cache files for mobile apps
- Allows for easy integration of custom maps into data collection workflows for ODK Collect
- Is particularly helpful for fieldwork or data collection in remote or hard-to-reach areas

To use Basemapper, simply provide it with the necessary input data, such as a bounding box or a list of tile coordinates. The program will then create the specified basemap file in either mbtiles or sqlitedb format.

It is recommended to store the resulting basemap file on a device or server that can be accessed by the mobile app using a TMS data source.

Overall, Basemapper is a valuable tool for developers and data collectors looking to create basemaps for mobile mapping applications. Its ability to create basemaps in multiple formats and its efficient processing capabilities make it a great option for large or remote areas. The program's ability to create mbtiles basemaps for ODK Collect is also a helpful feature for those working in data collection workflows.
