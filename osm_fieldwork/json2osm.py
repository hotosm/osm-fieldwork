#!/usr/bin/python3

# Copyright (c) 2023 Humanitarian OpenStreetMap Team
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
import os
import logging
import sys
import json
from sys import argv
from osm_fieldwork.convert import Convert
from osm_fieldwork.osmfile import OsmFile
from osm_fieldwork.xlsforms import xlsforms_path
from geojson import Point, Feature, FeatureCollection, dump
#import pandas as pd
#import re

# set log level for urlib
log = logging.getLogger(__name__)

class JsonDump(Convert):
    """A class to parse the CSV files from ODK Central"""

    def __init__(self,
                 yaml: str = None
                 ):
        self.fields = dict()
        self.nodesets = dict()
        self.data = list()
        self.osm = None
        self.json = None
        self.features = list()
        path = xlsforms_path.replace("xlsforms", "")
        if yaml:
            file = f"{path}{yaml}"
        else:
            file = f"{path}/xforms.yaml"
        self.config = super().__init__(yaml)

    # def parseXLS(self, xlsfile: str):
    #     """Parse the source XLSFile if available to look for details we need"""
    #     if xlsfile is not None and len(xlsfile) > 0:
    #         entries = pd.read_excel(xlsfile, sheet_name=[0])
    #         # There will only be a single sheet
    #         names = entries[0]['name']
    #         defaults = entries[0]['default']
    #         total = len(names)
    #         i = 0
    #         while i < total:
    #             entry = defaults[i]
    #             if str(entry) != 'nan':
    #                 pat = re.compile("..last-saved.*")
    #                 if pat.match(entry):
    #                     name = entry.split('#')[1][:-1]
    #                     self.saved[name] = None
    #                 else:
    #                     self.defaults[names[i]] = entry
    #             i += 1
    #     return True

    def createOSM(self,
                  filespec: str = "tmp.osm"
                  ):
        """Create an OSM XML output files"""
        log.debug("Creating OSM XML file: %s" % filespec)
        self.osm = OsmFile(filespec)
        #self.osm.header()
    def writeOSM(self,
                 feature: dict
                 ):
        """Write a feature to an OSM XML output file"""
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
        """Write the OSM XML file footer and close it"""
        self.osm.footer()

    def createGeoJson(self, file="tmp.geojson"):
        """Create a GeoJson output file"""
        log.debug("Creating GeoJson file: %s" % file)
        self.json = open(file, "w")

    def writeGeoJson(self,
                     feature: dict
                     ):
        """Write a feature to a GeoJson output file"""
        # These get written later when finishing , since we have to create a FeatureCollection
        if "lat" not in feature["attrs"] or "lon" not in feature["attrs"]:
            return None
        self.features.append(feature)

    def finishGeoJson(self):
        """Write the GeoJson FeatureCollection to the output file and close it"""
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

    def getAllTags(self,
                   data
                   ):
        all_tags = dict()
        tags = dict()
        if type(data) == str:
            return data
        elif type(data) == dict:
            for k, v in data.items():
                if type(v) == dict:
                    log.info(f"Processing tag {k} = {v}")
                    for k1, v1 in v.items():
                        # tags.update(self.getAllTags(v))
                        if type(v1) == dict:
                            for i, j in v1.items():
                                if type(j) == dict:
                                    # FIXME: this should handle more than one
                                    # but so far I've only it be accuracy, no other
                                    # tags
                                    k2 = list(j.keys())[0]
                                    tags[k2] = list(j.values())[0]
                                else:
                                    tags[i] = j
                        else:
                            tags[k1] = v1
                    log.debug(f"TAGS: {tags}")
                else:
                    if v:
                        # if k in self.saved:
                        #     if str(v) == 'nan' or len(v) == 0:
                        #         log.debug(f"FIXME: {k} {v}")
                        #         val = self.saved[k]
                        #         if val and len(v) == 0:
                        #             log.warning(f"Using last saved value for \"{k}\"! Now \"{val}\"" )
                        #             value = val
                        #         else:
                        #             self.saved[k] = value
                        #             log.debug(f"Updating last saved value for \"{k}\" with \"{value}\"")
                        if type(v) == float:
                            tags[k] = str(v)
                        else:
                            tags[k] = v
                all_tags.update(tags)
        return all_tags

    def parse(self,
              filespec: str,
              data: str = None
              ):
        """Parse the JSON file from ODK Central and convert it to a data structure"""
        all_tags = list()
        if not data:
            f = open(filespec, newline="")
            reader = json.load(f)
        else:
            reader = json.loads(data)
        
        total = list()
        for row in reader['value']:
            # log.info(f"ROW: {row}")
            tags = dict()
            for keyword, value in row.items():
                # There's many extraneous fields in the input file which we don't need.
                base = keyword.lower()
                if (
                    base is None
                    or base in self.ignore
                    or value is None
                    or len(value) == 0
                ):
                    continue
                if keyword is None or len(keyword) == 0:
                    continue
                alltags = self.getAllTags(value)
                print(f"FIXME3: {alltags}")
                for k, v in alltags.items():
                    if k in self.ignore:
                        continue
                    if v:
                        items = dict()
                        if type(v) == dict:
                            v1 = alltags[k]
                            if len(v1) > 1:
                                log.warning("Got more than 1 result! {v1}")
                                v2 = v1[v1.keys()]
                                items = self.convertEntry(k, v2)
                        else:
                            items = self.convertEntry(k, v)
                        #    for entry in items:
                        #        for k, v in entry.items():
                        #            tags[k] = v
                        #    else:
                        #tags[k1] = v1
                        tags.update(items)
            log.debug(f"\tFIXME1: {tags}")
            total.append(tags)
        return total

    def createEntry(self,
                    entry: dict
                    ):
        """Create the feature data structure"""
        # print(line)
        feature = dict()
        attrs = dict()
        tags = dict()
        priv = dict()
        refs = list()

        # log.debug("Creating entry")
        # First convert the tag to the approved OSM equivalent
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
            if key == "geometry":
                if value and len(value) == 3:
                    attrs["lat"] = value[1]
                    attrs["lon"] = value[0]
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
                    elif len(str(value)) > 0:
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="convert CSV from ODK Central to OSM XML"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-y", "--yaml", help="Alternate YAML file")
    parser.add_argument("-x", "--xlsfile", help="Source XLSFile")
    parser.add_argument(
        "-i", "--infile", help="The input file downloaded from ODK Central"
    )
    args = parser.parse_args()
    
    # if verbose, dump to the terminal.
    if args.verbose is not None:
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)

        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        ch.setFormatter(formatter)
        root.addHandler(ch)

    if args.yaml:
        jsonin = JsonDump(args.yaml)
    else:
        jsonin = JsonDump()
    # jsonin.parseXLS(args.xlsfile)    
    osmoutfile = os.path.basename(args.infile.replace(".json", ".osm"))
    jsonin.createOSM(osmoutfile)

    jsonoutfile = os.path.basename(args.infile.replace(".json", ".geojson"))
    jsonin.createGeoJson(jsonoutfile)

    log.debug("Parsing csv files %r" % args.infile)
    data = jsonin.parse(args.infile)
    # This OSM XML file only has OSM appropriate tags and values
    for entry in data:
        feature = jsonin.createEntry(entry)
        # Sometimes bad entries, usually from debugging XForm design, sneak in
        if len(feature) == 0:
            continue
        if len(feature) > 0:
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
