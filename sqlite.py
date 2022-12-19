#!/usr/bin/python3

# Copyright (c) 2020, 2021, 2022 Humanitarian OpenStreetMap Team
#
# This file is part of Odkconvert.
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
#     along with Odkconvert.  If not, see <https:#www.gnu.org/licenses/>.
#

import argparse
import os
import logging
import sys
import epdb
from sys import argv
import sqlite3
import locale

# mbtiles
# -------
# CREATE TABLE tiles (zoom_level integer, tile_column integer, tile_row integer, tile_data blob);
# CREATE INDEX tiles_idx on tiles (zoom_level, tile_column, tile_row);
# CREATE TABLE metadata (name text, value text);
# CREATE UNIQUE INDEX metadata_idx  ON metadata (name);
# sqlite> 

# osmand
# ------
# CREATE TABLE tiles (x int, y int, z int, s int, image blob, PRIMARY KEY (x,y,z,s));
# CREATE INDEX IND on tiles (x,y,z,s);
# CREATE TABLE info(minzoom,maxzoom);
# CREATE TABLE android_metadata (locale TEXT);


class MapTile(object):
    def __init__(self, x=None, y=None, z=None, blob=None):
        self.tile = dict()
        self.tile['x'] = x
        self.tile['y'] = y
        self.tile['z'] = z
        self.blob = blob

    def createTile(self, x=None, y=None, z=None, blob=None):
        if x:
            self.tile['x'] = x
        if y:
            self.tile['y'] = y
        if z:
            self.tile['z'] = z
        if blob:
            self.addBlob(blob)

    def addBlob(self, blob=None):
        self.blob = blob

    def getTile(self, format=None):
        if format == 'mbtiles':
            out = (z, y, x) 
        elif format == 'osmand':
            out = (x, y, z)             
        elif format == 'postgres':
            out = (x, y, z)             
        return out

    def dump(self):
        print(self.x)
        print(self.y)
        print(self.z)

class DataFile(object):
    def __init__(self, dbname=None):
        self.db = None
        self.cursor = None
        if dbname:
            self.createDB(dbname)
        self.metadata = None
    
    def createDB(self, dbname=None):
        suffix = os.path.splitext(dbname)[1]
        
        logging.info("Created database file %s" % dbname)
        self.db = sqlite3.connect(dbname)
        self.cursor = self.db.cursor()
        if suffix == '.mbtiles':
            self.cursor.execute("CREATE TABLE tiles (zoom_level integer, tile_column integer, tile_row integer, tile_data blob)")
            self.cursor.execute("CREATE INDEX tiles_idx on tiles (zoom_level, tile_column, tile_row)")
            self.cursor.execute("CREATE TABLE metadata (name text, value text)")
            self.cursor.execute("CREATE UNIQUE INDEX metadata_idx  ON metadata (name)")
            self.cursor.execute("INSERT INTO metadata (name, value) VALUES('version', '1.1')")
            self.cursor.execute("INSERT INTO metadata (name, value) VALUES('type', 'baselayer')")
            self.cursor.execute("INSERT INTO metadata (name, value) VALUES('name', 'fixme')")
            self.cursor.execute("INSERT INTO metadata (name, value) VALUES('description', 'fixme')")
            self.cursor.execute("INSERT INTO metadata (name, value) VALUES('bounds', 'fixme')")
            self.cursor.execute("INSERT INTO metadata (name, value) VALUES('format', 'png')")
        elif suffix == '.sqlitedb':
            # s is always 0
            self.cursor.execute("CREATE TABLE tiles (x int, y int, z int, s int, image blob, PRIMARY KEY (x,y,z,s));")
            self.cursor.execute("CREATE INDEX IND on tiles (x,y,z,s)")
            # Info is simple "2|4" for example
            self.cursor.execute("CREATE TABLE info (maxzoom Int, minzoom Int);")
            # the metadata is the locale as a string, 'en_US' in out case
            loc = locale.getlocale()[0]
            self.cursor.execute(f"CREATE TABLE  android_metadata ({loc})")
        self.db.commit()

    def writeTile(self):
        pass

    def readTile(self):
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create an mbtiles basemap for ODK Collect')
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-d", "--database", default="test.mbtiles", help='Database file name')
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

        outfile = DataFile(args.database)
