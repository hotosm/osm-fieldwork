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

import logging
import string
import epdb
import argparse
from yamlfile import YamlFile
from dejagnu import DejaGnu

parser = argparse.ArgumentParser(description='Read and parse a YAML file')
parser.add_argument("--infile", default="xforms.yaml", help='The YAML input file')
args = parser.parse_args()
data = YamlFile(args.infile)

dj = DejaGnu()
foo = data.getValues("validate")
bar = foo[1]['leisure']
if "firepit" in bar:
    dj.passes("getValues(list)")
else:
    dj.fails("getValues(list)")

if data.getValues("bear box") == True:
    dj.passes("getValues(bool)")
else:
    dj.fails("getValues(bool)")

if data.getKeyword("caravans") == "tourism":
    dj.passes("getKeyword()")
else:
    # yaml.dump()
    dj.fails("getKeyword()")
