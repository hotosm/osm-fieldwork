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
import os
import logging
import sys
import epdb
from sys import argv
from osgeo import ogr
import json
from geojson import Point, Polygon, Feature
from OSMPythonTools.overpass import Overpass
from OSMPythonTools.api import Api

# all possible queries
choices = ["buildings", "amenities", "toilets", "landuse", "emergency"]

class OutputFile(object):
    def __init__(self, filespec=None):
        """Initialize OGR output layer"""
        outdrv = ogr.GetDriverByName("GeoJson")
        if os.path.exists(filespec):
            outdrv.DeleteDataSource(filespec)

        self.outdata  = outdrv.CreateDataSource(filespec)
        self.outlayer = self.outdata.CreateLayer("buildings", geom_type=ogr.wkbPolygon)
        self.fields = self.outlayer.GetLayerDefn()
        newid = ogr.FieldDefn("id", ogr.OFTInteger)
        self.outlayer.CreateField(newid)
        bld = ogr.FieldDefn("tags", ogr.OFTString)
        self.outlayer.CreateField(bld)
        self.filespec = filespec

    def addFeature(self, feature=None):
        """Add an OGR feature to the output layer"""
        self.outlayer.CreateFeature(feature)

class PostgresClient(OutputFile):
    """Class to handle SQL queries for the categories"""
    def __init__(self, dbhost=None, dbname=None, output=None):
        """Initialize the postgres handler"""
        OutputFile.__init__( self, output)
        logging.info("Opening database connection to: %s" % dbhost)
        connect = "PG: dbname=" + dbname
        connect += " host=" + dbhost
        self.pg = ogr.Open(connect)
        self.boundary = None

    def getFeature(self, boundary=None, filespec=None, category='buildings'):
        """Extract buildings from Postgres"""
        logging.info("Extracting buildings...")

        if category not in choices:
            pass
        else:
            pass

        tables = list()
        if category == 'buildings':
            tables.append("ways_poly")
            tables.append("relations")
            filter = "tags->>'building' IS NOT NULL"
        elif category == 'amenity':
            tables.append("nodes", "ways_poly")
            filter = "tags->>'amenity' IS NOT NULL"
        elif category == 'toilets':
            tables.append("nodes", "ways_poly")            
            filter = "tags->>'amenity'='toilets'"

        # Clip the large file using the supplied boundary
        memdrv = ogr.GetDriverByName("MEMORY")
        mem = memdrv.CreateDataSource('buildings')
        memlayer = mem.CreateLayer('buildings', geom_type=ogr.wkbMultiPolygon)
        for table in tables:
            logging.debug("Querying table %s..." % table)
            osm = self.pg.GetLayerByName(table)
            osm.SetAttributeFilter(filter)
            if boundary:
                poly = ogr.Open(boundary)
                layer = poly.GetLayer()
                ogr.Layer.Clip(osm, layer, memlayer)
            else:
                memlayer = osm

            logging.info("There are %d buildings in the table" % osm.GetFeatureCount())
            for feature in memlayer:
                poly = feature.GetGeometryRef()
                center = poly.Centroid()
                feature.SetGeometry(center)
                self.outlayer.CreateFeature(feature)

        logging.info("Wrote output file %s" % filespec)
        self.outdata.Destroy()

class OverpassClient(OutputFile):
    """Class to handle Overpass queries"""
    def __init__(self, output=None):
        """Initialize Overpass handler"""
        self.overpass = Overpass()
        OutputFile.__init__( self, output)

    def getFeature(self, boundary=None, filespec=None):
        """Extract buildings from Overpass"""
        logging.info("Extracting buildings...")
        poly = ogr.Open(boundary)
        layer = poly.GetLayer()

        extent = layer.GetExtent()
        bbox = f"{extent[2]},{extent[0]},{extent[3]},{extent[1]}"
        query = f'(way["building"]({bbox}); ); out body; >; out skel qt;'
        # logging.debug(query)
        result = self.overpass.query(query)

        nodes = dict()
        for node in result.nodes():
            wkt = "POINT(%f %f)" %  (float(node.lon()) , float(node.lat()))
            center = ogr.CreateGeometryFromWkt(wkt)
            nodes[node.id()] = center
        
        ways = result.ways()
        for way in ways:
            for ref in way.nodes():
                # FIXME: There's probably a better way to get the node ID.
                nd = ref._queryString.split('/')[1]
                feature = ogr.Feature(self.fields)
                feature.SetGeometry(nodes[float(nd)])
                feature.SetField("id", way.id())
                feature.SetField('tags', json.dumps(way.tags()))
                self.addFeature(feature)
        logging.info("Wrote data extract to: %s" % self.filespec)
        self.outdata.Destroy()

class FileClient(OutputFile):
    """Class to handle Overpass queries"""
    def __init__(self, infile=None, output=None):
        """Initialize Overpass handler"""
        OutputFile.__init__( self, output)
        self.infile = infile

    def getFeature(self, boundary=None, infile=None, outfile=None):
        """Extract buildings from a disk file"""
        logging.info("Extracting buildings from %s..." % infile)
        if boundary:
            poly = ogr.Open(boundary)
            layer = poly.GetLayer()
            ogr.Layer.Clip(osm, layer, memlayer)
        else:
            layer = poly.GetLayer()

        tmp = ogr.Open(infile)
        layer = tmp.GetLayer()

        layer.SetAttributeFilter("tags->>'building' IS NOT NULL")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Make GeoJson data file for ODK from OSM')
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-o", "--overpass", action="store_true", help='Use Overpass Turbo')
    parser.add_argument("-p", "--postgres", action="store_true", help='Use a postgres database')
    parser.add_argument("-g", "--geojson", default="tmp.geojson", help='Name of the GeoJson output file')
    parser.add_argument("-i", "--infile", help='Use a data file')
    parser.add_argument("-dn", "--dbname", help='Database name')
    parser.add_argument("-dh", "--dbhost", default="localhost", help='Database host')
    parser.add_argument("-b", "--boundary", help='Boundary polygon to limit the data size')
    parser.add_argument("-c", "--category", default="buildings", choices=choices, help='Which category to extract')
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

if args.postgres:
    logging.info("Using a Postgres database for the data source")
    pg = PostgresClient(args.dbhost, args.dbname, args.geojson)
    pg.getFeature(args.boundary, args.geojson, args.category)
elif args.overpass:
    logging.info("Using Overpass Turbo for the data source")
    op = OverpassClient(args.geojson)
    op.getFeature(args.boundary, args.geojson, args.category)
elif args.infile:
    f = FileClient(args.infile)
    f.getFeature(args.boundary, args.geojson, args.category)
    logging.info("Using file %s for the data source" % args.infile)
else:
    logging.error("You need to supply either --overpass or --postgres")
    
