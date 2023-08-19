#!/usr/bin/python3

# Copyright (c) 2020, 2021, 2022, 2023 Humanitarian OpenStreetMap Team
#
# This file is part of Osm-Fieldwork.
#
#     Osm-Fieldwork is free software: you can redistribute it and/or modify
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
#     along with Osm-Fieldwork.  If not, see <https:#www.gnu.org/licenses/>.
#

import yaml
import argparse
import logging
import sys

"""This parses a yaml file into a dictionary for easy access."""

# Instantiate logger
log = logging.getLogger(__name__)


class YamlFile(object):
    """Config file in YAML format"""

    def __init__(self, data):
        self.filespec = None
        #if data == str:
        self.filespec = data
        self.file = open(data, "rb").read()
        self.yaml = yaml.load(self.file, Loader=yaml.Loader)
        #else:
        #    self.yaml = yaml.load(str(data), Loader=yaml.Loader)

    def privateData(self, keyword: str):
        """See if a keyword is in the private data category"""
        for value in self.yaml["private"]:
            if keyword.lower() in value:
                return True
        return False

    def ignoreData(self, keyword: str):
        """See if a keyword is in the ignore data category"""
        for value in self.yaml["ignore"]:
            if keyword.lower() in value:
                return True
        return False

    def convertData(self, keyword: str):
        """See if a keyword is in the convert data category"""
        for value in self.yaml["convert"]:
            if keyword.lower() in value:
                return True
        return False

    def hasList(self, keyword: str):
        for tags in self.yaml["tags"]:
            for tag in tags:
                if tag == keyword:
                    return tag
            logging.debug(type(tags))

    def dump(self):
        """Dump the contents of the yaml file"""
        if self.filespec:
            print("YAML file: %s" % self.filespec)
        for key, values in self.yaml.items():
            print(f"Key is:{key}")
            for k in values:
                print(f"\t{k}")

    def write(self, table: list, where: list):
        tab = "    "
        yaml = ["select:", f"{tab}\"osm_id\": id", f"{tab}tags:"]
        for item in where:
            yaml.append(f"{tab}{tab}- {item}")
        yaml.append("from:")
        for item in table:
            yaml.append(f"{tab}- {item}")
        yaml.append("where:")
        yaml.append(f"{tab}tags:")
        notnull = f"{tab}{tab}- " + "{"
        for item in where:
            notnull += f"{item}: NOT NULL, "
        notnull = f"{notnull[:-2]}"
        notnull += "}"
        yaml.append(f"{notnull}")
        return yaml

#
# This script can be run standalone for debugging purposes. It's easier to debug
# this way than using pytest,
#
if __name__ == "__main__":
    # Enable logging to the terminal by default
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    root.addHandler(ch)

    parser = argparse.ArgumentParser(description="Read and parse a YAML file")
    parser.add_argument(
        "-i", "--infile", default="./xforms.yaml", help="The YAML input file"
    )
    args = parser.parse_args()

    yaml1 = YamlFile(args.infile)

    table = ("nodes", "ways_poly")
    where = ("building", "amenity", "shop", "tourism")
    tmp = yaml1.write(table, where)
    yaml2 = YamlFile(tmp)
    yaml2.dump()
