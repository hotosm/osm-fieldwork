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
from pathlib import Path

from geojson import Feature, FeatureCollection, Point, dump

from osm_fieldwork.osmfile import OsmFile

# Instantiate logger
log = logging.getLogger(__name__)


def basename(
    line: str,
) -> str:
    """Extract the basename of a path after the last -.

    Args:
        line (str): The path from the json file entry

    Returns:
        (str): The last node of the path
    """
    if line.find("-") > 0:
        tmp = line.split("-")
        if len(tmp) > 0:
            return tmp[len(tmp) - 1]
    elif line.find(":") > 0:
        tmp = line.split(":")
        if len(tmp) > 0:
            return tmp[len(tmp) - 1]
    else:
        # return tmp[len(tmp) - 1]
        return line


class OutSupport(object):
    def __init__(
        self,
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
        """Create an OSM XML output files.

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
        """Write a feature to an OSM XML output file.

        Args:
            feature (dict): The OSM feature to write to
        """
        out = ""
        if "tags" in feature:
            if "id" in feature["tags"]:
                feature["id"] = feature["tags"]["id"]
        else:
            return True
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
        """Create a GeoJson output file.

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
        """Write a feature to a GeoJson output file.

        Args:
            feature (dict): The OSM feature to write to
        """
        # These get written later when finishing , since we have to create a FeatureCollection
        if "lat" not in feature["attrs"] or "lon" not in feature["attrs"]:
            return None
        self.features.append(feature)

        return True

    def finishGeoJson(self):
        """Write the GeoJson FeatureCollection to the output file and close it."""
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

    def WriteData(
        self,
        base: str,
        data: dict(),
    ) -> bool:
        """Write the data to the output files.

        Args:
            base (str): The base of the input file name
            data (dict): The data to write

        Returns:
            (bool): Whether the data got written
        """
        osmoutfile = f"{base}.osm"
        self.createOSM(osmoutfile)

        jsonoutfile = f"{base}.geojson"
        self.createGeoJson(jsonoutfile)

        nodeid = -1000
        for feature in data:
            if len(feature) == 0:
                continue
            if "refs" in feature:
                # it's a way
                refs = list()
                for ref in feature["refs"]:
                    now = datetime.now().strftime("%Y-%m-%dT%TZ")
                    if len(ref) == 0:
                        continue
                    coords = ref.split(" ")
                    node = {
                        "attrs": {"id": nodeid, "version": 1, "timestamp": now, "lat": coords[0], "lon": coords[1]},
                        "tags": dict(),
                    }
                    self.writeOSM(node)
                    self.writeGeoJson(node)
                    refs.append(nodeid)
                    nodeid -= 1
                feature["refs"] = refs
            else:
                # it's a node
                if "lat" not in feature["attrs"]:
                    # Sometimes bad entries, usually from debugging XForm design, sneak in
                    log.warning("Bad record! %r" % feature)
                    continue
            self.writeOSM(feature)

        self.finishOSM()
        log.info("Wrote OSM XML file: %r" % osmoutfile)
        self.finishGeoJson()
        log.info("Wrote GeoJson file: %r" % jsonoutfile)

        return True
