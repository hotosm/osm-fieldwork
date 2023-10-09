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
import concurrent.futures
import logging
import os
import sys

import geojson
import shapely
from codetiming import Timer
from cpuinfo import get_cpu_info
from geojson import Point
from haversine import Unit, haversine
from osm_rawdata.postgres import PostgresClient
from shapely.geometry import mapping, shape
from thefuzz import fuzz

from osm_fieldwork.convert import escape
from osm_fieldwork.data_models import data_models_path
from osm_fieldwork.osmfile import OsmFile

# Instantiate logger
log = logging.getLogger(__name__)

# The number of threads is based on the CPU cores
info = get_cpu_info()
cores = info["count"]


class OdkMerge(object):
    def __init__(
        self,
        source: str,
        boundary: str = None,
    ):
        """Initialize Input data source.

        Args:
            source (str):
            boundary: str = None

        Returns:
            (OdkMerge): An instance of this object
        """
        self.postgres = list()
        self.source = source
        self.tags = dict()
        # Distance in meters for conflating with postgis
        self.tolerance = 7
        self.data = dict()
        self.analyze = ("name", "amenity", "landuse", "cuisine", "tourism", "leisure")
        # PG: is the same prefix as ogr2ogr
        # "[user[:password]@][netloc][:port][/dbname]"
        if source[0:3] == "PG:":
            uri = source[3:]
            # self.source = "underpass" is not support yet
            # Each thread needs it's own connection to postgres to avoid problems.
            for _thread in range(0, cores + 1):
                db = PostgresClient(uri, f"{data_models_path}/{config}")
                self.postgres.append(db)
                if boundary:
                    self.clip(boundary, db)
        else:
            log.info("Opening data file: %s" % source)
            src = open(source, "r")
            self.data = geojson.load(src)
            if boundary:
                self.clip(boundary)

    def clip(
        self,
        boundary: str,
        db: PostgresClient,
    ):
        """Clip a data source by a boundary.

        Args:
             boundary (str): The filespec of the project AOI
             db (PostgresClient): A reference to the existing database connection

        Returns:
            (bool): If the region was clipped sucessfully
        """
        if not boundary:
            return False

        if type(boundary) != dict:
            clip = open(boundary, "r")
            geom = geojson.load(clip)
            if "features" in geom:
                poly = geom["features"][0]["geometry"]
            else:
                poly = geom["geometry"]
        else:
            poly = boundary
        ewkt = shape(poly)

        if len(self.data) > 0:
            # TODO: FMTM produces data extracts the exact size of the boundary
            # polygon, so  we don't need to clip it. In the future though we
            # want this to produce a subset from a larger file.
            for feature in self.data["features"]:
                shapely.from_geojson(str(feature))
            #     if not shapely.contains(ewkt, entry):
            #         log.debug(f"CONTAINS {entry}")
            #         del self.data[self.data['features']]
            pass
        else:
            # setup the postgres VIEWs with a dummy SQL query
            sql = "SELECT COUNT(osm_id) FROM nodes"
            db.queryLocal(sql, ewkt)
        return True

    def makeNewFeature(
        self,
        attrs: dict = None,
        tags: dict = None,
    ):
        """Create a new feature with optional data.

        Args:
            attrs (dict): All of the attributes and their values
            tags (dict): All of the tags and their values

        Returns:
            (dict): A template feature with no data
        """
        newf = dict()
        if attrs:
            newf["attrs"] = attrs
        else:
            newf["attrs"] = dict()
        if tags:
            newf["tags"] = tags
        else:
            newf["tags"] = dict()
        return newf

    def conflateFile(
        self,
        feature: dict,
    ):
        """Conflate a POI against all the features in a GeoJson file.

        Args:
            feature (dict): The feature to conflate

        Returns:
            (dict):  The modified feature
        """
        # Most smartphone GPS are 5-10m off most of the time, plus sometimes
        # we're standing in front of an amenity and recording that location
        # instead of in the building.
        gps_accuracy = 10
        # this is the treshold for fuzzy string matching
        match_threshold = 80
        # log.debug(f"conflateFile({feature})")
        hits = False
        geom = Point((float(feature["attrs"]["lon"]), float(feature["attrs"]["lat"])))
        wkt = shape(geom)
        for existing in self.data["features"]:
            id = int(existing["properties"]["id"])
            entry = shapely.from_geojson(str(existing))
            if entry.geom_type != "Point":
                center = shapely.centroid(entry)
            else:
                center = entry
                # dist = shapely.hausdorff_distance(center, wkt)
                # if 'name' in existing['properties']:
                #     print(f"DIST1: {dist}, {existing['properties']['name']}")
            # x = shapely.distance(wkt, entry)
            # haversine reverses the order of lat & lon from what shapely uses. We
            # use this as meters is easier to deal with than cartesian coordinates.
            x1 = (center.coords[0][1], center.coords[0][0])
            x2 = (wkt.coords[0][1], wkt.coords[0][0])
            dist = haversine(x1, x2, unit=Unit.METERS)
            if dist < gps_accuracy:
                # if 'name' in existing['properties']:
                # log.debug(f"DIST2: {dist}")
                # log.debug(f"Got a Hit! {feature['tags']['name']}")
                for key, value in feature["tags"].items():
                    if key in self.analyze:
                        if key in existing["properties"]:
                            result = fuzz.ratio(value, existing["properties"][key])
                            if result > match_threshold:
                                # log.debug(f"Matched: {result}: {feature['tags']['name']}")
                                existing["properties"]["fixme"] = "Probably a duplicate!"
                                log.debug(f"Got a dup in file!!! {existing['properties']['name'] }")
                                hits = True
                                break
            if hits:
                version = int(existing["properties"]["version"])
                # coords = feature['geometry']['coordinates']
                # lat = coords[1]
                # lon = coords[0]
                attrs = {"id": id, "version": version, "lat": feature["attrs"]["lat"], "lon": feature["attrs"]["lon"]}
                tags = existing["properties"]
                tags["fixme"] = "Probably a duplicate!"
                # Data extracts for ODK Collect
                del tags["title"]
                del tags["label"]
                if "building" in tags:
                    return {"attrs": attrs, "tags": tags, "refs": list()}
                return {"attrs": attrs, "tags": tags}
        return dict()

    def conflateWay(
        self,
        feature: dict,
        dbindex: int,
    ):
        """Conflate a POI against all the ways in a postgres view.

        Args:
            feature (dict): The feature to conflate
            dbindex (int): An index into the array of postgres connections

        Returns:
            (dict):  The modified feature
        """
        # log.debug(f"conflateWay({feature})")
        hits = False
        result = list()
        geom = Point((float(feature["attrs"]["lon"]), float(feature["attrs"]["lat"])))
        wkt = shape(geom)
        for key, value in feature["tags"].items():
            if key in self.analyze:
                # Sometimes the duplicate is a polygon, really common for parking lots.
                cleanval = escape(value)
                query = f"SELECT osm_id,tags,version,ST_AsText(ST_Centroid(geom)) FROM ways_view WHERE ST_Distance(geom::geography, ST_GeogFromText('SRID=4326;{wkt.wkt}')) < {self.tolerance} AND levenshtein(tags->>'{key}', '{cleanval}') <= 1"
                # log.debug(query)
                self.postgres[dbindex].dbcursor.execute(query)
                try:
                    result = self.postgres[dbindex].dbcursor.fetchall()
                except:
                    result = list()
                    # log.warning(f"No results at all for {query}")
                if len(result) > 0:
                    hits = True
                    break
        if hits:
            log.debug(f"Got a dup in ways!!! {feature['tags']['name']}")
            # the result is a list from what we specify for SELECT
            version = int(result[0][2]) + 1
            attrs = {"id": int(result[0][0]), "version": version}
            tags = result[0][1]
            tags[f"old_{key}"] = value
            tags["fixme"] = "Probably a duplicate!"
            geom = mapping(shapely.from_wkt(result[0][3]))
            refs = list()
            # FIXME: iterate through the points and find the existing nodes,
            # which I'm not sure
            # is possible
            # SELECT osm_id,tags,version FROM nodes WHERE ST_Contains(geom, ST_GeomFromText('Point(-105.9918636 38.5360821)'));
            # for i in geom['coordinates'][0]:
            #    print(f"XXXXX: {i}")
            return {"attrs": attrs, "tags": tags, "refs": refs}
        return dict()

    def conflateNode(
        self,
        feature: dict,
        dbindex: int,
    ):
        """Conflate a POI against all the nodes in the view.

        Args:
            feature (dict): The feature to conflate
            dbindex (int): An index into the array of postgres connections

        Returns:
            (dict):  The modified feature
        """
        # log.debug(f"conflateNode({feature})")
        hits = False
        geom = Point((float(feature["attrs"]["lon"]), float(feature["attrs"]["lat"])))
        wkt = shape(geom)
        result = list()
        ratio = 1
        for key, value in feature["tags"].items():
            if key in self.analyze:
                # print("%s = %s" % (key, value))
                # Use a Geography data type to get the answer in meters, which
                # is easier to deal with than degress of the earth.
                cleanval = escape(value)
                query = f"SELECT osm_id,tags,version,ST_AsEWKT(geom) FROM nodes_view WHERE ST_Distance(geom::geography, ST_GeogFromText('SRID=4326;{wkt.wkt}')) < {self.tolerance} AND levenshtein(tags->>'{key}', '{cleanval}') <= {ratio}"
                # print(query)
                # FIXME: this currently only works with a local database, not underpass yet
                self.postgres[dbindex].dbcursor.execute(query)
                try:
                    result = self.postgres[dbindex].dbcursor.fetchall()
                except:
                    result = list()
                    # log.warning(f"No results at all for {query}")
                if len(result) > 0:
                    hits = True
                    break
        if hits:
            log.debug(f"Got a dup in nodes!!! {feature['tags']}")
            version = int(result[0][2]) + 1
            coords = shapely.from_wkt(result[0][3][10:])
            lat = coords.y
            lon = coords.x
            attrs = {"id": int(result[0][0]), "version": version, "lat": lat, "lon": lon}
            tags = result[0][1]
            tags[f"old_{key}"] = value
            tags["fixme"] = "Probably a duplicate!"
            return {"attrs": attrs, "tags": tags}
        return dict()

    def conflateById(
        self,
        feature: dict,
        dbindex: int,
    ):
        """Conflate a feature with existing ways using the OSM ID.

        Args:
            feature (dict): The feature to conflate
            dbindex (int): An index into the array of postgres connections

        Returns:
            (dict):  The modified feature
        """
        log.debug(f"conflateById({feature})")
        id = int(feature["attrs"]["id"])
        if id > 0:
            if self.source[:3] != "PG:":
                sql = f"SELECT osm_id,tags,version,ST_AsText(geom) FROM ways_view WHERE tags->>'id'='{id}'"
                # log.debug(sql)
                self.postgres[0].dbcursor.execute(sql)
                result = self.postgres[0].dbcursor.fetchone()
                if result:
                    version = int(result[0][2]) + 1
                    attrs = {"id": int(result[0][0]), "version": version}
                    tags = result[0][1]
                    # tags[f'old_{key}'] = value
                    tags["fixme"] = "Probably a duplicate!"
                    mapping(shapely.from_wkt(result[0][3]))
                    return {"attrs": attrs, "tags": tags}
                else:
                    sql = f"SELECT osm_id,tags,version,ST_AsText(geom) FROM ways_view WHERE tags->>'id'='{id}'"
                    # log.debug(sql)
                    self.postgres[dbindex].dbcursor.execute(sql)
                    result = self.postgres[dbindex].dbcursor.fetchone()
                    if result:
                        version = int(result[0][2]) + 1
                        attrs = {"id": int(result[0][0]), "version": version}
                        tags = result[0][1]
                        # tags[f'old_{key}'] = value
                        tags["fixme"] = "Probably a duplicate!"
                        mapping(shapely.from_wkt(result[0][3]))
                    return {"attrs": attrs, "tags": tags, "refs": refs}
            else:
                for key, value in self.data.items():
                    if key == id:
                        return value
        return dict()

    def cleanFeature(
        self,
        feature: dict,
    ):
        """Remove tags that are attributes instead
        Args:
            feature (dict): The feature to clean.

        Returns:
            (dict):  The modified feature
        """
        # We only use the version and ID in the attributes
        if "id" in feature["tags"]:
            del feature["tags"]["id"]
        if "version" in feature["tags"]:
            del feature["tags"]["version"]
        if "title" in feature["tags"]:
            del feature["tags"]["title"]
        if "label" in feature["tags"]:
            del feature["tags"]["label"]
        return feature

    def dump(self):
        """Dump internal data."""
        print(f"Data source is: {self.source}")
        print(f"There are {len(self.data)} existing features")
        # if len(self.versions) > 0:
        #     for k, v in self.original.items():
        #         print(f"{k}(v{self.versions[k]}) = {v}")

    def conflateData(
        self,
        odkdata: list,
    ):
        """Conflate all the data. This the primary interfacte for conflation.

        Args:
            odkdata (list): A list of all the entries in the OSM XML input file

        Returns:
            (dict):  The modified features
        """
        timer = Timer(text="conflateData() took {seconds:.0f}s")
        timer.start()
        # Use fuzzy string matching to handle minor issues in the name column,
        # which is often used to match an amenity.
        if len(self.data) == 0:
            self.postgres[0].dbcursor.execute("CREATE EXTENSION IF NOT EXISTS fuzzystrmatch")
        log.debug(f"OdkMerge::conflateData() called! {len(odkdata)} features")

        # A chunk is a group of threads
        chunk = round(len(odkdata) / cores)

        # cycle = range(0, len(odkdata), chunk)

        # Chop the data into a subset for each thread
        newdata = list()
        future = None
        result = None
        index = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=cores) as executor:
            i = 0
            subset = dict()
            futures = list()
            for key, value in odkdata.items():
                subset[key] = value
                if i == chunk:
                    i = 0
                    result = executor.submit(conflateThread, subset, self, index)
                    index += 1
                    # result.add_done_callback(callback)
                    futures.append(result)
                    subset = dict()
                i += 1
            for future in concurrent.futures.as_completed(futures):
                # # for future in concurrent.futures.wait(futures, return_when='ALL_COMPLETED'):
                log.debug("Waiting for thread to complete..")
                # print(f"YYEESS!! {future.result(timeout=10)}")
                newdata.append(future.result(timeout=5))
        timer.stop()
        return newdata
        # return alldata


def conflateThread(
    features: dict,
    source: str,
    dbindex: int,
):
    """Conflate a subset of the data.

    Args:
        feature (dict): The feature to conflate
        source (str): The data source for conflation, file or database
        dbindex (int): An index into the array of postgres connections

    Returns:
    """
    timer = Timer(text="conflateThread() took {seconds:.0f}s")
    timer.start()
    log.debug(f"conflateThread() called! {len(features)} features")
    merged = list()
    result = dict()
    dups = 0
    # This is brute force, slow but accurate. Process each feature
    # and look for a possible match with existing data.
    for _key, value in features.items():
        id = int(value["attrs"]["id"])
        # Each of the conflation methods take a single feature
        # as a parameter, and returns a possible match or a zero
        # length dictionary.
        if id > 0:
            # Any feature ID greater than zero is existing data.
            if source.source[:3] != "PG:":
                result = source.conflateFile(value)
            else:
                # Any feature ID less than zero is new data collected
                # using geopoint in the XLSForm.
                result = source.conflateById(value, dbindex)
        elif id < 0:
            if source.source[:3] != "PG:":
                result = source.conflateFile(value)
            else:
                result = source.conflateNode(value, dbindex)
                if len(result) == 0:
                    result = source.conflateWay(value, dbindex)
        if result and len(result) > 0:
            # Merge the tags and attributes together, the OSM data and ODK data.
            # If no match is found, the ODK data is used to create a new feature.
            if "fixme" in result["tags"]:
                dups += 1
                # newf = source.cleanFeature(result)
                attrs = value["attrs"] | result["attrs"]
                tags = value["tags"] | result["tags"]
                merged.append({"attrs": attrs, "tags": tags})
            else:
                merged.append(value)
        else:
            merged.append(value)
            # log.error(f"There are no results!")
    timer.stop()
    log.debug(f"Found {dups} duplicates")
    return merged


def main():
    """This main function lets this class be run standalone by a bash script."""
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
        OR refix with "PG:[url]" to use a postgres database
        """,
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-o", "--outfile", help="Output file from the conflation")
    # parser.add_argument("-e", "--extract",  help="OSM data extract created by Osm-Fieldwork")
    # parser.add_argument("-f", "--odkfile",  required=True, help="OSM XML file created by Osm-Field")
    parser.add_argument("-b", "--boundary", help="Boundary polygon to limit the data size")

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
        log.setLevel(logging.DEBUG)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(threadName)10s - %(name)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        log.addHandler(ch)

    if args.outfile:
        outfile = args.outfile
    else:
        outfile = os.path.basename(osmdata.replace(".osm", "-foo.osm"))

    # This is the existing OSM data, a database or a file
    if args.boundary:
        extract = OdkMerge(source, args.boundary)
    else:
        extract = OdkMerge(source)

    if extract:
        odkf = OsmFile(outfile)  # output file
        osm = odkf.loadFile(osmdata)  # input file
        # odkf.dump()
    else:
        log.error("No ODK data source specified!")
        parser.print_help()
        quit()

    # This returns a list of lists of dictionaries. Each thread returns
    # a list of the features, and len(data) is thre number of CPU cores.
    data = extract.conflateData(osm)
    out = list()
    # print(data)
    for entry in data:
        # if 'refs' in feature or 'building' in feature['tags']:
        for feature in entry:
            if "refs" in feature:
                feature["refs"] = list()
                out.append(odkf.createWay(feature, True))
            else:
                out.append(odkf.createNode(feature, True))

    # out = ""
    # for id, feature in osm.items():
    #     result = extract.conflateFile(feature)
    #     if len(result) > 0:
    #         node = odkf.featureToNode(result)
    #     else:
    #         node = feature
    #     out += odkf.createNode(node, True)
    odkf.write(out)
    log.info(f"Wrote {outfile}")


if __name__ == "__main__":
    """This is just a hook so this file can be run standlone during development."""
    main()
