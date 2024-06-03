#!/usr/bin/python3

# Copyright (c) 2023, 2024 Humanitarian OpenStreetMap Team
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
import json
import logging

# import pandas as pd
import sys
from pathlib import Path

import flatdict
import geojson
from geojson import Feature, FeatureCollection, Point, dump

from osm_fieldwork.convert import Convert
from osm_fieldwork.osmfile import OsmFile

log = logging.getLogger(__name__)


class JsonDump(Convert):
    """A class to parse the JSON files from ODK Central or odk2geojson."""

    def __init__(
        self,
        yaml: str = None,
    ):
        """A class to convert the JSON file from ODK Central, or the GeoJson
        file created by the odk2geojson utility.

        Args:
            yaml (str): The filespec of the YAML config file

        Returns:
            (JsonDump): An instance of this object
        """
        self.fields = dict()
        self.nodesets = dict()
        self.data = list()
        self.osm = None
        self.json = None
        self.features = list()
        self.config = super().__init__(yaml)

    def createOSM(
        self,
        filespec: str = "tmp.osm",
    ) -> OsmFile:
        """Create an OSM XML output files.

        Args:
            filespec (str): The filespec for the output OSM XML file

        Returns:
            (OsmFile): An instance of the OSM XML output file
        """
        log.debug(f"Creating OSM XML file: {filespec}")
        self.osm = OsmFile(filespec)
        return self.osm

    def writeOSM(
        self,
        feature: dict,
    ):
        """Write a feature to an OSM XML output file.

        Args:
            feature (dict): The feature to write to the OSM XML output file
        """
        out = ""
        if "id" in feature["tags"]:
            feature["id"] = feature["tags"]["id"]
        if "lat" not in feature["attrs"] or "lon" not in feature["attrs"]:
            return None
        if "user" in feature["tags"] and "user" not in feature["attrs"]:
            feature["attrs"]["user"] = feature["tags"]["user"]
            del feature["tags"]["user"]
        if "uid" in feature["tags"] and "uid" not in ["attrs"]:
            feature["attrs"]["uid"] = feature["tags"]["uid"]
            del feature["tags"]["uid"]
        if "refs" not in feature:
            out += self.osm.createNode(feature, True)
        else:
            out += self.osm.createWay(feature, True)
        self.osm.write(out)

    def finishOSM(self):
        """Write the OSM XML file footer and close it. The destructor in the
        OsmFile class should do this, but this is the manual way.
        """
        self.osm.footer()

    def createGeoJson(
        self,
        file="tmp.geojson",
    ):
        """Create a GeoJson output file.

        Args:
            file (str): The filespec of the output GeoJson file
        """
        log.debug("Creating GeoJson file: %s" % file)
        self.json = open(file, "w")

    def writeGeoJson(
        self,
        feature: dict,
    ):
        """Write a feature to a GeoJson output file.

        Args:
            feature (dict): The feature to write to the GeoJson output file
        """
        # These get written later when finishing , since we have to create a FeatureCollection
        if "lat" not in feature["attrs"] or "lon" not in feature["attrs"]:
            return None
        self.features.append(feature)

    def finishGeoJson(self):
        """Write the GeoJson FeatureCollection to the output file and close it."""
        features = list()
        for item in self.features:
            # poi = Point()
            poi = Point((float(item["attrs"]["lon"]), float(item["attrs"]["lat"])))
            if "private" in item:
                props = {**item["tags"], **item["private"]}
            else:
                props = item["tags"]
            features.append(Feature(geometry=poi, properties=props))
        collection = FeatureCollection(features)
        dump(collection, self.json)

    def parse(
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


# def json2osm(
#         cmdln: dict,
# ) -> str:
#     """
#     Process the JSON file from ODK Central or the GeoJSON file to OSM XML format.

#     Args:
#         cmdln (dict): The data from the command line

#     Returns:
#         osmoutfile (str): Path to the converted OSM XML file.
#     """
#     log.info(f"Converting JSON file to OSM: {cmdln['infile']}")
#     if yaml_file:
#         jsonin = JsonDump({cmd['yaml']})
#     else:
#         jsonin = JsonDump()

#     # Modify the input file name for the 2 output files, which will get written
#     # to the current directory.

#     base = Path(input_file).stem
#     osmoutfile = f"{base}-out.osm"
#     jsonin.createOSM(osmoutfile)

#     data = jsonin.parse(input_file)
#     # This OSM XML file only has OSM appropriate tags and values

#     for entry in data:
#         feature = jsonin.createEntry(entry)

#         # Sometimes bad entries, usually from debugging XForm design, sneak in
#         if len(feature) == 0:
#             continue

#         if len(feature) > 0:
#             if "lat" not in feature["attrs"]:
#                 if "geometry" in feature["tags"]:
#                     if isinstance(feature["tags"]["geometry"], str):
#                         coords = list(feature["tags"]["geometry"])
#                         # del feature['tags']['geometry']
#                 elif "coordinates" in feature["tags"]:
#                     coords = feature["tags"]["coordinates"]
#                     feature["attrs"] = {"lat": coords[1], "lon": coords[0]}
#                 else:
#                     log.warning(f"Bad record! {feature}")
#                     continue  # Skip bad records

#             jsonin.writeOSM(feature)
#     # log.debug("Writing final OSM XML file...")

#     # jsonin.finishOSM()
#     log.info(f"Wrote OSM XML file: {osmoutfile}")

#     return osmoutfile


def main():
    """Run conversion directly from the terminal."""
    parser = argparse.ArgumentParser(description="convert JSON from ODK Central to OSM XML")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-y", "--yaml", help="Alternate YAML file")
    parser.add_argument("-x", "--xlsfile", help="Source XLSFile")
    parser.add_argument("-i", "--infile", required=True, help="The input file downloaded from ODK Central")
    args = parser.parse_args()

    # if verbose, dump to the terminal.
    if args.verbose is not None:
        logging.basicConfig(
            level=logging.DEBUG,
            format=("%(threadName)10s - %(name)s - %(levelname)s - %(message)s"),
            datefmt="%y-%m-%d %H:%M:%S",
            stream=sys.stdout,
        )
        logging.getLogger("urllib3").setLevel(logging.DEBUG)

    if args.yaml:
        jsonvin = JsonDump(args.yaml)
    else:
        jsonin = JsonDump()

    jsonin.parseXLS(args.xlsfile)

    base = Path(args.infile).stem
    osmoutfile = f"{base}.osm"
    jsonin.createOSM(osmoutfile)

    jsonoutfile = f"{base}.geojson"
    jsonin.createGeoJson(jsonoutfile)

    log.debug("Parsing json files %r" % args.infile)
    data = jsonin.parse(args.infile)
    # This OSM XML file only has OSM appropriate tags and values
    nodeid = -1000
    for entry in data:
        feature = jsonin.createEntry(entry)
        if len(feature) == 0:
            continue
        if "refs" in feature:
            refs = list()
            for ref in feature["refs"]:
                now = datetime.now().strftime("%Y-%m-%dT%TZ")
                if len(ref) == 0:
                    continue
                coords = ref.split(" ")
                print(coords)
                node = {"attrs": {"id": nodeid, "version": 1, "timestamp": now, "lat": coords[0], "lon": coords[1]}, "tags": dict()}
                jsonin.writeOSM(node)
                refs.append(nodeid)
                nodeid -= 1

            feature["refs"] = refs
            jsonin.writeOSM(feature)
        else:
            # Sometimes bad entries, usually from debugging XForm design, sneak in
            if "lat" not in feature["attrs"]:
                log.warning("Bad record! %r" % feature)
                continue
            jsonin.writeOSM(feature)
            # This GeoJson file has all the data values
            jsonin.writeGeoJson(feature)
            # print("TAGS: %r" % feature['tags'])

    jsonin.finishOSM()
    jsonin.finishGeoJson()
    log.info("Wrote OSM XML file: %r" % osmoutfile)
    log.info("Wrote GeoJson file: %r" % jsonoutfile)


if __name__ == "__main__":
    """This is just a hook so this file can be run standlone during development."""
    main()
