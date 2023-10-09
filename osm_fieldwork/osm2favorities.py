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
import logging
import sys

import geojson
import gpxpy
import gpxpy.gpx
import shapely
from lxml import etree
from shapely.geometry import shape

# set log level for urlib
log = logging.getLogger(__name__)


def createExtension(icon):
    """Create an extended feature with Osmand styling."""
    # camp_pitch.png, tourism_camp_site.png, topo_camp_pitch.png, topo_camp_site.png
    # trailhead.png, tourism_picnic_site.png, tourism_picnic_site.png,
    # tourism_attraction.png, tourism_information.png, information_board.png,
    # firepit.png, historic_ruins.png, amenity_drinking_water.png,
    # amenity_toilets.png, amenity_parking.png, special_trekking
    colors = {"tourism_camp_site": "#ff5020", "tourism_picnic_site": "#ff5020", "special_trekking": "#a71de1"}
    nsmap = {"osmand": "https://osmand.net"}
    png = etree.Element("{osmand}icon", nsmap=nsmap)
    png.text = icon
    back = etree.Element("{osmand}background", nsmap=nsmap)
    back.text = "circle"
    color = None
    if icon in colors:
        color = etree.Element("{osmand}color", nsmap=nsmap)
        color.text = colors[icon]
        return (png, back, color)
    else:
        return (png, back)


def main():
    """This main function lets this class be run standalone by a bash script."""
    parser = argparse.ArgumentParser(description="convert GeoJson to a GPX favorites file for Osmand")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-i", "--infile", required=True, help="The data extract")
    args = parser.parse_args()

    # if verbose, dump to the termina
    if args.verbose is not None:
        log.setLevel(logging.DEBUG)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(threadName)10s - %(name)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        log.addHandler(ch)

    infile = open(args.infile, "r")
    indata = geojson.load(infile)

    # gpxpy.gpxfield.GPXField()
    gpx = gpxpy.gpx.GPX()
    gpx.nsmap["osmand"] = "https://osmand.net"
    gpx.creator = "osm2favorites 0.1"
    for feature in indata["features"]:
        coords = feature["geometry"]["coordinates"]
        if feature["geometry"]["type"] == "Polygon":
            wkt = shape(feature["geometry"])
            center = shapely.centroid(wkt)
            lat = center.y
            lon = center.x
        else:
            lat = coords[1]
            lon = coords[0]
        name = ""
        if "name" in feature["properties"]:
            name = feature["properties"]["name"]
            tourism = None
            if "tourism" in feature["properties"]:
                tourism = feature["properties"]["tourism"]
            highway = None
            if "highway" in feature["properties"]:
                highway = feature["properties"]["highway"]
            amenity = None
            if "amenity" in feature["properties"] and not highway:
                amenity = feature["properties"]["amenity"]
        for key, value in feature["properties"].items():
            if key == "name":
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
        extensions = ""
        if tourism and tourism != "picnic site":
            extensions = createExtension("tourism_camp_site")
        elif tourism and tourism != "picnic site":
            extensions = createExtension("tourism_picnic_site")
        elif highway and highway == "trailhead":
            extensions = createExtension("special_trekking")
        elif amenity and amenity == "parking":
            extensions = createExtension("amenity_parking")

        for ext in extensions:
            way.extensions.append(ext)
        gpx.waypoints.append(way)
    outfile = "output.gpx"
    with open(outfile, "w") as f:
        f.write(gpx.to_xml())

    log.info(f"Wrote {outfile}")


if __name__ == "__main__":
    """This is just a hook so this file can be run standlone during development."""
    main()
