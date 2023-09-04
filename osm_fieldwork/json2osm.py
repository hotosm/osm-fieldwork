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
import geojson
from sys import argv
from osm_fieldwork.convert import Convert, escape
from osm_fieldwork.osmfile import OsmFile
from osm_fieldwork.xlsforms import xlsforms_path
from geojson import Point, Feature, FeatureCollection, dump
from pathlib import Path
#import pandas as pd
import math
import re
import flatdict


# set log level for urlib
log = logging.getLogger(__name__)

class JsonDump(Convert):
    """A class to parse the JSON files from ODK Central or odk2geojson"""
    def __init__(self,
                 yaml: str = None,
                 ):
        """
        A class to convert the JSON file from ODK Central, or the GeoJson
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

    # FIXME: a work in progress
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
                  filespec: str = "tmp.osm",
                  ):
        """
        Create an OSM XML output files

        Args:
            filespec (str): The filespec for the output OSM XML file

        Returns:
            (OsmFile): An instance of the OSM XML output file
        """
        log.debug("Creating OSM XML file: %s" % filespec)
        self.osm = OsmFile(filespec)
        return self.osm

    def writeOSM(self,
                 feature: dict,
                 ):
        """
        Write a feature to an OSM XML output file

        Args:
            feature (dict): The feature to write to the OSM XML output file
        """
        out = ""
        if "id" in feature["tags"]:
            feature["id"] = feature["tags"]["id"]
        if "lat" not in feature["attrs"] or "lon" not in feature["attrs"]:
            return None
        if 'user' in feature['tags'] and 'user' not in feature["attrs"]:
            feature["attrs"]['user'] = feature['tags']['user']
            del feature['tags']['user']
        if 'uid' in feature['tags'] and 'uid' not in ["attrs"]:
            feature["attrs"]['uid'] = feature['tags']['uid']
            del feature['tags']['uid']
        if "refs" not in feature:
            out += self.osm.createNode(feature, True)
        else:
            out += self.osm.createWay(feature, True)
        self.osm.write(out)

    def finishOSM(self):
        """
        Write the OSM XML file footer and close it. The destructor in the
        OsmFile class should do this, but this is the manual way.
        """
        self.osm.footer()

    def createGeoJson(self,
                      file="tmp.geojson",
                      ):
        """
        Create a GeoJson output file

        Args:
                file (str): The filespec of the output GeoJson file
        """
        log.debug("Creating GeoJson file: %s" % file)
        self.json = open(file, "w")

    def writeGeoJson(self,
                     feature: dict,
                     ):
        """
        Write a feature to a GeoJson output file

        Args:
            feature (dict): The feature to write to the GeoJson output file
        """
        # These get written later when finishing , since we have to create a FeatureCollection
        if "lat" not in feature["attrs"] or "lon" not in feature["attrs"]:
            return None
        self.features.append(feature)

    def finishGeoJson(self):
        """
        Write the GeoJson FeatureCollection to the output file and close it.
        """
        features = list()
        for item in self.features:
            #poi = Point()
            poi = Point((float(item["attrs"]["lon"]), float(item["attrs"]["lat"])))
            if "private" in item:
                props = {**item["tags"], **item["private"]}
            else:
                props = item["tags"]
            features.append(Feature(geometry=poi, properties=props))
        collection = FeatureCollection(features)
        dump(collection, self.json)

    def parse(self,
              filespec: str = None,
              data: str = None,
              ):
        """
        Parse the JSON file from ODK Central and convert it to a data structure.
        The input is either a filespec to open, or the data itself.

        Args:
            filespec (str): The JSON or GeoJson input file to convert
            data (str): The data to convert

        Returns:
            (list): A list of all the features in the input file
        """
        all_tags = list()
        if not data:
            file = open(filespec, "r")
            infile = Path(filespec)
            if infile.suffix == ".geojson":
                reader = geojson.load(file)
            elif infile.suffix == ".json":
                reader = json.load(file)
            else:
                log.error("Need to specify a JSON or GeoJson file!")
                return all_tags
        elif type(data) == str:
            reader = geojson.loads(data)
        elif type(data) == list:
            reader = data
        
        total = list()
        # JSON files from Central use value as the keyword, whereas
        # GeoJSON uses features for the same thing.
        if 'value' in reader:
            data = reader['value']
        elif 'features' in reader:
            data = reader['features']
        else:
            data = reader
        for row in data:
            # log.info(f"ROW: {row}")
            tags = dict()
            if 'geometry' in row:
                tags['geometry'] = row['geometry']
            else:
                pat = re.compile("[-0-9.]*, [0-9.-]*, [0-9.]*")
                gps = re.findall(pat, str(row))
                # If geopoint warmup is used, there will be two matches, we only
                # want the second one, which is the location.
                for coords in gps:
                    tags['geometry'] = coords
            if 'properties' in row:
                indata = row['properties'] # A GeoJson formatted file
            else:
                indata = row    # A JOSM file from ODK Central

            # flatten all the groups into a single data structure
            flattened = flatdict.FlatDict(row)
            for k, v in flattened.items():
                last = k.rfind(':') + 1
                key = k[last:]
                # log.debug(f"Processing tag {key} = {v}")
                # names and comments may have spaces, otherwise
                # it's from a select_multiple
                pat = re.compile("name[:a-z]*")
                names = re.findall(pat, key)
                if len(names) > 0:
                    for name in names:
                        tags[name] = v
                    continue
                if key == 'comment':
                    tags[key] = v
                # a JSON file from ODK Central always uses coordinates as
                # the keyword
                if key == 'coordinates':
                    if type(v) == list:
                        lat = v[1]
                        lon = v[0]
                        tags['geometry'] = f"{lat} {lon}"
                    continue
                tags[key] = v
            total.append(tags)
        return total

    def createEntry(self,
                    entry: dict,
                    ):
        """
        Create the feature data structure for this entry.

        Args:
            entry (dict): The feature to convert to the output format

        Returns:
            (dict): The new entry for the output file
        """
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
            lat = None
            lon = None
            if type(value) == float:
                continue
            # log.debug(f"FIXME: {key} = {value} {type(value)}")
            if key == "xid" and value is not None:
                attrs['id'] = int(value)
            if key == "geometry":
                # The GeoJson file has the geometry field. Usually it's a dict
                # but on occasion it's a string instead, so turn it into a list
                if type(value) == str:
                    if value[0] ==  '[':
                        coords = eval(value)
                        lat = coords[1]
                        lon = coords[0]
                    else:
                        coords = value.split(' ')
                        lat = coords[0]
                        lon = coords[1]
                    # log.debug(f"VALUE STRING: {coords}")
                elif type(value) == geojson.geometry.Point:
                    lat = value['coordinates'][1]
                    lon = value['coordinates'][0]
                    # log.debug(f"VALUE POINT: {lat}/{lon}")
                elif type(value) == list:
                    lat = float(value[1])
                    lon = float(value[0])
                attrs["lat"] = lat
                attrs["lon"] = lon
                # log.debug(f"ATTRS: {attrs}")

            # Some tags are actually attributes
            # print(f"FIXME: {key} {key in attributes}")
            # if key in self.multiple:
            #     for item in value:
            #         if key in item:
            #             for entry in item[key].split():
            #                 vals = self.getValues(key)
            #                 if entry in vals:
            #                     if vals[entry].find("="):
            #                         tmp = vals[entry].split("=")
            #                         tags[tmp[0]] = tmp[1]
            #                 else:
            #                     tags[entry] = "yes"
            #     continue

            if value is not None and value != "no" and value != "unknown":
                if key == "track" or key == "geoline":
                    refs.append(tag)
                    log.debug("Adding reference %s" % tag)
                elif len(str(value)) > 0:
                    if self.privateData(key):
                        priv[key] = value
                    else:
                        item = self.convertEntry(key, value)
                        if item is not None and type(item) == dict:
                            tags.update(item)
                        elif type(item) == list:
                            for entry in item:
                                tags.update(entry)

            if len(tags) > 0:
                if 'geometry' in tags:
                    del tags['geometry']
                feature["attrs"] = attrs
                feature["tags"] = tags
            if len(refs) > 0:
                feature["refs"] = refs
            if len(priv) > 0:
                feature["private"] = priv

        return feature

def json2osm(input_file, yaml_file=None):
    """
    Process the JSON file from ODK Central or the GeoJSON file to OSM XML format.

    Args:
        input_file (str): The path to the input JSON or GeoJSON file.
        yaml_file (str): The path to the YAML config file (optional).

    Returns:
        osmoutfile (str): Path to the converted OSM XML file.
    """
    if yaml_file:
        jsonin = JsonDump(yaml_file)
    else:
        jsonin = JsonDump()

    # jsonin.parseXLS(args.xlsfile)

    # Modify the input file name for the 2 output files, which will get written
    # to the current directory.

    base = Path(input_file).stem
    osmoutfile = f"{base}-out.osm"
    log.debug(f"Creating OSM XML file: {osmoutfile}")
    jsonin.createOSM(osmoutfile)

    log.debug(f"Parsing JSON file {args.infile}")
    data = jsonin.parse(input_file.as_posix())
    # This OSM XML file only has OSM appropriate tags and values

    for entry in data:
        feature = jsonin.createEntry(entry)

        # Sometimes bad entries, usually from debugging XForm design, sneak in
        if len(feature) == 0:
            continue

        if len(feature) > 0:
            if "lat" not in feature["attrs"]:
                if 'geometry' in feature['tags']:
                    if type(feature['tags']['geometry']) == str:
                        coords = list(feature['tags']['geometry'])
                        # del feature['tags']['geometry']
                elif 'coordinates' in feature['tags']:
                    coords = feature['tags']['coordinates']
                    feature['attrs'] = {'lat': coords[1], 'lon': coords[0]}
                else:
                    log.warning(f"Bad record! {feature}")
                    continue  # Skip bad records

            log.debug("Writing final OSM XML file...")
            jsonin.writeOSM(feature)

    jsonin.finishOSM()
    log.info(f"Wrote OSM XML file: {osmoutfile}")

    return osmoutfile


def main():
    """Run conversion directly from the terminal."""
    parser = argparse.ArgumentParser(
        description="convert JSON from ODK Central to OSM XML"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-y", "--yaml", help="Alternate YAML file")
    parser.add_argument("-x", "--xlsfile", help="Source XLSFile")
    parser.add_argument("-i", "--infile", required=True,
        help="The input file downloaded from ODK Central"
    )
    args = parser.parse_args()

    # if verbose, dump to the terminal.
    if args.verbose is not None:
        log.setLevel(logging.DEBUG)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(threadName)10s - %(name)s - %(levelname)s - %(message)s"
        )
        ch.setFormatter(formatter)
        log.addHandler(ch) 

    json2osm(args.infile, args.yaml)

if __name__ == "__main__":
    """This is just a hook so this file can be run standlone during development."""
    main()
