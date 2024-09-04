#!/usr/bin/python3

# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
#
# This file is part of osm_fieldwork.
#
#     osm-fieldwork is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     osm-fieldwork is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with osm_fieldwork.  If not, see <https:#www.gnu.org/licenses/>.
#

import argparse
import os

from osm_fieldwork.osmfile import OsmFile

# find the path of root tests dir
rootdir = os.path.dirname(os.path.abspath(__file__))


def test_init(infile=f"{rootdir}/testdata/odk_pois.osm"):
    """Make sure the OSM file is initialized."""
    assert os.path.exists(infile)


def test_header(infile=f"{rootdir}/testdata/odk_pois.osm"):
    osm = OsmFile(f"{rootdir}/testdata/test-out.osm")
    osm.header()
    assert os.stat(infile).st_size > 0


def test_footer(infile=f"{rootdir}/testdata/odk_pois.osm"):
    osm = OsmFile(f"{rootdir}/testdata/test-out.osm")
    osm.footer()
    tmp = open(infile, "r")
    lines = tmp.readlines()
    for line in lines:
        last = line
    assert last == "</osm>\n"


def test_create_tag():
    osm = OsmFile(f"{rootdir}/testdata/test-out.osm")
    tmp = osm.createTag("foo", "bar")
    assert tmp["foo"] == "bar"


def test_create_node_notags():
    osm = OsmFile(f"{rootdir}/testdata/test-out.osm")
    node = dict()
    attrs = dict(id=12345, lat=1, lon=2, uid=54321, user="bar")
    node["attrs"] = attrs
    tmp = osm.createNode(node).lstrip().split(" ")
    assert tmp[1] == "id='12345'" and tmp[2] == "version='1'" and tmp[3] == "lat='1'"
    # print(tmp)


def test_create_node_modified():
    osm = OsmFile(f"{rootdir}/testdata/test-out.osm")
    node = dict()
    attrs = dict(id=12345, lat=1, lon=2, version=2, uid=54321, user="bar")
    node["attrs"] = attrs
    node["version"] = 7
    tmp = osm.createNode(node, modified=True)
    assert tmp.find("action")
    # print(tmp)


def test_create_node_tags():
    osm = OsmFile(f"{rootdir}/testdata/test-out.osm")
    node = dict()
    attrs = dict(id=12345, lat=1, lon=2, uid=54321, user="bar")
    node["attrs"] = attrs
    tmp = osm.createNode(node)
    assert tmp.find("bar") and tmp.find("foo")
    # print(tmp)


def test_create_way():
    osm = OsmFile(f"{rootdir}/testdata/test-out.osm")
    way = dict()
    way = dict()
    attrs = dict(id=12345, lat=1, lon=2, uid=54321, user="bar")
    way["attrs"] = attrs
    tags = dict(foo="bar", bar="foo")
    refs = list()
    refs.append(12345)
    refs.append(23456)
    refs.append(34567)
    way["tags"] = tags
    way["refs"] = refs
    osm.createWay(way)
    # print(tmp)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read and parse a CSV file from ODK Central")
    parser.add_argument("--infile", default=f"{rootdir}/testdata/odk_pois.osm", help="The CSV input file")
    parser.add_argument("--outfile", default=f"{rootdir}/testdata/test-out.osm", help="The output OSM XML file")
    args = parser.parse_args()

    # Delete the test output file
    if os.path.exists(args.outfile):
        os.remove(args.outfile)

    test_init(infile=args.infile)
    test_header(infile=args.infile)
    test_footer(infile=args.infile)
    test_create_tag()
    test_create_node_notags()
    test_create_node_tags()
    test_create_way()
    test_create_node_modified()
    # Delete the test output file
    if os.path.exists(args.outfile):
        os.remove(args.outfile)
