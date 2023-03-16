# Basemapper.py

Basemapper is a program that makes basemaps for mobile apps, namely
mbtiles, which are supported by many apps, and the sqlitedb format
used by Osmand. Both of these use sqlite3, with similar database
schemas. Basemapper does not store anything in memory, all processing
is done as a stream, so large areas can be downloaded. Time to go buy a
really large hard drive... You can also use this map tile cache for
any program that supports a TMS data source. Luckily once downloaded,
you don't have to update the map tile cache very often, but it's also
easy to do so when you need to.

# Options

- -h, --help show this help message and exit
- -v, --verbose verbose output
- -b BOUNDARY, --boundary BOUNDARY - The boundary for the area you want
- -z ZOOMS, --zooms ZOOMS - The Zoom levels
- -t TILES, --tiles TILES - Top level directory for tile cache
- -o OUTFILE, --outfile - OUTFILE Output file name
- -d OUTDIR, --outdir OUTDIR -Output directory name for tile cache
- -s {ersi,bing,topo,google,oam}, --source {ersi,bing,topo,google,oam} - Imagery source

# Examples

***Example 1:***
This command will generate a basemap for Osmand using ERSI imagery, and
supports zoom levels 12 through 19. The suffix of the data file is
used to determine which format to write. This uses the boundary file
to download and make a basemap.

    ./basemapper.py -z 12-19 -b test.geojson -o test.sqlitedb -s ersi

***Example 2:***
This command is similar to the  number one above but it generates  basemap for ODK Collect
 using mbtiles format.

    ./basemapper.py -z 12-19 -b test.geojson -o test.mbtiles -s ersi

***Example 3:***
This command is similar to the number two as it generates basemap for ODK Collect, 
however the imagery source is bing.
    
    ./basemapper.py -z 12-19 -b  test.geojson -o test.mbtiles -s bing

***Example 4:***
This command will generate a basemap for the Topo imagery source using sqlitedb format.
 Additionally, the `-d` option specifies directory name for the title cache; /tiles/test. This is useful
 if you want to use the tile cache for other programs or update it later
    
    ./basemapper.py -z 12-19 -b test.geojson -o test.sqlitedb -s topo -d /tiles/tests

***Example 5:***
This command will generate a basemap for the Google imagery source in mbtiles format. The `-v` 
option enables verbose output, which will show more details about the download and processing progress   
   
    ./basemapper.py -z 12-19 -b test.geojson -o test.mbtiles -s google -v
