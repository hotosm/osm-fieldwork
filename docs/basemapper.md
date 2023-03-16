# Basemapper.py

Basemapper is a program that makes basemaps for mobile apps in two primary formats:

- mbtiles, supported by many apps.
- sqlite, supported by OSMAnd
 namely

Both of these use formats use underlying sqlite3, with similar database
schemas. 

Basemapper does not store anything in memory, all processing
is done as a stream, so large areas can be downloaded. Time to go buy a
really large hard drive... You can also use this map tile cache for
any program that supports a TMS data source. Luckily once downloaded,
you don't have to update the map tile cache very often, but it's also
easy to do so when you need to.

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
