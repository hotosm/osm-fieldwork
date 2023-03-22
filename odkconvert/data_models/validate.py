#!/usr/bin/python3

# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
#
# This file is part of odkconvert.
#
#     ODKConvert is free software: you can redistribute it and/or modify
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
#     along with odkconvert.  If not, see <https:#www.gnu.org/licenses/>.
#

import argparse
import logging
import sys
import os
import pandas as pd
import sqlite3
import requests
from requests.auth import HTTPBasicAuth

#
# This program is a utility to validate tags & values from the
# Impact spreadsheet with what is defined on the OSM Wiki
# or in taginfo, which is all tags every used in OSM. It's purpose
# is to create the private data section for ODK->OSM conversion.
#

# Instantiate logger
logging.basicConfig(stream = sys.stdout,level=logging.INFO)

class ValidateModel(object):
    def __init__(self):
        self.tags = dict()
        self.wiki = "taginfo-wiki.db"
        self.taginfo = "taginfo-db.db"
        if not os.path.exists(f"{self.wiki}.bz2") and not os.path.exists(self.wiki):
            log.error("""You need to download the taginfo wiki database from: 
            https://taginfo.openstreetmap.org/download/taginfo-wiki.db.bz2""")
            quit()
        self.wikidb = sqlite3.connect(self.wiki)
        self.wikicursor = self.wikidb.cursor()
        if not os.path.exists(f"{self.taginfo}.bz2") and not os.path.exists(self.taginfo):
            log.error("""You need to download the full taginfo database from: 
            https://taginfo.openstreetmap.org/download/taginfo-db.db.bz2""")
            quit()
        self.db = sqlite3.connect(self.taginfo)
        self.cursor = self.db.cursor()
        self.threshold = dict()
        self.url = "https://taginfo.openstreetmap.org/taginfo/apidoc#api_4_key_values?"
        self.session = requests.Session()
        self.headers = {'Content-Type': 'application/json;charset=UTF-8'}
        self.threshold = 100

    def parse(self):
        models = 'Impact Areas - Data Models V1.1.xlsx'
        data = pd.read_excel(models, sheet_name="Overview - all Tags", usecols=["key", "value"])
        
        entries = data.to_dict()
        total = len(entries['key'])
        index = 1
        while index < total:
            key = entries['key'][index]
            value = entries['value'][index]
            if value == "<text>":
                index += 1
                continue
            if key not in self.tags:
                self.tags[key.strip()] = list()
            self.tags[key.strip()].append(value.strip())
            index += 1
        return self.tags

    def validateTaginfo(self):
        threshold = self.threshold
        for key in self.tags.keys():
            for value in self.tags[key]:
                if value[:3] == 'yes' or value[:2] == 'no' or value[0] == '<':
                    continue
                threshold = self.threshold
                sql = f"SELECT value,count_all FROM tags where key='{key}'"
                result = self.cursor.execute(sql)
                data = result.fetchall()
                if len(data) == 0:
                    logging.warning(f"\'{key}\' does not exist in taginfo!")
                else:
                    for val in data:
                        if val[0] == value:
                            if value[:3] == 'yes' or value[:2] == 'no' or value[0] == '<':
                                continue
                            # logging.info(f"\"{value}\" exists in the taginfo for \"{key}\"!")
                            if val[1] < threshold:
                                logging.warning(f"\"{value}\" doesn't pass the threshold for \"{key}\"! Only {val[1]} occurances")
                            break
            #import epdb; epdb.st()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Validate data_models using taginfo database"
    )
    parser.add_argument("-v", "--verbose", nargs="?", const="0", help="verbose output")
    args = parser.parse_args()

    model = ValidateModel()
    tags = model.parse()
    # import epdb; epdb.st()
    model.validateTaginfo()

