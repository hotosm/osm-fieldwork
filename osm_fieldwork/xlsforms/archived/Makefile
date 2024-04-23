# Copyright (c) 2020, 2021, 2022, 2023 Humanitarian OpenStreetMap Team
#
# This file is part of OSM-Fieldwork.
#
#     Osm-Fieldwork is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Osm-Fieldwork is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Osm-Fieldwork.  If not, see <https:#www.gnu.org/licenses/>.
#

# The Rob project on odk.hotosm.org
PROJECT=56
#DBNAME=nepal
DBNAME=underpass
POLY=../thamel.geojson
XLSFILES = \
	nature.xls \
	landusage.xls \
	waterpoints.xls \
	buildings.xls \
	cemeteries.xls \
	education.xls \
	places.xls \
	religious.xls \
	toilets.xls \
	wastedisposal.xls \
	health.xls \
	waterways.xls \
	camping.xls \
	amenities.xls
#	transportation.xls

XMLFILES = $(XLSFILES:.xls=.xml)
JSONFILES = $(XLSFILES:.xls=.geojson)
ODKFILES = $(XLSFILES:.xls=.odk)

all: $(XMLFILES)

EXTRACT = ../make_data_extract.py
CLIENT = ../odk_client.py
STAMPDIR=/tmp

# Convert XLSForm to XForm
%.xml : %.xls
	@xls2xform --pretty_print $<
	@echo "Generating $<"

%.stamp : %.xls
	stamp=$(STAMPDIR)/odk-$@; \
	touch $${stamp}; \
	echo "Generating $${stamp}"

landusage.geojson: landusage.stamp
landusage.stamp: landusage.xls

# Upload XForm and data extract to ODK Central
%.odk: %.xml
	@target=$*; \
	category=$*; \
	case $${category} in \
		"landusage") category="landuse";; \
		"health") category="healthcare";; \
		"nature") category="natural";; \
		"amenity") category="amenities";; \
	esac; \
	echo "Uploading data extract and XForm for \"$${category}\""; \
	datafiles="/tmp/$${target}.geojson"; \
	$(CLIENT) -v -i $(PROJECT) -f $${category} -x create $${target}.xml $${datafiles}

# Generate a data extract
%.geojson: %.xls
	@target=$(<:.xls=); \
	base=$(basename $(notdir $(POLY))); \
	category=$(subst .xls,,$<); \
	case $${category} in \
		"landusage") category="landuse";; \
		"health") category="healthcare";; \
		"nature") category="natural";; \
		"amenities") category="amenity";; \
	esac; \
	echo "Generating data extract for \"$${category}\""; \
	$(EXTRACT) -b $(POLY) -p -dn $(DBNAME) -g $${target}.geojson -c $${category}

%.clone: %.xml
	@target=$(<:.xml=); \
	base=$(basename $(notdir $(POLY))); \
	case $${category} in \
		"landusage") category="landuse";; \
		"health") category="healthcare";; \
		"nature") category="natural";; \
		"amenities") category="amenity";; \
	esac; \
	sed -e "s:<data id=\"[a-zA-Z0-9_]*\":<data id=\"$${base} $${target}\":" \
		-e "s/<h:title>[a-zA-Z0-9_]*</<h:title>$${base} $${target}</" \
		-e "s,jr://file/[a-zA-Z0-9_]*.geojson,jr://file/$${base}_$${target}.geojson," $< > $${base}_$${target}.xml; \
	cp -f $${target}.geojson $${base}_$${target}.geojson

# A simple naming convention is used to make it possible to automate as
# much as possible. The basename of the XLSForm file matches the form_id
# column in the settings sheet. The make_data_extract.py also uses the
# same value in the category options.
# Any associated data extract file from OSM is uploaded as well if it
# exists. Note that when using an external geojson file, Enketo doesn't
# support that. It only works on a device.

# Generate all XForms
xform: $(XMLFILES)

# Upload all XForms and data extracts to ODK Central
upload: $(ODKFILES)

# Get data extract
extract: $(JSONFILES)

# Cleanup the mess
clean: 
	rm -f *.xml *.geojson

force:

.SUFFIXES: .xml .xls .geojson .odk .clone
