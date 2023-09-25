#!/usr/bin/python3

# Copyright (c) 2020, 2021, 2022 Humanitarian OpenStreetMap Team
#
# This file is part of OSM-Fieldwork.
#
#     This is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with OSM-Fieldwork.  If not, see <https:#www.gnu.org/licenses/>.
#

import argparse
import concurrent.futures
import json
import logging
import os
import queue
import sys
import threading

import mercantile
from cpuinfo import get_cpu_info
from pySmartDL import SmartDL
from shapely.geometry import shape
from shapely.ops import unary_union

from osm_fieldwork.sqlite import DataFile, MapTile
from osm_fieldwork.xlsforms import xlsforms_path
from osm_fieldwork.yamlfile import YamlFile

log = logging.getLogger(__name__)


def dlthread(
    dest: str,
    mirrors: list,
    tiles: list,
    xy: bool,
):
    """Thread to handle downloads for Queue.

    Args:
        dest (str): The filespec of the tile cache
        mirrors (list): The list of mirrors to get imagery
        tiles (list): The list of tiles to download
        xy (bool): Whether to swap the X & Y fields in the TMS URL
    """
    if len(tiles) == 0:
        # epdb.st()
        return
    # counter = -1

    # start = datetime.now()

    # totaltime = 0.0
    log.info("Downloading %d tiles in thread %d to %s" % (len(tiles), threading.get_ident(), dest))
    for tile in tiles:
        bingkey = mercantile.quadkey(tile)
        filespec = f"{tile[2]}/{tile[1]}/{tile[0]}"
        for site in mirrors:
            if site["source"] != "topo":
                filespec += "." + site["suffix"]
            url = site["url"]
            if site["source"] == "bing":
                remote = url % bingkey
            elif site["source"] == "google":
                path = f"x={tile[0]}&s=&y={tile[1]}&z={tile[2]}"
                remote = url % path
            elif site["source"] == "custom":
                if not xy:
                    path = f"x={tile[0]}&s=&y={tile[1]}&z={tile[2]}"
                else:
                    path = f"x={tile[0]}&s=&y={tile[2]}&z={tile[1]}"
                remote = url % path
            else:
                remote = url % filespec
            print("Getting file from: %s" % remote)
            # Create the subdirectories as pySmartDL doesn't do it for us
            if os.path.isdir(dest) is False:
                tmp = ""
                paths = dest.split("/")
                for i in paths[1:]:
                    tmp += "/" + i
                    if os.path.isdir(tmp):
                        continue
                    else:
                        os.mkdir(tmp)
                        log.debug("Made %s" % tmp)

        try:
            if site["source"] == "topo":
                filespec += "." + site["suffix"]
            outfile = dest + "/" + filespec
            if not os.path.exists(outfile):
                dl = SmartDL(remote, dest=outfile, connect_default_logger=False)
                dl.start()
            else:
                log.debug("%s exists!" % (outfile))
        except Exception as e:
            log.error(e)
            log.error("Couldn't download from %r: %s" % (filespec, dl.get_errors()))


class BaseMapper(object):
    def __init__(
        self,
        boundary: str,
        base: str,
        source: str,
        xy: bool,
    ):
        """Create an mbtiles basemap for ODK Collect.

        Args:
            boundary (str): A BBOX string or GeoJSON file of the AOI.
                The GeoJSON can contain multiple geometries.
            base (str): The base directory to cache map tile in
            source (str): The upstream data source for map tiles
            xy (bool): Whether to swap the X & Y fields in the TMS URL

        Returns:
            (BaseMapper): An instance of this class
        """
        self.bbox = self.makeBbox(boundary)
        self.tiles = list()
        self.base = base
        # sources for imagery
        self.source = source
        self.sources = dict()
        self.xy = xy

        path = xlsforms_path.replace("xlsforms", "imagery.yaml")
        self.yaml = YamlFile(path)

        for entry in self.yaml.yaml["sources"]:
            for k, v in entry.items():
                src = dict()
                for item in v:
                    src["source"] = k
                    for k1, v1 in item.items():
                        # print(f"\tFIXME2: {k1} - {v1}")
                        src[k1] = v1
                self.sources[k] = src

    def customTMS(
        self,
        url: str,
        name: str = "custom",
        source: str = "custom",
        suffix: str = "jpg",
    ):
        """Add a custom TMS URL to the list of sources.

        Args:
            name (str): The name to display
            url (str): The URL string
            suffix (str): The suffix, png or jpg
            source (str): The source value to use as an index
        """
        self.sources["custom"] = {"name": name, "url": url, "suffix": suffix, "source": source}
        self.source = "custom"

    def getFormat(self):
        """Returns:
        (str): the upstream source for map tiles.
        """
        return self.sources[self.source]["suffix"]

    def getTiles(
        self,
        zoom: int = None,
    ):
        """Get a list of tiles for the specifed zoom level.

        Args:
            zoom (int): The Zoom level of the desired map tiles

        Returns:
            (int): The total number of map tiles downloaded
        """
        info = get_cpu_info()
        cores = info["count"]

        self.tiles = list(mercantile.tiles(self.bbox[0], self.bbox[1], self.bbox[2], self.bbox[3], zoom))
        total = len(self.tiles)
        log.info("%d tiles for zoom level %d" % (len(self.tiles), zoom))
        chunk = round(len(self.tiles) / cores)
        queue.Queue(maxsize=cores)
        log.info("%d threads, %d tiles" % (cores, total))

        mirrors = [self.sources[self.source]]
        # epdb.st()
        if len(self.tiles) < chunk or chunk == 0:
            dlthread(self.base, mirrors, self.tiles, self.xy)
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=cores) as executor:
                block = 0
                while block <= len(self.tiles):
                    executor.submit(dlthread, self.base, mirrors, self.tiles[block : block + chunk])
                    log.debug("Dispatching Block %d:%d" % (block, block + chunk))
                    block += chunk
                executor.shutdown()
            # log.info("Had %r errors downloading %d tiles for data for %r" % (self.errors, len(tiles), os.path.basename(self.base)))

        return len(self.tiles)

    def tileExists(
        self,
        tile: MapTile,
    ):
        """See if a map tile already exists.

        Args:
            tile (MapTile): The map tile to check for the existence of

        Returns:
            (bool): Whether the tile exists in the map tile cache
        """
        filespec = f"{self.base}{tile[2]}/{tile[1]}/{tile[0]}.{self.sources[{self.source}]['suffix']}"
        if os.path.exists(filespec):
            log.debug("%s exists" % filespec)
            return True
        else:
            log.debug("%s doesn't exists" % filespec)
            return False

    def makeBbox(
        self,
        boundary: str,
    ):
        """Make a bounding box from a shapely geometry.

        Args:
            boundary (str): A BBOX string or GeoJSON file of the AOI.
                The GeoJSON can contain multiple geometries.

        Returns:
            (list): The bounding box coordinates
        """
        if not boundary.lower().endswith((".json", ".geojson")):
            # Is BBOX string
            try:
                bbox_parts = boundary.split(",")
                bbox = tuple(float(x) for x in bbox_parts)
                if len(bbox) == 4:
                    # BBOX valid
                    return bbox
                else:
                    log.error(f"BBOX string malformed: {bbox}")
                    return
            except Exception as e:
                log.error(e)
                log.error(f"Failed to parse BBOX string: {boundary}")
                return

        log.debug(f"Reading geojson file: {boundary}")
        with open(boundary, "r") as f:
            poly = json.load(f)
        if "features" in poly:
            geometry = shape(poly["features"][0]["geometry"])
        else:
            geometry = shape(poly)

        if isinstance(geometry, list):
            # Multiple geometries
            log.debug("Creating union of multiple bbox geoms")
            geometry = unary_union(geometry)

        if geometry.is_empty:
            log.warning(f"No bbox extracted from {geometry}")
            return None

        bbox = geometry.bounds
        # left, bottom, right, top
        # minX, minY, maxX, maxY
        return bbox


def main():
    """This main function lets this class be run standalone by a bash script."""
    parser = argparse.ArgumentParser(description="Create an mbtiles basemap for ODK Collect")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-b", "--boundary", required=True, help="The boundary for the area you want")
    parser.add_argument("-t", "--tms", help="Custom TMS URL")
    parser.add_argument("--xy", default=False, help="Swap the X & Y coordinates when using a custom TMS")
    parser.add_argument("-o", "--outfile", required=True, help="Output file name")
    parser.add_argument("-z", "--zooms", default="12-17", help="The Zoom levels")
    parser.add_argument("-d", "--outdir", help="Output directory name for tile cache")
    parser.add_argument(
        "-s",
        "--source",
        default="esri",
        choices=["esri", "bing", "topo", "google", "oam"],
        help="Imagery source",
    )
    args = parser.parse_args()

    # if verbose, dump to the terminal.
    if args.verbose is not None:
        log.setLevel(logging.DEBUG)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(threadName)10s - %(name)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        log.addHandler(ch)

    # Get all the zoom levels we want
    zooms = list()
    if args.zooms:
        if args.zooms.find("-") > 0:
            start = int(args.zooms.split("-")[0])
            end = int(args.zooms.split("-")[1]) + 1
            x = range(start, end)
            for i in x:
                zooms.append(i)
        elif args.zooms.find(",") > 0:
            levels = args.zooms.split(",")
            for level in levels:
                zooms.append(int(level))
        else:
            zooms.append(int(args.zooms))

    # Make a bounding box from the boundary file
    if not args.boundary:
        log.error("You need to specify a boundary file!")
        parser.print_help()
        quit()

    if not args.outdir:
        base = "/var/www/html"
    else:
        base = args.outdir
    base = f"{base}/{args.source}tiles"

    if args.source and not args.tms:
        basemap = BaseMapper(args.boundary, base, args.source, args.xy)
    elif args.tms:
        basemap = BaseMapper(args.boundary, base, "custom", args.xy)
        basemap.customTMS(args.tms)
    else:
        log.error("You need to specify a source!")
        parser.print_help()
        quit()

    if args.outfile is None:
        log.error("You need to specify an mbtiles or sqlitedb file!!")
        parser.print_help()
        quit()

    outf = DataFile(args.outfile, basemap.getFormat())
    suffix = os.path.splitext(args.outfile)[1]
    if suffix == ".mbtiles":
        outf.addBounds(basemap.bbox)
    for level in zooms:
        basemap.getTiles(level)
        if args.outfile:
            # Create output database and specify image format, png, jpg, or tif
            outf.writeTiles(basemap.tiles, base)
        else:
            log.info("Only downloading tiles to %s!" % base)


if __name__ == "__main__":
    """This is just a hook so this file can be run standlone during development."""
    main()
