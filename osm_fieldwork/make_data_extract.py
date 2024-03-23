#!/usr/bin/python3

# Copyright (c) 2022 Humanitarian OpenStreetMap Team
#
# This file is part of OSM-Fieldwork.
#
#     OSM-Fieldwork is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     OSM-Fieldwork is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with OSM-Fieldwork.  If not, see <https:#www.gnu.org/licenses/>.
#

import argparse
import logging
import os
import sys
from io import BytesIO

import geojson
import yaml
from geojson import FeatureCollection, dump
from osm_rawdata.config import QueryConfig
from osm_rawdata.postgres import PostgresClient
from shapely.geometry import shape

from osm_fieldwork.data_models import data_models_path
from osm_fieldwork.filter_data import FilterData
from osm_fieldwork.xlsforms import xlsforms_path

# Instantiate logger
log = logging.getLogger(__name__)


def getChoices():
    """Get the categories and associated XLSFiles from the config file.

    Returns:
        (list): A list of the XLSForms included in osm-fieldwork
    """
    data = dict()
    if os.path.exists(f"{data_models_path}/category.yaml"):
        file = open(f"{data_models_path}/category.yaml", "r").read()
        contents = yaml.load(file, Loader=yaml.Loader)
        for entry in contents:
            [[k, v]] = entry.items()
            data[k] = v[0]
    return data


class MakeExtract(object):
    """Class to handle SQL queries for the categories."""

    def __init__(
        self,
        dburi: str,
        config: str,
        xlsfile: str,
    ):
        """Initialize the postgres handler.

        Args:
            dburi (str): The URI string for the database connection
            config (str): The filespec for the query config file
            xlsfile (str): The filespec for the XLSForm file

        Returns:
            (MakeExtract): An instance of this object
        """
        self.db = PostgresClient(dburi, f"{data_models_path}/{config}.yaml")

        # Read in the XLSFile
        if "/" in xlsfile:
            file = open(xlsfile, "rb")
        else:
            file = open(f"{xlsforms_path}/{xlsfile}", "rb")
        self.xls = BytesIO(file.read())
        self.config = QueryConfig(config)

    def getFeatures(
        self,
        boundary: FeatureCollection,
        polygon: bool,
    ):
        """Extract features from Postgres.

        Args:
            boundary (str): The filespec for the project AOI in GeoJson format
            filespec (str): The optional output file for the query
            polygon (bool): Whether to have the full geometry or just centroids returns

        Returns:
            (FeatureCollection): The features returned from the query
        """
        log.info("Extracting features from Postgres...")

        if "features" in boundary:
            poly = boundary["features"][0]["geometry"]
        else:
            poly = boundary["geometry"]
        shape(poly)

        collection = self.db.execQuery(boundary, None, False)
        if not collection:
            return None

        return collection

    def cleanFeatures(
        self,
        collection: FeatureCollection,
    ):
        """Filter out any data not in the data_model.

        Args:
            collection (bytes): The input data or filespec to the input data file

        Returns:
            (FeatureCollection): The modifed data

        """
        log.debug("Cleaning features")
        cleaned = FilterData()
        cleaned.parse(self.xls, self.config)
        new = cleaned.cleanData(collection)
        # jsonfile = open(filespec, "w")
        # dump(new, jsonfile)
        return new


def main():
    """This program makes data extracts from OSM data, which can be used with ODK Collect."""
    getChoices()

    parser = argparse.ArgumentParser(
        prog="make_data_extract",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Make GeoJson data file for ODK from OSM",
        epilog="""
        This program makes data extracts for ODK Collect. It uses
        either a local postgres database, or the remote Underpass
        database, which is updated every minute for the planet.

        Because ODK Collect won't launch if there are tags in the
        data extract not also in the choices sheet, this program
        filters the data based on the XLSForm.

        example:
            make_data_extract -b [POLY] -c [CONFIG] -x [XLSFORM] -u [URI]

            Where POLY is a boundary polygon for the extract, and
            CONFIG is YAML or JSON config for the query, and
            XLSFILE is the XLSForm for this data collection,
            and URI is the database URI.

        The defaults are buildings.yaml for the config file,
        buildings.xls for the XLSForm, and for the database,
        it uses the remote Underpass database.
        """,
    )
    parser.add_argument("-v", "--verbose", nargs="?", const="0", help="verbose output")
    parser.add_argument("-p", "--polygon", action="store_true", default=False, help="Output polygons instead of centroids")
    parser.add_argument("-g", "--geojson", default="extract.geojson", help="Name of the GeoJson output file")
    parser.add_argument("-u", "--uri", default="underpass", help="Database URI")
    parser.add_argument("-b", "--boundary", required=True, help="Boundary polygon to limit the data size")
    parser.add_argument("-c", "--config", default="buildings.yaml", help="Config file for the query")
    parser.add_argument("-x", "--xlsfile", default="buildings.xls", help="XLSForm for this data collection")
    parser.add_argument("-l", "--list", action="store_true", help="List files in the XLSForm library")
    args = parser.parse_args()

    if args.list:
        files = getChoices()
        for k, v in files.items():
            print(f"Category: {k},  XLSForm: {v}")
        quit()

    # if verbose, dump to the terminal.
    if args.verbose is not None:
        logging.basicConfig(
            level=logging.DEBUG,
            format=("%(asctime)s.%(msecs)03d [%(levelname)s] " "%(name)s | %(funcName)s:%(lineno)d | %(message)s"),
            datefmt="%y-%m-%d %H:%M:%S",
            stream=sys.stdout,
        )

    extract = MakeExtract(args.uri, args.config, args.xlsfile)
    file = open(args.boundary, "r")
    poly = geojson.load(file)
    data = extract.getFeatures(poly, args.polygon)
    log.debug(f"Query returned {len(data['features'])} features")
    # FIXME: just for debugging before filtering!
    # if len(data['features']) > 0:
    #     jsonfile = open(args.geojson, "w")
    #     dump(data, jsonfile)
    #     jsonfile.close()

    cleaned = extract.cleanFeatures(data)

    jsonfile = open(args.geojson, "w")
    dump(cleaned, jsonfile)
    jsonfile.close()

    log.info("Wrote output data file to: %s" % args.geojson)


if __name__ == "__main__":
    """This is just a hook so this file can be run standalone during development."""
    main()
