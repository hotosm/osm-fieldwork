#!/usr/bin/python3

# Copyright (c) 2020, 2021 Humanitarian OpenStreetMap Team
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
import csv
import os
from sys import argv
from convert import Convert
from osmfile import OsmFile


class CSVDump(object):
    """A class to parse the CSV files from ODK Central"""
    def __init__(self):
        self.fields = dict()
        self.nodesets = dict()
        self.data = list()
        self.osm = None
        if argv[0][0] == "/" and os.path.dirname(argv[0]) != "/usr/local/bin":
            self.convert = Convert(os.path.dirname(argv[0]) + "/xforms.yaml")
        else:
            if os.path.exists("xforms.yaml"):
                self.convert = Convert("xforms.yaml")
            else:
                self.convert = Convert("../xforms.yaml")
        self.ignore = ["attachmentsexpected",  "attachmentspresent", "reviewstate", "edits", "gps_type", "accuracy", "deviceid"]
        self.ignore.extend(["key", "start", "end", "today", "status", "instanceid", "audio", "image", "phonenumber", "detail"])
        # self.convert.dump()

    def createOSM(self, file="tmp.osm"):
        self.osm = OsmFile(filespec=file)
        self.osm.header()

    def finishOSM(self):
        self.osm.footer()

    def parse(self, file):
        all = list()
        print("Parsing csv files %r" % file)
        with open(file, newline='') as csvfile:
            spamreader = csv.DictReader(csvfile, delimiter=',')
            for row in spamreader:
                tags = dict()
                for keyword, value in row.items():
                    base = self.basename(keyword).lower()
                    if base not in self.ignore:
                        key = self.convert.convertTag(base)
                        if len(value) > 0:
                             tags[key] = value
                all.append(tags)
        return all

    def basename(self, line):
        tmp = line.split('-')
        if len(tmp) == 0:
            return line
        base = tmp[len(tmp)-1]
        return base

    def createEntry(self, line=None):
        # print(line)
        obj = dict()
        tags = dict()
        refs = list()
        out = ""
        attributes = ("id", "timestamp", "lat", "lon", "uid", "user", "timestamp", "version", "action")
        for key, value in line.items():
            if key in self.ignore:
                continue
            if key in attributes:
                obj[key] = value
            else:
                if value is not None:
                    # a tag with a space is from a multiple selection, so break it into
                    # each piece. FIXME: Most OSM tags have no embedded spaces, I think...
                    for tag in value.split(' '):
                        # First convert the tag to the approved OSM equivalent
                        tmp = self.convert.convertTag(tag)
                        # Get the keyword for the value
                        keyword = self.convert.getKeyword(tmp)
                        if keyword == tmp:
                            tmp = tag
                        # print("XXX %r - %r: %r = %r" % (key, tag, tmp, keyword))
                        if key != "none":
                            tags[key] = tmp
                        if key == "track":
                            refs.append(tag)
                else:
                    continue
                    #rint(tmp, key, value)
            if len(tags) > 0:
                obj['tags'] = tags
                obj['refs'] = refs
        if 'lat' in obj:
            out += self.osm.createNode(obj)
        else:
            out += self.osm.createWay(obj)
        self.osm.write(out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='convert ODK CSV to OSM')
    parser.add_argument("--infile", help='The input file from ODK Central')
    parser.add_argument("--outfile", default='tmp.osm', help='The output file for JOSM')
    args = parser.parse_args()

    csvin = CSVDump()
    data = csvin.parse(args.infile)
    csvin.createOSM(args.outfile)
    for entry in data:
        csvin.createEntry(entry)

    csvin.finishOSM()
