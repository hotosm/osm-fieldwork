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

import argparse
import csv
import logging
import os
import sys
from datetime import datetime

from osm_fieldwork.convert import Convert
from osm_fieldwork.support import basename
from osm_fieldwork.xlsforms import xlsforms_path

# Instantiate logger
log = logging.getLogger(__name__)


class CSVDump(Convert):
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

    def parse(
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


def main():
    """Run conversion directly from the terminal."""
    parser = argparse.ArgumentParser(description="convert CSV from ODK Central to OSM XML")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-y", "--yaml", help="Alternate YAML file")
    parser.add_argument("-x", "--xlsfile", help="Source XLSFile")
    parser.add_argument("-i", "--infile", required=True, help="The input file downloaded from ODK Central")
    args = parser.parse_args()

    # if verbose, dump to the terminal.
    if args.verbose is not None:
        logging.basicConfig(
            level=logging.DEBUG,
            format=("%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            datefmt="%y-%m-%d %H:%M:%S",
            stream=sys.stdout,
        )
        logging.getLogger("urllib3").setLevel(logging.DEBUG)

    if args.yaml:
        csvin = CSVDump(args.yaml)
    else:
        csvin = CSVDump()

    csvin.parseXLS(args.xlsfile)
    osmoutfile = os.path.basename(args.infile.replace(".csv", ".osm"))
    csvin.createOSM(osmoutfile)

    jsonoutfile = os.path.basename(args.infile.replace(".csv", ".geojson"))
    csvin.createGeoJson(jsonoutfile)

    log.debug("Parsing csv files %r" % args.infile)
    data = csvin.parse(args.infile)
    # This OSM XML file only has OSM appropriate tags and values
    nodeid = -1000
    for entry in data:
        feature = csvin.createEntry(entry)
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
                csvin.writeOSM(node)
                refs.append(nodeid)
                nodeid -= 1

            feature["refs"] = refs
            csvin.writeOSM(feature)
        else:
            # Sometimes bad entries, usually from debugging XForm design, sneak in
            if "lat" not in feature["attrs"]:
                log.warning("Bad record! %r" % feature)
                continue
            csvin.writeOSM(feature)
            # This GeoJson file has all the data values
            csvin.writeGeoJson(feature)
            # print("TAGS: %r" % feature['tags'])

    csvin.finishOSM()
    csvin.finishGeoJson()
    log.info("Wrote OSM XML file: %r" % osmoutfile)
    log.info("Wrote GeoJson file: %r" % jsonoutfile)


if __name__ == "__main__":
    """This is just a hook so this file can be run standlone during development."""
    main()
