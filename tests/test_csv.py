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
import os

from osm_fieldwork.CSVDump import CSVDump

# find the path of root tests dir
rootdir = os.path.dirname(os.path.abspath(__file__))

parser = argparse.ArgumentParser(description="Read and parse a CSV file from ODK Central")
parser.add_argument("--infile", default=f"{rootdir}/testdata/test.csv", help="The CSV input file")
args = parser.parse_args()
csv = CSVDump()
print(args)
data = csv.parse(args.infile)
print(data)


def test_csv():
    """Make sure the CSV file got loaded and parsed."""
    assert len(data) > 0


def test_init():
    """Make sure the YAML file got loaded."""
    assert len(csv.yaml.yaml) > 0


def test_osm_entry():
    csv.createOSM(args.infile)
    line = {
        "timestamp": "2021-09-25T14:27:43.862Z",
        "end": "2021-09-24T17:55:26.194-06:00",
        "today": "2021-09-24",
        "features": "firepit parking caravans",
        "internet": "none",
        "lat": "38.3697403",
        "lon": "-106.3078813",
        "ele": "2825.998",
        "uid": "123435",
        "user": "Foobar",
    }
    csv.createEntry(line)
    # assert tmp


if __name__ == "__main__":
    test_init()
    test_csv()
    # test_osm_entry()
