#!/usr/bin/python3

# Copyright (c) 2022 Humanitarian OpenStreetMap Team
#
# This program is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

import argparse
import logging
from sys import argv
import os
import epdb
import sys
from osgeo import ogr
from geojson import Point, Feature, FeatureCollection, dump
from progress.bar import Bar, PixelBar
from progress.spinner import PixelSpinner
from codetiming import Timer

class OutputFile(object):
    def __init__(self, outfile=None):
        """Initialize OGR output layer"""
        outdrv = ogr.GetDriverByName("GeoJson")
        if os.path.exists(outfile):
            outdrv.DeleteDataSource(outfile)

        logging.info("Creating output data file: %s" % outfile)
        self.outdata  = outdrv.CreateDataSource(outfile)
        self.outlayer = self.outdata.CreateLayer("data", geom_type=ogr.wkbPolygon)
        self.fields = self.outlayer.GetLayerDefn()
        # newid = ogr.FieldDefn("id", ogr.OFTInteger)
        # self.outlayer.CreateField(newid)
        self.filespec = outfile


class InputFile(object):
    def __init__(self, source=None):
        """Initialize Input Layer"""
        self.datain = None
        self.source = source
        if source[0:3] == "pg:":
            logging.info("Opening database connection to: %s" % source)
            connect = "PG: dbname=" + source[3:]
            # if options.get('dbhost') != "localhost":
            #connect += " host=" + options.get('dbhost')
            self.datain = ogr.Open(connect)
        else:
            logging.info("Opening data file: %s" % source)
            self.datain = ogr.Open(source)

        # Copy the data into memory for better performance
        memdrv = ogr.GetDriverByName("MEMORY")
        self.msmem = memdrv.CreateDataSource('msmem')
        self.msmem.CopyLayer(self.datain.GetLayer(), "msmem")
        self.layer = self.msmem.GetLayer()
        self.memlayer = None
        self.mem = None

    def clip(self, boundary=None):
        """Clip a data source by a boundary"""
        if boundary:
            logging.info("Clipping %s using %s" % (self.source, boundary))
            memdrv = ogr.GetDriverByName("MEMORY")
            self.mem = memdrv.CreateDataSource("data")
            self.memlayer = self.mem.CreateLayer("data", geom_type=ogr.wkbUnknown)

            poly = ogr.Open(boundary)
            layer = poly.GetLayer()
            ogr.Layer.Clip(self.layer, layer, self.memlayer)
        
        
    def dump(self):
        """Dump internal data"""
        print(f"Data source is: {self.source}")
        if self.layer:
           print("There are %d in the layer" % self.layer.GetFeatureCount())
        if self.memlayer:
           print("There are %d in the layer" % self.memlayer.GetFeatureCount())
        
if __name__ == '__main__':
    # Command Line options
    parser = argparse.ArgumentParser(description='This program conflates ODK data with existing features from OSM.')
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-c", "--odkfile", help="ODK CSV file downloaded from ODK Central")
    parser.add_argument("-f", "--osmfile", help="OSM XML file created by odkconvert")
    parser.add_argument("-o", "--outfile", default="tmp.osm", help="Output file from the merge")
    parser.add_argument("-b", "--boundary", help='Boundary polygon to limit the data size')
    args = parser.parse_args()

    if len(argv) == 1:
        parser.print_help()
        quit()

    # if verbose, dump to the terminal.
    if args.verbose is not None:
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)

    if args.osmfile:
        osmf = InputFile(args.osmfile)
        osmf.dump()
        if args.boundary:
            osmf.clip(args.boundary)
    else:
        logging.error("No OSM data source specified!")
        parser.print_help()
        quit()
        
    if args.odkfile:
        odkf = InputFile(args.odkfile)
        odkf.dump()
        if args.boundary:
            odkf.clip(args.boundary)
    else:
        logging.error("No ODK CSV file specified!")
        parser.print_help()
        quit()

# osmoutfile = os.path.basename(args.infile.replace(".csv", ".osm"))
#csvin.createOSM(osmoutfile)
