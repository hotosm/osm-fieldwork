#!/usr/bin/python3

# Copyright (c) 2020, 2021, 2022, 2023 Humanitarian OpenStreetMap Team
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

import pandas as pd
from geojson import Feature, FeatureCollection, Point, dump

from osm_fieldwork.convert import Convert
from osm_fieldwork.osmfile import OsmFile
from osm_fieldwork.xlsforms import xlsforms_path

# set log level for urlib
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

    def lastSaved(
        self,
        keyword: str,
    ):
        if keyword is not None and len(keyword) > 0:
            return self.saved[keyword]
        return None

    def updateSaved(
        self,
        keyword: str,
        value: str,
    ):
        if keyword is not None and value is not None and len(value) > 0:
            self.saved[keyword] = value

    def parseXLS(
        self,
        xlsfile: str,
    ):
        """Parse the source XLSFile if available to look for details we need."""
        if xlsfile is not None and len(xlsfile) > 0:
            entries = pd.read_excel(xlsfile, sheet_name=[0])
            # There will only be a single sheet
            names = entries[0]["name"]
            defaults = entries[0]["default"]
            total = len(names)
            i = 0
            while i < total:
                entry = defaults[i]
                if str(entry) != "nan":
                    pat = re.compile("..last-saved.*")
                    if pat.match(entry):
                        name = entry.split("#")[1][:-1]
                        self.saved[name] = None
                    else:
                        self.defaults[names[i]] = entry
                i += 1
        return True

    def createOSM(
        self,
        filespec: str,
    ):
        """Create an OSM XML output files."""
        log.debug("Creating OSM XML file: %s" % filespec)
        self.osm = OsmFile(filespec)
        # self.osm.header()

    def writeOSM(
        self,
        feature: dict,
    ):
        """Write a feature to an OSM XML output file."""
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

    def finishOSM(self):
        """Write the OSM XML file footer and close it."""
        self.osm.footer()

    def createGeoJson(
        self,
        file: str = "tmp.geojson",
    ):
        """Create a GeoJson output file."""
        log.debug("Creating GeoJson file: %s" % file)
        self.json = open(file, "w")

    def writeGeoJson(
        self,
        feature: dict,
    ):
        """Write a feature to a GeoJson output file."""
        # These get written later when finishing , since we have to create a FeatureCollection
        if "lat" not in feature["attrs"] or "lon" not in feature["attrs"]:
            return None
        self.features.append(feature)

    def finishGeoJson(self):
        """Write the GeoJson FeatureCollection to the output file and close it."""
        features = list()
        for item in self.features:
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
        filespec: str,
        data: str = None,
    ):
        """Parse the CSV file from ODK Central and convert it to a data structure."""
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
                if keyword is None or len(keyword) == 0:
                    continue

                base = self.basename(keyword).lower()
                # There's many extraneous fields in the input file which we don't need.
                if base is None or base in self.ignore or value is None:
                    continue
                # if base in self.multiple:
                #     epdb.st()
                #     entry = reader[keyword]
                #     for key, val in entry.items():
                #         print(key)75.66.108.181
                #         if key == "name":
                #             tags['name'] = val
                #     continue
                else:
                    # When using geopoint warmup, once the display changes to the map
                    # location, there is not always a value if the accuracy is way
                    # off. In this case use the warmup value, which is where we are
                    # standing anyway.
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

    def basename(
        self,
        line: str,
    ):
        """Extract the basename of a path after the last -."""
        tmp = line.split("-")
        if len(tmp) == 0:
            return line
        base = tmp[len(tmp) - 1]
        return base

    def createEntry(
        self,
        entry: dict,
    ):
        """Create the feature data structure."""
        # print(line)
        feature = dict()
        attrs = dict()
        tags = dict()
        priv = dict()
        refs = list()

        # log.debug("Creating entry")
        # First convert the tag to the approved OSM equivalent
        if "lat" in entry and "lon" in entry:
            attrs["lat"] = entry["lat"]
            attrs["lon"] = entry["lon"]
        for key, value in entry.items():
            attributes = (
                "id",
                "timestamp",
                "lat",
                "lon",
                "uid",
                "user",
                "version",
                "action",
            )

            # When using existing OSM data, there's a special geometry field.
            # Otherwise use the GPS coordinates where you are.
            if key == "geometry" and len(value) > 0:
                geometry = value.split(" ")
                if len(geometry) == 4:
                    attrs["lat"] = geometry[0]
                    attrs["lon"] = geometry[1]
                continue

            if len(attrs["lat"]) == 0:
                continue
            if key is not None and len(key) > 0 and key in attributes:
                attrs[key] = value
                log.debug("Adding attribute %s with value %s" % (key, value))
            else:
                if key in self.multiple:
                    for item in value:
                        if key in item:
                            for entry in item[key].split():
                                vals = self.getValues(key)
                                if entry in vals:
                                    if vals[entry].find("="):
                                        tmp = vals[entry].split("=")
                                        tags[tmp[0]] = tmp[1]
                                else:
                                    tags[entry] = "yes"
                    continue

                if value is not None and value != "no" and value != "unknown":
                    if key == "track" or key == "geoline":
                        refs.append(tag)
                        log.debug("Adding reference %s" % tag)
                    elif len(value) > 0:
                        if self.privateData(key):
                            priv[key] = value
                        else:
                            tags[key] = value
            if len(tags) > 0:
                feature["attrs"] = attrs
                feature["tags"] = tags
            if len(refs) > 0:
                feature["refs"] = refs
            if len(priv) > 0:
                feature["private"] = priv

        return feature


def main():
    """ """
    parser = argparse.ArgumentParser(description="convert CSV from ODK Central to OSM XML")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-y", "--yaml", help="Alternate YAML file")
    parser.add_argument("-x", "--xlsfile", help="Source XLSFile")
    parser.add_argument("-i", "--infile", required=True, help="The input file downloaded from ODK Central")
    args = parser.parse_args()

    # if verbose, dump to the terminal.
    if args.verbose is not None:
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)

        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        root.addHandler(ch)

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
    for entry in data:
        feature = csvin.createEntry(entry)
        # Sometimes bad entries, usually from debugging XForm design, sneak in
        if len(feature) == 0:
            continue
        if len(feature) > 0:
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
