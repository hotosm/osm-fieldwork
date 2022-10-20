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
XMLFILES = $(XLSFILES:.xls=.xml)

# these are used by select_one_from_file or select_multiple_from_file
DATAFILES = towns.csv municipality.csv provider.csv opening_hours.csv

.SUFFIXES: .xls .xml

all: $(XMLFILES)

%.xml : %.xls
	cd lib/ && xls2xform --pretty_print ../$<

upload: $(XMLFILES)
	echo "Do nothing yet"
	echo $<
	echo $?
	echo $*
	echo $@
	cd lib && ../../odk_client.py -i 4 -f toilets -x create ../$< l $(DATAFILES)

force:
.PHONEY: upload
