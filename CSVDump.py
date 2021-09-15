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

import sys
import argparse
import glob
import yaml
import logging
import csv
import argparse
import epdb                      # FIXME: remove later
from osmfile import OsmFile

class CSVDump(object):
    """A class to parse the CSV files from ODK Central"""
    def __init__(self):
        self.fields = dict()
        self.nodesets = dict()
        self.data = list()

    def parse(self, file):
        data = list()
        print("Parsing csv files %r" % file)
        with open(file, newline='') as csvfile:
            spamreader = csv.DictReader(csvfile, delimiter=',')
            for row in spamreader:
                tag = dict()
                # print("XXX %r" % row)
                for keyword,value in row.items():
                    base = self.basename(keyword).lower()
                    #epdb.st()
                    if base == "latitude":
                        key = "lat"
                    elif base == "longitude":
                        key = "lon"
                    elif base == "altitude":
                        key = "ele"
                    elif base == "submitterid":
                        key = "uid"
                    elif base == "submittername":
                        key = "user"
                    elif base == "submissiondate":
                        key = "timestamp"
                    elif base == "attachmentspresent":
                        continue
                    elif base == "attachmentsexpected":
                        continue
                    elif base == "reviewstate":
                        continue
                    elif base == "edits":
                        continue
                    elif base == "gps_type":
                        continue
                    elif base == "accuracy":
                        continue
                    elif base == "deviceid":
                        continue
                    elif base == "key":
                        continue
                    elif base == "start":
                        continue
                    elif base == "end":
                        continue
                    elif base == "today":
                        continue
                    elif base == "status":
                        continue
                    elif base == "instanceid":
                        continue
                    else:
                        key = base
                    #print(key, value)
                    if len(value) == 0:
                        continue
                    tag[key] = value
                data.append(tag)
        return data

    def basename(self, line):
        tmp = line.split('-')
        if len(tmp) == 0:
            return line
        base = tmp[len(tmp)-1]
        return base

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='convert ODK CSV to OSM')
    parser.add_argument("--infile", help='The input file from ODK Central')
    parser.add_argument("--outfile", default='tmp.osm', help='The output file for JOSM')
    args = parser.parse_args()
    print(args)
    
    infile = CSVDump()
    outfile =  args.outfile
    osm = OsmFile(filespec=outfile)
    osm.header()

    # These become attributes for the feature. Anything not listed
    # here becomes a tag.
    nottags = ("lat", "lon", "uid", "user", "timestamp")
    attrs = dict()
    tags = dict()
    tmp = infile.parse(args.infile)
    for item in tmp:            
        for key,value in item.items():
            try:
                idx = nottags.index(key.lower())
                attrs[key.lower()] = value.lower()
            except:
                logging.info("Not an attribute %r!" % key.lower())
                tags[key.lower()] = value.lower()
            # print("XXX %s" % key, value, )
        try:
            idx = nottags.index("lat")
            node = osm.createNode(attrs, tags)
            osm.writeNode(node)
        except:
            way = osm.createWay(attrs, tags)
            osm.writeWay(way)
            point = False
    
    osm.footer()
    
