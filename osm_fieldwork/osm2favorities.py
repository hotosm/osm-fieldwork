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
from geojson import Point, Feature, FeatureCollection, dump
from pathlib import Path
import gpxpy
import gpxpy.gpx
from lxml import etree


# set log level for urlib
log = logging.getLogger(__name__)

def createExtension(icon):
    # camp_pitch.png, tourism_camp_site.png, topo_camp_pitch.png, topo_camp_site.png
    # trailhead.png, tourism_picnic_site.png, tourism_picnic_site.png,
    # tourism_attraction.png, tourism_information.png, information_board.png,
    # firepit.png, historic_ruins.png, amenity_drinking_water.png,
    # amenity_toilets.png
    # amenity_parking.png


    # template = f"""<extensions><osmand:icon>{icon}</osmand:icon>
    # <osmand:background>circle</osmand:background>
    # <osmand:color>#ff5020</osmand:color>
    # </extensions>
    # """
    nsmap = {'osmand': 'https://osmand.net'}
    png = etree.Element('{osmand}icon', nsmap=nsmap)
    png.text = icon
    back = etree.Element('{osmand}background', nsmap=nsmap)
    back.text = "circle"
    color = etree.Element('{osmand}color', nsmap=nsmap)
    color.text = '#ff5020'
    return (png, back, color)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="convert JSON from ODK Central to OSM XML"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-i", "--infile", help="The data extract")
    args = parser.parse_args()

    if len(argv) <= 1:
        parser.print_help()
        quit()

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

        infile = open(args.infile, "r")
        indata = geojson.load(infile)

        # gpxpy.gpxfield.GPXField()
        gpx = gpxpy.gpx.GPX()
        gpx.nsmap['osmand'] = "https://osmand.net"
        gpx.creator = "osm2favorites 0.1"
        for feature in indata['features']:
            coords = feature['geometry']['coordinates']
            lat = coords[1]
            lon = coords[0]
            name = ""
            if 'name' in feature['properties']:
                name = feature['properties']['name']
            for key, value in feature['properties'].items():
                if key == 'name':
                    continue
                description = "<p>"
                description += f"{key} = {value}<br>"
                description += "</p>"
            way = gpxpy.gpx.GPXWaypoint(
                latitude=lat,
                longitude=lon,
                description=description,
                name=name,
                # symbol="",
                # comment="",
            )
            extensions = createExtension("tourism_camp_site")
            for ext in extensions:
                way.extensions.append(ext)
            gpx.waypoints.append(way)
        outfile = "output.gpx"
        with open(outfile, "w") as f:
            f.write(gpx.to_xml())

        log.info(f"Wrote {outfile}")
