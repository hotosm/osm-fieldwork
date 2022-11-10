#!/usr/bin/python3

# Copyright (c) 2020, 2021 Humanitarian OpenStreetMap Team
#
# This file is part of Odkconvert.
#
#     Odkconvert is free software: you can redistribute it and/or modify
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

# This uses https://github.com/kivy/python-for-android to produce apks for Android,
# and a zip file for python pip.

PACKAGE := org.odkconvert.py
NAME := ODKConvert
VERSION := 0.1

XLSFILES = healthcare.xls
XMLFILES = $(XLSFILES:.xls=.xml)

all: healthcare

%.xml : %.xls
	xls2xform --pretty_print $<

healthcare: healthcare.xml
	make_data_extract.py -p -dn colorado -c healthcare -ou health.geojson

force:
