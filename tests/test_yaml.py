#!/usr/bin/python3

# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
#
# This file is part of osm_fieldwork.
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
#     along with osm_fieldwork.  If not, see <https:#www.gnu.org/licenses/>.
#

import argparse
import logging

from osm_fieldwork.xlsforms import xlsforms_path
from osm_fieldwork.yamlfile import YamlFile

log = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description="Read and parse a YAML file")
parser.add_argument("--infile", help="The YAML input file")
args = parser.parse_args()

path = xlsforms_path.replace("/xlsforms", "")
infile = f"{path}/xforms.yaml"
data = YamlFile(infile)
# data.dump()


def test_load():
    """See if the file got loaded."""
    hits = 0
    if len(data.yaml.keys()) > 0:
        hits = 1
    if len(data.yaml["convert"]) > 0:
        hits += 1
    if len(data.yaml["ignore"]) > 0:
        hits += 1
    if len(data.yaml["private"]) > 0:
        hits += 1
    assert hits == 4


def test_good():
    hits = 0
    if data.convertData("amenity"):
        hits += 1
    if data.convertData("foobar") is False:
        hits += 1
    assert hits == 2


def test_private():
    hits = 0
    if data.privateData("income"):
        hits += 1
    if data.privateData("foobar") is False:
        hits += 1
    assert hits == 2


def test_ignore():
    hits = 0
    if data.ignoreData("model"):
        hits += 1
    if data.ignoreData("foobar") is False:
        hits += 1
    assert hits == 2


# def test_bool_bad():
#     assert "bad keyword" data.yaml['convert'] is not True


# def test_value():
#     assert "caravans" == "tourism"


if __name__ == "__main__":
    test_load()
    test_good()
    test_private()
    test_ignore()
