## 0.5.4 (2024-03-19)

### Fix

- updated the error message for invalid odk-credentials (#241)
- method to update review state of submission (#236)

## 0.5.3 (2024-03-05)

### Fix

- **odk**: upload media failing validation if extension stripped accidentally
- argparse parsing of bbox string
- default outdir to current working dir
- optional bbox as space separated and comma separated
- add correct typing for bbox var and return types

## 0.5.2 (2024-03-04)

### Fix

- **regression**: upload Media uploading test data instead of real data

## 0.5.1 (2024-02-29)

### Fix

- rename form_fields --> formFields and handle all http errors (#230)

## 0.5.0 (2024-02-28)

### Feat

- add media upload filename validation against xform
- allow passing bytesio object for createForm & uploadMedia
- add media upload filename validation against xform
- allow passing bytesio object for createForm & uploadMedia

### Fix

- minor fixes to OdkForm
- mediaUpload for xform geojson
- return form name regardless of if exists or not
- minor fixes to OdkForm
- mediaUpload for xform geojson
- return form name regardless of if exists or not

## 0.4.4 (2024-02-26)

### Fix

- do not index xform path for form name

## 0.4.3 (2024-02-26)

### Fix

- more flexible parsing of xform name for uploadMedia

## 0.4.3rc0 (2024-02-13)

### Fix

- error handling in submission downloadThread (#227)

## 0.4.2 (2024-01-30)

### Fix

- update OdkAppUser qrcode & create methods
- replace HTTPBasicAuth with session tokens
- return types for OdkCentral submission methods
- work with wildcsrds with spaces
- Add tile filespec if it's an empty image

## 0.4.1 (2024-01-18)

### Fix

- For ODK, make sure there is always a label & title
- Fix logging, and fix polygon vs centroid
- Be less verbose with debugging
- Improve the values for the tags so it actually works
- Add filter_data api doc

### Refactor

- return full submissions detail
- add param debug log during basemap generation

## 0.4.0 (2023-12-05)

### Feat

- basic kivy ui to download basemaps

### Fix

- Fix merge conflict
- Make sure ref exists before trying to use it from a dict
- Add default variables

## 0.3.8 (2023-11-18)

### Fix

- Make less verbose
- Always escape the value for embedded quotes
- Fix bug with referencing an out of scope variable
- Use geojson instead of json to read in the boundary file
- Don't call OsmFile.footer, it's now handled by a destructor
- Add link to XLSForm design doc

## 0.3.7 (2023-10-23)

### Fix

- Add simple test case for creating imagery basemaps
- Accumulate all tiles for all zoom levels
- Use boundary file that is a single Feature in addition to a FeatureCollection
- Pass the config file to the YAML parser
- Add USGS reference numbers for highways
- custom tms download logic (tile ordering)
- bug pmtile generation if file exists in first dir
- create basemap directory automatically

## 0.3.6 (2023-10-09)

### Fix

- update all data-models to latest osm-rawdata syntax
- update indexes for xlsforms and data_models
- update xlsforms index

### Refactor

- update rootdir refs to variables

## 0.3.6rc3 (2023-10-09)

### Fix

- Merge in rawdata branch
- Drop extraneous parameter
- Set title and label always
- Use the right path to the xforms library
- Add name and name:em to keep
- xlocation accepted in the conflation if present
- Update for current reality, andd a few more programs
- Update doc to match code changes
- Add make_data_extract API doc
- Improve how the boundary gets parese dand passed as a parameter
- Use the new config class instead of parsing the YAML file
- ikport uriParser
- Enale logging

## 0.3.6rc2 (2023-09-11)

### Fix

- json2osm handle polygons and points (#192)
- Update raw-osmdata to 0.1.1
- add osm-rawdata dependency
- Major refactoring to use the new osm-rawdata module
- Add join_or tag which is now required in the enhanced YAML format
- Use optional env variable for the raw data API
- initialize variable
- Arg, change the raw data URI again
- json2osm calling via api
- The URL for raw data has changed
- Add config file for waterways

## 0.3.6rc1 (2023-09-07)

### Fix

- json2osm via cmdline + programatically

## 0.3.6rc0 (2023-09-01)

### Feat

- complete overhaul of docs, mkdocstrings

### Fix

- csv parsing for test
- Delete the UML images for clean
- Generate PDFs from the primary markdown files in docs/about
- Drop unused main.py file
- Add support for doxygen API docs
- fix typo in url for data flow diagram
- Add new data flow charts
- Use new imagery.yaml file for sources instead of hardcoding them all
- Add USGS topo map as a source
- Improve parsing to cover more than one format
- Add support for a custom TMS URL
- Add missing test data file
- Improve processing of Rwanda submissions, capture OSM ID and improve the conversion config file
- list forms api
- filespec made optional in the filterdata class
- text 78 was present, it is now removed
- indentation on odk_merge
- typing issues and imports
- Fix listForms(), the parameter name changed
- Add trailing comma to all function parameter blocks
- Add the deep tech docs
- fix typo in parameter name
- Add the more obscure utilities to the API docs
- Add more API wrappers
- Add mkdocs code comments
- Add mkdocs code comments
- Fix broken indent in debugging code, it was only being executed with -v
- Add standalone script for osm2favorites
- Add mkdocs code comments
- Add mkdocs code comments
- Add mkdocs code comments
- Add mkdocs code comments
- Add mkdocs comments
- Add mkdocs code comments
- Add bash wrapper for basemapper.py
- Update a few mkdocs comments so mkdocs serve is happy
- Minor updates to mkdoc comment, fix indentation
- Add mkdocs code comments
- Add more docs, organize top level links
- Replace lines of code that got deleted by accident
- Add mkdoc strings
- creating a project that already exists
- Add pySmartDL

### Refactor

- update refs logging --> log
- remove mkgendocs config

## 0.3.5 (2023-08-11)

### Fix

- Add mercantile
- indentation error in basemapper

## 0.3.4 (2023-08-06)

### Feat

- get extended details of a project
- get form full details
- Handle geometries better in the other json variant from Central

### Fix

- Improve methods to test data contents for tags
- Add more real tests
- conflateThread() takes an additional argument now
- Add some real tests for conversion
- Add test data for JSON to OSM conversion
- disable warnings from depenancies when running pytest
- getAllSubmissions() now takes an optional argument, which is the list of XForms
- Use flatfic module instead of traversing it ourselves
- comment out debug message
- handle uid/user in attrs better
- add flatdict module
- use a flattened dictionary instead of traversing everything ourselves
- use lower case for string matching, it's faster than fuzzy matching
- Minor update
- all tags should be in lower case
- if node is not present, return False in loadFIle in osmfile class
- load file in osmfile class
- no of threads missing some data at the end
- Add comment on commented out code block
- Drop escaping - in regex
- Trap bad auth with the ODK Central server
- Add timer to see how long it takes to process the data
- Add support to download all submissions for all tasks in a project
- Remove large block of commented out code
- Add support to download all submissions for all tasks in a project
- main, not moon
- Add new XLSForm for highways
- chunk set to 1 when the chunk value is 1
- fix indenting mistake that prevented display forms
- Add support to the underpass query to return linestrings
- Add support for highways
- handle XLSForms that don't use a data extract
- Add support for highways
- highways use ways_line, not ways_poly
- Add config file for highway query

## 0.3.3 (2023-07-25)

### Fix

- uncomment my stupid mistakes
- Add the new conflatin doc to the sidebar
- Add doc on how this project does conflation
- fix minor type
- Add make_data_extract to scripts
- Add more content
- Now that there are multiple postgres connections, clip all of them
- Handle no data returned errors
- Addd main() so it can be called when run standalone
- Add standalone scripts so all programs can be run from the install package
- Fix type in maion
- make a main function to they can run standalone
- Add a main function to this can run standalone from the installed python package
- Add new user manual to the sidebar
- Add new user manual
- Refactor to use an array of database connections, one for each thread to avoid proble
- Not all data has a timestamp, and it gets set anyone to the current time
- Major refactoring to support conflation with either postgis or the data extract used for FMTM
- keep more tags for the output file
- add more tags to keep for the output file
- Add newline after writing </way>
- Add government_menu to ignore
- Add tests for conflating with a database
- Add test prpoject boundary
- Improve test cases so they can find the test data files under pytest
- Update test data, and add test case for odk_merge
- Add section on importing the data into postgres
- use log so it works in FMTM, get the feature version in SQL queries
- Add support for using a GeoJson data extract as the conflation source
- Implement writing the OSM XML output file
- There are weird capitalization in the keywords
- Put the modified warning in a note instead of fixme
- Handle errors if there is no forms or project
- handle xlsfile better
- osmfile.footer() is now called by a destructor
- Don't escape spaces
- Implement conflating a POI against ways
- Add a destructor so the footer gets added when class is deleted
- Make output file optional
- Conversion from gdal is done, startin gto implement threads
- output files go into current dir, not /tmp
- escape is now a standalone function
- Make infile a required argument
- escape is now a standalone function so it can be used by other classes
- Update test cases since now data files get installed
- Add function for parsing database URIs, add test case for URI parser
- parse the OSM XML file if the data is in a dict
- THis gets processed lower down, so this is duplicate code
- Don't pass bogus config file
- Fix support to use Google imagery
- Fix support for bing imagery
- Update section on setting the default in Collect from OSM data
- Drop outfile from calling PostgresClient()
- Add roof:shape and roof:levels to keep
- Add shop to keep

## 0.3.2 (2023-06-27)

### Fix

- Convert the currt JSON format as downloaded from FMTM
- Fix processing of the ignore section
- Always write the value as a sting
- Remove the sldes.xls file
- Also use an optional user and password for database access

## 0.3.1 (2023-06-21)

### Fix

- For polygons in the data file, just use the centroids
- Add one to the ending zoom level so range() stops loosing the last zoom level
- Display usage() if no arguments are given
- Add qualifiers to limit the shops that get returned

## 0.3.1rc2 (2023-06-01)

### Fix

- Add utility that generates a fovorites file for Osmand
- Trap error for no output file and print usage()
- Add accuracy to ignore section
- Fix message in usage
- Added Osmand extensions for styling the favorites
- Write GPX file with Osmand specific styling
- Convert a GeoJson file into a favorites.gpx file for Osmand complete with all the tags
- Delete geometry tag from input datata stream so it doesn't casue confusion later
- Add support for processing either GeoJson (usually from odk2geojson) or JSON from Central
- Make timestamp for filename longer
- Change gosm to osm-fieldwork. Oops
- New program that converts the ODK XML instance files off your phone and turns it into good GeoJson for JOSM
- Disable debug message
- Major refactoring, it actually works now
- Always grab all the submissions

### Refactor

- improve logging for OdkCentral + createProject

## 0.3.1rc1 (2023-05-18)

### Fix

- xform in getSubmissions function
- output file in osm extracts
- add a default value
- use type for parameters to methods
- Use type for all parameters to methods
- conversion now returns a dict
- Remove accidental map-icons submodule, use types with all method parameters
- Drop paren
- Use line not linestring as a type, turn data into a dict from queryRemote()
- Default to using the underpass database for raw OSM data
- Remove debug message
- Add XLSForms for camping and small town amenity mapping
- Changes made while camping, mostly minor tweaks
- Remove stamp file
- Extract the metadata from the XLSForm
- Use the warmup location if there isn't one for the geopoint
- Add json as an input source
- Download the josn file of submissions from Central
- add more tags to ignore
- Process the json file from Central and write OSM XML and Geojsaon files
- return a dict instead of a list
- Convert the JSON fike from ODATA into OSM
- Process the defaults from the XLSFile
- process all rows to get the fields, as not all files have the same ones
- COnvert openfire tpo leisure=firepit, which is more common
- If the extract would be empty, write dummy entry so ODK Collect will still launch
- Fix logging
- Write dummy geojson file if there ios nothing in the extract
- fix logging setup, readoing CSV file
- use yaml as the config file if it exists
- Add support for generating variants of an XLSForm
- Add new non humanitarian XLSForms
- add support for amenities XLSForm
- Update the column names in all XLSForms to use the same name so they can all be scanned for the title and ID
- Add config file for amenities
- Add XLSForm for historical sites
- When querying a local database, collect all results
- Add support for new camping form
- refactor the groups of survey questions
- Add OSM map-icons as submodule
- fix typo in comment

## 0.3.1rc0 (2023-05-04)

### Fix

- got queryLocal(), get all the nodes and ways
- Process ODK_CENTRAL_SECURE correctly as the value from the end is a string, but the default is a bool
- Updates to layout, play with fancy colors
- Add method to extract the data extract filename, the XLSFOrm ID, and the XLSForm title from the spreadsheet
- Make default values work so we don't break the FMTM frontend
- Add content about name conflicts when using data extracts
- delete downloaded zip file after extracting the data file
- Implement uploading to Central
- minor changes
- Fix xform target and suffix rules to work with the name changes to avoid conflicts with OSM tags
- rename to avoid name conflict with OSM tag
- Fix typo in keyword
- Rename place to places to avoid a name conflict with an OSM tag
- when run standalone, the xform doesn't have to be changed, and fix wrong error message
- Updated so all the columns are in the same order, cleanup high lighting
- minor formatting changes
- rename t oplaces to avoid a conflict with the OSM place tag
- The yaml config filenane should match the xlsform, not the category
- rename file to avoid a nanme conflict with healthcare OSM tag
- Extract the XForm title and the name of the data extract from the XLSFoem
- Filter the types of waste amenities wanted, otherwise we get all amenities
- Rename to avoid naming conflicts with an OSM tag
- Rename natural to nature to avoid name conflicts with OSM
- Make the XLSForm for a category configurable via a YAML file to avoid name conflicts
- renamed to avoid a name conflict with the waste OSM tag
- rename landuse.yaml to landusage to avoid a name conflict with the landuse tag
- Add support to generate data extracts for all categories for testing
- rename landude.xls to landusage so the name doesn't conflict with the tag
- Update to support OSM data extracts, a few tewaks for the data models
- Add tag values to json file for remote database queries
- Improve command line for polygon vs centroid
- Enable reding tags to keep from yaml file
- Optionally output polygons instead of centroids when using a local postgres database
- Use python package to find xforms.yaml file
- Fix test cases to work with pythohn package
- add healthcare_type
- use list_name with an underbar instead of space
- Updated to support data extracts
- Make the OSM tags to keep configurable in the yaml file
- When reading an environment variable that is a boolean, convert the string to a bool
- Add nsupport to extract either polygons of centroids. Add boundary polygon to the extract
- Support a option to specify the path to the taginfo db and output csv
- Update file with YAML file syntax and examples
- Update docs, some content pulled into new files
- Refacor the programs.md file, move large detailed content into there own files

## 0.2.0 (2023-03-31)

### Feat

- rename repo odkconvert --> osm-fieldwork

### Fix

- For querying Overpass, use either a file or a geojson dict
- fix merge conflicts
- Merge documentation changes from development branch
- modified all files, replacing odkconvert wth osm-fieldwork
- Add overpy
- Minor typo fix
- Refactor and update

## 0.1.1 (2023-03-29)

### Fix

- Refactor and update

## 0.1.0 (2023-03-25)

### Feat

- set ssl verify via environment variable, default true
- option to configure standalone odkconvert via env vars
- index for xform files, plus path

### Fix

- update logging
- listProjects and findAppUser methods for OdkCentral, update logging
- relative imports --> absolute imports for packaging
- update verify=True for urllib to verify certs
- allow listProjects to fail gracefully if none exist
- typo for religious
- makefile zip bundle, pyproject version attr
- update paths for xforms.yaml, fix CSVDump.parse

### Refactor

- rename xforms to xlsforms throughout code
- rename xform dir to xlsform, more descriptive
- rename xforms path var for clarity
- remove redundant csv output files from xforms
- update refs to xforms dir and odk_client.py
- rename XForms dir to lowercase xforms
- add includes to pyproject to bundle odkconvert dir
- missed yaml file for restructure
- rename test dir to pytest default (tests)
- restructure, move .py files to odkconvert dir
