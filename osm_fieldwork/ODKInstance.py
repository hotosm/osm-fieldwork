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
import json
import logging
import os
import re
import sys

import flatdict
import xmltodict

# Instantiate logger
log = logging.getLogger(__name__)


class ODKInstance(object):
    def __init__(
        self,
        filespec: str = None,
        data: str = None,
    ):
        """This class imports a ODK Instance file, which is in XML into a
        data structure.

        Args:
            filespec (str): The filespec to the ODK XML Instance file
            data (str): The XML data

        Returns:
            (ODKInstance): An instance of this object
        """
        self.data = data
        self.filespec = filespec
        self.ignore = ["today", "start", "deviceid", "nodel", "instanceID"]
        if filespec:
            self.data = self.parse(filespec=filespec)
        elif data:
            self.data = self.parse(data)

    def parse(
        self,
        filespec: str,
        data: str = None,
    ) -> dict:
        """Import an ODK XML Instance file ito a data structure. The input is
        either a filespec to the Instance file copied off your phone, or
        the XML that has been read in elsewhere.

        Args:
            filespec (str): The filespec to the ODK XML Instance file
            data (str): The XML data

        Returns:
            (dict): All the entries in the OSM XML Instance file
        """
        row = dict()
        if filespec:
            logging.info("Processing instance file: %s" % filespec)
            file = open(filespec, "rb")
            # Instances are small, read the whole file
            xml = file.read(os.path.getsize(filespec))
        elif data:
            xml = data
        doc = xmltodict.parse(xml)

        json.dumps(doc)
        tags = dict()
        data = doc["data"]
        flattened = flatdict.FlatDict(data)
        rows = list()
        pat = re.compile("[0-9.]* [0-9.-]* [0-9.]* [0-9.]*")
        for key, value in flattened.items():
            if key[0] == "@" or value is None:
                continue
            if re.search(pat, value):
                gps = value.split(" ")
                row["lat"] = gps[0]
                row["lon"] = gps[1]
                continue

            # print(key, value)
            tmp = key.split(":")
            if tmp[len(tmp) - 1] in self.ignore:
                continue
            row[tmp[len(tmp) - 1]] = value

        return row


if __name__ == "__main__":
    """This is just a hook so this file can be run standlone during development."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", nargs="?", const="0", help="verbose output")
    parser.add_argument("-i", "--infile", required=True, help="instance data in XML format")
    args = parser.parse_args()

    os.path.basename(args.infile)

    # if verbose, dump to the terminal as well as the logfile.
    if args.verbose is not None:
        logging.basicConfig(
            level=logging.DEBUG,
            format=("%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            datefmt="%y-%m-%d %H:%M:%S",
            stream=sys.stdout,
        )

    if not args.infile:
        parser.print_help()
        quit()

    inst = ODKInstance(args.infile)
    data = inst.parse(args.infile)
    # print(data)
