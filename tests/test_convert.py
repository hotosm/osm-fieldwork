#!/usr/bin/python3

# Copyright (c) 2021, 2022, 2023 Humanitarian OpenStreetMap Team
#
# This file is part of Osm-Fieldwork.
#
#     Osm-Fieldwork is free software: you can redistribute it and/or modify
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
#     along with Osm-Fieldwork.  If not, see <https:#www.gnu.org/licenses/>.
#

import argparse
import os

from osm_fieldwork.convert import Convert
from osm_fieldwork.xlsforms import xlsforms_path

# find the path of root tests dir
rootdir = os.path.dirname(os.path.abspath(__file__))

parser = argparse.ArgumentParser(description="Read and convert a JSON file from ODK Central")
parser.add_argument("--infile", default=f"{rootdir}/testdata/testcamps.json", help="The JSON input file")
args = parser.parse_args()

path = xlsforms_path.replace("/xlsforms", "")
csv = Convert(f"{path}/xforms.yaml")


def test_keywords():
    """Convert a feature."""
    hits = 0
    if csv.convertData("fee"):
        hits += 1
    if csv.convertData("sac_scale") is False:
        hits += 1
    assert hits == 2


def test_convert_tag():
    """Test tag conversion."""
    hits = 0
    # Test a tag that gets converted
    if csv.convertTag("altitude") == "ele":
        hits += 1
    # Test a tag that doesn't get converted
    if csv.convertTag("foobar") == "foobar":
        hits += 1
    assert hits == 2


def test_single_value():
    """Test tag value conversion."""
    hits = 0
    # Test a value that gets converted
    if csv.convertValue("building:floor", "wood"):
        hits += 1
    assert hits == 1


def test_sub_value():
    """Test tag value conversion."""
    hits = 0
    # Test a value that gets converted
    val = csv.convertValue("cemetery_services", "cemetery")
    if len(val) == 1 and val[0]["amenity"] == "grave_yard":
        hits += 1
    assert hits == 1


def test_multiple_value():
    """Test tag value conversion."""
    hits = 0
    # Test a value that gets converted
    vals = csv.convertValue("amenity", "coffee")
    if len(vals) == 2 and vals[0]["amenity"] == "cafe" and vals[1]["cuisine"] == "coffee_shop":
        hits += 1
    assert hits == 1


# Run standalone for easier debugging when not under pytest
if __name__ == "__main__":
    test_keywords()
    test_convert_tag()
    test_single_value()
    test_sub_value()
    test_multiple_value()
