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


class OutputFile(object):
    def __init__(self, filespec=None):
        """Initialize OGR output layer"""
        # filespec += "foo"
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
        self.outlayer.CreateFeature(feature)

class PostgresClient(object):
    """Class to handle SQL queries for the categories"""
    def __init__(self, dbhost=None, dbname=None, output=None):
        """Initialize the postgres handler"""
        logging.info("Opening database connection to: %s" % dbhost)
        connect = "PG: dbname=" + dbname
        connect += " host=" + dbhost
        self.pg = ogr.Open(connect)
        self.boundary = None

        outdrv = ogr.GetDriverByName("GeoJson")
        if os.path.exists(output):
            outdrv.DeleteDataSource(output)
        outdata  = outdrv.CreateDataSource(output)
        self.outlayer = outdata.CreateLayer("buildings", geom_type=ogr.wkbPolygon)

    def getBuildings(self, boundary=None, filespec=None):
        """Extract buildings from Postgres"""
        logging.info("Extracting buildings...")

        # Create output file, delete it first if it already exists
        jsondrv = ogr.GetDriverByName("GeoJSON")
        if os.path.exists(filespec):
            jsondrv.DeleteDataSource(filespec)
        
        outfile  = jsondrv.CreateDataSource(filespec)
        outlayer = outfile.CreateLayer("buildings", geom_type=ogr.wkbPolygon)
        
        osm = self.pg.GetLayerByName("ways_poly")
        # logging.info("There are %d buildings in the output file" % osm.GetFeatureCount())
        osm.SetAttributeFilter("tags->>'building' IS NOT NULL")

        memdrv = ogr.GetDriverByName("MEMORY")
        mem = memdrv.CreateDataSource('buildings')
        memlayer = mem.CreateLayer('buildings', geom_type=ogr.wkbMultiPolygon)
        if boundary:
            poly = ogr.Open(boundary)
            layer = poly.GetLayer()
            ogr.Layer.Clip(osm, layer, memlayer)
        else:
            memlayer = osm

        logging.info("Writing to output file %s" % filespec)
        for feature in memlayer:
            poly = feature.GetGeometryRef()
            center = poly.Centroid()
            feature.SetGeometry(center)
            outlayer.CreateFeature(feature)

        #logging.info("There are %r buildings in the output file" % memlayer.GetFeatureCount())
        osm = self.pg.GetLayerByName("relations")
        memlayer = mem.CreateLayer('relations', geom_type=ogr.wkbMultiPolygon)
        if boundary:
            poly = ogr.Open(boundary)
            layer = poly.GetLayer()
            ogr.Layer.Clip(osm, layer, memlayer)
        else:
            memlayer = osm
        #logging.info("There are %r relations in the output file" % memlayer.GetFeatureCount())
        logging.info("Writing to output file %s" % filespec)
        for feature in memlayer:
            poly = feature.GetGeometryRef()
            center = poly.Centroid()
            feature.SetGeometry(center)
            outlayer.CreateFeature(feature)

        outfile.Destroy()

class OverpassClient(OutputFile):
    """Class to handle Overpass queries"""
    def __init__(self, output=None):
        """Initialize Overpass handler"""
        self.overpass = Overpass()
        OutputFile.__init__( self, output)

    def getBuildings(self, boundary=None, filespec=None):
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

class FileClient(object):
    """Class to handle Overpass queries"""
    def __init__(self, output=None):
        """Initialize Overpass handler"""
        outdrv = ogr.GetDriverByName("GeoJson")
        if os.path.exists(output):
            outdrv.DeleteDataSource(output)
        outdata  = outdrv.CreateDataSource(output)
        self.outlayer = outdata.CreateLayer("buildings", geom_type=ogr.wkbPolygon)
        fields = self.outlayer.GetLayerDefn()
        newid = ogr.FieldDefn("id", ogr.OFTInteger)
        self.outlayer.CreateField(newid)
        bld = ogr.FieldDefn("tags", ogr.OFTString)
        self.outlayer.CreateField(bld)

    def getBuildings(self, boundary=None, infile=None, outfile=None):
        """Extract buildings from a disk file"""
        logging.info("Extracting buildings from %s..." % infile)
        

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
    parser.add_argument("-c", "--category", default="buildings", choices=['buildings', 'amenities'], help='Which category to extract')
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
    pg.getBuildings(args.boundary, args.geojson)    
elif args.overpass:
    logging.info("Using Overpass Turbo for the data source")
    op = OverpassClient(args.geojson)
    op.getBuildings(args.boundary, args.geojson)        
elif args.infile:
    # FileClient()
    logging.info("Using file %s for the data source" % args.infile)
else:
    logging.error("You need to supply either --overpass or --postgres")
    
