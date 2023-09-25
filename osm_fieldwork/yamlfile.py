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

import argparse
import logging
import sys

import yaml

# Instantiate logger
log = logging.getLogger(__name__)


class YamlFile(object):
    """Config file in YAML format."""

    def __init__(
        self,
        data: str,
    ):
        """This parses a yaml file into a dictionary for easy access.

        Args:
            data (str): The filespec of the YAML file to read

        Returns:
            (YamlFile): An instance of this object
        """
        self.filespec = None
        # if data == str:
        self.filespec = data
        self.file = open(data, "rb").read()
        self.yaml = yaml.load(self.file, Loader=yaml.Loader)
        # else:
        #    self.yaml = yaml.load(str(data), Loader=yaml.Loader)

    def privateData(
        self,
        keyword: str,
    ):
        """See if a keyword is in the private data category.

        Args:
            keyword (str): The keyword to search for

        Returns:
            (bool): Check to see if the keyword is in the private data section
        """
        for value in self.yaml["private"]:
            if keyword.lower() in value:
                return True
        return False

    def ignoreData(
        self,
        keyword: str,
    ):
        """See if a keyword is in the ignore data category.

        Args:
            keyword (str): The keyword to search for

        Returns:
            (bool): Check to see if the keyword is in the ignore data section
        """
        for value in self.yaml["ignore"]:
            if keyword.lower() in value:
                return True
        return False

    def convertData(
        self,
        keyword: str,
    ):
        """See if a keyword is in the convert data category.

        Args:
            keyword (str): The keyword to search for

        Returns:
            (bool): Check to see if the keyword is in the convert data section
        """
        for value in self.yaml["convert"]:
            if keyword.lower() in value:
                return True
        return False

    def dump(self):
        """Dump internal data structures, for debugging purposes only."""
        if self.filespec:
            print("YAML file: %s" % self.filespec)
        for key, values in self.yaml.items():
            print(f"Key is: {key}")
            for v in values:
                if type(v) == dict:
                    for k1, v1 in v.items():
                        if type(v1) == list:
                            for item in v1:
                                for i, j in item.items():
                                    print(f"\t{i} = {j}")
                        else:
                            print(f"\t{k1} = {v1}")
                    print("------------------")
                else:
                    print(f"\t{v}")

    def write(
        self,
        table: list,
    ):
        """Add to the YAML file.

        Args:
              table (list): The name of the database table

        Returns:
            (str): The modified YAML data
        """
        tab = "    "
        yaml = ["select:", f'{tab}"osm_id": id', f"{tab}tags:"]
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
    """This is just a hook so this file can be run standlone during development."""
    parser = argparse.ArgumentParser(description="Read and parse a YAML file")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-i", "--infile", required=True, default="./xforms.yaml", help="The YAML input file")
    args = parser.parse_args()

    # if verbose, dump to the terminal.
    if args.verbose is not None:
        log.setLevel(logging.DEBUG)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(threadName)10s - %(name)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        log.addHandler(ch)

    yaml1 = YamlFile(args.infile)
    yaml1.dump()

    table = ("nodes", "ways_poly")
    where = ("building", "amenity", "shop", "tourism")
    # tmp = yaml1.write(table)
    # yaml2 = YamlFile(tmp)
    # yaml2.dump()
