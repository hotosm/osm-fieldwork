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
from CSVDump import CSVDump
import pytest

parser = argparse.ArgumentParser(description='Read and parse a CSV file from ODK Central')
parser.add_argument("--infile", default="test.csv", help='The CSV input file')
args = parser.parse_args()

csv = CSVDump()


def test_init():
    """Make sure the YAML file got loaded"""
    assert len(csv.data.yaml) > 0


def test_csv():
    """Make sure the CSV file got loaded"""
    tmp = csv.parse("test.csv")
    print(tmp)


if __name__ == '__main__':
    test_init()
    test_csv()
