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

import argparse
import csv
import logging
import os
import re
import sys
from datetime import datetime
from collections import OrderedDict
from pathlib import Path
import xmltodict
from geojson import Feature, FeatureCollection, dump
from osm_fieldwork.osmfile import OsmFile
from osm_fieldwork.xlsforms import xlsforms_path
from osm_fieldwork.ODKInstance import ODKInstance
from osm_fieldwork.support import basename

# Instantiate logger
log = logging.getLogger(__name__)


class ODKParsers(Convert):
    """
    A class to parse the CSV files from ODK Central.
    """
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
        """
        Parse the CSV file from ODK Central and convert it to a data structure.

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
                if keyword is None or len(value) == 0:
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
                                for tag in vals:
                                    tags.update(tag)
                                # print(f"BASE {tags}")
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
        """
        Parse the JSON file from ODK Central and convert it to a data structure.
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
            # Extract the location regardless of what the tag is
            # called.
            # pat = re.compile("[-0-9.]*, [0-9.-]*, [0-9.]*")
            # gps = re.findall(pat, str(row))
            # tmp = list()
            # if len(gps) == 0:
            #     log.error(f"No location data in: {row}")
            #     continue
            # elif len(gps) == 1:
            #     # Only the warmup has any coordinates.
            #     tmp = gps[0].split(" ")
            # elif len(gps) == 2:
            #     # both the warmup and the coordinates have values
            #     tmp = gps[1].split(" ")

            # if len(tmp) > 0:
            #     lat = float(tmp[0][:-1])
            #     lon = float(tmp[1][:-1])
            #     geom = Point([lon, lat])
            #     row["geometry"] = geom
            #     # tags["geometry"] = row["geometry"]

            if "properties" in row:
                row["properties"]  # A GeoJson formatted file
            else:
                pass  # A JOSM file from ODK Central

            # flatten all the groups into a sodk2geojson.pyingle data structure
            flattened = flatdict.FlatDict(row)
            for k, v in flattened.items():
                last = k.rfind(":") + 1
                key = k[last:]
                # a JSON file from ODK Central always uses coordinates as
                # the keyword
                if key is None or key in self.ignore or v is None:
                    continue
                log.debug(f"Processing tag {key} = {v}")
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
                            for tag in vals:
                                tags.update(tag)
                            # print(f"BASE {tags}")
                        continue

                items = self.convertEntry(key, v)
                if items is None or len(items) == 0:
                    continue

                if type(items) == str:
                    log.debug(f"string Item {items}")
                else:
                    log.debug(f"dict Item {items}")
                    if len(items) == 0:
                        tags.update(items[0])
            # log.debug(f"TAGS: {tags}")
            if len(tags) > 0:
                total.append(tags)

        # log.debug(f"Finished parsing JSON file {filespec}")
        return total

from osm_fieldwork.ODKInstance import ODKInstance
from osm_fieldwork.ODKInstance import ODKInstance
