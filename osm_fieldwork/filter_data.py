#!/usr/bin/python3

# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
#
# This file is part of osm-Fieldwork.
#
#     Osm-Fieldwork is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Underpass is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with osm_fieldwork.  If not, see <https:#www.gnu.org/licenses/>.
#

import argparse
import logging
import os
import sys

import geojson
import pandas as pd
from geojson import Feature, FeatureCollection
from osm_rawdata.config import QueryConfig

# from osm_fieldwork import package_root
# from osm_fieldwork.data_models import data_models_path
from osm_fieldwork.xlsforms import xlsforms_path

# Instantiate logger
log = logging.getLogger(__name__)


class FilterData(object):
    def __init__(
        self,
        filespec: str = None,
        config: QueryConfig = None,
    ):
        """Args:
            filespec (str): The optional data file to read.

        Returns:
            (FilterData): An instance of this object
        """
        self.tags = dict()
        self.qc = config
        if filespec and config:
            self.parse(filespec, config)

    def parse(
        self,
        filespec: str,
        config: QueryConfig,
    ):
        """Read in the XLSForm and extract the data we want.

        Args:
            filespec (str): The filespec to the XLSForm file

        Returns:
            title (str): The title from the XLSForm Setting sheet
            extract (str): The data extract filename from the XLSForm Survey sheet
        """
        if config:
            self.qc = config
        excel_object = pd.ExcelFile(filespec)
        entries = excel_object.parse(sheet_name=[0, 1, 2], index_col=0, usercols=[0, 1, 2])
        entries = pd.read_excel(filespec, sheet_name=[0, 1, 2])
        title = entries[2]["form_title"].to_list()[0]
        extract = ""
        for entry in entries[0]["type"]:
            if str(entry) == "nan":
                continue
            if entry[:20] == "select_one_from_file":
                extract = entry[21:]
                log.info(f'Got data extract filename: "{extract}", title: "{title}"')
            else:
                extract = "none"
        total = len(entries[1]["list_name"])
        index = 1
        while index < total:
            key = entries[1]["list_name"][index]
            if key == "model" or str(key) == "nan":
                index += 1
                continue
            value = entries[1]["name"][index]
            if value == "<text>" or str(value) == "null":
                index += 1
                continue
            if key not in self.tags:
                self.tags[key] = list()
            self.tags[key].append(value)
            index += 1

        # The yaml config file for the query has a list of columns
        # to keep in addition to this default set. These wind up
        # in the SELECT
        keep = (
            "name",
            "name:en",
            "id",
            "operator",
            "addr:street",
            "addr:housenumber",
            "osm_id",
            "title",
            "tags",
            "label",
            "landuse",
            "opening_hours",
            "tourism",
        )
        self.keep = list(keep)
        if "keep" in config["keep"]:
            self.keep.extend(config["keep"])

        return title, extract

    def cleanData(
        self,
        data,
    ):
        """Filter out any data not in the data_model.

        Args:
            data (bytes): The input data or filespec to the input data file

        Returns:
            (FeatureCollection): The modifed data

        """
        log.debug("Cleaning data...")
        if type(data) == str:
            outfile = open(f"new-{data}", "x")
            infile = open(tmpfile, "r")
            indata = geojson.load(infile)
        elif type(data) == bytes:
            indata = eval(data.decode())
        else:
            indata = data
        # these just create noise in the log file
        ignore = (
            "timestamp",
            "version",
            "changeset",
        )
        keep = ("osm_id", "id", "version")
        collection = list()
        for feature in indata["features"]:
            log.debug(f"FIXME0: {feature}")
            properties = dict()
            for key, value in feature["properties"].items():
                # log.debug(f"{key} = {value}")
                # FIXME: this is a hack!
                if True:
                    if key == "tags":
                        for k, v in value.items():
                            if k[:4] == "name":
                                properties["title"] = value[k]
                                properties["label"] = value[k]
                            else:
                                properties[k] = v
                    else:
                        if key == "osm_id":
                            properties["id"] = value
                            properties["title"] = value
                            properties["label"] = value
                        else:
                            properties[key] = value
                            if key[:4] == "name":
                                properties["title"] = value
                                properties["label"] = value
                else:
                    log.debug(f"FIXME2: {key} = {value}")
                    if key in keep:
                        properties[key] = value
                        continue
                    if key in self.tags:
                        if key == "name" or key == "name:en":
                            properties["title"] = self.tags[key]
                            properties["label"] = self.tags[key]
                        if value in self.tags[key]:
                            properties[key] = value
                        else:
                            if value != "yes":
                                log.warning(f"Value {value} not in the data model!")
                            continue
                    else:
                        if key in ignore:
                            continue
                        log.warning(f"Tag {key} not in the data model!")
                        continue
            newfeature = Feature(geometry=feature["geometry"], properties=properties)
            collection.append(newfeature)
        if type(data) == str:
            geojson.dump(FeatureCollection(collection), outfile)
        return FeatureCollection(collection)


def main():
    """This main function lets this class be run standalone by a bash script."""
    parser = argparse.ArgumentParser(description="Convert ODK XML instance file to CSV format")
    parser.add_argument("-v", "--verbose", nargs="?", const="0", help="verbose output")
    parser.add_argument("-i", "--infile", required=True, help="The data extract for ODK Collect")
    parser.add_argument("-x", "--xform", required=True, help="The XForm for ODK Collect")
    parser.add_argument("-o", "--outfile", default="models.yaml", help="The Yaml file of all tags and values")
    args = parser.parse_args()

    # if verbose, dump to the termina
    if args.verbose is not None:
        log.setLevel(logging.DEBUG)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(threadName)10s - %(name)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        log.addHandler(ch)

    FilterData()
    xlsforms_path.replace("xlsforms", "data_models")
    models = FilterData()
    data = models.parse(args.xform)
    if args.infile:
        models.cleanData(args.infile)
    else:
        if os.path.exists(args.outfile):
            os.remove(args.outfile)
        outfile = open(args.outfile, "w")
        current = None
        tab = "    "
        outfile.write(
            """
        # Do not edit this file, it is generated by the filter_data.py
        # script from the XForm spreadsheet.
        """
        )
        for key, value in data.items():
            if key != current:
                outfile.write(f"\n{key}:\n")
                for val in value:
                    outfile.write(f"{tab}- {val}\n")


if __name__ == "__main__":
    """This is just a hook so this file can be run standlone during development."""
    main()
