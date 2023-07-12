#!/usr/bin/python3

# Copyright (c) 2023 Humanitarian OpenStreetMap Team
#
# This file is part of osm_fieldwork.
#
#     This is free software: you can redistribute it and/or modify
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
import sys
from osm_fieldwork.odk_merge import OdkMerge, conflateThread
from osm_fieldwork.osmfile import OsmFile


parser = argparse.ArgumentParser(
    description="Test odk_merge"
)
parser.add_argument("--odk", default="testdata/odk_pois.osm", help="The ODK file")
parser.add_argument("--osm", default="testdata/osm_buildings.geojson", help="The OSM data")
args = parser.parse_args()

def test_file():
    passes = 0
    osm = OsmFile()
    osmdata = osm.loadFile(args.odk)
    odk = OdkMerge(args.osm)
    data = conflateThread(osmdata, odk)
    # There are 8 features in the test data
    if len(data) == 8:
        passes += 1
    # The first feature is a match, so has the OSM ID, the second
    # feature doesn't match, so negative ID
    if data[0]['attrs']['id'] > 0 and data[0]['attrs']['id'] < 0:
        passes += 1
    # feature doesn't match, so negative ID
    if 'fixme' in data[0]['tags'] and 'fixme' not in data[1]['tags']:
        passes += 1
    assert(passes == 3)


if __name__ == "__main__":
    print("--- test_dbname_only() ---")
    test_file()
    print("--- done ---")
