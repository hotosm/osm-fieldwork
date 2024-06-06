#!/usr/bin/python3

# Copyright (c) 2020, 2021, 2022, 2023, 2024 Humanitarian OpenStreetMap Team
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

import logging
from datetime import datetime
from geojson import Feature, FeatureCollection, Point, dump
from osm_fieldwork.osmfile import OsmFile
from osm_fieldwork.xlsforms import xlsforms_path
from pathlib import Path

# Instantiate logger
log = logging.getLogger(__name__)

class OutSupport(object):
    def __init__(self,
               filespec: str = None,
               ):
        self.osm = None
        self.filespec = filespec
        self.features = list()
        if filespec:
            path = Path(filespec)
            if path.suffix == ".osm":
                self.createOSM(filespec)
            elif path.suffix == ".geojson":
                self.createGeoJson(filespec)
            else:
                log.error(f"{filespec} is not a valid file!")

    def createOSM(
        self,
        filespec: str = None,
    ) -> bool:
        """
        Create an OSM XML output files.

        Args:
            filespec (str): The output file name
        """
        if filespec is not None:
            log.debug("Creating OSM XML file: %s" % filespec)
            self.osm = OsmFile(filespec)
        elif self.filespec is not None:
            log.debug("Creating OSM XML file: %s" % self.filespec)
            self.osm = OsmFile(self.filespec)

        return True

    def writeOSM(
        self,
        feature: dict,
    ) -> bool:
        """
        Write a feature to an OSM XML output file.

        Args:
            feature (dict): The OSM feature to write to
        """
        out = ""
        if "id" in feature["tags"]:
            feature["id"] = feature["tags"]["id"]
        if "lat" not in feature["attrs"] or "lon" not in feature["attrs"]:
            return None
        if "refs" not in feature:
            out += self.osm.createNode(feature)
        else:
            out += self.osm.createWay(feature)
        self.osm.write(out)

        return True

    def finishOSM(self):
        """Write the OSM XML file footer and close it."""
        # This is now handled by a destructor in the OsmFile class
        # self.osm.footer()

    def createGeoJson(
        self,
        filespec: str = "tmp.geojson",
    ) -> bool:
        """
        Create a GeoJson output file.

        Args:
            filespec (str): The output file name
        """
        log.debug("Creating GeoJson file: %s" % filespec)
        self.json = open(filespec, "w")

        return True

    def writeGeoJson(
        self,
        feature: dict,
    ) -> bool:
        """
        Write a feature to a GeoJson output file.

        Args:
            feature (dict): The OSM feature to write to
        """
        # These get written later when finishing , since we have to create a FeatureCollection
        if "lat" not in feature["attrs"] or "lon" not in feature["attrs"]:
            return None
        self.features.append(feature)

        return True

    def finishGeoJson(self):
        """
        Write the GeoJson FeatureCollection to the output file and close it.
        """
        features = list()
        for item in self.features:
            if len(item["attrs"]["lon"]) == 0 or len(item["attrs"]["lat"]) == 0:
                log.warning("Bad location data in entry! %r", item["attrs"])
                continue
            poi = Point((float(item["attrs"]["lon"]), float(item["attrs"]["lat"])))
            if "private" in item:
                props = {**item["tags"], **item["private"]}
            else:
                props = item["tags"]
            features.append(Feature(geometry=poi, properties=props))
        collection = FeatureCollection(features)
        dump(collection, self.json)
