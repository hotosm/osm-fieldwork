# Basemapper.py

Basemapper is a program that creates basemaps for mobile apps in the mbtiles and sqlitedb formats. These formats are commonly used by mobile mapping applications like Osmand and ODK Collect in two primary formats:

- mbtiles, supported by many apps.
- sqlite, supported by OSMAnd

Both of these formats use underlying sqlite3, with similar database
schemas. 

Basemapper does not store anything in memory, all processing
is done as a stream, so large areas can be downloaded. Time to go buy a
really large hard drive... You can also use this map tile cache for
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


## Benefits

- Streamlines the process of creating basemaps for mobile apps
- Creates easily usable cache files for mobile apps
- Allows for easy integration of custom maps into data collection workflows for ODK Collect
- Particularly helpful for fieldwork or data collection in remote or hard-to-reach areas

To use Basemapper, simply provide it with the necessary input data, such as a bounding box or a list of tile coordinates. The program will then create the specified basemap file in either mbtiles or sqlitedb format.

It is recommended to store the resulting basemap file on a device or server that can be accessed by the mobile app using a TMS data source.

Overall, Basemapper is a valuable tool for developers and data collectors looking to create basemaps for mobile mapping applications. Its ability to create basemaps in multiple formats and its efficient processing capabilities make it a great option for large or remote areas. The program's ability to create mbtiles basemaps for ODK Collect is also a helpful feature for those working in data collection workflows.
