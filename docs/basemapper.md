# Basemapper.py

Basemapper is a program that creates basemaps for mobile apps in the mbtiles and sqlitedb formats. These formats are commonly used by mobile mapping applications like Osmand and ODK Collect in two primary formats:

- mbtiles, supported by many apps.
- sqlite, supported by OSMAnd
 namely

Both of these use formats use underlying sqlite3, with similar database
schemas. 

Basemapper does not store anything in memory, all processing
is done as a stream, so large areas can be downloaded. Time to go buy a
really large hard drive. You can also use this map tile cache for
any program that supports a TMS data source. Luckily once downloaded,
you don't have to update the map tile cache very often, but it's also
easy to do so when you need to.

In addition to that, `Basemapper.py` is a Python script included in the osm-fieldwork package, which builds mbtiles and sqlitedb files for ODK Collect and Osmand, typically containing satellite imagery. The script downloads map tiles to a cache and uses them to generate the basemap files. It does not perform data conversion. The resulting output can be used for visualizing geographic data and analyzing survey responses in a spatial context. The script provides various command-line options for customizing the output, such as setting the zoom levels, boundary, tile cache, output file name, and more.

# Usage
The `Basemapper.py` script is run from the command line. The basic syntax is as follows:

    Basemapper.py [-h] [-v] [-b BOUNDARY] [-z ZOOMS] [-t TILES] [-o OUTFILE] [-d OUTDIR] [-s {ersi,bing,topo,google,oam}] input_file

Converts form with a geoshape question into a map with tile overlays.

# Options
- -input_file, --This is a required positional argument that specifies the path to the input ODK form.
- -h, --help show this help message and exit
- -v, --verbose verbose output
- -b BOUNDARY, --boundary BOUNDARY - The boundary for the area you want
- -z ZOOMS, --zooms ZOOMS - The Zoom levels
- -t TILES, --tiles TILES - Top level directory for tile cache
- -o OUTFILE, --outfile - OUTFILE Output file name
- -d OUTDIR, --outdir OUTDIR -Output directory name for tile cache
- -s {ersi,bing,topo,google,oam}, --source {ersi,bing,topo,google,oam} - Imagery source

## Examples

**Example 1:**
Generate a basemap for OSMAnd using ERSI imagery, for an area specified by a geojson bounding box, and supporting zoom levels 12 through 19.

    ./basemapper.py -z 12-19 -b test.geojson -o test.sqlitedb -s ersi

**Example 2:**
As above, but mbtiles format, and Bing imagery source. The `-v` option enables verbose output,
which will show more details about the download and processing progress.   
   

    ./basemapper.py -z 12-19 -b test.geojson -o test.mbtiles -s bing -
    
    ./basemapper.py -z 12-19 -b test.geojson -o test.mbtiles -s ersi

## More examples of using Basemapper.py

### Example 1: Convert an ODK form with default settings

- Streamlines the process of creating basemaps for mobile apps
- Creates easily usable cache files for mobile apps
- Allows for easy integration of custom maps into data collection workflows for ODK Collect
- Is particularly helpful for fieldwork or data collection in remote or hard-to-reach areas

In this example, the script will use default settings for zoom levels, boundary, tile cache, output file name, and imagery source to generate a map output. The input file is `input_form.xml`.

### Example 2: Set custom zoom levels and imagery source

    python Basemapper.py -z 12-16 -s google input_form.xml

In this example, the `-z` option sets the zoom levels to 12-16, and the `-s` option sets the imagery source to Google. The input file is `input_form.xml`. The other options, such as boundary, tile cache, and output file name, will use their default settings.

### Example 3: Set custom boundary and output file name

    python Basemapper.py -b "25.5, -122.8, 37.5, -118.3" -o my_map.html input_form.xml

In this example, the `-b` option sets the boundary to "25.5, -122.8, 37.5, -118.3", which defines the southwest and northeast corners of the map. The `-o` option sets the output file name to "my_map.html". The input file is `input_form.xml`. The other options, such as zoom levels, tile cache, and imagery source, will use their default settings.

### Example 4: Enable verbose output

    python Basemapper.py -v input_form.xml

In this example, the `-v` option enables verbose output. The input file is `input_form.xml`. The other options, such as zoom levels, boundary, tile cache, output file name, and imagery source, will use their default settings.

### Example 5: Set custom tile cache and imagery source

    python Basemapper.py -t /path/to/tile/cache -s bing input_form.xml

In this example, the `-t` option sets the top level directory for the tile cache to "/path/to/tile/cache", and the `-s` option sets the imagery source to Bing. The input file is `input_form.xml`. The other options, such as zoom levels, boundary, and output file name, will use their default settings.

### Example 6: Set custom verbose output and imagery source

    python Basemapper.py -v -s ersi input_form.xml

In this example, the `-v` option enables verbose output, and the `-s` option sets the imagery source to ersi. The input file is `input_form.xml`. The other options, such as zoom levels, boundary, tile cache, and output file name, will use their default settings.
