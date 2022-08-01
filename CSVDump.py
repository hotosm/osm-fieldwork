#!/usr/bin/python3

# Copyright (c) 2020, 2021, 2022 Humanitarian OpenStreetMap Team
#
# This file is part of Odkconvert.
#
#     Odkconvert is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Odkconvert is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Odkconvert.  If not, see <https:#www.gnu.org/licenses/>.
#

import argparse
import csv
import os
import logging
import sys
from sys import argv
from convert import Convert
from osmfile import OsmFile
from geojson import Point, Feature, FeatureCollection, dump


class CSVDump(object):
    """A class to parse the CSV files from ODK Central"""
    def __init__(self):
        self.fields = dict()
        self.nodesets = dict()
        self.data = list()
        self.osm = None
        self.json = None
        self.features = list()
        if argv[0][0] == "/" and os.path.dirname(argv[0]) != "/usr/local/bin":
            self.convert = Convert(os.path.dirname(argv[0]) + "/xforms.yaml")
        else:
            if os.path.exists("xforms.yaml"):
                self.convert = Convert("xforms.yaml")
            else:
                self.convert = Convert("../xforms.yaml")
        self.ignore = self.convert.yaml.yaml['ignore']
        self.private = self.convert.yaml.yaml['private']

    def createOSM(self, file="tmp.osm"):
        logging.debug("Creating OSM XML file: %s" % file)
        self.osm = OsmFile(filespec=file)
        self.osm.header()

    def writeOSM(self, feature):
        out = ""
        if 'refs' not in feature:
            out += self.osm.createNode(feature)
        else:
            out += self.osm.createWay(feature)
        self.osm.write(out)

    def finishOSM(self):
        self.osm.footer()

    def privateData(self, keyword):
        return keyword in self.private

    def createGeoJson(self, file="tmp.geojson"):
        logging.debug("Creating GeoJson file: %s" % file)
        self.json = open(file, 'w')

    def writeGeoJson(self, feature):
        # These written later when finishing , since we have to create a FeatureCollection
        self.features.append(feature)

    def finishGeoJson(self):
        features = list()
        for item in self.features:
            poi = Point((float(item['attrs']['lon']), float(item['attrs']['lat'])))
            if 'private' in item:
                props = {**item['tags'], **item['private']}
            else:
                props = item['tags']
            features.append(Feature(geometry=poi, properties=props))
        collection = FeatureCollection(features)
        dump(collection, self.json)

    def parse(self, file):
        all = list()
        logging.debug("Parsing csv files %r" % file)
        with open(file, newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')
            for row in reader:
                tags = dict()
                print(row)
                for keyword, value in row.items():
                    if keyword is None or len(keyword) == 0:
                        continue
                    base = self.basename(keyword).lower()
                    # There's many extraneous fields in the input file which we don't need.
                    if base is None or base in self.ignore or value is None:
                        continue
                    selection = value.split(' ')
                    if len(selection) > 1:
                        for item in selection:
                            tags[item] = "yes"
                        continue
                    else:
                        key = self.convert.convertTag(base)
                        tmp = key.split('=')
                        if len(tmp) == 1:
                            tags[key] = self.convert.escape(value)
                        else:
                            tags[tmp[0]] = tmp[1]
                all.append(tags)
        return all

    def basename(self, line):
        tmp = line.split('-')
        if len(tmp) == 0:
            return line
        base = tmp[len(tmp)-1]
        return base

    def createEntry(self, entry=None):
        # print(line)
        feature = dict()
        attrs = dict()
        tags = dict()
        priv = dict()
        refs = list()

        logging.debug("Creating entry")
        # First convert the tag to the approved OSM equivalent
        for key, value in entry.items():
            attributes = ("id", "timestamp", "lat", "lon", "uid", "user", "version", "action")
            if len(key) > 0 and key in attributes:
                attrs[key] = value
                logging.debug("Adding attribute %s with value %s" % (key, value))
            else:
                if value is not None:
                    if key == "track" or key == "geoline":
                        refs.append(tag)
                        logging.debug("Adding reference %s" % tag)
                    elif len(value) > 0:
                        if self.privateData(key):
                            priv[key] = value
                        else:
                            tags[key] = value
            if len(tags) > 0:
                feature['attrs'] = attrs
                feature['tags'] = tags
            if len(refs) > 0:
                feature['refs'] = refs
            if len(priv) > 0:
                feature['private'] = priv

        return feature


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='convert ODK CSV to OSM')
    parser.add_argument("-v", "--verbose", nargs="?",const="0", help="verbose output")
    parser.add_argument("-i", "--infile", help='The input file from ODK Central')
    parser.add_argument("-o", "--outfile", help='The output file for JOSM')
    args = parser.parse_args()

    # if verbose, dump to the terminal.
    if args.verbose is not None:
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)

        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        root.addHandler(ch)

    csvin = CSVDump()
    osmoutfile = os.path.basename(args.infile.replace(".csv", ".osm"))
    csvin.createOSM(osmoutfile)

    jsonoutfile = os.path.basename(args.infile.replace(".csv", ".geojson"))
    csvin.createGeoJson(jsonoutfile)
    data = csvin.parse(args.infile)
    for entry in data:
        # This OSM XML file only has OSM appropriate tags and values 
        feature = csvin.createEntry(entry)
        csvin.writeOSM(feature)
        # This GeoJson file has all the data values
        csvin.writeGeoJson(feature)
        print("FOO: %r" % feature['tags'])

    csvin.finishOSM()
    csvin.finishGeoJson()
    logging.info("Wrote OSM XML file: %r" % osmoutfile)
    logging.info("Wrote GeoJson file: %r" % jsonoutfile)
