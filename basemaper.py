#!/usr/bin/python3

# Copyright (c) 2020, 2021, 2022 Humanitarian OpenStreetMap Team
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

import argparse
import os
import logging
import sys
import epdb
from sys import argv
import mercantile
import glob


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create an mbtiles basemap for ODK Collect')
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-b", "--boundry", help='The boundary for the area you want')
    parser.add_argument("-z", "--zooms", default="12-17", help='The Zoom levels')
    parser.add_argument("-o", "--outfile", help='Output file name')
    parser.add_argument("-s", "--source", default="ersi", choices="ersi bing topo", help='Imagery source')
    args = parser.parse_args()

    # if verbose, dump to the terminal.
    if args.verbose is not None:
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)

        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        root.addHandler(ch)

# Get all the zoom levels we want
zooms = list()
if args.zooms:
    epdb.st()
    if args.zooms.find("-") > 0:
        start = int(args.zooms.split('-')[0])
        end = int(args.zooms.split('-')[1])
        x = range(start, end)
        for i in x:
            zooms.append(i)
    elif args.zooms.find(",") > 0:
        levels = args.zooms.split(',')
        for level in levels:
            zooms.append(int(level))
        
