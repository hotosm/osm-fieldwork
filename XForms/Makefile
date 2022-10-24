# Copyright (c) 2022 Humanitarian OpenStreetMap Team
#
# This file is part of Odkconvert.
#
#     This is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Odkconvert is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Odkconvert.  If not, see <https:#www.gnu.org/licenses/>.
#

XLSFILES = toilets.xls
# We could also use a wildcard to get all the XLS files in the directory, but instead
# we're defining the variable manually since many of the XKLSForms aren't being worked
# on yet.
# XLSFILES = cemeteries.xls regilious.xls school.xls toilets.xls transportation.xls waterpoints.xls waterways.xls

XMLFILES = $(XLSFILES:.xls=.xml)

# these are used by select_one_from_file or select_multiple_from_file
DATAFILES = towns.csv \
	municipality.csv \
	provider.csv \
	opening_hours.csv \
	operational_status.csv

.SUFFIXES: .xls .xml

all: $(XMLFILES)

%.xml : %.xls
	cd lib/ && xls2xform --pretty_print ../$<

# A simple naming convention is used to make it possible to automate as
# much as possible. The basename of the XLSForm file matches the form_id
# column in the settings sheet. The make_data_extract.py also uses the
# same value in the category options.
# Any associated data extract file from OSM is uploaded as well if it
# exists. Note that when using an external geojson file, Enketo doesn't
# support that. It only works on a device.
upload: $(XMLFILES)
	@target=$(?:.xml=); \
	if test -e $${target}.geojson; then \
	datafiles="$(DATAFILES) $${target}.geojson"; \
	else \
	datafiles="$(DATAFILES)"; \
	fi; \
	cd lib && ../../odk_client.py -i 4 -f $${target} -x create ../$< $${datafiles}

force:
.PHONEY: upload
