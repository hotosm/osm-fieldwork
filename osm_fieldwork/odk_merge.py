#!/usr/bin/python3

# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
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
import sys
import os
from sys import argv
from osgeo import ogr
from osm_fieldwork.osmfile import OsmFile
from geojson import Point, Feature, FeatureCollection, dump, Polygon
import geojson
import psycopg2
from shapely.geometry import shape, Polygon
import shapely
from shapely import wkt
import xmltodict
from progress.bar import Bar, PixelBar
from progress.spinner import PixelSpinner
from osm_fieldwork.convert import escape
from osm_fieldwork.make_data_extract import PostgresClient, uriParser
from codetiming import Timer
import concurrent.futures
from cpuinfo import get_cpu_info
from time import sleep
import itertools


# Instantiate logger
log = logging.getLogger(__name__)
# The number of threads is based on the CPU cores
info = get_cpu_info()
cores = info['count']

class OdkMerge(PostgresClient):
    def __init__(self,
                 source: str,
                 boundary: str = None
                 ):
        """Initialize Input data source"""
        self.geojson = None
        self.source = source
        self.original = dict()
        self.tags = dict()
        # self.versions = dict()
        self.geometries = dict()
        # Distance in meters for conflating with postgis
        self.tolerance = 2
        # PG: is the same prefix as ogr2ogr
        # "[user[:password]@][netloc][:port][/dbname]"
        if source[0:3] == "PG:":
            uri = uriParser(source[3:])
            # self.source = "underpass"
            super().__init__(dbhost=uri['dbhost'], dbname=uri['dbname'], dbuser=uri['dbuser'], dbpass=uri['dbpass'])
            if boundary:
                self.extract.clip(boundary)
        else:
            log.info("Opening data file: %s" % source)
            src = open(source, "r")
            data = geojson.load(src)
            id = 0
            for feature in data['features']:
                geom = feature['geometry']
                if 'tags' in feature['properties']:
                    tags = feature['properties']['tags']
                else:
                    tags = feature['properties']
                if 'version' in feature['properties']:
                    version = feature['properties']['version']
                else:
                    version = 1
                if 'osm_id' not in feature['properties'] and 'id' not in feature['properties']:
                    log.error(f"Bad feature! {feature['properties']}")
                else:
                    if 'osm_id' in feature['properties']:
                        id = int(feature['properties']['osm_id'])
                    elif 'id' in feature['properties']:
                        id = int(feature['properties']['id'])
                    # store just the tags, not the atttributes
                    self.original[id] = tags
                    # the only attribute other than the ID we want is the version,
                    # since it has to be incremented if changed
                    # self.versions[id] = version
                    # if type(geom) == geojson.geometry.Polygon:
                    #     # import epdb; epdb.st()
                    #     wkt = shape(geom)
                    #     center = shapely.centroid(wkt)
                    #     self.geometries[id] = center
                    # else:
                    self.geometries[id] = geom

    def clip(self,
             boundary: str
             ):
        """Clip a data source by a boundary"""
        if not boundary:
            return False

        if type(boundary) != dict:
            clip = open(boundary, "r")
            geom = geojson.load(clip)
            if 'features' in geom:
                poly = geom['features'][0]['geometry']
            else:
                poly = geom["geometry"]
        else:
            poly = boundary
        ewkt = shape(poly)

        remove = list()
        if len(self.original) > 0:
            for id, feature in self.original.items():
                obj = shape(self.geometries[id])
                contains = shapely.contains(ewkt, obj)
                if not contains:
                    remove.append(id)
            for id in remove:
                del self.original[id]
                # FIXME: as long as self.original is used as the primary
                # data source, the other dictionaries don't need to
                # have items removed.
                # del self.versions[id]
                # del self.geometries[id]
            return True

        if self.dbcursor is not None:
            log.info("Clipping using %s" % (boundary))
            sql = f"DROP VIEW IF EXISTS ways_view;CREATE TEMP VIEW ways_view AS SELECT * FROM ways_poly WHERE ST_CONTAINS(ST_GeomFromEWKT('SRID=4326;{ewkt.wkt}'), geom)"
            self.dbcursor.execute(sql)
            sql = f"DROP VIEW IF EXISTS nodes_view;CREATE TEMP VIEW nodes_view AS SELECT * FROM nodes WHERE ST_CONTAINS(ST_GeomFromEWKT('SRID=4326;{ewkt.wkt}'), geom)"
            self.dbcursor.execute(sql)
            sql = f"DROP VIEW IF EXISTS relations_view;CREATE TEMP VIEW relations_view AS SELECT * FROM relations WHERE ST_CONTAINS(ST_GeomFromEWKT('SRID=4326;{ewkt.wkt}'), geom)"
            self.dbcursor.execute(sql)

            result = self.dbcursor.execute(f"SELECT COUNT(uid) FROM ways_view")
            result = self.dbcursor.fetchone()
            ways = int(result[0])

            nodes = self.dbcursor.execute(f"SELECT COUNT(uid) FROM nodes_view")
            result = self.dbcursor.fetchone()
            nodes = int(result[0])
            if ways + nodes == 0:
                return False

        return True

    def compareTags(self,
                  osm: str,
                  odk: str
                  ):
        """Merge two sets of tags together"""
        if str(osm).lower() < str(odk).lower():
            # logging.debug("No changes made to tags")
            return osm
        else:
            # logging.debug("Changes tags")
            return odk
        return None

    def mergeTags(self,
                     odkdata: dict,
                     ):
        """Conflate the ODK data with what is in the origin data extract"""
        data = list()
        newf = dict()
        if type(odkdata) == dict:
            if len(self.original) > 0:
                for id, feature in odkdata.items():
                    if id == 'attrs':
                        id = feature['attrs']['id']
                    if int(id) < 0:
                        data.append(feature)
                        continue
                    if int(id) in self.original:
                        # print(f"Got match for {self.original[int(id)]}")
                        newf['attrs'] = feature['attrs']
                        newf['attrs']['id'] = int(id)
                        newf['tags'] = dict()
                        tags = self.original[int(id)]
                        for k, v in tags.items():
                            tag = dict()
                            if k in feature['tags']:
                                value = self.compareTags(v, feature['tags'][k])
                                newf['tags'][k] = value
                            else:
                                newf['tags'][k] = v
                    data.append(newf)
            else:
                for id, feature in odkdata['tags'].items():
                    if int(id) < 0:
                        data.append(feature)
                        continue
                    else:
                        name = feature['tags']['name'].replace("'", '&apos;')
                        sql = f"SELECT tags FROM ways_view WHERE osm_id='{id}'"
                        # log.debug(sql)
                        self.dbcursor.execute(sql)
                        result = self.dbcursor.fetchone()
                        log.debug(f"Got {result} results in ways for ID {id}")
                        newf['attrs'] = feature['attrs']
                        # if this feature exists in the database, get all the tags
                        if result is not None and len(result) > 0:
                            tags = result[0]
                            newf['tags'] = tags
                            data.append(newf)
                        else:
                            sql = f"SELECT tags FROM nodes_view WHERE osm_id='{id}'"
                            log.debug(sql)
                            self.dbcursor.execute(sql)
                            result = self.dbcursor.fetchone()
                            log.debug(f"Got {result} results in nodes for ID {id}")
                            if result is not None and len(result) > 0:
                                tags = result[0]
                                newf['tags'] = tags
                                data.append(newf)

        return data

    def querySource(self,
                    entry: dict
                    ):
        """See if the entry has a match in existing data"""
        if len(self.geometries) == 0 and self.source[:3] == "PG:":
            id = int(entry['attrs']['id'])
            # any feature with a negative ID was collected via GPS,
            # and not by editing existing data with ODK
            if id < 0:
                results = self.conflateNode(entry)
                if len(results) > 0:
                    import epdb; epdb.st()
                    return results
                else:
                    return entry

    def makeNewFeature(self,
                       attrs: dict = None,
                       tags: dict = None
                       ):
        """Create a new feature with optional data"""
        newf = dict()
        if attrs:
            newf['attrs'] = attrs
        else:
            newf['attrs'] = dict()
        if tags:
            newf['tags'] = tags
        else:
            newf['tags'] = dict()
        return newf

    def conflateWays(self, feature):
        hits = False
        for key, value in feature['properties'].items():
            if key == 'amenity':
                # Sometimes the duplicate is a polygon, really common for parking lots.
                query = "SELECT osm_id,geom,tags FROM ways_view WHERE ST_Distance(ST_Centroid(geom::geography), ST_GeogFromText(\'SRID=4326;%s\')::geography) < %s AND tags->>'%s'='%s' AND tags->>'amenity' IS NOT NULL" % (wkt.wkt, tolerance, key, value.replace("\'", "&apos;"))
                # print(query)
                dbcursor.execute(query)
                all = dbcursor.fetchall()
                if len(all) > 0:
                    # log.debug(f"WAY: {all}")
                    if 'name' in all and name == all['name']:
                        log.debug(f"Same name!: {name}")
                        hits = True
                        break
            # We only need one good hit to identify a duplicate
            if hits:
                return True
            else:
                return False

    def conflateNode(self, feature):
        """Conflate a feature """
        hits = False
        geom = Point((float(feature["attrs"]["lon"]), float(feature["attrs"]["lat"])))
        wkt = shape(geom)
        for key,value in feature['tags'].items():
            # print("%s = %s" % (key, value))
            # Use a Geography data type to get the answer in meters, which
            # is easier to deal with than degress of the earth.
            cleanval = escape(value)
            query = f"SELECT osm_id,geom,tags FROM nodes_view WHERE ST_Distance(geom::geography, ST_GeogFromText(\'SRID=4326;{wkt.wkt}\')) < {self.tolerance} AND tags->>'{key}'='{cleanval}'"
            print(query)
            # FIXME: this currently only works with a local database, not underpass yet
            self.dbcursor.execute(query)
            all = self.dbcursor.fetchall()
            if len(all) > 0:
                hits = True
                break
        if hits:
            feature['tags']['fixme'] = "Probably a duplicate!"
            all.append(feature)
            return all
        return dict()

    def conflateById(self, feature):
        """Conflate a feature with existing ways"""
        id = int(feature['attrs']['id'])

        # Anything with a negative ID is a new feature
        #if id < 0:
        #    return feature

        newf = self.makeNewFeature()
        existing = dict()
        if len(self.original) > 0 and id > 0:
            if id in self.original:
                existing = self.original[id]
                geom = self.geometries[id]
                ewkt = shape(geom)
        else:
            poi = Point((float(feature["attrs"]["lon"]), float(feature["attrs"]["lat"])))
            ewkt = shape(poi)

        # See if the POI from ODK is in a building
        # sql = f"SELECT tags, ST_AsEWKT(geom) FROM ways_view WHERE osm_id='{id}' OR tags->>'name'='{feature['tags']['name']} OR ST_CONTAINS(ST_GeomFromEWKT('SRID=4326;{ewkt.wkt}'), geom)'"
        sql = f"SELECT tags, ST_AsEWKT(geom), osm_id FROM ways_view WHERE tags->>'building' IS NOT NULL and ST_CONTAINS(geom, ST_GeomFromEWKT('SRID=4326;{ewkt.wkt}'))"
        # log.debug(sql)
        self.dbcursor.execute(sql)
        result = self.dbcursor.fetchone()
        if result:
            # Yes, this POI is in a building
            tags = result[0]
            id = int(result[2])
            log.debug(f"The POI is in way ID {id}")
            ewkt = result[1]

        sql = f"SELECT tags, ST_AsEWKT(geom), osm_id FROM nodes_view WHERE ST_CONTAINS(ST_GeomFromEWKT('{ewkt}'), geom)"
        # log.debug(sql)
        self.dbcursor.execute(sql)
        result = self.dbcursor.fetchone()
        if result:
            id = int(result[2])
            log.debug(f"There is another POI is in way ID {id}")

        newf['tags'] = feature['tags']
        return newf

    def dump(self):
        """Dump internal data"""
        print(f"Data source is: {self.source}")
        print(f"There are {len(self.original)} existing features")
        for k, v in self.original.items():
            print(f"{k}(v{self.versions[k]}) = {v}")

    def conflateData(self,
                     odkdata: list,
                     ):
        """Conflate all the data"""
        # timer = Timer()
        # timer.start()
        odkf = OsmFile() # output file
        osm = odkf.loadFile(osmdata) # input file
        log.debug(f"OdkMerge::conflateThread() called! {len(osm)} features")
        # sliced = list()
        # A chunk is a group of threads
        chunk =  round(len(osm)/cores)
        cycle = range(0, len(osm), chunk)
        # Chop the data into a subset for each thread
        with concurrent.futures.ThreadPoolExecutor(max_workers = cores) as executor:
            i = 0
            subset = dict()
            for key, value in osm.items():
                subset[key] = value
                if i == chunk:
                    i = 0
                    conflateThread(subset)
                    result = {executor.submit(conflateThread, subset)}
                    subset = dict()
                    for future in concurrent.futures.as_completed(result):
                        log.debug(f"Waiting... {future.result()}")
                i += 1

        return odkdata

def conflateThread(features: dict):
    """Conflate a subset of the data"""
    # timer = Timer()
    # timer.start()
    log.debug(f"conflateThread() called! {len(features)} features")
    # timer.stop()
    return features


if __name__ == "__main__":


    # Command Line options
    parser = argparse.ArgumentParser(
        prog="odk_merge.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="This program conflates ODK data with existing features from OSM.",
        epilog="""
This program conflates the output from Osm-Fieldwork after converting
the JSON file from ODK Central to OSM XML. The data source for existing data can'
be either the data extract used by the XLSForm, or a postgresql database.

    examples:
        odk_merge.py [OPTIONS] [OSMFILE] [DATAFILE]
        Where OSMFILE is the output from json2osm.py
        And DATAFILE is either the data extract from make_data_extract.py,
        OR prefix with "PG:[url]" to use a postgres database
        """
    )
    parser.add_argument("-v", "--verbose",  action="store_true", help="verbose output")
    parser.add_argument("-o", "--outfile",  help="Output file from the conflation")
    # parser.add_argument("-e", "--extract",  help="OSM data extract created by Osm-Fieldwork")
    # parser.add_argument("-f", "--odkfile",  required=True, help="OSM XML file created by Osm-Field")
    parser.add_argument("-b", "--boundary", required=True, help="Boundary polygon to limit the data size")

    args, unknown = parser.parse_known_args()
    osmdata = None
    source = None
    if len(unknown) < 2:
        parser.print_help()
        quit()
    else:
        osmdata = unknown[0]
        source = unknown[1]

    # if verbose, dump to the terminal.
    if args.verbose:
        root = logging.getLogger()
        log.setLevel(logging.DEBUG)

        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        ch.setFormatter(formatter)
        root.addHandler(ch)

    if args.outfile:
        outfile = args.outfile
    else:
        outfile = os.path.basename(osmdata.replace('.osm', '-foo.osm'))

    # This is the existing OSM data, a database or a file
    extract = OdkMerge(source)
    #if args.boundary:
    #    extract.clip(args.boundary)
    if extract:
        odkf = OsmFile(outfile) # output file
        osm = odkf.loadFile(osmdata) # input file
        #odkf.dump()
    else:
        log.error("No ODK data source specified!")
        parser.print_help()
        quit()

    data = extract.conflateData(osm)
    odkf.write(data)
        
    # for id, entry in osm.items():
    #     hits = extract.querySource(entry)
    #     if len(hits) > 0:
    #         print(f"FIXME: {entry}")

    # # Get all the keys
    # key = list(osm.keys())[0]
    # data = list() # extract.mergeTags(osm[key])

    # for entry in data:
    #     if int(entry['attrs']['id']) < 0:
    #         # FIXME: Should scan the source spatially
    #         osmf.write(osmf.createNode(entry, True))
    #         continue
    #     else:
    #         log.debug(f"Need to conflate! {entry}")
    #         # FIXME: find the best key
    #         if 'id' in entry:
    #             feature = extract.conflateById(entry)
    #         if 'building' in feature['tags'] and feature['tags']['building'] == 'yes':
    #             entry['refs'] = {}
    #             osmf.write(osmf.createWay(entry, True))
    #         else:
    #             osmf.write(osmf.createNode(entry, True))

    odkf.footer()
    log.info(f"Wrote {outfile}")

    # # And also loads the POIs from the ODK Central submission
    # odkf.loadFile(args.odkfile)

    # for id in odkf.data:
    #     # print(odkf.data[id])
    #     feature = osmf.getFeature(odkf.data[id])
    #     out = list()
    #     if not feature:
    #         # logging.debug(f"No feature found for ID {id}")
    #         # feature = osmf.createFeature(odkf.data[id])
    #         out.append(odkf.createNode(odkf.data[id], modified=True))
    #     else:
    #         tags = osmf.mergeTags(feature["tags"], odkf.data[id]["tags"])
    #         if tags:
    #             odkf.data[id]["tags"] = tags
    #         if "name" in feature["tags"]:
    #             # if tags and odkf.data[id]['tags']['name'] != feature['tags']['name']:
    #             if tags:
    #                 out.append(odkf.createNode(odkf.data[id], modified=True))
    #         else:
    #             out.append(odkf.createWay(feature, modified=True))
    #     odkf.write(out)

    # # # FIXME: for now just copy the data file from Central
    # # # to test input parsing, and output accuracy.
    # # out = list()
    # # for id, node in odkf.data.items():
    # #     out.append(odkf.createNode(node, modified=True))
    # # odkf.write(out)
    # odkf.footer()
    # log.info("Wrote %s: " % args.outfile)

# osmoutfile = os.path.basename(args.infile.replace(".csv", ".osm"))
# csvin.createOSM(osmoutfile)
