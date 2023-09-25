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

from osm_fieldwork.odk_merge import OdkMerge, conflateThread
from osm_fieldwork.osmfile import OsmFile

# find the path of root tests dir
rootdir = os.path.dirname(os.path.abspath(__file__))

parser = argparse.ArgumentParser(description="Test odk_merge")
parser.add_argument("--odk", default=f"{rootdir}/testdata/odk_pois.osm", help="The ODK file")
parser.add_argument("--osm", default=f"{rootdir}/testdata/osm_buildings.geojson", help="The OSM data")
parser.add_argument("-d", "--database", default="PG:colorado", help="The database name")
parser.add_argument("-b", "--boundary", default=f"{rootdir}/testdata/Salida.geojson", help="The project AOI")
args = parser.parse_args()


def test_file():
    """This tests conflating against the GeoJson data extract file."""
    passes = 0
    osm = OsmFile()
    osmdata = osm.loadFile(args.odk)
    odk = OdkMerge(args.osm)
    # Although the code is multi-threaded, we can call the function that
    # does all the work directly without threading. Easier to debug this qay.
    data = conflateThread(osmdata, odk, 0)
    # There are 8 features in the test data
    if len(data) == 8:
        passes += 1
    # The first feature is a match, so has the OSM ID, the second
    # feature doesn't match, so negative ID
    if data[0]["attrs"]["id"] > 0 and data[1]["attrs"]["id"] < 0:
        passes += 1
    # duplicates have a fixme tag added
    if "fixme" in data[0]["tags"] and "fixme" not in data[1]["tags"]:
        passes += 1
    assert passes == 3


# FIXME update test_db to use local db in CI
# def test_db():
#     """This test against a local database. If there is no postgres, then
#     none of the tests get run."""
#     passes = 0
#     # this database always exists on this developer's machine
#     odk = OdkMerge("PG:colorado", args.boundary)
#     if odk.postgres is not None:
#         passes += 1
#     else:
#         return
#     # We also want to trap a bad database name
#     # odk = OdkMerge("PG:foobar")
#     # if odk.dbcursor is None:
#     #     passes += 1

#     osm = OsmFile()
#     osmdata = osm.loadFile(args.odk)
#     if len(osmdata) == 8:
#         passes += 1

#     # The first feature is a match, so has the OSM ID, the second
#     # feature doesn't match, so negative ID. Here we're just making
#     # sure it got loaded as a sanity check
#     keys = list(osmdata.keys())
#     if osmdata[keys[6]]['attrs']['id'] > 0 and osmdata[keys[0]]['attrs']['id'] < 0:
#         passes += 1

#     odk = OdkMerge(args.database, args.boundary)
#     # Although the code is multi-threaded, we can call the function that
#     # does all the work directly without threading. Easier to debug this way.
#     data = conflateThread(osmdata, odk, 0)
#     if len(data[6]['attrs']) > 0 and data[6]['attrs']['id'] > 0 and data[0]['attrs']['id'] < 0:
#         passes += 1
#     assert(passes == 4)

if __name__ == "__main__":
    print("--- test_file() ---")
    test_file()
    # print("--- test_db() ---")
    # test_db()
    print("--- done ---")
