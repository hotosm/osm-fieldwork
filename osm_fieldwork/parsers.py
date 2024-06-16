#!/usr/bin/python3

# Copyright (c) 2024 Humanitarian OpenStreetMap Team
#
# This file is part of OSM-Fieldwork.
#
#     OSM-Fieldwork is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     OSM-Fieldwork is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with OSM-Fieldwork.  If not, see <https:#www.gnu.org/licenses/>.
#

import csv
import json
import logging
import os
import re
from pathlib import Path

import flatdict
import xmltodict

from osm_fieldwork.convert import Convert
from osm_fieldwork.support import basename
from osm_fieldwork.xlsforms import xlsforms_path

# Instantiate logger
log = logging.getLogger(__name__)


class ODKParsers(Convert):
    """A class to parse the CSV files from ODK Central."""

    def __init__(
        self,
        yaml: str = None,
    ):
        self.fields = dict()
        self.nodesets = dict()
        self.data = list()
        self.osm = None
        self.json = None
        self.features = list()
        xlsforms_path.replace("xlsforms", "")
        if yaml:
            pass
        else:
            pass
        self.config = super().__init__(yaml)
        self.saved = dict()
        self.defaults = dict()
        self.entries = dict()
        self.types = dict()

    def CSVparser(
        self,
        filespec: str,
        data: str = None,
    ) -> list:
        """Parse the CSV file from ODK Central and convert it to a data structure.

        Args:
            filespec (str): The file to parse.
            data (str): Or the data to parse.

        Returns:
            (list): The list of features with tags
        """
        all_tags = list()
        if not data:
            f = open(filespec, newline="")
            reader = csv.DictReader(f, delimiter=",")
        else:
            reader = csv.DictReader(data, delimiter=",")
        for row in reader:
            tags = dict()
            # log.info(f"ROW: {row}")
            for keyword, value in row.items():
                if keyword is None or value is None:
                    continue
                if len(value) == 0:
                    continue
                base = basename(keyword).lower()
                # There's many extraneous fields in the input file which we don't need.
                if base is None or base in self.ignore or value is None:
                    continue
                else:
                    # log.info(f"ITEM: {keyword} = {value}")
                    if base in self.types:
                        if self.types[base] == "select_multiple":
                            vals = self.convertMultiple(value)
                            if len(vals) > 0:
                                tags.update(vals)
                            continue
                    # When using geopoint warmup, once the display changes to the map

                    # location, there is not always a value if the accuracy is way
                    # off. In this case use the warmup value, which is where we are
                    # hopefully standing anyway.
                    if base == "latitude" and len(value) == 0:
                        if "warmup-Latitude" in row:
                            value = row["warmup-Latitude"]
                            if base == "longitude" and len(value) == 0:
                                value = row["warmup-Longitude"]
                    items = self.convertEntry(base, value)
                    # log.info(f"ROW: {base} {value}")
                    if len(items) > 0:
                        if base in self.saved:
                            if str(value) == "nan" or len(value) == 0:
                                # log.debug(f"FIXME: {base} {value}")
                                val = self.saved[base]
                                if val and len(value) == 0:
                                    log.warning(f'Using last saved value for "{base}"! Now "{val}"')
                                    value = val
                            else:
                                self.saved[base] = value
                                log.debug(f'Updating last saved value for "{base}" with "{value}"')
                        # Handle nested dict in list
                        if isinstance(items, list):
                            items = items[0]
                        for k, v in items.items():
                            tags[k] = v
                    else:
                        tags[base] = value
            # log.debug(f"\tFIXME1: {tags}")
            all_tags.append(tags)
        return all_tags

    def JSONparser(
        self,
        filespec: str = None,
        data: str = None,
    ) -> list:
        """Parse the JSON file from ODK Central and convert it to a data structure.
        The input is either a filespec to open, or the data itself.

        Args:
            filespec (str): The JSON or GeoJson input file to convert
            data (str): The data to convert

        Returns:
            (list): A list of all the features in the input file
        """
        log.debug(f"Parsing JSON file {filespec}")
        total = list()
        if not data:
            file = open(filespec, "r")
            infile = Path(filespec)
            if infile.suffix == ".geojson":
                reader = geojson.load(file)
            elif infile.suffix == ".json":
                reader = json.load(file)
            else:
                log.error("Need to specify a JSON or GeoJson file!")
                return total
        elif isinstance(data, str):
            reader = geojson.loads(data)
        elif isinstance(data, list):
            reader = data

        # JSON files from Central use value as the keyword, whereas
        # GeoJSON uses features for the same thing.
        if "value" in reader:
            data = reader["value"]
        elif "features" in reader:
            data = reader["features"]
        else:
            data = reader
        for row in data:
            # log.debug(f"ROW: {row}\n")
            tags = dict()
            if "properties" in row:
                row["properties"]  # A GeoJson formatted file
            else:
                pass  # A JOSM file from ODK Central

            # flatten all the groups into a sodk2geojson.pyingle data structure
            flattened = flatdict.FlatDict(row)
            # log.debug(f"FLAT: {flattened}\n")
            for k, v in flattened.items():
                last = k.rfind(":") + 1
                key = k[last:]
                # a JSON file from ODK Central always uses coordinates as
                # the keyword
                if key is None or key in self.ignore or v is None:
                    continue
                # log.debug(f"Processing tag {key} = {v}")
                if key == "coordinates":
                    if isinstance(v, list):
                        tags["lat"] = v[1]
                        tags["lon"] = v[0]
                        # poi = Point(float(lon), float(lat))
                        # tags["geometry"] = poi
                    continue

                if key in self.types:
                    if self.types[key] == "select_multiple":
                        # log.debug(f"Found key '{self.types[key]}'")
                        if v is None:
                            continue
                        vals = self.convertMultiple(v)
                        if len(vals) > 0:
                            tags.update(vals)
                        continue
                items = self.convertEntry(key, v)
                if items is None or len(items) == 0:
                    continue

                if type(items) == str:
                    log.debug(f"string Item {items}")
                elif type(items) == list:
                    # log.debug(f"list Item {items}")
                    tags.update(items[0])
                elif type(items) == dict:
                    # log.debug(f"dict Item {items}")
                    tags.update(items)
            # log.debug(f"TAGS: {tags}")
            if len(tags) > 0:
                total.append(tags)

        # log.debug(f"Finished parsing JSON file {filespec}")
        return total

    def XMLparser(
        self,
        filespec: str,
        data: str = None,
    ) -> list:
        """Import an ODK XML Instance file ito a data structure. The input is
        either a filespec to the Instance file copied off your phone, or
        the XML that has been read in elsewhere.

        Args:
            filespec (str): The filespec to the ODK XML Instance file
            data (str): The XML data

        Returns:
            (list): All the entries in the OSM XML Instance file
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
        # total = list()
        # log.debug(f"FLAT: {flattened}")
        pat = re.compile("[0-9.]* [0-9.-]* [0-9.]* [0-9.]*")
        for key, value in flattened.items():
            if key[0] == "@" or value is None:
                continue
            # Get the last element deliminated by a dash
            # for CSV & JSON, or a colon for ODK XML.
            base = basename(key)
            log.debug(f"FLAT: {base} = {value}")
            if base in self.ignore:
                continue
            if re.search(pat, value):
                gps = value.split(" ")
                row["lat"] = gps[0]
                row["lon"] = gps[1]
                continue

            if base in self.types:
                if self.types[base] == "select_multiple":
                    # log.debug(f"Found key '{self.types[base]}'")
                    vals = self.convertMultiple(value)
                    if len(vals) > 0:
                        tags.update(vals)
                    continue
                else:
                    item = self.convertEntry(base, value)
                    if item is None or len(item) == 0:
                        continue
                    if len(tags) == 0:
                        tags = item[0]
                    else:
                        if type(item) == list:
                            # log.debug(f"list Item {item}")
                            tags.update(item[0])
                        elif type(item) == dict:
                            # log.debug(f"dict Item {item}")
                            tags.update(item)
        row.update(tags)
        return [row]
