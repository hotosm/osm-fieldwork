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
        tag = dict()
        print("Parsing csv files %r" % file)
        with open(file, newline='') as csvfile:
            spamreader = csv.DictReader(csvfile, delimiter=',')
            for row in spamreader:
                for keyword,value in row.items():
                    base = self.basename(keyword)
                    if base == "SubmitterID":
                        key = "uid"
                    elif base == "SubmitterName":
                        key = "user"
                    elif base == "SubmissionDate":
                        key = "timestamp"
                    elif base == "AttachmentsPresent":
                        continue
                    elif base == "AttachmentsExpected":
                        continue
                    elif base == "ReviewState":
                        continue
                    elif base == "Edits":
                        continue
                    elif base == "DeviceID":
                        continue
                    elif base == "KEY":
                        continue
                    elif base == "start":
                        continue
                    elif base == "end":
                        continue
                    elif base == "today":
                        continue
                    elif base == "Status":
                        continue
                    elif base == "instanceID":
                        continue
                    else:
                        key = base
                    #print(key, value)
                    if len(value) == 0:
                        continue
                    tag[key] = value
                # epdb.st()
                data.append(tag)
        return data

    def basename(self, line):
        tmp = line.split('-')
        if len(tmp) == 0:
            return line
        base = tmp[len(tmp)-1]
        return base

if __name__ == '__main__':

    infile = CSVDump()
    outfile = "foo.osm"
    osm = OsmFile(filespec=outfile)
    osm.header()

    tmp = infile.parse("camping.csv")
    print(tmp)
    
    osm.footer()
    
