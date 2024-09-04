#!/usr/bin/python3

# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
#
# This file is part of Osm-Fieldwork.
#
#     Osm-Fieldwork is free software: you can redistribute it and/or modify
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
#     along with Osm-Fieldwork.  If not, see <https:#www.gnu.org/licenses/>.
#

import argparse
import logging
import sqlite3
import sys

import pandas as pd

#
# This program is a utility to validate tags & values from the
# Impact spreadsheet with what is defined on the OSM Wiki
# or in taginfo, which is all tags every used in OSM. It's purpose
# is to create the private data section for ODK->OSM conversion.
#

# Instantiate logger
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


class ValidateModel(object):
    def __init__(self, taginfo=None):
        self.tags = dict()
        if not taginfo:
            self.taginfo = "taginfo-db.db"
        else:
            self.taginfo = taginfo
        self.db = sqlite3.connect(self.taginfo)
        self.cursor = self.db.cursor()
        self.threshold = 100

    def parse(self):
        models = "Impact Areas - Data Models V1.1.xlsx"
        data = pd.read_excel(models, sheet_name="Overview - all Tags", usecols=["key", "value"])

        entries = data.to_dict()
        total = len(entries["key"])
        index = 1
        while index < total:
            key = entries["key"][index]
            value = entries["value"][index]
            if value == "<text>":
                index += 1
                continue
            if key not in self.tags:
                self.tags[key.strip()] = list()
            self.tags[key.strip()].append(value.strip())
            index += 1
        return self.tags

    def validateTaginfo(self, csv=None):
        if csv:
            csvfile = open(csv, "w")
        threshold = self.threshold
        for key in self.tags.keys():
            for value in self.tags[key]:
                if value[:3] == "yes" or value[:2] == "no" or value[0] == "<":
                    continue
                threshold = self.threshold
                sql = f"SELECT value,count_all FROM tags where key='{key}'"
                # logging.debug(sql)
                result = self.cursor.execute(sql)
                data = result.fetchall()
                if len(data) == 0:
                    logging.warning(f"'{key}' does not exist in taginfo!")
                else:
                    for val in data:
                        if val[0] == value:
                            if value[:3] == "yes" or value[:2] == "no" or value[0] == "<":
                                continue
                            # logging.info(f"\"{value}\" exists in the taginfo for \"{key}\"!")
                        if val[1] < threshold:
                            logging.warning(f'"{value}" doesn\'t pass the threshold for "{key}"! Only {val[1]} occurances')
                            if csv:
                                csvfile.write(f"{key},{value},{val[1]}\n")
                            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate data_models using taginfo database")
    parser.add_argument("-v", "--verbose", nargs="?", const="0", help="verbose output")
    parser.add_argument("-t", "--taginfo", help="Taginfo database")
    parser.add_argument("-c", "--csv", help="Output CSV")
    args = parser.parse_args()

    # if verbose, dump to the termina
    if not args.verbose:
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)

        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        root.addHandler(ch)

    model = ValidateModel(args.taginfo)
    tags = model.parse()
    # import epdb; epdb.st()
    model.validateTaginfo(args.csv)
