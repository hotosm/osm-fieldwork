#!/usr/bin/python3

# Copyright (c) 2020, 2021, 2022, 2023, 2024 Humanitarian OpenStreetMap Team
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
import os
import re
import shutil
import sys
import threading
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple, Union

import geojson
import mercantile
from cpuinfo import get_cpu_info
from pmtiles.tile import Compression as PMTileCompression
from pmtiles.tile import TileType as PMTileType
from pmtiles.tile import zxy_to_tileid
from pmtiles.writer import Writer as PMTileWriter
from pySmartDL import SmartDL
from shapely.geometry import shape
from shapely.ops import unary_union

from osm_fieldwork.sqlite import DataFile, MapTile
from osm_fieldwork.xlsforms import xlsforms_path
from osm_fieldwork.yamlfile import YamlFile

# Instantiate logger
log = logging.getLogger(__name__)

BoundingBox = Tuple[float, float, float, float]


class BoundaryHandlerFactory:
    """Factory class for creating boundary handlers based on the type of input boundary provided."""

    def __init__(self, boundary: Union[str, BytesIO]):
        """Initialize the BoundaryHandlerFactory with a boundary input.

        Args:
            boundary (Union[str, BytesIO]): The boundary input, either as a GeoJSON BytesIO object or a BBOX string.
        """
        if isinstance(boundary, BytesIO):
            self.handler = BytesIOBoundaryHandler(boundary)
        elif isinstance(boundary, str):
            self.handler = StringBoundaryHandler(boundary)
        else:
            raise ValueError("Unsupported type for boundary parameter.")

        self.boundary_box = self.handler.make_bbox()

    def get_bounding_box(self) -> BoundingBox:
        """Get bounding box.

        Returns:
            BoundingBox: The bounding box as a tuple (min_x, min_y, max_x, max_y).
        """
        return self.boundary_box


class BoundaryHandler:
    """A class to extract Bounding Box (BBOX) from various boundary representations."""

    def make_bbox(self) -> BoundingBox:
        """Extract and return the bounding box from the boundary representation.

        Returns:
        BoundingBox: The bounding box as a tuple (min_x, min_y, max_x, max_y).
        """
        pass


class BytesIOBoundaryHandler(BoundaryHandler):
    """Extracts BBOX from GeoJSON data stored in a BytesIO object."""

    def __init__(self, boundary: BytesIO):
        """Initialize the BytesIOBoundaryHandler with a BytesIO input."""
        self.boundary = boundary

    def make_bbox(self) -> BoundingBox:
        """Extract and return the bounding box from the GeoJSON data.

        Returns:
            BoundingBox: The bounding box as a tuple (min_x, min_y, max_x, max_y).
        """
        log.debug(f"Reading geojson BytesIO : {self.boundary}")
        # Rewind the BytesIO object to the beginning before passing it to geojson.load()
        self.boundary.seek(0)
        with self.boundary as buffer:
            poly = geojson.load(buffer)

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


class StringBoundaryHandler(BoundaryHandler):
    """Extracts BBOX from string representation."""

    def __init__(self, boundary: str):
        """Initialize the StringBoundaryHandler with a BoundaryHandler input."""
        self.boundary = boundary

    def make_bbox(self) -> BoundingBox:
        """A function to parse BBOX string."""
        try:
            if "," in self.boundary:
                bbox_parts = self.boundary.split(",")
            else:
                bbox_parts = self.boundary.split(" ")
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
            msg = f"Failed to parse BBOX string: {self.boundary}"
            log.error(msg)
            raise ValueError(msg) from None


def format_url(site: dict, tile: tuple) -> Optional[str]:
    """Format the URL for the given site and tile.

    Args:
        site (dict): The site configuration with URL and source type.
        tile (tuple): The tile coordinates (x, y, z).

    Returns:
        str: The formatted URL or None if the source is unsupported.
    """
    source_url = site["url"]
    if site.get("xy"):
        # z/x/y format download, move to z/y/x structure on disk
        url_path = f"{tile[2]}/{tile[0]}/{tile[1]}"
    else:
        # z/y/x format download, keep the same on disk
        url_path = f"{tile[2]}/{tile[1]}/{tile[0]}"

    match site["source"]:
        # NOTE we use % syntax to replace the placeholder %s
        case "esri":
            return source_url % url_path
        case "bing":
            bingkey = mercantile.quadkey(tile)
            return source_url % bingkey
        case "topo":
            # FIXME does this work an intended?
            return source_url % f"{tile[2]}/{tile[1]}/{tile[0]}"
        case "google":
            return source_url % f"x={tile[0]}&s=&y={tile[1]}&z={tile[2]}"
        case "oam":
            return source_url % url_path
        case "custom":
            return source_url % url_path
        case _:
            log.error(f"Unsupported source: {site['source']}")
            return None


def download_tile(dest: str, tile: tuple, mirrors: list[dict]) -> None:
    """Download a single tile from the given list of mirrors.

    Args:
        dest (str): The destination directory.
        tile (tuple): The tile coordinates (x, y, z).
        mirrors (list): The list of mirrors to get imagery.
    """
    for site in mirrors:
        download_url = format_url(site, tile)
        if download_url:
            filespec = f"{tile[2]}/{tile[1]}/{tile[0]}.{site['suffix']}"
            outfile = Path(dest) / filespec
            if not outfile.exists():
                try:
                    log.debug(f"Attempting URL download: {download_url}")
                    dl = SmartDL(download_url, dest=str(outfile), connect_default_logger=False)
                    dl.start()
                    return
                except Exception as e:
                    log.error(e)
                    log.error(f"Couldn't download file for {filespec}")
            else:
                log.debug(f"{outfile} exists!")
        else:
            continue


def dlthread(dest: str, mirrors: list[dict], tiles: list[tuple]) -> None:
    """Thread to handle downloads for Queue.

    Args:
        dest (str): The filespec of the tile cache.
        mirrors (list): The list of mirrors to get imagery.
        tiles (list): The list of tiles to download.
    """
    if len(tiles) == 0:
        # epdb.st()
        return

    # Create the subdirectories as pySmartDL doesn't do it for us
    Path(dest).mkdir(parents=True, exist_ok=True)

    log.info(f"Downloading {len(tiles)} tiles in thread {threading.get_ident()} to {dest}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(download_tile, dest, tile, mirrors) for tile in tiles]
        concurrent.futures.wait(futures)


class BaseMapper(object):
    """Basemapper parent class."""

    def __init__(
        self,
        boundary: Union[str, BytesIO],
        base: str,
        source: str,
    ):
        """Create an tile basemap for ODK Collect.

        Args:
            boundary (Union[str, BytesIO]): A BBOX string or GeoJSON provided as BytesIO object of the AOI.
                The GeoJSON can contain multiple geometries.
            base (str): The base directory to cache map tile in
            source (str): The upstream data source for map tiles

        Returns:
            (BaseMapper): An instance of this class
        """
        bbox_factory = BoundaryHandlerFactory(boundary)
        self.bbox = bbox_factory.get_bounding_box()
        self.tiles = list()
        self.base = base
        # sources for imagery
        self.source = source
        self.sources = dict()

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

    def customTMS(self, url: str, is_oam: bool = False, is_xy: bool = False):
        """Add a custom TMS URL to the list of sources.

        The url must end in %s to be replaced with the tile xyz values.

        Format examples:
        https://basemap.nationalmap.gov/ArcGIS/rest/services/USGSTopo/MapServer/tile/{z}/{y}/{x}
        https://maps.nyc.gov/xyz/1.0.0/carto/basemap/%s
        https://maps.nyc.gov/xyz/1.0.0/carto/basemap/{z}/{x}/{y}.jpg

        The method will replace {z}/{x}/{y}.jpg with %s

        Args:
            url (str): The URL string
            source (str): The provier source, for setting attribution
            is_xy (bool): Swap the x and y for the provider --> 'zxy'
        """
        # Remove any file extensions if present and update the 'suffix' parameter
        # NOTE the file extension gets added again later for the download URL
        if url.endswith(".jpg"):
            suffix = "jpg"
            url = url[:-4]  # Remove the last 4 characters (".jpg")
        elif url.endswith(".png"):
            suffix = "png"
            url = url[:-4]  # Remove the last 4 characters (".png")
        else:
            # FIXME handle other formats for custom TMS
            suffix = "jpg"

        # Replace "{z}/{x}/{y}" with "%s"
        url = re.sub(r"/{[xyz]+\}", "", url)
        url = url + r"/%s"

        if is_oam:
            # Override dummy OAM URL
            source = "oam"
            self.sources[source]["url"] = url
        else:
            source = "custom"
            tms_params = {"name": source, "url": url, "suffix": suffix, "source": source, "xy": is_xy}
            log.debug(f"Setting custom TMS with params: {tms_params}")
            self.sources[source] = tms_params

        # Select the source
        self.source = source

    def getFormat(self):
        """Get the image format of the map tiles.

        Returns:
            (str): the upstream source for map tiles.
        """
        return self.sources[self.source]["suffix"]

    def getTiles(self, zoom: int) -> int:
        """Get a list of tiles for the specified zoom level.

        Args:
            zoom (int): The Zoom level of the desired map tiles.

        Returns:
            int: The total number of map tiles downloaded.
        """
        info = get_cpu_info()
        cores = info["count"]

        self.tiles = list(mercantile.tiles(self.bbox[0], self.bbox[1], self.bbox[2], self.bbox[3], zoom))
        total = len(self.tiles)
        log.info(f"{total} tiles for zoom level {zoom}")

        mirrors = [self.sources[self.source]]
        chunk_size = max(1, round(total / cores))

        if total < chunk_size or chunk_size == 0:
            dlthread(self.base, mirrors, self.tiles)
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=cores) as executor:
                futures = []
                for i in range(0, total, chunk_size):
                    chunk = self.tiles[i : i + chunk_size]
                    futures.append(executor.submit(dlthread, self.base, mirrors, chunk))
                    log.debug(f"Dispatching Block {i}:{i + chunk_size}")
                concurrent.futures.wait(futures)

        return total

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


def tileid_from_zyx_dir_path(filepath: Union[Path, str]) -> int:
    """Helper function to get the tile id from a tile in xyz (zyx) directory structure.

    TMS typically has structure z/y/x.png
    If the --xy flag was used previously, the TMS was downloaed into
    directories of z/y/x structure from their z/x/y URL.

    Args:
        filepath (Union[Path, str]): The path to tile image within the xyz directory.

    Returns:
        int: The globally defined tile id from the xyz definition.
    """
    # Extract the final 3 parts from the TMS file path
    tile_image_path = Path(filepath).parts[-3:]

    try:
        final_tile = int(Path(tile_image_path[-1]).stem)
    except ValueError as e:
        msg = f"Invalid tile path (cannot parse as int): {str(tile_image_path)}"
        log.error(msg)
        raise ValueError(msg) from e

    x = final_tile
    z, y = map(int, tile_image_path[:-1])

    return zxy_to_tileid(z, x, y)


def tile_dir_to_pmtiles(
    outfile: str,
    tile_dir: str | Path,
    bbox: tuple,
    image_format: str,
    zoom_levels: list[int],
    attribution: str,
):
    """Write PMTiles archive from tiles in the specified directory.

    Args:
        outfile (str): The output PMTiles archive file path.
        tile_dir (str | Path): The directory containing the tile images.
        bbox (tuple): Bounding box in format (min_lon, min_lat, max_lon, max_lat).
        attribution (str): Attribution string to include in PMTile archive.

    Returns:
        None
    """
    tile_dir = Path(tile_dir)

    # Abort if no files are present
    first_file = next((file for file in tile_dir.rglob("*.*") if file.is_file()), None)
    if not first_file:
        err = "No tile files found in the specified directory. Aborting PMTile creation."
        log.error(err)
        raise ValueError(err)

    tile_format = image_format.upper()
    # NOTE JPEG exception / flexible extension (.jpg, .jpeg)
    if tile_format == "JPG":
        tile_format = "JPEG"
    log.debug(f"PMTile determind internal file format: {tile_format}")
    possible_tile_formats = [f".{e.name.lower()}" for e in PMTileType]
    possible_tile_formats.append(".jpg")
    possible_tile_formats.remove(".unknown")

    with open(outfile, "wb") as pmtile_file:
        writer = PMTileWriter(pmtile_file)

        for tile_path in tile_dir.rglob("*"):
            if tile_path.is_file() and tile_path.suffix.lower() in possible_tile_formats:
                tile_id = tileid_from_zyx_dir_path(tile_path)

                with open(tile_path, "rb") as tile:
                    writer.write_tile(tile_id, tile.read())

        min_lon, min_lat, max_lon, max_lat = bbox
        log.debug(
            f"Writing PMTiles file with min_zoom ({zoom_levels[0]}) "
            f"max_zoom ({zoom_levels[-1]}) bbox ({bbox}) tile_compression None"
        )

        # Write PMTile metadata
        writer.finalize(
            header={
                "tile_type": PMTileType[tile_format],
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
            metadata={"attribution": f"© {attribution}"},
        )


def create_basemap_file(
    boundary=None,
    tms=None,
    xy=False,
    outfile=None,
    zooms="12-17",
    outdir=None,
    source="esri",
    append: bool = False,
) -> None:
    """Create a basemap with given parameters.

    Args:
        boundary (str | BytesIO, optional): The boundary for the area you want.
        tms (str, optional): Custom TMS URL.
        xy (bool, optional): Swap the X & Y coordinates when using a
            custom TMS if True.
        outfile (str, optional): Output file name for the basemap.
        zooms (str, optional): The Zoom levels, specified as a range
            (e.g., "12-17") or comma-separated levels (e.g., "12,13,14").
        outdir (str, optional): Output directory name for tile cache.
        source (str, optional): Imagery source, one of
            ["esri", "bing", "topo", "google", "oam", "custom"] (default is "esri").
        append (bool, optional): Whether to append to an existing file

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
        f"tms={tms}"
    )

    # Validation
    if not boundary:
        err = "You need to specify a boundary! (in-memory object or bbox)"
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

    # Source / TMS validation
    if not source and not tms:
        err = "You need to specify a source!"
        log.error(err)
        raise ValueError(err)
    if source == "oam" and not tms:
        err = "A TMS URL must be provided for OpenAerialMap!"
        log.error(err)
        raise ValueError(err)
    # A custom TMS provider
    if source != "oam" and tms:
        source = "custom"

    tiledir = base / f"{source}tiles"
    # Make tile download directory
    tiledir.mkdir(parents=True, exist_ok=True)
    # Convert to string for other methods
    tiledir = str(tiledir)

    basemap = BaseMapper(boundary, tiledir, source)

    if tms:
        # Add TMS URL to sources for download
        basemap.customTMS(tms, True if source == "oam" else False, xy)

    # Args parsed, main code:
    tiles = list()
    for zoom_level in zoom_levels:
        # Download the tile directory
        basemap.getTiles(zoom_level)
        tiles += basemap.tiles

    if not outfile:
        log.info(f"No outfile specified, tile download finished: {tiledir}")
        return

    suffix = Path(outfile).suffix.lower()
    image_format = basemap.sources[source].get("suffix", "jpg")
    log.debug(f"Basemap output format: {suffix} | Image format: {image_format}")

    if any(substring in suffix for substring in ["sqlite", "mbtiles"]):
        outf = DataFile(outfile, basemap.getFormat(), append)
        if suffix == ".mbtiles":
            outf.addBounds(basemap.bbox)
            outf.addZoomLevels(zoom_levels)
        # Create output database and specify image format, png, jpg, or tif
        outf.writeTiles(tiles, tiledir, image_format)

    elif suffix == ".pmtiles":
        tile_dir_to_pmtiles(outfile, tiledir, basemap.bbox, image_format, zoom_levels, source)

    else:
        msg = f"Format {suffix} not supported"
        log.error(msg)
        raise ValueError(msg) from None
    log.info(f"Wrote {outfile}")


def move_tiles(
    boundary=None,
    indir=None,
    outdir=None,
) -> None:
    """Move tiles within a boundary to another directory. Used for managing the
    map tile cache.

    Args:
        boundary (str | BytesIO, optional): The boundary for the area you want.
        indir (str, optional): Top level directory for existing tile cache.
        outdir (str, optional): Output directory name for the new tile cache.

    Returns:
        None
    """
    bbox_factory = BoundaryHandlerFactory(boundary)
    bbox = bbox_factory.get_bounding_box()
    zooms = os.listdir(indir)

    if not Path(outdir).exists():
        log.info(f"Making {outdir}...")

    for level in zooms:
        tiles = list(mercantile.tiles(bbox[0], bbox[1], bbox[2], bbox[3], int(level)))
        total = len(tiles)
        log.info("%d tiles for zoom level %r" % (total, level))

        for tile in tiles:
            base = f"{tile.z}/{tile.y}/{tile.x}.jpg"
            inspec = f"{indir}/{base}"
            if Path(inspec).exists():
                # log.debug("Input tile %s exists" % inspec)
                root = os.path.basename(indir)
                outspec = f"{outdir}/{root}/{tile.z}/{tile.y}"
                if not Path(outspec).exists():
                    os.makedirs(outspec)
                outspec += f"/{tile.x}.jpg"
                # print(f"Move {inspec} to {outspec}")
                shutil.move(inspec, outspec)
            else:
                # log.debug("Input tile %s doesn't exist" % inspec)
                continue


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
    parser.add_argument("--xy", action="store_true", help="Swap the X & Y coordinates when using a custom TMS")
    parser.add_argument(
        "-o", "--outfile", required=False, help="Output file name, allowed extensions [.mbtiles/.sqlitedb/.pmtiles]"
    )
    parser.add_argument("-z", "--zooms", default="12-17", help="The Zoom levels")
    parser.add_argument("-d", "--outdir", help="Output directory name for new tile cache")
    parser.add_argument("-m", "--move", help="Move tiles to different directory")
    parser.add_argument("-a", "--append", action="store_true", default=False, help="Append to an existing database file")
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

    if args.move and args.outfile is not None:
        log.error("You can't move files to the same directory!")
        parser.print_help()
        # quit()

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
        with open(Path(args.boundary[0]), "rb") as geojson_file:
            boundary = geojson_file.read()
            boundary_parsed = BytesIO(boundary)
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

    if args.move is not None and args.outdir is None:
        log.error("You need to specify the new tile cache directory!")
        parser.print_help()
        quit()
    elif args.move is not None and args.outdir is not None:
        move_tiles(boundary_parsed, args.move, args.outdir)
        return

    create_basemap_file(
        boundary=boundary_parsed,
        tms=args.tms,
        xy=args.xy,
        outfile=args.outfile,
        zooms=args.zooms,
        outdir=args.outdir,
        source=args.source,
        append=args.append,
    )


if __name__ == "__main__":
    """This is just a hook so this file can be run standlone during development."""
    main()
