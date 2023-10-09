#!/usr/bin/python3

#
#   Copyright (C) 2020, 2021, 2022 Humanitarian OpenstreetMap Team
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

import argparse
import logging
import os
import re
import sys

# from shapely.geometry import Point, LineString, Polygon
from collections import OrderedDict

import xmltodict

# Logging
log = logging.getLogger(__name__)


class ODKInstance(object):
    def __init__(
        self,
        filespec: str = None,
        data: str = None,
    ):
        """This class imports a ODK Instance file, which is in XML into a data
        structure.

        Args:
            filespec (str): The filespec to the ODK XML Instance file
            data (str): The XML data

        Returns:
            (ODKInstance): An instance of this object
        """
        self.data = data
        self.filespec = filespec
        if filespec:
            self.data = self.parse(filespec=filespec)
        elif data:
            self.data = self.parse(data)

    def parse(
        self,
        filespec: str,
        data: str = None,
    ):
        """Import an ODK XML Instance file ito a data structure. The input is
        either a filespec to the Instance file copied off your phone, or
        the XML that has been read in elsewhere.

        Args:
            filespec (str): The filespec to the ODK XML Instance file
            data (str): The XML data

        Returns:
            (list): All the entries in the IOPDK XML Instance file
        """
        rows = list()
        if filespec:
            logging.info("Processing instance file: %s" % filespec)
            file = open(filespec, "rb")
            # Instances are small, read the whole file
            xml = file.read(os.path.getsize(filespec))
        elif data:
            xml = data
        doc = xmltodict.parse(xml)
        import json

        json.dumps(doc)
        tags = dict()
        data = doc["data"]
        for i, j in data.items():
            if j is None or i == "meta":
                continue
            print(f"tag: {i} == {j}")
            pat = re.compile("[0-9.]* [0-9.-]* [0-9.]* [0-9.]*")
            if pat.match(str(j)):
                if i == "warmup":
                    continue
                gps = j.split(" ")
                tags["lat"] = gps[0]
                tags["lon"] = gps[1]
                continue
            if type(j) == OrderedDict or type(j) == dict:
                for ii, jj in j.items():
                    pat = re.compile("[0-9.]* [0-9.-]* [0-9.]* [0-9.]*")
                    if pat.match(str(jj)):
                        gps = jj.split(" ")
                        tags["lat"] = gps[0]
                        tags["lon"] = gps[1]
                        continue
                    if jj is None:
                        continue
                    print(f"tag: {i} == {j}")
                    if type(jj) == OrderedDict or type(jj) == dict:
                        for iii, jjj in jj.items():
                            if jjj is not None:
                                tags[iii] = jjj
                                # print(iii, jjj)
                            else:
                                print(ii, jj)
                                tags[ii] = jj
                    else:
                        if i[0:1] != "@":
                            tags[i] = j
            rows.append(tags)
        return rows


if __name__ == "__main__":
    """This is just a hook so this file can be run standlone during development."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", nargs="?", const="0", help="verbose output")
    parser.add_argument("-i", "--infile", required=True, help="instance data in XML format")
    args = parser.parse_args()

    os.path.basename(args.infile)

    # if verbose, dump to the terminal as well as the logfile.
    if not args.verbose:
        log.setLevel(logging.DEBUG)

        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        log.addHandler(ch)

    if not args.infile:
        parser.print_help()
        quit()

    inst = ODKInstance(args.infile)
    data = inst.parse(args.infile)
