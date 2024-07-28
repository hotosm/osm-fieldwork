#!/usr/bin/python3
#
# Copyright (C) 2020, 2021, 2022, 2023 Humanitarian OpenstreetMap Team
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

import argparse
import logging
import os
import sys
from datetime import datetime
from sys import argv

import xmltodict

from osm_fieldwork.convert import Convert, escape

# Instantiate logger
log = logging.getLogger(__name__)


class OsmFile(object):
    """OSM File output."""

    def __init__(
        self,
        filespec: str = None,
        options: dict = None,
        outdir: str = "/tmp/",
    ):
        """This class reads and writes the OSM XML formated files.

        Args:
            filespec (str): The input or output file
            options (dict): Command line options
            outdir (str): The output directory for the file

        Returns:
            (OsmFile): An instance of this object
        """
        if options is None:
            options = dict()
        self.options = options
        # Read the config file to get our OSM credentials, if we have any
        # self.config = config.config(self.options)
        self.version = 3
        self.visible = "true"
        self.osmid = -1
        # Open the OSM output file
        self.file = None
        if filespec is not None:
            self.file = open(filespec, "w")
            # self.file = open(filespec + ".osm", 'w')
            logging.info("Opened output file: " + filespec)
        self.header()
        # logging.error("Couldn't open %s for writing!" % filespec)

        # This is the file that contains all the filtering data
        # self.ctable = convfile(self.options.get('convfile'))
        # self.options['convfile'] = None
        # These are for importing the CO addresses
        self.full = None
        self.addr = None
        # decrement the ID
        self.start = -1
        # path = xlsforms_path.replace("xlsforms", "")
        self.convert = Convert()
        self.data = list()

    def __del__(self):
        """Close the OSM XML file automatically."""
        # log.debug("Closing output file")
        self.footer()

    def isclosed(self):
        """Is the OSM XML file open or closed ?

        Returns:
            (bool): The OSM XML file status
        """
        return self.file.closed

    def header(self):
        """Write the header of the OSM XML file."""
        if self.file is not None:
            self.file.write("<?xml version='1.0' encoding='UTF-8'?>\n")
            # self.file.write('<osm version="0.6" generator="osm-fieldowrk 0.3" timestamp="2017-03-13T21:43:02Z">\n')
            self.file.write('<osm version="0.6" generator="osm-fieldwork 0.3">\n')
            self.file.flush()

    def footer(self):
        """Write the footer of the OSM XML file."""
        # logging.debug("FIXME: %r" % self.file)
        if self.file is not None:
            self.file.write("</osm>\n")
            self.file.flush()
            if self.file is False:
                self.file.close()
        self.file = None

    def write(
        self,
        data=None,
    ):
        """Write the data to the OSM XML file."""
        if type(data) == list:
            if data is not None:
                for line in data:
                    self.file.write("%s\n" % line)
        else:
            self.file.write("%s\n" % data)

    def createWay(
        self,
        way: dict,
        modified: bool = False,
    ):
        """This creates a string that is the OSM representation of a node.

        Args:
            way (dict): The input way data structure
            modified (bool): Is this a modified feature ?

        Returns:
            (str): The OSM XML entry
        """
        attrs = dict()
        osm = ""

        # Add default attributes
        if modified:
            attrs["action"] = "modify"
        if "osm_way_id" in way["attrs"]:
            attrs["id"] = int(way["attrs"]["osm_way_id"])
        elif "osm_id" in way["attrs"]:
            attrs["id"] = int(way["attrs"]["osm_id"])
        elif "id" in way["attrs"]:
            attrs["id"] = int(way["attrs"]["id"])
        else:
            attrs["id"] = self.start
            self.start -= 1
        if "version" not in way["attrs"]:
            attrs["version"] = 1
        else:
            attrs["version"] = way["attrs"]["version"]
        attrs["timestamp"] = datetime.now().strftime("%Y-%m-%dT%TZ")
        # If the resulting file is publicly accessible without authentication, The GDPR applies
        # and the identifying fields should not be included
        if "uid" in way["attrs"]:
            attrs["uid"] = way["attrs"]["uid"]
        if "user" in way["attrs"]:
            attrs["user"] = way["attrs"]["user"]

        # Make all the nodes first. The data in the track has 4 fields. The first two
        # are the lat/lon, then the altitude, and finally the GPS accuracy.
        # newrefs = list()
        node = dict()
        node["attrs"] = dict()
        # The geometry is an EWKT string, so there is no need to get fancy with
        # geometries, just manipulate the string, as OSM XML it's only strings
        # anyway.
        # geom = way['geom'][19:][:-2]
        # print(geom)
        # points = geom.split(",")
        # print(points)

        # epdb.st()
        # loop = 0
        # while loop < len(way['refs']):
        #     #print(f"{points[loop]} {way['refs'][loop]}")
        #     node['timestamp'] = attrs['timestamp']
        #     if 'user' in attrs and attrs['user'] is not None:
        #         node['attrs']['user'] = attrs['user']
        #     if 'uid' in attrs and attrs['uid'] is not None:
        #         node['attrs']['uid'] = attrs['uid']
        #     node['version'] = 0
        #     lat,lon = points[loop].split(' ')
        #     node['attrs']['lat'] = lat
        #     node['attrs']['lon'] = lon
        #     node['attrs']['id'] = way['refs'][loop]
        #     osm += self.createNode(node) + '\n'
        #     loop += 1

        # Processs atrributes
        line = ""
        for ref, value in attrs.items():
            line += "%s=%r " % (ref, str(value))
        osm += "  <way " + line + ">"

        if "refs" in way:
            for ref in way["refs"]:
                osm += '\n    <nd ref="%s"/>' % ref
        if "tags" in way:
            for key, value in way["tags"].items():
                if value is None:
                    continue
                if key == "track":
                    continue
                if key not in attrs:
                    newkey = escape(key)
                    newval = escape(str(value))
                    osm += f"\n    <tag k='{newkey}' v='{newval}'/>"
            if modified and key != "note":
                osm += '\n    <tag k="note" v="Do not upload this without validation!"/>'
            osm += "\n"

        osm += "  </way>\n"

        return osm

    def featureToNode(
        self,
        feature: dict,
    ):
        """Convert a GeoJson feature into the data structures used here.

        Args:
            feature (dict): The GeoJson feature to convert

        Returns:
            (dict): The data structure used by this file
        """
        osm = dict()
        ignore = ("label", "title")
        tags = dict()
        attrs = dict()
        for tag, value in feature["properties"].items():
            if tag == "id":
                attrs["osm_id"] = value
            elif tag not in ignore:
                tags[tag] = value
        coords = feature["geometry"]["coordinates"]
        attrs["lat"] = coords[1]
        attrs["lon"] = coords[0]
        osm["attrs"] = attrs
        osm["tags"] = tags
        return osm

    def createNode(
        self,
        node: dict,
        modified: bool = False,
    ):
        """This creates a string that is the OSM representation of a node.

        Args:
            node (dict): The input node data structure
            modified (bool): Is this a modified feature ?

        Returns:
            (str): The OSM XML entry
        """
        attrs = dict()
        # Add default attributes
        if modified:
            attrs["action"] = "modify"

        if "id" in node["attrs"]:
            attrs["id"] = int(node["attrs"]["id"])
        else:
            attrs["id"] = self.start
            self.start -= 1
        if "version" not in node["attrs"]:
            attrs["version"] = "1"
        else:
            attrs["version"] = int(node["attrs"]["version"]) + 1
        attrs["lat"] = node["attrs"]["lat"]
        attrs["lon"] = node["attrs"]["lon"]
        attrs["timestamp"] = datetime.now().strftime("%Y-%m-%dT%TZ")
        # If the resulting file is publicly accessible without authentication, THE GDPR applies
        # and the identifying fields should not be included
        if "uid" in node["attrs"]:
            attrs["uid"] = node["attrs"]["uid"]
        if "user" in node["attrs"]:
            attrs["user"] = node["attrs"]["user"]

        # Processs atrributes
        line = ""
        osm = ""
        for ref, value in attrs.items():
            line += "%s=%r " % (ref, str(value))
        osm += "  <node " + line

        if "tags" in node:
            osm += ">"
            for key, value in node["tags"].items():
                if not value:
                    continue
                if key not in attrs:
                    newkey = escape(key)
                    newval = escape(str(value))
                    osm += f"\n    <tag k='{newkey}' v='{newval}'/>"
            if modified and key != "note":
                osm += '\n    <tag k="note" v="Do not upload this without validation!"/>'
            osm += "\n  </node>\n"
        else:
            osm += "/>"

        return osm

    def createTag(
        self,
        field: str,
        value: str,
    ):
        """Create a data structure for an OSM feature tag.

        Args:
            field (str): The tag name
            value (str): The value for the tag

        Returns:
            (dict): The newly created tag pair
        """
        newval = str(value)
        newval = newval.replace("&", "and")
        newval = newval.replace('"', "")
        tag = dict()
        # logging.debug("OSM:makeTag(field=%r, value=%r)" % (field, newval))

        newtag = field
        change = newval.split("=")
        if len(change) > 1:
            newtag = change[0]
            newval = change[1]

        tag[newtag] = newval
        return tag

    def loadFile(
        self,
        osmfile: str,
    ):
        """Read a OSM XML file generated by osm_fieldwork.

        Args:
            osmfile (str): The OSM XML file to load

        Returns:
            (list): The entries in the OSM XML file
        """
        size = os.path.getsize(osmfile)
        with open(osmfile, "r") as file:
            xml = file.read(size)
            doc = xmltodict.parse(xml)
            if "osm" not in doc:
                logging.warning("No data in this instance")
                return False
            data = doc["osm"]
            if "node" not in data:
                logging.warning("No nodes in this instance")
                return False

        for node in data["node"]:
            attrs = {
                "id": int(node["@id"]),
                "lat": node["@lat"][:10],
                "lon": node["@lon"][:10],
            }
            if "@timestamp" in node:
                attrs["timestamp"] = node["@timestamp"]

            tags = dict()
            if "tag" in node:
                for tag in node["tag"]:
                    if type(tag) == dict:
                        tags[tag["@k"]] = tag["@v"].strip()
                        # continue
                    else:
                        tags[node["tag"]["@k"]] = node["tag"]["@v"].strip()
                    # continue
            node = {"attrs": attrs, "tags": tags}
            self.data.append(node)

        for way in data["way"]:
            attrs = {
                "id": int(way["@id"]),
            }
            refs = list()
            if len(way["nd"]) > 0:
                for ref in way["nd"]:
                    refs.append(int(ref["@ref"]))

            if "@timestamp" in node:
                attrs["timestamp"] = node["@timestamp"]

            tags = dict()
            if "tag" in way:
                for tag in way["tag"]:
                    if type(tag) == dict:
                        tags[tag["@k"]] = tag["@v"].strip()
                        # continue
                    else:
                        tags[node["tag"]["@k"]] = node["tag"]["@v"].strip()
                    # continue
            way = {"attrs": attrs, "refs": refs, "tags": tags}
            self.data.append(way)

        return self.data

    def dump(self):
        """Dump internal data structures, for debugging purposes only."""
        for _id, item in self.data.items():
            for k, v in item["attrs"].items():
                print(f"{k} = {v}")
            for k, v in item["tags"].items():
                print(f"\t{k} = {v}")

    def getFeature(
        self,
        id: int,
    ):
        """Get the data for a feature from the loaded OSM data file.

        Args:
            id (int): The ID to retrieve the feasture of

        Returns:
            (dict): The feature for this ID or None
        """
        return self.data[id]

    def getFields(self):
        """Extract all the tags used in this file."""
        fields = list()
        for _id, item in self.data.items():
            keys = list(item["tags"].keys())
            for key in keys:
                if key not in fields:
                    fields.append(key)
        # print(fields)


if __name__ == "__main__":
    """This is just a hook so this file can be run standlone during development."""
    # Command Line options
    parser = argparse.ArgumentParser(description="This program conflates ODK data with existing features from OSM.")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-o", "--osmfile", required=True, help="OSM XML file created by Osm-Fieldwork")
    args = parser.parse_args()

    # This program needs options to actually do anything
    if len(argv) == 1:
        parser.print_help()
        quit()

    # if verbose, dump to the terminal.
    if args.verbose is not None:
        logging.basicConfig(
            level=logging.DEBUG,
            format=("%(threadName)10s - %(name)s - %(levelname)s - %(message)s"),
            datefmt="%y-%m-%d %H:%M:%S",
            stream=sys.stdout,
        )

    osm = OsmFile()
    osm.loadFile(args.osmfile)
    osm.dump()
