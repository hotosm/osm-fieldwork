#!/usr/bin/python3

# Copyright (c) 2020, 2021, 2022, 2023, 2024 Humanitarian OpenStreetMap Team
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
import re
import sys

import pandas as pd

from osm_fieldwork.xlsforms import xlsforms_path
from osm_fieldwork.yamlfile import YamlFile

# Instantiate logger
log = logging.getLogger(__name__)


def escape(value: str) -> str:
    """Escape characters like embedded quotes in text fields.

    Args:
        value (str):The string to modify

    Returns:
        (str): The escaped string
    """
    # tmp = value.replace(" ", "_")
    tmp = value.replace("&", " and ")
    return tmp.replace("'", "&apos;")


class Convert(YamlFile):
    """A class to apply a YAML config file and convert ODK to OSM.

    Returns:
        (Convert): An instance of this object
    """

    def __init__(
        self,
        xform: str = None,
    ):
        path = xlsforms_path.replace("xlsforms", "")
        if xform is not None:
            file = xform
        else:
            file = f"{path}/xforms.yaml"
        self.yaml = YamlFile(file)
        self.filespec = file
        # Parse the file contents into a data structure to make it
        # easier to retrieve values
        self.convert = dict()
        self.ignore = list()
        self.private = list()
        self.defaults = dict()
        self.entries = dict()
        self.types = dict()
        self.saved = dict()
        for item in self.yaml.yaml["convert"]:
            key = list(item.keys())[0]
            value = item[key]
            # print("ZZZZ: %r, %r" % (key, value))
            if type(value) is str:
                self.convert[key] = value
            elif type(value) is list:
                vals = dict()
                for entry in value:
                    if type(entry) is str:
                        # epdb.st()
                        tag = entry
                    else:
                        tag = list(entry.keys())[0]
                        vals[tag] = entry[tag]
                self.convert[key] = vals
        self.ignore = self.yaml.yaml["ignore"]
        self.private = self.yaml.yaml["private"]
        if "multiple" in self.yaml.yaml:
            self.multiple = self.yaml.yaml["multiple"]
        else:
            self.multiple = list()

    def privateData(
        self,
        keyword: str,
    ) -> bool:
        """Search the private data category for a keyword.

        Args:
            keyword (str): The keyword to search for

        Returns:
            (bool): =If the keyword is in the private data section
        """
        return keyword.lower() in self.private

    def convertData(
        self,
        keyword: str,
    ) -> bool:
        """Search the convert data category for a keyword.

        Args:
            keyword (str): The keyword to search for

        Returns:
            (bool): Check to see if the keyword is in the convert data section
        """
        return keyword.lower() in self.convert

    def ignoreData(
        self,
        keyword: str,
    ) -> bool:
        """Search the convert data category for a ketyword.

        Args:
            keyword (str): The keyword to search for

        Returns:
            (bool): Check to see if the keyword is in the ignore data section
        """
        return keyword.lower() in self.ignore

    def getKeyword(
        self,
        value: str,
    ) -> str:
        """Get the keyword for a value from the yaml file.

        Args:
            value (str): The value to find the keyword for

        Returns:
            (str): The keyword if found, or None
        """
        key = self.yaml.yaml(value)
        if type(key) == bool:
            return value
        if len(key) == 0:
            key = self.yaml.getKeyword(value)
        return key

    def getValues(
        self,
        keyword: str = None,
    ) -> str:
        """Get the values for a primary key.

        Args:
            keyword (str): The keyword to get the value of

        Returns:
            (str): The values or None
        """
        if keyword is not None:
            if keyword in self.convert:
                return self.convert[keyword]
        else:
            return None

    def convertEntry(
        self,
        tag: str,
        value: str,
    ) -> list:
        """Convert a tag and value from the ODK represention to an OSM one.

        Args:
            tag (str): The tag from the ODK XML file
            value (str): The value from the ODK XML file

        Returns:
            (list): The converted values
        """
        all = list()

        # If it's not in any conversion data, pass it through unchanged.
        if tag.lower() in self.ignore:
            # logging.debug(f"FIXME: Ignoring {tag}")
            return None
        low = tag.lower()
        if value is None:
            return low

        if low not in self.convert and low not in self.ignore and low not in self.private:
            return {tag: value}

        newtag = tag.lower()
        newval = value
        # If the tag is in the config file, convert it.
        if self.convertData(newtag):
            newtag = self.convertTag(newtag)
            # if newtag != tag:
            #    logging.debug(f"Converted Tag for entry {tag} to {newtag}")

        # Truncate the elevation, as it's really long
        if newtag == "ele":
            value = value[:7]
        newval = self.convertValue(newtag, value)
        # logging.debug("Converted Value for entry '%s' to '%s'" % (value, newval))
        # there can be multiple new tag/value pairs for some values from ODK
        if type(newval) == str:
            all.append({newtag: newval})
        elif type(newval) == list:
            for entry in newval:
                if type(entry) == str:
                    all.append({newtag: newval})
                elif type(entry) == dict:
                    for k, v in entry.items():
                        all.append({k: v})
        return all

    def convertValue(
        self,
        tag: str,
        value: str,
    ) -> list:
        """Convert a single tag value.

        Args:
            tag (str): The tag from the ODK XML file
            value (str): The value from the ODK XML file

        Returns:
            (list): The converted values
        """
        all = list()

        vals = self.getValues(tag)
        # There is no conversion data for this tag
        if vals is None:
            return value

        if type(vals) is dict:
            if value not in vals:
                all.append({tag: value})
                return all
            if type(vals[value]) is bool:
                entry = dict()
                if vals[value]:
                    entry[tag] = "yes"
                else:
                    entry[tag] = "no"
                all.append(entry)
                return all
            for item in vals[value].split(","):
                entry = dict()
                tmp = item.split("=")
                if len(tmp) == 1:
                    entry[tag] = vals[value]
                else:
                    entry[tmp[0]] = tmp[1]
                    logging.debug("\tValue %s converted value to %s" % (value, entry))
                all.append(entry)
        return all

    def convertTag(
        self,
        tag: str,
    ) -> str:
        """Convert a single tag.

        Args:
            tag (str): The tag from the ODK XML file

        Returns:
            (str): The new tag
        """
        low = tag.lower()
        if low in self.convert:
            newtag = self.convert[low]
            if type(newtag) is str:
                # logging.debug("\tTag '%s' converted tag to '%s'" % (tag, newtag))
                tmp = newtag.split("=")
                if len(tmp) > 1:
                    newtag = tmp[0]
            elif type(newtag) is list:
                logging.error("FIXME: list()")
                # epdb.st()
                return low, value
            elif type(newtag) is dict:
                # logging.error("FIXME: dict()")
                return low
            return newtag.lower()
        else:
            logging.debug(f"Not in convert!: {low}")
            return low

    def convertMultiple(
        self,
        value: str,
    ) -> list:
        """Convert a multiple tags from a select_multiple question..

        Args:
            value (str): The tags from the ODK XML file

        Returns:
            (list): The new tags
        """
        tags = dict()
        for tag in value.split(" "):
            low = tag.lower()
            if self.convertData(low):
                newtag = self.convert[low]
                if newtag.find("=") > 0:
                    tmp = newtag.split("=")
                    if tmp[0] in tags:
                        tags[tmp[0]] = f"{tags[tmp[0]]};{tmp[1]}"
                    else:
                        tags.update({tmp[0]: tmp[1]})
            else:
                tags.update({low: "yes"})
        # logging.debug(f"\tConverted multiple to {tags}")
        return tags

    def parseXLS(
        self,
        xlsfile: str,
    ):
        """Parse the source XLSFile if available to look for details we need."""
        if xlsfile is not None and len(xlsfile) > 0:
            self.entries = pd.read_excel(xlsfile, sheet_name=[0])[0]
            # There will only be a single sheet
            names = self.entries["name"]
            defaults = self.entries["default"]
            i = 0
            while i < len(self.entries):
                if type(self.entries["type"][i]) == float:
                    self.types[self.entries["name"][i]] = None
                else:
                    self.types[self.entries["name"][i]] = self.entries["type"][i].split(" ")[0]
                i += 1
            total = len(names)
            i = 0
            while i < total:
                entry = defaults[i]
                if str(entry) != "nan":
                    pat = re.compile("..last-saved.*")
                    if pat.match(entry):
                        name = entry.split("#")[1][:-1]
                        self.saved[name] = None
                    else:
                        self.defaults[names[i]] = entry
                i += 1
        return True

    def createEntry(
        self,
        entry: dict,
    ) -> dict:
        """Create the feature data structure.

        Args:
            entry (dict): The feature data

        Returns:
            (dict): The OSM data structure for this entry from the json file
        """
        # print(line)
        feature = dict()
        attrs = dict()
        tags = dict()
        priv = dict()
        refs = list()

        # log.debug("Creating entry")
        # First convert the tag to the approved OSM equivalent
        if "lat" in entry and "lon" in entry:
            attrs["lat"] = entry["lat"]
            attrs["lon"] = entry["lon"]
        for key, value in entry.items():
            attributes = (
                "id",
                "timestamp",
                "lat",
                "lon",
                "uid",
                "user",
                "version",
                "action",
            )

            if key in self.ignore:
                continue
            # When using existing OSM data, there's a special geometry field.
            # Otherwise use the GPS coordinates where you are.
            if key == "geometry" and len(value) > 0:
                geometry = value.split(" ")
                if len(geometry) == 4:
                    attrs["lat"] = geometry[0]
                    attrs["lon"] = geometry[1]
                continue

            # if 'lat' in attrs and len(attrs["lat"]) == 0:
            #    continue

            if key is not None and len(key) > 0 and key in attributes:
                attrs[key] = value
                # log.debug("Adding attribute %s with value %s" % (key, value))
                continue
            if value is not None and value != "no" and value != "unknown":
                if key == "username":
                    tags["user"] = value
                    continue
                items = self.convertEntry(key, value)
                if key in self.types:
                    if self.types[key] == "select_multiple":
                        vals = self.convertMultiple(value)
                        if len(vals) > 0:
                            for tag in vals:
                                tags.update(tag)
                        continue
                if key == "track" or key == "geoline":
                    # refs.append(tags)
                    # log.debug("Adding reference %s" % tags)
                    refs = value.split(";")
                elif type(value) != str:
                    if self.privateData(key):
                        priv[key] = str(value)
                    else:
                        tags[key] = str(value)
                elif len(value) > 0:
                    if self.privateData(key):
                        priv[key] = value
                    else:
                        tags[key] = value
            feature["attrs"] = attrs
            if len(tags) > 0:
                # logging.debug(f"TAGS: {tags}")
                feature["tags"] = tags
            if len(refs) > 1:
                feature["refs"] = refs
            if len(priv) > 0:
                feature["private"] = priv

        return feature

    def dump(self):
        """Dump internal data structures, for debugging purposes only."""
        print("YAML file: %s" % self.filespec)
        print("Convert section")
        for key, val in self.convert.items():
            if type(val) is list:
                print("\tTag %s is" % key)
                for data in val:
                    print("\t\t%r" % data)
            else:
                print("\tTag %s is %s" % (key, val))

        print("Ignore Section")
        for item in self.ignore:
            print(f"\tIgnoring tag {item}")


#
# This script can be run standalone for debugging purposes. It's easier to debug
# this way than using pytest,
#
def main():
    """This main function lets this class be run standalone by a bash script."""
    parser = argparse.ArgumentParser(description="Read and parse a YAML file")

    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-x", "--xform", default="xform.yaml", help="Default Yaml file")
    parser.add_argument(
        "-i",
        "--infile",
        required=True,
        help="The CSV input file",
    )
    args = parser.parse_args()

    # if verbose, dump to the terminal.
    if args.verbose is not None:
        logging.basicConfig(
            level=logging.DEBUG,
            format=("%(threadName)10s - %(name)s - %(levelname)s - %(message)s"),
            datefmt="%y-%m-%d %H:%M:%S",
            stream=sys.stdout,
        )

    # convert = Convert(args.xform)
    convert = Convert("xforms.yaml")
    print("-----")
    # tag = convert.convertTag("waterpoint_seasonal")
    # entry = convert.convertEntry("waterpoint_seasonal")
    # print("YY: %r" % entry)

    # print(convert.convertTag("tourism"))
    # entry = convert.convertEntry("tourism")
    # print(entry)
    # value = convert.convertEntry("waterpoint_seasonal")
    # print(value)
    # print("===============")

    # tag = convert.convertTag("waterpoint")
    # print(tag)
    # value = convert.convertValue("waterpoint", "well")
    # print(value)
    # value = convert.convertValue("power", "solar")

    entry = convert.convertEntry("waterpoint", "faucet")
    for i in entry:
        print("XX: %r" % i)

    entry = convert.convertEntry("operational_status", "closed")
    for i in entry:
        print("XX: %r" % i)

    entry = convert.convertEntry("seasonal", "wet")
    for i in entry:
        print("XX: %r" % i)

    entry = convert.convertEntry("seasonal", "rainy")
    for i in entry:
        print("XX: %r" % i)

    entry = convert.convertEntry("power", "solar")
    for i in entry:
        print("XX: %r" % i)


if __name__ == "__main__":
    """This is just a hook so this file can be run standlone during development."""
    main()
