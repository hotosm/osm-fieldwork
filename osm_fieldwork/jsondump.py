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

from osm_fieldwork.convert import Convert

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
