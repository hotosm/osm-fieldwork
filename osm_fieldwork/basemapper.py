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
"""Module for generating basemaps from various providers."""

import argparse
import concurrent.futures
import logging
import queue
import re
import sys
import threading
from pathlib import Path
from typing import Union

import geojson
import mercantile
from cpuinfo import get_cpu_info
from pmtiles.tile import (
    Compression as PMTileCompression,
)
from pmtiles.tile import (
    TileType as PMTileType,
)
from pmtiles.tile import (
    zxy_to_tileid,
)
from pmtiles.writer import Writer as PMTileWriter
from pySmartDL import SmartDL
from shapely.geometry import shape
from shapely.ops import unary_union

from osm_fieldwork.sqlite import DataFile, MapTile
from osm_fieldwork.xlsforms import xlsforms_path
from osm_fieldwork.yamlfile import YamlFile

# Instantiate logger
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
        filespec = f"{tile[2]}/{tile[1]}/{tile[0]}"
        for site in mirrors:
            if site["source"] != "topo":
                filespec += "." + site["suffix"]
            url = site["url"]
            if site["source"] == "bing":
                bingkey = mercantile.quadkey(tile)
                remote = url % bingkey
            elif site["source"] == "google":
                path = f"x={tile[0]}&s=&y={tile[1]}&z={tile[2]}"
                remote = url % path
            elif site["source"] == "custom":
                if not xy:
                    # z/y/x format
                    path = f"{tile[2]}/{tile[1]}/{tile[0]}"
                else:
                    # z/x/y format
                    path = f"{tile[2]}/{tile[0]}/{tile[1]}"
                remote = url % path
            else:
                remote = url % filespec
            print("Getting file from: %s" % remote)
            # Create the subdirectories as pySmartDL doesn't do it for us
            Path(dest).mkdir(parents=True, exist_ok=True)

        dl = None
        try:
            if site["source"] == "topo":
                filespec += "." + site["suffix"]
            outfile = dest + "/" + filespec
            if not Path(outfile).exists():
                dl = SmartDL(remote, dest=outfile, connect_default_logger=False)
                dl.start()
            else:
                log.debug("%s exists!" % (outfile))
        except Exception as e:
            log.error(e)
            if dl:
                log.error(f"Couldn't download {filespec}: {dl.get_errors()}")
            else:
                log.error(f"Couldn't download {filespec}")


class BaseMapper(object):
    """Basemapper parent class."""

    def __init__(
        self,
        boundary: str,
        base: str,
        source: str,
        xy: bool,
    ):
        """Create an tile basemap for ODK Collect.

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

    def customTMS(self, url: str, name: str = "custom", source: str = "custom", suffix: str = "jpg"):
        """Add a custom TMS URL to the list of sources.

        The url must end in %s to be replaced with the tile xyz values.

        Format examples:
        https://basemap.nationalmap.gov/ArcGIS/rest/services/USGSTopo/MapServer/tile/{z}/{y}/{x}
        https://maps.nyc.gov/xyz/1.0.0/carto/basemap/%s
        https://maps.nyc.gov/xyz/1.0.0/carto/basemap/{z}/{x}/{y}.jpg

        The method will replace {z}/{x}/{y}.jpg with %s

        Args:
            name (str): The name to display
            url (str): The URL string
            suffix (str): The suffix, png or jpg
            source (str): The source value to use as an index
        """
        # Remove any file extensions if present and update the 'suffix' parameter
        if url.endswith(".jpg"):
            source = "jpg"
            suffix = "jpg"
            url = url[:-4]  # Remove the last 4 characters (".jpg")
        elif url.endswith(".png"):
            source = "png"
            suffix = "png"
            url = url[:-4]  # Remove the last 4 characters (".png")

        # Replace "{z}/{x}/{y}" with "%s"
        url = re.sub(r"/{[xyz]+\}", "", url)
        url = url + r"/%s"

        tms_params = {"name": name, "url": url, "suffix": suffix, "source": source}
        log.debug(f"Setting custom TMS with params: {tms_params}")
        self.sources["custom"] = tms_params
        self.source = "custom"

    def getFormat(self):
        """Get the image format of the map tiles.

        Returns:
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
                # results = []
                block = 0
                while block <= len(self.tiles):
                    executor.submit(dlthread, self.base, mirrors, self.tiles[block : block + chunk], self.xy)
                    # result = executor.submit(dlthread, self.base, mirrors, self.tiles[block : block + chunk], self.xy)
                    # results.append(result)
                    log.debug("Dispatching Block %d:%d" % (block, block + chunk))
                    block += chunk
                executor.shutdown()
            # log.info("Had %r errors downloading %d tiles for data for %r" % (self.errors, len(tiles), Path(self.base).name))
            # for result in results:
            #     print(result.result())
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
        if Path(filespec).exists():
            log.debug("%s exists" % filespec)
            return True
        else:
            log.debug("%s doesn't exists" % filespec)
            return False

    def makeBbox(
        self,
        boundary: str,
    ) -> tuple[float, float, float, float]:
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
                if "," in boundary:
                    bbox_parts = boundary.split(",")
                else:
                    bbox_parts = boundary.split(" ")
                bbox = tuple(float(x) for x in bbox_parts)
                if len(bbox) == 4:
                    # BBOX valid
                    return bbox
                else:
                    msg = f"BBOX string malformed: {bbox}"
                    log.error(msg)
                    raise ValueError(msg) from None
            except Exception as e:
                log.error(e)
                msg = f"Failed to parse BBOX string: {boundary}"
                log.error(msg)
                raise ValueError(msg) from None

        log.debug(f"Reading geojson file: {boundary}")
        with open(boundary, "r") as f:
            poly = geojson.load(f)
        if "features" in poly:
            geometry = shape(poly["features"][0]["geometry"])
        elif "geometry" in poly:
            geometry = shape(poly["geometry"])
        else:
            geometry = shape(poly)

        if isinstance(geometry, list):
            # Multiple geometries
            log.debug("Creating union of multiple bbox geoms")
            geometry = unary_union(geometry)

        if geometry.is_empty:
            msg = f"No bbox extracted from {geometry}"
            log.error(msg)
            raise ValueError(msg) from None

        bbox = geometry.bounds
        # left, bottom, right, top
        # minX, minY, maxX, maxY
        return bbox


def tileid_from_tms_path(filepath: Union[Path, str]):
    """Helper function to get the tile id from a tile in z/x/y directory structure.

    Args:
        filepath (Union[Path, str]): The path to the y tile in /z/x/y.jpg structure.
    """
    # Extract the final 3 parts from the TMS file path
    zxy_path = Path(filepath).parts[-3:]
    # Extract filename without extension
    y_tile_filename = Path(zxy_path[-1]).stem
    # If filename contains a dot, take the part before the dot as 'y'
    y = int(y_tile_filename.split(".")[0]) if "." in y_tile_filename else int(y_tile_filename)
    # Extract z and x values
    z, x = map(int, zxy_path[:-1])
    return zxy_to_tileid(z, x, y)


def tile_dir_to_pmtiles(outfile: str, tile_dir: str, bbox: tuple, attribution: str):
    """Write PMTiles archive from tiles in the specified directory.

    Args:
        outfile (str): The output PMTiles archive file path.
        tile_dir (str): The directory containing the tile images.
        bbox (tuple): Bounding box in format (min_lon, min_lat, max_lon, max_lat).
        attribution (str): Attribution string to include in PMTile archive.

    Returns:
        None
    """
    tile_dir = Path(tile_dir)

    # Get tile image format from the first file encountered
    first_file = next((file for file in tile_dir.rglob("*.*") if file.is_file()), None)

    if not first_file:
        err = "No tile files found in the specified directory. Aborting PMTile creation."
        log.error(err)
        raise ValueError(err)

    # FIXME passing as PMTileType[tile_format] does not work
    # tile_format = first_file.suffix.upper()

    # Get zoom levels from dirs
    zoom_levels = sorted([int(x.stem) for x in tile_dir.glob("*") if x.is_dir()])

    # Process tiles
    with open(outfile, "wb") as pmtile_file:
        writer = PMTileWriter(pmtile_file)

        for tile_path in tile_dir.rglob("*"):
            if tile_path.is_file():
                tile_id = tileid_from_tms_path(tile_path)

                with open(tile_path, "rb") as tile:
                    writer.write_tile(tile_id, tile.read())

        # Extract bbox values
        min_lon, min_lat, max_lon, max_lat = bbox

        # Write metadata
        writer.finalize(
            {
                # "tile_type": TileType[tile_format.lstrip(".")],
                "tile_type": PMTileType.PNG,
                "tile_compression": PMTileCompression.NONE,
                "min_zoom": zoom_levels[0],
                "max_zoom": zoom_levels[-1],
                "min_lon_e7": int(min_lon * 10000000),
                "min_lat_e7": int(min_lat * 10000000),
                "max_lon_e7": int(max_lon * 10000000),
                "max_lat_e7": int(max_lat * 10000000),
                "center_zoom": zoom_levels[0],
                "center_lon_e7": int(min_lon + ((max_lon - min_lon) / 2)),
                "center_lat_e7": int(min_lat + ((max_lat - min_lat) / 2)),
            },
            {"attribution": f"© {attribution}"},
        )


def create_basemap_file(
    boundary=None,
    tms=None,
    xy=False,
    outfile=None,
    zooms="12-17",
    outdir=None,
    source="esri",
) -> None:
    """Create a basemap with given parameters.

    Args:
        boundary (str, optional): The boundary for the area you want.
        tms (str, optional): Custom TMS URL.
        xy (bool, optional): Swap the X & Y coordinates when using a
            custom TMS if True.
        outfile (str, optional): Output file name for the basemap.
        zooms (str, optional): The Zoom levels, specified as a range
            (e.g., "12-17") or comma-separated levels (e.g., "12,13,14").
        outdir (str, optional): Output directory name for tile cache.
        source (str, optional): Imagery source, one of
            ["esri", "bing", "topo", "google", "oam"] (default is "esri").

    Returns:
        None
    """
    log.debug(
        "Creating basemap with params: "
        f"boundary={boundary} | "
        f"outfile={outfile} | "
        f"zooms={zooms} | "
        f"outdir={outdir} | "
        f"source={source} | "
        f"xy={xy} | "
        f"tms={tms}"
    )

    # Validation
    if not boundary:
        err = "You need to specify a boundary! (file or bbox)"
        log.error(err)
        raise ValueError(err)

    # Get all the zoom levels we want
    zoom_levels = list()
    if zooms:
        if zooms.find("-") > 0:
            start = int(zooms.split("-")[0])
            end = int(zooms.split("-")[1]) + 1
            x = range(start, end)
            for i in x:
                zoom_levels.append(i)
        elif zooms.find(",") > 0:
            levels = zooms.split(",")
            for level in levels:
                zoom_levels.append(int(level))
        else:
            zoom_levels.append(int(zooms))

    if not outdir:
        base = Path.cwd().absolute()
    else:
        base = Path(outdir).absolute()

    source = "custom" if tms else source
    tiledir = base / f"{source}tiles"
    # Make tile download directory
    tiledir.mkdir(parents=True, exist_ok=True)
    # Convert to string for other methods
    tiledir = str(tiledir)

    if not source and not tms:
        err = "You need to specify a source!"
        log.error(err)
        raise ValueError(err)

    basemap = BaseMapper(boundary, tiledir, source, xy)

    if tms:
        # Add TMS URL to sources for download
        basemap.customTMS(tms)

    # Args parsed, main code:
    tiles = list()
    for level in zoom_levels:
        # Download the tile directory
        basemap.getTiles(level)
        tiles += basemap.tiles

    if not outfile:
        log.info(f"No outfile specified, tile download finished: {tiledir}")
        return

    suffix = Path(outfile).suffix.lower()
    log.debug(f"Basemap output format: {suffix}")

    if any(substring in suffix for substring in ["sqlite", "mbtiles"]):
        outf = DataFile(outfile, basemap.getFormat())
        if suffix == ".mbtiles":
            outf.addBounds(basemap.bbox)
        # Create output database and specify image format, png, jpg, or tif
        outf.writeTiles(tiles, tiledir)

    elif suffix == ".pmtiles":
        tile_dir_to_pmtiles(outfile, tiledir, basemap.bbox, source)

    else:
        msg = f"Format {suffix} not supported"
        log.error(msg)
        raise ValueError(msg) from None
    log.info(f"Wrote {outfile}")


def main():
    """This main function lets this class be run standalone by a bash script."""
    parser = argparse.ArgumentParser(description="Create an tile basemap for ODK Collect")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument(
        "-b",
        "--boundary",
        nargs="*",
        required=True,
        help=(
            "The boundary for the area you want. " "Accepts path to geojson file or bbox string. " "Format min_x min_y max_x max_y"
        ),
    )
    parser.add_argument("-t", "--tms", help="Custom TMS URL")
    parser.add_argument("--xy", default=False, help="Swap the X & Y coordinates when using a custom TMS")
    parser.add_argument(
        "-o", "--outfile", required=False, help="Output file name, allowed extensions [.mbtiles/.sqlitedb/.pmtiles]"
    )
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

    if not args.boundary:
        log.error("You need to specify a boundary! (file or bbox)")
        parser.print_help()
        quit()

    if not args.source:
        log.error("You need to specify a source!")
        parser.print_help()
        quit()

    if len(args.boundary) == 1:
        if Path(args.boundary[0]).suffix not in [".json", ".geojson"]:
            log.error("")
            log.error("*Error*: the boundary file must have .json or .geojson extension")
            log.error("")
            parser.print_help()
            quit()
        boundary_parsed = args.boundary[0]
    elif len(args.boundary) == 4:
        boundary_parsed = ",".join(args.boundary)
    else:
        log.error("")
        log.error("*Error*: the bounding box must have 4 coordinates")
        log.error("")
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

    create_basemap_file(
        boundary=boundary_parsed,
        tms=args.tms,
        xy=args.xy,
        outfile=args.outfile,
        zooms=args.zooms,
        outdir=args.outdir,
        source=args.source,
    )


if __name__ == "__main__":
    """This is just a hook so this file can be run standlone during development."""
    main()
