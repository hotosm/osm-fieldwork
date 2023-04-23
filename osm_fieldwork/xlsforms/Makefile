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
PROJECT=19

POLY=../thamel.geojson

XLSFILES = \
	landusage.xls \
	nature.xls \
	waterpoints.xls \
	buildings.xls \
	cemeteries.xls \
	education.xls \
	places.xls \
	religious.xls \
	toilets.xls \
	transportation.xls \
	wastedisposal.xls \
	health.xls \
	waterways.xls

XMLFILES = $(XLSFILES:.xls=.xml)
JSONFILES = $(XLSFILES:.xls=.geojson)

all: $(XMLFILES)

EXTRACT = ../make_data_extract.py

%.xml : %.xls
	xls2xform --pretty_print $<

%.geojson : %.xls
	@target=$(<:.geojson=); \
	base=$(basename $(notdir $(POLY))); \
	category=$(subst .xls,,$<); \
	echo "Generating data extract for \"$${category}\""; \
	$(EXTRACT) -b $(POLY) -p -dn underpass -g $${category}.geojson -c $${category}

# A simple naming convention is used to make it possible to automate as
# much as possible. The basename of the XLSForm file matches the form_id
# column in the settings sheet. The make_data_extract.py also uses the
# same value in the category options.
# Any associated data extract file from OSM is uploaded as well if it
# exists. Note that when using an external geojson file, Enketo doesn't
# support that. It only works on a device.
upload: $(XMLFILES)
	@target=$(<:.xml=); \
	if test -e $${target}.geojson; then \
	  datafiles="$(DATAFILES) $${target}.geojson"; \
	else \
	  datafiles="$(DATAFILES)"; \
	fi; \
	odk_client.py -i $(PROJECT) -f $${target} -x create $< $${datafiles}

xform: $(XMLFILES)
	target=$(<:.xml=); \
	base=$(basename $(notdir $(POLY))); \
	sed -e "s:<data id=\"[a-zA-Z0-9_]*\":<data id=\"$${base} $${target}\":" \
		-e "s/<h:title>[a-zA-Z0-9_]*</<h:title>$${base} $${target}</" \
		-e "s,jr://file/[a-zA-Z0-9_]*.geojson,jr://file/$${base}$${target}.geojson," $< > $${base}$${target}.xml

extract: $(JSONFILES)

clean: 
	rm *.xml *.geojson

force:

clean:
	rm -f *.xml

.PHONEY: upload
