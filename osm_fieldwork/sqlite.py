#!/usr/bin/python3

# Copyright (c) 2020, 2021, 2022, 2023 Humanitarian OpenStreetMap Team
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
import locale
import logging
import os
import sqlite3
import sys

import mercantile

# Instantiate logger
log = logging.getLogger(__name__)


class MapTile(object):
    def __init__(
        self,
        x: int = None,
        y: int = None,
        z: int = None,
        filespec: str = None,
        tile: "MapTile" = None,
        suffix="jpg",
    ):
        """This is a simple wrapper around mercantile.tile to associate a
        filespec with the grid coordinates.

        Args:
            x (int): The X index for this tile
            y (int): The Y index for this tile
            z (int): The Z index for this tile if there is one
            filespec (str): The location of this within the map tile cache
            tile (MapTile): Make a copy of this object
            suffix (str): The image suffix, jpg or png usually

        Returns:
            (MapTile): An instance of this object
        """
        if tile:
            self.x = tile.x
            self.y = tile.y
            self.z = tile.z
        else:
            self.x = x
            self.y = y
            self.z = z
        self.blob = None
        self.filespec = None
        if not filespec and self.z:
            self.filespec = f"{self.z}/{self.y}/{self.x}.{suffix}"
        elif filespec:
            self.filespec = filespec
            tmp = filespec.split("/")
            self.z = tmp[0]
            self.x = tmp[2]
            self.y = tmp[1].replace("." + suffix, "")

    def readImage(self, base: str = "./"):
        """Read a map tile out of the disk based map tile cache.

        Args:
            base (str): The top level directory for the map tile cache
        """
        file = f"{base}/{self.filespec}"
        logging.debug("Adding tile image: %s" % file)
        if os.path.exists(file):
            size = os.path.getsize(file)
            file = open(file, "rb")
            self.blob = file.read(size)

    def dump(self):
        """Dump internal data structures, for debugging purposes only."""
        if self.z:
            print("Z: %r" % self.z)
        if self.x:
            print("X: %r" % self.x)
        if self.y:
            print("Y: %r" % self.y)
        print("Filespec: %s" % self.filespec)
        if self.blob:
            print("Tile size is: %d" % len(self.blob))


class DataFile(object):
    def __init__(
        self,
        dbname: str = None,
        suffix: str = "jpg",
        append: bool = False,
    ):
        """Handle the sqlite3 database file.

        Args:
            dbname (str): The name of the output sqlite file
            suffix (str): The image suffix, jpg or png usually
            append (bool): Whether to append to or create the database

        Returns:
            (DataFile): An instance of this class
        """
        self.db = None
        self.cursor = None
        if dbname:
            self.createDB(dbname, append)
        self.dbname = dbname
        self.metadata = None
        self.toplevel = None
        self.suffix = suffix

    def addBounds(
        self,
        bounds: tuple[float, float, float, float],
    ):
        """Mbtiles has a bounds field, Osmand doesn't.

        Args:
            bounds (int): The bounds value for ODK Collect mbtiles
        """
        entry = str(bounds)
        entry = entry[1 : len(entry) - 1].replace(" ", "")
        self.cursor.execute(f"INSERT OR IGNORE INTO metadata (name, value) VALUES('bounds', '{entry}') ")

    def addZoomLevels(
        self,
        zoom_levels: list[int],
    ):
        """Mbtiles has a maxzoom and minzoom fields, Osmand doesn't.

        Args:
            bounds (int): The bounds value for ODK Collect mbtiles
        """
        min_zoom = min(zoom_levels)
        max_zoom = max(zoom_levels)
        self.cursor.execute(f"INSERT OR IGNORE INTO metadata (name, value) VALUES('minzoom', '{min_zoom}') ")
        self.cursor.execute(f"INSERT OR IGNORE INTO metadata (name, value) VALUES('maxzoom', '{max_zoom}') ")

    def createDB(
        self,
        dbname: str,
        append: bool = False,
    ):
        """Create and sqlitedb in either mbtiles or Osman sqlitedb format.

        Args:
            dbname (str): The filespec of the sqlite output file
        """
        suffix = os.path.splitext(dbname)[1]

        if os.path.exists(dbname) and append == False:
            os.remove(dbname)

        self.db = sqlite3.connect(dbname)
        self.cursor = self.db.cursor()
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tiles'")
        exists = self.cursor.fetchone()
        if exists and append:
            logging.info("Appending to database file %s" % dbname)
            return

        if suffix == ".mbtiles":
            self.cursor.execute("CREATE TABLE tiles (zoom_level integer, tile_column integer, tile_row integer, tile_data blob)")
            self.cursor.execute("CREATE INDEX tiles_idx on tiles (zoom_level, tile_column, tile_row)")
            self.cursor.execute("CREATE TABLE metadata (name text, value text)")
            # These get populated later
            name = dbname
            description = "Created by osm_fieldwork/basemapper.py"
            self.cursor.execute("CREATE UNIQUE INDEX metadata_idx  ON metadata (name)")
            self.cursor.execute("INSERT INTO metadata (name, value) VALUES('version', '1.1')")
            self.cursor.execute("INSERT INTO metadata (name, value) VALUES('type', 'baselayer')")
            self.cursor.execute(f"INSERT INTO metadata (name, value) VALUES('name', '{name}')")
            self.cursor.execute(f"INSERT INTO metadata (name, value) VALUES('description', '{description}')")
            # self.cursor.execute(f"INSERT INTO metadata (name, value) VALUES('bounds', '{bounds}')")
            self.cursor.execute("INSERT INTO metadata (name, value) VALUES('format', 'jpg')")
        if "sqlite" in suffix:
            # s is always 0
            self.cursor.execute("CREATE TABLE tiles (x int, y int, z int, s int, image blob, PRIMARY KEY (x,y,z,s));")
            self.cursor.execute("CREATE INDEX IND on tiles (x,y,z,s)")
            # Info is simple "2|4" for example, it gets populated later
            self.cursor.execute("CREATE TABLE info (maxzoom Int, minzoom Int);")
            # the metadata is the locale as a string
            loc = locale.getlocale()[0]
            self.cursor.execute(f"CREATE TABLE  android_metadata ({loc})")
        self.db.commit()
        logging.info("Created database file %s" % dbname)

    def writeTiles(self, tiles: list, base: str = "./", image_format: str = "jpg"):
        """Write map tiles into the to the map tile cache.

        Args:
            tiles (list): The map tiles to write to the map tile cache
            base (str): The default local to write tiles to disk
        """
        for tile in tiles:
            xyz = MapTile(tile=tile, suffix=image_format)
            xyz.readImage(base)
            # xyz.dump()
            self.writeTile(xyz)

    def writeTile(
        self,
        tile: MapTile,
    ):
        """Write a map tile into the sqlite database file.

        Args:
            tile (MapTile): The map tile to write to the file
        """
        if tile.blob is None:
            logging.error(f"Map tile {tile.filespec} has no image data!")
            # tile.dump()
            return False

        suffix = os.path.splitext(self.dbname)[1]

        if "sqlite" in suffix:
            # Osmand tops out at zoom level 16, so the real zoom level is inverse,
            # and can go negative for really high zoom levels.
            z = 17 - tile.z
            self.db.execute(
                "INSERT INTO tiles (x, y, z, s, image) VALUES (?, ?, ?, ?, ?)",
                [tile.x, tile.y, z, 0, sqlite3.Binary(tile.blob)],
            )

        if suffix == ".mbtiles":
            y = (1 << tile.z) - tile.y - 1
            self.db.execute(
                "INSERT INTO tiles (tile_row, tile_column, zoom_level, tile_data) VALUES (?, ?, ?, ?)",
                [y, tile.x, tile.z, sqlite3.Binary(tile.blob)],
            )

        self.db.commit()


if __name__ == "__main__":
    """This is just a hook so this file can be run standlone during development."""
    parser = argparse.ArgumentParser(description="Create an mbtiles basemap for ODK Collect")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-d", "--database", default="test.mbtiles", help="Database file name")
    args = parser.parse_args()

    # if verbose, dump to the terminal.
    if args.verbose is not None:
        logging.basicConfig(
            level=logging.DEBUG,
            format=("%(threadName)10s - %(name)s - %(levelname)s - %(message)s"),
            datefmt="%y-%m-%d %H:%M:%S",
            stream=sys.stdout,
        )

    outfile = DataFile(args.database, "jpg")
    toplevel = "/var/www/html/topotiles/"
    foo = "15/12744/6874.png"
    tmp = foo.split("/")
    z = tmp[0]
    x = tmp[1]
    y = tmp[2].replace(".jpg", "")

    # file = "10/388/212.jpg"
    # tile1 = MapTile(x=x, y=y, z=z)
    # tile2 = MapTile(filespec=file)
    # tile2.readImage(f'{toplevel}/{foo}')
    # outfile.writeTile(tile2)

    tile3 = mercantile.Tile(388, 211, 10)
    xyz = MapTile(tile=tile3)
    xyz.readImage(toplevel)
    xyz.dump()
