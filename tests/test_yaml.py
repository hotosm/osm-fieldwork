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
import sys
import os
from osm_fieldwork.xlsforms import xlsforms_path
from osm_fieldwork.yamlfile import YamlFile

parser = argparse.ArgumentParser(description="Read and parse a YAML file")
parser.add_argument(
    "--infile", help="The YAML input file"
)
args = parser.parse_args()

path = xlsforms_path.replace("/xlsforms", "")
infile = f"{path}/xforms.yaml"
data = YamlFile(infile)

def test_validate():
    """Tests for things under validate"""
    foo = data.yaml["validate"]
    bar = foo[1]["leisure"]
    assert "firepit" in bar


# def test_bool_good():
#     epdb.st()
#     assert "bear box" in data.yaml['convert'] is True

# def test_bool_bad():
#     assert "bad keyword" data.yaml['convert'] is not True


# def test_value():
#     assert "caravans" == "tourism"


if __name__ == "__main__":
    test_validate()
#    test_bool_good()
#    test_bool_bad()
#    test_value()
