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
