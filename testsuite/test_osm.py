#!/usr/bin/python3

# Copyright (c) 2020, 2021 Humanitarian OpenStreetMap Team
#
# This file is part of odkconvert.
#
#     Underpass is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Underpass is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with odkconvert.  If not, see <https:#www.gnu.org/licenses/>.
#

import os
import argparse
from osmfile import OsmFile

parser = argparse.ArgumentParser(description='Read and parse a CSV file from ODK Central')
parser.add_argument("--infile", default="test.csv", help='The CSV input file')
args = parser.parse_args()

# Delete the test output file
if os.path.exists("test.osm"):
    os.remove("test.osm")

osm = OsmFile(filespec="test.osm")


def test_init():
    """Make sure the OSM file is initialized"""
    assert os.path.exists("test.osm")


def test_header():
    osm.header()
    tmp = open("test.osm", 'r')
    lines = tmp.readlines()
    print(lines)
    assert os.stat("test.osm").st_size > 0


def test_footer():
    osm.footer()
    tmp = open("test.osm", 'r')
    lines = tmp.readlines()
    for line in lines:
        last = line
    assert last == "</osm>\n"


if __name__ == '__main__':
    test_init()
    test_header()
    test_footer()

